from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from aiohttp import web

from ..router import router
if TYPE_CHECKING:
    from ..customs import Request


redirect: Optional[str] = None


@router.get("/favicon.ico")
async def handler(request: Request) -> web.Response:
    global redirect
    redirect = redirect or request.app.interface.clients[0].user.avatar.url
    raise web.HTTPFound(redirect)
