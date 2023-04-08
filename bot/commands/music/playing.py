from __future__ import annotations

from customs import Context
from shared import interface


@interface.command(
    name="playing",
    brief="music.playing",
    description="Display the current playing source",
)
async def _playing_cmd(ctx: Context) -> None:
    try:
        await ctx.send(
            f"Currently playing in {ctx.voice_client.channel.mention}",
            embed=await ctx.voice_client.playing.create_embed(ctx.bot),
        )
    except AttributeError:
        await ctx.send("No audio player is currently playing!")
