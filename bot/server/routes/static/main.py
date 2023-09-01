from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .router import router
from ...tic_tac_toe import manager
from ...web_utils import html_replace
if TYPE_CHECKING:
    from ...customs import Request


__all__ = ()


@router.get("/")
async def handler(request: Request) -> web.Response:
    raise web.HTTPFound("/index.html")


@router.get("/commands{none:\/?}")
async def handler(request: Request) -> web.Response:
    raise web.HTTPFound("/commands/index.html")


@router.get("/proxy{none:\/?}")
async def handler(request: Request) -> web.Response:
    raise web.HTTPFound("/proxy/index.html")


@router.get("/tic-tac-toe{none:\/?}")
async def handler(request: Request) -> web.Response:
    raise web.HTTPFound("/tic-tac-toe/index.html")


@router.get("/tic-tac-toe/room/{room_id}{none:\/?}")
async def handler(request: Request) -> web.Response:
    with open("bot/web/tic-tac-toe/room.html", "r") as file:
        html = file.read()

    room_id = request.match_info["room_id"]
    room = manager.from_id(room_id)
    if room is None:
        raise web.HTTPNotFound

    html = html_replace(html, "game-id", room_id)
    return web.Response(body=html, content_type="text/html")


@router.get("/favicon.ico")
@router.get("/favicon.png")
async def handler(request: Request) -> web.Response:
    raise web.HTTPFound(request.app.interface.client.user.display_avatar.url)


router.static("/", "bot/web/")
