from __future__ import annotations

from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="repeat",
    brief="music.repeat",
    description="Toggle the REPEAT mode",
    transferable=True,
)
@commands.guild_only()
@commands.max_concurrency(1, commands.BucketType.guild, wait=True)
async def handler(ctx: Context) -> None:
    try:
        ctx.voice_client.switch_repeat()
        if ctx.voice_client.repeat:
            await ctx.send("`REPEAT` mode is on. The current song will be played repeatedly.")
        else:
            await ctx.send("`REPEAT` mode is off. All songs will be played as normal.")

    except AttributeError:
        if not await interface.transfer(ctx):
            await ctx.send("No audio player is currently playing!")
