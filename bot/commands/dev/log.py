from __future__ import annotations


import discord
from discord.ext import commands

from customs import Context
from environment import LOG_PATH
from shared import interface


@interface.command(
    name="log",
    brief="dev.log",
    description="Send the log file to the current channel",
    hidden=True,
)
@commands.is_owner()
async def handler(ctx: Context) -> None:
    interface.flush_logs()
    await ctx.send(embed=ctx.bot.display_status, file=discord.File(LOG_PATH))
