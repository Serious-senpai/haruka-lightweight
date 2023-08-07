from __future__ import annotations

from typing import TYPE_CHECKING


__all__ = (
    "ImageClientException",
    "CategoryNotFound",
)


class ImageClientException(Exception):
    pass


class CategoryNotFound(ImageClientException):

    __slots__ = ("category", "sfw")
    if TYPE_CHECKING:
        category: str
        sfw: bool

    def __init__(self, category: str, *, sfw: bool = True) -> None:
        self.category = category
        self.sfw = sfw

        mode = "sfw" if sfw else "nsfw"
        super().__init__(f"Category {category} ({mode}) not found")
