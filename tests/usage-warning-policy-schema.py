#!/usr/bin/env python3
"""Offline validation of explicit, versioned warning policy data."""
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


def policy():
    return {
        'schema_version': 1, 'kind': 'warning_policy', 'policy_id': 'local-policy',
        'policy_version': 1, 'scope': 'run',
        'created_at': '2026-01-01T00:00:00Z', 'expires_at': '2026-02-01T00:00:00Z',
        'token_threshold': {'value': 1000, 'unit': 'tokens'},
        'money_threshold': {'value': '1.25', 'unit': 'USD'},
        'minimum_completeness': {'value': '0.80', 'unit': 'fraction'},
        'historical_cohort': {
            'corpus_hash': 'a' * 64,
            'window_start': '2025-01-01T00:00:00Z',
            'window_end': '2025-12-31T00:00:00Z',
            'sample_size': 6, 'median_seconds': '120.5',
            'stage': 'execution', 'duration_kind': 'work', 'clock_quality': 'measured',
            'environment': 'local', 'profile': 'standard', 'contract': 'default',
            'configuration': 'default',
        },
    }


class WarningPolicySchemaTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_warning_policy', value), value)

    def test_complete_policy_and_explicit_unknowns_are_preserved(self):
        value = policy()
        self.assert_valid(value)
        value.update(token_threshold=None, money_threshold=None,
                     minimum_completeness=None, historical_cohort=None)
        self.assert_valid(value)
        for scope in ('request', 'span', 'run'):
            value['scope'] = scope
            self.assert_valid(value)
        value['token_threshold'] = {'value': 0, 'unit': 'tokens'}
        value['money_threshold'] = {'value': '0', 'unit': 'USD'}
        value['minimum_completeness'] = {'value': '1', 'unit': 'fraction'}
        self.assert_valid(value)
        value['minimum_completeness']['value'] = '0'
        self.assert_valid(value)

    def test_complete_fields_version_scope_and_time_are_required(self):
        value = policy()
        self.assert_valid(value)
        for field in value:
            with self.subTest(missing=field), self.assertRaises(ValueError):
                call('validate_warning_policy', {k: v for k, v in value.items() if k != field})
        for change in ({'schema_version': True}, {'schema_version': 2}, {'kind': 'budget'},
                       {'policy_id': '/private/path'}, {'policy_id': ''},
                       {'policy_version': True}, {'policy_version': 0},
                       {'scope': 'project'}, {'scope': None},
                       {'created_at': '/secret'}, {'expires_at': '2025-01-01T00:00:00Z'},
                       {'expires_at': '2026-02-30T00:00:00Z'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_warning_policy', value | change)

    def test_threshold_types_ranges_units_and_unknown_fields(self):
        value = policy()
        self.assert_valid(value)
        invalid = {
            'token_threshold': [{'value': -1, 'unit': 'tokens'}, {'value': True, 'unit': 'tokens'},
                                {'value': 9007199254740992, 'unit': 'tokens'},
                                {'value': 1, 'unit': 'USD'}],
            'money_threshold': [{'value': '-0.1', 'unit': 'USD'}, {'value': 1.1, 'unit': 'USD'},
                                {'value': 'NaN', 'unit': 'USD'}, {'value': '1', 'unit': 'EUR'}],
            'minimum_completeness': [{'value': '-0.1', 'unit': 'fraction'},
                                     {'value': '1.0001', 'unit': 'fraction'},
                                     {'value': 0.5, 'unit': 'fraction'},
                                     {'value': '0.5', 'unit': '%'}],
        }
        for field, choices in invalid.items():
            for choice in choices:
                with self.subTest(field=field, choice=choice), self.assertRaises(ValueError):
                    call('validate_warning_policy', value | {field: choice})
            extra = copy.deepcopy(value)
            extra[field]['raw'] = 'PRIVATE_CONTENT_SENTINEL'
            with self.subTest(field=field), self.assertRaises(ValueError) as error:
                call('validate_warning_policy', extra)
            self.assertNotIn('PRIVATE_CONTENT_SENTINEL', str(error.exception))

    def test_historical_evidence_requires_scope_window_and_explicit_statistics(self):
        value = policy()
        self.assert_valid(value)
        for field in value['historical_cohort']:
            invalid = copy.deepcopy(value)
            del invalid['historical_cohort'][field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                call('validate_warning_policy', invalid)
        for change in ({'corpus_hash': '/private/path'}, {'sample_size': -1},
                       {'sample_size': True}, {'median_seconds': '-1'},
                       {'median_seconds': 1.5}, {'window_start': 'not-a-time'},
                       {'window_end': '2024-01-01T00:00:00Z'},
                       {'clock_quality': '/private/clock'}, {'stage': '/private/path'},
                       {'raw': 'PRIVATE_CONTENT_SENTINEL'}):
            invalid = copy.deepcopy(value)
            invalid['historical_cohort'].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError) as error:
                call('validate_warning_policy', invalid)
            self.assertNotIn('PRIVATE_CONTENT_SENTINEL', str(error.exception))
        empty = copy.deepcopy(value)
        empty['historical_cohort'].update(sample_size=0, median_seconds=None)
        self.assert_valid(empty)

    def test_private_content_is_not_returned_in_validation_errors(self):
        value = policy()
        self.assert_valid(value)
        secret = 'PRIVATE_CONTENT_SENTINEL'
        for field in ('raw_content', 'prompt', 'token'):
            with self.subTest(field=field), self.assertRaises(ValueError) as error:
                call('validate_warning_policy', value | {field: secret})
            self.assertNotIn(secret, str(error.exception))

    def test_identity_and_json_duplicate_and_size_limits(self):
        value = policy()
        self.assert_valid(value)
        identity = call('warning_policy_id', value)
        self.assertRegex(identity, r'^[0-9a-f]{64}$')
        altered = copy.deepcopy(value)
        altered['policy_version'] += 1
        self.assertNotEqual(call('warning_policy_id', altered), identity)
        data = json.dumps(value, separators=(',', ':')).encode()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'WARNING_POLICY_LIMIT', size, create=True):
            self.assert_valid(value)
        with patch.object(contract, 'WARNING_POLICY_LIMIT', size - 1, create=True):
            with self.assertRaises(ValueError):
                call('validate_warning_policy', value)
        with patch.object(contract, 'WARNING_POLICY_LIMIT', len(data), create=True):
            self.assertEqual(call('validate_warning_policy_json', data), value)
            with self.assertRaises(ValueError):
                call('validate_warning_policy_json', data + b' ')
        with self.assertRaises(ValueError):
            call('validate_warning_policy_json', b'{"schema_version":1,"schema_version":1}')


if __name__ == '__main__':
    unittest.main()
