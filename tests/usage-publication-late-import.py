#!/usr/bin/env python3
"""Explicit independently certified late imports never alter closed lifecycle state."""
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('authority_tests', ROOT / 'tests/usage-authority-permit.py')
authority_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authority_tests)
ingest, contract = authority_tests.ingest, authority_tests.contract
rsa_spec = importlib.util.spec_from_file_location('rsa_tests', ROOT / 'tests/usage-authority-rsa-permit.py')
rsa_tests = importlib.util.module_from_spec(rsa_spec)
rsa_spec.loader.exec_module(rsa_tests)


@unittest.skipIf(authority_tests.Ed25519PrivateKey is None, 'optional verifier unavailable')
class LateImportTests(unittest.TestCase):
    def setUp(self):
        self.auth = authority_tests.AuthorityPermitTests('test_valid_independent_permit_accepts_exact_bundle')
        self.auth.setUp()
        self.addCleanup(self.auth.doCleanups)
        self.fixture = self.auth.fixture
        line = next(line for line in self.fixture.lifecycle.read_text().splitlines() if line.startswith('file='))
        self.run_file = Path(line.split('=', 1)[1])
        self.certificate_path = self.fixture.root / 'late-import.json'
        self.registration_body = {'schema_version': 1, 'kind': 'usage_registration_certificate',
                                  'run_id': self.fixture.run_id, 'scope': self.fixture.config['owner_scope'],
                                  'project_sha256': hashlib.sha256(self.fixture.config['project_identifier'].encode()).hexdigest(),
                                  'registration_key_fingerprint': ingest.key_fingerprint(bytes.fromhex(self.fixture.config['key_hex'])),
                                  'authority_key_sha256': hashlib.sha256(self.auth.public).hexdigest()}
        registration_signature = rsa_tests.sign(b'orchestrail:usage-registration-certificate:v1\0' +
                                                contract.canonical_bytes(self.registration_body))
        self.registration_certificate = self.registration_body | {'signature': registration_signature}
        self.body = {'schema_version': 1, 'kind': 'usage_late_import_certificate',
                     'run_id': self.fixture.run_id, 'scope': self.fixture.config['owner_scope'],
                     'profile_id': self.fixture.bundle['profile_id'],
                     'profile_version': self.fixture.bundle['profile_version'],
                     'bundle_sha256': hashlib.sha256(contract.canonical_bytes(self.fixture.bundle)).hexdigest(),
                     'project_sha256': hashlib.sha256(self.fixture.config['project_identifier'].encode()).hexdigest(),
                     'registration_key_fingerprint': ingest.key_fingerprint(bytes.fromhex(self.fixture.config['key_hex'])),
                     'authority_key_sha256': hashlib.sha256(self.auth.public).hexdigest(),
                     'registration_sha256': contract.content_id(self.registration_certificate)}
        self.write_certificate(self.body)
        ended = subprocess.run(['bash', str(ROOT / 'scripts/log-step.sh'), 'run-end', '--run', self.fixture.run_id,
                                '--outcome', 'completed'], env=self.fixture.env, text=True, capture_output=True, timeout=10)
        self.assertEqual(ended.returncode, 0)
        self.assertFalse(self.fixture.lifecycle.exists())
        self.closed = self.run_file.read_bytes()

    def write_certificate(self, body, *, signer=None):
        signature = (signer or self.auth.private).sign(b'orchestrail:usage-late-import:v1\0' + contract.canonical_bytes(body))
        self.certificate_path.write_bytes(contract.canonical_bytes({'registration': self.registration_certificate,
                                                                     'authorization': body | {'signature': signature.hex()}}))
        self.certificate_path.chmod(0o600)

    def invoke(self, *, certificate=True):
        with patch.dict(os.environ, self.fixture.env | {'USAGE_TELEMETRY_REGISTRATION_KEY':
                        '/etc/orchestrail/usage-registration-authorities/test.pem'}, clear=True), \
             patch.object(ingest, 'trusted_authority_key', return_value=self.auth.public), \
             patch.object(ingest, 'trusted_registration_key', return_value=rsa_tests.PUBLIC):
            return ingest.ingest(str(self.fixture.output), str(self.fixture.log_root),
                                 late_certificate=str(self.certificate_path) if certificate else None)

    def test_explicit_authorized_late_import_is_new_artifact_only(self):
        with self.assertRaises((ValueError, OSError)):
            self.invoke(certificate=False)
        receipt = self.invoke()
        self.assertFalse(receipt['duplicate'])
        self.assertEqual(self.fixture.artifact().read_bytes(), contract.canonical_bytes(self.fixture.bundle))
        self.assertTrue(self.invoke()['duplicate'])
        self.assertEqual(self.run_file.read_bytes(), self.closed)
        self.assertFalse(self.fixture.lifecycle.exists())

    def test_run_authority_cannot_self_certify_its_own_registration(self):
        registration = self.registration_body | {'signature': self.auth.private.sign(
            b'orchestrail:usage-registration-certificate:v1\0' +
            contract.canonical_bytes(self.registration_body)).hex()}
        self.registration_certificate = registration
        self.write_certificate(self.body | {'registration_sha256': contract.content_id(registration)})
        with self.assertRaises((ValueError, OSError)):
            self.invoke()
        self.assertFalse(self.fixture.artifact().exists())
        self.assertEqual(self.run_file.read_bytes(), self.closed)

    def test_unsigned_wrong_scope_key_or_bundle_cannot_import_late(self):
        for change in ({'run_id': '87654321'}, {'scope': self.body['scope'] | {'owner_id': 'sha256:' + 'f' * 64}},
                       {'bundle_sha256': '0' * 64}, {'authority_key_sha256': '0' * 64},
                       {'registration_key_fingerprint': '0' * 64}):
            with self.subTest(change=change):
                self.write_certificate(self.body | change)
                with self.assertRaises((ValueError, OSError)):
                    self.invoke()
                self.assertFalse(self.fixture.artifact().exists())
                self.assertEqual(self.run_file.read_bytes(), self.closed)
        self.write_certificate(self.body, signer=authority_tests.Ed25519PrivateKey.generate())
        with self.assertRaises((ValueError, OSError)):
            self.invoke()
        self.assertFalse(self.fixture.artifact().exists())


if __name__ == '__main__':
    unittest.main()
