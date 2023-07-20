from __future__ import annotations

import asyncio
import datetime
import sys
from types import TracebackType
from typing import Any, Generic, List, Optional, Type, TypeVar, Union, TYPE_CHECKING

import aioodbc
import discord
from aioodbc import cursor
from discord.ext import commands
from pyodbc import Row

if TYPE_CHECKING:
    from haruka import Haruka
    from lib.youtube import AudioPlayer


if sys.platform == "win32":
    Loop = asyncio.ProactorEventLoop
else:
    try:
        import uvloop
    except ImportError:
        Loop = asyncio.SelectorEventLoop
    else:
        Loop = uvloop.Loop


class _Embed(discord.Embed):
    def __init__(
        self,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[Union[int, discord.Colour]] = None,
        timestamp: Optional[datetime.datetime] = None,
        url: Optional[str] = None,
    ) -> None:
        color = color or discord.Colour(0x2ECC71)
        timestamp = timestamp or discord.utils.utcnow()
        super().__init__(
            title=title,
            description=description,
            color=color,
            timestamp=timestamp,
            url=url,
        )


discord.Embed = _Embed  # Not a good practice, but whatever


if TYPE_CHECKING:
    T = TypeVar("T")

    # Context managers type hint

    class _ContextManager(Generic[T]):
        def __enter__(self) -> T:
            ...

        def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> Any:
            ...

    class _AsyncContextManager(Generic[T]):
        async def __aenter__(self) -> T:
            ...

        async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> Any:
            ...

    # Overwrite type hint from discord.py

    class Guild(discord.Guild):
        voice_client: Optional[AudioPlayer]

    class Context(commands.Context[Haruka]):
        guild: Optional[Guild]
        voice_client: Optional[AudioPlayer]

    class Interaction(discord.Interaction[Haruka]):
        guild: Optional[Guild]

    # Overwrite (actually implement) type hint from aioodbc
    class Cursor(cursor.Cursor):
        async def execute(self, sql: str, *params) -> Cursor:
            ...

        async def fetchone(self) -> Optional[Row]:
            ...

        async def fetchall(self) -> List[Row]:
            ...

    class Connection(aioodbc.Connection):
        def cursor(self) -> _AsyncContextManager[Cursor]:
            ...

    class Pool(aioodbc.Pool):
        def acquire(self) -> _AsyncContextManager[Connection]:
            ...

else:
    Guild = discord.Guild
    Context = commands.Context
    Interaction = discord.Interaction
    Connection = aioodbc.Connection
    Pool = aioodbc.Pool
