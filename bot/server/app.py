from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .routes import api_router, static_router
from .middleware_group import MiddlewareGroup
from .middlewares import *
from .verification import otp_cache
if TYPE_CHECKING:
    from shared import SharedInterface


class WebApp(web.Application):

    __slots__ = (
        "interface",
    )
    if TYPE_CHECKING:
        interface: SharedInterface

    def __init__(self, *, interface: SharedInterface, **kwargs) -> None:
        self.interface = interface
        super().__init__(**kwargs)


class MainApp(WebApp):

    def __init__(self, *, interface: SharedInterface) -> None:
        super().__init__(
            interface=interface,
            middlewares=MiddlewareGroup().to_list(),
        )

        api = WebApp(interface=interface)
        api.add_routes(api_router)
        self.add_subapp("/api/", api)

        self.add_routes(static_router)

    async def startup(self) -> None:
        otp_cache.start_countdown()
        return await super().startup()
