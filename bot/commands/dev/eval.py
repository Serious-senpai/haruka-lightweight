from __future__ import annotations

import asyncio
import contextlib
import textwrap
import traceback
from os import path

import discord
from discord.ext import commands

import global_utils
from customs import Context
from environment import EVAL_PATH, EVAL_TASK_ATTR
from shared import interface


INDENT = " " * 4


@interface.command(
    name="eval",
    aliases=["exec"],
    brief="dev.eval",
    description="Evaluate a Python code",
    usage="{prefix}eval <code>",
    hidden=True,
)
@commands.is_owner()
@commands.max_concurrency(1)
async def handler(ctx: Context, *, code: str) -> None:
    if getattr(ctx.bot, EVAL_TASK_ATTR, None) is not None:
        await ctx.send("Another task is running, please wait for it to terminate!")
        return

    code = code.strip("`")
    code = code.removeprefix("python")
    code = code.removeprefix("py")
    code = textwrap.indent(code, INDENT)
    code = code.strip("\n")
    code = f"async def func():\n" + code

    env = {
        "bot": ctx.bot,
        "ctx": ctx,
    }
    try:
        exec(code, env, env)
    except BaseException:
        await ctx.send("Cannot create coroutine\n```\n" + traceback.format_exc() + "\n```")
        return

    with open(EVAL_PATH, "w", encoding="utf-8") as writer:
        with contextlib.redirect_stdout(writer):
            with global_utils.TimingContextManager() as measure:
                task = asyncio.create_task(env["func"]())
                setattr(ctx.bot, EVAL_TASK_ATTR, task)

                try:
                    await task
                except BaseException:
                    writer.write(traceback.format_exc())
                finally:
                    setattr(ctx.bot, EVAL_TASK_ATTR, None)

    header = f"Process completed after {global_utils.format(measure.result)}."
    if path.getsize(EVAL_PATH) == 0:
        await ctx.send(header)
    else:
        with open(EVAL_PATH, "r", encoding="utf-8") as file:
            content = file.read()

        if len(content) > 1800:
            await ctx.send(header, file=discord.File(EVAL_PATH))
        else:
            await ctx.send(f"{header}\n```\n{content}\n```")
