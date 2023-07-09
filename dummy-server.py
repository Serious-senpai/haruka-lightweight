from __future__ import annotations

import os
import signal
import threading
from typing import TYPE_CHECKING
from http.server import BaseHTTPRequestHandler, HTTPServer


class DummyServerHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("Server is preparing...".encode("utf-8"))


class ServerThread(threading.Thread):

    __slots__ = ("__server", "__poll_interval")
    if TYPE_CHECKING:
        __server: HTTPServer
        __poll_interval: float

    def __init__(self, *args, server: HTTPServer, poll_interval: float = 0.5, **kwargs) -> None:
        self.__server = server
        self.__poll_interval = poll_interval
        super().__init__(*args, **kwargs)

    def run(self) -> None:
        self.__server.serve_forever(self.__poll_interval)


hostname = "localhost"
port = int(os.environ.get("PORT", 8000))
server = HTTPServer((hostname, port), DummyServerHandler)
print(f"Dummy HTTP server starting on port {port}")

thread = ServerThread(name="dummy-thread", server=server)
thread.start()


signal.signal(signal.SIGTERM, lambda signum, frame: server.shutdown())


try:
    thread.join()
finally:
    print("Server stopped")
