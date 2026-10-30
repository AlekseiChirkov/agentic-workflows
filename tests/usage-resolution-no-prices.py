#!/usr/bin/env python3
"""Missing price inputs do not erase independently proven token usage."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)


class MissingPricesTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = integration.fixture()

    def assert_tokens_with_unknown_price(self):
        result = integration.resolve(self.data, integration.Verifier(self.allowed))
        self.assertEqual(result['tokens']['input'], {'value': '2000', 'quality': 'complete'})
        self.assertEqual(result['tokens']['output'], {'value': '200', 'quality': 'complete'})
        self.assertEqual(result['completeness']['finality'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(result['completeness']['priced'], {'numerator': 0, 'denominator': 2})
        self.assertNotIn('cost_usd', result['cost'])
        for response in result['responses']:
            self.assertNotIn('cost_usd', response['model_cost'])
            self.assertTrue(response['model_cost']['unpriced_ids'])

    def test_absent_scenario_and_snapshots_preserve_verified_token_totals(self):
        self.data.update(scenario=None, snapshots=[], price_evidence=[])
        self.assert_tokens_with_unknown_price()

    def test_scenario_without_selected_snapshots_remains_unpriced(self):
        self.data.update(snapshots=[], price_evidence=[])
        self.assert_tokens_with_unknown_price()

    def test_unknown_actual_model_does_not_use_scenario_model(self):
        for index, observation in enumerate(self.data['bundle']['observations']):
            previous = self.data['contexts'][index]
            context = copy.deepcopy(previous)
            context['parameters']['model'] = None
            context['evidence_objects'] = [proof for proof in context['evidence_objects']
                                           if proof.get('field') != 'model']
            self.data['contexts'][index] = context
            self.allowed = [item for item in self.allowed if not (
                item[0] == 'context' and item[2] == observation)]
            self.allowed.append(('context', self.data['scope'], observation, context))
        self.assert_tokens_with_unknown_price()

    def test_price_retrieved_after_cutoff_cannot_price_historical_work(self):
        snapshot = self.data['snapshots'][0]
        snapshot['retrieved_at'] = '2029-01-03T00:00:00Z'
        identity = integration.contract.price_snapshot_id(snapshot)
        self.data['scenario']['snapshot_ids'] = [identity]
        for proof in self.data['price_evidence']:
            if proof.get('kind') == 'price_snapshot_evidence':
                proof['snapshot_id'] = identity
        self.allowed = [item for item in self.allowed if item[0] != 'price']
        self.allowed.extend(('price', self.data['scope'], snapshot, proof)
                            for proof in self.data['price_evidence'])
        self.assert_tokens_with_unknown_price()

    def test_malformed_nonempty_price_input_is_rejected(self):
        self.data.update(snapshots=[{'raw': 'PRIVATE_SENTINEL'}], price_evidence=[])
        with self.assertRaises(ValueError) as caught:
            integration.resolve(self.data, integration.Verifier(self.allowed))
        self.assertNotIn('PRIVATE_SENTINEL', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
