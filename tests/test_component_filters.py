import sqlite3
import unittest
from component_filters import (CORE, MISSING, PREFIX, available_profile, category_counts, has_unique_model_rows, choice_key,
    option_label, parse_range, profile, reset_filters, snapshot, where_clause, family_of_kind,
    change_family, scalar_current, load_parameter_rows, install_parameter_rows)


class CatalogFilterTests(unittest.TestCase):
    def test_mlcc_completion_uses_source_fields_without_overriding_known_values(self):
        from catalog_mlcc_completion import complete
        record=dict(品牌='Sunway(信维通信)',型号='MC0100B101K100N2RH',_component_type='MLCC',
                    封装代码='0100',容值误差='±10%')
        values=complete(record)
        self.assertEqual(values['_size'],'01005')
        self.assertEqual(values['_tol'],'10')
        self.assertEqual(values['_mount_style'],'贴片')
        self.assertFalse(values['_mat'])
        record.update(_size='0402',_mat='X7R',_tol='5',_mount_style='插件')
        self.assertEqual(complete(record),dict(_size='0402',_mat='X7R',_tol='5',_mount_style='插件'))
        record['_component_type']='引线型陶瓷电容'
        self.assertEqual(complete(record)['_mount_style'],'插件')

    def test_mlcc_completion_scopes_codes_and_keeps_unknowns_unknown(self):
        from catalog_mlcc_completion import complete
        cctc=dict(品牌='三环CCTC',型号='TCC1206M3L103J501HT',_component_type='MLCC',_size='1206')
        self.assertEqual(complete(cctc)['_mat'],'M3L')
        cctc['品牌']='Unverified manufacturer'
        self.assertFalse(complete(cctc)['_mat'])
        self.assertFalse(complete(cctc)['_mount_style'])
        murata=dict(品牌='村田Murata',型号='DE2B3KY681KN3AM02',_component_type='MLCC')
        self.assertFalse(complete(murata)['_size'])
        self.assertFalse(complete(murata)['_mount_style'])
        self.assertFalse(complete(dict(品牌='Other',型号='MC0100B101K100N2RH',_component_type='MLCC',封装代码='0100'))['_size'])
        smd=dict(品牌='村田Murata',型号='GRM155R71C104KA88D',_component_type='MLCC',_size='0402')
        values=complete(smd)
        self.assertEqual(values['_mount_style'],'贴片')
        self.assertNotIn('生产状态',values)
        self.assertNotIn('_safety_class',values)

    def test_mlcc_resolver_fills_only_missing_fields_and_preserves_absolute_units(self):
        from catalog_mlcc_completion import complete
        record=dict(品牌='国巨YAGEO',型号='CS0402CRNPO9BNR10',_component_type='MLCC',_size='0402',_mat='COG',_pf=0.1)
        resolver=lambda model,brand: {'尺寸（inch）':'0603','材质（介质）':'X7R','容值误差':'±0.25pF','成本':999}
        values=complete(record,resolver)
        self.assertEqual(values['_size'],'0402')
        self.assertEqual(values['_mat'],'COG')
        self.assertEqual(values['_tol'],'0.25PF')
        self.assertNotIn('成本',values)
        field=next(f for f in profile('MLCC')[1] if f.key=='_tol')
        self.assertEqual(option_label(field,values['_tol']),'±0.25 pF')

    def test_mlcc_overlay_counts_and_rows_share_filled_values_without_new_models(self):
        self.conn.execute('UPDATE components_search_capacitor SET _size=NULL,_mat=NULL,_tol=NULL WHERE 型号=?',('C3',))
        before=list(self.conn.execute('SELECT * FROM components_search_capacitor'))
        details=[dict(品牌='B',型号='C3',_component_type='MLCC',_size='01005',_mat='M3L',_tol='0.1PF',_mount_style='贴片'),
                 dict(品牌='B',型号='DELETED',_component_type='MLCC',_size='01005',_mat='X7R'),
                 dict(品牌='A',型号='C1',_component_type='MLCC',_size='1206',_mat='X5R',_tol='20')]
        install_parameter_rows(self.conn,'MLCC',details)
        result=snapshot(self.conn,'MLCC',{'_size':['01005'],'_mat':['M3L'],'_tol':['0.1PF'],'_mount_style':['贴片']},include_rows=True)
        self.assertEqual(result['total'],1)
        self.assertEqual(result['rows'][0]['型号'],'C3')
        self.assertEqual(dict(result['facets']['_size']),{'01005':1})
        self.assertEqual(snapshot(self.conn,'MLCC')['total'],3)
        self.assertEqual(snapshot(self.conn,'MLCC',{'_size':['0402']},include_rows=True)['rows'][0]['_mat'],'X7R')
        self.assertEqual(before,list(self.conn.execute('SELECT * FROM components_search_capacitor')))
        self.assertEqual(snapshot(self.conn,'厚膜电阻')['total'],6)
        install_parameter_rows(self.conn,'MLCC',details)  # idempotent in one connection

    def test_mlcc_completion_projects_raw_parquet_and_takes_one_actual_record(self):
        import tempfile
        from pathlib import Path
        import pyarrow as pa
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'prepared.parquet'
            pq.write_table(pa.Table.from_pylist([
                dict(品牌='Sunway(信维通信)',型号='MC0100B101K100N2RH',_component_type='MLCC',_size='',_mat='X7R',_tol='',_mount_style='',封装代码='0100',容值误差='±10%',成本=999),
                dict(品牌='Sunway(信维通信)',型号='MC0100B101K100N2RH',_component_type='MLCC',_size='0402',_mat='X5R',_tol='5',_mount_style='插件',封装代码='0402',容值误差='±5%',成本=1),
                dict(品牌='A',型号='Q1',_component_type='MOSFET',封装代码='SOT-23')]),path)
            rows=load_parameter_rows(path,'MLCC')
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['_size'],'01005')
            self.assertEqual(rows[0]['_mat'],'X7R')
            self.assertEqual(rows[0]['_tol'],'10')
            self.assertNotIn('成本',rows[0])
            self.assertNotIn('封装代码',rows[0])

    def test_inferred_mounting_does_not_expand_cached_prepared_repairs(self):
        import tempfile
        from pathlib import Path
        import pyarrow as pa
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'prepared.parquet'
            records=[dict(品牌='村田Murata',型号='GRM155R71C104KA'+str(i),_component_type='MLCC',
                          _size='0402',_mat='X7R',_tol='10',_mount_style='',安装方式='') for i in range(2100)]
            pq.write_table(pa.Table.from_pylist(records),path)
            self.assertEqual(load_parameter_rows(path,'MLCC'),[])
        self.conn.executemany('INSERT INTO components_search_capacitor VALUES (?,?,?,?,?,?,?,?)',
            [(r['品牌'],r['型号'],'MLCC','0402','X7R',100000,'10',16) for r in records])
        install_parameter_rows(self.conn,'MLCC',[])
        result=snapshot(self.conn,'MLCC',{'_mount_style':['贴片']})
        self.assertEqual(result['total'],2100)

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
            install_parameter_rows(readonly,'MLCC',[dict(品牌='B',型号='C3',_component_type='MLCC',_mat='M3L')])
            self.assertEqual(snapshot(readonly,'MLCC',{'_mat':['M3L']})['total'],1)
            self.assertEqual(snapshot(readonly,'MLCC')['total'],3)
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
                _catalog_filters=SimpleNamespace(SEMICONDUCTORS={'MOSFET'},INDUCTORS={'功率电感'},passive_completion=SimpleNamespace(KINDS={'MLCC','厚膜电阻'}),load_parameter_rows=lambda path,kind,**kwargs: [kind]),resolve_catalog_mlcc_rule=lambda model,brand:{})
            exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),namespace)
            load=namespace['cached_catalog_parameters']
            self.assertEqual(load('cold','MLCC'),['MLCC'])
            self.assertEqual(extracted,[[str(target)]])
            self.assertEqual(load('cold','MOSFET'),['MOSFET'])
            self.assertEqual(extracted,[[str(target)],[str(target)]])
            target.write_bytes(b'fixture')
            load('warm','MOSFET')
            self.assertEqual(len(extracted),2)

    def test_catalogue_brand_decoder_rejects_wrong_brand_type_and_unverified_rules(self):
        import ast
        from pathlib import Path
        source=Path(__file__).resolve().parents[1]/'component_matcher.py'
        tree=ast.parse(source.read_text(encoding='utf-8'))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='resolve_catalog_mlcc_rule')
        parsed={}
        namespace=dict(parse_model_rule=lambda *args,**kwargs:parsed,
            brand_matches_loose=lambda a,b: bool(a) and a==b,normalize_component_type=lambda v:v)
        exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),namespace)
        resolve=namespace['resolve_catalog_mlcc_rule']
        for bad in ({'品牌':'A'},{'品牌':'B','_model_rule_authority':'rule'},
                    {'品牌':'A','_model_rule_authority':'rule','器件类型':'钽电容'}):
            parsed.clear();parsed.update(bad)
            self.assertEqual(resolve('C1','A'),{})
        parsed.clear();parsed.update(品牌='A',_model_rule_authority='rule',器件类型='MLCC',容值误差='0.1PF')
        self.assertEqual(resolve('C1','A')['容值误差'],'0.1PF')


class PassiveParameterCompletionTests(unittest.TestCase):
    def test_official_export_import_rejects_changed_or_mismatched_receipts(self):
        import hashlib,json,tempfile
        from pathlib import Path
        from tools.import_samsung_catalogue_evidence import verified_export
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'samsung-official-cr-RC0402.json'
            path.write_bytes(b'{"searchListJson":[]}')
            entry=dict(url='https://product.samsungsem.com/cr/bSearch.do',request={'partNumber':'RC0402'},checked_at='2026-10-20T12:00:00+00:00',source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(verified_export(path,{path.name:entry},'cr',{'partNumber':'RC0402'})[1],entry['checked_at'])
            with self.assertRaises(ValueError):verified_export(path,{},'cr',{'partNumber':'RC0402'})
            with self.assertRaises(ValueError):verified_export(path,{path.name:entry},'cr',{'partNumber':'RC0603'})
            path.write_bytes(b'{"searchListJson":[{}]}')
            with self.assertRaises(ValueError):verified_export(path,{path.name:entry},'cr',{'partNumber':'RC0402'})

    def test_versioned_lifecycle_artifact_contains_only_valid_reviewed_records(self):
        import json
        import manufacturer_lifecycle as lifecycle
        raw=json.loads(lifecycle.EVIDENCE.read_text(encoding='utf-8'))['records']
        self.assertEqual(len(lifecycle.records()),len(raw))
        self.assertEqual(len({(r['manufacturer'],r['model']) for r in raw}),len(raw))
        self.assertTrue(all(r['raw_status'] in lifecycle.STATUSES for r in raw))

    def test_unreviewed_brand_never_promotes_legacy_active_even_without_evidence(self):
        from unittest.mock import patch
        import manufacturer_lifecycle as lifecycle
        for evidence in ([],[dict(manufacturer='samsung',model='CL1C',status='量产',source='https://product.samsungsem.com/cn/mlcc/CL1.do',checked_at='2026-10-20T12:00:00+00:00')]):
            conn=sqlite3.connect(':memory:')
            conn.executescript("CREATE TABLE components_search_core(品牌 TEXT,型号 TEXT,_component_type TEXT,生产状态 TEXT);INSERT INTO components_search_core VALUES ('Unreviewed','XTAL1','晶振','Active');")
            with patch.object(lifecycle,'records',return_value=evidence):table=lifecycle.install(conn,CORE,'晶振')
            self.assertEqual(conn.execute('SELECT 型号,生产状态 FROM "'+table+'"').fetchall(),[('XTAL1',None)])
            self.assertEqual(conn.execute('SELECT 生产状态 FROM components_search_core').fetchall(),[('Active',)])
            self.assertEqual(snapshot(conn,'晶振')['total'],1)
            conn.close()

    def test_official_collector_keeps_tls_defaults_and_rejects_redirect_or_oversize(self):
        from tools.collect_manufacturer_lifecycle import read_product
        from urllib.error import HTTPError
        class Response:
            def __init__(self,status,chunks):self.status_code=status;self.chunks=chunks
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def iter_content(self,chunk_size):return iter(self.chunks)
        class Session:
            def __init__(self,response):self.response=response
            def get(self,url,**kwargs):self.arguments=kwargs;return self.response
        session=Session(Response(200,[b'<h2>',b'product</h2>']))
        self.assertEqual(read_product(session,'https://product.samsungsem.com/cn/mlcc/CL1.do','Audit/1.0'),b'<h2>product</h2>')
        self.assertFalse(session.arguments['allow_redirects'])
        self.assertNotIn('verify',session.arguments)
        with self.assertRaises(HTTPError) as raised:read_product(Session(Response(302,[])),'https://product.samsungsem.com/a','Audit/1.0')
        raised.exception.close()
        with self.assertRaises(ValueError):read_product(Session(Response(200,[b'x'*2_000_001])),'https://product.samsungsem.com/a','Audit/1.0')

    def test_exact_samsung_catalogue_resistor_parameters_not_family_or_defaults(self):
        import json
        from manufacturer_lifecycle import samsung_catalogue_records
        product=dict(partNumber='RC0402F100CS',status='NRND',rValue='10Ω',ratedPower='0.031 W (1/32 W)',sizeCode='01005/0402',tolerance='±1.0%',ratedVdc=0)
        source=json.dumps({'searchListJson':[product]})
        rows=samsung_catalogue_records(source,'cr',{'partNumber':'RC0402'},'2026-10-20T12:00:00+00:00')
        self.assertEqual([r['model'] for r in rows],['RC0402F100CS'])
        self.assertEqual(rows[0]['status'],'NRND（不推荐新设计）')
        self.assertEqual(rows[0]['parameters'],dict(_res_ohm=10,_power_watt=1/32,_size='01005',_tol='1'))
        self.assertNotIn('_volt_num',rows[0]['parameters'])
        with self.assertRaises(ValueError):samsung_catalogue_records(source,'cr',{'partNumber':'RC0603'},rows[0]['checked_at'])
        with self.assertRaises(ValueError):samsung_catalogue_records(source,'mlcc',{'partNumber':'CL10'},rows[0]['checked_at'])
        self.assertEqual(samsung_catalogue_records(source.replace('NRND','Active'),'cr',{'partNumber':'RC0402'},rows[0]['checked_at']),[])
        product.update(rValue='0Ω',ratedPower='derived from 01005',tolerance='0.05ohm Max')
        zero=samsung_catalogue_records(json.dumps({'searchListJson':[product]}),'cr',{'partNumber':'RC0402'},rows[0]['checked_at'])[0]
        self.assertEqual(zero['parameters']['_res_ohm'],0)
        self.assertNotIn('_tol',zero['parameters'])
        self.assertNotIn('_power_watt',zero['parameters'])

    def test_catalogue_evidence_validation_and_blank_only_same_source_filters(self):
        import json,tempfile
        from pathlib import Path
        from unittest.mock import patch
        import manufacturer_lifecycle as lifecycle
        data={'searchListJson':[dict(partNumber='RC0402F100CS',status='Mass Production',rValue='10Ω',ratedPower='0.031 W (1/32 W)',sizeCode='01005/0402',tolerance='±1%')]}
        evidence=lifecycle.samsung_catalogue_records(json.dumps(data),'cr',{'partNumber':'RC0402'},'2026-10-20T12:00:00+00:00')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'evidence.json'
            path.write_text(json.dumps({'records':evidence}),encoding='utf-8')
            self.assertEqual(len(lifecycle._read(str(path),1)),1)
            bad=dict(evidence[0],source='https://product.samsungsem.com.attacker.test/cn/cr/basic-search.do')
            bad2=dict(evidence[0],parameters={'_power_watt':True})
            bad3=dict(evidence[0],request={'partNumber':'RC0603'})
            path.write_text(json.dumps({'records':[bad,bad2,bad3]}),encoding='utf-8')
            self.assertEqual(lifecycle._read(str(path),2),())
        conn=sqlite3.connect(':memory:')
        conn.executescript('CREATE TABLE components_search_core(品牌 TEXT,型号 TEXT,_component_type TEXT,_res_ohm REAL,_power_watt REAL,_size TEXT,_tol TEXT);')
        conn.executemany('INSERT INTO components_search_core VALUES (?,?,?,?,?,?,?)',[
            ('三星Samsung','RC0402F100CS','厚膜电阻',None,None,'',''),
            ('Samsung','RC0402F100CS','厚膜电阻',0,2,'known','5'),
            ('Other','RC0402F100CS','厚膜电阻',None,None,None,None)])
        original=conn.execute('SELECT * FROM components_search_core').fetchall()
        with patch.object(lifecycle,'records',return_value=evidence):lifecycle.install(conn,CORE,'厚膜电阻')
        columns=[r[1] for r in conn.execute('PRAGMA table_info(catalog_lifecycle_source)')]
        values={r[0]:dict(zip(columns,r)) for r in conn.execute('SELECT * FROM catalog_lifecycle_source')}
        self.assertEqual(values['三星Samsung']['_power_watt'],1/32)
        self.assertEqual(values['Samsung']['_power_watt'],2)
        self.assertEqual(values['Samsung']['_res_ohm'],0)
        self.assertEqual(values['Samsung']['_size'],'known')
        self.assertIsNone(values['Other']['生产状态'])
        self.assertEqual(snapshot(conn,'厚膜电阻',{'生产状态':['量产']})['total'],2)
        self.assertEqual(snapshot(conn,'厚膜电阻',ranges={'_res_ohm':(10,10)})['total'],1)
        self.assertEqual(conn.execute('SELECT * FROM components_search_core').fetchall(),original)
        conn.close()

    def test_power_inductor_catalogue_hash_is_not_arbitrary_packaging(self):
        import json
        from manufacturer_lifecycle import samsung_catalogue_records
        source=json.dumps({'searchListJson':[dict(partNumber='CIGT1412R6TMR33MB',status='Mass Production',inductance=.33,lSize='1.40±0.20mm',wSize='1.20±0.20mm',tSizeMax='0.65mm',tolerance='±20%',sizeCode='0605/1412',itempMax=3.4,isatMax=5)]})
        rows=samsung_catalogue_records(source,'pi',{'status':['Mass Production']},'2026-10-20T12:00:00+00:00')
        self.assertEqual([r['model'] for r in rows],['CIGT1412R6TMR33MB#'])
        self.assertEqual(rows[0]['parameters'],{'_catalog_inductance_uh':.33,'_body_size':'1.40±0.20 × 1.20±0.20 × 0.65 max mm','_size':'0605','_tol':'20'})
        self.assertNotIn('_current_amps',rows[0]['parameters'])
        self.assertNotIn('_saturation_amps',rows[0]['parameters'])

    def test_lifecycle_requires_exact_product_table_and_explicit_packaging_identity(self):
        from manufacturer_lifecycle import samsung_records
        base='CL10B104KB8NNN'
        url='https://product.samsungsem.com/cn/mlcc/'+base+'.do'
        source='<h2 class="subject">'+base+'#</h2><ul class="partlist"><li>'+base+'C</li></ul><table><tr><th>生产状况</th><td>NRND</td></tr></table><div>Mass Production Discontinued</div><h2 class="subject">包装说明</h2>'
        rows=samsung_records(source,url,base,'2026-10-20T12:00:00+00:00')
        self.assertEqual({r['model'] for r in rows},{base+'#',base+'C'})
        self.assertEqual({r['status'] for r in rows},{'NRND（不推荐新设计）'})
        self.assertEqual(samsung_records(source.replace('生产状况','电压'),url,base,'2026-10-20T12:00:00+00:00'),[])
        self.assertEqual(samsung_records(source.replace('<td>NRND</td>','<td>EOL</td>'),url,base,'2026-10-20T12:00:00+00:00'),[])
        self.assertEqual(samsung_records(source.replace(base+'#','OTHER#'),url,base,'2026-10-20T12:00:00+00:00'),[])
        with self.assertRaises(ValueError):samsung_records(source,url.replace('product.samsungsem.com','example.com'),base,'2026-10-20T12:00:00+00:00')

    def test_verified_lifecycle_overlay_preserves_library_and_never_promotes_legacy_active(self):
        from unittest.mock import patch
        import manufacturer_lifecycle as lifecycle
        conn=sqlite3.connect(':memory:')
        conn.executescript('CREATE TABLE components_search_core(品牌 TEXT,型号 TEXT,_component_type TEXT,生产状态 TEXT);')
        conn.executemany('INSERT INTO components_search_core VALUES (?,?,?,?)',[
            ('三星Samsung','CL1C','MLCC','Active'),('三星Samsung','CL2C','MLCC','Active'),('Other','CL1C','MLCC','Active')])
        evidence=[dict(manufacturer='samsung',model='CL1C',status='量产',source='https://product.samsungsem.com/cn/mlcc/CL1.do',checked_at='2026-10-20T12:00:00+00:00'),
                  dict(manufacturer='samsung',model='NOT-IN-LIBRARY',status='已停产',source='https://product.samsungsem.com',checked_at='2026-10-20T12:00:00+00:00')]
        original=conn.execute('SELECT * FROM components_search_core').fetchall()
        with patch.object(lifecycle,'records',return_value=evidence):lifecycle.install(conn,CORE,'MLCC')
        result=snapshot(conn,'MLCC',include_rows=True)
        self.assertEqual(result['total'],3)
        by_pair={(r['品牌'],r['型号']):r for r in result['rows']}
        self.assertEqual(by_pair[('三星Samsung','CL1C')]['生产状态'],'量产')
        self.assertIsNone(by_pair[('三星Samsung','CL2C')]['生产状态'])
        self.assertIsNone(by_pair[('Other','CL1C')]['生产状态'])
        self.assertEqual(by_pair[('三星Samsung','CL1C')]['_lifecycle_checked'],'2026-10-20T12:00:00+00:00')
        self.assertEqual(snapshot(conn,'MLCC',{'生产状态':['量产']})['total'],1)
        self.assertEqual(conn.execute('SELECT * FROM components_search_core').fetchall(),original)
        conn.close()

    def test_fojan_official_dimensions_and_resistance_do_not_guess_other_series_or_power(self):
        from catalog_passive_completion import complete
        def specs(model, **extra):
            return complete(dict(品牌='FOJAN(富捷)',型号=model,_component_type='厚膜电阻',**extra))
        self.assertEqual(specs('FPS2512F2000TS')['_res_ohm'],200)
        self.assertEqual(specs('FPS1210J101TS')['_res_ohm'],100)
        self.assertEqual(specs('FPL2512FR240TS')['_res_ohm'],.24)
        self.assertEqual(specs('FRC0201F0000TS')['_res_ohm'],0)
        self.assertEqual(specs('FRC0201F1000TS')['_body_size'],'0.60±0.03 × 0.30±0.03 × 0.23±0.03 mm')
        self.assertEqual(specs('FPS2512F2000TS')['_body_size'],'6.35±0.10 × 3.10±0.15 × 0.55±0.10 mm')
        self.assertNotIn('_res_ohm',specs('FPS2512F2000TS',_res_ohm=0))
        self.assertNotIn('_body_size',specs('FPS2512F2000TS',_body_size='explicit source dimension'))
        for model in ('FPQ1206F6800TS','FQP1206F6800TS','FPS0201F1000TS','FPS2512F200TS','FPS2512F2000TSX'):
            self.assertEqual(specs(model),{})
        self.assertEqual(complete(dict(品牌='Other',型号='FPS2512F2000TS',_component_type='厚膜电阻')), {})
        self.assertNotIn('_power_watt',specs('FPS2512F2000TS'))
        self.assertNotIn('生产状态',specs('FPS2512F2000TS'))

    def test_explicit_dimensions_pitch_temperature_and_units(self):
        from catalog_passive_completion import complete
        record = dict(品牌='TDK',型号='B32529C0104K000',_component_type='薄膜电容',
                      封装代码='RADIAL/P5.0',容值='0.1',容值单位='uF',安装方式='插件',工作温度='-55°C ~ +105°C')
        record.update({'尺寸（mm）':'7.3*2.5*6.5mm','脚距（mm）':'5.0','耐压（V）':'63V'})
        result = complete(record)
        self.assertEqual(result['_size'],'RADIAL/P5.0')
        self.assertEqual(result['_body_size'],'7.3*2.5*6.5mm')
        self.assertEqual(result['_pitch'],'5.0 mm')
        self.assertEqual(result['_pf'],100000)
        self.assertEqual((result['_temp_low'],result['_temp_high']),(-55,105))
        self.assertEqual(result['_volt_num'],63)
        record.update(_pf=0,_volt_num=16,_size='KNOWN',_temp_low=-40)
        result = complete(record)
        self.assertFalse({'_pf','_volt_num','_size','_temp_low'} & result.keys())
        self.assertNotIn('_safety_class',result)

    def test_conditioned_impedance_is_readable_and_ranges_are_not_fake_scalars(self):
        from catalog_passive_completion import complete
        record = dict(品牌='Abracon',型号='ACML-0201-121-T',_component_type='磁珠',阻抗单位='Ω')
        record['阻抗@100MHz']='120 Ohms @ 100MHz'
        result=complete(record)
        self.assertEqual(result['_catalog_impedance_ohm'],120)
        self.assertEqual(result['_impedance_text'],'120 Ohms @ 100MHz')
        record['阻抗@100MHz']='60 - 600 Ω'
        result=complete(record)
        self.assertNotIn('_catalog_impedance_ohm',result)
        self.assertEqual(result['_impedance_text'],'60 - 600 Ω @100MHz')
        record['阻抗@100MHz']='120 Ω @ 1GHz'
        self.assertNotIn('_catalog_impedance_ohm',complete(record))

    def test_no_temperature_from_model_or_material_and_no_unsafe_numeric_truncation(self):
        from catalog_passive_completion import complete,temperature,scalar
        for bad in ('X7R','B32529C0104K000','storage -55~125C','-500~1C','+125C reflow 260C'):
            self.assertEqual(temperature(bad),(None,None))
        for bad in ('1-10','10 @ 25C','nan','inf','1e999'):
            self.assertIsNone(scalar(bad))
        result=complete(dict(品牌='Unknown',型号='MP825-25.0-1%',_component_type='厚膜电阻',_res_ohm=0))
        self.assertFalse(result)
        result=complete(dict(品牌='三星Samsung',型号='CLR1CR25QA1INNG',_component_type='MLCC',_mat='COG'))
        self.assertNotIn('_tol',result)
        self.assertNotIn('_temp_low',result)

    def test_profiles_only_request_applicable_parameters(self):
        keys=lambda kind:{f.key for f in profile(kind)[1]}
        self.assertNotIn('_pitch',keys('MLCC'))
        self.assertNotIn('_life_hours_num',keys('MLCC'))
        self.assertIn('_life_hours_num',keys('铝电解电容'))
        self.assertNotIn('inductance_uh',keys('磁珠'))
        self.assertNotIn('_saturation_amps',keys('磁珠'))
        self.assertIn('_impedance_text',keys('磁珠'))
        self.assertNotIn('电源电压',keys('晶振'))
        self.assertNotIn('负载电容（pF）',keys('振荡器'))
        self.assertIn('负载电容（pF）',keys('晶振'))
        self.assertIn('接口类型',keys('实时时钟模块'))

    def test_streamed_compressed_overlay_reads_only_specs_and_preserves_indexed_identities(self):
        import tempfile,gzip,json
        from pathlib import Path
        import pyarrow as pa
        import pyarrow.parquet as pq
        from catalog_passive_completion import load,install
        fixture=CatalogFilterTests();fixture.setUp()
        conn=fixture.conn
        try:
            conn.execute("UPDATE components_search_resistor SET _power_watt=NULL WHERE 型号='R2'")
            original=list(conn.execute('SELECT * FROM components_search_resistor'))
            records=[dict(品牌='B',型号='R4',_component_type='厚膜电阻',封装代码='AXIAL',_mount_style='插件',_res_ohm=0,_tol=None,_power_watt=.25,_power_source='size',成本=999),
                     dict(品牌='B',型号='R4',_component_type='厚膜电阻',封装代码='DIFFERENT',_tol='1',成本=999),
                     dict(品牌='A',型号='R1',_component_type='厚膜电阻',封装代码='SHOULD-NOT-REPLACE',_res_ohm=999,成本=999),
                     dict(品牌='A',型号='R2',_component_type='厚膜电阻',_power_watt=.125,_power_source='context'),
                     dict(品牌='A',型号='NOT-INDEXED',_component_type='厚膜电阻',封装代码='AXIAL',成本=999)]
            with tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'prepared.parquet'
                pq.write_table(pa.Table.from_pylist(records),path)
                compressed=load(path,'厚膜电阻')
                self.assertIsInstance(compressed,bytes)
                raw=gzip.decompress(compressed).decode('utf-8')
                self.assertNotIn('成本',raw)
                install(conn,'厚膜电阻',compressed,'components_search_resistor')
                result=snapshot(conn,'厚膜电阻',{'_size':['AXIAL']},include_rows=True)
                self.assertEqual([r['型号'] for r in result['rows']],['R4'])
                self.assertIsNone(result['rows'][0]['_tol'])
                self.assertIsNone(result['rows'][0]['_power_watt'])
                self.assertEqual(snapshot(conn,'厚膜电阻')['total'],6)
                self.assertEqual(snapshot(conn,'厚膜电阻',keyword='R1',keyword_mode='exact',include_rows=True)['rows'][0]['_res_ohm'],1000)
                self.assertEqual(snapshot(conn,'厚膜电阻',keyword='R2',keyword_mode='exact',include_rows=True)['rows'][0]['_power_watt'],.125)
                self.assertEqual(list(conn.execute('SELECT * FROM components_search_resistor')),original)
                self.assertFalse(conn.execute("SELECT name FROM sqlite_master WHERE name LIKE 'catalog_passive%'").fetchall())
        finally:
            fixture.tearDown()

    def test_shared_source_is_readonly_thread_safe_and_has_no_account_context(self):
        import ast,tempfile
        from pathlib import Path
        from concurrent.futures import ThreadPoolExecutor
        import catalog_passive_completion as completion
        source=Path(__file__).resolve().parents[1]/'component_matcher.py'
        tree=ast.parse(source.read_text(encoding='utf-8'))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cached_catalog_passive_source')
        function.decorator_list=[]
        called=[]
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'public-index.sqlite'
            with sqlite3.connect(path) as conn:
                conn.execute('CREATE TABLE catalogue (model TEXT)')
                conn.execute("INSERT INTO catalogue VALUES ('PUBLIC-ONLY')")
            conn.close()
            namespace=dict(sqlite3=sqlite3,SEARCH_DB_PATH=str(path),
                install_jianghai_search_overlay=lambda conn:called.append('manufacturer'),
                install_catalog_parameters=lambda *args:called.append('specs'),
                _catalog_filters=SimpleNamespace(passive_completion=completion))
            exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),namespace)
            resource=namespace['cached_catalog_passive_source']('revision','薄膜电阻')
            def read():
                with resource.lock:
                    return resource.connection.execute('SELECT model FROM catalogue').fetchone()[0]
            with ThreadPoolExecutor(max_workers=2) as workers:
                self.assertEqual(list(workers.map(lambda _:read(),range(4))),['PUBLIC-ONLY']*4)
            with self.assertRaises(sqlite3.OperationalError):
                resource.connection.execute('DELETE FROM catalogue')
            self.assertEqual(called,['manufacturer','specs'])
            self.assertNotIn('session_state',ast.unparse(function))
            self.assertNotIn('current_member',ast.unparse(function))
            resource.connection.close()

    def test_inductor_keeps_unrelated_core_fields_and_uses_explicit_value_fallback(self):
        import gzip,json
        from catalog_passive_completion import complete,install
        fixture=CatalogFilterTests();fixture.setUp()
        try:
            conn=fixture.conn
            conn.execute('ALTER TABLE components_search_value ADD COLUMN _volt_num REAL')
            conn.execute('UPDATE components_search_value SET _volt_num=99')
            patch=complete(dict(品牌='A',型号='L3',_component_type='功率电感',电感值='5.6',电感单位='uH'))
            compressed=gzip.compress((json.dumps(['A','L3',patch])+'\n').encode())
            install(conn,'功率电感',compressed,'components_search_value')
            rows=snapshot(conn,'功率电感',ranges={'inductance_uh':(5.6,5.6)},include_rows=True)['rows']
            self.assertEqual([row['型号'] for row in rows],['L3'])
            self.assertEqual(conn.execute("SELECT _volt_num FROM catalog_passive_source WHERE 型号='L3'").fetchone()[0],99)
        finally:
            fixture.tearDown()

    def test_cold_restore_canonicalizes_revision_before_building_shared_catalogue(self):
        import ast
        from pathlib import Path
        from types import SimpleNamespace
        path=Path(__file__).resolve().parents[1]/'component_matcher.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='cached_catalog_snapshot')
        function.decorator_list=[]
        called=[]
        namespace=dict(_catalog_filters=SimpleNamespace(passive_completion=SimpleNamespace(KINDS={'MLCC'})),
            os=SimpleNamespace(path=SimpleNamespace(isfile=lambda path:False)),PREPARED_CACHE_PATH='public.parquet',
            cached_catalog_parameters=lambda *args:called.append(('restore',args)),
            catalog_filter_data_signature=lambda:'restored-revision')
        exec(compile(ast.Module(body=[function],type_ignores=[]),str(path),'exec'),namespace)
        snapshot_function=namespace['cached_catalog_snapshot']
        namespace['cached_catalog_snapshot']=lambda *args:called.append(('canonical',args)) or 'canonical-result'
        self.assertEqual(snapshot_function('missing-revision','MLCC',{}, {},'',1,20,True),'canonical-result')
        self.assertEqual(called[0],('restore',('missing-revision','MLCC')))
        self.assertEqual(called[1][1][0],'restored-revision')


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

    def test_upgrade_drops_removed_inapplicable_sort_without_losing_account_or_valid_filter(self):
        at=self.app()
        self.action(at,'kind',kind='MLCC')
        at.session_state[PREFIX+'sort']='_pitch'
        at.session_state[PREFIX+'desc']=True
        at.session_state[PREFIX+'_mat']=['X7R']
        at.session_state['_member_auth_token']='KEEP'
        at.run()
        self.assertFalse(at.exception)
        self.assertNotIn(PREFIX+'sort',at.session_state)
        self.assertEqual(at.session_state[PREFIX+'_mat'],['X7R'])
        self.assertEqual(at.session_state['_member_auth_token'],'KEEP')
