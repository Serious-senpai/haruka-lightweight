from __future__ import annotations

from typing import List

import discord
from discord.ext import commands

import emoji_ui
from customs import Context
from core import saucenao
from shared import interface


async def _send_single_sauce(ctx: Context, image_url: str) -> None:
    results = await saucenao.SauceResult.get_sauce(image_url, session=ctx.bot.session)
    if not results:
        await ctx.send("Cannot find the image sauce!")
    else:
        total = len(results)
        embeds = []
        for index, result in enumerate(results):
            embed = result.create_embed()
            embed.set_author(
                name="Image search result",
                icon_url=ctx.bot.user.display_avatar.url,
            )
            embed.set_footer(text=f"Displaying result {index + 1}/{total}")
            embeds.append(embed)

        display = emoji_ui.NavigatorPagination(ctx.bot, embeds)
        await display.send(ctx.channel)


@interface.command(
    name="sauce",
    brief="search.sauce",
    description="Find the image source with saucenao.",
    usage="{prefix}sauce <image URL(s)>\n{prefix}sauce <attachment(s)>",
)
@commands.cooldown(1, 5, commands.BucketType.user)
async def handler(ctx: Context, *image_urls: str) -> None:
    urls = list(image_urls)
    for attachment in ctx.message.attachments:
        urls.append(attachment.url)

    total = len(urls)
    if total == 0:
        raise commands.UserInputError

    if total == 1:
        await _send_single_sauce(ctx, urls[0])
    else:
        embeds: List[discord.Embed] = []
        breakpoints: List[int] = []
        for index, url in enumerate(urls):
            results = await saucenao.SauceResult.get_sauce(url, session=interface.session)
            result_total = len(results)
            if result_total > 0:
                breakpoints.append(len(embeds))

            for result_index, result in enumerate(results):
                embed = result.create_embed()
                embed.set_author(
                    name="Image search result",
                    icon_url=ctx.bot.user.display_avatar.url,
                )
                embed.set_footer(text=f"Displaying result {result_index + 1}/{result_total} (image {index + 1}/{total})")
                embeds.append(embed)

        if embeds:
            display = emoji_ui.StackedNavigatorPagination(ctx.bot, embeds, breakpoints)
            await display.send(ctx.channel)
        else:
            await ctx.send("Cannot find the sauce for any of the images provided!")
