from __future__ import annotations

import asyncio
import contextlib
import secrets
from typing import Any, Awaitable, Dict, Literal, Optional, Set, Tuple, TYPE_CHECKING

from aiohttp import web

from .errors import AlreadyStarted, InvalidTurn, NotEnoughPlayer, NotStarted
from .players import Player
from .state import CoordinateT, State
from ..utils import Serializable, json_encode


class Room(Serializable):

    __slots__ = (
        "__id",
        "__listeners",
        "__players",
        "__state",
    )
    rooms: Dict[str, Room] = {}
    if TYPE_CHECKING:
        __id: int
        __listeners: Set[web.WebSocketResponse]
        __players: Tuple[Player, Optional[Player]]
        __state: Optional[State]

    def __init__(self, *, host: Player) -> None:
        self.__id = secrets.token_urlsafe(8)
        while self.__id in self.rooms:
            self.__id = secrets.token_urlsafe(8)

        self.rooms[self.__id] = self

        self.__listeners = {host.websocket}
        self.__players = (host, None)
        self.__state = None

    @property
    def id(self) -> str:
        return self.__id

    @property
    def host(self) -> Player:
        return self.__players[0]

    @property
    def players(self) -> Tuple[Player, Optional[Player]]:
        return self.__players

    @property
    def winner(self) -> Optional[Literal[0, 1]]:
        if self.__state is not None:
            return self.__state.winner

    def to_json(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "players": json_encode(self.players),
            "state": json_encode(self.__state),
        }

    def add_listener(self, websocket: web.WebSocketResponse) -> None:
        self.__listeners.add(websocket)

    def remove_listener(self, websocket: web.WebSocketResponse) -> None:
        self.__listeners.remove(websocket)

    def is_full(self) -> bool:
        return self.__players[1] is not None

    async def join(self, player: Player) -> None:
        self.__players = (self.host, player)
        self.add_listener(player.websocket)
        await self.__notify_all()

    async def leave(self, player_index: Literal[0, 1]) -> None:
        if self.__players[player_index] is None:
            return

        if self.__state is not None:
            assert (self.__state.started)
            self.__state.end(1 - player_index)
        elif player_index == 0:
            self.__players = (self.__players[1], None)
        elif player_index == 1:
            self.__players = (self.__players[0], None)
        else:
            raise ValueError(f"Invalid player index {player_index}")

        await self.__notify_all()

    async def remove(self) -> None:
        with contextlib.suppress(KeyError):
            self.rooms.pop(self.__id)
            await self.__notify_all()

    async def start(self) -> None:
        if self.__state is not None:
            assert (self.__state.started)
            raise AlreadyStarted

        if not self.is_full():
            raise NotEnoughPlayer

        state = self.__state = State(room=self)
        await state.start()

        async def wait_until_ended() -> None:
            await state.wait_until_ended()
            await self.remove()

        asyncio.create_task(wait_until_ended())
        await self.__notify_all()

    async def move(
        self,
        player: Literal[0, 1],
        row: CoordinateT,
        column: CoordinateT,
    ) -> None:
        if self.__state is None:
            raise NotStarted

        if player == self.__state.player_turn:
            ended = self.__state.move(row, column)
            await self.__notify_all()

            if ended:
                await self.remove()
                for websocket in self.__listeners:
                    with contextlib.suppress(ConnectionError):
                        await websocket.close()
        else:
            raise InvalidTurn

    def __notify_all(self) -> Awaitable[None]:
        return asyncio.gather(*[self.notify(websocket) for websocket in self.__listeners])

    async def notify(self, websocket: web.WebSocketResponse) -> None:
        with contextlib.suppress(ConnectionError):
            await websocket.send_json(
                {
                    "error": False,
                    "data": json_encode(self),
                }
            )

    @classmethod
    def from_id(cls, id: str) -> Optional[Room]:
        return cls.rooms.get(id)
