#!/usr/bin/env python3
"""Offline checks for immutable, provenance-authorized usage publication."""
import copy
import hashlib
import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import stat
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


contract = load('publication_contract', ROOT / 'scripts/usage_telemetry_contract.py')
fixtures = load('publication_fixtures', ROOT / 'tests/usage-observation-bundle-schema.py')
publication_path = ROOT / 'scripts/usage_telemetry_publication.py'
publication = load('usage_telemetry_publication', publication_path) if publication_path.exists() else None

SCOPE = {'owner_kind': 'run', 'owner_id': 'sha256:' + '3' * 64,
         'attribution_quality': 'unknown'}


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'log'
        self.root.mkdir(mode=0o700)
        self.lifecycle = self.root / 'runs' / 'run' / 'metadata.json'
        self.lifecycle.parent.mkdir(parents=True)
        self.lifecycle.write_bytes(b'{"seq":7,"last_epoch":15,"duration":4}')
        self.original = self.lifecycle.read_bytes()
        self.bundle = fixtures.bundle()
        self.expected = contract.canonical_bytes(self.bundle)
        self.digest = hashlib.sha256(self.expected).hexdigest()
        # The caller is responsible for establishing the selected profile and
        # source provenance independently. A trusted verifier compares against
        # the locally established bundle, not a claim within the bundle itself.
        expected = copy.deepcopy(self.bundle)
        self.authorize = lambda candidate, scope: candidate == expected and scope == SCOPE

    def publish(self, bundle=None, *, mode='on', scope=SCOPE, authorize='default'):
        if publication is None:
            return None
        if authorize == 'default':
            authorize = self.authorize
        return publication.publish_usage(self.bundle if bundle is None else bundle,
            root=self.root, mode=mode, scope=scope, authorize=authorize)

    @property
    def artifact(self):
        return self.root / 'usage' / 'v1' / (self.digest + '.json')

    def assert_lifecycle_intact(self):
        self.assertEqual(self.lifecycle.read_bytes(), self.original)

    def test_authorized_bundle_is_installed_and_only_then_receipted(self):
        receipt = self.publish()
        self.assertIsInstance(receipt, dict)
        self.assertEqual(contract.validate_usage_receipt(receipt), receipt)
        self.assertEqual(receipt['bundle_sha256'], self.digest)
        self.assertEqual(receipt['scope'], SCOPE)
        self.assertFalse(receipt['duplicate'])
        self.assertEqual(self.artifact.read_bytes(), self.expected)
        self.assertEqual(stat.S_IMODE(self.artifact.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.artifact.parent.stat().st_mode), 0o700)
        self.assert_lifecycle_intact()

    def test_disabled_or_unregistered_never_publishes_or_authorizes(self):
        for mode, scope in [(None, SCOPE), ('off', SCOPE), ('invalid', SCOPE), ('on', None)]:
            with self.subTest(mode=mode, scope=scope):
                self.assertIsNone(self.publish(mode=mode, scope=scope,
                    authorize=lambda *_: self.fail('disabled publication consulted provenance')))
                self.assertFalse((self.root / 'usage').exists())
                self.assert_lifecycle_intact()

    def test_missing_untrusted_or_mismatched_provenance_rejected_before_writes(self):
        for verifier in (None, True, False, lambda *_: False):
            with self.subTest(verifier=verifier):
                with self.assertRaises(ValueError):
                    self.publish(authorize=verifier)
                self.assertFalse((self.root / 'usage').exists())
        for field in ('project_id', 'source_id', 'provider_scope', 'evidence'):
            changed = copy.deepcopy(self.bundle)
            if field == 'project_id':
                changed['project_id'] = 'sha256:' + '1' * 64
            elif field == 'source_id':
                changed['sources'][0]['source_id'] = 'sha256:' + '2' * 64
            elif field == 'provider_scope':
                changed['observations'][0]['provider_scope'] = 'sha256:' + '3' * 64
            else:
                changed['observations'][0]['measurements']['input_uncached']['evidence'] = '4' * 64
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.publish(changed)
            self.assertFalse((self.root / 'usage').exists())
        self.assert_lifecycle_intact()

    def test_schema_size_and_privacy_checks_happen_before_any_write(self):
        for change in ({'schema_version': 2},
                       {'raw_content': 'PRIVATE_PAYLOAD_SENTINEL'},
                       {'diagnostics': ['x' * (33 * 1024 * 1024)]}):
            with self.subTest(field=next(iter(change))):
                with self.assertRaises(ValueError) as error:
                    self.publish(self.bundle | change, authorize=lambda *_: True)
                self.assertNotIn('PRIVATE_PAYLOAD_SENTINEL', str(error.exception))
                self.assertFalse((self.root / 'usage').exists())
        self.assert_lifecycle_intact()

    def test_exact_duplicate_and_concurrent_attempts_install_one_file(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            receipts = list(pool.map(lambda _: self.publish(), range(16)))
        self.assertTrue(all(isinstance(item, dict) for item in receipts))
        self.assertEqual(sum(not item['duplicate'] for item in receipts), 1)
        self.assertEqual(sum(item['duplicate'] for item in receipts), 15)
        self.assertEqual([p.name for p in self.artifact.parent.glob('*.json')], [self.artifact.name])
        self.assertEqual(self.artifact.read_bytes(), self.expected)
        self.assert_lifecycle_intact()

    def test_corrupt_or_symlink_existing_address_never_overwritten(self):
        self.artifact.parent.mkdir(parents=True)
        outside = Path(self.tmp.name) / 'private-target'
        outside.write_bytes(self.expected)
        for malicious in ('corrupt', 'symlink'):
            with self.subTest(malicious=malicious):
                if self.artifact.exists() or self.artifact.is_symlink():
                    self.artifact.unlink()
                if malicious == 'corrupt':
                    self.artifact.write_bytes(b'bad')
                else:
                    self.artifact.symlink_to(outside)
                with self.assertRaises((ValueError, OSError)):
                    self.publish()
                self.assertEqual(outside.read_bytes(), self.expected)
                if malicious == 'corrupt':
                    self.assertEqual(self.artifact.read_bytes(), b'bad')
                else:
                    self.assertTrue(self.artifact.is_symlink())
        self.assert_lifecycle_intact()

    def test_symlinked_usage_directory_is_rejected(self):
        outside = Path(self.tmp.name) / 'private-directory'
        outside.mkdir()
        (self.root / 'usage').symlink_to(outside, target_is_directory=True)
        with self.assertRaises((ValueError, OSError)):
            self.publish()
        self.assertEqual(list(outside.iterdir()), [])
        self.assert_lifecycle_intact()

    def test_failed_atomic_install_never_returns_receipt_or_changes_lifecycle(self):
        if publication is None:
            self.fail('publication module is not implemented')
        with patch.object(os, 'link', side_effect=OSError('simulated disk failure')):
            with self.assertRaises(OSError):
                self.publish()
        self.assertFalse(self.artifact.exists())
        self.assert_lifecycle_intact()


if __name__ == '__main__':
    unittest.main()
