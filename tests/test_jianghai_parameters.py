import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd

import jianghai_parameters as jp


class JianghaiParameterTests(unittest.TestCase):
    def test_dataset_has_only_unique_catalog_keys_with_provenance(self):
        payload, models = jp.load_data()
        self.assertEqual(len(payload['records']), 4661)
        self.assertEqual(len(models), 4661)
        self.assertGreater(sum('_life_hours_num' in r['values'] for r in payload['records']), 1000)
        for record in payload['records']:
            for field in jp.NUMERIC:
                if field in record['values']:
                    self.assertIn(record['source'], payload['sources'])
                    self.assertIn(1, record['pages'])

    def test_cd293_units_conditions_and_numeric_fields_agree(self):
        row = jp.enrich_record({'品牌':'江海Jianghai','型号':'ECS1ABZ183M250030','备注1':'original'})
        self.assertEqual(row['寿命（h）'], '2000')
        self.assertEqual(row['_life_hours_num'], 2000)
        self.assertEqual(row['工作温度'], '-40~85℃')
        self.assertEqual(row['ESR'], '30mΩ')
        self.assertEqual(row['ESR典型值'], '24mΩ')
        self.assertEqual(row['纹波电流'], '3.6A')
        self.assertIn('120Hz', row['ESR条件'])
        self.assertIn('85℃', row['纹波电流条件'])
        self.assertIn('original', row['备注1'])
        self.assertEqual(row['耐压（V）'], '10')
        self.assertEqual(jp.enrich_record(row), row)

    def test_wrong_brand_incomplete_code_and_new_variant_are_not_fuzzy_filled(self):
        for brand,model in [('OTHER','ECS1ABZ183M250030'),('江海','ECS1ABZ183M25003'),('江海','ECS1ABZ183M250030X')]:
            row={'品牌':brand,'型号':model,'ESR':''}
            self.assertEqual(jp.enrich_record(row), row)

    def test_voltage_is_not_the_capacitance_code_and_temperature_uses_correct_band(self):
        row=jp.enrich_record({'品牌':'江海Jianghai','型号':'ECR0JBK330M','耐压（V）':'330'})
        self.assertEqual(row['耐压（V）'],'6.3')
        self.assertEqual(row['_temp_low'],-40)
        high=jp.enrich_record({'品牌':'江海Jianghai','型号':'ECS2HBZ101M'})
        self.assertEqual(high['耐压（V）'],'500')
        self.assertEqual(high['_temp_low'],-25)

    def test_pending_display_does_not_invent_numeric_values(self):
        frame=pd.DataFrame([{'品牌':'江海Jianghai','型号':'ECS1ABZ183M250030','纹波电流':'','寿命（h）':'','_life_hours_num':None}])
        shown=jp.annotate_pending_display(frame)
        self.assertIn('待核实',shown.at[0,'寿命（h）'])
        self.assertIsNone(shown.at[0,'_life_hours_num'])

    def test_frame_preserves_other_brand_and_numeric_index_and_original(self):
        original = pd.DataFrame([
            {'品牌':'江海Jianghai','型号':'ECS1ABZ183M250030','寿命（h）':'','_life_hours_num':None},
            {'品牌':'OTHER','型号':'ECS1ABZ183M250030','寿命（h）':'123','_life_hours_num':123},
        ])
        out=jp.enrich_frame(original)
        self.assertEqual(out.loc[0,'_life_hours_num'],2000)
        self.assertEqual(out.loc[1,'寿命（h）'],'123')
        self.assertEqual(original.loc[0,'寿命（h）'],'')

    def test_sql_filter_and_hydration_use_overlay_without_persistent_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'catalog.sqlite'
            conn=sqlite3.connect(path)
            conn.execute('CREATE TABLE components_search_capacitor (品牌 TEXT, 型号 TEXT, _life_hours_num REAL, _temp_low REAL, _temp_high REAL, _pf REAL, _volt_num REAL)')
            conn.executemany('INSERT INTO components_search_capacitor VALUES (?,?,?,?,?,?,?)',[
                ('江海Jianghai','ECS1ABZ183M250030',None,None,None,18000000000,250),
                ('OTHER','ECS1ABZ183M250030',1000,-10,50,1,250),
            ])
            conn.commit();conn.close()
            before=hashlib.sha256(path.read_bytes()).hexdigest()
            conn=sqlite3.connect(f'file:{path.as_posix()}?mode=ro',uri=True)
            jp.install_search_overlay(conn)
            jp.install_search_overlay(conn)
            rows=conn.execute('SELECT 品牌 FROM components_search_capacitor WHERE _life_hours_num>=2000 AND _temp_high>=85 AND _temp_low<=-40').fetchall()
            self.assertEqual(rows,[('江海Jianghai',)])
            self.assertEqual(conn.execute('SELECT _volt_num FROM components_search_capacitor WHERE 品牌="江海Jianghai"').fetchone(),(10,))
            self.assertEqual(conn.execute('SELECT _life_hours_num FROM main.components_search_capacitor WHERE 品牌="江海Jianghai"').fetchone(),(None,))
            conn.close()
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)

    def test_no_table_noop_and_bad_payload_fail_closed(self):
        conn=sqlite3.connect(':memory:')
        jp.install_search_overlay(conn)
        conn.close()
        with tempfile.TemporaryDirectory() as folder:
            bad=Path(folder)/'bad.json'
            bad.write_text('{"schema_version":999}',encoding='utf-8')
            with patch.object(jp,'DATA_PATH',bad):
                payload,_=jp.load_data()
                self.assertEqual(payload['records'],[])

    def test_string_numeric_columns_and_duplicate_bom_indices(self):
        original=pd.DataFrame([{'品牌':'江海Jianghai','型号':'ECS1ABZ183M250030','_life_hours_num':'','_volt_num':'250'}]*2,index=[7,7])
        original['_life_hours_num']=original['_life_hours_num'].astype('string')
        original['_volt_num']=original['_volt_num'].astype('string')
        out=jp.enrich_frame(original)
        self.assertEqual(out.index.tolist(),[7,7])
        self.assertEqual(out['_life_hours_num'].tolist(),[2000,2000])
        self.assertEqual(out['_volt_num'].tolist(),[10,10])


if __name__=='__main__':
    unittest.main()
