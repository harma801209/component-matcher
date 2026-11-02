"""Build public-only ready-to-query filters offline; no runtime DB writes.

Example: python tools/build_catalog_ready.py --details /path/public.parquet
Use only reviewed published query/detail inputs. The existing library bundle
is not rebuilt, replaced or implicitly extracted by this tool.
"""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import platform
import runpy
import sqlite3
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import catalog_prebuilt as ready
import component_filters as filters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, default=ROOT/'cache/components_search.sqlite')
    parser.add_argument('--details', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT/'catalog_ready')
    args = parser.parse_args()
    sources = ready.source_members()
    for member, path in (('cache/components_search.sqlite', args.index),
                         ('cache/components_prepared_v5.parquet', args.details)):
        if path.stat().st_size != sources[member]['size'] or ready.digest(path) != sources[member]['sha256']:
            raise ValueError('Inputs do not match the reviewed published bundle: '+member)
        if Path(str(path)+'-wal').is_file() and Path(str(path)+'-wal').stat().st_size:
            raise ValueError('Cannot build from a live WAL')
    with tempfile.TemporaryDirectory(prefix='catalog-ready-isolated-') as folder:
        # Importing the app in build mode must not see production auth/cost/BOM
        # paths, run startup maintenance or contact remote runtime stores.
        for key, name in (('MEMBER_AUTH_DB_PATH','member'),('COST_PRICE_DB_PATH','cost'),
                          ('NO_MATCH_REPORT_DB_PATH','reports'),('BOM_JOB_DB_PATH','jobs')):
            os.environ[key] = str(Path(folder)/(name+'.sqlite'))
        os.environ.update(COMPONENT_MATCHER_BUILD_MODE='1', COMPONENT_MATCHER_STARTUP_MAINTENANCE='0',
                          MEMBER_AUTH_REMOTE_FORCE='0', RUNTIME_STORE_REMOTE_FORCE='0')
        if os.name == 'nt':
            platform._wmi = None
        loaded = runpy.run_path(str(ROOT/'component_matcher.py'), run_name='catalog_ready_build')
        app = loaded['clean_text'].__globals__
        app['SEARCH_DB_PATH'], app['PREPARED_CACHE_PATH'] = str(args.index), str(args.details)
        def connection():
            conn = sqlite3.connect(args.index.resolve().as_uri()+'?mode=ro', uri=True)
            app['install_jianghai_search_overlay'](conn)
            app['install_amotech_catalogue_overlay'](conn)
            return conn
        with closing(connection()) as conn:
            categories = filters.category_counts(conn)
        args.output.mkdir(parents=True, exist_ok=True)
        document = dict(schema=ready.SCHEMA, recipe=ready.recipe(), sources=sources, categories=categories, kinds={})
        for kind, count in categories:
            started = time.perf_counter()
            print('Preparing', kind, count, flush=True)
            with closing(connection()) as conn:
                app['install_catalog_parameters'](conn, 'offline-ready-v1', kind)
                name = __import__('hashlib').sha256(kind.encode()).hexdigest()[:16]+'.sqlite.gz'
                entry = ready.export(conn, kind, args.output/name)
                # A category must not lose or add identities during completion.
                if entry['total'] != count:
                    raise ValueError('Catalogue identity count changed: '+kind)
                document['kinds'][kind] = entry
            print('Ready', kind, entry['total'], (args.output/name).stat().st_size,
                  round(time.perf_counter()-started, 3), 'seconds', flush=True)
        if document['recipe'] != ready.recipe():
            raise ValueError('Code changed during build; rebuild before publication')
        temporary = args.output/'manifest.json.part'
        temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        os.replace(temporary, args.output/'manifest.json')
        print('Complete:', len(categories), 'categories; published inputs unchanged.', flush=True)


if __name__ == '__main__':
    main()
