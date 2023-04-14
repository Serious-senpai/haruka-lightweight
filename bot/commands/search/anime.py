from __future__ import annotations

import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

import emoji_ui
from customs import Context
from lib import mal
from shared import interface


@interface.command(
    name="anime",
    brief="search.anime",
    description="Search for an anime in the MyAnimeList database",
    usage="anime <query>"
)
@commands.cooldown(1, 3, commands.BucketType.user)
async def _handler(ctx: Context, *, query: str) -> None:
    if len(query) < 3:
        await ctx.send(f"Search query must have at least 3 characters")
        return

    results = await mal.MALSearchResult.search(query, criteria="anime", session=interface.session)

    if not results:
        await ctx.send("No matching result was found.")
    else:
        desc = "\n".join(f"{emoji_ui.CHOICES[index]} {result.title}" for index, result in enumerate(results))
        embed = discord.Embed(
            title=f"Search results for {query}",
            description=escape(desc),
        )
        message = await ctx.send(embed=embed)

        display = emoji_ui.SelectMenu(ctx.bot, message, len(results))
        choice = await display.listen(ctx.author.id)

        if choice is not None:
            anime = await mal.Anime.get(results[choice].id, session=interface.session)
            if anime:
                if not anime.is_safe() and not getattr(ctx.channel, "nsfw", False):
                    await ctx.send("🔞 This anime contains NSFW content and cannot be displayed in this channel!")
                else:
                    embed = anime.create_embed()
                    embed.set_author(
                        name=f"{ctx.author.name}'s request",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
                    )
                    await ctx.send(embed=embed)
            else:
                await ctx.send("An unexpected error has occurred.")
