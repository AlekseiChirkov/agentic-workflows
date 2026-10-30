#!/usr/bin/env python3
"""Scoped reprice, per-response thresholds, and independently verified aliases."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
contract = base.contract


def bind_snapshot(data, allowed):
    snapshot = data['snapshots'][0]
    identity = contract.price_snapshot_id(snapshot)
    data['scenario']['snapshot_ids'] = [identity]
    for proof in data['price_evidence']:
        if proof['kind'] == 'price_snapshot_evidence':
            proof['snapshot_id'] = identity
    allowed[:] = [item for item in allowed if item[0] != 'price']
    for proof in data['price_evidence']:
        if proof['kind'] != 'model_alias_evidence':
            allowed.append(('price', data['scope'], snapshot, proof))


class ConditionalPricingTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = base.fixture()

    def report(self, allowed=None):
        return base.resolve(self.data, base.Verifier(self.allowed if allowed is None else allowed))

    def test_derived_operand_uses_threshold_for_each_response_not_run_total(self):
        snapshot = self.data['snapshots'][0]
        high = copy.deepcopy(snapshot['rates'][0])
        high['usd'] = '3'
        high['threshold'] = {'operand': 'input_uncached', 'operator': '>', 'value': 600}
        snapshot['rates'].append(high)
        self.data['scenario']['threshold_rules'] = [{'operand': 'input_uncached', 'operator': '>',
                                                     'value': 600, 'components': ['input_uncached']}]
        bind_snapshot(self.data, self.allowed)
        result = self.report()
        self.assertEqual(result['responses'][0]['model_cost']['cost_usd'], '0.00289')
        snapshot['rates'][-1]['threshold']['value'] = 599
        self.data['scenario']['threshold_rules'][0]['value'] = 599
        bind_snapshot(self.data, self.allowed)
        result = self.report()
        self.assertEqual(result['responses'][0]['model_cost']['cost_usd'], '0.00349')
        self.assertEqual(result['completeness']['priced'], {'numerator': 1, 'denominator': 2})

    def test_unverified_source_operand_does_not_select_threshold_rate(self):
        snapshot = self.data['snapshots'][0]
        high = copy.deepcopy(snapshot['rates'][0])
        high.update(usd='3', threshold={'operand': 'input_uncached', 'operator': '>', 'value': 599})
        snapshot['rates'].append(high)
        self.data['scenario']['threshold_rules'] = [{'operand': 'input_uncached', 'operator': '>',
                                                     'value': 599, 'components': ['input_uncached']}]
        bind_snapshot(self.data, self.allowed)
        allowed = [item for item in self.allowed if not (item[0] == 'measurement' and
                   item[2]['field'] == 'input_total' and item[2]['observation']['record_number'] == 1)]
        result = self.report(allowed)
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])
        self.assertNotIn('cost_usd', result['cost'])

    def test_alias_requires_independent_exact_mapping_and_source(self):
        snapshot = self.data['snapshots'][0]
        snapshot['model'] = 'vendor/canonical'
        proof = {'schema_version': 1, 'kind': 'model_alias_evidence', 'source_hash': 'b' * 64,
                 'alias': 'vendor/model', 'model': 'vendor/canonical'}
        snapshot['aliases'] = [{'alias': proof['alias'], 'evidence': contract.content_id(proof)}]
        self.data['price_evidence'].append(proof)
        bind_snapshot(self.data, self.allowed)
        self.allowed.append(('alias', self.data['scope'], snapshot, proof))
        self.assertEqual(contract.validate_evidence_object(proof), proof)
        self.assertEqual(self.report()['responses'][0]['model_cost']['cost_usd'], '0.00289')
        untrusted = [item for item in self.allowed if item[0] != 'alias']
        result = self.report(untrusted)
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])
        self.assertEqual(result['tokens']['input']['value'], '2000')
        forged = copy.deepcopy(proof)
        forged['model'] = 'vendor/other'
        self.data['price_evidence'][-1] = forged
        snapshot['aliases'][0]['evidence'] = contract.content_id(forged)
        bind_snapshot(self.data, self.allowed)
        self.allowed.append(('alias', self.data['scope'], snapshot, forged))
        result = self.report()
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])

    def test_multiplier_needs_per_record_provenance_not_general_price_authority(self):
        snapshot = self.data['snapshots'][0]
        rate = snapshot['rates'][0]
        rate['multiplier'] = {'state': 'known', 'factor': '1.25', 'scope': 'tier'}
        bind_snapshot(self.data, self.allowed)
        proof = {'schema_version': 1, 'kind': 'multiplier_evidence',
                 'snapshot_id': contract.price_snapshot_id(snapshot), 'rate_id': contract.content_id(rate),
                 'scope': 'tier', 'factor': '1.25', 'applies': True,
                 'profile_id': self.data['profile']['profile_id'], 'source_hash': 'a' * 64, 'record_number': 1}
        self.data['price_evidence'].append(proof)
        self.allowed.append(('price', self.data['scope'], snapshot, proof))
        result = self.report()
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])
        self.allowed.append(('pricing_context', self.data['scope'], self.data['bundle']['observations'][0], proof))
        result = self.report()
        self.assertEqual(result['responses'][0]['model_cost']['cost_usd'], '0.00319')
        other = [item for item in self.allowed if not (item[0] == 'pricing_context' and item[3] == proof)]
        result = self.report(other)
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])

    def test_explicit_reprice_is_conditional_and_never_a_historical_total(self):
        snapshot = self.data['snapshots'][0]
        snapshot['effective_period'] = {'state': 'unknown', 'reason': 'historical_period_unavailable'}
        self.data['scenario']['basis'] = 'reprice'
        self.data['scenario']['assumptions'] = {'region': 'example-region'}
        self.data['scenario']['source_parameters']['region'] = None
        bind_snapshot(self.data, self.allowed)
        result = self.report()
        self.assertEqual(result['completeness']['priced'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(result['cost']['priced_subtotal_usd'], '0.00578')
        self.assertIs(result['cost']['conditional'], True)
        self.assertTrue(all(item['model_cost']['conditional'] is True for item in result['responses']))
        self.assertNotIn('cost_usd', result['cost'])

    def test_owned_reprice_is_also_marked_conditional(self):
        spec = importlib.util.spec_from_file_location('ownership_fixture', ROOT / 'tests/usage-resolution-ownership.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fixture = module.OwnershipIntegrationTests(methodName='test_shared_parent_pool_is_counted_once_without_leaf_allocation')
        fixture.setUp()
        fixture.data['scenario']['basis'] = 'reprice'
        result = fixture.report()
        parent = fixture.scopes(result)[module.PARENT]
        self.assertEqual(parent['model_cost']['cost_usd'], '0.00578')
        self.assertIs(parent['model_cost']['conditional'], True)
        self.assertIs(result['cost']['conditional'], True)

    def test_reprice_cannot_assume_or_guess_the_actual_model(self):
        snapshot = self.data['snapshots'][0]
        snapshot['effective_period'] = {'state': 'unknown', 'reason': 'historical_period_unavailable'}
        self.data['scenario']['basis'] = 'reprice'
        self.data['scenario']['assumptions'] = {'region': 'example-region'}
        bind_snapshot(self.data, self.allowed)
        for index, observation in enumerate(self.data['bundle']['observations']):
            context = copy.deepcopy(self.data['contexts'][index])
            context['parameters']['model'] = None
            context['evidence_objects'] = [proof for proof in context['evidence_objects'] if proof.get('field') != 'model']
            self.data['contexts'][index] = context
            self.allowed = [item for item in self.allowed if not (item[0] == 'context' and item[2] == observation)]
            self.allowed.append(('context', self.data['scope'], observation, context))
            self.allowed.append(('response_privacy', self.data['scope'], observation, observation))
        result = self.report()
        self.assertEqual(result['tokens']['input']['value'], '2000')
        self.assertEqual(result['completeness']['priced'], {'numerator': 0, 'denominator': 2})
        self.assertTrue(all('cost_usd' not in item['model_cost'] for item in result['responses']))


if __name__ == '__main__':
    unittest.main()
