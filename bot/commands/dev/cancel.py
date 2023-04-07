from __future__ import annotations

from discord.ext import commands

from customs import Context
from environment import EVAL_TASK_ATTR
from shared import interface


@interface.command(
    name="cancel",
    brief="dev.cancel",
    description="Cancel the running `eval` task",
    hidden=True,
)
@commands.is_owner()
async def _cancel_cmd(ctx: Context) -> None:
    task = getattr(ctx.bot, EVAL_TASK_ATTR, None)
    if task is None:
        await ctx.send("No `eval` task is running!")
    else:
        task.cancel()
        await ctx.send("Task cancelled!")
