from __future__ import annotations

import asyncio
import contextlib
import datetime
import secrets
from collections import deque
from typing import ClassVar, Deque, Dict, NamedTuple, Optional, TYPE_CHECKING, overload

from discord import abc
from discord.ext import tasks
from discord.utils import utcnow, sleep_until

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


class TokenMapping:
    """Mapping between users and their tokens"""

    __instance__: Optional[TokenMapping] = None
    __slots__ = (
        "__user_to_token",
        "__token_to_user",
    )
    if TYPE_CHECKING:
        __user_to_token: Dict[abc.User, str]
        __token_to_user: Dict[str, abc.User]

    def __new__(cls) -> TokenMapping:
        if cls.__instance__ is None:
            self = super().__new__(TokenMapping)
            self.__user_to_token = {}
            self.__token_to_user = {}

            cls.__instance__ = self

        return cls.__instance__

    def generate_token(self, user: abc.User) -> str:
        """Return the token of a user, or generate a new one if
        that user doesn't have one yet
        """
        try:
            return self[user]
        except KeyError:
            token = f"{user.id}.{secrets.token_hex(16)}"
            self.__user_to_token[user] = token
            self.__token_to_user[token] = user
            return token

    def check_token(self, token: str) -> Optional[abc.User]:
        """Return the user from a given token"""
        return self.__token_to_user.get(token)

    @overload
    def __getitem__(self, key: str) -> abc.User: ...

    @overload
    def __getitem__(self, key: abc.User) -> str: ...

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.__token_to_user[key]

        if isinstance(key, abc.User):
            return self.__user_to_token[key]

        raise TypeError(f"Expected str or discord.abc.User, not {key.__class__.__name__}")


otp_cache = OTPCache()
token_mapping = TokenMapping()


def authenticate_request(request: Request) -> Optional[abc.User]:
    token = request.headers.get("X-Auth-Token")
    if isinstance(token, str):
        return token_mapping.check_token(token)
