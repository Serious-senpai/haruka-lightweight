from __future__ import annotations

import asyncio
import contextlib
import time
import traceback
from functools import partial
from inspect import iscoroutinefunction
from types import TracebackType
from typing import Any, Callable, Coroutine, Generic, Iterable, Iterator, List, Optional, Set, Type, TypeVar, TYPE_CHECKING

import discord
from discord.ext import commands
from typing_extensions import ParamSpec

from environment import DEFAULT_COMMAND_PREFIX, FUZZY_MATCH
if TYPE_CHECKING:
    from haruka import Haruka


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

    return None


async def get_prefixes(bot: Haruka, message: discord.Message) -> List[str]:
    """This function is a coroutine

    Get all acceptable prefixes of the current invocation
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
    prefixes = []
    custom_prefix = await get_custom_prefix(bot, message)
    if custom_prefix is not None:
        prefixes.append(custom_prefix)

    getter = commands.when_mentioned_or(*prefixes)
    return getter(bot, message)


async def get_prefix(bot: Haruka, message: discord.Message) -> str:
    """This function is a coroutine

    Get a prefix of the current invocation context. Prioritize
    the custom prefix over mention-as-prefix ones.

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

    prefixes = await get_prefixes(bot, message)
    return prefixes[-1]


def get_all_subclasses(cls: Type[T]) -> Iterator[Type[T]]:
    """A generator that yields all subclasses of a class"""
    for subclass in cls.__subclasses__():
        yield subclass
        yield from get_all_subclasses(subclass)


def format_permission_name(permission: str) -> str:
    return permission.replace("_", " ").replace("guild", "server").title()


class MaxRetryReached(Exception):
    """Exception raised when running out of retries"""

    __slots__ = (
        "max_retry",
        "original",
    )
    if TYPE_CHECKING:
        max_retry: int
        original: Exception

    def __init__(self, max_retry: int, original: Exception) -> None:
        self.max_retry = max_retry
        self.original = original
        super().__init__(f"Process failed after retrying {max_retry} times")


def retry(max_retry: int, *, wait: float = 0.0) -> Callable[[Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]]:
    """Decorator for an async function that allows retrying for a given
    number of times.

    When running out of retries, throw ``MaxRetryReached``.

    Parameters
    -----
    max_retry: ``int``
        The maximum number of times to retry
    wait: ``float``
        The duration (in seconds) to wait between 2 consecutive retries
    """
    def decorator(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            retry = max_retry
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    retry -= 1
                    if retry > 0:
                        await asyncio.sleep(wait)
                    else:
                        raise MaxRetryReached(max_retry, exc) from exc

        return wrapper

    return decorator


def format_exception(error: Exception) -> str:
    return "".join(traceback.format_exception(error.__class__, error, error.__traceback__))


def slice_string(string: str, limit: int, *, reverse: bool = False) -> str:
    if len(string) < limit:
        return string

    return "[...]" + string[-limit:] if reverse else string[:limit] + "[...]"


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
        return None

    if message.reference.cached_message:
        return message.reference.cached_message

    with contextlib.suppress(discord.HTTPException):
        return await message.channel.fetch_message(message.reference.message_id)


async def fuzzy_match(string: str, against: Iterable[str]) -> str:
    args = [FUZZY_MATCH]
    args.append(string)
    args.extend(against)

    process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await process.communicate()
    return stdout.decode("utf-8")


async def coro_func(value: T) -> T:
    return value


INSTANCE_T = TypeVar("INSTANCE_T")


class ExtendedCoroutineFunction(Generic[P, T]):

    __slots__ = (
        "_callbacks",
        "_func",
        "_injected",
    )
    if TYPE_CHECKING:
        _callbacks: Set[Callable[[T], Coroutine[Any, Any, Any]]]
        _func: Callable[P, Coroutine[Any, Any, T]]
        _injected: Any

    def __init__(self, func: Callable[P, Coroutine[Any, Any, T]]) -> None:
        self._callbacks = set()
        self._func = func
        if not iscoroutinefunction(func):
            message = f"Expected a coroutine function, not {func.__class__.__name__}"
            raise TypeError(message)

        self._injected = None

    def __get__(self, instance: INSTANCE_T, _: Type[INSTANCE_T]) -> ExtendedCoroutineFunction[P, T, INSTANCE_T]:
        if instance is None:
            return self

        copy = ExtendedCoroutineFunction(self._func)
        copy._callbacks = self._callbacks
        copy._injected = instance
        return copy

    def add_callback(self, callback: Callable[[T], Coroutine[Any, Any, Any]], /) -> None:
        """Add a callback to be invoked whenever this coroutine function completes."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[T], Coroutine[Any, Any, Any]], /) -> None:
        with contextlib.suppress(KeyError):
            self._callbacks.remove(callback)

    async def invoke(self, *args: Any, **kwargs: Any) -> T:
        func = self._func if self._injected is None else partial(self._func, self._injected)
        result = await func(*args, **kwargs)
        if len(self._callbacks) > 0:
            await asyncio.wait([callback(result) for callback in self._callbacks])

        return result

    def __call__(self, *args: Any, **kwargs: Any) -> Coroutine[Any, Any, T]:
        return self.invoke(*args, **kwargs)
