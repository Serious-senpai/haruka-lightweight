from __future__ import annotations

from os import path
from typing import Optional, TYPE_CHECKING

from aiohttp import web

from ..router import router
if TYPE_CHECKING:
    from ..customs import Request


avatar_url: Optional[str] = None


@router.get("/favicon.ico")
@router.get("/favicon.png")
@router.get("/icons/{filename:.+?\.(?:png|jpg)}")
async def handler(request: Request) -> web.Response:
    global avatar_url
    avatar_url = avatar_url or request.app.interface.clients[0].user.avatar.url
    raise web.HTTPFound(avatar_url)


@router.get("/{filename:.+?\.(?:html|js|json|otf|ttf)}")
async def handler(request: Request) -> web.Response:
    filepath = path.join("bot/server/build", request.match_info["filename"])

    if not path.isfile(filepath):
        raise web.HTTPNotFound

    return web.FileResponse(filepath)
