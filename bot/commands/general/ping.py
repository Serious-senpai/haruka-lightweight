from __future__ import annotations

import global_utils
from customs import Context
from shared import interface


@interface.command(
    name="ping",
    brief="general.ping",
    description="Measure the bot's latency",
    parallel=True,
)
async def handler(ctx: Context) -> None:
    with global_utils.TimingContextManager() as measure:
        message = await ctx.send("🏓 **Ping!**")

    await message.edit(content=f"🏓 **Pong!** in {global_utils.format(measure.result)} (websocket average latency {global_utils.format(ctx.bot.latency)})")
