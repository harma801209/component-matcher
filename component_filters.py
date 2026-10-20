"""Read-only faceted browsing of the existing public search sidecars.

No rule-generated models, prices, full-library DataFrames or schema changes.
SQL identifiers/expressions are internal constants; all user values are bound.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import math
import os
import re
import catalog_mlcc_completion as mlcc_completion
import catalog_passive_completion as passive_completion

CORE = "components_search_core"
MISSING = "__catalog_missing__"
PREFIX = "catalog_filter_"
TEXT_MODE = "型号／文字搜索"
FILTER_MODE = "按规格筛选"
SEMICONDUCTORS = {"MOSFET", "二极管", "TVS二极管", "三极管"}
INDUCTORS = {"共模电感", "功率电感", "射频电感", "磁珠"}
DETAIL_COLUMNS = ("品牌", "型号", "_component_type", "封装代码", "极性", "特殊用途", "_volt_num", "耐压（V）", "额定电流", "DCR", "饱和电流", "屏蔽类型", "回路数", "安装方式", "生产状态", "工作温度", "_power")


def family_of_kind(kind):
    if '电阻' in kind:
        return '电阻'
    if kind in {'MLCC', '钽电容'} or '电容' in kind:
        return '电容'
    if kind in INDUCTORS:
        return '电感／磁珠'
    if kind in {'晶振', '振荡器', '实时时钟模块'}:
        return '晶振／时钟'
    if kind == 'MOSFET':
        return 'MOS管'
    if '二极管' in kind:
        return '二极管'
    if kind == '三极管':
        return '三极管'
    return '其他'


def scalar_current(value):
    """Only an unambiguous single current; never strip test conditions/ranges."""
    match = re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(A|mA|µA|μA|uA)\s*', str(value or ''))
    if not match:
        return None
    number = float(match[1]) * {'A':1, 'mA':1e-3, 'µA':1e-6, 'μA':1e-6, 'uA':1e-6}[match[2]]
    return number if math.isfinite(number) else None


def load_parameter_rows(path, component_type, model_resolver=None):
    """Project only this kind's missing fields from the existing public asset.

    No source rebuild, writes or full-library DataFrame. Costs/auth columns are
    never read. Unknown kinds stay on the indexed-core fallback.
    """
    if component_type not in SEMICONDUCTORS | INDUCTORS | {'MLCC'} or not os.path.isfile(path):
        return []
    import pyarrow.parquet as pq
    with pq.ParquetFile(path) as source:
        names = set(source.schema_arrow.names)
    if not {'品牌', '型号', '_component_type'}.issubset(names):
        return []
    columns = [c for c in (mlcc_completion.RAW_COLUMNS if component_type == 'MLCC' else DETAIL_COLUMNS) if c in names]
    table = pq.read_table(path, columns=columns, filters=[('_component_type', '=', component_type)], use_threads=False)
    rows, seen = [], set()
    for row in (row for batch in table.to_batches(max_chunksize=2048) for row in batch.to_pylist()):
        identity = (row['品牌'], row['型号'], row['_component_type'])
        if not row['型号'] or identity in seen:
            continue
        # Select one actual record, never manufacture a composite specification.
        seen.add(identity)
        if component_type == 'MLCC':
            completed = mlcc_completion.complete(row, model_resolver)
            # SMD family inference runs directly on the current index below.
            # Cache only actual source/decoder repairs, not >100k identical
            # inferred-mount records copied on every Streamlit rerun.
            repaired = any(completed[key] and completed[key] != mlcc_completion.text(row.get(key)) for key in mlcc_completion.FIELDS[:3])
            explicit_mount = mlcc_completion.text(row.get('安装方式')) and completed['_mount_style'] != mlcc_completion.text(row.get('_mount_style'))
            if repaired or explicit_mount:
                rows.append({**dict(zip(('品牌', '型号', '_component_type'), identity)), **completed})
            continue
        row['_current_amps'] = scalar_current(row.get('额定电流'))
        row['_saturation_amps'] = scalar_current(row.get('饱和电流'))
        rows.append(row)
    return rows


def install_parameter_rows(conn, component_type, rows):
    """Connection-local LEFT JOIN: current indexed catalogue is the authority.

    New/deleted models cannot appear from a stale prepared file. Missing detail
    remains NULL; a newly indexed model is not dropped. TEMP data disappears on
    close, even when the search database is opened read-only.
    """
    if component_type == 'MLCC':
        install_mlcc_parameters(conn, rows)
        return
    if component_type not in SEMICONDUCTORS | INDUCTORS or not rows:
        return
    table, _ = available_profile(conn, component_type)
    base_columns = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
    allowed = set(DETAIL_COLUMNS) | {'_current_amps', '_saturation_amps'}
    columns = ['品牌', '型号', '_component_type'] + sorted((set().union(*(r.keys() for r in rows)) & allowed) - {'品牌', '型号', '_component_type'})
    valid = [r for r in rows if r.get('_component_type') == component_type and r.get('型号')]
    if not valid:
        return
    names = ','.join(f'"{c}"' for c in columns)
    conn.execute(f'CREATE TEMP TABLE catalog_filter_parameters ({names}, PRIMARY KEY ("品牌","型号","_component_type"))')
    conn.executemany(f'INSERT OR IGNORE INTO catalog_filter_parameters ({names}) VALUES ({",".join("?" for _ in columns)})', [tuple(r.get(c) for c in columns) for r in valid])
    # The core contains ~1.7M identities but only a few dozen MOS/transistors.
    # Materialize this indexed kind once, not a core scan for every facet.
    conn.execute(f'CREATE TEMP TABLE catalog_filter_base AS SELECT * FROM "{table}" WHERE "_component_type"=?', (component_type,))
    extra = ''.join(f', d."{c}" AS "{c}"' for c in columns if c not in base_columns)
    conn.execute(f'CREATE TEMP VIEW catalog_filter_source AS SELECT b.*{extra} FROM catalog_filter_base b LEFT JOIN catalog_filter_parameters d ON b."品牌" IS d."品牌" AND b."型号"=d."型号" AND b."_component_type"=d."_component_type"')


def install_mlcc_parameters(conn, rows):
    """Complete a connection-local copy; never alter the shipped search store."""
    if conn.execute("SELECT 1 FROM sqlite_temp_master WHERE name='catalog_mlcc_source'").fetchone():
        return
    columns = {r[1] for r in conn.execute('PRAGMA table_info(components_search_capacitor)')}
    if not {'品牌', '型号', '_component_type'}.issubset(columns):
        return
    conn.execute("CREATE TEMP TABLE catalog_mlcc_source AS SELECT * FROM components_search_capacitor WHERE _component_type='MLCC'")
    for key in mlcc_completion.FIELDS:
        if key not in columns:
            conn.execute(f'ALTER TABLE catalog_mlcc_source ADD COLUMN "{key}" TEXT')
    details = {}
    for row in rows:
        if row.get('_component_type') == 'MLCC':
            details.setdefault((row.get('品牌'), row.get('型号')), row)
    projection = ','.join('"'+key+'"' for key in ('品牌', '型号', '_component_type', *mlcc_completion.FIELDS))
    assignments = ','.join('"'+key+'"=?' for key in mlcc_completion.FIELDS)
    last = 0
    while True:
        batch = conn.execute('SELECT rowid,'+projection+' FROM catalog_mlcc_source WHERE rowid>? ORDER BY rowid LIMIT 2048', (last,)).fetchall()
        if not batch:
            break
        updates = []
        for item in batch:
            record = dict(zip(('品牌', '型号', '_component_type', *mlcc_completion.FIELDS), item[1:]))
            original = {key: mlcc_completion.text(record.get(key)) for key in mlcc_completion.FIELDS}
            detail = details.get((record['品牌'], record['型号']), {})
            for key in mlcc_completion.FIELDS:
                if not original[key] and mlcc_completion.text(detail.get(key)):
                    record[key] = detail[key]
            values = mlcc_completion.complete(record)
            if values != original:
                updates.append(tuple(values[key] or None for key in mlcc_completion.FIELDS)+(item[0],))
        conn.executemany('UPDATE catalog_mlcc_source SET '+assignments+' WHERE rowid=?', updates)
        last = batch[-1][0]
    conn.execute('CREATE INDEX catalog_mlcc_identity ON catalog_mlcc_source(品牌,型号)')


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    expression: str
    units: tuple = ()


def column(key, label, units=()):
    return Field(key, label, f'"{key}"', units)


def profile(component_type):
    """Unknown/new kinds remain browsable via the complete core catalogue."""
    common = [column("品牌", "品牌")]
    package = column("_size", "封装／尺寸代码")
    tolerance = column("_tol", "精度／误差")
    if component_type in {"贴片电阻", "厚膜电阻", "薄膜电阻", "合金电阻", "碳膜电阻", "绕线电阻", "金属氧化膜电阻", "热敏电阻"}:
        fields = common + [package, tolerance, column("_power_watt", "额定功率"), column("_res_ohm", "阻值范围", (("Ω", 1), ("kΩ", 1e3), ("MΩ", 1e6))), column('_body_size', '本体尺寸')]
        if component_type == '热敏电阻':
            fields += [column('B值', 'B值'), column('B值条件', 'B值测试条件')]
        return "components_search_resistor", fields
    if component_type in {"MLCC", "引线型陶瓷电容", "薄膜电容", "铝电解电容", "安规电容", "钽电容"}:
        fields = common + [package, tolerance, column("_mount_style", "安装方式"), column("_pf", "容量范围", (("pF", 1), ("nF", 1e3), ("µF", 1e6))), column("_volt_num", "额定耐压范围", (("V", 1),)), column("_body_size", "本体尺寸"), column("_special_use_norm", "用途／特性"), column('_temp_low', '最低工作温度（℃）'), column('_temp_high', '最高工作温度（℃）')]
        if component_type not in {'铝电解电容', '钽电容'}:
            fields += [column('_mat', '介质／材质'), column('_safety_class', '安规等级')]
        if component_type != 'MLCC':
            fields += [column('_pitch', '脚距')]
        if component_type == '铝电解电容':
            fields += [column('_life_hours_num', '寿命范围', (('h',1),))]
        return 'components_search_capacitor', fields
    if component_type in SEMICONDUCTORS:
        polarity = {'MOSFET':'沟道极性', '三极管':'NPN／PNP', 'TVS二极管':'单向／双向', '二极管':'结构／极性'}[component_type]
        dynamic = {'MOSFET':'Rds(on)及测试条件', '三极管':'hFE／动态参数', 'TVS二极管':'击穿／钳位参数', '二极管':'Vf／动态参数'}[component_type]
        return CORE, common + [column('封装代码','封装'), column('极性',polarity), column('特殊用途','类型／用途'), column('_volt_num','库内标注电压范围',(('V',1),)), column('_current_amps','库内额定电流范围',(('A',1),('mA',0.001))), column('额定电流','原始电流标注'), column('DCR',dynamic), column('_power','库内功率标注'), column('安装方式','安装方式'), column('生产状态','生产状态'), column('工作温度','工作温度')]
    if component_type in {"贴片压敏电阻", "引线型压敏电阻", "压敏电阻"}:
        fields = common + [package if component_type == '贴片压敏电阻' else column('_disc_size', '尺寸'), tolerance, column('_varistor_voltage', '压敏电压'), column('_body_size', '本体尺寸')]
        if component_type != '贴片压敏电阻':
            fields += [column('_pitch', '脚距')]
        return 'components_search_varistor', fields
    if component_type in {"共模电感", "功率电感", "射频电感", "磁珠", "晶振", "振荡器", "实时时钟模块"}:
        fields = common + [package]
        if component_type in {"晶振", "振荡器", "实时时钟模块"}:
            expr = 'CASE UPPER("_unit_upper") WHEN \'HZ\' THEN "_value_num" WHEN \'KHZ\' THEN "_value_num"*1000 WHEN \'MHZ\' THEN "_value_num"*1000000 WHEN \'GHZ\' THEN "_value_num"*1000000000 END'
            fields += [Field("frequency_hz", "频率范围", expr, (("MHz", 1e6), ("kHz", 1e3), ("Hz", 1))), column("频差（ppm）", "频差（ppm）")]
            if component_type == '振荡器':
                fields += [column('输出类型', '输出类型'), column('电源电压', '供电电压'), column('使能/待机功能', '使能／待机功能')]
            elif component_type == '实时时钟模块':
                fields += [column('电源电压', '供电电压'), column('接口类型', '接口类型')]
        else:
            fields += [tolerance, column('_current_amps','额定电流范围',(('A',1),('mA',0.001))), column('额定电流','原始额定电流'), column('DCR','DCR及测试条件')]
            if component_type == '功率电感':
                fields += [column('_saturation_amps','饱和电流范围',(('A',1),('mA',0.001))), column('饱和电流','原始饱和电流')]
            if component_type in {'功率电感', '射频电感'}:
                fields += [column('屏蔽类型','屏蔽类型')]
            if component_type in {'共模电感', '磁珠'}:
                fields += [column('回路数','回路数'), column('_impedance_text', '阻抗及测试条件')]
            expr = 'CASE WHEN "_unit_upper" IN (\'NH\',\'nH\') THEN "_value_num"*0.001 WHEN "_unit_upper" IN (\'UH\',\'uH\',\'µH\',\'μH\',\'ΜH\') THEN "_value_num" WHEN "_unit_upper" IN (\'MH\',\'mH\') THEN "_value_num"*1000 END'
            if component_type != '磁珠':
                fields += [Field("inductance_uh", "电感量范围", expr, (("µH", 1), ("nH", 0.001), ("mH", 1e3)))]
            if component_type in {"共模电感", "磁珠"}:
                expr = 'CASE WHEN "_unit_upper" IN (\'Ω\',\'OHM\',\'Ohm\') THEN "_value_num" WHEN "_unit_upper" IN (\'KΩ\',\'KOHM\') THEN "_value_num"*1000 END'
                fields += [Field("impedance_ohm", "库内主值：阻抗范围", expr, (("Ω", 1), ("kΩ", 1e3)))]
        if component_type in {'晶振','振荡器','实时时钟模块'}:
            fields += [column('频率温度特性（ppm）','频率温度特性（ppm）'), column('AEC等级','AEC等级')]
            if component_type == '晶振':
                fields += [column('负载电容（pF）','负载电容（pF）')]
        fields += [column('_body_size', '本体尺寸')]
        return "components_search_value", fields + [column("系列", "系列"), column("安装方式", "安装方式"), column("工作温度", "工作温度")]
    return CORE, common


def available_profile(conn, component_type):
    table, fields = profile(component_type)
    if component_type == 'MLCC' and conn.execute("SELECT 1 FROM sqlite_temp_master WHERE name='catalog_mlcc_source'").fetchone():
        table = 'catalog_mlcc_source'
    if conn.execute("SELECT 1 FROM sqlite_temp_master WHERE type='view' AND name='catalog_filter_source'").fetchone():
        current = conn.execute('SELECT _component_type FROM catalog_filter_parameters LIMIT 1').fetchone()
        if current and current[0] == component_type:
            table = 'catalog_filter_source'
    if conn.execute("SELECT 1 FROM sqlite_temp_master WHERE name='catalog_passive_source'").fetchone():
        current = conn.execute('SELECT _component_type FROM catalog_passive_source LIMIT 1').fetchone()
        if current and current[0] == component_type:
            table = 'catalog_passive_source'
    columns = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
    if not {"品牌", "型号", "_component_type"}.issubset(columns):
        table, fields = CORE, [column("品牌", "品牌")]
        columns = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
    if not {"品牌", "型号", "_component_type"}.issubset(columns):
        raise ValueError("筛选索引暂不可用，请使用型号搜索。")
    fields = [f for f in fields if f.key in columns or (f.key in {"frequency_hz", "inductance_uh", "impedance_ohm"} and {"_unit_upper", "_value_num"}.issubset(columns))]
    from dataclasses import replace
    fallback = {'frequency_hz':'_catalog_frequency_hz', 'inductance_uh':'_catalog_inductance_uh', 'impedance_ohm':'_catalog_impedance_ohm'}
    fields = [replace(f, expression=f'COALESCE(({f.expression}),"{fallback[f.key]}")') if f.key in fallback and fallback[f.key] in columns else f for f in fields]
    return table, fields


def category_counts(conn):
    return [(str(kind or ""), int(count)) for kind, count in conn.execute(
        f'SELECT "_component_type", COUNT(DISTINCT COALESCE("品牌",\'\')||char(0)||"型号") FROM "{CORE}" WHERE COALESCE("型号",\'\')<>\'\' GROUP BY "_component_type" ORDER BY "_component_type"'
    )]


def has_unique_model_rows(conn, component_type):
    table, _ = available_profile(conn, component_type)
    type_expression = '"_component_type"' if component_type else 'COALESCE("_component_type",\'\')'
    count, unique = conn.execute(f'SELECT COUNT(*),COUNT(DISTINCT COALESCE("品牌",\'\')||char(0)||"型号") FROM "{table}" WHERE {type_expression}=? AND COALESCE("型号",\'\')<>\'\'', (component_type,)).fetchone()
    return count == unique


def text_expression(field):
    return f"NULLIF(TRIM(CAST(({field.expression}) AS TEXT)), '')"


def parse_range(low, high, multiplier=1):
    def number(text):
        if str(text or "").strip() == "":
            return None
        try:
            value = float(Decimal(str(text).strip()) * Decimal(str(multiplier)))
        except (InvalidOperation, ValueError, OverflowError):
            raise ValueError("范围请填写数字，单位在旁边选择。") from None
        if not math.isfinite(value) or value < 0:
            raise ValueError("范围必须是大于或等于 0 的有限数值。")
        return value
    lower, upper = number(low), number(high)
    if lower is not None and upper is not None and lower > upper:
        raise ValueError("范围下限不能大于上限。")
    return lower, upper


def where_clause(fields, component_type, selected, ranges, keyword="", omit="", keyword_mode="contains"):
    known = {f.key: f for f in fields}
    if (set(selected) | set(ranges)) - set(known):
        raise ValueError("无效的筛选参数。")
    type_expression = '"_component_type"' if component_type else 'COALESCE("_component_type",\'\')'
    clauses = [f'{type_expression}=?', 'COALESCE("型号",\'\')<>\'\'']
    params = [component_type]
    for key, choices in selected.items():
        if key == omit or not choices:
            continue
        if known[key].units or len(choices) > 100:
            raise ValueError("无效的筛选选项。")
        expr = text_expression(known[key])
        nonempty = [str(v) for v in choices if v != MISSING]
        alternatives = []
        if MISSING in choices:
            alternatives.append(f"{expr} IS NULL")
        if nonempty:
            alternatives.append(f"{expr} IN ({','.join('?' for _ in nonempty)})")
            params.extend(nonempty)
        clauses.append('(' + ' OR '.join(alternatives) + ')')
    for key, bounds in ranges.items():
        if key == omit:
            continue
        if not known[key].units or len(bounds) != 2:
            raise ValueError("无效的数值范围。")
        lower, upper = bounds
        for bound in bounds:
            if bound is not None and (not math.isfinite(float(bound)) or float(bound) < 0):
                raise ValueError("无效的数值范围。")
        if lower is not None and upper is not None and lower > upper:
            raise ValueError("范围下限不能大于上限。")
        for value, sign in ((lower, '>='), (upper, '<=')):
            if value is not None:
                clauses.append(f'({known[key].expression}) {sign} ?')
                params.append(float(value))
    keyword = str(keyword or "").strip()
    if not isinstance(keyword_mode,str) or keyword_mode not in {'contains','prefix','exact'}:
        raise ValueError("无效的型号搜索方式。")
    if len(keyword) > 120:
        raise ValueError("型号关键词最多 120 个字符。")
    if keyword:
        escaped = keyword.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        clauses.append('"型号" LIKE ? ESCAPE \'\\\'')
        params.append(('%' if keyword_mode=='contains' else '') + escaped + ('%' if keyword_mode!='exact' else ''))
    return ' AND '.join(clauses), params


def snapshot(conn, component_type, selected=None, ranges=None, keyword="", page=1, page_size=20, include_rows=False, sort_key="", sort_desc=False, verified_unique=False, keyword_mode="contains"):
    table, fields = available_profile(conn, component_type)
    selected, ranges = selected or {}, ranges or {}
    where, params = where_clause(fields, component_type, selected, ranges, keyword, keyword_mode=keyword_mode)
    sortable = {f.key:f.expression for f in fields} | {'型号':'"型号"', '品牌':'"品牌"'}
    if sort_key and sort_key not in sortable:
        raise ValueError('无效的排序字段。')
    if sort_key == '_tol':
        text='TRIM(CAST("_tol" AS TEXT))'
        # Normalized percentages are stored as text: 2% must precede 10%,
        # while unspecified sentinels/compound markings stay unknown/last.
        sortable['_tol']=f'CASE WHEN {text} NOT GLOB \'*[^0-9.]*\' AND {text} GLOB \'*[0-9]*\' AND LENGTH({text})-LENGTH(REPLACE({text},\'.\',\'\'))<=1 AND CAST({text} AS REAL)>0 AND CAST({text} AS REAL)<=100 THEN CAST({text} AS REAL) END'
    order = (f'({sortable[sort_key]}) {"DESC" if sort_desc else "ASC"} NULLS LAST,' if sort_key else '') + '"品牌","型号"'
    identity = 'COALESCE("品牌",\'\')||char(0)||"型号"'
    # The app caches an actual uniqueness audit by database revision and kind.
    # Never assume a table is unique just because the normal builder dedupes it.
    counter = 'COUNT(*)' if verified_unique else f'COUNT(DISTINCT {identity})'
    total = int(conn.execute(f'SELECT {counter} FROM "{table}" WHERE {where}', params).fetchone()[0])
    facets = {}
    for field in fields:
        own_where, own_params = where_clause(fields, component_type, selected, ranges, keyword, omit=field.key, keyword_mode=keyword_mode)
        expr = field.expression if field.units else text_expression(field)
        if field.units:
            facets[field.key] = list(conn.execute(f'SELECT MIN(({expr})), MAX(({expr})) FROM "{table}" WHERE {own_where}', own_params).fetchone())
        else:
            facets[field.key] = [(MISSING if value is None else str(value), int(count)) for value, count in conn.execute(f'SELECT {expr} AS value, {counter} FROM "{table}" WHERE {own_where} GROUP BY value ORDER BY value', own_params)]
    size = max(1, min(100, int(page_size)))
    pages = max(1, (total + size - 1) // size)
    page = max(1, min(pages, int(page)))
    rows = []
    if include_rows and total:
        projection = ','.join(f'({field.expression}) AS "{field.key}"' for field in fields if field.key != '品牌')
        if projection:
            projection = ',' + projection
        # One real source record per pair; do not combine conflicting fields
        # from different records into a synthetic specification.
        group = '' if verified_unique else 'GROUP BY "品牌","型号"'
        cursor = conn.execute(f'SELECT "品牌","型号"{projection} FROM "{table}" WHERE {where} {group} ORDER BY {order} LIMIT ? OFFSET ?', params + [size, (page - 1) * size])
        columns = [d[0] for d in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return {'total':total, 'facets':facets, 'page':page, 'pages':pages, 'page_size':size, 'rows':rows, 'fields':fields}


def option_label(field, value):
    if value == MISSING or value is None or value == "":
        return "未提供"
    if field.key == '_tol':
        if re.fullmatch(r'\d+(?:\.\d+)?PF', str(value).upper()):
            return '±'+str(value)[:-2]+' pF'
        if str(value).replace('.', '', 1).isdigit():
            numeric = float(value)
            return f'±{value}%' if 0 < numeric <= 100 else '误差标注待核对'
        return str(value)
    if field.key == '_power_watt':
        try:
            number = float(value)
            fraction = Fraction(number).limit_denominator(1000)
            return f'{fraction} W' if fraction.denominator > 1 and abs(float(fraction) - number) < 1e-10 else f'{number:g} W'
        except (ValueError, TypeError):
            pass
    return str(value)


def reset_filters(state, keep_category=False):
    selectors = {PREFIX+'category', PREFIX+'family'}
    for key in list(state):
        if key.startswith(PREFIX) and key not in selectors:
            del state[key]
    if not keep_category:
        # Deleting a live selectbox key also removes its widget-id binding.
        # A later client update can then replay the family callback and erase
        # the newly chosen kind. Explicit None resets both UI and backend while
        # retaining the bindings across clear / same-family reselection.
        for key in selectors:
            state[key] = None


def change_family(state):
    family = state.get(PREFIX+'family')
    reset_filters(state)
    state[PREFIX+'family'] = family


def choice_key(field_key, value):
    return PREFIX + 'choice_' + field_key + '_' + hashlib.sha256(str(value).encode('utf-8')).hexdigest()[:20]


def render(st, categories, get_snapshot, on_login, is_member, on_match, results_renderer=None, panel_renderer=None):
    """Compact manufacturer-style facets; anonymous responses contain metadata only."""
    from catalog_filter_panel import build_payload as panel_payload, render_panel, handle_request as panel_action
    kind = st.session_state.get(PREFIX+'category')
    if kind not in dict(categories):
        kind = None
    selected, ranges, baseline, result = {}, {}, None, None
    invalid_ranges = []
    # This mode is specifications-only. Do not let the removed inline name
    # search silently constrain an already-open browser session after upgrade.
    # The separate main text-search input and account/customer scope are kept.
    st.session_state.pop(PREFIX+'keyword',None)
    st.session_state.pop(PREFIX+'keyword_mode',None)
    keyword, keyword_mode = '', 'contains'
    if kind is not None:
        allowed_sort = {'品牌','型号'} | {field.key for field in profile(kind)[1]}
        if st.session_state.get(PREFIX+'sort') not in allowed_sort:
            st.session_state.pop(PREFIX+'sort',None)
            st.session_state.pop(PREFIX+'desc',None)
        # Initial entry needs only one scan. Reuse its facets as the full
        # option universe rather than querying the same large kind twice.
        has_conditions = bool(keyword) or any(st.session_state.get(PREFIX+field.key+suffix)
            for field in profile(kind)[1] for suffix in (('_low','_high') if field.units else ('',)))
        if has_conditions:
            baseline = get_snapshot(kind, {}, {}, '', 1, 20, False, '', False)
        else:
            result = get_snapshot(kind, {}, {}, '', int(st.session_state.get(PREFIX+'page',1)),
                int(st.session_state.get(PREFIX+'size',20)), bool(is_member), st.session_state.get(PREFIX+'sort',''),
                bool(st.session_state.get(PREFIX+'desc',False)), keyword_mode=keyword_mode)
            baseline = result
        for field in baseline['fields']:
            if field.units:
                unit = st.session_state.get(PREFIX+field.key+'_unit', field.units[0][0])
                scale = dict(field.units).get(unit, field.units[0][1])
                try:
                    bounds = parse_range(st.session_state.get(PREFIX+field.key+'_low',''), st.session_state.get(PREFIX+field.key+'_high',''), scale)
                except ValueError as exc:
                    invalid_ranges.append(field.label+'：'+str(exc))
                    continue
                if bounds != (None,None):
                    ranges[field.key] = bounds
            elif st.session_state.get(PREFIX+field.key):
                selected[field.key] = list(st.session_state[PREFIX+field.key])
        if result is None:
            result = get_snapshot(kind, selected, ranges, keyword, int(st.session_state.get(PREFIX+'page',1)),
                int(st.session_state.get(PREFIX+'size',20)), bool(is_member), st.session_state.get(PREFIX+'sort',''),
                bool(st.session_state.get(PREFIX+'desc',False)), keyword_mode=keyword_mode)
    panel = panel_payload(categories,kind,baseline,result,selected,ranges,keyword,st.session_state)
    request = (panel_renderer or render_panel)(panel,key=PREFIX+'panel')
    if panel_action(st.session_state,panel,request):
        st.rerun()
    if kind is None:
        return
    if invalid_ranges:
        st.warning('请修正数值范围后查看结果。'+'；'.join(invalid_ranges))
        return
    if kind in SEMICONDUCTORS:
        st.caption('电压、电流按库内标注筛选，不代表相同测试条件或可直接替代；动态参数保留原始测试条件。')
    if len(result['fields']) == 1:
        st.info('此品类目前仅收录品牌和型号；未收录的电性参数不会默认补值。')
    active = []
    if keyword:
        active.append({'contains':'型号包含','prefix':'型号开头','exact':'型号完全一致'}[keyword_mode]+'：'+keyword)
    for field in result['fields']:
        if selected.get(field.key):
            active.append(field.label+'：'+'、'.join(option_label(field,value) for value in selected[field.key]))
        if field.key in ranges:
            unit=st.session_state.get(PREFIX+field.key+'_unit',field.units[0][0])
            low=st.session_state.get(PREFIX+field.key+'_low','') or '不限'
            high=st.session_state.get(PREFIX+field.key+'_high','') or '不限'
            active.append(f'{field.label}：{low} ～ {high} {unit}')
    condition='；'.join(active) if active else '该品类全部库内条目'
    if not is_member:
        st.info('登录会员后可查看具体型号；价格仍按原有账号和客户权限显示。')
        if st.button('登录查看筛选结果',type='primary'):
            on_login()
        return
    if not result['total']:
        st.warning('没有同时满足这些条件的库内型号。可移除部分条件或清空筛选；这不代表厂家不能生产。')
        return
    from catalog_result_table import build_payload, render_table, handle_request
    payload=build_payload(result,kind,condition,selected,ranges,keyword,st.session_state.get(PREFIX+'sort',''),bool(st.session_state.get(PREFIX+'desc',False)))
    request=(results_renderer or render_table)(payload,key=PREFIX+'result_table')
    if handle_request(st.session_state,payload,request,on_match):
        st.rerun()
