from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("Server is preparing...".encode("utf-8"))


hostname = "localhost"
port = int(os.environ.get("PORT", 8000))
server = HTTPServer((hostname, port), DummyServer)
print(f"Dummy HTTP server started on port {port}")

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
    print("Server stopped")
