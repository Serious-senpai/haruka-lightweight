from __future__ import annotations

import asyncio
import io
from typing import Optional

import aiohttp
import discord
from discord.ext import commands

from customs import Context
from shared import interface


@interface.command(
    name="send",
    brief="dev.send",
    description="Download data from provided URL(s) and send them to the current channel. If any of the given URL(s) contain data exceeding the file size limit, the URL will be sent instead.",
    usage="{prefix}send <URL(s)>",
    hidden=True,
)
@commands.is_owner()
async def handler(ctx: Context, *urls: str) -> None:
    if not urls:
        raise commands.UserInputError

    limit_size = 8 * 1024 * 1024
    if ctx.guild is not None:
        limit_size = ctx.guild.filesize_limit

    for url in urls:
        data: Optional[bytes] = None
        try:
            async with interface.session.get(url) as response:
                response.raise_for_status()

                filename = response.url.name
                data = await response.content.readexactly(limit_size)

        except (asyncio.TimeoutError, asyncio.IncompleteReadError, aiohttp.ClientError) as exc:
            if isinstance(exc, asyncio.IncompleteReadError):
                data = exc.partial

        finally:
            if data is not None:
                await ctx.send(file=discord.File(io.BytesIO(data), filename))
            else:
                await ctx.send(url)
