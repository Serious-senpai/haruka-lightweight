from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .router import router
if TYPE_CHECKING:
    from ...customs import Request


@router.get("/")
async def handler(request: Request) -> web.Response:
    raise web.HTTPFound("/index.html")


@router.get("/commands")
async def handler(request: Request) -> web.Response:
    raise web.HTTPFound("/commands/index.html")


@router.get("/favicon.ico")
@router.get("/favicon.png")
async def handler(request: Request) -> web.Response:
    raise web.HTTPFound(request.app.interface.client.user.avatar.url)


router.static("/", "bot/web/")
