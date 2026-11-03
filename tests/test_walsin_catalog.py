import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
import pandas as pd
import walsin_catalog as catalogue


class WalsinCatalogueTests(unittest.TestCase):
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
        self.assertFalse({'价格','成本','生产状态','member_id'} & set(row.index))

    def test_historical_corrections_are_exact_model_old_value_and_brand_guarded(self):
        self.assertEqual(len(catalogue.corrections()),187)
        self.assertEqual(sum(len(r['fields']) for r in catalogue.corrections().values()),190)
        for model, correction in catalogue.corrections().items():
            original={'品牌':catalogue.BRAND,'型号':model,'成本':123.45,'价格':678.9}
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
