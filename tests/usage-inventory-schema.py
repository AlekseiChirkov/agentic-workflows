#!/usr/bin/env python3
"""Offline inventory schema checks with independent synthetic declarations."""
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


def opaque(digit):
    return 'sha256:' + digit * 64


def inventory():
    value = {
        'schema_version': 1, 'kind': 'inventory',
        'profile_id': 'profile', 'profile_version': '1', 'source_hash': 'a' * 64,
        'owner_scope': {'owner_kind': 'run', 'owner_id': opaque('b')},
        'window': {'start': '2026-01-02T03:00:00Z', 'end': '2026-01-02T04:00:00Z'},
        'observed_at': '2026-01-02T04:01:00Z', 'state': 'partial',
        'evidence': 'c' * 64,
        'expected_calls': [{'call_id': opaque('1')}],
        'expected_responses': [{'response_id': opaque('2'), 'call_id': opaque('1')},
                               {'response_id': opaque('3'), 'call_id': opaque('1')}],
        'unresolved_slots': [{'call_id': opaque('1'), 'reason': 'identity_unresolved'}],
        'coverage': {'children': 'unknown', 'internal_checks': 'unknown', 'tools': 'unknown'},
    }
    value['evidence'] = contract.content_id(inventory_evidence(value))
    return value


def inventory_evidence(value):
    """Bind a separate evidence record to the full declaration without a cycle."""
    declaration = {key: item for key, item in value.items() if key != 'evidence'}
    return {'schema_version': 1, 'kind': 'inventory_evidence',
            'profile_id': value['profile_id'], 'profile_version': value['profile_version'],
            'source_hash': value['source_hash'],
            'inventory_digest': contract.content_id(declaration)}


def bundle():
    entry = inventory()
    return {'schema_version': 1, 'kind': 'usage_bundle', 'profile_id': 'profile',
            'profile_version': '1', 'project_id': opaque('d'), 'run_id': 'run',
            'sources': [{'source_id': opaque('e'), 'sha256': 'a' * 64}],
            'observations': [], 'evidence_objects': [inventory_evidence(entry)], 'inventories': [entry],
            'segments': [], 'diagnostics': []}


class InventoryTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_inventory', value), value)

    def test_known_responses_independent_calls_and_unresolved_slots_are_preserved(self):
        value = inventory()
        self.assert_valid(value)
        self.assertEqual(len(value['expected_calls']), 1)
        self.assertEqual(len(value['expected_responses']), 2)
        self.assertEqual(value['coverage']['tools'], 'unknown')
        unknown = copy.deepcopy(value)
        unknown.update(state='unknown', evidence=None)
        self.assert_valid(unknown)
        complete = copy.deepcopy(value)
        complete.update(state='complete', unresolved_slots=[])
        self.assert_valid(complete)

    def test_required_fields_versions_and_private_payload(self):
        value = inventory()
        self.assert_valid(value)
        for field in value:
            with self.subTest(field=field), self.assertRaises(ValueError):
                call('validate_inventory', {k: v for k, v in value.items() if k != field})
        for change in ({'schema_version': 2}, {'schema_version': True}, {'kind': 'other'},
                       {'state': 'final'}, {'owner_scope': {}}, {'evidence': '/private/path'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_inventory', value | change)
        secret = 'PRIVATE_CONTENT_SENTINEL'
        with self.assertRaises(ValueError) as error:
            call('validate_inventory', value | {'raw_content': secret})
        self.assertNotIn(secret, str(error.exception))

    def test_state_evidence_and_unresolved_slots_are_consistent(self):
        value = inventory()
        self.assert_valid(value)
        for change in ({'state': 'complete'}, {'evidence': None},
                       {'state': 'unknown', 'evidence': 'a' * 64}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_inventory', value | change)
        empty = copy.deepcopy(value)
        empty.update(state='complete', expected_calls=[], expected_responses=[], unresolved_slots=[])
        self.assert_valid(empty)

    def test_scope_window_coverage_and_links_are_closed(self):
        value = inventory()
        self.assert_valid(value)
        for change in ({'window': {'start': '2026-01-02', 'end': '2026-01-03'}},
                       {'window': {'start': '2026-01-03T00:00:00Z', 'end': '2026-01-02T00:00:00Z'}},
                       {'owner_scope': {'owner_kind': 'run', 'owner_id': '/private/path'}},
                       {'coverage': {'children': 'yes', 'internal_checks': 'unknown', 'tools': 'unknown'}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_inventory', value | change)
        broken = copy.deepcopy(value)
        broken['expected_responses'][0]['call_id'] = opaque('4')
        with self.assertRaises(ValueError):
            call('validate_inventory', broken)
        broken = copy.deepcopy(value)
        broken['expected_calls'].append(copy.deepcopy(broken['expected_calls'][0]))
        with self.assertRaises(ValueError):
            call('validate_inventory', broken)

    def test_collection_and_json_bounds(self):
        value = inventory()
        self.assert_valid(value)
        for field in ('expected_calls', 'expected_responses', 'unresolved_slots'):
            invalid = copy.deepcopy(value)
            invalid[field] = [None] * 10001
            with self.subTest(field=field), self.assertRaises(ValueError):
                call('validate_inventory', invalid)
        data = json.dumps(value, separators=(',', ':')).encode()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'INVENTORY_LIMIT', size, create=True):
            self.assert_valid(value)
        with patch.object(contract, 'INVENTORY_LIMIT', size - 1, create=True):
            with self.assertRaises(ValueError):
                call('validate_inventory', value)
        with patch.object(contract, 'INVENTORY_LIMIT', len(data), create=True):
            self.assertEqual(call('validate_inventory_json', data), value)
            with self.assertRaises(ValueError):
                call('validate_inventory_json', data + b' ')
        with self.assertRaises(ValueError):
            call('validate_inventory_json', b'{"schema_version":1,"schema_version":1}')

    def test_bundle_integration_and_scope(self):
        value = bundle()
        self.assertEqual(call('validate_usage_bundle', value), value)
        for field, bad in (('state', 'complete'), ('source_hash', 'f' * 64),
                           ('profile_id', 'other'), ('profile_version', '2')):
            invalid = copy.deepcopy(value)
            invalid['inventories'][0][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                call('validate_usage_bundle', invalid)
        invalid = copy.deepcopy(value)
        invalid['inventories'].append(copy.deepcopy(invalid['inventories'][0]))
        with self.assertRaises(ValueError):
            call('validate_usage_bundle', invalid)

    def test_complete_inventory_requires_response_or_unresolved_call(self):
        value = inventory()
        value.update(state='complete', unresolved_slots=[])
        self.assert_valid(value)
        missing = copy.deepcopy(value)
        missing['expected_responses'] = []
        with self.assertRaises(ValueError):
            call('validate_inventory', missing)
        partial = copy.deepcopy(missing)
        partial['state'] = 'partial'
        partial['unresolved_slots'] = [{'call_id': opaque('1'), 'reason': 'identity_unresolved'}]
        self.assert_valid(partial)

    def test_bundle_requires_linked_inventory_evidence(self):
        value = bundle()
        self.assertEqual(call('validate_usage_bundle', value), value)
        missing = copy.deepcopy(value)
        missing['evidence_objects'] = []
        with self.assertRaises(ValueError):
            call('validate_usage_bundle', missing)
        unrelated = copy.deepcopy(value)
        unrelated['inventories'][0]['evidence'] = 'f' * 64
        with self.assertRaises(ValueError):
            call('validate_usage_bundle', unrelated)
        tampered = copy.deepcopy(value)
        tampered['inventories'][0]['coverage']['tools'] = 'included'
        with self.assertRaises(ValueError):
            call('validate_usage_bundle', tampered)

    def test_missing_inventory_evidence_never_proves_complete(self):
        value = bundle()
        value['evidence_objects'] = []
        value['inventories'][0].update(state='complete', unresolved_slots=[], evidence='f' * 64)
        with self.assertRaises(ValueError):
            call('validate_usage_bundle', value)


if __name__ == '__main__':
    unittest.main()
