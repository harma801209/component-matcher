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
MURATA_SOURCE = 'Murata 原厂 Part Numbering，第1页尺寸／标称厚度表及第3页个别规格识别码／包装表；标称厚度不代表具体型号的公差或最大厚度，不推测个别规格识别码的内部含义。'


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


def yageo_mfr(model):
    """Original MFR V4 p2 codes; axial lead form is NOT chip package size."""
    match=re.fullmatch(r'(MFR)(-12|25S|-25|50S|-50|100|1WS|200|2WS|3WS)'
                      r'([DFGJ])([RTB])([EF-])'
                      r'(26-|52-|73-|52[ABCGH]|FB-|FFK|FKK|FK|MB|MT|FT|PN|AV|M|F)'
                      r'(\d*[RKM]\d*)',model)
    if not match or resistance(match[7]) is None:
        return [],''
    series,power,tol,packing,tcr,forming,code=match.groups()
    watts={'-12':'1/6W','25S':'1/4W','-25':'1/4W','50S':'1/2W','-50':'1/2W',
           '100':'1W','1WS':'1W','200':'2W','2WS':'2W','3WS':'3W'}
    forms={'26-':'轴向编带尺寸 A = 26 mm（不是引脚间距）',
           '52-':'轴向编带尺寸 A = 52.4 mm（不是引脚间距）',
           '73-':'轴向编带尺寸 A = 73 mm（不是引脚间距）',
           '52A':'轴向编带 A = 52.4 mm，引脚直径 0.4±0.02 mm',
           '52B':'轴向编带 A = 52.4 mm，引脚直径 0.45±0.02 mm',
           '52C':'轴向编带 A = 52.4 mm，引脚直径 0.5±0.02 mm',
           '52G':'轴向编带 A = 52.4 mm，引脚直径≥0.6 mm',
           '52H':'轴向编带 A = 52.4 mm，焊接部位不涂漆',
           'M':'M 型引脚成形，尺寸图见原厂第9页',
           'MB':'MB 型引脚成形，尺寸图见原厂第10页',
           'F':'F 型引脚成形，尺寸图见原厂第12页',
           'FK':'FK 型引脚成形，尺寸图见原厂第12页',
           'FFK':'F 型弯折引脚成形，尺寸图见原厂第12页',
           'FKK':'FKK 型引脚成形，尺寸图见原厂第12页',
           'FB-':'FB 型引脚成形，仅 -25／50S，尺寸图见原厂第13页',
           'MT':'MT 型引脚成形，尺寸图见原厂第14页',
           'FT':'FT 型引脚成形，尺寸图见原厂第14页',
           'PN':'PANAsert 引脚成形，尺寸图见原厂第14页',
           'AV':'AVIsert 引脚成形，尺寸图见原厂第14页'}
    if forming=='FB-' and power not in {'-25','50S'}:
        return [],''
    segments=[part(series,'系列','MFR 轴向引线金属膜电阻；不是贴片封装系列'),
              part(power,'功率',watts[power]+'（额定条件及降额见原厂规格表）'),
              part(tol,'阻值误差',tolerance(tol)),
              part(packing,'包装',{'R':'卷盘包装','T':'盒装编带','B':'散装'}[packing]),
              part(tcr,'温度系数',{'E':'±50 ppm/℃','F':'±100 ppm/℃','-':'按具体型号规格确认；本字符不指定数值'}[tcr],tcr!='-'),
              part(forming,'引脚成形',forms[forming]),part(code,'阻值',quantity(resistance(code)))]
    source='YAGEO 原厂 MFR，2024-04-03 V4，第2页订货表、第6页编带尺寸及第9–14页成形图。解码不证明具体组合可采购或当前在产。'
    if forming=='F' and power in {'-25','50S'}:
        source+=' 第16页修订记录曾计划于2023-02-28停用这两种功率的 F 成形；须另查具体型号最新 PCN，不能把该历史计划当作当前逐型号状态。'
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


def koa_resistor(model):
    """Original family tables, not a universal KOA letter/parameter guesser."""
    sizes={'1F':'01005','1H':'0201','1E':'0402','1J':'0603','2A':'0805',
           '2B':'1206','2E':'1210','2H':'2010','W2H':'2010','3A':'2512',
           'W3A':'2512','W3A2':'2512'}
    packs={'TX':'4 mm 宽压纹塑料带／1 mm 节距',
           'TBL':'压制纸带／2 mm 节距','TCM':'压制纸带／2 mm 节距',
           'TPL':'冲孔纸带／2 mm 节距','TP':'冲孔纸带／2 mm 节距',
           'TD':'冲孔纸带／4 mm 节距','TE':'压纹塑料带／4 mm 节距',
           'TDD':'10 英寸卷盘／纸带','TED':'10 英寸卷盘／压纹塑料带'}
    terminations={'T':'Sn（锡）','G':'Au（金）','L':'Sn/Pb（锡铅）'}
    match=re.fullmatch(r'(RN73H|RN73R|RN73)(1H|1E|1J|2A|2B|2E)([TGL])(TCM|TDD|TED|TP|TD|TE)([0-9R]{4})([ABCDF])(05|10|25|50|100)',model)
    if match:
        series,size,terminal,packing,code,tol,tcr=match.groups()
        if resistance(code) is None:
            return [],''
        if size=='1H' and series!='RN73H' or terminal=='G' and (series!='RN73H' or size not in {'1E','1J'}):
            return [],''
        if terminal=='L' and series!='RN73' or packing in {'TDD','TED'} and series!='RN73':
            return [],''
        if (packing=='TCM' and size!='1H' or packing=='TP' and size!='1E'
                or packing in {'TD','TDD'} and size not in {'1J','2A','2B','2E'}
                or packing in {'TE','TED'} and size not in {'2A','2B','2E'}
                or size=='1H' and packing!='TCM'):
            return [],''
        source=('KOA 原厂 RN73，2022-10-05，Ordering information，第 1 页；这是旧系列的订货结构，不证明当前在产。'
                if series=='RN73' else 'KOA 原厂 2026 Full Catalog，Ordering information，第 '+('32' if series=='RN73H' else '34')+' 页。')
        return [part(series,'系列',series+' 精密薄膜贴片电阻'),part(size,'封装',sizes[size]+'（英制）'),
            part(terminal,'端电极',terminations[terminal]),part(packing,'包装',packs[packing]),
            part(code,'阻值',quantity(resistance(code))),part(tol,'阻值误差',tolerance(tol)),
            part(tcr,'温度系数',f'±{int(tcr)} ppm/℃')],source
    match=re.fullmatch(r'(RK73B|RK73H|RK73Z)(W3A2|W3A|W2H|1F|1H|1E|1J|2A|2B|2E|2H|3A)(A?)([TGL])(TBL|TCM|TPL|TX|TP|TD|TE)([0-9R]{3,4})?([GJDF]?)',model)
    if match:
        series,size,characteristic,terminal,packing,code,tol=match.groups()
        if (characteristic and (terminal!='T' or size not in {'1E','1J','2A','2B'})
                or terminal=='G' and size not in {'1E','1J','2A'}
                or terminal=='L' and size in {'1F','1H','W2H','W3A','W3A2'}
                or series=='RK73Z' and size=='W3A2'):
            return [],''
        if series=='RK73Z':
            if code or tol: return [],''
        elif (not code or resistance(code) is None
              or series=='RK73B' and (len(code)!=3 or tol not in 'GJ')
              or series=='RK73H' and (len(code)!=4 or tol not in 'DF')):
            return [],''
        segments=[part(series,'系列','零欧跳线贴片电阻' if series=='RK73Z' else '通用厚膜贴片电阻') ,
                  part(size,'封装',sizes[size]+'（英制）；功率按该尺寸规格表，不从尺寸擅推')]
        if characteristic: segments.append(part(characteristic,'特性','耐热冲击类型'))
        segments.extend([part(terminal,'端电极',terminations[terminal]),part(packing,'包装',packs[packing])])
        if code: segments.extend([part(code,'阻值',quantity(resistance(code))),part(tol,'阻值误差',tolerance(tol))])
        return segments,'KOA 原厂 2026 Full Catalog，RK73B／RK73H／RK73Z 分系列 Ordering information，第 '+{'RK73B':'21','RK73H':'23','RK73Z':'25'}[series]+' 页。'
    match=re.fullmatch(r'(RS73F|RS73G)(1E|1J|2A|2B)(T)(TPL|TP|TD)([0-9R]{4})([BCDF])',model)
    if match and resistance(match[5]) is not None:
        series,size,terminal,packing,code,tol=match.groups()
        return ([part(series,'系列',series+' 高可靠厚膜贴片电阻'),
            part(size,'尺寸／功率',sizes[size]+'（英制）／'+{'1E':'0.125','1J':'0.2','2A':'0.25','2B':'0.33'}[size]+' W；额定温度与降额条件见该型号规格表'),
            part(terminal,'端电极','Sn（锡）'),part(packing,'包装',packs[packing]),
            part(code,'阻值',quantity(resistance(code))),part(tol,'阻值误差',tolerance(tol))],
            'KOA 原厂 2026 Full Catalog，RS73 Ordering information，第 36 页；具体组合仍以规格表为准。')
    return [],''


def vishay_crcw_variants(model):
    """Original Pb-bearing and HP tables, separate from the standard e3 table."""
    match=re.fullmatch(r'(CRCW)(0402|0603|0805|1206|1210|1218|2010|2512)([0-9RKM]{4})([DFJZ])([KNS0])([ET][A-Z])([A-Z0-9]{0,2})',model)
    if not match:return [],''
    series,size,code,tol,tcr,packing,special=match.groups()
    hp=special=='HP'
    lead_free=packing.startswith('E')
    if lead_free and not hp:return [],''  # existing standard-e3 handler owns it
    if special in {'HR','TR','37'}:return [],''  # different original tables
    if hp:
        options=({'0402':{'ED','EE'},'0603':{'EI','ED','EE','EA','EC'},
                  '0805':{'EA','EC'},'1206':{'EA','EC'},'1210':{'EA','EC'},
                  '1218':{'EK'},'2010':{'EF','EJ'},'2512':{'EG','EH'}} if lead_free else
                 {'0402':{'TD'},'0603':{'TA'},'0805':{'TA'},'1206':{'TA'},
                  '1210':{'TA'},'1218':{'TK'},'2010':{'TF'},'2512':{'TG'}})
        allowed_tolerance='DFJZ';jumper_tcr='0'
        source=('Vishay 原厂 CRCW-HP e3，2026-03-17，文档 20043，第2–3页。' if lead_free else
                'Vishay 原厂 CRCW-HP，2026-06-09，文档 20115，第2–3页；含铅端子版。')
    else:
        options={'0402':{'TD','TE'},'0603':{'TA','TC'},'0805':{'TA','TC'},
                 '1206':{'TA','TC'},'1210':{'TA','TC'},'1218':{'TK'},
                 '2010':{'TF'},'2512':{'TG','TH'}}
        allowed_tolerance='FJZ';jumper_tcr='S'
        source='Vishay 原厂 D/CRCW，2024-07-09，文档 20008，第3页；含铅端子版，不与无铅 e3 混用。'
    if packing not in options[size] or tol not in allowed_tolerance:return [],''
    value=Decimal(0) if code=='0000' else resistance(code)
    jumper=code=='0000'
    if value is None or not re.search('[RKM]',code) and not jumper or value==0 and not jumper:return [],''
    if jumper != (tol=='Z') or (tcr!=jumper_tcr if jumper else tcr not in 'KN'):return [],''
    packs={'TA':('纸带','5000','4','180'),'TC':('纸带','20000','4','330'),
           'TD':('纸带','10000','2','180'),'TE':('纸带','50000','2','330'),
           'TK':('压纹带','4000','4','180'),'TF':('压纹带','4000','4','180'),
           'TG':('压纹带','2000','8','180'),'TH':('压纹带','4000','4','180'),
           'EA':('纸带','5000','4','180'),'EC':('纸带','20000','4','330'),
           'ED':('纸带','10000','2','180'),'EE':('纸带','50000','2','330'),
           'EI':('纸带','5000','2','180'),'EK':('压纹带','4000','4','180'),
           'EF':('压纹带','4000','4','180'),'EJ':('压纹带','16000','4','330'),
           'EG':('压纹带','2000','8','180'),'EH':('压纹带','4000','4','180')}
    carrier,count,pitch,reel=packs[packing]
    width='8' if size in {'0402','0603','0805','1206'} or hp and size=='1210' else '12'
    meaning=f'{carrier}／{count}颗／带宽{width} mm／节距{pitch} mm／卷径{reel} mm；'+('e3 无铅纯锡端子版' if lead_free else '含铅端子版')
    segments=[part(series,'系列','厚膜贴片电阻；'+('高功率抗脉冲型' if hp else '通用型')),
        part(size,'封装',size+'（英制）'),part(code,'阻值',quantity(value)),
        part(tol,'阻值误差','跳线，不是百分比误差' if jumper else tolerance(tol)),
        part(tcr,'温度系数','跳线不规定温漂' if jumper else f"±{dict(K=100,N=200)[tcr]} ppm/℃"),
        part(packing,'包装',meaning)]
    if special:segments.append(part(special,'特殊选项','抗脉冲、高功率类型' if hp else '原厂特殊订货编号；此具体编号尚未核验',hp))
    return segments,source


def vishay_resistor(model):
    variant=vishay_crcw_variants(model)
    if variant[0]:return variant
    match=re.fullmatch(r'(CMF)(50|55|60)([0-9RKM]{6})([BCDFGJ])([EHKLNM])(EA|EB|EK|BF|RE|R6)([0-9]{1,3})?',model)
    if match and re.search('[RKM]',match[3]) and resistance(match[3]) is not None:
        series,size,code,tol,tcr,packing,special=match.groups()
        packs={'EA':'无铅／整盘编带','EB':'无铅／弹药盒 1000 颗（2025 版定义）',
               'EK':'无铅／散装 100 颗','BF':'含铅／散装 100 颗',
               'RE':'含铅／整盘编带','R6':'含铅／编带 1000 颗'}
        segments=[part(series,'系列','CMF 工业精密轴向金属膜电阻'),part(size,'外形',series+size+' 轴向外形代码，不是贴片尺寸'),
            part(code,'阻值',quantity(resistance(code))),part(tol,'阻值误差',tolerance(tol)),
            part(tcr,'温度系数',f"±{dict(E=25,H=50,K=100,L=150,N=200,M=300)[tcr]} ppm/℃"),
            part(packing,'包装',packs[packing])]
        if special: segments.append(part(special,'特殊订货码','此具体特殊订货编号尚未核验',False))
        return segments,'Vishay 原厂 CMF Industrial，2025-02-21，文档 31018，第 2 页；EK／BF／RE／R6 包装据原厂文档 31544，2013-02-25，第 1、4 页。仅适用 CMF50／55／60 工业型，不套用军标或阻燃型。'
    match=re.fullmatch(r'(CRCW|TNPW)(0201|0402|0603|0805|1206|1210|1218|2010|2512)([0-9RKM]{4})([BJDFZ])([KN0HEXY])(E[A-Z])(0H)?',model)
    if match:
        series,size,code,tol,tcr,packing,special=match.groups()
        value=Decimal(0) if code=='0000' else resistance(code)
        if value is None or not re.search('[RKM]',code) and code!='0000': return [],''
        if series=='CRCW':
            options={'0402':{'ED','EE'},'0603':{'EI','ED','EE','EA','EC'},
                     '0805':{'EA','EC'},'1206':{'EA','EC'},'1210':{'EA','EC'},
                     '1218':{'EK'},'2010':{'EF'},'2512':{'EG','EH'}}
            if size not in options or tol not in 'FJZ' or tcr not in 'KN0' or special:
                return [],''
            if (code=='0000')!=(tol=='Z') or (code=='0000')!=(tcr=='0'): return [],''
            ppm={'K':100,'N':200}
            source='Vishay 原厂 D/CRCW e3，2026-04-14，文档 20035，第 3 页；不套用于 CRCW-P、0201 或旧版非 e3 尾码。'
        else:
            options={'0201':{'ED'},'0402':{'ED'},'0603':{'EA','EC'},'0805':{'EA','EC'},'1206':{'EA','EC'},'1210':{'EA','EC'}}
            if size not in options or tol not in 'BDF' or tcr not in 'HEXY' or code=='0000': return [],''
            ppm={'H':50,'E':25,'X':15,'Y':10}
            source='Vishay 原厂 TNPW e3，2026-04-10，文档 28758，第 4 页；与 CRCW 的温漂码表不同。'
        if packing not in options[size] or series=='TNPW' and packing=='EC' and tcr not in 'HE': return [],''
        packs={'ED':'纸带／7 英寸／10000 颗／2 mm 节距','EE':'纸带／13 英寸／50000 颗／2 mm 节距',
               'EI':'纸带／7 英寸／5000 颗／2 mm 节距','EA':'纸带／7 英寸／5000 颗／4 mm 节距',
               'EC':'纸带／13 英寸／20000 颗／4 mm 节距','EK':'压纹带／7 英寸／4000 颗／4 mm 节距',
               'EF':'压纹带／7 英寸／4000 颗／4 mm 节距','EG':'压纹带／7 英寸／2000 颗／8 mm 节距',
               'EH':'压纹带／7 英寸／4000 颗／4 mm 节距'}
        segments=[part(series,'系列',series+(' 通用厚膜贴片电阻' if series=='CRCW' else '高稳定精密薄膜贴片电阻')),
            part(size,'封装',size+'（英制）'),part(code,'阻值',quantity(value)),
            part(tol,'阻值误差','跳线，不是百分比误差' if tol=='Z' else tolerance(tol)),
            part(tcr,'温度系数','跳线不规定温漂' if tcr=='0' else f'±{ppm[tcr]} ppm/℃'),
            part(packing,'包装',packs[packing]+'；E.. 为无铅包装代码')]
        if special: segments.append(part(special,'特殊选项','单一批次日期码（single lot date code）'))
        return segments,source
    match=re.fullmatch(r'(RNC|RNR)(50|55|60|65|70)([JHK])([0-9R]{4})([BDF])([MPRS])(B14|BSL|R36|R64|RE6|RSL)(\d{1,3})?',model)
    if match and resistance(match[4]) is not None:
        series,size,tcr,code,tol,failure,packing,special=match.groups()
        if packing=='R36' and size not in {'50','55','60'} or packing=='R64' and size not in {'65','70'}: return [],''
        packs={'B14':'锡铅端子／散装','BSL':'锡铅端子／散装／单一批次日期码',
               'R36':'锡铅端子／整盘编带','R64':'锡铅端子／整盘编带',
               'RE6':'锡铅端子／编带 1000 颗','RSL':'锡铅端子／编带／单一批次日期码'}
        segments=[part(series,'系列／引线',series+' 精密金属膜电阻；'+('可焊接及熔焊' if series=='RNC' else '仅可焊接')),
            part(size,'军标外形',series+size+' 外形代码（不是英制贴片尺寸）'),
            part(tcr,'温度系数',f"±{dict(J=25,H=50,K=100)[tcr]} ppm/℃"),
            part(code,'阻值',quantity(resistance(code))),part(tol,'阻值误差',tolerance(tol)),
            part(failure,'失效率等级',dict(M='1.0',P='0.1',R='0.01',S='0.001')[failure]+'%／1000 小时；不是阻值误差'),
            part(packing,'包装',packs[packing])]
        if special:
            known={'70':'4','50':'31','55':'65','65':'65','60':'201'}[size]==special
            segments.append(part(special,'特殊选项','引线热浸锡处理' if known else '原厂特殊订货编号；本资料未定义此具体编号',known))
        return segments,'Vishay 原厂 ERC（Military RNC/RNR），2025-09-04，文档 31025，第 2 页；失效率的当前可供等级须另向原厂确认。'
    return [],''


def pdc_faf(model):
    match=re.fullmatch(r'(FAF)(01|02|03|05|06|12|20|25)([TUABCDF])([TVUPX])([-TABCDERFGH])([0-9R]{4})([BCWVSQP])(-?)(HC|MH|MF|M)?',model)
    if not match or resistance(match[6]) is None: return [],''
    series,size,tol,packing,power,code,tcr,dash,special=match.groups()
    if dash and not special: return [],''
    sizes={'01':'0201','02':'0402','03':'0603','05':'0805','06':'1206','12':'1210','20':'2010','25':'2512'}
    standard={'01':'1/32','02':'1/16','03':'1/16','05':'1/10','06':'1/8','12':'1/4','20':'1/2','25':'3/4'}
    powers={'T':'1/20','A':'1/16','B':'1/10','C':'1/8','D':'1/4','E':'1/3','R':'2/5','F':'1/2','G':'3/4','H':'1'}
    packs={'T':'纸带／5000 颗','V':'纸带／10000 颗','U':'纸带／15000 颗',
           'P':'塑料带／4000 颗','X':'塑料带／8000 颗'}
    if (size in {'20','25'})!=(packing in {'P','X'}): return [],''
    segments=[part(series,'系列','精密薄膜贴片电阻'),part(size,'封装',sizes[size]+'（英制）'),
        part(tol,'阻值误差',tolerance(tol,dict(T='.01',U='.02',A='.05',B='.1',C='.25',D='.5',F='1'))),
        part(packing,'包装',packs[packing]),
        part(power,'功率',standard[size]+' W（此尺寸标准类型）' if power=='-' else powers[power]+' W（功能功率类型）'),
        part(code,'阻值',quantity(resistance(code))),
        part(tcr,'温度系数',f"±{dict(B=2,C=3,W=5,V=10,S=15,Q=25,P=50)[tcr]} ppm/℃")]
    if dash: segments.append(part(dash,'分隔符','特殊订货代码分隔符，不是负号'))
    if special:
        meanings={'HC':'抗硫化订货类型','M':'AEC-Q200 订货类型','MF':'抗硫化及 AEC-Q200 订货类型',
                  'MH':'氮化钽、抗硫化及 AEC-Q200 订货类型'}
        segments.append(part(special,'特殊订货类型',meanings[special]+'；代码本身不代替具体型号的认证记录'))
    return segments,'PSA／PDC 原厂 FAF Rev.7.0.M46，PDF 第 5 页（正文 4/7），功率见第 3 页；特殊订货代码见原厂 2020 三合一目录第 75 页（PDF 第 77 页）。不套用有歧义的三字符丝印规则。'


def pdc_thick_film(model):
    match=re.fullmatch(r'(FPS|FPF|FWF|FCF)(0A|01|02|03|05|06|12|20|25)([BCDFGJ])([TVUWPXYQ])([-EFGIK])([0-9R]{3,4})([NYLQP]?)(-?)(M|W)?',model)
    if not match: return [],''
    series,size,tol,packing,power,code,tcr,dash,special=match.groups()
    value=resistance(code)
    if value is None or value<1 and value!=0 or len(code)!=(3 if tol in 'GJ' else 4): return [],''
    sizes={'0A':'01005','01':'0201','02':'0402','03':'0603','05':'0805','06':'1206','12':'1210','20':'2010','25':'2512'}
    if series in {'FPS','FPF'}:
        if size not in {'03','05','06','12','20','25'} or tol not in 'FJ' or packing=='U' or tcr not in 'NYL' and tcr:
            return [],''
        if special not in {None,'M'} or dash and not special: return [],''
        boosts={'E':('03','1/3'),'F':('05','1/2'),'G':('06','3/4')}
        if series=='FPF': boosts.update(I=(None,'1.5'),K=('25','3'))
        if power!='-' and (power not in boosts or boosts[power][0] not in {None,size}): return [],''
        if packing=='Q' and (series!='FPF' or size!='25' or power!='K'): return [],''
        watts={'03':'1/8','05':'1/4','06':'1/2','12':'1/2','20':'1','25':'2'}[size] if power=='-' else boosts[power][1]
        description='高功率抗浪涌厚膜贴片电阻' if series=='FPS' else '高功率厚膜贴片电阻'
        ppm={'N':100,'Y':150,'L':200}
        page='63' if series=='FPS' else '62'
    elif series=='FWF':
        if size in {'0A','01'} or tol not in 'FJ' or power!='-' or tcr or special not in {None,'W'} or dash and not special or packing in 'UQ': return [],''
        watts={'02':'1/16','03':'1/10','05':'1/8','06':'1/4','12':'1/2','20':'1/2','25':'1'}[size]
        description='车用厚膜贴片电阻'
        ppm={}
        page='69'
    else:
        if power!='-' or tcr not in 'QP' and tcr or special or dash or packing=='Q': return [],''
        watts={'0A':'1/32','01':'1/20','02':'1/16','03':'1/10','05':'1/8','06':'1/4','12':'1/3','20':'3/4','25':'1'}[size]
        description='通用单颗厚膜贴片电阻（不是排阻或 FCF-E 低阻版本）'
        ppm={'Q':25,'P':50}
        page='70'
    packs={'T':'纸带／5000 颗','V':'纸带／10000 颗','U':'纸带／15000 颗','W':'纸带／20000 颗',
           'P':'塑料带／4000 颗','X':'塑料带／8000 颗','Y':'塑料带／16000 颗','Q':'塑料带／3000 颗'}
    segments=[part(series,'系列',description),part(size,'封装',sizes[size]+'（英制）'),part(tol,'阻值误差',tolerance(tol)),
        part(packing,'包装',packs[packing]),part(power,'功率',watts+' W（'+('标准' if power=='-' else '增强功率')+'类型；使用条件须按原厂表）'),
        part(code,'阻值',quantity(value))]
    if tcr: segments.append(part(tcr,'温度系数',f'±{ppm[tcr]} ppm/℃'))
    if dash: segments.append(part(dash,'分隔符','特殊订货代码分隔符，不是负号'))
    if special: segments.append(part(special,'特殊订货类型','抗硫化 H₂S 1000 ppm 类型' if special=='W' else 'AEC-Q200 订货类型；代码不代替具体型号认证记录'))
    return segments,'PSA／PDC 原厂 2020 三合一目录，'+series+' 分系列 Part Number 与额定表，正文第 '+page+' 页（PDF 第 '+str(int(page)+2)+' 页）。标准温漂未编码时不额外虚构一个温漂代码。'


def stackpole_resistor(model):
    match=re.fullmatch(r'(RNCF)(0201|0402|0603|0805|1206|1210|2010|2512)([TABCDF])([TK])([WYTSECD])([0-9RKM]{4})',model)
    if not match or not re.search('[RKM]',match[6]) or resistance(match[6]) is None: return [],''
    series,size,tol,packing,tcr,code=match.groups()
    pack=('7 英寸卷盘／1000 颗' if packing=='K' else
          '7 英寸纸带卷盘／'+('10000' if size in {'0201','0402'} else '5000')+' 颗' if size not in {'2010','2512'} else
          '7 英寸塑料带卷盘／4000 颗')
    return [part(series,'系列','精密薄膜贴片电阻'),part(size,'封装',size+'（英制）'),
        part(tol,'阻值误差',tolerance(tol)),part(packing,'包装',pack),
        part(tcr,'温度系数',f"±{dict(W=2,Y=5,T=10,S=15,E=25,C=50,D=100)[tcr]} ppm/℃"),
        part(code,'阻值',quantity(resistance(code)))], 'Stackpole 原厂署名 RNCF Series，2022-07-08，第 8 页 How to Order（欧洲网站存档）；T／K 包装与 T 温漂属于不同位置，不可混用。'


def taiyo_meas_mlcc(model):
    """MEAS only, original c_mlcc_E_e-E12R01 pages1--2."""
    match=re.fullmatch(r'(M)(E)(A)(S)([A-Z])(04|06|1L|10|16|21|31|32)([2358GLM])([A-Z])(B5|C6|D6)(\d{3}|\dR\d)([KM])([A-Z0-9]*)',model)
    if not match:return [],''
    group,category,kind,feature,volt,size,thick,dimension,material,cap,tol,tail=match.groups()
    volts={'P':'2.5','A':'4','J':'6.3','L':'10','E':'16'}
    sizes={'04':('0402','01005'),'06':('0603','0201'),'1L':('1005','0402'),'10':('1005','0402'),
           '16':('1608','0603'),'21':('2012','0805'),'31':('3216','1206'),'32':('3225','1210')}
    thickness={'2':'0.2','3':'0.3','5':'0.5','8':'0.8','G':'1.25','L':'1.6','M':'2.5'}
    dimensions={('32','M','A'):'L3.2±0.30、W2.5±0.30、T2.5±0.30 mm',
                ('06','3','B'):'L0.6±0.09、W0.3±0.09、T0.3±0.09 mm',
                ('21','G','B'):'L2.0+0.20/−0、W1.25+0.20/−0、T1.25+0.20/−0 mm',
                ('31','L','B'):'L3.2±0.30、W1.6±0.30、T1.6±0.30 mm',
                ('06','3','C'):'L0.6+0.15/−0.05、W0.3+0.15/−0.05、T0.3+0.15/−0.05 mm',
                ('10','5','C'):'L1.0+0.20/−0、W0.5+0.20/−0、T0.5+0.20/−0 mm',
                ('1L','3','N'):'L1.0+0.20/−0、W0.5+0.20/−0、T0.3±0.03 mm',
                ('10','5','N'):'L1.0+0.20/−0、W0.5+0.20/−0、T0.5+0.30/−0 mm',
                ('06','2','P'):'L0.6±0.09、W0.3±0.09、T0.2±0.02 mm',
                ('06','5','Q'):'L0.6±0.09、W0.3±0.09、T0.5±0.05 mm',
                ('04','2','S'):'L0.4±0.02、W0.2±0.02、T0.2±0.02 mm'}
    dimension_text=dimensions.get((size,thick,dimension))
    value=Decimal(cap.replace('R','.')) if 'R' in cap else Decimal(cap[:2])*10**int(cap[-1])
    segments=[part(group,'产品类型','多层陶瓷电容 MLCC'),part(category,'类别','仅移动设备用途（旧类别 E）；不能当成车规；2026年类别合并不在此自动改号'),
        part(kind,'结构','双端子'),part(feature,'特性','标准／通用'),
        part(volt,'额定电压',volts[volt]+' VDC' if volt in volts else '该电压码未在本表核实',volt in volts),
        part(size,'封装','公制 '+sizes[size][0]+'／英制 '+sizes[size][1]),part(thick,'厚度',thickness[thick]+' mm（标称值）'),
        part(dimension,'尺寸公差',dimension_text or '此尺寸／厚度组合未列于本表，需具体型号规格书',bool(dimension_text)),
        part(material,'温度特性',{'B5':'EIA X5R：−55～85℃、±15%；另列 JIS B 条件，二者不可混用',
             'C6':'EIA X6S：−55～105℃、±22%','D6':'EIA X6T：−55～105℃、+22/−33%'}[material]),
        part(cap,'容量',quantity(value,'pF')),part(tol,'容量误差',tolerance(tol))]
    packages={'A':'φ178mm 编带卷盘','F':'φ178mm 编带卷盘，2mm 节距','T':'φ178mm 编带卷盘，4mm 节距',
              'P':'φ178mm 编带卷盘，4mm 节距、1000颗／盘（3225／厚度M）','W':'φ178mm 压纹带卷盘，1mm 节距（0201／0402公制）'}
    if tail:
        segments.append(part(tail[0],'包装',packages.get(tail[0],'未公开于本版的包装代码'),tail[0] in packages))
        segments.append(part(tail[1:],'内部代码','原厂将此段定义为内部代码，未公开逐字符含义；需原厂确认',False))
    else:
        segments.append(part('','订货尾码','输入缺少包装和内部代码；不能自动补成完整订货型号',False))
    return segments,'太阳诱电原厂 c_mlcc_E_e-E12R01，第1–2页 MEAS 命名表；仅解释代码，不证明当前可订购或当前生产状态。'


def walsin_general_mlcc(model):
    match=re.fullmatch(r'(0201|0402|0603|0805|1206|1210|1812)([NBFXSA])(\d{3}|\dR\d)([ABCDFGJKM])(4R0|6R3|\d{3})([A-Z0-9]*)',model)
    if not match:return [],''
    size,material,cap,tol,volt,tail=match.groups()
    volts={'4R0':'4','6R3':'6.3','100':'10','160':'16','250':'25','350':'35','500':'50','101':'100'}
    value=Decimal(cap.replace('R','.')) if 'R' in cap else Decimal(cap[:2])*10**int(cap[-1])
    tol_text={'A':'±0.05 pF','B':'±0.1 pF','C':'±0.25 pF','D':'±0.5 pF'}.get(tol) or tolerance(tol)
    segments=[part(size,'封装',size+'（英制）'),part(material,'介质',dict(N='NP0 / C0G',B='X7R',F='Y5V',X='X5R',S='X6S',A='X7S')[material]),
              part(cap,'容量',quantity(value,'pF')),part(tol,'容量误差',tol_text),
              part(volt,'额定电压',volts[volt]+' VDC' if volt in volts else '此电压码未列于本版通用订货表',volt in volts)]
    if tail in {'CT','CG'}:
        segments.extend([part('C','端电极','Cu / Ni / Sn'),part(tail[1],'包装','7 英寸卷盘' if tail[1]=='T' else '13 英寸卷盘')])
    else:segments.append(part(tail,'订货尾码','缺少或尚未核实的端电极／包装尾码，须原厂确认',False))
    return segments,'华科原厂 ASC_General Purpose Series，2026-10，第2页 HOW TO ORDER；不可与 MT 或信昌的代码表混用。'


def walsin_mt_mlcc(model):
    """MT only: original September 2026 table, not PDC's overlapping MT."""
    match=re.fullmatch(r'(MT)(03|15|18|21|31|32)([GNBS])(\d{3}|\dR\d)([ABCDFGJKM])(6R3|12E|\d{3})([A-Z0-9]*)',model)
    if not match:return [],''
    series,size,material,cap,tol,voltage,tail=match.groups()
    sizes={'03':'0201','15':'0402','18':'0603','21':'0805','31':'1206','32':'1210'}
    volts={'6R3':'6.3','100':'10','160':'16','250':'25','500':'50','101':'100',
           '201':'200','251':'250','501':'500','631':'630','102':'1000','12E':'1250'}
    cap_value=Decimal(cap.replace('R','.')) if 'R' in cap else Decimal(cap[:2])*10**int(cap[-1])
    tol_text={'A':'±0.05 pF','B':'±0.1 pF','C':'±0.25 pF','D':'±0.5 pF'}.get(tol) or tolerance(tol)
    segments=[part(series,'系列','MT 车规安全用途系列；原厂标示 AEC-Q200 资格，不代表逐型号当前生产状态'),
              part(size,'封装',sizes[size]+'（英制）'),part(material,'介质',dict(G='X8G',N='NP0 / C0G',B='X7R',S='X6S')[material]),
              part(cap,'容量',quantity(cap_value,'pF')),part(tol,'容量误差',tol_text),
              part(voltage,'额定电压',volts[voltage]+' VDC' if voltage in volts else '此电压代码未列于本版订货表',voltage in volts)]
    if tail in {'CT','CG'}:
        segments.extend([part('C','端电极','Cu / Ni / Sn'),part(tail[1],'包装','7 英寸卷盘' if tail[1]=='T' else '13 英寸卷盘')])
    else:
        segments.append(part(tail,'完整订货尾码','基本料号缺少完整尾码，或此附加码未列于本版；须原厂确认',False))
    return segments,'Walsin 原厂 ASC_Automotive Cap_(MT)，2026-09，第2页 HOW TO ORDER；具体可供组合仍须核对实际型号目录。'


def yageo_cc_x7r(model):
    """Only the published CC X7R 6.3--250V table, not other CC families."""
    match=re.fullmatch(r'(CC)(0201|0402|0603|0805|1206|1210|1812|2220)([JKM])([RKPF])(X7R)([567890AY])(BB)(\d{3}|\dR\d)',model)
    if not match:return [],''
    series,size,tol,packing,material,voltage,process,cap=match.groups()
    volts=dict(zip('567890AY',('6.3','10','16','25','50','100','200','250')))
    packages={'R':'纸／PE 编带，7 英寸卷盘','K':'压纹带，7 英寸卷盘',
              'P':'纸／PE 编带，13 英寸卷盘','F':'压纹带，13 英寸卷盘'}
    value=Decimal(cap.replace('R','.')) if 'R' in cap else Decimal(cap[:2])*10**int(cap[-1])
    return [part(series,'系列','CC 通用／高容 MLCC'),part(size,'封装',size+'（英制）'),
            part(tol,'容量误差',tolerance(tol)),part(packing,'包装',packages[packing]),
            part(material,'介质','X7R'),part(voltage,'额定电压',volts[voltage]+' VDC'),
            part(process,'工艺／端电极代码','本版订货图列为 BB，但未分别解释两个 B 的定义；需原厂代码表，不能由库内参数倒推',False),
            part(cap,'容量',quantity(value,'pF'))], 'YAGEO 原厂 General Purpose & High Capacitance X7R 6.3V–250V，2026-03-06 V27，第2页；BB 逐位定义未公开于该页，故不标为完整解释。'


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
            if not segments:
                segments,source=yageo_mfr(model)
    elif resistor and any(token in manufacturer for token in ('WALSIN','华新科','華新科','华科')):
        segments,source=walsin_resistor(model)
    elif resistor and any(token in manufacturer for token in ('PDC','PSA','信昌')):
        segments,source=pdc_faf(model)
        if not segments: segments,source=pdc_fcf_array(model)
        if not segments: segments,source=pdc_thick_film(model)
    elif resistor and 'KOA' in manufacturer:
        segments,source=koa_resistor(model)
    elif resistor and any(token in manufacturer for token in ('VISHAY','威世')):
        segments,source=vishay_resistor(model)
    elif resistor and 'STACKPOLE' in manufacturer:
        segments,source=stackpole_resistor(model)
    elif mlcc and any(token in manufacturer for token in ('WALSIN','华新科','華新科','华科')):
        segments,source=walsin_mt_mlcc(model)
        if not segments:
            segments,source=walsin_general_mlcc(model)
    elif mlcc and any(token in manufacturer for token in ('YAGEO','国巨','國巨')):
        segments,source=yageo_cc_x7r(model)
    elif mlcc and any(token in manufacturer for token in ('TAIYO','太阳诱电','太陽誘電')):
        segments,source=taiyo_meas_mlcc(model)
    elif mlcc and any(token in manufacturer for token in ('MURATA','村田')):
        match = re.fullmatch(r'(GRM|GCM|GCJ|GJM|GQM|GRT|GCG|GCQ)([A-Z0-9]{2})(.)([A-Z0-9]{2})([A-Z0-9]{2})(\d{3}|R\d{2})([BCDFGJKMZ])([A-Z0-9]+)',model)
        if match:
            series,size,thickness,material,voltage,cap,tol,tail=match.groups()
            sizes={'01':('008004','0.25×0.125'),'02':('01005','0.4×0.2'),
                   '0D':('015015','0.38×0.38'),'0Y':('0202','0.6×0.6'),'MD':('015008','0.5×0.25'),
                   '03':('0201','0.6×0.3'),'05':('0202','0.5×0.5'),'08':('0303','0.8×0.8'),
                   '1U':('02404','0.6×1.0'),'15':('0402','1.0×0.5'),'18':('0603','1.6×0.8'),
                   'JN':('0704','1.8×1.0'),'21':('0805','2.0×1.25'),'22':('1111','2.8×2.8'),
                   '31':('1206','3.2×1.6'),'32':('1210','3.2×2.5'),'42':('1808','4.5×2.0'),
                   '43':('1812','4.5×3.2'),'52':('2211','5.7×2.8'),'55':('2220','5.7×5.0'),
                   '86':('-','8.0×6.0')}
            # The cited table excludes KR*/KC*/EVA; this branch supports none
            # of those families. These are nominal code values, not tolerances.
            thicknesses={'1':'0.125','2':'0.2','3':'0.3','4':'0.4','5':'0.5','6':'0.6',
                         '7':'0.7','8':'0.8','9':'0.85','A':'1.0','B':'1.25','C':'1.6',
                         'D':'2.0','E':'2.5','K':'0.08','M':'1.15','Q':'1.5','S':'0.16',
                         'T':'0.18','Y':'0.135'}
            packages={'L':'φ180 mm 卷盘／压纹带','D':'φ180 mm 卷盘／纸带',
                      'E':'φ180 mm 卷盘／纸带','W':'φ180 mm 卷盘／纸带',
                      'K':'φ330 mm 卷盘／压纹带','J':'φ330 mm 卷盘／纸带',
                      'F':'φ330 mm 卷盘／纸带','T':'散装托盘'}
            materials={'B1':'C0G','C1':'C0G','5C':'C0G','R6':'X5R','R7':'X7R','R9':'X8R','C6':'X5S','C7':'X7S','C8':'X6S','D6':'X5T','D7':'X7T','D8':'X6T'}
            volts={'0E':2.5,'0G':4,'0J':6.3,'1A':10,'1C':16,'1E':25,'1H':50,'1J':63,'2A':100,'2D':200,'2E':250,'2H':500,'3A':1000}
            cap_value = Decimal(cap.replace('R','.')) if 'R' in cap else Decimal(cap[:2])*10**int(cap[-1])
            tol_value = {'B':'±0.1 pF','C':'±0.25 pF','D':'±0.5 pF','Z':'-20%～+80%'}.get(tol) or tolerance(tol)
            segments=[part(series,'系列',text(record.get('系列说明')) or 'Murata '+series+' 系列'),
                part(size,'封装',sizes[size][0]+'（英制）；长×宽 '+sizes[size][1]+' mm（标称值）' if size in sizes else '该尺寸代码尚未核验',size in sizes),
                part(thickness,'厚度代码',thicknesses[thickness]+' mm（标称值；具体公差及最大厚度以该型号规格书为准）' if thickness in thicknesses else '按个别规格定义，须查具体型号规格书' if thickness=='X' else '该厚度代码尚未核验',thickness in thicknesses),
                part(material,'介质',materials.get(material,'该介质代码尚未核验'),material in materials),
                part(voltage,'额定电压',str(volts[voltage])+' V' if voltage in volts else '该电压代码尚未核验',voltage in volts),
                part(cap,'容量',quantity(cap_value,'pF')),part(tol,'容量误差',tol_value)]
            if re.fullmatch(r'[A-Z0-9]{3}[A-Z]',tail):
                segments.extend([
                    part(tail[:3],'个别规格识别码','原厂定义为三位个别规格识别码；公开命名表未逐字定义其内部含义，不作推测',False),
                    part(tail[3:],'包装',packages.get(tail[3:],'该包装代码尚未核验'),tail[3:] in packages)])
            else:
                segments.append(part(tail,'产品／包装尾码','尾码不符合已核验的三位规格识别码加一位包装码结构，须查具体型号订货表',False))
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
    complete=bool(segments) and all(row['verified'] for row in segments)
    links=[]
    if segments and mlcc and any(token in manufacturer for token in ('TAIYO','太阳诱电','太陽誘電')):
        links=[('太阳诱电原厂 MEAS 命名表','https://www.yuden.co.jp/en/product/support/pdf_spice_spara/upload/c_mlcc_E_e.pdf'),
               ('太阳诱电2026类别合并通知（不自动改型号）','https://www.yuden.co.jp/en/news/category/change_to_part_numbers.html')]
    elif segments and mlcc and any(token in manufacturer for token in ('MURATA','村田')):
        links=[('村田原厂命名表入口（含尺寸、厚度、包装）','https://www.murata.com/en-eu/support/faqs/capacitor/ceramiccapacitor/part/0001'),
               ('村田原厂个别规格识别码说明','https://www.murata.com/en-eu/support/faqs/capacitor/ceramiccapacitor/part/0011')]
    elif segments and mlcc and any(token in manufacturer for token in ('WALSIN','华新科','華新科','华科')):
        links=([('华科原厂 MT 命名表（2026-09，第2页）','https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_Automotive_MT.pdf')]
               if model.startswith('MT') else [('华科原厂通用 MLCC 命名表（第2页）','https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_General_Purpose.pdf')])
    elif segments and mlcc and any(token in manufacturer for token in ('YAGEO','国巨','國巨')):
        links=[('YAGEO CC X7R 原厂命名表（2026-03-06 V27，第2页）','https://yageogroup.com/content/datasheet/asset/file/UPY-GPHC_X7R_6_3V-TO-250V')]
    elif segments and resistor and any(token in manufacturer for token in ('YAGEO','国巨')) and model.startswith('MFR'):
        links=[('YAGEO MFR 原厂订货表（2024-04-03 V4，第2页）','https://yageogroup.com/content/datasheet/asset/file/YAGEO-MFR_DATASHEET')]
    elif segments and resistor and 'YAGEO' in manufacturer and model.startswith('RT'):
        links=[('YAGEO RT 原厂命名表（2026-02-12 V17，第2页）','https://www.yageogroup.com/content/datasheet/asset/file/PYU-RT_1-TO-0-01_ROHS_L')]
    elif segments and 'KOA' in manufacturer:
        links=[('KOA 原厂 RN73 命名表','https://www.koaspeer.com/pdfs/RN73.pdf')] if model.startswith('RN73') and not model.startswith(('RN73H','RN73R')) else [('KOA 原厂 2026 目录','https://www.koaspeer.com/pdfs/KOA_2026FullCatalog_Linked.pdf')]
    elif segments and any(token in manufacturer for token in ('VISHAY','威世')):
        pdf='20035/dcrcwe3.pdf' if model.startswith('CRCW') else '28758/tnpw_e3.pdf' if model.startswith('TNPW') else '31018/cmfind.pdf' if model.startswith('CMF') else '31025/erc.pdf'
        for document,path in (('20008','20008/dcrcw.pdf'),('20115','20115/crcwhp.pdf'),('20043','20043/crcwhpe3.pdf')):
            if '文档 '+document in source:pdf=path
        links=[('Vishay 原厂命名表','https://www.vishay.com/docs/'+pdf)]
        if model.startswith('CMF'): links.append(('Vishay 原厂轴向包装表','https://www.vishay.com/docs/31544/packthre.pdf'))
    elif segments and model.startswith('FAF') and any(token in manufacturer for token in ('PDC','PSA','信昌')):
        links=[('PDC 原厂 FAF 命名表','https://www.pdc.com.tw/storage/architecture/product~~19/product~~105/product~~160/FAF.pdf'),
               ('PDC 原厂特殊订货代码表','https://www.pdc.com.tw/storage/architecture/product~~19/product~~123/2020_3in1_catalog.pdf')]
    elif segments and resistor and any(token in manufacturer for token in ('PDC','PSA','信昌')) and model.startswith(('FPS','FPF','FWF','FCF')) and not re.match(r'FCF\d{3}',model):
        links=[('PDC 原厂分系列命名表','https://www.pdc.com.tw/storage/architecture/product~~19/product~~123/2020_3in1_catalog.pdf')]
    elif segments and 'STACKPOLE' in manufacturer:
        links=[('Stackpole 原厂署名 RNCF 命名表（欧洲存档）','https://stackpole-europe.com/specs/SEI-RNCF.pdf')]
    return dict(model=model,brand=brand,series=text(record.get('系列')),segments=segments,source=source,source_links=links,
                complete=complete,verified_segments=sum(bool(row['verified']) for row in segments),
                status='本型号逐码解释完整' if complete else '本型号仍有代码待核验' if segments else '该系列逐码规则尚未核验')


def guide_html(guide):
    escape=lambda value:html.escape(str(value),quote=True)
    segments=guide['segments']
    if not segments:
        return '<div class="naming-empty">该系列的逐码命名规则尚未核验，暂不把库内参数反写成代码含义。</div>'
    verified=sum(bool(s['verified']) for s in segments)
    status=('本型号逐码解释完整' if verified==len(segments) else f'已核验 {verified}／{len(segments)} 段，尚未完整')
    chips=''.join('<div class="naming-chip'+(' naming-unknown' if not s['verified'] else '')+'"><code>'+escape(s['code'])+'</code><span>'+escape(s['name'])+'</span></div>' for s in segments)
    rows=''.join('<tr><td><code>'+escape(s['code'])+'</code></td><td>'+escape(s['name'])+'</td><td>'+escape(s['meaning'])+(' <small>待核验</small>' if not s['verified'] else '')+'</td></tr>' for s in segments)
    links=' · '.join('<a href="'+escape(url)+'" target="_blank" rel="noopener noreferrer">'+escape(label)+'</a>'
                     for label,url in guide.get('source_links',[]) if re.fullmatch(r'https://[a-zA-Z0-9.-]+/[^\s<>]*',url))
    return '<p class="naming-source">'+status+'</p><div class="naming-chips">'+chips+'</div><div class="naming-table-wrap"><table class="naming-table"><thead><tr><th>代码</th><th>字段</th><th>含义／本例解读</th></tr></thead><tbody>'+rows+'</tbody></table></div><p class="naming-source">依据：'+escape(guide['source'])+'</p>'+('<p class="naming-source">'+links+'</p>' if links else '')


STYLE='''<style>
.section-title.naming-inline-title{margin:0}
[data-testid="stMarkdownContainer"]:has(>.naming-inline-title){margin-bottom:0}
[data-testid="stPopoverBody"]:has(.naming-guide-marker){width:min(760px,calc(100vw - 24px));max-height:80vh;overflow:auto;padding:12px 18px 16px}
[data-testid="stPopoverBody"]:has(.naming-guide-marker) [data-testid="stVerticalBlock"]{gap:12px}
.naming-guide-title{font-size:19px;font-weight:700;color:#17365c;margin:0}
.naming-chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 12px}
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
    try:
        row=st.container(horizontal=True,vertical_alignment='center',gap='small')
        content_width=dict(width='content')
    except TypeError:
        # Older Streamlit has no horizontal container/content-width API.
        # Stack accessibly instead of reserving a fixed fraction of the row.
        row=st.container()
        content_width={}
    with row:
        st.markdown('<div class="section-title naming-inline-title">'+html.escape(title)+'</div>',unsafe_allow_html=True,**content_width)
        with st.popover('型号命名对照',help='查看本次匹配结果中各品牌、系列的代码含义'):
            st.markdown('<div class="naming-guide-title naming-guide-marker">型号命名对照</div>',unsafe_allow_html=True)
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


def render_part_header(title, source_frame, matched_frame, instance_key):
    """Use only source and alternatives actually displayed for this input."""
    records=public_candidates(source_frame)+public_candidates(matched_frame)
    render_header(title,records,instance_key)
