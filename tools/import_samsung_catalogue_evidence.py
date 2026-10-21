"""Import reviewed official search responses, intersecting exact library identities.

Input files are public OEM exports fetched from the observed UI POST endpoints.
This offline import never fetches URLs, changes an index, or touches runtime DBs.
"""
import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from manufacturer_lifecycle import manufacturer,samsung_catalogue_records


def verified_export(path,manifest,category,request):
    source=path.read_bytes()
    entry=manifest.get(path.name,{})
    if entry.get('url')!='https://product.samsungsem.com/'+category+'/bSearch.do' or entry.get('request')!=request:
        raise ValueError('Missing/mismatched public export receipt: '+path.name)
    if entry.get('source_sha256')!=hashlib.sha256(source).hexdigest():
        raise ValueError('Public response changed after collection: '+path.name)
    checked=entry['checked_at']
    if datetime.fromisoformat(checked).tzinfo is None:raise ValueError('Export receipt requires a timezone')
    return source.decode('utf-8'),checked


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--index',type=Path,default=ROOT/'cache/components_search.sqlite')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with sqlite3.connect(args.index.resolve().as_uri()+'?mode=ro',uri=True) as conn:
        library={m for b,m in conn.execute('SELECT DISTINCT 品牌,型号 FROM components_search_core WHERE 型号 IS NOT NULL') if manufacturer(b)=='samsung'}
    document=json.loads(args.output.read_text(encoding='utf-8')) if args.output.exists() else {'schema':1,'records':[]}
    records={(r['manufacturer'],r['model']):r for r in document['records']}
    imported=[]
    manifests={}
    for category in ('cr','pi'):
        audit=args.folder/('samsung-'+category+'-export-audit.json')
        if audit.exists():
            for entry in json.loads(audit.read_text(encoding='utf-8'))['requests']:
                if entry.get('outcome')=='verified-export':manifests[entry['file']]=entry
    for path in sorted(args.folder.glob('samsung-official-cr-*.json')):
        prefix=path.stem.removeprefix('samsung-official-cr-')
        source,checked=verified_export(path,manifests,'cr',{'partNumber':prefix})
        rows=samsung_catalogue_records(source,'cr',{'partNumber':prefix},checked)
        matched=[r for r in rows if r['model'] in library]
        for record in matched: records[(record['manufacturer'],record['model'])]=record
        imported.append({'prefix':prefix,'official_products':len(rows),'library_models':len(matched)})
    path=args.folder/'samsung-official-pi-catalogue.json'
    if path.exists():
        source,checked=verified_export(path,manifests,'pi',{'status':['Mass Production']})
        rows=samsung_catalogue_records(source,'pi',{'status':['Mass Production']},checked)
        matched=[r for r in rows if r['model'] in library]
        for record in matched: records[(record['manufacturer'],record['model'])]=record
        imported.append({'category':'pi','official_products':len(rows),'library_models':len(matched)})
    document['records']=sorted(records.values(),key=lambda r:(r['manufacturer'],r['model']))
    args.output.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'batches':imported,'verified_total':len(records)},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
