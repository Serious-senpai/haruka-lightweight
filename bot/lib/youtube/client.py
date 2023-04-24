from __future__ import annotations

import asyncio
from types import TracebackType
from typing import Any, Awaitable, ClassVar, Dict, List, Optional, Tuple, Type, TYPE_CHECKING

import aiohttp
from yarl import URL

import utils
from shared import SharedInterface


__all__ = (
    "YouTubeClient",
)


INVIDIOUS_INSTANCES_URL = URL.build(scheme="https", host="api.invidious.io", path="/instances.json")
VALID_YOUTUBE_HOST = {
    "www.youtube.com",
    "youtube.com",
    "youtu.be",
}


class _ResponseContextManager:

    __slots__ = (
        "request_coro",
        "response",
    )
    if TYPE_CHECKING:
        request_coro: Awaitable[aiohttp.ClientResponse]
        response: Optional[aiohttp.ClientResponse]

    def __init__(self, request_coro: Awaitable[aiohttp.ClientResponse]) -> None:
        self.request_coro = request_coro
        self.response = None

    async def __aenter__(self) -> aiohttp.ClientResponse:
        self.response = await self.request_coro
        return self.response

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> None:
        if self.response is not None:
            self.response.close()


class YouTubeClient:

    __instance__: ClassVar[Optional[YouTubeClient]] = None
    __slots__ = (
        "__initialized",
        "__ready",
        "instances",
        "interface",
    )
    if TYPE_CHECKING:
        __initialized: bool
        __ready: asyncio.Event
        instances: List[URL]
        interface: SharedInterface

    def __new__(cls) -> YouTubeClient:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self.__initialized = False
            self.__ready = asyncio.Event()
            self.instances = []
            self.interface = SharedInterface()

            loop = asyncio.get_running_loop()
            loop.create_task(self.initialize())

            cls.__instance__ = self

        return cls.__instance__

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.interface.session

    @property
    def is_ready(self) -> bool:
        return self.__ready.is_set()

    async def wait_until_ready(self) -> None:
        await self.__ready.wait()

    async def initialize(self) -> None:
        if not self.__initialized:
            self.__initialized = True
            self.interface.log("Initializing YouTubeClient")

            async with self.session.get(INVIDIOUS_INSTANCES_URL) as response:
                response.raise_for_status()
                data: List[Tuple[str, Dict[str, Any]]] = await response.json(encoding="utf-8")  # List of length 2 with known types

                for instance_data in data:
                    host_name, host_data = instance_data
                    if host_name.endswith(".i2p") or host_name.endswith(".onion") or not host_data["api"]:
                        continue

                    self.instances.append(URL.build(scheme="https", host=host_name))

            self.interface.log("YouTube client is ready!")
            self.__ready.set()

            await self.sort_instances()

    async def sort_instances(self) -> None:
        ping: Dict[URL, float] = {}
        for instance in self.instances:
            with utils.TimingContextManager() as measure:
                try:
                    async with self.session.get(instance) as response:
                        response.raise_for_status()
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    ping[instance] = measure.result + 10 ** 9
                else:
                    ping[instance] = measure.result

        self.instances.sort(key=ping.__getitem__)

    async def _request(self, method: str, path: str, *, headers: Optional[Dict[str, Any]] = None) -> aiohttp.ClientResponse:
        await self.wait_until_ready()
        for instance in self.instances:
            try:
                url = instance.with_path(path)
                response = await self.session.request(method, url, headers=headers)
            except (asyncio.TimeoutError, aiohttp.ClientError):
                pass
            else:
                return response

        # Shouldn't reach here
        raise RuntimeError(f"Unable to make request to path {path} of any Invidious instances")

    def get(self, path: str, *, headers: Optional[Dict[str, Any]] = None) -> _ResponseContextManager:
        return _ResponseContextManager(self._request("GET", path, headers=headers))
