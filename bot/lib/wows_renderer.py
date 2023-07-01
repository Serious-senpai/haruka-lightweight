from __future__ import annotations

import io
import os

from renderer.render import Renderer
from replay_parser import ReplayParser


__all__ = ("render",)


WOWS_DIR = "wows-replay"
if not os.path.isdir(WOWS_DIR):
    os.mkdir(WOWS_DIR)


def render(data: io.BytesIO, id: int) -> str:
    replay_info = ReplayParser(data, strict=True, raw_data_output=False).get_info()
    renderer = Renderer(
        replay_info["hidden"]["replay_data"],
        logs=False,
        enable_chat=True,
        use_tqdm=True,
    )

    path = os.path.join(WOWS_DIR, f"replay-{id}.mp4")
    renderer.start(path)
    return path
