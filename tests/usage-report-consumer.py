#!/usr/bin/env python3
"""Immutable archive publication and failure behavior."""
import importlib.util
import base64
import subprocess
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / 'scripts'))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
publisher = load('publisher', ROOT / 'scripts/usage-report-publish.py')
fixture = load('export_fixture', ROOT / 'tests/usage-report-exports.py')

class ConsumerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.fd = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, self.fd)
        self.archive = publisher.exports.archive_exports(fixture.render(fixture.report()))

    def test_publish_and_exact_retry_refuse_conflicts(self):
        publisher.publish(self.fd, 'revision.tar', self.archive)
        self.assertEqual((self.path / 'revision.tar').read_bytes(), self.archive)
        publisher.publish(self.fd, 'revision.tar', self.archive)
        (self.path / 'occupied').write_bytes(b'other')
        with self.assertRaises(OSError):
            publisher.publish(self.fd, 'occupied', self.archive)
        self.assertEqual((self.path / 'occupied').read_bytes(), b'other')
        (self.path / 'link').symlink_to('occupied')
        with self.assertRaises(OSError):
            publisher.publish(self.fd, 'link', self.archive)
        self.assertEqual((self.path / 'occupied').read_bytes(), b'other')

    def test_partial_or_inconsistent_archive_never_publishes(self):
        for data in (self.archive[:512], self.archive[:-1], self.archive + b'x'):
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                publisher.publish(self.fd, 'revision.tar', data)
        self.assertEqual(list(self.path.iterdir()), [])

    def test_failed_write_and_moved_directory_leave_no_named_staging(self):
        with patch.object(os, 'fsync', side_effect=OSError('failure')):
            with self.assertRaises(OSError):
                publisher.publish(self.fd, 'revision.tar', self.archive)
        self.assertEqual(list(self.path.iterdir()), [])
        other = self.path.parent / (self.path.name + '-moved')
        os.rename(self.path, other)
        self.addCleanup(os.rename, other, self.path)
        # The operator must keep the parent stable throughout publication.
        with patch.object(publisher, '_check_location', side_effect=[str(self.path), str(other)]):
            with self.assertRaises(ValueError):
                publisher.publish(self.fd, 'revision.tar', self.archive)
        self.assertEqual(list(other.iterdir()), [])

    def test_full_archive_followed_by_producer_failure_never_installs(self):
        encoded = base64.b64encode(self.archive).decode('ascii')
        command = [sys.executable, '-c',
                   'import base64,sys; sys.stdout.buffer.write(base64.b64decode(sys.argv[1])); '
                   'sys.stdout.buffer.flush(); sys.exit(3)', encoded]
        with self.assertRaises(OSError):
            publisher.publish(self.fd, 'revision.tar', publisher.run_producer(command))
        self.assertEqual(list(self.path.iterdir()), [])
        command[-2] = command[-2].replace('sys.exit(3)', 'sys.exit(0)')
        publisher.publish(self.fd, 'revision.tar', publisher.run_producer(command))
        self.assertEqual((self.path / 'revision.tar').read_bytes(), self.archive)

    def test_cli_requires_protected_deployment_and_uses_typed_exit_codes(self):
        script = str(ROOT / 'scripts/usage-report-publish.py')
        args = ['--directory-fd', str(self.fd), '--name', 'revision.tar',
                '--corpus-manifest', '/missing-manifest', '--scenario', 'baseline',
                '--authority', '/missing-authority', '--authority-key', '/missing-key']
        result = subprocess.run([sys.executable, script, *args], pass_fds=[self.fd], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(self.path.iterdir()), [])
        result = subprocess.run([sys.executable, script, '--protected-directory-acknowledged', *args],
                                pass_fds=[self.fd], capture_output=True)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(list(self.path.iterdir()), [])

    def test_shared_storage_rejected(self):
        shared = self.path / 'logs' / 'usage' / 'v1'
        shared.mkdir(parents=True)
        fd = os.open(shared, os.O_RDONLY | os.O_DIRECTORY)
        try:
            with patch.dict(os.environ, {'ORCHESTRAIL_LOG_ROOT': str(self.path / 'logs')}):
                with self.assertRaises(ValueError):
                    publisher.publish(fd, 'revision.tar', self.archive)
        finally:
            os.close(fd)
        self.assertEqual(list(shared.iterdir()), [])

if __name__ == '__main__':
    unittest.main()
