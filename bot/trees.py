from __future__ import annotations

from typing import TYPE_CHECKING

from discord import app_commands

from customs import Interaction
if TYPE_CHECKING:
    from .haruka import Haruka


class SlashCommandTree(app_commands.CommandTree):

    if TYPE_CHECKING:
        client: Haruka

    async def interaction_check(self, interaction: Interaction) -> bool:
        if await self.client.interface.is_in_blacklist(interaction.user.id):
            await interaction.response.send_message("You are currently in the blacklist!", ephemeral=True)
            return False
        else:
            return True

    async def on_error(self, interaction: Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CheckFailure):
            return

        await super().on_error(interaction, error)
        await self.client.report("An error has just occured and was handled by `SlashCommandTree.on_error`", send_state=False)
