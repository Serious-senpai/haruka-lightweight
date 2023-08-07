from __future__ import annotations

import asyncio
import contextlib
import random
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .errors import CategoryNotFound
from shared import SharedInterface
from utils import fuzzy_match


__all__ = (
    "get_image",
    "list_categories",
    "fuzzy_search",
)


class ImageSource:

    __slots__ = (
        "_ready",
        "_urls_queue",
        "nsfw",
        "sfw",
    )
    __instance__: Optional[ImageSource] = None
    if TYPE_CHECKING:
        _ready: asyncio.Event
        _urls_queue: Dict[str, Tuple[asyncio.Queue[str], asyncio.Queue[str]]]
        nsfw: Tuple[str, ...]
        sfw: Tuple[str, ...]

    def __new__(cls) -> ImageSource:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self._ready = asyncio.Event()
            self._urls_queue = {}
            self.nsfw = ()
            self.sfw = ()

            task = asyncio.create_task(self.populate_tags())
            task.add_done_callback(lambda _: self._when_ready())

            cls.__instance__ = self

        return cls.__instance__

    def is_ready(self) -> bool:
        return self._ready.is_set()

    def _when_ready(self) -> None:
        sfw_display = ", ".join(self.sfw)
        nsfw_display = ", ".join(self.nsfw)

        interface = SharedInterface()
        interface.log(f"Got {len(self.sfw)} + {len(self.nsfw)} categories from waifu.im:\nsfw: {sfw_display}\nnsfw: {nsfw_display}")

        self._ready.set()

    async def wait_until_ready(self) -> None:
        await self._ready.wait()

    async def check_category(self, category: str, *, sfw: bool = True) -> None:
        await self.wait_until_ready()
        search = self.sfw if sfw else self.nsfw
        low = 0
        high = len(search)

        if high == 0:
            raise CategoryNotFound(category, sfw=sfw)

        # Result is in interval [low, high)
        while high - low > 1:
            mid = (low + high) // 2
            if search[mid] > category:
                high = mid
            else:
                low = mid

        if search[low] != category:
            raise CategoryNotFound(category, sfw=sfw)

    async def obtain_cache(self, category: str, *, sfw: bool = True) -> asyncio.Queue[str]:
        await self.check_category(category, sfw=sfw)
        try:
            return self._urls_queue[category][sfw]
        except KeyError:
            self._urls_queue[category] = (asyncio.Queue(), asyncio.Queue())
            return self._urls_queue[category][sfw]

    async def get_image(self, category: str, *, sfw: bool = True) -> str:
        cache = await self.obtain_cache(category, sfw=sfw)
        if cache.empty():
            asyncio.create_task(self.populate_cache(category, sfw=sfw))

        return await cache.get()

    async def populate_cache(self, category: str, *, sfw: bool = True) -> None:
        raise NotImplementedError

    async def populate_tags(self) -> None:
        raise NotImplementedError


async def get_image(category: str, *, sfw: bool = True) -> Optional[str]:
    types = ImageSource.__subclasses__()
    random.shuffle(types)
    for type in types:
        source = type()
        with contextlib.suppress(CategoryNotFound):
            return await source.get_image(category, sfw=sfw)

    return None


async def list_categories(*, sfw: bool) -> List[str]:
    results = []
    for type in ImageSource.__subclasses__():
        source = type()
        await source.wait_until_ready()
        results.extend(source.sfw if sfw else source.nsfw)

    return sorted(set(results))


async def fuzzy_search(category: str, *, sfw: bool) -> str:
    return await fuzzy_match(category, await list_categories(sfw=sfw))
