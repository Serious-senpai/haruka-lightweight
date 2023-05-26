from __future__ import annotations

import asyncio
import datetime
import sys
from typing import Generic, Optional, TypeVar, Union, TYPE_CHECKING

import aioodbc
import discord
from aioodbc.cursor import Cursor
from discord.ext import commands

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

    class _AsyncContextManager(Generic[T]):
        async def __aenter__(self) -> T:
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
