from __future__ import annotations

from typing import Any, Dict, List, Union

import discord
from discord.ext import commands
from frozenlist import FrozenList

import utils


class Serializable:
    def to_json(self) -> Union[List[Any], Dict[str, Any]]:
        raise NotImplementedError


def json_encode(obj: Any) -> Any:
    if obj is None:
        return None

    if isinstance(obj, Serializable):
        return obj.to_json()

    if isinstance(obj, commands.Command):
        command = utils.fill_command_metadata(obj, prefix="$")
        return {
            "name": command.name,
            "aliases": command.aliases,
            "brief": command.brief,
            "description": command.description,
            "usage": command.usage,
        }

    if isinstance(obj, discord.abc.User):
        return {
            "id": str(obj.id),
            "name": obj.display_name,
            "avatar": json_encode(obj.display_avatar),
        }

    if isinstance(obj, discord.Asset):
        return {
            "key": obj.key,
            "url": obj.url,
        }

    if isinstance(obj, (int, str)):
        return obj

    if isinstance(obj, (list, tuple, FrozenList)):
        return [json_encode(o) for o in obj]

    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if isinstance(key, str):
                result[key] = json_encode(value)
            else:
                raise TypeError(f"Error encoding {obj}: Invalid key {key}")

        return result

    raise TypeError(f"Unsupported JSON encoding type {obj.__class__.__name__}")
