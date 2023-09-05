from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from aiohttp import web
from discord import abc

from ..verification import authenticate_websocket
from ..web_utils import json_encode
if TYPE_CHECKING:
    from ..customs import Request


__all__ = ("Player",)


class Player:
    """Represents a tic-tac-toe player websocket session"""

    __slots__ = (
        "user",
        "websocket",
    )
    if TYPE_CHECKING:
        user: Optional[abc.User]
        websocket: web.WebSocketResponse

    def __init__(self, *, user: Optional[abc.User], websocket: web.WebSocketResponse) -> None:
        self.user = user
        self.websocket = websocket

    def to_json(self) -> Dict[str, Any]:
        return {
            "user": json_encode(self.user),
        }

    def __str__(self) -> str:
        if self.user is not None:
            return self.user.display_name

        return "Guest"

    def __repr__(self) -> str:
        return f"<Player user={self.user}>"

    @classmethod
    async def from_request(cls, request: Request, /) -> Player:
        """This function is a coroutine

        Upgrade the HTTP request to a websocket connection and perform authorization. The first
        message sent from the client (within 60s) must contain the user token.

        Parameters
        -----
        request: ``Request``
            The initial HTTP request

        Returns
        -----
        ``Player``
            The player session created after authenticated using the first websocket message received
            within 60s. If authentication fails, ``player.user`` will be None
        """
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        user = await authenticate_websocket(websocket, interface=request.app.interface)

        return cls(user=user, websocket=websocket)
