import unittest
from component_filters import snapshot, PREFIX
from catalog_result_table import build_payload,handle_request,numeric_display
from component_filters import profile
from tests import test_component_filters as fixtures


class SpecificationTableTests(unittest.TestCase):
    def test_column_widths_measure_page_content_instead_of_fixed_column_buckets(self):
        from pathlib import Path
        template=(Path(__file__).resolve().parents[1]/'catalog_results/index.html').read_text(encoding='utf-8')
        self.assertIn('function measureColumns()',template)
        self.assertIn('ctx.measureText(line).width',template)
        self.assertIn("co.style.width=widths.get(c.key)+'px'",template)
        self.assertIn('root.replaceChildren();measureColumns()',template)
        self.assertNotIn("c.key==='品牌'?145",template)
        self.assertIn('fitTable();height()',template)

    def test_result_template_has_compact_rows_without_repeated_model_caption(self):
        from pathlib import Path
        template=(Path(__file__).resolve().parents[1]/'catalog_results/index.html').read_text(encoding='utf-8')
        self.assertNotIn('查看价格与替代型号',template)
        self.assertIn('#root .scroll td{height:46px;padding:6px 9px}',template)
        self.assertIn('td.append(button(value,()=>openModel(row)))',template)

    def test_footer_has_counts_without_unrequested_help_or_price_permission_caption(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        template=(root/'catalog_results/index.html').read_text(encoding='utf-8')
        self.assertNotIn('表头可排序 · 型号列固定 · 数量不是库存',template)
        self.assertIn("'本页 '+data.rows.length+' 条",template)
        renderer=(root/'component_filters.py').read_text(encoding='utf-8')
        self.assertNotIn('点击型号查看匹配，价格沿用原有账号、客户和成本时间权限。',renderer)

    def setUp(self):
        self.fixture=fixtures.CatalogFilterTests()
        self.fixture.setUp()
        self.conn=self.fixture.conn
        self.result=snapshot(self.conn,'厚膜电阻',include_rows=True,page_size=2)
        self.payload=build_payload(self.result,'厚膜电阻','全部',{}, {},'')
    def tearDown(self):self.fixture.tearDown()
    def request(self,action,**values):return dict(view=self.payload['view'],event='event-'+action,action=action,**values)

    def test_sort_is_global_numeric_and_stable_across_pages_not_current_page_only(self):
        first=snapshot(self.conn,'厚膜电阻',include_rows=True,page_size=2,sort_key='_res_ohm')
        second=snapshot(self.conn,'厚膜电阻',include_rows=True,page_size=2,page=2,sort_key='_res_ohm')
        self.assertEqual([r['_res_ohm'] for r in first['rows']],[0,100])
        self.assertEqual([r['_res_ohm'] for r in second['rows']],[1000,5600])
        descending=snapshot(self.conn,'厚膜电阻',include_rows=True,page_size=2,sort_key='_res_ohm',sort_desc=True)
        self.assertEqual([r['_res_ohm'] for r in descending['rows']],[5600,5600])
        with self.assertRaises(ValueError):snapshot(self.conn,'厚膜电阻',sort_key='型号;DROP TABLE components_search_core')

    def test_normalized_tolerance_sorts_numerically_with_unknown_markings_last(self):
        self.conn.executemany('INSERT INTO components_search_resistor VALUES (?,?,?,?,?,?,?)',[
            ('A','R6','厚膜电阻','0402',100,'10',0.1),
            ('A','R7','厚膜电阻','0402',100,'2',0.1),
            ('A','R8','厚膜电阻','0402',100,'99999999998',0.1)])
        result=snapshot(self.conn,'厚膜电阻',include_rows=True,page_size=100,sort_key='_tol')
        self.assertEqual([r['_tol'] for r in result['rows'][:7]],['0.1','0.1','1','1','2','5','10'])
        self.assertEqual({r['_tol'] for r in result['rows'][7:]},{None,'99999999998'})

    def test_payload_keeps_values_and_labels_but_never_cost_or_raw_hidden_data(self):
        self.result['rows'][0]['成本']=999
        payload=build_payload(self.result,'厚膜电阻','全部',{}, {},'')
        self.assertTrue(payload['columns'][0]['visible'])
        self.assertEqual(payload['columns'][0]['key'],'型号')
        self.assertNotIn('成本',payload['rows'][0])
        self.assertNotEqual(payload['rows'][0]['id'],payload['rows'][1]['id'])
        self.assertEqual(payload['rows'][0]['_power_watt'],'1/16 W')
        self.assertEqual(payload['columns'][2]['key'],'_res_ohm')
        self.assertEqual(payload['columns'][2]['label'],'阻值')

    def test_match_requires_current_view_and_exact_server_side_row_no_autoselection(self):
        state={};matched=[]
        self.assertFalse(handle_request(state,self.payload,None,matched.append))
        self.assertFalse(handle_request(state,self.payload,self.request('match',id='forged'),matched.append))
        self.assertFalse(handle_request(state,self.payload,dict(self.request('match',id=self.payload['rows'][0]['id']),view='old'),matched.append))
        request=self.request('match',id=self.payload['rows'][0]['id'],model='ATTACKER MODEL')
        self.assertTrue(handle_request(state,self.payload,request,matched.append))
        self.assertEqual(matched,[self.payload['rows'][0]['型号']])
        self.assertFalse(handle_request(state,self.payload,request,matched.append))
        self.assertEqual(len(matched),1)

    def test_paging_size_and_sort_actions_are_bounded_and_keep_member_state(self):
        state={'_member_auth_token':'KEEP','search_query_input':'KEEP'}
        self.assertTrue(handle_request(state,self.payload,self.request('page',page=2),lambda _:None))
        self.assertEqual(state[PREFIX+'page'],2)
        self.assertTrue(handle_request(state,self.payload,self.request('size',size=50),lambda _:None))
        self.assertEqual(state[PREFIX+'page'],1)
        self.assertTrue(handle_request(state,self.payload,self.request('sort',column='_res_ohm',desc=True),lambda _:None))
        self.assertEqual(state[PREFIX+'sort'],'_res_ohm')
        self.assertTrue(state[PREFIX+'desc'])
        self.assertEqual(state['_member_auth_token'],'KEEP')
        self.assertEqual(state['search_query_input'],'KEEP')
        for action,values in [('page',{'page':999}),('size',{'size':999}),('page',{'page':True}),('sort',{'column':'成本','desc':True}),('sort',{'column':'型号','desc':'yes'})]:
            self.assertFalse(handle_request({},self.payload,self.request(action,**values),lambda _:None))

    def test_view_changes_when_conditions_or_page_or_sort_change(self):
        other=build_payload(self.result,'厚膜电阻','新条件',{'_size':['0402']},{},'')
        self.assertNotEqual(other['view'],self.payload['view'])
        next_page=snapshot(self.conn,'厚膜电阻',include_rows=True,page_size=2,page=2)
        self.assertNotEqual(build_payload(next_page,'厚膜电阻','全部',{}, {},'')['view'],self.payload['view'])

    def test_table_values_use_readable_units_without_changing_canonical_sort_values(self):
        fields={f.key:f for kind in ('厚膜电阻','MLCC','晶振','功率电感') for f in profile(kind)[1]}
        for key,value,expected in [('_pf',100000,'100 nF'),('_pf',1000000,'1 µF'),('_res_ohm',5600,'5.6 kΩ'),('frequency_hz',32768,'32.768 kHz'),('inductance_uh',0.01,'10 nH'),('_current_amps',0.2,'200 mA'),('_current_amps',0,'0 A')]:
            self.assertEqual(numeric_display(fields[key],value),expected)

    def test_inline_handoff_queues_model_without_mutating_an_already_mounted_mode_widget(self):
        import platform
        platform._wmi=None
        from streamlit.testing.v1 import AppTest
        source='''
import ast
from pathlib import Path
import streamlit as st
import component_filters
tree=ast.parse(Path('component_matcher.py').read_text(encoding='utf-8'))
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='handoff_catalog_model_to_search')
namespace=dict(st=st,clean_text=lambda value:str(value).strip(),_catalog_filters=component_filters)
exec(compile(ast.Module(body=[function],type_ignores=[]),'handoff-fixture','exec'),namespace)
st.session_state.setdefault('search_entry_mode',component_filters.FILTER_MODE)
st.radio('搜索方式',[component_filters.TEXT_MODE,component_filters.FILTER_MODE],key='search_entry_mode')
namespace['handoff_catalog_model_to_search'](' AO3400A ',defer=True)
'''
        at=AppTest.from_string(source,default_timeout=30).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['_catalog_match_model'],'AO3400A')
        self.assertEqual(at.session_state['search_entry_mode'],'按规格筛选')
