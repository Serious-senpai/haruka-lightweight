from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..router import router
from environment import INVITE_URL
if TYPE_CHECKING:
    from ..customs import Request


@router.get("/invite")
async def handler(request: Request) -> web.Response:
    raise web.HTTPFound(INVITE_URL)
