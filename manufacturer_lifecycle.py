"""Exact-model, primary-source lifecycle evidence (never an availability guess).

This store contains public catalogue evidence only. It is independent of member,
customer and price stores. Official adapter results are reviewed/versioned before
publication; end-user searches never crawl manufacturers or write the library.
"""
import hashlib
import json
import math
import re
from fractions import Fraction
from datetime import datetime
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

EVIDENCE = Path(__file__).with_name('manufacturer_lifecycle_evidence.json')
SAMSUNG_HOST = 'product.samsungsem.com'
STATUSES = {'Mass Production':'量产', 'NRND':'NRND（不推荐新设计）',
            'Pre Mass Production':'量产前', 'Discontinued':'已停产',
            'Planned Discontinuation':'计划停产'}
CATALOGUE_PARSER = 'samsung-catalogue-exact-v1'
SPEC_FIELDS = {'_res_ohm':'REAL', '_power_watt':'REAL', '_size':'TEXT', '_tol':'TEXT',
               '_catalog_inductance_uh':'REAL','_body_size':'TEXT'}
RESISTOR_SPECS = ('_res_ohm','_power_watt','_size','_tol')
INDUCTOR_SPECS = ('_catalog_inductance_uh','_body_size','_size','_tol')


def catalogue_parameters(row, category):
    """Explicit exact-product values only; never size-to-power or 0 V defaults."""
    result = {}
    if category == 'cr':
        value = re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*([kKMm]?)\s*[ΩΩ]', str(row.get('rValue','')))
        if value:
            result['_res_ohm'] = float(value[1]) * {'':1,'k':1e3,'K':1e3,'M':1e6,'m':1e-3}[value[2]]
        power = str(row.get('ratedPower','')).strip()
        fraction = re.fullmatch(r'[0-9]+(?:\.[0-9]+)?\s*W\s*\(([0-9]+/[1-9][0-9]*)\s*W\)',power)
        scalar = re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*W',power)
        if fraction: result['_power_watt'] = float(Fraction(fraction[1]))
        elif scalar and float(scalar[1])>0: result['_power_watt'] = float(scalar[1])
    elif category == 'pi':
        inductance = row.get('inductance')
        if isinstance(inductance,(float,int)) and not isinstance(inductance,bool) and math.isfinite(inductance) and inductance>0:
            result['_catalog_inductance_uh'] = inductance
        axes=[re.fullmatch(r'(\d+(?:\.\d+)?(?:±\d+(?:\.\d+)?)?)mm',str(row.get(key,''))) for key in ('lSize','wSize','tSizeMax')]
        if all(axes):result['_body_size'] = ' × '.join(axis[1]+(' max' if i==2 else '') for i,axis in enumerate(axes))+' mm'
    size = re.fullmatch(r'(\d{4,6})/(\d{4})',str(row.get('sizeCode','')))
    if size: result['_size'] = size[1]
    tolerance = re.fullmatch(r'±([0-9]+(?:\.[0-9]+)?)%',str(row.get('tolerance','')))
    if tolerance and 0 < float(tolerance[1]) <= 100: result['_tol'] = str(float(tolerance[1])).removesuffix('.0')
    return result


def samsung_catalogue_records(source, category, request, checked_at):
    """The site's observed public search response, not guessed family statuses.

    Chip-resistor partNumber is the exact ordering code. Power-inductor list
    entries use the explicit '#' identity displayed by the official grid; no
    packaging variants are generated. Intersect with the real library on import.
    """
    if category not in {'cr','pi'}: raise ValueError('Unsupported official catalogue')
    if category == 'cr' and (set(request) != {'partNumber'} or not re.fullmatch('[A-Z0-9]{3,12}',str(request['partNumber']))):
        raise ValueError('Expected bounded exact-prefix query')
    if category == 'pi' and request != {'status':['Mass Production']}: raise ValueError('Unexpected official query')
    datetime.fromisoformat(checked_at)
    rows = json.loads(source).get('searchListJson')
    if not isinstance(rows,list): raise ValueError('Not an official search result')
    digest = hashlib.sha256(source.encode('utf-8')).hexdigest()
    result = {}
    for row in rows:
        if not isinstance(row,dict): raise ValueError('Invalid product row')
        model, raw = row.get('partNumber'), row.get('status')
        if model is None: continue  # the site's explicit no-result sentinel
        if not re.fullmatch('[A-Z0-9]{5,40}',str(model)) or raw not in STATUSES: continue
        if category == 'cr' and not model.startswith(request['partNumber']): raise ValueError('Query scope mismatch')
        identity = model + ('#' if category == 'pi' else '')
        record = dict(manufacturer='samsung',model=identity,status=STATUSES[raw],raw_status=raw,
                      source='https://'+SAMSUNG_HOST+'/cn/'+category+'/basic-search.do',
                      request_url='https://'+SAMSUNG_HOST+'/'+category+'/bSearch.do',request=request,
                      checked_at=checked_at,source_sha256=digest,parser=CATALOGUE_PARSER,
                      parameters=catalogue_parameters(row,category))
        if identity in result and result[identity] != record: raise ValueError('Conflicting exact-model records')
        result[identity] = record
    return list(result.values())


def manufacturer(brand):
    value = str(brand or '').strip().upper()
    return 'samsung' if value in {'三星SAMSUNG','SAMSUNG','SAMSUNG ELECTRO-MECHANICS','三星电机'} else value


class SamsungPage(HTMLParser):
    """Read the product heading, its packaging list and its status table row.

    Deliberately ignore generic badges, menus, comments and lifecycle legends.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.heading, self.parts, self.rows = '', [], []
        self.in_heading = self.in_parts = self.in_li = False
        self.in_cell = False
        self.cell, self.row = '', []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h2' and 'subject' in attrs.get('class','').split() and not self.heading: self.in_heading = True
        if tag == 'ul' and 'partlist' in attrs.get('class','').split(): self.in_parts = True
        if tag == 'li' and self.in_parts: self.in_li = True; self.part = ''
        if tag == 'tr': self.row = []
        if tag in {'td','th'}: self.in_cell = True; self.cell = ''
    def handle_data(self, value):
        if self.in_heading: self.heading += value
        if self.in_li: self.part += value
        if self.in_cell: self.cell += value
    def handle_endtag(self, tag):
        if tag == 'h2': self.in_heading = False
        if tag == 'li' and self.in_li: self.parts.append(self.part.strip()); self.in_li = False
        if tag == 'ul': self.in_parts = False
        if tag in {'td','th'} and self.in_cell: self.row.append(' '.join(self.cell.split())); self.in_cell = False
        if tag == 'tr' and self.row: self.rows.append(self.row); self.row = []


def samsung_records(source, url, requested_base, checked_at):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname != SAMSUNG_HOST or parsed.path != '/cn/mlcc/'+requested_base+'.do':
        raise ValueError('Not the requested official Samsung product page')
    page = SamsungPage(); page.feed(source)
    if page.heading.strip() != requested_base+'#': return []
    status = [r[1] for r in page.rows if len(r)==2 and r[0] in {'生产状况','Production Status'}]
    if len(set(status)) != 1 or status[0] not in STATUSES: return []
    datetime.fromisoformat(checked_at)
    digest = hashlib.sha256(source.encode('utf-8')).hexdigest()
    parts = {p for p in page.parts if re.fullmatch(re.escape(requested_base)+r'[A-Z0-9]',p)}
    # A manufacturer's explicit '#' group is a valid library identity in its
    # own right, not permission to generate all possible packaging suffixes.
    parts.add(requested_base+'#')
    return [dict(manufacturer='samsung',model=model,status=STATUSES[status[0]],raw_status=status[0],
                 source=url,checked_at=checked_at,source_sha256=digest,parser='samsung-mlcc-table-v1') for model in sorted(parts)]


@lru_cache(maxsize=2)
def _read(path, modified):
    del modified
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    result = {}
    for record in raw.get('records',[]):
        if record.get('manufacturer') != 'samsung' or record.get('status') != STATUSES.get(record.get('raw_status')): continue
        url = urlsplit(record.get('source',''))
        model = record.get('model','')
        if url.scheme != 'https' or url.hostname != SAMSUNG_HOST or url.query or url.fragment or url.username: continue
        if record.get('parser') == 'samsung-mlcc-table-v1':
            if not re.fullmatch(r'CL[A-Z0-9]+[#A-Z0-9]',model) or url.path != '/cn/mlcc/'+model[:-1]+'.do': continue
        elif record.get('parser') == CATALOGUE_PARSER:
            if url.path not in {'/cn/cr/basic-search.do','/cn/pi/basic-search.do'}: continue
            category = url.path.split('/')[2]
            if record.get('request_url') != 'https://'+SAMSUNG_HOST+'/'+category+'/bSearch.do': continue
            request = record.get('request',{})
            if category == 'cr':
                if not isinstance(request,dict) or set(request) != {'partNumber'}: continue
                prefix = request['partNumber']
                if not isinstance(prefix,str) or not re.fullmatch('[A-Z0-9]{3,12}',prefix) or not re.fullmatch('[A-Z0-9]{5,40}',model) or not model.startswith(prefix): continue
            elif request != {'status':['Mass Production']} or not re.fullmatch(r'CIG[A-Z0-9]+#',model): continue
            parameters = record.get('parameters',{})
            if not isinstance(parameters,dict) or set(parameters)-set(SPEC_FIELDS): continue
            if any(not isinstance(v,(float,int)) or isinstance(v,bool) or not math.isfinite(v) or v<0 for k,v in parameters.items() if SPEC_FIELDS[k]=='REAL'): continue
            if any(not isinstance(v,str) or len(v)>120 for k,v in parameters.items() if SPEC_FIELDS[k]=='TEXT'): continue
            if '_size' in parameters and not re.fullmatch(r'\d{4,6}',parameters['_size']): continue
            if '_tol' in parameters and not re.fullmatch(r'\d+(?:\.\d+)?',parameters['_tol']): continue
        else: continue
        try: datetime.fromisoformat(record['checked_at'])
        except (ValueError,KeyError,TypeError): continue
        if not re.fullmatch('[0-9a-f]{64}',record.get('source_sha256','')): continue
        key = ('samsung',model)
        if key not in result or result[key]['checked_at'] < record['checked_at']: result[key] = record
    return tuple(result.values())


def records():
    return _read(str(EVIDENCE),EVIDENCE.stat().st_mtime_ns) if EVIDENCE.is_file() else ()


def install(conn, table, kind):
    evidence = records()
    if conn.execute("SELECT 1 FROM sqlite_temp_master WHERE name='catalog_lifecycle_source'").fetchone(): return 'catalog_lifecycle_source'
    # Narrow brand aliases to actual library labels, and leave all identities
    # on the existing source side of the LEFT JOIN.
    brands = [b for b, in conn.execute(f'SELECT DISTINCT 品牌 FROM "{table}" WHERE _component_type=?',(kind,))]
    specifications = RESISTOR_SPECS if kind in {'贴片电阻','厚膜电阻','薄膜电阻','合金电阻'} else INDUCTOR_SPECS if kind=='功率电感' else ()
    known = [(b,r['model'],r['status'],r['source'],r['checked_at'],*(r.get('parameters',{}).get(k) for k in specifications)) for b in brands for r in evidence if manufacturer(b)==r['manufacturer']]
    # Even a wholly unaudited brand/kind must not display legacy default
    # 'Active' as though an official exact-model check had taken place.
    declarations = ''.join(',"'+k+'" '+SPEC_FIELDS[k] for k in specifications)
    conn.execute('CREATE TEMP TABLE catalog_lifecycle_evidence (品牌 TEXT,型号 TEXT,生产状态 TEXT,_lifecycle_source TEXT,_lifecycle_checked TEXT'+declarations+',PRIMARY KEY(品牌,型号))')
    conn.executemany('INSERT OR IGNORE INTO catalog_lifecycle_evidence VALUES ('+','.join('?' for _ in range(5+len(specifications)))+')',known)
    columns = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
    expressions = []
    for column in dict.fromkeys([*columns,*specifications]):
        if column in {'生产状态','_lifecycle_source','_lifecycle_checked'}: continue
        original = 'b."'+column+'"' if column in columns else 'NULL'
        if column in specifications:
            original = 'CASE WHEN '+original+' IS NULL OR UPPER(TRIM(CAST('+original+' AS TEXT))) IN (\'\',\'-\',\'--\',\'/\',\'N/A\',\'NA\',\'NULL\',\'NONE\',\'NAN\') THEN e."'+column+'" ELSE '+original+' END'
        expressions.append(original+' AS "'+column+'"')
    projection = ','.join(expressions)
    conn.execute('CREATE TEMP VIEW catalog_lifecycle_source AS SELECT '+projection+',e.生产状态,e._lifecycle_source,e._lifecycle_checked FROM "'+table+'" b LEFT JOIN catalog_lifecycle_evidence e ON b.品牌 IS e.品牌 AND b.型号=e.型号 WHERE b._component_type='+"'"+kind.replace("'","''")+"'")
    return 'catalog_lifecycle_source'
