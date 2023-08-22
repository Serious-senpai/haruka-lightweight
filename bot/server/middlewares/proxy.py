from __future__ import annotations

import re
from typing import Dict, Pattern, Tuple, TYPE_CHECKING

import aiohttp
from aiohttp import hdrs, web
from multidict import CIMultiDictProxy

from ..middleware_group import MiddlewareGroup
if TYPE_CHECKING:
    from ..customs import Handler, Request


host_patterns: Tuple[Pattern[str], Pattern[str], Pattern[str]] = (
    re.compile(r"(.+?)\.haruka39\.me"),
    re.compile(r"(.+?)\.haruka39\.azurewebsites\.net"),
    re.compile(r"(.+?)\.localhost"),
)
data_sending_methods = {
    hdrs.METH_PATCH,
    hdrs.METH_POST,
    hdrs.METH_PUT,
}
excluded_client_headers = set(s.casefold() for s in ["Host", "Origin", "Referer"])
excluded_server_headers = set(s.casefold() for s in ["Content-Encoding", "Content-Length", "Date", "Server", "Transfer-Encoding"])


def forward_client_headers(source: CIMultiDictProxy[str]) -> Dict[str, str]:
    headers = {}
    for key, value in source.items():
        if key.casefold() not in excluded_client_headers:
            headers[key] = value

    return headers


def forward_server_headers(source: CIMultiDictProxy[str]) -> Dict[str, str]:
    headers = {}
    for key, value in source.items():
        if key.casefold() not in excluded_server_headers:
            if key.casefold() == "Set-Cookie".casefold():
                value = re.sub(r"[Dd]omain=[^;]+;?", "", value)

            headers[key] = value

    return headers


async def proxy_handler(host: str, *, original: Request) -> web.Response:
    method = original.method
    url = original.url.with_host(host).with_port(None)
    headers = forward_client_headers(original.headers)
    data = original.content.iter_chunked(4096) if original.method in data_sending_methods else None  # Use once, no retrying

    interface = original.app.interface
    interface.log(f"Received proxy request: {method} {url} from \"{original.url}\", headers {headers}")

    try:
        async with interface.proxy_session.request(method, url, headers=headers, data=data) as response:
            headers = forward_server_headers(response.headers)
            return web.Response(
                body=await response.read(),
                status=response.status,
                headers=headers,
            )

    except aiohttp.ServerConnectionError:
        raise web.HTTPInternalServerError


@MiddlewareGroup.middleware
async def handler(request: Request, handler: Handler) -> web.Response:
    host = request.host.split(":")[0]
    for pattern in host_patterns:
        if match := pattern.fullmatch(host):
            real_host = match.group(1)
            return await proxy_handler(real_host, original=request)

    return await handler(request)
