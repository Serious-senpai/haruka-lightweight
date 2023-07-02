from __future__ import annotations

import discord
from discord.ext import commands

from customs import Context
from lib import wows_renderer
from shared import interface


@interface.command(
    name="render",
    brief="general.render",
    description="Render a WoWs replay",
    usage="render <replay file>"
)
@commands.cooldown(1, 90, commands.BucketType.user)
async def _handler(ctx: Context) -> None:
    try:
        attachment = ctx.message.attachments[0]
    except IndexError:
        raise commands.UserInputError
    else:
        async with ctx.typing():
            path, stderr = await wows_renderer.render(await attachment.read(), id=ctx.message.id, log_func=interface.log)

            try:
                try:
                    await ctx.reply(file=discord.File(path))
                except discord.HTTPException:
                    await ctx.send(file=discord.File(path))
            except FileNotFoundError:
                await ctx.send(f"Cannot render replay file!\n```{stderr}```")
