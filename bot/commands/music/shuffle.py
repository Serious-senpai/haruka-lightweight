from __future__ import annotations

from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="shuffle",
    brief="music.shuffle",
    description="Toggle the SHUFFLE mode",
)
@commands.guild_only()
@commands.max_concurrency(1, commands.BucketType.guild, wait=True)
async def _handler(ctx: Context) -> None:
    try:
        ctx.voice_client.switch_shuffle()
        if ctx.voice_client.shuffle:
            await ctx.send("`SHUFFLE` mode is on. Songs will be played in random order.")
        else:
            await ctx.send("`SHUFFLE` mode is off. Songs will be played in the original order.")

    except AttributeError:
        await ctx.send("No audio player is currently playing!")
