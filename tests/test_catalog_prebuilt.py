import ast
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest

import catalog_prebuilt as ready
import component_filters as filters
from tests import test_component_filters as fixtures


class ReadyCatalogTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix='ready-filter-test-')
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.assets = self.root/'assets'
        self.fixture = fixtures.CatalogFilterTests()
        self.fixture.setUp()

    def tearDown(self):
        self.fixture.tearDown()

    def exported(self, kind='厚膜电阻'):
        self.assets.mkdir(exist_ok=True)
        entry = ready.export(self.fixture.conn, kind, self.assets/'0123456789abcdef.sqlite.gz')
        return dict(kinds={kind:entry})

    def opened(self, doc, kind='厚膜电阻'):
        return ready.open_source(doc, kind, self.assets, self.root/'cache')

    def function(self, name):
        path = Path(__file__).resolve().parents[1]/'component_matcher.py'
        node = next(n for n in ast.parse(path.read_text(encoding='utf-8')).body
                    if isinstance(n, ast.FunctionDef) and n.name == name)
        node.decorator_list = []
        return compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec')

    def test_roundtrip_exact_duplicates_nulls_zero_fields_filters_and_sort(self):
        doc = self.exported()
        source = self.opened(doc)
        self.assertIsNotNone(source)
        self.addCleanup(source.connection.close)
        self.assertFalse(source.verified_unique)  # fixture has actual duplicate rows
        cases = [{}, dict(selected={'_size':['0402'], '_tol':['1']}),
                 dict(ranges={'_res_ohm':(0,10000)}, sort_key='_tol', sort_desc=True),
                 dict(selected={'_tol':[filters.MISSING]}),
                 dict(keyword='R_',keyword_mode='prefix'),dict(page=2,page_size=2)]
        for case in cases:
            original = filters.snapshot(self.fixture.conn, '厚膜电阻', include_rows=True, **case)
            actual = filters.snapshot(source.connection, '厚膜电阻', include_rows=True,
                verified_unique=source.verified_unique, query_cache=source.query_cache, **case)
            self.assertEqual(actual, original)
        with self.assertRaises(sqlite3.OperationalError):
            source.connection.execute('DELETE FROM catalog_browse_source')

    def test_cold_initial_snapshot_uses_published_aggregates_without_whole_kind_scan(self):
        doc = self.exported('MLCC')
        source = self.opened(doc, 'MLCC')
        self.addCleanup(source.connection.close)
        statements = []
        source.connection.set_trace_callback(statements.append)
        anonymous = filters.snapshot(source.connection,'MLCC',include_rows=False,
            verified_unique=source.verified_unique,query_cache=source.query_cache)
        self.assertEqual(anonymous['total'],3)
        self.assertEqual(anonymous['rows'],[])
        self.assertFalse(any('COUNT(' in s or 'MIN(' in s for s in statements),statements)
        columns = {r[1] for r in source.connection.execute('PRAGMA table_info(catalog_browse_source)')}
        self.assertFalse(columns & {'成本','价格','username','member_id','customer_id','password'})

    def test_existing_completed_lifecycle_citations_are_exported_unchanged(self):
        conn = self.fixture.conn
        conn.execute('CREATE TEMP VIEW catalog_lifecycle_source AS SELECT *,\'NRND\' AS 生产状态,\'https://manufacturer.example/part\' AS _lifecycle_source,\'2026-11-02\' AS _lifecycle_checked FROM components_search_resistor WHERE _component_type=\'厚膜电阻\'')
        source = self.opened(self.exported())
        self.addCleanup(source.connection.close)
        snapshot = filters.snapshot(source.connection,'厚膜电阻',include_rows=True)
        self.assertEqual(snapshot['rows'][0]['生产状态'],'NRND')
        self.assertEqual(snapshot['rows'][0]['_lifecycle_source'],'https://manufacturer.example/part')

    def test_corrupt_or_wrong_kind_or_traversal_assets_never_open(self):
        doc = self.exported()
        self.assertIsNone(self.opened(doc,'MLCC'))
        entry = doc['kinds']['厚膜电阻']
        name = entry['file']
        for bad in ('../0123456789abcdef.sqlite.gz','other.sqlite.gz'):
            entry['file'] = bad
            self.assertIsNone(self.opened(doc))
        entry['file'] = name
        entry['raw_sha256'] = '0'*64
        self.assertIsNone(self.opened(doc))
        self.assertFalse(list((self.root/'cache').glob('*.part')))
        (self.assets/name).write_bytes(b'corrupt')
        self.assertIsNone(self.opened(doc))

    def revision_fixture(self):
        (self.root/'logic.py').write_text('PUBLIC = 1',encoding='utf-8')
        (self.root/'cache').mkdir(exist_ok=True)
        members = []
        for name, value in (('components_search.sqlite',b'query'),('components_prepared_v5.parquet',b'detail')):
            path = self.root/'cache'/name
            path.write_bytes(value)
            members.append(dict(path='cache/'+name,size=len(value),sha256=ready.digest(path)))
        (self.root/'streamlit_cloud_bundle.manifest.json').write_text(json.dumps(dict(members=members)))
        (self.root/'manufacturer_lifecycle_evidence.json').write_text('{}')
        self.assets.mkdir(exist_ok=True)
        document = dict(schema=ready.SCHEMA,recipe=ready.recipe(self.root),sources=ready.source_members(self.root),categories=[['MLCC',3]],kinds={})
        (self.assets/'manifest.json').write_text(json.dumps(document))
        return document

    def test_revision_checks_real_index_and_details_even_same_size_and_live_wal(self):
        self.revision_fixture()
        self.assertIsNotNone(ready.manifest(self.root,self.assets))
        index = self.root/'cache/components_search.sqlite'
        index.write_bytes(b'WRONG')
        self.assertIsNone(ready.manifest(self.root,self.assets))
        index.write_bytes(b'query')
        wal = Path(str(index)+'-wal')
        wal.write_bytes(b'pending')
        self.assertIsNone(ready.manifest(self.root,self.assets))
        wal.unlink()
        index.unlink()
        # Missing public input does not require a user-visible restore step.
        self.assertIsNotNone(ready.manifest(self.root,self.assets))
        (self.root/'cache/components_prepared_v5.parquet').write_bytes(b'BADBAD')
        self.assertIsNone(ready.manifest(self.root,self.assets))

    def test_recipe_evidence_and_bundle_changes_invalidate_but_release_stamp_does_not(self):
        self.revision_fixture()
        original = ready.recipe(self.root)
        (self.root/'component_matcher.py').write_text('PUBLIC_CODE_STAMP = "old"\n')
        first = ready.recipe(self.root)
        (self.root/'component_matcher.py').write_text('PUBLIC_CODE_STAMP = "new"\n')
        self.assertEqual(first, ready.recipe(self.root))
        self.assertNotEqual(first, original)
        self.assertIsNone(ready.manifest(self.root,self.assets))
        (self.root/'component_matcher.py').unlink()
        (self.root/'manufacturer_lifecycle_evidence.json').write_text('{"changed":true}')
        self.assertIsNone(ready.manifest(self.root,self.assets))

    def test_windows_and_linux_checkout_line_endings_have_identical_recipe(self):
        self.revision_fixture()
        path = self.root/'logic.py'
        path.write_bytes(b'PUBLIC = 1\r\nMORE = 2\r\n')
        windows = ready.recipe(self.root)
        path.write_bytes(b'PUBLIC = 1\nMORE = 2\n')
        self.assertEqual(windows,ready.recipe(self.root))

    def test_shipped_assets_cover_every_category_and_match_public_revision(self):
        path = ready.ASSETS/'manifest.json'
        if not path.is_file():
            self.skipTest('Offline build has not produced the shipped manifest yet')
        document = ready.manifest()
        self.assertIsNotNone(document,'Rebuild public filters after changing catalogue code or evidence')
        self.assertEqual(set(document['kinds']),{r[0] for r in document['categories']})
        for kind,count in document['categories']:
            entry = document['kinds'][kind]
            self.assertEqual(entry['total'],count)
            self.assertEqual(ready.digest(ready.ASSETS/entry['file']),entry['sha256'])

    def test_fast_app_route_never_restores_parquet_or_builds_temporary_catalogue(self):
        source = self.opened(self.exported())
        self.addCleanup(source.connection.close)
        namespace = dict(cached_catalog_ready_source=lambda *args:source,_catalog_filters=filters)
        exec(self.function('cached_catalog_snapshot'),namespace)
        result = namespace['cached_catalog_snapshot']('revision','厚膜电阻',{}, {},'',1,20,False)
        self.assertEqual(result['total'],6)
        self.assertEqual(result['rows'],[])
        namespace = dict(cached_catalog_ready_manifest=lambda *args:dict(categories=[['MLCC',3]]))
        exec(self.function('cached_catalog_categories'),namespace)
        self.assertEqual(namespace['cached_catalog_categories']('cold'),[('MLCC',3)])
