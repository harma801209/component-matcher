"""Versioned, exact-order-number parameters; no network or persistent DB writes.

The supplement is deliberately separate from member/cost/runtime databases and
the immutable catalog bundle.  Unknown/ambiguous fields are never inferred from
a similar part number.  Source conditions travel with each verified value.
"""
from functools import lru_cache
import json
import logging
import math
from pathlib import Path
import re

DATA_PATH = Path(__file__).with_name('data') / 'jianghai_parameters_v1.json'
NUMERIC = ('_life_hours_num', '_temp_low', '_temp_high', '_volt_num')
VALUE_FIELDS = {
    '寿命（h）', '工作温度', 'ESR', '纹波电流', '阻抗', 'ESR典型值',
    '寿命类型', '寿命条件', 'ESR条件', '纹波电流条件', '阻抗条件',
    '使用寿命（h）', '使用寿命条件', '参数来源', '参数核验状态',
    '耐压（V）', '_volt',
    *NUMERIC,
}


def is_jianghai(brand):
    text = str(brand).upper()
    return 'JIANGHAI' in text or '江海' in text


def model_key(model):
    # Whitespace is formatting, but electrical and terminal variant codes are
    # significant. No prefix/fuzzy match and no removal of suffix characters.
    return re.sub(r'\s+', '', str(model)).upper()


@lru_cache(maxsize=4)
def _read_data(path, mtime_ns, size):
    with open(path, encoding='utf-8') as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError('invalid Jianghai parameter document')
    if payload.get('schema_version') != 1:
        raise ValueError('unsupported Jianghai parameter schema')
    records = payload['records']
    sources = payload['sources']
    by_model = {}
    for entry in records:
        if not is_jianghai(entry['brand']):
            raise ValueError('non-Jianghai record in supplement')
        values = entry['values']
        if not set(values).issubset(VALUE_FIELDS):
            raise ValueError('unexpected parameter field')
        if any(not isinstance(v, (str, int, float)) for v in values.values()):
            raise ValueError('invalid parameter value')
        for key in NUMERIC:
            if key in values and not math.isfinite(float(values[key])):
                raise ValueError('non-finite numeric parameter')
        if values.get('_life_hours_num', 1) <= 0:
            raise ValueError('non-positive life')
        if any(k in values for k in NUMERIC):
            source = sources[entry['source']]
            if not re.fullmatch(r'[0-9a-f]{64}', source['sha256']):
                raise ValueError('missing source fingerprint')
            if not entry.get('pages') or any(not isinstance(p, int) or p < 1 for p in entry['pages']):
                raise ValueError('missing source pages')
        key = model_key(entry['model'])
        if key in by_model:
            raise ValueError('ambiguous duplicate order number')
        by_model[key] = entry
    return payload, by_model


def load_data():
    try:
        stat = DATA_PATH.stat()
        return _read_data(str(DATA_PATH), stat.st_mtime_ns, stat.st_size)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        logging.getLogger(__name__).warning('Jianghai supplement unavailable: %s', exc)
        return {'records': [], 'sources': {}}, {}


def enrich_record(record):
    if not is_jianghai(record.get('品牌', '')):
        return record
    _, by_model = load_data()
    entry = by_model.get(model_key(record.get('型号', '')))
    if entry is None:
        return record
    out = dict(record)
    out.update(entry['values'])
    # Existing result schemas already include notes, including BOM downloads.
    # Keep the original note and add conditions instead of losing them when a
    # caller selects a legacy set of display columns.
    previous = str(out.get('备注1', ''))
    if previous.strip().lower() in ('nan','none','null','<na>'):
        previous = ''
    previous = re.sub(r'^原厂参数补充\[[^\]]*\]\s*', '', previous)
    out['备注1'] = '原厂参数补充[' + entry['note'] + '] ' + previous
    if entry.get('source'):
        out['备注2'] = entry['values']['参数来源']
    return out


def enrich_frame(frame):
    if frame is None or frame.empty or not {'品牌', '型号'}.issubset(frame.columns):
        return frame
    if not frame.index.is_unique:
        out = enrich_frame(frame.reset_index(drop=True))
        out.index = frame.index
        return out
    mask = frame['品牌'].astype('string').fillna('').str.contains('江海|JIANGHAI', case=False, regex=True)
    if not mask.any():
        return frame
    _, by_model = load_data()
    indices = [idx for idx in frame.index[mask] if model_key(frame.at[idx, '型号']) in by_model]
    if not indices:
        return frame
    out = frame.copy()
    fields = set().union(*(by_model[model_key(out.at[i, '型号'])]['values'] for i in indices))
    for field in fields | {'备注1', '备注2'}:
        if field not in out:
            out[field] = float('nan') if field in NUMERIC else ''
        elif field in NUMERIC:
            import pandas as pd
            out[field] = pd.to_numeric(out[field], errors='coerce')
        elif field not in NUMERIC and str(out[field].dtype) != 'object':
            out[field] = out[field].astype('object')
    for idx in indices:
        row = enrich_record(out.loc[idx].to_dict())
        for field in fields | {'备注1', '备注2'}:
            if field in row:
                out.at[idx, field] = row[field]
    return out


def install_search_overlay(conn):
    """Shadow only capacitor numeric columns using a connection-local view.

    Persisted catalog and protected runtime DB bytes remain untouched. The
    original indexed tables retain their lookup indexes; the exact-key TEMP
    table is tiny. Repeated installation on a connection is a no-op.
    """
    table = 'components_search_capacitor'
    if not conn.execute('SELECT 1 FROM main.sqlite_master WHERE type="table" AND name=?', (table,)).fetchone():
        return
    if conn.execute('SELECT 1 FROM temp.sqlite_master WHERE name=?', (table,)).fetchone():
        return
    columns = [row[1] for row in conn.execute(f'PRAGMA main.table_info("{table}")')]
    if not {'品牌', '型号', *NUMERIC}.issubset(columns):
        return
    payload, _ = load_data()
    entries = [e for e in payload['records'] if any(k in e['values'] for k in NUMERIC)]
    if not entries:
        return
    conn.execute('CREATE TEMP TABLE jianghai_verified_parameters (brand TEXT, model TEXT, life REAL, low REAL, high REAL, voltage REAL, PRIMARY KEY(brand,model)) WITHOUT ROWID')
    conn.executemany('INSERT INTO temp.jianghai_verified_parameters VALUES (?,?,?,?,?,?)', [
        (e['brand'], e['model'], *(e['values'].get(k) for k in NUMERIC)) for e in entries
    ])
    aliases = dict(zip(NUMERIC, ('life', 'low', 'high', 'voltage')))
    selections = [
        f'COALESCE(v.{aliases[col]},c."{col}") AS "{col}"' if col in aliases else f'c."{col}"'
        for col in columns
    ]
    conn.execute(f'CREATE TEMP VIEW "{table}" AS SELECT ' + ','.join(selections) +
                 f' FROM main."{table}" c LEFT JOIN temp.jianghai_verified_parameters v '
                 'ON c."品牌"=v.brand AND c."型号"=v.model')


def annotate_pending_display(frame):
    """Display-only labels. Never use these strings as numerical search data."""
    if frame is None or frame.empty or not {'品牌','型号'}.issubset(frame.columns):
        return frame
    if not frame.index.is_unique:
        out = annotate_pending_display(frame.reset_index(drop=True))
        out.index = frame.index
        return out
    _, by_model = load_data()
    out = frame
    for idx in frame.index:
        if not is_jianghai(frame.at[idx,'品牌']):
            continue
        entry = by_model.get(model_key(frame.at[idx,'型号']))
        if entry is None:
            continue
        for field in ('寿命（h）','工作温度','ESR','纹波电流'):
            if field not in frame.columns or str(frame.at[idx,field]).strip().lower() not in ('','nan','none','null'):
                continue
            if out is frame:
                out = frame.copy()
            out.at[idx,field] = '待核实（见备注）'
    return out
