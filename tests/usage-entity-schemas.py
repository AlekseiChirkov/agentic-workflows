#!/usr/bin/env python3
"""Offline synthetic source-profile contract checks."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contract', ROOT / 'scripts/usage_telemetry_contract.py')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def call(name, *args):
    return getattr(contract, name, lambda *args: None)(*args)


def profile():
    return {
        'schema_version': 1, 'kind': 'source_profile',
        'profile_id': 'synthetic-profile', 'profile_version': '1',
        'provider': 'synthetic-provider', 'runtime': 'synthetic-runtime',
        'format_version': '1',
        'counter_fields': [{'path': ['usage', 'input'], 'measurement': 'input_uncached',
                            'counter_scope': 'response_total'}],
        'identity_scope': {'account': 'provider_account', 'response': 'response_id'},
        'finality': {'signals': ['complete'], 'status': 'verified'},
        'inventory': {'status': 'verified', 'evidence': 'synthetic-inventory-evidence'},
        'capabilities': {'cache': 'unknown', 'effort': 'unknown', 'tools': 'unknown'},
        'known_gaps': ['historical_prices'], 'verified_at': '2026-01-02T03:04:05Z',
        'source': 'https://example.invalid/synthetic-format',
    }


class SourceProfileTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_source_profile', value), value)

    def test_complete_profile_preserves_verified_and_unknown_capabilities(self):
        value = profile()
        self.assert_valid(value)
        self.assertEqual(value['capabilities'], {'cache': 'unknown', 'effort': 'unknown', 'tools': 'unknown'})

    def test_required_fields_and_unknown_fields_are_rejected_without_exposure(self):
        value = profile()
        self.assert_valid(value)
        for field in value:
            with self.subTest(field=field), self.assertRaises(ValueError):
                call('validate_source_profile', {key: item for key, item in value.items() if key != field})
        private = 'PRIVATE_SOURCE_CONTENT_SENTINEL'
        for field in ('raw_content', 'source_path', 'unexpected'):
            with self.subTest(field=field):
                with self.assertRaises(ValueError) as error:
                    call('validate_source_profile', value | {field: private})
                self.assertNotIn(private, str(error.exception))

    def test_versions_types_and_capabilities_are_checked(self):
        value = profile()
        self.assert_valid(value)
        for changes in ({'schema_version': 2}, {'schema_version': True},
                        {'kind': 'other'}, {'profile_version': ''},
                        {'capabilities': {'cache': True, 'effort': 'unknown', 'tools': 'unknown'}},
                        {'capabilities': {'cache': 'supported', 'effort': 'unknown'}},
                        {'counter_fields': []}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                call('validate_source_profile', value | changes)

    def test_identifiers_and_nested_fields_are_bounded_and_closed(self):
        value = profile()
        self.assert_valid(value)
        self.assert_valid(value | {'profile_id': 'p' * 256})
        for identifier in ('p' * 257, '/private/path', 'private source text'):
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                call('validate_source_profile', value | {'profile_id': identifier})
        bad = copy.deepcopy(value)
        bad['counter_fields'][0]['raw_content'] = 'PRIVATE_SOURCE_CONTENT_SENTINEL'
        with self.assertRaises(ValueError) as error:
            call('validate_source_profile', bad)
        self.assertNotIn('PRIVATE_SOURCE_CONTENT_SENTINEL', str(error.exception))

    def test_canonical_and_input_byte_limits(self):
        value = profile()
        data = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'PROFILE_LIMIT', size, create=True):
            self.assert_valid(value)
        with patch.object(contract, 'PROFILE_LIMIT', size - 1, create=True):
            with self.assertRaises(ValueError):
                call('validate_source_profile', value)
        with patch.object(contract, 'PROFILE_LIMIT', len(data), create=True):
            self.assertEqual(call('validate_source_profile_json', data), value)
            with self.assertRaises(ValueError):
                call('validate_source_profile_json', data + b' ')


if __name__ == '__main__':
    unittest.main()
