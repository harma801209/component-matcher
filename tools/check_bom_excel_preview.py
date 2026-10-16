"""Native Chrome test of the actual footer inside nested Streamlit-like iframes."""
import argparse
import hashlib
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import platform
import re
import tempfile
import threading
from pathlib import Path
import sys
platform._wmi = None
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.test_bom_excel_preview import fixture_bytes, footer_builder
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--phone', action='store_true')
args = parser.parse_args()
OUT = ROOT.parent / 'ocr-diagnostic-20261016/excel-preview'
OUT.mkdir(parents=True, exist_ok=True)
raw = fixture_bytes()
footer = footer_builder()(raw, 'BOM_匹配后.xlsx', initial_sheet='其他工作表')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return
        if self.path == '/':
            body = f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>BOM results</title><style>body{{margin:0}}iframe{{width:100%;height:100vh;border:0}}</style><iframe id="app" src="http://localhost:{server.server_port}/app" title="匹配系统"></iframe>'
        else:
            body = ('<meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;padding:18px;font:16px system-ui;color:#173453;background:#f4f7fd}.head{display:flex;align-items:center;gap:16px;justify-content:space-between}h2{font-size:21px}.actions{width:440px;height:48px;border:0}p{color:#6e83a1}@media(max-width:700px){.head{display:block}.actions{width:100%}}</style><p>复核视图显示第1–20行；在线打开和下载均使用完整匹配文件。</p><div class="head"><h2>BOM匹配结果</h2><iframe id="actions" class="actions" title="结果操作" sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-downloads" srcdoc="'
                    + html.escape(footer, quote=True) + '"></iframe></div>')
        data = body.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html;charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
label = 'phone' if args.phone else 'desktop'
try:
    with sync_playwright() as p, tempfile.TemporaryDirectory(prefix='excel-preview-native-') as tmp:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width':393,'height':852} if args.phone else {'width':1440,'height':900}, is_mobile=args.phone, has_touch=args.phone, accept_downloads=True)
        # Exercise the browser-download fallback, not an uncontrolled OS save dialog.
        context.add_init_script('Object.defineProperty(window,"showSaveFilePicker",{value:undefined,configurable:true});')
        errors, alerts, downloads = [], [], []
        def watch(page):
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda msg: errors.append(msg.text) if msg.type=='error' else None)
            page.on('dialog', lambda dialog: (alerts.append(dialog.message), dialog.dismiss()))
            page.on('download', lambda download: downloads.append(download.suggested_filename))
        context.on('page', watch)
        page = context.new_page()
        page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='load')
        actions = page.frame_locator('#app').frame_locator('#actions')
        opener = actions.get_by_role('link', name='在线打开匹配后 Excel，新标签页只读预览')
        opener.wait_for(state='visible')
        page.wait_for_timeout(180)
        assert opener.evaluate('n=>[...document.querySelectorAll(".bom-save-as-btn")].every(b=>{const r=b.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1&&r.bottom<=48})')
        page.screenshot(path=str(OUT / f'{label}-actions.png'))
        with page.expect_popup() as pending:
            opener.tap() if args.phone else opener.click()
        preview = pending.value
        preview.wait_for_url(re.compile(r'^blob:'),wait_until='domcontentloaded')
        preview.wait_for_load_state('domcontentloaded')
        assert preview.url.startswith('blob:')
        assert preview.evaluate('window.opener === null')
        assert not downloads, downloads
        assert preview.locator('#summary').inner_text().startswith('其他工作表')
        assert preview.locator('#sheets button').count()==3
        assert preview.locator('img').count()==0
        assert not alerts
        assert '12.5%' in preview.locator('tbody').inner_text()
        preview.get_by_role('button',name='完整BOM',exact=True).click()
        assert '223 / 223 行' in preview.locator('#summary').inner_text()
        assert preview.locator('tbody tr').count()==100
        assert '0201' in preview.locator('tbody').inner_text()
        assert '=SUM(E2:E3)' in preview.locator('tbody').inner_text()
        preview.get_by_role('button',name='下一页',exact=True).click()
        preview.get_by_role('button',name='下一页',exact=True).click()
        assert preview.locator('tbody tr:last-child th').inner_text()=='224'
        preview.locator('#search').fill('FRC0402J223 TS')
        assert preview.locator('tbody tr').count()==1
        assert '1 / 223 行' in preview.locator('#summary').inner_text()
        preview.screenshot(path=str(OUT / f'{label}-full-last-row.png'))
        preview.get_by_role('button',name='空工作表',exact=True).click()
        assert preview.get_by_text('空工作表',exact=True).count()>=1
        preview.get_by_role('button',name='其他工作表',exact=True).click()
        with preview.expect_download() as download_event:
            preview.get_by_role('button',name='下载 Excel',exact=True).click()
        path = Path(tmp) / 'from-viewer.xlsx'
        download_event.value.save_as(path)
        assert path.read_bytes()==raw
        with page.expect_download() as original_download:
            actions.get_by_role('button',name='下载 Excel',exact=True).click()
        original_path = Path(tmp) / 'from-original.xlsx'
        original_download.value.save_as(original_path)
        assert original_path.read_bytes()==raw
        assert len(downloads)==2
        assert not errors and not alerts,(errors,alerts)
        assert preview.evaluate('document.documentElement.scrollWidth<=innerWidth')
        print(json.dumps({'viewport':label,'opened_without_download':True,'visible_sheets':3,'full_rows':223,'last_original_row':224,'downloads_identical':True,'sha256':hashlib.sha256(raw).hexdigest(),'console_errors':errors,'alerts':alerts},ensure_ascii=False),flush=True)
        preview.close()
        page.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
