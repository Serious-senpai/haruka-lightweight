from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from shared import interface
if TYPE_CHECKING:
    from haruka import Haruka


@interface.command(
    name="say",
    brief="general.say",
    description="Make the bot say something",
)
async def _say_cmd(ctx: commands.Context[Haruka], *, content: str) -> None:
    await ctx.send(content, files=[await attachment.to_file() for attachment in ctx.message.attachments])


@interface.slash(
    name="say",
    description="Make the bot say something, can be used to send animated emojis",
)
@app_commands.describe(content="The message to repeat")
async def _say_slash(interaction: discord.Interaction[Haruka], content: str) -> None:
    await interaction.response.send_message(content)
