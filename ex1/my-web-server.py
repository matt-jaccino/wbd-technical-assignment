# exercise 1

import http.server
import os
import socketserver
from datetime import datetime

PORT = 8000


class HelloHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        resp = "Hello, World!\n"

        self.send_response(200)
        self.send_header("Content-type", "application/text")
        self.send_header("Content-Length", len(resp))
        self.end_headers()

        self.wfile.write(resp.encode())

handler = HelloHandler

with socketserver.TCPServer(("", PORT), handler) as server:
    print(
        f"{datetime.now().strftime('%F %T')} [{__file__.split(os.sep)[-1].split('.')[0]}] "
        f"- [INFO] Webserver listening: http://{server.server_address[0]}:{PORT} "
    )
    server.serve_forever()
