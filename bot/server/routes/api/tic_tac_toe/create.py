from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..router import router
from ....tic_tac_toe import manager
if TYPE_CHECKING:
    from ....customs import Request


@router.get("/tic-tac-toe/create")
async def handler(request: Request) -> web.Response:
    return web.json_response({"id": manager.create_new_id()})
