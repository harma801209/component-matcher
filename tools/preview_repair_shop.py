"""Read-only, loopback-only preview; never imports the application or its databases."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from product_training import build_training_html


class Preview(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split('?')[0] not in ('/', '/health'):
            self.send_error(404)
            return
        body = b'ok' if self.path == '/health' else build_training_html().encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain' if self.path == '/health' else 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    print('Repair-shop preview: http://127.0.0.1:8558/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8558), Preview).serve_forever()
