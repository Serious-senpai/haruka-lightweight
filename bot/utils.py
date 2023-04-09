from __future__ import annotations

import asyncio
import contextlib
import datetime
import re
import time
import traceback
from types import TracebackType
from typing import Iterator, Optional, Type, TypeVar, TYPE_CHECKING

import discord

from environment import FUZZY_SCRIPT


T = TypeVar("T")


def get_all_subclasses(cls: Type[T]) -> Iterator[Type[T]]:
    """A generator that yields all subclasses of a class"""
    for subclass in cls.__subclasses__():
        yield subclass
        yield from get_all_subclasses(subclass)


def format_exception(error: Exception) -> str:
    return "".join(traceback.format_exception(error.__class__, error, error.__traceback__))


def slice_string(string: str, limit: int) -> str:
    if len(string) < limit:
        return string

    return string[:limit] + " [...]"


def format(time: float) -> str:
    """Format a given time based on its value.

    Parameters
    -----
    time: ``float``
        The given time, in seconds.

    Returns
    -----
    ``str``
        The formated time (e.g. ``1.50 s``)
    """
    time = float(time)

    if time < 0:
        raise ValueError("time must be a positive value")

    elif time < 1:
        return "{:.2f} ms".format(1000 * time)

    else:
        days = int(time / 86400)
        time -= days * 86400
        hours = int(time / 3600)
        time -= hours * 3600
        minutes = int(time / 60)
        time -= minutes * 60

        ret = []
        if days > 0:
            ret.append(f"{days}d")

        if hours > 0:
            ret.append(f"{hours}h")

        if minutes > 0:
            ret.append(f"{minutes}m")

        if time > 0:
            if time.is_integer():
                ret.append(f"{int(time)}s")
            else:
                ret.append("{:.2f}s".format(time))

        return " ".join(ret)


class TimingContextManager(contextlib.AbstractContextManager):
    """Measure the execution time of a code block."""

    __slots__ = (
        "__result",
        "_start",
    )
    if TYPE_CHECKING:
        __result: Optional[float]
        _start: float

    def __init__(self) -> None:
        self._start = time.perf_counter()
        self.__result = None

    def __enter__(self) -> TimingContextManager:
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> None:
        self.__result = time.perf_counter() - self._start

    @property
    def result(self) -> float:
        """The execution time since the entrance of this
        context manager. Note that this property will
        be unchanged after exiting the code block.
        """
        if self.__result is None:
            return time.perf_counter() - self._start

        return self.__result


async def get_reply(message: discord.Message) -> Optional[discord.Message]:
    """This function is a coroutine

    Get the message that ``message`` is replying (to be precise,
    refering) to

    Parameters
    -----
    message: ``discord.Message``
        The target message to fetch information about

    Returns
    -----
    Optional[``discord.Message``]
        The message that this message refers to
    """
    if not message.reference:
        return

    if message.reference.cached_message:
        return message.reference.cached_message

    with contextlib.suppress(discord.HTTPException):
        return await message.channel.fetch_message(message.reference.message_id)


async def fuzzy_match(string: str, against: Iterator[str], *, pattern: str = r"\w+") -> str:
    args = [FUZZY_SCRIPT]
    args.append(string)
    args.extend(against)

    process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE)
    _stdout, _ = await process.communicate()
    stdout = _stdout.decode("utf-8")
    match = re.search(pattern, stdout)
    if match is not None:
        return match.group()

    raise RuntimeError(f"Cannot match regex pattern {repr(pattern)} with stdout {stdout}")


async def coro_func(value: T) -> T:
    return value


EPOCH = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


def from_unix_format(seconds: int) -> datetime.datetime:
    return EPOCH + datetime.timedelta(seconds=seconds)
