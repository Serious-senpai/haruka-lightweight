from __future__ import annotations

import contextlib

import discord
from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="speak",
    brief="general.speak",
    description="Make the bot say something. Unlike `say`, this will attempt to delete your command message first",
    usage="{prefix}speak <content>",
)
async def _handler(ctx: Context, *, content: str = "") -> None:
    if not content and not ctx.message.attachments:
        raise commands.UserInputError

    files = [await attachment.to_file() for attachment in ctx.message.attachments]
    with contextlib.suppress(discord.HTTPException):
        await ctx.message.delete()

    await ctx.send(content, files=files, reference=ctx.message.reference)
