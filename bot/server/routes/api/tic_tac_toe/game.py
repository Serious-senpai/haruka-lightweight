from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..router import router
from ....tic_tac_toe import Manager, Player, error_message, handle_ws_message
if TYPE_CHECKING:
    from ....customs import Request


@router.get("/tic-tac-toe/room/{room_id}")
async def handler(request: Request) -> web.Response:
    room_id = request.match_info["room_id"]
    room = Manager().from_id(room_id)
    if room is None:
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        await websocket.send_json(error_message("This room does not exist!"))
        await websocket.close()
        return websocket

    player = await Player.from_request(request)
    await room.try_join(player)

    try:
        websocket = player.websocket
        async for message in websocket:
            await handle_ws_message(player=player, message=message, room=room)

    finally:
        await room.leave(player)

    return websocket
