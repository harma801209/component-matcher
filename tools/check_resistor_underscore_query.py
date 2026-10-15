"""Native browser acceptance for underscore-delimited resistor requirements."""
import argparse
import json
import os
import platform
import re
import time
from pathlib import Path

platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--baseline', action='store_true')
parser.add_argument('--login', action='store_true')
parser.add_argument('--url', default='https://fruition-component.pages.dev/')
args = parser.parse_args()
out = Path(__file__).resolve().parents[2] / 'ocr-diagnostic-20261015/underscore-search'
out.mkdir(parents=True, exist_ok=True)
queries = ['0201_56k_1/32W_0.5%', '0402_5.6k_1/16W_0.1%', '0402_91Ω_1/16W_0.1%']
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width':1440, 'height':1000})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(args.url, wait_until='domcontentloaded', timeout=90000)
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        app = next((f for f in page.frames if f.get_by_role('button', name='开始匹配', exact=True).count()), None)
        if app: break
        page.wait_for_timeout(300)
    else: raise AssertionError('Search UI did not become ready')
    if args.login:
        account, password = os.environ.get('COMPONENT_QA_ACCOUNT'), os.environ.get('COMPONENT_QA_PASSWORD')
        if not account or not password:
            raise RuntimeError('Supply approved QA credentials through the environment')
        app.locator('.wb-login-button').click()
        app.get_by_role('textbox', name='账号', exact=True).first.fill(account)
        app.get_by_role('textbox', name='密码', exact=True).first.fill(password)
        app.get_by_role('button', name='登录', exact=True).click()
        app.locator('.wb-user-link').wait_for(timeout=90000)
        app.locator('.wb-nav').get_by_role('link', name='元器件搜索', exact=True).click()
        app.get_by_role('button', name='开始匹配', exact=True).wait_for(timeout=90000)
    app.locator('textarea').first.fill('\n'.join(queries))
    app.get_by_role('button', name='开始匹配', exact=True).click()
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        summary = app.locator('.search-progress-summary').inner_text() if app.locator('.search-progress-summary').count() else ''
        if '已完成' in summary and re.search(r'处理\s*3/3', summary): break
        page.wait_for_timeout(500)
    else: raise AssertionError('Search did not finish: ' + summary)
    body = app.locator('body').inner_text()
    tables = []
    for f in page.frames:
        for table in f.locator('.result-table').all():
            tables.append({'headers':table.locator('thead th').all_inner_texts(),
                           'rows':[row.locator('td').all_inner_texts() for row in table.locator('tbody tr').all()[:5]]})
    warnings = app.get_by_text('请确认搜索内容是否正确', exact=True).count()
    matched = re.search(r'有结果\s*(\d+)', summary)
    assert matched, summary
    count = int(matched.group(1))
    if args.baseline:
        assert count == 1 and warnings == 2, (summary, warnings)
    else:
        assert count == 2 and warnings == 0, (summary, warnings)
        assert app.locator('.section-title').filter(has_text='规格条件').count() == 3
        assert '请补充至少三个规格参数后再试' not in body, body[-2000:]
        assert not errors, errors
    name = 'baseline' if args.baseline else ('formal' if 'pages.dev' in args.url else 'local')
    app.locator('textarea').first.scroll_into_view_if_needed()
    page.screenshot(path=str(out / (name + '.png')), full_page=True)
    report = {'status':'passed', 'queries':queries, 'summary':summary, 'input_warnings':warnings,
              'tables':tables, 'browser_errors':errors}
    (out / (name + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status':'passed', 'summary':summary, 'input_warnings':warnings,
                      'table_count':len(tables), 'browser_errors':errors}, ensure_ascii=False), flush=True)
    browser.close()
