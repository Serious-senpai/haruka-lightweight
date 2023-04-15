from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from ..router import router
if TYPE_CHECKING:
    from ..customs import Request


@router.get("/commands")
async def handler(request: Request) -> web.Response:
    data = []
    for command in request.app.interface.commands:
        if not command.hidden:
            data.append({
                "name": command.name,
                "aliases": command.aliases,
                "brief": command.brief,
                "description": command.description,
                "usage": command.usage,
            })

    return web.json_response(data)
