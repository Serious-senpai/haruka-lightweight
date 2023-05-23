from __future__ import annotations

from os import path
from random import randint
from typing import TYPE_CHECKING

from aiohttp import web
from yarl import URL

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


@router.get(r"/{file:.+?\.(?:html|css|js|json|otf|ttf)}")
async def handler(request: Request) -> web.Response:
    file = request.match_info["file"]
    filepath = path.join("bot/server/build", file)

    if not path.isfile(filepath):
        raise web.HTTPNotFound

    return web.FileResponse(filepath)
