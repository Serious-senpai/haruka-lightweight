from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from yarl import URL


__all__ = ("Tag",)


class Tag:

    __slots__ = (
        "name",
        "locked",
        "deletable",
        "romaji",
        "_translations",
    )
    if TYPE_CHECKING:
        name: str
        locked: bool
        deletable: bool
        romaji: Optional[str]
        _translations: Dict[str, str]

    def __init__(self, data: Dict[str, Any]) -> None:
        self.name = data["tag"]
        self.locked = data["locked"]
        self.deletable = data["deletable"]
        self.romaji = data.get("romaji")
        self._translations = data.get("translation", {})

    def translate(self, language: str = "en") -> Optional[str]:
        return self._translations.get(language)

    @staticmethod
    def url(tag: Union[str, Tag]) -> URL:
        name = tag.name if isinstance(tag, Tag) else tag
        return URL.build(scheme="https", host="www.pixiv.net", path=f"/en/tags/{name}/artworks")

    def __str__(self) -> str:
        return self.translate() or self.name

    def __repr__(self) -> str:
        return f"<Tag name={self.name} translations={list(self._translations.keys())}>"

    @classmethod
    def guess(cls, payload: Dict[str, Any], /) -> List[Union[str, Tag]]:
        data = payload["tags"]
        if isinstance(data, dict):
            return [Tag(d) for d in data["tags"]]

        if isinstance(data, list):
            return data

        raise TypeError(f"Unrecognized data: {data!r}")
