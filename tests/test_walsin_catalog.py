import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
import pandas as pd
import walsin_catalog as catalogue


class WalsinCatalogueTests(unittest.TestCase):
    def test_index_ratings_do_not_reenrich_catalogue_or_fill_conflicting_rows(self):
        from unittest.mock import patch
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE components_search_core (品牌,型号,_model_clean,_component_type)')
            conn.execute('CREATE TABLE components_search_capacitor (id,品牌,型号,_component_type,_size,_mat,_pf,_volt_num,_temp_low,_temp_high)')
            model='HH18N1R5B500CT'
            rows=[(1,catalogue.BRAND,model,'MLCC','0603','C0G',1.5,50,None,None),
                  (2,catalogue.BRAND,model,'MLCC','0603','X7R',1.5,50,None,None),
                  (3,catalogue.BRAND,model,'MLCC','0603','C0G',99,50,None,None),
                  (4,catalogue.BRAND,model,'MLCC','0603','C0G',1.5,25,None,None),
                  (5,catalogue.BRAND,model,'MLCC','0603','C0G',1.5,50,None,999),
                  (6,catalogue.BRAND,model,'MLCC','9999','C0G',1.5,50,None,None),
                  (7,'Other',model,'MLCC','0603','C0G',1.5,50,None,None),
                  (8,catalogue.BRAND,model,'MLCC','0603','COG(NPO)',1.5,50,None,None),
                  (9,catalogue.BRAND,'\t '+model+' \n','MLCC','0603','C0G',1.5,50,None,None),
                  (10,catalogue.BRAND,model,'MLCC',603,'C0G',1.5,50,None,None),
                  (11,catalogue.BRAND,model,'MLCC','0603','C0G','1.5garbage',50,None,None)]
            conn.execute('INSERT INTO components_search_core VALUES (?,?,?,?)',(catalogue.BRAND,model,model,'MLCC'))
            conn.executemany('INSERT INTO components_search_capacitor VALUES (?,?,?,?,?,?,?,?,?,?)',rows)
            with patch.object(catalogue,'enrich_record',wraps=catalogue.enrich_record) as enrich:
                catalogue.install_search_overlay(conn)
                catalogue.install_search_overlay(conn)
                self.assertEqual(enrich.call_count,0)
            actual=conn.execute('SELECT id,_temp_low,_temp_high FROM components_search_capacitor WHERE id IS NOT NULL ORDER BY id').fetchall()
            self.assertEqual(actual,[(1,-55,125),(2,None,None),(3,None,None),(4,None,None),
                                     (5,None,999),(6,None,None),(7,None,None),(8,-55,125),(9,-55,125),
                                     (10,-55,125),(11,None,None)])
            self.assertEqual(conn.execute('SELECT * FROM main.components_search_capacitor ORDER BY id').fetchall(),rows)

    def test_index_corrections_keep_original_whitespace_and_case_normalization(self):
        from unittest.mock import patch
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE components_search_core (品牌,型号,_model_clean,_component_type)')
            conn.execute('CREATE TABLE components_search_capacitor (品牌,型号,_component_type,_size,_mat,_pf,_tol,_volt_num,_temp_low,_temp_high)')
            model=' \t1210b224k451ct \n'
            row=(catalogue.BRAND,model,'MLCC','1210','X7R',220000,'0.1PF',16,None,None)
            conn.execute('INSERT INTO components_search_core VALUES (?,?,?,?)',(catalogue.BRAND,model,model,'MLCC'))
            conn.execute('INSERT INTO components_search_capacitor VALUES (?,?,?,?,?,?,?,?,?,?)',row)
            with patch.object(catalogue,'enrich_record',wraps=catalogue.enrich_record) as enrich:
                catalogue.install_search_overlay(conn)
                self.assertEqual(enrich.call_count,1)
            self.assertEqual(conn.execute('SELECT _tol,_volt_num,_temp_low,_temp_high FROM components_search_capacitor WHERE 型号=?',(model,)).fetchone(),('10',450,-55,125))
            self.assertEqual(conn.execute('SELECT * FROM main.components_search_capacitor').fetchone(),row)

    def test_reviewed_family_temperature_tables_are_separate_and_blank_only(self):
        examples=('HH18N1R5B500CT','RF03N1R7B500CT','RF18G0R9A251',
                  '0603B101K201CT','SH15B104K160CT')
        for model in examples:
            with self.subTest(model=model):
                item=catalogue.listed(model)
                self.assertIsNotNone(item)
                profile=catalogue.temperature_profile(item)
                self.assertIsNotNone(profile)
                row={'品牌':catalogue.BRAND,'型号':model,'工作温度':'',
                     '_temp_low':None,'_temp_high':None,'成本':123}
                fixed=catalogue.enrich_record(row)
                self.assertEqual(fixed['_temp_low'],-55)
                self.assertEqual(fixed['_temp_high'],150 if item['material']=='X8G' else 125)
                self.assertIn(profile['url'],fixed['备注1'])
                self.assertEqual(fixed['成本'],123)
                self.assertEqual(catalogue.enrich_record(fixed),fixed)
                for changes in ({'品牌':'信昌PDC'},{'_mat':'Y5V'},{'_temp_high':999},
                                {'_pf':999999999},{'_size':'9999'},{'工作温度':'manual'}):
                    old=dict(row,**changes)
                    self.assertEqual(catalogue.enrich_record(old),old)
        for series,material in [('Microwave Caps_(RF series)','Y5V'),
                               ('Middle to High Voltage Caps_(200V-4kV)','Y5V'),
                               ('Automotive Caps Without AEC-Q200 Certification_(MG series)','X7R')]:
            self.assertIsNone(catalogue.temperature_profile(dict(series=series,material=material,size='0603',pf=100,voltage=250)))
        original=catalogue.listed('RF18G0R9A251')
        for changes in ({'voltage':100},{'size':'0201'},{'pf':1000}):
            self.assertIsNone(catalogue.temperature_profile(dict(original,**changes)))

    def test_temperature_frame_does_not_cross_duplicate_source_indexes(self):
        frame=pd.DataFrame([{'品牌':catalogue.BRAND,'型号':'HH18N1R5B500CT','工作温度':''},
                            {'品牌':'Other','型号':'HH18N1R5B500CT','工作温度':''}],index=[5,5])
        original=frame.copy(deep=True)
        fixed=catalogue.enrich_frame(frame)
        self.assertEqual(fixed['工作温度'].tolist(),['-55~125℃',''])
        self.assertEqual(list(fixed.index),[5,5])
        pd.testing.assert_frame_equal(frame,original)

    def test_unrelated_candidate_predicates_keep_main_spec_index_and_upstream_rows(self):
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE components_search_core (品牌,型号,_model_clean,_component_type)')
            conn.execute('CREATE INDEX test_core_model ON components_search_core(_model_clean)')
            conn.execute('CREATE TABLE components_search_capacitor (品牌,型号,_component_type,_size,_mat,_pf,_tol,_volt_num)')
            conn.execute('CREATE INDEX test_cap_spec ON components_search_capacitor(_size,_mat,_pf,_volt_num)')
            rows=[('信昌PDC','FN18X104K500PBG','MLCC','0603','X7R',100000,'10',50),
                  (None,'NULLBRAND','MLCC','0603','X7R',100000,'10',50),
                  ('Other','NULLTYPE',None,'0603','X7R',100000,'10',50),
                  (catalogue.BRAND,'0805A106K250CT','MLCC','0805',None,10000000,'10',25)]
            conn.executemany('INSERT INTO components_search_capacitor VALUES (?,?,?,?,?,?,?,?)',rows)
            conn.executemany('INSERT INTO components_search_core VALUES (?,?,?,?)',[(r[0],r[1],r[1],r[2]) for r in rows])
            conn.execute('CREATE TEMP TABLE upstream AS SELECT * FROM main.components_search_capacitor WHERE 0')
            conn.execute("INSERT INTO upstream VALUES ('Upstream','NEW','MLCC','0603','X7R',100000,'10',50)")
            conn.execute('CREATE TEMP VIEW components_search_capacitor AS SELECT * FROM main.components_search_capacitor UNION ALL SELECT * FROM upstream')
            catalogue.install_search_overlay(conn)
            for row in rows[:3]:
                self.assertEqual(conn.execute('SELECT * FROM components_search_capacitor WHERE 型号=?',(row[1],)).fetchone(),row)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM components_search_capacitor WHERE 型号='NEW'").fetchone()[0],1)
            self.assertEqual(conn.execute('SELECT _mat FROM components_search_capacitor WHERE 型号=?',('0805A106K250CT',)).fetchone()[0],'X7S')
            query='SELECT 品牌,型号 FROM components_search_capacitor WHERE _size=? AND _mat=? AND _pf=? AND _volt_num=?'
            plan=conn.execute('EXPLAIN QUERY PLAN '+query,('0603','X7R',100000,50)).fetchall()
            self.assertTrue(any('USING INDEX test_cap_spec' in row[3] for row in plan),plan)
            core_plan=conn.execute('EXPLAIN QUERY PLAN SELECT * FROM components_search_core WHERE _model_clean=?',('FN18X104K500PBG',)).fetchall()
            self.assertTrue(any('USING INDEX test_core_model' in row[3] for row in core_plan),core_plan)
            self.assertFalse(any('LEFT-JOIN' in row[3] for row in core_plan),core_plan)

    def test_mt_temperature_is_exact_catalogue_series_and_blank_only(self):
        row=catalogue.row(catalogue.listed('MT18B334K500CT'))
        self.assertEqual(row['工作温度'],'-55~125℃')
        self.assertIn('第3页',row['备注1'])
        old={'品牌':catalogue.BRAND,'型号':'MT18B334K500CT','工作温度':'','_temp_low':None,'_temp_high':None,'成本':123}
        fixed=catalogue.enrich_record(old)
        self.assertEqual(fixed['工作温度'],'-55~125℃')
        self.assertEqual(fixed['_temp_high'],125)
        self.assertEqual(fixed['成本'],123)
        self.assertEqual(catalogue.enrich_record(fixed),fixed)
        self.assertEqual(catalogue.enrich_record(dict(old,工作温度='-55~150℃'))['工作温度'],'-55~150℃')
        self.assertEqual(catalogue.enrich_record(dict(old,品牌='信昌PDC')),dict(old,品牌='信昌PDC'))
        self.assertEqual(catalogue.enrich_record(dict(old,型号='MT18B999K500CT'))['工作温度'],'')
        self.assertEqual(catalogue.enrich_record(dict(old,_mat='X5R'))['工作温度'],'')
        self.assertEqual(catalogue.enrich_record(dict(old,_temp_high=150))['工作温度'],'')
        for material,high in [('X8G',150),('C0G',125),('X7R',125),('X6S',105)]:
            self.assertEqual(catalogue.mt_temperature_high(dict(series='Automotive Caps Qualified to AEC-Q200 (MT series)',material=material)),high)
        self.assertIsNone(catalogue.mt_temperature_high(dict(series='Automotive Caps Without AEC-Q200 Certification_(MG series)',material='X7R')))


    def test_x7s_is_a_listed_manufacturer_identity_not_a_synthetic_grid(self):
        x7s=[r for r in catalogue.catalogue_rows() if r['材质（介质）']=='X7S']
        self.assertEqual(len(x7s),20)
        actual=catalogue.row(catalogue.listed('0805A106K250CT'),'0805A106K250CT')
        self.assertEqual(actual['材质（介质）'],'X7S')
        self.assertEqual(actual['容值_pf'],10_000_000)
        self.assertEqual(actual['耐压（V）'],25)
        self.assertEqual(actual['工作温度'],'-55~125℃')
        self.assertIn('±',actual['_body_size'])
        self.assertIn('1.25',actual['_body_size'])
        self.assertIsNone(catalogue.listed('0805A999K250CT'))

    def test_conflicting_public_record_is_not_treated_as_verified(self):
        self.assertIsNone(catalogue.listed('0805A474K101'))
        quarantined=catalogue.document()['quarantined']
        self.assertTrue(any(r['model']=='0805A474K101' and r['reason']=='capacitance_code_conflict' for r in quarantined))
        self.assertTrue(all(len(s['sha256'])==64 for s in catalogue.document()['sources']))
        self.assertTrue(all(not r.get('生产状态') and '价格' not in r and '成本' not in r for r in catalogue.catalogue_rows()))

    def test_only_base_identity_needs_ordering_suffix_confirmation(self):
        self.assertIn('尾码',catalogue.ordering_warning({'品牌':catalogue.BRAND,'型号':'0805A106K250'}))
        self.assertEqual(catalogue.ordering_warning({'品牌':catalogue.BRAND,'型号':'0805A106K250CT'}),'')
        self.assertEqual(catalogue.ordering_warning({'品牌':'信昌PDC','型号':'0805A106K250'}),'')

    def test_source_dimension_variants_are_not_fused(self):
        item=next(r for r in catalogue.document()['records'] if r.get('dimension_variants'))
        value=catalogue.row(item)
        self.assertFalse(value['长度（mm）'] or value['宽度（mm）'] or value['高度（mm）'])
        self.assertIn('多种',value['备注2'])
        self.assertFalse(value['_body_size'])

    def test_narrow_index_frames_keep_zero_price_and_lifecycle_out(self):
        frames=catalogue.index_frames()
        self.assertEqual(len(frames['components_search_core']),len(catalogue.document()['records']))
        row=frames['components_search_capacitor'].set_index('型号').loc['0805A106K250']
        self.assertEqual(row['_mat'],'X7S')
        self.assertEqual(row['_temp_high'],125)
        mt=frames['components_search_capacitor'].set_index('型号').loc['MT18B334K500']
        self.assertEqual(mt['_temp_low'],-55)
        self.assertEqual(mt['_temp_high'],125)
        self.assertFalse({'价格','成本','生产状态','member_id'} & set(row.index))

    def test_historical_corrections_are_exact_model_old_value_and_brand_guarded(self):
        self.assertEqual(len(catalogue.corrections()),187)
        self.assertEqual(sum(len(r['fields']) for r in catalogue.corrections().values()),190)
        for model, correction in catalogue.corrections().items():
            original={'品牌':catalogue.BRAND,'型号':model,'成本':123.45,'价格':678.9,'工作温度':'manual-temperature'}
            original.update({field:change['old'] for field,change in correction['fields'].items()})
            actual=catalogue.enrich_record(original)
            for field,change in correction['fields'].items():
                self.assertEqual(actual[field],change['new'],(model,field))
            self.assertEqual(actual['成本'],123.45)
            self.assertEqual(actual['价格'],678.9)
            self.assertEqual(catalogue.enrich_record(actual),actual)
            other=dict(original,品牌='Other')
            self.assertEqual(catalogue.enrich_record(other),other)
            revised=dict(original)
            revised.update({field:'manual-revision' for field in correction['fields']})
            self.assertEqual(catalogue.enrich_record(revised),revised)
        corrected=catalogue.enrich_frame(pd.DataFrame([{
            '品牌':catalogue.BRAND,'型号':'1210B224K451CT','_tol':'0.1PF',
            '容值误差':'±0.1pF','_volt_num':16.,'耐压（V）':'16V','成本':100}]))
        self.assertEqual(float(corrected.iloc[0]['_volt_num']),450)
        self.assertEqual(str(corrected.iloc[0]['_tol']),'10')
        self.assertEqual(corrected.iloc[0]['成本'],100)

    def test_temporary_overlay_preserves_base_known_values_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'public.sqlite'
            with sqlite3.connect(path) as c:
                c.execute('CREATE TABLE components_search_core (品牌,型号,_model_clean,_component_type)')
                c.execute('CREATE TABLE components_search_capacitor (品牌,型号,_component_type,_size,_mat,_pf,_tol,_volt_num,_mount_style)')
                c.execute('INSERT INTO components_search_core VALUES (?,?,?,?)',(catalogue.BRAND,'0805A106K250CT','0805A106K250CT','MLCC'))
                c.execute('INSERT INTO components_search_capacitor VALUES (?,?,?,?,?,?,?,?,?)',(catalogue.BRAND,'0805A106K250CT','MLCC','0805',None,10_000_000,'10',25,None))
                c.execute('INSERT INTO components_search_capacitor VALUES (?,?,?,?,?,?,?,?,?)',('Other','0805A106K250CT','MLCC','0805','Other',1,'5',16,None))
            c.close()
            before=hashlib.sha256(path.read_bytes()).hexdigest()
            with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as c:
                catalogue.install_search_overlay(c)
                catalogue.install_search_overlay(c)
                self.assertEqual(c.execute('SELECT _mat,_tol,_volt_num,_mount_style FROM components_search_capacitor WHERE 品牌=? AND 型号=?',(catalogue.BRAND,'0805A106K250CT')).fetchone(),('X7S','10',25,'贴片'))
                self.assertEqual(c.execute('SELECT COUNT(*) FROM components_search_core').fetchone()[0],len(catalogue.document()['records']))
                self.assertEqual(c.execute('SELECT _mat FROM components_search_capacitor WHERE 品牌=?',('Other',)).fetchone()[0],'Other')
                with self.assertRaises(sqlite3.OperationalError):
                    c.execute('DELETE FROM walsin_public_evidence.components_search_core')
            c.close()
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)

    def test_resistor_only_index_does_not_install_or_repeat_capacitor_overlay(self):
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE components_search_core (品牌,型号,_model_clean,_component_type)')
            catalogue.install_search_overlay(conn)
            catalogue.install_search_overlay(conn)
            self.assertEqual(conn.execute('SELECT count(*) FROM components_search_core').fetchone()[0],0)
            self.assertEqual(conn.execute('SELECT count(*) FROM temp.sqlite_master').fetchone()[0],0)

    def test_legacy_non_uri_connection_uses_memory_compatibility_without_file_writes(self):
        path=catalogue.public_sidecar()[1]
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE components_search_core (品牌,型号,_model_clean,_component_type)')
            conn.execute('CREATE TABLE components_search_capacitor (品牌,型号,_component_type,_size,_mat,_pf,_tol,_volt_num)')
            catalogue.install_search_overlay(conn)
            catalogue.install_search_overlay(conn)
            self.assertEqual(conn.execute('SELECT _mat FROM components_search_capacitor WHERE 型号=?',('0805A106K250',)).fetchone()[0],'X7S')
        conn.close()
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)


if __name__=='__main__':
    unittest.main()
