"""Verify grouped source-only cards; public QA never submits a report."""
import argparse
import json
import os
import platform
import time
from pathlib import Path

platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
args = parser.parse_args()
models = ['FRQ0603F33R0TS', 'FRQ0603F1002TS', 'FRQ0603F33R0TS']
out = Path(__file__).resolve().parents[2] / 'dark-ui-test/test-runtime/visual-qa/no-alt-cards'
out.mkdir(parents=True, exist_ok=True)
selector = '[class*="st-key-search_no_alt_card_"]'
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(viewport={'width':1440, 'height':1000})
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/' if args.public else 'http://127.0.0.1:8513/',
                  wait_until='domcontentloaded', timeout=90000)
        app = page.main_frame
        if args.public:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                app = next((f for f in page.frames if 'fruition-componentmatche.streamlit.app' in f.url), None)
                if app:
                    break
                page.wait_for_timeout(300)
            assert app, 'Formal app frame missing'
            account, password = os.getenv('COMPONENT_QA_ACCOUNT'), os.getenv('COMPONENT_QA_PASSWORD')
            if not account or not password:
                raise RuntimeError('Approved QA credentials must be supplied through the environment')
            app.locator('.wb-login-button').click(timeout=90000)
            app.get_by_role('textbox', name='账号', exact=True).first.fill(account)
            app.get_by_role('textbox', name='密码', exact=True).first.fill(password)
            app.get_by_role('button', name='登录', exact=True).click()
            app.locator('.wb-user-link').wait_for(timeout=90000)
            app.locator('.wb-nav').get_by_role('link', name='元器件搜索', exact=True).click()
            app.get_by_role('button', name='开始匹配', exact=True).wait_for(timeout=90000)
            app.locator('textarea').first.fill('\n'.join(models))
            app.get_by_role('button', name='开始匹配', exact=True).click()
            app.locator('.search-progress-summary-status').filter(has_text='已完成').wait_for(timeout=150000)
        app.locator(selector).first.wait_for(timeout=90000)
        assert app.locator(selector).count() == len(models)
        for width in [1440,900,390]:
            page.set_viewport_size({'width':width, 'height':1000})
            page.wait_for_timeout(500)
            for index, model in enumerate(models):
                card = app.locator(selector).nth(index)
                card.scroll_into_view_if_needed()
                assert model in card.inner_text()
                button = card.get_by_role('button', name='回报物料无匹配型号', exact=True)
                assert button.count() == 1 and button.is_visible()
                footer = card.locator('[class*="st-key-search_no_alt_footer_"]')
                assert footer.count() == 1
                assert '暂未找到其他品牌替代结果' in footer.inner_text()
                assert footer.get_by_role('button').count() == 1
                frame = card.locator('iframe').element_handle().content_frame()
                assert model in frame.locator('.result-table').inner_text()
                assert frame.locator('.match-card-footer').count() == 0
                box, action = card.bounding_box(), button.bounding_box()
                assert box['x'] <= action['x'] and box['y'] <= action['y']
                assert action['x']+action['width'] <= box['x']+box['width']+1
                assert action['y']+action['height'] <= box['y']+box['height']+1
                table_bottom = frame.locator('.result-table-wrap').evaluate('e=>e.getBoundingClientRect().bottom')
                iframe_height = card.locator('iframe').bounding_box()['height']
                header = card.locator('[data-testid="stMarkdownContainer"]').first
                header_box, table_box = header.bounding_box(), card.locator('iframe').bounding_box()
                assert header_box['y']+header_box['height'] <= table_box['y']+1, 'Header overlaps table'
                assert table_bottom <= iframe_height, (table_bottom,iframe_height)
                assert iframe_height-table_bottom < 32, 'Unnecessary blank below source table'
                assert footer.evaluate('e=>getComputedStyle(e).backgroundColor') != 'rgba(0, 0, 0, 0)'
                if index == 0:
                    card.screenshot(path=str(out/f'{"formal" if args.public else "local"}-{width}.png'))
            size = app.evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
            assert size['scroll'] <= size['client']+1, size
        if not args.public:
            frame = app.locator(selector).first.locator('iframe').element_handle().content_frame()
            frame.evaluate('''()=>{
                const body=document.querySelector('.result-table tbody'),row=body.firstElementChild;
                for(let i=0;i<5;i++)body.append(row.cloneNode(true));
                const wrap=document.querySelector('.result-table-wrap');
                if(wrap.scrollHeight<=wrap.clientHeight)throw Error('Long source table must scroll');
                wrap.scrollTop=wrap.scrollHeight;
                const bottom=body.lastElementChild.getBoundingClientRect().bottom;
                if(bottom>wrap.getBoundingClientRect().bottom+1)throw Error('Last source row unreachable');
            }''')
            # The isolated preview captures callbacks without creating business reports.
            for index in [1,0,2]:
                app.locator(selector).nth(index).get_by_role('button', name='回报物料无匹配型号', exact=True).click()
                app.get_by_text('已点击：'+models[index], exact=True).wait_for(timeout=30000)
        assert not errors, errors
        print(json.dumps({'status':'passed','public':args.public,'cards':3,'duplicate_input':True,
                          'widths':[1440,900,390],'native_report_grouping':True,
                          'public_reports_submitted':0,'browser_errors':errors}), flush=True)
    finally:
        context.close()
        browser.close()
