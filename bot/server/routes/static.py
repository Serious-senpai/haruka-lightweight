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
async def handler(request: Request) -> web.Response:
    try:
        raise web.HTTPFound(request.app.interface.clients[0].user.avatar.url)
    except AttributeError:
        raise web.HTTPNotFound


@router.get(r"/{filename:.+?\.(?:html|css|js|json|otf|ttf)}")
async def handler(request: Request) -> web.Response:
    filepath = path.join("bot/server/build", request.match_info["filename"])

    if not path.isfile(filepath):
        raise web.HTTPNotFound

    return web.FileResponse(filepath)
