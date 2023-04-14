from __future__ import annotations

import asyncio
from typing import Optional

import discord
from discord.ext import commands

from customs import Context
from lib import youtube
from shared import interface


async def join_voice(ctx: Context, channel: discord.VoiceChannel) -> youtube.AudioPlayer:
    vc: Optional[youtube.AudioPlayer] = ctx.voice_client
    if vc is None:
        return await channel.connect(cls=youtube.AudioPlayer)

    await vc.move_to(channel)
    vc.stop()  # Stop audio if already playing
    return vc


@interface.command(
    name="play",
    brief="music.play",
    description="Play audio from YouTube. `URL` can be a URL to a YouTube video or a YouTube playlist.",
    usage="play <URL>",
)
@commands.max_concurrency(1, commands.BucketType.guild, wait=True)
async def _handler(ctx: Context, url: str) -> None:
    if ctx.author.voice is None:
        await ctx.send("Please join a voice channel first!")
        return

    channel = ctx.author.voice.channel
    if not isinstance(channel, discord.VoiceChannel):
        await ctx.send("Playing music is only supported for voice channels!")
        return

    async with ctx.typing():
        track = await youtube.Track.from_url(url)
        if track is not None:
            client = await join_voice(ctx, channel)
            client.set_source(track)
            client.set_target(ctx.channel)
            asyncio.create_task(client.play())

            return

        playlist = await youtube.Playlist.from_url(url)
        if playlist is not None:
            client = await join_voice(ctx, channel)
            client.set_source(playlist)
            client.set_target(ctx.channel)
            asyncio.create_task(client.play())

            return

        await ctx.send(f"Cannot find any videos or public playlists from the URL `{url}`")
