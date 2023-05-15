from __future__ import annotations

import utils
from customs import Context
from shared import interface


@interface.command(
    name="rerun",
    brief="general.rerun",
    description="Rerun a command message by replying to it",
    usage="rerun",
)
async def _handler(ctx: Context) -> None:
    message = await utils.get_reply(ctx.message)
    if message is None:
        await ctx.send("You can invoke this command by replying to a command message.")
    else:
        await ctx.bot.process_commands(message)
