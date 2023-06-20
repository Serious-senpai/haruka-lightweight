from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from customs import Context, Interaction
from shared import interface


@interface.command(
    name="ava",
    brief="general.ava",
    description="View someone's avatar",
    usage="ava <user | default: yourself>",
)
async def _handler(ctx: Context, user: discord.User = commands.Author) -> None:
    embed = discord.Embed()
    embed.set_image(url=user.display_avatar.url)
    embed.set_author(
        name=f"This is {user.display_name}'s avatar",
        icon_url=ctx.bot.user.display_avatar.url,
    )
    await ctx.send(embed=embed)


@interface.slash(
    name="ava",
    description="View someone's avatar",
)
@app_commands.describe(user="The user to retrieve the avatar")
async def _handler(interaction: Interaction, user: discord.User) -> None:
    embed = discord.Embed()
    embed.set_image(url=user.display_avatar.url)
    embed.set_author(
        name=f"This is {user.display_name}'s avatar",
        icon_url=interaction.client.user.display_avatar.url,
    )
    await interaction.response.send_message(embed=embed)
