#!/usr/bin/env python3
"""Integration regressions for incomplete tool spend and duplicate revisions."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)
contract = integration.contract


class ResolutionRegressionTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = integration.fixture()

    def test_complete_model_prices_do_not_prove_absence_of_tool_expenses(self):
        snapshot = self.data['snapshots'][0]
        period = self.data['price_evidence'][0]
        period['end'] = '2029-01-01T00:00:00Z'
        snapshot['effective_period']['end'] = period['end']
        snapshot['effective_period']['evidence'] = contract.content_id(period)
        snapshot_id = contract.price_snapshot_id(snapshot)
        self.data['scenario']['snapshot_ids'] = [snapshot_id]
        binding = self.data['price_evidence'][1]
        binding['snapshot_id'] = snapshot_id
        self.allowed = [item for item in self.allowed if item[0] != 'price']
        self.allowed.extend(('price', self.data['scope'], snapshot, proof)
                            for proof in self.data['price_evidence'])
        result = integration.resolve(self.data, integration.Verifier(self.allowed))
        self.assertIsInstance(result, dict)
        self.assertEqual(result['completeness']['priced'], {'numerator': 2, 'denominator': 2})
        self.assertNotIn('cost_usd', result['cost'])

    def test_duplicate_finals_with_different_record_context_are_not_priced_by_arrival(self):
        original = self.data['bundle']['observations'][0]
        duplicate = copy.deepcopy(original)
        duplicate['observed_at'] = '2026-01-02T04:04:05Z'
        self.data['bundle']['observations'].append(duplicate)
        source_context = self.data['contexts'][0]
        context = copy.deepcopy(source_context)
        context['observation_id'] = contract.observation_id(duplicate)
        context['parameters']['model'] = 'vendor/other'
        for proof in context['evidence_objects']:
            if proof.get('kind') == 'source_parameter_evidence' and proof.get('field') == 'model':
                proof['value'] = 'vendor/other'
        self.data['contexts'].append(context)
        self.allowed.append(('context', self.data['scope'], duplicate, context))
        self.allowed.append(('response_privacy', self.data['scope'], duplicate, duplicate))
        for proof in context['evidence_objects']:
            self.allowed.append(('pricing_context', self.data['scope'], duplicate, proof))
        for kind, scope, subject, proof in list(self.allowed):
            if kind == 'measurement' and subject['observation'] == original:
                self.allowed.append((kind, scope, subject | {'observation': duplicate}, proof))
        result = integration.resolve(self.data, integration.Verifier(self.allowed))
        self.assertIsInstance(result, dict)
        self.assertEqual(result['completeness']['priced']['numerator'], 0)
        self.assertNotIn('cost_usd', result['cost'])
        self.assertNotEqual(result['cost'].get('subtotal_quality'), 'proven_lower_bound')


if __name__ == '__main__':
    unittest.main()
