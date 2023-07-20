from __future__ import annotations

from os import path
from typing import TYPE_CHECKING

from aiohttp import web

from ..router import router
if TYPE_CHECKING:
    from ..customs import Request


@router.get("/favicon.ico")
@router.get("/favicon.png")
@router.get(r"/icons/{filename:.+?\.(?:png|jpg)}")
async def handler_a(request: Request) -> web.Response:
    raise web.HTTPFound(request.app.interface.client.user.avatar.url)


@router.get(r"/{file:.+?\.(?:html|css|js|json|otf|ttf)}")
async def handler_b(request: Request) -> web.Response:
    file = request.match_info["file"]
    filepath = path.join("bot/server/build", file)

    if not path.isfile(filepath):
        raise web.HTTPNotFound

    return web.FileResponse(filepath)
