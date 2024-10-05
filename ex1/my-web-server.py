# exercise 1
#!/usr/bin/env python3

import os
import socketserver
from datetime import datetime
from http.server import BaseHTTPRequestHandler


PORT = 8000


class HelloHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        resp = "Hello, World!\n"

        self.send_response(200)
        self.send_header("Content-type", "application/text")
        self.send_header("Content-Length", len(resp))
        self.end_headers()

        self.wfile.write(resp.encode())


def main():
    with socketserver.TCPServer(("", PORT), HelloHandler) as server:
        print(
            f"{datetime.now().strftime('%F %T')} [{__file__.split(os.sep)[-1].split('.')[0]}] "
            f"- [INFO] Webserver listening: http://{server.server_address[0]}:{PORT} "
        )
        server.serve_forever()


if __name__ == "__main__":
    main()
