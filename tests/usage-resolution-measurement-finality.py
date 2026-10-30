#!/usr/bin/env python3
"""Measurement finality must not be inferred from a final snapshot alone."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('revisions', ROOT / 'tests/usage-resolution-revisions.py')
revisions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revisions)
base, contract = revisions.base, revisions.contract


class MeasurementFinalityTests(unittest.TestCase):
    def test_final_snapshot_with_partial_input_cannot_produce_complete_input_or_cost(self):
        data, _ = revisions.snapshot_fixture()
        observation = data['bundle']['observations'][1]
        observation['measurements']['input_uncached']['measurement_state'] = 'partial'
        data['contexts'][1]['observation_id'] = contract.observation_id(observation)
        result = base.resolve(data, base.Verifier(revisions.authorize(data)))
        self.assertNotEqual(result['tokens']['input'].get('quality'), 'complete')
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])
        self.assertEqual(result['completeness']['measurements']['input']['numerator'], 0)

    def test_verified_delta_parts_can_be_finalized_by_terminal(self):
        data, allowed = revisions.delta_fixture()
        result = base.resolve(data, base.Verifier(allowed))
        self.assertEqual(result['tokens']['input'], {'value': '30', 'quality': 'complete'})
        self.assertEqual(result['responses'][0]['model_cost']['cost_usd'], '0.00009')


if __name__ == '__main__':
    unittest.main()
