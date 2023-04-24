from __future__ import annotations

from typing import TYPE_CHECKING

from discord import app_commands

if TYPE_CHECKING:
    from .haruka import Haruka


class SlashCommandTree(app_commands.CommandTree):

    if TYPE_CHECKING:
        client: Haruka

    async def on_error(self) -> None:
        await super().on_error()
        await self.client.report("An error has just occured and was handled by `SlashCommandTree.on_error`", send_state=False)
