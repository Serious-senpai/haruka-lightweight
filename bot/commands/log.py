from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from environment import LOG_PATH
from shared import interface
if TYPE_CHECKING:
    from haruka import Haruka


@interface.command(
    name="log",
    brief="dev.log",
    description="Send the log file to the current channel",
    hidden=True,
)
@commands.is_owner()
async def _log_cmd(ctx: commands.Context[Haruka]) -> None:
    await ctx.send(embed=ctx.bot.display_status, file=discord.File(LOG_PATH))
