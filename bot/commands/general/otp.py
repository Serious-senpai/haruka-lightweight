from __future__ import annotations

import discord

from customs import Interaction
from environment import HOST
from shared import interface
from server.verification import otp_cache


@interface.slash(
    name="otp",
    description="Generate an OTP (One-Time Password) for your account",
)
async def _handler(interaction: Interaction) -> None:
    otp = otp_cache.add_key(interaction.user)

    embed = discord.Embed(description=f"Your OTP is `{otp}`\nUse this OTP to login [here]({HOST})")
    embed.set_author(name=interaction.user, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.set_footer(text="OTP is valid for 5 minutes")

    await interaction.response.send_message(embed=embed, ephemeral=True)
