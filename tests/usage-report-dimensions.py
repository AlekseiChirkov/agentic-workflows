#!/usr/bin/env python3
"""Exercise independently authorized dimensions over actual priced responses."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract
import usage_telemetry_exports as exports

spec = importlib.util.spec_from_file_location('report_evidence', ROOT / 'tests/usage-report-evidence-fields.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class ReportDimensionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.EvidenceBackedReportTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.scope = self.fixture.scope
        self.dimensions = {name: 'sha256:' + char * 64 for name, char in zip(
            ('run', 'opportunity', 'root_approach', 'stage', 'role', 'effort', 'attempt'), 'abcdef0')}
        self.records = []
        for number, observation in enumerate(self.fixture.base.data['bundle']['observations']):
            value = {'schema_version': 1, 'kind': 'dimension_evidence', 'scope': self.scope,
                     'observation_id': contract.observation_id(observation),
                     'dimensions': copy.deepcopy(self.dimensions), 'observed_at': '2028-01-03T00:00:00Z'}
            self.records.append(value)
            self.fixture.add('dimension-' + str(number), 'dimension_evidence', value)
            self.fixture.authorize('dimension_evidence', self.scope, value, value)
            self.fixture.authorize('dimension_privacy', self.scope, value, value)

    def test_verified_dimensions_include_actual_component_totals(self):
        report = self.fixture.analyze()
        self.assertEqual(report['coverage']['pricing'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['totals']['total_cost'], '0.00578')
        for dimension, identity in self.dimensions.items():
            row = next(item for item in report['slices'] if item['dimension'] == dimension and item['value'] == identity)
            self.assertEqual(row['count'], 2)
            self.assertEqual(row['request_count'], 2)
            self.assertEqual(row['input_uncached_tokens'], '1200')
            self.assertEqual(row['input_cache_read_tokens'], '400')
            self.assertEqual(row['input_cache_write_tokens'], '400')
            self.assertEqual(row['output_tokens'], '200')
            self.assertEqual(row['reasoning_tokens'], '50')
            self.assertIsNone(row['retry_count'])
            self.assertIsNone(row['escalation_count'])
            self.assertIsNone(row['wall_ms'])
            self.assertEqual(row['cost_usd'], '0.00578')
        for output in exports.render_exports(report).values():
            self.assertIn('1200', output)
            self.assertIn('input_cache_read_tokens', output)

    def test_untrusted_or_private_dimensions_are_unknown(self):
        positive = self.fixture.analyze()
        self.assertTrue(any(item['dimension'] == 'role' for item in positive['slices']))
        self.fixture.base.authority.allowed = [entry for entry in self.fixture.base.authority.allowed
                                               if entry[0] not in ('dimension_privacy', 'dimension_evidence')]
        denied = self.fixture.analyze()
        self.assertFalse(any(item['dimension'] in self.dimensions for item in denied['slices']))
        self.assertTrue(set(self.dimensions) <= set(denied['unavailable_dimensions']))
        for output in exports.render_exports(denied).values():
            for identity in self.dimensions.values():
                self.assertNotIn(identity, output)
        self.assertNotEqual(positive['corpus_id'], denied['corpus_id'])


if __name__ == '__main__':
    unittest.main()
