"""Native Chrome verifies source specification rows, never clicks report or price actions."""
import argparse
import json
import platform
import time
from pathlib import Path

platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
args = parser.parse_args()
OUT = Path(__file__).resolve().parents[2]/'repair-shop-qa'
OUT.mkdir(exist_ok=True)
tag = 'fpm-public' if args.public else 'fpm-local'
models = ['FPM253WFR300TM','FPM253WFR220TM','FPM253WFR330TM','FPM253WFR060TM']
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome',headless=True)
    page = browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/' if args.public else 'http://127.0.0.1:8559/',wait_until='domcontentloaded',timeout=120000)
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            app=next((f for f in page.frames if f.get_by_role('button',name='开始匹配',exact=True).count()),None)
            if app:break
            page.wait_for_timeout(400)
        else:raise AssertionError('Search UI did not load')
        app.locator('textarea').first.fill('\n'.join(models))
        app.get_by_role('button',name='开始匹配',exact=True).click()
        found={}
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            for frame in page.frames:
                for table in frame.locator('.result-table').all():
                    headers=table.locator('thead th').all_inner_texts()
                    for row in table.locator('tbody tr').all():
                        cells=row.locator('td').all_inner_texts()
                        model=next((m for m in models if m in cells),None)
                        if model:found[model]={'headers':headers,'cells':cells,'row':row}
            if len(found)==len(models):break
            page.wait_for_timeout(500)
        assert len(found)==len(models),{'found':list(found),'page':app.locator('body').inner_text()[:2000]}
        report=[]
        for model,record in found.items():
            cells=record['cells'];text=' '.join(cells)
            for expected in ['6432','2512','3W','±1%']:
                assert expected in text.replace(' ',''),(model,expected,cells)
            assert not any(h.startswith('_') for h in record['headers']),record['headers']
            record['row'].scroll_into_view_if_needed()
            report.append({'model':model,'package':'2512','metric_package':'6432','power':'3W','tolerance':'±1%'})
        found[models[0]]['row'].scroll_into_view_if_needed()
        page.screenshot(path=str(OUT/(tag+'-desktop.png')))
        page.set_viewport_size({'width':393,'height':960})
        found[models[0]]['row'].scroll_into_view_if_needed()
        page.screenshot(path=str(OUT/(tag+'-phone.png')))
        assert not errors,errors
        result={'status':'passed','public':args.public,'actual_result_rows':report,'errors':errors}
        (OUT/(tag+'-report.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/(tag+'-failure.png')))
        raise
    finally:
        browser.close()
