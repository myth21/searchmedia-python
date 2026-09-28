"""Helpers for the mappers: turn a JSON list or object map into a list, and read a nested field without failing when something on the path is missing or has the wrong type."""

from typing import Any


def iterable_items(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value

    if isinstance(value, dict):
        return list(value.values())

    return []


def nested(item: Any, *path: str) -> Any:
    for key in path:
        if not isinstance(item, dict):
            return None

        item = item.get(key)

    return item
