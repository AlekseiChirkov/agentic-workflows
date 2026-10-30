#!/usr/bin/env python3
"""Unknown rates never become a free independently accepted result."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract

spec = importlib.util.spec_from_file_location('outcome_fixtures', ROOT / 'tests/usage-retrospective-outcome-timing.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class UnpricedAcceptedOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.RetrospectiveOutcomeTimingTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)

    def test_fully_unpriced_accepted_work_is_unknown_not_zero(self):
        positive = self.base.analyze()
        self.assertEqual(positive['outcomes']['observed_workload_cost'], '1.5')
        self.assertEqual(positive['outcomes']['accepted_count'], 1)
        # Remove only the selected attempt containing the priced response. The
        # independently verified resumed attempt still references the second,
        # unpriced response in the same opportunity.
        kept = []
        for item in self.base.base.manifest['inputs']:
            if item['kind'] == 'outcome_attempt':
                record = contract.parse_json(Path(item['local_path']).read_bytes())
                if record['attempt_id'] == 'failed':
                    continue
            kept.append(item)
        self.base.base.manifest['inputs'] = kept
        report = self.base.analyze()
        summary = report['outcomes']
        self.assertEqual(summary['accepted_count'], 1)
        self.assertIsNone(summary['observed_workload_cost'])
        self.assertIsNone(summary['cost_per_accepted'])
        self.assertEqual(summary['ratio_quality'], 'unavailable')
        self.assertNotEqual(report['corpus_id'], positive['corpus_id'])


if __name__ == '__main__':
    unittest.main()
