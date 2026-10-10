"""Read-only guest acceptance of source conditions on the formal UI."""
import platform
platform._wmi = None
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[2] / 'jianghai-20261010' / 'public-qa'
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(viewport={'width':1440,'height':1000})
    page = context.new_page()
    errors=[]
    page.on('pageerror', lambda e: errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/',wait_until='domcontentloaded',timeout=90000)
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            app=next((f for f in page.frames if 'fruition-componentmatche.streamlit.app' in f.url),None)
            if app:break
            page.wait_for_timeout(300)
        assert app, 'Formal iframe missing'
        app.get_by_role('button',name='开始匹配',exact=True).wait_for(timeout=90000)
        app.get_by_text('指定品牌',exact=True).first.click()
        picker=app.get_by_role('combobox',name='选择匹配品牌')
        picker.click()
        app.get_by_role('option').filter(has_text='江海').first.click()
        app.locator('textarea').first.fill('ECS1ABZ183M250030\nECR0JBK330M\nECS2HBZ101M')
        app.get_by_role('button',name='开始匹配',exact=True).click()
        deadline=time.monotonic()+150
        observed={}
        while time.monotonic()<deadline:
            observed={}
            for f in page.frames:
                for table in f.locator('.result-table').all():
                    headers=table.locator('thead th').all_inner_texts()
                    for row in table.locator('tbody tr').all():
                        values=row.locator('td').all_inner_texts()
                        fields=dict(zip(headers,values))
                        model=fields.get('型号','').replace(' ','')
                        if model in ('ECS1ABZ183M250030','ECR0JBK330M','ECS2HBZ101M'):
                            observed[model]=fields
            if len(observed)==3 and app.locator('.search-progress-summary-status').filter(has_text='已完成').count():break
            page.wait_for_timeout(700)
        assert len(observed)==3, {'found':list(observed), 'body':app.locator('body').inner_text()[-2000:]}
        low=observed['ECS1ABZ183M250030']
        assert low.get('耐压（V）')=='10V',low
        assert '2000' in low.get('寿命(h)',low.get('寿命（h）','')),low
        assert low.get('ESR')=='30mΩ',low
        assert '120Hz' in low.get('ESR测试条件',''),low
        assert '85' in low.get('纹波电流测试条件',''),low
        assert '6.3' in observed['ECR0JBK330M'].get('耐压（V）',''),observed
        assert '-40' in observed['ECR0JBK330M'].get('工作温度',''),observed
        assert '500' in observed['ECS2HBZ101M'].get('耐压（V）',''),observed
        assert '-25' in observed['ECS2HBZ101M'].get('工作温度',''),observed
        assert not errors,errors
        page.screenshot(path=str(OUT/'formal-jianghai-parameters.png'),full_page=True)
        print(json.dumps({'status':'passed','models':observed,'browser_errors':errors},ensure_ascii=False))
    finally:
        context.close()
        browser.close()
