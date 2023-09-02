from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from global_utils import format_exception
from ..middleware_group import MiddlewareGroup
if TYPE_CHECKING:
    from ..customs import Handler, Request


@MiddlewareGroup.middleware
async def handler(request: Request, handler: Handler) -> web.Response:
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
