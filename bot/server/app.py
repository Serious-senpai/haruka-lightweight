from __future__ import annotations

import contextlib
from typing import Dict, TYPE_CHECKING

import discord
from aiohttp import web
from discord import abc

from .router import router
from .routes import *
from .verification import otp_cache
if TYPE_CHECKING:
    from shared import SharedInterface


class WebApp(web.Application):

    __slots__ = (
        "_cached_users",
        "_html",
        "interface",
    )
    if TYPE_CHECKING:
        _cached_users: Dict[int, abc.User]
        _html: str
        interface: SharedInterface

    def __init__(self, *, interface: SharedInterface) -> None:
        self._cached_users = {}

        with open("./bot/server/build/index.html", "rt", encoding="utf-8") as f:
            html = f.read()
            html = html.replace("A new Flutter project.", "Haruka frontend server")
            html = html.replace("haruka", "Haruka")
            self._html = html

        self.interface = interface
        super().__init__()

        self.add_routes(router)
        self.on_startup.append(lambda self: otp_cache.start_countdown())

    @property
    def cached_users(self) -> Dict[int, abc.User]:
        return self._cached_users

    @property
    def html(self) -> str:
        return self._html
