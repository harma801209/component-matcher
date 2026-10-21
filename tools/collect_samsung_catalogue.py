"""Bounded official Samsung catalogue export; no private store access or guesses.

Endpoints/payloads are those observed in the public basic-search page. Exact
library intersection and reviewed import are a separate offline operation.
"""
import argparse
import hashlib
import json
import math
import sqlite3
import sys
import time
import urllib.request
import urllib.robotparser
from datetime import datetime,timezone
from pathlib import Path
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from manufacturer_lifecycle import manufacturer,samsung_catalogue_records


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',type=Path,default=ROOT/'cache/components_search.sqlite')
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--category',choices=('cr','pi'),default='cr')
    parser.add_argument('--limit',type=int,default=30)
    parser.add_argument('--delay',type=float,default=1)
    parser.add_argument('--retry',action='store_true')
    args=parser.parse_args()
    if not 1<=args.limit<=100 or not math.isfinite(args.delay) or args.delay<1:parser.error('Use batches 1..100 and a delay of at least one second')
    if args.category=='cr':
        with sqlite3.connect(args.index.resolve().as_uri()+'?mode=ro',uri=True) as conn:
            models=[m for b,m in conn.execute("SELECT DISTINCT 品牌,型号 FROM components_search_core WHERE _component_type IN ('贴片电阻','厚膜电阻','薄膜电阻','合金电阻') AND 型号 IS NOT NULL") if manufacturer(b)=='samsung']
        requests=[({'partNumber':prefix},'samsung-official-cr-'+prefix+'.json') for prefix in sorted({m[:6] for m in models})]
    else:requests=[({'status':['Mass Production']},'samsung-official-pi-catalogue.json')]
    args.output_dir.mkdir(parents=True,exist_ok=True)
    agent='FruitionCatalogueAudit/1.0'
    root='https://product.samsungsem.com'
    robots=urllib.robotparser.RobotFileParser()
    try:
        with urllib.request.urlopen(urllib.request.Request(root+'/robots.txt',headers={'User-Agent':agent}),timeout=20) as response:robots.parse(response.read().decode().splitlines())
    except HTTPError as error:
        if error.code!=404:raise
        robots.parse([])
    url=root+'/'+args.category+'/bSearch.do'
    if not robots.can_fetch(agent,url):raise RuntimeError('Official robots policy does not allow the public search path')
    rate=robots.request_rate(agent)
    delay=max(args.delay,robots.crawl_delay(agent) or 0,rate.seconds/rate.requests if rate and rate.requests else 0)
    audit_path=args.output_dir/('samsung-'+args.category+'-export-audit.json')
    audit=json.loads(audit_path.read_text(encoding='utf-8')) if audit_path.exists() else {'requests':[]}
    done={r['file'] for r in audit['requests'] if r.get('outcome')=='verified-export'}
    queue=[(query,name) for query,name in requests if args.retry or name not in done]
    for query,name in queue[:args.limit]:
        started=time.monotonic()
        checked=datetime.now(timezone.utc).isoformat()
        entry=dict(file=name,url=url,request=query,checked_at=checked)
        stop=False
        try:
            request=urllib.request.Request(url,data=json.dumps(query).encode(),headers={'User-Agent':agent,'Content-Type':'application/json','Referer':root+'/cn/'+args.category+'/basic-search.do'})
            with urllib.request.urlopen(request,timeout=90) as response:
                source=response.read(20_000_001)
                if response.url!=url or len(source)>20_000_000:raise ValueError('Unexpected redirect/document size')
            rows=samsung_catalogue_records(source.decode('utf-8'),args.category,query,checked)
            (args.output_dir/name).write_bytes(source)
            entry.update(outcome='verified-export',official_products=len(rows),source_sha256=hashlib.sha256(source).hexdigest())
        except Exception as error:
            entry.update(outcome='error',error=type(error).__name__)
            if isinstance(error,HTTPError):
                entry['http_status']=error.code
                stop=error.code in {401,403,429}
        audit['requests'].append(entry)
        audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(name,entry['outcome'],entry.get('official_products',0),flush=True)
        if stop:break
        time.sleep(max(0,delay-(time.monotonic()-started)))


if __name__=='__main__':main()
