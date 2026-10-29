#!/usr/bin/env python3
"""Offline checks for typed usage measurements."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "usage_telemetry_contract", ROOT / "scripts" / "usage_telemetry_contract.py"
)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def validate(value):
    # Keep the tests collectable before the public validator exists.
    validator = getattr(contract, "validate_measurement", lambda value: None)
    return validator(value)


def known(value):
    return {"measurement_state": "final", "value": value,
            "reasons": [], "evidence": "record-1"}


class TypedMeasurementTests(unittest.TestCase):
    def test_evidenced_zero_is_a_numeric_value(self):
        result = validate(known(0))
        self.assertEqual(result, known(0))
        self.assertIs(type(result["value"]), int)

    def test_unavailable_measurement_has_reason_and_no_value(self):
        measurement = {"measurement_state": "unavailable", "reasons": ["source_unavailable"]}
        result = validate(measurement)
        self.assertEqual(result, measurement)
        self.assertNotIn("value", result)

    def test_all_measurement_states_preserve_supported_evidence(self):
        values = (
            known(1),
            {"measurement_state": "partial", "value": 1,
             "reasons": ["incomplete_source"], "evidence": "record-1"},
            {"measurement_state": "unavailable", "reasons": ["source_unavailable"]},
            {"measurement_state": "conflicted", "reasons": ["conflicting_evidence"]},
        )
        for measurement in values:
            with self.subTest(state=measurement["measurement_state"]):
                self.assertEqual(validate(measurement), measurement)

    def test_counter_boundaries_and_invalid_values(self):
        self.assertEqual(validate(known(0)), known(0))
        self.assertEqual(validate(known(9007199254740991)), known(9007199254740991))
        for value in (True, False, -1, 1.5, 9007199254740992):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate(known(value))

    def test_unavailable_placeholders_and_missing_reason_are_rejected(self):
        valid = {"measurement_state": "unavailable", "reasons": ["source_unavailable"]}
        self.assertEqual(validate(valid), valid)
        for value in (0, "", "unknown"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate(valid | {"value": value})
        with self.assertRaises(ValueError):
            validate({"measurement_state": "unavailable", "reasons": []})

    def test_invalid_state_and_unevidenced_zero_are_rejected(self):
        self.assertEqual(validate(known(0)), known(0))
        for invalid in (
            {"measurement_state": "not_applicable", "reasons": ["source_unavailable"]},
            {"measurement_state": "final", "value": 0, "reasons": []},
        ):
            with self.subTest(measurement=invalid), self.assertRaises(ValueError):
                validate(invalid)

    def test_specified_reasons_are_typed_and_preserved(self):
        reasons = (
            "unsupported_profile", "invalid_schema", "invalid_counter", "counter_conflict",
            "inventory_unknown", "stream_incomplete", "identity_unresolved", "revision_conflict",
            "unpriced_component", "attribution_unverified", "timing_unavailable",
            "source_record_quarantined", "source_changed", "digest_mismatch", "scope_violation",
            "forbidden_field", "input_limit_exceeded", "projection_mismatch", "publication_conflict",
            "stored_artifact_corrupt", "io_unavailable", "collection_disabled",
            "dependency_unavailable", "policy_unavailable", "delivery_pending",
            "accepted_denominator_zero", "comparison_ineligible",
        )
        for reason in reasons:
            measurement = {"measurement_state": "unavailable", "reasons": [reason]}
            with self.subTest(reason=reason):
                self.assertEqual(validate(measurement), measurement)
        with self.assertRaises(ValueError):
            validate({"measurement_state": "unavailable", "reasons": ["not_a_reason"]})

    def test_duplicate_keys_are_rejected_before_measurement_validation(self):
        self.assertEqual(validate(known(1)), known(1))
        with self.assertRaises(ValueError):
            contract.parse_json('{"measurement_state":"final","value":1,"value":0}')


if __name__ == "__main__":
    unittest.main()
