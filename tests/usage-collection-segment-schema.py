#!/usr/bin/env python3
"""Offline checks for scoped, bounded collection segment declarations."""
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


def segment():
    return {
        'schema_version': 1, 'kind': 'collection_segment',
        'segment_id': opaque('a'),
        'owner_scope': {'owner_kind': 'run', 'owner_id': opaque('b')},
        'mode': 'on',
        'start': '2026-01-02T03:00:00Z', 'end': '2026-01-02T04:00:00Z',
        'gap_before': {'state': 'unknown', 'start': None, 'end': None},
    }


def bundle():
    return {'schema_version': 1, 'kind': 'usage_bundle', 'profile_id': 'profile',
            'profile_version': '1', 'project_id': opaque('d'), 'run_id': 'run',
            'sources': [], 'observations': [], 'evidence_objects': [], 'inventories': [],
            'segments': [segment()], 'diagnostics': []}


class CollectionSegmentTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_collection_segment', value), value)

    def test_declared_boundaries_mode_and_explicit_unknown_are_preserved(self):
        value = segment()
        self.assert_valid(value)
        self.assertEqual(value['gap_before']['state'], 'unknown')
        opened = copy.deepcopy(value)
        opened.update(mode='off', end=None)
        self.assert_valid(opened)
        known_gap = copy.deepcopy(value)
        known_gap['gap_before'] = {'state': 'present', 'start': '2026-01-02T02:00:00Z',
                                   'end': '2026-01-02T03:00:00Z'}
        self.assert_valid(known_gap)
        continuous = copy.deepcopy(value)
        continuous['gap_before'] = {'state': 'none', 'start': None, 'end': None}
        self.assert_valid(continuous)

    def test_required_fields_versions_modes_and_private_payload(self):
        value = segment()
        self.assert_valid(value)
        for field in value:
            with self.subTest(field=field), self.assertRaises(ValueError):
                call('validate_collection_segment', {k: v for k, v in value.items() if k != field})
        for change in ({'schema_version': 2}, {'schema_version': True}, {'kind': 'other'},
                       {'mode': 'unknown'}, {'owner_scope': {}},
                       {'segment_id': '/private/path'},
                       {'owner_scope': {'owner_kind': 'run', 'owner_id': '/private/path'}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_collection_segment', value | change)
        secret = 'PRIVATE_CONTENT_SENTINEL'
        with self.assertRaises(ValueError) as error:
            call('validate_collection_segment', value | {'raw_content': secret})
        self.assertNotIn(secret, str(error.exception))

    def test_times_and_gap_state_do_not_invent_continuity(self):
        value = segment()
        self.assert_valid(value)
        for change in ({'start': '2026-01-02'}, {'end': '/private/path'},
                       {'end': '2026-01-02T02:00:00Z'},
                       {'gap_before': {'state': 'unknown', 'start': '2026-01-02T02:00:00Z', 'end': None}},
                       {'gap_before': {'state': 'present', 'start': None, 'end': None}},
                       {'gap_before': {'state': 'present', 'start': '2026-01-02T02:30:00Z',
                                       'end': '2026-01-02T02:00:00Z'}},
                       {'gap_before': {'state': 'present', 'start': '2026-01-02T02:00:00Z',
                                       'end': '2026-01-02T04:00:00Z'}},
                       {'gap_before': {'state': 'yes', 'start': None, 'end': None}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_collection_segment', value | change)

    def test_size_limit_and_duplicate_json_keys(self):
        value = segment()
        self.assert_valid(value)
        data = json.dumps(value, separators=(',', ':')).encode()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'SEGMENT_LIMIT', size, create=True):
            self.assert_valid(value)
        with patch.object(contract, 'SEGMENT_LIMIT', size - 1, create=True):
            with self.assertRaises(ValueError):
                call('validate_collection_segment', value)
        with patch.object(contract, 'SEGMENT_LIMIT', len(data), create=True):
            self.assertEqual(call('validate_collection_segment_json', data), value)
            with self.assertRaises(ValueError):
                call('validate_collection_segment_json', data + b' ')
        with self.assertRaises(ValueError):
            call('validate_collection_segment_json', b'{"schema_version":1,"schema_version":1}')

    def test_bundle_accepts_segment_and_rejects_invalid_or_duplicate_entries(self):
        value = bundle()
        self.assertEqual(call('validate_usage_bundle', value), value)
        invalid = copy.deepcopy(value)
        invalid['segments'][0]['mode'] = 'invalid'
        with self.assertRaises(ValueError):
            call('validate_usage_bundle', invalid)
        duplicate = copy.deepcopy(value)
        duplicate['segments'].append(copy.deepcopy(duplicate['segments'][0]))
        with self.assertRaises(ValueError):
            call('validate_usage_bundle', duplicate)


if __name__ == '__main__':
    unittest.main()
