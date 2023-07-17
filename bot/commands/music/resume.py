from __future__ import annotations

from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="resume",
    brief="music.resume",
    description="Resume the current audio player",
    transferable=True,
)
@commands.guild_only()
@commands.max_concurrency(1, commands.BucketType.guild, wait=True)
async def _handler(ctx: Context) -> None:
    try:
        await ctx.voice_client.resume()
        await ctx.send("Resumed audio.")
    except AttributeError:
        if not await ctx.bot.transfer(ctx):
            await ctx.send("No audio player is currently playing!")
