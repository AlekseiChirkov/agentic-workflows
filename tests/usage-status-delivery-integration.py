#!/usr/bin/env python3
"""Exercise pure status proposals through the authorized delivery owner."""
import importlib.util
import json
import os
import socket
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


time_fixture = load('duration_fixture', 'tests/usage-status-duration-integration.py')
delivery = load('warning_delivery', 'scripts/usage_telemetry_delivery.py')
status_tests = load('status_warning_tests', 'tests/usage-alert-status.py')


class StatusDeliveryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state_path = self.root / 'state.json'
        self.authority_path = self.root / 'authority.json'
        self.note_path = self.root / 'run.md'
        self.note_path.write_text('Run notes.\n', encoding='utf-8')
        self.note_path.chmod(0o600)
        snapshot, allowed = time_fixture.time_only()
        self.owner = snapshot['owner_scope']
        self.state_path.write_text(json.dumps(snapshot), encoding='utf-8')
        self.state_path.chmod(0o600)
        self.authority_path.write_text(json.dumps({'schema_version': 1, 'kind': 'status_authority',
            'bindings': [{'kind': kind, 'scope': scope, 'subject': subject, 'evidence': evidence}
                         for kind, scope, subject, evidence in allowed]}), encoding='utf-8')
        self.authority_path.chmod(0o600)
        self.destinations = {('run', self.owner['owner_id']): str(self.note_path)}

    def state(self):
        return json.loads(self.state_path.read_text(encoding='utf-8'))

    def status(self):
        before = self.state_path.read_bytes(), self.note_path.read_bytes()
        process = subprocess.run(['python3', str(ROOT / 'scripts/usage-telemetry.py'), 'status',
            '--receipt-snapshot', str(self.state_path), '--authority', str(self.authority_path),
            '--observed-at', time_fixture.NOW],
            cwd=self.root, capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual((self.state_path.read_bytes(), self.note_path.read_bytes()), before)
        return json.loads(process.stdout)

    def apply(self, result, destinations=None, checkpoint=None):
        return delivery.apply_revision(self.state_path, self.state()['revision'],
            result['proposed_snapshot'], owner_scope=self.owner,
            destinations=self.destinations if destinations is None else destinations,
            checkpoint=checkpoint)

    def test_owner_command_rejects_shared_state_or_note_before_mutation(self):
        result = self.status()
        proposal = self.root / 'proposal.json'
        proposal.write_text(json.dumps(result), encoding='utf-8')
        shared = self.root / 'logs' / 'usage' / 'v1'
        shared.mkdir(parents=True)
        shared_state = shared / 'state.json'
        shared_state.write_bytes(self.state_path.read_bytes())
        shared_state.chmod(0o600)
        shared_note = shared / 'note.md'
        shared_note.write_text('Shared evidence.\n', encoding='utf-8')
        shared_note.chmod(0o600)
        authority = self.root / 'owner.json'
        alias = self.root / 'shared-alias'
        alias.symlink_to(shared, target_is_directory=True)
        env = {**os.environ, 'ORCHESTRAIL_LOG_ROOT': str(self.root / 'logs')}
        for state, note in ((shared_state, self.note_path), (self.state_path, shared_note),
                            (alias / 'state.json', self.note_path), (self.state_path, alias / 'note.md')):
            with self.subTest(shared_state=state == shared_state):
                authority.write_text(json.dumps({'schema_version': 1, 'kind': 'warning_owner_authority',
                    'owner_scope': self.owner, 'destinations': [{'scope': self.owner, 'path': str(note)}]}))
                authority.chmod(0o600)
                paths = (self.state_path, shared_state, self.note_path, shared_note)
                before = [path.read_bytes() for path in paths]
                command = ['python3', str(ROOT / 'scripts/usage-telemetry.py'), 'owner-deliver',
                           '--state', str(state), '--owner-authority', str(authority), '--proposal', str(proposal)]
                process = subprocess.run(command, capture_output=True, env=env)
                self.assertNotEqual(process.returncode, 0)
                self.assertEqual([path.read_bytes() for path in paths], before)
                self.assertEqual(process.stdout, b'')
                self.assertFalse((shared / '.state.json.lock').exists())
                self.assertFalse((self.root / '.state.json.lock').exists())

    def test_owner_command_accepts_socket_output(self):
        authority = self.root / 'owner-socket.json'
        authority.write_text(json.dumps({'schema_version': 1, 'kind': 'warning_owner_authority',
            'owner_scope': self.owner, 'destinations': []}), encoding='utf-8')
        authority.chmod(0o600)
        command = ['python3', str(ROOT / 'scripts/usage-telemetry.py'), 'owner-deliver',
                   '--state', str(self.state_path), '--owner-authority', str(authority)]
        reader, writer = socket.socketpair()
        try:
            result = subprocess.run(command, stdout=writer, stderr=subprocess.PIPE)
            writer.close()
            output = b''
            while True:
                chunk = reader.recv(4096)
                if not chunk:
                    break
                output += chunk
        finally:
            reader.close()
            writer.close()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output)['warnings'], [])

    def test_owner_command_rejects_regular_output_before_any_mutation(self):
        result = self.status()
        proposal = self.root / 'proposal.json'
        proposal.write_text(json.dumps(result), encoding='utf-8')
        authority = self.root / 'owner.json'
        authority.write_text(json.dumps({'schema_version': 1, 'kind': 'warning_owner_authority',
            'owner_scope': self.owner, 'destinations': [{'scope': self.owner, 'path': str(self.note_path)}]}))
        authority.chmod(0o600)
        shared = self.root / 'logs' / 'usage' / 'v1'
        shared.mkdir(parents=True)
        output = shared / 'existing.json'
        output.write_bytes(b'existing evidence\n')
        before_state = self.state_path.read_bytes()
        before_note = self.note_path.read_bytes()
        command = ['python3', str(ROOT / 'scripts/usage-telemetry.py'), 'owner-deliver',
                   '--state', str(self.state_path), '--owner-authority', str(authority),
                   '--proposal', str(proposal)]
        with output.open('ab') as stream:
            process = subprocess.run(command, stdout=stream, stderr=subprocess.PIPE)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(output.read_bytes(), b'existing evidence\n')
        self.assertEqual(self.state_path.read_bytes(), before_state)
        self.assertEqual(self.note_path.read_bytes(), before_note)
        self.assertIn(b'owner delivery failed', process.stderr)

    def test_owner_command_delivers_and_reports_pending_recovery(self):
        authority = self.root / 'owner.json'
        authority.write_text(json.dumps({'schema_version': 1, 'kind': 'warning_owner_authority',
            'owner_scope': self.owner, 'destinations': []}), encoding='utf-8')
        authority.chmod(0o600)
        result = self.status()
        identifier = result['candidates'][0]['warning_id']
        proposal = self.root / 'proposal.json'
        proposal.write_text(json.dumps(result), encoding='utf-8')
        command = ['python3', str(ROOT / 'scripts/usage-telemetry.py'), 'owner-deliver',
                   '--state', str(self.state_path), '--owner-authority', str(authority)]
        first = subprocess.run(command + ['--proposal', str(proposal)], capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(json.loads(first.stdout)['warnings'][0]['delivery_state'], 'pending')
        authority.write_text(json.dumps({'schema_version': 1, 'kind': 'warning_owner_authority',
            'owner_scope': self.owner, 'destinations': [{'scope': self.owner, 'path': str(self.note_path)}]}))
        recovered = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        self.assertEqual(json.loads(recovered.stdout)['warnings'][0]['delivery_state'], 'delivered')
        again = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(self.note_path.read_text().count(identifier), 1)

    def test_lower_bound_details_survive_pending_delivery_and_retry(self):
        snapshot = status_tests.snapshot()
        self.owner = snapshot['owner_scope']
        self.state_path.write_text(json.dumps(snapshot), encoding='utf-8')
        self.destinations = {('run', self.owner['owner_id']): str(self.note_path)}
        analysis = status_tests.evaluated(1200, state='proven_lower_bound')
        with patch.object(status_tests.alerts, '_evaluate_snapshot', return_value=analysis):
            result = status_tests.alerts.evaluate_status(snapshot, status_tests.policy(),
                                                         observed_at=status_tests.NOW)
        warning = result['candidates'][0]
        report = self.apply(result, destinations={})
        details = report['warnings'][0]['details']
        self.assertEqual(details['measurement'], {'state': 'proven_lower_bound', 'value': 1200, 'unit': 'tokens'})
        self.assertEqual(details['threshold'], {'state': 'final', 'value': 1000, 'unit': 'tokens'})
        self.assertEqual(details['completeness']['state'], 'unknown')
        delivered = delivery.resume_delivery(self.state_path, owner_scope=self.owner, destinations=self.destinations)
        self.assertEqual(delivered['warnings'][0]['details'], details)
        note = self.note_path.read_text(encoding='utf-8')
        self.assertIn(warning['warning_id'], note)
        self.assertIn('proven_lower_bound', note)
        self.assertIn('1200', note)
        self.assertIn('1000', note)
        self.assertIn('unknown', note)
        self.assertIn(self.owner['owner_id'], note)

    def test_empty_parts_manifest_survives_status_and_recovery(self):
        original = self.state()
        original['parts'] = []
        self.state_path.write_text(json.dumps(original), encoding='utf-8')
        result = self.status()
        self.assertEqual(result['proposed_snapshot']['parts'], [])
        self.assertEqual(len(result['candidates']), 1)
        report = self.apply(result, destinations={})
        self.assertEqual(report['warnings'][0]['delivery_state'], 'pending')
        with self.assertRaisesRegex(ValueError, 'stale owner state'):
            delivery.apply_revision(self.state_path, original['revision'], result['proposed_snapshot'],
                                    owner_scope=self.owner, destinations=self.destinations)
        delivery.resume_delivery(self.state_path, owner_scope=self.owner, destinations=self.destinations)
        delivery.resume_delivery(self.state_path, owner_scope=self.owner, destinations=self.destinations)
        self.assertEqual(self.state()['parts'], [])
        self.assertEqual(self.note_path.read_text().count(result['candidates'][0]['warning_id']), 1)

    def test_real_status_proposal_is_accepted_and_repeat_does_not_duplicate(self):
        first = self.status()
        self.assertEqual(len(first['candidates']), 1)
        identifier = first['candidates'][0]['warning_id']
        self.apply(first)
        self.assertEqual(self.state()['warning_delivery'][0]['delivery_state'], 'delivered')
        self.assertEqual(self.note_path.read_text().count(identifier), 1)
        second = self.status()
        self.assertEqual(second['candidates'], [])
        self.apply(second)
        self.assertEqual(self.note_path.read_text().count(identifier), 1)

    def test_real_proposal_recovers_after_interrupted_acceptance(self):
        result = self.status()
        identifier = result['candidates'][0]['warning_id']
        def crash(stage):
            if stage == 'after_accept':
                raise RuntimeError('interrupted')
        with self.assertRaises(RuntimeError):
            self.apply(result, checkpoint=crash)
        self.assertEqual(self.state()['warning_delivery'][0]['delivery_state'], 'pending')
        delivery.resume_delivery(self.state_path, owner_scope=self.owner, destinations=self.destinations)
        delivery.resume_delivery(self.state_path, owner_scope=self.owner, destinations=self.destinations)
        self.assertEqual(self.state()['warning_delivery'][0]['delivery_state'], 'delivered')
        self.assertEqual(self.note_path.read_text().count(identifier), 1)

    def test_real_proposal_preserves_pending_report_until_destination_is_available(self):
        result = self.status()
        identifier = result['candidates'][0]['warning_id']
        report = self.apply(result, destinations={})
        self.assertEqual(self.state()['warning_delivery'][0]['delivery_state'], 'pending')
        self.assertIn('destination_unavailable', json.dumps(report))
        self.assertEqual(self.note_path.read_text(), 'Run notes.\n')
        pending = self.status()
        self.assertEqual(pending['candidates'][0]['warning_id'], identifier)
        delivery.resume_delivery(self.state_path, owner_scope=self.owner, destinations=self.destinations)
        self.assertEqual(self.note_path.read_text().count(identifier), 1)
        self.assertEqual(self.state()['warning_delivery'][0]['delivery_state'], 'delivered')


if __name__ == '__main__':
    unittest.main()
