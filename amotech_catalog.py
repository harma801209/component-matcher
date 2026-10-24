"""Source-backed AMOTECH ordering rules and explicitly listed catalogue models.

Decoding an ordering code does NOT establish catalogue membership, availability,
qualification, lifecycle or a price. Only captured manufacturer records enter
the searchable/filterable catalogue. See docs/amotech_coverage.md.
"""
from functools import lru_cache
from pathlib import Path
import json
import re

BRAND = 'AMOTECH(阿莫泰克)'
DATA = Path(__file__).with_name('catalog_sources') / 'amotech_verified.json'
NUMBERING = 'https://ts.amotech.co.kr/assets/productInfo/part-numbering-mlcc.pdf'
MATERIAL = {
    'C': ('C0G', 125), 'T': ('X8G', 150), 'X': ('X5R', 85),
    'S': ('X7R', 125), 'H': ('X7R', 125), 'B': ('X7R (AMO)', 125),
    'E': ('X8R', 150), '1': ('X6S', 105), '2': ('X7S', 125),
    '3': ('X7T', 125), '4': ('X8S', 150), '5': ('X8L', 150), '6': ('X8T', 150),
}
SIZE = {
    '0X': ('01005','0402',0.4,0.2), '01': ('0201','0603',0.6,0.3),
    '02': ('0402','1005',1.0,0.5), '03': ('0603','1608',1.6,0.8),
    '05': ('0805','2012',2.0,1.25), '06': ('1206','3216',3.2,1.6),
    '10': ('1210','3225',3.2,2.5), '12': ('1812','4532',4.5,3.2),
    '20': ('2220','5750',5.7,5.0),
}
THICKNESS = dict(zip('ZABCDEFGHJKLM', (.135,.5,.6,.85,1.15,1.25,1.4,1.,1.6,1.8,2.,2.5,2.7)))
THICKNESS.update({'S':2.8, 'W':6.4})
# 2B is explicitly 200 / 250 V on p.4, although p.1 says 250 V. Only an
# exact manufacturer model record may resolve it. Never choose the larger one.
VOLTAGE = {'02':2.5,'04':4,'06':6.3,'10':10,'16':16,'25':25,'35':35,
           '50':50,'75':75,'1B':100,'4B':450,'5B':500,'6B':630,
           '8B':800,'1C':1000,'1H':1500,'2C':2000,'2H':2500,'3C':3000}
TOLERANCE = {'Z':'0.01pF','P':'0.02pF','T':'0.025pF','Q':'0.03pF',
             'A':'0.05pF','B':'0.1pF','C':'0.25pF','D':'0.5pF',
             'F':'1','G':'2','J':'5','K':'10','M':'20'}
DESIGN = {'N':'常规设计','P':'Open mode','F':'Floating design','A':'低声噪设计','E':'ESD设计'}
ELECTRODE = {'N':'Ni/Cu/Sn','F':'软端子 Ni/Cu/Ag epoxy/Sn',
             'W':'软端子 VW80808','G':'镀金 Ni/Cu/Au','T':'薄金 Ni/Cu/Au',
             'M':'水平金属框架','V':'垂直金属框架','P':'Ni/Cu/SnPb',
             'E':'软端子 Ni/Cu/Ag epoxy/SnPb'}
PACKING = {'B':'散装','D':'180mm 纸带','J':'330mm 纸带',
           'L':'180mm 压纹带','K':'330mm 压纹带','T':'托盘'}
APPLICATION = {'C':'商用','G':'工业／通信','A':'汽车应用'}
STANDARD = re.compile(r'^AC(?P<material>[CTXSHBE1-6])(?P<size>0X|01|02|03|05|06|10|12|20)'
                      r'(?P<thickness>[XZABCDEFGHJKLM SWT])(?P<voltage>[0-9][0-9BCH])'
                      r'(?P<design>[NPFAE])(?P<cap>[0-9R]{3})(?P<tol>[ZPTQABCDFGJKM])'
                      r'(?P<electrode>[NFWGTMVPE])(?P<packing>[BDJLKT])(?P<application>[CGA])$'.replace(' ',''))
HIGH_Q = re.compile(r'^(?P<series>A60[ZLSF]|A80B)(?P<cap>[0-9R]{3})'
                    r'(?P<tol>[ABCDFGJKM])(?P<terminal>TN|T)(?P<voltage>[0-9]{2,4})(?P<laser>X?)T$')
LEGACY_SOURCE = 'https://www.mrc-gigacomp.de/pdfs/Amotech_EMI-ESD%20Catalogue(080603).pdf'
EXISTING_PROTECTION_MODELS = frozenset(('AVLC18S02003','AVLC18S02015','AVLC3N01100','AVLC5S02100','HESP02100ES1'))
SPECIAL_KINDS = frozenset(('ESD保护器件','EMI／ESD滤波器','RF耦合器'))
SPECIAL_TABLE = 'components_search_amotech_special'
SPECIAL_DETAIL_ONLY = frozenset(('电容定义／测试条件','压敏／击穿电压及条件','电气参数说明',
                                 '分段电气参数','功率条件','引脚／端口','官网链接'))
SPECIAL_NUMERIC = ('最大连续工作电压（V）','寄生电容量（pF）','串联电阻（Ω）','截止频率（MHz）',
                   '频段下限（MHz）','频段上限（MHz）','标称耦合（dB）','平均功率（W）')
SPECIAL_TEXT = ('系列','结构','尺寸（inch）','本体尺寸（mm）','回路数','安装方式','电容定义／测试条件',
                '压敏／击穿电压及条件','电气参数说明','分段电气参数','功率条件','引脚／端口',
                '工作温度','已列频段（MHz）','资料版本','资料状态','官网链接')


def decode_legacy_protection(model, brand=''):
    """Historical ordering semantics, NOT current catalogue membership.

    Protection/filter networks have their own pinout and voltage definitions.
    Never feed these partial records into the ordinary MLCC/TVS matcher.
    Existing exact library records continue through their original lookup.
    """
    model = key(model)
    if brand and not is_brand(brand) or model in EXISTING_PROTECTION_MODELS:
        return None
    fields = {}
    match = re.fullmatch(r'(ASES)12U(02|03)(0R2)',model)
    if match:
        fields = {'系列':match[1],'最大连续工作电压（V）':12,'寄生电容量（pF）':.2,
                  '结构':'单通道聚合物 ESD 抑制器','编码尺寸':match[2]}
    match = re.fullmatch(r'(AMES)12U(05)Q(0R2)',model)
    if match:
        fields = {'系列':match[1],'最大连续工作电压（V）':12,'寄生电容量（pF）':.2,
                  '结构':'四通道聚合物 ESD 抑制器','回路数':'4','编码尺寸':match[2]}
    match = re.fullmatch(r'(AD(?:UC|LC|MC))(5|10|30|40)(S|M)(02|03)([0-9R]{3})',model)
    if match:
        fields = {'系列':match[1],'最大连续工作电压（V）':5.5 if match[2]=='5' else int(match[2]),
                  '寄生电容量（pF）':float(match[5].replace('R','.')),
                  '压敏电压误差编码':match[3],'结构':'金属氧化物 ESD 保护器件','编码尺寸':match[4]}
    match = re.fullmatch(r'(AVL|AVLC)(5|10|14|18)(S|K|L|M)(01|02|03)([0-9]{3})',model)
    if match and not (match[1]=='AVL' and match[4]=='01'):
        fields = {'系列':match[1],'最大连续工作电压（V）':5.5 if match[2]=='5' else int(match[2]),
                  '压敏电压误差编码':match[3],'结构':'多层片式压敏电阻','编码尺寸':match[4]}
        fields['寄生电容量（pF）' if match[1]=='AVLC' else '峰值电流（A）'] = int(match[5])/(1 if match[1]=='AVLC' else 10)
    match = re.fullmatch(r'(AVNC|AVSC)(5|14|18)S(03|04|05)(Q|F|E)([0-9]{3})',model)
    if match and ((match[1]=='AVNC' and match[3] in {'03','05'} and match[4]=='Q') or
                  (match[1]=='AVSC' and (match[3],match[4]) in {('04','F'),('05','E')})):
        fields = {'系列':match[1],'最大连续工作电压（V）':5.5 if match[2]=='5' else int(match[2]),
                  '寄生电容量（pF）':int(match[5]),'结构':'多层阵列压敏电阻',
                  '回路数':'8' if match[4]=='E' else '4','编码尺寸':match[3]}
    match = re.fullmatch(r'(SR)(5|10|30|40)(S|M)(02|03)(010|020|030|050)(010|050|100)R',model)
    if match:
        fields = {'系列':match[1],'最大连续工作电压（V）':5.5 if match[2]=='5' else int(match[2]),
                  '电容标称／合计（pF）':int(match[5]),'串联电阻（Ω）':int(match[6]),
                  '结构':'单通道 RC 保护网络',
                  '编码尺寸':match[4]}
    match = re.fullmatch(r'(SF)(5|10|30|40)(S|M)(02|03)(010|030|050|100)',model)
    if match:
        fields = {'系列':match[1],'最大连续工作电压（V）':5.5 if match[2]=='5' else int(match[2]),
                  '寄生电容量（pF）':int(match[5]),'结构':'单通道穿心保护网络','编码尺寸':match[4]}
    match = re.fullmatch(r'(AMLV)(5|14|18)(S|M)(03)Q([0-9]{3})([0-9]{3})F',model)
    if match:
        fields = {'系列':match[1],'最大连续工作电压（V）':5.5 if match[2]=='5' else int(match[2]),
                  '寄生电容量（pF）':int(match[5]),'典型截止频率（MHz）':int(match[6]),
                  '结构':'四通道 LC EMI/ESD 网络','回路数':'4','编码尺寸':match[4]}
    match = re.fullmatch(r'(AVRC)(5|14|18)S(03|04|05)(Q|D)([0-9]{3})(010|050|100)R',model)
    if match and ((match[3] in {'03','05'} and match[4]=='Q') or (match[3]=='04' and match[4]=='D')):
        fields = {'系列':match[1],'最大连续工作电压（V）':5.5 if match[2]=='5' else int(match[2]),
                  '电容标称／合计（pF）':int(match[5]),'串联电阻（Ω）':int(match[6]),
                  '结构':'RC EMI/ESD 网络','回路数':'2' if match[4]=='D' else '4','编码尺寸':match[3]}
    match = re.fullmatch(r'(AVFC)(5|12|14)S(03|04|05)(Q|D)([0-9]{3})',model)
    if match and ((match[3] in {'03','05'} and match[4]=='Q') or (match[3]=='04' and match[4]=='D')):
        fields = {'系列':match[1],'最大连续工作电压（V）':5.5 if match[2]=='5' else int(match[2]),
                  '电容标称／合计（pF）':int(match[5]),'结构':'穿心 EMI/ESD 网络',
                  '回路数':'2' if match[4]=='D' else '4','编码尺寸':match[3]}
    if not fields:
        return None
    return {'品牌':BRAND,'型号':model,'器件类型':'ESD／EMI保护网络',**fields,
            '_unsupported_component':True,'_catalog_membership':'historical_rule_only',
            '_model_rule_authority':'amotech_historical_numbering',
            '_unsupported_reason':f"已识别 AMOTECH {fields['系列']} 历史命名规则；此型号的完整原厂参数与当前目录尚待核验，不能当作普通电容或 TVS 自动替代。",
            '备注1':f'原厂署名 2008 EMI/ESD 历史目录（公开镜像）：{LEGACY_SOURCE}',
            '备注2':'最大连续工作电压不是压敏电压／触发电压／钳位电压；须另外核验测试条件、通道和引脚。'}


def key(value):
    return re.sub(r'\s+', '', str(value or '')).upper()


def is_brand(value):
    return 'AMOTECH' in str(value).upper() or '阿莫泰克' in str(value)


def rf_confirmation_required(candidate, target):
    def rf(row):
        return is_brand(row.get('品牌','')) and key(row.get('型号','')).startswith(('ABCU','A60Z','A60L','A60S','A60F','A80B'))
    if not (rf(candidate) or rf(target)):
        return False
    return not (is_brand(candidate.get('品牌','')) and is_brand(target.get('品牌',''))
                and key(candidate.get('型号','')) == key(target.get('型号','')))


@lru_cache(maxsize=1)
def payload():
    return json.loads(DATA.read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def by_model():
    return {key(r['型号']): r for r in payload()['records']}


def quarantine_notice(model):
    compact = key(model)
    for row in payload()['quarantined']:
        if compact == row['model']:
            reason = row.get('detail') or f"原厂选型表的容差 {row.get('displayed_tolerance')} 与料号编码 {row.get('encoded_tolerance')}% 不一致"
            return {'品牌':BRAND,'型号':compact,'器件类型':row.get('kind','MLCC'),'_unsupported_component':True,
                    '_unsupported_reason':f"AMOTECH {reason}，已暂隔离，需人工核验原厂规格书。"}
    return None


def catalogue_rows():
    return [dict(r, **({'容值_pf':r['容值']} if '容值' in r else {})) for r in payload()['records']]


def special_record(model, brand=''):
    if brand and not is_brand(brand):
        return None
    row = by_model().get(key(model))
    return dict(row) if row and row.get('器件类型') in SPECIAL_KINDS else None


def decode_rf(model):
    """Field semantics only. Frequency/design codes are NOT numeric ratings."""
    match = re.fullmatch(r'(CXH|CXD)([0-9]{2})([NTFS])([0-9]{4})([A-Z]{2})',model)
    if not match:
        return None
    return {'品牌':BRAND,'型号':model,'器件类型':'RF耦合器','系列':match[1],
            '标称耦合（dB）':int(match[2]),'封装编码':match[3],
            '频段编码':match[4],'设计编码':match[5],
            '_catalog_membership':'rule_only','_unsupported_component':True,
            '_unsupported_reason':'已识别 AMOTECH RF 五段编码；频段、设计、端口和完整规格须查具体料号规格书，不能凭频段编码推算额定参数或生成替代料号。'}


def cap_pf(code):
    if re.fullmatch(r'[0-9]{3}', code):
        return int(code[:2]) * 10 ** int(code[2])
    if re.fullmatch(r'(?:[0-9]R[0-9]|R[0-9]{2})', code):
        return float(code.replace('R','.'))
    return None


def base_record(model):
    return {'品牌':BRAND, '型号':model, '器件类型':'MLCC', '安装方式':'贴片',
            '_model_rule_authority':'amotech_official_numbering',
            '_catalog_membership':'rule_only',
            '备注2':'按原厂命名规则解析；未收录的组合需向原厂确认，不能据此认定可订购、在产或已认证。'}


def decode_standard(model):
    match = STANDARD.fullmatch(model)
    if not match:
        return None
    g = match.groupdict()
    value = cap_pf(g['cap'])
    if not value or g['voltage'] not in VOLTAGE and g['voltage'] != '2B':
        return None
    if g['material']=='H' and g['voltage']!='2B' and VOLTAGE[g['voltage']]<100:
        return None
    material, high = MATERIAL[g['material']]
    inch, metric, length, width = SIZE[g['size']]
    thickness = width if g['thickness'] == 'X' else THICKNESS.get(g['thickness'])
    row = base_record(model)
    features = []
    if g['material'] == 'H':
        features.append('高压')
    if g['electrode'] in {'F','W','E'}:
        features.append('软端子')
    if g['electrode'] in {'M','V'}:
        features.append('金属框架')
    # Application encoding is NOT a blanket AEC-Q200 certification.
    if g['application'] == 'A':
        features.append('汽车应用（认证须查具体型号）')
    if g['design'] != 'N':
        features.append(DESIGN[g['design']])
    row.update({'系列':'AC'+g['material'], '系列说明':f'AMOTECH {material} MLCC',
                '特殊用途':' | '.join(features), '尺寸（inch）':inch, '尺寸（mm）':metric,
                '材质（介质）':material, '容值':value, '容值_pf':value, '容值单位':'pF',
                '容值误差':TOLERANCE[g['tol']], '耐压（V）':VOLTAGE.get(g['voltage'],''),
                '工作温度':f'-55~{high}℃', '长度（mm）':f'{length:g}', '宽度（mm）':f'{width:g}',
                '厚度（mm）':f'{thickness:g}' if thickness is not None else '',
                '备注1':f'原厂命名表 Rev.10N (2026-06-09)：{NUMBERING}；'
                         f"设计 {g['design']}={DESIGN[g['design']]}；端子 {g['electrode']}={ELECTRODE[g['electrode']]}；"
                         f"包装 {g['packing']}={PACKING[g['packing']]}；应用 {g['application']}={APPLICATION[g['application']]}"})
    if g['voltage'] == '2B':
        row['备注2'] += ' 原厂编码表 2B 同时标注 200/250V，须查具体型号规格书确认耐压。'
    return row


def decode_high_q(model):
    match = HIGH_Q.fullmatch(model)
    if not match:
        return None
    g = match.groupdict()
    rule = payload()['high_q_rules'][g['series']]
    allowed = rule['capacitances'].get(g['cap'])
    if not allowed or g['tol'] not in allowed['tolerances'] or int(g['voltage']) not in allowed['voltages']:
        return None
    if g['laser'] and g['series'] in {'A60Z','A60L'}:
        return None
    row = base_record(model)
    row.update({'系列':g['series'], '系列说明':'高Q／低损耗 RF／微波电容',
                '特殊用途':'高Q | 低损耗', '材质（介质）':'C0G',
                '尺寸（inch）':rule['inch'], '尺寸（mm）':rule['metric'],
                '容值':allowed['pf'], '容值_pf':allowed['pf'], '容值单位':'pF','容值误差':TOLERANCE[g['tol']],
                '耐压（V）':int(g['voltage']), '工作温度':'-55~125℃',
                '备注1':f"原厂系列规格书：{rule['source_url']}；端子 {g['terminal']}；包装 T=编带；可选 X=激光标记。"})
    return row


def decode_broadband(model):
    # Internal design/material codes are not universal dielectric or RF ratings.
    # Restrict their interpretation to combinations in the reviewed source data.
    match = re.fullmatch(r'(ABCU[ABC])([0-9]{2})([12SF])(0XX|01X|02X)([0-9R]{3})([KM])([NG])DG',model)
    if not match or not cap_pf(match[5]):
        return None
    templates = []
    for existing,row in by_model().items():
        template = re.fullmatch(r'(ABCU[ABC])([0-9]{2})([12SF])(0XX|01X|02X)([0-9R]{3})([KM])([NG])DG',existing)
        if template and template.groups()[:4] == match.groups()[:4]:
            templates.append(row)
    if not templates:
        return None
    row = base_record(model)
    template = templates[0]
    row.update({field:template[field] for field in ('系列','系列说明','尺寸（inch）','尺寸（mm）','耐压（V）','材质（介质）','工作温度')})
    row.update({'容值':cap_pf(match[5]),'容值_pf':cap_pf(match[5]),'容值单位':'pF','容值误差':TOLERANCE[match[6]],
                '特殊用途':'宽带 | 高频','备注1':'按已核验宽带系列的编码结构解析；'
                '频段、损耗和此组合的可订购性须查具体型号规格书。'})
    return row


def parse_model(model, brand='', component_type=''):
    model = key(model)
    if brand and not is_brand(brand):
        return None
    if quarantine_notice(model):
        return None
    exact = special_record(model,brand)
    if exact:
        return exact if not component_type or component_type == exact['器件类型'] else None
    rf = decode_rf(model)
    if rf:
        return rf if not component_type or component_type == 'RF耦合器' else None
    if not component_type or component_type == 'ESD／EMI保护网络':
        historical = decode_legacy_protection(model,brand)
        if historical:
            return historical
    if not model.startswith(('AC','ABCU','A60','A80')):
        return None
    if brand and not is_brand(brand):
        return None
    if component_type and component_type not in {'MLCC','陶瓷电容','贴片电容'}:
        return None
    # Conflicting manufacturer fields must not be silently repaired by decoding.
    if quarantine_notice(model):
        return None
    if model in by_model():
        return dict(by_model()[model], 容值_pf=by_model()[model]['容值'])
    return decode_standard(model) or decode_high_q(model) or decode_broadband(model)


def series_profile(model, brand=''):
    if brand and not is_brand(brand):
        return {}
    parsed = parse_model(model, brand)
    if not parsed:
        return {}
    return {k:parsed.get(k,'') for k in ('系列','系列说明','特殊用途')}


def install_search_overlay(conn, frames):
    """Add explicit manufacturer records to connection-local search views.

    No immutable bundle rebuild and no persisted/runtime DB writes. Existing
    records win by exact identity. Preserve an already installed Jianghai view.
    Rule-only combinations and quarantined records never enter these views.
    """
    # Detailed special-purpose records deliberately have their own schema;
    # do not squeeze protection networks or RF couplers into capacitor tables.
    install_special_rows(conn)
    for table in ('components_search_core','components_search_capacitor'):
        addon = 'amotech_catalogue_' + ('core' if table.endswith('_core') else 'capacitor')
        if conn.execute('SELECT 1 FROM temp.sqlite_master WHERE name=?',(addon,)).fetchone():
            continue
        if not conn.execute('SELECT 1 FROM main.sqlite_master WHERE type="table" AND name=?',(table,)).fetchone():
            continue
        frame = frames.get(table)
        if frame is None or frame.empty:
            continue
        columns = [r[1] for r in conn.execute(f'PRAGMA main.table_info("{table}")')]
        if not {'品牌','型号','_component_type'}.issubset(columns):
            continue
        names = ','.join('"'+c+'"' for c in columns)
        conn.execute(f'CREATE TEMP TABLE "{addon}" AS SELECT * FROM main."{table}" WHERE 0')
        # Convert missing pandas/Arrow values to SQL NULL, not textual "nan".
        values = []
        for row in frame.to_dict(orient='records'):
            values.append(tuple(None if row.get(c) is None or str(row.get(c)) in {'nan','<NA>','NaT'} else row.get(c) for c in columns))
        conn.executemany(f'INSERT INTO "{addon}" ({names}) VALUES ({",".join("?" for _ in columns)})',values)
        conn.execute(f'CREATE INDEX "{addon}_model" ON "{addon}"("品牌","型号")')
        if '_model_clean' in columns:
            conn.execute(f'CREATE INDEX "{addon}_clean" ON "{addon}"("_model_clean")')
        existing = conn.execute('SELECT type,sql FROM temp.sqlite_master WHERE name=?',(table,)).fetchone()
        if existing and existing[0] != 'view':
            raise ValueError('Unexpected temporary search table: '+table)
        base_select = re.split(r'\bAS\b',existing[1],maxsplit=1,flags=re.I)[1] if existing else f'SELECT * FROM main."{table}"'
        if existing:
            conn.execute(f'DROP VIEW temp."{table}"')
        conn.execute(f'CREATE TEMP VIEW "{table}" AS {base_select} UNION ALL SELECT {names} FROM temp."{addon}" a '
                     f'WHERE NOT EXISTS (SELECT 1 FROM main."{table}" b WHERE b."品牌"=a."品牌" AND b."型号"=a."型号" AND b."_component_type"=a."_component_type")')


def install_special_rows(conn):
    if conn.execute('SELECT 1 FROM temp.sqlite_master WHERE name=?',(SPECIAL_TABLE,)).fetchone():
        return
    columns = ('品牌','型号','_component_type',*SPECIAL_TEXT,*SPECIAL_NUMERIC)
    schema = ','.join('"'+c+'" '+('REAL' if c in SPECIAL_NUMERIC else 'TEXT') for c in columns)
    conn.execute(f'CREATE TEMP TABLE "{SPECIAL_TABLE}" ({schema}, PRIMARY KEY ("品牌","型号","_component_type"))')
    records = [dict(r,_component_type=r['器件类型']) for r in catalogue_rows() if r.get('器件类型') in SPECIAL_KINDS]
    names = ','.join('"'+c+'"' for c in columns)
    conn.executemany(f'INSERT INTO "{SPECIAL_TABLE}" ({names}) VALUES ({",".join("?" for _ in columns)})',
                     [tuple(r.get(c) for c in columns) for r in records])
