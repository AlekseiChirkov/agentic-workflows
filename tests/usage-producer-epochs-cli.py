#!/usr/bin/env python3
"""CLI epoch normalization requires an independent signed, scoped authority."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('epoch_fixtures', ROOT / 'tests/usage-producer-epochs.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
base, contract = fixtures.base, fixtures.contract


class EpochCliTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ProducerEpochTests('test_explicit_source_epochs_survive_bundle_and_resolve_without_double_count')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        source_result = self.fixture.produce()
        self.root = Path(self.fixture.temp.name)
        self.run = '1a2b3c4d'
        self.profile = self.fixture.profile
        source_hash = source_result['bundle']['sources'][0]['sha256']
        self.selection = fixtures.producer.source.manifest(self.fixture.path, self.fixture.path.read_bytes(),
                                                            owner_scope=self.fixture.scope)
        self.manifest = self.root / 'manifest.json'
        self.manifest.write_bytes(contract.canonical_bytes(self.selection))
        self.output = self.root / 'bundle.json'
        self.config = {'schema_version': 1, 'profiles': [{'profile': self.profile,
                         'sha256': hashlib.sha256(contract.canonical_bytes(self.profile)).hexdigest()}],
                       'owner_scope': self.fixture.scope, 'project_identifier': str(self.root),
                       'provider_identifier': 'PRIVATE_ACCOUNT', 'run_id': self.run,
                       'key_hex': b'private-mapping-key-that-is-long-enough-for-tests'.hex()}
        self.config_path = self.root / 'config.json'
        self.config_path.write_bytes(contract.canonical_bytes(self.config))
        self.config_path.chmod(0o600)
        self.private = self.root / 'private.pem'
        self.public = self.root / 'public.pem'
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048',
                        '-out', str(self.private)], check=True, capture_output=True)
        subprocess.run(['openssl', 'pkey', '-in', str(self.private), '-pubout', '-out', str(self.public)],
                       check=True, capture_output=True)
        bootstrap = self.root / 'bootstrap.py'
        bootstrap.write_text('import os, runpy, sys\n'
            'sys.path.insert(0, os.environ["TEST_SCRIPTS"])\n'
            'import usage_telemetry_ingest as authority\n'
            'authority.trusted_authority_key = lambda path: open(os.environ["TEST_PUBLIC"], "rb").read()\n'
            'sys.argv = sys.argv[1:]\n'
            'authority.main() if sys.argv[0].endswith("usage_telemetry_ingest.py") else runpy.run_path(sys.argv[0], run_name="__main__")\n')
        self.bootstrap = bootstrap
        bindir = self.root / 'authority-bin'
        bindir.mkdir()
        wrapper = bindir / 'python3'
        wrapper.write_text('#!/bin/sh\nexec ' + sys.executable + ' ' + str(bootstrap) + ' "$@"\n')
        wrapper.chmod(0o755)
        self.env = dict(os.environ, USAGE_TELEMETRY_CONFIG=str(self.config_path),
                        ORCHESTRAIL_LOG_ROOT=str(self.root / 'logs'), TEST_SCRIPTS=str(ROOT / 'scripts'),
                        TEST_PUBLIC=str(self.public), PATH=str(bindir) + os.pathsep + os.environ['PATH'],
                        USAGE_TELEMETRY_AUTHORITY_KEY='/etc/orchestrail/usage-authorities/test.pem')
        public_profile = base.profiles.profile()
        registration_config = copy.deepcopy(self.config)
        registration_config['profiles'] = [{'profile': public_profile,
                                           'sha256': contract.content_id(public_profile)}]
        self.config_path.write_bytes(contract.canonical_bytes(registration_config))
        started = subprocess.run(['bash', str(ROOT / 'scripts/log-step.sh'), 'run-start',
                                  '--pipeline', 'test', '--project', str(self.root)],
                                 env=self.env, text=True, capture_output=True, check=True)
        self.run = started.stdout.strip()
        self.assertRegex(self.run, r'^[0-9a-f]{8}$')
        self.active = self.root / 'logs' / '.active' / self.run
        self.assertIn('usage_authority_key_sha256=' + hashlib.sha256(self.public.read_bytes()).hexdigest(),
                      self.active.read_text())
        self.config['run_id'] = self.run
        self.fixture.scope = {'owner_kind': 'run', 'owner_id':
                              fixtures.producer.adapter._opaque(bytes.fromhex(self.config['key_hex']), 'run', self.run)}
        self.config['owner_scope'] = self.fixture.scope
        self.config_path.write_bytes(contract.canonical_bytes(self.config))
        self.selection['owner_scope'] = self.fixture.scope
        self.manifest.write_bytes(contract.canonical_bytes(self.selection))
        attestations = [{'kind': kind, 'subject_sha256': contract.content_id(subject),
                         'proof_sha256': contract.content_id(proof)}
                        for kind, profile, subject, proof in self.fixture.calls]
        self.body = {'schema_version': 1, 'kind': 'epoch_source_authority_permit',
                     'profile_sha256': contract.content_id(self.profile), 'scope': self.fixture.scope,
                     'source_sha256': source_hash, 'run_id': self.run,
                     'epoch_coverages': self.fixture.coverage, 'attestations': attestations}
        self.permit = self.root / 'permit.json'
        self.write_permit(self.body)

    def write_permit(self, body):
        message = b'orchestrail:epoch-source-authority:v1\0' + contract.canonical_bytes(body)
        signature = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(self.private)],
                                   input=message, capture_output=True, check=True).stdout.hex()
        self.permit.write_bytes(contract.canonical_bytes(body | {'signature': signature}))
        self.permit.chmod(0o600)

    def invoke(self, *, permit=True):
        args = [sys.executable, str(self.bootstrap), str(ROOT / 'scripts/usage-telemetry.py'), 'normalize',
                '--profile', self.profile['profile_id'], '--input-manifest', str(self.manifest)]
        if permit:
            args += ['--epoch-permit', str(self.permit)]
        return subprocess.run(args, env=self.env, capture_output=True, text=True, timeout=20)

    def test_real_cli_with_signed_exact_decisions_emits_resolvable_own_bundle(self):
        run = self.invoke()
        self.assertEqual(run.returncode, 0, run.stderr)
        bundle = json.loads(run.stdout)
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        self.assertEqual(len([item for item in bundle['evidence_objects'] if item.get('kind') == 'epoch_interval_evidence']), 1)
        result = self.fixture.resolve({'bundle': bundle})
        self.assertEqual(result['epochs']['aggregate']['total'], '20')
        self.assertNotIn('PRIVATE_EPOCH', run.stdout)

    def test_default_log_root_fails_closed_without_registration(self):
        self.env.pop('ORCHESTRAIL_LOG_ROOT', None)
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr.strip(), 'usage telemetry: normalization failed')

    def test_different_root_authority_key_cannot_replace_registered_key(self):
        other_private = self.root / 'other-private.pem'
        other_public = self.root / 'other-public.pem'
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048',
                        '-out', str(other_private)], check=True, capture_output=True)
        subprocess.run(['openssl', 'pkey', '-in', str(other_private), '-pubout', '-out', str(other_public)],
                       check=True, capture_output=True)
        self.private = other_private
        self.write_permit(self.body)
        self.env['TEST_PUBLIC'] = str(other_public)
        self.env['USAGE_TELEMETRY_AUTHORITY_KEY'] = '/etc/orchestrail/usage-authorities/other.pem'
        before = self.active.read_bytes()
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertEqual(self.active.read_bytes(), before)

    def test_missing_forged_or_wrong_scope_permit_never_authorizes(self):
        run = self.invoke(permit=False)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout, '')
        forged = self.body | {'scope': self.fixture.scope | {'owner_id': base.opaque('f')}}
        self.write_permit(forged)
        run = self.invoke()
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout, '')
        self.write_permit(self.body)
        data = json.loads(self.permit.read_text())
        data['signature'] = '00' * 256
        self.permit.write_bytes(contract.canonical_bytes(data))
        run = self.invoke()
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout, '')


if __name__ == '__main__':
    unittest.main()
