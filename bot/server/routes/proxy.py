from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web
from yarl import URL

from ..router import router
from ..web_utils import copy_proxy_headers
if TYPE_CHECKING:
    from ..customs import Request


@router.view("/proxy")
async def handler(request: Request) -> web.Response:
    try:
        url = URL(request.query["url"])
    except KeyError:
        raise web.HTTPBadRequest
    else:
        interface = request.app.interface
        async with interface.session.request(request.method, url, headers=copy_proxy_headers(request.headers), data=request.content.iter_chunked(4096)) as response:
            return web.Response(
                body=await response.read(),
                status=response.status,
                content_type=response.content_type,
            )
