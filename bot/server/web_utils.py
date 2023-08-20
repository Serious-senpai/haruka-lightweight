from __future__ import annotations

from typing import Any, Dict, List, Protocol, Tuple, TypedDict, TypeVar, overload, runtime_checkable

from discord import Asset, abc
from discord.ext import commands
from frozenlist import FrozenList

import utils
from environment import DEFAULT_COMMAND_PREFIX


__all__ = (
    "json_encode",
)


JsonT = TypeVar("JsonT", List[Any], Dict[str, Any])
T = TypeVar("T")


class _CommandData(TypedDict):
    name: str
    aliases: List[str]
    brief: str
    description: str
    usage: str


class _UserData(TypedDict):
    id: str
    name: str
    avatar: _AssetData


class _AssetData(TypedDict):
    key: str
    url: str


@runtime_checkable
class _Serializable(Protocol[JsonT]):
    def to_json(self) -> JsonT:
        raise NotImplementedError


@overload
def json_encode(value: None, /) -> None: ...
@overload
def json_encode(value: _Serializable[JsonT], /) -> JsonT: ...
@overload
def json_encode(value: commands.Command, /) -> _CommandData: ...
@overload
def json_encode(value: abc.User, /) -> _UserData: ...
@overload
def json_encode(value: Asset, /) -> _AssetData: ...
@overload
def json_encode(value: float, /) -> float: ...
@overload
def json_encode(value: int, /) -> int: ...
@overload
def json_encode(value: str, /) -> str: ...
@overload
def json_encode(value: List[Any], /) -> List[Any]: ...
@overload
def json_encode(value: Tuple[Any], /) -> List[Any]: ...
@overload
def json_encode(value: FrozenList[Any], /) -> List[Any]: ...
@overload
def json_encode(value: Dict[str, Any], /) -> Dict[str, Any]: ...


def json_encode(value, /):
    if value is None:
        return None

    if isinstance(value, _Serializable):
        return value.to_json()

    if isinstance(value, commands.Command):
        command = utils.fill_command_metadata(value, prefix=DEFAULT_COMMAND_PREFIX)
        return {
            "name": command.name,
            "aliases": list(command.aliases),
            "brief": command.brief,
            "description": command.description,
            "usage": command.usage,
        }

    if isinstance(value, abc.User):
        return {
            "id": str(value.id),
            "name": value.display_name,
            "avatar": json_encode(value.display_avatar),
        }

    if isinstance(value, Asset):
        return {
            "key": value.key,
            "url": value.url,
        }

    if isinstance(value, (int, str)):
        return value

    if isinstance(value, (list, tuple, FrozenList)):
        return [json_encode(o) for o in value]

    if isinstance(value, dict):
        result = {}
        for key, value in value.items():
            if isinstance(key, str):
                result[key] = json_encode(value)
            else:
                raise TypeError(f"Error encoding {value!r}: Invalid key {key!r}")

        return result

    raise TypeError(f"Unsupported JSON encoding type {value.__class__.__name__}")
