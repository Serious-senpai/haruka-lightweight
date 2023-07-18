from __future__ import annotations

import utils
from customs import Context
from shared import interface


@interface.command(
    name="ping",
    brief="general.ping",
    description="Measure the bot's latency",
    parallel=True,
)
async def _handler(ctx: Context) -> None:
    with utils.TimingContextManager() as measure:
        message = await ctx.send("🏓 **Ping!**")

    await message.edit(content=f"🏓 **Pong!** in {utils.format(measure.result)} (websocket average latency {utils.format(ctx.bot.latency)})")
