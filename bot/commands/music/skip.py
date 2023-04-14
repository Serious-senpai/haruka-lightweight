from __future__ import annotations

from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="skip",
    brief="music.skip",
    description="Skip to the next track in the playlist",
)
@commands.cooldown(1, 3, commands.BucketType.guild)
async def _handler(ctx: Context) -> None:
    try:
        await ctx.voice_client.skip()
    except AttributeError:
        await ctx.send("No audio player is currently playing!")
