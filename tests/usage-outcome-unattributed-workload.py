#!/usr/bin/env python3
"""Never call a selected workload complete when responses lack attempt attribution."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tests' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


evidence = load('evidence', 'usage-report-evidence-fields.py')
outcomes = load('outcomes', 'usage-retrospective-outcome-timing.py')


class UnattributedWorkloadTests(unittest.TestCase):
    def setUp(self):
        self.fixture = evidence.EvidenceBackedReportTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.scope = self.fixture.scope
        identity = outcomes.opportunity(1)
        selected = {'schema_version': 1, 'kind': 'outcome_opportunity', 'identity': identity,
                    'observed_at': '2028-01-01T00:00:00Z'}
        self.add('opportunity', 'outcome_opportunity', selected)
        accepted = {'schema_version': 1, 'kind': 'acceptance_revision', 'opportunity': identity,
                    'status': 'accepted', 'revision': 1, 'observed_at': '2028-01-02T00:00:00Z',
                    'acceptance_contract': 'contract-v1', 'evaluator_id': 'sha256:' + 'a' * 64,
                    'evidence_id': 'sha256:' + 'b' * 64}
        self.add('acceptance', 'acceptance_revision', accepted)
        self.attempts = []
        for number in (1, 2):
            attempt = {'schema_version': 1, 'kind': 'outcome_attempt', 'attempt_id': 'attempt-' + str(number),
                       'opportunity': identity, 'response_ids': ['sha256:' + str(number) * 64],
                       'category': 'workload', 'complete': True, 'observed_at': '2028-01-02T00:00:00Z'}
            self.attempts.append(self.add('attempt-' + str(number), 'outcome_attempt', attempt))

    def add(self, name, kind, record):
        self.fixture.add(name, kind, record)
        self.fixture.authorize(kind, self.scope, record, record)
        return self.fixture.base.manifest['inputs'][-1]

    def test_unattributed_priced_response_cannot_disappear_from_complete_workload(self):
        full = self.fixture.analyze()
        self.assertEqual(full['totals']['total_cost'], '0.00578')
        self.assertEqual(full['outcomes']['observed_workload_cost'], '0.00578')
        self.assertEqual(full['outcomes']['coverage'], 'complete')
        self.fixture.base.manifest['inputs'].remove(self.attempts[1])
        partial = self.fixture.analyze()
        self.assertEqual(partial['totals']['total_cost'], '0.00578')
        self.assertEqual(partial['outcomes']['accepted_count'], 1)
        result = partial['outcomes']
        if result['observed_workload_cost'] != '0.00578':
            self.assertEqual(result['coverage'], 'incomplete')
            self.assertNotEqual(result['ratio_quality'], 'complete')
        self.assertNotEqual(full['corpus_id'], partial['corpus_id'])


if __name__ == '__main__':
    unittest.main()
