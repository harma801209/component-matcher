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
from amotech_catalog import BRAND, cap_pf, decode_standard, TOLERANCE


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


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--captures',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'catalog_sources/amotech_verified.json')
    args=parser.parse_args()
    data=build(args.captures)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'models':len(data['records']),'quarantined':len(data['quarantined']),
                      'series':dict(Counter(r['系列'] for r in data['records']))},ensure_ascii=False))
