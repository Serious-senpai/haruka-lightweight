from __future__ import annotations

import random
from typing import TYPE_CHECKING

from aiohttp import web

from environment import OWNER_ID
from global_utils import get_all_subclasses
from .router import router
from ...verification import authenticate_request
if TYPE_CHECKING:
    from ...customs import Request


@router.post("/throw")
async def handler(request: Request) -> web.Response:
    user = await authenticate_request(request)
    if user is not None and user.id == OWNER_ID:
        errors = tuple(get_all_subclasses(BaseException))
        try:
            error_type = random.choice(errors)
            error = error_type()
        except TypeError:
            error = TypeError()

        raise error

    else:
        raise web.HTTPForbidden
