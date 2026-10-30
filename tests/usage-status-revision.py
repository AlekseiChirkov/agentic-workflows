#!/usr/bin/env python3
"""Pure status produces one successor owner revision and stable retries."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('duration_fixture', ROOT / 'tests/usage-status-duration-integration.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
contract = fixture.contract


class StatusRevisionTests(unittest.TestCase):
    def test_status_proposal_is_exactly_one_successor_and_input_is_unchanged(self):
        snapshot, allowed = fixture.time_only()
        original = copy.deepcopy(snapshot)
        first = fixture.evaluate(snapshot, allowed)
        second = fixture.evaluate(snapshot, allowed)
        self.assertEqual(snapshot, original)
        self.assertEqual(first, second)
        self.assertEqual(first['proposed_snapshot']['revision'], snapshot['revision'] + 1)
        contract.validate_current_run_snapshot(first['proposed_snapshot'])

    def test_replayed_proposal_is_stale_after_owner_accepts_successor(self):
        snapshot, allowed = fixture.time_only()
        first = fixture.evaluate(snapshot, allowed)
        accepted = first['proposed_snapshot']
        self.assertEqual(accepted['revision'], snapshot['revision'] + 1)
        next_result = fixture.evaluate(accepted, allowed)
        self.assertEqual(next_result['proposed_snapshot']['revision'], accepted['revision'] + 1)
        self.assertLessEqual(first['proposed_snapshot']['revision'], accepted['revision'])
        self.assertEqual(first['candidates'][0]['warning_id'], next_result['candidates'][0]['warning_id'])

    def test_unavailable_clock_still_proposes_one_revision_without_inventing_warning(self):
        snapshot, allowed = fixture.time_only(seconds=None, quality='unknown')
        result = fixture.evaluate(snapshot, allowed)
        self.assertEqual(result['candidates'], [])
        self.assertIn('timing_unavailable', result['diagnostics'])
        self.assertEqual(result['proposed_snapshot']['revision'], snapshot['revision'] + 1)
        contract.validate_current_run_snapshot(result['proposed_snapshot'])


if __name__ == '__main__':
    unittest.main()
