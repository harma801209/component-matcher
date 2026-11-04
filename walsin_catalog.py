"""Public Walsin catalogue supplementation, never rule-combination generation.

Only captured, cross-checked manufacturer base identities enter the catalogue.
Known values win except exact old-value corrections backed by source and code.
Blank completion is not proof of lifecycle or stock.
All search amendments are connection-local TEMP tables, not library rewrites.
"""
from functools import lru_cache
from pathlib import Path
import json
import re
import sqlite3
import tempfile
import threading

BRAND = '华新科Walsin'
DATA = Path(__file__).with_name('catalog_sources') / 'walsin_verified.json'
GENERAL_PDF = 'https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_General_Purpose.pdf'
MT_PDF = 'https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_Automotive_MT.pdf'


SIDECAR_LOCK=threading.RLock()


def is_brand(value):
    return 'WALSIN' in str(value).upper() or '华新科' in str(value)


def core(value):
    """Only the documented conventional C termination + T/G reel suffix."""
    value = re.sub(r'\s+', '', str(value or '')).upper()
    return re.sub(r'C[TG]$', '', value)


@lru_cache(maxsize=1)
def document():
    result = json.loads(DATA.read_text(encoding='utf-8'))
    if result.get('schema') != 1:
        raise ValueError('Unsupported Walsin evidence schema')
    return result


@lru_cache(maxsize=1)
def by_model():
    return {r['model']: r for r in document()['records']}


@lru_cache(maxsize=1)
def corrections():
    return {r['model']:r for r in document().get('corrections',())}


def normalized(value,field):
    value=str(value).strip().upper().replace('±','').replace('%','').replace(' ','')
    if field=='_mat':
        return 'C0G' if value in {'COG','C0G','NPO','NP0','COG(NPO)','COG;NPO'} else value
    if field=='_tol':
        match=re.fullmatch(r'(\d+(?:\.\d+)?)(PF)?',value)
        return f'{float(match[1]):g}'+(match[2] or '') if match else value
    try:
        return float(value.rstrip('V') if field=='_volt_num' else value)
    except ValueError:
        return value


def complete_mt_temperature(record):
    """Blank-only rating completion, never overriding conflicting supplied fields."""
    result=record
    item=listed(record.get('型号','')) if is_brand(record.get('品牌','')) else None
    high=mt_temperature_high(item) if item else None
    material_agrees = item is not None and all(
        blank(record.get(key)) or normalized(record[key], '_mat') == normalized(item['material'], '_mat')
        for key in ('_mat', '材质（介质）'))
    numeric_agrees = high is not None and all(
        blank(record.get(key)) or normalized(record[key], key) == value
        for key, value in (('_temp_low', -55), ('_temp_high', high)))
    if high is not None and material_agrees and numeric_agrees and blank(record.get('工作温度')):
        result=dict(record)
        result['工作温度']=f'-55~{high}℃'
        for key,value in (('_temp_low',-55),('_temp_high',high)):
            if key in result and blank(result[key]):result[key]=value
        note='华科 MT 原厂2026-09规格书第3页额定温区，核对2026-11-04：'+MT_PDF
        original=result.get('备注1')
        result['备注1']=note if blank(original) else str(original)+'；'+note
    return result


def enrich_record(record):
    """Exact-model, exact-old-value corrections corroborated by source/code."""
    result=record
    correction=corrections().get(str(record.get('型号','')).strip().upper())
    if not correction or not is_brand(record.get('品牌','')):
        return complete_mt_temperature(result)
    result=dict(result)
    companions={'_mat':('材质（介质）',),'_tol':('容值误差',),'_volt_num':('耐压（V）','_volt'),'_pf':('容值_pf',)}
    changed=False
    for field,change in correction['fields'].items():
        for column in (field,*companions[field]):
            if column in result and normalized(result[column],field)==normalized(change['old'],field):
                result[column]=change['new'];changed=True
        if field=='_pf' and '容值' in result:
            try:
                factor={'PF':1,'NF':1000,'UF':1e6}.get(str(result.get('容值单位','')).upper())
                if factor and float(result['容值'])*factor==change['old']:
                    result['容值']=change['new']/factor;changed=True
            except (ValueError,TypeError):pass
    if changed:
        source=document()['sources'][correction['source']]['url']
        note=f'华科原厂选型表与编码交叉核对，已修正历史参数（2026-11-03）：{source}'
        original=result.get('备注1')
        if blank(original):result['备注1']=note
        elif note not in str(original):result['备注1']=str(original)+'；'+note
    return complete_mt_temperature(result)


def enrich_frame(frame):
    if frame is None or frame.empty or not {'品牌','型号'}.issubset(frame.columns):
        return frame
    models=frame['型号'].astype(str).str.strip().str.upper()
    mask=models.isin(corrections())
    temperatures=frame['工作温度'].map(blank) if '工作温度' in frame else True
    mask |= models.str.startswith('MT') & frame['品牌'].map(is_brand) & temperatures
    if not mask.any():return frame
    result=frame.copy()
    for index in result.index[mask]:
        before=result.loc[index].to_dict();after=enrich_record(before)
        for key,value in after.items():
            if key not in result.columns:result[key]=''
            if str(value)!=str(before.get(key,'')):
                if str(result[key].dtype)=='category':result[key]=result[key].astype(object)
                result.at[index,key]=value
    return result


def listed(model):
    return by_model().get(core(model))


def blank(value):
    return value is None or str(value).strip().lower() in {'', 'none', 'nan', '<na>', 'nat', '-'}


def body_size(item):
    dimensions=[str(item.get(key) or '').strip() for key in ('length','width','height')]
    pattern=r'\d+(?:\.\d+)?(?:±\d+(?:\.\d+)?|\+\d+(?:\.\d+)?/-\d+(?:\.\d+)?)?'
    if all(re.fullmatch(pattern,value) for value in dimensions):
        return ' × '.join(dimensions)+' mm'
    return ''


def mt_temperature_high(item):
    # Original MT September-2026 page3 table: X8G150; NP0 and X7R125;
    # X6S105. No temperature is inferred for MG/ST or an unlisted identity.
    if item.get('series')!='Automotive Caps Qualified to AEC-Q200 (MT series)':
        return None
    return {'X8G':150,'C0G':125,'X7R':125,'X6S':105}.get(item.get('material'))


def row(item, model=None):
    """Published fields only; multiple body variants never become one body."""
    model = model or item['model']
    series = re.search(r'\(([A-Z0-9]+) series\)', item['series'])
    series = series[1] if series else ('常规' if item['series']=='General Purpose Caps' else item['series'])
    source = document()['sources'][item['source']]['url']
    result = {'品牌':BRAND, '型号':model, '器件类型':'MLCC', '系列':series,
              '系列说明':item['series'], '尺寸（inch）':item['size'],
              '材质（介质）':item['material'], '容值':item['pf'], '容值单位':'pF',
              '容值_pf':item['pf'], '容值误差':item['tol'], '耐压（V）':item['voltage'],
              '长度（mm）':item.get('length') or '', '宽度（mm）':item.get('width') or '',
              '高度（mm）':item.get('height') or '', '安装方式':'贴片',
              '_catalog_membership':'manufacturer_listed', '_model_rule_authority':'walsin_public_catalogue',
              '生产状态':'', '备注1':f'华科原厂选型表，核对2026-11-03：{source}',
              '型号粒度':'原厂选型基本料号；订货端子／包装尾码待确认' if model==item['model'] else '输入的完整料号；基础规格已核对，订货尾码须独立确认',
              '_walsin_source_url':source}
    result['_body_size']=body_size(item)
    if item['series']=='General Purpose Caps':
        high={'C0G':125,'X7R':125,'X5R':85,'X6S':105,'X7S':125}.get(item['material'])
        if high:
            result['工作温度']=f'-55~{high}℃'
    high=mt_temperature_high(item)
    if high is not None:
        result['工作温度']=f'-55~{high}℃'
        result['备注1']+='；额定温区依据原厂2026-09规格书第3页：'+MT_PDF
    if 'Qualified to AEC-Q200' in item['series']:
        result['特殊用途']='车规 AEC-Q200'
    if 'Soft' in item['series'] or 'Soft term' in item['series']:
        result['特殊用途']=(result.get('特殊用途','')+' | 软端子').strip(' |')
    if item.get('dimension_variants'):
        result['备注2']='原厂同一基本料号列有多种本体尺寸／厚度，具体结构须核对独立规格书，未组合不同版本尺寸。'
    return result


@lru_cache(maxsize=1)
def catalogue_rows():
    return tuple(row(r) for r in document()['records'])


def rows_for_pairs(pairs):
    result=[]
    for brand,model in pairs:
        item=listed(model) if is_brand(brand) else None
        if item:
            result.append(row(item,model))
    return result


def ordering_warning(record):
    if is_brand(record.get('品牌','')) and str(record.get('型号','')).upper() in by_model():
        return '原厂目录列的是基本料号，端子／包装完整订货尾码尚待确认，不能直接下单'
    return ''


@lru_cache(maxsize=1)
def index_frames():
    """Narrow public sidecars without preparing 23k full application rows.

    The source snapshot has already validated units and coding. Normal search
    prepares only its selected candidate rows, not this complete catalogue.
    """
    import pandas as pd
    cores=[];capacitors=[]
    for item in document()['records']:
        identity={'品牌':BRAND,'型号':item['model'],'_component_type':'MLCC'}
        cores.append(dict(identity,_model_clean=item['model']))
        special=[]
        if 'Qualified to AEC-Q200' in item['series']:
            special.extend(('车规','AEC-Q200'))
        if 'Soft' in item['series']:
            special.append('软端子')
        high=({'C0G':125,'X7R':125,'X5R':85,'X6S':105,'X7S':125}.get(item['material'])
              if item['series']=='General Purpose Caps' else mt_temperature_high(item))
        capacitors.append(dict(identity,_size=item['size'],
            _mat='COG(NPO)' if item['material']=='C0G' else item['material'],
            _pf=item['pf'],_tol=item['tol'],_volt_num=item['voltage'],
            _mount_style='贴片',_special_use_norm=' | '.join(special),
            _body_size=body_size(item) or None,
            _temp_low=-55 if high else None,_temp_high=high,
            **{'长度（mm）':item.get('length'),'宽度（mm）':item.get('width'),'高度（mm）':item.get('height')}))
    return {'components_search_core':pd.DataFrame(cores),'components_search_capacitor':pd.DataFrame(capacitors)}


def public_sidecar():
    with SIDECAR_LOCK:
        return _build_public_sidecar()


@lru_cache(maxsize=1)
def _build_public_sidecar():
    """One public-only indexed file per process; never copy it per query."""
    folder=tempfile.TemporaryDirectory(prefix='walsin-public-evidence-')
    path=Path(folder.name)/'listed.sqlite'
    conn=sqlite3.connect(path)
    try:
        for table,frame in index_frames().items():
            frame.to_sql(table,conn,index=False)
            conn.execute(f'CREATE UNIQUE INDEX "{table}_model" ON "{table}"(型号)')
        conn.commit()
    finally:
        conn.close()
    return folder,path


def install_search_overlay(conn):
    """Supplement the public index without changing any persisted database.

    Known values are retained except evidence-guarded historical corrections.
    Aliased CT/CG identities suppress adding a
    duplicate base identity. Upstream overlays are retained and idempotent.
    """
    marker='walsin_catalogue_capacitor'
    if conn.execute('SELECT 1 FROM temp.sqlite_master WHERE name=?',(marker,)).fetchone():
        return
    tables=('components_search_core','components_search_capacitor')
    if not all(conn.execute('SELECT 1 FROM main.sqlite_master WHERE name=?',(table,)).fetchone() for table in tables):
        return
    if not any(r[1]=='walsin_public_evidence' for r in conn.execute('PRAGMA database_list')):
        path=public_sidecar()[1]
        try:
            conn.execute('ATTACH DATABASE ? AS walsin_public_evidence',(path.as_uri()+'?mode=ro',))
        except sqlite3.OperationalError as exc:
            # Legacy callers opened without SQLite URI support. Keep their
            # compatibility copy entirely in memory, never open the file RW.
            if 'unable to open database' not in str(exc):raise
            conn.execute("ATTACH DATABASE ':memory:' AS walsin_public_evidence")
            evidence=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
            try:
                for table in tables:
                    schema=evidence.execute(f'PRAGMA table_info("{table}")').fetchall()
                    definition=','.join(f'"{r[1]}" {r[2]}' for r in schema)
                    conn.execute(f'CREATE TABLE walsin_public_evidence."{table}" ({definition})')
                    conn.executemany(f'INSERT INTO walsin_public_evidence."{table}" VALUES ({",".join("?" for _ in schema)})',evidence.execute(f'SELECT * FROM "{table}"'))
                    conn.execute(f'CREATE UNIQUE INDEX walsin_public_evidence."{table}_model" ON "{table}"(型号)')
            finally:
                evidence.close()
    for table in tables:
        columns=[r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
        names=','.join('"'+c+'"' for c in columns)
        existing=[dict(zip(columns,r)) for r in conn.execute(f'SELECT * FROM "{table}" WHERE _component_type=\'MLCC\' AND (UPPER(品牌) LIKE \'%WALSIN%\' OR 品牌 LIKE \'%华新科%\')')]
        changes=[]
        for old in existing:
            completed=dict(enrich_record(old))
            if completed != old:
                changes.append(completed)
        addon='walsin_catalogue_'+('core' if table.endswith('_core') else 'capacitor')
        known=addon+'_identities'
        conn.execute(f'CREATE TEMP TABLE "{known}" (model TEXT PRIMARY KEY)')
        conn.executemany(f'INSERT OR IGNORE INTO "{known}" VALUES (?)',((core(r['型号']),) for r in existing))
        conn.execute(f'CREATE TEMP TABLE "{addon}" AS SELECT * FROM main."{table}" WHERE 0')
        values=[tuple(None if blank(r.get(c)) else r.get(c) for c in columns) for r in changes]
        if values:
            conn.executemany(f'INSERT INTO "{addon}" ({names}) VALUES ({",".join("?" for _ in columns)})',values)
        conn.execute(f'CREATE INDEX "{addon}_identity" ON "{addon}"(品牌,型号,_component_type)')
        if '_model_clean' in columns:
            conn.execute(f'CREATE INDEX "{addon}_clean" ON "{addon}"(_model_clean)')
        prior=conn.execute('SELECT type,sql FROM temp.sqlite_master WHERE name=?',(table,)).fetchone()
        if prior and prior[0]!='view':
            raise ValueError('Unexpected temporary Walsin source')
        base=re.split(r'\bAS\b',prior[1],maxsplit=1,flags=re.I)[1] if prior else f'SELECT * FROM main."{table}"'
        if prior:
            conn.execute(f'DROP VIEW temp."{table}"')
        available={r[1] for r in conn.execute(f'PRAGMA walsin_public_evidence.table_info("{table}")')}
        projections=[]
        for key in columns:
            if key in {'品牌','型号','_component_type','_model_clean'}:
                projections.append(f'b."{key}" AS "{key}"')
                continue
            current=f'COALESCE(a."{key}",b."{key}")'
            if key in available and key not in {'品牌','型号','_component_type','_model_clean'}:
                current=f'CASE WHEN ({current} IS NULL OR LOWER(TRIM(CAST({current} AS TEXT))) IN (\'\',\'none\',\'nan\',\'<na>\',\'nat\',\'-\')) AND q."{key}" IS NOT NULL THEN q."{key}" ELSE {current} END'
            projections.append(current+f' AS "{key}"')
        source_columns=','.join(f'q."{key}"' if key in available else 'NULL' for key in columns)
        if table == 'components_search_core':
            # Core carries identity only: Walsin completion never changes its
            # existing rows. Keep exact model lookup free of needless joins.
            conn.execute(f'CREATE TEMP VIEW "{table}" AS {base} '
                         f'UNION ALL SELECT {source_columns} FROM walsin_public_evidence."{table}" q '
                         f'WHERE NOT EXISTS (SELECT 1 FROM temp."{known}" k WHERE k.model=q.型号)')
            continue
        # Do not put every manufacturer's specification columns behind
        # CASE/COALESCE and two LEFT JOINs: that prevents the caller's spec
        # predicate from using the main table's compound index. The untouched
        # branch includes NULL brand/type rows and all upstream overlay rows.
        scoped="COALESCE(b._component_type='MLCC' AND (UPPER(b.品牌) LIKE '%WALSIN%' OR b.品牌 LIKE '%华新科%'),0)"
        unchanged=','.join(f'b."{key}"' for key in columns)
        conn.execute(f'CREATE TEMP VIEW "{table}" AS SELECT {unchanged} FROM ({base}) b WHERE NOT {scoped} '
                     f'UNION ALL SELECT {",".join(projections)} FROM ({base}) b '
                     f'LEFT JOIN temp."{addon}" a ON a.品牌=b.品牌 AND a.型号=b.型号 AND a._component_type=b._component_type '
                     f'LEFT JOIN walsin_public_evidence."{table}" q ON '
                     f'b._component_type=\'MLCC\' AND (UPPER(b.品牌) LIKE \'%WALSIN%\' OR b.品牌 LIKE \'%华新科%\') AND '
                     f'q.型号=CASE WHEN UPPER(SUBSTR(b.型号,-2)) IN (\'CT\',\'CG\') THEN UPPER(SUBSTR(b.型号,1,LENGTH(b.型号)-2)) ELSE UPPER(b.型号) END '
                     f'WHERE {scoped} '
                     f'UNION ALL SELECT {source_columns} FROM walsin_public_evidence."{table}" q '
                     f'WHERE NOT EXISTS (SELECT 1 FROM temp."{known}" k WHERE k.model=q.型号)')
