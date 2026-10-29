"""Strict JSON primitives and deterministic identities for usage telemetry.

Set-valued paths and their ordering keys are supplied by the owning schema;
arrays at all other paths retain their order. These primitives do not validate
a complete envelope.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable, Iterable, Mapping

MAX_COUNTER = 9007199254740991
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?\Z")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _invalid_number(value: str) -> None:
    raise ValueError(f"unsupported JSON number: {value}")


def _integer(value: str) -> int:
    if value == "-0":
        raise ValueError("noncanonical integer")
    return int(value)


def parse_json(data: str | bytes) -> Any:
    """Parse JSON without duplicate keys, fractions, or non-finite numbers."""
    return json.loads(data, object_pairs_hook=_object, parse_int=_integer,
                      parse_float=_invalid_number, parse_constant=_invalid_number)


def validate_counter(value: Any) -> int:
    """Validate an observed nonnegative, interoperable integer counter."""
    if type(value) is not int or not 0 <= value <= MAX_COUNTER:
        raise ValueError("counter must be an integer within the observation range")
    return value


def validate_decimal(value: Any) -> str:
    """Validate a nonnegative canonical decimal string."""
    if not isinstance(value, str) or _DECIMAL.fullmatch(value) is None:
        raise ValueError("amount must be a canonical nonnegative decimal string")
    return value


def _encode(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, UnicodeError, ValueError) as error:
        raise ValueError("value cannot be encoded as canonical JSON") from error


def canonical_bytes(value: Any, *, set_paths: Iterable[tuple[str, ...]] = (),
                    set_keys: Mapping[tuple[str, ...], Callable[[Any], Any]] | None = None) -> bytes:
    """Sort declared sets by schema key; set_paths selects canonical-byte ordering."""
    if isinstance(value, dict) and "schema_version" in value:
        if type(value["schema_version"]) is not int or value["schema_version"] != 1:
            raise ValueError("unsupported schema version")
    paths = frozenset(tuple(path) for path in set_paths)
    keys = {tuple(path): key for path, key in (set_keys or {}).items()}
    if paths.intersection(keys):
        raise ValueError("set path has conflicting ordering declarations")

    def normalize(item: Any, path: tuple[str, ...]) -> Any:
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise ValueError("JSON object keys must be strings")
            return {key: normalize(child, path + (key,)) for key, child in item.items()}
        if isinstance(item, list):
            children = [normalize(child, path) for child in item]
            if path in keys:
                return sorted(children, key=lambda child: (keys[path](child), _encode(child)))
            return sorted(children, key=_encode) if path in paths else children
        if item is None or type(item) in (str, int, bool):
            return item
        raise ValueError("unsupported JSON value")

    return _encode(normalize(value, ()))


def content_id(value: Any, *, set_paths: Iterable[tuple[str, ...]] = (),
               set_keys: Mapping[tuple[str, ...], Callable[[Any], Any]] | None = None) -> str:
    """Return the SHA-256 identity of the complete canonical value."""
    return hashlib.sha256(canonical_bytes(value, set_paths=set_paths, set_keys=set_keys)).hexdigest()


def observation_id(value: dict[str, Any], *, set_paths: Iterable[tuple[str, ...]] = (),
                   set_keys: Mapping[tuple[str, ...], Callable[[Any], Any]] | None = None) -> str:
    """Return an observation identity without its own identifier field."""
    if not isinstance(value, dict):
        raise ValueError("observation must be an object")
    return content_id({key: item for key, item in value.items() if key != "id"},
                      set_paths=set_paths, set_keys=set_keys)
