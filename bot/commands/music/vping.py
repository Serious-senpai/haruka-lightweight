from __future__ import annotations

from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="vping",
    brief="general.vping",
    description="Measure the voice websocket latency to the current server",
    transferable=True,
)
@commands.guild_only()
async def handler(ctx: Context) -> None:
    try:
        await ctx.send(f"WebSocket latency `{1000 * ctx.voice_client.latency:.2f} ms` to `{ctx.voice_client.endpoint}`")
    except AttributeError:
        if not await interface.transfer(ctx):
            await ctx.send("No audio player is currently playing!")
