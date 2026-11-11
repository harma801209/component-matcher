"""Read-only naming audit of public prepared, exact-search and ready outputs.

Never opens member/cost/report stores or imports the application. Reports each
source separately; overlapping rows are not presented as unique model counts.
Dynamic/customer-supplied outputs are explicitly not certified by this audit.
"""
import argparse
from contextlib import closing
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.audit_model_naming_coverage import audit, audit_catalogue
import catalog_prebuilt


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def sqlite_audit(path, table, kind=''):
    if table not in ('components_search_core','catalog_browse_source'):raise ValueError('Unknown public table')
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as conn:
        conn.execute('PRAGMA query_only=ON')
        columns={row[1] for row in conn.execute('PRAGMA table_info('+table+')')}
        if not {'品牌','型号'}<=columns:raise ValueError('Missing public identity columns')
        names=['品牌','型号']+[name for name in ('系列','器件类型','_component_type') if name in columns]
        cursor=conn.execute('SELECT '+','.join('"'+name+'"' for name in names)+' FROM '+table)
        def records():
            while batch:=cursor.fetchmany(4096):
                for values in batch:
                    row=dict(zip(names,values))
                    row['器件类型']=row.get('器件类型') or row.get('_component_type') or kind
                    yield row
        result=audit(records())
        assert result['summary']['records']==conn.execute('SELECT count(*) FROM '+table).fetchone()[0]
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.suffix!='.json':parser.error('Output must be a separate JSON report')
    sources=catalog_prebuilt.source_members(args.root)
    decoder_sha=digest(ROOT/'model_naming_guide.py')
    for name,expected in sources.items():
        path=args.root/name
        if path.resolve()==args.output.resolve():raise ValueError('Cannot overwrite source')
        assert path.stat().st_size==expected['size'] and digest(path)==expected['sha256']
    manifest=json.loads((args.root/'catalog_ready/manifest.json').read_text(encoding='utf-8'))
    assert manifest['sources']==sources
    report=dict(scope='Enumerated public prepared/exact-search/ready outputs; source counts overlap.',
                units='Input records per source, NOT unique model or true family counts.',
                dynamic_and_customer_outputs_verified=False,all_system_coverage_verified=False,
                public_sources=sources,decoder_sha256=decoder_sha,reports={})
    report['reports']['prepared']=audit_catalogue(args.root/'cache/components_prepared_v5.parquet',4096)
    print('Audited prepared',report['reports']['prepared']['summary'],flush=True)
    report['reports']['exact_search']=sqlite_audit(args.root/'cache/components_search.sqlite','components_search_core')
    print('Audited exact_search',report['reports']['exact_search']['summary'],flush=True)
    with tempfile.TemporaryDirectory(prefix='public-naming-ready-audit-') as directory:
        for kind,entry in manifest['kinds'].items():
            compressed=args.root/'catalog_ready'/entry['file']
            assert digest(compressed)==entry['sha256']
            temporary=Path(directory)/'public.sqlite'
            with gzip.open(compressed,'rb') as source,temporary.open('wb') as target:shutil.copyfileobj(source,target)
            assert digest(temporary)==entry['raw_sha256']
            result=sqlite_audit(temporary,'catalog_browse_source',kind)
            # Manifest total is a UI/catalogue count and may exclude duplicate
            # identities; audit every physical row, retaining any discrepancy.
            result['manifest_total']=entry['total']
            result['manifest_count_matches_physical_rows']=result['summary']['records']==entry['total']
            report['reports']['ready:'+kind]=result
            print('Audited ready',kind,result['summary'],flush=True)
    # A catalogue decoder edit invalidates the runtime recipe, not the reviewed
    # public evidence. No manifest is rewritten just to make this audit pass.
    for name,expected in sources.items():assert digest(args.root/name)==expected['sha256']
    assert digest(ROOT/'model_naming_guide.py')==decoder_sha,'Decoder changed during audit; rerun frozen revision'
    report['enumerated_sources_complete']=all(r['summary']['full_coverage'] for r in report['reports'].values())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Source inventory complete; all-system verification remains false until dynamic outputs are audited.',flush=True)


if __name__=='__main__':main()
