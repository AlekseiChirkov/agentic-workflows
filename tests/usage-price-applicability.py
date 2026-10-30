#!/usr/bin/env python3
"""Offline pricing applicability checks using explicit, scoped evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
contract_spec = importlib.util.spec_from_file_location('contract', ROOT / 'scripts/usage_telemetry_contract.py')
contract = importlib.util.module_from_spec(contract_spec)
contract_spec.loader.exec_module(contract)


def load_selector():
    path = ROOT / 'scripts/usage_telemetry_applicability.py'
    if not path.exists():
        return lambda *args: None
    spec = importlib.util.spec_from_file_location('applicability', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.select_rate


select_rate = load_selector()


def fixture():
    source = 'a' * 64
    period = {'schema_version': 1, 'kind': 'price_period_evidence', 'source_hash': 'b' * 64,
              'start': '2025-01-01T00:00:00Z', 'end': '2027-01-01T00:00:00Z'}
    time = {'schema_version': 1, 'kind': 'execution_time_evidence', 'profile_id': 'profile',
            'source_hash': source, 'record_number': 1, 'value': '2026-01-01T00:00:00Z'}
    params = {}
    evidence = [period, time]
    for field, value in {'model': 'vendor/model', 'service_tier': 'standard',
                         'region': 'example-region', 'modality': 'text'}.items():
        obj = {'schema_version': 1, 'kind': 'source_parameter_evidence', 'profile_id': 'profile',
               'source_hash': source, 'record_number': 1, 'field': field, 'value': value}
        evidence.append(obj)
        params[field] = {'value': value, 'evidence': contract.content_id(obj)}
    rate = {'component': 'input_uncached', 'usd': '2', 'unit': 'tokens', 'unit_quantity': 1000000,
            'cache_ttl_seconds': None, 'threshold': None, 'multiplier': {'state': 'none'}}
    snapshot = {'schema_version': 1, 'kind': 'price_snapshot', 'currency': 'USD',
                'retrieved_at': '2026-02-01T00:00:00Z', 'model': 'vendor/model', 'aliases': [],
                'modality': 'text', 'service_tier': 'standard', 'region': 'example-region',
                'effective_period': {'state': 'known', 'start': period['start'], 'end': period['end'],
                                     'evidence': contract.content_id(period)},
                'rates': [rate], 'primary_sources': ['https://example.org/pricing']}
    scenario = {'schema_version': 1, 'kind': 'pricing_scenario', 'scenario_id': 'baseline',
                'basis': 'at_execution', 'currency': 'USD', 'display_precision': 4,
                'snapshot_ids': [contract.price_snapshot_id(snapshot)],
                'source_parameters': params, 'assumptions': {}, 'threshold_rules': []}
    request = {'component': 'input_uncached', 'unit': 'tokens', 'cache_ttl_seconds': None,
               'tool_id': None, 'execution_time': {'value': time['value'], 'evidence': contract.content_id(time)},
               'profile_id': 'profile', 'source_hash': source, 'record_number': 1,
               'operands': {}, 'verified_aliases': []}
    trusted = {contract.content_id(item) for item in evidence}
    return [snapshot], scenario, request, evidence, trusted


def invoke(parts):
    snapshots, scenario, request, evidence, trusted = parts
    scenario['snapshot_ids'] = [contract.price_snapshot_id(item) for item in snapshots]
    return select_rate(snapshots, scenario, request, evidence, trusted)


def attest(parts):
    """Attach independently trusted, non-cyclic snapshot and work attestations."""
    snapshots, _, request, evidence, trusted = parts
    for snapshot in snapshots:
        proof = {'schema_version': 1, 'kind': 'price_snapshot_evidence',
                 'snapshot_id': contract.price_snapshot_id(snapshot),
                 'source_hash': 'b' * 64}
        digest = contract.content_id(proof)
        if proof not in evidence:
            evidence.append(proof)
        trusted.add(digest)
        for rate in snapshot['rates']:
            multiplier = rate.get('multiplier', {})
            if multiplier.get('state') != 'known':
                continue
            proof = {'schema_version': 1, 'kind': 'multiplier_evidence',
                     'snapshot_id': contract.price_snapshot_id(snapshot),
                     'rate_id': contract.content_id(rate), 'scope': multiplier['scope'],
                     'factor': multiplier['factor'], 'applies': True,
                     'profile_id': request['profile_id'], 'source_hash': request['source_hash'],
                     'record_number': request['record_number']}
            if proof not in evidence:
                evidence.append(proof)
            trusted.add(contract.content_id(proof))
    for field in ('cache_ttl_seconds', 'tool_id'):
        value = request[field]
        if value is None or isinstance(value, dict):
            continue
        proof = {'schema_version': 1, 'kind': 'rate_parameter_evidence', 'field': field,
                 'value': value, 'profile_id': request['profile_id'],
                 'source_hash': request['source_hash'], 'record_number': request['record_number']}
        if proof not in evidence:
            evidence.append(proof)
        identity = contract.content_id(proof)
        trusted.add(identity)
        request[field] = {'value': value, 'evidence': identity}


class ApplicabilityTests(unittest.TestCase):
    def assert_priced(self, parts, usd='2', factor='1', conditional=False):
        attest(parts)
        result = invoke(parts)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['state'], 'priced')
        self.assertEqual(result['rate']['usd'], usd)
        self.assertEqual(result['factor'], factor)
        self.assertEqual(result['conditional'], conditional)

    def assert_unknown(self, parts):
        attest(parts)
        result = invoke(parts)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['state'], 'unpriced')
        self.assertTrue(result['reason'])
        self.assertNotIn('rate', result)

    def test_historical_applicability_requires_scoped_evidence(self):
        base = fixture()
        self.assert_priced(base)
        for mutation in ('untrusted_period', 'untrusted_model', 'time_outside', 'wrong_source', 'missing_model'):
            parts = copy.deepcopy(base)
            snapshots, scenario, request, evidence, trusted = parts
            if mutation == 'untrusted_period': trusted.remove(snapshots[0]['effective_period']['evidence'])
            if mutation == 'untrusted_model': trusted.remove(scenario['source_parameters']['model']['evidence'])
            if mutation == 'time_outside': request['execution_time']['value'] = '2028-01-01T00:00:00Z'
            if mutation == 'wrong_source': request['source_hash'] = 'c' * 64
            if mutation == 'missing_model': scenario['source_parameters']['model'] = None
            with self.subTest(mutation=mutation): self.assert_unknown(parts)

    def test_period_bounds_and_unknown_historical_period(self):
        base = fixture()
        for period in ({'state': 'unknown', 'reason': 'historical_period_unavailable'},):
            parts = copy.deepcopy(base)
            parts[0][0]['effective_period'] = period
            self.assert_unknown(parts)
        parts = copy.deepcopy(base)
        parts[3][1]['value'] = '2027-01-01T00:00:00Z'
        parts[2]['execution_time'] = {'value': parts[3][1]['value'], 'evidence': contract.content_id(parts[3][1])}
        parts[4].add(contract.content_id(parts[3][1]))
        self.assert_unknown(parts)

    def test_missing_or_mismatched_pricing_dimensions_are_unknown(self):
        base = fixture()
        for field in ('model', 'service_tier', 'region', 'modality'):
            for value in (None, 'other'):
                parts = copy.deepcopy(base)
                parts[0][0][field] = value if field != 'model' or value is not None else 'other'
                with self.subTest(field=field, value=value): self.assert_unknown(parts)

    def test_alias_needs_independent_mapping_and_trusted_evidence(self):
        parts = fixture()
        parts[0][0]['model'] = 'vendor/canonical'
        parts[0][0]['aliases'] = [{'alias': 'vendor/model', 'evidence': 'd' * 64}]
        self.assert_unknown(parts)
        parts[2]['verified_aliases'] = [{'alias': 'vendor/model', 'model': 'vendor/canonical', 'evidence': 'd' * 64}]
        self.assert_unknown(parts)
        parts[4].add('d' * 64)
        self.assert_priced(parts)
        parts[2]['verified_aliases'][0]['model'] = 'vendor/other'
        self.assert_unknown(parts)

    def test_multiplier_requires_explicit_known_applicability(self):
        base = fixture()
        for multiplier in (None, {'state': 'unknown', 'scope': 'tier', 'reason': 'unavailable'}):
            parts = copy.deepcopy(base)
            if multiplier is None: del parts[0][0]['rates'][0]['multiplier']
            else: parts[0][0]['rates'][0]['multiplier'] = multiplier
            self.assert_unknown(parts)
        parts = copy.deepcopy(base)
        parts[0][0]['rates'][0]['multiplier'] = {'state': 'known', 'factor': '1.25', 'scope': 'tier'}
        self.assert_priced(parts, factor='1.25')

    def test_threshold_is_per_request_strictly_greater(self):
        parts = fixture()
        base_rate = parts[0][0]['rates'][0]
        high = copy.deepcopy(base_rate)
        high['usd'] = '3'
        high['threshold'] = {'operand': 'input_uncached', 'operator': '>', 'value': 1000}
        parts[0][0]['rates'].append(high)
        parts[1]['threshold_rules'] = [{'operand': 'input_uncached', 'operator': '>', 'value': 1000,
                                        'components': ['input_uncached']}]
        measurement = {'schema_version': 1, 'kind': 'measurement_evidence', 'profile_id': 'profile',
                       'source_hash': parts[2]['source_hash'], 'record_number': 1,
                       'field': 'input_uncached', 'value': 1000}
        parts[3].append(measurement)
        parts[4].add(contract.content_id(measurement))
        parts[2]['operands']['input_uncached'] = {'value': 1000, 'evidence': contract.content_id(measurement)}
        self.assert_priced(parts, '2')
        measurement['value'] = 1001
        parts[4].add(contract.content_id(measurement))
        parts[2]['operands']['input_uncached'] = {'value': 1001, 'evidence': contract.content_id(measurement)}
        self.assert_priced(parts, '3')
        del parts[2]['operands']['input_uncached']
        self.assert_unknown(parts)

    def test_ttl_tool_identity_and_units_must_match(self):
        parts = fixture()
        rate = parts[0][0]['rates'][0]
        rate.update(component='input_cache_write', cache_ttl_seconds=300)
        parts[2].update(component='input_cache_write', cache_ttl_seconds=300)
        self.assert_priced(parts)
        for ttl in (None, 3600):
            bad = copy.deepcopy(parts); bad[2]['cache_ttl_seconds'] = ttl
            self.assert_unknown(bad)
        rate.update(component='tool', unit='request', cache_ttl_seconds=None, tool_id='search')
        parts[2].update(component='tool', unit='request', cache_ttl_seconds=None, tool_id='search')
        self.assert_priced(parts)
        for tool in (None, 'fetch'):
            bad = copy.deepcopy(parts); bad[2]['tool_id'] = tool
            self.assert_unknown(bad)
        bad = copy.deepcopy(parts); del bad[0][0]['rates'][0]['tool_id']
        self.assert_unknown(bad)
        bad = copy.deepcopy(parts); bad[2]['unit'] = 'tokens'
        self.assert_unknown(bad)

    def test_conflicting_overlaps_and_possible_unknown_are_never_first_match(self):
        parts = fixture()
        second = copy.deepcopy(parts[0][0]); second['rates'][0]['usd'] = '3'
        parts[0].append(second)
        self.assert_unknown(parts)
        parts[0].reverse()
        self.assert_unknown(parts)
        parts[0][0]['effective_period'] = {'state': 'unknown', 'reason': 'unavailable'}
        self.assert_unknown(parts)

    def test_reprice_is_conditional_and_assumes_only_explicit_dimensions(self):
        parts = fixture()
        parts[1]['basis'] = 'reprice'
        parts[0][0]['effective_period'] = {'state': 'unknown', 'reason': 'unavailable'}
        parts[1]['source_parameters']['region'] = None
        self.assert_unknown(parts)
        parts[1]['assumptions'] = {'region': 'example-region'}
        self.assert_priced(parts, conditional=True)
        parts[1]['source_parameters']['model'] = None
        self.assert_unknown(parts)


class IndependentEvidenceTests(unittest.TestCase):
    def state(self, parts):
        value = invoke(parts)
        self.assertIsInstance(value, dict)
        return value['state']

    def test_period_evidence_does_not_attest_a_different_snapshot(self):
        parts = fixture()
        attest(parts)
        self.assertEqual(self.state(parts), 'priced')
        # Price changes alter the snapshot id, but never the period evidence id.
        parts[0][0]['rates'][0]['usd'] = '999'
        self.assertEqual(self.state(parts), 'unpriced')
        attest(parts)
        self.assertEqual(self.state(parts), 'priced')
        binding = next(x for x in reversed(parts[3]) if x['kind'] == 'price_snapshot_evidence')
        parts[4].remove(contract.content_id(binding))
        self.assertEqual(self.state(parts), 'unpriced')

    def test_cache_and_tool_identifiers_need_record_scoped_evidence(self):
        for component, unit, field, value in (('input_cache_write', 'tokens', 'cache_ttl_seconds', 300),
                                               ('tool', 'request', 'tool_id', 'search')):
            parts = fixture()
            rate = parts[0][0]['rates'][0]
            rate.update(component=component, unit=unit)
            rate[field] = value
            parts[2].update(component=component, unit=unit)
            # Bind the price first while the work parameter is absent.
            attest(parts)
            parts[2][field] = value
            # A bare value cannot establish actual cache or tool identity.
            self.assertEqual(self.state(parts), 'unpriced')
            attest(parts)
            self.assertEqual(self.state(parts), 'priced')
            digest = parts[2][field]['evidence']
            parts[4].remove(digest)
            self.assertEqual(self.state(parts), 'unpriced')
            parts[4].add(digest)
            parts[2]['record_number'] = 2
            self.assertEqual(self.state(parts), 'unpriced')

    def test_multiplier_requires_scoped_positive_or_negative_applicability_evidence(self):
        parts = fixture()
        parts[0][0]['rates'][0]['multiplier'] = {'state': 'known', 'factor': '1.25', 'scope': 'tier'}
        attest(parts)
        self.assertEqual(self.state(parts), 'priced')
        proof = next(x for x in parts[3] if x['kind'] == 'multiplier_evidence')
        digest = contract.content_id(proof)
        parts[4].remove(digest)
        self.assertEqual(self.state(parts), 'unpriced')
        # A trusted explicit negative attestation proves that the base rate applies.
        proof['applies'] = False
        parts[4].add(contract.content_id(proof))
        result = invoke(parts)
        self.assertEqual(result['state'], 'priced')
        self.assertEqual(result['factor'], '1')
        proof['scope'] = 'unrelated'
        parts[4].add(contract.content_id(proof))
        self.assertEqual(self.state(parts), 'unpriced')

    def test_untrusted_competing_period_is_potential_overlap(self):
        parts = fixture()
        competitor = copy.deepcopy(parts[0][0])
        competitor['rates'][0]['usd'] = '3'
        competitor['effective_period'] = {'state': 'known', 'start': '2028-01-01T00:00:00Z',
                                           'end': '2029-01-01T00:00:00Z', 'evidence': 'd' * 64}
        parts[0].append(competitor)
        attest(parts)
        self.assertEqual(self.state(parts), 'unpriced')
        period = {'schema_version': 1, 'kind': 'price_period_evidence', 'source_hash': 'b' * 64,
                  'start': competitor['effective_period']['start'], 'end': competitor['effective_period']['end']}
        competitor['effective_period']['evidence'] = contract.content_id(period)
        parts[3].append(period)
        parts[4].add(contract.content_id(period))
        attest(parts)
        self.assertEqual(self.state(parts), 'priced')
        parts[4].remove(contract.content_id(period))
        self.assertEqual(self.state(parts), 'unpriced')


if __name__ == '__main__':
    unittest.main()
