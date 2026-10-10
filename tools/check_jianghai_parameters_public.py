"""Acceptance of source conditions; credentials supplied only by the runner."""
import platform
platform._wmi = None
import json
import os
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
        account=os.environ.get('COMPONENT_QA_ACCOUNT','')
        password=os.environ.get('COMPONENT_QA_PASSWORD','')
        if not account or not password:
            raise RuntimeError('Provide approved QA credentials through COMPONENT_QA_ACCOUNT and COMPONENT_QA_PASSWORD')
        app.locator('.wb-login-button').click()
        app.get_by_role('button',name='登录',exact=True).wait_for(timeout=90000)
        app.get_by_role('textbox',name='账号',exact=True).first.fill(account)
        app.get_by_role('textbox',name='密码',exact=True).first.fill(password)
        app.get_by_role('button',name='登录',exact=True).click()
        app.locator('.wb-user-link').wait_for(timeout=90000)
        app.locator('.wb-nav').get_by_role('link',name='元器件搜索',exact=True).click()
        app.get_by_role('button',name='开始匹配',exact=True).wait_for(timeout=90000)
        app.get_by_text('指定品牌',exact=True).first.click()
        picker=app.get_by_role('combobox',name='选择匹配品牌')
        picker.click()
        # The long brand menu is virtualized; filter rather than waiting for an
        # off-screen option that has not been mounted in the browser yet.
        picker.fill('江海')
        app.get_by_role('option').filter(has_text='江海').first.click()
        picker.press('Escape')
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
        def field(row,*names):
            return next((row[name] for name in names if name in row),'')
        low=observed['ECS1ABZ183M250030']
        assert field(low,'耐压（V）','额定电压（V）')=='10V',low
        assert '2000' in low.get('寿命(h)',low.get('寿命（h）','')),low
        assert low.get('ESR')=='30mΩ',low
        assert '120Hz' in field(low,'ESR测试条件','ESR条件'),low
        assert '85' in field(low,'纹波电流测试条件','纹波电流条件'),low
        assert '6.3' in field(observed['ECR0JBK330M'],'耐压（V）','额定电压（V）'),observed
        assert '-40' in observed['ECR0JBK330M'].get('工作温度',''),observed
        assert observed['ECR0JBK330M'].get('纹波电流')=='105mA',observed
        assert '500' in field(observed['ECS2HBZ101M'],'耐压（V）','额定电压（V）'),observed
        assert '-25' in observed['ECS2HBZ101M'].get('工作温度',''),observed
        assert all(not str(key).startswith('_') for row in observed.values() for key in row), 'Internal index fields leaked into the UI'
        assert not errors,errors
        page.screenshot(path=str(OUT/'formal-jianghai-parameters.png'),full_page=True)
        print(json.dumps({'status':'passed','models':observed,'browser_errors':errors},ensure_ascii=False))
    finally:
        context.close()
        browser.close()
