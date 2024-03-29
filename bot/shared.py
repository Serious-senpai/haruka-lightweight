from __future__ import annotations

import asyncio
import contextlib
import datetime
import io
import signal
import sys
from typing import Any, Callable, ClassVar, Coroutine, Dict, List, Optional, Set, TypeVar, Union, TYPE_CHECKING

import aiohttp
import aioodbc
import discord
from aiohttp import web
from discord import app_commands
from discord.ext import commands
from discord.utils import utcnow
if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec

from customs import Context, Pool
from environment import LOG_PATH, ODBC_CONNECTION_STRING, PORT
from server import MainApp
if TYPE_CHECKING:
    from haruka import Haruka


if TYPE_CHECKING:
    T = TypeVar("T")
    P = ParamSpec("P")
    CommandCallback = Callable[Concatenate[commands.Context[Haruka], P], Coroutine]
    GroupCallback = Callable[Concatenate[commands.Context[Haruka], P], Coroutine]
    SlashCommandCallback = Callable[Concatenate[discord.Interaction[Haruka], P], Coroutine]


class SharedInterface:

    __instance__: ClassVar[Optional[SharedInterface]] = None
    __slots__ = (
        "__parallel_commands",
        "__pool",
        "__proxy_session",
        "__ready",
        "__session",
        "__transferable_commands",
        "__webapp",
        "_closed",
        "_started",
        "_transfer_exclusion",
        "clients",
        "commands",
        "log",
        "logfile",
        "slash_commands",
        "uptime",
    )
    if TYPE_CHECKING:
        __parallel_commands: Set[commands.Command]
        __pool: Optional[Pool]
        __proxy_session: Optional[aiohttp.ClientSession]
        __ready: asyncio.Event
        __session: Optional[aiohttp.ClientSession]
        __transferable_commands: Set[commands.Command]
        __webapp: Optional[MainApp]
        _closed: bool
        _started: bool
        _transfer_exclusion: Dict[int, Set[Haruka]]
        clients: List[Haruka]
        commands: Set[commands.Command]
        log: Callable[[str], None]
        logfile: io.TextIOWrapper
        slash_commands: Set[app_commands.Command]
        uptime: datetime.datetime

    def __new__(cls) -> SharedInterface:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self.__parallel_commands = set()
            self.__pool = None
            self.__proxy_session = None
            self.__ready = asyncio.Event()
            self.__session = None
            self.__transferable_commands = set()
            self.__webapp = None
            self._closed = False
            self._started = False
            self._transfer_exclusion = {}
            self.clients = []
            self.commands = set()
            self.log = self._log
            self.logfile = open(LOG_PATH, "wt", encoding="utf-8")
            self.slash_commands = set()
            self.uptime = utcnow()

            cls.__instance__ = self

        return cls.__instance__

    @property
    def pool(self) -> Optional[Pool]:
        return self.__pool

    @property
    def session(self) -> aiohttp.ClientSession:
        if self.__session is None:
            self.__session = aiohttp.ClientSession(
                headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62",
                },
                timeout=aiohttp.ClientTimeout(total=12.0),
            )

        return self.__session

    @property
    def proxy_session(self) -> aiohttp.ClientSession:
        if self.__proxy_session is None:
            self.__proxy_session = aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar())

        return self.__proxy_session

    @property
    def client(self) -> Optional[Haruka]:
        with contextlib.suppress(IndexError):
            return self.clients[0]

    def add_client(self, client: Haruka) -> None:
        self.clients.append(client)

    def flush_logs(self) -> None:
        if not self.logfile.closed:
            self.logfile.flush()

    def _log(self, content: str) -> None:
        if not self.logfile.closed:
            self.logfile.write(content + "\n")
            self.flush_logs()

    async def transfer(self, original_ctx: Context) -> bool:
        command = original_ctx.command
        if not self.is_transferable_command(command):
            raise ValueError(f"Command \"{command}\" is not transferable")

        message_id = original_ctx.message.id
        invoker = original_ctx.bot
        try:
            self._transfer_exclusion[message_id].add(invoker)
        except KeyError:
            self._transfer_exclusion[message_id] = {invoker}

        for client in self.clients:
            if client not in self._transfer_exclusion[message_id]:
                transferable_context_cache = client.transferable_context_cache
                await client.wait_for_transferable_cache(message_id, timeout=1.0)  # Make sure that transferable_context_cache is properly populated

                # Binary search transferable_context_cache, hopefully it is sorted (it should be!) according to message IDs
                low = 0
                high = len(transferable_context_cache)

                if high == 0:
                    continue

                # Result is in interval [low, high)
                while high - low > 1:
                    mid = (low + high) // 2
                    ctx = transferable_context_cache[mid]
                    if ctx.message.id > message_id:
                        high = mid
                    else:
                        low = mid

                ctx = transferable_context_cache[low]
                if ctx.message.id == message_id:
                    asyncio.create_task(ctx.reinvoke())
                    return True

        return False

    def is_parallel_command(self, command: Any) -> bool:
        return command in self.__parallel_commands

    def is_transferable_command(self, command: Any) -> bool:
        return command in self.__transferable_commands

    def command(
        self,
        *,
        name: str,
        brief: str,  # For classifying commands
        description: str,
        parallel: bool = False,
        transferable: bool = False,
        **kwargs: Any,
    ) -> Callable[[Union[commands.Command, CommandCallback]], commands.Command]:
        def decorator(func: Union[commands.Command, CommandCallback]) -> commands.Command:
            command = func if isinstance(func, commands.Command) else commands.Command(
                func,
                name=name,
                description=description,
                brief=brief,
                **kwargs,
            )

            self.commands.add(command)
            if parallel and transferable:
                raise ValueError("A command cannot be both parallel and transferable")

            if parallel:
                self.__parallel_commands.add(command)
            elif transferable:
                self.__transferable_commands.add(command)

            if appender := getattr(func, "__appender__", None):
                command.extras["appender"] = appender

            return command

        return decorator

    def group(
        self,
        *,
        name: str,
        brief: str,  # For classifying groups
        description: str,
        parallel: bool = False,
        transferable: bool = False,
        **kwargs: Any,
    ) -> Callable[[Union[commands.Group, GroupCallback]], commands.Group]:
        def decorator(func: Union[commands.Group, GroupCallback]) -> commands.Group:
            group = func if isinstance(func, commands.Group) else commands.Group(
                func,
                name=name,
                description=description,
                brief=brief,
                **kwargs,
            )

            self.commands.add(group)
            if parallel and transferable:
                raise ValueError("A group cannot be both parallel and transferable")

            if parallel:
                self.__parallel_commands.add(group)
            elif transferable:
                self.__transferable_commands.add(group)

            if appender := getattr(func, "__appender__", None):
                group.extras["appender"] = appender

            return group

        return decorator

    def slash(
        self,
        *,
        name: str,
        description: str = "...",
        nsfw: bool = False,
    ) -> Callable[[Union[app_commands.Command, SlashCommandCallback]], app_commands.Command]:
        def decorator(func: Union[app_commands.Command, SlashCommandCallback]) -> app_commands.Command:
            command = func if isinstance(func, app_commands.Command) else app_commands.Command(
                name=name,
                description=description,
                callback=func,
                nsfw=nsfw,
            )
            self.slash_commands.add(command)
            return command

        return decorator

    def append_description(self, appender: Callable[[], Coroutine[Any, Any, str]]) -> Callable[[T], T]:
        def decorator(func: T) -> T:
            if isinstance(func, commands.Command):
                func.extras["appender"] = appender
            else:
                func.__appender__ = appender

            return func

        return decorator

    async def start(self) -> None:
        if self._started:
            return

        self._started = True

        if self.__pool is None:
            self.__pool = await aioodbc.create_pool(
                dsn=ODBC_CONNECTION_STRING,
                minsize=1,
                maxsize=10,
                autocommit=True,
            )
            pool = self.pool
            assert pool is not None
            async with pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute("IF NOT EXISTS (SELECT * FROM sysobjects WHERE name = 'blacklist') CREATE TABLE blacklist (id varchar(max))")
                    await cursor.execute("IF NOT EXISTS (SELECT * FROM sysobjects WHERE name = 'prefix') CREATE TABLE prefix (id varchar(max), pref varchar(max))")
                    await cursor.execute("IF NOT EXISTS (SELECT * FROM sysobjects WHERE name = 'tokens') CREATE TABLE tokens (id varchar(max), token varchar(max))")

            self.log("Initialized database")

        if self.__webapp is None:
            self.__webapp = webapp = MainApp(interface=self)
            runner = web.AppRunner(webapp)
            await runner.setup()
            site = web.TCPSite(runner, port=PORT)
            await site.start()

            self.log(f"Started serving on port {PORT}")

            self.setup_signal_handler()

        for command in self.commands:
            if appender := command.extras.get("appender"):
                description = command.description + "\n" + await appender()
                command.description = command.__original_kwargs__["description"] = description  # Unstable!

        self.__ready.set()

    def is_ready(self) -> bool:
        return self.__ready.is_set()

    async def wait_until_ready(self) -> None:
        await self.__ready.wait()

    def setup_signal_handler(self) -> None:
        def graceful_exit() -> None:
            raise KeyboardInterrupt

        if sys.platform == "linux":
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(signal.SIGHUP, graceful_exit)
            loop.add_signal_handler(signal.SIGINT, graceful_exit)
            loop.add_signal_handler(signal.SIGTERM, graceful_exit)
            self.log("Added signal handler")

    async def blacklist_check(self, id: int, /) -> bool:
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT * FROM blacklist WHERE id = ?", str(id))
                return await cursor.fetchone() is not None

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            self.log("Closing interface")

            if self.__session is not None:
                await self.__session.close()
                self.log("Closed HTTP session")

            if self.__proxy_session is not None:
                await self.__proxy_session.close()
                self.log("Closed HTTP proxy session")

            if self.__pool is not None:
                self.__pool.close()
                await self.__pool.wait_closed()
                self.log("Closed database pool")

            self.logfile.close()
            self.log = print


interface = SharedInterface()
interface.log(f"Running on {sys.platform}\nPython {sys.version}")
