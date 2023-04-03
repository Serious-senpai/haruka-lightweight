from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from shared import interface
if TYPE_CHECKING:
    from haruka import Haruka


@interface.command(
    name="sync",
    brief="dev.sync",
    description="Sync all slash commands to Discord server",
    hidden=True,
)
@commands.is_owner()
async def _sync_cmd(ctx: commands.Context[Haruka]) -> None:
    commands = await ctx.bot.tree.sync()
    content = f"Synced {len(commands)} command"
    if len(commands) != 1:
        content += "s"

    await ctx.send(content)
