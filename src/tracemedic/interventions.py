"""Bounded JSON replacements for trusted fixture experiments; no source edits."""

import copy
import json


def validate_changes(changes):
    if not isinstance(changes, list) or not 1 <= len(changes) <= 2:
        raise ValueError("Supply one or two JSON replacements")
    serialized = json.dumps(changes, allow_nan=False)
    if len(serialized.encode()) > 4096:
        raise ValueError("Changes exceed 4096 bytes")
    pointers = set()

    def bounded(value, depth=0):
        if depth > 4:
            raise ValueError("Replacement values may nest at most four levels")
        if isinstance(value, (dict, list)):
            if len(value) > 64:
                raise ValueError("Replacement collections are limited to 64 entries")
            for child in value.values() if isinstance(value, dict) else value:
                bounded(child, depth + 1)
        elif isinstance(value, str) and len(value) > 1024:
            raise ValueError("Replacement strings are limited to 1024 characters")
        elif isinstance(value, (int, float)) and abs(value) > 1_000_000_000:
            raise ValueError("Replacement numbers exceed supported magnitude")

    for change in changes:
        if not isinstance(change, dict) or set(change) != {"path", "value"}:
            raise ValueError("Each change needs exactly path and value")
        pointer = change["path"]
        if not isinstance(pointer, str) or len(pointer) > 200:
            raise ValueError("Invalid JSON pointer")
        parts = pointer.split("/")
        if not 3 <= len(parts) <= 6 or parts[0] != "" or parts[1] not in {"settings", "input"}:
            raise ValueError("Only existing /settings/... or /input/... values can change")
        if any(not p for p in parts[2:]) or pointer in pointers:
            raise ValueError("Empty or repeated JSON pointer")
        pointers.add(pointer)
        bounded(change["value"])


def apply_changes(config, data, changes):
    validate_changes(changes)
    documents = {"settings": copy.deepcopy(config), "input": copy.deepcopy(data)}
    for change in changes:
        parts = [p.replace("~1", "/").replace("~0", "~") for p in change["path"].split("/")[1:]]
        target = documents
        for key in parts[:-1]:
            target = target[int(key)] if isinstance(target, list) else target[key]
        key = parts[-1]
        if isinstance(target, list):
            index = int(key)
            if str(index) != key or not 0 <= index < len(target):
                raise ValueError("List index must name an existing element")
            target[index] = change["value"]
        elif isinstance(target, dict) and key in target:
            target[key] = change["value"]
        else:
            raise ValueError("JSON pointer must name an existing value")
    return documents["settings"], documents["input"]
