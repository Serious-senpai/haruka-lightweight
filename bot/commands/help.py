from __future__ import annotations

import re
from typing import Dict, List, Mapping, Optional, TYPE_CHECKING

import discord
from discord.ext import commands

import utils
from environment import COMMAND_PREFIX
if TYPE_CHECKING:
    from haruka import Haruka


category_matcher = re.compile(r"(.+?)\.\w+")
category_icons = {
    "dev": "🛠️",
    "general": "💬",
    "music": "🎶",
    "search": "🔍",
}


def display_category(category: str) -> str:
    result = category.capitalize()
    result = result.replace("_", " ")
    return result


class HelpCommand(commands.HelpCommand):

    if TYPE_CHECKING:
        context: commands.Context[Haruka]

    def __init__(self) -> None:
        super().__init__(
            command_attrs={
                "name": "help",
                "brief": "general.help",
                "description": "Get all available commands or help for a specific command.",
                "usage": "help\nhelp <command>",
            },
        )

    @property
    def bot(self) -> Haruka:
        return self.context.bot

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]], /) -> None:
        show_hidden = await self.bot.is_owner(self.context.author)

        category_mapping: Dict[str, List[str]] = {}
        for command in self.bot.walk_commands():
            if show_hidden or not command.hidden:
                match = category_matcher.fullmatch(command.brief)
                assert match is not None
                category = match.group(1)
                category_mapping.setdefault(category, [])
                category_mapping[category].append(command.name)

        categories = sorted(category_mapping.keys())
        for value in category_mapping.values():
            value.sort()

        embed = discord.Embed(
            description=f"You can also invoke command with <@!{self.bot.user.id}> as a prefix.\nTo get help for a command, type `{COMMAND_PREFIX}help <command>`."
        )
        embed.set_author(
            name=f"{self.bot.user} command list",
            icon_url=self.bot.user.avatar.url,
        )
        embed.set_thumbnail(url=self.context.author.avatar.url if self.context.author.avatar else None)

        for category in categories:
            icon = category_icons.get(category)
            category_display = display_category(category)
            embed.add_field(
                name=f"{icon} {category_display}" if icon is not None else category_display,
                value="```" + ", ".join(category_mapping[category]) + "```",
                inline=False,
            )

        await self.context.send(embed=embed)

    async def send_command_help(self, command: commands.Command) -> None:
        if command.aliases and command.qualified_name not in command.aliases:
            command.aliases.insert(0, command.qualified_name)
        elif not command.aliases:
            command.aliases = [command.qualified_name]

        description = command.description.format(prefix=COMMAND_PREFIX)

        cooldown = command._buckets
        cooldown_notify = "**Cooldown**\nNo cooldown"
        if cooldown._cooldown:
            _cd_time = cooldown._cooldown.per
            cooldown_notify = f"**Cooldown**\n{utils.format(_cd_time)} per {cooldown._type.name}"

        embed = discord.Embed(
            title=command.qualified_name,
            description=f"```\n{command.usage}\n```\n**Description**\n{description}\n**Aliases**\n" + ", ".join(f"`{alias}`" for alias in command.aliases) + "\n" + cooldown_notify,
        )
        embed.set_author(
            name=f"{self.context.author.name}, this is an instruction for {command.qualified_name}!",
            icon_url=self.context.author.avatar.url if self.context.author.avatar else None,
        )
        await self.context.send(embed=embed)

    async def command_not_found(self, string: str) -> str:
        if len(string) > 20:
            return "There is no such long command."

        show_hidden = await self.bot.is_owner(self.context.author)

        # Also include aliases (don't use walk_commands)
        command_names = [command.name for command in self.bot.all_commands.values() if show_hidden or not command.hidden]

        word = await utils.fuzzy_match(string, command_names)
        return f"No command called `{string}` was found. Did you mean `{word}`?"

    def subcommand_not_found(self, command: commands.Command, string: str) -> str:
        return f"Command `{command.qualified_name}` has no subcommand named `{string}`!"
