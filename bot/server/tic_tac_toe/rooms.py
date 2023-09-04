from __future__ import annotations

import asyncio
import contextlib
from typing import Any, Dict, List, Literal, Optional, Set, TYPE_CHECKING

from aiohttp import web

from global_utils import ExtendedCoroutineFunction
from .errors import (
    AlreadyEnded,
    AlreadyStarted,
    InvalidMove,
    InvalidTurn,
    MissingPermission,
    NotEnoughPlayer,
    NotStarted,
)
from .players import Player
from .utils import data_message
from ..web_utils import json_encode


__all__ = (
    "Room",
)


BOARD_SIZE = 15


class Room:
    """Represents a tic-tac-toe room"""

    __slots__ = (
        "_host",
        "_id",
        "_logs",
        "_other",
        "_spectators",

        # Game state controllers
        "_board",
        "_end",
        "_is_host_turn",
        "_started",
        "_winner",
    )
    if TYPE_CHECKING:
        _host: Player
        _id: str
        _logs: List[str]
        _other: Optional[Player]
        _spectators: Set[Player]

        # Game state controllers
        _board: List[List[Optional[int]]]
        _end: asyncio.Event
        _is_host_turn: bool
        _started: bool
        _winner: int

    def __init__(self, *, id: str, host: Player) -> None:
        self._host = host
        self._id = id
        self._logs = [f"{host} hosted room {id}. Type \"/start\" to start the game."]
        self._other = None
        self._spectators = set()

        self._board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self._end = asyncio.Event()
        self._is_host_turn = True
        self._started = False
        self._winner = 0

    @property
    def host(self) -> Player:
        return self._host

    # State broadcasting control

    def to_json(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "logs": self._logs,
            "host": json_encode(self._host),
            "other": json_encode(self._other),
            "board": json_encode(self._board),
            "turn": 1 - self._is_host_turn,
            "started": self._started,
            "ended": self.ended,
            "winner": self._winner,
        }

    async def wait_until_ended(self) -> None:
        """Wait until the game is over"""
        await self._end.wait()

    @ExtendedCoroutineFunction
    async def notify_all(self) -> None:
        """Send the state of this room to all listening websockets"""
        data = self.to_json()
        futures = [self.notify(player.websocket, data=data) for player in self._spectators]
        futures.append(self.notify(self._host.websocket, data=data))
        if self._other is not None:
            futures.append(self.notify(self._other.websocket, data=data))

        await asyncio.wait(futures)

    async def notify(self, websocket: web.WebSocketResponse, *, data: Any = None) -> None:
        """This function is a coroutine

        Send data to a specific websocket.

        Parameters
        -----
        websocket: ``web.WebSocketResponse``
            The websocket to send data to.
        data: Any
            The data to send to the websocket. If this is None, send the room state
            instead.
        """
        if data is None:
            data = self.to_json()

        with contextlib.suppress(ConnectionError):
            await websocket.send_json(data_message(data))

    async def add(self, player: Player, /) -> bool:
        """This function is a coroutine

        Add a player to the room. If the room is full, assign the player as a spectator
        instead.

        Parameters
        -----
        player: ``Player``
            The player to join. Note that unauthorized players will always be spectators.

        Returns
        -----
        ``bool``
            If True, the player joined the game, otherwise the player is treated as a
            spectator.
        """
        if player != self._host:
            if self._other is None:
                self._logs.append(f"{player} joined the game")
                self._other = player
                await self.notify_all()
                return True

            else:
                self._spectators.add(player)
                await self.notify(player.websocket)
                return False

    async def leave(self, player: Player, /) -> None:
        """This function is a coroutine

        Remove a player from the room. If the player is a participant, leave 1 vacant slot.

        Parameters
        -----
        player: ``Player``
            The player to remove from the room.
        """
        message = f"{player} left the game"
        if player == self._host:
            self._logs.append(message)
            if self._started:
                await self.end(host_win=False, reason=message)
            elif self._other is None:
                self._end.set()  # No player in the room
            else:
                self._host, self._other = self._other, None
                await self.notify_all()

        elif player == self._other:
            self._logs.append(message)
            if self._started:
                await self.end(host_win=True, reason=message)
            else:
                self._other = None
                await self.notify_all()

        else:
            with contextlib.suppress(KeyError):
                self._spectators.remove(player)

    async def chat(self, player: Player, content: str) -> None:
        """This function is a coroutine

        Add the chat content of a player to the chat logs.

        Parameters
        -----
        player: ``Player``
            The player that sent the message
        content: ``str``
            The message content
        """
        prefix = f"[{player}]"
        if player not in (self._host, self._other):
            # is spectator
            prefix += " (spectator)"

        self._logs.append(f"{prefix}: {content}")
        await self.notify_all()

    async def start(self, *, player: Player) -> None:
        if self._started:
            raise AlreadyStarted

        if player != self._host:
            raise MissingPermission

        if self._other is None:
            raise NotEnoughPlayer

        self._started = True
        self._logs.append("Game started!")
        await self.notify_all()

    async def end(self, *, host_win: bool, reason: str) -> None:
        if host_win:
            self._logs.append(f"{self._host} won: {reason}")
        else:
            self._logs.append(f"{self._other} won: {reason}")

        self._winner = 1 - host_win
        self._end.set()
        await self.notify_all()

    # Game state control

    @property
    def ended(self) -> bool:
        return self._end.is_set()

    def _check_vertical(self, *, column: int, expect: Literal[0, 1]) -> bool:
        consecutive = 0
        board = self._board
        for row in range(BOARD_SIZE):
            if board[row][column] == expect:
                consecutive += 1
                if consecutive == 5:
                    return True

            else:
                consecutive = 0

        return False

    def _check_horizontal(self, *, row: int, expect: Literal[0, 1]) -> bool:
        consecutive = 0
        r = self._board[row]
        for column in range(BOARD_SIZE):
            if r[column] == expect:
                consecutive += 1
                if consecutive == 5:
                    return True

            else:
                consecutive = 0

        return False

    def _check_diagonal(self, *, row: int, column: int, expect: Literal[0, 1]) -> bool:
        shift = min(row, column)
        row -= shift
        column -= shift

        consecutive = 0
        board = self._board
        while row < BOARD_SIZE and column < BOARD_SIZE:
            if board[row][column] == expect:
                consecutive += 1
                if consecutive == 5:
                    return True

            else:
                consecutive = 0

            row += 1
            column += 1

        return False

    def _check_antidiagonal(self, *, row: int, column: int, expect: Literal[0, 1]) -> bool:
        sum = row + column

        consecutive = 0
        board = self._board

        for row in range(max(0, sum - BOARD_SIZE + 1), min(sum + 1, BOARD_SIZE)):
            column = sum - row
            if board[row][column] == expect:
                consecutive += 1
                if consecutive == 5:
                    return True

            else:
                consecutive = 0

        return False

    async def move(self, row: int, column: int, *, player: Player) -> None:
        if not self._started:
            raise NotStarted

        if self.ended:
            raise AlreadyEnded

        valid = 0
        for value in range(BOARD_SIZE):
            valid += (value == row) + (value == column)

        if valid < 2:
            raise InvalidMove

        if (player == self._host and self._is_host_turn) or (player == self._other and not self._is_host_turn):
            self._board[row][column] = index = 1 - self._is_host_turn
            if any(
                [
                    self._check_vertical(column=column, expect=index),
                    self._check_horizontal(row=row, expect=index),
                    self._check_diagonal(row=row, column=column, expect=index),
                    self._check_antidiagonal(row=row, column=column, expect=index),
                ],
            ):
                await self.end(host_win=self._is_host_turn, reason="Got 5 marks in a row")

            self._is_host_turn = not self._is_host_turn
            await self.notify_all()

        else:
            raise InvalidTurn(is_spectator=player not in (self._host, self._other))
