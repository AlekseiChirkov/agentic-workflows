#!/usr/bin/env python3
"""Offline checks for the versioned measurement and observation contract."""

import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "usage_telemetry_contract", ROOT / "scripts" / "usage_telemetry_contract.py"
)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def validate_measurement(value):
    validator = getattr(contract, "validate_measurement", lambda value: None)
    return validator(value)


def validate_observation(value):
    validator = getattr(contract, "validate_observation", lambda value: None)
    return validator(value)


class TypedSchemaTests(unittest.TestCase):
    def test_unavailable_measurement_retains_reason_and_omits_value(self):
        measurement = {"state": "unavailable", "reasons": ["source_unavailable"]}
        self.assertEqual(validate_measurement(measurement), measurement)
        self.assertNotIn("value", validate_measurement(measurement))

    def test_evidenced_zero_remains_numeric(self):
        measurement = {"state": "final", "value": 0, "reasons": [], "evidence": "record-1"}
        self.assertEqual(validate_measurement(measurement), measurement)
        self.assertIs(type(validate_measurement(measurement)["value"]), int)

    def test_missing_measurement_requires_reason_and_rejects_placeholder_values(self):
        for measurement in (
            {"state": "unavailable", "reasons": []},
            {"state": "unavailable", "value": 0, "reasons": ["source_unavailable"]},
            {"state": "unavailable", "value": "unknown", "reasons": ["source_unavailable"]},
            {"state": "unavailable", "value": "", "reasons": ["source_unavailable"]},
        ):
            with self.subTest(measurement=measurement), self.assertRaises(ValueError):
                validate_measurement(measurement)

    def test_counters_reject_invalid_types_and_out_of_range_values(self):
        for value in (True, -1, 1.5, 9007199254740992):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_measurement({"state": "final", "value": value,
                                      "reasons": [], "evidence": "record-1"})

    def test_observation_rejects_unsupported_version_and_unknown_fields(self):
        observation = {"schema_version": 1, "kind": "request_usage",
                       "profile_id": "profile-1", "source_hash": "a" * 64,
                       "record_number": 1, "observed_at": "2026-01-02T03:04:05Z",
                       "measurements": {"input_tokens": {"state": "unavailable",
                                                         "reasons": ["source_unavailable"]}}}
        for change in ({"schema_version": 2}, {"unexpected": "raw source content"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_observation(observation | change)

    def test_observation_rejects_oversized_identifier_and_payload(self):
        observation = {"schema_version": 1, "kind": "request_usage",
                       "profile_id": "p" * 257, "source_hash": "a" * 64,
                       "record_number": 1, "observed_at": "2026-01-02T03:04:05Z",
                       "measurements": {}}
        with self.assertRaises(ValueError):
            validate_observation(observation)
        with self.assertRaises(ValueError):
            validate_observation(observation | {"profile_id": "p", "padding": "é" * 524289})

    def test_producer_exports_versioned_usage_schema(self):
        result = subprocess.run(["bash", str(ROOT / "scripts" / "log-step.sh"), "contract"],
                                check=True, text=True, capture_output=True)
        entries = dict(line.split("=", 1) for line in result.stdout.splitlines())
        schema = json.loads(entries.get("usage_schema", "null"))
        self.assertIsInstance(schema, dict)
        self.assertEqual(schema["schema_version"], 1)
        self.assertEqual(set(schema["measurement_states"]),
                         {"partial", "final", "unavailable", "conflicted"})


if __name__ == "__main__":
    unittest.main()
