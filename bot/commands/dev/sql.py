from __future__ import annotations

import io

import discord
import pyodbc
from discord.ext import commands

import global_utils
from customs import Context
from shared import interface


@interface.command(
    name="sql",
    brief="dev.sql",
    description="Execute a SQL command",
    usage="{prefix}sql <command>",
    hidden=True,
)
@commands.is_owner()
async def handler(ctx: Context, *, cmd: str) -> None:
    async with interface.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            content = ""
            output = io.StringIO()
            send_output = True
            try:
                with global_utils.TimingContextManager() as measure:
                    await cursor.execute(cmd)

                columns = cursor.description
                if columns is None:
                    send_output = False
                else:
                    column_names = [str(column[0]) for column in columns]
                    column_sizes = [len(column_name) for column_name in column_names]

                    rows = await cursor.fetchall()
                    for row in rows:
                        for index, value in enumerate(row):
                            column_sizes[index] = max(column_sizes[index], len(str(value)))

                    for column_name, column_size in zip(column_names, column_sizes):
                        output.write(" " + column_name + " " * (column_size - len(column_name) + 1) + "|")

                    output.write("\n")

                    for column_size in column_sizes:
                        output.write("-" * (column_size + 2) + "+")

                    output.write("\n")

                    for row in rows:
                        for value, column_size in zip(row, column_sizes):
                            to_write = str(value)
                            output.write(" " + to_write + " " * (column_size - len(to_write) + 1) + "|")

                        output.write("\n")

            except pyodbc.ProgrammingError as e:
                output.write(global_utils.format_exception(e))

            finally:
                content = f"Process completed after {global_utils.format(measure.result)}\n{content}"
                output.seek(0)
                await ctx.send(content, file=discord.File(output, filename="sql.txt") if send_output else None)
