from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web, web_ws

from .parsers import handle_message
from ...router import router
from ...tic_tac_toe import Player, Room
if TYPE_CHECKING:
    from ...customs import Request


@router.get("/tic-tac-toe/room/{room_id}")
async def handler(request: Request) -> web.Response:
    room_id = request.match_info["room_id"]
    room = Room.from_id(room_id)
    if room is None:
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        await websocket.send_json(
            {
                "error": True,
                "message": "This room does not exist!",
            }
        )
        await websocket.close()
        return websocket

    player = await Player.from_request(request)
    if player is not None:
        websocket = player.websocket
        await room.try_join(player)
    else:
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)

    room.add_listener(websocket)
    await room.notify(websocket)

    try:
        async for message in websocket:
            await handle_message(player=player, message=message, room=room)

    finally:
        await room.leave(player)

    return websocket
