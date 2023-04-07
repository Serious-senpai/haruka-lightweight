from __future__ import annotations

import asyncio
import datetime
import io
import signal
import sys
from typing import Any, Awaitable, Callable, ClassVar, Concatenate, Optional, ParamSpec, Set, Union, TYPE_CHECKING

import aiohttp
import discord
from aiohttp import web
from discord import app_commands
from discord.ext import commands
from discord.utils import utcnow

import utils
from environment import LOG_PATH, PORT
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
        "__session",
        "__webapp",
        "_closed",
        "commands",
        "log",
        "logfile",
        "slash_commands",
        "uptime",
    )
    if TYPE_CHECKING:
        __session: Optional[aiohttp.ClientSession]
        __webapp: Optional[WebApp]
        _closed: bool
        commands: Set[commands.Command]
        log: Callable[[str], None]
        logfile: io.TextIOWrapper
        slash_commands: Set[app_commands.Command]
        uptime: datetime.datetime

    def __new__(cls) -> SharedInterface:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self.__session = None
            self.__webapp = None
            self._closed = False
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
                timeout=aiohttp.ClientTimeout(total=10.0, connect=5.0),
            )

        return self.__session

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

        self.__webapp = webapp = WebApp(interface=self)
        runner = web.AppRunner(webapp)
        await runner.setup()
        site = web.TCPSite(runner, port=PORT)
        await site.start()

        self.log(f"Started serving on port {PORT}")

        if sys.platform == "linux":
            self.setup_signal_handler()

            self.log("Installing ffmpeg")
            await utils.install_ffmpeg(writer=self.logfile)

    def setup_signal_handler(self) -> None:
        def graceful_exit() -> None:
            self.log("Received SIGTERM signal")
            raise KeyboardInterrupt

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, graceful_exit)
        loop.add_signal_handler(signal.SIGINT, graceful_exit)
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
