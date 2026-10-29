#!/usr/bin/env python3
"""Exercise publication against the lifecycle's concurrent close boundary."""
import fcntl
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('authority_tests', ROOT / 'tests/usage-authority-permit.py')
authority_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authority_tests)
ingest = authority_tests.ingest


@unittest.skipIf(authority_tests.Ed25519PrivateKey is None, 'optional verifier unavailable')
class PublicationRunRaceTests(unittest.TestCase):
    def setUp(self):
        self.auth = authority_tests.AuthorityPermitTests(methodName='test_valid_independent_permit_accepts_exact_bundle')
        self.auth.setUp()
        self.addCleanup(self.auth.doCleanups)
        self.fixture = self.auth.fixture
        metadata = self.fixture.lifecycle.read_text().splitlines()
        file_line = next(line for line in metadata if line.startswith('file='))
        self.run_file = Path(file_line.split('=', 1)[1])

    def invoke(self):
        return self.auth.invoke_with_trusted_loader()

    def end_run(self):
        return subprocess.run(['bash', str(ROOT / 'scripts/log-step.sh'), 'run-end',
                               '--run', self.fixture.run_id, '--outcome', 'completed'],
                              env=self.fixture.env, text=True, capture_output=True, timeout=10)

    def test_contended_lifecycle_lock_fails_closed_without_waiting(self):
        with self.run_file.open('ab') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            start = time.monotonic()
            with self.assertRaises((ValueError, OSError)):
                self.invoke()
            self.assertLess(time.monotonic() - start, 1)
        self.assertTrue(self.fixture.lifecycle.exists())
        self.assertFalse(self.fixture.artifact().exists())

    def test_registration_cannot_go_stale_before_publication(self):
        verify = ingest.authorized_by_independent_authority
        ended = []
        def close_while_verifying(*args):
            result = self.end_run()
            self.assertEqual(result.returncode, 0)
            ended.append(not self.fixture.lifecycle.exists())
            return verify(*args)
        try:
            with patch.object(ingest, 'authorized_by_independent_authority', side_effect=close_while_verifying):
                self.invoke()
        except (ValueError, OSError):
            accepted = False
        else:
            accepted = True
        self.assertTrue(ended)
        self.assertFalse(ended[0] and accepted, 'publication accepted stale registration after run-end')
        self.assertEqual(self.fixture.artifact().exists(), accepted)

    def test_uncontended_valid_registration_still_publishes(self):
        receipt = self.invoke()
        self.assertFalse(receipt['duplicate'])
        self.assertTrue(self.fixture.artifact().exists())
        self.assertTrue(self.fixture.lifecycle.exists())

    def test_closed_run_does_not_authorize_active_ingestion(self):
        result = self.end_run()
        self.assertEqual(result.returncode, 0)
        self.assertFalse(self.fixture.lifecycle.exists())
        with self.assertRaises((ValueError, OSError)):
            self.invoke()
        self.assertFalse(self.fixture.artifact().exists())


if __name__ == '__main__':
    unittest.main()
