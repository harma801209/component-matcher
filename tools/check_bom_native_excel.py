"""Native Chrome footer QA. Protocol launch is checked, not OS prompt bypassed."""
import argparse
import hashlib
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import platform
import sys
import tempfile
import threading
import time
platform._wmi = None
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.test_bom_excel_preview import fixture_bytes, footer_builder
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phone', action='store_true')
    args = parser.parse_args()
    out = ROOT.parent / 'ocr-diagnostic-20261016/native-excel'
    out.mkdir(parents=True, exist_ok=True)
    raw = fixture_bytes()
    url = 'https://fruition-component.pages.dev/x/' + 'A'*43 + '/BOM.xlsx'
    footer = footer_builder()(raw, 'BOM_匹配后.xlsx', native_link={'url':url,'expires':time.time()+300})

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/favicon.ico':
                self.send_response(204); self.end_headers(); return
            if self.path == '/':
                body = f'<meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{margin:0}}iframe{{width:100%;height:100vh;border:0}}</style><iframe id="app" src="http://localhost:{server.server_port}/app"></iframe>'
            else:
                body = ('<meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;padding:18px;font:16px system-ui;color:#173453;background:#f4f7fd}.head{display:flex;gap:16px;justify-content:space-between}.actions{width:440px;height:72px;border:0}@media(max-width:700px){.head{display:block}.actions{width:100%}}</style><div class="head"><h2>BOM匹配结果</h2><iframe id="actions" class="actions" sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-downloads" srcdoc="'
                        + html.escape(footer, quote=True) + '"></iframe></div>')
            data = body.encode()
            self.send_response(200); self.send_header('Content-Type','text/html;charset=utf-8')
            self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
        def log_message(self,*args): pass

    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p, tempfile.TemporaryDirectory(prefix='native-excel-footer-') as tmp:
            browser = p.chromium.launch(channel='chrome',headless=True)
            context = browser.new_context(viewport={'width':393,'height':852} if args.phone else {'width':1440,'height':900},
                                          is_mobile=args.phone,has_touch=args.phone,accept_downloads=True)
            context.add_init_script('Object.defineProperty(window,"showSaveFilePicker",{value:undefined,configurable:true});')
            page = context.new_page(); errors=[]
            page.clock.install()
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='load')
            actions = page.frame_locator('#app').frame_locator('#actions')
            link = actions.get_by_role('link',name='用本机 Excel 打开匹配后文件（只读）')
            link.wait_for()
            assert link.get_attribute('href') == 'ms-excel:ofv|u|' + url
            assert link.evaluate('n=>[...document.querySelectorAll(".bom-save-as-btn")].every(b=>{const r=b.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1&&r.bottom<=46})')
            assert actions.locator('.bom-excel-help').evaluate('n=>n.getBoundingClientRect().bottom<=innerHeight')
            assert link.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(out/('phone-actions.png' if args.phone else 'desktop-actions.png')))
            # Expiry can be observed without making an uncontrolled OS launch.
            page.clock.fast_forward(301000)
            assert link.get_attribute('aria-disabled') == 'true'
            assert link.get_attribute('href') is None
            with page.expect_download() as event:
                actions.get_by_role('button',name='下载 Excel',exact=True).click()
            path=Path(tmp)/'download.xlsx'; event.value.save_as(path)
            assert path.read_bytes()==raw
            assert not errors,errors
            print(json.dumps({'viewport':'phone' if args.phone else 'desktop','native_read_only_uri':True,
                              'expiry_disables_launch':True,'download_after_expiry_exact':True,
                              'sha256':hashlib.sha256(raw).hexdigest(),'page_errors':errors},ensure_ascii=False))
            browser.close()
    finally:
        server.shutdown(); server.server_close()


if __name__ == '__main__': main()
