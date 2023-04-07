from __future__ import annotations

import discord
from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="ava",
    brief="general.ava",
    description="View someone's avatar",
    usage="ava <user | default: yourself>",
)
async def _ava_cmd(ctx: Context, user: discord.User = commands.Author) -> None:
    if user.avatar is None:
        await ctx.send("This user hasn't set an avatar yet!")
    else:
        embed = discord.Embed()
        embed.set_image(url=user.avatar.url)
        embed.set_author(
            name=f"This is {user.name}'s avatar",
            icon_url=ctx.bot.user.avatar.url,
        )
        await ctx.send(embed=embed)
