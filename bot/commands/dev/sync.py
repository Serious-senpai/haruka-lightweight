from __future__ import annotations

from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="sync",
    brief="dev.sync",
    description="Sync all slash commands to Discord server",
    parallel=True,
    hidden=True,
)
@commands.is_owner()
async def handler(ctx: Context) -> None:
    commands = await ctx.bot.tree.sync()
    content = f"Synced {len(commands)} command"
    if len(commands) != 1:
        content += "s"

    await ctx.send(content)
