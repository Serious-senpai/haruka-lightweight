from __future__ import annotations

import asyncio
from os import path
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

import utils
from environment import BASH_PATH
from shared import interface
if TYPE_CHECKING:
    from haruka import Haruka


@interface.command(
    name="bash",
    aliases=["sh", "ssh"],
    brief="dev.bash",
    description="Execute a bash command",
    usage="bash <command>",
    hidden=True,
)
@commands.is_owner()
@commands.max_concurrency(1)
async def _bash_cmd(ctx: commands.Context[Haruka], *, cmd: str):
    with open(BASH_PATH, "w", encoding="utf-8") as writer:
        with utils.TimingContextManager() as measure:
            try:
                process = await asyncio.create_subprocess_shell(cmd, stdout=writer, stderr=writer)
                await process.communicate()
            except asyncio.TimeoutError:
                process.kill()

    await ctx.send(
        f"Process completed with return code {process.returncode} after {utils.format(measure.result)}",
        file=discord.File(BASH_PATH) if path.getsize(BASH_PATH) > 0 else None,
    )
