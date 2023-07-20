from __future__ import annotations

import asyncio
import contextlib
import io
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.utils import escape_markdown as escape
from yarl import URL

from .tags import Tag
from .users import User
from shared import SharedInterface
if TYPE_CHECKING:
    from haruka import Haruka


__all__ = ("Artwork",)


class Artwork:

    __slots__ = (
        "interface",
        "title",
        "description",
        "id",
        "author",
        "tags",
        "created_at",
        "is_nsfw",
        "width",
        "height",
        "pages_count",
        "bookmarks_count",
        "views_count",
        "image_url",
    )
    if TYPE_CHECKING:
        interface: SharedInterface
        title: str
        description: str
        id: str
        author: User
        tags: List[Tag]
        created_at: datetime
        is_nsfw: bool
        width: int
        height: int
        pages_count: int
        bookmarks_count: int
        views_count: int
        image_url: Optional[str]

    def __init__(self, data: Dict[str, Any], *, fallback_image_url: Optional[str] = None) -> None:
        self.interface = SharedInterface()
        self.title = data["title"]
        self.description = BeautifulSoup(data["description"], "html.parser").get_text(separator="\n")
        self.id = data["id"]
        self.author = User(id=data["userId"], name=data["userName"])
        self.tags = [Tag(d) for d in data["tags"]["tags"]]
        self.created_at = datetime.fromisoformat(data["createDate"])
        self.is_nsfw = bool(data["xRestrict"])
        self.width = data["width"]
        self.height = data["height"]
        self.pages_count = data["pageCount"]
        self.bookmarks_count = data["bookmarkCount"]
        self.views_count = data["viewCount"]
        self.image_url = data["urls"]["regular"] or fallback_image_url

    @property
    def url(self) -> URL:
        return URL.build(scheme="https", host="www.pixiv.net", path=f"/en/artworks/{self.id}")

    async def prepare_message(self, bot: Haruka) -> Tuple[discord.Embed, Optional[discord.File]]:
        embed = discord.Embed(
            title=escape(self.title),
            description=escape(self.description),
            url=self.url,
            timestamp=self.created_at,
        )
        embed.set_author(name="Pixiv artwork", icon_url=bot.user.avatar.url)
        embed.set_footer(text="Created at")

        if self.tags:
            embed.add_field(
                name="Tags",
                value=", ".join(f"[{str(tag)}]({tag.url})" for tag in self.tags),
                inline=False,
            )

        embed.add_field(
            name="Artwork ID",
            value=self.id,
        )
        embed.add_field(
            name="Author",
            value=f"[{escape(self.author.name)}]({self.author.url})",
        )
        embed.add_field(
            name="Size",
            value=f"{self.width} x {self.height}",
        )

        embed.add_field(
            name="Pages count",
            value=self.pages_count,
        )
        embed.add_field(
            name="Bookmarks count",
            value=self.bookmarks_count,
        )
        embed.add_field(
            name="Views count",
            value=self.views_count,
        )

        embed.add_field(
            name="Artwork URL",
            value=self.url,
            inline=False,
        )

        if self.image_url is not None:
            try:
                async with self.interface.session.get(self.image_url, headers={"referer": "https://www.pixiv.net/"}) as response:
                    response.raise_for_status()
                    data = io.BytesIO(await response.read())
                    data.seek(0)
                    file = discord.File(data, filename="image.png")
                    embed.set_image(url="attachment://image.png")

                    return embed, file

            except (asyncio.TimeoutError, aiohttp.ClientError):
                pass

        return embed, None

    @classmethod
    async def from_id(cls, artwork_id: int, *, fallback_image_url: Optional[str] = None) -> Optional[Artwork]:
        interface = SharedInterface()
        with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
            url = URL.build(scheme="https", host="www.pixiv.net", path=f"/ajax/illust/{artwork_id}")
            async with interface.session.get(url) as response:
                response.raise_for_status()
                data = await response.json(encoding="utf-8")
                if data["error"]:
                    return None

                return cls(data["body"], fallback_image_url=fallback_image_url)
