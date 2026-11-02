"""Reviewed exact-identity public resistor corrections, never price/account data.

The immutable imported catalogue remains available for provenance/rollback.
Effective record and SQL projections share this versioned, source-cited list.
This is deliberately NOT a generic model decoder or an all-brand override.
"""
import json
import math
from pathlib import Path
import re
from functools import lru_cache

PATH=Path(__file__).resolve().parent/'data/resistance_corrections_v1.json'
ALIASES={'KOA':('KOA','Koa'), 'Vishay':('Vishay','VISHAY','威世Vishay','威世VISHAY')}
KINDS=('薄膜电阻','厚膜电阻','贴片电阻','金属膜电阻')
FIELDS=('容值','容值单位','_resistance_ohm','_res_ohm','_value_num','_unit_upper','规格摘要')


def text(value):
    return '' if value is None else str(value).strip()


def compact(value):
    return re.sub(r'\s+','',text(value)).upper()


@lru_cache(maxsize=1)
def catalogue():
    payload=json.loads(PATH.read_text(encoding='utf-8'))
    if payload['schema']!=1: raise ValueError('Unknown resistance correction schema')
    lookup={}
    for group in payload['groups']:
        value=group['ohms']
        if group['brand'] not in ALIASES or group['source'] not in payload['sources'] or not math.isfinite(value) or value<0:
            raise ValueError('Invalid reviewed resistance correction')
        for model in group['models']:
            key=(group['brand'],model)
            if key in lookup or compact(model)!=model: raise ValueError('Duplicate/invalid correction identity')
            lookup[key]={**group,'model':model,'revision':payload['revision'],
                         'evidence':payload['sources'][group['source']]}
    return lookup


def lookup(brand,model,kind=''):
    if kind and kind not in KINDS: return None
    brand_key=compact(brand)
    canonical=next((key for key,aliases in ALIASES.items() if brand_key in {compact(a) for a in aliases}),None)
    return catalogue().get((canonical,compact(model)))


def value_unit(ohms):
    multiplier,unit=(1e6,'MΩ') if ohms>=1e6 else (1e3,'KΩ') if ohms>=1e3 else (1,'Ω')
    return format(ohms/multiplier,'.12g'),unit


def enrich_record(record):
    correction=lookup(record.get('品牌'),record.get('型号'),text(record.get('_component_type') or record.get('器件类型')))
    if not correction: return record
    value,unit=value_unit(correction['ohms'])
    expected={'容值':value,'容值单位':unit,'_resistance_ohm':correction['ohms'],
              '_res_ohm':correction['ohms'],'_value_num':float(value),'_unit_upper':unit,
              '_resistance_correction_revision':correction['revision'],
              '_resistance_correction_source':correction['evidence']['url']}
    if all(text(record.get(k))==text(v) if isinstance(v,str) else isinstance(record.get(k),(int,float)) and record[k]==v for k,v in expected.items()):
        return record
    out=dict(record)
    if not out.get('_resistance_correction_original'):
        original={key:None if isinstance(out.get(key),float) and not math.isfinite(out[key]) else out.get(key)
                  for key in FIELDS if key in out}
        # Only the public resistance fields above; never copy an entire row.
        out['_resistance_correction_original']=json.dumps(original,ensure_ascii=False,default=str)
    out.update(expected)
    summary=text(out.get('规格摘要'))
    if summary:
        pattern=r'(?<![A-Za-z0-9])\d+(?:\.\d+)?\s*[kKmMµμu]?\s*(?:Ω|Ω|[Oo][Hh][Mm][Ss]?)'
        out['规格摘要']=re.sub(pattern,lambda _:value+unit,summary,count=1)
    return out


def enrich_frame(frame):
    if frame is None or frame.empty or not {'品牌','型号'}.issubset(frame.columns): return frame
    # Exact membership first: inspect at most the reviewed records, not decode
    # the1.7M-row library. Positional writes preserve duplicate dataframe indexes.
    models={key[1] for key in catalogue()}
    positions=[i for i,hit in enumerate(frame['型号'].isin(models).to_numpy()) if hit]
    updates=[]
    for pos in positions:
        old=frame.iloc[pos].to_dict()
        new=enrich_record(old)
        if new is not old: updates.append((pos,new))
    if not updates: return frame
    out=frame.copy()
    keys=(*FIELDS,'_resistance_correction_original','_resistance_correction_revision','_resistance_correction_source')
    numeric={'_res_ohm','_resistance_ohm','_value_num'}
    for key in keys:
        if key not in out.columns: out[key]=None if key in numeric else ''
        # Some published prepared snapshots store even numeric aliases as
        # pandas StringDtype. Preserve unrelated values while allowing a real
        # float for reviewed identities (including sub-ohm fractional values).
        if key in numeric:
            if str(out[key].dtype) not in ('float64','float32','object'):
                out[key]=out[key].astype('object')
        elif str(out[key].dtype)!='object':
            out[key]=out[key].astype('object')
    for pos,row in updates:
        for key in keys:
            if key in row: out.iat[pos,out.columns.get_loc(key)]=row[key]
    return out


def install_search_overlay(conn):
    """Read-only source, tiny connection-local replacements, indexed UNION.

    No UPDATE against main and no materialization of the full resistor index.
    Ordinary numeric WHERE clauses still push into the original indexed branch.
    Identity counts/duplicates and all unrelated fields are preserved.
    """
    table='components_search_resistor'
    if conn.execute("SELECT 1 FROM temp.sqlite_master WHERE name='verified_resistance_rows'").fetchone(): return
    columns=[r[1] for r in conn.execute(f'PRAGMA main.table_info("{table}")')]
    if not {'品牌','型号','_component_type','_res_ohm'}.issubset(columns): return
    existing=conn.execute('SELECT type,sql FROM temp.sqlite_master WHERE name=?',(table,)).fetchone()
    if existing and existing[0]!='view': raise ValueError('Unexpected temporary resistor source')
    base=(re.split(r'\bAS\b',existing[1],maxsplit=1,flags=re.I)[1] if existing else f'SELECT * FROM main."{table}"')
    conn.execute('CREATE TEMP VIEW verified_resistance_input AS '+base)
    conn.execute('CREATE TEMP TABLE verified_resistance_values (brand TEXT,model TEXT,ohms REAL,PRIMARY KEY(brand,model)) WITHOUT ROWID')
    conn.executemany('INSERT INTO verified_resistance_values VALUES (?,?,?)',
        [(alias,entry['model'],entry['ohms']) for entry in catalogue().values() for alias in ALIASES[entry['brand']]])
    kinds=','.join("'"+k+"'" for k in KINDS)
    quoted=lambda key:'"'+key.replace('"','""')+'"'
    selections=','.join('v.ohms AS "_res_ohm"' if c=='_res_ohm' else 'b.'+quoted(c) for c in columns)
    # Pin the tiny reviewed set as the outer loop. Without CROSS JOIN SQLite
    # may scan every resistor by kind on each new search connection.
    conn.execute(f'CREATE TEMP TABLE verified_resistance_rows AS SELECT {selections} FROM verified_resistance_values v CROSS JOIN verified_resistance_input b ON b."品牌"=v.brand AND b."型号"=v.model WHERE b."_component_type" IN ({kinds})')
    conn.execute('CREATE INDEX verified_resistance_identity ON verified_resistance_rows(品牌,型号,_component_type)')
    conn.execute('CREATE INDEX verified_resistance_numeric ON verified_resistance_rows(_component_type,_size,_res_ohm)' if '_size' in columns else 'CREATE INDEX verified_resistance_numeric ON verified_resistance_rows(_component_type,_res_ohm)')
    if existing: conn.execute(f'DROP VIEW temp."{table}"')
    names=','.join(quoted(c) for c in columns)
    conn.execute(f'CREATE TEMP VIEW "{table}" AS SELECT {names} FROM verified_resistance_input b WHERE NOT EXISTS (SELECT 1 FROM verified_resistance_rows r WHERE r."品牌"=b."品牌" AND r."型号"=b."型号" AND r."_component_type"=b."_component_type") UNION ALL SELECT {names} FROM verified_resistance_rows')
