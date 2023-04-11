from discord import app_commands
from discord.ext import commands

from customs import Context, Interaction
from lib import urban
from shared import interface


@interface.command(
    name="urban",
    brief="search.urban",
    description="Search for a term from Urban Dictionary",
    usage="urban <query>"
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _urban_cmd(ctx: Context, *, query: str):
    result = await urban.UrbanSearch.search(query, session=interface.session)
    if result:
        embed = await result.create_embed()
        embed.set_author(
            name=f"{ctx.author.name} searched for {query}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("No matching result was found.")


@interface.slash(
    name="urban",
    description="Search for a term from Urban Dictionary",
)
@app_commands.describe(query="The searching query")
async def _urban_slash(interaction: Interaction, query: str) -> None:
    await interaction.response.defer(thinking=True)
    result = await urban.UrbanSearch.search(query, session=interface.session)
    if result:
        embed = await result.create_embed()
        embed.set_author(
            name=f"{interaction.user.name} searched for {query}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None,
        )
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("No matching result was found.")
