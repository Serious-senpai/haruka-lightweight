from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from shared import interface
if TYPE_CHECKING:
    from haruka import Haruka


@interface.command(
    name="speak",
    brief="general.speak",
    description="Make the bot say something. Unlike `say`, this will attempt to delete your command message first",
)
async def _say_cmd(ctx: commands.Context[Haruka], *, content: str) -> None:
    files = [await attachment.to_file() for attachment in ctx.message.attachments]
    with contextlib.suppress(discord.HTTPException):
        await ctx.message.delete()

    await ctx.send(content, files=files)
