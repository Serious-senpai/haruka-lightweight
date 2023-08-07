from __future__ import annotations

import discord
from discord.ext import commands

from customs import Context
from lib import images
from shared import interface


async def list_categories() -> str:
    display = ", ".join(f"`{category}`" for category in await images.list_categories(sfw=True))
    return f"Supported SFW categories: {display}"


@interface.command(
    name="sfw",
    brief="search.sfw",
    description="Send a random SFW image.",
    usage="{prefix}sfw <category>",
)
@interface.append_description(list_categories)
@commands.cooldown(1, 2, commands.BucketType.user)
async def handler(ctx: Context, *, category: str) -> None:
    url = await images.get_image(category, sfw=True)
    if url is None:
        guess = await images.fuzzy_search(category, sfw=True)
        await ctx.send(f"Unsupported category: `{category}`. Did you mean `{guess}`?")
    else:
        embed = discord.Embed()
        embed.set_author(
            name=f"{ctx.author.name}, this is an image of {category}!",
            icon_url=ctx.bot.user.avatar.url,
        )
        embed.set_image(url=url)

        await ctx.send(embed=embed)
