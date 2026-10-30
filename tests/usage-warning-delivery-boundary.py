#!/usr/bin/env python3
"""Owner writer boundaries and detection of changes outside that protocol."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('delivery_tests', ROOT / 'tests/usage-warning-delivery.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class OwnerBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.case = base.WarningDeliveryTests('test_acceptance_precedes_note_and_marks_delivery_confirmed')
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.case.root.chmod(0o700)
        self.case.state.chmod(0o600)
        self.case.note.chmod(0o600)

    def test_private_state_owner_and_directory_boundary(self):
        for kind in ('directory', 'state'):
            with self.subTest(kind=kind):
                case = base.WarningDeliveryTests('test_acceptance_precedes_note_and_marks_delivery_confirmed')
                case.setUp()
                self.addCleanup(case.doCleanups)
                case.root.chmod(0o700)
                case.state.chmod(0o600)
                case.note.chmod(0o600)
                path = case.root if kind == 'directory' else case.state
                before = case.state.read_bytes()
                path.chmod(0o777 if kind == 'directory' else 0o666)
                try:
                    with self.assertRaises((ValueError, OSError)):
                        case.apply()
                    self.assertEqual(case.state.read_bytes(), before)
                    self.assertEqual(case.note.read_text(), 'Existing notes.\n')
                finally:
                    path.chmod(0o700 if kind == 'directory' else 0o600)

    def test_other_writable_note_is_not_a_valid_destination(self):
        self.case.note.chmod(0o666)
        report = self.case.apply()
        self.assertEqual(self.case.note.read_text(), 'Existing notes.\n')
        self.assertEqual(self.case.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.assertIn('pending', json.dumps(report))

    def test_detect_state_change_after_accept_before_touching_note(self):
        def change(stage):
            if stage == 'after_accept':
                other = self.case.current()
                other['revision'] += 1
                other['mode'] = 'off'
                self.case.state.write_text(json.dumps(other), encoding='utf-8')
        with self.assertRaises(ValueError):
            self.case.apply(checkpoint=change)
        self.assertEqual(self.case.note.read_text(), 'Existing notes.\n')
        self.assertEqual(self.case.current()['mode'], 'off')

    def test_renamed_note_after_append_does_not_confirm_replacement(self):
        moved = self.case.root / 'moved.md'
        def move(stage):
            if stage == 'after_note':
                self.case.note.rename(moved)
                self.case.note.write_text('Replacement.\n', encoding='utf-8')
        report = self.case.apply(checkpoint=move)
        self.assertEqual(self.case.note.read_text(), 'Replacement.\n')
        self.assertEqual(self.case.current()['warning_delivery'][0]['delivery_state'], 'pending')
        self.assertIn('pending', json.dumps(report))

    def test_cooperating_owner_writers_still_have_one_winner(self):
        self.case.test_concurrent_acceptance_has_single_winner()


if __name__ == '__main__':
    unittest.main()
