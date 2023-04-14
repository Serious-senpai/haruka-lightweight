from __future__ import annotations

from customs import Context
from shared import interface


@interface.command(
    name="playing",
    brief="music.playing",
    description="Display the current playing source",
)
async def _handler(ctx: Context) -> None:
    try:
        embed = await ctx.voice_client.playing.create_embed(ctx.bot)
        ctx.voice_client.append_state(embed)
        await ctx.send(f"Currently playing in {ctx.voice_client.channel.mention}", embed=embed)
    except AttributeError:
        await ctx.send("No audio player is currently playing!")
