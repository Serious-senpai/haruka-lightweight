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
    description="Compile and run a C++ program. You can attach a text file to pipe to stdin.",
    usage="cppeval <code> <attachment: input>",
    hidden=True,
)
@commands.is_owner()
@commands.max_concurrency(1)
async def _handler(ctx: Context, *, code: str) -> None:
    code = code.strip("`")
    code = code.removeprefix("cpp")
    code = code.removeprefix("c")

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
            await process.communicate(code.encode("utf-8"))

    if process.returncode != 0:
        await ctx.send(
            f"Compiler completed with exit code {process.returncode} after {utils.format(measure.result)}",
            file=discord.File(C_EVAL_PATH),
        )
    else:
        with open(C_EVAL_PATH, "w", encoding="utf-8") as writer:
            try:
                attachment = ctx.message.attachments[0]
            except IndexError:
                process = await asyncio.create_subprocess_exec(C_EVAL_BINARY_PATH, stdout=writer, stderr=writer)
                with utils.TimingContextManager() as measure:
                    await process.communicate()
            else:
                async with interface.session.get(attachment.url) as request:
                    data = await request.read()

                process = await asyncio.create_subprocess_exec(C_EVAL_BINARY_PATH, stdin=asyncio.subprocess.PIPE, stdout=writer, stderr=writer)
                with utils.TimingContextManager() as measure:
                    await process.communicate(data)

        await ctx.send(
            f"Program completed with exit code {process.returncode} after {utils.format(measure.result)}",
            file=discord.File(C_EVAL_PATH),
        )
