#!/usr/bin/env python3
"""A recovered note marker must be made durable before confirmation."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('delivery_tests', ROOT / 'tests/usage-warning-delivery.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
delivery = base.delivery


class RecoveredMarkerDurabilityTests(unittest.TestCase):
    def setUp(self):
        self.case = base.WarningDeliveryTests('test_acceptance_precedes_note_and_marks_delivery_confirmed')
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.directory = self.case.root / 'notes'
        self.directory.mkdir(mode=0o700)
        self.case.note = self.directory / 'run.md'
        self.case.note.write_text('Existing notes.\n', encoding='utf-8')
        self.case.note.chmod(0o600)
        self.case.destinations = {('run', self.case.owner['owner_id']): str(self.case.note)}
        self.original_fsync = delivery.os.fsync
        self.directory_inode = self.directory.stat().st_ino

    def reject_directory_sync(self, fd):
        info = os.fstat(fd)
        if stat.S_ISDIR(info.st_mode) and info.st_ino == self.directory_inode:
            raise OSError('injected directory sync failure')
        return self.original_fsync(fd)

    def pending_marker(self):
        with patch.object(delivery.os, 'fsync', side_effect=self.reject_directory_sync):
            report = self.case.apply()
        self.assertEqual(self.case.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.assertIn('pending', json.dumps(report))
        self.assertEqual(self.case.note.read_text().count(self.case.warning['warning_id']), 1)

    def test_retry_remains_pending_until_marker_directory_is_synced(self):
        self.pending_marker()
        with patch.object(delivery.os, 'fsync', side_effect=self.reject_directory_sync):
            report = self.case.retry()
        self.assertEqual(self.case.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.assertIn('pending', json.dumps(report))
        self.assertEqual(self.case.note.read_text().count(self.case.warning['warning_id']), 1)

    def test_retry_remains_pending_when_existing_note_cannot_be_synced(self):
        self.pending_marker()
        note_inode = self.case.note.stat().st_ino
        def reject_note(fd):
            if os.fstat(fd).st_ino == note_inode:
                raise OSError('injected file sync failure')
            return self.original_fsync(fd)
        with patch.object(delivery.os, 'fsync', side_effect=reject_note):
            report = self.case.retry()
        self.assertEqual(self.case.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.assertIn('pending', json.dumps(report))
        self.assertEqual(self.case.note.read_text().count(self.case.warning['warning_id']), 1)

    def test_retry_syncs_existing_note_and_directory_before_confirmation(self):
        self.pending_marker()
        note_inode = self.case.note.stat().st_ino
        synced = []
        def observe(fd):
            info = os.fstat(fd)
            synced.append((info.st_ino, stat.S_ISDIR(info.st_mode)))
            return self.original_fsync(fd)
        with patch.object(delivery.os, 'fsync', side_effect=observe):
            self.case.retry()
        self.assertIn((note_inode, False), synced)
        self.assertIn((self.directory_inode, True), synced)
        self.assertEqual(self.case.current()['warning_delivery'][0]['delivery_state'], 'delivered')
        self.assertEqual(self.case.note.read_text().count(self.case.warning['warning_id']), 1)


if __name__ == '__main__':
    unittest.main()
