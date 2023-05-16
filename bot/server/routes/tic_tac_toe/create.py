from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .parsers import handle_message
from ...router import router
from ...tic_tac_toe import Player, Room
if TYPE_CHECKING:
    from ...customs import Request


@router.get("/tic-tac-toe/create")
async def handler(request: Request) -> web.Response:
    player = await Player.from_request(request)
    if player is None:
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        await websocket.send_json(
            {
                "error": True,
                "message": "Not logged in",
            }
        )
        await websocket.close()

    else:
        room = Room(host=player)
        websocket = player.websocket
        await room.notify(websocket)

        try:
            async for message in websocket:
                await handle_message(player=player, message=message, room=room)

        finally:
            await room.leave(player)

    return websocket
