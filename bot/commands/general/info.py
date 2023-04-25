from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from customs import Context, Interaction
from lib import info
from shared import interface


@interface.command(
    name="info",
    brief="general.info",
    description="View a Discord user's information",
    usage="info <user | default: yourself>",
)
async def _handler(ctx: Context, user: discord.User = commands.Author) -> None:
    await ctx.send(embed=info.user_info(user))


@interface.slash(
    name="info",
    description="View a Discord user's information",
)
@app_commands.describe(user="The user to retrieve the information")
async def _handler(interaction: Interaction, user: discord.User) -> None:
    await interaction.response.send_message(embed=info.user_info(user))
