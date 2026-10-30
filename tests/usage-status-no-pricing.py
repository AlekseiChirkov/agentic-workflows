#!/usr/bin/env python3
"""Token and coverage status remain observable when prices are unavailable."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('status_fixture', ROOT / 'tests/usage-status-integration.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class UnpricedStatusTests(unittest.TestCase):
    def test_verified_tokens_and_coverage_survive_missing_prices(self):
        snapshot, extra, allowed = fixture.inputs()
        extra.update(snapshots=[], scenario=None, price_evidence=[])
        selected = fixture.policy()
        selected['money_threshold'] = None
        result = fixture.alerts.evaluate_status(snapshot, selected, observed_at=fixture.NOW,
                    analysis_inputs=extra, verifier=fixture.resolution.Verifier(allowed))
        self.assertEqual(result['measurements']['tokens'], {'state': 'final', 'value': 2200, 'unit': 'tokens'})
        self.assertEqual(result['measurements']['completeness'], {'state': 'final', 'value': '1', 'unit': 'fraction'})
        self.assertEqual([item['metric'] for item in result['candidates']], ['tokens'])
        self.assertIn(result['measurements'].get('cost_usd', {}).get('state', 'unknown'), ('unknown', 'unpriced'))
        self.assertIsNone(result['measurements'].get('cost_usd', {}).get('value'))


if __name__ == '__main__':
    unittest.main()
