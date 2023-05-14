from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web, web_ws

from .parsers import MOVE, START
from ...router import router
from ...tic_tac_toe import InvalidMove, InvalidTurn, NotStarted, Player, Room
if TYPE_CHECKING:
    from ...customs import Request


@router.get("/tic-tac-toe/room/{room_id}")
async def handler(request: Request) -> web.Response:
    room_id = request.match_info["room_id"]
    room = Room.from_id(room_id)
    if room is None:
        raise web.HTTPNotFound

    is_spectator = True
    player = await Player.from_request(request)
    if player is not None:
        websocket = player.websocket
        if not room.is_full():
            await room.join(player)
            is_spectator = False
    else:
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)

    room.add_listener(websocket)
    await room.notify(websocket)

    try:
        async for message in websocket:
            if is_spectator:
                # Ignore all client messages
                continue

            content = message.data
            if isinstance(content, str):
                if match := MOVE.fullmatch(content):
                    row, column = match.groups()
                    try:
                        await room.move(1, int(row), int(column))
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
                    await websocket.send_json(
                        {
                            "error": True,
                            "message": "Only the host can start the game!",
                        }
                    )

            else:
                await websocket.close(code=web_ws.WSCloseCode.UNSUPPORTED_DATA)

    finally:
        if not is_spectator:
            await room.leave(1)

    return websocket
