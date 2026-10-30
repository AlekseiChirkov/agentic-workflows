#!/usr/bin/env python3
"""Offline checks for bounded, private source normalization."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

contract = load('contract', ROOT / 'scripts/usage_telemetry_contract.py')
fixtures = load('source_fixtures', ROOT / 'tests/usage-bounded-source-reads.py')
profiles = load('profile_fixtures', ROOT / 'tests/usage-source-profiles.py')
adapter_path = ROOT / 'scripts/usage_telemetry_adapter.py'
adapter = load('usage_telemetry_adapter', adapter_path) if adapter_path.exists() else None
KEY = b'private-mapping-key-that-is-long-enough-for-tests'
PROJECT = 'private-project'
PROVIDER = 'private-provider-account'
RUN = 'run-1'


def normalize(selection, profile=None, key=KEY):
    if adapter is None:
        return None
    return adapter.normalize_selection(selection, profile=profiles.profile() if profile is None else profile,
        expected_owner_scope=fixtures.OWNER, project_identifier=PROJECT,
        provider_identifier=PROVIDER, run_id=RUN, key=key)


class SourceNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.path = self.directory / 'private-selected-export.jsonl'
        self.raw = {'usage': {'input': 1000, 'read': 200, 'write': 150,
                    'short': 100, 'long': 50, 'output': 500, 'reasoning': 100},
                    'complete': True, 'secret': 'PRIVATE_PAYLOAD_SENTINEL'}
        self.write([self.raw])

    def write(self, records):
        content = b''.join((json.dumps(value, ensure_ascii=False) + '\n').encode('utf-8') for value in records)
        self.path.write_bytes(content)
        self.selection = fixtures.manifest(self.path, content)
        return content

    def test_valid_selected_source_produces_private_bounded_bundle_with_evidence(self):
        result = normalize(self.selection)
        self.assertIsInstance(result, dict)
        self.assertFalse(result['partial'])
        self.assertEqual(result['quarantine'], [])
        bundle = result['bundle']
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        self.assertEqual(len(bundle['observations']), 1)
        observation = bundle['observations'][0]
        self.assertEqual(observation['observed_at'], self.selection['observed_at'])
        self.assertEqual(observation['source_hash'], self.selection['sources'][0]['sha256'])
        self.assertEqual(observation['record_number'], 1)
        self.assertEqual(observation['measurements']['tokens_in']['value'], 1000)
        self.assertEqual(observation['measurements']['output_total']['value'], 500)
        self.assertTrue(bundle['evidence_objects'])
        exposed = json.dumps(result, sort_keys=True)
        for secret in (PROJECT, PROVIDER, str(self.path), str(self.directory),
                       'PRIVATE_PAYLOAD_SENTINEL', KEY.decode()):
            self.assertNotIn(secret, exposed)

    def test_duplicate_selected_sources_preserve_distinct_records_and_contexts(self):
        resolution = load('producer_resolution_fixture', ROOT / 'tests/usage-producer-resolution.py')
        record = copy.deepcopy(self.raw)
        record['metadata'] = {'response': 'response-1', 'call': 'call-1', 'session': 'session-1',
                              'time': '2026-01-01T00:00:00Z', 'complete': True,
                              'model': 'vendor/model', 'service_tier': 'standard',
                              'region': 'example-region', 'modality': 'text'}
        first = self.write([record])
        duplicate = self.directory / 'duplicate.jsonl'
        duplicate.write_bytes(first)
        distinct = self.directory / 'distinct.jsonl'
        second_record = copy.deepcopy(record)
        second_record['metadata']['response'] = 'response-2'
        second_record['metadata']['call'] = 'call-2'
        second_record['usage']['output'] = 501
        second = (json.dumps(second_record) + '\n' + json.dumps({'usage': {'input': -1}}) + '\n').encode()
        distinct.write_bytes(second)
        for index, path, content in ((3, duplicate, first), (4, distinct, second)):
            source_id = 'sha256:' + str(index) * 64
            self.selection['sources'].append({'source_id': source_id, 'local_path': str(path),
                'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content)})
            self.selection['attribution_map'].append({'source_id': source_id, 'owner_kind': 'unattributed',
                                                       'quality': 'unknown', 'candidates': []})
        self.selection['max_source_bytes'] = max(len(first), len(second))
        self.selection['max_total_bytes'] = 2 * len(first) + len(second)
        contract.validate_source_selection(self.selection)
        result = adapter.normalize_selection(self.selection, profile=resolution.profile(),
            expected_owner_scope=fixtures.OWNER, project_identifier=PROJECT, provider_identifier=PROVIDER,
            run_id=RUN, key=KEY, verify_resolution=lambda *_: True)
        bundle = result['bundle']
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        self.assertEqual(len(bundle['sources']), 3)
        self.assertEqual(len(bundle['observations']), 2)
        self.assertEqual(sorted(item['measurements']['output_total']['value'] for item in bundle['observations']),
                         [500, 501])
        self.assertEqual(len(result['contexts']), 2)
        self.assertEqual({item['observation_id'] for item in result['contexts']},
                         {contract.observation_id(item) for item in bundle['observations']})
        wrappers = [item['context'] for item in bundle['evidence_objects']
                    if item['kind'] == 'resolution_context_evidence']
        self.assertEqual(wrappers, result['contexts'])
        self.assertTrue(result['partial'])
        self.assertEqual(len(result['quarantine']), 1)
        self.assertEqual(result['quarantine'][0]['record_number'], 2)
        self.assertEqual(len(bundle['diagnostics']), 1)
        self.assertEqual(bundle['diagnostics'][0]['source_id'], bundle['sources'][2]['source_id'])

    def test_keyed_ids_are_deterministic_domain_separated_and_keyed(self):
        first = normalize(self.selection)
        self.assertIsInstance(first, dict)
        self.assertEqual(first, normalize(self.selection))
        second = normalize(self.selection, key=b'another-private-test-key-which-is-long')
        self.assertNotEqual(first['bundle']['project_id'], second['bundle']['project_id'])
        self.assertNotEqual(first['bundle']['sources'][0]['source_id'], second['bundle']['sources'][0]['source_id'])
        self.assertNotEqual(first['bundle']['observations'][0]['provider_scope'],
                            second['bundle']['observations'][0]['provider_scope'])
        same_identifier = patch.object(sys.modules[__name__], 'PROVIDER', PROJECT)
        with same_identifier:
            shared = normalize(self.selection)['bundle']
        self.assertNotEqual(shared['project_id'], shared['observations'][0]['provider_scope'])

    def test_only_explicit_sources_are_opened_and_network_is_unused(self):
        neighbor = self.directory / 'PRIVATE_NEIGHBOR'
        neighbor.write_text('PRIVATE_NEIGHBOR_CONTENT', encoding='utf-8')
        actual = __import__('usage_telemetry_sources')._open_regular
        opened = []
        def tracked(path):
            opened.append(path)
            return actual(path)
        with patch('socket.socket', side_effect=AssertionError('unexpected network')), \
             patch('usage_telemetry_sources._open_regular', side_effect=tracked):
            result = normalize(self.selection)
        self.assertIsInstance(result, dict)
        self.assertEqual(opened, [str(self.path)])
        self.assertNotIn('PRIVATE_NEIGHBOR', json.dumps(result))

    def test_invalid_record_is_quarantined_without_payload_and_valid_siblings_are_partial(self):
        invalid = {'usage': {'input': -1}, 'private': 'PRIVATE_BAD_RECORD'}
        self.write([self.raw, invalid, self.raw | {'usage': self.raw['usage'] | {'output': 501}}])
        result = normalize(self.selection)
        self.assertIsInstance(result, dict)
        self.assertTrue(result['partial'])
        self.assertEqual([item['record_number'] for item in result['bundle']['observations']], [1, 3])
        self.assertEqual(len(result['quarantine']), 1)
        self.assertEqual(result['quarantine'][0]['record_number'], 2)
        self.assertEqual(result['quarantine'][0]['reason'], 'source_record_quarantined')
        self.assertNotIn('PRIVATE_BAD_RECORD', json.dumps(result))
        self.assertEqual(contract.validate_usage_bundle(result['bundle']), result['bundle'])
        self.assertTrue(all(item['state'] == 'partial' for item in result['bundle']['observations']))

    def test_malformed_record_does_not_discard_valid_siblings(self):
        content = (json.dumps(self.raw) + '\n' + '{PRIVATE_BAD_JSON\n' + json.dumps(self.raw) + '\n').encode()
        self.path.write_bytes(content)
        self.selection = fixtures.manifest(self.path, content)
        result = normalize(self.selection)
        self.assertIsInstance(result, dict)
        self.assertTrue(result['partial'])
        self.assertEqual([item['record_number'] for item in result['bundle']['observations']], [1, 3])
        self.assertEqual(result['quarantine'][0]['record_number'], 2)
        self.assertNotIn('PRIVATE_BAD_JSON', json.dumps(result))

    def test_quarantine_diagnostics_survive_bundle_extraction_and_preserve_source_scope(self):
        self.write([self.raw, {'usage': {'input': -1}, 'private': 'PRIVATE_BAD_RECORD'}])
        bundle = normalize(self.selection)['bundle']
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        self.assertEqual(len(bundle['diagnostics']), 1)
        diagnostic = bundle['diagnostics'][0]
        self.assertEqual(diagnostic['kind'], 'source_issue')
        self.assertEqual(diagnostic['source_id'], bundle['sources'][0]['source_id'])
        self.assertEqual(diagnostic['source_hash'], bundle['sources'][0]['sha256'])
        self.assertEqual(diagnostic['record_number'], 2)
        self.assertEqual(diagnostic['reason'], 'source_record_quarantined')
        self.assertEqual(diagnostic['completeness'], 'partial')
        self.assertNotIn('PRIVATE_BAD_RECORD', json.dumps(bundle))
        self.assertNotIn(str(self.path), json.dumps(bundle))

    def test_prefix_diagnostic_survives_bundle_extraction(self):
        content = self.path.read_bytes()
        self.path.write_bytes(content + b'PRIVATE_SUFFIX')
        self.selection['sources'][0]['verified_prefix_bytes'] = len(content)
        self.selection['sources'][0]['size_bytes'] = self.path.stat().st_size
        bundle = normalize(self.selection)['bundle']
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        self.assertEqual(len(bundle['diagnostics']), 1)
        diagnostic = bundle['diagnostics'][0]
        self.assertEqual(diagnostic['kind'], 'source_issue')
        self.assertEqual(diagnostic['source_id'], bundle['sources'][0]['source_id'])
        self.assertEqual(diagnostic['source_hash'], bundle['sources'][0]['sha256'])
        self.assertIsNone(diagnostic['record_number'])
        self.assertEqual(diagnostic['reason'], 'incomplete_source')
        self.assertEqual(diagnostic['completeness'], 'partial')
        self.assertNotIn('PRIVATE_SUFFIX', json.dumps(bundle))

    def test_record_byte_limit_accepts_boundary_and_quarantines_larger_record(self):
        prefix = b'{"usage":{"output":2},"unknown":"'
        suffix = b'"}'
        limit = 256
        boundary = prefix + b'a' * (limit - len(prefix) - len(suffix)) + suffix
        too_large = prefix + b'b' * (limit + 1 - len(prefix) - len(suffix)) + suffix
        content = boundary + b'\n' + too_large + b'\n'
        self.path.write_bytes(content)
        self.selection = fixtures.manifest(self.path, content)
        with patch('usage_telemetry_sources.RECORD_LIMIT', limit):
            result = normalize(self.selection)
        bundle = result['bundle']
        self.assertEqual([item['record_number'] for item in bundle['observations']], [1])
        self.assertTrue(result['partial'])
        self.assertEqual(result['quarantine'][0]['reason'], 'input_limit_exceeded')
        diagnostic = bundle['diagnostics'][0]
        self.assertEqual(diagnostic['record_number'], 2)
        self.assertEqual(diagnostic['reason'], 'input_limit_exceeded')
        self.assertEqual(diagnostic['completeness'], 'partial')
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        self.assertNotIn('bbbbbbbb', json.dumps(bundle))

    def test_record_tree_limits_report_input_limit_without_leaking_payload(self):
        nested = {'private': 'PRIVATE_NESTED_SENTINEL'}
        for _ in range(34):
            nested = {'child': nested}
        excessive_keys = {f'key_{number}': number for number in range(257)}
        excessive_keys['secret'] = 'PRIVATE_KEYS_SENTINEL'
        for invalid, secret in ((nested, 'PRIVATE_NESTED_SENTINEL'),
                                (excessive_keys, 'PRIVATE_KEYS_SENTINEL')):
            with self.subTest(secret=secret):
                self.write([self.raw, invalid])
                result = normalize(self.selection)
                bundle = result['bundle']
                self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
                self.assertEqual([item['record_number'] for item in bundle['observations']], [1])
                self.assertEqual(result['quarantine'][0]['reason'], 'input_limit_exceeded')
                issue = bundle['diagnostics'][0]
                self.assertEqual(issue['reason'], 'input_limit_exceeded')
                self.assertEqual(issue['record_number'], 2)
                self.assertEqual(issue['completeness'], 'partial')
                self.assertNotIn(secret, json.dumps(result))

    def test_invalid_selection_profile_and_changed_file_reject_atomically_without_private_errors(self):
        if adapter is None:
            self.fail('source normalizer is unavailable')
        bad_selection = copy.deepcopy(self.selection)
        del bad_selection['max_total_bytes']
        bad_profile = profiles.profile()
        bad_profile['profile_version'] = 'wrong'
        for selection, profile in ((bad_selection, profiles.profile()), (self.selection, bad_profile)):
            with self.subTest(selection=selection, profile=profile), \
                 patch('usage_telemetry_sources._open_regular', side_effect=AssertionError('source opened')):
                with self.assertRaises(ValueError) as error:
                    normalize(selection, profile=profile)
                self.assertNotIn(str(self.path), str(error.exception))
        self.path.write_bytes(b'CHANGED_PRIVATE_SOURCE')
        with self.assertRaises(ValueError) as error:
            normalize(self.selection)
        self.assertNotIn('CHANGED_PRIVATE_SOURCE', str(error.exception))
        self.assertNotIn(str(self.path), str(error.exception))

    def test_prefix_and_absent_measurements_never_claim_complete(self):
        raw = {'usage': {'output': 500}, 'complete': True}
        self.write([raw])
        content = self.path.read_bytes()
        self.path.write_bytes(content + b'private unselected suffix')
        self.selection['sources'][0]['verified_prefix_bytes'] = len(content)
        self.selection['sources'][0]['size_bytes'] = self.path.stat().st_size
        result = normalize(self.selection)
        self.assertIsInstance(result, dict)
        self.assertTrue(result['partial'])
        observation = result['bundle']['observations'][0]
        self.assertEqual(observation['state'], 'partial')
        self.assertNotIn('value', observation['measurements']['tokens_in'])
        self.assertEqual(observation['measurements']['output_total']['value'], 500)
        self.assertNotIn('private unselected suffix', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
