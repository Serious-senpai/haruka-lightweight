from __future__ import annotations

import asyncio
from typing import ClassVar

from yarl import URL

from .sources import ImageSource
from shared import SharedInterface


__all__ = ("WaifuImSource",)


class WaifuImSource(ImageSource):

    __slots__ = ()
    BASE_URL: ClassVar[URL] = URL.build(scheme="https", host="api.waifu.im")

    async def populate_cache(self, cache: asyncio.Queue[str], *, category: str, sfw: bool = True) -> None:
        interface = SharedInterface()

        url = self.BASE_URL
        url = url.with_path("/search")
        url = url.with_query(
            {
                "included_tags": category,
                "is_nsfw": str(not sfw),
                "many": "true",
            },
        )

        async with interface.session.get(url) as response:
            data = await response.json(encoding="utf-8")
            for image in data["images"]:
                await cache.put(image["url"])

    async def populate_tags(self) -> None:
        interface = SharedInterface()

        url = self.BASE_URL
        url = url.with_path("/tags")

        async with interface.session.get(url) as response:
            data = await response.json(encoding="utf-8")

            versatile = set(data["versatile"])
            nsfw = set(data["nsfw"])

            self.sfw = tuple(sorted(versatile))
            self.nsfw = tuple(sorted(versatile | nsfw))
