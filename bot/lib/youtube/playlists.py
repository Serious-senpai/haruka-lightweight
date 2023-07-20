from __future__ import annotations

import contextlib
from typing import Any, Dict, Optional, List, Union, TYPE_CHECKING

import discord
from discord.utils import escape_markdown as escape
from yarl import URL

import utils
from .client import YouTubeClient, VALID_YOUTUBE_HOST
from .tracks import Track
if TYPE_CHECKING:
    from haruka import Haruka
    from shared import SharedInterface


__all__ = (
    "Playlist",
)


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

    @property
    def url(self) -> URL:
        return URL.build(scheme="https", host="youtube.com", path="/playlist", query={"list": self.id})

    async def create_embed(self, bot: Haruka) -> discord.Embed:
        embed = discord.Embed(
            title=escape(self.title),
            description=utils.slice_string(escape(self.description), 100),
            url=self.url,
        )

        track_display = "\n".join(f"**#{index + 1}** [{escape(track.title)}]({track.url})" for index, track in enumerate(self.tracks[:7]))
        if len(self.tracks) > 7:
            track_display += f"\n... and {len(self.tracks) - 7} more"

        embed.add_field(
            name=f"Tracks ({len(self.tracks)})",
            value=track_display,
            inline=False,
        )
        embed.set_author(name=self.author, icon_url=bot.user.avatar.url)

        if not self.tracks:
            embed.set_thumbnail(url=bot.user.avatar.url)
        else:
            embed.set_thumbnail(url=self.tracks[0].thumbnail_url)

        return embed

    @classmethod
    async def from_id(cls, id: str) -> Optional[Playlist]:
        client = YouTubeClient()
        async with client.get(f"/api/v1/playlists/{id}") as response:
            if response.status == 200:
                data = await response.json(encoding="utf-8")
                return cls(data)

    @classmethod
    async def from_url(cls, url: Union[str, URL]) -> Optional[Playlist]:
        if isinstance(url, str):
            url = URL(url)

        with contextlib.suppress(AssertionError, KeyError):
            assert url.host in VALID_YOUTUBE_HOST
            return await cls.from_id(url.query["list"])

    def __repr__(self) -> str:
        return f"<Playlist title={self.title} id={self.id}> author={self.author}"
