from __future__ import annotations

import asyncio
from typing import ClassVar, Dict, List, Literal

from yarl import URL

from .sources import ImageSource
from shared import SharedInterface


__all__ = ("WaifuPicsSource",)


class WaifuPicsSource(ImageSource):

    __slots__ = ()
    BASE_URL: ClassVar[URL] = URL.build(scheme="https", host="api.waifu.pics")
    DUMMY_JSON: ClassVar[Dict[Literal["exclude"], List[str]]] = {"exclude": [""]}  # Damn that API

    async def populate_cache(self, cache: asyncio.Queue[str], *, category: str, sfw: bool = True) -> None:
        interface = SharedInterface()
        type = "sfw" if sfw else "nsfw"

        url = self.BASE_URL
        url = url.with_path(f"/many/{type}/{category}")

        async with interface.session.post(url, data=self.DUMMY_JSON) as response:
            data = await response.json(encoding="utf-8")
            for url in data["files"]:
                await cache.put(url)

    async def populate_tags(self) -> None:
        interface = SharedInterface()

        url = self.BASE_URL
        url = url.with_path("/endpoints")

        async with interface.session.get(url) as response:
            data = await response.json(encoding="utf-8")

            self.sfw = tuple(sorted(data["sfw"]))
            self.nsfw = tuple(sorted(data["nsfw"]))
