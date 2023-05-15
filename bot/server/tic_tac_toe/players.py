from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from aiohttp import web
from discord import abc

from ..customs import Request
from ..utils import Serializable, json_encode
from ..verification import authenticate_request


class Player(Serializable):

    __slots__ = (
        "user",
        "websocket",
    )
    cached_users: Dict[int, abc.User] = {}
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
        user = authenticate_request(request)
        if user is None:
            try:
                id = int(request.query["id"])
            except (KeyError, ValueError):
                return
            else:
                user = cls.cached_users.get(id) or await request.app.interface.clients[0].fetch_user(id)

        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        return Player(user=user, websocket=websocket)
