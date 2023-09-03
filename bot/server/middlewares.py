from __future__ import annotations

import re
from typing import Dict, TYPE_CHECKING

import aiohttp
from aiohttp import hdrs, web
from multidict import CIMultiDictProxy

from global_utils import format_exception

if TYPE_CHECKING:
    from .customs import Handler, Request


__all__ = (
    "proxy",
    "report",
)


@web.middleware
async def report(request: Request, handler: Handler) -> web.Response:
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:
        interface = request.app.interface

        headers_info = "\n".join(f"{key}: {value}" for key, value in request.headers.items())
        request_info = f"Method: {request.method}\nURL: {request.url}\nHeaders\n-----\n{headers_info}\n-----\n{e}"
        interface.log(f"Error serving request:\n{request_info}\n{format_exception(e)}")

        await interface.client.report("An error has just occured while processing a server request.", send_state=False)
        raise web.HTTPInternalServerError


data_sending_methods = {
    hdrs.METH_PATCH,
    hdrs.METH_POST,
    hdrs.METH_PUT,
}


class ContentTransformer:

    __slots__ = (
        "_bob_host",
        "_proxy_host",
        "_support_https",
    )
    excluded_server_headers = set(s.casefold() for s in ["Content-Encoding", "Content-Length", "Date", "Server", "Transfer-Encoding"])
    bob_host_finder_from_proxy_url = re.compile(r"(?<=\/\/)[-\w@:%.\+~#=]{1,256}\.[a-zA-Z0-9]{1,6}(?:(?=\.haruka39\.me)|(?=\.haruka39\.azurewebsites\.net)|(?=\.localhost))")
    proxy_host_finder_from_proxy_url = re.compile(r"haruka39\.me|haruka39\.azurewebsites\.net|localhost(?::\d*)?")
    scheme_finder_from_proxy_url = re.compile(r"(https?)(:\/\/[-\w@:%.\+~#=]{1,256}\.[a-zA-Z0-9]{1,6}\.(?:haruka39\.me|haruka39\.azurewebsites\.net|localhost(?::\d*)?))")

    if TYPE_CHECKING:
        _bob_host: str
        _proxy_host: str
        _support_https: bool

    def __init__(self, *, proxy_url: str) -> None:
        self._bob_host = self.bob_host_finder_from_proxy_url.search(proxy_url).group(0)
        self._proxy_host = self.proxy_host_finder_from_proxy_url.search(proxy_url).group(0)
        self._support_https = (self.scheme_finder_from_proxy_url.search(proxy_url).group(1) == "https")

    @property
    def bob_host(self) -> str:
        return self._bob_host

    def forward_client_headers(self, source: CIMultiDictProxy[str]) -> Dict[str, str]:
        headers = {}
        for key, value in source.items():
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

    def _ensure_http(self, match: re.Match[str]) -> str:
        return "http" + match.group(2)

    def ensure_proxy_url(self, source: str) -> str:
        result = re.sub(re.escape(self._bob_host), self._append_proxy_host, source, flags=re.IGNORECASE)
        if not self._support_https:
            result = re.sub(self.scheme_finder_from_proxy_url, self._ensure_http, result)

        return result

    def ensure_bob_url(self, source: str) -> str:
        pattern = re.escape("." + self._proxy_host)
        return re.sub(pattern, "", source, flags=re.IGNORECASE)


async def proxy_handler(original: Request, /) -> web.StreamResponse:
    transformer = ContentTransformer(proxy_url=str(original.url))

    method = original.method
    url = original.url.with_host(transformer.bob_host).with_port(None).with_scheme("https")
    headers = transformer.forward_client_headers(original.headers)
    data = original.content.iter_chunked(4096) if original.method in data_sending_methods else None  # Use once, no retrying

    interface = original.app.interface
    try:
        async with interface.proxy_session.request(method, url, headers=headers, data=data, allow_redirects=False) as response:
            headers = transformer.forward_server_headers(response.headers)
            if response.content_type in ("text/html", "text/javascript", "text/css"):
                data = await response.read()
                try:
                    body = transformer.ensure_proxy_url(data.decode("utf-8"))
                except UnicodeDecodeError:
                    body = data

                return web.Response(body=body, status=response.status, headers=headers)

            else:
                r = web.StreamResponse(status=response.status, headers=headers)
                await r.prepare(original)
                async for data in response.content.iter_chunked(2048):
                    await r.write(data)

                return r

    except aiohttp.ServerConnectionError:
        raise web.HTTPInternalServerError


@web.middleware
async def proxy(request: Request, handler: Handler) -> web.Response:
    bob_host = ContentTransformer.bob_host_finder_from_proxy_url.search(str(request.url))
    if bob_host is not None:
        return await proxy_handler(request)

    return await handler(request)
