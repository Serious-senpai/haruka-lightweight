from __future__ import annotations

import asyncio
import os
from typing import Any, Callable, Tuple


__all__ = ("render",)


installed = False
install_lock = asyncio.Lock()
WOWS_DIR = "wows-replay"
if not os.path.isdir(WOWS_DIR):
    os.mkdir(WOWS_DIR)


async def install_minimap_renderer() -> None:
    process = await asyncio.create_subprocess_shell(
        "pip install --upgrade --force-reinstall git+https://github.com/WoWs-Builder-Team/minimap_renderer.git",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await process.communicate()

    global installed
    installed = True


async def render(data: bytes, *, id: int, log_func: Callable[[str], Any]) -> Tuple[str, str]:
    async with install_lock:
        if not installed:
            log_func("Installing minimap_renderer")
            await install_minimap_renderer()

    name = f"replay-{id}"
    input_path = os.path.join(WOWS_DIR, f"{name}.wowsreplay")
    output_path = os.path.join(WOWS_DIR, f"{name}.mp4")
    with open(input_path, "wb") as f:
        f.write(data)

    process = await asyncio.create_subprocess_exec(
        "python",
        "-m", "render",
        "--replay", input_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )

    _, stderr = await process.communicate()
    return output_path, stderr.decode("utf-8")
