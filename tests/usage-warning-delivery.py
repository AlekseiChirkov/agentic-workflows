#!/usr/bin/env python3
"""Owner-scoped warning acceptance and crash recovery checks."""
import copy
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
from unittest.mock import patch
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixtures = load('tests/usage-current-run-snapshot-schema.py', 'snapshot_fixtures')
try:
    delivery = load('scripts/usage_telemetry_delivery.py', 'delivery')
except FileNotFoundError:
    delivery = None


class WarningDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / 'state.json'
        self.note = self.root / 'run-notes.md'
        self.note.write_text('Existing notes.\n', encoding='utf-8')
        self.note.chmod(0o600)
        self.initial = fixtures.snapshot()
        self.initial['warning_delivery'] = []
        self.state.write_text(json.dumps(self.initial), encoding='utf-8')
        self.state.chmod(0o600)
        self.owner = self.initial['owner_scope']
        self.warning = fixtures.warning()
        self.warning.update(crossing_state='crossed', delivery_state='pending')
        self.proposed = copy.deepcopy(self.initial)
        self.proposed['revision'] += 1
        self.proposed['warning_delivery'] = [self.warning]
        self.destinations = {('run', self.owner['owner_id']): str(self.note)}

    def apply(self, *, proposal=None, expected=None, owner=None, destinations=None, checkpoint=None):
        self.assertIsNotNone(delivery, 'warning delivery implementation is required')
        return delivery.apply_revision(
            self.state, self.initial['revision'] if expected is None else expected,
            copy.deepcopy(self.proposed if proposal is None else proposal),
            owner_scope=self.owner if owner is None else owner,
            destinations=self.destinations if destinations is None else destinations,
            checkpoint=checkpoint)

    def retry(self, *, destinations=None, checkpoint=None):
        self.assertIsNotNone(delivery, 'warning delivery implementation is required')
        return delivery.resume_delivery(self.state, owner_scope=self.owner,
            destinations=self.destinations if destinations is None else destinations,
            checkpoint=checkpoint)

    def current(self):
        return json.loads(self.state.read_text(encoding='utf-8'))

    def test_acceptance_precedes_note_and_marks_delivery_confirmed(self):
        observed = []
        def checkpoint(stage):
            observed.append((stage, self.current()['warning_delivery'][0]['delivery_state'],
                             self.note.read_text(encoding='utf-8')))
        report = self.apply(checkpoint=checkpoint)
        self.assertIn(('after_accept', 'pending', 'Existing notes.\n'), observed)
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'delivered')
        self.assertIn(self.warning['warning_id'], self.note.read_text(encoding='utf-8'))
        self.assertIn(self.warning['warning_id'], json.dumps(report))

    def test_crash_after_accept_recovers_idempotently(self):
        def crash(stage):
            if stage == 'after_accept':
                raise RuntimeError('interrupted')
        with self.assertRaises(RuntimeError):
            self.apply(checkpoint=crash)
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.assertNotIn(self.warning['warning_id'], self.note.read_text(encoding='utf-8'))
        self.retry()
        self.retry()
        self.assertEqual(self.note.read_text(encoding='utf-8').count(self.warning['warning_id']), 1)
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'delivered')

    def test_crash_after_note_before_confirmation_recovers_without_duplicate(self):
        def crash(stage):
            if stage == 'after_note':
                raise RuntimeError('interrupted')
        with self.assertRaises(RuntimeError):
            self.apply(checkpoint=crash)
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.retry()
        self.assertEqual(self.note.read_text(encoding='utf-8').count(self.warning['warning_id']), 1)
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'delivered')

    def test_missing_destination_stays_pending_and_reported_across_disable(self):
        report = self.apply(destinations={})
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.assertIn(self.warning['warning_id'], json.dumps(report))
        self.assertIn('pending', json.dumps(report))
        modes = load('scripts/usage_telemetry_modes.py', 'collection_modes')
        disabled = modes.transition_collection(self.current(), 'off', '2026-01-02T04:00:00Z',
                                               authorized=True, profile_verified=True)['snapshot']
        # The owner persists its separate collection transition under its lock.
        with delivery._locked(self.state) as (directory, name):
            _, info = delivery._load(directory, name)
            delivery._save(directory, name, disabled, info)
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.retry()
        self.assertEqual(self.note.read_text(encoding='utf-8').count(self.warning['warning_id']), 1)

    def test_status_proposal_cannot_change_collection_or_evidence(self):
        for changes in ({'mode': 'off', 'segments': []}, {'overlap_state': 'resolved'},
                        {'accepted_receipts': [], 'bundles': [], 'inventories': [], 'inventory_evidence': []}):
            with self.subTest(changes=changes):
                proposal = copy.deepcopy(self.proposed)
                proposal.update(changes)
                before = self.state.read_bytes()
                with self.assertRaises(ValueError):
                    self.apply(proposal=proposal, destinations={})
                self.assertEqual(self.state.read_bytes(), before)
                self.assertEqual(self.note.read_text(encoding='utf-8'), 'Existing notes.\n')

    def test_owner_and_scope_are_checked_before_any_side_effect(self):
        foreign = {'owner_kind': 'run', 'owner_id': fixtures.opaque('f')}
        before = self.state.read_bytes()
        with self.assertRaises(ValueError):
            self.apply(owner=foreign)
        self.assertEqual(self.state.read_bytes(), before)
        self.assertEqual(self.note.read_text(encoding='utf-8'), 'Existing notes.\n')

    def test_leaf_goes_only_to_matching_leaf_not_run_or_other_leaf(self):
        leaf = fixtures.opaque('a')
        other = self.root / 'other.md'
        other.write_text('Other.\n', encoding='utf-8')
        leaf_note = self.root / 'leaf.md'
        leaf_note.write_text('Leaf.\n', encoding='utf-8')
        leaf_note.chmod(0o600)
        self.warning['scope'] = {'owner_kind': 'span', 'owner_id': leaf}
        self.proposed['warning_delivery'] = [self.warning]
        destinations = self.destinations | {('span', leaf): str(leaf_note),
            ('span', fixtures.opaque('e')): str(other)}
        report = self.apply(destinations=destinations)
        self.assertIn(self.warning['warning_id'], leaf_note.read_text(encoding='utf-8'))
        self.assertNotIn(self.warning['warning_id'], self.note.read_text(encoding='utf-8'))
        self.assertEqual(other.read_text(encoding='utf-8'), 'Other.\n')
        self.assertIn(self.warning['warning_id'], json.dumps(report))

    def test_symlink_destination_never_modifies_its_target(self):
        outside = self.root / 'outside.md'
        outside.write_text('Unrelated.\n', encoding='utf-8')
        link = self.root / 'link.md'
        link.symlink_to(outside)
        report = self.apply(destinations={('run', self.owner['owner_id']): str(link)})
        self.assertEqual(outside.read_text(encoding='utf-8'), 'Unrelated.\n')
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.assertIn('pending', json.dumps(report))

    def test_stale_revision_is_rejected_without_overwriting_other_edit(self):
        changed = copy.deepcopy(self.initial)
        changed.update(revision=2, mode='off')
        self.state.write_text(json.dumps(changed), encoding='utf-8')
        before = self.state.read_bytes()
        with self.assertRaises(ValueError):
            self.apply()
        self.assertEqual(self.state.read_bytes(), before)
        self.assertEqual(self.note.read_text(encoding='utf-8'), 'Existing notes.\n')

    def test_concurrent_acceptance_has_single_winner(self):
        self.assertIsNotNone(delivery, 'warning delivery implementation is required')
        barrier = threading.Barrier(2)
        outcomes = []
        def worker():
            barrier.wait()
            try:
                self.apply()
                outcomes.append('accepted')
            except ValueError:
                outcomes.append('stale')
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertCountEqual(outcomes, ['accepted', 'stale'])
        self.assertEqual(self.note.read_text(encoding='utf-8').count(self.warning['warning_id']), 1)

    def test_state_file_cannot_be_used_as_note_destination(self):
        report = self.apply(destinations={('run', self.owner['owner_id']): str(self.state)})
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.assertIn('pending', json.dumps(report))

    def test_short_write_keeps_retry_idempotent(self):
        original = delivery.os.write
        def short_write(fd, data):
            end = data.index(self.warning['warning_id'].encode('ascii')) + len(self.warning['warning_id'])
            return original(fd, data[:end])
        with patch.object(delivery.os, 'write', side_effect=short_write):
            self.apply()
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.retry()
        self.assertEqual(self.note.read_text(encoding='utf-8').count(self.warning['warning_id']), 1)
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'delivered')

    def test_pending_warning_cannot_be_erased_by_proposal(self):
        self.apply(destinations={})
        proposal = self.current()
        proposal['revision'] += 1
        proposal['mode'] = 'off'
        proposal['warning_delivery'][0]['delivery_state'] = 'unknown'
        with self.assertRaises(ValueError):
            self.apply(proposal=proposal, expected=proposal['revision'] - 1, destinations={})
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'pending')

    def test_lock_file_cannot_be_used_as_note_destination(self):
        lock = self.root / '.state.json.lock'
        def worker(queue):
            try:
                queue.put(('ok', self.apply(destinations={('run', self.owner['owner_id']): str(lock)})))
            except Exception as error:
                queue.put(('error', type(error).__name__))
        context = multiprocessing.get_context('fork')
        queue = context.Queue()
        process = context.Process(target=worker, args=(queue,))
        process.start()
        process.join(2)
        if process.is_alive():
            process.terminate()
            process.join()
            self.fail('delivery blocked on its own lock file')
        outcome, report = queue.get(timeout=2)
        self.assertEqual(outcome, 'ok')
        self.assertIn('pending', json.dumps(report))
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'pending')

    def test_detectable_external_state_edit_before_replace_is_rejected(self):
        original = delivery.os.fsync
        changed = copy.deepcopy(self.initial)
        changed.update(revision=2, mode='off')
        def concurrent_edit(fd):
            original(fd)
            self.state.write_text(json.dumps(changed), encoding='utf-8')
        with patch.object(delivery.os, 'fsync', side_effect=concurrent_edit):
            with self.assertRaises(ValueError):
                self.apply()
        self.assertEqual(self.current(), changed)
        self.assertEqual(self.note.read_text(encoding='utf-8'), 'Existing notes.\n')

    def test_note_rename_before_write_does_not_mutate_moved_file_or_confirm(self):
        moved = self.root / 'moved.md'
        original = delivery.os.write
        def concurrent_rename(fd, data):
            os.rename(self.note, moved)
            self.note.write_text('Replacement.\n', encoding='utf-8')
            return original(fd, data)
        with patch.object(delivery.os, 'write', side_effect=concurrent_rename):
            self.apply()
        self.assertEqual(moved.read_text(encoding='utf-8'), 'Existing notes.\n')
        self.assertEqual(self.note.read_text(encoding='utf-8'), 'Replacement.\n')
        self.assertEqual(self.current()['warning_delivery'][0]['delivery_state'], 'pending')

    def test_private_payload_is_rejected_without_echo_or_write(self):
        secret = 'PRIVATE_CONTENT_SENTINEL'
        proposal = copy.deepcopy(self.proposed)
        proposal['warning_delivery'][0]['message'] = secret
        before = self.state.read_bytes()
        with self.assertRaises(ValueError) as error:
            self.apply(proposal=proposal)
        self.assertNotIn(secret, str(error.exception))
        self.assertEqual(self.state.read_bytes(), before)
        self.assertNotIn(secret, self.note.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
