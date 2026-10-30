#!/usr/bin/env python3
"""End-to-end token totals with independently authorized measurements."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)


class TokenTotalsTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = integration.fixture()

    def report(self, allowed=None):
        verifier = integration.Verifier(self.allowed if allowed is None else allowed)
        return integration.resolve(self.data, verifier)

    def test_complete_input_and_output_have_nonoverlapping_exact_totals(self):
        report = self.report()
        self.assertEqual(report['tokens']['input'], {'value': '2000', 'quality': 'complete'})
        self.assertEqual(report['tokens']['output'], {'value': '200', 'quality': 'complete'})

    def test_missing_one_source_operand_cannot_complete_input(self):
        allowed = [item for item in self.allowed if not (
            item[0] == 'measurement' and item[2]['field'] == 'input_total' and
            item[2]['observation']['record_number'] == 2)]
        report = self.report(allowed)
        self.assertEqual(report['tokens']['input'], {'value': '1000', 'quality': 'proven_lower_bound'})
        self.assertEqual(report['tokens']['output'], {'value': '200', 'quality': 'complete'})

    def test_unknown_inventory_cannot_justify_complete_token_coverage(self):
        allowed = [item for item in self.allowed if item[0] != 'inventory']
        report = self.report(allowed)
        self.assertEqual(report['tokens']['input'], {'value': '2000', 'quality': 'proven_lower_bound'})
        self.assertEqual(report['tokens']['output'], {'value': '200', 'quality': 'proven_lower_bound'})

    def test_large_derived_totals_are_canonical_decimal_strings(self):
        maximum = 9007199254740991
        self.data, self.allowed = integration.fixture({'input': maximum, 'read': 0, 'write': 0,
                                                       'short': 0, 'long': 0, 'output': maximum,
                                                       'reasoning': 0})
        report = self.report()
        self.assertEqual(report['tokens']['input'], {'value': '18014398509481982', 'quality': 'complete'})
        self.assertEqual(report['tokens']['output'], {'value': '18014398509481982', 'quality': 'complete'})

    def test_unavailable_evidence_is_not_zero(self):
        allowed = [item for item in self.allowed if item[0] != 'measurement']
        report = self.report(allowed)
        self.assertEqual(report['tokens']['input'], {'quality': 'unavailable'})
        self.assertEqual(report['tokens']['output'], {'quality': 'unavailable'})


if __name__ == '__main__':
    unittest.main()
