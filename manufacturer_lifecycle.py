"""Exact-model, primary-source lifecycle evidence (never an availability guess).

This store contains public catalogue evidence only. It is independent of member,
customer and price stores. Official adapter results are reviewed/versioned before
publication; end-user searches never crawl manufacturers or write the library.
"""
import hashlib
import json
import re
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
        if url.scheme != 'https' or url.hostname != SAMSUNG_HOST or not re.fullmatch(r'CL[A-Z0-9]+[#A-Z0-9]',model): continue
        if url.path != '/cn/mlcc/'+model[:-1]+'.do' or record.get('parser') != 'samsung-mlcc-table-v1': continue
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
    if not evidence: return table
    if conn.execute("SELECT 1 FROM sqlite_temp_master WHERE name='catalog_lifecycle_source'").fetchone(): return 'catalog_lifecycle_source'
    # Narrow brand aliases to actual library labels, and leave all identities
    # on the existing source side of the LEFT JOIN.
    brands = [b for b, in conn.execute(f'SELECT DISTINCT 品牌 FROM "{table}" WHERE _component_type=?',(kind,))]
    known = [(b,r['model'],r['status'],r['source'],r['checked_at']) for b in brands for r in evidence if manufacturer(b)==r['manufacturer']]
    if not known: return table
    conn.execute('CREATE TEMP TABLE catalog_lifecycle_evidence (品牌 TEXT,型号 TEXT,生产状态 TEXT,_lifecycle_source TEXT,_lifecycle_checked TEXT,PRIMARY KEY(品牌,型号))')
    conn.executemany('INSERT OR IGNORE INTO catalog_lifecycle_evidence VALUES (?,?,?,?,?)',known)
    columns = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
    projection = ','.join('b."'+c+'"' for c in columns if c not in {'生产状态','_lifecycle_source','_lifecycle_checked'})
    conn.execute('CREATE TEMP VIEW catalog_lifecycle_source AS SELECT '+projection+',e.生产状态,e._lifecycle_source,e._lifecycle_checked FROM "'+table+'" b LEFT JOIN catalog_lifecycle_evidence e ON b.品牌 IS e.品牌 AND b.型号=e.型号 WHERE b._component_type='+"'"+kind.replace("'","''")+"'")
    return 'catalog_lifecycle_source'
