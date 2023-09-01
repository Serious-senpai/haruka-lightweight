from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..router import router
from ....tic_tac_toe import Player, manager
if TYPE_CHECKING:
    from ....customs import Request


@router.get("/tic-tac-toe/rooms")
async def handler(request: Request) -> web.Response:
    player = await Player.from_request(request)
    await manager.add_listener(player)

    websocket = player.websocket
    try:
        async for message in websocket:
            if message.data == "REQUEST":
                await manager.notify(websocket)

    finally:
        manager.remove_listener(player)

    return websocket
