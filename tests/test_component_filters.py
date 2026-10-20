import sqlite3
import unittest
from component_filters import (CORE, MISSING, PREFIX, available_profile, category_counts, has_unique_model_rows, choice_key,
    option_label, parse_range, profile, reset_filters, snapshot, where_clause, family_of_kind,
    change_family, scalar_current, load_parameter_rows, install_parameter_rows)


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

    def test_manufacturer_keyword_modes_keep_literal_wildcards_and_linked_facets(self):
        self.assertEqual(snapshot(self.conn,'厚膜电阻',keyword='1')['total'],2)
        self.assertEqual(snapshot(self.conn,'厚膜电阻',keyword='R1',keyword_mode='prefix')['total'],1)
        self.assertEqual(snapshot(self.conn,'厚膜电阻',keyword='R',keyword_mode='exact')['total'],0)
        exact=snapshot(self.conn,'厚膜电阻',keyword='r1',keyword_mode='exact',include_rows=True)
        self.assertEqual([r['型号'] for r in exact['rows']],['R1'])
        self.assertEqual(dict(exact['facets']['_size']),{'0402':1})
        self.assertEqual(snapshot(self.conn,'厚膜电阻',keyword='R_100%',keyword_mode='exact')['total'],1)
        self.assertEqual(snapshot(self.conn,'厚膜电阻',keyword='R_',keyword_mode='prefix')['total'],1)
        for mode in ('invalid',{},None):
            with self.assertRaises(ValueError):snapshot(self.conn,'厚膜电阻',keyword='R',keyword_mode=mode)
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
        self.assertIsNone(state[PREFIX+'category'])
        self.assertIsNone(state[PREFIX+'family'])
        self.assertEqual(state['search_query_input'], 'KEEP')

    def test_clear_retains_live_selector_bindings_and_explicitly_resets_values(self):
        class LiveState(dict):
            def __delitem__(self, key):
                if key in {PREFIX+'category', PREFIX+'family'}:
                    raise AssertionError('Deleting a live selector loses its widget binding')
                super().__delitem__(key)
        state=LiveState({PREFIX+'family':'电感／磁珠',PREFIX+'category':'共模电感',PREFIX+'page':2})
        reset_filters(state)
        self.assertEqual(state,{PREFIX+'family':None,PREFIX+'category':None})
        state[PREFIX+'family']='电感／磁珠'
        change_family(state)
        self.assertEqual(state,{PREFIX+'family':'电感／磁珠',PREFIX+'category':None})
        state[PREFIX+'category']='功率电感'
        reset_filters(state,True)
        self.assertEqual(state,{PREFIX+'family':'电感／磁珠',PREFIX+'category':'功率电感'})

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

    def test_all_existing_kinds_have_specific_parameter_profiles_and_family(self):
        kinds = ['MLCC','MOSFET','TVS二极管','三极管','二极管','共模电感','功率电感','厚膜电阻','合金电阻','实时时钟模块','射频电感','引线型压敏电阻','引线型陶瓷电容','振荡器','晶振','热敏电阻','碳膜电阻','磁珠','绕线电阻','薄膜电容','薄膜电阻','贴片压敏电阻','贴片电阻','金属氧化膜电阻','铝电解电容']
        for kind in kinds:
            with self.subTest(kind=kind):
                self.assertNotEqual(family_of_kind(kind), '其他')
                self.assertGreater(len(profile(kind)[1]), 2)
        self.assertEqual(family_of_kind('新增器件'), '其他')
        self.assertNotIn('_tol', [f.key for f in profile('晶振')[1]])
        self.assertIn('频差（ppm）', [f.key for f in profile('晶振')[1]])
        self.assertIn('B值条件', [f.key for f in profile('热敏电阻')[1]])

    def test_current_units_reject_conditions_ranges_signs_and_mega_ambiguity(self):
        self.assertEqual(scalar_current('200mA'), 0.2)
        self.assertEqual(scalar_current('5.7 A'), 5.7)
        self.assertEqual(scalar_current('3µA'), 3e-6)
        for value in ('1~3A','5A@25℃','-5A','1MA','nan','',None,'3V'):
            self.assertIsNone(scalar_current(value))

    def test_semiconductor_details_join_only_existing_models_and_preserve_unknowns(self):
        self.conn.executemany(f'INSERT INTO {CORE} VALUES (?,?,?)', [('A','Q2','MOSFET'),('A','Q3','MOSFET')])
        before = list(self.conn.execute(f'SELECT * FROM {CORE}'))
        rows = [dict(品牌='A',型号='Q1',_component_type='MOSFET',封装代码='SOT-23',极性='N沟道',_volt_num=30,_current_amps=5.7,DCR='26.5mΩ@10V;48mΩ@2.5V'),
                dict(品牌='A',型号='Q2',_component_type='MOSFET',封装代码='SOT-23',极性='P沟道',_volt_num=30,_current_amps=4),
                dict(品牌='A',型号='DELETED',_component_type='MOSFET',封装代码='SOT-23',极性='N沟道',_volt_num=30)]
        install_parameter_rows(self.conn, 'MOSFET', rows)
        result = snapshot(self.conn,'MOSFET',{'封装代码':['SOT-23'],'极性':['N沟道']},{'_volt_num':(30,30),'_current_amps':(5,None)},include_rows=True)
        self.assertEqual([r['型号'] for r in result['rows']], ['Q1'])
        self.assertEqual(result['rows'][0]['DCR'], '26.5mΩ@10V;48mΩ@2.5V')
        self.assertEqual(snapshot(self.conn,'MOSFET')['total'], 3)
        self.assertEqual(snapshot(self.conn,'MOSFET',{'封装代码':[MISSING]})['total'], 1)
        self.assertEqual(snapshot(self.conn,'MOSFET',ranges={'_current_amps':(0,0)})['total'], 0)
        self.assertEqual(before,list(self.conn.execute(f'SELECT * FROM {CORE}')))
        self.assertEqual(snapshot(self.conn,'新增器件')['total'],1)
        self.assertEqual([f.key for f in snapshot(self.conn,'新增器件')['fields']], ['品牌'])

    def test_inductor_current_and_shielding_use_details_without_changing_indexed_value(self):
        install_parameter_rows(self.conn,'功率电感',[dict(品牌='A',型号='L1',_component_type='功率电感',屏蔽类型='屏蔽',_current_amps=2,_saturation_amps=3,_value_num=999)])
        result = snapshot(self.conn,'功率电感',{'屏蔽类型':['屏蔽']},{'inductance_uh':(1,1),'_current_amps':(2,2),'_saturation_amps':(3,3)},include_rows=True)
        self.assertEqual([r['型号'] for r in result['rows']],['L1'])
        self.assertEqual(result['rows'][0]['inductance_uh'],1)

    def test_projected_parquet_details_are_type_scoped_and_do_not_read_costs(self):
        import tempfile
        from pathlib import Path
        import pyarrow as pa
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'prepared.parquet'
            pq.write_table(pa.Table.from_pylist([
                dict(品牌='A',型号='Q1',_component_type='MOSFET',额定电流='200mA',DCR='7Ω@10V',成本=999),
                dict(品牌='A',型号='Q1',_component_type='MOSFET',额定电流='1A',DCR='WRONG COMPOSITE',成本=123),
                dict(品牌='B',型号='D1',_component_type='二极管',额定电流='2A',DCR='',成本=456)]),path)
            rows = load_parameter_rows(path,'MOSFET')
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['_current_amps'],0.2)
            self.assertEqual(rows[0]['DCR'],'7Ω@10V')
            self.assertNotIn('成本',rows[0])
            self.assertEqual(load_parameter_rows(path,'新增器件'),[])
            self.assertEqual(load_parameter_rows(path/'MISSING','MOSFET'),[])

    def test_family_change_clears_incompatible_parameters_but_keeps_login_and_text(self):
        state = {PREFIX+'family':'MOS管', PREFIX+'category':'MLCC', PREFIX+'_mat':['X7R'], PREFIX+'picked':('A','C1'), 'search_query_input':'KEEP', '_member_auth_token':'KEEP'}
        change_family(state)
        self.assertEqual(state,{PREFIX+'family':'MOS管',PREFIX+'category':None,'search_query_input':'KEEP','_member_auth_token':'KEEP'})

    def test_detail_overlay_works_on_readonly_database_and_never_writes_main(self):
        import tempfile
        import hashlib
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'search.sqlite'
            disk=sqlite3.connect(path)
            self.conn.commit()
            self.conn.backup(disk)
            disk.close()
            before=hashlib.sha256(path.read_bytes()).hexdigest()
            readonly=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
            install_parameter_rows(readonly,'MOSFET',[dict(品牌='A',型号='Q1',_component_type='MOSFET',封装代码='SOT-23',极性='N沟道',_current_amps=1)])
            self.assertEqual(snapshot(readonly,'MOSFET',{'封装代码':['SOT-23']})['total'],1)
            readonly.close()
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)
            reopened=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
            self.assertFalse(reopened.execute("SELECT name FROM sqlite_master WHERE name LIKE 'catalog_filter_%'").fetchall())
            reopened.close()

    def test_cold_detail_asset_is_lazy_and_extracts_only_existing_prepared_member(self):
        import ast
        import os
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        source=Path(__file__).resolve().parents[1]/'component_matcher.py'
        tree=ast.parse(source.read_text(encoding='utf-8'))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cached_catalog_parameters')
        function.decorator_list=[]
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'prepared.parquet'
            extracted=[]
            namespace=dict(os=os,PREPARED_CACHE_PATH=str(target),ensure_streamlit_cloud_data_bundle=lambda **kw: extracted.append(kw['required_paths']),
                _catalog_filters=SimpleNamespace(SEMICONDUCTORS={'MOSFET'},INDUCTORS={'功率电感'},load_parameter_rows=lambda path,kind: [kind]))
            exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),namespace)
            load=namespace['cached_catalog_parameters']
            self.assertEqual(load('cold','MLCC'),['MLCC'])
            self.assertEqual(extracted,[])
            self.assertEqual(load('cold','MOSFET'),['MOSFET'])
            self.assertEqual(extracted,[[str(target)]])
            target.write_bytes(b'fixture')
            load('warm','MOSFET')
            self.assertEqual(len(extracted),1)


class CatalogFilterUITests(unittest.TestCase):
    SOURCE = '''
import streamlit as st
from component_filters import render, snapshot, category_counts
from tests.test_component_filters import CatalogFilterTests
fixture=CatalogFilterTests()
fixture.setUp()
def match(model):
    st.session_state['matched_from_catalog']=model
def table(payload,key):
    st.json(payload)
    return st.session_state.pop('fixture_action',None)
def panel(payload,key):
    st.session_state['fixture_panel']=payload
    return st.session_state.pop('fixture_panel_action',None)
try:
    render(st,category_counts(fixture.conn),lambda *args, **kwargs: snapshot(fixture.conn,*args,**kwargs),lambda: st.write('LOGIN-REQUIRED'),True,match,table,panel)
finally:
    fixture.tearDown()
'''

    def app(self, anonymous=False, source=None):
        import platform
        platform._wmi=None
        from streamlit.testing.v1 import AppTest
        source=source or self.SOURCE
        if anonymous:
            source=source.replace('True,match,table,panel)', 'False,match,table,panel)')
        return AppTest.from_string(source,default_timeout=30).run()

    def action(self, at, action, **values):
        payload=at.session_state['fixture_panel']
        import uuid
        at.session_state['fixture_panel_action']=dict(view=payload['view'],event=uuid.uuid4().hex,action=action,**values)
        at.run()
        self.assertFalse(at.exception)
        return at.session_state['fixture_panel']

    def test_render_range_clear_and_explicit_handoff(self):
        import json
        at=self.app()
        self.assertIsNone(at.session_state['fixture_panel']['kind'])
        self.action(at,'kind',kind='厚膜电阻')
        self.action(at,'choice',field='_size',value='0402',checked=True)
        self.action(at,'range',field='_res_ohm',low='5.6',high='5.6',unit='kΩ')
        payload=json.loads(at.json[0].value)
        self.assertEqual(payload['total'],1)
        at.session_state['fixture_action']=dict(action='match',view=payload['view'],event='test-match',id=payload['rows'][0]['id'])
        at.run()
        self.assertEqual(at.session_state['matched_from_catalog'],'R3')
        before=at.session_state['fixture_panel']['view']
        self.action(at,'range',field='_res_ohm',low='5.6',high='1',unit='kΩ')
        self.assertEqual(at.session_state['fixture_panel']['view'],before)
        self.action(at,'clear_all')
        self.assertEqual(at.session_state['fixture_panel']['kind'],'厚膜电阻')
        self.assertEqual(at.session_state['fixture_panel']['total'],6)

    def test_category_switch_resets_old_parameters_and_anonymous_rows_are_hidden(self):
        at=self.app(anonymous=True)
        self.action(at,'kind',kind='厚膜电阻')
        self.action(at,'choice',field='_size',value='0402',checked=True)
        panel=self.action(at,'kind',kind='MLCC')
        self.assertFalse(any(o['checked'] for g in panel['groups'] if not g['units'] for o in g['options']))
        self.assertEqual(len(at.json),0)
        self.assertNotIn('rows',panel)
        next(b for b in at.button if b.label=='登录查看筛选结果').click().run()
        self.assertTrue(any('LOGIN-REQUIRED' in m.value for m in at.markdown))

    def test_all_families_remain_available_without_auto_kind_or_model(self):
        import json
        at=self.app()
        panel=at.session_state['fixture_panel']
        self.assertIsNone(panel['kind'])
        self.assertIn('电阻',{c['family'] for c in panel['categories']})
        self.assertIn('MOS管',{c['family'] for c in panel['categories']})
        self.action(at,'kind',kind='MLCC')
        self.action(at,'choice',field='_mat',value='X7R',checked=True)
        self.action(at,'kind',kind='MOSFET')
        self.assertEqual(json.loads(at.json[0].value)['total'],1)
        self.assertNotIn('matched_from_catalog',at.session_state)
        self.assertNotIn(PREFIX+'_mat',at.session_state)

    def test_repeated_clear_and_same_family_reselection_keeps_actual_kind(self):
        import json
        source=self.SOURCE.replace('fixture.setUp()', '''fixture.setUp()
fixture.conn.execute("INSERT INTO components_search_core VALUES ('A','CM1','共模电感')")
fixture.conn.execute("INSERT INTO components_search_value VALUES ('A','CM1','共模电感','0603','UH',1,'10')")''')
        at=self.app(source=source)
        for kind in ('共模电感','功率电感','共模电感','功率电感'):
            self.action(at,'kind',kind=kind)
            self.assertEqual(json.loads(at.json[0].value)['kind'],kind)
            panel=self.action(at,'clear_all')
            self.assertEqual(panel['kind'],kind)
            self.assertFalse(any(o['checked'] for g in panel['groups'] if not g['units'] for o in g['options']))

    def test_old_invalid_numeric_state_remains_editable_and_never_shows_stale_rows(self):
        at=self.app()
        self.action(at,'kind',kind='厚膜电阻')
        at.session_state[PREFIX+'_res_ohm_low']='5.6'
        at.session_state[PREFIX+'_res_ohm_high']='1'
        at.run()
        self.assertFalse(at.exception)
        self.assertTrue(any('请修正数值范围' in w.value for w in at.warning))
        self.assertEqual(len(at.json),0)
        self.assertTrue(at.session_state['fixture_panel']['groups'])
        panel=self.action(at,'clear_group',field='_res_ohm')
        self.assertEqual(panel['total'],6)
        self.assertEqual(len(at.json),1)

    def test_specifications_only_clears_removed_inline_keyword_but_keeps_main_search(self):
        import json
        at=self.app()
        self.action(at,'kind',kind='MLCC')
        at.session_state[PREFIX+'keyword']='NONEXISTENT-OLD-INLINE-NAME'
        at.session_state[PREFIX+'keyword_mode']='exact'
        at.session_state['search_query_input']='KEEP-MAIN-TEXT-SEARCH'
        at.session_state['_member_auth_token']='KEEP-MEMBER'
        at.run()
        self.assertFalse(at.exception)
        self.assertEqual(json.loads(at.json[0].value)['total'],3)
        self.assertNotIn(PREFIX+'keyword',at.session_state)
        self.assertNotIn(PREFIX+'keyword_mode',at.session_state)
        self.assertEqual(at.session_state['search_query_input'],'KEEP-MAIN-TEXT-SEARCH')
        self.assertEqual(at.session_state['_member_auth_token'],'KEEP-MEMBER')
