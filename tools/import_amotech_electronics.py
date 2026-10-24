"""Reviewed actual electronic-component records, never generated combinations.

Inputs: rendered official RF table capture and manufacturer PDF table/text
extracts. The historical EMI/ESD catalogue is explicitly dated 2008; catalogue
presence does not imply current availability or lifecycle. No database writes.
"""
import json
import re
from amotech_catalog import BRAND, LEGACY_SOURCE, EXISTING_PROTECTION_MODELS


def decode_font(text):
    return re.sub(r'\(cid:(\d+)\)',lambda m:chr(int(m[1])+31) if int(m[1])<128 else {130:'±',291:'<',643:'Ω'}.get(int(m[1]),m[0]),text).replace('¡','±')


def build_historical(folder):
    pages = json.loads((folder/'emc2008-tables.json').read_text(encoding='utf-8'))
    # Only the actual Electrical Characteristics rows on visually reviewed
    # pages. Ordering examples, curves, applications and dimensions don't add
    # additional model identities.
    patterns = {
        6:r'(ASES)\s+12U\s+(02|03)\s+0R2',
        8:r'(AMES)\s+12U\s+05Q\s+0R2',
        12:r'(ADUC|ADMC)\s+(?:10|30|5)[SM]\s+(02|03)\s+[0-9R]{3}',
        16:r'(SR|SF)\s+5S\s+02\s+[0-9]{3}(?:\s+[0-9]{3}R)?',
        19:r'(AVLC)\s+(?:10|5)S\s+01\s+[0-9]{3}',
        22:r'(AVL|AVLC)\s+(?:5|14|15|18)[MKS]\s+(02|03)\s+[0-9]{3}(?:\s+LC(?:75|120))?',
        24:r'(AVNC)\s+(?:5|14|18)S\s+(03|05)Q\s+[0-9]{3}',
        26:r'(AVSC)\s+(?:5|14|18)S\s+(04F|05E)\s+[0-9]{3}',
        30:r'(AMLV)\s+14S\s+03Q\s+[0-9]{3}\s+[0-9]{3}F',
        33:r'(AVRC)\s+(?:5|14|18)S\s+(03|05)Q\s+[0-9]{3}\s+[0-9]{3}R',
        39:r'(AVRC)\s+(?:5|14|18)S\s+04D\s+[0-9]{3}\s+[0-9]{3}R',
        42:r'(AVFC)\s+(?:5|14|18)S\s+(03|05)Q\s+[0-9]{3}',
        45:r'(AVFC)\s+5S\s+04D\s+150',
    }
    records,quarantined=[],[]
    seen=set()
    for page in pages:
        number=page['page']
        if number not in patterns:
            continue
        text=decode_font(page['text']).split('Dimension Specification')[0]
        for line in text.splitlines():
            match=re.match(patterns[number],line)
            if not match:
                continue
            model=re.sub(r'\s','',match[0])
            if model in seen or model in EXISTING_PROTECTION_MODELS:
                continue
            seen.add(model)
            if model in {'AVLC15S02036','AVFC5S04D150'}:
                detail = ('编码末尾036与电气表33pF不一致' if model.startswith('AVLC') else
                          '订货编码150与电气表100pF不一致，且订货页对C1+C2定义不同')
                quarantined.append({'model':model,'kind':'ESD保护器件' if model.startswith('AVLC') else 'EMI／ESD滤波器',
                                    'detail':detail,'source_url':LEGACY_SOURCE,'pdf_page':number})
                continue
            family=match[1]
            emi=family in {'SR','SF','AMLV','AVRC','AVFC'}
            voltage_code=re.search(r'^(?:ASES|AMES|ADUC|ADMC|AVLC|AVL|AVNC|AVSC|SR|SF|AMLV|AVRC|AVFC)(\d+)[USMK]',model)[1]
            voltage = 5.5 if voltage_code=='5' else float(voltage_code)
            size_code=re.search(r'[USMK](0[1-5])',model)[1]
            size={'01':'0201','02':'0402','03':'0603','04':'0504','05':'0805'}[size_code]
            body={'01':'.60 × .30','02':'1.0 × .5','03':'1.6 × .8','04':'1.4 × .9','05':'2.05 × 1.25'}[size_code]
            if family=='AMES':
                size,body='','2.5 × 1.0'
            row={'品牌':BRAND,'型号':model,'器件类型':'EMI／ESD滤波器' if emi else 'ESD保护器件',
                 '系列':family,'安装方式':'贴片','尺寸（inch）':size,'本体尺寸（mm）':body,
                 '最大连续工作电压（V）':voltage,'生产状态':'',
                 '资料版本':f'2008 EMI/ESD目录，印刷页{number-1}／PDF页{number}',
                 '资料状态':'历史目录；当前供货及生产状态待核验','官网链接':LEGACY_SOURCE,
                 '_amotech_source_url':LEGACY_SOURCE,'_amotech_source_page':number,
                 '_catalog_membership':'manufacturer_listed','_model_rule_authority':'amotech_historical_catalogue',
                 '_manual_equivalence_required':True}
            structure={'ASES':'单通道聚合物ESD抑制器','AMES':'四通道聚合物ESD抑制器',
                       'ADUC':'低寄生电容金属氧化物保护器件','ADMC':'金属氧化物保护器件',
                       'AVL':'多层片式压敏电阻','AVLC':'低寄生电容片式压敏电阻',
                       'AVNC':'四元件阵列压敏电阻','AVSC':'紧凑阵列压敏电阻',
                       'SR':'单通道RC保护网络','SF':'单通道穿心保护网络',
                       'AMLV':'四通道LC EMI/ESD网络','AVRC':'RC EMI/ESD网络','AVFC':'穿心EMI/ESD网络'}[family]
            row['结构']=structure
            row['回路数']='8' if family=='AVSC' and size_code=='05' else '2' if '04D' in model else '4' if family in {'AMES','AVNC','AVSC','AMLV','AVRC','AVFC'} else '1'
            tail=line[match.end():].strip()
            if family in {'ASES','AMES'}:
                row.update({'寄生电容量（pF）':.2,'电容定义／测试条件':'Cp：1MHz；0.2pF典型／0.3pF最大',
                            '工作温度':'-40~85℃','压敏／击穿电压及条件':'触发Vt：100V典型；不是连续工作电压',
                            '电气参数说明':'VC_ESD：65V典型／100V最大；IL@12Vdc：0.1nA典型；IEC61000-4-2接触8kV／空气15kV典型。详见原表测试条件。'})
            else:
                # Keep raw condition-bearing facts, including limits and
                # tolerances, rather than stripping symbols into false ratings.
                headings={
                    12:'Vdc(V)；Vn@1mA DC(V)；Cp@1MHz/0.5Vrms(pF)；IL@Vdc(µA)；IR@3.6Vdc(MΩ)',
                    16:'Vdc(V)；Vn@1mA DC(V)；Rdc(Ω)；Rdc容差(%)；Cp@1MHz/0.5Vrms(pF)；Cp容差(%)；IR@3.6Vdc(MΩ)（SF无Rdc两列）',
                    19:'Vdc(V)；Vn@1mA DC(V)；Cp@1kHz/0.5Vrms(pF)；IL@Vdc(µA)；IR@3.6Vdc(MΩ)',
                    22:'Vdc(V)；Vn@1mA DC(V)；IL@Vdc(µA)；Cp@1kHz/0.5Vrms(pF)；VC(V)；Imax(A)；Wmax(J)；IR@3.6V(MΩ)',
                    24:'Vdc(V)；Vn@1mA DC(V)；Cp@1kHz/0.5Vrms(pF)；VC(V)；Imax(A)；Wmax(J)；IR@3.6V(MΩ)',
                    26:'Vdc(V)；Vn(V)；响应(ns)；Cp@1MHz(pF)；Cp容差(%)；IR（原表单位Ω）',
                    30:'Vdc(V)；Vn@1mA DC(V)；Cp@1MHz/0.5Vrms(pF)；Cp容差(%)；IR@3V(MΩ)；截止-3dB(MHz)；最低-20dB衰减带(MHz)',
                    33:'Vdc(V)；Vn@1mA DC(V)；Rdc(Ω)；Rdc容差(%)；C1+C2@1MHz/0.5Vrms(pF)；Cp容差(%)；IR@3V(MΩ)；截止-3dB(MHz)；最低-20dB衰减带(MHz)',
                    39:'Vdc(V)；Vn@1mA DC(V)；Rdc(Ω)；Rdc容差(%)；C1+C2@1kHz/0.5Vrms(pF)；Cp容差(%)；IR@3V(MΩ)；截止-3dB(MHz)；最低-20dB衰减带(MHz)',
                    42:'Vdc(V)；Vn@1mA DC(V)；Cp@1MHz/0.5Vrms(pF)；Cp容差(%)；IR@3V(MΩ)；截止-3dB(MHz)；最低-20dB衰减带(MHz)',
                }
                row['电气参数说明']='原表列顺序：'+headings[number]+'\n原表列值：'+tail
                if family=='AVL':
                    cap={'AVL5M02200':480,'AVL14K02200':160,'AVL5M03300':800,'AVL14K03300':350,
                         'AVL18S03300LC75':75,'AVL18S03300LC120':120}[model]
                elif family in {'SR','AVRC'}:
                    cap=int(model[-7:-4])
                    row['串联电阻（Ω）']=int(model[-4:-1])
                elif family=='AMLV':
                    cap=int(model[-7:-4])
                else:
                    code=model[-3:]
                    cap=float(code.replace('R','.'))
                row['寄生电容量（pF）']=cap
                freq='1MHz' if family in {'ADUC','ADMC','AVSC','SR','SF','AMLV','AVRC','AVFC'} and number!=39 else '1kHz'
                if family in {'SR','AVRC'}:
                    definition='C1+C2合计；不是单个支路电容'
                else:
                    definition='Cp标称／典型；范围及容差见原表'
                row['电容定义／测试条件']=definition+'；'+freq+('，0.5Vrms' if family not in {'AVSC'} else '')
                if family=='AMLV':
                    row['截止频率（MHz）']=int(model[-4:-1])
                elif family in {'AVRC','AVFC'}:
                    cutoff=re.search(r'>\s*10\s+(\d+)\s+\d+~\d+$',tail)
                    assert cutoff, (model,tail)
                    row['截止频率（MHz）']=int(cutoff[1])
                # Breakdown/varistor voltage always retains its test current.
                vn=re.match(r'\s*[\d.]+\s*(?:max\.)?\s+(.+?)\s+(?:Max\.|max\.|\d+\s*(?:±30|\())',tail)
                if family in {'SR','SF','AMLV','AVRC','AVFC'}:
                    vn=re.search(r'^\s*[\d.]+\s+([\d.]+±[\d.]+)',tail)
                    if vn:row['压敏／击穿电压及条件']=vn[1]+' V @1mA DC'
            records.append(row)
    return records,quarantined


def flatten_table(table):
    return '\n'.join(' | '.join((c or '').replace('\n',' / ') for c in row) for row in table if any(row))


def rf_electrical_table(page):
    return next(t for t in page['tables'] if 'Frequency' in flatten_table(t) and
                any(re.search(r'\d+\s*~\s*\d+',r[0] or '') for r in t))


def readable_rf_table(model,table):
    if model=='CXH03F1723AG':
        return '1700～2300MHz：幅度平衡Max ±0.3dB；插损Max 0.25dB；回损Min 21dB；隔离Min 20dB；相位90±4°；平均功率40W；工作温度-55～125℃。'
    start=next(i for i,r in enumerate(table) if re.search(r'\d+\s*~\s*\d+',r[0] or ''))
    headers=[' '.join(str(r[c] or '').replace('\n',' ').strip() for r in table[:start] if r[c]).strip() for c in range(len(table[start]))]
    result=[]
    for row in table[start:]:
        bands=re.findall(r'(\d+)\s*~\s*(\d+)',row[0] or '')
        for index,(low,high) in enumerate(bands):
            facts=[]
            for c in range(1,len(row)):
                values=(row[c] or '').splitlines()
                assert len(values) in (0,1,len(bands)), (model,c,values)
                if values:
                    facts.append(headers[c]+': '+values[0 if len(values)==1 else index])
            result.append(f'{low}～{high}MHz；'+'；'.join(facts))
    return '\n'.join(result)


def build_rf(qa):
    folder=qa/'amotech-sources'
    capture=json.loads((qa/'amotech-official-rf-rows.json').read_text(encoding='utf-8'))
    manifest=json.loads((folder/'rf-manifest.json').read_text(encoding='utf-8'))
    records=[]
    for table in capture['tables']:
        for item in table[1:]:
            model=re.sub(r'\s','',item['cells'][0])
            source=next(s for s in manifest if s['model']==model)
            assert source.get('sha256'),source
            pages=json.loads((folder/(model+'-tables.json')).read_text(encoding='utf-8'))
            page=next(p for p in pages if p['page'] not in (3,4))
            electrical=rf_electrical_table(page)
            pinpage=next(p for p in pages if p['page']==4)
            text=(folder/(model+'.txt')).read_text(encoding='utf-8')
            revision=re.search(r'Rev\.\s*([\w.]+)',text)[1]
            # Read ranges only from the actual specification table, never the
            # wider axes of plots or four digits in the model code.
            bands=[]
            for row in electrical:
                if row and row[0]:
                    bands.extend((int(a),int(b)) for a,b in re.findall(r'(\d+)\s*~\s*(\d+)',row[0]))
            assert bands,model
            temperature=re.search(r'-55\s*~\s*(125|140)',flatten_table(electrical))
            shape=model[5]
            inch={'T':'0805','F':'2013','S':'2520'}[shape]
            row={'品牌':BRAND,'型号':model,'器件类型':'RF耦合器','系列':model[:3],
                 '结构':'90°混合耦合器' if '90-Degree Hybrid' in text[:300] else '定向耦合器',
                 '安装方式':'贴片','尺寸（inch）':inch,'标称耦合（dB）':int(model[3:5]),
                 '频段下限（MHz）':min(a for a,b in bands),'频段上限（MHz）':max(b for a,b in bands),
                 '分段电气参数':readable_rf_table(model,electrical),
                 '已列频段（MHz）':'；'.join(f'{a}～{b}' for a,b in bands),
                 '功率条件':'详见分段原表；Avg与Max定义不得混用，按温度降额；频段上下限不代表中间所有频点均有保证',
                 '引脚／端口':flatten_table(pinpage['tables'][1]) if len(pinpage['tables'])>1 else '详见原厂规格书第4页',
                 '工作温度':f'-55~{temperature[1]}℃' if temperature else '',
                 '资料版本':f'原厂具体型号规格书 Rev.{revision}，电气参数第{page["page"]}页',
                 '资料状态':'Preliminary（规格书标识；不是NRND或生产状态）' if 'Preliminary' in text else '原厂规格书；生产状态待核验',
                 '生产状态':'','官网链接':source['url'],'_amotech_source_url':source['url'],
                 '_amotech_source_page':page['page'],'_source_electrical_table':electrical,
                 '_source_band_segments':bands,'_source_sha256':source['sha256'],
                 '_manual_equivalence_required':True,'_catalog_membership':'manufacturer_listed',
                 '_model_rule_authority':'amotech_official_datasheet'}
            # Retain the power meaning as text with its original header. Avoid
            # inventing one numeric Avg rating where the source says Max.
            if model=='CXH02F1822AG':row['功率条件']='原厂规格书：平均24W @95℃；官网简表25W；以具体规格书和降额曲线为准。'
            records.append(row)
    return records,manifest


def extend(data,qa):
    records,conflicts=build_historical(qa/'amotech-sources')
    rf,sources=build_rf(qa)
    data['records'].extend(records+rf)
    data['quarantined'].extend(conflicts)
    data['sources'].extend(sources)
    data['schema_version']=2
    return data
