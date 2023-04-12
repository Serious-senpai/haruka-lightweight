from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from app import WebApp


class Request(web.Request):
    if TYPE_CHECKING:
        app: WebApp
