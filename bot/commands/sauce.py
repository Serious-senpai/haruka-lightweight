from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

import emoji_ui
from lib import saucenao
from shared import interface
if TYPE_CHECKING:
    from haruka import Haruka


async def _send_single_sauce(bot: Haruka, target: discord.abc.Messageable, image_url: str) -> None:
    results = await saucenao.SauceResult.get_sauce(image_url, session=bot.session)
    if not results:
        await target.send("Cannot find the image sauce!")
    else:
        total = len(results)
        embeds = []
        for index, result in enumerate(results):
            embed = result.create_embed()
            embed.set_author(
                name="Image search result",
                icon_url=bot.user.avatar.url,
            )
            embed.set_footer(text=f"Displaying result {index + 1}/{total}")
            embeds.append(embed)

        display = emoji_ui.NavigatorPagination(bot, embeds)
        await display.send(target)


@interface.command(
    name="sauce",
    brief="search.sauce",
    description="Find the image source with saucenao.",
    usage="sauce <image URL(s)>\nsauce <attachment(s)>",
)
@commands.cooldown(1, 3, commands.BucketType.user)
async def _sauce_cmd(ctx: commands.Context[Haruka], *image_urls: str) -> None:
    urls = list(image_urls)
    for attachment in ctx.message.attachments:
        urls.append(attachment.url)

    total = len(urls)
    if total == 0:
        raise commands.UserInputError

    if total == 1:
        await _send_single_sauce(ctx.bot, ctx.channel, urls[0])
    else:
        embeds = []
        breakpoints = []
        for index, url in enumerate(urls):
            results = await saucenao.SauceResult.get_sauce(url, session=ctx.bot.session)
            result_total = len(results)
            if result_total > 0:
                breakpoints.append(len(embeds))

            for result_index, result in enumerate(results):
                embed = result.create_embed()
                embed.set_author(
                    name="Image search result",
                    icon_url=ctx.bot.user.avatar.url,
                )
                embed.set_footer(text=f"Displaying result {result_index + 1}/{result_total} (image {index + 1}/{total})")
                embeds.append(embed)

        if embeds:
            display = emoji_ui.StackedNavigatorPagination(ctx.bot, embeds, breakpoints)
            await display.send(ctx.channel)
        else:
            await ctx.send("Cannot find the sauce for any of the images provided!")
