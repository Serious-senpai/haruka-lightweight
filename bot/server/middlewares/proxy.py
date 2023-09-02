from __future__ import annotations

import re
from typing import Dict, Optional, Pattern, Tuple, TYPE_CHECKING

import aiohttp
from aiohttp import hdrs, web
from multidict import CIMultiDictProxy

from ..middleware_group import MiddlewareGroup
if TYPE_CHECKING:
    from ..customs import Handler, Request


__all__ = ()


data_sending_methods = {
    hdrs.METH_PATCH,
    hdrs.METH_POST,
    hdrs.METH_PUT,
}


class ContentTransformer:

    __slots__ = (
        "_bob_host",
        "_proxy_host",
    )
    # excluded_client_headers = set(s.casefold() for s in ["Host", "Origin", "Referer"])
    excluded_server_headers = set(s.casefold() for s in ["Content-Encoding", "Content-Length", "Date", "Server", "Transfer-Encoding"])
    bob_host_finder_from_proxy_url = re.compile(r"(?<=\/\/)[-\w@:%.\+~#=]{1,256}\.[a-zA-Z0-9]{1,6}(?:(?=\.haruka39\.me)|(?=\.haruka39\.azurewebsites\.net)|(?=\.localhost))")
    proxy_host_finder_from_proxy_url = re.compile(r"haruka39\.me|haruka39\.azurewebsites\.net|localhost(?::\d*)?")

    if TYPE_CHECKING:
        _bob_host: str
        _proxy_host: str

    def __init__(self, *, proxy_url: str) -> None:
        self._bob_host = self.bob_host_finder_from_proxy_url.search(proxy_url).group(0)
        self._proxy_host = self.proxy_host_finder_from_proxy_url.search(proxy_url).group(0)

    @property
    def bob_host(self) -> str:
        return self._bob_host

    def forward_client_headers(self, source: CIMultiDictProxy[str]) -> Dict[str, str]:
        headers = {}
        for key, value in source.items():
            # if key.casefold() not in self.excluded_client_headers:
            headers[key] = self.ensure_bob_url(value)

        return headers

    def forward_server_headers(self, source: CIMultiDictProxy[str]) -> Dict[str, str]:
        headers = {}
        for key, value in source.items():
            if key.casefold() not in self.excluded_server_headers:
                headers[key] = self.ensure_proxy_url(value)

        return headers

    def _append_proxy_host(self, match: re.Match[str]) -> str:
        return match.group(0) + "." + self._proxy_host

    def ensure_proxy_url(self, source: str) -> str:
        pattern = re.escape(self._bob_host)
        return re.sub(pattern, self._append_proxy_host, source, flags=re.IGNORECASE)

    def ensure_bob_url(self, source: str) -> str:
        pattern = re.escape("." + self._proxy_host)
        return re.sub(pattern, "", source, flags=re.IGNORECASE)


async def proxy_handler(original: Request, /) -> web.StreamResponse:
    transformer = ContentTransformer(proxy_url=str(original.url))

    method = original.method
    url = original.url.with_host(transformer.bob_host).with_port(None)
    headers = transformer.forward_client_headers(original.headers)
    data = original.content.iter_chunked(4096) if original.method in data_sending_methods else None  # Use once, no retrying

    interface = original.app.interface
    try:
        async with interface.proxy_session.request(method, url, headers=headers, data=data) as response:
            headers = transformer.forward_server_headers(response.headers)
            if response.content_type in ("text/html", "text/javascript", "text/css"):
                body = await response.text(encoding="utf-8")
                body = transformer.ensure_proxy_url(body)

                return web.Response(body=body, status=response.status, headers=headers)

            else:
                r = web.StreamResponse(status=response.status, headers=headers)
                await r.prepare(original)
                async for data in response.content.iter_chunked(2048):
                    await r.write(data)

                return r

    except aiohttp.ServerConnectionError:
        raise web.HTTPInternalServerError


@MiddlewareGroup.middleware
async def handler(request: Request, handler: Handler) -> web.Response:
    bob_host = ContentTransformer.bob_host_finder_from_proxy_url.search(str(request.url))
    if bob_host is not None:
        return await proxy_handler(request)

    return await handler(request)
