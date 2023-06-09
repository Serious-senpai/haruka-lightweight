from __future__ import annotations

import asyncio
import contextlib
import datetime
import secrets
from collections import deque
from typing import ClassVar, Deque, Dict, NamedTuple, Optional, TYPE_CHECKING

from discord import abc
from discord.ext import tasks
from discord.utils import utcnow, sleep_until

if TYPE_CHECKING:
    from shared import SharedInterface
    from .customs import Request


class OTPCountdown(NamedTuple):
    timestamp: datetime.datetime
    key: str


class OTPCache:
    """Cache for OTP that deletes items after 5 minutes"""

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

    async def start_countdown(self) -> None:
        self.__countdown.start()

    def add_key(self, user: abc.User) -> str:
        key = f"{user.id}{secrets.token_hex(8)}"
        self.__data[key] = user
        self.__queue.append(OTPCountdown(timestamp=utcnow() + self.DELETE_AFTER, key=key))
        self.__countdown.restart()

        return key

    def pop_key(self, key: str) -> Optional[abc.User]:
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


async def authenticate_request(request: Request, *, interface: SharedInterface) -> Optional[abc.User]:
    token = request.headers.get("X-Auth-Token")
    if isinstance(token, str):
        async with interface.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT * FROM tokens WHERE token = ?", token)
                row = await cursor.fetchone()

                if row is not None:
                    return await interface.client.fetch_user(int(row[0]))
