#!/usr/bin/env python3
"""Actual response streams with independently authorized finality and corrections."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load('integration', 'tests/usage-resolution-integration.py')
evidence = load('evidence', 'tests/usage-resolution-evidence.py')
contract = base.contract


def authorize(data):
    scope, bundle = data['scope'], data['bundle']
    profile, inventory = data['profile'], bundle['inventories'][0]
    inv_proof = next(item for item in bundle['evidence_objects'] if item['kind'] == 'inventory_evidence')
    allowed = [('profile', scope, profile, profile), ('inventory', scope, inventory, inv_proof),
               ('nonnegative_scope', scope, inventory, inv_proof)]
    objects = {contract.content_id(item): item for item in bundle['evidence_objects']}
    by_id = {contract.observation_id(item): item for item in bundle['observations']}
    for context in data['contexts']:
        observation = by_id[context['observation_id']]
        allowed.append(('context', scope, observation, context))
        allowed.append(('response_privacy', scope, observation, observation))
        for proof in context['evidence_objects']:
            allowed.append(('pricing_context', scope, observation, proof))
        for field, measurement in observation['measurements'].items():
            parts = [(part['ttl'], part['tokens']) for part in measurement] if isinstance(measurement, list) else [(None, measurement)]
            for ttl, item in parts:
                if 'evidence' not in item:
                    continue
                subject = {'observation': observation, 'field': field}
                if ttl is not None:
                    subject['ttl'] = ttl
                allowed.append(('measurement', scope, subject, objects[item['evidence']]))
    evidence.authorize_operands(data, allowed)
    for proof in data['price_evidence']:
        allowed.append(('price', scope, data['snapshots'][0], proof))
    return allowed


def snapshot_fixture(*, correction=False):
    data, _ = base.fixture()
    bundle = data['bundle']
    first, second = bundle['observations']
    second['response_id'], second['call_id'] = first['response_id'], first['call_id']
    second['source_time'] = '2026-01-01T00:00:00Z'
    second['observed_at'] = '2026-01-02T04:04:05Z'
    normalized = contract.normalize_source_counters(data['profile'], {'usage': {
        'input': 1100, 'read': 200, 'write': 200, 'short': 100, 'long': 100,
        'output': 100, 'reasoning': 25}}, profile_version='1', source_hash='a' * 64, record_number=2)
    for measurement in normalized['measurements'].values():
        parts = [item['tokens'] for item in measurement] if isinstance(measurement, list) else [measurement]
        for part in parts:
            if part['measurement_state'] == 'partial':
                part['measurement_state'] = 'final'
    second['measurements'] = normalized['measurements']
    bundle['evidence_objects'] = [item for item in bundle['evidence_objects']
                                  if item.get('record_number') != 2 and item['kind'] != 'inventory_evidence']
    bundle['evidence_objects'].extend(normalized['evidence_objects'])
    inventory = bundle['inventories'][0]
    inventory['expected_calls'] = [inventory['expected_calls'][0]]
    inventory['expected_responses'] = [inventory['expected_responses'][0]]
    inventory, inv_proof = base.inventories.bind(inventory)
    bundle['inventories'] = [inventory]
    bundle['evidence_objects'].append(inv_proof)
    first_context, second_context = data['contexts']
    first_context['observation_id'] = contract.observation_id(first)
    second_context['observation_id'] = contract.observation_id(second)
    first_context['event'] = {'kind': 'snapshot', 'final': correction, 'sequence': 1}
    second_context['event'] = {'kind': 'snapshot', 'final': True, 'sequence': 2}
    if correction:
        second_context['event']['correction_of'] = 'sha256:' + contract.observation_id(first)
    second_context['execution_time'] = '2026-01-01T00:00:00Z'
    for item in second_context['evidence_objects']:
        if item['kind'] == 'execution_time_evidence':
            item['value'] = second_context['execution_time']
    contract.validate_usage_bundle(bundle)
    return data, authorize(data)


def delta_fixture():
    profile = base.profiles.profile(False)
    profile['counter_fields'] = [entry for entry in profile['counter_fields']
                                 if entry['measurement'] in ('input_uncached', 'output_total')]
    for entry in profile['counter_fields']:
        entry['counter_scope'] = 'incremental_delta'
    profile['capabilities']['cache'] = 'unsupported'
    data, _ = base.fixture(profile_override=profile)
    bundle = data['bundle']
    first, second = bundle['observations']
    second['response_id'], second['call_id'] = first['response_id'], first['call_id']
    second['source_time'] = '2026-01-01T00:00:00Z'
    second['observed_at'] = '2026-01-02T04:04:05Z'
    bundle['evidence_objects'] = []
    for observation, values in ((first, (10, 1)), (second, (20, 2))):
        observation['counter_scope'] = 'incremental_delta'
        observation['measurements'] = {}
        for field, raw_field, value in (('input_uncached', 'input', values[0]), ('output_total', 'output', values[1])):
            proof = {'schema_version': 1, 'kind': 'measurement_evidence', 'profile_id': profile['profile_id'],
                     'source_hash': observation['source_hash'], 'record_number': observation['record_number'],
                     'field': field, 'value': value, 'path': ['usage', raw_field]}
            observation['measurements'][field] = {'measurement_state': 'partial', 'value': value,
                                                   'reasons': [], 'evidence': contract.content_id(proof)}
            bundle['evidence_objects'].append(proof)
    terminal = copy.deepcopy(second)
    terminal['record_number'] = 3
    terminal['observed_at'] = '2026-01-02T04:05:05Z'
    terminal['measurements'] = {'input_uncached': {'measurement_state': 'unavailable', 'reasons': ['source_unavailable']},
                                'output_total': {'measurement_state': 'unavailable', 'reasons': ['source_unavailable']}}
    bundle['observations'].append(terminal)
    first_context, second_context = data['contexts']
    terminal_context = copy.deepcopy(second_context)
    for index, (observation, context) in enumerate(zip(bundle['observations'],
                                                        (first_context, second_context, terminal_context)), 1):
        context.update(observation_id=contract.observation_id(observation), record_number=index,
                       counter_scope='incremental_delta', execution_time='2026-01-01T00:00:00Z')
        context['event'] = {'kind': 'delta' if index < 3 else 'terminal', 'sequence': index}
        for proof in context['evidence_objects']:
            if 'record_number' in proof:
                proof['record_number'] = index
            if proof['kind'] == 'execution_time_evidence':
                proof['value'] = context['execution_time']
    data['contexts'].append(terminal_context)
    inventory = bundle['inventories'][0]
    inventory['expected_calls'] = [inventory['expected_calls'][0]]
    inventory['expected_responses'] = [inventory['expected_responses'][0]]
    inventory, inv_proof = base.inventories.bind(inventory)
    bundle['inventories'] = [inventory]
    bundle['evidence_objects'].append(inv_proof)
    contract.validate_source_profile(profile)
    contract.validate_usage_bundle(bundle)
    return data, authorize(data)


class RevisionIntegrationTests(unittest.TestCase):
    def test_partial_snapshot_replaced_by_final_without_double_count(self):
        data, allowed = snapshot_fixture()
        result = base.resolve(data, base.Verifier(allowed))
        self.assertEqual(result['tokens']['input'], {'value': '1100', 'quality': 'complete'})
        self.assertEqual(result['tokens']['output'], {'value': '100', 'quality': 'complete'})
        self.assertEqual(result['completeness']['priced'], {'numerator': 1, 'denominator': 1})
        self.assertEqual(result['responses'][0]['model_cost']['cost_usd'], '0.00309')
        self.assertEqual(result['cost']['priced_subtotal_usd'], '0.00309')

    def test_verified_correction_replaces_old_final_and_untrusted_correction_conflicts(self):
        data, allowed = snapshot_fixture(correction=True)
        observation = data['bundle']['observations'][1]
        context = data['contexts'][1]
        untrusted = base.resolve(data, base.Verifier(allowed))
        self.assertNotEqual(untrusted['tokens']['input'].get('quality'), 'complete')
        self.assertNotIn('cost_usd', untrusted['responses'][0]['model_cost'])
        allowed.append(('revision', data['scope'], observation, context['event']))
        result = base.resolve(data, base.Verifier(allowed))
        self.assertEqual(result['tokens']['input'], {'value': '1100', 'quality': 'complete'})
        self.assertEqual(result['responses'][0]['model_cost']['cost_usd'], '0.00309')
        self.assertEqual(result['completeness']['priced'], {'numerator': 1, 'denominator': 1})

    def test_contiguous_deltas_and_terminal_are_summed_once(self):
        data, allowed = delta_fixture()
        result = base.resolve(data, base.Verifier(allowed))
        self.assertEqual(result['tokens']['input'], {'value': '30', 'quality': 'complete'})
        self.assertEqual(result['tokens']['output'], {'value': '3', 'quality': 'complete'})
        self.assertEqual(result['responses'][0]['model_cost']['cost_usd'], '0.00009')
        self.assertEqual(result['completeness']['finality'], {'numerator': 1, 'denominator': 1})

    def test_later_partial_snapshot_does_not_reuse_old_final_cost(self):
        data, _ = snapshot_fixture()
        data['contexts'][0]['event']['final'] = True
        data['contexts'][1]['event']['final'] = False
        result = base.resolve(data, base.Verifier(authorize(data)))
        self.assertNotEqual(result['tokens']['input'].get('quality'), 'complete')
        self.assertEqual(result['completeness']['finality']['numerator'], 0)
        self.assertTrue(all('cost_usd' not in item['model_cost'] for item in result['responses']))
        self.assertNotIn('cost_usd', result['cost'])

    def test_large_verified_delta_total_stays_exact_and_prices_without_rounding(self):
        data, _ = delta_fixture()
        maximum = 9007199254740991
        for observation in data['bundle']['observations'][:2]:
            measurement = observation['measurements']['input_uncached']
            proof = next(item for item in data['bundle']['evidence_objects']
                         if contract.content_id(item) == measurement['evidence'])
            proof['value'] = maximum
            measurement.update(value=maximum, evidence=contract.content_id(proof))
        for observation, context in zip(data['bundle']['observations'], data['contexts']):
            context['observation_id'] = contract.observation_id(observation)
        allowed = authorize(data)
        result = base.resolve(data, base.Verifier(allowed))
        self.assertEqual(result['tokens']['input'], {'value': '18014398509481982', 'quality': 'complete'})
        self.assertEqual(result['tokens']['output'], {'value': '3', 'quality': 'complete'})
        self.assertEqual(result['responses'][0]['model_cost']['cost_usd'], '36028797018.963994')

    def test_missing_delta_or_terminal_proof_cannot_be_final(self):
        data, _ = delta_fixture()
        data['contexts'][1]['event']['sequence'] = 3
        data['contexts'][2]['event']['sequence'] = 4
        allowed = authorize(data)
        result = base.resolve(data, base.Verifier(allowed))
        self.assertNotEqual(result['tokens']['input'].get('quality'), 'complete')
        self.assertTrue(all('cost_usd' not in item['model_cost'] for item in result['responses']))
        data, allowed = delta_fixture()
        allowed = [item for item in allowed if not (item[0] == 'context' and item[2]['record_number'] == 3)]
        result = base.resolve(data, base.Verifier(allowed))
        self.assertNotEqual(result['tokens']['input'].get('quality'), 'complete')
        self.assertTrue(all('cost_usd' not in item['model_cost'] for item in result['responses']))

    def test_snapshot_scope_cannot_be_reinterpreted_as_delta(self):
        data, _ = snapshot_fixture()
        data['contexts'][0]['event'] = {'kind': 'delta', 'sequence': 1}
        data['contexts'][1]['event'] = {'kind': 'terminal', 'sequence': 2}
        result = base.resolve(data, base.Verifier(authorize(data)))
        self.assertNotEqual(result['tokens']['input'].get('quality'), 'complete')
        self.assertTrue(all('cost_usd' not in item['model_cost'] for item in result['responses']))

    def test_delta_scope_cannot_be_reinterpreted_as_snapshot(self):
        data, _ = delta_fixture()
        data['contexts'][1]['event'] = {'kind': 'snapshot', 'final': True, 'sequence': 2}
        result = base.resolve(data, base.Verifier(authorize(data)))
        self.assertNotEqual(result['tokens']['input'].get('quality'), 'complete')
        self.assertTrue(all('cost_usd' not in item['model_cost'] for item in result['responses']))

    def test_stream_order_is_semantic_not_input_arrival(self):
        data, allowed = snapshot_fixture(correction=True)
        allowed.append(('revision', data['scope'], data['bundle']['observations'][1], data['contexts'][1]['event']))
        first = base.resolve(data, base.Verifier(allowed))
        data['bundle']['observations'].reverse()
        data['bundle']['evidence_objects'].reverse()
        data['contexts'].reverse()
        self.assertEqual(first, base.resolve(data, base.Verifier(allowed)))
        self.assertEqual(first['tokens']['input']['value'], '1100')


if __name__ == '__main__':
    unittest.main()
