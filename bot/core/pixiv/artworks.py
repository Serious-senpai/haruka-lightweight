from __future__ import annotations

import asyncio
import contextlib
import io
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.utils import escape_markdown
from yarl import URL

from .tags import Tag
from .users import User
from emoji_ui import NAVIGATOR
from global_utils import slice_string
from shared import SharedInterface
if TYPE_CHECKING:
    from haruka import Haruka


__all__ = ("PartialArtwork", "Artwork",)


class PartialArtwork:

    __slots__ = (
        "interface",
        "title",
        "id",
        "author",
        "tags",
        "created_at",
        "is_nsfw",
        "width",
        "height",
        "pages_count",
        "image_url",
    )
    if TYPE_CHECKING:
        interface: SharedInterface
        title: str
        id: str
        author: User
        tags: List[Union[str, Tag]]
        created_at: datetime
        is_nsfw: bool
        width: int
        height: int
        pages_count: int
        image_url: Optional[str]

    def __init__(self, data: Dict[str, Any], *, image_url: Optional[str] = None) -> None:
        self.interface = SharedInterface()
        self.title = data["title"]
        self.id = data["id"]
        self.author = User(id=data["userId"], name=data["userName"])
        self.tags = Tag.guess(data)
        self.created_at = datetime.fromisoformat(data["createDate"])
        self.is_nsfw = bool(data["xRestrict"])
        self.width = data["width"]
        self.height = data["height"]
        self.pages_count = data["pageCount"]
        self.image_url = image_url

    @property
    def url(self) -> URL:
        return URL.build(scheme="https", host="www.pixiv.net", path=f"/en/artworks/{self.id}")

    async def fetch(self) -> Artwork:
        return await Artwork.from_id(int(self.id), fallback_image_url=self.image_url)

    @staticmethod
    async def display_search(query: str, *, target: discord.abc.Messageable, bot: Haruka) -> None:
        index = 0
        page = 1
        artworks = await PartialArtwork.search(query, page=page)
        artwork = artworks[0] = await artworks[0].fetch()
        embed, file = await artwork.prepare_message(bot)
        embed.set_footer(text=f"Result #{index + 1}")
        if file is None:
            message = await target.send(embed=embed)
        else:
            message = await target.send(embed=embed, file=file)

        for emoji in NAVIGATOR:
            await message.add_reaction(emoji)

        def check(payload: discord.RawReactionActionEvent) -> bool:
            return payload.message_id == message.id

        while True:
            done, _ = await asyncio.wait([
                bot.wait_for("raw_reaction_add", check=check),
                bot.wait_for("raw_reaction_remove", check=check),
            ],
                timeout=300.0,
                return_when=asyncio.FIRST_COMPLETED,
            )

            if done:
                payload: discord.RawReactionActionEvent = done.pop().result()

                try:
                    action = NAVIGATOR.index(str(payload.emoji))
                    if action == 0 and index == 0:
                        raise ValueError

                except ValueError:
                    continue

                if action == 0:
                    index -= 1

                elif action == 1:
                    index += 1
                    if index >= len(artworks):
                        page += 1
                        next_page = await PartialArtwork.search(query, page=page)
                        artworks.extend(next_page)
                        if len(next_page) == 0:
                            index = 0

                else:
                    raise ValueError(f"Unknown action = {action}")

                artwork = artworks[index] = await artworks[index].fetch()
                embed, file = await artwork.prepare_message(bot)
                embed.set_footer(text=f"Result #{index + 1}")
                if file is None:
                    await message.edit(embed=embed)
                else:
                    await message.edit(embed=embed, attachments=[file])

                await asyncio.sleep(1.0)

            else:
                await message.edit(content="This message has timed out.")

    @classmethod
    async def search(cls, query: str, *, page: int = 1) -> List[PartialArtwork]:
        interface = SharedInterface()
        params = {
            "order": "date_d",
            "mode": "all",
            "s_mode": "s_tag",
            "type": "all",
            "lang": "en",
            "p": page,
        }
        async with interface.session.get(f"https://www.pixiv.net/ajax/search/artworks/{query}", params=params) as response:
            data = await response.json(encoding="utf-8")
            data = data["body"]["illustManga"]["data"]
            return [PartialArtwork(d, image_url=d["url"]) for d in data]


class Artwork(PartialArtwork):

    __slots__ = (
        "description",
        "bookmarks_count",
        "views_count",
    )
    if TYPE_CHECKING:
        description: str
        bookmarks_count: int
        views_count: int

    def __init__(self, data: Dict[str, Any], *, fallback_image_url: Optional[str] = None) -> None:
        super().__init__(data, image_url=data["urls"]["regular"] or fallback_image_url)
        self.description = BeautifulSoup(data["description"], "html.parser").get_text(separator="\n")
        self.bookmarks_count = data["bookmarkCount"]
        self.views_count = data["viewCount"]

    async def fetch(self) -> Artwork:
        return self

    async def prepare_message(self, bot: Haruka) -> Tuple[discord.Embed, Optional[discord.File]]:
        embed = discord.Embed(
            title=escape_markdown(self.title),
            description=slice_string(escape_markdown(self.description), 4000),
            url=self.url,
            timestamp=self.created_at,
        )
        embed.set_author(name="Pixiv artwork", icon_url=bot.user.display_avatar.url)

        if self.tags:
            embed.add_field(
                name="Tags",
                value=slice_string(", ".join(f"[{str(tag)}]({Tag.url(tag)})" for tag in self.tags), 1000),
                inline=False,
            )

        embed.add_field(
            name="Artwork ID",
            value=self.id,
        )
        embed.add_field(
            name="Author",
            value=f"[{self.author.name}]({self.author.url})",
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
