#!/usr/bin/env python3
"""Offline checks for fixed, explicitly selected retrospective evidence."""
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
import usage_telemetry_contract as contract

MODULE = ROOT / 'scripts/usage_telemetry_corpus.py'
if MODULE.exists():
    spec = importlib.util.spec_from_file_location('corpus', MODULE)
    corpus = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(corpus)
else:
    corpus = None

SCOPE = {'owner_kind': 'run', 'owner_id': 'sha256:' + '1' * 64}
AS_OF = '2026-01-02T03:04:05Z'


def bundle(observed=AS_OF, number=1):
    evidence = {'schema_version': 1, 'kind': 'measurement_evidence',
                'profile_id': 'profile', 'source_hash': 'a' * 64,
                'record_number': number, 'field': 'input_uncached', 'value': 0}
    digest = hashlib.sha256(contract.canonical_bytes(evidence)).hexdigest()
    observation = {'schema_version': 1, 'kind': 'request_usage', 'profile_id': 'profile',
                   'profile_version': '1', 'source_hash': 'a' * 64, 'record_number': number,
                   'counter_scope': 'response_total', 'provider_scope': 'sha256:' + 'c' * 64,
                   'source_time': '2026-01-01T00:00:00Z', 'source_time_quality': 'verified',
                   'observed_at': observed, 'state': 'partial', 'outcome': 'unknown',
                   'attribution': {'owner_kind': 'unattributed', 'quality': 'asserted',
                                   'candidates': []},
                   'measurements': {'input_uncached': {'measurement_state': 'final',
                                                      'value': 0, 'reasons': [],
                                                      'evidence': digest}}}
    return {'schema_version': 1, 'kind': 'usage_bundle', 'profile_id': 'profile',
            'profile_version': '1', 'project_id': 'sha256:' + 'd' * 64, 'run_id': 'run',
            'sources': [{'source_id': 'sha256:' + 'e' * 64, 'sha256': 'a' * 64}],
            'observations': [observation], 'evidence_objects': [evidence],
            'inventories': [], 'segments': [], 'diagnostics': []}


class FixedCorpusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.manifest = {'schema_version': 1, 'kind': 'analysis_corpus', 'as_of': AS_OF,
                         'scope': copy.deepcopy(SCOPE), 'scenario_id': 'scenario',
                         'versions': {'bundle_schema_version': 1, 'receipt_schema_version': 1,
                                      'price_schema_version': 1, 'normalizer_version': '1'},
                         'identifier_mappings': [], 'inputs': [], 'exclusions': [],
                         'max_source_bytes': 100000, 'max_total_bytes': 200000, 'max_records': 10}
        self.add_bundle('selected.json', bundle())

    def add_bundle(self, name, value):
        data = contract.canonical_bytes(value)
        path = self.directory / name
        path.write_bytes(data)
        self.manifest['inputs'].append({'kind': 'usage_bundle', 'schema_version': 1,
                                        'local_path': str(path),
                                        'sha256': hashlib.sha256(data).hexdigest(),
                                        'size_bytes': len(data)})
        return path

    @staticmethod
    def verify(item, value, scope):
        # This callback represents an independent local authority, not input claims.
        return {'scope': copy.deepcopy(scope), 'observed_at': '2026-01-01T00:00:00Z'}

    def freeze(self, manifest=None, verifier=None):
        if corpus is None:
            return None
        return corpus.freeze_corpus(copy.deepcopy(manifest or self.manifest),
                                    verify_input=verifier or self.verify)

    def test_fixed_corpus_contains_only_selected_hash_verified_data(self):
        self.add_bundle('unselected.json', bundle(number=3))
        unselected = self.manifest['inputs'].pop()
        with patch('os.listdir', side_effect=AssertionError('implicit discovery')), \
             patch('os.scandir', side_effect=AssertionError('implicit discovery')), \
             patch('socket.socket', side_effect=AssertionError('network access')):
            result = self.freeze()
        self.assertIsInstance(result, dict)
        self.assertEqual(result['manifest'], self.manifest)
        self.assertEqual(len(result['inputs']), 1)
        self.assertEqual(result['inputs'][0]['sha256'], self.manifest['inputs'][0]['sha256'])
        self.assertNotIn(unselected['sha256'], json.dumps(result))
        self.assertNotIn(str(self.directory / 'unselected.json'), json.dumps(result))
        self.assertEqual(len(result['corpus_id']), 64)

    def test_selected_byte_tampering_and_invalid_json_fail_closed(self):
        path = Path(self.manifest['inputs'][0]['local_path'])
        path.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.freeze()
        data = b'{invalid json}'
        path.write_bytes(data)
        self.manifest['inputs'][0].update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        with self.assertRaises(ValueError):
            self.freeze()

    def test_verification_is_required_and_scope_is_not_a_boolean_claim(self):
        for bad in (None, True, False, {}, {'scope': SCOPE},
                    {'scope': {'owner_kind': 'run', 'owner_id': 'sha256:' + '2' * 64},
                     'observed_at': AS_OF}):
            with self.subTest(verifier_result=bad), self.assertRaises(ValueError):
                self.freeze(verifier=lambda *_: bad)
        with self.assertRaises((ValueError, TypeError)):
            corpus.freeze_corpus(copy.deepcopy(self.manifest), verify_input=None)

    def test_late_observation_is_excluded_by_availability_not_source_time(self):
        late = bundle('2026-01-02T03:04:06Z', number=2)
        self.add_bundle('late.json', late)
        result = self.freeze()
        self.assertEqual(len(result['inputs']), 2)
        observations = [observation for item in result['inputs']
                        for observation in item['value']['observations']]
        self.assertEqual([observation['record_number'] for observation in observations], [1])
        self.assertIn(self.manifest['inputs'][1]['sha256'], json.dumps(result['exclusions']))

    def test_late_verified_input_is_excluded_even_with_early_source_time(self):
        def late_verifier(item, value, scope):
            return {'scope': scope, 'observed_at': '2026-01-02T03:04:06Z'}
        result = self.freeze(verifier=late_verifier)
        self.assertEqual(result['inputs'], [])
        self.assertIn(self.manifest['inputs'][0]['sha256'], json.dumps(result['exclusions']))

    def test_previous_corpus_is_reproducible_after_explicit_late_selection(self):
        old = self.freeze()
        self.add_bundle('late.json', bundle('2026-01-02T03:04:06Z', number=2))
        old_manifest = copy.deepcopy(self.manifest)
        old_manifest['inputs'].pop()
        self.assertEqual(self.freeze(old_manifest), old)
        self.assertNotEqual(self.freeze()['corpus_id'], old['corpus_id'])

    def test_selection_order_is_semantically_stable_and_scenario_is_frozen(self):
        self.add_bundle('second.json', bundle(number=2))
        first = self.freeze()
        reversed_manifest = copy.deepcopy(self.manifest)
        reversed_manifest['inputs'].reverse()
        second = self.freeze(reversed_manifest)
        self.assertEqual(first['corpus_id'], second['corpus_id'])
        self.assertEqual(first['inputs'], second['inputs'])
        changed = copy.deepcopy(self.manifest)
        changed['scenario_id'] = 'other-scenario'
        self.assertNotEqual(first['corpus_id'], self.freeze(changed)['corpus_id'])

    def test_size_record_and_permission_failures_never_emit_a_corpus(self):
        for change in ({'max_source_bytes': 1}, {'max_total_bytes': 1}, {'max_records': 0}):
            manifest = self.manifest | change
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.freeze(manifest)
        path = Path(self.manifest['inputs'][0]['local_path'])
        path.unlink()
        with self.assertRaises(ValueError):
            self.freeze()

    def test_invalid_container_and_scope_are_rejected(self):
        path = Path(self.manifest['inputs'][0]['local_path'])
        data = b'[]'
        path.write_bytes(data)
        self.manifest['inputs'][0].update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        with self.assertRaises(ValueError):
            self.freeze()


    def test_verified_decision_changes_are_bound_to_corpus_identity(self):
        early = self.freeze()
        def late_verifier(item, value, scope):
            return {'scope': scope, 'observed_at': '2026-01-02T03:04:06Z'}
        late = self.freeze(verifier=late_verifier)
        self.assertEqual(len(early['inputs']), 1)
        self.assertEqual(late['inputs'], [])
        self.assertNotEqual(early['corpus_id'], late['corpus_id'])
        self.assertEqual(early, self.freeze())
        self.assertEqual(late, self.freeze(verifier=late_verifier))

    def test_declared_exclusion_is_never_included(self):
        self.assertEqual(len(self.freeze()['inputs']), 1)
        manifest = copy.deepcopy(self.manifest)
        digest = manifest['inputs'][0]['sha256']
        manifest['exclusions'].append({'input_sha256': digest, 'reason': 'unknown'})
        try:
            result = self.freeze(manifest)
        except ValueError:
            return  # Rejecting contradictory declarations is also safe.
        self.assertEqual(result['inputs'], [])
        self.assertIn(digest, json.dumps(result['exclusions']))

    def test_late_observation_does_not_leave_associated_evidence(self):
        original = self.freeze()['inputs'][0]['value']
        self.assertEqual(len(original['evidence_objects']), 1)
        self.add_bundle('late.json', bundle('2026-01-02T03:04:06Z', number=2))
        late_digest = self.manifest['inputs'][1]['sha256']
        result = self.freeze()
        late_value = next(item['value'] for item in result['inputs'] if item['sha256'] == late_digest)
        self.assertEqual(late_value['observations'], [])
        self.assertEqual(late_value['evidence_objects'], [])

    def test_undated_nested_members_need_independent_first_seen_times(self):
        value = bundle()
        segment = {'schema_version': 1, 'kind': 'collection_segment',
                   'segment_id': 'sha256:' + 'a' * 64, 'owner_scope': SCOPE,
                   'mode': 'on', 'start': '2026-01-02T03:00:00Z',
                   'end': '2026-01-02T04:00:00Z',
                   'gap_before': {'state': 'unknown', 'start': None, 'end': None}}
        diagnostic = {'schema_version': 1, 'kind': 'diagnostic_measurement',
                      'metric': 'context.loaded_bytes', 'value': 42, 'unit': 'bytes',
                      'scope': SCOPE, 'source_id': 'sha256:' + 'b' * 64, 'quality': 'measured'}
        value['segments'] = [segment]
        value['diagnostics'] = [diagnostic]
        contract.validate_usage_bundle(value)
        self.manifest['inputs'] = []
        self.add_bundle('with-members.json', value)
        # A verifier that only asserts the outer file's time has not proved the
        # availability of members that carry no independent observation time.
        try:
            result = self.freeze()
        except ValueError:
            pass
        else:
            included = result['inputs'][0]['value']
            self.assertEqual(included['segments'], [])
            self.assertEqual(included['diagnostics'], [])
        member_times = {contract.content_id(segment): '2026-01-01T00:00:00Z',
                        contract.content_id(diagnostic): '2026-01-02T03:04:06Z'}
        def verifier(item, decoded, scope):
            return {'scope': scope, 'observed_at': '2026-01-01T00:00:00Z',
                    'member_times': member_times}
        result = self.freeze(verifier=verifier)
        included = result['inputs'][0]['value']
        self.assertEqual(included['segments'], [segment])
        self.assertEqual(included['diagnostics'], [])


    def test_split_cache_measurement_retains_and_revalidates_evidence(self):
        fixture_spec = importlib.util.spec_from_file_location(
            'source_profiles_fixture', ROOT / 'tests/usage-source-profiles.py')
        fixture = importlib.util.module_from_spec(fixture_spec)
        fixture_spec.loader.exec_module(fixture)
        source = fixture.split_bundle()
        self.assertEqual(contract.validate_usage_bundle(source), source)
        self.manifest['inputs'] = []
        self.add_bundle('split.json', source)
        retained = self.freeze()['inputs'][0]['value']
        self.assertEqual(contract.validate_usage_bundle(retained), retained)
        self.assertEqual({contract.content_id(item) for item in retained['evidence_objects']},
                         {contract.content_id(item) for item in source['evidence_objects']})

    def test_derived_measurement_retains_transitive_operands(self):
        fixture_spec = importlib.util.spec_from_file_location(
            'source_profiles_fixture', ROOT / 'tests/usage-source-profiles.py')
        fixture = importlib.util.module_from_spec(fixture_spec)
        fixture_spec.loader.exec_module(fixture)
        selected = fixture.profile()
        normalized = fixture.normalize(selected, {'input': 1000, 'read': 200, 'write': 150,
                                                   'short': 100, 'long': 50})
        source = fixture.split_bundle()
        source['observations'][0]['measurements'] = {
            'input_uncached': normalized['measurements']['input_uncached']}
        source['evidence_objects'] = normalized['evidence_objects']
        self.assertEqual(contract.validate_usage_bundle(source), source)
        self.manifest['inputs'] = []
        self.add_bundle('derived.json', source)
        self.manifest['max_records'] = 100
        retained = self.freeze()['inputs'][0]['value']
        self.assertEqual(contract.validate_usage_bundle(retained), retained)
        measurement = retained['observations'][0]['measurements']['input_uncached']
        objects = {contract.content_id(item): item for item in retained['evidence_objects']}
        proof = objects[measurement['evidence']]
        self.assertTrue(all(operand in objects for operand in proof['operands']))
        self.assertTrue(contract.verify_derived_measurement_evidence(
            measurement, proof, retained['evidence_objects'], selected))


if __name__ == '__main__':
    unittest.main()
