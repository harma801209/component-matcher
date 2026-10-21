"""Native Chrome acceptance of the actual search input; no report/price writes."""
import argparse
import json
import os
import platform
import time
from pathlib import Path

platform._wmi = None
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='https://fruition-component.pages.dev/')
    parser.add_argument('--login', action='store_true')
    args = parser.parse_args()
    out = Path(__file__).resolve().parents[2] / 'high-power-match-qa'
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        try:
            page.goto(args.url, wait_until='domcontentloaded', timeout=90000)
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                app = next((f for f in page.frames if f.get_by_role(
                    'button', name='开始匹配', exact=True).count()), None)
                if app:
                    break
                page.wait_for_timeout(400)
            else:
                raise AssertionError('Search UI unavailable')
            if args.login:
                account = os.environ['COMPONENT_QA_ACCOUNT']
                password = os.environ['COMPONENT_QA_PASSWORD']
                app.locator('.wb-login-button').click()
                app.get_by_role('textbox', name='账号', exact=True).first.fill(account)
                app.get_by_role('textbox', name='密码', exact=True).first.fill(password)
                app.get_by_role('button', name='登录', exact=True).click()
                app.locator('.wb-user-link').wait_for(timeout=90000)
                app.locator('.wb-nav').get_by_role('link', name='元器件搜索', exact=True).click()
                app.get_by_role('button', name='开始匹配', exact=True).wait_for(timeout=90000)
            query = '1.2Ω ±1% 500mW,1206'
            app.locator('textarea').first.fill(query)
            app.get_by_role('button', name='开始匹配', exact=True).click()
            deadline = time.monotonic() + 150
            summary = ''
            while time.monotonic() < deadline:
                status = app.locator('.search-progress-summary')
                summary = status.inner_text() if status.count() else ''
                if '已完成' in summary and '1/1' in summary:
                    break
                page.wait_for_timeout(500)
            else:
                raise AssertionError('Search incomplete: ' + summary)
            matched = []
            for frame in page.frames:
                for table in frame.locator('.result-table').all():
                    headers = table.locator('thead th').all_inner_texts()
                    for row in table.locator('tbody tr').all():
                        cells = row.locator('td').all_inner_texts()
                        if any('FRP1206F1R20TS' in value.replace(' ', '') for value in cells):
                            matched.append(dict(zip(headers, cells)))
                            row.scroll_into_view_if_needed()
            assert matched, 'Expected FRP1206F1R20TS absent from actual result table'
            for row in matched:
                assert any('完全匹配' in value for value in row.values()), row
                assert any('1.2' in value for value in row.values()), row
                assert any('1/2' in value or '0.5W' in value.replace(' ', '') for value in row.values()), row
                assert any('±1%' in value for value in row.values()), row
                assert any('1206' == value.strip() for value in row.values()), row
            assert app.locator('textarea').first.input_value() == query
            assert not errors, errors
            name = 'formal' if 'pages.dev' in args.url else 'local'
            page.screenshot(path=str(out / f'{name}.png'))
            # Deliberately omit prices/account data from reports.
            report = {'status': 'passed', 'query': query, 'model': 'FRP1206F1R20TS',
                      'exact_match': True, 'rating_watts': .5, 'browser_errors': errors}
            (out / f'{name}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(report, ensure_ascii=False), flush=True)
        finally:
            browser.close()


if __name__ == '__main__':
    main()
