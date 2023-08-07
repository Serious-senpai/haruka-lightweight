from __future__ import annotations

import asyncio
from typing import ClassVar

from yarl import URL

from .sources import ImageSource
from shared import SharedInterface


class WaifuImSource(ImageSource):

    cache_lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    BASE_URL = URL.build(scheme="https", host="api.waifu.im")

    async def populate_cache(self, category: str, *, sfw: bool = True) -> None:
        cache = await self.obtain_cache(category, sfw=sfw)
        async with self.cache_lock:
            if cache.empty():
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
