from __future__ import annotations

import asyncio
import ntpath
from pathlib import Path
from typing import TYPE_CHECKING

from aiohttp import web

from environment import OWNER_ID
from .router import router
from ...verification import authenticate_request
if TYPE_CHECKING:
    from ...customs import Request


UPLOAD_DIR = Path("uploaded")
UPLOAD_DIR.mkdir(exist_ok=True)
router.static("/uploaded", UPLOAD_DIR, show_index=True)
allowed_uploads = {OWNER_ID}


@router.post("/upload")
async def handler(request: Request) -> web.Response:
    user = await authenticate_request(request)
    if user is not None and user.id in allowed_uploads:
        try:
            name = ntpath.basename(request.query["name"])
            assert isinstance(name, str) and len(name) > 0
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

            user_dir = UPLOAD_DIR / str(user.id)
            user_dir.mkdir(parents=True, exist_ok=True)

            file_path = user_dir / name
            with file_path.open("wb") as file:
                reader = request.content
                while data := await reader.read(1024):
                    file.write(data)

            extract = bool(request.query.get("extract", False))
            if extract:
                extract_dir = user_dir / name.removesuffix(".tar")
                extract_dir.mkdir(parents=True, exist_ok=True)

                process = await asyncio.create_subprocess_exec(
                    "tar",
                    "-xf", str(file_path),
                    "--directory", str(extract_dir),
                    stderr=asyncio.subprocess.PIPE,
                )
                asyncio.create_task(process.communicate())

            return web.Response(status=204)

    else:
        raise web.HTTPForbidden
