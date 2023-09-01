from __future__ import annotations

from typing import Any, Callable, Coroutine, Union, TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from .app import WebApp


if TYPE_CHECKING:
    class Request(web.Request):
        app: WebApp

    Handler = Callable[[Request], Coroutine[Any, Any, Union[web.Response, web.WebSocketResponse]]]
    MiddlewareFunc = Callable[[Request, Handler], Coroutine[Any, Any, Union[web.Response, web.WebSocketResponse]]]
