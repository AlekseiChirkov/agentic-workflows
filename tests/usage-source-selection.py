#!/usr/bin/env python3
"""Offline tests for explicit, bounded local source selections."""
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


def selection():
    return {
        'schema_version': 1, 'kind': 'source_selection',
        'profile_id': 'synthetic-profile', 'profile_version': '1',
        'owner_scope': {'owner_kind': 'task', 'owner_id': 'sha256:' + '1' * 64},
        'attribution_map': [{'source_id': 'sha256:' + '2' * 64,
                             'owner_kind': 'unattributed', 'quality': 'unknown',
                             'candidates': []}],
        'observed_at': '2026-01-02T03:04:05Z',
        'sources': [{'source_id': 'sha256:' + '2' * 64,
                     'local_path': '/local/selected.jsonl', 'sha256': '3' * 64,
                     'size_bytes': 100}],
        'max_source_bytes': 100, 'max_total_bytes': 100, 'max_records': 10,
    }


class SourceSelectionTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_source_selection', value), value)

    def test_complete_selection_and_explicit_unknowns_are_preserved(self):
        value = selection()
        self.assert_valid(value)
        self.assertEqual(value['attribution_map'][0]['quality'], 'unknown')
        prefix = copy.deepcopy(value)
        prefix['sources'][0]['verified_prefix_bytes'] = 50
        self.assert_valid(prefix)

    def test_required_fields_versions_and_closed_fields(self):
        value = selection()
        self.assert_valid(value)
        for field in value:
            with self.subTest(field=field), self.assertRaises(ValueError):
                call('validate_source_selection', {k: v for k, v in value.items() if k != field})
        for changes in ({'schema_version': 2}, {'schema_version': True}, {'kind': 'other'},
                        {'observed_at': '2026-01-02'}, {'profile_id': ''}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                call('validate_source_selection', value | changes)
        secret = 'PRIVATE_CONTENT_SENTINEL'
        with self.assertRaises(ValueError) as error:
            call('validate_source_selection', value | {'raw_content': secret})
        self.assertNotIn(secret, str(error.exception))

    def test_source_entries_require_safe_shape_and_exact_digests(self):
        value = selection()
        self.assert_valid(value)
        for field in ('source_id', 'local_path', 'sha256', 'size_bytes'):
            bad = copy.deepcopy(value)
            del bad['sources'][0][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                call('validate_source_selection', bad)
        for field, bad_value in [('sha256', 'a' * 63), ('sha256', 'A' * 64),
                                 ('source_id', '/private/source'), ('local_path', ''),
                                 ('local_path', '/local/*.jsonl'), ('size_bytes', -1),
                                 ('size_bytes', True), ('verified_prefix_bytes', 101),
                                 ('verified_prefix_bytes', -1)]:
            bad = copy.deepcopy(value)
            bad['sources'][0][field] = bad_value
            with self.subTest(field=field, value=bad_value), self.assertRaises(ValueError):
                call('validate_source_selection', bad)
        bad = copy.deepcopy(value)
        bad['sources'].append(copy.deepcopy(bad['sources'][0]))
        with self.assertRaises(ValueError):
            call('validate_source_selection', bad)

    def test_limits_are_explicit_integer_and_cover_selected_extent(self):
        value = selection()
        self.assert_valid(value)
        for field, bad_value in [('max_source_bytes', 99), ('max_total_bytes', 99),
                                 ('max_records', 0), ('max_records', True),
                                 ('max_total_bytes', -1), ('max_source_bytes', '100')]:
            with self.subTest(field=field, value=bad_value), self.assertRaises(ValueError):
                call('validate_source_selection', value | {field: bad_value})
        # A selected prefix permits a bounded read even if the complete file is larger.
        prefix = copy.deepcopy(value)
        prefix['sources'][0]['verified_prefix_bytes'] = 50
        prefix['max_source_bytes'] = prefix['max_total_bytes'] = 50
        self.assert_valid(prefix)

    def test_entries_and_attribution_are_bounded_and_closed(self):
        value = selection()
        self.assert_valid(value)
        bad = copy.deepcopy(value)
        bad['sources'] = bad['sources'] * 10001
        with self.assertRaises(ValueError):
            call('validate_source_selection', bad)
        for changes in ({'attribution_map': []}, {'attribution_map': [{}]},
                        {'owner_scope': {}}, {'sources': []}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                call('validate_source_selection', value | changes)
        bad = copy.deepcopy(value)
        bad['attribution_map'][0]['source_id'] = 'sha256:' + '4' * 64
        with self.assertRaises(ValueError):
            call('validate_source_selection', bad)

    def test_json_duplicate_keys_and_input_and_canonical_byte_bounds(self):
        value = selection()
        data = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'SELECTION_LIMIT', size, create=True):
            self.assert_valid(value)
        with patch.object(contract, 'SELECTION_LIMIT', size - 1, create=True):
            with self.assertRaises(ValueError):
                call('validate_source_selection', value)
        with patch.object(contract, 'SELECTION_LIMIT', len(data), create=True):
            self.assertEqual(call('validate_source_selection_json', data), value)
            with self.assertRaises(ValueError):
                call('validate_source_selection_json', data + b' ')
        with self.assertRaises(ValueError):
            call('validate_source_selection_json', b'{"schema_version":1,"schema_version":1}')

    def test_validation_never_reads_selected_path(self):
        value = selection()
        with patch('builtins.open', side_effect=AssertionError('source must not be read')):
            self.assert_valid(value)


if __name__ == '__main__':
    unittest.main()
