from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .middleware_group import middleware_group
from .middlewares import *
from .router import router
from .routes import *
from .verification import otp_cache
if TYPE_CHECKING:
    from shared import SharedInterface


class WebApp(web.Application):

    __slots__ = (
        "_html",
        "interface",
    )
    if TYPE_CHECKING:
        _html: str
        interface: SharedInterface

    def __init__(self, *, interface: SharedInterface) -> None:
        with open("./bot/server/build/index.html", "rt", encoding="utf-8") as f:
            html = f.read()
            html = html.replace("A new Flutter project.", "Haruka frontend server")
            html = html.replace("haruka", "Haruka")
            self._html = html

        self.interface = interface
        super().__init__(middlewares=middleware_group.to_list())

        self.add_routes(router)
        self.on_startup.append(lambda self: otp_cache.start_countdown())

    @property
    def html(self) -> str:
        return self._html
