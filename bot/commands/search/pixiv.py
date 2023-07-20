import re
from typing import Optional

import discord
from discord import app_commands

from customs import Interaction
from lib import pixiv
from shared import interface


URL_PATTERN = re.compile(r"^https:\/\/(?:www\.)?pixiv\.net(?:\/en)?\/artworks\/(\d+)(?:\/.*?)?$")
ID_PATTERN = re.compile(r"^(\d+)$")


@interface.slash(
    name="pixiv",
    description="Display a Pixiv artwork",
)
@app_commands.describe(identifier="The artwork URL or ID", display_url="The URL to the image to display if auto-fetching fails")
async def handler(interaction: Interaction, identifier: str, display_url: Optional[str]) -> None:
    await interaction.response.defer()
    for pattern in (URL_PATTERN, ID_PATTERN):
        match = pattern.fullmatch(identifier)
        if match is not None:
            id = match.group(1)
            artwork = await pixiv.Artwork.from_id(int(id), fallback_image_url=display_url)
            if artwork is None:
                await interaction.followup.send(f"Cannot find any artworks from the ID `{id}`")
            else:
                if artwork.is_nsfw and not isinstance(interaction.channel, discord.DMChannel):
                    channel = interaction.channel
                    is_nsfw = getattr(channel, "is_nsfw", None)
                    if is_nsfw is None or not is_nsfw():
                        await interaction.followup.send("🔞 This artwork contains NSFW content and cannot be displayed in this channel!")
                        return

                embed, file = await artwork.prepare_message(interaction.client)
                if file is None:
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(embed=embed, file=file)

            return

    await interaction.followup.send("Invalid artwork identifier")
