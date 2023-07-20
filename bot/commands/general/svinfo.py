from __future__ import annotations

from discord import app_commands
from discord.ext import commands

from customs import Context, Interaction
from lib import info
from shared import interface


@interface.command(
    name="svinfo",
    brief="general.svinfo",
    description="Retrieve information about this server",
)
@commands.guild_only()
async def handler_a(ctx: Context) -> None:
    await ctx.send(embed=info.guild_info(ctx.guild))


@interface.slash(
    name="svinfo",
    description="Retrieve information about this server",
)
@app_commands.guild_only()
async def handler_b(interaction: Interaction) -> None:
    await interaction.response.send_message(embed=info.guild_info(interaction.guild))
