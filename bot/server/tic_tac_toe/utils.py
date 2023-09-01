from __future__ import annotations

from typing import Any, Literal, TypedDict, TYPE_CHECKING

from aiohttp import web_ws

from .errors import (
    AlreadyEnded,
    AlreadyStarted,
    InvalidMove,
    InvalidTurn,
    MissingPermission,
    NotEnoughPlayer,
    NotStarted,
)
if TYPE_CHECKING:
    from .players import Player
    from .rooms import Room


__all__ = (
    "data_message",
    "error_message",
    "handle_ws_message",
)


class ErrorMessage(TypedDict):
    error: Literal[True]
    message: str


class DataMessage:
    error: Literal[False]
    data: Any


def data_message(data: Any, /) -> DataMessage:
    return {
        "error": False,
        "data": data,
    }


def error_message(message: str, /) -> ErrorMessage:
    return {
        "error": True,
        "message": message,
    }


async def handle_ws_message(*, player: Player, message: web_ws.WSMessage, room: Room) -> None:
    websocket = player.websocket
    data = message.data
    if isinstance(data, str):
        if data.startswith("CHAT "):
            await room.chat(player, data.removeprefix("CHAT "))

        elif data.startswith("MOVE "):
            try:
                row, column = map(int, data.removeprefix("MOVE ").split())
                await room.move(row, column, player=player)
            except AlreadyEnded:
                await websocket.send_json(error_message("Game has already ended!"))
            except InvalidMove:
                await websocket.send_json(error_message("Invalid move!"))
            except InvalidTurn as e:
                await websocket.send_json(error_message("You are spectating this game" if e.is_spectator else "Not your turn yet!"))
            except NotStarted:
                await websocket.send_json(error_message("Game hasn't started yet!"))
            except ValueError:
                await websocket.send_json(error_message("Invalid message data"))

        elif data == "START":
            try:
                await room.start(player=player)
            except AlreadyStarted:
                await websocket.send_json(error_message("Game has already started!"))
            except MissingPermission:
                await websocket.send_json(error_message("Only the host can start the game!"))
            except NotEnoughPlayer:
                await websocket.send_json(error_message("Not enough players to start!"))
