#!/usr/bin/env python3
"""End-to-end offline resolution with independently authorized evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


contract = load('contract', 'scripts/usage_telemetry_contract.py')
profiles = load('profile_fixtures', 'tests/usage-source-profiles.py')
inventories = load('inventory_fixtures', 'tests/usage-inventory-completeness.py')
prices = load('price_fixtures', 'tests/usage-price-applicability.py')
applicability = load('applicability', 'scripts/usage_telemetry_applicability.py')


def opaque(char):
    return 'sha256:' + char * 64


class Verifier:
    """Explicit independent authority: exact binding, never an input flag."""
    def __init__(self, allowed):
        self.allowed = copy.deepcopy(allowed)
        self.calls = []

    def __call__(self, kind, scope, subject, evidence):
        binding = (kind, scope, subject, evidence)
        self.calls.append(copy.deepcopy(binding))
        return binding in self.allowed


def fixture(raw_override=None, profile_override=None):
    profile = profiles.profile() if profile_override is None else profile_override
    inventory, _ = inventories.inventory()
    inventory['profile_id'] = profile['profile_id']
    inventory['window']['end'] = '2029-01-01T00:00:00Z'
    inventory['observed_at'] = '2029-01-01T00:00:01Z'
    inventory, inventory_evidence = inventories.bind(inventory)
    scope = inventory['owner_scope']
    bundle = profiles.split_bundle()
    bundle['observations'] = []
    bundle['evidence_objects'] = [inventory_evidence]
    bundle['inventories'] = [inventory]
    contexts = []
    raw = {'input': 1000, 'read': 200, 'write': 200, 'short': 100,
           'long': 100, 'output': 100, 'reasoning': 25}
    if raw_override is not None:
        raw = raw_override
    for record, char in ((1, '1'), (2, '2')):
        normalized = contract.normalize_source_counters(
            profile, {'usage': raw}, profile_version='1', source_hash='a' * 64,
            record_number=record)
        for measurement in normalized['measurements'].values():
            parts = [item['tokens'] for item in measurement] if isinstance(measurement, list) else [measurement]
            for part in parts:
                if part['measurement_state'] == 'partial':
                    part['measurement_state'] = 'final'
        observation = profiles.split_bundle()['observations'][0]
        observation.update(record_number=record, response_id=opaque(char), call_id=opaque(char),
                           source_time=('2026-01-01T00:00:00Z' if record == 1 else '2028-01-01T00:00:00Z'),
                           source_time_quality='verified',
                           observed_at=('2026-01-02T03:04:05Z' if record == 1 else '2028-01-02T03:04:05Z'),
                           measurements=normalized['measurements'])
        bundle['observations'].append(observation)
        bundle['evidence_objects'].extend(normalized['evidence_objects'])
        # All supplemental facts are exact, per-observation evidence declarations.
        context = {'observation_id': contract.observation_id(observation),
                   'profile_id': profile['profile_id'], 'profile_version': '1',
                   'source_hash': observation['source_hash'], 'record_number': record,
                   'provider_scope': observation['provider_scope'], 'counter_scope': 'response_total',
                   'provider': profile['provider'], 'session_id': opaque('e'),
                   'event': {'kind': 'snapshot', 'final': True},
                   'execution_time': '2026-01-01T00:00:00Z' if record == 1 else '2028-01-01T00:00:00Z',
                   'parameters': {'model': 'vendor/model', 'service_tier': 'standard',
                                  'region': 'example-region', 'modality': 'text'},
                   'cache_ttl_seconds': {'5m': 300, '1h': 3600}}
        context['evidence_objects'] = [
            {'schema_version': 1, 'kind': 'execution_time_evidence', 'profile_id': profile['profile_id'],
             'source_hash': observation['source_hash'], 'record_number': record, 'value': context['execution_time']},
            *[{'schema_version': 1, 'kind': 'source_parameter_evidence', 'profile_id': profile['profile_id'],
               'source_hash': observation['source_hash'], 'record_number': record, 'field': field, 'value': value}
              for field, value in context['parameters'].items()],
            *[{'schema_version': 1, 'kind': 'rate_parameter_evidence', 'profile_id': profile['profile_id'],
               'source_hash': observation['source_hash'], 'record_number': record,
               'field': 'cache_ttl_seconds', 'value': value}
              for value in context['cache_ttl_seconds'].values()]]
        contexts.append(context)
    snapshots, scenario, _, evidence, _ = prices.fixture()
    snapshot = snapshots[0]
    snapshot['rates'] = [
        {'component': name, 'usd': amount, 'unit': 'tokens', 'unit_quantity': 1000000,
         'cache_ttl_seconds': ttl, 'threshold': None, 'multiplier': {'state': 'none'}}
        for name, amount, ttl in [('input_uncached', '2', None), ('input_cache_read', '0.2', None),
                                   ('input_cache_write', '2.5', 300), ('input_cache_write', '4', 3600),
                                   ('output', '10', None)]]
    scenario['snapshot_ids'] = [contract.price_snapshot_id(snapshot)]
    # Existing applicability evidence schema is itself per-record. Additional
    # context attestations bind the profile, source, scope, record and value.
    price_evidence = [item for item in evidence if item['kind'] == 'price_period_evidence']
    price_evidence.append({'schema_version': 1, 'kind': 'price_snapshot_evidence',
                           'snapshot_id': contract.price_snapshot_id(snapshot), 'source_hash': 'b' * 64})
    allowed = []
    allowed.append(('inventory', scope, inventory, inventory_evidence))
    allowed.append(('nonnegative_scope', scope, inventory, inventory_evidence))
    allowed.append(('profile', scope, profile, profile))
    for observation, context in zip(bundle['observations'], contexts):
        allowed.append(('context', scope, observation, context))
        allowed.append(('response_privacy', scope, observation, observation))
        for proof in context['evidence_objects']:
            applicability._validate_applicability_evidence(proof)
            allowed.append(('pricing_context', scope, observation, proof))
        for field, measurement in observation['measurements'].items():
            if field == 'input_cache_write':
                for part in measurement:
                    proof = next(e for e in bundle['evidence_objects']
                                 if contract.content_id(e) == part['tokens']['evidence'])
                    allowed.append(('measurement', scope, {'observation': observation, 'field': field,
                                                          'ttl': part['ttl']}, proof))
            elif 'evidence' in measurement:
                proof = next(e for e in bundle['evidence_objects']
                             if contract.content_id(e) == measurement['evidence'])
                allowed.append(('measurement', scope, {'observation': observation, 'field': field}, proof))
    # A derived value is trustworthy only when each source operand has an
    # independently authorized record and scope binding of its own.
    objects = {contract.content_id(item): item for item in bundle['evidence_objects']}
    for observation in bundle['observations']:
        def authorize_operand(digest):
            proof = objects[digest]
            if proof['kind'] == 'derived_measurement_evidence':
                for operand in proof['operands']:
                    authorize_operand(operand)
            else:
                subject = {'observation': observation, 'field': proof['field']}
                if 'ttl' in proof:
                    subject['ttl'] = proof['ttl']
                binding = ('measurement', scope, subject, proof)
                if binding not in allowed:
                    allowed.append(binding)
        for measurement in observation['measurements'].values():
            parts = [part['tokens'] for part in measurement] if isinstance(measurement, list) else [measurement]
            for part in parts:
                if 'evidence' in part:
                    authorize_operand(part['evidence'])
    for proof in price_evidence:
        allowed.append(('price', scope, snapshot, proof))
    contract.validate_source_profile(profile)
    contract.validate_usage_bundle(bundle)
    contract.validate_price_snapshot(snapshot)
    contract.validate_pricing_scenario(scenario)
    return {'bundle': bundle, 'profile': profile, 'contexts': contexts,
            'snapshots': [snapshot], 'scenario': scenario, 'price_evidence': price_evidence,
            'scope': scope, 'as_of': '2029-01-02T00:00:00Z'}, allowed


def resolve(data, verifier):
    path = ROOT / 'scripts/usage_telemetry_resolution.py'
    if not path.exists():
        return None
    return load('usage_resolution', 'scripts/usage_telemetry_resolution.py').resolve_usage(
        **data, verifier=verifier)


class ResolutionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = fixture()
        self.verifier = Verifier(self.allowed)

    def report(self):
        result = resolve(self.data, self.verifier)
        self.assertIsInstance(result, dict, 'an integrated offline resolver is required')
        return result

    def test_real_bundle_separates_final_tokens_from_historical_price_coverage(self):
        report = self.report()
        self.assertEqual(report['completeness']['measurements']['input'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['completeness']['measurements']['output'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['completeness']['priced'], {'numerator': 1, 'denominator': 2})
        self.assertNotIn('cost_usd', report['cost'])
        self.assertEqual(report['cost']['priced_subtotal_usd'], '0.00289')
        self.assertEqual(report['cost']['subtotal_quality'], 'proven_lower_bound')
        self.assertTrue(any(call[0] == 'inventory' for call in self.verifier.calls))
        contexts = [call for call in self.verifier.calls if call[0] == 'context']
        self.assertEqual({call[2]['record_number'] for call in contexts}, {1, 2})
        self.assertTrue(all(call[1] == self.data['scope'] and
                            call[2]['counter_scope'] == call[3]['counter_scope'] and
                            call[2]['source_hash'] == call[3]['source_hash'] for call in contexts))
        measurements = [call for call in self.verifier.calls if call[0] == 'measurement']
        self.assertTrue(any(call[2].get('ttl') == '5m' and call[3]['value'] == 100 for call in measurements))
        self.assertTrue(any(call[2].get('ttl') == '1h' and call[3]['value'] == 100 for call in measurements))

    def test_untrusted_inventory_never_proves_denominator_or_complete_cost(self):
        self.verifier.allowed = [item for item in self.allowed if item[0] != 'inventory']
        report = self.report()
        self.assertIsNone(report['completeness']['priced']['denominator'])
        self.assertNotIn('cost_usd', report['cost'])

    def test_forged_scope_or_wrong_record_context_is_not_authorized(self):
        context = self.data['contexts'][0]
        context['counter_scope'] = 'session_total'
        report = self.report()
        self.assertNotEqual(report['completeness']['measurements']['input']['numerator'], 2)
        self.assertNotIn('cost_usd', report['cost'])
        self.assertFalse(any(call[0] == 'context' and call in self.allowed for call in self.verifier.calls
                             if call[0] == 'context' and call[2]['record_number'] == 1))

    def test_one_record_measurement_cannot_authorize_another_record(self):
        self.verifier.allowed = [item for item in self.allowed if not (
            item[0] == 'measurement' and item[2]['observation']['record_number'] == 2)]
        report = self.report()
        self.assertEqual(report['completeness']['measurements']['input']['numerator'], 1)
        self.assertNotIn('cost_usd', report['cost'])

    def test_call_only_overlap_cannot_create_additive_cost(self):
        observation = copy.deepcopy(self.data['bundle']['observations'][0])
        observation['record_number'] = 3
        del observation['response_id']
        observation['measurements'] = {'input_uncached': {'measurement_state': 'unavailable', 'reasons': ['source_unavailable']}}
        self.data['bundle']['observations'].append(observation)
        context = copy.deepcopy(self.data['contexts'][0])
        context.update(observation_id=contract.observation_id(observation), record_number=3)
        self.data['contexts'].append(context)
        self.verifier.allowed.append(('context', self.data['scope'], observation, context))
        self.verifier.allowed.append(('response_privacy', self.data['scope'], observation, observation))
        report = self.report()
        self.assertNotIn('cost_usd', report['cost'])
        self.assertNotEqual(report['cost'].get('subtotal_quality'), 'proven_lower_bound')

    def test_set_order_is_deterministic_and_no_network_or_history_is_read(self):
        with patch('socket.socket', side_effect=AssertionError('network access')):
            first = self.report()
            self.data['bundle']['observations'].reverse()
            self.data['bundle']['evidence_objects'].reverse()
            self.data['contexts'].reverse()
            second = self.report()
        self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
