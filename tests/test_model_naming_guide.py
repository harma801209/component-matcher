import ast
import copy
from pathlib import Path
import unittest

import model_naming_guide as guide


class NamingGuideTests(unittest.TestCase):
    def test_murata_published_dimensions_and_packaging_do_not_use_stock_values(self):
        row=dict(品牌='村田Murata',型号='GRM033R60J105ME15D',器件类型='MLCC',
                 厚度='999',尺寸='999')
        data=guide.explain(row)
        fields={p['name']:p for p in data['segments']}
        self.assertIn('0.6×0.3 mm',fields['封装']['meaning'])
        self.assertIn('0201',fields['封装']['meaning'])
        self.assertEqual(fields['厚度代码']['meaning'],'0.3 mm（标称值；具体公差及最大厚度以该型号规格书为准）')
        self.assertTrue(fields['厚度代码']['verified'])
        self.assertEqual(fields['个别规格识别码']['code'],'E15')
        self.assertFalse(fields['个别规格识别码']['verified'])
        self.assertEqual(fields['包装']['code'],'D')
        self.assertIn('180 mm',fields['包装']['meaning'])
        self.assertIn('纸带',fields['包装']['meaning'])
        self.assertTrue(fields['包装']['verified'])
        self.assertFalse(data['complete'])
        self.assertEqual(len(data['segments']),9)
        self.assertEqual(data['verified_segments'],8)
        self.assertEqual(''.join(p['code'] for p in data['segments']),row['型号'])
        self.assertTrue(any('murata.com' in url for _,url in data['source_links']))
        self.assertNotIn('999',repr(data['segments']))
        for code,value in [('5','0.5'),('8','0.8'),('B','1.25'),('M','1.15'),('Y','0.135')]:
            other=guide.explain(dict(row,型号='GRM03'+code+'R60J105ME15D'))
            thickness=next(p for p in other['segments'] if p['name']=='厚度代码')
            self.assertTrue(thickness['verified'])
            self.assertTrue(thickness['meaning'].startswith(value+' mm'))
        for model,field in [('GRM03XR60J105ME15D','厚度代码'),
                            ('GRM03ZR60J105ME15D','厚度代码'),
                            ('GRM033R60J105ME15Z','包装')]:
            unknown=guide.explain(dict(row,型号=model))
            self.assertFalse(next(p for p in unknown['segments'] if p['name']==field)['verified'])
            self.assertEqual(''.join(p['code'] for p in unknown['segments']),model)
        self.assertFalse(guide.explain(dict(row,品牌='信昌PDC'))['segments'])

    def test_vishay_leaded_and_hp_codes_use_their_own_original_tables(self):
        base=dict(品牌='威世Vishay',器件类型='厚膜电阻')
        for model,document in [('CRCW08053K90FKTA','20008'),('CRCW06030000ZSTA','20008'),
                               ('CRCW060368R0FKTAHP','20115'),('CRCW060368R0FKEAHP','20043'),
                               ('CRCW04020000Z0TDHP','20115'),('CRCW201010K0FKEJHP','20043')]:
            data=guide.explain(dict(base,型号=model))
            self.assertTrue(data['complete'],model)
            self.assertEqual(''.join(p['code'] for p in data['segments']),model)
            self.assertIn(document,data['source'])
            self.assertTrue(any('/'+document+'/' in u for _,u in data['source_links']))
        leaded=guide.explain(dict(base,型号='CRCW08053K90FKTA'))
        fields={p['name']:p['meaning'] for p in leaded['segments']}
        self.assertEqual(fields['阻值'],'3.9 kΩ')
        self.assertEqual(fields['温度系数'],'±100 ppm/℃')
        self.assertIn('含铅',fields['包装'])
        self.assertIn('8 mm',fields['包装'])
        extra=guide.explain(dict(base,型号='CRCW08053K90FKTA99'))
        self.assertTrue(extra['segments']);self.assertFalse(extra['complete'])
        for model in ('CRCW02013K90FKTA','CRCW04023K90FKTA','CRCW08050000Z0TA',
                      'CRCW08053K90FKTCHP','CRCW08050000ZSTAHP','CRCW08053K90FKTAHP99','CRCW0805000RFKTA'):
            self.assertFalse(guide.explain(dict(base,型号=model))['segments'],model)
        self.assertFalse(guide.explain(dict(base,品牌='YAGEO',型号='CRCW08053K90FKTA'))['segments'])

    def test_yageo_mfr_axial_codes_are_complete_without_guessing_stock_or_status(self):
        row=dict(品牌='国巨YAGEO',器件类型='薄膜电阻',型号='MFR-25FTE52-130K',温度系数='999ppm/℃')
        data=guide.explain(row)
        self.assertTrue(data['complete'])
        self.assertEqual(''.join(p['code'] for p in data['segments']),row['型号'])
        fields={p['name']:p['meaning'] for p in data['segments']}
        self.assertEqual(fields['功率'].split('（')[0],'1/4W')
        self.assertEqual(fields['阻值'],'130 kΩ')
        self.assertEqual(fields['温度系数'],'±50 ppm/℃')
        self.assertIn('52.4',fields['引脚成形'])
        self.assertNotIn('封装',fields)
        self.assertTrue(data['source_links'])
        for model in ('MFR25SFRF26-1R5','MFR200FTF73-100R','MFR-25FT-FB-10K'):
            result=guide.explain(dict(row,型号=model))
            self.assertTrue(result['segments'])
            self.assertEqual(''.join(p['code'] for p in result['segments']),model)
        unspecified=guide.explain(dict(row,型号='MFR-25FT-52-10K'))
        self.assertFalse(unspecified['complete'])
        historical=guide.explain(dict(row,型号='MFR-25FTEF100R'))
        self.assertIn('历史计划',historical['source'])
        for model in ('MFR-25BTE52-10K','MFR-25FTD52-10K','MFR100FTEFB-10K','MFR-25FTE52-10KXYZ'):
            self.assertFalse(guide.explain(dict(row,型号=model))['segments'])
        self.assertFalse(guide.explain(dict(row,品牌='华科Walsin'))['segments'])

    def test_streaming_coverage_audit_counts_every_row_without_claiming_full_coverage(self):
        import hashlib
        import tempfile
        import pyarrow as pa
        import pyarrow.parquet as pq
        from tools.audit_model_naming_coverage import audit_catalogue
        with tempfile.TemporaryDirectory(prefix='naming-coverage-stream-') as directory:
            path=Path(directory)/'public.parquet'
            pq.write_table(pa.Table.from_pylist([
                {'品牌':'华新科Walsin','型号':'0201X225M6R3CT','系列':'常规','器件类型':'MLCC'},
                {'品牌':'太阳诱电Taiyo','型号':'MEASJ063BB5225M','系列':'MEASJ','器件类型':'MLCC'},
                {'品牌':'Other','型号':'UNKNOWN','系列':None,'器件类型':'MLCC'},
            ]),path)
            before=hashlib.sha256(path.read_bytes()).hexdigest()
            report=audit_catalogue(path,batch_size=1)
            self.assertEqual(report,audit_catalogue(path,batch_size=64))
            self.assertEqual(report['summary']['records'],3)
            self.assertEqual(report['summary']['complete'],1)
            self.assertEqual(report['summary']['partial'],1)
            self.assertEqual(report['summary']['unexplained'],1)
            self.assertFalse(report['summary']['full_coverage'])
            self.assertEqual(report['source_sha256'],before)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)

    def test_taiyo_meas_screenshot_has_original_code_segments_not_inferred_values(self):
        row=dict(品牌='太阳诱电Taiyo',型号='MEASJ063BB5225M',器件类别='陶瓷贴片电容（MLCC）',容值='999',耐压='999V')
        data=guide.explain(row)
        self.assertTrue(data['segments'])
        fields={p['name']:p for p in data['segments']}
        self.assertEqual(fields['额定电压']['meaning'],'6.3 VDC')
        self.assertIn('0201',fields['封装']['meaning'])
        self.assertIn('X5R',fields['温度特性']['meaning'])
        self.assertEqual(fields['容量']['meaning'],'2.2 µF')
        self.assertEqual(fields['容量误差']['meaning'],'±20%')
        self.assertIn('0.09',fields['尺寸公差']['meaning'])
        self.assertFalse(data['complete'])
        self.assertIn('缺少',repr(data['segments']))
        self.assertTrue(data['source_links'])
        full=guide.explain(dict(row,型号='MEASJ063BB5225MF1A01'))
        self.assertFalse(full['complete'])
        self.assertEqual(''.join(p['code'] for p in full['segments']),'MEASJ063BB5225MF1A01')
        self.assertFalse(guide.explain(dict(row,品牌='信昌PDC'))['segments'])

    def test_walsin_general_mlcc_codes_are_not_mt_or_pdc_tables(self):
        row=dict(品牌='华新科Walsin',型号='0201X225M6R3CT',器件类别='MLCC')
        data=guide.explain(row)
        self.assertTrue(data['complete'])
        fields={p['name']:p['meaning'] for p in data['segments']}
        self.assertEqual(fields['介质'],'X5R')
        self.assertEqual(fields['容量'],'2.2 µF')
        self.assertEqual(fields['额定电压'],'6.3 VDC')
        self.assertEqual(fields['端电极'],'Cu / Ni / Sn')
        self.assertFalse(guide.explain(dict(row,型号='0201X225M6R3'))['complete'])
        self.assertFalse(guide.explain(dict(row,品牌='信昌PDC'))['segments'])

    def test_direct_part_branch_has_entry_for_visible_source_and_matches(self):
        path=Path(__file__).resolve().parents[1]/'component_matcher.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='render_part_model_naming_header']
        self.assertEqual(len(calls),2)
        self.assertEqual([ast.unparse(n.args[1]) for n in calls],['part_info_df','part_info_df'])
        self.assertEqual({ast.unparse(n.args[2]) for n in calls},{'show_df','[]'})

    def test_yageo_cc_x7r_explains_published_fields_without_inventing_bb(self):
        result=guide.explain({'品牌':'国巨YAGEO','型号':'CC0603KRX7R9BB104','器件类型':'MLCC'})
        fields={p['name']:p for p in result['segments']}
        self.assertEqual(fields['容量']['meaning'],'100 nF')
        self.assertEqual(fields['额定电压']['meaning'],'50 VDC')
        self.assertEqual(fields['容量误差']['meaning'],'±10%')
        self.assertIn('7 英寸',fields['包装']['meaning'])
        self.assertFalse(fields['工艺／端电极代码']['verified'])
        self.assertFalse(result['complete'])
        self.assertEqual(''.join(p['code'] for p in result['segments']),'CC0603KRX7R9BB104')
        self.assertTrue(result['source_links'])
        for brand,kind,model in [('TDK','MLCC','CC0603KRX7R9BB104'),('Yageo','厚膜电阻','CC0603KRX7R9BB104'),
                                  ('Yageo','MLCC','CC0603KRX5R9BB104'),('Yageo','MLCC','CC0603KRX7R3BB104')]:
            self.assertFalse(guide.explain({'品牌':brand,'器件类型':kind,'型号':model})['segments'])


    def test_walsin_mt_complete_code_is_brand_scoped_and_source_backed(self):
        actual=guide.explain({'品牌':'华新科Walsin','型号':'MT18B334K500CT','器件类型':'MLCC'})
        self.assertTrue(actual['complete'])
        fields={p['name']:p['meaning'] for p in actual['segments']}
        self.assertEqual(fields['介质'],'X7R')
        self.assertEqual(fields['容量'],'330 nF')
        self.assertEqual(fields['端电极'],'Cu / Ni / Sn')
        self.assertEqual(fields['包装'],'7 英寸卷盘')
        self.assertTrue(actual['source_links'])
        for model,tol in (('MT18N4R0A500CG','±0.05 pF'),('MT18N4R0B500CT','±0.1 pF')):
            result=guide.explain({'品牌':'Walsin','型号':model,'器件类型':'MLCC'})
            self.assertTrue(result['complete'])
            self.assertIn(tol,[p['meaning'] for p in result['segments']])
        for model in ('MT18B334K500','MT18B334K500CTX'):
            result=guide.explain({'品牌':'Walsin','型号':model,'器件类型':'MLCC'})
            self.assertFalse(result['complete'])
            self.assertEqual(''.join(p['code'] for p in result['segments']),model)
        other=guide.explain({'品牌':'信昌PDC','型号':'MT18B334K500CT','器件类型':'MLCC'})
        self.assertFalse(other['complete'])
        self.assertNotIn('2026-09',other['source'])


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

    def test_user_walsin_wr_screenshot_uses_manufacturer_field_positions(self):
        p=self.parts(self.record('WR04X1602FTL','华新科Walsin','WR','厚膜电阻'))
        self.assertEqual(p['封装']['meaning'],'0402（英制）')
        self.assertEqual(p['阻值']['meaning'],'16 kΩ')
        self.assertEqual(p['阻值误差']['meaning'],'±1%')
        self.assertIn('常规阻值',p['类型']['meaning'])
        self.assertEqual(p['包装']['meaning'],'7 英寸卷盘')
        self.assertEqual(p['端电极']['meaning'],'Sn 基（无铅）')
        self.assertTrue(all(s['verified'] for s in p.values()))
        self.assertNotIn('温度系数',p)  # X is not a TCR letter.

    def test_walsin_wr_jumper_spaces_and_wf_subtypes_do_not_share_type_codes(self):
        p=self.parts(self.record('WR04X000 PTL','Walsin','WR'))
        self.assertEqual(p['阻值']['meaning'],'0 Ω')
        self.assertIn('跳线',p['阻值误差']['meaning'])
        p=self.parts(self.record('WR06W4R70FTL','Walsin','WR'))
        self.assertEqual(p['阻值']['meaning'],'4.7 Ω')
        self.assertIn('扩展阻值',p['类型']['meaning'])
        p=self.parts(self.record('WF04H1602BTL','Walsin','WF'))
        self.assertIn('厚膜',p['类型']['meaning'])
        self.assertNotIn('温度系数',p)
        p=self.parts(self.record('WF06U3742DTL','Walsin','WF'))
        self.assertEqual(p['温度系数']['meaning'],'±25 ppm/℃')
        self.assertEqual(p['阻值']['meaning'],'37.4 kΩ')
        for model in ('WR04X160FTL','WR04X1602PTL','WF04H1602JTL','WF04Z1602BTL'):
            self.assertEqual(guide.explain(self.record(model,'Walsin','WR'))['segments'],[],model)

    def test_user_yageo_rc_screenshot_includes_the_tcr_dash_not_rt_table(self):
        p=self.parts(self.record('RC0402FR-0716KL','国巨YAGEO','RC','厚膜电阻'))
        self.assertEqual(p['阻值']['meaning'],'16 kΩ')
        self.assertEqual(p['阻值误差']['meaning'],'±1%')
        self.assertEqual(p['温度系数']['code'],'-')
        self.assertIn('按规格表',p['温度系数']['meaning'])
        self.assertIn('标准功率',p['卷盘／功率']['meaning'])
        self.assertIn('默认',p['订货尾码']['meaning'])
        self.assertNotIn('无铅',p['订货尾码']['meaning'])  # L alone is not that claim.

    def test_yageo_rc_reel_power_variants_decimal_resistance_and_invalid_fields(self):
        for reel,expected in (('10','10 英寸'),('13','13 英寸'),('7W','2 倍标准功率'),
                              ('7D','2 倍标准装量'),('3W','13 英寸')):
            p=self.parts(self.record('RC0402FR-'+reel+'9K76L','YAGEO','RC'))
            self.assertEqual(p['阻值']['meaning'],'9.76 kΩ')
            self.assertIn(expected,p['卷盘／功率']['meaning'])
        p=self.parts(self.record('RC0402JR-070RL','YAGEO','RC'))
        self.assertEqual(p['阻值']['meaning'],'0 Ω')
        for model in ('RC0402FRD0716KL','RC0402FR-071602L','RC0402FS-7N16KL',
                      'RC0402FR-7D16KXL','RC9999FR-0716KL'):
            self.assertEqual(guide.explain(self.record(model,'YAGEO','RC'))['segments'],[],model)

    def test_pdc_fcf_array_is_not_a_single_resistor_package_or_e_code_series(self):
        p=self.parts(self.record('FCF240FT-163','PSA(信昌电陶)','FCF','贴片电阻'))
        self.assertIn('0402 × 4',p['结构／尺寸']['meaning'])
        self.assertIn('凸电极',p['结构／尺寸']['meaning'])
        self.assertEqual(p['阻值']['meaning'],'16 kΩ')
        self.assertIn('5000',p['包装']['meaning'])
        for model,structure in (('FCF241FT-1602','凹电极'),('FCF35RJT-103','10P8R'),
                                ('FCF370JV-000','16P8R')):
            p=self.parts(self.record(model,'信昌PDC','FCF'))
            self.assertIn(structure,p['结构／尺寸']['meaning'])
        for model in ('FCF240FT-R050E','FCF240FT-163XYZ'):
            self.assertEqual(guide.explain(self.record(model,'信昌PDC','FCF'))['segments'],[],model)
        p=self.parts(self.record('FCF02FT-1602','信昌PDC','FCF'))
        self.assertEqual(p['封装']['meaning'],'0402（英制）')
        self.assertNotIn('结构／尺寸',p)

    def test_viking_cr_dash_padding_and_0a_size_are_not_ar_codes(self):
        p=self.parts(self.record('CR-02FL6---16K','光颉Viking','CR','厚膜电阻'))
        self.assertEqual(p['阻值']['meaning'],'16 kΩ')
        self.assertEqual(p['封装']['meaning'],'0402（英制）')
        self.assertEqual(p['补位符']['code'],'---')
        self.assertIn('10000',p['包装']['meaning'])
        p=self.parts(self.record('CR-0AFH7---1R2','Viking','CR'))
        self.assertEqual(p['封装']['meaning'],'2010（英制）')
        self.assertIn('超高功率',p['功能']['meaning'])
        self.assertEqual(p['阻值']['meaning'],'1.2 Ω')
        self.assertNotIn('温度系数',p)
        for model in ('CR-02FL6--16K','CR-02FL6---160','CR-02FZ6---16K'):
            self.assertEqual(guide.explain(self.record(model,'Viking','CR'))['segments'],[],model)

    def test_new_rules_remain_brand_and_component_scoped(self):
        for model,brand in (('RC0402FR-0716KL','Walsin'),('WR04X1602FTL','YAGEO'),
                            ('FCF240FT-163','FOJAN'),('CR-02FL6---16K','Other')):
            self.assertEqual(guide.explain(self.record(model,brand))['segments'],[])
        self.assertEqual(guide.explain(self.record('WR04X1602FTL','Walsin',kind='MLCC'))['segments'],[])

    def test_koa_rn73_families_keep_termination_packaging_tolerance_and_tcr_separate(self):
        cases=[('RN73H1ETTP1200B25','120 Ω','25'),('RN73H2ATTD1003B25','100 kΩ','25'),
               ('RN73R1ETTP64R9B10','64.9 Ω','10'),('RN732ATTD16R0B25','16 Ω','25'),
               ('RN731JLTDD5102F100','51 kΩ','100')]
        for model,value,tcr in cases:
            record=self.record(model,'KOA','RN73','薄膜电阻')
            p=self.parts(record)
            self.assertEqual(p['阻值']['meaning'],value)
            self.assertEqual(p['温度系数']['meaning'],f'±{tcr} ppm/℃')
            self.assertTrue(guide.explain(record)['complete'])
        self.assertIn('10 英寸',self.parts(self.record(cases[-1][0],'KOA'))['包装']['meaning'])
        self.assertEqual(self.parts(self.record('RN73H1EGTP1200B25','KOA'))['端电极']['meaning'],'Au（金）')
        for model in ('RN73R1EGTP1200B25','RN73H2AGTD1003B25','RN73H1ETTD1200B25',
                      'RN73R1HTCM1200B25','RN73H2ATDD1003B25','RN73H2ATTD1003B99'):
            self.assertFalse(guide.explain(self.record(model,'KOA'))['complete'],model)

    def test_koa_rk73_jumper_has_no_invented_resistance_or_tolerance_digits(self):
        p=self.parts(self.record('RK73B2BTTD102J','KOA'))
        self.assertEqual(p['阻值']['meaning'],'1 kΩ')
        self.assertEqual(p['阻值误差']['meaning'],'±5%')
        p=self.parts(self.record('RK73H1EATTP1003F','KOA'))
        self.assertIn('耐热冲击',p['特性']['meaning'])
        self.assertEqual(p['阻值']['meaning'],'100 kΩ')
        p=self.parts(self.record('RK73Z1ETTP','KOA'))
        self.assertIn('零欧',p['系列']['meaning'])
        self.assertNotIn('阻值误差',p)
        for model in ('RK73Z1ETTP000J','RK73B1ETTP1003F','RK73H1EAGTP1003F'):
            self.assertEqual(guide.explain(self.record(model,'KOA'))['segments'],[],model)
        p=self.parts(self.record('RS73G1JTTD1002B','KOA'))
        self.assertEqual(p['阻值']['meaning'],'10 kΩ')
        self.assertIn('0.2 W',p['尺寸／功率']['meaning'])

    def test_vishay_crcw_and_tnpw_tcr_codes_are_not_interchangeable(self):
        p=self.parts(self.record('CRCW0402120RFKED','威世Vishay'))
        self.assertEqual(p['阻值']['meaning'],'120 Ω')
        self.assertEqual(p['温度系数']['meaning'],'±100 ppm/℃')
        self.assertIn('10000',p['包装']['meaning'])
        p=self.parts(self.record('CRCW25121M00JNEG','Vishay'))
        self.assertEqual(p['阻值']['meaning'],'1 MΩ')
        self.assertIn('8 mm',p['包装']['meaning'])
        p=self.parts(self.record('CRCW06030000Z0EA','Vishay'))
        self.assertIn('跳线',p['阻值误差']['meaning'])
        self.assertEqual(p['阻值']['meaning'],'0 Ω')
        for tcr,ppm in [('H',50),('E',25),('X',15),('Y',10)]:
            p=self.parts(self.record('TNPW04022K05B'+tcr+'ED0H','Vishay'))
            self.assertEqual(p['温度系数']['meaning'],f'±{ppm} ppm/℃')
            self.assertEqual(p['阻值']['meaning'],'2.05 kΩ')
            self.assertIn('单一批次',p['特殊选项']['meaning'])
        for model in ('CRCW0402120RFEED','CRCW0402120RFKEA','CRCW06030000FKEA',
                      'CRCW0201120RFKED','TNPW04022K05BKED','TNPW080527K4BXEC',
                      'TNPW04022K05BEEDXX'):
            self.assertEqual(guide.explain(self.record(model,'Vishay'))['segments'],[],model)

    def test_vishay_military_failure_rate_is_not_tolerance_or_lifecycle(self):
        for model,size,value,ppm in [('RNC55J1142BSB14','55','11.4 kΩ',25),
                                     ('RNC50H9880FSB14','50','988 Ω',50),
                                     ('RNC60H38R1FSRE6','60','38.1 Ω',50),
                                     ('RNR65K3014FMR64','65','3.01 MΩ',100)]:
            record=self.record(model,'威世Vishay')
            p=self.parts(record)
            self.assertEqual(p['阻值']['meaning'],value)
            self.assertEqual(p['温度系数']['meaning'],f'±{ppm} ppm/℃')
            self.assertIn('不是英制',p['军标外形']['meaning'])
            self.assertIn('1000 小时',p['失效率等级']['meaning'])
            self.assertTrue(guide.explain(record)['complete'])
        self.assertIn('热浸锡',self.parts(self.record('RNC60H38R1FSRE6201','Vishay'))['特殊选项']['meaning'])
        data=guide.explain(self.record('RNC60H38R1FSRE6999','Vishay'))
        self.assertFalse(data['complete'])
        self.assertEqual(data['verified_segments'],7)

    def test_pdc_faf_standard_function_tcr_and_special_order_codes(self):
        for model,watts,ppm,value in [('FAF01FTT1000Q','1/20',25,'100 Ω'),
                                     ('FAF06FT-1001Q','1/8',25,'1 kΩ'),
                                     ('FAF02BVA1002P','1/16',50,'10 kΩ'),
                                     ('FAF25FPH3302W','1',5,'33 kΩ')]:
            record=self.record(model,'PSA(信昌电陶)','FAF','薄膜电阻')
            p=self.parts(record)
            self.assertIn(watts+' W',p['功率']['meaning'])
            self.assertEqual(p['温度系数']['meaning'],f'±{ppm} ppm/℃')
            self.assertEqual(p['阻值']['meaning'],value)
            self.assertTrue(guide.explain(record)['complete'])
        for tail,meaning in [('M','AEC-Q200'),('-MH','氮化钽'),('MF','抗硫化'),('-HC','抗硫化')]:
            p=self.parts(self.record('FAF02BVA1002P'+tail,'信昌PDC'))
            self.assertIn(meaning,p['特殊订货类型']['meaning'])
        for model in ('FAF03BTB01BV','FAF06FT-1001Q-','FAF25FT-1001Q','FAF02BVA1002PQ'):
            self.assertEqual(guide.explain(self.record(model,'PSA'))['segments'],[],model)

    def test_full_decode_status_requires_all_segments_and_brand_and_kind_scope(self):
        for brand,model in [('Other','RN73H1ETTP1200B25'),('Vishay','FAF06FT-1001Q'),
                             ('KOA','CRCW0402120RFKED'),('PSA','RN73H1ETTP1200B25')]:
            self.assertFalse(guide.explain(self.record(model,brand))['complete'])
        for brand,model in [('KOA','RN73H1ETTP1200B25'),('Vishay','CRCW0402120RFKED'),('PSA','FAF06FT-1001Q')]:
            self.assertFalse(guide.explain(self.record(model,brand,kind='MLCC'))['complete'])
            data=guide.explain(self.record(model,brand))
            self.assertTrue(data['complete'])
            self.assertTrue(data['source_links'])
            self.assertIn('逐码解释完整',guide.guide_html(data))
        partial=guide.explain(self.record('FRH0402B4703TS'))
        self.assertFalse(partial['complete'])
        self.assertIn('尚未完整',guide.guide_html(partial))

    def test_vishay_cmf_six_character_value_and_industrial_packaging(self):
        for model,value,pack in [('CMF55499R00DHBF','499 Ω','含铅／散装'),
                                  ('CMF552K0000FKEK','2 kΩ','无铅／散装'),
                                  ('CMF55800R00BHBF','800 Ω','含铅／散装'),
                                  ('CMF55301R00FKEA','301 Ω','整盘编带')]:
            record=self.record(model,'Vishay')
            p=self.parts(record)
            self.assertEqual(p['阻值']['meaning'],value)
            self.assertIn(pack,p['包装']['meaning'])
            self.assertTrue(guide.explain(record)['complete'])
        for model in ('CMF552K0000FKEK999','CMF07100R00FKEA','CMF552K000FKEK'):
            self.assertFalse(guide.explain(self.record(model,'Vishay'))['complete'])

    def test_stackpole_rncf_tolerance_and_tcr_t_are_different_fields(self):
        cases=[('RNCF0805BTE32K0','±0.1%',25,'32 kΩ','5000'),
               ('RNCF0603TTC10K0','±0.01%',50,'10 kΩ','5000'),
               ('RNCF0805DKE174K','±0.5%',25,'174 kΩ','1000'),
               ('RNCF0402BKE61R9','±0.1%',25,'61.9 Ω','1000')]
        for model,tol,ppm,value,qty in cases:
            record=self.record(model,'Stackpole','RNCF','薄膜电阻')
            p=self.parts(record)
            self.assertEqual(p['阻值']['meaning'],value)
            self.assertEqual(p['阻值误差']['meaning'],tol)
            self.assertEqual(p['温度系数']['meaning'],f'±{ppm} ppm/℃')
            self.assertIn(qty,p['包装']['meaning'])
            self.assertTrue(guide.explain(record)['complete'])
        for model in ('RNCF0805BTE1002','RNCF0805BTT32K0XX'):
            self.assertFalse(guide.explain(self.record(model,'Stackpole'))['complete'])

    def test_pdc_thick_film_standard_and_boost_tables_do_not_merge_families(self):
        for model,watts in [('FPS06FT-3R90','1/2'),('FPS03FT-10R0-M','1/8'),
                            ('FPF25FQK4700N','3'),('FPF06FTG1001N','3/4'),
                            ('FWF02FV-1000-W','1/16'),('FCF12FT-6800P','1/3')]:
            record=self.record(model,'PSA(信昌电陶)')
            p=self.parts(record)
            self.assertIn(watts+' W',p['功率']['meaning'])
            self.assertTrue(guide.explain(record)['complete'],model)
        for model in ('FPS25FQK1001N','FPS05FTG1001N','FPF02FV-10R0',
                      'FPF06FT-R080','FCF03FT-R500','FWF02FV-1000M'):
            self.assertFalse(guide.explain(self.record(model,'PSA'))['complete'],model)
        data=guide.explain(self.record('FV31X221K202ECG','PDC','FV','MLCC'))
        self.assertNotIn('2020_3in1_catalog',repr(data['source_links']))

    def test_source_links_reject_executable_urls_and_escape_labels(self):
        data=guide.explain(self.record('CRCW0402120RFKED','Vishay'))
        data['source_links']=[('<img src=x>','https://www.vishay.com/docs/20035/dcrcwe3.pdf'),
                              ('bad','javascript:alert(1)')]
        output=guide.guide_html(data)
        self.assertNotIn('<img',output)
        self.assertNotIn('javascript:',output)
        self.assertIn('&lt;img',output)
        self.assertIn('noopener noreferrer',output)

    def test_coverage_audit_cannot_call_partial_or_selectable_brands_complete(self):
        from tools.audit_model_naming_coverage import audit
        rows=[self.record('RN73H1ETTP1200B25','KOA'),
              self.record('FRH0402B4703TS','FOJAN'),self.record('UNKNOWN','Other')]
        before=copy.deepcopy(rows)
        result=audit(rows)['summary']
        self.assertEqual((result['records'],result['complete'],result['partial'],result['unexplained']),(3,1,1,1))
        self.assertFalse(result['full_coverage'])
        self.assertEqual(rows,before)
        self.assertTrue(audit(rows[:1])['summary']['full_coverage'])
        self.assertFalse(audit([])['summary']['full_coverage'])

    def test_murata_and_samsung_use_separate_size_and_voltage_tables(self):
        m=self.parts(self.record('GRM155R71C104KA88D','村田Murata','GRM','MLCC'))
        s=self.parts(self.record('CL05B104KO5NNNC','三星Samsung','CL','MLCC'))
        self.assertIn(s['封装']['meaning'],m['封装']['meaning'])
        self.assertEqual(m['容量']['meaning'],'100 nF')
        self.assertEqual(s['额定电压']['meaning'],'16 V')
        self.assertTrue(m['厚度代码']['verified'])
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

    def test_heading_and_popover_use_content_width_not_fixed_ratio_columns(self):
        tree=ast.parse(Path(guide.__file__).read_text(encoding='utf-8'))
        render=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_render_header')
        calls=[n for n in ast.walk(render) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
               and isinstance(n.func.value,ast.Name) and n.func.value.id=='st']
        self.assertFalse(any(n.func.attr=='columns' for n in calls))
        horizontal=[n for n in calls if n.func.attr=='container' and any(k.arg=='horizontal' and ast.literal_eval(k.value) for k in n.keywords)]
        self.assertEqual(len(horizontal),1)
        self.assertEqual({k.arg:ast.literal_eval(k.value) for k in horizontal[0].keywords},
                         dict(horizontal=True,vertical_alignment='center',gap='small'))
        self.assertIn('naming-inline-title',Path(guide.__file__).read_text(encoding='utf-8'))

    def test_popover_spacing_is_scoped_and_has_no_empty_heading_marker(self):
        source=Path(guide.__file__).read_text(encoding='utf-8')
        self.assertIn('[data-testid="stPopoverBody"]:has(.naming-guide-marker)',guide.STYLE)
        self.assertIn('padding:12px 18px 16px',guide.STYLE)
        self.assertIn('[data-testid="stVerticalBlock"]{gap:12px}',guide.STYLE)
        self.assertIn('<div class="naming-guide-title naming-guide-marker">',source)
        self.assertNotIn('<span class="naming-guide-marker">',source)
        self.assertNotIn('naming-guide-sub',source)
        self.assertNotIn('仅展示本次匹配出现的品牌与系列；点击面板外部即可关闭。',source)


class NamingGuideUITests(unittest.TestCase):
    def test_direct_mlcc_header_keeps_results_and_separate_instances(self):
        from streamlit.testing.v1 import AppTest
        script='''
import streamlit as st
from model_naming_guide import render_part_header
st.session_state['parent_runs']=st.session_state.get('parent_runs',0)+1
source=[dict(品牌='太阳诱电Taiyo',型号='MEASJ063BB5225M',系列='MEASJ',器件类别='MLCC',成本=123,username='SECRET')]
matched=[dict(品牌='华新科Walsin',型号='0201X225M6R3CT',系列='常规',器件类别='MLCC',成本=456)]
render_part_header('匹配料号资料 · MEASJ063BB5225M',source,matched,'direct')
render_part_header('匹配料号资料 · 仅原厂',source,[],'source_only')
st.caption('原匹配结果仍在')
'''
        at=AppTest.from_string(script).run(timeout=30)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['parent_runs'],1)
        self.assertEqual(at.selectbox[1].value,'MEASJ063BB5225M')
        self.assertEqual(at.selectbox[3].value,'MEASJ063BB5225M')
        self.assertEqual(set(at.selectbox[0].options),{'太阳诱电Taiyo · MEASJ（1 个型号）','华新科Walsin · 常规（1 个型号）'})
        self.assertTrue(any('6.3 VDC' in m.value for m in at.markdown))
        self.assertNotIn('SECRET',''.join(m.value for m in at.markdown))
        at.selectbox[0].select(('华新科Walsin','常规')).run(timeout=30)
        self.assertFalse(at.exception)
        self.assertEqual(at.selectbox[1].value,'0201X225M6R3CT')
        self.assertTrue(any('Cu / Ni / Sn' in m.value for m in at.markdown))
        # AppTest.run() reruns the full test script. The actual fragment-only
        # widget event is checked in the real-browser preview, not simulated here.
        self.assertTrue(any('原匹配结果仍在' in m.value for m in at.caption))

    def test_different_specs_models_and_multiple_placeholders_keep_content_width(self):
        from streamlit.testing.v1 import AppTest
        script='''
import streamlit as st
from model_naming_guide import render_header
st.session_state['parent_runs']=st.session_state.get('parent_runs',0)+1
st.session_state['heading_layouts']=[]
st.session_state['heading_widths']=[]
original_container,original_markdown=st.container,st.markdown
def recorded_container(*args,**kwargs):
    if kwargs.get('horizontal'):
        st.session_state['heading_layouts'].append(kwargs)
    return original_container(*args,**kwargs)
def recorded_markdown(body,*args,**kwargs):
    if 'class="section-title naming-inline-title"' in str(body):
        st.session_state['heading_widths'].append(kwargs.get('width'))
    return original_markdown(body,*args,**kwargs)
st.container,st.markdown=recorded_container,recorded_markdown
cases=[
 ('贴片电阻（Chip Resistor）规格条件','FOJAN(富捷)','FRC0402J103TS','FRC','厚膜电阻'),
 ('贴片电阻（Chip Resistor）规格条件','FOJAN(富捷)','FRC0402F1602TS','FRC','厚膜电阻'),
 ('陶瓷贴片电容（MLCC）规格条件','信昌PDC','FV31X221K202ECG','FV','MLCC'),
 ('料号片段反推规格','FOJAN(富捷)','FPM253WFR300TM','FPM','合金电阻'),
 ('共模电感（Common Mode Choke）规格条件','Test','REAL-INPUT-ROW','Test','共模电感'),
 ('长标题：规格与型号混合的多条搜索结果 · 陶瓷贴片电容（MLCC）规格条件','村田Murata','GRM155R71C104KA88D','GRM','MLCC')]
try:
    for index,(title,brand,model,series,kind) in enumerate(cases):
        placeholder=st.empty()
        placeholder.markdown('<div class="section-title">'+title+'</div>',unsafe_allow_html=True)
        rows=[dict(品牌=brand,型号=model,系列=series,器件类别=kind)]
        if index==0:
            rows.append(dict(品牌='PSA(信昌电陶)',型号='FPF02JV-103',系列='FPF',器件类别='厚膜电阻'))
        with placeholder.container():
            render_header(title,rows,'variant_'+str(index))
finally:
    st.container,st.markdown=original_container,original_markdown
'''
        at=AppTest.from_string(script).run(timeout=30)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['parent_runs'],1)
        self.assertEqual(at.session_state['heading_widths'],['content']*6)
        self.assertEqual(at.session_state['heading_layouts'],
                         [dict(horizontal=True,vertical_alignment='center',gap='small')]*6)
        self.assertEqual(len(at.selectbox),12)
        self.assertEqual(at.selectbox[1].value,'FRC0402J103TS')

    def test_older_streamlit_without_horizontal_container_keeps_accessible_popover(self):
        from streamlit.testing.v1 import AppTest
        script='''
import streamlit as st
from model_naming_guide import render_header
original=st.container
def legacy_container(**kwargs):
    if 'horizontal' in kwargs:
        raise TypeError('unexpected keyword horizontal')
    return original(**kwargs)
st.container=legacy_container
try:
    render_header('规格条件',[dict(品牌='华新科Walsin',型号='WR04X1602FTL',系列='WR',器件类别='厚膜电阻')],'legacy')
finally:
    st.container=original
'''
        at=AppTest.from_string(script).run(timeout=20)
        self.assertFalse(at.exception)
        self.assertEqual(at.selectbox[1].value,'WR04X1602FTL')
        self.assertTrue(any('16 kΩ' in item.value for item in at.markdown))

    def test_popover_has_only_real_result_options_and_model_specific_tables(self):
        from streamlit.testing.v1 import AppTest
        script='''
import streamlit as st
from model_naming_guide import render_header
st.session_state['parent_runs']=st.session_state.get('parent_runs',0)+1
rows=[dict(品牌='FOJAN(富捷)',型号='FRH0402B4703TS',系列='FRH',器件类别='厚膜电阻'),
      dict(品牌='光颉Viking',型号='AR02BTC4703',系列='AR',器件类别='薄膜电阻'),
      dict(品牌='华新科Walsin',型号='WR04X1602FTL',系列='WR',器件类别='厚膜电阻'),
      dict(品牌='国巨YAGEO',型号='RC0402FR-0716KL',系列='RC',器件类别='厚膜电阻')]
render_header('贴片电阻（Chip Resistor）规格条件',rows,'fixture')
st.caption('原匹配结果仍在')
'''
        at=AppTest.from_string(script).run(timeout=20)
        self.assertFalse(at.exception)
        self.assertEqual(len(at.selectbox),2)
        self.assertEqual(at.selectbox[1].value,'FRH0402B4703TS')
        self.assertTrue(any('470 kΩ' in item.value for item in at.markdown))
        self.assertTrue(any('<div class="naming-guide-title naming-guide-marker">型号命名对照</div>'==item.value for item in at.markdown))
        self.assertNotIn('点击面板外部即可关闭',''.join(item.value for item in at.markdown))
        self.assertTrue(any('尚未完整' in item.value or '逐码解释完整' in item.value for item in at.markdown))
        at.selectbox[0].select(('光颉Viking','AR')).run(timeout=20)
        self.assertFalse(at.exception)
        self.assertEqual(at.selectbox[1].value,'AR02BTC4703')
        self.assertTrue(any('±25 ppm/℃' in item.value for item in at.markdown))
        self.assertTrue(any('原匹配结果仍在' in item.value for item in at.caption))
        for brand,series,model,source in (('华新科Walsin','WR','WR04X1602FTL','ASC_WR_V23'),
                                          ('国巨YAGEO','RC','RC0402FR-0716KL','2025-11-14 V.14')):
            at.selectbox[0].select((brand,series)).run(timeout=20)
            self.assertFalse(at.exception)
            self.assertEqual(at.selectbox[1].value,model)
            self.assertTrue(any('16 kΩ' in item.value and source in item.value for item in at.markdown))
