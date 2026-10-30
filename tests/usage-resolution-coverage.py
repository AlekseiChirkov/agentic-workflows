#!/usr/bin/env python3
"""Independent finality, historical inventory and cost-bound evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = integration.fixture()

    def report(self, allowed=None):
        result = integration.resolve(self.data, integration.Verifier(self.allowed if allowed is None else allowed))
        self.assertIsInstance(result, dict)
        return result

    def test_proven_lower_bound_requires_nonnegative_excluded_scope(self):
        positive = self.report()
        self.assertEqual(positive['cost']['subtotal_quality'], 'proven_lower_bound')
        untrusted = [item for item in self.allowed if item[0] != 'nonnegative_scope']
        negative = self.report(untrusted)
        self.assertEqual(negative['cost']['subtotal_quality'], 'subtotal_only')
        self.assertNotIn('cost_usd', negative['cost'])

    def test_finality_follows_authorized_terminal_event_not_measurement_availability(self):
        missing_measurements = [item for item in self.allowed if item[0] != 'measurement']
        result = self.report(missing_measurements)
        self.assertEqual(result['completeness']['finality'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(result['completeness']['measurements']['input']['numerator'], 0)
        self.assertEqual(result['completeness']['measurements']['output']['numerator'], 0)
        no_terminal = [item for item in missing_measurements if item[0] != 'context']
        unverified = self.report(no_terminal)
        self.assertEqual(unverified['completeness']['finality']['numerator'], 0)

    def test_future_inventory_cannot_establish_historical_denominator(self):
        self.data['as_of'] = '2028-12-31T23:59:59Z'
        result = self.report()
        self.assertIsNone(result['completeness']['finality']['denominator'])
        self.assertIsNone(result['completeness']['priced']['denominator'])
        self.assertNotIn('cost_usd', result['cost'])

    def test_nonboolean_or_untrusted_scope_claim_cannot_prove_lower_bound(self):
        allowed = [item for item in self.allowed if item[0] != 'nonnegative_scope']
        verifier = integration.Verifier(allowed)
        def claims(kind, scope, subject, evidence):
            if kind == 'nonnegative_scope':
                return {'verified': True}
            return verifier(kind, scope, subject, evidence)
        result = integration.resolve(self.data, claims)
        self.assertEqual(result['cost']['subtotal_quality'], 'subtotal_only')


if __name__ == '__main__':
    unittest.main()
