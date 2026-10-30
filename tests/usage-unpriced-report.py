#!/usr/bin/env python3
"""Retrospective reports do not present an empty priced set as zero spend."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('report_fixtures', ROOT / 'tests/usage-resolved-report-integration.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class UnpricedReportTests(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.ResolvedReportTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)

    def assert_priced_control(self):
        positive = self.base.analyze()
        self.assertEqual(positive['pricing']['priced_subtotal_cost'], '0.00289')
        self.assertEqual(positive['coverage']['pricing'], {'numerator': 1, 'denominator': 2})
        return positive

    def assert_unavailable(self, report, positive):
        self.assertEqual(report['coverage']['pricing'], {'numerator': 0, 'denominator': 2})
        self.assertIsNone(report['totals']['total_cost'])
        self.assertIsNone(report['pricing']['priced_subtotal_cost'])
        self.assertEqual(report['pricing']['subtotal_quality'], 'unavailable')
        self.assertNotEqual(report['corpus_id'], positive['corpus_id'])

    def test_unselected_price_evidence_cannot_produce_a_zero_subtotal(self):
        positive = self.assert_priced_control()
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
                                       if item['kind'] != 'price_evidence']
        self.assert_unavailable(self.base.analyze(), positive)

    def test_untrusted_price_evidence_cannot_produce_a_zero_subtotal(self):
        positive = self.assert_priced_control()
        self.base.authority.allowed = [item for item in self.base.authority.allowed if item[0] != 'price']
        self.assert_unavailable(self.base.analyze(), positive)


if __name__ == '__main__':
    unittest.main()
