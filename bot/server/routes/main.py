from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..router import router
if TYPE_CHECKING:
    from ..customs import Request


@router.get("/")
async def handler(request: Request) -> web.Response:
    return web.Response(
        text=request.app.html,
        status=200,
        content_type="text/html",
    ) if request.app.interface.is_ready() else web.Response(
        text="Server is preparing",
        status=200,
        content_type="text/plain",
    )
