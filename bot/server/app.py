from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from shared import SharedInterface


class WebApp(web.Application):

    __slots__ = ("interface",)
    if TYPE_CHECKING:
        interface: SharedInterface

    def __init__(self, *, interface: SharedInterface) -> None:
        self.interface = interface
        super().__init__()
