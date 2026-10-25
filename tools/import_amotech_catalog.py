"""Reproduce a reviewed AMOTECH catalogue snapshot from public DOM exports.

Input files are captured using the official rendered product-search UI, not a
private API. PDF table extracts are from the cited manufacturer-authored files.
This script writes only the named JSON source asset; never any runtime DB.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from amotech_catalog import BRAND, cap_pf, decode_standard, TOLERANCE, HIGH_Q


def build_high_q(folder):
    rules = {}
    for name, inch, metric, voltage in (
        ('a60z','0201','0603',200), ('a60l','0402','1005',200),
        ('a60s','0603','1608',250), ('a60f','0805','2012',250),
        ('a80b','1111','2828',None),
    ):
        pages = json.loads((folder/(name+'-tables.json')).read_text(encoding='utf-8'))
        page = next(p for p in pages if p['page'] == (5 if name == 'a80b' else 4))
        table = page['tables'][-1]
        if name == 'a60z':
            # Poppler/pdfplumber finds three distinct side-by-side tables here.
            tables = [t for t in page['tables'] if t[0] == ['Value [pF]','Cap Code','Tolerance']]
            table = [tables[0][0]] + [row for t in tables for row in t[1:]]
        caps = {}
        if name != 'a80b':
            header = table[0]
            for start, cell in enumerate(header):
                if not cell or not cell.startswith('Value'):
                    continue
                tol_col = next(i for i in range(start+2,len(header)) if header[i] == 'Tolerance')
                for row in table[1:]:
                    values = (row[start] or '').splitlines()
                    codes = (row[start+1] or '').splitlines()
                    tolerances = (row[tol_col] or '').splitlines()
                    assert len(values) == len(codes) == len(tolerances)
                    for value,code,tol in zip(values,codes,tolerances):
                        assert abs(cap_pf(code)-float(value)) < 1e-8
                        caps[code] = {'pf':float(value),'tolerances':tol.split(','),'voltages':[voltage]}
        else:
            # This table's merged cells apply downwards within each 5-column
            # block. STD and EXT are distinct allowed orderable voltage options.
            for start in (0,5,10,15):
                previous = [None]*5
                for row in table[6:]:
                    cells = row[start:start+5]
                    if not cells or not cells[0] or not re.fullmatch(r'\d+(?:\.\d+)?',cells[0]):
                        continue
                    previous = [value if value is not None else old for value,old in zip(cells,previous)]
                    value,code,tol,std,ext = previous
                    assert abs(cap_pf(code)-float(value)) < 1e-8
                    caps[code] = {'pf':float(value),'tolerances':re.sub(r'\s','',tol).split(','),
                                  'voltages':[int(std.rstrip('V')),int(ext.rstrip('V'))]}
        source = next(x for x in json.loads((folder/'manifest.json').read_text(encoding='utf-8')) if x['name'] == name)
        rules[name.upper()] = {'inch':inch,'metric':metric,'source_url':source['url'],
                               'source_sha256':source['sha256'],'capacitances':caps}
    return rules


def build(qa):
    records, quarantined, sources = {}, [], []
    for file in ('amotech-official-mlcc-rows.json','amotech-official-broadband-rows.json'):
        raw = json.loads((qa/file).read_text(encoding='utf-8'))
        sources.append({'url':raw['url'],'category':raw.get('category','Multilayer Ceramic Capacitors'),
                        'retrieved':raw['retrieved'],'captured_rows':len(raw['rows']),
                        'capture_sha256':hashlib.sha256((qa/file).read_bytes()).hexdigest()})
        for cells in raw['rows']:
            model = re.sub(r'\s','',cells[0]).upper()
            inch,metric = cells[1].split('/')
            value,unit = cells[2].split()
            value_pf = float(value)*{'pF':1,'nF':1000,'uF':1e6}[unit]
            cap_code = re.search(r'([0-9R]{3})([A-Z])[NFGMWV][BDJLKT][ACG]$',model)
            assert cap_code and cap_pf(cap_code[1]) == value_pf, model
            tol = re.fullmatch(r'([A-Z])\((\d+(?:\.\d+)?)(%|pF)\)',cells[3])
            assert tol, cells[3]
            if tol[1] != cap_code[2]:
                quarantined.append({'model':model,'reason':'原厂选型表容差与料号编码不一致',
                                    'encoded_tolerance':TOLERANCE[cap_code[2]],'displayed_tolerance':cells[3],
                                    'source_url':raw['url']})
                continue
            row = decode_standard(model) if model.startswith('AC') else {}
            row = row or {'品牌':BRAND,'型号':model,'器件类型':'MLCC','安装方式':'贴片'}
            series = cells[0].split()[0]
            broadband = model.startswith('ABCU')
            feature_map = {'ST':'软端子','MF':'金属框架','Op':'Open mode',
                           'FI':'Floating design','LP':'低外形','HF':'高频'}
            features = [feature_map[v] for v in cells[7].splitlines() if v in feature_map]
            if broadband:
                features.append('宽带')
            if cells[9] == 'AEC-Q200':
                features.append('车规 AEC-Q200')
            row.update({'品牌':BRAND,'型号':model,'系列':series,
                        '系列说明':f"AMOTECH {cells[5]} {'宽带电容' if broadband else 'MLCC'}",
                        '特殊用途':' | '.join(features),'尺寸（inch）':inch,'尺寸（mm）':metric,
                        '容值':value_pf,'容值单位':'pF','容值误差':tol[2]+('pF' if tol[3]=='pF' else ''),
                        '耐压（V）':float(cells[4]),'材质（介质）':cells[5],
                        '工作温度':cells[6].replace('℃','').replace('+','')+'℃',
                        '生产状态':'','_model_rule_authority':'amotech_official_catalogue',
                        '_catalog_membership':'manufacturer_listed','_amotech_source_url':raw['url'],
                        '备注1':f"AMOTECH 原厂选型工具，核对于 {raw['retrieved']}：{raw['url']}",
                        '备注2':'宽带／微波用途必须另外核验 S 参数、插入损耗、回波损耗及频段。' if broadband else ''})
            assert model not in records
            records[model] = row
    # Exact legacy models from manufacturer-authored individual datasheets.
    manifest = json.loads((qa/'amotech-sources/manifest.json').read_text(encoding='utf-8'))
    for name,model,inch,metric,volt,tol,high,material,frequency in (
        ('abcua06','ABCUA06F0XX104MNDG','01005','0402',6.3,'20',85,'宽带专用介质（F）','16kHz～40GHz+'),
        ('abcua','ABCUA10201X104KNDG','0201','0603',10,'10',125,'宽带专用介质（2）','16kHz～40GHz+'),
        ('abcub','ABCUB10201X104KNDG','0201','0603',10,'10',125,'宽带专用介质（2）','16kHz～56GHz+'),
    ):
        source = next(x for x in manifest if x['name']==name)
        assert source.get('sha256')
        records[model] = {'品牌':BRAND,'型号':model,'器件类型':'MLCC','系列':model[:5],
                          '系列说明':'AMOTECH 宽带微波电容','特殊用途':'宽带 | 高频',
                          '安装方式':'贴片','尺寸（inch）':inch,'尺寸（mm）':metric,
                          '容值':100000,'容值单位':'pF','容值误差':tol,'耐压（V）':volt,
                          '材质（介质）':material,'工作温度':'','生产状态':'',
                          'TCC测试温区':f'-55~{high}℃',
                          '_model_rule_authority':'amotech_official_datasheet',
                          '_catalog_membership':'manufacturer_listed','_amotech_source_url':source['url'],
                          '备注1':f"AMOTECH 原厂规格书：{source['url']}；典型频段 {frequency}，以原厂测试条件为准；TCC测试温区保存于独立字段，不据此推定完整额定工作温度。",
                          '备注2':'宽带／微波用途必须另外核验 S 参数、插入损耗、回波损耗及频段；不能仅按容量、耐压认定等效。'}
    return {'schema_version':1,'reviewed_at':'2026-10-24','manufacturer':'AMOTECH',
            'policy':'Actual listed model records only. No Cartesian generation; no assumed price, stock, lifecycle or certification.',
            'sources':sources+manifest,'records':list(records.values()),'quarantined':quarantined,
            'high_q_rules':build_high_q(qa/'amotech-sources')}


def extend_listed_high_q(data,folder,listings_file=ROOT/'catalog_sources/amotech_highq_listings.json'):
    """Cross-check finite listed identities, never enumerate rule combinations.

    Public channel pages establish only that the exact identity was listed.
    All electrical fields come from the separately hashed manufacturer PDF.
    Keep this evidence class distinct from manufacturer-listed catalogue rows.
    """
    listing=json.loads(listings_file.read_text(encoding='utf-8'))
    identities={}
    for group in listing['groups']:
        for model in group['models']:
            assert re.fullmatch(r'[A-Z0-9]+',model),model
            identities.setdefault(model,[]).append(group['url'])
    manifests=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    dimensions={
        'A60Z':(.6,.3,'L 0.6±0.03mm；W 0.3±0.03mm；T 0.3±0.03mm'),
        'A60L':(1,.5,'L 1.0±0.10mm；W 0.5±0.10mm；T ≤0.6mm'),
        'A60S':(1.6,.8,'L 1.6±0.15mm；W 0.8±0.15mm；T ≤0.89mm'),
        'A60F':(2,1.24,'L 2.0±0.20mm；W 1.24±0.20mm；T ≤1.3mm'),
        'A80B':(2.79,2.79,'L 2.79 +0.51/-0.25mm；W 2.79±0.38mm；T ≤1.78mm'),
    }
    for series,rule in data['high_q_rules'].items():
        actual=hashlib.sha256((folder/(series.lower()+'.pdf')).read_bytes()).hexdigest()
        assert actual==rule['source_sha256'],series
    existing={r['型号'] for r in data['records']}
    pending=[]
    for model,urls in sorted(identities.items()):
        match=HIGH_Q.fullmatch(model)
        if not match:
            pending.append({'model':model,'reason':'完整写法不符合已核验原厂订货结构；可能为旧别名或缺包装后缀，不自动补T或改型号',
                            'listing_urls':urls})
            continue
        g=match.groupdict()
        rule=data['high_q_rules'][g['series']]
        allowed=rule['capacitances'].get(g['cap'])
        if not allowed or g['tol'] not in allowed['tolerances'] or int(g['voltage']) not in allowed['voltages'] or (g['laser'] and g['series'] in {'A60Z','A60L'}):
            pending.append({'model':model,'reason':'渠道列出身份，但容量／容差／工作电压／标记选项未通过原厂参数矩阵核对',
                            'listing_urls':urls})
            continue
        if model in existing:
            continue
        length,width,body=dimensions[g['series']]
        revision={'A60Z':'03','A60L':'04','A60S':'06','A60F':'04','A80B':'05'}[g['series']]
        row={'品牌':BRAND,'型号':model,'器件类型':'MLCC','系列':g['series'],
             '系列说明':'高Q／低损耗 RF／微波电容','特殊用途':'高Q | 低损耗',
             '安装方式':'贴片','尺寸（inch）':rule['inch'],'尺寸（mm）':rule['metric'],
             '长度（mm）':f'{length:g}','宽度（mm）':f'{width:g}',
             '容值':allowed['pf'],'容值单位':'pF','容值误差':TOLERANCE[g['tol']],
             '耐压（V）':int(g['voltage']),'材质（介质）':'C0G','工作温度':'-55~125℃',
             '生产状态':'','资料版本':f'2021-07-13 Rev.{revision}',
             '资料状态':'公开渠道列出完整型号，原厂系列规格交叉核验；供货与生产状态待核验',
             '型号来源':'渠道目录与原厂规格书交叉核验','Q值及测试条件':'≥2000 @1MHz',
             '尺寸说明':body,'端子材料':'Sn/Ni' if g['terminal']=='T' else 'Sn／非磁性阻挡层',
             '包装':'编带','激光标记':'有' if g['laser'] else '无X标记',
             '备注1':f"电性参数依据原厂 Rev.{revision} 第3页及容量表第{'5' if g['series']=='A80B' else '4'}页：{rule['source_url']}；{body}；型号列出来源："+'；'.join(urls),
             '备注2':'渠道列出不等于原厂当前可订购、量产、认证或有价；高Q替代须另外核验Q、ESR、频段与端子，不能仅按基本规格认定完全替代。',
             '_catalog_membership':'cross_verified_listed','_model_rule_authority':'amotech_official_datasheet_channel_identity',
             '_amotech_source_url':rule['source_url'],'_source_sha256':rule['source_sha256'],
             '_source_pages':[2,3,5 if g['series']=='A80B' else 4],
             '_identity_source_urls':urls,'_identity_reviewed_at':listing['reviewed_at']}
        if g['series']=='A60Z':
            row['厚度（mm）']='0.3'
        else:
            row['厚度上限（mm）']={'A60L':.6,'A60S':.89,'A60F':1.3,'A80B':1.78}[g['series']]
        data['records'].append(row)
        existing.add(model)
    data['pending_high_q_listings']=pending
    data['sources'].append({'kind':'channel_identity_crosschecked_manufacturer_pdf',
                            'reviewed_at':listing['reviewed_at'],
                            'identity_manifest_sha256':hashlib.sha256(listings_file.read_bytes()).hexdigest(),
                            'listing_urls':[g['url'] for g in listing['groups']],
                            'policy':listing['policy']})
    data['reviewed_at']=listing['reviewed_at']
    data['schema_version']=4
    return data


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--captures',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'catalog_sources/amotech_verified.json')
    args=parser.parse_args()
    data=build(args.captures)
    if not (args.captures/'amotech-official-rf-rows.json').exists():
        raise SystemExit('Missing reviewed RF capture; refusing to silently shrink the published electronic-component catalogue.')
    from import_amotech_electronics import extend
    data=extend(data,args.captures)
    data=extend_listed_high_q(data,args.captures/'amotech-sources')
    assert len({r['型号'] for r in data['records']}) == len(data['records'])
    assert all('(cid:' not in str(r) for r in data['records']), 'Unresolved PDF glyph in source record'
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'models':len(data['records']),'quarantined':len(data['quarantined']),
                      'series':dict(Counter(r['系列'] for r in data['records']))},ensure_ascii=False))
