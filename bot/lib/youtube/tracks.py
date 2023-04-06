from __future__ import annotations

from typing import Any, ClassVar, Dict, Literal, TYPE_CHECKING

from yarl import URL

from .client import YouTubeClient


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
