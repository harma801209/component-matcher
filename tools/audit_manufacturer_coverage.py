"""Read-only all-brand lifecycle coverage, including every still-pending label."""
import argparse
import json
import sqlite3
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import manufacturer_lifecycle as lifecycle


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',type=Path,default=ROOT/'cache/components_search.sqlite')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    evidence=lifecycle.records()
    with sqlite3.connect(args.index.resolve().as_uri()+'?mode=ro',uri=True) as conn:
        brands=list(conn.execute("SELECT 品牌,COUNT(DISTINCT 型号) FROM components_search_core WHERE COALESCE(型号,'')<>'' GROUP BY 品牌 ORDER BY COUNT(DISTINCT 型号) DESC,品牌"))
        conn.execute('CREATE TEMP TABLE checked(品牌 TEXT,型号 TEXT,状态 TEXT,PRIMARY KEY(品牌,型号))')
        conn.executemany('INSERT OR IGNORE INTO checked VALUES (?,?,?)',[(b,r['model'],r['status']) for b,_ in brands for r in evidence if lifecycle.manufacturer(b)==r['manufacturer']])
        verified={(b,s):n for b,s,n in conn.execute('SELECT b.品牌,e.状态,COUNT(DISTINCT b.型号) FROM components_search_core b JOIN checked e ON b.品牌 IS e.品牌 AND b.型号=e.型号 GROUP BY b.品牌,e.状态')}
        result=[]
        for brand,total in brands:
            counts={status:n for (b,status),n in verified.items() if b==brand}
            checked=sum(counts.values())
            result.append(dict(brand=brand,library_models=total,verified_models=checked,pending_models=total-checked,statuses=counts))
    report=dict(checked_at=datetime.now(timezone.utc).isoformat(),identity='distinct raw brand label + existing model; alias labels not silently merged',
                library_models=sum(r['library_models'] for r in result),raw_brand_labels=len(result),
                verified_models=sum(r['verified_models'] for r in result),brands=result)
    report['pending_models']=report['library_models']-report['verified_models']
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='brands'},ensure_ascii=False))


if __name__=='__main__':main()
