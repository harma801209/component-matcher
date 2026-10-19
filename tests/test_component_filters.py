import sqlite3
import unittest
from component_filters import (CORE, MISSING, PREFIX, available_profile, category_counts, has_unique_model_rows, choice_key,
    option_label, parse_range, profile, reset_filters, snapshot, where_clause)


class CatalogFilterTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.executescript('''
            CREATE TABLE components_search_core (品牌 TEXT, 型号 TEXT, _component_type TEXT);
            CREATE TABLE components_search_resistor (品牌 TEXT, 型号 TEXT, _component_type TEXT, _size TEXT, _res_ohm REAL, _tol TEXT, _power_watt REAL);
            CREATE TABLE components_search_capacitor (品牌 TEXT, 型号 TEXT, _component_type TEXT, _size TEXT, _mat TEXT, _pf REAL, _tol TEXT, _volt_num REAL);
            CREATE TABLE components_search_value (品牌 TEXT, 型号 TEXT, _component_type TEXT, _size TEXT, _unit_upper TEXT, _value_num REAL, _tol TEXT);
        ''')
        self.conn.executemany('INSERT INTO components_search_resistor VALUES (?,?,?,?,?,?,?)', [
            ('A','R1','厚膜电阻','0402',1000,'1',0.0625),
            ('A','R1','厚膜电阻','0402',1000,'1',0.0625),
            ('A','R2','厚膜电阻','0603',5600,'0.1',0.1),
            ('B','R3','厚膜电阻','0402',5600,'0.1',0.0625),
            ('B','R4','厚膜电阻',None,None,None,None),
            ('B','R5','厚膜电阻','0402',0,'5',0.25),
            ('A','R_100%','厚膜电阻','0402',100,'1',0.0625),
        ])
        self.conn.executemany('INSERT INTO components_search_capacitor VALUES (?,?,?,?,?,?,?,?)', [
            ('A','C1','MLCC','0402','X7R',100000,'10',16),
            ('B','C2','MLCC','0603','X5R',1000000,'20',6.3),
            ('B','C3','MLCC','0603',None,None,None,None),
        ])
        self.conn.executemany('INSERT INTO components_search_value VALUES (?,?,?,?,?,?,?)', [
            ('A','X1','晶振','3225','MHZ',16,'20'),
            ('A','X2','晶振','3225','KHZ',16000,'20'),
            ('A','L1','功率电感','0603','NH',1000,'10'),
            ('A','L2','功率电感','0603','UH',1,'10'),
            ('A','L3','功率电感','0603','KΩ',1,'10'),
        ])
        for table in ('components_search_resistor','components_search_capacitor','components_search_value'):
            self.conn.execute(f'INSERT INTO {CORE} SELECT 品牌,型号,_component_type FROM {table}')
        self.conn.executemany(f'INSERT INTO {CORE} VALUES (?,?,?)', [('A','Q1','MOSFET'),('B','NEW1','新增器件')])

    def tearDown(self):
        self.conn.close()

    def test_all_categories_count_distinct_models_not_duplicate_rows(self):
        counts = dict(category_counts(self.conn))
        self.assertEqual(counts['厚膜电阻'], 6)
        self.assertEqual(counts['MLCC'], 3)
        self.assertEqual(counts['MOSFET'], 1)
        self.assertEqual(counts['新增器件'], 1)

    def test_or_within_and_across_facets_and_disjunctive_counts(self):
        result = snapshot(self.conn, '厚膜电阻', {'品牌':['A'], '_size':['0402','0603'], '_tol':['0.1']}, include_rows=True)
        self.assertEqual([r['型号'] for r in result['rows']], ['R2'])
        self.assertEqual(dict(result['facets']['品牌']), {'A':1, 'B':1})
        self.assertEqual(dict(result['facets']['_tol']), {'0.1':1, '1':2})

    def test_missing_numeric_is_not_zero_and_explicit_missing_option(self):
        zero = snapshot(self.conn, '厚膜电阻', ranges={'_res_ohm':(0,0)}, include_rows=True)
        self.assertEqual([r['型号'] for r in zero['rows']], ['R5'])
        missing = snapshot(self.conn, '厚膜电阻', {'_size':[MISSING]}, include_rows=True)
        self.assertEqual([r['型号'] for r in missing['rows']], ['R4'])
        self.assertEqual(snapshot(self.conn, '厚膜电阻')['total'], 6)

    def test_capacitance_voltage_and_package_filters(self):
        result = snapshot(self.conn, 'MLCC', {'_size':['0402'],'_mat':['X7R']}, {'_pf':parse_range('0.1','0.1',1e6), '_volt_num':(10,None)}, include_rows=True)
        self.assertEqual([r['型号'] for r in result['rows']], ['C1'])
        self.assertNotIn('生产状态', [f.key for f in result['fields']])

    def test_frequency_and_inductance_normalize_units_without_impedance_mixup(self):
        result = snapshot(self.conn, '晶振', ranges={'frequency_hz':parse_range('16','16',1e6)}, include_rows=True)
        self.assertEqual({r['型号'] for r in result['rows']}, {'X1','X2'})
        result = snapshot(self.conn, '功率电感', ranges={'inductance_uh':(1,1)}, include_rows=True)
        self.assertEqual({r['型号'] for r in result['rows']}, {'L1','L2'})

    def test_numeric_range_validation_and_no_default_bound(self):
        self.assertEqual(parse_range('',''), (None,None))
        self.assertEqual(parse_range('5.6','5.6',1e3), (5600,5600))
        for low, high in [('nan',''),('inf',''),('-1',''),('6','5'),('wrong',''),('1e999','')]:
            with self.subTest(low=low,high=high), self.assertRaises(ValueError):
                parse_range(low,high)
        for ranges in ({'_res_ohm':(10,1)}, {'_res_ohm':(float('nan'),None)}, {'not_a_column':(0,1)}):
            with self.assertRaises(ValueError):
                snapshot(self.conn, '厚膜电阻', ranges=ranges)

    def test_values_are_bound_and_model_wildcards_are_literal(self):
        result = snapshot(self.conn, '厚膜电阻', {'品牌':["' OR 1=1 --"]}, include_rows=True)
        self.assertEqual(result['total'], 0)
        self.assertEqual(snapshot(self.conn, '厚膜电阻', keyword='_100%', include_rows=True)['total'], 1)
        with self.assertRaises(ValueError):
            snapshot(self.conn, '厚膜电阻', {'品牌) OR 1=1': ['A']})
        with self.assertRaises(ValueError):
            snapshot(self.conn, '厚膜电阻', keyword='x'*121)

    def test_pagination_is_bounded_stable_and_deduplicated(self):
        first = snapshot(self.conn, '厚膜电阻', page_size=2, include_rows=True)
        second = snapshot(self.conn, '厚膜电阻', page=2, page_size=2, include_rows=True)
        self.assertEqual(first['pages'], 3)
        self.assertFalse({r['型号'] for r in first['rows']} & {r['型号'] for r in second['rows']})
        last = snapshot(self.conn, '厚膜电阻', {'品牌':['A']}, page=99, page_size=2, include_rows=True)
        self.assertEqual(last['page'], 2)
        self.assertEqual(len(last['rows']), 1)

    def test_anonymous_metadata_has_no_model_rows_or_prices(self):
        result = snapshot(self.conn, '厚膜电阻')
        self.assertEqual(result['total'], 6)
        self.assertEqual(result['rows'], [])
        logged = snapshot(self.conn, '厚膜电阻', include_rows=True)
        self.assertTrue(all(not any('成本' in key or '价格' in key for key in row) for row in logged['rows']))

    def test_unknown_category_and_missing_detail_table_fall_back_to_core(self):
        self.assertEqual(snapshot(self.conn, '新增器件', include_rows=True)['rows'][0]['型号'], 'NEW1')
        self.conn.execute('DROP TABLE components_search_resistor')
        result = snapshot(self.conn, '厚膜电阻', include_rows=True)
        self.assertEqual(result['total'], 6)
        self.assertEqual([f.key for f in result['fields']], ['品牌'])

    def test_clear_and_category_change_do_not_clear_login_or_text_query(self):
        state = {PREFIX+'category':'MLCC', PREFIX+'_size':['0402'], PREFIX+'_pf_low':'0.1', PREFIX+'page':4, PREFIX+'picked':1, 'search_query_input':'KEEP','_member_auth_token':'KEEP'}
        reset_filters(state, True)
        self.assertEqual(state, {PREFIX+'category':'MLCC', 'search_query_input':'KEEP','_member_auth_token':'KEEP'})
        reset_filters(state)
        self.assertNotIn(PREFIX+'category', state)
        self.assertEqual(state['search_query_input'], 'KEEP')

    def test_power_and_tolerance_labels_are_readable(self):
        _, fields = profile('厚膜电阻')
        fields = {f.key:f for f in fields}
        self.assertEqual(option_label(fields['_power_watt'],'0.0625'), '1/16 W')
        self.assertEqual(option_label(fields['_tol'],'0.1'), '±0.1%')
        self.assertEqual(option_label(fields['_tol'],MISSING), '未提供')
        self.assertEqual(option_label(fields['_tol'],'99999999998'), '误差标注待核对')

    def test_fast_counts_require_verified_uniqueness_and_match_deduped_counts(self):
        self.assertFalse(has_unique_model_rows(self.conn, '厚膜电阻'))
        self.assertTrue(has_unique_model_rows(self.conn, 'MLCC'))
        slow = snapshot(self.conn, 'MLCC', include_rows=True)
        fast = snapshot(self.conn, 'MLCC', include_rows=True, verified_unique=True)
        self.assertEqual(fast, slow)


class CatalogFilterUITests(unittest.TestCase):
    SOURCE = '''
import streamlit as st
from component_filters import render, snapshot, category_counts
from tests.test_component_filters import CatalogFilterTests
fixture=CatalogFilterTests()
fixture.setUp()
def match(model):
    st.session_state['matched_from_catalog']=model
render(st,category_counts(fixture.conn),lambda *args: snapshot(fixture.conn,*args),lambda: st.write('LOGIN-REQUIRED'),True,match)
fixture.tearDown()
'''

    def test_render_state_changes_invalid_range_clear_and_handoff(self):
        import platform
        platform._wmi = None
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_string(self.SOURCE, default_timeout=30).run()
        self.assertFalse(at.exception)
        at.selectbox(key=PREFIX+'category').select('厚膜电阻').run()
        self.assertFalse(at.exception)
        at.checkbox(key=choice_key('_size','0402')).check().run()
        at.text_input(key=PREFIX+'_res_ohm_low').set_value('5.6').run()
        at.selectbox(key=PREFIX+'_res_ohm_unit').select('kΩ').run()
        at.text_input(key=PREFIX+'_res_ohm_high').set_value('5.6').run()
        self.assertFalse(at.exception)
        self.assertTrue(any('找到 1 个' in item.value for item in at.markdown))
        at.selectbox(key=PREFIX+'picked').select(('B','R3')).run()
        next(b for b in at.button if b.label=='查看价格与替代型号').click().run()
        self.assertEqual(at.session_state['matched_from_catalog'], 'R3')
        at.text_input(key=PREFIX+'_res_ohm_high').set_value('1').run()
        self.assertFalse(at.exception)
        self.assertTrue(any('下限不能大于上限' in w.value for w in at.warning))
        self.assertFalse(any('找到 ' in item.value for item in at.markdown))
        at.button(key=PREFIX+'clear').click().run()
        self.assertIsNone(at.selectbox(key=PREFIX+'category').value)
        self.assertFalse(at.exception)

    def test_category_switch_resets_old_parameters_and_anonymous_rows_are_hidden(self):
        import platform
        platform._wmi = None
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_string(self.SOURCE.replace('True,match)', 'False,match)'), default_timeout=30).run()
        at.selectbox(key=PREFIX+'category').select('厚膜电阻').run()
        at.checkbox(key=choice_key('_size','0402')).check().run()
        at.selectbox(key=PREFIX+'category').select('MLCC').run()
        self.assertFalse(at.checkbox(key=choice_key('_size','0402')).value)
        self.assertFalse(at.exception)
        self.assertFalse(any(b.label=='查看价格与替代型号' for b in at.button))
        next(b for b in at.button if b.label=='登录查看筛选结果').click().run()
        self.assertTrue(any('LOGIN-REQUIRED' in m.value for m in at.markdown))
