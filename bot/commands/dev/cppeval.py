from __future__ import annotations

import asyncio
import contextlib
import os

import discord
from discord.ext import commands

import utils
from customs import Context
from environment import C_EVAL_PATH, C_EVAL_BINARY_PATH
from shared import interface


@interface.command(
    name="cppeval",
    aliases=["cppexec"],
    brief="dev.cppeval",
    description="Attach a C++ source file, compile and run.\nProgram stdin is read from the text message.",
    usage="{prefix}cppeval <stdin> <attachment>",
    hidden=True,
)
@commands.is_owner()
@commands.max_concurrency(1)
async def _handler(ctx: Context, *, input: str) -> None:
    try:
        async with interface.session.get(ctx.message.attachments[0].url) as request:
            code_data = await request.read()
    except IndexError:
        await ctx.send("Please attach a C++ source file")
    else:
        input = input.strip("`")
        with contextlib.suppress(FileNotFoundError):
            os.remove(C_EVAL_BINARY_PATH)

        with open(C_EVAL_PATH, "w", encoding="utf-8") as writer:
            process = await asyncio.create_subprocess_exec(
                "g++",
                "-std=c++2a",
                "-Wall",
                "-o", C_EVAL_BINARY_PATH,
                "-x", "c++",
                "-",
                stdin=asyncio.subprocess.PIPE,
                stdout=writer,
                stderr=writer,
            )
            with utils.TimingContextManager() as measure:
                await process.communicate(code_data)

        if process.returncode != 0:
            await ctx.send(
                f"Compiler failed with exit code {process.returncode} after {utils.format(measure.result)}",
                file=discord.File(C_EVAL_PATH),
            )
        else:
            with open(C_EVAL_PATH, "w", encoding="utf-8") as writer:
                process = await asyncio.create_subprocess_exec(
                    C_EVAL_BINARY_PATH,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=writer,
                    stderr=writer,
                )
                with utils.TimingContextManager() as measure:
                    await process.communicate(input.encode("utf-8"))

            await ctx.send(
                f"Program completed with exit code {process.returncode} after {utils.format(measure.result)}",
                file=discord.File(C_EVAL_PATH),
            )
