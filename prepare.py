from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import threading
from typing import TYPE_CHECKING
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class DummyServerHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("Server is preparing...".encode("utf-8"))


class DummyHTTPServer(ThreadingHTTPServer):
    def server_bind(self):
        with contextlib.suppress(Exception):
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)

        return super().server_bind()


class ServerThread(threading.Thread):

    __slots__ = ("__server", "__poll_interval")
    if TYPE_CHECKING:
        __server: DummyHTTPServer
        __poll_interval: float

    def __init__(self, *args, server: DummyHTTPServer, poll_interval: float = 0.5, **kwargs) -> None:
        self.__server = server
        self.__poll_interval = poll_interval
        super().__init__(*args, **kwargs)

    def run(self) -> None:
        self.__server.serve_forever(self.__poll_interval)


hostname = "localhost"
port = int(os.environ.get("PORT", 8000))

print("Initializing dummy server...")
server = DummyHTTPServer((hostname, port), DummyServerHandler)
print(f"Dummy HTTP server starting on port {port}")

thread = ServerThread(name="dummy-thread", server=server)
thread.start()


processes = [
    subprocess.Popen("pip install -r requirements.txt", shell=True),
    subprocess.Popen("apt install ffmpeg g++ git -y", shell=True),
]


for process in processes:
    process.wait()


process = subprocess.Popen("g++ -std=c++2a -Wall bot/c++/fuzzy.cpp -o bot/c++/fuzzy.out", shell=True)
process.wait()


try:
    server.shutdown()
    thread.join()
finally:
    print("Completed preparation. Launching main application.")
