from __future__ import annotations

import asyncio
import datetime
import io
import signal
import sys
from typing import Any, Awaitable, Callable, ClassVar, Concatenate, List, Optional, ParamSpec, Set, Union, TYPE_CHECKING

import aiohttp
import discord
from aiohttp import web
from discord import app_commands
from discord.ext import commands
from discord.utils import utcnow

import utils
from environment import COMMAND_PREFIX, FUZZY_MATCH, LOG_PATH, PORT
from server import WebApp
if TYPE_CHECKING:
    from haruka import Haruka


if TYPE_CHECKING:
    P = ParamSpec("P")
    CommandCallback = Callable[Concatenate[commands.Context[Haruka], P], Awaitable[Any]]
    SlashCommandCallback = Callable[Concatenate[discord.Interaction[Haruka], P], Awaitable[Any]]


class SharedInterface:

    __instance__: ClassVar[Optional[SharedInterface]] = None
    __slots__ = (
        "__ready",
        "__session",
        "__webapp",
        "_closed",
        "clients",
        "commands",
        "log",
        "logfile",
        "slash_commands",
        "uptime",
    )
    if TYPE_CHECKING:
        __ready: asyncio.Event
        __session: Optional[aiohttp.ClientSession]
        __webapp: Optional[WebApp]
        _closed: bool
        clients: List[Haruka]
        commands: Set[commands.Command]
        log: Callable[[str], None]
        logfile: io.TextIOWrapper
        slash_commands: Set[app_commands.Command]
        uptime: datetime.datetime

    def __new__(cls) -> SharedInterface:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self.__ready = asyncio.Event()
            self.__session = None
            self.__webapp = None
            self._closed = False
            self.clients = []
            self.commands = set()
            self.log = self._log
            self.logfile = open(LOG_PATH, "wt", encoding="utf-8")
            self.slash_commands = set()
            self.uptime = utcnow()

            cls.__instance__ = self

        return cls.__instance__

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

    def add_client(self, client: Haruka) -> None:
        self.clients.append(client)

    def _log(self, content: str) -> None:
        self.logfile.write(content + "\n")
        self.logfile.flush()

    def command(
        self,
        *,
        name: str,
        brief: str,  # For classifying commands
        description: str,
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
            command.usage = command.usage if command.usage else command.qualified_name
            command.usage = COMMAND_PREFIX + command.usage.replace("\n", f"\n{COMMAND_PREFIX}")

            self.commands.add(command)
            return command

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

    async def start(self) -> None:
        if self.__webapp is not None:
            return

        # Start the server first so Azure will not complain
        self.__webapp = webapp = WebApp(interface=self)
        runner = web.AppRunner(webapp)
        await runner.setup()
        site = web.TCPSite(runner, port=PORT)
        await site.start()

        self.log(f"Started serving on port {PORT}")

        try:
            if sys.platform == "linux":
                self.setup_signal_handler()

                # Start dummy clients
                clients: List[discord.Client] = []
                coros: List[Awaitable[None]] = []
                for bot in self.clients:
                    client = discord.Client(activity=discord.Game("Preparing..."), intents=discord.Intents.none())
                    clients.append(client)
                    coros.append(client.start(bot.token))

                self.log("Starting dummy clients")
                dummy_start = asyncio.gather(*coros, return_exceptions=True)

                # Continue building binaries (~6 minutes)
                process = await asyncio.create_subprocess_shell("apt install ffmpeg g++ -y", stdout=asyncio.subprocess.DEVNULL, stderr=self.logfile)
                await process.communicate()

                process = await asyncio.create_subprocess_shell(f"g++ -std=c++2a -Wall bot/c++/fuzzy.cpp -o {FUZZY_MATCH}", stdout=asyncio.subprocess.DEVNULL, stderr=self.logfile)
                await process.communicate()

                # Stop dummy clients
                async def stop_dummy_clients() -> None:
                    self.log("Stopping dummy clients")
                    await asyncio.gather(*[client.close() for client in clients], return_exceptions=True)
                    await dummy_start

                    await asyncio.wait_for(stop_dummy_clients(), timeout=30)
        except BaseException as exc:
            self.log(utils.format_exception(exc))
        finally:
            self.__ready.set()

    async def wait_until_ready(self) -> None:
        await self.__ready.wait()

    def setup_signal_handler(self) -> None:
        def graceful_exit() -> None:
            raise KeyboardInterrupt

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGHUP, graceful_exit)
        loop.add_signal_handler(signal.SIGINT, graceful_exit)
        loop.add_signal_handler(signal.SIGTERM, graceful_exit)
        self.log("Added signal handler")

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            self.log("Closing interface")

            if self.__session is not None:
                await self.__session.close()
                self.log("Closed HTTP session")

            self.logfile.close()
            self.log = print


interface = SharedInterface()
interface.log(f"Running on {sys.platform}\nPython {sys.version}")
