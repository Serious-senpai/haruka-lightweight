from __future__ import annotations

import contextlib
import re
from typing import Mapping, Pattern, Tuple, TYPE_CHECKING

from aiohttp import web
from multidict import CIMultiDictProxy

import utils
from ..middleware_group import middleware_group
if TYPE_CHECKING:
    from ..customs import Handler, Request


host_patterns: Tuple[Pattern[str], Pattern[str], Pattern[str]] = (
    re.compile(r"(.+?)\.haruka39\.me"),
    re.compile(r"(.+?)\.haruka39\.azurewebsites\.net"),
    re.compile(r"(.+?)\.localhost"),
)


def forward_client_headers(source: CIMultiDictProxy[str]) -> Mapping[str, str]:
    headers = {}
    excluded_headers = set(s.casefold() for s in ["host"])
    for key, value in source.items():
        if key.casefold() not in excluded_headers:
            headers[key] = value

    return headers


@utils.retry(3, wait=0.2)
async def proxy_handler(host: str, *, original: Request) -> web.Response:
    interface = original.app.interface
    interface.log(f"Responding to proxy request to {host} (from {original.url})")

    async with interface.session.request(
        original.method,
        original.url.with_host(host),
        headers=forward_client_headers(original.headers),
        data=original.content.iter_chunked(4096),
    ) as response:
        return web.Response(
            body=await response.read(),
            status=response.status,
            content_type=response.content_type,
        )


@middleware_group
async def handler(request: Request, handler: Handler) -> web.Response:
    host = request.host.split(":")[0]
    for pattern in host_patterns:
        if match := pattern.fullmatch(host):
            real_host = match.group(1)
            with contextlib.suppress(utils.MaxRetryReached):
                return await proxy_handler(real_host, original=request)

            raise web.HTTPInternalServerError

    return await handler(request)
