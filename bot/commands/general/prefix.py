from __future__ import annotations

from typing import Optional

from discord.ext import commands

from customs import Context
from shared import interface
from global_utils import get_custom_prefix


@interface.command(
    name="prefix",
    brief="general.prefix",
    description="Change the bot's prefix within this server.",
    usage="{prefix}prefix <new prefix>"
)
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def handler(ctx: Context, prefix: Optional[str]) -> None:
    if prefix is None:
        custom_prefix = await get_custom_prefix(ctx.bot, ctx.message)
        if custom_prefix is None:
            await ctx.send("Cannot fetch the custom prefix now. Please try again later.")
        else:
            await ctx.send(f"The current prefix is `{custom_prefix}`")

    elif interface.pool is not None:
        async with interface.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("DELETE FROM prefix WHERE id = ?", str(ctx.guild.id))
                await cursor.execute("INSERT INTO prefix VALUES(?, ?)", str(ctx.guild.id), prefix)

        await ctx.send(f"Prefix has been set to `{prefix}`")

    else:
        await ctx.send("Operation failed. Please try again later!")
