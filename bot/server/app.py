from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .router import router
from .routes import *
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
            self._html = f.read()

        self.interface = interface
        super().__init__()

        self.add_routes(router)

    @property
    def html(self) -> str:
        return self._html
