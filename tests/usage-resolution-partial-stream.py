#!/usr/bin/env python3
"""Incomplete response streams retain independently verified partial measurements."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('revisions', ROOT / 'tests/usage-resolution-revisions.py')
revisions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revisions)
base, contract = revisions.base, revisions.contract


def partial_snapshots():
    data, _ = revisions.snapshot_fixture()
    for observation, context, number in zip(data['bundle']['observations'], data['contexts'], (1, 40)):
        measurement = observation['measurements']['output_total']
        proof = next(item for item in data['bundle']['evidence_objects']
                     if contract.content_id(item) == measurement['evidence'])
        proof['value'] = number
        measurement.update(value=number, measurement_state='partial', evidence=contract.content_id(proof))
        context['event']['final'] = False
        context['observation_id'] = contract.observation_id(observation)
    return data, revisions.authorize(data)


class PartialStreamTests(unittest.TestCase):
    def test_latest_snapshot_is_partial_and_never_added_or_finalized(self):
        data, allowed = partial_snapshots()
        result = base.resolve(data, base.Verifier(allowed))
        self.assertEqual(result['responses'][0]['tokens']['output'], {'value': '40', 'quality': 'partial'})
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])
        self.assertNotEqual(result['completeness']['measurements']['output']['numerator'], 1)
        data['bundle']['observations'].reverse()
        data['contexts'].reverse()
        self.assertEqual(base.resolve(data, base.Verifier(allowed))['responses'][0]['tokens']['output'],
                         {'value': '40', 'quality': 'partial'})

    def test_rejected_latest_measurement_is_not_published(self):
        data, allowed = partial_snapshots()
        allowed = [binding for binding in allowed if not (binding[0] == 'measurement'
                   and binding[2]['field'] == 'output_total' and binding[2]['observation']['record_number'] == 2)]
        result = base.resolve(data, base.Verifier(allowed))
        self.assertNotEqual(result['responses'][0]['tokens']['output'].get('value'), '40')
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])

    def test_deltas_without_terminal_are_preserved_as_partial(self):
        data, _ = revisions.delta_fixture()
        data['bundle']['observations'].pop()
        data['contexts'].pop()
        result = base.resolve(data, base.Verifier(revisions.authorize(data)))
        self.assertEqual(result['responses'][0]['tokens']['input'], {'value': '30', 'quality': 'partial'})
        self.assertEqual(result['responses'][0]['tokens']['output'], {'value': '3', 'quality': 'partial'})
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])

    def test_delta_gap_remains_partial_and_is_not_final(self):
        data, _ = revisions.delta_fixture()
        data['contexts'][1]['event']['sequence'] = 3
        data['contexts'][2]['event']['sequence'] = 4
        result = base.resolve(data, base.Verifier(revisions.authorize(data)))
        self.assertEqual(result['responses'][0]['tokens']['input'], {'value': '30', 'quality': 'partial'})
        self.assertEqual(result['responses'][0]['tokens']['output'], {'value': '3', 'quality': 'partial'})
        self.assertNotIn('cost_usd', result['responses'][0]['model_cost'])

    def test_final_snapshot_supersedes_partials_without_addition(self):
        data, allowed = revisions.snapshot_fixture()
        result = base.resolve(data, base.Verifier(allowed))
        self.assertEqual(result['responses'][0]['tokens']['output'], {'value': '100', 'quality': 'complete'})


if __name__ == '__main__':
    unittest.main()
