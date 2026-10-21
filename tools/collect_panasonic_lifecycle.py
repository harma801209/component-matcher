"""Bounded Panasonic exact-product collection and receipt-checked offline import.

Only explicit product-header/part-number NRFND badges are supported initially.
No badge, a linked NRND replacement list, a failed request or a 404 never assigns
a lifecycle. This tool reads the published index without modifying any database.
"""
import argparse
import hashlib
import json
import sqlite3
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import manufacturer_lifecycle as lifecycle
import panasonic_lifecycle as panasonic
from tools.collect_manufacturer_lifecycle import read_product


def import_receipts(folder,attempts,library):
    records={}
    for entry in attempts:
        model=entry.get('model')
        if model not in library or entry.get('http_status')!=200 or 'file' not in entry: continue
        official=panasonic.official_model(model)
        if entry['file']!=official+'.html': raise ValueError('Unexpected product response filename')
        raw=(folder/entry['file']).read_bytes()
        if len(raw)>2_000_000 or hashlib.sha256(raw).hexdigest()!=entry.get('source_sha256'):
            raise ValueError('Changed/oversized official response: '+model)
        record=panasonic.product_record(raw.decode('utf-8'),entry['url'],model,entry['checked_at'])
        if record: records[(record['manufacturer'],record['model'])]=record
    return list(records.values())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--index',type=Path,default=ROOT/'cache/components_search.sqlite')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--limit',type=int,default=30)
    parser.add_argument('--delay',type=float,default=1.5)
    parser.add_argument('--prefix',action='append',default=[])
    parser.add_argument('--import-only',action='store_true')
    parser.add_argument('--retry',action='store_true')
    args=parser.parse_args()
    if not 1<=args.limit<=300 or args.delay<1.5: parser.error('Use limit 1..300 and delay >=1.5 seconds')
    with sqlite3.connect(args.index.resolve().as_uri()+'?mode=ro',uri=True) as conn:
        library={m for b,m in conn.execute('SELECT DISTINCT 品牌,型号 FROM components_search_core WHERE 型号 IS NOT NULL') if lifecycle.manufacturer(b)=='panasonic'}
    args.folder.mkdir(parents=True,exist_ok=True)
    audit_path=args.folder/'audit.json'
    audit=json.loads(audit_path.read_text(encoding='utf-8')) if audit_path.is_file() else {'attempts':[]}
    if not args.import_only:
        import requests
        agent='ComponentLibraryEvidence/1.0 (public specification research)'
        seen={e['model'] for e in audit['attempts']}
        pending=[]
        for model in sorted(library):
            try: official=panasonic.official_model(model)
            except ValueError: continue
            if args.prefix and not any(official.startswith(prefix) for prefix in args.prefix): continue
            if not args.retry and model in seen: continue
            pending.append((model,official))
        with requests.Session() as session:
            robots=session.get(panasonic.ORIGIN+'/robots.txt',timeout=20,allow_redirects=False)
            rules=RobotFileParser()
            if robots.status_code==200: rules.parse(robots.text.splitlines())
            elif robots.status_code in {404,410}: rules.parse([])
            else: raise ValueError('Official robots unavailable; no product requests sent')
            delay=max(args.delay,rules.crawl_delay(agent) or rules.crawl_delay('*') or 0)
            for model,official in pending[:args.limit]:
                url=panasonic.ORIGIN+panasonic.PATH+official
                if not rules.can_fetch(agent,url): raise ValueError('Official robots disallows product page')
                time.sleep(delay)
                entry=dict(model=model,official_model=official,url=url)
                try:
                    source=read_product(session,url,agent)
                    filename=official+'.html'
                    (args.folder/filename).write_bytes(source)
                    entry.update(http_status=200,file=filename,source_sha256=hashlib.sha256(source).hexdigest())
                except HTTPError as error:
                    entry.update(http_status=error.code,error='HTTP '+str(error.code)); error.close()
                except Exception as error: entry['error']=str(error)
                entry['checked_at']=datetime.now(timezone.utc).isoformat()
                audit['attempts'].append(entry)
                audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                print(model,entry.get('http_status','failed'),flush=True)
                if entry.get('http_status') in {401,403,429}: break
    imported=import_receipts(args.folder,audit['attempts'],library)
    document=json.loads(args.output.read_text(encoding='utf-8')) if args.output.is_file() else {'schema':1,'records':[]}
    merged={(r['manufacturer'],r['model']):r for r in document['records']}
    for record in imported: merged[(record['manufacturer'],record['model'])]=record
    document['records']=sorted(merged.values(),key=lambda r:(r['manufacturer'],r['model']))
    args.output.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(imported_exact_models=len(imported),reviewed_total=len(merged),attempts=len(audit['attempts'])),ensure_ascii=False))


if __name__=='__main__': main()
