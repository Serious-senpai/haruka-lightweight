from __future__ import annotations

from typing import TYPE_CHECKING

from yarl import URL


class User:

    __slots__ = (
        "id",
        "name",
    )
    if TYPE_CHECKING:
        id: str
        name: str

    def __init__(self, *, id: str, name: str) -> None:
        self.id = id
        self.name = name

    @property
    def url(self) -> URL:
        return URL.build(scheme="https", host="www.pixiv.net", path=f"/en/users/{self.id}")
