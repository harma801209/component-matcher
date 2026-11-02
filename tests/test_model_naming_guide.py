import ast
import copy
from pathlib import Path
import unittest

import model_naming_guide as guide


class NamingGuideTests(unittest.TestCase):
    def record(self,model,brand='FOJAN(富捷)',series='FRH',kind='厚膜电阻'):
        return dict(品牌=brand,型号=model,系列=series,器件类别=kind)

    def parts(self,record):
        result=guide.explain(record)
        self.assertTrue(result['segments'])
        self.assertEqual(''.join(r['code'] for r in result['segments']),guide.compact(record['型号']))
        return {r['name']:r for r in result['segments']}

    def test_user_screenshot_fojan_examples_decode_without_fake_suffix_claims(self):
        for model,series in (('FRH0402B4703T','FRH'),('FRH0402B4703TS','FRH'),
                             ('FRT0402B4703TSV','FRT'),('FRT0402B4703TSX','FRT'),
                             ('FTH0402B4703TSX','FTH')):
            parts=self.parts(self.record(model,series=series))
            self.assertEqual(parts['封装']['meaning'],'0402（英制代码）')
            self.assertEqual(parts['阻值误差']['meaning'],'±0.1%')
            self.assertEqual(parts['阻值']['meaning'],'470 kΩ')
            if series!='FRT':
                self.assertFalse(parts['附加订货码']['verified'])

    def test_frt_termination_is_not_power_and_tcr_is_series_scoped(self):
        for tail,ppm in (('TSX',25),('TSV',50)):
            parts=self.parts(self.record('FRT0402B4703'+tail,series='FRT'))
            self.assertEqual(parts['端电极']['meaning'],'Sn（锡）')
            self.assertEqual(parts['温度系数']['meaning'],f'±{ppm} ppm/℃')
            self.assertNotIn('功率',parts)
        self.assertNotIn('温度系数',self.parts(self.record('FTH0402B4703TSX',series='FTH')))

    def test_same_tcr_has_different_codes_in_viking_and_yageo(self):
        v=self.parts(self.record('AR02BTC4703','光颉Viking','AR','薄膜电阻'))
        y=self.parts(self.record('RT0402BRD07470KL','国巨YAGEO','RT','薄膜电阻'))
        self.assertEqual((v['温度系数']['code'],y['温度系数']['code']),('C','D'))
        self.assertEqual(v['温度系数']['meaning'],y['温度系数']['meaning'])
        self.assertEqual(v['阻值']['meaning'],y['阻值']['meaning'])
        c=self.parts(self.record('RT0402BRC07470KL','国巨YAGEO','RT','薄膜电阻'))
        self.assertEqual(c['温度系数']['meaning'],'±15 ppm/℃')

    def test_viking_optional_power_and_marking_fields_keep_correct_positions(self):
        p=self.parts(self.record('AR03BTCX1001N','Viking','AR','薄膜电阻'))
        self.assertEqual(p['功率代码']['code'],'X')
        self.assertIn('1/10 W',p['功率代码']['meaning'])
        self.assertEqual(p['阻值']['meaning'],'1 kΩ')
        self.assertEqual(p['标记代码']['meaning'],'无标记')

    def test_zero_ohm_decimal_and_whitespace_are_not_lost(self):
        p=self.parts(self.record(' frc0402j000 TS ',series='FRC'))
        self.assertEqual(p['阻值']['meaning'],'0 Ω')
        p=self.parts(self.record('FPL2512FR002TS',series='FPL'))
        self.assertEqual(p['阻值']['meaning'],'0.002 Ω')

    def test_murata_and_samsung_use_separate_size_and_voltage_tables(self):
        m=self.parts(self.record('GRM155R71C104KA88D','村田Murata','GRM','MLCC'))
        s=self.parts(self.record('CL05B104KO5NNNC','三星Samsung','CL','MLCC'))
        self.assertEqual(m['封装']['meaning'],s['封装']['meaning'])
        self.assertEqual(m['容量']['meaning'],'100 nF')
        self.assertEqual(s['额定电压']['meaning'],'16 V')
        self.assertFalse(m['厚度代码']['verified'])
        self.assertFalse(s['厚度／产品／包装尾码']['verified'])

    def test_tdk_metric_size_and_pdc_voltage_are_not_misread(self):
        t=self.parts(self.record('C1608X7R1H104K080AA','东电化TDK','C','MLCC'))
        self.assertEqual(t['封装']['meaning'],'1608（公制）→ 0603')
        p=self.parts(self.record('FV31X221K202ECG','信昌PDC','FV','MLCC'))
        self.assertEqual(p['额定电压']['meaning'],'2000 V')
        self.assertEqual(p['容量']['meaning'],'220 pF')
        # FH/FK impulse-voltage codes must NOT reuse the FV DC-voltage rule.
        self.assertEqual(guide.explain(self.record('FK08X221K502EGG','信昌PDC','FK','MLCC'))['segments'],[])

    def test_amotech_uses_existing_source_backed_codes_without_claiming_certification(self):
        import amotech_catalog
        model=next(r['型号'] for r in amotech_catalog.catalogue_rows() if amotech_catalog.STANDARD.fullmatch(r['型号']))
        p=self.parts(self.record(model,'AMOTECH(阿莫泰克)','AC','MLCC'))
        self.assertIn('不等于已通过 AEC-Q200',p['应用']['meaning'])
        self.assertIn('端电极',p)

    def test_wrong_brand_kind_unknown_and_malformed_models_do_not_invent_codes(self):
        for row in (self.record('FRH0402B4703TS','Other'),self.record('AR02BTC4703','FOJAN(富捷)'),
                    self.record('FRH0402B4703TS',kind='MLCC'),self.record('AR02BTCRRRR','Viking'),
                    self.record('CL05B104KO5NNNC','Other',kind='MLCC'),self.record('UNKNOWN')):
            self.assertEqual(guide.explain(row)['segments'],[],row)

    def test_result_only_groups_and_allowlist_remove_all_account_and_price_data(self):
        rows=[{**self.record('FRH0402B4703TS'),'成本':9.99,'客户名称':'SECRET','_member_token':'SECRET'},
              self.record('FRH0402B4703 TS'),self.record('FRT0402B4703TSX',series='FRT'),
              self.record('OTHER','Other','Unverified')]
        before=copy.deepcopy(rows)
        safe=guide.public_candidates(rows)
        self.assertEqual(len(safe),3)
        self.assertNotIn('SECRET',repr(safe))
        self.assertEqual(set(guide.result_groups(safe)),{('FOJAN(富捷)','FRH'),('FOJAN(富捷)','FRT'),('Other','Unverified')})
        self.assertEqual(rows,before)
        self.assertEqual(guide.public_candidates([dict(品牌=float('nan'),型号=None)]),[])

    def test_html_escapes_library_content_and_unknown_text_is_not_a_fake_decode(self):
        data=dict(model='A',brand='B',series='C',segments=[guide.part('<script>','<svg>','<img onerror=x>',False)],source='<script>')
        html=guide.guide_html(data)
        self.assertNotIn('<script>',html)
        self.assertNotIn('<img ',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertIn('待核验',html)
        self.assertIn('暂不把库内参数反写',guide.guide_html(guide.explain(self.record('UNKNOWN'))))

    def test_search_hook_uses_final_visible_matches_and_has_no_quote_or_auth_write(self):
        path=Path(__file__).resolve().parents[1]/'component_matcher.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='render_model_naming_header']
        self.assertEqual(len(calls),1)
        self.assertEqual(ast.unparse(calls[0].args[1]),'show_df')
        ui=Path(guide.__file__).read_text(encoding='utf-8')
        for prohibited in ('sqlite3','session_state','cached_run_query_match','complete_member_search_audit','urllib','requests.'):
            self.assertNotIn(prohibited,ui)
        self.assertIn('st.fragment(_render_header)',ui)


class NamingGuideUITests(unittest.TestCase):
    def test_popover_has_only_real_result_options_and_model_specific_tables(self):
        from streamlit.testing.v1 import AppTest
        script='''
import streamlit as st
from model_naming_guide import render_header
st.session_state['parent_runs']=st.session_state.get('parent_runs',0)+1
rows=[dict(品牌='FOJAN(富捷)',型号='FRH0402B4703TS',系列='FRH',器件类别='厚膜电阻'),
      dict(品牌='光颉Viking',型号='AR02BTC4703',系列='AR',器件类别='薄膜电阻')]
render_header('贴片电阻（Chip Resistor）规格条件',rows,'fixture')
st.caption('原匹配结果仍在')
'''
        at=AppTest.from_string(script).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.selectbox),2)
        self.assertEqual(at.selectbox[1].value,'FRH0402B4703TS')
        self.assertTrue(any('470 kΩ' in item.value for item in at.markdown))
        at.selectbox[0].select(('光颉Viking','AR')).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.selectbox[1].value,'AR02BTC4703')
        self.assertTrue(any('±25 ppm/℃' in item.value for item in at.markdown))
        self.assertTrue(any('原匹配结果仍在' in item.value for item in at.caption))
