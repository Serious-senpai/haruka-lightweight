from __future__ import annotations

from typing import ClassVar, Optional

from aiohttp import web


class RouteTableDef(web.RouteTableDef):

    __instance__: ClassVar[Optional[RouteTableDef]] = None
    __slots__ = ()

    def __new__(cls) -> RouteTableDef:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            RouteTableDef.__init__(self)

            cls.__instance__ = self

        return cls.__instance__


router = RouteTableDef()
