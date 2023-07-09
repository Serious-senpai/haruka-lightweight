from __future__ import annotations

from typing import Tuple

import discord
from discord import app_commands
from discord.ext import commands

from customs import Context, Interaction
from shared import interface
from lib.classifier import LearnerManager


async def process_attachment(attachment: discord.Attachment, /) -> Tuple[str, float]:
    data = await attachment.read()
    result, index, prob = await LearnerManager.load_and_predict("miku-or-fubuki", item=data)
    confidence = prob[index]

    return result, confidence


@interface.command(
    name="mof",
    brief="general.mof",
    description="Miku or Fubuki?",
    usage="{prefix}mof <image>",
)
@commands.cooldown(1, 5, commands.BucketType.user)
async def _handler(ctx: Context) -> None:
    try:
        attachment = ctx.message.attachments[0]
    except IndexError:
        raise commands.UserInputError
    else:
        async with ctx.typing():
            result, confidence = await process_attachment(attachment)
            await ctx.send(f"Result: `{result}` (confidence {100 * confidence:.2f}%)")


@interface.slash(
    name="mof",
    description="Miku or Fubuki?",
)
@app_commands.describe(image="An image of Hatsune Miku or Shirakami Fubuki")
async def _handler(interaction: Interaction, image: discord.Attachment) -> None:
    await interaction.response.defer()

    result, confidence = await process_attachment(image)
    await interaction.followup.send(f"Result: `{result}` (confidence {100 * confidence:.2f}%)")
