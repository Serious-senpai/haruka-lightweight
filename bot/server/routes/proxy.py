from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web
from yarl import URL

from ..proxy import ProxyManager, forward_client_headers
from ..router import router
if TYPE_CHECKING:
    from ..customs import Request


@router.view("/proxy")
async def handler(request: Request) -> web.Response:
    interface = request.app.interface
    try:
        url = URL(request.query["url"])
        async with interface.session.request(request.method, url) as _:
            pass

    except Exception:
        raise web.HTTPBadRequest
    else:
        manager = ProxyManager(interface=interface)
        port = await manager.get_port(url.host)
        proxy_url = request.url.with_port(port).with_path(url.path)
        raise web.HTTPFound(proxy_url, headers=forward_client_headers(request.headers), body=request.content.iter_chunked(4096))
