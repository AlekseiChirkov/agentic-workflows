#!/usr/bin/env python3
"""Publication cannot delay closure or return a receipt after stale registration."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('race_tests', ROOT / 'tests/usage-publication-run-race.py')
races = importlib.util.module_from_spec(spec)
spec.loader.exec_module(races)
ingest = races.ingest


@unittest.skipIf(races.authority_tests.Ed25519PrivateKey is None, 'optional verifier unavailable')
class CloseDuringPublicationTests(unittest.TestCase):
    def setUp(self):
        self.race = races.PublicationRunRaceTests('test_uncontended_valid_registration_still_publishes')
        self.race.setUp()
        self.addCleanup(self.race.doCleanups)

    def test_run_closed_during_install_does_not_install_active_bundle(self):
        original = ingest.publication._install

        def close_before_install(*args):
            ended = self.race.end_run()
            self.assertEqual(ended.returncode, 0)
            self.assertFalse(self.race.fixture.lifecycle.exists())
            return original(*args)

        with patch.object(ingest.publication, '_install', side_effect=close_before_install):
            with self.assertRaises((ValueError, OSError)):
                self.race.invoke()
        self.assertFalse(self.race.fixture.artifact().exists())

    def test_paused_install_never_delays_close_or_returns_stale_receipt(self):
        entered, resume = threading.Event(), threading.Event()
        original = ingest.publication.publish_usage
        def blocked(*args, **kwargs):
            entered.set()
            if not resume.wait(8):
                raise ValueError('publication interrupted')
            return original(*args, **kwargs)
        def publish():
            try:
                return self.race.invoke()
            except (ValueError, OSError):
                return None
        with patch.object(ingest.publication, 'publish_usage', side_effect=blocked):
            with ThreadPoolExecutor(max_workers=2) as pool:
                future = pool.submit(publish)
                self.assertTrue(entered.wait(3))
                try:
                    ended = pool.submit(self.race.end_run).result(timeout=3)
                    self.assertEqual(ended.returncode, 0)
                    self.assertFalse(self.race.fixture.lifecycle.exists())
                finally:
                    resume.set()
                self.assertIsNone(future.result(timeout=8))
        # The immutable file may already exist even if no receipt was returned.


if __name__ == '__main__':
    unittest.main()
