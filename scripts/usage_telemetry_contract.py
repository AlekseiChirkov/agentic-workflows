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
        if kind == "source_profile" and path in {
            ("counter_fields",), ("counter_fields", "includes"),
            ("known_gaps",), ("finality", "signals"),
        }:
            return True
        if not envelope:
            return False
        if path[-2:] == ("attribution", "candidates"):
            return True
        if len(path) >= 3 and path[-3] == "measurements" and path[-1] == "reasons":
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
    attribution = value["attribution"]
    _fields(attribution, {"owner_kind", "quality", "candidates"})
    _choice(attribution["owner_kind"], frozenset({"span", "task", "shared_pool", "unattributed"}))
    _choice(attribution["quality"], frozenset({"asserted", "verified", "inferred"}))
    candidates = attribution["candidates"]
    if not isinstance(candidates, list) or len(candidates) > 64:
        raise ValueError("invalid owner candidates")
    for candidate in candidates:
        _private_identifier(candidate)
    if len(set(candidates)) != len(candidates):
        raise ValueError("duplicate owner candidate")
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
    # Entity-specific schemas are supplied separately; fail closed until available.
    if value["inventories"] or value["segments"] or value["diagnostics"]:
        raise ValueError("unsupported bundle entity")
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
    evidence_by_hash = {}
    for evidence in value["evidence_objects"]:
        validate_evidence_object(evidence)
        digest = content_id(evidence)
        if digest in evidence_by_hash:
            raise ValueError("duplicate evidence")
        evidence_by_hash[digest] = evidence
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


def validate_source_selection_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, SELECTION_LIMIT, validate_source_selection)


def validate_observation_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, OBSERVATION_LIMIT, validate_observation)


def validate_source_profile_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, PROFILE_LIMIT, validate_source_profile)


def validate_usage_bundle_json(data: str | bytes) -> dict[str, Any]:
    return _validate_json(data, BUNDLE_LIMIT, validate_usage_bundle)
