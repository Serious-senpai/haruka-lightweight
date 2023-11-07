from __future__ import annotations

import discord
from discord.ext import commands

from customs import Context
from core import images
from shared import interface


async def list_categories() -> str:
    display = ", ".join(f"`{category}`" for category in await images.list_categories(sfw=False))
    return f"Supported NSFW categories: {display}"


@interface.command(
    name="nsfw",
    brief="search.nsfw",
    description="Send a random NSFW image.",
    usage="{prefix}nsfw <category>",
)
@interface.append_description(list_categories)
@commands.is_nsfw()
@commands.cooldown(1, 2, commands.BucketType.user)
async def handler(ctx: Context, *, category: str) -> None:
    url = await images.get_image(category, sfw=False)
    if url is None:
        await ctx.send(await images.unknown_category_message(category, sfw=False))
    else:
        embed = discord.Embed()
        embed.set_author(
            name=f"{ctx.author.name}, this is an image of {category}!",
            icon_url=ctx.bot.user.display_avatar.url,
        )
        embed.set_image(url=url)

        await ctx.send(embed=embed)
