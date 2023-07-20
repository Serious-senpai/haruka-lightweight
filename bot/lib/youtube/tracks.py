from __future__ import annotations

import contextlib
from typing import Any, ClassVar, Dict, Literal, Optional, Union, TYPE_CHECKING

import discord
from discord.utils import escape_markdown as escape
from yarl import URL

import utils
from .client import YouTubeClient, VALID_YOUTUBE_HOST
if TYPE_CHECKING:
    from haruka import Haruka
    from shared import SharedInterface


__all__ = (
    "Track",
)


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
        author_url: URL
        length: int

    def __init__(self, data: Dict[str, Any]) -> None:
        self.title = data["title"]
        self.id = data["videoId"]
        self.author = data["author"]
        self.author_url = URL.build(scheme="https", host="youtube.com", path=data["authorUrl"])
        self.length = data["lengthSeconds"]

    @property
    def url(self) -> URL:
        return URL.build(scheme="https", host="youtube.com", path="/watch", query={"v": self.id})

    @property
    def thumbnail_url(self) -> URL:
        return URL.build(scheme="https", host="img.youtube.com", path=f"/vi/{self.id}/mqdefault.jpg")

    async def create_embed(self, bot: Haruka) -> discord.Embed:
        embed = discord.Embed(title=escape(self.title), url=self.url)
        embed.set_thumbnail(url=self.thumbnail_url)
        embed.set_author(name=self.author, url=self.author_url, icon_url=bot.user.avatar.url)
        embed.set_footer(text=f"Length: {utils.format(self.length)}")

        return embed

    @utils.retry(2)
    async def get_audio_url(self, *, audio_format: Literal["64", "96", "140", "192", "256", "320", "mp3128"] = "mp3128") -> str:
        client = YouTubeClient()
        payload = {
            "k_query": str(self.url),
            "k_page": "mp3",
            "hl": "en",
        }

        async with client.session.post(self._analyzer, data=payload) as response:
            response.raise_for_status()
            data = await response.json(encoding="utf-8")

        key = data["links"]["mp3"][audio_format]["k"]
        return await self._convert(key=key)

    @utils.retry(5, wait=0.75)
    async def _convert(self, *, key: str) -> str:
        client = YouTubeClient()
        async with client.session.post(self._converter, data={"vid": self.id, "k": key}) as response:
            response.raise_for_status()
            data = await response.json(encoding="utf-8")

        return data["dlink"]

    @classmethod
    async def from_id(cls, id: str) -> Optional[Track]:
        client = YouTubeClient()
        async with client.get(f"/api/v1/videos/{id}") as response:
            if response.status == 200:
                data = await response.json(encoding="utf-8")
                return cls(data)

    @classmethod
    async def from_url(cls, url: Union[str, URL]) -> Optional[Track]:
        if isinstance(url, str):
            url = URL(url)

        with contextlib.suppress(AssertionError, KeyError):
            assert url.host in VALID_YOUTUBE_HOST
            return await cls.from_id(url.query["v"])

    def __repr__(self) -> str:
        return f"<Track title={self.title} id={self.id} author={self.author}>"
