"""Reviewed actual electronic-component records, never generated combinations.

Inputs: rendered official RF table capture and manufacturer PDF table/text
extracts. The historical EMI/ESD catalogue is explicitly dated 2008; catalogue
presence does not imply current availability or lifecycle. No database writes.
"""
import json
import re
import hashlib
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


def build_automotive(qa):
    """Only six reviewed 2018 line-up tables, not customer/MP-history rows.

    The captured PDF's digest and each literal electrical row must agree before
    importing. No ordering-code inference, lifecycle or AEC qualification.
    """
    folder=qa/'amotech-sources'
    source=json.loads((folder/'emc2018-manifest.json').read_text(encoding='utf-8'))
    assert source['sha256']=='aa4dc9e722cd23f7b36d941d04e9c9907334362b419688bd5199e48a422e14fa'
    assert hashlib.sha256((folder/'emc2018.pdf').read_bytes()).hexdigest()==source['sha256']
    pages={p['page']:p['text'] for p in json.loads((folder/'emc2018-pages.json').read_text(encoding='utf-8'))}
    compact=lambda s: re.sub(r'\s+','',s).replace('Ω','Ω')
    records=[]

    def add(model,page,table_row,**facts):
        assert compact(table_row) in compact(pages[page]), (model,page,table_row)
        family=re.match(r'[A-Z]+',model)[0]
        metric=facts.pop('metric')
        # These are metric package codes, not EIA inch codes. A 1210 CMF is
        # 1.2 x 1.0mm, not the 3.2 x 2.5mm EIA 1210 capacitor footprint.
        body={'1005':'1.0 × 0.5','1608':'1.6 × 0.8','2012':'2.0 × 1.2','1210':'1.2 × 1.0'}[metric]
        row={'品牌':BRAND,'型号':model,'器件类型':'ESD保护器件' if family in {'AIES','AVMC'} else 'EMI／ESD滤波器',
             '系列':family,'尺寸（mm）':metric,'本体尺寸（mm）':body,'安装方式':'贴片',
             '资料版本':f'2018-10 Automotive Application Rev.R22，PDF页{page}',
             '资料状态':'2018历史资料；当前供货、生产状态及逐型号认证待核验',
             '生产状态':'','官网链接':source['url'],'_amotech_source_url':source['url'],
             '_amotech_source_page':page,'_source_sha256':source['sha256'],
             '_source_table_row':table_row,'_catalog_membership':'manufacturer_listed',
             '_model_rule_authority':'amotech_manufacturer_lineup_2018',
             '_manual_equivalence_required':True,**facts}
        records.append(row)

    for model,clock,rdc,branch in (
        ('ASF10S03100EF1',33,70,50),('ASF10S03065EF5',70,32,32.5),
        ('ASF10S03065EF1',33,70,32.5),('ASF10S03033F1B',155,8.5,16.5),
        ('ASF10S03025F1B',193,8.5,12.5),('ASF10S03025F2B',255,3,12.5),
    ):
        add(model,32,f'{model} {clock}MHz↓ 1608mm–1ch {rdc}Ω {branch}+{branch}pF 10MΩmin.',
            metric='1608',结构='单通道π型RLC EMI／ESD滤波网络',回路数='1',
            **{'串联电阻（Ω）':rdc,'合计电容量（pF）':branch*2,'适用时钟上限（MHz）':clock,
               '电容定义／测试条件':f'C1+C2：{branch}+{branch}pF；1MHz；合计值不是单支路电容',
               '电气参数说明':f'Rdc {rdc}Ω；IR ≥10MΩ（测试电压未列）；适用时钟≤{clock}MHz，不是-3dB截止频率。额定电压未列，不从10S推断。',
               '引脚／端口':'In/Out两端，另外两侧为GND；详见第32页等效电路和尺寸图。'})
    for model,clock,rdc,branch in (
        ('ADF10S05Q080EF2',33,80,40),('ADF10S05Q100EF2',33,70,50),
        ('ADF10S05Q050EF1',65,30,25),('ADF10S05Q050EF2',65,20,25),
    ):
        add(model,31,f'{clock}MHz↓ {model} 2012mm {rdc}Ω {branch}+{branch}pF 1.0MΩmin.',
            metric='2012',结构='四通道π型RLC EMI／ESD滤波网络',回路数='4',
            **{'串联电阻（Ω）':rdc,'合计电容量（pF）':branch*2,'适用时钟上限（MHz）':clock,
               '电容定义／测试条件':f'每路C1+C2：{branch}+{branch}pF；1MHz；合计值不是单支路电容',
               '电气参数说明':f'Rdc {rdc}Ω；IR ≥1.0MΩ（测试电压未列）；适用时钟≤{clock}MHz，不是-3dB截止频率。额定电压未列，不从10S推断。',
               '引脚／端口':'Ch1 1↔5，Ch2 2↔6，Ch3 3↔7，Ch4 4↔8；左右侧为GND，按原图方向核对。'})
    for model,metric,z,rdc,cap in (
        ('AHFE12D350CL','1210',35,3,1.2),('AHFE12D900CL','1210',90,5,1.7),
        ('AHFE12D121CL','1210',120,5,1.7),('AHFE20Q101ES','2012',100,4,1.2),
    ):
        array='(Array)' if metric=='2012' else ''
        add(model,33,f'{model} {metric}mm{array} 5V {z}Ω {rdc}Ωmax. {cap}pFmax. 10MΩmin.',
            metric=metric,结构='共模EMI／ESD复合滤波网络',回路数='4' if array else '2',
            **{'额定电压（V）':5,'共模阻抗@100MHz（Ω）':z,'直流电阻上限（Ω）':rdc,
               '电容量上限（pF）':cap,'电容定义／测试条件':f'Cp ≤{cap}pF；1MHz；上限不是标称值',
               '电气参数说明':f'共模阻抗 {z}Ω @100MHz（非差模阻抗）；Rdc ≤{rdc}Ω；IR ≥10MΩ（测试电压未列）。通道数按第9页；第33页1pole/2pole指差分对。'})
    for model,metric,clock,rdc,rtol,cap in (
        ('ADMF12D065F08','1210',80,14,5,65),('ADMF12D022F3B','1210',200,4,2,22),
        ('ADMF20Q022F3B','2012',200,4,2,22),('ADMF16Q022F3B','1608',200,4,2,22),
    ):
        add(model,34,f'{clock}MHz↓ {model} {metric}mm 10V 25±5V {rdc}±{rtol}Ω {cap}pF±30% 10MΩmin.',
            metric=metric,结构='差模／共模EMI／ESD复合滤波网络',
            **{'额定电压（V）':10,'串联电阻（Ω）':rdc,'寄生电容量（pF）':cap,
               '适用时钟上限（MHz）':clock,'电容定义／测试条件':f'Cp {cap}pF ±30%；1MHz；端子定义按原图',
               '压敏／击穿电压及条件':'Vn 25±5 V @1mA；不是额定电压',
               '电气参数说明':f'Rdc {rdc}±{rtol}Ω；IR ≥10MΩ（测试电压未列）；适用时钟≤{clock}MHz，不是-3dB截止频率。引脚和通道须按具体型号图纸核对。'})
    for model,metric,rated,clamp in (
        ('AIES12U02AG1','1005',12,40),('AIES24U02CG2','1005',24,35),('AIES24U03AG1','1608',24,45),
    ):
        add(model,35,f'{model} {metric}mm {rated}V {clamp}Vtyp. 0.1pFtyp.',
            metric=metric,结构='超低电容ESD抑制器（系列标注开路失效）',
            **{'额定电压（V）':rated,'寄生电容量（pF）':.1,
               '电容定义／测试条件':'Cp 0.1pF典型；此表未列电容测试频率和电平',
               '电气参数说明':f'钳位电压 {clamp}V典型，原表未列脉冲条件，不作保证上限或直流耐压。系列说明失效模式为开路；不是保证任意过应力均安全。'})
    for model,metric,vn,cap,clamp,imax in (
        ('AVMC18S03120','1608',24.5,120,40,30),
        ('AVMC18S05400','2012',24.5,400,40,120),('AVMC5S03500','1608',12,500,25,30),
    ):
        add(model,21,f'{model} {metric} {vn} {cap} {clamp} {imax}',
            metric=metric,结构='片式ESD／EOS压敏保护器件',
            **{'寄生电容量（pF）':cap,'钳位电压@1A8／20µs（V）':clamp,'峰值电流@8／20µs（A）':imax,
               '电容定义／测试条件':f'Cp {cap}pF；1kHz；此表未列测试电平和容差',
               '压敏／击穿电压及条件':f'Vn {vn}V；此表未列测试电流，不是额定或最大连续工作电压',
               '电气参数说明':f'VC {clamp}V @1A，8/20µs脉冲；Imax {imax}A @8/20µs。18S/5S不直接推成连续工作电压；当前供货须核实。'})
    assert len(records)==24 and len({r['型号'] for r in records})==24
    assert compact('AVMC18S03220 24.5 200 40 60') in compact(pages[36])
    conflicts=[{'model':'AVMC18S03220','kind':'ESD保护器件',
                'detail':'型号尾码220与原厂2018表列200pF不一致；第21和36页均列200pF，缺完整命名定义，不擅自选200或220入库',
                'source_url':source['url'],'pdf_page':36,'source_sha256':source['sha256']}]
    return records,conflicts,dict(source,revision='2018-10 Automotive Application Rev.R22',reviewed_pages=[9,19,20,21,31,32,33,34,35,36])


def extend(data,qa):
    records,conflicts=build_historical(qa/'amotech-sources')
    rf,sources=build_rf(qa)
    data['records'].extend(records+rf)
    data['quarantined'].extend(conflicts)
    data['sources'].extend(sources)
    automotive,conflicts,source=build_automotive(qa)
    assert not ({r['型号'] for r in automotive}&{r['型号'] for r in data['records']})
    data['records'].extend(automotive)
    data['quarantined'].extend(conflicts)
    data['sources'].append(source)
    data['schema_version']=3
    return data
