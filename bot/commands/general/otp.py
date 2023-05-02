from __future__ import annotations

from customs import Interaction
from shared import interface
from server.verification import otp_cache


@interface.slash(
    name="otp",
    description="Generate an OTP (One-Time Password) for your account",
)
async def _handler(interaction: Interaction) -> None:
    otp = otp_cache.add_key(interaction.user)
    await interaction.response.send_message(f"Your OTP is `{otp}`. Please don't share this password to anyone else!", ephemeral=True)
