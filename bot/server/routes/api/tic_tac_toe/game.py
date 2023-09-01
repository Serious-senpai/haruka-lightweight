from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..router import router
from ....tic_tac_toe import Player, handle_ws_message, manager
if TYPE_CHECKING:
    from ....customs import Request


@router.get("/tic-tac-toe/room/{room_id}")
async def handler(request: Request) -> web.Response:
    player = await Player.from_request(request)

    room_id = request.match_info["room_id"]
    room = manager.from_id(room_id)

    if room is None:
        room = await manager.create_room(host=player, id=room_id)
    else:
        await room.add(player)

    websocket = player.websocket
    try:
        async for message in websocket:
            await handle_ws_message(player=player, message=message, room=room)

    finally:
        await room.leave(player)

    return websocket
