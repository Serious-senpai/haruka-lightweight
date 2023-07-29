from __future__ import annotations

import asyncio
import datetime
import io
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

import aiohttp
import async_timeout
import discord
from discord.ext import commands, tasks

import environment
import utils
from customs import Context, Loop, Pool
from shared import SharedInterface
from trees import SlashCommandTree
from commands.general.help import HelpCommand


try:
    import uvloop
except ImportError:
    print("Unable to import uvloop, asynchronous operations will be slower.")
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class Haruka(commands.Bot):

    __instances__: Dict[str, Haruka] = {}
    __processed_message_ids: Set[int] = set()
    if TYPE_CHECKING:
        __transferable_context_cache_update: asyncio.Event
        __users_cache: Dict[int, discord.abc.User]
        cooldown_notify: Dict[int, Dict[str, bool]]
        interface: SharedInterface
        loop: Loop
        owner: Optional[discord.User]
        owner_id: int
        token: str
        transferable_context_cache: List[Context]

    def __init__(self, *, token: str) -> None:
        assert token not in self.__instances__
        self.__instances__[token] = self

        super().__init__(
            activity=discord.Game("with my senpai!"),
            command_prefix=utils.get_prefixes,
            help_command=HelpCommand(),
            tree_cls=SlashCommandTree,
            intents=environment.INTENTS,
            case_insensitive=True,
        )

        self.__transferable_context_cache_update = asyncio.Event()
        self.__users_cache = {}
        self.cooldown_notify = {}
        self.interface = SharedInterface()
        self.owner = None
        self.owner_id = environment.OWNER_ID
        self.token = token
        self.transferable_context_cache = []

        self.interface.add_client(self)

        # Global command check
        async def _global_check(ctx: Context) -> bool:
            if not self.interface.is_parallel_command(ctx.command):
                if ctx.message.id in self.__processed_message_ids:
                    return False

                self.__processed_message_ids.add(ctx.message.id)

            return not await self.interface.blacklist_check(ctx.author.id)

        self.add_check(_global_check)

    @property
    def uptime(self) -> datetime.datetime:
        return self.interface.uptime

    async def setup_hook(self) -> None:
        self._periodic_report.start()
        if self.owner is None:
            self.owner = await self.fetch_user(self.owner_id)

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")
        self.log(f"Logged in as {self.user}")

    async def on_command_error(self, ctx: Context, error: Exception) -> None:
        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.CommandOnCooldown):
            if await self.is_owner(ctx.author):
                await ctx.reinvoke()
                return

            if ctx.author.id not in self.cooldown_notify:
                self.cooldown_notify[ctx.author.id] = {}

            if not self.cooldown_notify[ctx.author.id].get(ctx.command.name, False):
                self.cooldown_notify[ctx.author.id][ctx.command.name] = True
            else:
                return

            await ctx.send(f"⏱️{ctx.author.mention} This command is on cooldown!\nYou can use it after **{utils.format(error.retry_after)}**!")

            await asyncio.sleep(error.retry_after)
            self.cooldown_notify[ctx.author.id][ctx.command.name] = False

        elif isinstance(error, commands.UserInputError):
            await ctx.send_help(ctx.command)

        # These are the subclasses of commands.CheckFailure
        elif isinstance(error, commands.NotOwner):
            return

        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command can only be invoked in a server channel.")

        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("🚫 I do not have permission to execute this command: " + ", ".join(f"`{perm}`" for perm in error.missing_permissions))

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You do not have permission to invoke this command: " + ", ".join(f"`{perm}`" for perm in error.missing_permissions))

        elif isinstance(error, commands.NSFWChannelRequired):
            await ctx.send("🔞 This command can only be invoked in a NSFW channel.")

        elif isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send("Too many people are using this command!")

        elif isinstance(error, commands.CheckFailure):
            return

        elif isinstance(error, commands.CommandInvokeError):
            await self.on_command_error(ctx, error.original)

        # Other exceptions
        elif isinstance(error, discord.Forbidden):
            return

        elif isinstance(error, discord.DiscordServerError):
            return

        else:
            self.log(f"'{ctx.message.content}' in {ctx.message.id}/{ctx.channel.id} from {ctx.author} ({ctx.author.id}):")
            self.log(utils.format_exception(error))
            await self.report("An error has just occured and was handled by `Haruka.on_command_error`", send_state=False)

    async def on_error(self, event_method: str, /, *args, **kwargs) -> None:
        await super().on_error(event_method, *args, **kwargs)
        await self.report("An error has just occured and was handled by `Haruka.on_error`", send_state=False)

    async def process_commands(self, message: discord.Message, /) -> None:
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        command = ctx.command
        if command is not None and self.interface.is_transferable_command(command) and ctx.valid:
            self.transferable_context_cache.append(ctx)
            self.__transferable_context_cache_update.set()
            self.__transferable_context_cache_update.clear()

        await self.invoke(ctx)

    async def wait_for_transferable_cache(self, message_id: int, *, timeout: Optional[float] = None) -> None:
        async with async_timeout.timeout(timeout) as timeout:
            while len(self.transferable_context_cache) == 0 or self.transferable_context_cache[-1].message.id < message_id:
                await self.__transferable_context_cache_update.wait()

    def log(self, content: str) -> None:
        is_single_line = "\n" not in content
        logging = f"[HARUKA {self.user} ID={self.user.id}]:"
        logging += " " if is_single_line else "\n"
        logging += content
        self.interface.log(logging)

    async def report(
        self,
        message: str,
        *,
        send_state: bool = True,
        send_log: bool = True
    ) -> Optional[discord.Message]:
        if self.owner is not None:
            kwargs: Dict[str, Any] = {}

            if send_state:
                kwargs["embed"] = self.display_status

            if send_log:
                self.interface.flush_logs()
                with open(environment.LOG_PATH, "r", encoding="utf-8") as file:
                    kwargs["file"] = discord.File(io.StringIO(file.read()), filename="log.txt")

            return await self.owner.send(message, **kwargs)

    @property
    def display_status(self) -> discord.Embed:
        guilds = self.guilds
        users = self.users
        emojis = self.emojis
        stickers = self.stickers
        voice_clients = self.voice_clients
        private_channels = self.private_channels
        messages = self._connection._messages

        embed = discord.Embed()
        embed.set_thumbnail(url=self.user.avatar.url)
        embed.set_author(
            name="Internal status",
            icon_url=self.user.avatar.url,
        )

        embed.add_field(
            name="Cached servers",
            value=f"{len(guilds)} servers",
            inline=False,
        )
        embed.add_field(
            name="Cached users",
            value=f"{len(users)} users",
        )
        embed.add_field(
            name="Cached emojis",
            value=f"{len(emojis)} emojis",
        )
        embed.add_field(
            name="Cached stickers",
            value=f"{len(stickers)} stickers",
        )
        embed.add_field(
            name="Cached voice clients",
            value=f"{len(voice_clients)} voice clients",
        )
        embed.add_field(
            name="Cached DM channels",
            value=f"{len(private_channels)} channels",
        )
        embed.add_field(
            name="Cached messages",
            value=f"{len(messages)} messages",
            inline=False,
        )
        embed.add_field(
            name="Uptime",
            value=discord.utils.utcnow() - self.uptime,
            inline=False,
        )

        return embed

    @tasks.loop(hours=12)
    async def _periodic_report(self) -> None:
        await self.report("This is the periodic report")

    @_periodic_report.before_loop
    async def _periodic_report_before(self) -> None:
        await self.wait_until_ready()

    def import_commands(self) -> None:
        for command in self.interface.commands:
            self.add_command(command)

    def import_slash_commands(self) -> None:
        for command in self.interface.slash_commands:
            self.tree.add_command(command)

    async def start(self) -> None:
        await self.interface.wait_until_ready()
        await super().start(token=self.token)

    async def close(self) -> None:
        await self.interface.close()
        await self.report("Terminating bot. This is the final report.")
        await super().close()

    async def fetch_user(self, user_id: int, /) -> discord.User:
        try:
            return self.__users_cache[user_id]
        except KeyError:
            self.__users_cache[user_id] = user = await super().fetch_user(user_id)
            return user

    @property
    def pool(self) -> Optional[Pool]:
        return self.interface.pool

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.interface.session

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Haruka):
            return self.token == other.token

        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.token)

    def __repr__(self) -> str:
        return f"<Haruka user={self.user}>"
