from __future__ import annotations

import asyncio
import contextlib
import secrets
from typing import Any, ClassVar, Dict, List, Optional, Set, TYPE_CHECKING

from aiohttp import web

from .players import Player
from .rooms import Room
from .utils import data_message
from ..web_utils import json_encode


__all__ = (
    "Manager",
    "manager",
)


class Manager:

    __instance__: ClassVar[Optional[Manager]] = None
    __slots__ = (
        "_listeners",
        "_rooms",
    )
    if TYPE_CHECKING:
        _listeners: Set[Player]
        _rooms: Dict[str, Room]

    def __new__(cls) -> Manager:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self._listeners = set()
            self._rooms = {}

            cls.__instance__ = self

        return cls.__instance__

    def from_id(self, id: str, /) -> Optional[Room]:
        return self._rooms.get(id)

    def to_json(self) -> List[Any]:
        return json_encode(list(self._rooms.values()))

    async def add_listener(self, player: Player, /) -> None:
        self._listeners.add(player)
        await self.notify(player.websocket)

    def remove_listener(self, player: Player, /) -> None:
        with contextlib.suppress(KeyError):
            self._listeners.remove(player)

    async def notify_all(self) -> None:
        data = self.to_json()
        futures = [self.notify(player.websocket, data=data) for player in self._listeners]
        if len(futures) > 0:
            await asyncio.wait(futures)

    async def notify(self, websocket: web.WebSocketResponse, *, data: Any = None) -> None:
        if data is None:
            data = self.to_json()

        with contextlib.suppress(ConnectionError):
            await websocket.send_json(data_message(data))

    def create_new_id(self) -> str:
        id = secrets.token_urlsafe(8)
        while id in self._rooms:
            id = secrets.token_urlsafe(8)

        return id

    async def create_room(self, *, host: Player, id: Optional[str] = None) -> Room:
        if id is None:
            id = self.create_new_id()
        elif id in self._rooms:
            raise ValueError(f"Room ID {id} already exists!")

        def when_ended() -> None:
            self._rooms.pop(id)
            asyncio.create_task(self.notify_all())

        self._rooms[id] = room = Room(id=id, host=host)
        asyncio.create_task(room.wait_until_ended()).add_done_callback(lambda _: when_ended())

        room.notify_all.add_callback(lambda _: self.notify_all())
        await room.notify_all()
        return room


manager = Manager()
