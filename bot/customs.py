from __future__ import annotations

import asyncio
import datetime
import sys
from typing import Optional, TYPE_CHECKING

import discord
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
        color: discord.Colour = discord.Colour(0x2ECC71),
        timestamp: datetime.datetime = discord.utils.utcnow(),
        url: Optional[str] = None,
    ) -> None:
        super().__init__(
            title=title,
            description=description,
            color=color,
            timestamp=timestamp,
            url=url,
        )


discord.Embed = _Embed  # Not a good practice, but whatever


if TYPE_CHECKING:
    class Guild(discord.Guild):
        voice_client: Optional[AudioPlayer]

    class Context(commands.Context[Haruka]):
        guild: Optional[Guild]
        voice_client: Optional[AudioPlayer]

    class Interaction(discord.Interaction[Haruka]):
        guild: Optional[Guild]

else:

    Guild = discord.Guild
    Context = commands.Context
    Interaction = discord.Interaction
