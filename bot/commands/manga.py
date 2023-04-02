from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

import emoji_ui
from lib import mal
from shared import interface
if TYPE_CHECKING:
    from haruka import Haruka


@interface.command(
    name="manga",
    brief="search.manga",
    description="Search for an manga in the MyAnimeList database",
    usage="manga <query>"
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _manga_cmd(ctx: commands.Context[Haruka], *, query: str) -> None:
    if len(query) < 3:
        await ctx.send(f"Search query must have at least 3 characters")
        return

    results = await mal.MALSearchResult.search(query, criteria="manga", session=interface.session)

    if not results:
        return await ctx.send("No matching result was found.")

    desc = "\n".join(f"{emoji_ui.CHOICES[index]} {result.title}" for index, result in enumerate(results))
    embed = discord.Embed(
        title=f"Search results for {query}",
        description=escape(desc),
    )
    message = await ctx.send(embed=embed)

    display = emoji_ui.SelectMenu(ctx.bot, message, len(results))
    choice = await display.listen(ctx.author.id)

    if choice is not None:
        manga = await mal.Manga.get(results[choice].id, session=interface.session)
        if manga:

            if not manga.is_safe() and not getattr(ctx.channel, "nsfw", False):
                return await ctx.send("🔞 This manga contains NSFW content and cannot be displayed in this channel!")

            embed = manga.create_embed()
            embed.set_author(
                name=f"{ctx.author.name}'s request",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            )
            await ctx.send(embed=embed)
        else:
            return await ctx.send("An unexpected error has occurred.")
