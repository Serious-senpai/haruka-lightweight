from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ...router import router
from ...tic_tac_toe import Room
if TYPE_CHECKING:
    from ...customs import Request


@router.get("/tic-tac-toe/rooms")
async def handler(request: Request) -> web.Response:
    websocket = web.WebSocketResponse()
    await websocket.prepare(request)

    Room.rooms.add_listener(websocket)
    await Room.rooms.notify(websocket)

    try:
        async for message in websocket:
            if message.data == "PING":
                await websocket.send_str("PONG")

    finally:
        Room.rooms.remove_listener(websocket)

    return websocket
