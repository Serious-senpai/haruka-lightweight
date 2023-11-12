from __future__ import annotations

import asyncio
from os import path

import discord
from discord.ext import commands

import global_utils
from customs import Context
from environment import BASH_PATH
from shared import interface


@interface.command(
    name="bash",
    aliases=["sh", "ssh"],
    brief="dev.bash",
    description="Execute a bash command",
    usage="{prefix}bash <command>",
    hidden=True,
)
@commands.is_owner()
@commands.max_concurrency(1)
async def handler(ctx: Context, *, cmd: str) -> None:
    with open(BASH_PATH, "w", encoding="utf-8") as writer:
        with global_utils.TimingContextManager() as measure:
            process = await asyncio.create_subprocess_shell(cmd, stdout=writer, stderr=writer)
            try:
                await process.communicate()
            except asyncio.TimeoutError:
                process.kill()

    header = f"Process completed with return code {process.returncode} after {global_utils.format(measure.result)}."
    if path.getsize(BASH_PATH) == 0:
        await ctx.send(header)
    else:
        with open(BASH_PATH, "r", encoding="utf-8") as file:
            content = file.read()

        if len(content) > 1800:
            await ctx.send(header, file=discord.File(BASH_PATH))
        else:
            await ctx.send(f"{header}\n```\n{content}\n```")
