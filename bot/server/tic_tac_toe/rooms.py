from __future__ import annotations

import asyncio
import contextlib
import secrets
from typing import Any, Awaitable, Dict, List, Literal, Optional, Set, Tuple, TYPE_CHECKING

from aiohttp import web

from .errors import AlreadyEnded, AlreadyStarted, InvalidTurn, NotEnoughPlayer, NotStarted
from .players import Player
from .state import CoordinateT, State
from ..utils import Serializable, json_encode


class RoomsManager:

    __slots__ = (
        "__listeners",
        "__notify_lock",
        "__notify_semaphore",
        "__rooms",
    )
    if TYPE_CHECKING:
        __listeners: Set[web.WebSocketResponse]
        __notify_lock: asyncio.Lock
        __notify_semaphore: asyncio.Semaphore
        __rooms: Dict[str, Room]

    def __init__(self) -> None:
        self.__listeners = set()
        self.__notify_lock = asyncio.Lock()
        self.__notify_semaphore = asyncio.Semaphore(2)
        self.__rooms = {}

    def add(self, room: Room, /) -> Awaitable[None]:
        self.__rooms[room.id] = room
        return self.notify_all()

    def remove(self, room: Room, /) -> Awaitable[None]:
        assert room == self.__rooms.pop(room.id)
        return self.notify_all()

    def get(self, room_id: str, /) -> Optional[Room]:
        return self.__rooms.get(room_id)

    def add_listener(self, websocket: web.WebSocketResponse, /) -> None:
        self.__listeners.add(websocket)

    def remove_listener(self, websocket: web.WebSocketResponse, /) -> None:
        self.__listeners.remove(websocket)

    async def notify_all(self) -> None:
        if self.__notify_semaphore.locked():
            return

        async with self.__notify_semaphore:
            async with self.__notify_lock:
                await asyncio.gather(*[self.notify(websocket) for websocket in self.__listeners])

            await asyncio.sleep(2)

    async def notify(self, websocket: web.WebSocketResponse, /) -> None:
        with contextlib.suppress(ConnectionError):
            await websocket.send_json([json_encode(room) for room in self.__rooms.values()])

    def __contains__(self, room_id: str, /) -> bool:
        return self.__rooms.__contains__(room_id)


class Room(Serializable):

    __slots__ = (
        "__id",
        "__listeners",
        "__logs",
        "__players",
        "__removed",
        "__state",
    )
    rooms: RoomsManager = RoomsManager()
    if TYPE_CHECKING:
        __id: int
        __listeners: Set[web.WebSocketResponse]
        __logs: List[str]
        __players: Tuple[Player, Optional[Player]]
        __removed: bool
        __state: Optional[State]

    def __init__(self, *, host: Player) -> None:
        self.__id = secrets.token_urlsafe(8)
        while self.__id in self.rooms:
            self.__id = secrets.token_urlsafe(8)

        asyncio.create_task(self.rooms.add(self))

        self.__listeners = {host.websocket}
        self.__logs = [f"Room hosted by {host.user}"]
        self.__players = (host, None)
        self.__removed = False
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

    def chat(self, player: Optional[Player], content: str, /) -> Awaitable[None]:
        user_display = str(player.user) if player is not None else "Anonymous"
        return self.log(f"[{user_display}]: {content}")

    async def log(self, content: str, /) -> None:
        self.__logs.append(content)
        await self.__notify_all()

    def to_json(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "logs": self.__logs,
            "players": json_encode(self.players),
            "state": json_encode(self.__state),
        }

    def add_listener(self, websocket: web.WebSocketResponse) -> None:
        self.__listeners.add(websocket)

    def remove_listener(self, websocket: web.WebSocketResponse) -> None:
        self.__listeners.remove(websocket)

    def is_full(self) -> bool:
        return self.__players[1] is not None

    def index(self, player: Optional[Player], /) -> Optional[Literal[0, 1]]:
        if player is None:
            return

        for index in range(2):
            if player == self.__players[index]:
                return index

    async def try_join(self, player: Player) -> None:
        if self.is_full():
            return

        self.__players = (self.host, player)
        self.add_listener(player.websocket)
        await self.log(f"{player.user} joined the game")

    async def leave(self, player: Optional[Player], /) -> None:
        player_index = self.index(player)
        if player_index is None or self.__players[player_index] is None:
            return

        assert isinstance(player, Player)
        await self.log(f"{player.user} left the game")
        if self.__state is not None:
            assert (self.__state.started)
            self.__state.end(1 - player_index)

        elif player_index == 0:
            self.__players = (self.__players[1], None)

        elif player_index == 1:
            self.__players = (self.__players[0], None)

        else:
            raise ValueError(f"Invalid player index {player_index}")

        if self.__players[0] is None:
            # Mustn't send state to avoid client-side errors
            await self.remove()
        else:
            await self.__notify_all()

    async def remove(self) -> None:
        if not self.__removed:
            self.__removed = True
            await self.rooms.remove(self)
            self.__listeners.clear()

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

        if self.__state.ended:
            raise AlreadyEnded

        if player == self.__state.player_turn:
            ended = self.__state.move(row, column)
            await self.__notify_all()

            if ended:
                winner = self.__state.winner
                if winner is None:
                    await self.log("Game draw!")
                else:
                    await self.log(f"{self.players[winner].user} won!")

                await self.remove()
                for websocket in self.__listeners:
                    with contextlib.suppress(ConnectionError):
                        await websocket.close()
        else:
            raise InvalidTurn

    def __notify_all(self) -> Awaitable[None]:
        if not self.__removed:
            futures = [self.notify(websocket) for websocket in self.__listeners]
            futures.append(self.rooms.notify_all())
            return asyncio.gather(*futures)

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
