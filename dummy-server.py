from __future__ import annotations

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
web.run_app(app)
