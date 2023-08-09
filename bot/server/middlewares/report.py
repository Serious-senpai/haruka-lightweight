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
        error_message = utils.slice_string(utils.format_exception(e), 1500, reverse=True)
        interface.log(error_message)
        await interface.client.report(f"An error has just occured while processing a server request.```\n{error_message}```", send_state=False)
        raise web.HTTPInternalServerError
