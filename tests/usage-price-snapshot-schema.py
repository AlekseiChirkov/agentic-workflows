#!/usr/bin/env python3
"""Offline contract checks for immutable price snapshots."""
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


def snapshot():
    return {
        'schema_version': 1, 'kind': 'price_snapshot', 'currency': 'USD',
        'retrieved_at': '2026-01-01T00:00:00Z',
        'effective_period': {'state': 'known', 'start': '2025-01-01T00:00:00Z',
                             'end': '2027-01-01T00:00:00Z', 'evidence': 'a' * 64},
        'model': 'example-model',
        'aliases': [{'alias': 'example-alias', 'evidence': 'b' * 64}],
        'modality': 'text', 'service_tier': 'standard', 'region': 'example-region',
        'rates': [
            {'component': 'input_uncached', 'usd': '2', 'unit': 'tokens',
             'unit_quantity': 1000000, 'cache_ttl_seconds': None, 'threshold': None},
            {'component': 'input_cache_write', 'usd': '2.5', 'unit': 'tokens',
             'unit_quantity': 1000000, 'cache_ttl_seconds': 300,
             'threshold': {'operand': 'input_tokens', 'operator': '>=', 'value': 200000}},
            {'component': 'tool', 'usd': '0.02', 'unit': 'request',
             'unit_quantity': 1, 'cache_ttl_seconds': None, 'threshold': None},
        ],
        'primary_sources': ['https://example.org/pricing'],
    }


class PriceSnapshotSchemaTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_price_snapshot', value), value)

    def test_complete_snapshot_preserves_declared_parameters(self):
        self.assert_valid(snapshot())
        value = snapshot()
        value['rates'][0]['usd'] = '0'
        self.assert_valid(value)
        # Unsupported exact divisors are retained as evidence; pricing decides whether
        # a component can be evaluated exactly and must never silently round it.
        value['rates'][0]['unit_quantity'] = 3
        self.assert_valid(value)

    def test_unknown_period_and_explicit_unknown_applicability(self):
        value = snapshot()
        value['effective_period'] = {'state': 'unknown', 'reason': 'historical_period_unavailable'}
        value['region'] = None
        value['service_tier'] = None
        value['modality'] = None
        self.assert_valid(value)
        for period in ({'state': 'unknown'}, {'state': 'known'},
                       {'state': 'unknown', 'reason': ''},
                       {'state': 'unknown', 'reason': 'unavailable', 'start': '2020-01-01T00:00:00Z'}):
            with self.subTest(period=period), self.assertRaises(ValueError):
                call('validate_price_snapshot', value | {'effective_period': period})

    def test_malformed_rates_and_required_fields_fail(self):
        value = snapshot()
        self.assert_valid(value)
        for amount in (0, True, '', '00', '0.0', '1.00', '+1', '-1', '1e3', '$1', '1,000', 'NaN'):
            bad = copy.deepcopy(value)
            bad['rates'][0]['usd'] = amount
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                call('validate_price_snapshot', bad)
        for field in value:
            with self.subTest(missing=field), self.assertRaises(ValueError):
                call('validate_price_snapshot', {key: item for key, item in value.items() if key != field})
        for change in ({'currency': 'EUR'}, {'schema_version': True}, {'schema_version': 2},
                       {'kind': 'other'}, {'model': ''}, {'rates': []}, {'primary_sources': []}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_price_snapshot', value | change)

    def test_effective_period_timestamps_and_verified_aliases(self):
        value = snapshot()
        self.assert_valid(value)
        for change in ({'retrieved_at': '2026-02-30T00:00:00Z'},
                       {'retrieved_at': '2026-01-01T00:00:00+00:00'},
                       {'effective_period': {'state': 'known', 'start': '2027-01-01T00:00:00Z',
                                             'end': '2025-01-01T00:00:00Z', 'evidence': 'a' * 64}},
                       {'aliases': [{'alias': 'example-alias'}]},
                       {'aliases': [{'alias': 'example-alias', 'evidence': '/private/path'}]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_price_snapshot', value | change)

    def test_rate_units_cache_and_thresholds_are_typed(self):
        value = snapshot()
        self.assert_valid(value)
        changes = ({'unit': ''}, {'unit_quantity': 0}, {'unit_quantity': True},
                   {'unit_quantity': 9007199254740992}, {'cache_ttl_seconds': -1},
                   {'cache_ttl_seconds': True}, {'component': 'arbitrary'},
                   {'threshold': {'operand': '', 'operator': '>=', 'value': 1}},
                   {'threshold': {'operand': 'input_tokens', 'operator': '=', 'value': 1}},
                   {'threshold': {'operand': 'input_tokens', 'operator': '>', 'value': -1}})
        for change in changes:
            bad = copy.deepcopy(value)
            bad['rates'][1].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_price_snapshot', bad)
        for key in value['rates'][0]:
            bad = copy.deepcopy(value)
            del bad['rates'][0][key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                call('validate_price_snapshot', bad)

    def test_forbidden_fields_and_source_urls_do_not_leak(self):
        value = snapshot()
        self.assert_valid(value)
        secret = 'PRIVATE_CONTENT_SENTINEL'
        with self.assertRaises(ValueError) as error:
            call('validate_price_snapshot', value | {'raw_content': secret})
        self.assertNotIn(secret, str(error.exception))
        for url in ('/private/pricing', 'file:///private', 'https://user:secret@example.org/',
                    'https://example.org/?token=secret', 'https://example.org/#secret'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                call('validate_price_snapshot', value | {'primary_sources': [url]})

    def test_identity_and_set_order(self):
        value = snapshot()
        self.assert_valid(value)
        identity = call('price_snapshot_id', value)
        self.assertIsInstance(identity, str)
        self.assertRegex(identity, r'^[0-9a-f]{64}$')
        reordered = copy.deepcopy(value)
        reordered['rates'].reverse()
        self.assertEqual(call('price_snapshot_id', reordered), identity)
        reordered['rates'][0]['usd'] = '3'
        self.assertNotEqual(call('price_snapshot_id', reordered), identity)

    def test_raw_and_canonical_byte_limits_and_duplicate_keys(self):
        value = snapshot()
        self.assert_valid(value)
        data = json.dumps(value, separators=(',', ':')).encode()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'PRICE_SNAPSHOT_LIMIT', size, create=True):
            self.assert_valid(value)
        with patch.object(contract, 'PRICE_SNAPSHOT_LIMIT', size - 1, create=True):
            with self.assertRaises(ValueError):
                call('validate_price_snapshot', value)
        with patch.object(contract, 'PRICE_SNAPSHOT_LIMIT', len(data), create=True):
            self.assertEqual(call('validate_price_snapshot_json', data), value)
            with self.assertRaises(ValueError):
                call('validate_price_snapshot_json', data + b' ')
        with self.assertRaises(ValueError):
            call('validate_price_snapshot_json', b'{"schema_version":1,"schema_version":1}')


if __name__ == '__main__':
    unittest.main()
