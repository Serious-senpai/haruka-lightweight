from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ...router import router
from ...tic_tac_toe import Room
from ...utils import json_encode
if TYPE_CHECKING:
    from ...customs import Request


@router.get("/tic-tac-toe/rooms")
async def handler(request: Request) -> web.Response:
    return web.json_response([json_encode(room) for room in Room.rooms.values()])
