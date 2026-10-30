#!/usr/bin/env python3
"""Warnings use only the completeness of their own scope."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('duration_fixture', ROOT / 'tests/usage-status-duration-integration.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
alerts = fixture.fixture.alerts


class ScopedCompletenessTests(unittest.TestCase):
    def evaluate(self, kind, coverage):
        snapshot, allowed = fixture.time_only()
        owner = snapshot['owner_scope']
        target = {'owner_kind': kind, 'owner_id': 'sha256:' + 'e' * 64}
        entry = snapshot['duration_inputs'][0]
        entry['scope'] = target
        entry['candidate']['id'] = target['owner_id']
        entry['evidence']['candidate_id'] = target['owner_id']
        entry['evidence']['scope'] = target
        allowed = [('duration', owner, entry['candidate'], entry['evidence'])]
        if kind == 'request':
            snapshot.pop('duration_inputs')
            allowed = []
        metrics = {'tokens': {'state': 'proven_lower_bound', 'value': 1100, 'unit': 'tokens'}}
        if coverage is not None:
            metrics['completeness'] = {'state': 'final', 'value': coverage, 'unit': 'fraction'}
        analysis = {'scope': owner, 'metrics': {'completeness': {'state': 'final', 'value': '0.9', 'unit': 'fraction'}},
                    'scoped_metrics': [{'scope': target, 'owner_scope': owner, 'membership': 'verified', 'metrics': metrics}]}
        policy = fixture.fixture.policy()
        policy['scope'] = kind
        policy['money_threshold'] = None
        with patch.object(alerts, '_evaluate_snapshot', return_value=analysis):
            return alerts.evaluate_status(snapshot, policy, observed_at=fixture.NOW,
                                           verifier=fixture.fixture.resolution.Verifier(allowed))

    def test_distinct_and_unknown_scope_completeness(self):
        for kind in ('request', 'span'):
            for coverage in ('0.4', None):
                with self.subTest(kind=kind, coverage=coverage):
                    result = self.evaluate(kind, coverage)
                    expected = ({'state': 'final', 'value': coverage, 'unit': 'fraction'} if coverage is not None else
                                {'state': 'unknown', 'value': None, 'unit': 'fraction'})
                    for metric in (('tokens', 'duration_ms') if kind == 'span' else ('tokens',)):
                        warning = next(item for item in result['candidates'] if item['metric'] == metric)
                        self.assertEqual(warning['details']['completeness'], expected)


if __name__ == '__main__':
    unittest.main()
