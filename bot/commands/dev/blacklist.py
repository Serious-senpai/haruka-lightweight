from __future__ import annotations

import discord
from discord.ext import commands

from customs import Context
from shared import interface


@interface.group(
    name="blacklist",
    brief="dev.blacklist",
    description="Operations on the blacklist",
    hidden=True,
    invoke_without_command=True,
)
@commands.is_owner()
async def handler(ctx: Context) -> None:
    async with interface.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM blacklist")
            rows = await cursor.fetchall()

    count = len(set(row[0] for row in rows))
    if count == 1:
        await ctx.send("There is 1 user in the blacklist.")
    else:
        await ctx.send(f"There are `{count}` users in the blacklist.")


@handler.command(
    name="add",
    brief="dev.blacklist_add",
    description="Add a user to the blacklist",
    hidden=True,
)
@commands.is_owner()
async def handler_add(ctx: Context, user: discord.User) -> None:
    async with interface.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute("INSERT INTO blacklist VALUES (?)", str(user.id))

    await ctx.send(f"Added `{user}` to the blacklist!")


@handler.command(
    name="remove",
    brief="dev.blacklist_remove",
    description="Remove a user from the blacklist",
    hidden=True,
)
@commands.is_owner()
async def handler_remove(ctx: Context, user: discord.User) -> None:
    async with interface.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute("DELETE FROM blacklist WHERE id = ?", str(user.id))

    await ctx.send(f"Removed `{user}` from the blacklist!")
