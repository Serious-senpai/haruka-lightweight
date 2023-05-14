from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Literal, Optional, Set, TYPE_CHECKING

from frozenlist import FrozenList

from .errors import InvalidMove
from ..utils import Serializable, json_encode
if TYPE_CHECKING:
    from .rooms import Room


TileState: Optional[Literal[0, 1]]
valid_index: Set[Literal[0, 1, 2]] = {0, 1, 2}


class State(Serializable):

    __slots__ = (
        "__board",
        "__end",
        "__player_index",
        "__start",
        "__winner",
        "room",
    )
    if TYPE_CHECKING:
        __board: List[List[TileState]]
        __end: asyncio.Event
        __player_index: Literal[0, 1]
        __start: asyncio.Event
        __winner: Optional[Literal[0, 1]]
        room: Room

    def __init__(self, *, room: Room) -> None:
        self.__board = [[None] * 3 for _ in range(3)]
        self.__end = asyncio.Event()
        self.__player_index = 0
        self.__start = asyncio.Event()
        self.__winner = None
        self.room = room

    @property
    def board(self) -> FrozenList[FrozenList[TileState]]:
        result = FrozenList(FrozenList(row) for row in self.__board)
        result.freeze()
        return result

    @property
    def started(self) -> bool:
        return self.__start.is_set()

    @property
    def ended(self) -> bool:
        return self.__end.is_set()

    @property
    def winner(self) -> Optional[Literal[0, 1]]:
        return self.__winner

    @property
    def player_turn(self) -> Literal[0, 1]:
        return self.__player_index

    def to_json(self) -> Dict[str, Any]:
        return {
            "board": json_encode(self.board),
            "ended": self.ended,
            "started": self.started,
            "turn": self.player_turn,
            "winner": self.winner,
        }

    async def wait_until_started(self) -> None:
        await self.__start.wait()

    async def wait_until_ended(self) -> None:
        await self.__end.wait()

    async def start(self) -> None:
        self.__start.set()

    def end(self, winner: Literal[0, 1]) -> None:
        self.__winner = winner
        self.__end.set()

    def move(
        self,
        row: Literal[0, 1, 2],
        column: Literal[0, 1, 2],
    ) -> bool:
        if self._move(row, column):
            # Set winner
            self.end(1 - self.__player_index)
            return True

        return False

    def _move(
        self,
        row: Literal[0, 1, 2],
        column: Literal[0, 1, 2],
    ) -> bool:
        board = self.__board
        if row not in valid_index or column not in valid_index or board[row][column] is not None:
            raise InvalidMove

        player_index = self.__player_index
        self.__player_index = 1 - self.__player_index
        board[row][column] = player_index

        # Does the move we just made result in a win?
        if board[row][(column + 1) % 3] == board[row][(column + 2) % 3] == player_index:
            return True

        if board[(row + 1) % 3][column] == board[(row + 2) % 3][column] == player_index:
            return True

        if board[(row + 1) % 3][(column + 1) % 3] == board[(row + 2) % 3][(column + 2) % 3] == player_index:
            return True

        if board[(row + 1) % 3][(column - 1) % 3] == board[(row + 2) % 3][(column - 2) % 3] == player_index:
            return True

        return False
