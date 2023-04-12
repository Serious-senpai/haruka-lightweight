from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..router import router
if TYPE_CHECKING:
    from ..customs import Request


@router.get("/")
async def handler(request: Request) -> web.Response:
    raise web.HTTPTemporaryRedirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
