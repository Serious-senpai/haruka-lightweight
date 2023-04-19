from __future__ import annotations

from typing import Any, Dict, List, Union, overload

import discord
from discord.ext import commands


def _json_encode(obj: Any) -> Any:
    if obj is None:
        return None

    if isinstance(obj, commands.Command):
        return {
            "name": obj.name,
            "aliases": obj.aliases,
            "brief": obj.brief,
            "description": obj.description,
            "usage": obj.usage,
        }

    if isinstance(obj, discord.abc.User):
        return {
            "id": obj.id,
            "name": obj.name,
            "discriminator": obj.discriminator,
            "avatar": _json_encode(obj.avatar),
        }

    if isinstance(obj, discord.Asset):
        return {
            "key": obj.key,
            "url": obj.url,
        }

    if isinstance(obj, list):
        return [_json_encode(o) for o in obj]

    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if isinstance(key, str):
                result[key] = _json_encode(value)
            else:
                raise TypeError(f"Error encoding {obj}: Invalid key {key}")

        return result

    raise TypeError(f"Unsupported JSON encoding type {obj.__class__.__name__}")


@overload
def json_encode(data: None) -> None: ...


@overload
def json_encode(data: Union[commands.Command, discord.abc.User, discord.Asset, Dict[str, Any]]) -> Dict[str, Any]: ...


@overload
def json_encode(data: List[Any]) -> List[Any]: ...


def json_encode(data):
    """Encode data into JSON for sending over the network"""
    return _json_encode(data)
