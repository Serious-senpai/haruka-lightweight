from __future__ import annotations

from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="stop",
    brief="music.stop",
    description="Stop the current audio player",
    transferable=True,
)
@commands.guild_only()
@commands.max_concurrency(1, commands.BucketType.guild, wait=True)
async def handler(ctx: Context) -> None:
    try:
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect(force=True)
        await ctx.send("Stopped audio.")
    except AttributeError:
        if not await interface.transfer(ctx):
            await ctx.send("No audio player is currently playing!")
