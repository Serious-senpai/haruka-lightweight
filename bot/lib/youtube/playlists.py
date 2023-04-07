from __future__ import annotations

import contextlib
from typing import Any, Dict, Optional, List,  Union, TYPE_CHECKING

from yarl import URL

from .client import YouTubeClient, VALID_YOUTUBE_HOST
from .tracks import Track


class Playlist:

    __slots__ = (
        "title",
        "id",
        "author",
        "description",
        "tracks",
    )
    if TYPE_CHECKING:
        title: str
        id: str
        author: str
        description: str
        tracks: List[Track]

    def __init__(self, data: Dict[str, Any]) -> None:
        self.title = data["title"]
        self.id = data["playlistId"]
        self.author = data["author"]
        self.description = data["description"]
        self.tracks = [Track(d) for d in data["videos"]]

    @classmethod
    async def from_id(cls, *, id: str) -> Optional[Playlist]:
        client = YouTubeClient()
        async with client.get(f"/api/v1/playlists/{id}") as response:
            data = await response.json(encoding="utf-8")
            return cls(data)

    @classmethod
    async def from_url(cls, *, url: Union[str, URL]) -> Optional[Playlist]:
        if isinstance(url, str):
            url = URL(url)

        with contextlib.suppress(AssertionError, KeyError):
            assert url.host in VALID_YOUTUBE_HOST
            return await cls.from_id(id=url.query["list"])

    def __repr__(self) -> str:
        return f"<Playlist title={self.title} id={self.id}> author={self.author}"
