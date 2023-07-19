from __future__ import annotations

import asyncio
import contextlib
import datetime
import time
import traceback
from types import TracebackType
from typing import Awaitable, Callable, Iterator, List, Optional, ParamSpec, Type, TypeVar, TYPE_CHECKING

import discord
from discord.ext import commands

from environment import DEFAULT_COMMAND_PREFIX, FUZZY_MATCH
if TYPE_CHECKING:
    from haruka import Haruka


if TYPE_CHECKING:
    T = TypeVar("T")
    P = ParamSpec("P")


def fill_command_metadata(command: commands.Command, *, prefix: str) -> commands.Command:
    """Return a copy of `command` with the appropriate metadata"""
    command = command.copy()
    if command.aliases and command.qualified_name not in command.aliases:
        assert isinstance(command.aliases, list)
        command.aliases.insert(0, command.qualified_name)
    elif not command.aliases:
        command.aliases = [command.qualified_name]

    if command.usage is None:
        command.usage = prefix + command.qualified_name

    command.usage = command.usage.format(prefix=prefix)
    command.description = command.description.format(prefix=prefix)

    return command


def fill_group_metadata(group: commands.Group) -> commands.Group:
    """Return a copy of `group` with the appropriate metadata"""
    group = group.copy()
    if group.aliases and group.aliases not in group.aliases:
        assert isinstance(group.aliases, list)
        group.aliases.insert(0, group.qualified_name)
    elif not group.aliases:
        group.aliases = [group.qualified_name]

    return group


async def get_custom_prefix(bot: Haruka, message: discord.Message) -> Optional[str]:
    """This function is a coroutine

    Attempt to get the custom prefix of the current invocation
    context.

    Parameters
    -----
    bot: ``Haruka``
        The bot to handle the command
    message: ``discord.Message``
        The message to check for command prefix

    Returns
    -----
    Optional[``str``]
        The custom prefix of the current invocation context, will
        be None if the database pool hasn't been initialized yet
    """
    if message.guild is None:
        return DEFAULT_COMMAND_PREFIX

    pool = bot.pool
    if pool is not None:
        async with pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT pref FROM prefix WHERE id = ?", str(message.guild.id))
                row = await cursor.fetchone()
                return DEFAULT_COMMAND_PREFIX if row is None else row[0]


async def get_prefixes(bot: Haruka, message: discord.Message) -> List[str]:
    prefixes = []
    custom_prefix = await get_custom_prefix(bot, message)
    if custom_prefix is not None:
        prefixes.append(custom_prefix)

    getter = commands.when_mentioned_or(*prefixes)
    return getter(bot, message)


async def get_prefix(bot: Haruka, message: discord.Message) -> str:
    prefixes = await get_prefixes(bot, message)
    return prefixes[-1]


def get_all_subclasses(cls: Type[T]) -> Iterator[Type[T]]:
    """A generator that yields all subclasses of a class"""
    for subclass in cls.__subclasses__():
        yield subclass
        yield from get_all_subclasses(subclass)


def max_retry(retry_count: int, *, sleep: float = 0.0) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            retry = retry_count
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception:
                    retry -= 1
                    if retry > 0:
                        await asyncio.sleep(sleep)
                    else:
                        raise

        return wrapper

    return decorator


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


async def fuzzy_match(string: str, against: Iterator[str]) -> str:
    args = [FUZZY_MATCH]
    args.append(string)
    args.extend(against)

    process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await process.communicate()
    return stdout.decode("utf-8")


async def coro_func(value: T) -> T:
    return value


EPOCH = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


def from_unix_format(seconds: int) -> datetime.datetime:
    return EPOCH + datetime.timedelta(seconds=seconds)
