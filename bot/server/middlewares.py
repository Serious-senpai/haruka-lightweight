from __future__ import annotations

import asyncio
import contextlib
import re
from typing import ClassVar, Dict, Mapping, Optional, Set, Union, TYPE_CHECKING

import aiohttp
from aiohttp import hdrs, web
from multidict import CIMultiDictProxy
from yarl import URL

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
        request_info = f"Method: {request.method}\nURL: {request.url}\nHeaders:\n-----\n{headers_info}\n-----\n{e}"
        interface.log(f"Error serving request:\n{request_info}\n{format_exception(e)}")

        await interface.client.report("An error has just occured while processing a server request.", send_state=False)
        raise web.HTTPInternalServerError


class NotProxyRequest(Exception):
    pass


class ProxyRequestHandler:

    __slots__ = (
        "_proxy_host",
        "_request",
        "_server_host",
    )
    if TYPE_CHECKING:
        proxy_host: str
        request: Request
        server_host: str

    excluded_client_headers: ClassVar[Set[str]] = set(
        s.casefold() for s in [
            "X-ARR-LOG-ID",
            "CLIENT-IP",
            "X-Client-IP",
            "DISGUISED-HOST",
            "X-SITE-DEPLOYMENT-ID",
            "WAS-DEFAULT-HOSTNAME",
            "X-Forwarded-Proto",
            "X-AppService-Proto",
            "X-ARR-SSL",
            "X-Forwarded-TlsVersion",
            "X-Forwarded-For",
            "X-Original-URL",
            "X-WAWS-Unencoded-URL",
            "X-Client-Port",
        ]
    )
    excluded_server_headers: ClassVar[Set[str]] = set(
        s.casefold() for s in [
            "Content-Encoding",
            "Content-Length",
            "Date",
            "Server",
            "Transfer-Encoding",
        ]
    )
    possible_proxies: ClassVar[Set[str]] = {
        "haruka39.me",
        "haruka39.azurewebsites.net",
        "localhost",
    }
    data_sending_methods: ClassVar[Set[str]] = {
        hdrs.METH_PATCH,
        hdrs.METH_POST,
        hdrs.METH_PUT,
    }

    def __init__(self, request: Request, /) -> None:
        self._request = request

        authority = self.omit_port(request.url.authority)
        self._proxy_host = self.get_proxy_host(authority)
        if self._proxy_host is None:
            raise NotProxyRequest

        self._server_host = authority.removesuffix("." + self._proxy_host)

    @property
    def full_proxy_host(self) -> str:
        return self._server_host + "." + self._proxy_host

    @staticmethod
    def omit_port(hostname: str) -> str:
        return hostname.split(":")[0]

    @staticmethod
    def get_proxy_host(full_proxy_host: str) -> Optional[str]:
        for proxy_host in ProxyRequestHandler.possible_proxies:
            if full_proxy_host.endswith("." + proxy_host):
                return proxy_host

        return None

    @staticmethod
    async def forward_ws_message(sender: Union[web.WebSocketResponse, aiohttp.ClientWebSocketResponse], receiver: Union[web.WebSocketResponse, aiohttp.ClientWebSocketResponse], /) -> None:
        async for message in sender:
            if message.type == aiohttp.WSMsgType.TEXT:
                await receiver.send_str(message.data)
            elif message.type == aiohttp.WSMsgType.BINARY:
                await receiver.send_bytes(message.data)

        await receiver.close(code=aiohttp.WSCloseCode.OK if sender.close_code is None else sender.close_code)

    def forward_client_headers(self) -> Dict[str, str]:
        headers = {}
        for key, value in self._request.headers.items():
            if key.casefold() not in self.excluded_client_headers:
                headers[key] = self.remove_proxy_host(value)

        return headers

    def forward_server_headers(self, source: CIMultiDictProxy[str]) -> Dict[str, str]:
        headers = {}
        for key, value in source.items():
            if key.casefold() not in self.excluded_server_headers:
                headers[key] = self.append_proxy_host(value)

        return headers

    def remove_proxy_host(self, source: str) -> str:
        result = source

        # Remove hosts with ports
        result = re.sub(re.escape("." + self._proxy_host + f":{self._request.url.port}"), "", result, flags=re.IGNORECASE)

        # Remove hosts without ports
        result = re.sub(re.escape("." + self._proxy_host), "", result, flags=re.IGNORECASE)

        return result

    def append_proxy_host(self, source: str) -> str:
        # Lowercase all server's hosts
        result = re.sub(re.escape(self._server_host), self._server_host, source, flags=re.IGNORECASE)

        # Replace with full proxy hosts
        result = result.replace(self._server_host, self.full_proxy_host)
        return result

    def is_ws_request(self) -> bool:
        headers = self._request.headers
        upgrade = str(headers.get(hdrs.UPGRADE)).lower()
        connection = str(headers.get(hdrs.CONNECTION)).lower()
        return upgrade == "websocket" and connection == "upgrade"

    async def handle(self) -> Union[web.WebSocketResponse, web.StreamResponse]:
        method = self._request.method
        url = self._request.url.with_host(self._server_host)
        headers = self.forward_client_headers()

        interface = self._request.app.interface
        interface.log(f"Proxy {method} {self._request.url} -> {url} with transformer {self}")

        if self.is_ws_request():
            client_ws = web.WebSocketResponse()
            await client_ws.prepare(self._request)
            try:
                async with interface.proxy_session.ws_connect(url, method=method, headers=headers) as server_ws:
                    await asyncio.gather(
                        self.forward_ws_message(client_ws, server_ws),
                        self.forward_ws_message(server_ws, client_ws),
                    )

            finally:
                return client_ws

        else:
            try:
                data = self._request.content.iter_chunked(4096) if method in self.data_sending_methods else None  # Use once, no retrying
                async with interface.proxy_session.request(method, url, headers=headers, data=data, allow_redirects=True) as response:
                    headers = self.forward_server_headers(response.headers)
                    if response.content_type in ("text/html", "text/javascript", "text/css"):
                        data = await response.read()
                        try:
                            body = self.append_proxy_host(data.decode("utf-8"))
                        except UnicodeDecodeError:
                            body = data

                        return web.Response(body=body, status=response.status, headers=headers)

                    else:
                        r = web.StreamResponse(status=response.status, headers=headers)
                        with contextlib.suppress(ConnectionResetError):
                            await r.prepare(self._request)
                            async for data in response.content.iter_chunked(2048):
                                await r.write(data)

                        return r

            except aiohttp.ClientError as error:
                interface.log(f"Proxy error within server side:\nHeaders:{headers!r}\n{format_exception(error)}")
                raise web.HTTPInternalServerError

    def __repr__(self) -> str:
        return f"<ProxyRequestTransformer server={self._server_host!r} proxy={self._proxy_host!r} is_ws_request={self.is_ws_request()}>"


@web.middleware
async def proxy(request: Request, handler: Handler) -> web.Response:
    try:
        return await ProxyRequestHandler(request).handle()
    except NotProxyRequest:
        return await handler(request)
