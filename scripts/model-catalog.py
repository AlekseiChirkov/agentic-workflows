#!/usr/bin/env python3
"""Validate and inspect an optional local Markdown catalog without network access.

CLI: model-catalog.py [--catalog PATH] [--today YYYY-MM-DD] [--refresh CANDIDATE]
JSON reports use exit 0 for a usable catalog/successful refresh and 2 otherwise.
Only explicit refresh writes configuration; the candidate is supplied by its owner.

Schema version 1 has refreshed/evidence_date dates and exact model entries. A non-null
capability_evidence is an independently source-supported ordinal quality rating 1..5,
never a probability or a price-derived judgment. Uncalibrated/unknown capability is
null. price_snapshot references a separate owner's price evidence; no ledger is kept.
The human tier table is derived from this single structured payload.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

TIERS = ("light", "standard", "frontier")
TRAITS = ("creative", "heavy-reasoning", "mechanical")
PROVIDERS = ("anthropic", "openai")
AVAILABILITY = ("available", "unavailable", "unknown")
TABLE_HEADER = "| tier | anthropic model id | openai model id | relative cost |"
PAYLOAD_KEYS = {"schema_version", "refreshed", "evidence_date", "models"}
MODEL_KEYS = {"provider", "id", "tier", "availability", "context_window", "tools",
              "traits", "capability_evidence", "price_snapshot"}


class CatalogError(ValueError):
    """The supplied catalog cannot safely support deterministic selection."""


def _object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise CatalogError(f"{label}: expected exactly {', '.join(sorted(keys))}")
    return value


def _enum(value: Any, choices: tuple[str, ...], label: str) -> str:
    if not isinstance(value, str) or value not in choices:
        raise CatalogError(f"{label}: expected {' | '.join(choices)}")
    return value


def _date(value: Any, ceiling: date, label: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise CatalogError(f"{label}: expected an ISO YYYY-MM-DD date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise CatalogError(f"{label}: invalid calendar date") from error
    if parsed > ceiling:
        raise CatalogError(f"{label}: date exceeds {ceiling.isoformat()}")
    return parsed


def _unique_strings(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(
            not isinstance(item, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", item)
            for item in value):
        raise CatalogError(f"{label}: expected capability names as a string array")
    if len(value) != len(set(value)):
        raise CatalogError(f"{label}: duplicate value")
    return value


def _evidence(value: Any, ceiling: date, kind: str) -> None:
    if value is None:
        return
    metric = "quality" if kind == "capability_evidence" else "relative_cost"
    evidence = _object(value, {"reference", "date", metric}, kind)
    reference = evidence["reference"]
    if not isinstance(reference, str) or not reference.strip() or any(
            ord(character) < 32 for character in reference):
        raise CatalogError(f"{kind}: expected a nonempty source reference")
    _date(evidence["date"], ceiling, f"{kind}.date")
    number = evidence[metric]
    if metric == "quality":
        if type(number) is not int or not 1 <= number <= 5:
            raise CatalogError("capability_evidence.quality: expected an ordinal integer 1..5")
    elif (type(number) not in (int, float) or number <= 0 or number > sys.float_info.max
          or not math.isfinite(number)):
        raise CatalogError("price_snapshot.relative_cost: expected a finite positive number")


def _validate_models(value: Any, evidence_date: date) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise CatalogError("models: expected a nonempty array")
    identities: set[tuple[str, str]] = set()
    seen_tiers: set[str] = set()
    for raw in value:
        model = _object(raw, MODEL_KEYS, "model")
        provider = _enum(model["provider"], PROVIDERS, "model.provider")
        identity = model["id"]
        if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]*", identity):
            raise CatalogError("model.id: expected an exact identifier without whitespace")
        if (provider, identity) in identities:
            raise CatalogError("models: duplicate provider/model identity")
        identities.add((provider, identity))
        seen_tiers.add(_enum(model["tier"], TIERS, "model.tier"))
        _enum(model["availability"], AVAILABILITY, "model.availability")
        context = model["context_window"]
        if context is not None and (type(context) is not int or context <= 0):
            raise CatalogError("model.context_window: expected a positive integer or null")
        if model["tools"] is not None:
            _unique_strings(model["tools"], "model.tools")
        for trait in _unique_strings(model["traits"], "model.traits"):
            _enum(trait, TRAITS, "model.traits")
        _evidence(model["capability_evidence"], evidence_date, "capability_evidence")
        _evidence(model["price_snapshot"], evidence_date, "price_snapshot")
    if seen_tiers != set(TIERS):
        raise CatalogError("models: light, standard and frontier cost tiers must all be represented")
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError(f"JSON: duplicate key {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise CatalogError(f"JSON: non-finite number {value}")


def tier_rows(catalog: dict[str, Any]) -> list[list[str]]:
    """Derive display rows from already validated model entries, never quality bands."""
    rows = []
    for tier in TIERS:
        entries = sorted((model for model in catalog["models"] if model["tier"] == tier),
                         key=lambda model: model["id"])
        provider_ids = [", ".join(model["id"] for model in entries if model["provider"] == provider)
                        or "-" for provider in PROVIDERS]
        costs = []
        for model in entries:
            snapshot = model["price_snapshot"]
            relative_cost = format(snapshot["relative_cost"], "g") if snapshot else "unknown"
            costs.append(f"{model['id']}={relative_cost}")
        rows.append([tier, *provider_ids, "; ".join(costs) or "unknown"])
    return rows


def _validate_table(markdown: str, catalog: dict[str, Any]) -> None:
    lines = markdown.splitlines()
    headers = [index for index, line in enumerate(lines) if line.strip() == TABLE_HEADER]
    if len(headers) != 1:
        raise CatalogError("tier table: expected one canonical header")
    start = headers[0] + 1
    if start >= len(lines) or not re.fullmatch(r"\|\s*:?-+:?\s*" * 4 + r"\|", lines[start]):
        raise CatalogError("tier table: missing four-column Markdown separator")
    actual = []
    for line in lines[start + 1:]:
        if not line.strip().startswith("|"):
            break
        if not line.strip().endswith("|"):
            raise CatalogError("tier table: malformed row")
        actual.append([cell.strip() for cell in line.strip()[1:-1].split("|")])
    if actual != tier_rows(catalog):
        raise CatalogError("tier table: rows differ from the canonical structured payload")


def validate_catalog(markdown: str, today: date) -> dict[str, Any]:
    """Return the strict canonical payload or raise CatalogError without any I/O."""
    markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.findall(r"^```json model-catalog[ \t]*\n(.*?)^```[ \t]*$", markdown,
                        re.MULTILINE | re.DOTALL)
    if len(blocks) != 1:
        raise CatalogError("catalog: expected exactly one fenced json model-catalog payload")
    try:
        decoded = json.loads(blocks[0], object_pairs_hook=_unique_object,
                             parse_constant=_reject_constant)
    except (ValueError, RecursionError) as error:
        raise CatalogError(f"catalog: invalid JSON payload ({error})") from error
    catalog = _object(decoded, PAYLOAD_KEYS, "catalog")
    if type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1:
        raise CatalogError("schema_version: unsupported version; expected integer 1")
    refreshed = _date(catalog["refreshed"], today, "refreshed")
    evidence_date = _date(catalog["evidence_date"], refreshed, "evidence_date")
    _validate_models(catalog["models"], evidence_date)
    _validate_table(markdown, catalog)
    return catalog


def _usable_report(catalog: dict[str, Any], today: date) -> dict[str, Any]:
    age = (today - date.fromisoformat(catalog["refreshed"])).days
    status = "fresh" if age < 14 else "dated" if age <= 30 else "stale"
    prefix = {"fresh": "Fresh catalog", "dated": "Dated catalog notice",
              "stale": "Stale catalog warning"}[status]
    return {"status": status, "age_days": age, "selection_available": True,
            "session_action": "preserve", "catalog": catalog, "errors": [], "refreshed": False,
            "notice": f"{prefix}: refreshed {catalog['refreshed']}, {age} days old; "
                      f"evidence dated {catalog['evidence_date']}."}


def inspect_catalog(path: Path, today: date) -> dict[str, Any]:
    """Read local configuration only; missing or invalid input preserves the session."""
    try:
        catalog = validate_catalog(Path(path).read_text(encoding="utf-8"), today)
    except (OSError, UnicodeError, CatalogError) as error:
        return {"status": "unavailable", "age_days": None, "selection_available": False,
                "session_action": "preserve", "catalog": None, "errors": [str(error)],
                "refreshed": False,
                "notice": "Catalog selection unavailable; preserve the session default."}
    return _usable_report(catalog, today)


def refresh_catalog(path: Path, candidate: Path, today: date) -> dict[str, Any]:
    """Validate supplied bytes before staging and atomically replacing one local file."""
    path, candidate = Path(path), Path(candidate)
    temporary: Path | None = None
    report: dict[str, Any] | None = None
    try:
        content = candidate.read_bytes()
        catalog = validate_catalog(content.decode("utf-8"), today)
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="wb", prefix=".model-catalog-", suffix=".tmp",
                                         dir=path.parent, delete=False) as staging:
            temporary = Path(staging.name)
            staging.write(content)
            staging.flush()
            os.fsync(staging.fileno())
        os.replace(temporary, path)
        temporary = None
        report = _usable_report(catalog, today)
        report["refreshed"] = True
        return report
    except (OSError, UnicodeError, CatalogError) as error:
        report = inspect_catalog(path, today)
        report["errors"].append(f"Refresh rejected: {error}")
        return report
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as error:
                if report is not None:
                    report["errors"].append(f"Temporary catalog cleanup failed: {error}")


def default_catalog_path() -> Path:
    """Honor an explicit XDG root; otherwise use ~/.config/orchestrail/model-catalog.md."""
    config = os.environ.get("XDG_CONFIG_HOME")
    root = Path(config) if config else Path.home() / ".config"
    return root / "orchestrail" / "model-catalog.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=default_catalog_path())
    parser.add_argument("--today", default=date.today().isoformat(), metavar="YYYY-MM-DD")
    parser.add_argument("--refresh", type=Path, metavar="CANDIDATE",
                        help="explicitly validate and atomically install this offline candidate")
    arguments = parser.parse_args(argv)
    try:
        today = date.fromisoformat(arguments.today)
        _date(arguments.today, today, "--today")
    except (ValueError, CatalogError):
        parser.error("--today requires an ISO YYYY-MM-DD calendar date")
    report = (refresh_catalog(arguments.catalog, arguments.refresh, today)
              if arguments.refresh is not None else inspect_catalog(arguments.catalog, today))
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    successful = report["refreshed"] if arguments.refresh is not None else report["selection_available"]
    return 0 if successful else 2


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        raise SystemExit("model catalog requires Python 3.11 or newer")
    raise SystemExit(main())
