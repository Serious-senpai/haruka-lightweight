from __future__ import annotations

import asyncio
from typing import Optional

from discord.ext import commands

from customs import Context
from environment import EVAL_TASK_ATTR
from shared import interface


@interface.command(
    name="cancel",
    brief="dev.cancel",
    description="Cancel the running `eval` task",
    transferable=True,
    hidden=True,
)
@commands.is_owner()
async def handler(ctx: Context) -> None:
    task: Optional[asyncio.Task] = getattr(ctx.bot, EVAL_TASK_ATTR, None)
    if task is None:
        if not await interface.transfer(ctx):
            await ctx.send("No `eval` task is running!")

    else:
        task.cancel()
        await ctx.send("Task cancelled!")
