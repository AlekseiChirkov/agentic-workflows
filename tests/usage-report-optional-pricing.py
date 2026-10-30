#!/usr/bin/env python3
"""Retrospective tokens remain available without a selected price basis."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from usage_telemetry_exports import render_exports

spec = importlib.util.spec_from_file_location('report_fixtures', ROOT / 'tests/usage-resolved-report-integration.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class OptionalPricingReportTests(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.ResolvedReportTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)

    def test_verified_tokens_survive_absent_price_inputs(self):
        priced = self.base.analyze()
        self.assertEqual(priced['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
            if item['kind'] not in ('pricing_scenario', 'price_snapshot', 'price_evidence')]
        report = self.base.analyze()
        self.assertNotEqual(report['corpus_id'], priced['corpus_id'])
        self.assertEqual(report['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['completeness']['measurements'], 'complete')
        tokens = {item['name']: item for item in report['metrics']}
        self.assertEqual(tokens['input_tokens']['value'], '2000')
        self.assertEqual(tokens['output_tokens']['value'], '200')
        self.assertEqual(tokens['input_tokens']['quality'], 'complete')
        self.assertIsNone(report['totals']['total_cost'])
        self.assertNotEqual(report['completeness']['pricing'], 'complete')
        rendered = render_exports(report)
        self.assertTrue(all('2000' in artifact and '200' in artifact for artifact in rendered.values()))

    def test_foreign_or_unverified_context_never_becomes_known_tokens(self):
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
            if item['kind'] not in ('pricing_scenario', 'price_snapshot', 'price_evidence')]
        positive = self.base.analyze()
        self.assertEqual(positive['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.base.authority.allowed = [item for item in self.base.authority.allowed if item[0] != 'context']
        report = self.base.analyze()
        self.assertNotEqual(report['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.assertIsNone(report['totals']['total_cost'])
        self.assertNotEqual(report['corpus_id'], positive['corpus_id'])


if __name__ == '__main__':
    unittest.main()
