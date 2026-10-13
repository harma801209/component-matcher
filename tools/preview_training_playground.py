"""Read-only local preview of the real embedded training assets, no business DBs."""
import argparse
import platform
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

platform._wmi = None
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from product_training import build_training_html

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8534)
args = parser.parse_args()
HOST = '''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;overflow:hidden}section{height:100vh;overflow:auto;padding:16px;box-sizing:border-box;display:flex;flex-direction:column;background:#f4f7fc}iframe{width:100%;border:0}#training-wrap{height:1050px;flex:0 0 1050px}</style></head><body><section data-testid="stMain"><div id="training-wrap" data-testid="stElementContainer"><iframe src="/lesson" height="1050" scrolling="no" title="培训实时3D实验"></iframe></div></section></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        text = build_training_html() if self.path.split('?')[0]=='/lesson' else HOST
        body = text.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self,*args):
        pass

print(f'Read-only training preview at http://127.0.0.1:{args.port}',flush=True)
ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
