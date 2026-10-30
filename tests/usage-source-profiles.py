#!/usr/bin/env python3
"""Offline source-counter normalization and split cache evidence checks."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contract', ROOT / 'scripts/usage_telemetry_contract.py')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def field(name, measurement, includes=(), ttl=None):
    result = {'path': ['usage', name], 'measurement': measurement,
              'counter_scope': 'response_total', 'semantics_status': 'verified',
              'includes': list(includes)}
    if ttl is not None:
        result['ttl'] = ttl
    return result


def profile(included=True):
    first = field('input', 'input_total', ('input_cache_read', 'input_cache_write')) if included else field('input', 'input_uncached')
    return {'schema_version': 1, 'kind': 'source_profile', 'profile_id': 'synthetic-profile',
            'profile_version': '1', 'provider': 'synthetic-provider', 'runtime': 'synthetic-runtime',
            'format_version': '1', 'counter_fields': [first,
                field('read', 'input_cache_read'), field('write', 'input_cache_write_unsplit'),
                field('short', 'input_cache_write', ttl='5m'),
                field('long', 'input_cache_write', ttl='1h'),
                field('output', 'output_total', ('reasoning_subset',)),
                field('reasoning', 'reasoning_subset')],
            'identity_scope': {'account': 'provider_account', 'response': 'response_id'},
            'finality': {'signals': ['complete'], 'status': 'verified'},
            'inventory': {'status': 'verified', 'evidence': 'synthetic-inventory-evidence'},
            'capabilities': {'cache': 'supported', 'effort': 'unknown', 'tools': 'unknown'},
            'capability_evidence': {'cache': 'synthetic-cache-evidence'},
            'known_gaps': [], 'verified_at': '2026-01-02T03:04:05Z',
            'source': 'https://example.invalid/synthetic-format'}


def normalize(selected_profile, counters, version='1'):
    return contract.normalize_source_counters(selected_profile, {'usage': counters},
                                              profile_version=version, source_hash='a' * 64,
                                              record_number=1)


def evidence(ttl, value):
    return {'schema_version': 1, 'kind': 'measurement_evidence', 'profile_id': 'synthetic-profile',
            'source_hash': 'a' * 64, 'record_number': 1, 'field': 'input_cache_write',
            'ttl': ttl, 'value': value}


def split_bundle():
    objects = [evidence('5m', 100), evidence('1h', 50)]
    pieces = [{'ttl': obj['ttl'], 'tokens': {'measurement_state': 'final', 'value': obj['value'],
                                           'reasons': [], 'evidence': contract.content_id(obj)}}
              for obj in objects]
    obs = {'schema_version': 1, 'kind': 'request_usage', 'profile_id': 'synthetic-profile',
           'profile_version': '1', 'source_hash': 'a' * 64, 'record_number': 1,
           'counter_scope': 'response_total', 'provider_scope': 'sha256:' + 'c' * 64,
           'source_time': None, 'source_time_quality': 'unknown',
           'observed_at': '2026-01-02T03:04:05Z', 'state': 'final', 'outcome': 'succeeded',
           'attribution': {'owner_kind': 'unattributed', 'quality': 'asserted', 'candidates': []},
           'measurements': {'input_cache_write': pieces,
                            'input_cache_write_unsplit': {'measurement_state': 'final', 'value': 150, 'reasons': []}}}
    return {'schema_version': 1, 'kind': 'usage_bundle', 'profile_id': 'synthetic-profile',
            'profile_version': '1', 'project_id': 'sha256:' + 'd' * 64, 'run_id': 'run',
            'sources': [{'source_id': 'sha256:' + 'e' * 64, 'sha256': 'a' * 64}],
            'observations': [obs], 'evidence_objects': objects,
            'inventories': [], 'segments': [], 'diagnostics': []}


class SourceNormalizationTests(unittest.TestCase):
    def test_included_and_separate_inputs_have_equal_nonoverlapping_totals(self):
        raw = {'input': 1000, 'read': 200, 'write': 150, 'short': 100, 'long': 50,
               'output': 500, 'reasoning': 100}
        included = profile()
        separate = profile(False)
        self.assertEqual(contract.validate_source_profile(included), included)
        self.assertEqual(contract.validate_source_profile(separate), separate)
        one = normalize(included, raw)['measurements']
        two = normalize(separate, raw | {'input': 650})['measurements']
        for result in (one, two):
            self.assertEqual(result['input_uncached']['value'], 650)
            self.assertEqual(result['tokens_in']['value'], 1000)
            self.assertEqual(result['output_total']['value'], 500)
            self.assertEqual(result['reasoning_subset']['value'], 100)
            self.assertEqual({part['ttl']: part['tokens']['value'] for part in result['input_cache_write']},
                             {'5m': 100, '1h': 50})
        no_write = copy.deepcopy(included)
        no_write['counter_fields'] = [entry for entry in no_write['counter_fields']
                                      if entry['measurement'] not in ('input_cache_write', 'input_cache_write_unsplit')]
        no_write['counter_fields'][0]['includes'] = ['input_cache_read']
        self.assertEqual(contract.validate_source_profile(no_write), no_write)
        self.assertEqual(normalize(no_write, {'input': 1000, 'read': 200})['measurements']['input_uncached']['value'], 800)

    def test_matching_split_retains_evidence_and_does_not_double_count(self):
        result = normalize(profile(), {'input': 1000, 'read': 200, 'write': 150, 'short': 100, 'long': 50})
        measurements = result['measurements']
        self.assertEqual(measurements['tokens_in']['value'], 1000)
        by_digest = {contract.content_id(obj): obj for obj in result['evidence_objects']}
        for part in measurements['input_cache_write']:
            obj = by_digest[part['tokens']['evidence']]
            self.assertEqual(obj['ttl'], part['ttl'])
            self.assertEqual(obj['value'], part['tokens']['value'])
            self.assertEqual(obj['profile_id'], 'synthetic-profile')
            self.assertEqual(obj['source_hash'], 'a' * 64)
            self.assertEqual(obj['record_number'], 1)

    def test_mismatch_and_negative_remainder_preserve_unaffected_output(self):
        for raw in ({'input': 1000, 'read': 200, 'write': 151, 'short': 100, 'long': 50, 'output': 500},
                    {'input': 100, 'read': 200, 'write': 150, 'short': 100, 'long': 50, 'output': 500}):
            with self.subTest(raw=raw):
                result = normalize(profile(), raw)['measurements']
                self.assertEqual(result['output_total']['value'], 500)
                self.assertNotEqual(result['tokens_in']['measurement_state'], 'final')
                self.assertNotIn('value', result['tokens_in'])
                self.assertTrue(any(item.get('measurement_state') == 'conflicted'
                                    for item in result.values() if isinstance(item, dict)))

    def assert_conflicting_write_counters_are_unavailable(self, included):
        selected = profile(included)
        selected['counter_fields'].append(field('other_write', 'input_cache_write_unsplit'))
        contract.validate_source_profile(selected)
        result = normalize(selected, {'input': 1000 if included else 650, 'read': 200,
                                      'write': 150, 'other_write': 999, 'short': 100,
                                      'long': 50, 'output': 500, 'reasoning': 100})
        measurements = result['measurements']
        self.assertEqual(measurements['input_cache_write_unsplit']['measurement_state'], 'conflicted')
        self.assertNotIn('value', measurements['tokens_in'])
        self.assertIn(measurements['tokens_in']['measurement_state'], ('unavailable', 'conflicted'))
        if included:
            self.assertNotIn('value', measurements['input_uncached'])
        else:
            self.assertEqual(measurements['input_uncached']['value'], 650)
        self.assertEqual(measurements['output_total']['value'], 500)
        self.assertEqual(measurements['reasoning_subset']['value'], 100)
        self.assertFalse(any(obj['kind'] == 'derived_measurement_evidence' and
                             obj['field'] in ('tokens_in', 'input_uncached')
                             for obj in result['evidence_objects']))
        bundle = split_bundle()
        bundle['observations'][0]['measurements'] = measurements
        bundle['evidence_objects'] = result['evidence_objects']
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)

    def test_conflicting_unsplit_writes_block_separate_input_total(self):
        self.assert_conflicting_write_counters_are_unavailable(False)

    def test_conflicting_unsplit_writes_block_included_input_remainder(self):
        self.assert_conflicting_write_counters_are_unavailable(True)

    def test_reasoning_exceeding_output_is_conflicted(self):
        result = normalize(profile(), {'input': 1000, 'read': 200, 'write': 150, 'short': 100,
                                       'long': 50, 'output': 100, 'reasoning': 101})['measurements']
        self.assertEqual(result['reasoning_subset']['measurement_state'], 'conflicted')
        self.assertEqual(result['tokens_in']['value'], 1000)

    def test_unsupported_version_and_unknown_cache_are_never_invented_zero(self):
        raw = {'input': 1000, 'read': 200, 'output': 400}
        unsupported = normalize(profile(), raw, version='unknown')['measurements']
        for measurement in unsupported.values():
            if isinstance(measurement, dict):
                self.assertNotEqual(measurement['measurement_state'], 'final')
                self.assertNotEqual(measurement.get('value'), 0)
        unknown = normalize(profile(), raw)['measurements']
        self.assertNotEqual(unknown['tokens_in']['measurement_state'], 'final')
        self.assertNotIn('value', unknown['tokens_in'])
        self.assertNotEqual(unknown.get('input_cache_write_unsplit', {}).get('value'), 0)
        self.assertEqual(unknown['output_total']['value'], 400)

    def test_unverified_counter_semantics_cannot_be_used_to_infer_remainder(self):
        selected = profile()
        selected['counter_fields'][0]['semantics_status'] = 'unknown'
        del selected['counter_fields'][0]['includes']
        self.assertEqual(contract.validate_source_profile(selected), selected)
        result = normalize(selected, {'input': 1000, 'read': 200, 'write': 150, 'short': 100,
                                      'long': 50, 'output': 500})['measurements']
        self.assertNotEqual(result['input_uncached']['measurement_state'], 'final')
        self.assertNotIn('value', result['input_uncached'])
        self.assertEqual(result['output_total']['value'], 500)


class SplitSchemaTests(unittest.TestCase):
    def test_observation_and_bundle_validate_per_component_evidence_and_canonical_order(self):
        one = split_bundle()
        two = copy.deepcopy(one)
        two['observations'][0]['measurements']['input_cache_write'].reverse()
        two['evidence_objects'].reverse()
        for bundle in (one, two):
            obs = bundle['observations'][0]
            self.assertEqual(contract.validate_observation(obs), obs)
            for obj in bundle['evidence_objects']:
                self.assertEqual(contract.validate_evidence_object(obj), obj)
            self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        self.assertEqual(contract.canonical_bytes(one), contract.canonical_bytes(two))
        self.assertEqual(contract.content_id(one), contract.content_id(two))
        self.assertEqual(contract.observation_id(one['observations'][0]), contract.observation_id(two['observations'][0]))

    def test_duplicate_ttl_mismatched_total_and_wrong_evidence_are_rejected(self):
        for defect in ('duplicate', 'total', 'evidence'):
            value = split_bundle()
            obs = value['observations'][0]
            pieces = obs['measurements']['input_cache_write']
            if defect == 'duplicate':
                pieces.append(copy.deepcopy(pieces[0]))
            elif defect == 'total':
                obs['measurements']['input_cache_write_unsplit']['value'] = 151
            else:
                pieces[0]['tokens']['evidence'] = pieces[1]['tokens']['evidence']
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                contract.validate_usage_bundle(value)


class NormalizationEvidenceTests(unittest.TestCase):
    def test_large_derived_sum_is_exact_decimal_string_in_observation(self):
        maximum = 9007199254740991
        selected = profile(False)
        result = normalize(selected, {'input': maximum, 'read': maximum, 'write': 1,
                                      'short': 1, 'long': 0})
        measurement = result['measurements']['tokens_in']
        self.assertEqual(measurement['value'], str(maximum * 2 + 1))
        obs = split_bundle()['observations'][0]
        obs['measurements'] = {'tokens_in': measurement}
        self.assertEqual(contract.validate_observation(obs), obs)
        proof = next(obj for obj in result['evidence_objects']
                     if contract.content_id(obj) == measurement['evidence'])
        self.assertTrue(contract.verify_derived_measurement_evidence(
            measurement, proof, result['evidence_objects'], selected))

    def test_proven_total_remains_usable_when_one_ttl_is_unknown(self):
        result = normalize(profile(), {'input': 1000, 'read': 200, 'write': 150,
                                       'short': 100, 'output': 400})['measurements']
        self.assertEqual(result['input_uncached']['value'], 650)
        self.assertEqual(result['tokens_in']['value'], 1000)
        pieces = {part['ttl']: part['tokens'] for part in result['input_cache_write']}
        self.assertEqual(pieces['5m']['value'], 100)
        self.assertEqual(pieces['1h']['measurement_state'], 'unavailable')
        self.assertNotIn('value', pieces['1h'])
        self.assertEqual(result['output_total']['value'], 400)

    def test_known_part_above_total_conflicts_even_with_missing_ttl(self):
        result = normalize(profile(), {'input': 1000, 'read': 200, 'write': 150,
                                       'short': 200, 'output': 400})['measurements']
        self.assertEqual(result['input_cache_write_unsplit']['measurement_state'], 'conflicted')
        self.assertNotIn('value', result['tokens_in'])
        self.assertNotEqual(result['tokens_in']['measurement_state'], 'final')
        self.assertEqual(result['output_total']['value'], 400)

    def test_derived_evidence_references_operands_and_verified_profile(self):
        selected = profile()
        result = normalize(selected, {'input': 1000, 'read': 200, 'write': 150,
                                      'short': 100, 'long': 50})
        by_hash = {contract.content_id(obj): obj for obj in result['evidence_objects']}
        for field in ('input_uncached', 'tokens_in'):
            with self.subTest(field=field):
                measurement = result['measurements'][field]
                proof = by_hash[measurement['evidence']]
                self.assertEqual(proof['kind'], 'derived_measurement_evidence')
                self.assertEqual(proof['profile_hash'], contract.content_id(selected))
                self.assertIn(proof['operation'], ('sum', 'subtract'))
                self.assertGreaterEqual(len(proof['operands']), 2)
                operands = [by_hash[reference] for reference in proof['operands']]
                self.assertTrue(all(obj['profile_id'] == selected['profile_id'] and
                                    obj['source_hash'] == 'a' * 64 and obj['record_number'] == 1
                                    for obj in operands))
                self.assertTrue(contract.verify_derived_measurement_evidence(
                    measurement, proof, result['evidence_objects'], selected))
                self.assertFalse(contract.verify_derived_measurement_evidence(
                    measurement, proof, [obj for obj in result['evidence_objects']
                                         if contract.content_id(obj) != proof['operands'][0]], selected))
        uncached_proof = by_hash[result['measurements']['input_uncached']['evidence']]
        operand_fields = {by_hash[reference]['field'] for reference in uncached_proof['operands']}
        self.assertEqual(operand_fields, {'input_total', 'input_cache_read', 'input_cache_write_unsplit'})

    def test_derived_proof_rejects_rehashed_value_scope_and_profile_tampering(self):
        selected = profile()
        result = normalize(selected, {'input': 1000, 'read': 200, 'write': 150,
                                      'short': 100, 'long': 50})
        measurement = result['measurements']['input_uncached']
        objects = result['evidence_objects']
        proof = next(obj for obj in objects if contract.content_id(obj) == measurement['evidence'])
        self.assertTrue(contract.verify_derived_measurement_evidence(measurement, proof, objects, selected))
        for defect in ('value', 'scope', 'profile', 'operand'):
            with self.subTest(defect=defect):
                candidate = copy.deepcopy(proof)
                altered_measurement = copy.deepcopy(measurement)
                altered_objects = copy.deepcopy(objects)
                altered_profile = copy.deepcopy(selected)
                if defect == 'value':
                    candidate['value'] += 1
                    altered_measurement['value'] += 1
                elif defect == 'scope':
                    candidate['record_number'] += 1
                elif defect == 'profile':
                    altered_profile['counter_fields'][0]['includes'] = ['input_cache_read']
                    candidate['profile_hash'] = contract.content_id(altered_profile)
                else:
                    original_hash = candidate['operands'][0]
                    operand = next(obj for obj in altered_objects if contract.content_id(obj) == original_hash)
                    operand['value'] += 1
                    candidate['operands'][0] = contract.content_id(operand)
                altered_measurement['evidence'] = contract.content_id(candidate)
                self.assertFalse(contract.verify_derived_measurement_evidence(
                    altered_measurement, candidate, altered_objects, altered_profile))


if __name__ == '__main__':
    unittest.main()
