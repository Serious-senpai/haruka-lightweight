from __future__ import annotations

import discord
from discord.ext import commands

import emoji_ui
from customs import Context
from lib import zerochan
from shared import interface


@interface.command(
    name="zerochan",
    aliases=["zero"],
    brief="search.zerochan",
    description="Search zerochan for images",
    usage="{prefix}zerochan <query>",
)
@commands.cooldown(1, 10, commands.BucketType.user)
async def handler(ctx: Context, *, query: str) -> None:
    async with ctx.typing():
        urls = await zerochan.search(query, session=interface.session)

        if not urls:
            await ctx.send("No matching result was found.")
            return None

        no_results = len(urls)
        embeds = []
        for index, url in enumerate(urls):
            embed = discord.Embed()
            embed.set_author(
                name=f"Zerochan search for {query}",
                icon_url=ctx.bot.user.display_avatar.url,
            )
            embed.set_image(url=url)
            embed.set_footer(text=f"Result {index + 1}/{no_results}")
            embeds.append(embed)

    display = emoji_ui.NavigatorPagination(ctx.bot, embeds)
    await display.send(ctx.channel)
