from __future__ import annotations

import contextlib
from typing import Any, ClassVar, Dict, Literal, Optional, Union, TYPE_CHECKING

from yarl import URL

from .client import YouTubeClient, VALID_YOUTUBE_HOST


class Track:

    _analyzer: ClassVar[URL] = URL.build(scheme="https", host="www.y2mate.com", path="/mates/analyzeV2/ajax")
    _converter: ClassVar[URL] = URL.build(scheme="https", host="www.y2mate.com", path="/mates/convertV2/index")
    __slots__ = (
        "title",
        "id",
        "author",
        "author_url",
        "length",
    )
    if TYPE_CHECKING:
        title: str
        id: str
        author: str
        author_url: str
        length: int

    def __init__(self, data: Dict[str, Any]) -> None:
        self.title = data["title"]
        self.id = data["videoId"]
        self.author = data["author"]
        self.author_url = data["authorUrl"]
        self.length = data["lengthSeconds"]

    @property
    def url(self) -> URL:
        return URL.build(scheme="https", host="youtube.com", path="/watch", query={"v": self.id})

    async def get_audio_url(self, *, format: Literal["140", "mp3128"] = "mp3128") -> URL:
        client = YouTubeClient()
        async with client.session.post(self._analyzer, data={"k_query": str(self.url)}) as response:
            response.raise_for_status()
            data = await response.json(encoding="utf-8")

        key = data["links"]["mp3"][format]["k"]
        async with client.session.post(self._converter, data={"vid": self.id, "k": key}) as response:
            response.raise_for_status()
            data = await response.json(encoding="utf-8")

        return data["dlink"]

    @classmethod
    async def from_id(cls, *, id: str) -> Optional[Track]:
        client = YouTubeClient()
        async with client.get(f"/api/v1/videos/{id}") as response:
            data = await response.json(encoding="utf-8")
            return cls(data)

    @classmethod
    async def from_url(cls, *, url: Union[str, URL]) -> Optional[Track]:
        if isinstance(url, str):
            url = URL(url)

        with contextlib.suppress(AssertionError, KeyError):
            assert url.host in VALID_YOUTUBE_HOST
            return await cls.from_id(id=url.query["v"])

    def __repr__(self) -> str:
        return f"<Track title={self.title} id={self.id} author={self.author}>"
