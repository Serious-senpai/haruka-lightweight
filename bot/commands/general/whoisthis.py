from __future__ import annotations

import io
from typing import Optional, Tuple

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from customs import Context, Interaction
from shared import interface
from core.classifier import LearnerManager


async def process_url(url: str, /) -> Tuple[str, float, bytes]:
    async with interface.session.get(url) as response:
        response.raise_for_status()
        data = await response.read()

    result, index, prob = await LearnerManager.load_and_predict("anime-girl", item=data)
    confidence = prob[index]

    return result, confidence, data


@interface.command(
    name="whoisthis",
    aliases=["who"],
    brief="general.whoisthis",
    description="Classify an image of an anime girl. Only few characters are supported.",
    usage="{prefix}whoisthis <url or image>",
)
@commands.cooldown(1, 5, commands.BucketType.user)
async def handler_a(ctx: Context, *, url: Optional[str] = None) -> None:
    try:
        attachment = ctx.message.attachments[0]
    except IndexError:
        pass
    else:
        url = attachment.url

    if url is None:
        raise commands.UserInputError

    async with ctx.typing():
        try:
            result, confidence, image_data = await process_url(url)
        except aiohttp.ClientError:
            await ctx.send("Error! Couldn't download the image!")
        else:
            embed = discord.Embed(description=f"Result: `{result}` (confidence {100 * confidence:.2f}%)")
            embed.set_author(name="Prediction of the provided image", icon_url=ctx.bot.user.display_avatar.url)
            embed.set_image(url="attachment://image.png")
            await ctx.send(embed=embed, file=discord.File(io.BytesIO(image_data), filename="image.png"))


@interface.slash(
    name="whoisthis",
    description="Classify an image of an anime girl. Only few characters are supported",
)
@app_commands.describe(
    image="The image as an attachment",
    url="The URL to an image",
)
async def handler_b(interaction: Interaction, image: Optional[discord.Attachment] = None, url: Optional[str] = None) -> None:
    await interaction.response.defer()

    if image is not None:
        url = image.url

    if url is None:
        await interaction.followup.send("Please provide at least one of the parameters!")
        return

    try:
        result, confidence, image_data = await process_url(url)
    except aiohttp.ClientError:
        await interaction.followup.send("Error! Couldn't download the image!")
    else:
        embed = discord.Embed(description=f"Result: `{result}` (confidence {100 * confidence:.2f}%)")
        embed.set_author(name="Prediction of the provided image", icon_url=interaction.client.user.display_avatar.url)
        embed.set_image(url="attachment://image.png")
        await interaction.followup.send(embed=embed, file=discord.File(io.BytesIO(image_data), filename="image.png"))
