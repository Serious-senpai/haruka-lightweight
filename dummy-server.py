from __future__ import annotations

import os

from aiohttp import web


routes = web.RouteTableDef()


@routes.get("/")
async def main(request: web.Request) -> web.Response:
    return web.Response(
        text="Server is preparing",
        status=200,
        content_type="text/plain",
    )


app = web.Application()
app.add_routes(routes)

port = int(os.environ["PORT"])

print(f"Starting dummy server on port {port}")
web.run_app(app, port=port)
