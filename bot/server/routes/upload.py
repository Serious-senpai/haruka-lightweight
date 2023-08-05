from __future__ import annotations

import os
from typing import Set, TYPE_CHECKING

from aiohttp import web

from environment import OWNER_ID
from ..router import router
from ..verification import authenticate_request
if TYPE_CHECKING:
    from ..customs import Request


UPLOAD_DIR = "uploaded"
if not os.path.isdir(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)


router.static("/uploaded", UPLOAD_DIR, show_index=True)
allowed_uploads: Set[int] = set([OWNER_ID])


@router.post("/upload")
async def handler(request: Request) -> web.Response:
    user = await authenticate_request(request, interface=request.app.interface)
    if user is not None and user.id in allowed_uploads:
        try:
            name = request.query["name"]
            assert name
        except (AssertionError, KeyError):
            return web.Response(
                text="Missing \"name\" query parameter",
                status=400,
                content_type="text/plain",
            )
        else:
            if not request.body_exists:
                return web.Response(
                    text="No HTTP BODY",
                    status=400,
                    content_type="text/plain",
                )

            path = os.path.join(UPLOAD_DIR, name)
            with open(path, "wb") as file:
                reader = request.content
                while data := await reader.read(1024):
                    file.write(data)

            return web.Response(status=204)

    else:
        raise web.HTTPForbidden
