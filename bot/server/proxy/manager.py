from __future__ import annotations

import functools
from random import randint
from typing import ClassVar, Dict, Optional, TYPE_CHECKING

import aiohttp
from aiohttp import web

import utils
from .proxy_utils import forward_client_headers
if TYPE_CHECKING:
    from ..customs import Handler
    from shared import SharedInterface


class ProxyManager:

    __instance__: ClassVar[Optional[ProxyManager]] = None
    __slots__ = (
        "interface",
        "proxy_mapping",
    )
    if TYPE_CHECKING:
        interface: SharedInterface
        proxy_mapping: Dict[str, int]

    def __new__(cls, *, interface: SharedInterface) -> ProxyManager:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self.interface = interface
            self.proxy_mapping = {}

            cls.__instance__ = self

        return cls.__instance__

    async def get_port(self, host: str) -> int:
        try:
            return self.proxy_mapping[host]
        except KeyError:
            app = web.Application(middlewares=[self.report])
            session = aiohttp.ClientSession()
            app.router.add_view(
                "/{path:.*}",
                functools.partial(
                    self.handler,
                    host=host,
                    session=session,  # idk why, but we need a seperate session
                ),
            )

            # TODO: Close the session

            runner = web.AppRunner(app)
            await runner.setup()

            port = randint(49152, 65535)
            while True:
                try:
                    site = web.TCPSite(runner, port=port)
                    await site.start()
                except OSError:
                    port = randint(49152, 65535)
                else:
                    self.proxy_mapping[host] = port
                    self.interface.client.log(f"Binded {host} to proxy port {port}")
                    return port

    async def handler(self, request: web.Request, *, host: str, session: aiohttp.ClientSession) -> web.Response:
        async with session.request(
            request.method,
            request.url.with_host(host).with_port(None),
            headers=forward_client_headers(request.headers),
            data=request.content.iter_chunked(4096),
        ) as response:
            return web.Response(
                body=await response.read(),
                status=response.status,
                content_type=response.content_type,
            )

    @web.middleware
    async def report(self, request: web.Request, handler: Handler) -> web.Response:
        try:
            return await handler(request)
        except web.HTTPException:
            raise
        except Exception as e:
            error_message = utils.format_exception(e)
            self.interface.log(error_message)
            await self.interface.client.report(f"An error has just occured while processing a proxy request.```\n{error_message}```", send_state=False)
            raise web.HTTPInternalServerError
