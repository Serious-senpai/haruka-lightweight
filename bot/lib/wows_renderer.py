from __future__ import annotations

import asyncio
import importlib
from pathlib import Path
from typing import Any, Callable, Tuple


__all__ = ("render",)


install_lock = asyncio.Lock()
WOWS_DIR = Path("wows-replay")
WOWS_DIR.mkdir(exist_ok=True)


async def install_minimap_renderer() -> None:
    process = await asyncio.create_subprocess_shell(
        "pip install -U git+https://github.com/WoWs-Builder-Team/minimap_renderer",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await process.communicate()


async def render(data: bytes, *, id: int, log_func: Callable[[str], Any]) -> Tuple[str, str]:
    async with install_lock:
        try:
            importlib.import_module("render")
        except ModuleNotFoundError:
            log_func("minimap_renderer not found. Installing...")
            await install_minimap_renderer()
            log_func("minimap_renderer installed!")

    name = f"replay-{id}"
    input_path = WOWS_DIR / f"{name}.wowsreplay"
    output_path = WOWS_DIR / f"{name}.mp4"
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
