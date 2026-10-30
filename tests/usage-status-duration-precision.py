#!/usr/bin/env python3
"""Exact milliseconds and independent current-owner duration intervals."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('duration_fixture', ROOT / 'tests/usage-status-duration-integration.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class PreciseDurationStatusTests(unittest.TestCase):
    def test_fractional_second_crossing_preserves_exact_milliseconds(self):
        snapshot, allowed = fixture.time_only(seconds='7200.125')
        result = fixture.evaluate(snapshot, allowed)
        self.assertEqual(result['measurements']['duration_ms']['value'], 7200125)
        self.assertEqual([entry['metric'] for entry in result['candidates']], ['duration_ms'])
        boundary, proof = fixture.time_only(seconds='7200.000')
        self.assertEqual(fixture.evaluate(boundary, proof)['candidates'], [])

    def test_run_and_closed_span_episodes_are_independent(self):
        snapshot, allowed = fixture.time_only(seconds=7201)
        owner = snapshot['owner_scope']
        second = copy.deepcopy(snapshot['duration_inputs'][0])
        target = {'owner_kind': 'span', 'owner_id': 'sha256:' + 'f' * 64}
        second['candidate']['id'] = target['owner_id']
        second['candidate']['seconds'] = 7202
        second['scope'] = target
        second['evidence']['candidate_id'] = target['owner_id']
        second['evidence']['scope'] = target
        allowed.append(('duration', owner, second['candidate'], second['evidence']))
        snapshot['duration_inputs'].append(second)
        first = fixture.evaluate(snapshot, allowed)
        self.assertEqual({entry['scope']['owner_kind'] for entry in first['candidates']}, {'run', 'span'})
        self.assertEqual(len({entry['warning_id'] for entry in first['candidates']}), 2)
        span = next(item for item in first['scoped_measurements'] if item['scope'] == target)
        self.assertEqual(span['metrics']['duration_ms']['value'], 7202000)
        retry = fixture.evaluate(first['proposed_snapshot'], allowed)
        self.assertEqual({entry['warning_id'] for entry in retry['candidates']},
                         {entry['warning_id'] for entry in first['candidates']})
        denied = [entry for entry in allowed if entry[2] != second['candidate']]
        result = fixture.evaluate(snapshot, denied)
        self.assertEqual([entry['scope']['owner_kind'] for entry in result['candidates']], ['run'])

    def test_missing_clock_evidence_has_a_diagnostic(self):
        snapshot, allowed = fixture.time_only()
        snapshot['duration_inputs'] = []
        result = fixture.evaluate(snapshot, allowed)
        self.assertEqual(result['candidates'], [])
        self.assertIn('timing_unavailable', result['diagnostics'])


if __name__ == '__main__':
    unittest.main()
