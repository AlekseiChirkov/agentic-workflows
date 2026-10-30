#!/usr/bin/env python3
"""Offline acceptance checks for lifecycle compatibility and publication recovery."""
import copy
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


publication = load('recovery_publication', ROOT / 'scripts/usage_telemetry_publication.py')
contract = load('recovery_contract', ROOT / 'scripts/usage_telemetry_contract.py')
fixtures = load('recovery_fixtures', ROOT / 'tests/usage-observation-bundle-schema.py')
SCOPE = {'owner_kind': 'run', 'owner_id': 'sha256:' + '3' * 64,
         'attribution_quality': 'unknown'}


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.log = self.root / 'log'
        self.env = os.environ.copy()
        self.env.update(ORCHESTRAIL_HOME=str(ROOT), ORCHESTRAIL_LOG_ROOT=str(self.log))
        self.bundle = fixtures.bundle()
        self.encoded = contract.canonical_bytes(self.bundle)
        self.digest = hashlib.sha256(self.encoded).hexdigest()

    def command(self, *args, env=None):
        return subprocess.run(['/bin/bash', str(ROOT / 'scripts/log-step.sh'), *args],
                              env=env or self.env, capture_output=True, text=True, timeout=15)

    def start(self, env=None):
        result = self.command('run-start', '--pipeline', 'test', '--project', str(self.root), env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout.strip(), r'^[0-9a-f]{8}$')
        return result.stdout.strip()

    def lifecycle_snapshot(self):
        # Include clock and auxiliary metadata under the lifecycle roots.
        return {str(p.relative_to(self.log)): p.read_bytes()
                for directory in ('runs', '.active')
                for p in (self.log / directory).rglob('*') if p.is_file()}

    def isolated_path(self, forbidden):
        directory = self.root / ('path-' + '-'.join(sorted(forbidden)))
        directory.mkdir()
        for parent in (Path('/usr/bin'), Path('/bin')):
            for item in parent.iterdir():
                if item.name in forbidden or item.name.startswith('python'):
                    if item.name.startswith('python') and 'python3' not in forbidden:
                        pass
                    else:
                        continue
                target = directory / item.name
                if not target.exists() and item.is_file() and os.access(item, os.X_OK):
                    target.symlink_to(item.resolve())
        return str(directory)

    def test_legacy_full_lifecycle_without_optional_dependencies(self):
        signatures = []
        for forbidden in (set(), {'jq'}, {'python3'}, {'jq', 'python3'}):
            with self.subTest(forbidden=forbidden):
                self.log = self.root / ('log-' + '-'.join(sorted(forbidden)))
                env = self.env | {'ORCHESTRAIL_LOG_ROOT': str(self.log),
                                  'PATH': self.isolated_path(forbidden)}
                run = self.start(env)
                step = self.command('step', '--run', run, '--step', 'subtask', '--outcome', 'ok', env=env)
                end = self.command('run-end', '--run', run, '--outcome', 'completed', env=env)
                self.assertEqual((step.returncode, end.returncode), (0, 0))
                files = list((self.log / 'runs').rglob('*.jsonl'))
                self.assertEqual(len(files), 1, (step.stderr, end.stderr))
                events = [json.loads(line) for line in files[0].read_text().splitlines()]
                signatures.append([(e['event'], e.get('seq'), e.get('outcome')) for e in events])
                self.assertFalse((self.log / '.active' / run).exists())
        self.assertTrue(all(signature == signatures[0] for signature in signatures), signatures)
        self.assertEqual([row[0] for row in signatures[0]], ['run-start', 'step', 'run-end'])

    def test_invalid_usage_calls_leave_all_lifecycle_bytes_intact(self):
        run = self.start()
        original = self.lifecycle_snapshot()
        manifest = self.root / 'invalid.json'
        manifest.write_text('{"PRIVATE_SENTINEL": true}')
        calls = [
            ('step', '--run', run, '--step', 'subtask', '--outcome', 'ok', '--cost-usd', '0'),
            ('step', '--run', run, '--step', 'subtask', '--outcome', 'ok', '--cost-usd', '-1'),
            ('step', '--run', run, '--step', 'subtask', '--outcome', 'ok', '--usage-file', str(manifest)),
            ('usage-ingest', '--manifest', str(manifest)),
        ]
        for args in calls:
            with self.subTest(args=args):
                result = self.command(*args)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')
                self.assertEqual(self.lifecycle_snapshot(), original)
                self.assertNotIn('PRIVATE_SENTINEL', result.stderr)

    def test_checkpoint_replay_preserves_original_lifecycle_bytes(self):
        if not shutil.which('jq'):
            self.skipTest('checkpoint correlation requires jq')
        run = self.start()
        args = ('step', '--run', run, '--step', 'subtask', '--outcome', 'ok',
                '--session-id', 'session', '--agent-id', 'actor', '--checkpoint-id', 'first',
                '--span-start-ms', '1000', '--span-end-ms', '2000',
                '--timing-source', 'hook', '--boundary', 'subagent')
        first = self.command(*args)
        self.assertEqual(first.returncode, 0)
        accepted = json.loads(first.stdout)
        self.assertFalse(accepted['duplicate'])
        original = self.lifecycle_snapshot()
        second = self.command(*args)
        replay = json.loads(second.stdout)
        self.assertTrue(replay.pop('duplicate'))
        accepted.pop('duplicate')
        self.assertEqual(replay, accepted)
        self.assertEqual(self.lifecycle_snapshot(), original)
        changed = self.command(*args[:-1], 'session')
        self.assertEqual(changed.stdout, '')
        self.assertEqual(self.lifecycle_snapshot(), original)

    @property
    def artifact(self):
        return self.log / 'usage' / 'v1' / (self.digest + '.json')

    def publish(self):
        return publication.publish_usage(self.bundle, root=self.log, mode='on', scope=SCOPE,
                                         authorize=lambda candidate, scope: candidate == self.bundle and scope == SCOPE)

    def test_disable_and_resume_preserves_evidence_without_backfill(self):
        run = self.start()
        receipt = self.publish()
        self.assertFalse(receipt['duplicate'])
        accepted_bundle = self.artifact.read_bytes()
        run_file = next((self.log / 'runs').rglob('*.jsonl'))
        accepted_events = run_file.read_bytes()

        # Disabled publication must not authorize or install anything, even when
        # the selected input is missing and Python is unavailable to the logger.
        disabled_env = self.env | {'ORCHESTRAIL_USAGE_MODE': 'off',
                                   'PATH': self.isolated_path({'python3'})}
        disabled = self.command('usage-ingest', '--manifest', str(self.root / 'missing.json'),
                                env=disabled_env)
        self.assertEqual(disabled.returncode, 0)
        self.assertEqual(disabled.stdout, '')
        with patch.object(publication, '_install', side_effect=AssertionError('installed')):
            self.assertIsNone(publication.publish_usage(
                self.bundle, root=self.log, mode='off', scope=SCOPE,
                authorize=lambda *_: self.fail('disabled publication authorized')))
        self.assertEqual(self.artifact.read_bytes(), accepted_bundle)
        self.assertEqual(run_file.read_bytes(), accepted_events)

        step = self.command('step', '--run', run, '--step', 'subtask', '--outcome', 'ok',
                            env=disabled_env)
        self.assertEqual(step.returncode, 0)
        self.assertTrue(run_file.read_bytes().startswith(accepted_events))
        after_disabled = self.lifecycle_snapshot()
        duplicate = self.publish()
        self.assertTrue(duplicate['duplicate'])
        self.assertEqual(self.artifact.read_bytes(), accepted_bundle)
        self.assertEqual(self.lifecycle_snapshot(), after_disabled)
        self.assertEqual(list(self.artifact.parent.glob('*.json')), [self.artifact])

    def test_disable_resume_status_preserves_receipts_and_reports_segment_gap(self):
        status = load('recovery_status_fixture', ROOT / 'tests/usage-status-integration.py')
        modes = load('recovery_modes', ROOT / 'scripts/usage_telemetry_modes.py')
        snapshot, inputs, allowed = status.inputs()
        original = copy.deepcopy(snapshot)
        def transition(value, mode, when):
            return modes.transition_collection(value, mode, when, authorized=True,
                                               profile_verified=True)['snapshot']
        enabled = transition(snapshot, 'on', '2029-01-01T01:00:00Z')
        disabled = transition(enabled, 'off', '2029-01-01T02:00:00Z')
        resumed = transition(disabled, 'on', '2029-01-01T03:00:00Z')
        self.assertEqual(resumed['segments'][0], disabled['segments'][0])
        self.assertEqual(resumed['segments'][1]['gap_before'], {
            'state': 'present', 'start': '2029-01-01T02:00:00Z',
            'end': '2029-01-01T03:00:00Z'})
        for key in ('accepted_receipts', 'bundles', 'inventories', 'inventory_evidence'):
            self.assertEqual(resumed[key], original[key])
        verifier = status.resolution.Verifier(allowed)
        before = copy.deepcopy(resumed)
        result = status.alerts.evaluate_status(resumed, status.policy(), observed_at=status.NOW,
                                               analysis_inputs=inputs, verifier=verifier)
        self.assertEqual(resumed, before)
        self.assertEqual(result['proposed_snapshot']['segments'], resumed['segments'])
        for key in ('accepted_receipts', 'bundles', 'inventories', 'inventory_evidence'):
            self.assertEqual(result['proposed_snapshot'][key], original[key])
        self.assertEqual(result['measurements']['tokens']['value'], 2200)
        self.assertTrue(any(call[0] == 'receipt' for call in verifier.calls))

    def test_permission_disk_and_sync_failures_do_not_create_false_receipts(self):
        self.start()
        original = self.lifecycle_snapshot()
        # Failure before installation leaves no visible bundle; exact retry installs it.
        for operation, error in (('_install', errno.EACCES), ('_install', errno.ENOSPC),
                                 ('fsync', errno.ENOSPC)):
            with self.subTest(operation=operation, error=error):
                target = publication if operation == '_install' else os
                with patch.object(target, operation, side_effect=OSError(error, os.strerror(error))):
                    with self.assertRaises(OSError):
                        self.publish()
                self.assertFalse(self.artifact.exists())
                self.assertEqual(self.lifecycle_snapshot(), original)
                receipt = self.publish()
                self.assertFalse(receipt['duplicate'])
                self.assertEqual(self.artifact.read_bytes(), self.encoded)
                self.artifact.unlink()

    def test_directory_sync_failure_after_install_has_unknown_confirmation(self):
        self.start()
        original = self.lifecycle_snapshot()
        real_fsync = os.fsync
        calls = 0

        def fail_directory_sync(fd):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError(errno.ENOSPC, 'directory sync failed')
            return real_fsync(fd)

        with patch.object(os, 'fsync', side_effect=fail_directory_sync):
            with self.assertRaises(OSError):
                self.publish()
        self.assertEqual(calls, 2)
        self.assertEqual(self.artifact.read_bytes(), self.encoded)
        self.assertEqual(self.lifecycle_snapshot(), original)
        self.assertTrue(self.publish()['duplicate'])
        self.assertEqual(self.artifact.read_bytes(), self.encoded)
        self.assertEqual(self.lifecycle_snapshot(), original)

    def test_kill_before_and_after_atomic_install_requires_exact_retry(self):
        if not hasattr(os, 'fork'):
            self.skipTest('process interruption requires fork')
        self.start()
        original = self.lifecycle_snapshot()
        for after in (False, True):
            with self.subTest(after=after):
                read_fd, write_fd = os.pipe()
                pid = os.fork()
                if pid == 0:
                    os.close(read_fd)
                    original_install = publication._install
                    def interrupted(*args):
                        if after:
                            original_install(*args)
                        os.kill(os.getpid(), signal.SIGKILL)
                    publication._install = interrupted
                    try:
                        receipt = self.publish()
                        os.write(write_fd, json.dumps(receipt).encode())
                    finally:
                        os._exit(0)
                os.close(write_fd)
                _, status = os.waitpid(pid, 0)
                result = os.read(read_fd, 65536)
                os.close(read_fd)
                self.assertTrue(os.WIFSIGNALED(status))
                self.assertEqual(os.WTERMSIG(status), signal.SIGKILL)
                self.assertEqual(result, b'')
                self.assertEqual(self.artifact.exists(), after)
                self.assertEqual(self.lifecycle_snapshot(), original)
                retry = self.publish()
                self.assertEqual(retry['duplicate'], after)
                self.assertEqual(self.artifact.read_bytes(), self.encoded)
                self.artifact.unlink()


if __name__ == '__main__':
    unittest.main()
