#!/usr/bin/env python3
"""Offline checks for deterministic usage telemetry encoding."""

import hashlib
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "usage_telemetry_contract.py"


class CanonicalEncodingTests(unittest.TestCase):
    def setUp(self):
        global contract
        if MODULE_PATH.exists():
            spec = importlib.util.spec_from_file_location("usage_telemetry_contract", MODULE_PATH)
            contract = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(contract)
        else:
            def unimplemented(*args, **kwargs):
                return None

            contract = SimpleNamespace(**{name: unimplemented for name in (
                "parse_json", "canonical_bytes", "content_id", "observation_id",
                "validate_counter", "validate_decimal")})

    def test_key_and_set_permutations_preserve_bytes_and_hash(self):
        first = {"schema_version": 1, "members": ["β", "a"], "nested": {"z": 0, "a": 1}}
        second = {"nested": {"a": 1, "z": 0}, "members": ["a", "β"], "schema_version": 1}
        first_bytes = contract.canonical_bytes(first, set_paths=(("members",),))
        second_bytes = contract.canonical_bytes(second, set_paths=(("members",),))
        self.assertIsInstance(first_bytes, bytes)
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(contract.content_id(first, set_paths=(("members",),)),
                         contract.content_id(second, set_paths=(("members",),)))
        self.assertEqual(contract.content_id(first, set_paths=(("members",),)),
                         hashlib.sha256(first_bytes).hexdigest())

    def test_stream_order_changes_bytes_and_identity(self):
        first = {"schema_version": 1, "stream": ["first", "second"]}
        second = {"schema_version": 1, "stream": ["second", "first"]}
        self.assertNotEqual(contract.canonical_bytes(first), contract.canonical_bytes(second))
        self.assertNotEqual(contract.content_id(first), contract.content_id(second))

    def test_strict_json_rejects_duplicate_keys_and_special_numbers(self):
        for text in ('{"a":1,"a":2}', '{"outer":{"a":1,"a":2}}',
                     '{"a":NaN}', '{"a":Infinity}', '{"a":-Infinity}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                contract.parse_json(text)

    def test_counter_rejects_boolean_fraction_negative_and_overflow(self):
        for value in (True, False, -1, 1.5, 9007199254740992):
            with self.subTest(value=value), self.assertRaises(ValueError):
                contract.validate_counter(value)
        self.assertEqual(contract.validate_counter(0), 0)
        self.assertEqual(contract.validate_counter(9007199254740991), 9007199254740991)

    def test_decimal_rejects_noncanonical_prices(self):
        for value in ("", "+1", "1e3", "01", "1.0", "0.00", "-1", "1,000", "$1", 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                contract.validate_decimal(value)
        self.assertEqual(contract.validate_decimal("0"), "0")
        self.assertEqual(contract.validate_decimal("0.00264"), "0.00264")

    def test_unknown_schema_version_is_rejected(self):
        for version in (0, 2, True, "1"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                contract.canonical_bytes({"schema_version": version})

    def test_fixed_observation_has_stable_documented_utf8_vector(self):
        observation = {"schema_version": 1, "observed_at": "2026-01-02T03:04:05Z",
                       "name": "é", "counts": [], "id": "ignored"}
        vector = ('{"counts":[],"name":"é","observed_at":"2026-01-02T03:04:05Z",'
                  '"schema_version":1}').encode("utf-8")
        without_id = {key: value for key, value in observation.items() if key != "id"}
        self.assertEqual(contract.canonical_bytes(without_id), vector)
        expected = hashlib.sha256(vector).hexdigest()
        with patch("time.time", return_value=1767312000):
            first_id = contract.observation_id(observation)
            first_bytes = contract.canonical_bytes(without_id)
        with patch("time.time", return_value=1767398400):
            second_id = contract.observation_id(dict(reversed(list(observation.items()))))
            second_bytes = contract.canonical_bytes(without_id)
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(first_id, expected)
        self.assertEqual(second_id, expected)


if __name__ == "__main__":
    unittest.main()
