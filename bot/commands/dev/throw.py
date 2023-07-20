from __future__ import annotations

import random

from discord.ext import commands

import utils
from customs import Context
from shared import interface


@interface.command(
    name="throw",
    aliases=["raise"],
    brief="dev.throw",
    description="Throw (raise) a random exception",
    hidden=True,
)
@commands.is_owner()
async def handler(ctx: Context) -> None:
    errors = tuple(utils.get_all_subclasses(BaseException))
    try:
        error_type = random.choice(errors)
        error = error_type()
    except TypeError:
        error = TypeError()

    await ctx.send(f"Throwing `{error.__class__.__name__}`")
    raise error
