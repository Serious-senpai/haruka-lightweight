from __future__ import annotations

import asyncio
import io

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
            try:
                path = await asyncio.to_thread(
                    wows_renderer.render,
                    io.BytesIO(await attachment.read()),
                    ctx.message.id,
                )

            except Exception:
                try:
                    await ctx.reply("Cannot render replay file!")
                except discord.HTTPException:
                    await ctx.send("Cannot render replay file!")

            else:
                try:
                    await ctx.reply(file=discord.File(path))
                except discord.HTTPException:
                    await ctx.send(file=discord.File(path))
