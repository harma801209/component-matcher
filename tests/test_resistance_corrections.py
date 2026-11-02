"""Public resistance corrections: exact identity, preserved source, all read paths."""
import ast
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import pandas as pd
import resistance_corrections as corrections


class ResistanceCorrectionsTests(unittest.TestCase):
    def rows(self):
        return [dict(品牌=corrections.ALIASES[e['brand']][-1], 型号=e['model'],
                     _component_type='厚膜电阻' if e['model'].startswith('RS73') else '薄膜电阻', _size='0603', _res_ohm=e['old_ohms'],
                     _resistance_ohm=e['old_ohms'], 容值=str(e['old_ohms']), 容值单位='Ω',
                     _value_num=e['old_ohms'], _unit_upper='Ω', _tol='±1%',
                     _power_watt=0.25, 规格摘要=f"{e['old_ohms']}Ω ±1% 1/4W",
                     成本=7.5, _model_rule_authority='source')
                for e in corrections.catalogue().values()]

    def test_all_40_display_and_numeric_aliases_agree_and_source_is_retained(self):
        rows=self.rows()
        self.assertEqual(len(rows),40)
        for old in rows:
            entry=corrections.lookup(old['品牌'],old['型号'])
            fixed=corrections.enrich_record(old)
            self.assertEqual(fixed['_res_ohm'],entry['ohms'])
            self.assertEqual(fixed['_resistance_ohm'],entry['ohms'])
            value,unit=corrections.value_unit(entry['ohms'])
            self.assertEqual((fixed['容值'],fixed['容值单位']),(value,unit))
            self.assertEqual(fixed['_value_num'],float(value))
            self.assertEqual(fixed['_unit_upper'],unit)
            self.assertEqual(fixed['规格摘要'],value+unit+' ±1% 1/4W')
            original=json.loads(fixed['_resistance_correction_original'])
            self.assertEqual(original['_res_ohm'],entry['old_ohms'])
            self.assertNotIn('成本',original)
            for field in ('成本','_tol','_power_watt','_model_rule_authority','品牌','型号'):
                self.assertEqual(fixed[field],old[field])
            self.assertEqual(fixed['_resistance_correction_source'],entry['evidence']['url'])
            self.assertIs(corrections.enrich_record(fixed),fixed)
            self.assertEqual(old['_res_ohm'],entry['old_ohms'])

    def test_brand_kind_and_exact_identity_boundaries(self):
        row=self.rows()[0]
        for change in ({'品牌':'OTHER'}, {'型号':row['型号']+'X'}, {'_component_type':'MLCC'}):
            other={**row,**change}
            self.assertIs(corrections.enrich_record(other),other)
        alias={**row,'品牌':'koa','型号':' '+row['型号'].lower()+' '}
        self.assertEqual(corrections.enrich_record(alias)['_res_ohm'],280000)

    def test_reviewed_values_agree_with_independent_naming_code_decoder(self):
        from model_naming_guide import resistance
        for entry in corrections.catalogue().values():
            self.assertEqual(float(resistance(entry['code'])),entry['ohms'])

    def test_frame_preserves_duplicate_index_categorical_columns_and_unrelated_rows(self):
        source=self.rows()+[dict(品牌='OTHER',型号='UNCHANGED',_res_ohm=123,容值='123')]
        frame=pd.DataFrame(source,index=[0]*len(source))
        frame['容值']=frame['容值'].astype('category')
        frame['_value_num']=frame['_value_num'].astype('string')
        fixed=corrections.enrich_frame(frame)
        self.assertEqual(len(fixed),len(frame))
        self.assertEqual(fixed.index.tolist(),frame.index.tolist())
        self.assertEqual(fixed.iloc[0]['_res_ohm'],280000)
        self.assertEqual(fixed.iloc[-1]['_res_ohm'],123)
        self.assertEqual(frame.iloc[0]['_res_ohm'],28000)
        self.assertIs(corrections.enrich_frame(fixed),fixed)

    def fixture(self,conn):
        conn.execute('CREATE TABLE components_search_resistor (品牌 TEXT,型号 TEXT,_component_type TEXT,_size TEXT,_res_ohm REAL,_tol TEXT,_power_watt REAL)')
        conn.execute('CREATE INDEX identity_lookup ON components_search_resistor(品牌,型号)')
        conn.execute('CREATE INDEX numeric_lookup ON components_search_resistor(_component_type,_size,_res_ohm,_tol,_power_watt)')
        names=('品牌','型号','_component_type','_size','_res_ohm','_tol','_power_watt')
        rows=self.rows()
        conn.executemany('INSERT INTO components_search_resistor VALUES(?,?,?,?,?,?,?)',
                         [tuple(r[k] for k in names) for r in rows+[rows[0]]])
        conn.execute('INSERT INTO components_search_resistor VALUES(?,?,?,?,?,?,?)',('OTHER',rows[0]['型号'],'薄膜电阻','0603',28000,'±5%',1))
        conn.execute('INSERT INTO components_search_resistor VALUES(?,?,?,?,?,?,?)',('KOA',rows[0]['型号'],'MLCC','0603',28000,'±5%',1))
        conn.commit()

    def test_read_only_sql_overlay_corrects_40_and_keeps_duplicates_and_original_index(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'public.sqlite'
            with closing(sqlite3.connect(path)) as conn:self.fixture(conn)
            before=path.read_bytes()
            with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as conn:
                corrections.install_search_overlay(conn)
                corrections.install_search_overlay(conn)
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM components_search_resistor').fetchone()[0],43)
                for row in self.rows():
                    key=(row['品牌'],row['型号'],row['_component_type'])
                    expected=corrections.lookup(*key)['ohms']
                    values=conn.execute('SELECT _res_ohm,_tol,_power_watt FROM components_search_resistor WHERE 品牌=? AND 型号=? AND _component_type=?',key).fetchall()
                    self.assertTrue(values)
                    self.assertTrue(all(v==(expected,'±1%',0.25) for v in values))
                    self.assertFalse(conn.execute('SELECT 1 FROM components_search_resistor WHERE 品牌=? AND 型号=? AND _component_type=? AND _res_ohm=?',(*key,row['_res_ohm'])).fetchall())
                self.assertEqual(conn.execute('SELECT _res_ohm FROM main.components_search_resistor LIMIT 1').fetchone()[0],28000)
                self.assertEqual(conn.execute("SELECT _res_ohm FROM components_search_resistor WHERE 品牌='OTHER'").fetchone()[0],28000)
                self.assertEqual(conn.execute("SELECT _res_ohm FROM components_search_resistor WHERE _component_type='MLCC'").fetchone()[0],28000)
                plan=' '.join(str(r) for r in conn.execute('EXPLAIN QUERY PLAN SELECT 型号 FROM components_search_resistor WHERE _component_type=? AND _size=? AND _res_ohm=?',('薄膜电阻','0603',280000)))
                self.assertIn('numeric_lookup',plan)
                self.assertIn('verified_resistance_numeric',plan)
            self.assertEqual(path.read_bytes(),before)

    def test_overlay_composes_with_existing_view_and_ignores_absent_tables(self):
        with closing(sqlite3.connect(':memory:')) as conn:
            corrections.install_search_overlay(conn)
            self.fixture(conn)
            conn.execute('CREATE TEMP VIEW components_search_resistor AS SELECT * FROM main.components_search_resistor WHERE 品牌 != \'OTHER\'')
            corrections.install_search_overlay(conn)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM components_search_resistor').fetchone()[0],42)
            self.assertEqual(conn.execute("SELECT _res_ohm FROM components_search_resistor WHERE _component_type='薄膜电阻' AND 型号=?",(self.rows()[0]['型号'],)).fetchone()[0],280000)

    def test_application_and_offline_builder_use_same_corrections(self):
        root=Path(__file__).resolve().parents[1]
        tree=ast.parse((root/'component_matcher.py').read_text(encoding='utf-8'))
        functions={n.name:ast.unparse(n) for n in tree.body if isinstance(n,ast.FunctionDef)}
        for name in ('open_search_db_connection','cached_catalog_passive_source'):
            self.assertIn('_resistance_corrections.install_search_overlay(conn)',functions[name])
        for name in ('prepare_search_dataframe','_load_prepared_data_cached'):
            self.assertIn('_resistance_corrections.enrich_frame',functions[name])
        self.assertIn('_resistance_corrections.enrich_record',functions['build_lightweight_component_row_from_search_sidecar'])
        self.assertIn("app['_resistance_corrections'].install_search_overlay(conn)",(root/'tools/build_catalog_ready.py').read_text(encoding='utf-8'))


if __name__=='__main__':unittest.main()
