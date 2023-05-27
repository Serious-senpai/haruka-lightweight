from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, Set, TYPE_CHECKING

from .errors import InvalidMove
from ..web_utils import Serializable, json_encode
if TYPE_CHECKING:
    from .rooms import Room


BOARD_SIZE = 15
TileState = Optional[Literal[0, 1]]
CoordinateT = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
valid_index: Set[CoordinateT] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14}


class State(Serializable):

    __slots__ = (
        "__board",
        "__end",
        "__move_count",
        "__player_turn",
        "__start",
        "__winner",
        "room",
    )
    if TYPE_CHECKING:
        __board: List[List[TileState]]
        __end: asyncio.Event
        __move_count: int
        __player_turn: Literal[0, 1]
        __start: asyncio.Event
        __winner: Optional[Literal[0, 1]]
        room: Room

    def __init__(self, *, room: Room) -> None:
        self.__board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.__end = asyncio.Event()
        self.__move_count = 0
        self.__player_turn = 0
        self.__start = asyncio.Event()
        self.__winner = None
        self.room = room

    @property
    def board(self) -> List[List[TileState]]:
        return deepcopy(self.__board)

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
    def draw(self) -> bool:
        return self.ended and self.winner is None

    @property
    def player_turn(self) -> Literal[0, 1]:
        return self.__player_turn

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

    def end(self, winner: Optional[Literal[0, 1]]) -> None:
        self.__winner = winner
        self.__end.set()

    def move(
        self,
        row: CoordinateT,
        column: CoordinateT
    ) -> bool:
        board = self.__board
        if row not in valid_index or column not in valid_index or board[row][column] is not None:
            raise InvalidMove

        player_index = self.__player_turn
        self.__player_turn = 1 - self.__player_turn
        board[row][column] = player_index

        self.__move_count += 1

        # Does the move we just made result in a win?
        if any(
            [
                self._check_vertical(column=column, player=player_index),
                self._check_horizontal(row=row, player=player_index),
                self._check_diagonal(row=row, column=column, player=player_index),
                self._check_antidiagonal(row=row, column=column, player=player_index),
            ],
        ):
            self.end(player_index)
            return True

        if self.__move_count == BOARD_SIZE ** 2:
            self.end(None)
            return True

        return False

    def _check_vertical(self, *, column: CoordinateT, player: Literal[0, 1]) -> bool:
        consecutive = 0
        board = self.__board
        for i in range(BOARD_SIZE):
            if board[i][column] == player:
                consecutive += 1
                if consecutive == 5:
                    return True

            else:
                consecutive = 0

        return False

    def _check_horizontal(self, *, row: CoordinateT, player: Literal[0, 1]) -> bool:
        consecutive = 0
        board = self.__board
        for i in range(BOARD_SIZE):
            if board[row][i] == player:
                consecutive += 1
                if consecutive == 5:
                    return True

            else:
                consecutive = 0

        return False

    def _check_diagonal(self, *, row: CoordinateT, column: CoordinateT, player: Literal[0, 1]) -> bool:
        i = max(0, row - column)
        j = max(0, column - row)
        consecutive = 0
        board = self.__board
        while i < BOARD_SIZE and j < BOARD_SIZE:
            if board[i][j] == player:
                consecutive += 1
                if consecutive == 5:
                    return True

            else:
                consecutive = 0

            i += 1
            j += 1

        return False

    def _check_antidiagonal(self, *, row: CoordinateT, column: CoordinateT, player: Literal[0, 1]) -> bool:
        consecutive = 0
        board = self.__board
        for i in range(BOARD_SIZE):
            j = row + column - i
            if 0 <= j < BOARD_SIZE:
                if board[i][j] == player:
                    consecutive += 1
                    if consecutive == 5:
                        return True

                else:
                    consecutive = 0

        return False
