"""Read-only faceted browsing of the existing public search sidecars.

No rule-generated models, prices, full-library DataFrames or schema changes.
SQL identifiers/expressions are internal constants; all user values are bound.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import math

CORE = "components_search_core"
MISSING = "__catalog_missing__"
PREFIX = "catalog_filter_"
TEXT_MODE = "型号／文字搜索"
FILTER_MODE = "按规格筛选"


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
        return "components_search_resistor", common + [package, tolerance, column("_power_watt", "额定功率"), column("_res_ohm", "阻值范围", (("Ω", 1), ("kΩ", 1e3), ("MΩ", 1e6)))]
    if component_type in {"MLCC", "引线型陶瓷电容", "薄膜电容", "铝电解电容", "安规电容", "钽电容"}:
        return "components_search_capacitor", common + [package, column("_mat", "介质／材质"), tolerance, column("_mount_style", "安装方式"), column("_safety_class", "安规等级"), column("_pf", "容量范围", (("pF", 1), ("nF", 1e3), ("µF", 1e6))), column("_volt_num", "额定耐压范围", (("V", 1),)), column("_body_size", "本体尺寸"), column("_pitch", "脚距"), column("_special_use_norm", "用途／特性")]
    if component_type in {"贴片压敏电阻", "引线型压敏电阻", "压敏电阻"}:
        return "components_search_varistor", common + [column("_disc_size", "尺寸"), tolerance, column("_varistor_voltage", "压敏电压"), column("_pitch", "脚距")]
    if component_type in {"共模电感", "功率电感", "射频电感", "磁珠", "晶振", "振荡器", "实时时钟模块"}:
        fields = common + [package, tolerance]
        if component_type in {"晶振", "振荡器", "实时时钟模块"}:
            expr = 'CASE UPPER("_unit_upper") WHEN \'HZ\' THEN "_value_num" WHEN \'KHZ\' THEN "_value_num"*1000 WHEN \'MHZ\' THEN "_value_num"*1000000 WHEN \'GHZ\' THEN "_value_num"*1000000000 END'
            fields += [Field("frequency_hz", "频率范围", expr, (("MHz", 1e6), ("kHz", 1e3), ("Hz", 1))), column("输出类型", "输出类型"), column("电源电压", "供电电压"), column("频差（ppm）", "频差（ppm）")]
        else:
            expr = 'CASE WHEN "_unit_upper" IN (\'NH\',\'nH\') THEN "_value_num"*0.001 WHEN "_unit_upper" IN (\'UH\',\'uH\',\'µH\',\'μH\',\'ΜH\') THEN "_value_num" WHEN "_unit_upper" IN (\'MH\',\'mH\') THEN "_value_num"*1000 END'
            fields += [Field("inductance_uh", "电感量范围", expr, (("µH", 1), ("nH", 0.001), ("mH", 1e3)))]
            if component_type in {"共模电感", "磁珠"}:
                expr = 'CASE WHEN "_unit_upper" IN (\'Ω\',\'OHM\',\'Ohm\') THEN "_value_num" WHEN "_unit_upper" IN (\'KΩ\',\'KOHM\') THEN "_value_num"*1000 END'
                fields += [Field("impedance_ohm", "库内主值：阻抗范围", expr, (("Ω", 1), ("kΩ", 1e3)))]
        return "components_search_value", fields + [column("系列", "系列"), column("安装方式", "安装方式"), column("工作温度", "工作温度")]
    return CORE, common


def available_profile(conn, component_type):
    table, fields = profile(component_type)
    columns = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
    if not {"品牌", "型号", "_component_type"}.issubset(columns):
        table, fields = CORE, [column("品牌", "品牌")]
        columns = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
    if not {"品牌", "型号", "_component_type"}.issubset(columns):
        raise ValueError("筛选索引暂不可用，请使用型号搜索。")
    fields = [f for f in fields if f.key in columns or (f.key in {"frequency_hz", "inductance_uh", "impedance_ohm"} and {"_unit_upper", "_value_num"}.issubset(columns))]
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


def where_clause(fields, component_type, selected, ranges, keyword="", omit=""):
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
    if len(keyword) > 120:
        raise ValueError("型号关键词最多 120 个字符。")
    if keyword:
        escaped = keyword.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        clauses.append('"型号" LIKE ? ESCAPE \'\\\'')
        params.append('%' + escaped + '%')
    return ' AND '.join(clauses), params


def snapshot(conn, component_type, selected=None, ranges=None, keyword="", page=1, page_size=20, include_rows=False, verified_unique=False):
    table, fields = available_profile(conn, component_type)
    selected, ranges = selected or {}, ranges or {}
    where, params = where_clause(fields, component_type, selected, ranges, keyword)
    identity = 'COALESCE("品牌",\'\')||char(0)||"型号"'
    # The app caches an actual uniqueness audit by database revision and kind.
    # Never assume a table is unique just because the normal builder dedupes it.
    counter = 'COUNT(*)' if verified_unique else f'COUNT(DISTINCT {identity})'
    total = int(conn.execute(f'SELECT {counter} FROM "{table}" WHERE {where}', params).fetchone()[0])
    facets = {}
    for field in fields:
        own_where, own_params = where_clause(fields, component_type, selected, ranges, keyword, omit=field.key)
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
        cursor = conn.execute(f'SELECT "品牌","型号"{projection} FROM "{table}" WHERE {where} {group} ORDER BY "品牌","型号" LIMIT ? OFFSET ?', params + [size, (page - 1) * size])
        columns = [d[0] for d in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return {'total':total, 'facets':facets, 'page':page, 'pages':pages, 'page_size':size, 'rows':rows, 'fields':fields}


def option_label(field, value):
    if value == MISSING or value is None or value == "":
        return "未提供"
    if field.key == '_tol':
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
    for key in list(state):
        if key.startswith(PREFIX) and not (keep_category and key == PREFIX + 'category'):
            del state[key]


def choice_key(field_key, value):
    return PREFIX + 'choice_' + field_key + '_' + hashlib.sha256(str(value).encode('utf-8')).hexdigest()[:20]


def render(st, categories, get_snapshot, on_login, is_member, on_match):
    """Streamlit UI; counts are public catalogue metadata, models require login."""
    st.markdown('### 按规格查找库内器件')
    st.caption('每个数量按该品类的“品牌＋型号”去重，不是库存数量；只统计库内条目，不含规则推导的候选型号。')
    counts = dict(categories)
    head = st.columns([4, 1])
    with head[0]:
        kind = st.selectbox('器件品类', [None] + list(counts), key=PREFIX+'category', format_func=lambda k: '请选择品类 · 查看全部已收录种类' if k is None else f'{k or "未分类"}（{counts[k]:,}）', on_change=reset_filters, args=(st.session_state, True))
    with head[1]:
        st.button('清空筛选', key=PREFIX+'clear', on_click=reset_filters, args=(st.session_state,), use_container_width=True)
    if kind is None:
        import pandas as pd
        st.dataframe(pd.DataFrame([{'器件品类':k or '未分类', '库内型号数':n} for k, n in categories]), hide_index=True, use_container_width=True, height=360)
        st.info('先选择器件品类，再按封装、品牌和电性参数缩小范围。')
        return

    _, definitions = profile(kind)
    selected, ranges = {}, {}
    try:
        for field in definitions:
            if field.units:
                unit = st.session_state.get(PREFIX+field.key+'_unit', field.units[0][0])
                multiplier = dict(field.units).get(unit, field.units[0][1])
                bounds = parse_range(st.session_state.get(PREFIX+field.key+'_low', ''), st.session_state.get(PREFIX+field.key+'_high', ''), multiplier)
                if bounds != (None, None):
                    ranges[field.key] = bounds
            elif st.session_state.get(PREFIX+field.key):
                selected[field.key] = list(st.session_state[PREFIX+field.key])
        result = get_snapshot(kind, selected, ranges, st.session_state.get(PREFIX+'keyword', ''), int(st.session_state.get(PREFIX+'page', 1)), int(st.session_state.get(PREFIX+'size', 20)), bool(is_member))
    except ValueError as exc:
        st.warning(str(exc))
        # Keep invalid input editable; don't display old results as current.
        result = get_snapshot(kind, selected, {}, '', 1, 20, False)
        invalid = True
    else:
        invalid = False

    def changed():
        st.session_state[PREFIX+'page'] = 1
        st.session_state.pop(PREFIX+'picked', None)

    st.text_input('在筛选结果中查找型号', key=PREFIX+'keyword', max_chars=120, placeholder='可输入型号的一部分（可留空）', on_change=changed)
    active = []
    facets = result['facets']
    if len(result['fields']) == 1:
        st.info('此品类的筛选索引目前仅收录品牌和型号。可选择具体型号查看详情；未收录的电性参数不会默认补值。')
    categorical = [f for f in result['fields'] if not f.units and (any(v != MISSING for v, _ in facets.get(f.key, [])) or selected.get(f.key))]
    def render_choices(group):
        for offset in range(0, len(group), 3):
            for box, field in zip(st.columns(3), group[offset:offset+3]):
                with box:
                    options = dict(facets.get(field.key, []))
                    for value in selected.get(field.key, []):
                        options.setdefault(value, 0)
                    values = selected.get(field.key, [])
                    # Keep the expander identity stable while counts change;
                    # otherwise each tick closes the group during multi-select.
                    with st.expander(field.label, expanded=False):
                        st.caption(f'已选 {len(values)} 项' if values else '不限，可多选')
                        search = st.text_input('查找'+field.label+'选项', key=PREFIX+'option_search_'+field.key, placeholder='输入关键词查找全部选项')
                        visible = [v for v in options if v in values or not search or search.casefold() in option_label(field,v).casefold()]
                        if len(visible) > 100:
                            st.caption(f'共 {len(visible):,} 项，先显示 100 项；输入关键词可查找其余选项。')
                            visible = list(values) + [v for v in visible if v not in values][:max(0,100-len(values))]
                        with st.container(height=180):
                            for value in visible:
                                widget_key = choice_key(field.key, value)
                                def toggle(key=field.key, item=value, widget=widget_key):
                                    current = list(st.session_state.get(PREFIX+key, []))
                                    if st.session_state.get(widget) and item not in current:
                                        current.append(item)
                                    elif not st.session_state.get(widget) and item in current:
                                        current.remove(item)
                                    st.session_state[PREFIX+key] = current
                                    changed()
                                # A boolean widget serializes only checked state,
                                # never its changing display label/count.
                                st.checkbox(f'{option_label(field,value)}（{options[value]:,}）', value=value in values, key=widget_key, on_change=toggle, disabled=value not in values and len(values)>=100)
                        st.caption('同组可多选；数量受其他参数影响，不受本组已选项限制。')
                    if values:
                        active.append(field.label + '：' + '、'.join(option_label(field, v) for v in values))
    render_choices(categorical[:4])
    if len(categorical) > 4:
        with st.expander('更多参数', expanded=any(selected.get(f.key) for f in categorical[4:])):
            render_choices(categorical[4:])
    numeric = [f for f in result['fields'] if f.units and (facets.get(f.key, [None])[0] is not None or f.key in ranges)]
    if numeric:
        with st.expander('数值范围 · 可只填一端；精确值请把上下限填成相同数值', expanded=bool(ranges) or invalid):
            for field in numeric:
                st.markdown(f'**{field.label}**')
                cols = st.columns([2, 2, 1])
                cols[0].text_input(field.label+'下限', key=PREFIX+field.key+'_low', placeholder='不限', on_change=changed)
                cols[1].text_input(field.label+'上限', key=PREFIX+field.key+'_high', placeholder='不限', on_change=changed)
                cols[2].selectbox(field.label+'单位', [u for u, _ in field.units], key=PREFIX+field.key+'_unit', on_change=changed)
                minimum, maximum = facets.get(field.key, [None, None])
                if minimum is not None:
                    unit = st.session_state.get(PREFIX+field.key+'_unit', field.units[0][0])
                    scale = dict(field.units)[unit]
                    st.caption(f'其他条件下已收录范围：{minimum/scale:g} ～ {maximum/scale:g} {unit}')
                if field.key in ranges:
                    low = st.session_state.get(PREFIX+field.key+'_low', '') or '不限'
                    high = st.session_state.get(PREFIX+field.key+'_high', '') or '不限'
                    unit = st.session_state.get(PREFIX+field.key+'_unit', field.units[0][0])
                    active.append(f'{field.label}：{low} ～ {high} {unit}')
    if invalid:
        st.info('请修正范围后查看结果；当前没有展示旧结果。')
        return
    st.caption('已选条件：' + ('；'.join(active) if active else '该品类全部库内条目'))
    st.markdown(f'#### 找到 {result["total"]:,} 个库内型号')
    st.caption('缺失参数仅在“不限”或“未提供”时纳入；选择数值范围后，不会把未知值当作 0。筛选结果不代表可替代性或供货承诺。')
    if not is_member:
        st.info('登录会员后可查看具体型号；价格仍按原有账号和客户权限显示。')
        if st.button('登录查看筛选结果', type='primary'):
            on_login()
        return
    if not result['total']:
        st.warning('没有同时满足这些条件的库内型号。可移除部分条件或清空筛选；这不代表厂家不能生产。')
        return
    pager = st.columns([2, 2, 3])
    pager[0].selectbox('每页型号数', [20, 50, 100], key=PREFIX+'size', on_change=changed)
    # A changed filter can reduce the maximum page; synchronize before widget.
    st.session_state[PREFIX+'page'] = result['page']
    pager[1].number_input('页码', min_value=1, max_value=result['pages'], step=1, key=PREFIX+'page', on_change=lambda: st.session_state.pop(PREFIX+'picked', None))
    pager[2].caption(f'第 {result["page"]} / {result["pages"]} 页 · 总计 {result["total"]:,} 个型号')
    import pandas as pd
    shown = []
    for row in result['rows']:
        item = {'品牌':row.get('品牌',''), '型号':row['型号'], '器件品类':kind}
        for field in result['fields']:
            if field.key == '品牌':
                continue
            value = row.get(field.key)
            if field.units and value is not None:
                unit, scale = field.units[0]
                item[field.label] = f'{float(value)/scale:g} {unit}'
            else:
                item[field.label] = option_label(field, value)
        shown.append(item)
    st.dataframe(pd.DataFrame(shown), hide_index=True, use_container_width=True, height=min(640, 40+35*len(shown)))
    by_pair = {(row.get('品牌') or '', row['型号']):row for row in result['rows']}
    if st.session_state.get(PREFIX+'picked') is not None and st.session_state[PREFIX+'picked'] not in by_pair:
        st.session_state.pop(PREFIX+'picked', None)
    picked = st.selectbox('选择型号，继续查看价格与替代型号', [None]+list(by_pair), key=PREFIX+'picked', format_func=lambda pair: '请选择一个型号' if pair is None else f'{pair[0]} · {pair[1]}')
    st.button('查看价格与替代型号', type='primary', disabled=picked is None, on_click=on_match, args=(by_pair[picked]['型号'] if picked is not None else '',), use_container_width=True)
    st.caption('此处不展示成本。继续后使用原有搜索、客户和成本时间设置，不会自动放宽规格。')
