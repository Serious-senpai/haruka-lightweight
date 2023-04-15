from __future__ import annotations

from typing import ClassVar, Optional

from aiohttp import web


class RouteTableDef(web.RouteTableDef):

    __instance__: ClassVar[Optional[RouteTableDef]] = None

    def __new__(cls) -> RouteTableDef:
        if cls.__instance__ is None:
            self = super().__new__(cls)
            self.__init__()

            cls.__instance__ = self

        return cls.__instance__


router = RouteTableDef()
