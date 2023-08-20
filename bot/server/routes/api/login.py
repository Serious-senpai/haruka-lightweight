from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .router import router
from ...verification import authenticate_request, generate_token, otp_cache
from ...web_utils import json_encode
if TYPE_CHECKING:
    from ...customs import Request


@router.get("/login")
async def handler_get(request: Request) -> web.Response:
    user = await authenticate_request(request)
    if user is not None:
        return web.json_response({"success": True, "user": json_encode(user)})

    return web.json_response({"success": False})


@router.post("/login")
async def handler_post(request: Request) -> web.Response:
    key = request.headers.get("Login-Key")
    if key is not None:
        user = otp_cache.pop_key(key)
        if user is not None:
            token = await generate_token(user, interface=request.app.interface)
            return web.json_response({"success": True, "user": json_encode(user), "token": token})

    return web.json_response({"success": False})
