#!/usr/bin/env python3
"""Offline integration checks for authorized immutable usage ingestion."""
import copy
import hashlib
import hmac
import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

base = load('normalization_fixtures', ROOT / 'tests/usage-normalize-cli.py')
contract = base.contract


class PublicationCliTests(unittest.TestCase):
    def setUp(self):
        fixture = base.NormalizeCliTests(methodName='test_normalize_emits_self_contained_sanitized_bundle')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.__dict__.update({k: v for k, v in fixture.__dict__.items() if not k.startswith('_')})
        self.run_cli = fixture.run_cli
        self.write_config = fixture.write_config
        started = subprocess.run(['bash', str(ROOT / 'scripts/log-step.sh'), 'run-start',
            '--pipeline', 'test', '--project', str(self.root)], env=self.env,
            text=True, capture_output=True, timeout=10)
        self.assertRegex(started.stdout.strip(), r'^[0-9a-f]{8}$')
        self.run_id = started.stdout.strip()
        self.lifecycle = self.log_root / '.active' / self.run_id
        self.original = self.lifecycle.read_bytes()
        self.config['run_id'] = self.run_id
        self.config['project_identifier'] = str(self.root)
        opaque_run = base.load('adapter_fixture', ROOT / 'scripts/usage_telemetry_adapter.py')._opaque(
            bytes.fromhex(self.config['key_hex']), 'run', self.run_id)
        self.config['owner_scope'] = {'owner_kind': 'run', 'owner_id': opaque_run}
        self.selection['owner_scope'] = copy.deepcopy(self.config['owner_scope'])
        self.write_config()
        fixture.write_manifest()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.bundle = json.loads(self.output.read_text())
        self.provenance = self.root / 'private-provenance.json'
        self.env.update(ORCHESTRAIL_USAGE_MODE='on',
                        USAGE_TELEMETRY_PROVENANCE=str(self.provenance))
        self.sign()

    def sign(self, *, key=None):
        body = {'schema_version': 1, 'kind': 'usage_provenance',
                'bundle_sha256': hashlib.sha256(contract.canonical_bytes(self.bundle)).hexdigest(),
                'profile_id': self.bundle['profile_id'], 'profile_version': self.bundle['profile_version'],
                'scope': self.config['owner_scope']}
        key = key if key is not None else bytes.fromhex(self.config['key_hex'])
        body['mac'] = hmac.new(key, b'orchestrail:usage-provenance:v1\0' +
                               contract.canonical_bytes(body), hashlib.sha256).hexdigest()
        self.provenance.write_bytes(contract.canonical_bytes(body))
        self.provenance.chmod(0o600)

    def ingest(self, *, env=None, manifest=None):
        result = subprocess.run(['bash', str(ROOT / 'scripts/log-step.sh'), 'usage-ingest',
                                 '--manifest', str(manifest or self.output)],
                                env=env or self.env, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0)
        self.assertLessEqual(len(result.stderr.encode()), 512)
        self.assertLessEqual(len(result.stderr.splitlines()), 1)
        self.assertNotIn('PRIVATE_', result.stdout + result.stderr)
        self.assertNotIn(str(self.source), result.stdout + result.stderr)
        self.assertEqual(self.lifecycle.read_bytes(), self.original)
        return result

    def artifact(self):
        return self.log_root / 'usage' / 'v1' / (hashlib.sha256(contract.canonical_bytes(self.bundle)).hexdigest() + '.json')

    def no_receipt(self, result):
        self.assertEqual(result.stdout.strip(), '')
        self.assertFalse(self.artifact().exists())

    def test_authorized_bundle_is_visible_before_receipt_and_exact_repeat(self):
        # A normalized bundle and its author-controlled MAC alone are not an
        # independent authorization to publish.
        self.no_receipt(self.ingest())
        self.no_receipt(self.ingest())

    def test_disabled_invalid_and_unregistered_scope_do_not_publish(self):
        for mode in (None, 'off', 'invalid'):
            env = self.env.copy()
            if mode is None:
                env.pop('ORCHESTRAIL_USAGE_MODE', None)
            else:
                env['ORCHESTRAIL_USAGE_MODE'] = mode
            with self.subTest(mode=mode):
                result = self.ingest(env=env)
                self.no_receipt(result)
                self.assertIn('collection_disabled', result.stderr)
        env = self.env.copy()
        del env['USAGE_TELEMETRY_CONFIG']
        self.no_receipt(self.ingest(env=env))

    def test_unsigned_forged_or_changed_bundle_is_rejected(self):
        self.provenance.unlink()
        self.no_receipt(self.ingest())
        self.sign(key=b'wrong key' * 4)
        self.no_receipt(self.ingest())
        self.sign()
        for field in ('project_id', 'source_id', 'provider_scope', 'evidence'):
            changed = copy.deepcopy(self.bundle)
            if field == 'project_id':
                changed['project_id'] = 'sha256:' + '1' * 64
            elif field == 'source_id':
                changed['sources'][0]['source_id'] = 'sha256:' + '2' * 64
            elif field == 'provider_scope':
                changed['observations'][0]['provider_scope'] = 'sha256:' + '3' * 64
            else:
                measurement = next(iter(changed['observations'][0]['measurements'].values()))
                measurement['evidence'] = '4' * 64
            self.output.write_bytes(contract.canonical_bytes(changed))
            self.no_receipt(self.ingest())
        self.output.write_bytes(contract.canonical_bytes(self.bundle))

    def test_signed_bundle_without_registered_lifecycle_run_is_rejected(self):
        self.lifecycle.unlink()
        result = subprocess.run(['bash', str(ROOT / 'scripts/log-step.sh'), 'usage-ingest',
            '--manifest', str(self.output)], env=self.env, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), '')
        self.assertFalse(self.artifact().exists())

    def test_invalid_private_registration_and_profile_cannot_authorize(self):
        self.config_path.chmod(0o644)
        self.no_receipt(self.ingest())
        self.config_path.chmod(0o600)
        self.config['profiles'][0]['sha256'] = '0' * 64
        self.write_config()
        self.no_receipt(self.ingest())

    def test_normalizer_produces_verifiable_private_provenance(self):
        self.output.unlink()
        self.provenance.unlink()
        result = subprocess.run([sys.executable, str(base.CLI), 'normalize', '--profile',
            'synthetic-profile', '--input-manifest', str(self.manifest), '--output', str(self.output),
            '--provenance-output', str(self.provenance)], env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.provenance.stat().st_mode & 0o777, 0o600)
        self.no_receipt(self.ingest())

    def test_concurrent_publications_create_one_file_and_valid_receipts(self):
        # Concurrent author-controlled submissions cannot bypass authority.
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: self.ingest(), range(6)))
        for result in results:
            self.assertEqual(result.stdout.strip(), '')
        self.assertFalse((self.log_root / 'usage').exists())

    def test_corrupt_or_symlink_address_and_parent_never_return_receipt(self):
        artifact = self.artifact()
        artifact.parent.mkdir(parents=True)
        outside = self.root / 'outside'
        outside.write_bytes(contract.canonical_bytes(self.bundle))
        for kind in ('corrupt', 'symlink'):
            artifact.unlink(missing_ok=True)
            if kind == 'corrupt':
                artifact.write_bytes(b'corrupt')
            else:
                artifact.symlink_to(outside)
            result = self.ingest()
            self.assertEqual(result.stdout.strip(), '')
            self.assertEqual(outside.read_bytes(), contract.canonical_bytes(self.bundle))
            self.assertTrue(artifact.is_symlink() if kind == 'symlink' else artifact.read_bytes() == b'corrupt')
        artifact.unlink()
        artifact.parent.rmdir()
        (self.log_root / 'usage').rmdir()
        (self.log_root / 'usage').symlink_to(self.root, target_is_directory=True)
        self.assertEqual(self.ingest().stdout.strip(), '')
        self.assertFalse((self.root / 'v1').exists())

    def test_missing_python_fails_closed_and_lifecycle_logging_remains_usable(self):
        tools = self.root / 'without-python'
        tools.mkdir()
        (tools / 'dirname').symlink_to('/usr/bin/dirname')
        env = self.env | {'PATH': str(tools)}
        # Invoke bash by its absolute path because PATH intentionally omits Python.
        result = subprocess.run(['/bin/bash', str(ROOT / 'scripts/log-step.sh'), 'usage-ingest',
                                 '--manifest', str(self.output)], env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), '')
        self.assertIn('dependency_unavailable', result.stderr)
        self.assertFalse(self.artifact().exists())
        self.assertEqual(self.lifecycle.read_bytes(), self.original)


if __name__ == '__main__':
    unittest.main()
