#!/usr/bin/env python3
"""Empty and unpriced lifecycle projections do not invent price snapshots."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('states', ROOT / 'tests/usage-lifecycle-projection-states.py')
states = importlib.util.module_from_spec(spec)
spec.loader.exec_module(states)
contract = states.contract


class ProjectionWithoutPricesTests(unittest.TestCase):
    def test_proven_empty_scope_needs_no_price_scenario(self):
        value = states.empty_projection()
        value['price_snapshots'] = []
        value['scenario'] = None
        self.assertEqual(contract.validate_lifecycle_projection(value), value)
        bad = copy.deepcopy(value)
        bad['cost_usd'] = '0.01'
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(bad)

    def test_fully_unpriced_work_needs_no_fabricated_snapshot(self):
        value = states.unpriced_projection()
        value['price_snapshots'] = []
        value['scenario'] = None
        for contributor in value['contributors']:
            contributor['price_snapshot_id'] = None
            contributor['priced_usd'] = None
        del value['priced_subtotal_usd']
        del value['subtotal_quality']
        self.assertEqual(contract.validate_lifecycle_projection(value), value)
        bad = copy.deepcopy(value)
        bad['cost_usd'] = '0'
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(bad)
        bad = copy.deepcopy(value)
        bad['contributors'][0]['priced_usd'] = '0'
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(bad)

    def test_all_unpriced_work_cannot_claim_zero_priced_subtotal(self):
        value = states.unpriced_projection()
        for contributor in value['contributors']:
            contributor['price_snapshot_id'] = None
            contributor['priced_usd'] = None
        value.update(priced_subtotal_usd='0', subtotal_quality='subtotal_only')
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(value)
        self.assertEqual(contract.validate_lifecycle_projection(states.empty_projection())['cost_usd'], '0')

    def test_scenario_and_snapshots_must_be_consistent(self):
        value = states.unpriced_projection()
        value['scenario'] = None
        for contributor in value['contributors']:
            contributor['price_snapshot_id'] = None
            contributor['priced_usd'] = None
        value.pop('priced_subtotal_usd')
        value.pop('subtotal_quality')
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(value)


if __name__ == '__main__':
    unittest.main()
