from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

import utils
from ..middleware_group import middleware_group
if TYPE_CHECKING:
    from ..customs import Handler, Request


@middleware_group
async def error_handler(request: Request, handler: Handler) -> web.Response:
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:
        interface = request.app.interface
        interface.log(utils.format_exception(e))
        await interface.client.report("An error has just occured while processing a server request.", send_state=False)
        raise web.HTTPInternalServerError
