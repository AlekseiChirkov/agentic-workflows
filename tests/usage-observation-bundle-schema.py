#!/usr/bin/env python3
"""Offline checks for bounded sanitized usage envelopes."""
import copy
import hashlib
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


def evidence():
    return {'schema_version': 1, 'kind': 'measurement_evidence', 'profile_id': 'profile',
            'source_hash': 'a' * 64, 'record_number': 1, 'field': 'input_uncached', 'value': 0}


def observation():
    digest = hashlib.sha256(contract.canonical_bytes(evidence())).hexdigest()
    return {'schema_version': 1, 'kind': 'request_usage', 'profile_id': 'profile',
            'profile_version': '1', 'source_hash': 'a' * 64, 'record_number': 1,
            'counter_scope': 'response_total', 'provider_scope': 'sha256:' + 'c' * 64,
            'source_time': None, 'source_time_quality': 'unknown',
            'observed_at': '2026-01-02T03:04:05Z', 'state': 'partial',
            'outcome': 'unknown', 'attribution': {'owner_kind': 'unattributed',
                                                   'quality': 'asserted', 'candidates': []},
            'measurements': {'input_uncached': {'measurement_state': 'final', 'value': 0,
                                                'reasons': [], 'evidence': digest}}}


def bundle():
    return {'schema_version': 1, 'kind': 'usage_bundle', 'profile_id': 'profile',
            'profile_version': '1', 'project_id': 'sha256:' + 'd' * 64, 'run_id': 'run',
            'sources': [{'source_id': 'sha256:' + 'e' * 64, 'sha256': 'a' * 64}],
            'observations': [observation()], 'evidence_objects': [evidence()],
            'inventories': [], 'segments': [], 'diagnostics': []}


class EnvelopeTests(unittest.TestCase):
    def test_observation_and_bundle_accept_and_preserve_identities(self):
        for name, fixture in [('validate_observation', observation()), ('validate_usage_bundle', bundle())]:
            with self.subTest(name=name):
                reversed_keys = dict(reversed(list(fixture.items())))
                self.assertEqual(call(name, fixture), fixture)
                self.assertEqual(call(name, reversed_keys), reversed_keys)
                identify = contract.observation_id if name == 'validate_observation' else contract.content_id
                self.assertEqual(identify(fixture), identify(reversed_keys))

    def test_invalid_versions_and_raw_fields_are_rejected_without_leakage(self):
        private = 'PRIVATE_SOURCE_CONTENT_SENTINEL'
        for name, fixture in [('validate_observation', observation()), ('validate_usage_bundle', bundle())]:
            for change in ({'schema_version': 2}, {'raw_content': private}, {'source_path': private}):
                with self.subTest(name=name, change=change):
                    with self.assertRaises(ValueError) as error:
                        call(name, fixture | change)
                    self.assertNotIn(private, str(error.exception))

    def test_observation_requires_explicit_metadata(self):
        valid = observation()
        self.assertEqual(call('validate_observation', valid), valid)
        for field in ('schema_version', 'kind', 'profile_id', 'profile_version',
                      'source_hash', 'record_number', 'counter_scope', 'provider_scope',
                      'source_time', 'source_time_quality', 'observed_at', 'state',
                      'outcome', 'attribution', 'measurements'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                call('validate_observation', {key: value for key, value in valid.items() if key != field})

    def test_counter_scope_is_explicit_and_recognized(self):
        valid = observation()
        self.assertEqual(call('validate_observation', valid), valid)
        with self.assertRaises(ValueError):
            call('validate_observation', valid | {'counter_scope': 'request'})

    def test_identifier_character_limit(self):
        valid = observation() | {'profile_id': 'p' * 256}
        self.assertEqual(call('validate_observation', valid), valid)
        with self.assertRaises(ValueError):
            call('validate_observation', valid | {'profile_id': 'p' * 257})

    def test_opaque_identifiers_reject_paths_and_free_text(self):
        valid = bundle()
        self.assertEqual(call('validate_usage_bundle', valid), valid)
        for unsafe in ('/private/source.json', '../private/source.json',
                       'C:\\private\\source.json', 'private source content', 'private_secret_token'):
            variants = []
            project = copy.deepcopy(valid)
            project['project_id'] = unsafe
            variants.append(project)
            source = copy.deepcopy(valid)
            source['sources'][0]['source_id'] = unsafe
            variants.append(source)
            provider = copy.deepcopy(valid)
            provider['observations'][0]['provider_scope'] = unsafe
            variants.append(provider)
            candidate = copy.deepcopy(valid)
            candidate['observations'][0]['attribution']['candidates'] = [unsafe]
            variants.append(candidate)
            for variant in variants:
                with self.subTest(unsafe=unsafe, variant=variants.index(variant)):
                    with self.assertRaises(ValueError) as error:
                        call('validate_usage_bundle', variant)
                    self.assertNotIn(unsafe, str(error.exception))

    def test_other_identifiers_reject_paths_and_free_text(self):
        valid = observation() | {'response_id': 'response-1', 'call_id': 'call-1'}
        self.assertEqual(call('validate_observation', valid), valid)
        self.assertEqual(call('validate_usage_bundle', bundle()), bundle())
        self.assertEqual(call('validate_evidence_object', evidence()), evidence())
        for unsafe in ('/private/source.json', '../private/source.json',
                       'C:\\private\\source.json', 'private source content'):
            for field in ('profile_id', 'profile_version', 'response_id', 'call_id'):
                with self.subTest(unsafe=unsafe, field=field):
                    with self.assertRaises(ValueError) as error:
                        call('validate_observation', valid | {field: unsafe})
                    self.assertNotIn(unsafe, str(error.exception))
            with self.subTest(unsafe=unsafe, field='run_id'):
                with self.assertRaises(ValueError) as error:
                    call('validate_usage_bundle', bundle() | {'run_id': unsafe})
                self.assertNotIn(unsafe, str(error.exception))
            with self.subTest(unsafe=unsafe, field='evidence_profile_id'):
                with self.assertRaises(ValueError) as error:
                    call('validate_evidence_object', evidence() | {'profile_id': unsafe})
                self.assertNotIn(unsafe, str(error.exception))

    def test_timestamps_are_not_opaque_identifiers(self):
        valid = observation() | {'source_time': '2026-01-02T03:04:04Z',
                                 'source_time_quality': 'verified',
                                 'observed_at': '2026-01-02T03:04:05Z'}
        self.assertEqual(call('validate_observation', valid), valid)

    def test_invalid_timestamps_are_rejected_without_exposure(self):
        valid = observation() | {'source_time': '2026-01-02T03:04:04Z',
                                 'source_time_quality': 'verified'}
        self.assertEqual(call('validate_observation', valid), valid)
        for field in ('source_time', 'observed_at'):
            for unsafe in ('/private/source.json', 'private source text',
                           '2026-99-99T12:00:00Z', '2026-01-02'):
                with self.subTest(field=field, unsafe=unsafe):
                    with self.assertRaises(ValueError) as error:
                        call('validate_observation', valid | {field: unsafe})
                    self.assertNotIn(unsafe, str(error.exception))

    def test_candidate_set_is_canonical(self):
        first = observation()
        first['attribution']['candidates'] = ['sha256:' + 'a' * 64, 'sha256:' + 'b' * 64]
        second = copy.deepcopy(first)
        second['attribution']['candidates'].reverse()
        self.assertEqual(contract.canonical_bytes(first), contract.canonical_bytes(second))
        self.assertEqual(contract.observation_id(first), contract.observation_id(second))

    def test_bundle_sets_are_canonical_and_sequences_remain_ordered(self):
        first = observation()
        second = copy.deepcopy(first)
        one = bundle()
        one['observations'] = [first, second | {'record_number': 2}]
        one['evidence_objects'] = [evidence(), evidence() | {'record_number': 2}]
        for item in one['observations']:
            item['measurements'] = {'input_uncached': {'measurement_state': 'final', 'value': 1, 'reasons': []}}
        one['sources'].append({'source_id': 'sha256:' + 'f' * 64, 'sha256': 'f' * 64})
        two = copy.deepcopy(one)
        two['sources'].reverse()
        two['observations'].reverse()
        two['evidence_objects'].reverse()
        self.assertEqual(call('validate_usage_bundle', one), one)
        self.assertEqual(call('validate_usage_bundle', two), two)
        self.assertEqual(contract.canonical_bytes(one), contract.canonical_bytes(two))
        self.assertEqual(contract.content_id(one), contract.content_id(two))
        self.assertNotEqual(contract.canonical_bytes({'stream': [1, 2]}),
                            contract.canonical_bytes({'stream': [2, 1]}))

    def test_evidence_profile_record_and_bundle_scope_are_checked(self):
        valid = observation()
        self.assertTrue(call('verify_measurement_evidence', valid, 'input_uncached', evidence()))
        for change in ({'profile_id': 'other'}, {'record_number': 2}):
            item = evidence() | change
            candidate = copy.deepcopy(valid)
            candidate['measurements']['input_uncached']['evidence'] = contract.content_id(item)
            self.assertFalse(call('verify_measurement_evidence', candidate, 'input_uncached', item))
        good = bundle()
        self.assertEqual(call('validate_usage_bundle', good), good)
        for change in ({'profile_id': 'other'}, {'profile_version': 'other'}, {'source_hash': 'b' * 64}):
            invalid = copy.deepcopy(good)
            invalid['observations'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_usage_bundle', invalid)

    def test_exact_canonical_bundle_limit_and_multibyte_input(self):
        value = bundle()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'BUNDLE_LIMIT', size):
            self.assertEqual(call('validate_usage_bundle', value), value)
        with patch.object(contract, 'BUNDLE_LIMIT', size - 1):
            with self.assertRaises(ValueError):
                call('validate_usage_bundle', value)
        obs = observation() | {'profile_id': 'é'}
        data = json.dumps(obs, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        with patch.object(contract, 'OBSERVATION_LIMIT', len(data)):
            self.assertEqual(call('validate_observation_json', data), obs)
            with self.assertRaises(ValueError):
                call('validate_observation_json', data + b' ')

    def test_canonical_observation_limit_gate(self):
        value = observation()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'OBSERVATION_LIMIT', size):
            self.assertEqual(call('validate_observation', value), value)
        with patch.object(contract, 'OBSERVATION_LIMIT', size - 1):
            with self.assertRaises(ValueError):
                call('validate_observation', value)

    def test_observation_json_input_byte_limit(self):
        data = json.dumps(observation(), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        exact = data + b' ' * (1024 * 1024 - len(data))
        self.assertEqual(call('validate_observation_json', exact), observation())
        with self.assertRaises(ValueError):
            call('validate_observation_json', exact + b' ')

    def test_bundle_json_input_byte_limit(self):
        data = json.dumps(bundle(), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        exact = data + b' ' * (32 * 1024 * 1024 - len(data))
        self.assertEqual(call('validate_usage_bundle_json', exact), bundle())
        with self.assertRaises(ValueError):
            call('validate_usage_bundle_json', exact + b' ')

    def test_bundle_observation_count_limit(self):
        value = bundle()
        base = observation()
        base['measurements'] = {'input_uncached': {'measurement_state': 'final',
                                                   'value': 1, 'reasons': []}}
        value['evidence_objects'] = []
        value['observations'] = [base | {'record_number': n} for n in range(1, 10001)]
        self.assertEqual(call('validate_usage_bundle', value), value)
        extra = value | {'observations': value['observations'] + [base | {'record_number': 10001}]}
        with self.assertRaises(ValueError):
            call('validate_usage_bundle', extra)

    def test_bundle_canonical_byte_limit(self):
        base = observation()
        base['measurements'] = {'input_uncached': {'measurement_state': 'final',
                                                    'value': 1, 'reasons': []}}
        base['attribution']['candidates'] = ['sha256:' + hashlib.sha256(str(i).encode()).hexdigest() for i in range(64)]
        value = bundle() | {'evidence_objects': []}
        value['observations'] = [base | {'record_number': n} for n in range(1, 6001)]
        self.assertLessEqual(len(contract.canonical_bytes(value)), 32 * 1024 * 1024)
        self.assertEqual(call('validate_usage_bundle', value), value)
        larger = value | {'observations': value['observations'] +
                          [base | {'record_number': n} for n in range(6001, 7101)]}
        self.assertGreater(len(contract.canonical_bytes(larger)), 32 * 1024 * 1024)
        with self.assertRaises(ValueError):
            call('validate_usage_bundle', larger)

    def test_evidence_association_requires_matching_separate_object(self):
        obs = observation()
        measurement = obs['measurements']['input_uncached']
        self.assertTrue(call('verify_measurement_evidence', obs, 'input_uncached', evidence()))
        altered = evidence() | {'value': 1}
        self.assertFalse(call('verify_measurement_evidence', obs, 'input_uncached', altered))
        self.assertFalse(call('verify_measurement_evidence', obs, 'input_uncached', None))
        for changed in ({'field': 'output_tokens'}, {'source_hash': 'b' * 64}, {'value': 1}):
            mismatch = evidence() | changed
            candidate = copy.deepcopy(obs)
            candidate['measurements']['input_uncached']['evidence'] = contract.content_id(mismatch)
            self.assertFalse(call('verify_measurement_evidence', candidate, 'input_uncached', mismatch))
        circular = evidence() | {'evidence': measurement['evidence']}
        candidate = copy.deepcopy(obs)
        candidate['measurements']['input_uncached']['evidence'] = contract.content_id(circular)
        self.assertFalse(call('verify_measurement_evidence', candidate, 'input_uncached', circular))

    def test_rejects_missing_measurements_and_malformed_hash(self):
        for value in (observation() | {'measurements': None}, observation() | {'source_hash': 'xyz'}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                call('validate_observation', value)

    def test_rejects_duplicate_json_keys_before_validation(self):
        data = json.dumps(observation(), separators=(',', ':'))
        duplicate = data[:-1] + ',"schema_version":1}'
        with self.assertRaises(ValueError):
            call('validate_observation_json', duplicate)


if __name__ == '__main__':
    unittest.main()
