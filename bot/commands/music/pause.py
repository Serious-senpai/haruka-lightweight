from __future__ import annotations

from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="pause",
    brief="music.pause",
    description="Pause the current audio player",
)
@commands.guild_only()
@commands.max_concurrency(1, commands.BucketType.guild, wait=True)
async def _handler(ctx: Context) -> None:
    try:
        await ctx.voice_client.pause()
        await ctx.send("Paused audio.")
    except AttributeError:
        await ctx.send("No audio player is currently playing!")
