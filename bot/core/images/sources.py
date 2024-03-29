from __future__ import annotations

import asyncio
import contextlib
import random
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .errors import CategoryNotFound
from global_utils import fuzzy_match, slice_string
from shared import SharedInterface


__all__ = (
    "get_image",
    "list_categories",
    "unknown_category_message",
)


class ImageSource:

    __slots__ = (
        "_cache_lock",
        "_ready",
        "_urls_queue",
        "nsfw",
        "sfw",
    )
    __instance__: Optional[ImageSource] = None
    if TYPE_CHECKING:
        _cache_lock: asyncio.Lock
        _ready: asyncio.Event
        _urls_queue: Dict[str, Tuple[asyncio.Queue[str], asyncio.Queue[str]]]
        nsfw: Tuple[str, ...]
        sfw: Tuple[str, ...]

    def __new__(cls) -> ImageSource:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self._cache_lock = asyncio.Lock()
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

    async def _obtain_cache(self, category: str, *, sfw: bool = True) -> asyncio.Queue[str]:
        await self.check_category(category, sfw=sfw)
        try:
            return self._urls_queue[category][sfw]
        except KeyError:
            self._urls_queue[category] = (asyncio.Queue(), asyncio.Queue())
            return self._urls_queue[category][sfw]

    async def get_image(self, category: str, *, sfw: bool = True) -> str:
        cache = await self._obtain_cache(category, sfw=sfw)

        # Non-blocking when cache is not empty
        if cache.empty():
            async with self._cache_lock:
                # Check if cache is really empty at this time
                if cache.empty():
                    await self.populate_cache(cache, category=category, sfw=sfw)

        return await cache.get()

    async def populate_cache(self, cache: asyncio.Queue[str], *, category: str, sfw: bool = True) -> None:
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


async def unknown_category_message(category: str, *, sfw: bool) -> str:
    message = f"Unsupported category `{slice_string(category, 800)}`. "
    if len(category) < 300:
        guess = await fuzzy_match(category, await list_categories(sfw=sfw))
        message += f"Did you mean `{guess}`?"

    return message
