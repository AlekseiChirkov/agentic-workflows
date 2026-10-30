#!/usr/bin/env python3
"""Offline checks for explicit, owner-scoped collection transitions."""
import copy
import importlib.util
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixtures = load('snapshot_fixtures', 'tests/usage-current-run-snapshot-schema.py')
contract = load('contract', 'scripts/usage_telemetry_contract.py')
module_path = ROOT / 'scripts/usage_telemetry_modes.py'
modes = load('modes', 'scripts/usage_telemetry_modes.py') if module_path.exists() else None


def transition(snapshot, mode, when, *, authorized=True, profile_verified=True):
    if modes is None:
        return None
    return modes.transition_collection(snapshot, mode, when,
                                       authorized=authorized,
                                       profile_verified=profile_verified)


def empty_snapshot():
    value = fixtures.snapshot()
    value.update(mode='off', segments=[])
    return value


class CollectionTransitionTests(unittest.TestCase):
    def change(self, snapshot, mode, when, **kwargs):
        before = copy.deepcopy(snapshot)
        with patch('builtins.open', side_effect=AssertionError('unexpected file access')), \
             patch.object(Path, 'open', side_effect=AssertionError('unexpected file access')), \
             patch.object(socket, 'socket', side_effect=AssertionError('network access')):
            result = transition(snapshot, mode, when, **kwargs)
        self.assertEqual(snapshot, before, 'transition must not mutate its input')
        self.assertIsInstance(result, dict)
        self.assertEqual(set(result), {'snapshot', 'reason', 'changed'})
        self.assertEqual(contract.validate_current_run_snapshot(result['snapshot']), result['snapshot'])
        return result

    def test_unset_mode_defaults_off_without_creating_a_segment(self):
        snapshot = empty_snapshot()
        result = self.change(snapshot, None, '2026-01-02T04:00:00Z')
        self.assertEqual(result['snapshot'], snapshot)
        self.assertEqual(result['reason'], 'collection_disabled')
        self.assertFalse(result['changed'])

    def test_enable_disable_and_reenable_preserve_evidence_and_expose_gap(self):
        snapshot = empty_snapshot()
        enabled = self.change(snapshot, 'on', '2026-01-02T04:00:00Z')
        first = enabled['snapshot']['segments'][0]
        self.assertTrue(enabled['changed'])
        self.assertEqual(enabled['snapshot']['mode'], 'on')
        self.assertEqual(first['owner_scope'], snapshot['owner_scope'])
        self.assertEqual(first['start'], '2026-01-02T04:00:00Z')
        self.assertIsNone(first['end'])
        self.assertEqual(first['gap_before'], {'state': 'unknown', 'start': None, 'end': None})
        disabled = self.change(enabled['snapshot'], 'off', '2026-01-02T05:00:00Z')
        self.assertEqual(disabled['snapshot']['mode'], 'off')
        self.assertEqual(disabled['snapshot']['segments'][0]['end'], '2026-01-02T05:00:00Z')
        self.assertEqual(disabled['reason'], 'collection_disabled')
        resumed = self.change(disabled['snapshot'], 'on', '2026-01-02T06:00:00Z')
        self.assertEqual(len(resumed['snapshot']['segments']), 2)
        first_closed, second = resumed['snapshot']['segments']
        self.assertEqual(first_closed, disabled['snapshot']['segments'][0])
        self.assertNotEqual(first_closed['segment_id'], second['segment_id'])
        self.assertEqual(second['gap_before'], {'state': 'present',
                         'start': '2026-01-02T05:00:00Z', 'end': '2026-01-02T06:00:00Z'})
        for key in ('accepted_receipts', 'bundles', 'inventories', 'inventory_evidence',
                    'warning_delivery', 'overlap_state'):
            self.assertEqual(resumed['snapshot'][key], snapshot[key])

    def test_duplicate_transitions_are_idempotent_and_equal_boundary_is_valid(self):
        initial = empty_snapshot()
        on = self.change(initial, 'on', '2026-01-02T04:00:00Z')['snapshot']
        again = self.change(on, 'on', '2026-01-02T04:00:00Z')
        self.assertFalse(again['changed'])
        self.assertEqual(again['snapshot'], on)
        off = self.change(on, 'off', '2026-01-02T04:00:00Z')['snapshot']
        duplicate = self.change(off, 'off', '2026-01-02T04:00:00Z')
        self.assertFalse(duplicate['changed'])
        self.assertEqual(duplicate['snapshot'], off)
        resumed = self.change(off, 'on', '2026-01-02T04:00:00Z')['snapshot']
        self.assertNotEqual(resumed['segments'][0]['segment_id'], resumed['segments'][1]['segment_id'])
        self.assertEqual(resumed['segments'][1]['gap_before'], {'state': 'present',
                         'start': '2026-01-02T04:00:00Z', 'end': '2026-01-02T04:00:00Z'})

    def test_invalid_mode_and_missing_authorization_fail_closed(self):
        snapshot = empty_snapshot()
        for mode, options in [('invalid', {}), ('ON', {}), ('', {}),
                              ('on', {'authorized': False}),
                              ('on', {'profile_verified': False})]:
            with self.subTest(mode=mode, options=options):
                result = self.change(snapshot, mode, '2026-01-02T04:00:00Z', **options)
                self.assertEqual(result['snapshot'], snapshot)
                self.assertIsInstance(result['reason'], str)
                self.assertTrue(result['reason'])
                self.assertFalse(result['changed'])
        on = self.change(snapshot, 'on', '2026-01-02T04:00:00Z')['snapshot']
        stopped = self.change(on, 'invalid', '2026-01-02T05:00:00Z')
        self.assertEqual(stopped['snapshot']['mode'], 'off')
        self.assertEqual(stopped['snapshot']['segments'][0]['end'], '2026-01-02T05:00:00Z')
        self.assertTrue(stopped['reason'])
        self.assertEqual(stopped['snapshot']['warning_delivery'], on['warning_delivery'])

    def test_invalid_or_backwards_boundary_is_rejected_without_mutation(self):
        snapshot = empty_snapshot()
        for when in ('2026-01-02', 'secret/path', '', None):
            before = copy.deepcopy(snapshot)
            with self.subTest(when=when), self.assertRaises(ValueError):
                transition(snapshot, 'on', when)
            self.assertEqual(snapshot, before)
        on = self.change(snapshot, 'on', '2026-01-02T04:00:00Z')['snapshot']
        before = copy.deepcopy(on)
        with self.assertRaises(ValueError):
            transition(on, 'off', '2026-01-02T03:59:59Z')
        self.assertEqual(on, before)

    def test_missing_open_segment_cannot_silently_claim_active_collection(self):
        initial = empty_snapshot()
        initial['mode'] = 'on'
        contract.validate_current_run_snapshot(initial)
        for requested in ('on', 'off'):
            with self.subTest(requested=requested), self.assertRaises(ValueError):
                transition(initial, requested, '2026-01-02T04:00:00Z')
        valid = self.change(empty_snapshot(), 'on', '2026-01-02T04:00:00Z')
        self.assertEqual(valid['snapshot']['segments'][0]['gap_before']['state'], 'unknown')

    def test_overlapping_closed_segments_cannot_prove_a_collection_gap(self):
        initial = empty_snapshot()
        active = self.change(initial, 'on', '2026-01-02T04:00:00Z')['snapshot']
        stopped = self.change(active, 'off', '2026-01-02T05:00:00Z')['snapshot']
        resumed = self.change(stopped, 'on', '2026-01-02T06:00:00Z')['snapshot']
        closed = self.change(resumed, 'off', '2026-01-02T07:00:00Z')['snapshot']
        valid = self.change(closed, 'on', '2026-01-02T08:00:00Z')['snapshot']
        self.assertEqual(valid['segments'][-1]['gap_before']['start'], '2026-01-02T07:00:00Z')
        overlap = copy.deepcopy(closed)
        overlap['segments'][1]['start'] = '2026-01-02T04:30:00Z'
        overlap['segments'][1]['gap_before'] = {'state': 'unknown', 'start': None, 'end': None}
        contract.validate_current_run_snapshot(overlap)
        with self.assertRaises(ValueError):
            transition(overlap, 'on', '2026-01-02T08:00:00Z')

    def test_explicit_off_segment_keeps_full_gap_since_collection_stopped(self):
        initial = empty_snapshot()
        active = self.change(initial, 'on', '2026-01-02T04:00:00Z')['snapshot']
        stopped = self.change(active, 'off', '2026-01-02T05:00:00Z')['snapshot']
        stopped['segments'].append({
            'schema_version': 1, 'kind': 'collection_segment',
            'segment_id': 'sha256:' + 'f' * 64,
            'owner_scope': copy.deepcopy(stopped['owner_scope']), 'mode': 'off',
            'start': '2026-01-02T05:00:00Z', 'end': '2026-01-02T06:00:00Z',
            'gap_before': {'state': 'none', 'start': None, 'end': None},
        })
        contract.validate_current_run_snapshot(stopped)
        resumed = self.change(stopped, 'on', '2026-01-02T07:00:00Z')['snapshot']
        self.assertEqual(resumed['segments'][-1]['gap_before'], {
            'state': 'present', 'start': '2026-01-02T05:00:00Z',
            'end': '2026-01-02T07:00:00Z'})
        self.assertEqual(resumed['segments'][1], stopped['segments'][1])
        self.assertNotEqual(resumed['segments'][-1]['segment_id'], stopped['segments'][0]['segment_id'])

    def test_distinct_segments_cannot_share_an_identity(self):
        initial = empty_snapshot()
        active = self.change(initial, 'on', '2026-01-02T04:00:00Z')['snapshot']
        stopped = self.change(active, 'off', '2026-01-02T05:00:00Z')['snapshot']
        resumed = self.change(stopped, 'on', '2026-01-02T06:00:00Z')['snapshot']
        self.assertNotEqual(resumed['segments'][0]['segment_id'], resumed['segments'][1]['segment_id'])
        ambiguous = copy.deepcopy(resumed)
        ambiguous['segments'][1]['segment_id'] = ambiguous['segments'][0]['segment_id']
        contract.validate_current_run_snapshot(ambiguous)
        with self.assertRaises(ValueError):
            transition(ambiguous, 'off', '2026-01-02T07:00:00Z')

    def test_session_owner_is_preserved_and_unrelated_owners_are_rejected(self):
        snapshot = empty_snapshot()
        snapshot.update(owner_scope={'owner_kind': 'session', 'owner_id': 'sha256:' + 'e' * 64},
                        accepted_receipts=[], bundles=[], inventories=[], inventory_evidence=[],
                        warning_delivery=[])
        on = self.change(snapshot, 'on', '2026-01-02T04:00:00Z')['snapshot']
        self.assertEqual(on['segments'][0]['owner_scope'], snapshot['owner_scope'])
        foreign = copy.deepcopy(on)
        foreign['segments'][0]['owner_scope']['owner_id'] = 'sha256:' + 'f' * 64
        with self.assertRaises(ValueError):
            transition(foreign, 'off', '2026-01-02T05:00:00Z')


if __name__ == '__main__':
    unittest.main()
