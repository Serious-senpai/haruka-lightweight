from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

import utils
from ..middleware_group import middleware_group
if TYPE_CHECKING:
    from ..customs import Handler, Request


@middleware_group
async def handler(request: Request, handler: Handler) -> web.Response:
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:
        interface = request.app.interface
        interface.log(utils.format_exception(e))

        headers_info = "\n".join(f"{key}: {value}" for key, value in request.headers.items())
        request_info = f"Method: {request.method}\nURL: {request.url}\nHeaders\n-----\n{headers_info}\n-----\n{e}"

        await interface.client.report(f"An error has just occured while processing a server request.```\n{request_info}```", send_state=False)
        raise web.HTTPInternalServerError
