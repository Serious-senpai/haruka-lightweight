from __future__ import annotations

import asyncio
import contextlib
import shlex
from random import randint
from typing import Any, Optional, Union, TYPE_CHECKING

import discord

import utils
from .playlists import Playlist
from .tracks import Track
if TYPE_CHECKING:
    from haruka import Haruka


class AudioPlayer(discord.VoiceClient):
    """A voice client which is able to play audio within
    a voice channel.

    Each guild has at most one active client.
    """

    __slots__ = (
        "__operable",
        "__play_lock",
        "__repeat",
        "__shuffle",
        "__stop_request",
        "__waiter",
        "playing",
        "target",
    )
    if TYPE_CHECKING:
        __operable: asyncio.Event
        __play_lock: asyncio.Lock
        __repeat: bool
        __shuffle: bool
        __stop_request: bool
        __waiter: asyncio.Event
        bitrate: int
        playing: Optional[Union[Playlist, Track]]
        target: Optional[discord.abc.Messageable]

        # Override types from superclass
        channel: discord.VoiceChannel
        client: Haruka

    def __init__(self, client: Haruka, channel: discord.VoiceChannel) -> None:
        super().__init__(client, channel)
        self.__play_lock = asyncio.Lock()
        self.__operable = asyncio.Event()
        self.__repeat = False
        self.__shuffle = False
        self.__stop_request = False
        self.__waiter = asyncio.Event()
        self.bitrate = 128
        self.playing = None
        self.target = None

    @property
    def repeat(self) -> bool:
        """The current REPEAT mode"""
        return self.__repeat

    @property
    def shuffle(self) -> bool:
        """The current SHUFFLE mode"""
        return self.__shuffle

    def switch_repeat(self) -> None:
        self.__repeat = not self.__repeat

    def switch_shuffle(self) -> None:
        self.__shuffle = not self.__shuffle

    def set_source(self, source: Union[Playlist, Track]) -> None:
        """Set an audio source to be ready for playing"""
        if not isinstance(source, (Playlist, Track)):
            raise TypeError(f"Expected a Playlist or Track to be set, not {source.__class__.__name__}")

        self.playing = source

    def set_target(self, target: discord.abc.Messageable) -> None:
        if not isinstance(target, discord.abc.Messageable):
            raise TypeError(f"Expected a messagable channel to be set, not {target.__class__.__name__}")

        self.target = target

    def append_state(self, embed: discord.Embed) -> None:
        embed.add_field(
            name="Bitrate",
            value=f"{self.bitrate} kbps",
        )
        embed.add_field(
            name="`REPEAT` mode",
            value=self.__repeat,
        )
        embed.add_field(
            name="`SHUFFLE` mode",
            value=self.__shuffle,
        )

    async def notify(self, content: Optional[str] = None, **kwargs: Any) -> Optional[discord.Message]:
        with contextlib.suppress(discord.HTTPException, AttributeError):
            return await self.target.send(content, **kwargs)

    async def play(self) -> None:
        """This function is a coroutine

        Play audio of the current playlist or track. If the current source
        is a playlist, play it according to the current REPEAT or SHUFFLE
        mode. If the current source is a track, play it repeatedly regardless
        of the aforementioned modes.

        This function returns when the audio finishes playing.

        Raises
        -----
        `ValueError`: The set playlist is empty
        `TypeError`: No audio source was set or the audio source is invalid
        """
        async with self.__play_lock:
            source = self.playing
            if source is None:
                raise RuntimeError("No audio source was set")

            if isinstance(source, Playlist):
                tracks = source.tracks
                if not tracks:
                    raise ValueError("The provided playlist is empty")

                await self.notify(embed=await source.create_embed(self.client))

                index = 0
                self.__stop_request = False
                while self.is_connected() and not self.__stop_request:
                    await self.__play_track(tracks[index])
                    if not self.__repeat:
                        if self.__shuffle:
                            index += randint(0, len(tracks) - 1)
                        else:
                            index += 1

                        index %= len(tracks)

            elif isinstance(source, Track):
                self.__stop_request = False
                while self.is_connected() and not self.__stop_request:
                    await self.__play_track(source)

            else:
                raise TypeError(f"Expected a Playlist or Track to be set, not {source.__class__.__name__}")

    async def __play_track(self, track: Track) -> None:
        embed = await track.create_embed(self.client)
        try:
            audio_url = await track.get_audio_url()
        except Exception as exc:
            self.client.log(f"Unable to get audio URL for {track}\n" + utils.format_exception(exc))

            await self.client.report(f"Unable to get audio URL for track ID `{track.id}`", send_state=False)
            await self.notify("Unable to play this track, skipping.", embed=embed)
        else:
            def after(error: Optional[Exception]) -> None:
                self.__waiter.set()
                if error is not None:
                    self.client.log(utils.format_exception(error))

            before_options = (
                "-start_at_zero",
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "1",
            )
            options = (
                "-vn",
                "-filter:a", "volume=0.2",
            )

            with contextlib.suppress(discord.HTTPException):
                if self.target is not None:
                    await self.target.typing()

                source = discord.FFmpegOpusAudio(
                    audio_url,
                    bitrate=self.bitrate,
                    stderr=self.client.interface.logfile,
                    before_options=shlex.join(before_options),
                    options=shlex.join(options),
                )

                await self.notify(embed=embed)

            if self.__stop_request or not self.is_connected():
                return

            self.__waiter.clear()
            self.__operable.set()

            super().play(source, after=after)
            await self.__waiter.wait()

            self.__operable.clear()

    async def pause(self) -> None:
        await self.__operable.wait()
        if self.is_playing():
            super().pause()

    async def resume(self) -> None:
        await self.__operable.wait()
        if self.is_paused():
            super().resume()

    async def skip(self) -> None:
        await self.__operable.wait()
        super().stop()

    def stop(self) -> None:
        self.__stop_request = True
        super().stop()
