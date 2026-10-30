"""Evaluate duration warnings from explicitly supplied evidence only.

A corpus digest identifies a corpus; it does not prove sample provenance.
"""

from datetime import datetime
from fractions import Fraction
import math
import re


_GROUP_FIELDS = frozenset({"stage", "duration_kind", "clock_quality", "environment",
                           "profile", "contract", "configuration"})
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\Z")


def _time(value):
    if not isinstance(value, str) or not _TIMESTAMP.fullmatch(value):
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None


def _seconds(value):
    if isinstance(value, str):
        if len(value) > 256 or not re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]{1,3})?', value):
            return None
        return Fraction(value)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value < 0:
        return None
    return Fraction(value)


def _group(value):
    return (isinstance(value, dict) and set(value) == _GROUP_FIELDS
            and all(isinstance(item, str) and item for item in value.values()))


def _eligible_history(history, candidate, now):
    if (not isinstance(history, dict) or type(history.get("schema_version")) is not int
            or history["schema_version"] != 1):
        return None
    group = history.get("group")
    if not _group(group) or group != candidate.get("group"):
        return None
    digest = history.get("corpus_hash")
    if not isinstance(digest, str) or not _HASH.fullmatch(digest):
        return None
    current = _time(now)
    start = _time(history.get("window_start"))
    end = _time(history.get("window_end"))
    created = _time(history.get("created_at"))
    expires = _time(history.get("expires_at"))
    if any(value is None for value in (current, start, end, created, expires)):
        return None
    if not (start <= end <= created <= current < expires):
        return None
    samples = history.get("samples")
    if not isinstance(samples, list):
        return None
    eligible = []
    seen = set()
    for item in samples:
        if not isinstance(item, dict):
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier or identifier == candidate.get("id"):
            continue
        if identifier in seen:
            return None
        seen.add(identifier)
        duration = _seconds(item.get("seconds"))
        if (duration is None or item.get("closed") is not True
                or item.get("kind") != group["duration_kind"]
                or item.get("kind") not in ("work", "run")
                or item.get("clock_quality") != "measured"
                or item.get("group") != group):
            continue
        eligible.append(duration)
    eligible.sort()
    size = history.get("sample_size")
    if type(size) is not int or size != len(eligible) or size < 5:
        return None
    middle = len(eligible) // 2
    if len(eligible) % 2:
        median = eligible[middle]
    else:
        median = (eligible[middle - 1] + eligible[middle]) / 2
    declared = history.get("median")
    if (not isinstance(declared, str) or len(declared) > 128
            or not re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", declared)):
        return None
    if Fraction(declared) != median:
        return None
    return median


def evaluate_duration(candidate, history, observed_at):
    """Evaluate one closed interval without reading or writing external state.

    History is a caller-provided sample export, never a discovery request.
    Invalid exports fall back to two hours. Five compatible measured samples
    additionally require exceeding three times their median.
    """
    if not isinstance(candidate, dict):
        return {"available": False, "reason": "clock_unavailable"}
    duration = _seconds(candidate.get("seconds"))
    quality = candidate.get("clock_quality")
    if duration is None or quality not in ("measured", "approximate"):
        return {"available": False, "reason": "clock_unavailable"}
    if candidate.get("closed") is not True:
        return {"available": False, "reason": "interval_unclosed"}
    approximate = quality == "approximate"
    median = None
    group = candidate.get("group")
    if (not approximate and _group(group) and group["clock_quality"] == quality
            and isinstance(candidate.get("id"), str) and candidate["id"]):
        median = _eligible_history(history, candidate, observed_at)
    warn = duration > 7200 and (median is None or duration > 3 * median)
    return {"available": True, "warn": warn, "historical": median is not None,
            "approximate": approximate}
