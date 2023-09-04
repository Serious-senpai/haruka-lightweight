from __future__ import annotations

import asyncio
import contextlib
import datetime
import secrets
from collections import deque
from typing import ClassVar, Deque, Dict, NamedTuple, Optional, TYPE_CHECKING

from aiohttp import web
from discord import abc
from discord.ext import tasks
from discord.utils import utcnow, sleep_until

if TYPE_CHECKING:
    from shared import SharedInterface
    from .customs import Request


__all__ = (
    "otp_cache",
    "generate_token",
    "authenticate_request",
    "authenticate_websocket",
)


class OTPCountdown(NamedTuple):
    timestamp: datetime.datetime
    key: str


class OTPCache:
    """Cache for OTPs that deletes items after 5 minutes"""

    DELETE_AFTER: ClassVar[datetime.timedelta] = datetime.timedelta(minutes=5)

    __instance__: Optional[OTPCache] = None
    if TYPE_CHECKING:
        __data: Dict[str, abc.User]
        __queue: Deque[OTPCountdown]

    def __new__(cls) -> OTPCache:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self.__data = {}
            self.__queue = deque()

            cls.__instance__ = self

        return cls.__instance__

    def start_countdown(self) -> None:
        """Start the background task that deletes OTP after the specified
        amount of time.
        """
        self.__countdown.start()

    def add_key(self, user: abc.User, /) -> str:
        """Add a new OTP for the specified user"""
        key = f"{user.id}{secrets.token_hex(8)}"
        self.__data[key] = user
        self.__queue.append(OTPCountdown(timestamp=utcnow() + self.DELETE_AFTER, key=key))
        self.__countdown.restart()

        return key

    def pop_key(self, key: str, /) -> Optional[abc.User]:
        """Get the user associated with the given key"""
        with contextlib.suppress(KeyError):
            return self.__data.pop(key)

    @tasks.loop()
    async def __countdown(self) -> None:
        if not self.__queue:
            await asyncio.sleep(3600)
        else:
            next = self.__queue[0]
            await sleep_until(next.timestamp)
            self.pop_key(next.key)
            self.__queue.popleft()

    def __getitem__(self, key: str) -> abc.User:
        return self.__data[key]


otp_cache = OTPCache()


async def generate_token(user: abc.User, *, interface: SharedInterface) -> str:
    async with interface.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM tokens WHERE id = ?", str(user.id))
            row = await cursor.fetchone()
            if row is not None:
                return row[1]

            token = f"{user.id}.{secrets.token_hex(16)}"
            await cursor.execute("INSERT INTO tokens (id, token) VALUES (?, ?)", str(user.id), token)

            return token


async def _get_user(token: str, *, interface: SharedInterface) -> Optional[abc.User]:
    async with interface.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM tokens WHERE token = ?", token)
            row = await cursor.fetchone()

            if row is not None:
                return await interface.client.fetch_user(int(row[0]))


async def authenticate_request(request: Request) -> Optional[abc.User]:
    token = request.headers.get("X-Auth-Token")
    if isinstance(token, str):
        return await _get_user(token, interface=request.app.interface)


async def authenticate_websocket(websocket: web.WebSocketResponse, *, interface: SharedInterface) -> Optional[abc.User]:
    """This function is a coroutine

    Wait for the next websocket message sent from client (timeout 60s) containing the
    user token.

    Parameters
    -----
    websocket: ``web.WebSocketResponse``
        The websocket that needs authentication
    interfaces: ``SharedInterface``
        The application shared interface

    Returns
    -----
    Optional[``abc.User``]
        The associated Discord account of this user
    """
    try:
        token = await websocket.receive_str(timeout=60)
    except Exception:
        return None
    else:
        return await _get_user(token, interface=interface)
