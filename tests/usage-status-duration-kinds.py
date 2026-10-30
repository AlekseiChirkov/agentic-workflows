#!/usr/bin/env python3
"""Work and run duration have separate episodes and clock provenance."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('duration_fixture', ROOT / 'tests/usage-status-duration-integration.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class DurationKindsTests(unittest.TestCase):
    def test_one_scope_can_warn_independently_for_work_and_run(self):
        snapshot, allowed = fixture.time_only(seconds=7201)
        owner = snapshot['owner_scope']
        run = copy.deepcopy(snapshot['duration_inputs'][0])
        run['candidate']['id'] = 'sha256:' + 'e' * 64
        run['candidate']['group']['duration_kind'] = 'run'
        run['candidate']['seconds'] = 7202
        run['evidence']['candidate_id'] = run['candidate']['id']
        allowed.append(('duration', owner, run['candidate'], run['evidence']))
        snapshot['duration_inputs'].append(run)
        first = fixture.evaluate(snapshot, allowed)
        self.assertEqual(len(first['candidates']), 2)
        self.assertTrue(all(warning['scope'] == owner for warning in first['candidates']))
        self.assertEqual(len({warning['warning_id'] for warning in first['candidates']}), 2)
        self.assertEqual(len({warning['policy_id'] for warning in first['candidates']}), 2)
        again = fixture.evaluate(first['proposed_snapshot'], allowed)
        self.assertEqual({warning['warning_id'] for warning in first['candidates']},
                         {warning['warning_id'] for warning in again['candidates']})
        unknown = fixture.evaluate(first['proposed_snapshot'], [])
        self.assertEqual({warning['warning_id'] for warning in first['candidates']},
                         {warning['warning_id'] for warning in unknown['candidates']})

    def test_unknown_clock_source_is_not_a_duration_measurement(self):
        snapshot, allowed = fixture.time_only(seconds=7201)
        owner = snapshot['owner_scope']
        entry = snapshot['duration_inputs'][0]
        entry['evidence']['clock_source'] = 'unknown'
        allowed = [('duration', owner, entry['candidate'], entry['evidence'])]
        result = fixture.evaluate(snapshot, allowed)
        self.assertEqual(result['candidates'], [])
        self.assertNotIn('duration_ms', result['measurements'])
        self.assertIn('timing_unavailable', result['diagnostics'])


if __name__ == '__main__':
    unittest.main()
