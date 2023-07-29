from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web
from yarl import URL

from ..middleware_group import middleware_group
from ..web_utils import copy_proxy_headers
if TYPE_CHECKING:
    from ..customs import Handler, Request


@middleware_group
async def proxy_handler(request: Request, handler: Handler) -> web.Response:
    try:
        assert not request.path.startswith("/proxy")

        url = URL(request.headers["referer"])
        assert url.path.startswith("/proxy")

        proxy_url = URL(url.query["url"]).with_path(request.path).with_query(request.query)
        raise web.HTTPFound(
            URL.build(path="/proxy", query={"url": str(proxy_url)}),
            body=request.content.iter_chunked(4096),
            headers=copy_proxy_headers(request.headers),
        )

    except (AssertionError, KeyError):
        return await handler(request)
