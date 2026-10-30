"""Strict JSON primitives and deterministic identities for usage telemetry.

Set-valued paths and their ordering keys are supplied by the owning schema;
arrays at all other paths retain their order. These primitives do not validate
a complete envelope.
"""

from __future__ import annotations

import copy
import hashlib
from datetime import datetime
from fractions import Fraction
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlsplit

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


MEASUREMENT_STATES = frozenset({"partial", "final", "unavailable", "conflicted"})
MEASUREMENT_REASONS = frozenset({
    "source_unavailable", "incomplete_source", "conflicting_evidence",
    "unsupported_profile", "invalid_schema", "invalid_counter", "counter_conflict",
    "inventory_unknown", "stream_incomplete", "identity_unresolved", "revision_conflict",
    "unpriced_component", "attribution_unverified", "timing_unavailable",
    "source_record_quarantined", "source_changed", "digest_mismatch", "scope_violation",
    "forbidden_field", "input_limit_exceeded", "projection_mismatch", "publication_conflict",
    "stored_artifact_corrupt", "io_unavailable", "collection_disabled",
    "dependency_unavailable", "policy_unavailable", "delivery_pending",
    "accepted_denominator_zero", "comparison_ineligible",
})


def validate_measurement(value: Any, *, allow_derived: bool = False) -> dict[str, Any]:
    """Validate structure only; consumers must verify evidence and its scope.

    An evidence reference is the SHA-256 of a sanitized evidence object. Its
    syntax does not establish that the object is safe, authentic, or relevant.
    Consumers must verify the object and its connection to the measurement.
    """
    if not isinstance(value, dict) or set(value) - {
        "measurement_state", "value", "reasons", "evidence"
    }:
        raise ValueError("invalid measurement fields")
    state = value.get("measurement_state")
    if not isinstance(state, str) or state not in MEASUREMENT_STATES:
        raise ValueError("invalid measurement state")
    reasons = value.get("reasons")
    if not isinstance(reasons, list) or any(
        not isinstance(reason, str) or reason not in MEASUREMENT_REASONS
        for reason in reasons
    ):
        raise ValueError("invalid measurement reasons")
    if len(set(reasons)) != len(reasons):
        raise ValueError("duplicate measurement reason")
    evidence = value.get("evidence")
    if "evidence" in value and (
        not isinstance(evidence, str) or re.fullmatch(r"[0-9a-f]{64}", evidence) is None
    ):
        raise ValueError("invalid measurement evidence reference")
    if state == "conflicted" and not reasons:
        raise ValueError("conflicted measurement requires a reason")
    if "value" not in value:
        if state == "final":
            raise ValueError("final measurement requires a value")
        if not reasons:
            raise ValueError("missing measurement requires a reason")
    else:
        if state == "unavailable":
            raise ValueError("unavailable measurement must omit its value")
        counter = value["value"]
        if allow_derived and isinstance(counter, str):
            if re.fullmatch(r"0|[1-9][0-9]*", counter) is None:
                raise ValueError("invalid derived counter")
            counter = int(counter)
        else:
            counter = validate_counter(counter)
        if counter == 0 and evidence is None:
            raise ValueError("zero measurement requires evidence")
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

    kind = value.get("kind") if isinstance(value, dict) else None
    envelope = isinstance(kind, str) and kind in {"request_usage", "inventory", "reported_aggregate", "usage_bundle"}

    def schema_set(path: tuple[str, ...]) -> bool:
        if kind == "tool_usage" and path == ("evidence_objects",):
            return True
        if (kind == "resolution_context_evidence" and path == ("context", "evidence_objects") or
                kind == "usage_bundle" and path == ("evidence_objects", "context", "evidence_objects") or
                kind == "current_run_snapshot" and path == ("bundles", "evidence_objects", "context", "evidence_objects")):
            return True
        if ((kind == "outcome_attempt" and path == ("response_ids",)) or
                (kind == "duration_graph" and path == ("event_hashes",)) or
                (kind == "experimental_inventory" and path == ("expected_attempt_ids",)) or
                (kind == "ownership_selection" and path in {("owner_scopes",), ("entries",), ("entries", "attribution", "candidates")})):
            return True
        if kind == "derived_measurement_evidence" and path in {
            ("operands",), ("profile", "counter_fields"), ("profile", "counter_fields", "includes"),
            ("profile", "known_gaps"), ("profile", "finality", "signals"),
        }:
            return True
        if kind == "usage_bundle" and path in {
            ("evidence_objects", "operands"), ("evidence_objects", "profile", "counter_fields"),
            ("evidence_objects", "profile", "counter_fields", "includes"),
            ("evidence_objects", "profile", "known_gaps"),
            ("evidence_objects", "profile", "finality", "signals"),
        }:
            return True
        if kind == "current_run_snapshot":
            if path in {("segments",), ("accepted_receipts",), ("bundles",),
                        ("inventories",), ("inventory_evidence",), ("warning_delivery",),
                        ("parts",), ("part_references",), ("duration_inputs",), ("duration_inputs", "history", "samples"), ("accepted_receipts", "observation_ids"),
                        ("inventories", "expected_calls"), ("inventories", "expected_responses"),
                        ("inventories", "unresolved_slots"), ("bundles", "sources"),
                        ("bundles", "observations"), ("bundles", "evidence_objects"),
                        ("bundles", "inventories"), ("bundles", "segments"),
                        ("bundles", "diagnostics"), ("bundles", "inventories", "expected_calls"),
                        ("bundles", "inventories", "expected_responses"),
                        ("bundles", "inventories", "unresolved_slots"),
                        ("analysis_inputs", "contexts"), ("analysis_inputs", "contexts", "evidence_objects"),
                        ("analysis_inputs", "snapshots"), ("analysis_inputs", "snapshots", "aliases"),
                        ("analysis_inputs", "snapshots", "rates"), ("analysis_inputs", "snapshots", "primary_sources"),
                        ("analysis_inputs", "price_evidence"), ("analysis_inputs", "ownership_evidence"),
                        ("analysis_inputs", "profile", "counter_fields"),
                        ("analysis_inputs", "profile", "counter_fields", "includes"),
                        ("analysis_inputs", "profile", "known_gaps"),
                        ("analysis_inputs", "profile", "finality", "signals"),
                        ("analysis_inputs", "scenario", "snapshot_ids"),
                        ("analysis_inputs", "scenario", "threshold_rules"),
                        ("analysis_inputs", "scenario", "threshold_rules", "components")}:
                return True
            if path[-2:] == ("attribution", "candidates"):
                return True
            if len(path) >= 3 and path[-3] == "measurements" and path[-1] == "reasons":
                return True
        if kind == "lifecycle_projection" and path in {
            ("contributors",), ("contributors", "observation_ids"),
            ("evidence_objects",), ("price_snapshots",),
            ("price_snapshots", "aliases"), ("price_snapshots", "rates"),
            ("price_snapshots", "primary_sources"),
            ("scenario", "snapshot_ids"), ("scenario", "threshold_rules"),
            ("scenario", "threshold_rules", "components"),
        }:
            return True
        if (kind == "lifecycle_projection" and len(path) >= 3
                and path[-3] == "measurements" and path[-1] == "reasons"):
            return True
        if kind == "usage_accepted" and path == ("observation_ids",):
            return True
        if kind == "pricing_scenario" and path in {
            ("snapshot_ids",), ("threshold_rules",), ("threshold_rules", "components"),
        }:
            return True
        if kind == "price_snapshot" and path in {
            ("aliases",), ("rates",), ("primary_sources",),
        }:
            return True
        if kind == "source_profile" and path in {
            ("counter_fields",), ("counter_fields", "includes"),
            ("known_gaps",), ("finality", "signals"),
        }:
            return True
        if kind == "analysis_corpus" and path in {
            ("inputs",), ("exclusions",), ("identifier_mappings",),
        }:
            return True
        if path[-2:] == ("measurements", "input_cache_write"):
            return True
        if not envelope:
            return False
        if path[-2:] == ("attribution", "candidates"):
            return True
        if (len(path) >= 3 and path[-1] == "reasons" and
                "measurements" in path[:-1]):
            return True
        if (kind == "inventory" and path in {("expected_calls",), ("expected_responses",),
                                               ("unresolved_slots",)}):
            return True
        if (kind == "usage_bundle" and path in {
            ("inventories", "expected_calls"), ("inventories", "expected_responses"),
            ("inventories", "unresolved_slots"),
        }):
            return True
        return kind == "usage_bundle" and path in {
            ("sources",), ("observations",), ("evidence_objects",),
            ("inventories",), ("segments",), ("diagnostics",),
        }

    if any(schema_set(path) for path in keys):
        raise ValueError("schema set ordering cannot be overridden")

    def normalize(item: Any, path: tuple[str, ...], array_member: bool = False) -> Any:
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise ValueError("JSON object keys must be strings")
            return {key: normalize(child, path + (key,)) for key, child in item.items()}
        if isinstance(item, list):
            children = [normalize(child, path, array_member=True) for child in item]
            if array_member:
                return children
            if path in keys:
                return sorted(children, key=lambda child: (keys[path](child), _encode(child)))
            return sorted(children, key=_encode) if path in paths or schema_set(path) else children
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

# Envelope bounds apply to UTF-8 bytes, not character counts.
OBSERVATION_LIMIT = 1024 * 1024
BUNDLE_LIMIT = 32 * 1024 * 1024
PROFILE_LIMIT = 1024 * 1024
SELECTION_LIMIT = 1024 * 1024
INVENTORY_LIMIT = 1024 * 1024
SEGMENT_LIMIT = 1024 * 1024
DIAGNOSTIC_LIMIT = 1024 * 1024
PRICE_SNAPSHOT_LIMIT = 1024 * 1024
PRICING_SCENARIO_LIMIT = 1024 * 1024
WARNING_POLICY_LIMIT = 1024 * 1024
ANALYSIS_CORPUS_LIMIT = 1024 * 1024
RECEIPT_LIMIT = 1024 * 1024
LIFECYCLE_PROJECTION_LIMIT = 1024 * 1024
CURRENT_RUN_SNAPSHOT_LIMIT = 1024 * 1024
DIAGNOSTIC_METRICS = {
    "context.loaded_bytes": "bytes",
    "orchestration.tool_calls": "count",
    "verification.evidence_reuses": "count",
    "tool_output.full_bytes": "bytes",
    "tool_output.shown_bytes": "bytes",
    "tool_output.additional_read_bytes": "bytes",
    "repair.attempts": "count",
    "decomposition.rework": "count",
}
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_COUNTER_SCOPES = frozenset({"response_total", "incremental_delta", "cumulative_epoch",
                             "provider_aggregate", "caller_aggregate"})
_MEASUREMENT_FIELDS = frozenset({"input_uncached", "input_cache_read", "input_cache_write_unsplit",
                                 "output_total", "reasoning_subset", "tokens_in"})


def _fields(value: Any, required: set[str], optional: set[str] = frozenset()) -> None:
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - required - optional:
        raise ValueError("invalid envelope fields")


def _identifier(value: Any) -> None:
    if (not isinstance(value, str) or not value or len(value) > 256
            or any(char in "/\\" or char.isspace() or unicodedata.category(char).startswith("C")
                   for char in value)):
        raise ValueError("invalid identifier")


def _timestamp(value: Any) -> None:
    if not isinstance(value, str) or re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z", value
    ) is None or len(value) > 256:
        raise ValueError("invalid UTC timestamp")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise ValueError("invalid UTC timestamp") from None


def _instant(timestamp: str) -> tuple[str, str]:
    """Compare UTC timestamps without truncating arbitrary fractional precision."""
    whole, _, fraction = timestamp[:-1].partition(".")
    return whole, fraction.rstrip("0")


def _private_identifier(value: Any) -> None:
    # Syntax alone does not prove safe origin or prevent encoded secrets.
    if not isinstance(value, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise ValueError("invalid opaque identifier")


def _hash(value: Any) -> None:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise ValueError("invalid digest")


def _version(value: Any) -> None:
    if type(value) is not int or value != 1:
        raise ValueError("unsupported schema version")


def _bounded_tree(value: Any, depth: int = 0) -> None:
    if depth > 32:
        raise ValueError("envelope nesting exceeds limit")
    if isinstance(value, dict):
        if len(value) > 256 or any(not isinstance(key, str) for key in value):
            raise ValueError("invalid object keys")
        for child in value.values():
            _bounded_tree(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _bounded_tree(child, depth + 1)
    elif value is not None and type(value) not in (str, int, bool):
        raise ValueError("invalid JSON value")


def _choice(value: Any, choices: frozenset[str]) -> None:
    if not isinstance(value, str) or value not in choices:
        raise ValueError("invalid envelope value")


def validate_source_profile(value: Any) -> dict[str, Any]:
    """Validate structure, not the origin or secrecy of referenced evidence.

    Callers must independently establish provenance, applicability, and privacy.
    Absent counter semantics are unknown and must not be inferred by consumers.
    """
    required = {"schema_version", "kind", "profile_id", "profile_version", "provider",
                "runtime", "format_version", "counter_fields", "identity_scope",
                "finality", "inventory", "capabilities", "known_gaps", "verified_at",
                "source"}
    _fields(value, required, {"capability_evidence", "resolution_fields", "epoch_fields"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"source_profile"}))
    for field in ("profile_id", "profile_version", "provider", "runtime", "format_version"):
        _identifier(value[field])
    counters = value["counter_fields"]
    if not isinstance(counters, list) or not 1 <= len(counters) <= 256:
        raise ValueError("invalid counter fields")
    seen = set()
    for counter in counters:
        _fields(counter, {"path", "measurement", "counter_scope"},
                {"semantics_status", "includes", "ttl"})
        path = counter["path"]
        if not isinstance(path, list) or not 1 <= len(path) <= 32:
            raise ValueError("invalid counter path")
        for part in path:
            _identifier(part)
        key = tuple(path)
        if key in seen:
            raise ValueError("duplicate counter path")
        seen.add(key)
        _choice(counter["measurement"], _MEASUREMENT_FIELDS | {"input_total", "input_cache_write"})
        _choice(counter["counter_scope"], _COUNTER_SCOPES)
        status = counter.get("semantics_status", "unknown")
        _choice(status, frozenset({"verified", "unknown"}))
        includes = counter.get("includes")
        if status == "unknown":
            if ("includes" in counter or "ttl" in counter or
                    counter["measurement"] == "input_cache_write"):
                raise ValueError("unknown counter semantics have details")
        else:
            if not isinstance(includes, list) or len(includes) > 3:
                raise ValueError("invalid included measurements")
            allowed = {
                "input_total": frozenset({"input_cache_read", "input_cache_write_unsplit", "input_cache_write"}),
                "output_total": frozenset({"reasoning_subset"}),
            }.get(counter["measurement"], frozenset())
            if any(not isinstance(item, str) or item not in allowed for item in includes):
                raise ValueError("invalid included measurement")
            if len(set(includes)) != len(includes):
                raise ValueError("duplicate included measurement")
            if counter["measurement"] == "input_cache_write":
                _identifier(counter.get("ttl"))
            elif "ttl" in counter:
                raise ValueError("TTL requires split cache write")
    epoch_fields = value.get("epoch_fields")
    if epoch_fields is not None:
        if not isinstance(epoch_fields, dict):
            raise ValueError("invalid epoch fields")
        if epoch_fields.get("status") == "unknown":
            _fields(epoch_fields, {"status"})
        elif epoch_fields.get("status") == "verified":
            _fields(epoch_fields, {"status", "epoch", "model", "sequence", "position"})
            for name in ("epoch", "model", "sequence", "position"):
                path = epoch_fields[name]
                if not isinstance(path, list) or not 1 <= len(path) <= 32:
                    raise ValueError("invalid epoch source path")
                for part in path:
                    _identifier(part)
            if (len(counters) != 1 or counters[0]["counter_scope"] != "cumulative_epoch" or
                    counters[0]["measurement"] != "input_uncached" or
                    counters[0].get("semantics_status") != "verified"):
                raise ValueError("invalid epoch counter profile")
        else:
            raise ValueError("invalid epoch status")
    resolution = value.get("resolution_fields")
    if resolution is not None:
        if not isinstance(resolution, dict):
            raise ValueError("invalid resolution fields")
        if resolution.get("status") == "unknown":
            _fields(resolution, {"status"})
        elif resolution.get("status") == "verified":
            _fields(resolution, {"status", "response_id", "call_id", "session_id", "execution_time",
                                 "finality", "parameters", "cache_ttl_seconds"})
            def source_path(path: Any) -> None:
                if not isinstance(path, list) or not 1 <= len(path) <= 32:
                    raise ValueError("invalid source field path")
                for part in path:
                    _identifier(part)
            for name in ("response_id", "call_id", "session_id", "execution_time"):
                source_path(resolution[name])
            finality_mapping = resolution["finality"]
            if value["finality"]["status"] != "verified":
                raise ValueError("unverified source finality")
            if finality_mapping.get("kind") == "snapshot":
                _fields(finality_mapping, {"path", "kind", "final_value"})
                source_path(finality_mapping["path"])
                if type(finality_mapping["final_value"]) is not bool:
                    raise ValueError("invalid source finality")
            elif finality_mapping.get("kind") == "stream":
                _fields(finality_mapping, {"kind", "kind_path", "sequence_path", "final_path",
                                          "correction_record_path", "kinds"})
                for name in ("kind_path", "sequence_path", "final_path", "correction_record_path"):
                    source_path(finality_mapping[name])
                kinds = finality_mapping["kinds"]
                _fields(kinds, {"snapshot", "delta", "terminal"})
                for label in kinds.values():
                    _identifier(label)
                if len(set(kinds.values())) != len(kinds):
                    raise ValueError("ambiguous stream event mapping")
            else:
                raise ValueError("invalid source finality")
            parameters = resolution["parameters"]
            _fields(parameters, {"model", "service_tier", "region", "modality"})
            for path in parameters.values():
                source_path(path)
            ttls = resolution["cache_ttl_seconds"]
            if not isinstance(ttls, dict) or len(ttls) > 256:
                raise ValueError("invalid source cache durations")
            for ttl, seconds in ttls.items():
                _identifier(ttl)
                if validate_counter(seconds) == 0:
                    raise ValueError("invalid source cache duration")
        else:
            raise ValueError("invalid resolution status")
    identity = value["identity_scope"]
    _fields(identity, {"account", "response"})
    for field in ("account", "response"):
        _identifier(identity[field])
    finality = value["finality"]
    _fields(finality, {"signals", "status"})
    _choice(finality["status"], frozenset({"verified", "unknown"}))
    signals = finality["signals"]
    if not isinstance(signals, list) or len(signals) > 256:
        raise ValueError("invalid finality signals")
    for signal in signals:
        _identifier(signal)
    if (len(set(signals)) != len(signals) or
            (finality["status"] == "unknown" and signals) or
            (finality["status"] == "verified" and not signals)):
        raise ValueError("invalid finality evidence")
    inventory = value["inventory"]
    _fields(inventory, {"status", "evidence"})
    _choice(inventory["status"], frozenset({"verified", "unknown"}))
    if inventory["status"] == "unknown":
        if inventory["evidence"] is not None:
            raise ValueError("unknown inventory has evidence")
    else:
        _identifier(inventory["evidence"])
    capabilities = value["capabilities"]
    _fields(capabilities, {"cache", "effort", "tools"})
    evidence = value.get("capability_evidence", {})
    if not isinstance(evidence, dict) or evidence.keys() - capabilities.keys():
        raise ValueError("invalid capability evidence")
    for name, state in capabilities.items():
        _choice(state, frozenset({"unknown", "supported", "unsupported"}))
        if state == "unknown":
            if name in evidence:
                raise ValueError("unknown capability has evidence")
        else:
            _identifier(evidence.get(name))
    if capabilities["cache"] == "unsupported":
        cache_fields = {"input_cache_read", "input_cache_write", "input_cache_write_unsplit"}
        if any(counter["measurement"] in cache_fields or
               cache_fields.intersection(counter.get("includes", [])) for counter in counters):
            raise ValueError("unsupported cache contradicts counter semantics")
    gaps = value["known_gaps"]
    if not isinstance(gaps, list) or len(gaps) > 256:
        raise ValueError("invalid known gaps")
    for gap in gaps:
        _identifier(gap)
    if len(set(gaps)) != len(gaps):
        raise ValueError("duplicate known gap")
    _timestamp(value["verified_at"])
    source = value["source"]
    if not isinstance(source, str) or len(source) > 2048:
        raise ValueError("invalid source reference")
    try:
        if len(source.encode("utf-8")) > 2048:
            raise ValueError("invalid source reference")
        url = urlsplit(source)
        if (url.scheme != "https" or not url.hostname or url.username is not None or
                url.password is not None or url.query or url.fragment or
                any(char.isspace() or unicodedata.category(char).startswith("C") for char in source)):
            raise ValueError("invalid source reference")
        url.port
    except (ValueError, UnicodeError):
        raise ValueError("invalid source reference") from None
    if len(canonical_bytes(value)) > PROFILE_LIMIT:
        raise ValueError("profile exceeds byte limit")
    return value


def normalize_source_counters(profile: Any, source: Any, *, profile_version: str,
                              source_hash: str, record_number: int) -> dict[str, Any]:
    """Normalize one selected record without reading files or assuming provenance.

    Profile and record authenticity must be established by the caller. Counter
    categories are only combined when the selected profile proves their meaning.
    """
    validate_source_profile(profile)
    _hash(source_hash)
    validate_counter(record_number)
    if not isinstance(source, dict):
        raise ValueError("invalid source record")
    fields = ("input_uncached", "input_cache_read", "input_cache_write_unsplit",
              "output_total", "reasoning_subset", "tokens_in")

    def missing(reason: str = "source_unavailable", state: str = "unavailable") -> dict[str, Any]:
        return {"measurement_state": state, "reasons": [reason]}

    if profile_version != profile["profile_version"]:
        return {"measurements": {name: missing("unsupported_profile") for name in fields},
                "evidence_objects": []}

    source_scopes = {entry["counter_scope"] for entry in profile["counter_fields"]}
    source_scope = next(iter(source_scopes)) if len(source_scopes) == 1 else None
    if (source_scope not in {"response_total", "incremental_delta"} and
            not (source_scope == "cumulative_epoch" and profile.get("epoch_fields", {}).get("status") == "verified")):
        return {"measurements": {name: missing("source_unavailable") for name in fields},
                "evidence_objects": []}
    observations: dict[str, list[tuple[dict[str, Any], int | None]]] = {}
    absent = object()
    for definition in profile["counter_fields"]:
        item: Any = source
        for segment in definition["path"]:
            if not isinstance(item, dict) or segment not in item:
                item = absent
                break
            item = item[segment]
        if item is not absent:
            validate_counter(item)
        else:
            item = None
        observations.setdefault(definition["measurement"], []).append((definition, item))

    evidence_objects: list[dict[str, Any]] = []
    def observed(field: str, value: int, ttl: str | None = None,
                 definition: dict[str, Any] | None = None) -> dict[str, Any]:
        validate_counter(value)
        evidence = {"schema_version": 1, "kind": "measurement_evidence",
                    "profile_id": profile["profile_id"], "source_hash": source_hash,
                    "record_number": record_number, "field": field, "value": value}
        if ttl is not None:
            evidence["ttl"] = ttl
        if definition is not None:
            evidence["path"] = list(definition["path"])
        evidence_objects.append(evidence)
        return {"measurement_state": "partial", "value": value,
                "reasons": [], "evidence": content_id(evidence)}

    def derived(field: str, value: int, operation: str, operands: list[str]) -> dict[str, Any]:
        encoded: int | str = value if value <= MAX_COUNTER else str(value)
        evidence = {"schema_version": 1, "kind": "derived_measurement_evidence",
                    "profile_id": profile["profile_id"], "profile_version": profile["profile_version"],
                    "profile_hash": content_id(profile), "profile": copy.deepcopy(profile),
                    "source_hash": source_hash, "record_number": record_number,
                    "field": field, "value": encoded, "operation": operation, "operands": operands}
        evidence_objects.append(evidence)
        return {"measurement_state": "partial", "value": encoded,
                "reasons": [], "evidence": content_id(evidence)}

    def resolve(name: str) -> tuple[dict[str, Any] | None, int | None, bool]:
        entries = observations.get(name, [])
        if not entries:
            return None, None, False
        if len(entries) != 1:
            return None, None, True
        definition, amount = entries[0]
        if definition.get("semantics_status") != "verified" or definition["counter_scope"] != source_scope:
            return definition, None, False
        return definition, amount, False

    resolved = {name: resolve(name) for name in fields if name != "tokens_in"}
    resolved["input_total"] = resolve("input_total")
    measurements: dict[str, Any] = {}
    for name in ("input_cache_read", "input_cache_write_unsplit", "output_total", "reasoning_subset"):
        definition, amount, conflict = resolved[name]
        measurements[name] = (missing("counter_conflict", "conflicted") if conflict else
                              observed(name, amount, definition=definition) if amount is not None else missing())

    split = observations.get("input_cache_write", [])
    split_values: list[dict[str, Any]] = []
    split_seen: set[str] = set()
    split_conflict = False
    split_complete = bool(split)
    for definition, amount in split:
        ttl = definition["ttl"]
        if ttl in split_seen:
            split_conflict = True
            continue
        split_seen.add(ttl)
        if definition["counter_scope"] != source_scope or amount is None:
            split_complete = False
            split_values.append({"ttl": ttl, "tokens": missing()})
        else:
            split_values.append({"ttl": ttl, "tokens": observed("input_cache_write", amount, ttl, definition)})
    if split_values:
        measurements["input_cache_write"] = split_values
    split_total = sum(part["tokens"]["value"] for part in split_values if "value" in part["tokens"])
    write_total = resolved["input_cache_write_unsplit"][1]
    if split_conflict or (write_total is not None and
                          (split_total > write_total or (split_complete and split_total != write_total))):
        split_conflict = True
        measurements["input_cache_write_unsplit"] = missing("counter_conflict", "conflicted")
    write = (None if split_conflict else write_total if write_total is not None else
             split_total if split_complete else None)

    _, read, read_conflict = resolved["input_cache_read"]
    total_definition, total, total_conflict = resolved["input_total"]
    _, uncached, uncached_conflict = resolved["input_uncached"]
    uncached_operands: list[str] = []
    if total is not None and uncached is not None:
        total_conflict = True
    if total is not None and total_definition is not None:
        included = set(total_definition["includes"])
        deductions: list[int] = []
        uncertain = False
        if "input_cache_read" in included:
            if read is None or read_conflict:
                uncertain = True
            else:
                deductions.append(read)
        if included.intersection({"input_cache_write", "input_cache_write_unsplit"}):
            if write is None:
                uncertain = True
            else:
                deductions.append(write)
        if not uncertain and not total_conflict:
            remainder = total - sum(deductions)
            if remainder < 0:
                total_conflict = True
            else:
                uncached = remainder
                uncached_operands.append(observed("input_total", total, definition=total_definition)["evidence"])
                if "input_cache_read" in included:
                    uncached_operands.append(measurements["input_cache_read"]["evidence"])
                if included.intersection({"input_cache_write", "input_cache_write_unsplit"}):
                    if write_total is not None:
                        uncached_operands.append(measurements["input_cache_write_unsplit"]["evidence"])
                    else:
                        uncached_operands.extend(part["tokens"]["evidence"] for part in split_values)
    if total_conflict or uncached_conflict:
        measurements["input_uncached"] = missing("counter_conflict", "conflicted")
    elif uncached is None:
        measurements["input_uncached"] = missing()
    else:
        measurements["input_uncached"] = (derived("input_uncached", uncached, "subtract", uncached_operands)
                                          if uncached_operands else observed(
                                              "input_uncached", uncached, definition=resolved["input_uncached"][0]))

    cache_not_applicable = profile["capabilities"]["cache"] == "unsupported"
    if cache_not_applicable and not observations.get("input_cache_read"):
        read = 0
    if cache_not_applicable and not observations.get("input_cache_write") and not observations.get("input_cache_write_unsplit"):
        write = 0
    complete = (uncached is not None and read is not None and write is not None and
                not any((split_conflict, read_conflict, total_conflict, uncached_conflict)))
    input_sum = uncached + read + write if complete else None
    if input_sum is not None:
        operands = [measurements["input_uncached"]["evidence"]]
        if not (cache_not_applicable and not observations.get("input_cache_read")):
            operands.append(measurements["input_cache_read"]["evidence"])
        if write_total is not None:
            operands.append(measurements["input_cache_write_unsplit"]["evidence"])
        elif split_complete:
            operands.extend(part["tokens"]["evidence"] for part in split_values)
        measurements["tokens_in"] = derived("tokens_in", input_sum, "sum", operands)
    else:
        measurements["tokens_in"] = missing("counter_conflict" if any(
            (split_conflict, read_conflict, total_conflict, uncached_conflict)) else "source_unavailable")

    output = resolved["output_total"][1]
    reasoning = resolved["reasoning_subset"][1]
    if output is not None and reasoning is not None and reasoning > output:
        measurements["reasoning_subset"] = missing("counter_conflict", "conflicted")
    return {"measurements": measurements, "evidence_objects": evidence_objects}


def validate_source_selection(value: Any) -> dict[str, Any]:
    """Validate a local selection without opening or trusting any source.

    Declared sizes and hashes must be checked against actual selected bytes by
    the consumer before records are processed. The owner scope and attribution
    map are claims, not proof of causal ownership.
    """
    _fields(value, {"schema_version", "kind", "profile_id", "profile_version",
                    "owner_scope", "attribution_map", "observed_at", "sources",
                    "max_source_bytes", "max_total_bytes", "max_records"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"source_selection"}))
    for key in ("profile_id", "profile_version"):
        _identifier(value[key])
    _timestamp(value["observed_at"])
    scope = value["owner_scope"]
    _fields(scope, {"owner_kind", "owner_id"})
    _choice(scope["owner_kind"], frozenset({"run", "session", "task", "span", "shared_pool"}))
    _private_identifier(scope["owner_id"])
    for key in ("max_source_bytes", "max_total_bytes", "max_records"):
        validate_counter(value[key])
    if value["max_records"] == 0:
        raise ValueError("record limit must be positive")
    sources = value["sources"]
    if not isinstance(sources, list) or not 1 <= len(sources) <= 10000:
        raise ValueError("invalid source selection count")
    ids: set[str] = set()
    selected_total = 0
    for source in sources:
        _fields(source, {"source_id", "local_path", "sha256", "size_bytes"},
                {"verified_prefix_bytes"})
        _private_identifier(source["source_id"])
        if source["source_id"] in ids:
            raise ValueError("duplicate selected source")
        ids.add(source["source_id"])
        path = source["local_path"]
        if (not isinstance(path, str) or not path or
                any(char in "*?[]" or unicodedata.category(char).startswith("C") for char in path)):
            raise ValueError("invalid local source path")
        _hash(source["sha256"])
        size = validate_counter(source["size_bytes"])
        selected_size = size
        if "verified_prefix_bytes" in source:
            selected_size = validate_counter(source["verified_prefix_bytes"])
            if selected_size > size:
                raise ValueError("selected prefix exceeds declared source size")
        if selected_size > value["max_source_bytes"]:
            raise ValueError("selected source exceeds byte limit")
        selected_total += selected_size
    if selected_total > value["max_total_bytes"]:
        raise ValueError("selected sources exceed total byte limit")
    mappings = value["attribution_map"]
    if not isinstance(mappings, list) or len(mappings) != len(ids):
        raise ValueError("invalid attribution map")
    mapped: set[str] = set()
    for mapping in mappings:
        _fields(mapping, {"source_id", "owner_kind", "quality", "candidates"})
        _private_identifier(mapping["source_id"])
        if mapping["source_id"] not in ids or mapping["source_id"] in mapped:
            raise ValueError("invalid source attribution mapping")
        mapped.add(mapping["source_id"])
        _choice(mapping["owner_kind"], frozenset({"span", "task", "shared_pool", "unattributed"}))
        _choice(mapping["quality"], frozenset({"unknown", "asserted", "verified", "inferred"}))
        candidates = mapping["candidates"]
        if not isinstance(candidates, list) or len(candidates) > 64:
            raise ValueError("invalid attribution candidates")
        for candidate in candidates:
            _private_identifier(candidate)
        if len(set(candidates)) != len(candidates):
            raise ValueError("duplicate attribution candidate")
    if len(canonical_bytes(value)) > SELECTION_LIMIT:
        raise ValueError("selection exceeds byte limit")
    return value


def validate_attribution(value: Any) -> dict[str, Any]:
    """Validate ownership claims without establishing their factual provenance.

    Opaque identifiers and evidence digests are structural references only;
    consumers must verify their origin, scope, and causal relationship.
    """
    _fields(value, {"owner_kind", "quality", "candidates"},
            {"owner_scope", "parent_span_id", "root_command", "stage", "role",
             "execution_path", "attempt", "capability", "basis", "evidence"})
    _bounded_tree(value)
    _choice(value["owner_kind"], frozenset({"span", "task", "shared_pool", "unattributed"}))
    _choice(value["quality"], frozenset({"unknown", "asserted", "verified", "inferred"}))
    candidates = value["candidates"]
    if not isinstance(candidates, list) or len(candidates) > 64:
        raise ValueError("invalid owner candidates")
    for candidate in candidates:
        _private_identifier(candidate)
    if len(set(candidates)) != len(candidates):
        raise ValueError("duplicate owner candidate")
    if value.get("owner_scope") is not None:
        scope = value["owner_scope"]
        _fields(scope, {"owner_kind", "owner_id"})
        _choice(scope["owner_kind"], frozenset({"run", "session", "task", "span", "shared_pool"}))
        _private_identifier(scope["owner_id"])
    for key in ("parent_span_id", "root_command", "stage", "role", "capability"):
        if value.get(key) is not None:
            _private_identifier(value[key])
    if value.get("execution_path") is not None:
        _choice(value["execution_path"], frozenset({"full", "fast"}))
    if value.get("attempt") is not None:
        validate_counter(value["attempt"])
    if "basis" in value:
        _choice(value["basis"], frozenset({"unknown", "submission_metadata", "correlation", "verified_import"}))
    if value.get("evidence") is not None:
        _hash(value["evidence"])
    return value


def validate_observation(value: Any) -> dict[str, Any]:
    """Validate a bounded, sanitized observation without resolving evidence."""
    required = {"schema_version", "kind", "profile_id", "profile_version", "source_hash",
                "record_number", "counter_scope", "provider_scope", "source_time",
                "source_time_quality", "observed_at", "state", "outcome", "attribution",
                "measurements"}
    _fields(value, required, {"id", "response_id", "call_id", "supersedes"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"request_usage", "inventory", "reported_aggregate"}))
    for name in ("profile_id", "profile_version"):
        _identifier(value[name])
    _private_identifier(value["provider_scope"])
    for name in ("response_id", "call_id"):
        if name in value:
            _identifier(value[name])
    for name in ("source_hash", "supersedes"):
        if name in value:
            _hash(value[name])
    validate_counter(value["record_number"])
    _choice(value["counter_scope"], _COUNTER_SCOPES)
    _choice(value["source_time_quality"], frozenset({"unknown", "verified", "asserted", "inferred"}))
    if value["source_time"] is None:
        if value["source_time_quality"] != "unknown":
            raise ValueError("missing source time must be unknown")
    else:
        _timestamp(value["source_time"])
    _timestamp(value["observed_at"])
    _choice(value["state"], MEASUREMENT_STATES)
    _choice(value["outcome"], frozenset({"succeeded", "failed", "cancelled", "timed_out", "unknown"}))
    validate_attribution(value["attribution"])
    measurements = value["measurements"]
    if (not isinstance(measurements, dict) or not measurements or
            measurements.keys() - (_MEASUREMENT_FIELDS | {"input_cache_write"})):
        raise ValueError("invalid measurement fields")
    for field, measurement in measurements.items():
        if field != "input_cache_write":
            validate_measurement(measurement, allow_derived=field == "tokens_in")
            continue
        if not isinstance(measurement, list) or not 1 <= len(measurement) <= 256:
            raise ValueError("invalid cache write components")
        ttls = set()
        for component in measurement:
            _fields(component, {"ttl", "tokens"})
            _identifier(component["ttl"])
            if component["ttl"] in ttls:
                raise ValueError("duplicate cache write TTL")
            ttls.add(component["ttl"])
            validate_measurement(component["tokens"])
        total = measurements.get("input_cache_write_unsplit")
        if (total is not None and total["measurement_state"] == "final" and
                all(part["tokens"]["measurement_state"] == "final" for part in measurement) and
                total["value"] != sum(part["tokens"]["value"] for part in measurement)):
            raise ValueError("cache write total conflicts with components")
    if len(canonical_bytes(value)) > OBSERVATION_LIMIT:
        raise ValueError("observation exceeds byte limit")
    if "id" in value:
        _hash(value["id"])
        if value["id"] != observation_id(value):
            raise ValueError("observation identifier mismatch")
    return value


def validate_evidence_object(value: Any) -> dict[str, Any]:
    """Validate the separate evidence record; the hash is not an authenticity claim."""
    if isinstance(value, dict) and value.get("kind") == "epoch_interval_evidence":
        _fields(value, {"schema_version", "kind", "pack"})
        _version(value["schema_version"])
        pack = value["pack"]
        _fields(pack, {"profile", "observations", "evidence_objects", "interval", "observed_at"})
        _bounded_tree(pack)
        validate_source_profile(pack["profile"])
        _timestamp(pack["observed_at"])
        if not isinstance(pack["observations"], list) or len(pack["observations"]) != 2:
            raise ValueError("invalid epoch observations")
        if not isinstance(pack["evidence_objects"], list) or len(pack["evidence_objects"]) > 10000:
            raise ValueError("invalid epoch evidence")
        objects = {}
        for item in pack["evidence_objects"]:
            if not isinstance(item, dict) or item.get("kind") == "epoch_interval_evidence":
                raise ValueError("recursive epoch evidence")
            validate_evidence_object(item)
            digest = content_id(item)
            if digest in objects:
                raise ValueError("duplicate epoch evidence")
            objects[digest] = item
        interval = pack["interval"]
        _fields(interval, {"before", "after", "coverage"})
        for observation, name in zip(pack["observations"], ("before", "after")):
            validate_observation(observation)
            snapshot = interval[name]
            _fields(snapshot, {"provider", "account", "model", "units", "epoch", "sequence", "position", "value"})
            _identifier(snapshot["provider"])
            _private_identifier(snapshot["account"])
            _private_identifier(snapshot["epoch"])
            _identifier(snapshot["units"])
            if not isinstance(snapshot["model"], str) or not snapshot["model"] or len(snapshot["model"]) > 256:
                raise ValueError("invalid epoch model")
            for field in ("sequence", "position", "value"):
                validate_counter(snapshot[field])
            measurement = observation["measurements"].get("input_uncached", {})
            if (observation["counter_scope"] != "cumulative_epoch" or
                    observation["profile_id"] != pack["profile"]["profile_id"] or
                    observation["profile_version"] != pack["profile"]["profile_version"] or
                    snapshot["account"] != observation["provider_scope"] or
                    snapshot["provider"] != pack["profile"]["provider"] or
                    snapshot["units"] != "input_uncached_tokens" or
                    snapshot["value"] != measurement.get("value") or
                    not verify_measurement_evidence(observation, "input_uncached", objects.get(measurement.get("evidence")))):
                raise ValueError("epoch observation mismatch")
        coverage = interval["coverage"]
        _fields(coverage, {"complete", "before_clear", "after_clear", "atomic_on_completion", "requests"})
        for flag in ("complete", "before_clear", "after_clear", "atomic_on_completion"):
            if type(coverage[flag]) is not bool:
                raise ValueError("invalid epoch coverage")
        if not isinstance(coverage["requests"], list) or len(coverage["requests"]) > 10000:
            raise ValueError("invalid epoch requests")
        for request in coverage["requests"]:
            _fields(request, {"id", "start", "end"})
            _private_identifier(request["id"])
            validate_counter(request["start"])
            validate_counter(request["end"])
        if len(canonical_bytes(value)) > BUNDLE_LIMIT:
            raise ValueError("epoch evidence exceeds limit")
        return value
    if isinstance(value, dict) and value.get("kind") == "resolution_context_evidence":
        _fields(value, {"schema_version", "kind", "context"})
        _version(value["schema_version"])
        validate_resolution_context(value["context"])
        return value
    if isinstance(value, dict) and value.get("kind") == "derived_measurement_evidence":
        _fields(value, {"schema_version", "kind", "profile_id", "profile_version", "profile_hash",
                        "profile", "source_hash", "record_number", "field", "value", "operation", "operands"})
        _bounded_tree(value)
        _version(value["schema_version"])
        validate_source_profile(value["profile"])
        for name in ("profile_id", "profile_version"):
            _identifier(value[name])
            if value[name] != value["profile"][name]:
                raise ValueError("derived evidence profile mismatch")
        _hash(value["profile_hash"])
        if value["profile_hash"] != content_id(value["profile"]):
            raise ValueError("derived evidence profile digest mismatch")
        _hash(value["source_hash"])
        validate_counter(value["record_number"])
        _choice(value["field"], frozenset({"input_uncached", "tokens_in"}))
        _choice(value["operation"], frozenset({"subtract", "sum"}))
        validate_measurement({"measurement_state": "partial", "value": value["value"],
                              "reasons": [], "evidence": "0" * 64},
                             allow_derived=value["field"] == "tokens_in")
        operands = value["operands"]
        if not isinstance(operands, list) or not 1 <= len(operands) <= 256:
            raise ValueError("invalid derived operands")
        for operand in operands:
            _hash(operand)
        if len(set(operands)) != len(operands):
            raise ValueError("duplicate derived operand")
        return value
    if isinstance(value, dict) and value.get("kind") == "price_period_evidence":
        _fields(value, {"schema_version", "kind", "source_hash", "start", "end"})
        _version(value["schema_version"])
        _hash(value["source_hash"])
        _timestamp(value["start"])
        _timestamp(value["end"])
        return value
    if isinstance(value, dict) and value.get("kind") == "source_parameter_evidence":
        _fields(value, {"schema_version", "kind", "profile_id", "source_hash", "record_number", "field", "value"})
        _version(value["schema_version"])
        _identifier(value["profile_id"])
        _hash(value["source_hash"])
        validate_counter(value["record_number"])
        _choice(value["field"], frozenset({"model", "service_tier", "region", "modality"}))
        if value["field"] == "model":
            if (not isinstance(value["value"], str) or len(value["value"]) > 256 or
                    re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*(?:/[A-Za-z0-9][A-Za-z0-9._:-]*)?", value["value"]) is None):
                raise ValueError("invalid model identifier")
        else:
            _identifier(value["value"])
        return value
    if isinstance(value, dict) and value.get("kind") == "execution_time_evidence":
        _fields(value, {"schema_version", "kind", "profile_id", "source_hash", "record_number", "value"})
        _version(value["schema_version"])
        _identifier(value["profile_id"])
        _hash(value["source_hash"])
        validate_counter(value["record_number"])
        _timestamp(value["value"])
        return value
    if isinstance(value, dict) and value.get("kind") == "tool_quantity_evidence":
        _fields(value, {"schema_version", "kind", "profile_id", "source_hash", "record_number", "tool_id", "unit", "value"})
        _version(value["schema_version"])
        _identifier(value["profile_id"])
        _hash(value["source_hash"])
        validate_counter(value["record_number"])
        _identifier(value["tool_id"])
        _identifier(value["unit"])
        validate_counter(value["value"])
        return value
    if isinstance(value, dict) and value.get("kind") == "model_alias_evidence":
        _fields(value, {"schema_version", "kind", "source_hash", "alias", "model"})
        _version(value["schema_version"])
        _hash(value["source_hash"])
        for name in ("alias", "model"):
            item = value[name]
            if (not isinstance(item, str) or len(item) > 256 or
                    re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*(?:/[A-Za-z0-9][A-Za-z0-9._:-]*)?", item) is None):
                raise ValueError("invalid model alias")
        if value["alias"] == value["model"]:
            raise ValueError("redundant model alias")
        return value
    if isinstance(value, dict) and value.get("kind") == "price_snapshot_evidence":
        _fields(value, {"schema_version", "kind", "snapshot_id", "source_hash"})
        _version(value["schema_version"])
        _hash(value["snapshot_id"])
        _hash(value["source_hash"])
        return value
    if isinstance(value, dict) and value.get("kind") in {"rate_parameter_evidence", "multiplier_evidence"}:
        common = {"schema_version", "kind", "profile_id", "source_hash", "record_number"}
        fields = ({"field", "value"} if value["kind"] == "rate_parameter_evidence" else
                  {"snapshot_id", "rate_id", "scope", "factor", "applies"})
        _fields(value, common | fields)
        _bounded_tree(value)
        _version(value["schema_version"])
        _identifier(value["profile_id"])
        _hash(value["source_hash"])
        validate_counter(value["record_number"])
        if value["kind"] == "rate_parameter_evidence":
            if value["field"] == "cache_ttl_seconds":
                if validate_counter(value["value"]) == 0:
                    raise ValueError("invalid cache duration")
            elif value["field"] == "tool_id":
                _identifier(value["value"])
            else:
                raise ValueError("invalid rate parameter")
        else:
            _hash(value["snapshot_id"])
            _hash(value["rate_id"])
            _identifier(value["scope"])
            validate_decimal(value["factor"])
            if type(value["applies"]) is not bool:
                raise ValueError("invalid multiplier applicability")
        return value
    if isinstance(value, dict) and value.get("kind") == "inventory_evidence":
        _fields(value, {"schema_version", "kind", "profile_id", "profile_version",
                        "source_hash", "inventory_digest"})
        _bounded_tree(value)
        _version(value["schema_version"])
        _identifier(value["profile_id"])
        _identifier(value["profile_version"])
        _hash(value["source_hash"])
        _hash(value["inventory_digest"])
        return value
    _fields(value, {"schema_version", "kind", "profile_id", "source_hash", "record_number", "field", "value"}, {"ttl", "path"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"measurement_evidence"}))
    _identifier(value["profile_id"])
    _hash(value["source_hash"])
    validate_counter(value["record_number"])
    _choice(value["field"], _MEASUREMENT_FIELDS | {"input_cache_write", "input_total"})
    if value["field"] == "input_cache_write":
        _identifier(value.get("ttl"))
    elif "ttl" in value:
        raise ValueError("TTL requires split cache write")
    if "path" in value:
        if not isinstance(value["path"], list) or not 1 <= len(value["path"]) <= 32:
            raise ValueError("invalid source counter path")
        for part in value["path"]:
            _identifier(part)
    validate_counter(value["value"])
    return value


def verify_derived_measurement_evidence(measurement: Any, evidence: Any, evidence_objects: Any,
                                        profile: Any) -> bool:
    """Verify arithmetic and declared profile semantics, not external provenance."""
    try:
        validate_source_profile(profile)
        if not isinstance(evidence_objects, list):
            return False
        by_hash = {content_id(item): item for item in evidence_objects}
        if len(by_hash) != len(evidence_objects):
            return False
        active: set[str] = set()
        profile_scopes = {entry["counter_scope"] for entry in profile["counter_fields"]}
        if len(profile_scopes) != 1 or next(iter(profile_scopes)) not in {"response_total", "incremental_delta"}:
            return False
        source_scope = next(iter(profile_scopes))

        def verify(proof: Any) -> bool:
            validate_evidence_object(proof)
            digest = content_id(proof)
            if proof.get("kind") != "derived_measurement_evidence" or digest in active:
                return False
            if proof["profile_hash"] != content_id(profile):
                return False
            active.add(digest)
            items = []
            for reference in proof["operands"]:
                item = by_hash.get(reference)
                if item is None:
                    return False
                validate_evidence_object(item)
                if any(item.get(key) != proof[key] for key in ("profile_id", "source_hash", "record_number")):
                    return False
                if item["kind"] == "derived_measurement_evidence":
                    if not verify(item):
                        return False
                elif item["kind"] == "measurement_evidence":
                    candidates = [entry for entry in profile["counter_fields"]
                                  if entry["path"] == item.get("path") and
                                  entry["measurement"] == item["field"] and
                                  entry.get("semantics_status") == "verified" and
                                  entry["counter_scope"] == source_scope and
                                  (item["field"] != "input_cache_write" or entry.get("ttl") == item.get("ttl"))]
                    if len(candidates) != 1:
                        return False
                else:
                    return False
                items.append(item)
            active.remove(digest)
            grouped: dict[str, list[dict[str, Any]]] = {}
            for item in items:
                grouped.setdefault(item["field"], []).append(item)

            def valid_write(required: bool) -> bool:
                totals = grouped.get("input_cache_write_unsplit", [])
                splits = grouped.get("input_cache_write", [])
                if totals and splits or len(totals) > 1:
                    return False
                if splits:
                    expected = {entry["ttl"] for entry in profile["counter_fields"]
                                if entry["measurement"] == "input_cache_write"}
                    if len(splits) != len(expected) or {item["ttl"] for item in splits} != expected:
                        return False
                if totals:
                    definitions = {entry["ttl"]: entry for entry in profile["counter_fields"]
                                   if entry["measurement"] == "input_cache_write"}
                    known = {}
                    for item in by_hash.values():
                        if (item.get("kind") != "measurement_evidence" or item.get("field") != "input_cache_write" or
                                any(item.get(key) != proof[key] for key in ("profile_id", "source_hash", "record_number"))):
                            continue
                        definition = definitions.get(item.get("ttl"))
                        if (definition is None or item.get("path") != definition["path"] or
                                definition.get("semantics_status") != "verified" or
                                definition["counter_scope"] != source_scope):
                            continue
                        validate_evidence_object(item)
                        if item["ttl"] in known:
                            return False
                        known[item["ttl"]] = item["value"]
                    subtotal = sum(known.values())
                    if subtotal > totals[0]["value"] or (len(known) == len(definitions) and definitions and
                                                          subtotal != totals[0]["value"]):
                        return False
                if required and not totals and not splits:
                    return False
                return True

            if proof["field"] == "input_uncached" and proof["operation"] == "subtract":
                if len(grouped.get("input_total", [])) != 1 or set(grouped) - {
                        "input_total", "input_cache_read", "input_cache_write_unsplit", "input_cache_write"}:
                    return False
                total = grouped["input_total"][0]
                definition = next(entry for entry in profile["counter_fields"] if entry["path"] == total["path"])
                includes = set(definition["includes"])
                read_required = "input_cache_read" in includes
                write_required = bool(includes.intersection({"input_cache_write", "input_cache_write_unsplit"}))
                if len(grouped.get("input_cache_read", [])) != int(read_required) or not valid_write(write_required):
                    return False
                if not write_required and (grouped.get("input_cache_write") or grouped.get("input_cache_write_unsplit")):
                    return False
                expected = int(total["value"]) - sum(int(item["value"]) for item in items if item is not total)
            elif proof["field"] == "tokens_in" and proof["operation"] == "sum":
                if len(grouped.get("input_uncached", [])) != 1 or set(grouped) - {
                        "input_uncached", "input_cache_read", "input_cache_write_unsplit", "input_cache_write"}:
                    return False
                cache_absent = profile["capabilities"]["cache"] == "unsupported"
                has_read = any(entry["measurement"] == "input_cache_read" for entry in profile["counter_fields"])
                has_write = any(entry["measurement"] in {"input_cache_write", "input_cache_write_unsplit"}
                                for entry in profile["counter_fields"])
                if len(grouped.get("input_cache_read", [])) != int(has_read or not cache_absent):
                    return False
                if not valid_write(has_write or not cache_absent):
                    return False
                expected = sum(int(item["value"]) for item in items)
            else:
                return False
            return expected >= 0 and expected == int(proof["value"])

        validate_measurement(measurement, allow_derived=evidence.get("field") == "tokens_in")
        return (measurement.get("evidence") == content_id(evidence) and
                measurement.get("value") == evidence.get("value") and verify(evidence))
    except (ValueError, KeyError, TypeError, RecursionError, StopIteration, OverflowError):
        return False


def verify_measurement_evidence(observation: Any, field: str, evidence: Any, ttl: str | None = None) -> bool:
    """Verify digest and field/source linkage; external provenance remains unverified."""
    try:
        validate_observation(observation)
        validate_evidence_object(evidence)
        measurement = observation["measurements"][field]
        if field == "input_cache_write":
            measurement = next(part["tokens"] for part in measurement if part["ttl"] == ttl)
        return (measurement.get("evidence") == content_id(evidence)
                and evidence["field"] == field and evidence["value"] == measurement.get("value")
                and (field != "input_cache_write" or evidence.get("ttl") == ttl)
                and all(evidence[key] == observation[key]
                        for key in ("profile_id", "source_hash", "record_number")))
    except (ValueError, KeyError, TypeError, RecursionError, StopIteration):
        return False


def validate_inventory(value: Any) -> dict[str, Any]:
    """Validate a bounded inventory declaration, without asserting its provenance.

    The evidence digest and declared scope do not by themselves establish
    independent coverage. Consumers must verify the source and its evidence.
    """
    _fields(value, {"schema_version", "kind", "profile_id", "profile_version", "source_hash",
                    "owner_scope", "window", "observed_at", "state", "evidence",
                    "expected_calls", "expected_responses", "unresolved_slots", "coverage"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"inventory"}))
    for field in ("profile_id", "profile_version"):
        _identifier(value[field])
    _hash(value["source_hash"])
    scope = value["owner_scope"]
    _fields(scope, {"owner_kind", "owner_id"})
    _choice(scope["owner_kind"], frozenset({"run", "session", "task", "span", "shared_pool"}))
    _private_identifier(scope["owner_id"])
    window = value["window"]
    _fields(window, {"start", "end"})
    for field in ("start", "end"):
        _timestamp(window[field])
    _timestamp(value["observed_at"])
    if datetime.fromisoformat(window["start"][:-1] + "+00:00") > datetime.fromisoformat(window["end"][:-1] + "+00:00"):
        raise ValueError("invalid inventory window")
    _choice(value["state"], frozenset({"complete", "partial", "unknown"}))
    if value["state"] == "unknown":
        if value["evidence"] is not None:
            raise ValueError("unknown inventory cannot assert evidence")
    else:
        _hash(value["evidence"])
    coverage = value["coverage"]
    _fields(coverage, {"children", "internal_checks", "tools"})
    for state in coverage.values():
        _choice(state, frozenset({"included", "excluded", "unknown"}))
    for field in ("expected_calls", "expected_responses", "unresolved_slots"):
        if not isinstance(value[field], list) or len(value[field]) > 10000:
            raise ValueError("invalid inventory collection")
    calls = set()
    for entry in value["expected_calls"]:
        _fields(entry, {"call_id"})
        _private_identifier(entry["call_id"])
        if entry["call_id"] in calls:
            raise ValueError("duplicate inventory call")
        calls.add(entry["call_id"])
    responses = set()
    answered_calls = set()
    for entry in value["expected_responses"]:
        _fields(entry, {"response_id", "call_id"})
        _private_identifier(entry["response_id"])
        if entry["call_id"] is not None:
            _private_identifier(entry["call_id"])
        if ((entry["call_id"] is not None and entry["call_id"] not in calls) or
                entry["response_id"] in responses):
            raise ValueError("invalid inventory response link")
        responses.add(entry["response_id"])
        if entry["call_id"] is not None:
            answered_calls.add(entry["call_id"])
    slots = set()
    for entry in value["unresolved_slots"]:
        _fields(entry, {"call_id", "reason"})
        _private_identifier(entry["call_id"])
        _choice(entry["reason"], MEASUREMENT_REASONS)
        identity = (entry["call_id"], entry["reason"])
        if entry["call_id"] not in calls or identity in slots:
            raise ValueError("invalid unresolved inventory slot")
        slots.add(identity)
    if value["state"] == "complete" and (slots or calls != answered_calls or any(
            entry["call_id"] is None for entry in value["expected_responses"])):
        raise ValueError("complete inventory has unresolved slots")
    if len(canonical_bytes(value)) > INVENTORY_LIMIT:
        raise ValueError("inventory exceeds byte limit")
    return value


def validate_collection_segment(value: Any) -> dict[str, Any]:
    """Validate a scoped segment without inferring collection continuity."""
    _fields(value, {"schema_version", "kind", "segment_id", "owner_scope", "mode",
                    "start", "end", "gap_before"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"collection_segment"}))
    _private_identifier(value["segment_id"])
    scope = value["owner_scope"]
    _fields(scope, {"owner_kind", "owner_id"})
    _choice(scope["owner_kind"], frozenset({"run", "session"}))
    _private_identifier(scope["owner_id"])
    _choice(value["mode"], frozenset({"on", "off"}))
    _timestamp(value["start"])
    start = _instant(value["start"])
    if value["end"] is not None:
        _timestamp(value["end"])
        if _instant(value["end"]) < start:
            raise ValueError("invalid segment boundaries")
    gap = value["gap_before"]
    _fields(gap, {"state", "start", "end"})
    _choice(gap["state"], frozenset({"unknown", "none", "present"}))
    if gap["state"] == "present":
        _timestamp(gap["start"])
        _timestamp(gap["end"])
        gap_start = _instant(gap["start"])
        gap_end = _instant(gap["end"])
        if gap_start > gap_end or gap_end > start:
            raise ValueError("invalid gap boundaries")
    elif gap["start"] is not None or gap["end"] is not None:
        raise ValueError("gap boundaries require a known gap")
    if len(canonical_bytes(value)) > SEGMENT_LIMIT:
        raise ValueError("segment exceeds byte limit")
    return value


def validate_diagnostic_measurement(value: Any) -> dict[str, Any]:
    """Validate a registered diagnostic without deriving usage or cost.

    Opaque reference syntax does not establish privacy, provenance, or scope;
    producers must establish these independently before publication.
    """
    _fields(value, {"schema_version", "kind", "metric", "value", "unit",
                    "scope", "source_id", "quality"},
            {"event_id", "attempt_id", "context_hash"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"diagnostic_measurement"}))
    metric = value["metric"]
    if not isinstance(metric, str) or metric not in DIAGNOSTIC_METRICS:
        raise ValueError("unregistered diagnostic metric")
    if value["unit"] != DIAGNOSTIC_METRICS[metric]:
        raise ValueError("invalid diagnostic unit")
    scope = value["scope"]
    _fields(scope, {"owner_kind", "owner_id"})
    _choice(scope["owner_kind"], frozenset({"run", "session"}))
    _private_identifier(scope["owner_id"])
    _private_identifier(value["source_id"])
    for field in ("event_id", "attempt_id", "context_hash"):
        if field in value and value[field] is not None:
            _private_identifier(value[field])
    _choice(value["quality"], frozenset({"measured", "unknown"}))
    if value["quality"] == "unknown":
        if value["value"] is not None:
            raise ValueError("unknown diagnostic must omit its value")
    else:
        validate_counter(value["value"])
    if len(canonical_bytes(value)) > DIAGNOSTIC_LIMIT:
        raise ValueError("diagnostic exceeds byte limit")
    return value


def validate_source_issue(value: Any) -> dict[str, Any]:
    """Validate a bounded record or prefix exclusion without source contents."""
    _fields(value, {"schema_version", "kind", "source_id", "source_hash",
                    "record_number", "reason", "completeness"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"source_issue"}))
    _private_identifier(value["source_id"])
    _hash(value["source_hash"])
    _choice(value["reason"], frozenset({"source_record_quarantined",
                                        "input_limit_exceeded", "incomplete_source"}))
    _choice(value["completeness"], frozenset({"partial"}))
    if value["reason"] == "incomplete_source":
        if value["record_number"] is not None:
            raise ValueError("prefix issue cannot identify a record")
    elif validate_counter(value["record_number"]) == 0:
        raise ValueError("source issue record number must be positive")
    if len(canonical_bytes(value)) > DIAGNOSTIC_LIMIT:
        raise ValueError("source issue exceeds byte limit")
    return value


def diagnostic_registry_view(records: Any, metrics: Any, scope: Any,
                             source_id: Any) -> list[dict[str, Any]]:
    """Select diagnostic evidence without turning it into usage or cost.

    Equal event deliveries are returned once per metric; conflicting values
    for the same event and metric fail closed. Distinct metrics of an event
    remain independent measurements. An absent requested metric is unknown.
    """
    _fields(scope, {"owner_kind", "owner_id"})
    _choice(scope["owner_kind"], frozenset({"run", "session"}))
    _private_identifier(scope["owner_id"])
    _private_identifier(source_id)
    if (not isinstance(records, list) or len(records) > 10000 or
            not isinstance(metrics, list) or len(metrics) > len(DIAGNOSTIC_METRICS)):
        raise ValueError("invalid diagnostic selection")
    if any(not isinstance(metric, str) or metric not in DIAGNOSTIC_METRICS
           for metric in metrics) or len(set(metrics)) != len(metrics):
        raise ValueError("invalid diagnostic selection")

    selected = []
    events = {}
    present = set()
    for record in records:
        validate_diagnostic_measurement(record)
        if (record["scope"] != scope or record["source_id"] != source_id or
                record["metric"] not in metrics):
            continue
        encoded = canonical_bytes(record)
        event = record.get("event_id")
        if event is not None:
            identity = (record["metric"], event)
            if identity in events and events[identity] != encoded:
                raise ValueError("conflicting diagnostic event")
            if identity in events:
                continue
            events[identity] = encoded
        selected.append((encoded, record))
        present.add(record["metric"])

    for metric in metrics:
        if metric not in present:
            unknown = {"schema_version": 1, "kind": "diagnostic_measurement",
                       "metric": metric, "value": None, "unit": DIAGNOSTIC_METRICS[metric],
                       "scope": dict(scope), "source_id": source_id, "quality": "unknown"}
            selected.append((canonical_bytes(unknown), unknown))
    return [record for _, record in sorted(selected, key=lambda item: item[0])]


def validate_usage_bundle(value: Any) -> dict[str, Any]:
    """Validate a self-contained, bounded sanitized bundle."""
    _fields(value, {"schema_version", "kind", "profile_id", "profile_version", "project_id",
                    "run_id", "sources", "observations", "evidence_objects", "inventories",
                    "segments", "diagnostics"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"usage_bundle"}))
    for field in ("profile_id", "profile_version", "run_id"):
        _identifier(value[field])
    _private_identifier(value["project_id"])
    for field in ("sources", "observations", "evidence_objects", "inventories", "segments", "diagnostics"):
        if not isinstance(value[field], list) or len(value[field]) > 10000:
            raise ValueError("invalid bundle collection")
    diagnostic_members = set()
    for diagnostic in value["diagnostics"]:
        if isinstance(diagnostic, dict) and diagnostic.get("kind") == "source_issue":
            validate_source_issue(diagnostic)
        else:
            validate_diagnostic_measurement(diagnostic)
        member = canonical_bytes(diagnostic)
        if member in diagnostic_members:
            raise ValueError("duplicate diagnostic")
        diagnostic_members.add(member)
    segment_ids = set()
    for segment in value["segments"]:
        validate_collection_segment(segment)
        if segment["segment_id"] in segment_ids:
            raise ValueError("duplicate segment")
        segment_ids.add(segment["segment_id"])
    source_hashes = set()
    source_members = set()
    for source in value["sources"]:
        _fields(source, {"source_id", "sha256"})
        _private_identifier(source["source_id"])
        _hash(source["sha256"])
        member = canonical_bytes(source)
        if member in source_members:
            raise ValueError("duplicate source")
        source_members.add(member)
        source_hashes.add(source["sha256"])
    for diagnostic in value["diagnostics"]:
        if diagnostic.get("kind") == "source_issue":
            source = {"source_id": diagnostic["source_id"], "sha256": diagnostic["source_hash"]}
            if canonical_bytes(source) not in source_members:
                raise ValueError("source issue is outside bundle scope")
    inventory_members = set()
    for inventory in value["inventories"]:
        validate_inventory(inventory)
        member = canonical_bytes(inventory)
        if member in inventory_members:
            raise ValueError("duplicate inventory")
        inventory_members.add(member)
        if (inventory["profile_id"] != value["profile_id"] or
                inventory["profile_version"] != value["profile_version"] or
                inventory["source_hash"] not in source_hashes):
            raise ValueError("inventory is outside bundle scope")
    evidence_by_hash = {}
    for evidence in value["evidence_objects"]:
        validate_evidence_object(evidence)
        digest = content_id(evidence)
        if digest in evidence_by_hash:
            raise ValueError("duplicate evidence")
        evidence_by_hash[digest] = evidence
    for inventory in value["inventories"]:
        if inventory["evidence"] is None:
            continue
        evidence = evidence_by_hash.get(inventory["evidence"])
        declaration = {key: item for key, item in inventory.items() if key != "evidence"}
        if (not evidence or evidence.get("kind") != "inventory_evidence" or
                evidence["inventory_digest"] != content_id(declaration) or
                any(evidence[key] != inventory[key]
                    for key in ("profile_id", "profile_version", "source_hash"))):
            raise ValueError("unverified inventory evidence")
    observation_members = set()
    for observation in value["observations"]:
        validate_observation(observation)
        member = observation_id(observation)
        if member in observation_members:
            raise ValueError("duplicate observation")
        observation_members.add(member)
        if (observation["profile_id"] != value["profile_id"] or
                observation["profile_version"] != value["profile_version"] or
                observation["source_hash"] not in source_hashes):
            raise ValueError("observation is outside bundle scope")
        for field, measurement in observation["measurements"].items():
            if field == "input_cache_write":
                for part in measurement:
                    tokens = part["tokens"]
                    if "evidence" in tokens and not verify_measurement_evidence(
                            observation, field, evidence_by_hash.get(tokens["evidence"]), part["ttl"]):
                        raise ValueError("unverified cache write evidence")
                continue
            proof = evidence_by_hash.get(measurement.get("evidence"))
            if isinstance(proof, dict) and proof.get("kind") == "derived_measurement_evidence":
                if (proof["field"] != field or any(proof[key] != observation[key]
                        for key in ("profile_id", "profile_version", "source_hash", "record_number")) or
                        not verify_derived_measurement_evidence(measurement, proof, value["evidence_objects"], proof["profile"])):
                    raise ValueError("unverified derived measurement evidence")
                continue
            if "evidence" in measurement and not verify_measurement_evidence(
                    observation, field, evidence_by_hash.get(measurement["evidence"])):
                raise ValueError("unverified measurement evidence")
    contexts = set()
    observations_by_id = {observation_id(item): item for item in value["observations"]}
    for evidence in value["evidence_objects"]:
        if evidence.get("kind") != "resolution_context_evidence":
            continue
        context = evidence["context"]
        identifier = context["observation_id"]
        observation = observations_by_id.get(identifier)
        if identifier in contexts or observation is None:
            raise ValueError("ambiguous context evidence")
        if any(context[name] != observation[name] for name in
               ("profile_id", "profile_version", "source_hash", "record_number", "provider_scope", "counter_scope")):
            raise ValueError("context evidence scope mismatch")
        contexts.add(identifier)
    for evidence in value["evidence_objects"]:
        if evidence.get("kind") != "epoch_interval_evidence":
            continue
        pack = evidence["pack"]
        if (pack["profile"]["profile_id"] != value["profile_id"] or
                pack["profile"]["profile_version"] != value["profile_version"] or
                any(observation_id(item) not in observation_members for item in pack["observations"]) or
                any(content_id(item) not in evidence_by_hash for item in pack["evidence_objects"])):
            raise ValueError("epoch evidence is outside bundle scope")
    if len(canonical_bytes(value)) > BUNDLE_LIMIT:
        raise ValueError("bundle exceeds byte limit")
    return value


def _validate_json(data: str | bytes, limit: int, validator: Callable[[Any], Any]) -> Any:
    if not isinstance(data, (str, bytes)):
        raise ValueError("invalid JSON input")
    try:
        raw = data.encode("utf-8") if isinstance(data, str) else data
        if len(raw) > limit:
            raise ValueError("input exceeds byte limit")
        return validator(parse_json(raw))
    except (ValueError, UnicodeError, RecursionError, TypeError, OverflowError):
        raise ValueError("invalid bounded telemetry input") from None


def validate_price_snapshot(value: Any) -> dict[str, Any]:
    """Validate a snapshot's structure; evidence still requires independent verification.

    An absent multiplier means its applicability is unknown, not that no
    multiplier applies. Consumers must not treat the affected component as
    reliably priced without evidence resolving that uncertainty. An absent
    tool_id means the tool's identity is unknown; consumers must not match the
    rate to a specific tool by guessing. Unsupported exact units remain
    unpriced until exact arithmetic is available. This function does not infer
    historical prices or decide whether a rate applies.
    """
    _fields(value, {"schema_version", "kind", "currency", "retrieved_at", "effective_period",
                    "model", "aliases", "modality", "service_tier", "region", "rates",
                    "primary_sources"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"price_snapshot"}))
    _choice(value["currency"], frozenset({"USD"}))
    _timestamp(value["retrieved_at"])
    def model_identifier(name: Any) -> None:
        # Namespace syntax restricts paths but does not establish provenance or privacy.
        if (not isinstance(name, str) or len(name) > 256 or
                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*(?:/[A-Za-z0-9][A-Za-z0-9._:-]*)?", name) is None):
            raise ValueError("invalid model identifier")

    model_identifier(value["model"])
    for field in ("modality", "service_tier", "region"):
        if value[field] is not None:
            _identifier(value[field])

    period = value["effective_period"]
    if not isinstance(period, dict):
        raise ValueError("invalid effective period")
    if period.get("state") == "known":
        _fields(period, {"state", "start", "end", "evidence"})
        _timestamp(period["start"])
        _timestamp(period["end"])
        def instant(timestamp: str) -> tuple[str, str]:
            # Compare arbitrarily precise fractions without truncating to microseconds.
            whole, _, fraction = timestamp[:-1].partition(".")
            return whole, fraction.rstrip("0")
        if instant(period["start"]) >= instant(period["end"]):
            raise ValueError("invalid effective period")
        _hash(period["evidence"])
    elif period.get("state") == "unknown":
        _fields(period, {"state", "reason"})
        _identifier(period["reason"])
    else:
        raise ValueError("invalid effective period")

    aliases = value["aliases"]
    if not isinstance(aliases, list) or len(aliases) > 10000:
        raise ValueError("invalid aliases")
    alias_names = set()
    for alias in aliases:
        _fields(alias, {"alias", "evidence"})
        model_identifier(alias["alias"])
        _hash(alias["evidence"])
        if alias["alias"] == value["model"] or alias["alias"] in alias_names:
            raise ValueError("duplicate model alias")
        alias_names.add(alias["alias"])

    rates = value["rates"]
    if not isinstance(rates, list) or not 1 <= len(rates) <= 10000:
        raise ValueError("invalid rates")
    tool_rates = [rate for rate in rates if isinstance(rate, dict) and rate.get("component") == "tool"]
    if len(tool_rates) > 1 and any("tool_id" not in rate for rate in tool_rates):
        raise ValueError("multiple tool rates require tool identities")
    seen_rates = set()
    for rate in rates:
        _fields(rate, {"component", "usd", "unit", "unit_quantity", "cache_ttl_seconds", "threshold"},
                {"tool_id", "multiplier"})
        _choice(rate["component"], frozenset({"input_uncached", "input_cache_read", "input_cache_write",
                                               "output", "reasoning", "tool"}))
        validate_decimal(rate["usd"])
        if "tool_id" in rate:
            if rate["component"] != "tool":
                raise ValueError("tool identity requires a tool rate")
            _identifier(rate["tool_id"])
        if "multiplier" in rate:
            multiplier = rate["multiplier"]
            if not isinstance(multiplier, dict):
                raise ValueError("invalid multiplier")
            if multiplier.get("state") == "none":
                _fields(multiplier, {"state"})
            elif multiplier.get("state") == "known":
                _fields(multiplier, {"state", "factor", "scope"})
                validate_decimal(multiplier["factor"])
                _identifier(multiplier["scope"])
            elif multiplier.get("state") == "unknown":
                _fields(multiplier, {"state", "scope", "reason"})
                _identifier(multiplier["scope"])
                _identifier(multiplier["reason"])
            else:
                raise ValueError("invalid multiplier")
        _identifier(rate["unit"])
        if validate_counter(rate["unit_quantity"]) == 0:
            raise ValueError("rate unit quantity must be positive")
        ttl = rate["cache_ttl_seconds"]
        if ttl is not None:
            if rate["component"] != "input_cache_write" or validate_counter(ttl) == 0:
                raise ValueError("invalid cache duration")
        threshold = rate["threshold"]
        if threshold is not None:
            _fields(threshold, {"operand", "operator", "value"})
            _identifier(threshold["operand"])
            _choice(threshold["operator"], frozenset({">", ">="}))
            validate_counter(threshold["value"])
        encoded = canonical_bytes(rate)
        if encoded in seen_rates:
            raise ValueError("duplicate rate")
        seen_rates.add(encoded)

    sources = value["primary_sources"]
    if not isinstance(sources, list) or not 1 <= len(sources) <= 10000:
        raise ValueError("invalid source references")
    seen_sources = set()
    for source in sources:
        if not isinstance(source, str) or len(source) > 2048:
            raise ValueError("invalid source reference")
        try:
            if len(source.encode("utf-8")) > 2048:
                raise ValueError("invalid source reference")
            parsed = urlsplit(source)
            if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None or
                    parsed.password is not None or parsed.query or parsed.fragment or
                    any(char.isspace() or unicodedata.category(char).startswith("C") for char in source)):
                raise ValueError("invalid source reference")
            parsed.port
        except (ValueError, UnicodeError):
            raise ValueError("invalid source reference") from None
        if source in seen_sources:
            raise ValueError("duplicate source reference")
        seen_sources.add(source)

    if len(canonical_bytes(value)) > PRICE_SNAPSHOT_LIMIT:
        raise ValueError("price snapshot exceeds byte limit")
    return value


def price_snapshot_id(value: Any) -> str:
    """Identify all canonical snapshot content without asserting source authenticity."""
    return content_id(validate_price_snapshot(value))


def validate_price_snapshot_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, PRICE_SNAPSHOT_LIMIT, validate_price_snapshot)



def validate_pricing_scenario(value: Any) -> dict[str, Any]:
    """Validate scenario shape, not price applicability or evidence provenance.

    A null source parameter remains unknown. Consumers must independently
    verify source evidence and snapshots, prove their scope and timing, and
    reconcile threshold rules with the actual measured work and rates.
    Assumptions never establish the actual model or any measured quantities.
    """
    _fields(value, {"schema_version", "kind", "scenario_id", "basis", "currency",
                    "display_precision", "snapshot_ids", "source_parameters",
                    "assumptions", "threshold_rules"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"pricing_scenario"}))
    _identifier(value["scenario_id"])
    _choice(value["basis"], frozenset({"at_execution", "reprice"}))
    _choice(value["currency"], frozenset({"USD"}))
    if validate_counter(value["display_precision"]) > 18:
        raise ValueError("display precision exceeds limit")

    snapshots = value["snapshot_ids"]
    if not isinstance(snapshots, list) or not 1 <= len(snapshots) <= 10000:
        raise ValueError("invalid snapshot references")
    seen_snapshots = set()
    for snapshot in snapshots:
        _hash(snapshot)
        if snapshot in seen_snapshots:
            raise ValueError("duplicate snapshot reference")
        seen_snapshots.add(snapshot)

    parameters = value["source_parameters"]
    _fields(parameters, {"model", "service_tier", "region", "modality"})
    for name, parameter in parameters.items():
        if parameter is None:
            continue
        _fields(parameter, {"value", "evidence"})
        if name == "model":
            model = parameter["value"]
            if (not isinstance(model, str) or len(model) > 256 or
                    re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*(?:/[A-Za-z0-9][A-Za-z0-9._:-]*)?", model) is None):
                raise ValueError("invalid model identifier")
        else:
            _identifier(parameter["value"])
        _hash(parameter["evidence"])

    assumptions = value["assumptions"]
    _fields(assumptions, set(), {"service_tier", "region", "modality"})
    if value["basis"] != "reprice" and assumptions:
        raise ValueError("historical scenario cannot use assumptions")
    for assumption in assumptions.values():
        _identifier(assumption)

    rules = value["threshold_rules"]
    if not isinstance(rules, list) or len(rules) > 10000:
        raise ValueError("invalid threshold rules")
    seen_rules = set()
    for rule in rules:
        _fields(rule, {"operand", "operator", "value", "components"})
        _identifier(rule["operand"])
        _choice(rule["operator"], frozenset({">", ">="}))
        validate_counter(rule["value"])
        components = rule["components"]
        if not isinstance(components, list) or not 1 <= len(components) <= 6:
            raise ValueError("invalid threshold components")
        seen_components = set()
        for component in components:
            _choice(component, frozenset({"input_uncached", "input_cache_read",
                                          "input_cache_write", "output", "reasoning", "tool"}))
            if component in seen_components:
                raise ValueError("duplicate threshold component")
            seen_components.add(component)
        canonical_rule = canonical_bytes(rule, set_paths={("components",)})
        if canonical_rule in seen_rules:
            raise ValueError("duplicate threshold rule")
        seen_rules.add(canonical_rule)

    if len(canonical_bytes(value)) > PRICING_SCENARIO_LIMIT:
        raise ValueError("pricing scenario exceeds byte limit")
    return value


def pricing_scenario_id(value: Any) -> str:
    """Identify scenario content without asserting historical applicability."""
    return content_id(validate_pricing_scenario(value))


def validate_pricing_scenario_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, PRICING_SCENARIO_LIMIT, validate_pricing_scenario)


def validate_warning_policy(value: Any) -> dict[str, Any]:
    """Validate a closed policy without deciding applicability or reading history.

    Explicit nulls indicate absent thresholds or cohort evidence. Consumers must
    verify the cohort provenance and compatibility and check expiry at use time.
    Identifier syntax alone cannot prove that a producer omitted private data.
    """
    _fields(value, {"schema_version", "kind", "policy_id", "policy_version", "scope",
                    "created_at", "expires_at", "token_threshold", "money_threshold",
                    "minimum_completeness", "historical_cohort"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"warning_policy"}))
    _identifier(value["policy_id"])
    if validate_counter(value["policy_version"]) == 0:
        raise ValueError("invalid policy version")
    _choice(value["scope"], frozenset({"request", "span", "run"}))

    def instant(timestamp: Any) -> tuple[str, str]:
        _timestamp(timestamp)
        whole, _, fraction = timestamp[:-1].partition(".")
        return whole, fraction.rstrip("0")

    if instant(value["created_at"]) >= instant(value["expires_at"]):
        raise ValueError("invalid policy validity")

    def decimal(number: Any) -> str:
        if (not isinstance(number, str) or len(number) > 256 or
                re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", number) is None):
            raise ValueError("invalid exact decimal")
        return number

    for name, unit in (("token_threshold", "tokens"), ("money_threshold", "USD"),
                       ("minimum_completeness", "fraction")):
        threshold = value[name]
        if threshold is None:
            continue
        _fields(threshold, {"value", "unit"})
        _choice(threshold["unit"], frozenset({unit}))
        if name == "token_threshold":
            validate_counter(threshold["value"])
        else:
            number = decimal(threshold["value"])
            if name == "minimum_completeness":
                whole, _, fractional = number.partition(".")
                if whole not in {"0", "1"} or (whole == "1" and fractional.strip("0")):
                    raise ValueError("completeness outside range")

    cohort = value["historical_cohort"]
    if cohort is not None:
        _fields(cohort, {"corpus_hash", "window_start", "window_end", "sample_size",
                         "median_seconds", "stage", "duration_kind", "clock_quality",
                         "environment", "profile", "contract", "configuration"})
        _hash(cohort["corpus_hash"])
        if instant(cohort["window_start"]) >= instant(cohort["window_end"]):
            raise ValueError("invalid cohort window")
        sample_size = validate_counter(cohort["sample_size"])
        if sample_size == 0:
            if cohort["median_seconds"] is not None:
                raise ValueError("empty cohort has no median")
        else:
            decimal(cohort["median_seconds"])
        for key in ("stage", "duration_kind", "clock_quality", "environment", "profile",
                    "contract", "configuration"):
            _identifier(cohort[key])
    if len(canonical_bytes(value)) > WARNING_POLICY_LIMIT:
        raise ValueError("warning policy exceeds byte limit")
    return value


def warning_policy_id(value: Any) -> str:
    """Identify declared policy content without asserting its applicability."""
    return content_id(validate_warning_policy(value))


def validate_warning_policy_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, WARNING_POLICY_LIMIT, validate_warning_policy)


def validate_analysis_corpus(value: Any) -> dict[str, Any]:
    """Validate a closed local selection without accessing or trusting inputs.

    Consumers must check selected bytes, authorization, schema applicability,
    identifier mappings, and evidence availability at the declared cutoff.
    """
    _fields(value, {"schema_version", "kind", "as_of", "scope", "scenario_id",
                    "versions", "identifier_mappings", "inputs", "exclusions",
                    "max_source_bytes", "max_total_bytes", "max_records"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"analysis_corpus"}))
    _timestamp(value["as_of"])
    _identifier(value["scenario_id"])
    scope = value["scope"]
    _fields(scope, {"owner_kind", "owner_id"})
    _choice(scope["owner_kind"], frozenset({"run", "session", "task", "span", "shared_pool"}))
    _private_identifier(scope["owner_id"])
    versions = value["versions"]
    _fields(versions, {"bundle_schema_version", "receipt_schema_version", "price_schema_version",
                       "normalizer_version"})
    for key in ("bundle_schema_version", "receipt_schema_version", "price_schema_version"):
        _version(versions[key])
    _identifier(versions["normalizer_version"])
    for key in ("max_source_bytes", "max_total_bytes", "max_records"):
        validate_counter(value[key])
    if value["max_records"] == 0:
        raise ValueError("record limit must be positive")

    inputs = value["inputs"]
    if not isinstance(inputs, list) or not 1 <= len(inputs) <= 10000:
        raise ValueError("invalid selected input count")
    paths: set[str] = set()
    total = 0
    for item in inputs:
        _fields(item, {"kind", "schema_version", "local_path", "sha256", "size_bytes"},
                {"verified_prefix_bytes"})
        _choice(item["kind"], frozenset({"lifecycle_event", "usage_bundle", "inventory",
                                         "price_snapshot", "acceptance_revision", "source_profile",
                                         "pricing_scenario", "resolution_context", "price_evidence", "outcome_opportunity",
                                         "outcome_attempt", "duration_graph", "experimental_inventory",
                                         "revision_metadata", "ownership_selection", "dimension_evidence", "tool_usage"}))
        _version(item["schema_version"])
        path = item["local_path"]
        if (not isinstance(path, str) or not path or
                any(char in "*?[]" or unicodedata.category(char).startswith("C") for char in path)):
            raise ValueError("invalid local input path")
        if path in paths:
            raise ValueError("duplicate selected input")
        paths.add(path)
        _hash(item["sha256"])
        size = validate_counter(item["size_bytes"])
        selected = size
        if "verified_prefix_bytes" in item:
            selected = validate_counter(item["verified_prefix_bytes"])
            if selected > size:
                raise ValueError("selected prefix exceeds declared input size")
        if selected > value["max_source_bytes"]:
            raise ValueError("selected input exceeds byte limit")
        total += selected
    if total > value["max_total_bytes"]:
        raise ValueError("selected inputs exceed total byte limit")

    mappings = value["identifier_mappings"]
    if not isinstance(mappings, list) or len(mappings) > 10000:
        raise ValueError("invalid identifier mapping count")
    mapped: set[str] = set()
    for mapping in mappings:
        _fields(mapping, {"from_id", "to_id", "quality"})
        _private_identifier(mapping["from_id"])
        if mapping["from_id"] in mapped:
            raise ValueError("duplicate identifier mapping")
        mapped.add(mapping["from_id"])
        _choice(mapping["quality"], frozenset({"unknown", "asserted", "verified", "inferred"}))
        if mapping["quality"] == "unknown":
            if mapping["to_id"] is not None:
                raise ValueError("unknown mapping has no destination")
        else:
            _private_identifier(mapping["to_id"])

    exclusions = value["exclusions"]
    if not isinstance(exclusions, list) or len(exclusions) > 10000:
        raise ValueError("invalid exclusion count")
    seen_exclusions: set[bytes] = set()
    for exclusion in exclusions:
        _fields(exclusion, {"input_sha256", "reason"})
        _hash(exclusion["input_sha256"])
        _identifier(exclusion["reason"])
        encoded = canonical_bytes(exclusion)
        if encoded in seen_exclusions:
            raise ValueError("duplicate exclusion")
        seen_exclusions.add(encoded)
    if len(canonical_bytes(value)) > ANALYSIS_CORPUS_LIMIT:
        raise ValueError("analysis corpus exceeds byte limit")
    return value


def analysis_corpus_id(value: Any) -> str:
    """Identify the declared local selection, not evidence validity."""
    return content_id(validate_analysis_corpus(value))


def validate_analysis_corpus_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, ANALYSIS_CORPUS_LIMIT, validate_analysis_corpus)


def _projection_prices(value: dict[str, Any]) -> dict[str, dict[str, Any]]:
    snapshots = value["price_snapshots"]
    if not isinstance(snapshots, list) or len(snapshots) > 10000:
        raise ValueError("invalid projection price snapshots")
    if not snapshots and value["scenario"] is None:
        return {}
    if not snapshots or value["scenario"] is None:
        raise ValueError("projection scenario snapshots do not match")
    prices = {}
    for snapshot in snapshots:
        validate_price_snapshot(snapshot)
        identity = price_snapshot_id(snapshot)
        if identity in prices:
            raise ValueError("duplicate projection price snapshot")
        prices[identity] = snapshot
    scenario = validate_pricing_scenario(value["scenario"])
    if set(scenario["snapshot_ids"]) != set(prices):
        raise ValueError("projection scenario snapshots do not match")
    return prices


def _projection_component_cost(field: str, quantity: int, snapshot: dict[str, Any],
                               scenario: dict[str, Any], execution_time: str, ttl: int | None = None) -> Fraction:
    # Conservative subset: no inferred thresholds, aliases, tool identities, or TTLs.
    components = {"input_uncached": "input_uncached", "input_cache_read": "input_cache_read",
                  "output_total": "output", "input_cache_write": "input_cache_write"}
    if field not in components or scenario["threshold_rules"]:
        raise ValueError("projection component is not demonstrably priced")
    parameters = scenario["source_parameters"]
    for name in ("model", "service_tier", "region", "modality"):
        parameter = parameters[name]
        assumed = scenario["assumptions"].get(name)
        selected = assumed if assumed is not None else (parameter["value"] if parameter is not None else None)
        if selected is None or selected != snapshot[name]:
            raise ValueError("projection price parameters do not match")
    period = snapshot["effective_period"]
    if scenario["basis"] == "at_execution" and (period["state"] != "known" or
            not _instant(period["start"]) <= _instant(execution_time) < _instant(period["end"])):
        raise ValueError("projection price period is unavailable")
    matches = [rate for rate in snapshot["rates"] if rate["component"] == components[field]
               and rate["cache_ttl_seconds"] == ttl]
    if len(matches) != 1:
        raise ValueError("projection component rate is ambiguous")
    rate = matches[0]
    if (rate["unit"] != "tokens" or rate["threshold"] is not None or
            rate["cache_ttl_seconds"] != ttl or
            rate.get("multiplier", {}).get("state") != "none"):
        raise ValueError("projection rate applicability is unknown")
    unit_price = Fraction(rate["usd"]) / rate["unit_quantity"]
    denominator = unit_price.denominator
    for factor in (2, 5):
        while denominator % factor == 0:
            denominator //= factor
    if denominator != 1:
        raise ValueError("projection rate is not an exact decimal per unit")
    return unit_price * quantity


def _projection_possible_snapshot(field: str, snapshot: dict[str, Any],
                                  scenario: dict[str, Any], execution_time: str, ttl: int | None = None) -> bool:
    """Keep unknown applicability as a possible match, never silently exclude it."""
    components = {"input_uncached": "input_uncached", "input_cache_read": "input_cache_read",
                  "output_total": "output", "input_cache_write": "input_cache_write"}
    component = components.get(field)
    if component is None or not any(rate["component"] == component and rate["cache_ttl_seconds"] == ttl for rate in snapshot["rates"]):
        return False
    parameters = scenario["source_parameters"]
    for name in ("model", "service_tier", "region", "modality"):
        parameter = parameters[name]
        selected = scenario["assumptions"].get(name)
        if selected is None and parameter is not None:
            selected = parameter["value"]
        available = snapshot[name]
        if name == "model" and selected is not None and selected != available:
            if selected not in {alias["alias"] for alias in snapshot["aliases"]}:
                return False
        elif name != "model" and selected is not None and available is not None and selected != available:
            return False
    period = snapshot["effective_period"]
    if (scenario["basis"] == "at_execution" and period["state"] == "known" and
            not _instant(period["start"]) <= _instant(execution_time) < _instant(period["end"])):
        return False
    return True


def validate_lifecycle_projection(value: Any) -> dict[str, Any]:
    """Validate a self-contained projection without asserting external evidence provenance.

    Completeness and ownership are declarations. The receiving producer must verify
    their evidence and provenance, independently assess applicable quantities, and
    compare scalar flags before accepting a projection. Unsupported pricing remains
    unpriced rather than being rounded or guessed.
    """
    _fields(value, {"schema_version", "kind", "scope", "as_of", "contributors",
                    "evidence_objects", "price_snapshots", "scenario", "completeness"},
            {"cost_usd", "priced_subtotal_usd", "subtotal_quality", "display_cost_usd", "inventory"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"lifecycle_projection"}))
    _timestamp(value["as_of"])
    scope = value["scope"]
    _fields(scope, {"owner_kind", "owner_id", "attribution_quality"})
    _choice(scope["owner_kind"], frozenset({"run", "session"}))
    _private_identifier(scope["owner_id"])
    _choice(scope["attribution_quality"], frozenset({"unknown", "asserted", "verified", "inferred"}))
    completeness = value["completeness"]
    dimensions = {"inventory", "identity", "measurements", "pricing", "attribution"}
    _fields(completeness, dimensions)
    for state in completeness.values():
        _choice(state, frozenset({"complete", "partial", "unknown", "not_applicable"}))
    if value["contributors"] and any(completeness[name] == "not_applicable"
                                     for name in ("inventory", "identity", "measurements", "attribution")):
        raise ValueError("nonempty scope dimension is applicable")
    prices = _projection_prices(value)
    empty = not value["contributors"]
    if empty:
        inventory = validate_inventory(value.get("inventory"))
        evidence_objects = value["evidence_objects"]
        proof = next((item for item in evidence_objects if content_id(item) == inventory["evidence"]), None)
        if (inventory["owner_scope"] != {key: scope[key] for key in ("owner_kind", "owner_id")} or
                inventory["state"] != "complete" or inventory["expected_calls"] or inventory["expected_responses"] or
                inventory["unresolved_slots"] or any(state != "included" for state in inventory["coverage"].values()) or
                _instant(inventory["observed_at"]) > _instant(value["as_of"]) or
                proof is None or proof.get("kind") != "inventory_evidence" or
                proof.get("inventory_digest") != content_id({k: v for k, v in inventory.items() if k != "evidence"}) or
                any(proof.get(k) != inventory[k] for k in ("profile_id", "profile_version", "source_hash"))):
            raise ValueError("empty scope inventory is unavailable")
        if completeness != {"inventory": "complete", "identity": "not_applicable",
                            "measurements": "not_applicable", "pricing": "not_applicable",
                            "attribution": "not_applicable"}:
            raise ValueError("empty scope completeness mismatch")
    complete = all(state == "complete" for state in completeness.values()) or empty
    if complete and "cost_usd" not in value:
        raise ValueError("complete projection requires full cost")
    if "cost_usd" in value:
        validate_decimal(value["cost_usd"])
        if not complete or scope["attribution_quality"] != "verified":
            raise ValueError("full cost requires complete verified scope")
    if ("priced_subtotal_usd" in value) != ("subtotal_quality" in value):
        raise ValueError("partial amount requires quality")
    if "priced_subtotal_usd" in value:
        validate_decimal(value["priced_subtotal_usd"])
        _choice(value["subtotal_quality"], frozenset({"subtotal_only", "proven_lower_bound"}))
        if value["subtotal_quality"] == "proven_lower_bound" and (
                any(completeness[dimension] != "complete" for dimension in
                    ("identity", "pricing", "measurements", "attribution")) or
                (value["scenario"] is None or value["scenario"]["basis"] != "at_execution") or
                scope["attribution_quality"] != "verified"):
            raise ValueError("lower bound requires resolved work and historical pricing")
    if "display_cost_usd" in value:
        display = value["display_cost_usd"]
        if not isinstance(display, str) or re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", display) is None:
            raise ValueError("invalid display amount")
    objects = value["evidence_objects"]
    if not isinstance(objects, list) or len(objects) > 10000:
        raise ValueError("invalid projection evidence")
    evidence = {}
    for item in objects:
        validate_evidence_object(item)
        identity = content_id(item)
        if identity in evidence:
            raise ValueError("duplicate projection evidence")
        evidence[identity] = item
    for snapshot in prices.values():
        period = snapshot["effective_period"]
        if period["state"] == "known":
            item = evidence.get(period["evidence"])
            if (item is None or item["kind"] != "price_period_evidence" or
                    item["start"] != period["start"] or item["end"] != period["end"]):
                raise ValueError("price period evidence does not match")
    for field, parameter in (value["scenario"]["source_parameters"] if value["scenario"] is not None else {}).items():
        if parameter is None:
            continue
        item = evidence.get(parameter["evidence"])
        if (item is None or item["kind"] != "source_parameter_evidence" or
                item["field"] != field or item["value"] != parameter["value"]):
            raise ValueError("source parameter evidence does not match")
    contributors = value["contributors"]
    if not isinstance(contributors, list) or len(contributors) > 10000:
        raise ValueError("invalid projection contributors")
    seen_ids, seen_observations, seen_records = set(), set(), set()
    total = Fraction(0)
    priced_contributors = 0
    for contributor in contributors:
        _fields(contributor, {"contributor_id", "observation_ids", "profile_id", "profile_version",
                              "measurements", "price_snapshot_id", "priced_usd", "execution_time",
                              "parameter_evidence"})
        identity = contributor["contributor_id"]
        _private_identifier(identity)
        if identity in seen_ids:
            raise ValueError("duplicate contributor")
        seen_ids.add(identity)
        _identifier(contributor["profile_id"])
        _identifier(contributor["profile_version"])
        observations = contributor["observation_ids"]
        if not isinstance(observations, list) or not 1 <= len(observations) <= 10000:
            raise ValueError("invalid contributor observations")
        for observation in observations:
            _hash(observation)
            if observation in seen_observations:
                raise ValueError("overlapping contributor observations")
            seen_observations.add(observation)
        price_id = contributor["price_snapshot_id"]
        unpriced = price_id is None and contributor["priced_usd"] is None
        if not unpriced:
            _hash(price_id)
            if price_id not in prices:
                raise ValueError("missing contributor price")
        elif completeness["pricing"] == "complete":
            raise ValueError("unpriced contributor requires partial pricing")
        execution = contributor["execution_time"]
        _fields(execution, {"value", "evidence"})
        _timestamp(execution["value"])
        _hash(execution["evidence"])
        time_evidence = evidence.get(execution["evidence"])
        if (time_evidence is None or time_evidence["kind"] != "execution_time_evidence" or
                time_evidence["value"] != execution["value"] or
                time_evidence["profile_id"] != contributor["profile_id"]):
            raise ValueError("execution time evidence does not match")
        if _instant(execution["value"]) > _instant(value["as_of"]):
            raise ValueError("execution is after observation")
        record = (time_evidence["profile_id"], time_evidence["source_hash"], time_evidence["record_number"])
        if record in seen_records:
            raise ValueError("overlapping contributor source records")
        seen_records.add(record)
        parameters = value["scenario"]["source_parameters"] if value["scenario"] is not None else {}
        parameter_evidence = contributor["parameter_evidence"]
        known_fields = ({name for name, parameter in parameters.items() if parameter is not None}
                        if value["scenario"] is not None else set(parameter_evidence))
        if not known_fields <= {"model", "service_tier", "region", "modality"}:
            raise ValueError("invalid parameter evidence fields")
        _fields(parameter_evidence, known_fields)
        for field in known_fields:
            _hash(parameter_evidence[field])
            item = evidence.get(parameter_evidence[field])
            if (item is None or item["kind"] != "source_parameter_evidence" or
                    item["field"] != field or (value["scenario"] is not None and item["value"] != parameters[field]["value"]) or
                    item["profile_id"] != contributor["profile_id"] or
                    item["source_hash"] != time_evidence["source_hash"] or
                    item["record_number"] != time_evidence["record_number"]):
                raise ValueError("parameter evidence is outside contributor record")
        measurements = contributor["measurements"]
        if not isinstance(measurements, dict) or not measurements:
            raise ValueError("missing contributor measurements")
        if "input_cache_write" in measurements and "input_cache_write_unsplit" in measurements:
            raise ValueError("overlapping cache write measurements")
        amount = Fraction(0)
        for field, measurement in measurements.items():
            if field == "input_cache_write":
                if not isinstance(measurement, list) or not measurement or len(measurement) > 2:
                    raise ValueError("invalid cache writes")
                parts = []
                for part in measurement:
                    _fields(part, {"ttl", "tokens"})
                    _choice(part["ttl"], frozenset({"5m", "1h"}))
                    parts.append((part["ttl"], part["tokens"]))
                if len({ttl for ttl, _ in parts}) != len(parts):
                    raise ValueError("duplicate cache write ttl")
            else:
                _choice(field, _MEASUREMENT_FIELDS | frozenset({"input_cache_write_unsplit"}))
                parts = [(None, measurement)]
            for ttl, entry in parts:
                validate_measurement(entry)
                if entry["measurement_state"] != "final" or "evidence" not in entry:
                    if not unpriced or completeness["measurements"] == "complete":
                        raise ValueError("priced measurement requires final evidence")
                    continue
                item = evidence.get(entry["evidence"])
                if (item is None or item.get("kind") != "measurement_evidence" or
                        item["field"] != field or item["value"] != entry["value"] or
                        item["profile_id"] != contributor["profile_id"] or
                        item["source_hash"] != time_evidence["source_hash"] or
                        item["record_number"] != time_evidence["record_number"] or
                        (ttl is not None and item.get("ttl") != ttl)):
                    raise ValueError("measurement evidence does not match")
                if unpriced:
                    continue
                seconds = {"5m": 300, "1h": 3600}.get(ttl)
                matches = [snapshot for snapshot in prices.values()
                           if _projection_possible_snapshot(field, snapshot, value["scenario"], execution["value"], seconds)]
                if len(matches) != 1 or matches[0] is not prices[price_id]:
                    raise ValueError("projection component price is ambiguous")
                amount += _projection_component_cost(field, entry["value"], prices[price_id],
                                                     value["scenario"], execution["value"], seconds)
        if not unpriced:
            validate_decimal(contributor["priced_usd"])
            if amount != Fraction(contributor["priced_usd"]):
                raise ValueError("contributor amount does not match")
            total += amount
            priced_contributors += 1
    if contributors and not priced_contributors and "priced_subtotal_usd" in value:
        raise ValueError("unpriced scope has no priced subtotal")
    for field in ("cost_usd", "priced_subtotal_usd"):
        if field in value and total != Fraction(value[field]):
            raise ValueError("projection total does not match")
    for field, parameter in (value["scenario"]["source_parameters"] if value["scenario"] is not None else {}).items():
        if not empty and parameter is not None and not any(
                contributor["parameter_evidence"].get(field) == parameter["evidence"]
                for contributor in contributors):
            raise ValueError("scenario evidence is outside contributor records")
    if "display_cost_usd" in value:
        if "cost_usd" not in value:
            raise ValueError("display cost requires full cost")
        cents = total * 100
        whole, remainder = divmod(cents.numerator, cents.denominator)
        if remainder * 2 > cents.denominator or (remainder * 2 == cents.denominator and whole % 2):
            whole += 1
        if value["display_cost_usd"] != f"{whole // 100}.{whole % 100:02d}":
            raise ValueError("display cost does not match rounded total")
    if len(canonical_bytes(value)) > LIFECYCLE_PROJECTION_LIMIT:
        raise ValueError("projection exceeds byte limit")
    return value


def validate_lifecycle_projection_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, LIFECYCLE_PROJECTION_LIMIT, validate_lifecycle_projection)


def validate_usage_receipt(value: Any) -> dict[str, Any]:
    """Validate receipt structure; neither scope nor publication is proven here.

    Consumers must independently authenticate the receipt and verify its bundle
    and observation identities. Attribution quality is a claim, not proof.
    """
    _fields(value, {"schema_version", "kind", "bundle_sha256", "observation_ids",
                    "scope", "duplicate", "validator_version"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"usage_accepted"}))
    _hash(value["bundle_sha256"])
    observations = value["observation_ids"]
    if not isinstance(observations, list) or len(observations) > 10000:
        raise ValueError("invalid receipt observations")
    seen = set()
    for observation in observations:
        _hash(observation)
        if observation in seen:
            raise ValueError("duplicate receipt observation")
        seen.add(observation)
    scope = value["scope"]
    _fields(scope, {"owner_kind", "owner_id", "attribution_quality"})
    _choice(scope["owner_kind"], frozenset({"run", "session"}))
    _private_identifier(scope["owner_id"])
    _choice(scope["attribution_quality"], frozenset({"unknown", "asserted", "verified", "inferred"}))
    if type(value["duplicate"]) is not bool:
        raise ValueError("invalid duplicate flag")
    _identifier(value["validator_version"])
    if len(canonical_bytes(value)) > RECEIPT_LIMIT:
        raise ValueError("receipt exceeds byte limit")
    return value


def validate_usage_receipt_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, RECEIPT_LIMIT, validate_usage_receipt)


def validate_current_run_snapshot(value: Any, *, materialized_limit: int | None = None) -> dict[str, Any]:
    """Validate a bounded explicit snapshot without accessing persistent history.

    Receipt and attribution claims require independent authentication by the
    owner. A matching digest establishes structure, not provenance or consent.
    The owner must verify that each warning request or span belongs to its scope;
    a declared owner_scope is not proof of causal attribution.
    The owner must explicitly load selected parts, enforce input byte limits,
    and verify their size, digest, schema and scope before computing status.
    """
    _fields(value, {"schema_version", "kind", "owner_scope", "revision", "mode",
                    "segments", "accepted_receipts", "bundles", "inventories",
                    "inventory_evidence", "overlap_state", "warning_delivery", "bounds"}, {"parts", "part_references", "analysis_inputs", "duration_inputs"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"current_run_snapshot"}))
    scope = value["owner_scope"]
    _fields(scope, {"owner_kind", "owner_id"})
    _choice(scope["owner_kind"], frozenset({"run", "session"}))
    _private_identifier(scope["owner_id"])
    validate_counter(value["revision"])
    _choice(value["mode"], frozenset({"on", "off"}))
    _choice(value["overlap_state"], frozenset({"unknown", "resolved", "unresolved"}))
    bounds = value["bounds"]
    _fields(bounds, {"max_bytes", "max_entries", "max_source_bytes", "max_total_bytes", "max_records"})
    if (type(bounds["max_bytes"]) is not int or not 0 < bounds["max_bytes"] <= CURRENT_RUN_SNAPSHOT_LIMIT or
            type(bounds["max_entries"]) is not int or not 0 < bounds["max_entries"] <= 10000):
        raise ValueError("invalid snapshot bounds")
    for field in ("max_source_bytes", "max_total_bytes", "max_records"):
        validate_counter(bounds[field])
    if bounds["max_records"] == 0:
        raise ValueError("snapshot record limit must be positive")
    sections = ("segments", "accepted_receipts", "bundles", "inventories",
                "inventory_evidence", "warning_delivery")
    if "parts" in value:
        sections += ("parts",)
    if "part_references" in value:
        sections += ("part_references",)
    if "duration_inputs" in value:
        sections += ("duration_inputs",)
    if any(not isinstance(value[field], list) for field in sections):
        raise ValueError("invalid snapshot collection")
    if sum(len(value[field]) for field in sections) > bounds["max_entries"]:
        raise ValueError("snapshot entry limit exceeded")
    byte_limit = bounds["max_bytes"]
    if materialized_limit is not None:
        if (type(materialized_limit) is not int or materialized_limit < byte_limit or
                materialized_limit > byte_limit + bounds["max_total_bytes"]):
            raise ValueError("invalid materialized limit")
        byte_limit = materialized_limit
    if len(canonical_bytes(value)) > byte_limit:
        raise ValueError("snapshot byte limit exceeded")
    for field in sections:
        seen = set()
        for item in value[field]:
            member = canonical_bytes(item)
            if member in seen:
                raise ValueError("duplicate snapshot entry")
            seen.add(member)
    for segment in value["segments"]:
        validate_collection_segment(segment)
        if segment["owner_scope"] != scope:
            raise ValueError("foreign snapshot segment")
    part_paths = set()
    part_hashes = set()
    selected_bytes = 0
    for part in value.get("parts", []):
        _fields(part, {"kind", "local_path", "sha256", "size_bytes"})
        _choice(part["kind"], frozenset({"usage_bundle", "usage_accepted", "inventory",
                                         "inventory_evidence", "collection_segment", "warning_delivery"}))
        path = part["local_path"]
        if (not isinstance(path, str) or not path or
                any(char in "*?[]" or unicodedata.category(char).startswith("C") for char in path)):
            raise ValueError("invalid selected part path")
        _hash(part["sha256"])
        size = validate_counter(part["size_bytes"])
        if size > BUNDLE_LIMIT or size > bounds["max_source_bytes"]:
            raise ValueError("selected part exceeds byte limit")
        selected_bytes += size
        if selected_bytes > bounds["max_total_bytes"]:
            raise ValueError("selected parts exceed total byte limit")
        if path in part_paths or part["sha256"] in part_hashes:
            raise ValueError("duplicate selected part")
        part_paths.add(path)
        part_hashes.add(part["sha256"])
    for reference in value.get("part_references", []):
        _fields(reference, {"kind", "sha256", "size_bytes"})
        _choice(reference["kind"], frozenset({"usage_bundle", "usage_accepted", "inventory",
                                              "inventory_evidence", "collection_segment", "warning_delivery"}))
        _hash(reference["sha256"])
        size = validate_counter(reference["size_bytes"])
        if size > BUNDLE_LIMIT or size > bounds["max_source_bytes"]:
            raise ValueError("part reference exceeds byte limit")
        selected_bytes += size
        if selected_bytes > bounds["max_total_bytes"] or reference["sha256"] in part_hashes:
            raise ValueError("invalid part reference")
        part_hashes.add(reference["sha256"])
    deferred_bundles = any(item["kind"] == "usage_bundle" for item in value.get("part_references", []))
    bundles = {}
    for bundle in value["bundles"]:
        validate_usage_bundle(bundle)
        for item in bundle["segments"] + bundle["inventories"]:
            if item["owner_scope"] != scope:
                raise ValueError("foreign bundle entry")
        bundles[content_id(bundle)] = bundle
    accepted = set()
    for receipt in value["accepted_receipts"]:
        validate_usage_receipt(receipt)
        if any(receipt["scope"][key] != scope[key] for key in scope):
            raise ValueError("foreign snapshot receipt")
        digest = receipt["bundle_sha256"]
        bundle = bundles.get(digest)
        if bundle is None or set(receipt["observation_ids"]) != {
                observation_id(item) for item in bundle["observations"]}:
            raise ValueError("receipt is not bound to a snapshot bundle")
        accepted.add(digest)
    if accepted != set(bundles):
        raise ValueError("snapshot contains an unaccepted bundle")
    evidence = {}
    for item in value["inventory_evidence"]:
        validate_evidence_object(item)
        if item["kind"] != "inventory_evidence":
            raise ValueError("invalid inventory evidence")
        evidence[content_id(item)] = item
    for inventory in value["inventories"]:
        validate_inventory(inventory)
        if inventory["owner_scope"] != scope:
            raise ValueError("foreign snapshot inventory")
        if inventory["evidence"] is not None:
            item = evidence.get(inventory["evidence"])
            declaration = {key: entry for key, entry in inventory.items() if key != "evidence"}
            if (item is None or item["inventory_digest"] != content_id(declaration) or
                    any(item[key] != inventory[key] for key in ("profile_id", "profile_version", "source_hash"))):
                raise ValueError("unverified snapshot inventory")
    if "analysis_inputs" in value:
        analysis = value["analysis_inputs"]
        _fields(analysis, {"profile", "contexts", "snapshots", "scenario", "price_evidence", "ownership_evidence"})
        validate_source_profile(analysis["profile"])
        for field in ("contexts", "snapshots", "price_evidence", "ownership_evidence"):
            items = analysis[field]
            if not isinstance(items, list) or len(items) > 10000:
                raise ValueError("invalid analysis inputs")
            identities = [canonical_bytes(item) for item in items]
            if len(set(identities)) != len(identities):
                raise ValueError("duplicate analysis input")
        def count_nested_lists(item):
            if isinstance(item, list):
                return len(item) + sum(count_nested_lists(child) for child in item)
            if isinstance(item, dict):
                return sum(count_nested_lists(child) for child in item.values())
            return 0
        if sum(len(value[field]) for field in sections) + count_nested_lists(analysis) > bounds["max_entries"]:
            raise ValueError("snapshot analysis entry limit exceeded")
        observations = {observation_id(item): item for bundle in value["bundles"] for item in bundle["observations"]}
        seen_contexts = set()
        for context in analysis["contexts"]:
            validate_resolution_context(context)
            identity = context["observation_id"]
            observation = observations.get(identity)
            if (identity in seen_contexts or (observation is None and not deferred_bundles) or
                    (observation is not None and any(context[key] != observation[key] for key in ("profile_id", "profile_version", "source_hash", "record_number", "provider_scope", "counter_scope")))):
                raise ValueError("invalid context binding")
            seen_contexts.add(identity)
        snapshot_ids = []
        for price in analysis["snapshots"]:
            validate_price_snapshot(price)
            snapshot_ids.append(price_snapshot_id(price))
        if len(set(snapshot_ids)) != len(snapshot_ids):
            raise ValueError("duplicate price snapshot")
        scenario = analysis["scenario"]
        if scenario is not None:
            validate_pricing_scenario(scenario)
            if set(scenario["snapshot_ids"]) != set(snapshot_ids):
                raise ValueError("pricing snapshot mismatch")
        elif snapshot_ids or analysis["price_evidence"]:
            raise ValueError("pricing scenario required")
        for proof in analysis["price_evidence"]:
            validate_evidence_object(proof)
        seen_owners = set()
        for proof in analysis["ownership_evidence"]:
            _fields(proof, {"owner_scope", "observation_id", "basis"}, {"target_scope", "completion", "tool_coverage"})
            if (proof["owner_scope"] != scope or
                    (proof["observation_id"] not in observations and not deferred_bundles)):
                raise ValueError("invalid ownership binding")
            _choice(proof["basis"], frozenset({"verified_import", "correlation", "submission_metadata"}))
            if "target_scope" in proof:
                target = proof["target_scope"]
                _fields(target, {"owner_kind", "owner_id"})
                _choice(target["owner_kind"], frozenset({"request", "span"}))
                _private_identifier(target["owner_id"])
            for field, state in (("completion", "complete"), ("tool_coverage", "empty")):
                if field in proof:
                    evidence = proof[field]
                    _fields(evidence, {"scope", "state", "observed_at"})
                    if "target_scope" not in proof or evidence["scope"] != proof["target_scope"]:
                        raise ValueError("invalid scoped evidence")
                    _choice(evidence["state"], frozenset({state}))
                    _timestamp(evidence["observed_at"])
            if proof["observation_id"] in seen_owners:
                raise ValueError("duplicate ownership binding")
            seen_owners.add(proof["observation_id"])
    duration_inputs = value.get("duration_inputs", [])
    if len(duration_inputs) > 10000:
        raise ValueError("too many duration inputs")
    duration_scopes = set()
    for entry in duration_inputs:
        _fields(entry, {"candidate", "evidence", "history"}, {"scope"})
        target = entry.get("scope", scope)
        _fields(target, {"owner_kind", "owner_id"})
        _choice(target["owner_kind"], frozenset({"run", "span"}))
        _private_identifier(target["owner_id"])
        if target["owner_kind"] == "run" and target != scope:
            raise ValueError("foreign duration scope")
        candidate = entry["candidate"]
        _fields(candidate, {"id", "seconds", "closed", "clock_quality", "collection", "group"})
        _private_identifier(candidate["id"])
        seconds = candidate["seconds"]
        if seconds is not None:
            if isinstance(seconds, str):
                if len(seconds) > 256 or re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,3})?", seconds) is None:
                    raise ValueError("invalid millisecond duration")
            else:
                validate_counter(seconds)
        if type(candidate["closed"]) is not bool:
            raise ValueError("invalid duration closure")
        _choice(candidate["clock_quality"], frozenset({"measured", "approximate", "unknown"}))
        _choice(candidate["collection"], frozenset({"on", "off"}))
        group = candidate["group"]
        _fields(group, {"stage", "duration_kind", "clock_quality", "environment", "profile", "contract", "configuration"})
        for key, item in group.items():
            _identifier(item)
        _choice(group["duration_kind"], frozenset({"work", "run"}))
        key = (target["owner_kind"], target["owner_id"], group["duration_kind"])
        if key in duration_scopes:
            raise ValueError("ambiguous duration scope")
        duration_scopes.add(key)
        if group["clock_quality"] != candidate["clock_quality"]:
            raise ValueError("duration clock mismatch")
        evidence = entry["evidence"]
        _fields(evidence, {"owner_scope", "candidate_id", "clock_source", "observed_at"}, {"scope"})
        if (evidence["owner_scope"] != scope or evidence["candidate_id"] != candidate["id"] or
                (target != scope and (evidence.get("scope") != target or candidate["id"] != target["owner_id"])) or
                ("scope" in evidence and evidence["scope"] != target)):
            raise ValueError("invalid duration evidence binding")
        _choice(evidence["clock_source"], frozenset({"monotonic", "wall", "unknown"}))
        _timestamp(evidence["observed_at"])
        history = entry["history"]
        if history is not None:
            _fields(history, {"schema_version", "group", "corpus_hash", "window_start", "window_end",
                              "created_at", "expires_at", "sample_size", "median", "samples"})
            _version(history["schema_version"])
            _private_identifier(history["corpus_hash"])
            _fields(history["group"], set(group))
            for item in history["group"].values():
                _identifier(item)
            for field in ("window_start", "window_end", "created_at", "expires_at"):
                _timestamp(history[field])
            validate_counter(history["sample_size"])
            if history["median"] is not None:
                validate_decimal(history["median"])
            samples = history["samples"]
            if not isinstance(samples, list) or len(samples) > 10000:
                raise ValueError("invalid duration samples")
            for sample in samples:
                _fields(sample, {"id", "seconds", "closed", "clock_quality", "kind", "group"})
                _private_identifier(sample["id"])
                validate_counter(sample["seconds"])
                if type(sample["closed"]) is not bool:
                    raise ValueError("invalid sample closure")
                _choice(sample["clock_quality"], frozenset({"measured", "approximate", "unknown"}))
                _choice(sample["kind"], frozenset({"work", "run", "wait", "summary"}))
                _fields(sample["group"], set(group))
                for item in sample["group"].values():
                    _identifier(item)
    warning_ids = set()
    warning_scopes = set()
    for warning in value["warning_delivery"]:
        _fields(warning, {"warning_id", "policy_id", "policy_version", "scope", "owner_scope", "metric",
                          "episode", "crossing_state", "delivery_state"}, {"details"})
        if "details" in warning:
            details = warning["details"]
            _fields(details, {"measurement", "threshold", "completeness"})
            for item_name in ("measurement", "threshold", "completeness"):
                item = details[item_name]
                _fields(item, {"state", "value", "unit"})
                _choice(item["state"], frozenset({"final", "proven_lower_bound", "partial", "unknown"}))
                _choice(item["unit"], frozenset({"tokens", "USD", "fraction", "ms"}))
                number = item["value"]
                if item["state"] == "unknown":
                    if number is not None:
                        raise ValueError("unknown warning value")
                elif isinstance(number, dict):
                    _fields(number, {"numerator", "denominator"})
                    validate_counter(number["numerator"])
                    if validate_counter(number["denominator"]) == 0:
                        raise ValueError("invalid warning fraction")
                elif type(number) is int:
                    validate_counter(number)
                else:
                    if not isinstance(number, str) or re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", number) is None:
                        raise ValueError("invalid warning value")
                    if len(number) > 256:
                        raise ValueError("warning value too long")
        _private_identifier(warning["warning_id"])
        _identifier(warning["policy_id"])
        if validate_counter(warning["policy_version"]) == 0 or validate_counter(warning["episode"]) == 0:
            raise ValueError("invalid warning version or episode")
        if warning["owner_scope"] != scope:
            raise ValueError("foreign warning owner")
        warning_scope = warning["scope"]
        _fields(warning_scope, {"owner_kind", "owner_id"})
        _choice(warning_scope["owner_kind"], frozenset({"request", "span", "run"}))
        _private_identifier(warning_scope["owner_id"])
        if scope["owner_kind"] == "run" and warning_scope["owner_kind"] == "run" and warning_scope != scope:
            raise ValueError("foreign warning run")
        _choice(warning["metric"], frozenset({"duration_ms", "tokens", "cost_usd", "completeness"}))
        _choice(warning["crossing_state"], frozenset({"unknown", "below", "crossed", "cleared"}))
        _choice(warning["delivery_state"], frozenset({"unknown", "pending", "delivered", "failed"}))
        if warning["warning_id"] in warning_ids:
            raise ValueError("duplicate warning state")
        warning_ids.add(warning["warning_id"])
        identity = (warning["policy_id"], warning["policy_version"], warning["metric"],
                    warning_scope["owner_kind"], warning_scope["owner_id"], warning["episode"])
        if identity in warning_scopes:
            raise ValueError("duplicate warning episode scope")
        warning_scopes.add(identity)
    return value


def validate_current_run_snapshot_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, CURRENT_RUN_SNAPSHOT_LIMIT, validate_current_run_snapshot)


def validate_source_selection_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, SELECTION_LIMIT, validate_source_selection)


def validate_inventory_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, INVENTORY_LIMIT, validate_inventory)


def validate_collection_segment_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, SEGMENT_LIMIT, validate_collection_segment)


def validate_diagnostic_measurement_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, DIAGNOSTIC_LIMIT, validate_diagnostic_measurement)


def validate_observation_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_observation)


def validate_source_profile_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, PROFILE_LIMIT, validate_source_profile)


def validate_usage_bundle_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, BUNDLE_LIMIT, validate_usage_bundle)


def validate_tool_usage_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_tool_usage)


def _opportunity_identity(value: Any) -> None:
    _fields(value, {"task_revision", "input_revision", "acceptance_contract", "strategy", "repetition"})
    for name in ("task_revision", "input_revision", "acceptance_contract", "strategy"):
        _identifier(value[name])
    if validate_counter(value["repetition"]) == 0:
        raise ValueError("invalid opportunity repetition")


def validate_outcome_opportunity(value: Any) -> dict[str, Any]:
    _fields(value, {"schema_version", "kind", "identity", "observed_at"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"outcome_opportunity"}))
    _opportunity_identity(value["identity"])
    _timestamp(value["observed_at"])
    return value


def validate_outcome_attempt(value: Any) -> dict[str, Any]:
    _fields(value, {"schema_version", "kind", "attempt_id", "opportunity", "response_ids",
                    "category", "complete", "observed_at"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"outcome_attempt"}))
    _identifier(value["attempt_id"])
    _opportunity_identity(value["opportunity"])
    _choice(value["category"], frozenset({"workload", "production_verification", "experimental_evaluation"}))
    if type(value["complete"]) is not bool:
        raise ValueError("invalid attempt completeness")
    references = value["response_ids"]
    if not isinstance(references, list) or len(references) > 10000:
        raise ValueError("invalid response references")
    for reference in references:
        _private_identifier(reference)
    if len(set(references)) != len(references):
        raise ValueError("duplicate response reference")
    _timestamp(value["observed_at"])
    return value


def validate_acceptance_revision(value: Any) -> dict[str, Any]:
    _fields(value, {"schema_version", "kind", "opportunity", "status", "revision", "observed_at",
                    "acceptance_contract", "evaluator_id", "evidence_id"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"acceptance_revision"}))
    _opportunity_identity(value["opportunity"])
    _choice(value["status"], frozenset({"accepted", "rejected", "defect"}))
    if validate_counter(value["revision"]) == 0:
        raise ValueError("invalid acceptance revision")
    _timestamp(value["observed_at"])
    _identifier(value["acceptance_contract"])
    if value["acceptance_contract"] != value["opportunity"]["acceptance_contract"]:
        raise ValueError("acceptance contract mismatch")
    _private_identifier(value["evaluator_id"])
    _private_identifier(value["evidence_id"])
    return value


def validate_duration_graph(value: Any) -> dict[str, Any]:
    _fields(value, {"schema_version", "kind", "run_id", "root_checkpoint_id", "group",
                    "event_hashes", "complete", "observed_at"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"duration_graph"}))
    for field in ("run_id", "root_checkpoint_id", "group"):
        _identifier(value[field])
    if type(value["complete"]) is not bool:
        raise ValueError("invalid graph completeness")
    hashes = value["event_hashes"]
    if not isinstance(hashes, list) or not 1 <= len(hashes) <= 10000:
        raise ValueError("invalid graph event references")
    for digest in hashes:
        _hash(digest)
    if len(set(hashes)) != len(hashes):
        raise ValueError("duplicate graph event reference")
    _timestamp(value["observed_at"])
    return value


def validate_dimension_evidence(value: Any) -> dict[str, Any]:
    _fields(value, {'schema_version', 'kind', 'scope', 'observation_id', 'dimensions', 'observed_at'})
    _bounded_tree(value)
    _version(value['schema_version'])
    _choice(value['kind'], frozenset({'dimension_evidence'}))
    _fields(value['scope'], {'owner_kind', 'owner_id'})
    _choice(value['scope']['owner_kind'], frozenset({'run', 'session', 'task', 'span', 'shared_pool'}))
    _private_identifier(value['scope']['owner_id'])
    _hash(value['observation_id'])
    _timestamp(value['observed_at'])
    dimensions = value['dimensions']
    allowed = {'run', 'opportunity', 'root_approach', 'stage', 'role', 'effort', 'attempt'}
    if not isinstance(dimensions, dict) or not dimensions or not set(dimensions) <= allowed:
        raise ValueError('invalid report dimensions')
    for identifier in dimensions.values():
        _private_identifier(identifier)
    return value


def validate_dimension_evidence_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_dimension_evidence)


def validate_revision_metadata(value: Any) -> dict[str, Any]:
    _fields(value, {'schema_version', 'kind', 'scope', 'source_hash', 'expanded_hash', 'observed_at'})
    _bounded_tree(value)
    _version(value['schema_version'])
    _choice(value['kind'], frozenset({'revision_metadata'}))
    _fields(value['scope'], {'owner_kind', 'owner_id'})
    _choice(value['scope']['owner_kind'], frozenset({'run', 'session', 'task', 'span', 'shared_pool'}))
    _private_identifier(value['scope']['owner_id'])
    _hash(value['source_hash'])
    _hash(value['expanded_hash'])
    _timestamp(value['observed_at'])
    return value


def validate_ownership_selection(value: Any) -> dict[str, Any]:
    _fields(value, {'schema_version', 'kind', 'owner_scopes', 'entries', 'observed_at'})
    _bounded_tree(value)
    _version(value['schema_version'])
    _choice(value['kind'], frozenset({'ownership_selection'}))
    _timestamp(value['observed_at'])
    scopes = value['owner_scopes']
    entries = value['entries']
    if not isinstance(scopes, list) or len(scopes) > 256 or not isinstance(entries, list) or len(entries) > 10000:
        raise ValueError('invalid ownership selection')
    seen = set()
    for scope in scopes:
        _fields(scope, {'owner_kind', 'owner_id'})
        _choice(scope['owner_kind'], frozenset({'run', 'session', 'task', 'span', 'shared_pool'}))
        _private_identifier(scope['owner_id'])
        key = canonical_bytes(scope)
        if key in seen:
            raise ValueError('duplicate ownership scope')
        seen.add(key)
    for entry in entries:
        _fields(entry, {'observation_id', 'observed_at', 'attribution'})
        _hash(entry['observation_id'])
        _timestamp(entry['observed_at'])
        attr = entry['attribution']
        _fields(attr, {'response_id', 'provider', 'provider_scope', 'owner_kind', 'owner_id', 'candidates', 'basis'})
        for key in ('response_id', 'provider_scope', 'owner_id'):
            _private_identifier(attr[key])
        _identifier(attr['provider'])
        _choice(attr['owner_kind'], frozenset({'task', 'span', 'shared_pool', 'unattributed'}))
        _choice(attr['basis'], frozenset({'submission', 'correlation', 'verified_import'}))
        candidates = attr['candidates']
        if not isinstance(candidates, list) or len(candidates) > 64:
            raise ValueError('invalid attribution candidates')
        for candidate in candidates:
            _private_identifier(candidate)
        if len(set(candidates)) != len(candidates):
            raise ValueError('duplicate attribution candidate')
    return value


def validate_revision_metadata_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_revision_metadata)


def validate_ownership_selection_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_ownership_selection)


def validate_experimental_inventory(value: Any) -> dict[str, Any]:
    _fields(value, {"schema_version", "kind", "scope", "state", "expected_attempt_ids", "observed_at"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"experimental_inventory"}))
    scope = value["scope"]
    _fields(scope, {"owner_kind", "owner_id"})
    _choice(scope["owner_kind"], frozenset({"run", "session", "task", "span", "shared_pool"}))
    _private_identifier(scope["owner_id"])
    _choice(value["state"], frozenset({"complete", "partial", "unknown"}))
    attempts = value["expected_attempt_ids"]
    if not isinstance(attempts, list) or len(attempts) > 10000:
        raise ValueError("invalid experimental inventory")
    for attempt in attempts:
        _identifier(attempt)
    if len(set(attempts)) != len(attempts) or (value["state"] == "unknown" and attempts):
        raise ValueError("invalid experimental inventory")
    _timestamp(value["observed_at"])
    return value


def validate_experimental_inventory_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_experimental_inventory)


def validate_outcome_opportunity_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_outcome_opportunity)


def validate_outcome_attempt_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_outcome_attempt)


def validate_acceptance_revision_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_acceptance_revision)


def validate_duration_graph_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_duration_graph)


def validate_tool_usage_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_tool_usage)


def schema_registry(version: int = 1) -> dict[str, Any]:
    """Describe the available versioned validators and their input byte limits.

    Validator names refer to executable definitions in the exported source.
    Consumers must authenticate that source before executing it and must still
    validate actual inputs.
    """
    if type(version) is not int or version != 1:
        raise ValueError("unsupported schema version")
    definitions = {
        "source_profile": (validate_source_profile_json, PROFILE_LIMIT),
        "source_selection": (validate_source_selection_json, SELECTION_LIMIT),
        "observation": (validate_observation_json, OBSERVATION_LIMIT),
        "tool_usage": (validate_tool_usage_json, OBSERVATION_LIMIT),
        "usage_bundle": (validate_usage_bundle_json, BUNDLE_LIMIT),
        "inventory": (validate_inventory_json, INVENTORY_LIMIT),
        "collection_segment": (validate_collection_segment_json, SEGMENT_LIMIT),
        "diagnostic_measurement": (validate_diagnostic_measurement_json, DIAGNOSTIC_LIMIT),
        "price_snapshot": (validate_price_snapshot_json, PRICE_SNAPSHOT_LIMIT),
        "pricing_scenario": (validate_pricing_scenario_json, PRICING_SCENARIO_LIMIT),
        "warning_policy": (validate_warning_policy_json, WARNING_POLICY_LIMIT),
        "analysis_corpus": (validate_analysis_corpus_json, ANALYSIS_CORPUS_LIMIT),
        "usage_accepted": (validate_usage_receipt_json, RECEIPT_LIMIT),
        "lifecycle_projection": (validate_lifecycle_projection_json, LIFECYCLE_PROJECTION_LIMIT),
        "current_run_snapshot": (validate_current_run_snapshot_json, CURRENT_RUN_SNAPSHOT_LIMIT),
    }
    source = Path(__file__).read_bytes().decode("utf-8")
    return {
        "schema_version": version,
        "measurement_states": sorted(MEASUREMENT_STATES),
        "measurement_reasons": sorted(MEASUREMENT_REASONS),
        "validator_source": source,
        "validator_source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "kinds": {kind: {"validator": validator.__name__, "max_bytes": limit}
                  for kind, (validator, limit) in definitions.items()},
    }


def export_schema_registry() -> str:
    """Return compact registry JSON only after checking its executable bindings."""
    registry = schema_registry()
    if not isinstance(registry, dict) or set(registry) != {
        "schema_version", "measurement_states", "measurement_reasons", "kinds",
        "validator_source", "validator_source_sha256"
    } or type(registry["schema_version"]) is not int or registry["schema_version"] != 1:
        raise ValueError("invalid schema registry")
    if (registry["measurement_states"] != sorted(MEASUREMENT_STATES) or
            registry["measurement_reasons"] != sorted(MEASUREMENT_REASONS)):
        raise ValueError("invalid schema vocabulary")
    if (not isinstance(registry["validator_source"], str) or
            hashlib.sha256(registry["validator_source"].encode("utf-8")).hexdigest() !=
            registry["validator_source_sha256"]):
        raise ValueError("invalid schema source")
    kinds = registry["kinds"]
    if not isinstance(kinds, dict) or not kinds:
        raise ValueError("invalid schema kinds")
    for kind, definition in kinds.items():
        if (not isinstance(kind, str) or not kind or not isinstance(definition, dict) or
                set(definition) != {"validator", "max_bytes"} or
                not isinstance(definition["validator"], str) or
                not callable(globals().get(definition["validator"])) or
                type(definition["max_bytes"]) is not int or definition["max_bytes"] <= 0):
            raise ValueError("invalid schema definition")
    return json.dumps(registry, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def validate_resolution_context(value: Any) -> dict[str, Any]:
    """Validate bounded per-observation facts; provenance requires a verifier."""
    _fields(value, {'observation_id', 'profile_id', 'profile_version', 'source_hash',
                    'record_number', 'provider_scope', 'counter_scope', 'provider', 'session_id',
                    'event', 'execution_time', 'parameters', 'cache_ttl_seconds', 'evidence_objects'})
    _bounded_tree(value)
    _hash(value['observation_id'])
    for field in ('profile_id', 'profile_version', 'provider'):
        _identifier(value[field])
    _hash(value['source_hash'])
    validate_counter(value['record_number'])
    _private_identifier(value['provider_scope'])
    _private_identifier(value['session_id'])
    _choice(value['counter_scope'], _COUNTER_SCOPES)
    event = value['event']
    if not isinstance(event, dict) or event.get('kind') not in ('snapshot', 'delta', 'terminal'):
        raise ValueError('invalid event')
    required = {'kind', 'final'} if event['kind'] == 'snapshot' else {'kind', 'sequence'}
    optional = {'sequence', 'correction_of'} if event['kind'] == 'snapshot' else set()
    _fields(event, required, optional)
    if 'final' in event and type(event['final']) is not bool:
        raise ValueError('invalid finality')
    if 'sequence' in event and validate_counter(event['sequence']) == 0:
        raise ValueError('invalid sequence')
    if 'correction_of' in event:
        _private_identifier(event['correction_of'])
        if not event['final'] or 'sequence' not in event:
            raise ValueError('invalid correction reference')
    if value['execution_time'] is not None:
        _timestamp(value['execution_time'])
    parameters = value['parameters']
    _fields(parameters, {'model', 'service_tier', 'region', 'modality'})
    for name, item in parameters.items():
        if item is None:
            continue
        if name == 'model':
            if not isinstance(item, str) or len(item) > 256 or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]*(?:/[A-Za-z0-9][A-Za-z0-9._:-]*)?', item) is None:
                raise ValueError('invalid model')
        else:
            _identifier(item)
    ttls = value['cache_ttl_seconds']
    if not isinstance(ttls, dict) or len(ttls) > 256:
        raise ValueError('invalid cache durations')
    for ttl, seconds in ttls.items():
        _identifier(ttl)
        if validate_counter(seconds) == 0:
            raise ValueError('invalid cache duration')
    proofs = value['evidence_objects']
    if not isinstance(proofs, list) or len(proofs) > 10000:
        raise ValueError('invalid context evidence')
    for proof in proofs:
        if isinstance(proof, dict) and proof.get('kind') == 'rate_parameter_evidence':
            _fields(proof, {'schema_version', 'kind', 'profile_id', 'source_hash', 'record_number', 'field', 'value'})
            _version(proof['schema_version'])
            _identifier(proof['profile_id'])
            _hash(proof['source_hash'])
            validate_counter(proof['record_number'])
            _choice(proof['field'], frozenset({'cache_ttl_seconds'}))
            if validate_counter(proof['value']) == 0:
                raise ValueError('invalid cache duration')
        else:
            validate_evidence_object(proof)
    if len(canonical_bytes(value)) > OBSERVATION_LIMIT:
        raise ValueError('context exceeds byte limit')
    return value



def validate_tool_usage(value: Any) -> dict[str, Any]:
    """Validate an explicit tool usage record without asserting provenance."""
    _fields(value, {"schema_version", "kind", "usage_id", "profile_id", "profile_version", "source_hash",
                    "record_number", "provider_scope", "tool_id", "unit", "quantity", "observed_at",
                    "execution_time", "parameters", "evidence_objects"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"tool_usage"}))
    _private_identifier(value["usage_id"])
    _private_identifier(value["provider_scope"])
    for name in ("profile_id", "profile_version", "tool_id", "unit"):
        _identifier(value[name])
    _hash(value["source_hash"])
    validate_counter(value["record_number"])
    validate_counter(value["quantity"])
    _timestamp(value["observed_at"])
    if value["execution_time"] is not None:
        _timestamp(value["execution_time"])
    _fields(value["parameters"], {"model", "service_tier", "region", "modality"})
    for name, item in value["parameters"].items():
        if item is None:
            continue
        if name == "model":
            if (not isinstance(item, str) or len(item) > 256 or
                    re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*(?:/[A-Za-z0-9][A-Za-z0-9._:-]*)?", item) is None):
                raise ValueError("invalid model")
        else:
            _identifier(item)
    proofs = value["evidence_objects"]
    if not isinstance(proofs, list) or not 1 <= len(proofs) <= 10000:
        raise ValueError("invalid tool evidence")
    identities = set()
    quantities = []
    for proof in proofs:
        validate_evidence_object(proof)
        identity = content_id(proof)
        if identity in identities:
            raise ValueError("duplicate tool evidence")
        identities.add(identity)
        if proof.get("kind") == "tool_quantity_evidence":
            quantities.append(proof)
    if (len(quantities) != 1 or
            any(quantities[0].get(name) != value[name] for name in
                ("profile_id", "source_hash", "record_number", "tool_id", "unit")) or
            quantities[0]["value"] != value["quantity"]):
        raise ValueError("tool quantity evidence mismatch")
    if len(canonical_bytes(value)) > OBSERVATION_LIMIT:
        raise ValueError("tool usage exceeds limit")
    return value
