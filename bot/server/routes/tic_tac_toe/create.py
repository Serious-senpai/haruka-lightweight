from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web, web_ws

from .parsers import MOVE, START
from ...router import router
from ...tic_tac_toe import (
    AlreadyStarted,
    InvalidMove,
    InvalidTurn,
    NotEnoughPlayer,
    NotStarted,
    Player,
    Room,
)
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
                content = message.data
                if isinstance(content, str):
                    if content == "PING":
                        await websocket.send_str("PONG")
                    elif match := MOVE.fullmatch(content):
                        row, column = match.groups()
                        try:
                            await room.move(0, int(row), int(column))
                        except InvalidMove:
                            await websocket.send_json(
                                {
                                    "error": True,
                                    "message": "Invalid move!",
                                }
                            )
                        except NotStarted:
                            await websocket.send_json(
                                {
                                    "error": True,
                                    "message": "Game hasn't started yet!",
                                }
                            )
                        except InvalidTurn:
                            await websocket.send_json(
                                {
                                    "error": True,
                                    "message": "Not your turn yet!",
                                }
                            )

                    elif match := START.fullmatch(content):
                        try:
                            await room.start()
                        except AlreadyStarted:
                            await websocket.send_json(
                                {
                                    "error": True,
                                    "message": "Game has already started!",
                                }
                            )
                        except NotEnoughPlayer:
                            await websocket.send_json(
                                {
                                    "error": True,
                                    "message": "Not enough players to start!",
                                }
                            )

                else:
                    await websocket.close(code=web_ws.WSCloseCode.UNSUPPORTED_DATA)

        finally:
            await room.leave(0)

    return websocket
