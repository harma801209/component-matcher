"""Audit a public catalogue without importing the app, logging in or changing data.

Usage: python tools/audit_model_naming_coverage.py --catalogue public.parquet
       --output coverage.json [--require-complete]
The optional strict mode exits 2 until every input record is fully explained.
Counts are input records, not inventory, unique manufacturers or true series.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import model_naming_guide as guide


def audit(records):
    groups={}
    for record in records:
        brand,series,kind=(guide.text(record.get(k)) for k in ('品牌','系列','器件类型'))
        key=(brand,series,kind)
        row=groups.setdefault(key,dict(brand=brand,series=series,kind=kind,records=0,
            complete=0,partial=0,unexplained=0,unexplained_examples=[],partial_examples=[]))
        decoded=guide.explain(record)
        row['records']+=1
        state='complete' if decoded['complete'] else 'partial' if decoded['segments'] else 'unexplained'
        row[state]+=1
        if state!='complete' and len(row[state+'_examples'])<3:
            row[state+'_examples'].append(decoded['model'])
    ordered=sorted(groups.values(),key=lambda r:(r['unexplained']+r['partial'],r['records']),reverse=True)
    summary={key:sum(row[key] for row in ordered) for key in ('records','complete','partial','unexplained')}
    summary.update(full_coverage=summary['complete']==summary['records'] and summary['records']>0,
        raw_brand_labels=len({key[0] for key in groups}),raw_group_labels=len(groups),
        unit='catalogue_records',scope='Only the supplied public catalogue snapshot; not the whole live matching output.',
        grouping_note='Raw labels may contain aliases or dirty series identifiers; these are not counts of distinct manufacturers or true families.')
    return dict(summary=summary,groups=ordered)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--require-complete',action='store_true')
    args=parser.parse_args()
    if args.catalogue.resolve()==args.output.resolve(): parser.error('Output cannot overwrite the input catalogue')
    if args.catalogue.suffix.lower()!='.parquet' or args.output.suffix.lower()!='.json':
        parser.error('Expected a public .parquet input and a separate .json report')
    import pandas as pd
    frame=pd.read_parquet(args.catalogue,columns=['品牌','型号','系列','器件类型']).fillna('')
    result=audit(dict(zip(frame.columns,values)) for values in frame.itertuples(index=False,name=None))
    with args.catalogue.open('rb') as stream:
        result['source_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
    result['source']=str(args.catalogue.resolve())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result['summary'],ensure_ascii=False))
    return 2 if args.require_complete and not result['summary']['full_coverage'] else 0


if __name__=='__main__':
    raise SystemExit(main())
