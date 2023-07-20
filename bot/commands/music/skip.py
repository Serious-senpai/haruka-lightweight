from __future__ import annotations

from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="skip",
    brief="music.skip",
    description="Skip to the next track in the playlist",
    transferable=True,
)
@commands.guild_only()
@commands.cooldown(1, 3, commands.BucketType.guild)
async def handler(ctx: Context) -> None:
    try:
        await ctx.voice_client.skip()
        await ctx.send("Skipped to the next track!")
    except AttributeError:
        if not await interface.transfer(ctx):
            await ctx.send("No audio player is currently playing!")
