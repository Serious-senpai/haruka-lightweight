from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from environment import OWNER_ID
from ..router import router
from ..utils import json_encode
from ..verification import authenticate_request
if TYPE_CHECKING:
    from ..customs import Request


@router.get("/commands")
async def handler(request: Request) -> web.Response:
    user = authenticate_request(request)
    show_hidden = False
    if user is not None:
        show_hidden = user.id == OWNER_ID

    commands = [command for command in request.app.interface.commands if show_hidden or not command.hidden]
    return web.json_response(json_encode(commands))
