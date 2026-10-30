#!/usr/bin/env python3
"""Evidence-backed response terms and independent identity coverage."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class ReportEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = base.fixture()

    def report(self, allowed=None):
        return base.resolve(self.data, base.Verifier(self.allowed if allowed is None else allowed))

    def test_actual_terms_are_exact_unique_and_per_response(self):
        result = self.report()
        self.assertEqual(result['identity']['state'], 'complete')
        first, second = sorted(result['responses'], key=lambda row: row['identity']['id'])
        self.assertEqual(sorted(term['amount'] for term in first['terms']),
                         sorted(['0.0012', '0.00004', '0.00025', '0.0004', '0.001']))
        self.assertEqual(second['terms'], [])
        self.assertEqual(len({term['id'] for term in first['terms']}), 5)
        self.assertEqual(first['terms'], self.report()['responses'][0]['terms'])

    def test_missing_prices_remove_terms_without_losing_identity(self):
        result = self.report([item for item in self.allowed if item[0] != 'price'])
        self.assertEqual(result['identity']['state'], 'complete')
        self.assertTrue(all(not row['terms'] for row in result['responses']))

    def test_missing_measurements_do_not_conflate_identity_and_coverage(self):
        result = self.report([item for item in self.allowed if item[0] != 'measurement'])
        self.assertEqual(result['identity']['state'], 'complete')
        self.assertNotEqual(result['completeness']['measurements']['input']['numerator'], 2)
        self.assertTrue(all(not row['terms'] for row in result['responses']))

    def test_missing_context_or_inventory_does_not_prove_identity(self):
        for kind in ('context', 'inventory'):
            with self.subTest(kind=kind):
                result = self.report([item for item in self.allowed if item[0] != kind])
                self.assertNotEqual(result['identity']['state'], 'complete')
                if kind == 'context':
                    self.assertTrue(all(not row['terms'] for row in result['responses']))

    def test_reprice_terms_are_explicitly_conditional(self):
        self.data['scenario']['basis'] = 'reprice'
        result = self.report()
        terms = [term for row in result['responses'] for term in row['terms']]
        self.assertEqual(len(terms), 10)
        self.assertEqual(len({term['id'] for term in terms}), 10)
        self.assertTrue(all(term.get('conditional') is True for term in terms))


if __name__ == '__main__':
    unittest.main()
