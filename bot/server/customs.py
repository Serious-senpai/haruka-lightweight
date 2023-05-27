from __future__ import annotations

from typing import Awaitable, Callable,  Literal, Union, TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from app import WebApp


if TYPE_CHECKING:
    class Request(web.Request):
        app: WebApp

    Handler = Callable[[Request], Awaitable[Union[web.Response, web.WebSocketResponse]]]
    MiddlewareFunc = Callable[[Request, Handler], Awaitable[Union[web.Response, web.WebSocketResponse]]]

    class Middleware(MiddlewareFunc):
        __middleware_version__: Literal[1]
