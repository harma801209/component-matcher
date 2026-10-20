import unittest
from component_filters import PREFIX, snapshot, category_counts
from catalog_filter_panel import build_payload, handle_request
from tests import test_component_filters as fixtures


class CatalogPanelTests(unittest.TestCase):
    def test_filter_template_has_no_duplicate_name_search_or_manual_search_gate(self):
        from pathlib import Path
        template=(Path(__file__).resolve().parents[1]/'catalog_facets/index.html').read_text(encoding='utf-8')
        for obsolete in ('model-keyword','启用实时搜索','部分一致','前方一致','完全一致','pending-filter-state'):
            self.assertNotIn(obsolete,template)
        self.assertIn("left.append(node('h3','筛选条件'),toggle)",template)
        self.assertIn("request('choice'",template)

    def setUp(self):
        self.fixture=fixtures.CatalogFilterTests()
        self.fixture.setUp()
        self.conn=self.fixture.conn
        self.categories=category_counts(self.conn)
        self.state={PREFIX+'category':'MLCC',PREFIX+'family':'电容','search_query_input':'KEEP','member_auth':'KEEP','cost_date':'KEEP'}

    def tearDown(self):
        self.fixture.tearDown()

    def payload(self, selected=None, ranges=None, keyword=''):
        return build_payload(self.categories,'MLCC',snapshot(self.conn,'MLCC'),snapshot(self.conn,'MLCC',selected,ranges,keyword),selected or {},ranges or {},keyword,self.state)

    def send(self, payload, action, **values):
        import hashlib
        event=hashlib.sha256((action+str(values)).encode()).hexdigest()
        return handle_request(self.state,payload,dict(view=payload['view'],event=event,action=action,**values))

    def test_stable_universe_retains_zero_options_and_checked_zero_can_be_removed(self):
        payload=self.payload({'_size':['0402']})
        material=next(g for g in payload['groups'] if g['key']=='_mat')
        self.assertEqual({o['value']:o['count'] for o in material['options']},{'X5R':0,'X7R':1,'__catalog_missing__':0})
        self.assertFalse(self.send(payload,'choice',field='_mat',value='X5R',checked=True))
        payload=self.payload({'_size':['0402'],'_mat':['X5R']})
        self.assertTrue(self.send(payload,'choice',field='_mat',value='X5R',checked=False))
        self.assertEqual(self.state[PREFIX+'_mat'],[])

    def test_group_clear_does_not_clear_other_fields_or_account_scope(self):
        self.state.update({PREFIX+'_size':['0402'],PREFIX+'_mat':['X7R'],PREFIX+'_pf_low':'1',PREFIX+'_pf_unit':'µF'})
        self.assertTrue(self.send(self.payload(),'clear_group',field='_size'))
        self.assertEqual(self.state[PREFIX+'_mat'],['X7R'])
        self.assertEqual(self.state[PREFIX+'_pf_unit'],'µF')
        self.assertTrue(self.send(self.payload(),'clear_all'))
        self.assertEqual(self.state[PREFIX+'category'],'MLCC')
        self.assertEqual(self.state['search_query_input'],'KEEP')
        self.assertEqual(self.state['member_auth'],'KEEP')
        self.assertEqual(self.state['cost_date'],'KEEP')

    def test_ranges_validate_units_order_finiteness_and_do_not_apply_invalid_input(self):
        payload=self.payload()
        for values in [('2','1','µF'),('nan','3','µF'),('-1','3','µF'),('1','3','fake')]:
            self.assertFalse(self.send(payload,'range',field='_pf',low=values[0],high=values[1],unit=values[2]))
        self.assertNotIn(PREFIX+'_pf_low',self.state)
        self.assertTrue(self.send(payload,'range',field='_pf',low='0.1',high='0.1',unit='µF'))
        self.assertEqual(self.state[PREFIX+'_pf_low'],'0.1')
        self.assertEqual(self.state[PREFIX+'page'],1)

    def test_request_rejects_forged_views_fields_options_categories_and_replay(self):
        payload=self.payload()
        self.assertFalse(handle_request(self.state,payload,dict(view='wrong',event='e',action='clear_all')))
        self.assertFalse(self.send(payload,'kind',kind='fabricated'))
        self.assertFalse(self.send(payload,'choice',field='成本',value='100',checked=True))
        self.assertFalse(self.send(payload,'choice',field='_mat',value='fabricated',checked=True))
        self.assertFalse(self.send(payload,'keyword',keyword='x'*121))
        self.assertTrue(self.send(payload,'keyword',keyword='C_1%'))
        self.assertFalse(self.send(payload,'keyword',keyword='C_1%'))
        self.assertEqual(self.state[PREFIX+'keyword'],'C_1%')

    def test_metadata_never_contains_models_costs_or_account_state(self):
        import json
        payload=self.payload()
        text=json.dumps(payload,ensure_ascii=False)
        self.assertNotIn('"C1"',text)
        self.assertNotIn('成本',text)
        self.assertNotIn('member_auth',text)
        self.assertNotIn('rows',payload)
        self.assertIn('电阻',{c['family'] for c in payload['categories']})

    def test_changed_panel_asset_gets_new_iframe_url_but_keeps_instance_key(self):
        from unittest.mock import patch,Mock
        from catalog_filter_panel import render_panel
        component=Mock(return_value=None)
        with patch('streamlit.components.v1.declare_component',return_value=component) as declare, patch('pathlib.Path.read_bytes',side_effect=[b'first-asset',b'changed-asset']):
            render_panel({'view':'one'},key=PREFIX+'panel')
            render_panel({'view':'two'},key=PREFIX+'panel')
        first,second=[call.args[0] for call in declare.call_args_list]
        self.assertNotEqual(first,second)
        self.assertTrue(first.startswith('catalog_parametric_filters_'))
        self.assertEqual([call.kwargs['key'] for call in component.call_args_list],[PREFIX+'panel',PREFIX+'panel'])

    def test_keyword_mode_is_in_view_identity_and_validated_with_keyword(self):
        panel=self.payload()
        self.assertFalse(self.send(panel,'keyword',keyword='C1',mode={'bad':'value'}))
        self.assertFalse(self.send(panel,'keyword',keyword='C1',mode='unknown'))
        self.assertTrue(self.send(panel,'keyword',keyword='C1',mode='exact'))
        exact=self.payload(keyword='C1')
        self.assertEqual(exact['keyword_mode'],'exact')
        self.assertNotEqual(panel['view'],exact['view'])

    def test_accepted_unchanged_search_has_ack_without_changing_view(self):
        panel=self.payload()
        self.assertTrue(self.send(panel,'keyword',keyword='',mode='contains'))
        current=self.payload()
        self.assertEqual(panel['view'],current['view'])
        self.assertNotEqual(panel['ack'],current['ack'])

    def test_deferred_batch_is_atomic_preserves_multiple_choices_and_account_scope(self):
        panel=self.payload()
        actions=[dict(action='choice',field='_size',value='0402',checked=True),dict(action='choice',field='_size',value='0603',checked=True),dict(action='keyword',keyword='C',mode='prefix')]
        self.assertTrue(self.send(panel,'batch',actions=actions))
        self.assertEqual(set(self.state[PREFIX+'_size']),{'0402','0603'})
        self.assertEqual(self.state[PREFIX+'keyword_mode'],'prefix')
        self.assertEqual(self.state['member_auth'],'KEEP')
        before=dict(self.state)
        self.assertFalse(self.send(panel,'batch',actions=[dict(action='clear_group',field='_size'),dict(action='range',field='_pf',low='2',high='1',unit='µF')]))
        self.assertEqual(self.state,before)
        self.assertFalse(self.send(panel,'batch',actions=[dict(action='kind',kind='MOSFET')]))
        self.assertFalse(self.send(panel,'batch',actions=actions*101))


class SearchModeSwitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import ast
        from pathlib import Path
        tree = ast.parse((Path(__file__).resolve().parents[1]/'component_matcher.py').read_text(encoding='utf-8'))
        cls.mode = next(node for node in tree.body if isinstance(node, ast.With) and any(
            isinstance(item.context_expr, ast.Call) and any(
                keyword.arg == 'key' and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == 'search-mode-tabs'
                for keyword in item.context_expr.keywords) for item in node.items))
        start = next(i for i, node in enumerate(tree.body) if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == 'catalog_match_model'
                             for target in node.targets))
        cls.entry_source = '\n'.join(ast.unparse(node) for node in tree.body[start:tree.body.index(cls.mode)+1])
        cls.handoff_source = ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                                             and node.name == 'handoff_catalog_model_to_search'))

    def test_mode_navigation_is_scoped_native_and_retains_internal_values(self):
        import ast
        from precision_theme import CSS
        calls = [node for node in ast.walk(self.mode) if isinstance(node, ast.Call)
                 and ast.unparse(node.func) == 'st.radio']
        self.assertEqual(len(calls), 1)
        args = {keyword.arg: keyword.value for keyword in calls[0].keywords}
        self.assertEqual(ast.literal_eval(args['key']), 'search_entry_mode')
        self.assertEqual(ast.literal_eval(args['label_visibility']), 'collapsed')
        self.assertEqual(ast.unparse(calls[0].args[1]), '[_catalog_filters.TEXT_MODE, _catalog_filters.FILTER_MODE]')
        for selector in ('label[data-baseweb="radio"]>div:first-child',
                         'label[data-testid="stRadioOption"]>div>div:first-child',
                         'label:has(input[type="radio"]):has(input:checked)',
                         'label:has(input[type="radio"]):has(input:focus-visible)'):
            self.assertIn('.st-key-search-mode-tabs ' + selector, CSS)
        self.assertIn('.st-key-search-mode-tabs label:has(input[type="radio"]) {flex:1;min-width:0;', CSS)

    def test_switch_and_pending_catalogue_handoff_keep_original_state_contract(self):
        from streamlit.testing.v1 import AppTest
        source = '''
import streamlit as st
import component_filters as _catalog_filters
clean_text = lambda value: str(value or '').strip()
pending_search_after_login = ''
'''
        source += self.handoff_source + '\n' + self.entry_source
        source += '''
if search_entry_mode == _catalog_filters.FILTER_MODE:
    if st.button('查看型号匹配'):
        handoff_catalog_model_to_search(' AO3400A ', defer=True)
        st.rerun()
    st.stop()
kwargs = dict(label='请输入料号，可多行输入', key='search_query_input')
if 'search_query_input' not in st.session_state:
    kwargs['value'] = st.session_state.get('_last_search_query_input', '')
st.text_area(**kwargs)
'''
        at = AppTest.from_string(source, default_timeout=30)
        at.session_state['_last_search_query_input'] = 'FRC0402J102 TS'
        at.session_state['_member_auth_token'] = 'KEEP'
        at.session_state['cost_date'] = 'KEEP'
        at.run()
        self.assertFalse(at.exception)
        self.assertEqual(at.radio[0].options, ['型号搜索', '规格筛选'])
        self.assertEqual(at.radio[0].value, '型号／文字搜索')
        at.text_area[0].set_value('DRAFT\n0402 1kΩ').run()
        at.radio[0].set_value('按规格筛选').run()
        self.assertFalse(at.exception)
        self.assertEqual(at.radio[0].value, '按规格筛选')
        self.assertEqual(len(at.text_area), 0)
        at.radio[0].set_value('型号／文字搜索').run()
        self.assertEqual(at.text_area[0].value, 'DRAFT\n0402 1kΩ')
        self.assertEqual(at.session_state['_last_search_query_input'], 'FRC0402J102 TS')
        at.radio[0].set_value('按规格筛选').run()
        at.button[0].click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.radio[0].value, '型号／文字搜索')
        self.assertEqual(at.text_area[0].value, 'AO3400A')
        self.assertEqual(at.session_state['_member_auth_token'], 'KEEP')
        self.assertEqual(at.session_state['cost_date'], 'KEEP')


class SearchFormLayoutTests(unittest.TestCase):
    @staticmethod
    def panel():
        import ast
        from pathlib import Path
        tree = ast.parse((Path(__file__).resolve().parents[1]/'component_matcher.py').read_text(encoding='utf-8'))
        return next(node for node in tree.body if isinstance(node, ast.With) and any(
            isinstance(item.context_expr, ast.Call) and any(
                keyword.arg == 'key' and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == 'workbench-search-panel'
                for keyword in item.context_expr.keywords) for item in node.items))

    def test_text_input_and_submit_live_inside_brand_column(self):
        import ast
        panel = self.panel()
        columns = [node for node in panel.body if isinstance(node, ast.With)]
        self.assertEqual([ast.unparse(node.items[0].context_expr) for node in columns],
                         ['customer_column', 'brand_column'])
        brand = columns[1]
        calls = [node for node in ast.walk(brand) if isinstance(node, ast.Call)]
        self.assertEqual(sum(ast.unparse(node.func) == 'st.text_area' for node in calls), 1)
        self.assertEqual(sum(ast.unparse(node.func) == 'st.button' for node in calls), 1)
        from precision_theme import CSS
        self.assertIn('.st-key-workbench-search-panel [data-testid="stColumn"] {width:100%!important;flex:1 1 100%!important;}', CSS)

    def test_moved_form_preserves_input_and_brand_customer_guards(self):
        import ast
        from streamlit.testing.v1 import AppTest
        source = '''
import streamlit as st
SEARCH_BRAND_MODE_AUTO = '自动匹配其他品牌'
SEARCH_BRAND_MODE_CUSTOM = '指定品牌'
SEARCH_BRAND_MAX_SELECTIONS = 5
search_brand_mode_key = 'search_brand_mode'
search_selected_brands_key = 'search_selected_brands'
pending_customer_type = pending_customer_name = ''
clean_text = lambda value: str(value or '').strip()
bom_export_brand_options = lambda: ['Brand A', 'Brand B']
st.session_state.setdefault(search_brand_mode_key, SEARCH_BRAND_MODE_AUTO)
def render_sales_cost_customer_selector(**kwargs):
    return '', '', st.session_state.get('fixture_ready', True)
'''
        source += ast.unparse(self.panel())
        source += "\nif search_clicked: st.success(query_input)\n"
        at = AppTest.from_string(source)
        at.session_state['_last_search_query_input'] = 'FRC0402J102 TS'
        at.session_state['_member_auth_token'] = 'KEEP'
        at.session_state['cost_date'] = 'KEEP'
        at.run()
        self.assertFalse(at.exception)
        self.assertEqual(at.text_area[0].value, 'FRC0402J102 TS')
        self.assertFalse(at.button[0].disabled)
        at.text_area[0].set_value('FRC0603J221 TS\n0402 1kΩ').run()
        at.session_state['search_brand_mode'] = '指定品牌'
        at.run()
        self.assertTrue(at.button[0].disabled)
        self.assertEqual(at.text_area[0].value, 'FRC0603J221 TS\n0402 1kΩ')
        at.multiselect[0].select('Brand A').run()
        self.assertFalse(at.button[0].disabled)
        at.button[0].click().run()
        self.assertEqual(at.success[0].value, 'FRC0603J221 TS\n0402 1kΩ')
        at.session_state['fixture_ready'] = False
        at.run()
        self.assertTrue(at.button[0].disabled)
        self.assertEqual(at.session_state['_member_auth_token'], 'KEEP')
        self.assertEqual(at.session_state['cost_date'], 'KEEP')
        self.assertFalse(at.exception)


if __name__=='__main__':
    unittest.main()
