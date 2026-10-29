"""Strict JSON primitives and deterministic identities for usage telemetry.

Set-valued paths and their ordering keys are supplied by the owning schema;
arrays at all other paths retain their order. These primitives do not validate
a complete envelope.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
import json
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


def validate_measurement(value: Any) -> dict[str, Any]:
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
        counter = validate_counter(value["value"])
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
    envelope = kind in {"request_usage", "inventory", "reported_aggregate", "usage_bundle"}

    def schema_set(path: tuple[str, ...]) -> bool:
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
        if not envelope:
            return False
        if path[-2:] == ("attribution", "candidates"):
            return True
        if len(path) >= 3 and path[-3] == "measurements" and path[-1] == "reasons":
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

    def normalize(item: Any, path: tuple[str, ...]) -> Any:
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise ValueError("JSON object keys must be strings")
            return {key: normalize(child, path + (key,)) for key, child in item.items()}
        if isinstance(item, list):
            children = [normalize(child, path) for child in item]
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
    _fields(value, required, {"capability_evidence"})
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
    if not isinstance(measurements, dict) or not measurements or measurements.keys() - _MEASUREMENT_FIELDS:
        raise ValueError("invalid measurement fields")
    for measurement in measurements.values():
        validate_measurement(measurement)
    if len(canonical_bytes(value)) > OBSERVATION_LIMIT:
        raise ValueError("observation exceeds byte limit")
    if "id" in value:
        _hash(value["id"])
        if value["id"] != observation_id(value):
            raise ValueError("observation identifier mismatch")
    return value


def validate_evidence_object(value: Any) -> dict[str, Any]:
    """Validate the separate evidence record; the hash is not an authenticity claim."""
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
    _fields(value, {"schema_version", "kind", "profile_id", "source_hash", "record_number", "field", "value"})
    _bounded_tree(value)
    _version(value["schema_version"])
    _choice(value["kind"], frozenset({"measurement_evidence"}))
    _identifier(value["profile_id"])
    _hash(value["source_hash"])
    validate_counter(value["record_number"])
    _choice(value["field"], _MEASUREMENT_FIELDS)
    validate_counter(value["value"])
    return value


def verify_measurement_evidence(observation: Any, field: str, evidence: Any) -> bool:
    """Verify digest and field/source linkage; external provenance remains unverified."""
    try:
        validate_observation(observation)
        validate_evidence_object(evidence)
        measurement = observation["measurements"][field]
        return (measurement.get("evidence") == content_id(evidence)
                and evidence["field"] == field and evidence["value"] == measurement.get("value")
                and all(evidence[key] == observation[key]
                        for key in ("profile_id", "source_hash", "record_number")))
    except (ValueError, KeyError, TypeError, RecursionError):
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
    start = datetime.fromisoformat(value["start"][:-1] + "+00:00")
    if value["end"] is not None:
        _timestamp(value["end"])
        if datetime.fromisoformat(value["end"][:-1] + "+00:00") < start:
            raise ValueError("invalid segment boundaries")
    gap = value["gap_before"]
    _fields(gap, {"state", "start", "end"})
    _choice(gap["state"], frozenset({"unknown", "none", "present"}))
    if gap["state"] == "present":
        _timestamp(gap["start"])
        _timestamp(gap["end"])
        gap_start = datetime.fromisoformat(gap["start"][:-1] + "+00:00")
        gap_end = datetime.fromisoformat(gap["end"][:-1] + "+00:00")
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
            if "evidence" in measurement and not verify_measurement_evidence(
                    observation, field, evidence_by_hash.get(measurement["evidence"])):
                raise ValueError("unverified measurement evidence")
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
                                         "price_snapshot", "acceptance_revision"}))
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
