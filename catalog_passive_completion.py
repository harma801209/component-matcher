"""Bounded, blank-only catalogue projection from existing explicit source fields.

This never rewrites a library/runtime DB or generates ordering codes. Compressed
line records keep large leaded-resistor categories out of Streamlit's object
cache; installation uses batches and only a connection-local TEMP table.
"""
import gzip
import io
import json
import math
import re
import sqlite3
import threading
from contextlib import closing
from pathlib import Path

KINDS = frozenset(('贴片电阻 厚膜电阻 薄膜电阻 合金电阻 碳膜电阻 绕线电阻 金属氧化膜电阻 热敏电阻 '
                   'MLCC 引线型陶瓷电容 薄膜电容 铝电解电容 安规电容 钽电容 '
                   '贴片压敏电阻 引线型压敏电阻 压敏电阻 共模电感 功率电感 射频电感 磁珠 晶振 振荡器 实时时钟模块').split())
EMPTY = {'', '-', '--', '/', 'N/A', 'NA', 'NULL', 'NONE', 'NAN'}
NUMERIC = frozenset(('_pf', '_volt_num', '_res_ohm', '_power_watt', '_temp_low', '_temp_high',
                     '_catalog_inductance_uh', '_catalog_impedance_ohm', '_catalog_frequency_hz'))
TEXT = ('_size', '_body_size', '_pitch', '_tol', '_mount_style', '_impedance_text')
FIELDS = (*TEXT, *sorted(NUMERIC))
RAW_COLUMNS = ('品牌', '型号', '_component_type', *FIELDS, '封装代码', '尺寸（inch）', '尺寸（mm）',
               '脚距（mm）', '安装方式', '工作温度', '容值', '容值单位', '耐压（V）',
               '电感值', '电感单位', '电感误差', '共模阻抗', '阻抗单位', '阻抗@100MHz', '输出频率', '频率', '频率单位')

# FOJAN FRC/FPS/FPL official PDFs, dimensions p.3 and order codes p.2.
# See docs/catalog_parameter_completion.md for exact URLs/revisions. These are
# series-scoped physical dimensions, NOT generic size-to-power assumptions.
FOJAN_DIMENSIONS = {
    '01005':'0.40±0.02 × 0.20±0.02 × 0.13±0.03 mm',
    '0201':'0.60±0.03 × 0.30±0.03 × 0.23±0.03 mm',
    '0402':'1.00±0.05 × 0.50±0.05 × 0.35±0.05 mm',
    '0603':'1.60±0.10 × 0.80±0.10 × 0.45±0.10 mm',
    '0805':'2.00±0.10 × 1.25±0.10 × 0.50±0.10 mm',
    '1206':'3.10±0.10 × 1.60±0.10 × 0.55±0.10 mm',
    '1210':'3.10±0.10 × 2.50±0.15 × 0.55±0.10 mm',
    '1218':'3.10±0.10 × 4.60±0.10 × 0.55±0.10 mm',
    '1812':'4.50±0.20 × 3.10±0.20 × 0.55±0.10 mm',
    '2010':'5.00±0.10 × 2.50±0.15 × 0.55±0.10 mm',
    '2512':'6.35±0.10 × 3.10±0.15 × 0.55±0.10 mm',
}


def fojan_explicit_specs(row):
    brand = text(row.get('品牌')).upper().replace(' ', '')
    if not ('FOJAN' in brand or '富捷' in brand) or row.get('_component_type') not in {'贴片电阻','厚膜电阻'}:
        return {}
    match = re.fullmatch(r'(FRC|FPS|FPL)(01005|\d{4})([ABCDFJKMP])([0-9R]{3,4})([TQRB])([SCA])',
                         text(row.get('型号')).upper().replace(' ', ''))
    if not match:
        return {}
    series, size, tolerance, code, _, _ = match.groups()
    sizes = set(FOJAN_DIMENSIONS)
    if series == 'FPS': sizes -= {'01005','0201','0402'}
    if series == 'FPL': sizes -= {'01005','0201'}
    if size not in sizes or (text(row.get('_size')) and text(row['_size']) != size):
        return {}
    if series == 'FPL':
        if tolerance not in 'FJ' or not re.fullmatch(r'R\d{2}' if size == '0603' else r'R\d{3}',code): return {}
    elif tolerance not in ('ABCDFJ' if series == 'FRC' else 'FJ') or len(code) != (3 if tolerance == 'J' else 4):
        return {}
    patch = {'_body_size': FOJAN_DIMENSIONS[size]}
    # Unknown/ambiguous encoding is left blank. In particular do not treat FPQ
    # as FQP, use EIA-96 without its table, or infer a power from the package.
    resistance = None
    if series == 'FPL':
        digits = 3 if size == '0603' else 4
        if len(code) == digits and re.fullmatch(r'R\d+',code): resistance = float('0.'+code[1:])
    elif (series == 'FRC' and tolerance in 'ABCDF') or (series == 'FPS' and tolerance == 'F'):
        if len(code) == 4:
            if code.isdigit() and int(code[-1]) <= 6: resistance = int(code[:-1]) * 10**int(code[-1])
            elif re.fullmatch(r'\d*R\d+',code): resistance = float(code.replace('R','.'))
    elif tolerance == 'J' and len(code) == 3:
        if code.isdigit() and int(code[-1]) <= 6: resistance = int(code[:-1]) * 10**int(code[-1])
        elif re.fullmatch(r'\d*R\d+',code): resistance = float(code.replace('R','.'))
    if resistance is not None: patch['_res_ohm'] = resistance
    return patch


def fields_for_kind(kind):
    fields = {'_size', '_body_size', '_mount_style', '_tol'}
    if kind in {'共模电感', '功率电感', '射频电感', '磁珠'}:
        fields |= {'_catalog_inductance_uh', '_catalog_impedance_ohm', '_impedance_text'}
    elif kind in {'晶振', '振荡器', '实时时钟模块'}:
        fields.add('_catalog_frequency_hz')
    elif kind in {'MLCC', '引线型陶瓷电容', '薄膜电容', '铝电解电容', '安规电容', '钽电容'}:
        fields |= {'_pf', '_volt_num', '_pitch', '_temp_low', '_temp_high'}
    elif '压敏' in kind:
        fields.add('_pitch')
    else:
        fields |= {'_res_ohm', '_power_watt'}
        fields.discard('_mount_style')
    return fields


def columns_for_kind(kind):
    columns = {'品牌', '型号', '_component_type', '封装代码', '尺寸（inch）', '尺寸（mm）', '安装方式'} | fields_for_kind(kind)
    if kind in {'共模电感', '功率电感', '射频电感', '磁珠'}:
        columns |= {'电感值', '电感单位', '电感误差', '共模阻抗', '阻抗单位', '阻抗@100MHz'}
    elif kind in {'晶振', '振荡器', '实时时钟模块'}:
        columns |= {'输出频率', '频率', '频率单位'}
    elif kind in {'MLCC', '引线型陶瓷电容', '薄膜电容', '铝电解电容', '安规电容', '钽电容'}:
        columns |= {'容值', '容值单位', '耐压（V）', '工作温度', '脚距（mm）'}
    elif '压敏' in kind:
        columns.add('脚距（mm）')
    return columns


def text(value):
    value = '' if value is None else str(value).strip()
    return '' if value.upper() in EMPTY else value


def scalar(value, multiplier=1):
    value = text(value)
    if not re.fullmatch(r'[+]?(?:\d+(?:\.\d*)?|\.\d+)', value):
        return None
    number = float(value) * multiplier
    return number if math.isfinite(number) and number >= 0 else None


def temperature(value):
    # Only a complete explicit working-temperature field, never model text,
    # a series code, storage/reflow temperature or a dielectric class code.
    value = text(value).upper().replace('−', '-').replace('–', '-').replace('～', '~').replace('至', '~')
    value = value.replace('°C', '').replace('˚C', '').replace('℃', '').replace('C', '').replace('TO', '~')
    match = re.fullmatch(r'\s*([+-]?\d+(?:\.\d+)?)\s*(?:~|-)\s*([+-]?\d+(?:\.\d+)?)\s*', value)
    if not match:
        return None, None
    low, high = map(float, match.groups())
    return (low, high) if -273.15 <= low <= high <= 1000 else (None, None)


def physical_size(value):
    value = text(value)
    # Keep actual dimensions with their tolerances, not coarse AXIAL/SMD labels.
    return value if re.search(r'\d.*[x×*].*\d|[ØΦφ]\s*\d|D\d+(?:\.\d+)?', value, re.I) else ''


def complete(row, model_resolver=None):
    """Return a sparse patch; known normalized values always win."""
    kind = row.get('_component_type')
    if kind not in KINDS or not text(row.get('型号')):
        return {}
    patch = {}
    def put(key, value):
        if key not in patch and not text(row.get(key)) and value is not None and text(value):
            patch[key] = value
    if kind != 'MLCC':
        put('_size', text(row.get('尺寸（inch）')) or text(row.get('封装代码')))
    put('_body_size', physical_size(row.get('尺寸（mm）')))
    for key, value in fojan_explicit_specs(row).items():
        put(key, value)
    pitch = text(row.get('脚距（mm）'))
    match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*(?:mm)?', pitch, re.I)
    if match:
        put('_pitch', match[1] + ' mm')
    put('_mount_style', text(row.get('安装方式')))
    if kind in {'MLCC', '引线型陶瓷电容', '薄膜电容', '铝电解电容', '安规电容', '钽电容'}:
        unit = text(row.get('容值单位')).upper().replace('Μ', 'U').replace('µ', 'U').replace('μ', 'U')
        if unit in {'PF', 'NF', 'UF', 'MF', 'F'}:
            put('_pf', scalar(row.get('容值'), {'PF':1, 'NF':1e3, 'UF':1e6, 'MF':1e9, 'F':1e12}[unit]))
        voltage = re.fullmatch(r'(\d+(?:\.\d+)?)\s*(?:V(?:DC)?)?', text(row.get('耐压（V）')), re.I)
        if voltage:
            put('_volt_num', scalar(voltage[1]))
        low, high = temperature(row.get('工作温度'))
        put('_temp_low', low)
        put('_temp_high', high)
        if kind == 'MLCC' and model_resolver and any(not text(row.get(k)) and k not in patch for k in ('_pf', '_volt_num')):
            decoded = model_resolver(text(row.get('型号')), text(row.get('品牌'))) or {}
            decoded_unit = text(decoded.get('容值单位')).upper()
            if decoded_unit in {'PF', 'NF', 'UF'}:
                put('_pf', scalar(decoded.get('容值'), {'PF':1, 'NF':1e3, 'UF':1e6}[decoded_unit]))
            put('_volt_num', scalar(decoded.get('耐压（V）')))
    if kind in {'共模电感', '功率电感', '射频电感', '磁珠'}:
        unit = text(row.get('电感单位')).upper().replace('Μ', 'U').replace('µ', 'U').replace('μ', 'U')
        if unit in {'NH', 'UH', 'MH', 'H'}:
            put('_catalog_inductance_uh', scalar(row.get('电感值'), {'NH':.001, 'UH':1, 'MH':1e3, 'H':1e6}[unit]))
        impedance = text(row.get('阻抗@100MHz')) if kind == '磁珠' else text(row.get('共模阻抗'))
        if impedance:
            put('_impedance_text', impedance + (' @100MHz' if kind == '磁珠' and not re.search('MHZ', impedance, re.I) else ''))
            # A range/series envelope is useful text, not a scalar rating.
            match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*(Ω|Ohms?|kΩ)?(?:\s*@\s*100\s*MHz)?', impedance, re.I)
            if match and (match[2] or text(row.get('阻抗单位')) in {'Ω', 'OHM'}):
                put('_catalog_impedance_ohm', scalar(match[1], 1000 if (match[2] or '').lower() == 'kω' else 1))
        tolerance = text(row.get('电感误差'))
        if re.fullmatch(r'±?\d+(?:\.\d+)?%?', tolerance):
            put('_tol', tolerance.lstrip('±').rstrip('%'))
    if kind in {'晶振', '振荡器', '实时时钟模块'}:
        unit = text(row.get('频率单位')).upper()
        if unit in {'HZ', 'KHZ', 'MHZ', 'GHZ'}:
            put('_catalog_frequency_hz', scalar(text(row.get('输出频率')) or row.get('频率'), {'HZ':1, 'KHZ':1e3, 'MHZ':1e6, 'GHZ':1e9}[unit]))
    return patch


def load(path, kind, model_resolver=None, index_path=None, trusted_power_sources=frozenset({'text', 'numeric', 'context', 'thermistor_max_power'})):
    """Stream projected public specification columns into immutable gzip bytes."""
    if kind not in KINDS or not Path(path).is_file():
        return b''
    import pyarrow.parquet as pq
    import pyarrow.compute as pc
    existing, missing = set(), {}
    ordered = sorted(fields_for_kind(kind))
    bits = {key:1 << position for position,key in enumerate(ordered)}
    if index_path and Path(index_path).is_file():
        from component_filters import profile
        table, _ = profile(kind)
        with closing(sqlite3.connect(Path(index_path).resolve().as_uri()+'?mode=ro', uri=True)) as index:
            existing = {r[1] for r in index.execute(f'PRAGMA table_info("{table}")')} & set(ordered)
            mask = '+'.join(f'CASE WHEN "{key}" IS NULL OR UPPER(TRIM(CAST("{key}" AS TEXT))) IN (\'\',\'-\',\'--\',\'/\',\'N/A\',\'NA\',\'NULL\',\'NONE\',\'NAN\') THEN {bits[key]} ELSE 0 END' for key in sorted(existing)) or '0'
            for brand, model, value in index.execute(f'SELECT 品牌,型号,({mask}) AS gaps FROM "{table}" WHERE _component_type=? AND COALESCE(型号,\'\')<>\'\' AND gaps>0', (kind,)):
                identity = (brand or '')+'\0'+model
                missing[identity] = missing.get(identity,0) | value
    output = io.BytesIO()
    with pq.ParquetFile(path) as source, gzip.GzipFile(fileobj=output, mode='wb', mtime=0, compresslevel=1) as zipped:
        names = set(source.schema_arrow.names)
        if not {'品牌', '型号', '_component_type'}.issubset(names):
            return b''
        wanted = columns_for_kind(kind)
        if '_power_watt' in fields_for_kind(kind):
            wanted.add('_power_source')
        columns = sorted(wanted & names)
        projected = fields_for_kind(kind) - {'_temp_low', '_temp_high'}
        for batch in source.iter_batches(batch_size=2048, columns=columns, use_threads=False):
            batch = batch.filter(pc.equal(batch.column('_component_type'), kind))
            for row in batch.to_pylist():
                patch = complete(row, model_resolver)
                gap_mask = missing.get((row['品牌'] or '')+'\0'+(row['型号'] or ''),0)
                # Existing indexed fields may be absent/stale even when their
                # prepared counterpart was already normalized. Do not cache
                # Python dicts for hundreds of thousands of these records.
                for key in projected:
                    if key in existing and not gap_mask & bits[key]:
                        continue
                    if key == '_power_watt' and text(row.get('_power_source')) not in trusted_power_sources:
                        continue
                    value = row.get(key)
                    if key not in patch and text(value):
                        if key in NUMERIC:
                            value = scalar(value)
                        if value is not None:
                            patch[key] = value
                patch = {key:value for key,value in patch.items() if key in bits and (key not in existing or gap_mask & bits[key])}
                if patch:
                    zipped.write((json.dumps([row['品牌'], row['型号'], patch], ensure_ascii=False, separators=(',', ':'))+'\n').encode('utf-8'))
    return output.getvalue()


def install(conn, kind, compressed, table):
    """Return the completed TEMP source name. Never changes a main-store row."""
    if kind not in KINDS or not compressed:
        return table
    if conn.execute("SELECT 1 FROM sqlite_temp_master WHERE name='catalog_passive_source'").fetchone():
        return 'catalog_passive_source'
    columns = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
    if not {'品牌', '型号', '_component_type'}.issubset(columns):
        return table
    fields = sorted(fields_for_kind(kind))
    declarations = ','.join(f'"{key}" {"REAL" if key in NUMERIC else "TEXT"}' for key in fields)
    conn.execute('CREATE TEMP TABLE catalog_passive_patch_rows (品牌 TEXT,型号 TEXT,'+declarations+')')
    conn.execute('PRAGMA temp.cache_size = -16384')
    pending = []
    def flush():
        conn.executemany('INSERT INTO catalog_passive_patch_rows VALUES ('+','.join('?' for _ in range(len(fields)+2))+')', pending)
        pending.clear()
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as source:
        for line in source:
            brand, model, patch = json.loads(line)
            if not model or not isinstance(patch, dict):
                continue
            patch = {k:v for k,v in patch.items() if k in fields_for_kind(kind)}
            pending.append((brand, model, *(patch.get(key) for key in fields)))
            if len(pending) == 2048:
                flush()
    flush()
    # Bulk-load without a per-row B-tree update; then keep one whole actual
    # source record (the first), never MAX/COALESCE values across duplicates.
    conn.execute('CREATE INDEX catalog_passive_patch_order ON catalog_passive_patch_rows(品牌,型号)')
    conn.execute('CREATE TEMP TABLE catalog_passive_patches AS SELECT p.* FROM catalog_passive_patch_rows p JOIN (SELECT MIN(rowid) AS chosen FROM catalog_passive_patch_rows GROUP BY 品牌,型号) first ON p.rowid=first.chosen')
    conn.execute('CREATE UNIQUE INDEX catalog_passive_patch_identity ON catalog_passive_patches(品牌,型号)')
    conn.execute('DROP TABLE catalog_passive_patch_rows')
    expressions = []
    for key in sorted(columns | fields_for_kind(kind)):
        original = f'b."{key}"' if key in columns else 'NULL'
        if key in fields:
            # Preserve known zero, explicit values and all indexed identities.
            value = f'd."{key}"'
            original = f'CASE WHEN {original} IS NULL OR UPPER(TRIM(CAST({original} AS TEXT))) IN (\'\',\'-\',\'--\',\'/\',\'N/A\',\'NA\',\'NULL\',\'NONE\',\'NAN\') THEN {value} ELSE {original} END'
        expressions.append(original + f' AS "{key}"')
    conn.execute('CREATE TEMP TABLE catalog_passive_source AS SELECT '+','.join(expressions)+f' FROM "{table}" b LEFT JOIN catalog_passive_patches d ON b.品牌 IS d.品牌 AND b.型号=d.型号 WHERE b._component_type=?', (kind,))
    conn.execute('CREATE INDEX catalog_passive_identity ON catalog_passive_source(品牌,型号)')
    conn.execute('DROP TABLE catalog_passive_patches')
    return 'catalog_passive_source'


class SharedSource:
    """Public-catalogue-only resource; never holds member/customer/cost state."""
    def __init__(self, connection):
        self.connection = connection
        self.lock = threading.RLock()

    def __del__(self):
        try:
            self.connection.close()
        except Exception:
            pass
