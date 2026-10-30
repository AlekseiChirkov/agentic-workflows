#!/usr/bin/env python3
"""Verified corrections must not combine measurements from incompatible snapshots."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('revisions', ROOT / 'tests/usage-resolution-revisions.py')
revisions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revisions)
base, contract = revisions.base, revisions.contract


class CorrectionOrderTests(unittest.TestCase):
    def test_reverse_sequence_correction_cannot_mix_old_final_measurements(self):
        data, _ = revisions.snapshot_fixture(correction=True)
        first, correction = data['bundle']['observations']
        data['contexts'][0]['event']['sequence'] = 2
        data['contexts'][1]['event']['sequence'] = 1
        correction['measurements']['output_total'] = {'measurement_state': 'unavailable', 'reasons': ['source_unavailable']}
        data['contexts'][1]['observation_id'] = contract.observation_id(correction)
        allowed = revisions.authorize(data)
        allowed.append(('revision', data['scope'], correction, data['contexts'][1]['event']))
        result = base.resolve(data, base.Verifier(allowed))
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])
        self.assertNotEqual(result['tokens']['output'].get('quality'), 'complete')
        self.assertEqual(result['completeness']['priced']['numerator'], 0)

    def test_correctly_ordered_incomplete_correction_does_not_inherit_old_output(self):
        data, _ = revisions.snapshot_fixture(correction=True)
        correction = data['bundle']['observations'][1]
        correction['measurements']['output_total'] = {'measurement_state': 'unavailable', 'reasons': ['source_unavailable']}
        data['contexts'][1]['observation_id'] = contract.observation_id(correction)
        allowed = revisions.authorize(data)
        allowed.append(('revision', data['scope'], correction, data['contexts'][1]['event']))
        result = base.resolve(data, base.Verifier(allowed))
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])
        self.assertNotEqual(result['tokens']['output'].get('quality'), 'complete')


if __name__ == '__main__':
    unittest.main()
