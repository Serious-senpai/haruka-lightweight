from __future__ import annotations

import io

import discord
import pyodbc
from discord.ext import commands

import utils
from customs import Context
from shared import interface


@interface.command(
    name="sql",
    brief="dev.sql",
    description="Execute a SQL command",
    usage="sql <command>",
    hidden=True,
)
@commands.is_owner()
async def _handler(ctx: Context, *, cmd: str) -> None:
    async with interface.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            content = ""
            output = io.StringIO()
            try:
                with utils.TimingContextManager() as measure:
                    await cursor.execute(cmd)

                columns = cursor.description
                if columns is None:
                    output.write("---No SELECT statement---")
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
                output.write(utils.format_exception(e))

            finally:
                content = f"Process completed after {utils.format(measure.result)}\n{content}"
                output.seek(0)
                await ctx.send(content, file=discord.File(output, filename="sql.txt"))
