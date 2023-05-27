from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

import discord
from aiohttp import web
from discord import abc

from ..verification import authenticate_request
from ..web_utils import Serializable, json_encode
if TYPE_CHECKING:
    from ..customs import Request


class Player(Serializable):

    __slots__ = (
        "user",
        "websocket",
    )
    if TYPE_CHECKING:
        user: abc.User
        websocket: web.WebSocketResponse

    def __init__(self, *, user: abc.User, websocket: web.WebSocketResponse) -> None:
        self.user = user
        self.websocket = websocket

    def to_json(self) -> Dict[str, Any]:
        return {
            "user": json_encode(self.user),
        }

    def __repr__(self) -> str:
        return f"<Player user={self.user}>"

    @classmethod
    async def from_request(cls, request: Request) -> Optional[Player]:
        user = await authenticate_request(request, interface=request.app.interface)
        if user is None:
            try:
                id = int(request.query["id"])
            except (KeyError, ValueError):
                return
            else:
                try:
                    user = await request.app.interface.client.fetch_user(id)
                except discord.NotFound:
                    raise web.HTTPNotFound

        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        return Player(user=user, websocket=websocket)
