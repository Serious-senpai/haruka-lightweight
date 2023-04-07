from __future__ import annotations

import inspect
import io

import discord

from customs import Context
from shared import interface


@interface.command(
    name="source",
    brief="general.source",
    description="Get the source code of a command",
)
async def _source_cmd(ctx: Context, command_name: str) -> None:
    command_name = command_name.lower()
    command = ctx.bot.get_command(command_name)
    if command is None:
        await ctx.send(f"No command named `{command_name}` was found!")
    else:
        source = inspect.getsource(command.callback)
        data = io.StringIO(source)
        await ctx.send("This is the source code", file=discord.File(data, "source.py"))
