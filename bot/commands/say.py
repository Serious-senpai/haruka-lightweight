from __future__ import annotations

from discord import app_commands
from discord.ext import commands

from customs import Context, Interaction
from shared import interface


@interface.command(
    name="say",
    brief="general.say",
    description="Make the bot say something",
    usage="say <content>",
)
async def _handler(ctx: Context, *, content: str = "") -> None:
    if not content and not ctx.message.attachments:
        raise commands.UserInputError

    await ctx.send(content, files=[await attachment.to_file() for attachment in ctx.message.attachments], reference=ctx.message.reference)


@interface.slash(
    name="say",
    description="Make the bot say something, can be used to send animated emojis",
)
@app_commands.describe(content="The message to repeat")
async def _say_slash(interaction: Interaction, content: str) -> None:
    await interaction.response.send_message(content)
