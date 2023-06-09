from __future__ import annotations

from typing import List, Optional, Set, TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from .customs import Middleware, MiddlewareFunc


class MiddlewareGroup:

    __instance__: Optional[MiddlewareGroup] = None
    __slots__ = (
        "_middlewares",
    )
    if TYPE_CHECKING:
        _middlewares: Set[Middleware]

    def __new__(cls) -> MiddlewareGroup:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self.__init__()
            self._middlewares = set()

            cls.__instance__ = self

        return cls.__instance__

    def to_list(self) -> List[Middleware]:
        return list(self._middlewares)

    def __call__(self, func: MiddlewareFunc, /) -> Middleware:
        middleware = web.middleware(func)
        self._middlewares.add(middleware)
        return middleware


middleware_group = MiddlewareGroup()
