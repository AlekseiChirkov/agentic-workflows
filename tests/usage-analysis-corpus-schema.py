#!/usr/bin/env python3
"""Offline contract tests for explicitly selected analysis inputs."""
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


def corpus():
    return {
        'schema_version': 1, 'kind': 'analysis_corpus',
        'as_of': '2026-01-02T03:04:05Z',
        'scope': {'owner_kind': 'run', 'owner_id': 'sha256:' + '1' * 64},
        'scenario_id': 'synthetic-scenario',
        'versions': {'bundle_schema_version': 1, 'receipt_schema_version': 1,
                     'price_schema_version': 1, 'normalizer_version': '1'},
        'identifier_mappings': [{'from_id': 'sha256:' + '5' * 64,
                                 'to_id': None, 'quality': 'unknown'}],
        'inputs': [
            {'kind': 'usage_bundle', 'schema_version': 1, 'local_path': '/local/selected-bundle.json',
             'sha256': '2' * 64, 'size_bytes': 80},
            {'kind': 'acceptance_revision', 'schema_version': 1, 'local_path': '/local/selected-receipt.json',
             'sha256': '3' * 64, 'size_bytes': 20},
        ],
        'exclusions': [{'input_sha256': '4' * 64, 'reason': 'unknown'}],
        'max_source_bytes': 80, 'max_total_bytes': 100, 'max_records': 10,
    }


class AnalysisCorpusSchemaTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_analysis_corpus', value), value)

    def test_complete_manifest_preserves_inputs_and_explicit_unknowns(self):
        value = corpus()
        self.assert_valid(value)
        self.assertEqual(value['exclusions'][0]['reason'], 'unknown')
        self.assertIsNone(value['identifier_mappings'][0]['to_id'])
        mapped = copy.deepcopy(value)
        mapped['identifier_mappings'][0].update(to_id='sha256:' + '6' * 64, quality='verified')
        self.assert_valid(mapped)
        mapped['identifier_mappings'] = []
        self.assert_valid(mapped)
        for kind in ('lifecycle_event', 'usage_bundle', 'inventory', 'price_snapshot',
                     'acceptance_revision'):
            item = copy.deepcopy(value)
            item['inputs'][0]['kind'] = kind
            self.assert_valid(item)
        item = copy.deepcopy(value)
        item['inputs'][0]['verified_prefix_bytes'] = 50
        self.assert_valid(item)

    def test_required_fields_versions_scope_and_closed_shape(self):
        value = corpus()
        self.assert_valid(value)
        for field in value:
            with self.subTest(missing=field), self.assertRaises(ValueError):
                call('validate_analysis_corpus', {k: v for k, v in value.items() if k != field})
        for change in ({'schema_version': 2}, {'schema_version': True}, {'kind': 'other'},
                       {'as_of': '2026-01-02'}, {'scope': {}}, {'scope': {'owner_kind': 'other',
                                                                          'owner_id': 'x'}},
                       {'scenario_id': '/private/path'}, {'versions': {}}, {'inputs': []}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_analysis_corpus', value | change)
        for field in value['versions']:
            bad = copy.deepcopy(value)
            del bad['versions'][field]
            with self.subTest(version=field), self.assertRaises(ValueError):
                call('validate_analysis_corpus', bad)
            bad = copy.deepcopy(value)
            bad['versions'][field] = '' if field == 'normalizer_version' else 2
            with self.subTest(version=field), self.assertRaises(ValueError):
                call('validate_analysis_corpus', bad)

    def test_entries_require_explicit_hash_type_path_and_size(self):
        value = corpus()
        self.assert_valid(value)
        for field in value['inputs'][0]:
            bad = copy.deepcopy(value)
            del bad['inputs'][0][field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                call('validate_analysis_corpus', bad)
        for field, bad_value in [('sha256', 'a' * 63), ('sha256', 'A' * 64),
                                 ('kind', 'directory'), ('schema_version', 2), ('local_path', ''),
                                 ('local_path', '/local/*.json'), ('size_bytes', -1),
                                 ('size_bytes', True), ('verified_prefix_bytes', 81)]:
            bad = copy.deepcopy(value)
            bad['inputs'][0][field] = bad_value
            with self.subTest(field=field, value=bad_value), self.assertRaises(ValueError):
                call('validate_analysis_corpus', bad)
        bad = copy.deepcopy(value)
        bad['inputs'].append(copy.deepcopy(bad['inputs'][0]))
        with self.assertRaises(ValueError):
            call('validate_analysis_corpus', bad)

    def test_explicit_limits_cover_selected_bytes_and_entry_count(self):
        value = corpus()
        self.assert_valid(value)
        for field, bad_value in [('max_source_bytes', 79), ('max_total_bytes', 99),
                                 ('max_records', 0), ('max_records', True),
                                 ('max_source_bytes', -1), ('max_total_bytes', '100')]:
            with self.subTest(field=field, value=bad_value), self.assertRaises(ValueError):
                call('validate_analysis_corpus', value | {field: bad_value})
        prefix = copy.deepcopy(value)
        prefix['inputs'][0]['verified_prefix_bytes'] = 50
        prefix['max_source_bytes'], prefix['max_total_bytes'] = 50, 70
        self.assert_valid(prefix)
        bad = copy.deepcopy(value)
        bad['inputs'] *= 5001
        with self.assertRaises(ValueError):
            call('validate_analysis_corpus', bad)
        bad = copy.deepcopy(value)
        bad['exclusions'] *= 10001
        with self.assertRaises(ValueError):
            call('validate_analysis_corpus', bad)

    def test_exclusions_are_explicit_and_private_content_is_not_echoed(self):
        value = corpus()
        self.assert_valid(value)
        for change in ({'input_sha256': '/private/path'}, {'reason': '/secret'},
                       {'reason': ''}, {'raw': 'PRIVATE_CONTENT_SENTINEL'}):
            bad = copy.deepcopy(value)
            bad['exclusions'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError) as error:
                call('validate_analysis_corpus', bad)
            self.assertNotIn('PRIVATE_CONTENT_SENTINEL', str(error.exception))
        with self.assertRaises(ValueError) as error:
            call('validate_analysis_corpus', value | {'raw_content': 'PRIVATE_CONTENT_SENTINEL'})
        self.assertNotIn('PRIVATE_CONTENT_SENTINEL', str(error.exception))

    def test_identifier_mappings_require_explicit_bounded_and_safe_values(self):
        value = corpus()
        self.assert_valid(value)
        for field in value['identifier_mappings'][0]:
            bad = copy.deepcopy(value)
            del bad['identifier_mappings'][0][field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                call('validate_analysis_corpus', bad)
        for change in ({'from_id': '/private/path'}, {'to_id': '/private/path'},
                       {'quality': 'bogus'}, {'quality': 'verified'},
                       {'raw': 'PRIVATE_CONTENT_SENTINEL'}):
            bad = copy.deepcopy(value)
            bad['identifier_mappings'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError) as error:
                call('validate_analysis_corpus', bad)
            self.assertNotIn('PRIVATE_CONTENT_SENTINEL', str(error.exception))
        bad = copy.deepcopy(value)
        bad['identifier_mappings'] *= 10001
        with self.assertRaises(ValueError):
            call('validate_analysis_corpus', bad)

    def test_json_duplicate_keys_and_raw_and_canonical_byte_limits(self):
        value = corpus()
        self.assert_valid(value)
        data = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'ANALYSIS_CORPUS_LIMIT', size, create=True):
            self.assert_valid(value)
        with patch.object(contract, 'ANALYSIS_CORPUS_LIMIT', size - 1, create=True):
            with self.assertRaises(ValueError):
                call('validate_analysis_corpus', value)
        with patch.object(contract, 'ANALYSIS_CORPUS_LIMIT', len(data), create=True):
            self.assertEqual(call('validate_analysis_corpus_json', data), value)
            with self.assertRaises(ValueError):
                call('validate_analysis_corpus_json', data + b' ')
        with self.assertRaises(ValueError):
            call('validate_analysis_corpus_json', b'{"schema_version":1,"schema_version":1}')

    def test_manifest_validation_never_reads_or_discovers_history(self):
        with patch('builtins.open', side_effect=AssertionError('input must not be read')):
            self.assert_valid(corpus())


if __name__ == '__main__':
    unittest.main()
