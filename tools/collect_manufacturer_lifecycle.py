"""Bounded/resumable official Samsung MLCC audit, public library read-only.

No guessed status, no credentials, no anti-bot bypass. Other brands require
their own validated exact-model adapters; they remain pending, not 'active'.
"""
import argparse
import io
import json
import math
import sqlite3
import sys
import time
import urllib.request
import urllib.robotparser
from urllib.error import HTTPError
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from manufacturer_lifecycle import samsung_records,manufacturer


def read_product(session,url,agent):
    """Reuse a normal verified HTTPS connection; redirects remain forbidden."""
    with session.get(url,headers={'User-Agent':agent},timeout=20,allow_redirects=False,stream=True) as response:
        if response.status_code!=200:
            raise HTTPError(url,response.status_code,'Official product request failed',None,io.BytesIO())
        source=bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            source.extend(chunk)
            if len(source)>2_000_000:raise ValueError('Unexpected document size')
        return bytes(source)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--index',type=Path,default=ROOT/'cache/components_search.sqlite')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--limit',type=int,default=30)
    parser.add_argument('--delay',type=float,default=1.0)
    parser.add_argument('--retry',action='store_true',help='Recheck previously attempted pages')
    args=parser.parse_args()
    if not 1<=args.limit<=1000 or not math.isfinite(args.delay) or args.delay<1: parser.error('Use batches of 1..1000 pages, at least one second apart')
    existing=json.loads(args.output.read_text(encoding='utf-8')) if args.output.exists() else {'schema':1,'records':[]}
    verified={(r['manufacturer'],r['model']):r for r in existing['records']}
    conn=sqlite3.connect(args.index.resolve().as_uri()+'?mode=ro',uri=True)
    models=[(b,m) for b,m in conn.execute("SELECT DISTINCT 品牌,型号 FROM components_search_core WHERE _component_type='MLCC' AND 型号 LIKE 'CL%' AND 型号 IS NOT NULL ORDER BY 型号") if manufacturer(b)=='samsung']
    conn.close()
    audit_path=args.output.with_suffix('.audit.json')
    results=json.loads(audit_path.read_text(encoding='utf-8')).get('pages',[]) if audit_path.exists() else []
    attempted={r['url'] for r in results}
    bases=sorted({m[:-1] for _,m in models if ('samsung',m) not in verified
                  and (args.retry or 'https://product.samsungsem.com/cn/mlcc/'+m[:-1]+'.do' not in attempted)})
    agent='FruitionCatalogueAudit/1.0'
    robots=urllib.robotparser.RobotFileParser()
    try:
        with urllib.request.urlopen(urllib.request.Request('https://product.samsungsem.com/robots.txt',headers={'User-Agent':agent}),timeout=20) as r: robots.parse(r.read().decode('utf-8').splitlines())
    except HTTPError as error:
        if error.code!=404: raise
        robots.parse([])
    delay=max(args.delay,robots.crawl_delay(agent) or 0)
    rate=robots.request_rate(agent)
    if rate and rate.requests: delay=max(delay,rate.seconds/rate.requests)
    import requests
    session=requests.Session()
    for position,base in enumerate(bases[:args.limit],start=1):
        url='https://product.samsungsem.com/cn/mlcc/'+base+'.do'
        if not robots.can_fetch(agent,url): raise RuntimeError('Official robots policy does not allow this path')
        started=time.monotonic()
        checked=datetime.now(timezone.utc).isoformat()
        stop=False
        try:
            source=read_product(session,url,agent)
            rows=samsung_records(source.decode('utf-8'),url,base,checked)
            library={m for _,m in models}
            rows=[r for r in rows if r['model'] in library]
            for record in rows: verified[(record['manufacturer'],record['model'])]=record
            results.append({'url':url,'checked_at':checked,'verified_models':len(rows),'outcome':'verified' if rows else 'unconfirmed'})
        except Exception as error:
            results.append({'url':url,'checked_at':checked,'verified_models':0,'outcome':'error','error':type(error).__name__})
            if isinstance(error,HTTPError):
                results[-1]['http_status']=error.code
                stop=error.code in {401,403,429}
                error.close()
        existing.update(records=sorted(verified.values(),key=lambda r:(r['manufacturer'],r['model'])))
        args.output.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        audit_path.write_text(json.dumps({'adapter':'samsung-mlcc-table-v1','library_models':len(models),'remaining_pages':len(bases)-position,'pages':results},ensure_ascii=False,indent=2),encoding='utf-8')
        print(base,results[-1]['outcome'],results[-1]['verified_models'],flush=True)
        if stop:break
        time.sleep(max(0,delay-(time.monotonic()-started)))
    session.close()
    print('Verified exact Samsung MLCC library models:',sum(r.get('parser')=='samsung-mlcc-table-v1' for r in verified.values()),'of',len(models),'All stored identities:',len(verified))

if __name__=='__main__':main()
