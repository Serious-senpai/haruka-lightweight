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
    if player.user is None:
        websocket = player.websocket
        await websocket.send_json(error_message("Not logged in yet!"))
        await websocket.close()
        return websocket

    room = await Manager().create_room(host=player)

    try:
        websocket = player.websocket
        async for message in websocket:
            await handle_ws_message(player=player, message=message, room=room)

    finally:
        await room.leave(player)

    return websocket
