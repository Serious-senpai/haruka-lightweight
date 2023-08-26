from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..router import router
from ....tic_tac_toe import Manager, Player, error_message, handle_ws_message
if TYPE_CHECKING:
    from ....customs import Request


@router.get("/tic-tac-toe/create")
async def handler(request: Request) -> web.Response:
    player = await Player.from_request(request)
    room = await Manager().create_room(host=player)

    websocket = player.websocket
    try:
        async for message in websocket:
            await handle_ws_message(player=player, message=message, room=room)

    finally:
        await room.leave(player)

    return websocket
