from __future__ import annotations

import re
from typing import Literal, Optional, TypedDict

import aiohttp
from aiohttp import web_ws

from ...tic_tac_toe import (
    BOARD_SIZE,
    AlreadyEnded,
    AlreadyStarted,
    InvalidMove,
    InvalidTurn,
    NotEnoughPlayer,
    NotStarted,
    Player,
    Room,
)

valid_index_group = "|".join(str(i) for i in range(BOARD_SIZE))
CHAT = re.compile(r"^CHAT (.+?)$")
MOVE = re.compile(rf"^MOVE ({valid_index_group}) ({valid_index_group})$")
PING = re.compile(r"^PING$")
START = re.compile(r"^START$")


class ErrorMessage(TypedDict):
    error: Literal[True]
    message: str


def error_message(message: str) -> ErrorMessage:
    return {
        "error": True,
        "message": message,
    }


async def handle_message(*, player: Optional[Player], message: web_ws.WSMessage, room: Room) -> None:
    if player is None:
        return

    websocket = player.websocket
    data = message.data
    if isinstance(data, str):
        if match := CHAT.fullmatch(data):
            content = match.group(1)
            await room.chat(player, content)

        elif match := MOVE.fullmatch(data):
            player_index = room.index(player)

            if player_index is not None:
                row, column = match.groups()
                try:
                    await room.move(player_index, int(row), int(column))
                except AlreadyEnded:
                    await websocket.send_json(error_message("Game has already ended!"))
                except InvalidMove:
                    await websocket.send_json(error_message("Invalid move!"))
                except InvalidTurn:
                    await websocket.send_json(error_message("Not your turn yet!"))
                except NotStarted:
                    await websocket.send_json(error_message("Game hasn't started yet!"))

        if match := PING.fullmatch(data):
            await websocket.send_str("PONG")

        elif match := START.fullmatch(data):
            player_index = room.index(player)
            if player_index == 0:
                try:
                    await room.start()
                except AlreadyStarted:
                    await websocket.send_json(error_message("Game has already started!"))
                except NotEnoughPlayer:
                    await websocket.send_json(error_message("Not enough players to start!"))
            else:
                await websocket.send_json(error_message("Only the host can start the game!"))
