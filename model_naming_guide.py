"""Result-scoped, read-only ordering-code help. Never a matching/price rule.

Only public fields from the actual displayed matches enter the popover. Unknown
suffixes stay unknown; a decoded code never proves availability or equivalence.
"""
from collections import OrderedDict
from decimal import Decimal
import hashlib
import html
import math
import re

PUBLIC_FIELDS = ('品牌', '型号', '系列', '系列说明', '器件类别', '器件类型',
                 '尺寸（inch）', '尺寸（mm）', '材质（介质）', '容值', '容值单位',
                 '容值误差', '耐压（V）', '功率', '_power', '工作温度')
TOL = {'T':'.01','A':'.05','B':'.1','C':'.25','D':'.5','F':'1','G':'2','J':'5','K':'10','M':'20'}
FOJAN_SOURCE = '系统已接入的富捷系列规则；未逐码核验的附加码会单独标出。'
VIKING_SOURCE = 'Viking AR Series，REV.F3，2022-02-10，Part Numbering，第 2 页。'
YAGEO_SOURCE = 'YAGEO RT Series 原厂数据表，Ordering information / Global part number。'
MURATA_SOURCE = '系统已接入的 Murata GR 系列命名规则；产品控制／包装尾码不作额外推断。'


def text(value):
    if value is None or isinstance(value, float) and math.isnan(value):
        return ''
    return str(value).strip()


def compact(value):
    return re.sub(r'\s+', '', text(value)).upper()


def public_candidates(frame):
    """Positive allowlist: no price, customer, account, audit or session fields."""
    if hasattr(frame, 'columns'):
        rows = frame[[key for key in PUBLIC_FIELDS if key in frame.columns]].to_dict('records')
    else:
        rows = frame
    result, seen = [], set()
    for row in rows:
        record = {key:text(row.get(key)) for key in PUBLIC_FIELDS if text(row.get(key))}
        identity = (record.get('品牌',''), compact(record.get('型号')))
        if not identity[1] or identity in seen:
            continue
        seen.add(identity)
        result.append(record)
    return result


def result_groups(records):
    groups = OrderedDict()
    for record in public_candidates(records):
        key = (record.get('品牌') or '品牌未标注', record.get('系列') or '系列未标注')
        groups.setdefault(key, []).append(record)
    return groups


def resistance(code):
    if re.fullmatch(r'\d{3,4}', code):
        return Decimal(code[:-1]) * Decimal(10) ** int(code[-1])
    match = re.fullmatch(r'(\d*)([RKM])(\d*)', code)
    if match and (match[1] or match[3]):
        return Decimal((match[1] or '0')+'.'+(match[3] or '0')) * {'R':1,'K':1000,'M':1000000}[match[2]]
    return None


def quantity(number, base='Ω'):
    number = Decimal(str(number))
    for multiplier, prefix in ((1000000,'M'),(1000,'k'),(1,'')):
        if abs(number) >= multiplier or multiplier == 1:
            value = format(number / multiplier, 'f')
            if '.' in value:
                value = value.rstrip('0').rstrip('.')
            unit = {1000000:'µF',1000:'nF',1:'pF'}[multiplier] if base == 'pF' else prefix+base
            return value+' '+unit


def tolerance(code, table=TOL):
    value = table.get(code)
    return '±'+format(Decimal(value).normalize(),'f')+'%' if value else '代码含义尚未核验'


def part(code, name, meaning, verified=True):
    return dict(code=code, name=name, meaning=meaning, verified=verified)


def walsin_resistor(model):
    """Separate WR type letters from WF precision/TCR letters (original tables)."""
    sizes={'04':'0402','06':'0603','08':'0805','12':'1206'}
    match=re.fullmatch(r'(WR)(04|06|08|12)([XW])([0-9R]{3,4})([FJP])([TQGHBDA])(L)',model)
    if match:
        series,size,subtype,code,tol,packing,tail=match.groups()
        value=resistance(code)
        if value is None or len(code)!=(4 if tol=='F' else 3) or tol=='P' and value!=0:
            return [],''
        if packing in 'HDA' and size!='04':
            return [],''
        packs={'T':'7 英寸卷盘','Q':'10 英寸卷盘','G':'13 英寸卷盘','H':'13 英寸卷盘／50000 颗（0402）',
               'B':'散装','D':'7 英寸卷盘／20000 颗（0402）','A':'7 英寸卷盘／15000 颗（0402）'}
        segments=[part(series,'系列','WR 通用厚膜贴片电阻'),part(size,'封装',sizes[size]+'（英制）'),
            part(subtype,'类型','常规阻值／跳线类型；实际范围按该尺寸规格表' if subtype=='X' else '±1% 扩展阻值类型；不是温漂代码'),
            part(code,'阻值',quantity(value)),part(tol,'阻值误差','跳线（非百分比误差）' if tol=='P' else tolerance(tol)),
            part(packing,'包装',packs[packing]),part(tail,'端电极','Sn 基（无铅）')]
        return segments,'Walsin 原厂 ASC_WR_V23，2015-04，Catalogue Numbers，第 6 页（原厂署名规格书存档）。'
    match=re.fullmatch(r'(WF)(04|06|08|12)([HU])([0-9R]{4})([ABCDF])(T)(L)',model)
    if not match or resistance(match[4]) is None:
        return [],''
    series,size,subtype,code,tol,packing,tail=match.groups()
    if subtype=='H' and tol not in 'BD':
        return [],''
    segments=[part(series,'系列','WF 精密贴片电阻'),part(size,'封装',sizes[size]+'（英制）')]
    if subtype=='H':
        segments.append(part(subtype,'类型','高精度厚膜（误差小于 1%）；不是温漂代码'))
        source='Walsin 原厂 ASC_WFxxH_V03，2023-05，Catalogue Numbers，第 4 页（原厂署名规格书存档）。'
    else:
        segments.append(part(subtype,'温度系数','±25 ppm/℃'))
        source='Walsin 原厂 ASC_WFxxU_V16，2012-03，Catalogue Numbers，第 6 页（原厂署名规格书存档）；只采用本版本已明确的尺寸和字段。'
    segments.extend([part(code,'阻值',quantity(resistance(code))),part(tol,'阻值误差',tolerance(tol)),
        part(packing,'包装','编带卷盘'),part(tail,'端电极','Sn 基（无铅）')])
    return segments,source


def yageo_rc(model):
    match=re.fullmatch(r'(RC)(0075|0100|0201|0402|0603|0805|1206|1210|1218|2010|2512)([BDFJ])([RKS])(-)(07|10|13|7W|7D|7N|3W)(\d*[RKM]\d*)(L)',model)
    if not match:
        return [],''
    series,size,tol,packing,tcr,reel,code,tail=match.groups()
    value=resistance(code)
    if value is None or not 2<=len(code)<=4:
        return [],''
    if (packing=='S' or reel=='7N') and size not in {'0075','0100'} or reel=='7D' and size not in {'0201','0402'}:
        return [],''
    reels={'07':'7 英寸卷盘／标准功率','10':'10 英寸卷盘','13':'13 英寸卷盘',
           '7W':'7 英寸卷盘／2 倍标准功率','7D':'7 英寸卷盘／2 倍标准装量（0201／0402）',
           '7N':'7 英寸防静电卷盘（0075／0100）','3W':'13 英寸卷盘／2 倍标准功率'}
    segments=[part(series,'系列','RC 通用厚膜贴片电阻'),part(size,'封装',size+'（英制尺寸代码）'),
        part(tol,'阻值误差',tolerance(tol)),part(packing,'包装',{'R':'纸带卷盘','K':'压纹带卷盘','S':'防静电卷盘'}[packing]),
        part(tcr,'温度系数','按规格表，不能由此位得出一个固定 ppm 数值'),part(reel,'卷盘／功率',reels[reel]),
        part(code,'阻值',quantity(value)),part(tail,'订货尾码','订货系统默认代码；不是生产状态或认证标志')]
    return segments,'YAGEO 原厂 RC_L Series，2025-11-14 V.14，Ordering Information，第 2 页。'


def viking_cr(model):
    match=re.fullmatch(r'(CR-)(E5|01|02|03|05|06|10|0A|12|25|62)([BCDFJ])([LEPH])([0245679ABCD])(-*)(\d+[RKM]\d*)',model)
    if not match:
        return [],''
    series,size,tol,function,packing,padding,code=match.groups()
    if len(padding+code)!=6 or resistance(code) is None:
        return [],''
    sizes={'E5':'01005','01':'0201','02':'0402','03':'0603','05':'0805','06':'1206',
           '10':'1210','0A':'2010','12':'2512','25':'1225','62':'0612'}
    packs={'0':'7 英寸／15000 颗','2':'7 英寸／2000 颗','4':'7 英寸／4000 颗','5':'7 英寸／20000 颗',
           '6':'7 英寸／10000 颗','7':'7 英寸／5000 颗','9':'10 英寸／8000 颗','A':'10 英寸／10000 颗',
           'B':'10 英寸／20000 颗','C':'13 英寸／40000 颗','D':'13 英寸／20000 颗'}
    functions={'L':'标准／高精度类型；温漂按规格表','E':'TC50（±50 ppm/℃）类型','P':'高功率类型；具体瓦数按尺寸规格表','H':'超高功率类型；具体瓦数按尺寸规格表'}
    segments=[part(series,'系列','CR 厚膜贴片电阻'),part(size,'封装',sizes[size]+'（英制）'),
        part(tol,'阻值误差',tolerance(tol)),part(function,'功能',functions[function]),part(packing,'包装',packs[packing])]
    if padding:
        segments.append(part(padding,'补位符','阻值区补足 6 个字符的位置符，不是负号'))
    segments.append(part(code,'阻值',quantity(resistance(code))))
    return segments,'Viking 原厂 CR Series REV.C6，2021-03-10，Part Numbering，正文第 2 页（PDF 第 3 页）。'


def pdc_fcf_array(model):
    # The 3-character network structure must not reuse single-chip FCF/FCF-E sizes.
    match=re.fullmatch(r'(FCF)(220|240|241|320|340|341|35R|370)([FJ])([TVW])(-)([0-9R]{3,4})',model)
    if not match or resistance(match[6]) is None:
        return [],''
    series,size,tol,packing,dash,code=match.groups()
    sizes={'220':'0402 × 2（4P2R）','240':'0402 × 4（8P4R，凸电极）','241':'0402 × 4（8P4R，凹电极）',
           '320':'0603 × 2（4P2R，凸电极）','340':'0603 × 4（8P4R，凸电极）','341':'0603 × 4（8P4R，凹电极）',
           '35R':'10P8R 排阻结构','370':'16P8R 排阻结构'}
    segments=[part(series,'系列','FCF 厚膜排阻／电阻网络（不是单颗电阻）'),part(size,'结构／尺寸',sizes[size]),
        part(tol,'阻值误差',tolerance(tol)),part(packing,'包装',{'T':'纸带／5000 颗','V':'纸带／10000 颗','W':'纸带／20000 颗'}[packing]),
        part(dash,'标准代码','标准订货位置符'),part(code,'阻值',quantity(resistance(code)))]
    return segments,'PSA／PDC 原厂 FCF ARRAY Rev.12.0.I48，Part Number，正文第 3 页（PDF 第 4 页）；四联结构不可当作单颗直接替换。'


def explain(record):
    brand, model = text(record.get('品牌')), compact(record.get('型号'))
    manufacturer = compact(brand)
    kind = text(record.get('器件类别') or record.get('器件类型'))
    segments, source = [], ''
    resistor = not kind or '电阻' in kind or 'RESISTOR' in kind.upper()
    mlcc = not kind or '电容' in kind or 'MLCC' in kind.upper()
    if resistor and ('FOJAN' in manufacturer or '富捷' in manufacturer):
        from fojan_resistor_catalog import FOJAN_SPECIAL_RESISTOR_SERIES
        match = re.fullmatch(r'(FRC|FRH|FRT|FTH|FRV|FRQ|FRR|FRG|FRD|FPS|FPL|FQP|FQR|FQT|FTR)(01005|\d{4})([TABCD F GJKM])([0-9R]{3,4})([A-Z]*)'.replace(' ',''),model)
        if match:
            series, size, tol, code, tail = match.groups()
            spec = FOJAN_SPECIAL_RESISTOR_SERIES.get(series,{})
            description = text(record.get('系列说明')) or spec.get('description') or '本系列代号'
            # FPL uses a decimal-R convention; standard J uses three digits.
            valid = len(code) == (3 if tol == 'J' or series == 'FPL' and size == '0603' else 4)
            value = resistance(code)
            if valid and value is not None:
                segments = [part(series,'系列',description),part(size,'封装',size+'（英制代码）'),
                            part(tol,'阻值误差',tolerance(tol)),part(code,'阻值',quantity(value))]
                if series == 'FRT' and re.fullmatch(r'[TQRB][SCA][AEXV]',tail):
                    segments.extend([part(tail[0],'包装',{'T':'7 英寸卷盘','Q':'10 英寸卷盘','R':'13 英寸卷盘','B':'散装'}[tail[0]]),
                        part(tail[1],'端电极',{'S':'Sn（锡）','C':'Cu（铜）','A':'Au（金）'}[tail[1]]),
                        part(tail[2],'温度系数',f"±{dict(A=10,E=15,X=25,V=50)[tail[2]]} ppm/℃")])
                    source='富捷 FRT 原厂规格书，FJ-JS-3001-V1.0／2021-01-25，Parts Number Explanation，第 1 页；具体组合须按当前型号规格书确认。'
                elif tail:
                    segments.append(part(tail,'附加订货码','该系列的包装／版本等附加代码尚未逐位核验，请按具体订货表确认。',False))
                source = source or FOJAN_SOURCE
    elif resistor and any(token in manufacturer for token in ('VIKING','光颉','光頡')):
        match = re.fullmatch(r'(AR)(01|02|03|05|06|13|10|12)([TAB CDF])([TB])([5XOSBNCD])([NYXWMPVOUQT]?)([0-9R]{4})(N?)'.replace(' ',''),model)
        if match and resistance(match[7]) is not None:
            series,size,tol,packing,tcr,power,code,mark = match.groups()
            sizes={'01':'0201','02':'0402','03':'0603','05':'0805','06':'1206','13':'1210','10':'2010','12':'2512'}
            tcrs={'5':1,'X':2,'O':3,'S':5,'B':10,'N':15,'C':25,'D':50}
            powers={'N':'1/20','Y':'1/16','X':'1/10','W':'1/8','M':'1/6','P':'1/5','V':'1/4','O':'1/3','U':'1/2','Q':'3/4','T':'1'}
            segments=[part(series,'系列','AR 薄膜精密晶片电阻'),part(size,'封装',sizes[size]+'（英制）'),
                part(tol,'阻值误差',tolerance(tol)),part(packing,'包装','编带卷盘' if packing=='T' else '散装'),
                part(tcr,'温度系数',f'±{tcrs[tcr]} ppm/℃')]
            if power:
                segments.append(part(power,'功率代码',powers[power]+' W；还需核对该尺寸／阻值允许组合'))
            segments.append(part(code,'阻值',quantity(resistance(code))))
            if mark:
                segments.append(part(mark,'标记代码','无标记'))
            source=VIKING_SOURCE
        else:
            segments,source=viking_cr(model)
    elif resistor and any(token in manufacturer for token in ('YAGEO','国巨')):
        match = re.fullmatch(r'(RT)(\d{4})([LPWBCDF])([RK])([ABCDE])(\d{2})([0-9RKM.]+)(L)',model)
        if match and resistance(match[7]) is not None:
            series,size,tol,packing,tcr,reel,code,tail=match.groups()
            segments=[part(series,'系列','RT 高精度高稳定薄膜电阻'),part(size,'封装',size+'（英制）'),
                part(tol,'阻值误差',tolerance(tol,dict(L='.01',P='.02',W='.05',B='.1',C='.25',D='.5',F='1'))),
                part(packing,'包装','纸／PE 编带卷盘' if packing=='R' else '压纹带卷盘'),
                part(tcr,'温度系数',f"±{dict(A=5,B=10,C=15,D=25,E=50)[tcr]} ppm/℃"),
                part(reel,'卷盘代码','7 英寸' if reel=='07' else '具体卷盘尺寸须查订货表',reel=='07'),
                part(code,'阻值',quantity(resistance(code))),part(tail,'订货尾码','订货系统固定尾码，不单独证明生产状态或认证')]
            source=YAGEO_SOURCE
        else:
            segments,source=yageo_rc(model)
    elif resistor and any(token in manufacturer for token in ('WALSIN','华新科','華新科','华科')):
        segments,source=walsin_resistor(model)
    elif resistor and any(token in manufacturer for token in ('PDC','PSA','信昌')):
        segments,source=pdc_fcf_array(model)
    elif mlcc and any(token in manufacturer for token in ('MURATA','村田')):
        match = re.fullmatch(r'(GRM|GCM|GCJ|GJM|GQM|GRT|GCG|GCQ)(\d{2})(.)([A-Z0-9]{2})([A-Z0-9]{2})(\d{3}|R\d{2})([BCDFGJKMZ])([A-Z0-9]+)',model)
        if match:
            series,size,thickness,material,voltage,cap,tol,tail=match.groups()
            sizes={'02':'01005','03':'0201','15':'0402','18':'0603','21':'0805','31':'1206','32':'1210','42':'1808','43':'1812','55':'2220'}
            materials={'B1':'C0G','C1':'C0G','5C':'C0G','R6':'X5R','R7':'X7R','R9':'X8R','C6':'X5S','C7':'X7S','C8':'X6S','D6':'X5T','D7':'X7T','D8':'X6T'}
            volts={'0E':2.5,'0G':4,'0J':6.3,'1A':10,'1C':16,'1E':25,'1H':50,'1J':63,'2A':100,'2D':200,'2E':250,'2H':500,'3A':1000}
            cap_value = Decimal(cap.replace('R','.')) if 'R' in cap else Decimal(cap[:2])*10**int(cap[-1])
            tol_value = {'B':'±0.1 pF','C':'±0.25 pF','D':'±0.5 pF','Z':'-20%～+80%'}.get(tol) or tolerance(tol)
            segments=[part(series,'系列',text(record.get('系列说明')) or 'Murata '+series+' 系列'),
                part(size,'封装',sizes.get(size,'该尺寸代码尚未核验')+'（英制）',size in sizes),
                part(thickness,'厚度代码','具体厚度须按该型号产品表确认',False),
                part(material,'介质',materials.get(material,'该介质代码尚未核验'),material in materials),
                part(voltage,'额定电压',str(volts[voltage])+' V' if voltage in volts else '该电压代码尚未核验',voltage in volts),
                part(cap,'容量',quantity(cap_value,'pF')),part(tol,'容量误差',tol_value),
                part(tail,'产品／包装尾码','具体产品控制与包装定义须查该系列订货表',False)]
            source=MURATA_SOURCE
    elif mlcc and any(token in manufacturer for token in ('PDC','信昌')):
        match=re.fullmatch(r'(FV|FM|FS|FP|FN|MT|MG)(\d{2})([BNXTAYS])(\d{3}|\dR\d)([DFGJKMZ])(6R3|\d{3})([A-Z])([A-Z])([A-Z0-9]*)',model)
        if match:
            series,size,material,cap,tol,voltage,packing,thickness,tail=match.groups()
            sizes={'03':'0201','15':'0402','18':'0603','21':'0805','31':'1206','32':'1210','42':'1808','43':'1812','46':'1825','52':'2211','55':'2220','56':'2225'}
            materials={'B':'X5R','N':'C0G','X':'X7R','T':'X7T','Y':'Y5V'}
            # Latest FS A/S meanings differ from older general MLCC tables.
            if series=='FS': materials.update(A='X7S',S='X6S')
            cap_value=Decimal(cap.replace('R','.')) if 'R' in cap else Decimal(cap[:2])*10**int(cap[-1])
            volt_value='6.3' if voltage=='6R3' else str(int(voltage[:2])*10**int(voltage[-1]))
            packages={'B':'散装','T':'托盘','E':'7 英寸卷盘／压纹带','P':'7 英寸卷盘／纸带','K':'10 英寸卷盘／压纹带','D':'10 英寸卷盘／纸带','L':'13 英寸卷盘／压纹带','G':'13 英寸卷盘／纸带'}
            tol_value='±0.5 pF' if tol=='D' else '-20%～+80%' if tol=='Z' else tolerance(tol)
            segments=[part(series,'系列',text(record.get('系列说明')) or 'PDC '+series+' 系列'),
                part(size,'封装',sizes.get(size,'待核验')+'（英制）',size in sizes),
                part(material,'介质',materials.get(material,'该系列此代码尚未核验'),material in materials),
                part(cap,'容量',quantity(cap_value,'pF')),part(tol,'容量误差',tol_value),part(voltage,'额定电压',volt_value+' V'),
                part(packing,'包装',packages.get(packing,'包装代码尚未核验'),packing in packages),
                part(thickness,'厚度代码','具体厚度及公差须查该系列厚度表',False)]
            if tail: segments.append(part(tail,'控制尾码','按该型号的原厂控制代码表确认，不据此判断生产状态',False))
            source='PDC 原厂 MLCC 目录的分系列 Part Number 表；FS A／S 介质沿用已核验的新版 FS 表，厚度和控制码未作推测。'
    elif mlcc and any(token in manufacturer for token in ('SAMSUNG','三星')):
        match=re.fullmatch(r'(CL)(\d{2})([ABCXYZ])(\d{3}|\dR\d)([FGJKMZ])([RQPOALBCDEFGH])([A-Z0-9]+)',model)
        if match:
            series,size,material,cap,tol,voltage,tail=match.groups()
            sizes={'02':'01005','03':'0201','05':'0402','10':'0603','21':'0805','31':'1206','32':'1210','42':'1808','43':'1812','55':'2220'}
            materials=dict(A='X5R',B='X7R',C='C0G',X='X6S',Y='X7S',Z='X7T')
            volts=dict(R=4,Q=6.3,P=10,O=16,A=25,L=35,B=50,C=100,D=200,E=250,F=500,G=630,H=1000)
            cap_value=Decimal(cap.replace('R','.')) if 'R' in cap else Decimal(cap[:2])*10**int(cap[-1])
            segments=[part(series,'产品类型','Samsung 多层陶瓷电容'),part(size,'封装',sizes.get(size,'待核验')+'（英制）',size in sizes),
                part(material,'介质',materials[material]),part(cap,'容量',quantity(cap_value,'pF')),
                part(tol,'容量误差','-20%～+80%' if tol=='Z' else tolerance(tol)),part(voltage,'额定电压',str(volts[voltage])+' V'),
                part(tail,'厚度／产品／包装尾码','各位置具体定义须查该系列完整订货表',False)]
            source='系统已接入的 Samsung CL 产品编码规则；不把特殊产品／包装尾码当作通用参数。'
    elif mlcc and any(token in manufacturer for token in ('TDK','东电化')):
        match=re.fullmatch(r'(C)(\d{4})(X5R|X7R|X6S|X7S|X7T|C0G)([0-9A-Z]{2})(\d{3}|\dR\d)([BCDFGJKMZ])([A-Z0-9]+)',model)
        if match:
            series,size,material,voltage,cap,tol,tail=match.groups()
            sizes={'0603':'0201','1005':'0402','1608':'0603','2012':'0805','3216':'1206','3225':'1210','4520':'1808','4532':'1812','5750':'2220'}
            volts={'0E':2.5,'0G':4,'0J':6.3,'1A':10,'1C':16,'1E':25,'1H':50,'1J':63,'2A':100,'2D':200,'2E':250,'2H':500,'3A':1000}
            cap_value=Decimal(cap.replace('R','.')) if 'R' in cap else Decimal(cap[:2])*10**int(cap[-1])
            tol_value={'B':'±0.1 pF','C':'±0.25 pF','D':'±0.5 pF','Z':'-20%～+80%'}.get(tol) or tolerance(tol)
            segments=[part(series,'系列','TDK C 系列 MLCC'),part(size,'封装',size+'（公制）→ '+sizes.get(size,'英制待核验'),size in sizes),
                part(material,'介质',material),part(voltage,'额定电压',str(volts[voltage])+' V' if voltage in volts else '待核验',voltage in volts),
                part(cap,'容量',quantity(cap_value,'pF')),part(tol,'容量误差',tol_value),part(tail,'厚度／产品／包装尾码','须按该型号订货表进一步确认',False)]
            source='系统已接入的 TDK C 系列命名结构；这里的四位尺寸码是公制，不是英制。'
    elif mlcc and ('AMOTECH' in manufacturer or '阿莫泰克' in manufacturer):
        import amotech_catalog as amo
        match=amo.STANDARD.fullmatch(model)
        parsed=amo.decode_standard(model)
        if match and parsed:
            g=match.groupdict()
            volts = '200／250 V（原厂表存在双值，须查具体型号）' if g['voltage']=='2B' else str(amo.VOLTAGE[g['voltage']])+' V'
            meanings=[('material','介质',amo.MATERIAL[g['material']][0]),('size','封装',amo.SIZE[g['size']][0]+'（英制）'),
                ('thickness','厚度代码','等于宽度' if g['thickness']=='X' else str(amo.THICKNESS.get(g['thickness'],'待核验'))+' mm'),
                ('voltage','额定电压',volts),('design','设计',amo.DESIGN[g['design']]),('cap','容量',quantity(amo.cap_pf(g['cap']),'pF')),
                ('tol','容量误差','±'+amo.TOLERANCE[g['tol']]+('' if 'pF' in amo.TOLERANCE[g['tol']] else '%')),
                ('electrode','端电极',amo.ELECTRODE[g['electrode']]),('packing','包装',amo.PACKING[g['packing']]),
                ('application','应用',amo.APPLICATION[g['application']]+'；不等于已通过 AEC-Q200 认证')]
            segments=[part('AC','产品类型','多层陶瓷电容')]+[part(g[key],name,meaning,
                not (key=='voltage' and g[key]=='2B') and not (key=='thickness' and g[key] not in amo.THICKNESS and g[key]!='X')) for key,name,meaning in meanings]
            source='AMOTECH 原厂 MLCC Part Numbering，Rev.10N（2026-06-09）；沿用已核验规则。'
    if segments and ''.join(row['code'] for row in segments) != model:
        segments,source=[],''
    return dict(model=model,brand=brand,series=text(record.get('系列')),segments=segments,source=source,
                status='已接入分段说明' if segments else '该系列逐码规则尚未核验')


def guide_html(guide):
    escape=lambda value:html.escape(str(value),quote=True)
    segments=guide['segments']
    if not segments:
        return '<div class="naming-empty">该系列的逐码命名规则尚未核验，暂不把库内参数反写成代码含义。</div>'
    chips=''.join('<div class="naming-chip'+(' naming-unknown' if not s['verified'] else '')+'"><code>'+escape(s['code'])+'</code><span>'+escape(s['name'])+'</span></div>' for s in segments)
    rows=''.join('<tr><td><code>'+escape(s['code'])+'</code></td><td>'+escape(s['name'])+'</td><td>'+escape(s['meaning'])+(' <small>待核验</small>' if not s['verified'] else '')+'</td></tr>' for s in segments)
    return '<div class="naming-chips">'+chips+'</div><div class="naming-table-wrap"><table class="naming-table"><thead><tr><th>代码</th><th>字段</th><th>含义／本例解读</th></tr></thead><tbody>'+rows+'</tbody></table></div><p class="naming-source">依据：'+escape(guide['source'])+'</p>'


STYLE='''<style>
[data-testid="stPopoverBody"]:has(.naming-guide-marker){width:min(760px,calc(100vw - 24px));max-height:80vh;overflow:auto}
.naming-guide-marker{display:none}.naming-guide-title{font-size:19px;font-weight:700;color:#17365c;margin:0 0 5px}
.naming-guide-sub{color:#65758b;font-size:13px;margin:0 0 14px}.naming-chips{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 16px}
.naming-chip{display:flex;flex-direction:column;text-align:center;background:#edf4ff;border:1px solid #cfdef5;border-radius:7px;padding:9px 12px;min-width:44px}
.naming-chip code{font:700 17px ui-monospace,Consolas,monospace;color:#1956ad;background:none;padding:0}.naming-chip span{font-size:11px;color:#61748f;margin-top:4px}
.naming-unknown{background:#fff8e8;border-color:#ebd9af}.naming-unknown code{color:#886325}
.naming-table-wrap{overflow-x:auto}.naming-table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.5}
.naming-table th{background:#f3f6fa;text-align:left;color:#3e5673;font-weight:600}.naming-table td,.naming-table th{padding:8px 10px;border-bottom:1px solid #e5eaf0;vertical-align:top}
.naming-table td:first-child{white-space:nowrap}.naming-table code{color:#1956ad;background:none}.naming-table small{display:inline-block;color:#886325;background:#fff4d8;padding:1px 5px;border-radius:3px;font-size:11px}
.naming-source,.naming-empty{font-size:12px;color:#6b7787;margin-top:12px}.naming-empty{padding:16px;background:#f5f7fa;border-radius:6px}
@media(max-width:600px){.naming-chip{padding:7px 8px}.naming-table td,.naming-table th{padding:7px 6px;font-size:12px}}
</style>'''


def _render_header(title, records, instance_key):
    import streamlit as st
    groups=result_groups(records)
    if not groups or not hasattr(st,'popover'):
        st.markdown('<div class="section-title">'+html.escape(title)+'</div>',unsafe_allow_html=True)
        return
    st.markdown(STYLE,unsafe_allow_html=True)
    columns=st.columns([3,2])
    with columns[0]:
        st.markdown('<div class="section-title">'+html.escape(title)+'</div>',unsafe_allow_html=True)
    with columns[1]:
        with st.popover('型号命名对照',help='查看本次匹配结果中各品牌、系列的代码含义'):
            st.markdown('<span class="naming-guide-marker"></span><div class="naming-guide-title">型号命名对照</div><p class="naming-guide-sub">仅展示本次匹配出现的品牌与系列；点击面板外部即可关闭。</p>',unsafe_allow_html=True)
            options=list(groups)
            if hasattr(st,'fragment'):
                chosen=st.selectbox('品牌／系列',options,format_func=lambda key:f'{key[0]} · {key[1]}（{len(groups[key])} 个型号）',key='naming_group_'+instance_key)
                models=groups[chosen]
                token=hashlib.sha256(repr(chosen).encode()).hexdigest()[:12]
                selected=st.selectbox('示例型号',[r['型号'] for r in models],key='naming_model_'+instance_key+'_'+token)
                record=next(r for r in models if r['型号']==selected)
                guide=explain(record)
                st.markdown(guide_html(guide),unsafe_allow_html=True)
                if not guide['segments']:
                    values=[dict(参数=key,库内记录=value) for key,value in record.items() if key not in {'品牌','型号','系列','系列说明','器件类别','器件类型'}]
                    if values:
                        st.caption('以下为该型号的库内参数，不代表已知对应代码位置：')
                        st.dataframe(values,hide_index=True,use_container_width=True)
            else:
                # Older Streamlit: native details, no widget rerun that would
                # erase an already displayed search or create another quote.
                for key,models in groups.items():
                    st.markdown('<details><summary>'+html.escape(' · '.join(key))+'</summary>'+guide_html(explain(models[0]))+'</details>',unsafe_allow_html=True)
            st.caption('不同品牌／系列不能混用同一代码表。代码说明不等于可订购、在产、已认证或可直接替代；最终以具体型号原厂规格书为准。')


def render_header(title, frame, instance_key):
    import streamlit as st
    records=public_candidates(frame)
    signature=hashlib.sha256(repr([(r.get('品牌'),r.get('型号'),r.get('系列')) for r in records]).encode()).hexdigest()[:12]
    renderer=st.fragment(_render_header) if hasattr(st,'fragment') else _render_header
    renderer(title,records,str(instance_key)+'_'+signature)
