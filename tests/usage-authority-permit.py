#!/usr/bin/env python3
"""Test independently signed permits and trust-anchor registration."""
import builtins
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

cli_tests = load('publication_cli', ROOT / 'tests/usage-publication-cli.py')
ingest = load('usage_telemetry_ingest', ROOT / 'scripts/usage_telemetry_ingest.py')
contract = cli_tests.contract
try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:
    Ed25519PrivateKey = None


@unittest.skipIf(Ed25519PrivateKey is None, 'optional Ed25519 verifier unavailable')
class AuthorityPermitTests(unittest.TestCase):
    def setUp(self):
        self.fixture = cli_tests.PublicationCliTests(methodName='test_authorized_bundle_is_visible_before_receipt_and_exact_repeat')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.private = Ed25519PrivateKey.generate()
        self.public = self.private.public_key().public_bytes(serialization.Encoding.PEM,
                                                            serialization.PublicFormat.SubjectPublicKeyInfo)
        self.key_path = self.fixture.root / 'untrusted-public-key.pem'
        self.key_path.write_bytes(self.public)
        self.permit_path = self.fixture.root / 'permit.json'
        self.fixture.env.update(USAGE_TELEMETRY_AUTHORITY_KEY=str(self.key_path),
                                USAGE_TELEMETRY_AUTHORITY_PERMIT=str(self.permit_path))
        # Simulate the fingerprint written by trusted run registration. The
        # loader alone is replaced below; signature verification stays real.
        with self.fixture.lifecycle.open('ab') as stream:
            stream.write(('usage_authority_key_sha256=' + hashlib.sha256(self.public).hexdigest() + '\n').encode())
        self.fixture.original = self.fixture.lifecycle.read_bytes()
        self.write_permit(self.fixture.bundle)

    def write_permit(self, bundle, *, key=None):
        body = {'schema_version': 1, 'kind': 'usage_authority_permit',
                'bundle_sha256': hashlib.sha256(contract.canonical_bytes(bundle)).hexdigest(),
                'profile_id': bundle['profile_id'], 'profile_version': bundle['profile_version'],
                'run_id': bundle['run_id'], 'scope': self.fixture.config['owner_scope']}
        signature = (key or self.private).sign(b'orchestrail:usage-authority:v1\0' + contract.canonical_bytes(body))
        body['signature'] = signature.hex()
        self.permit_path.write_bytes(contract.canonical_bytes(body))
        self.permit_path.chmod(0o600)

    def invoke_with_trusted_loader(self, public=None):
        with patch.dict(os.environ, self.fixture.env, clear=True), \
             patch.object(ingest, 'trusted_authority_key', return_value=public or self.public):
            return ingest.ingest(str(self.fixture.output), str(self.fixture.log_root))

    def test_valid_independent_permit_accepts_exact_bundle(self):
        receipt = self.invoke_with_trusted_loader()
        self.assertFalse(receipt['duplicate'])
        self.assertEqual(self.fixture.artifact().read_bytes(), contract.canonical_bytes(self.fixture.bundle))
        self.assertEqual(self.fixture.lifecycle.read_bytes(), self.fixture.original)

    def test_unsigned_or_mismatched_permit_cannot_authorize(self):
        wrong_signer = Ed25519PrivateKey.generate()
        self.write_permit(self.fixture.bundle, key=wrong_signer)
        with self.assertRaises(ValueError):
            self.invoke_with_trusted_loader()
        changed = copy.deepcopy(self.fixture.bundle)
        changed['project_id'] = 'sha256:' + '1' * 64
        self.write_permit(changed)
        with self.assertRaises(ValueError):
            self.invoke_with_trusted_loader()
        self.assertFalse((self.fixture.log_root / 'usage').exists())

    def test_different_authority_key_cannot_replace_registered_key(self):
        another = Ed25519PrivateKey.generate()
        public = another.public_key().public_bytes(serialization.Encoding.PEM,
                                                  serialization.PublicFormat.SubjectPublicKeyInfo)
        self.write_permit(self.fixture.bundle, key=another)
        with self.assertRaises(ValueError):
            self.invoke_with_trusted_loader(public)
        self.assertFalse((self.fixture.log_root / 'usage').exists())

    def test_missing_crypto_dependency_fails_closed(self):
        original_import = builtins.__import__
        def without_crypto(name, *args, **kwargs):
            if name.startswith('cryptography'):
                raise ImportError('unavailable')
            return original_import(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=without_crypto):
            with self.assertRaises(ValueError):
                self.invoke_with_trusted_loader()
        self.assertFalse((self.fixture.log_root / 'usage').exists())

    def test_user_owned_anchor_fails_closed_at_real_cli(self):
        result = self.fixture.ingest()
        self.assertEqual(result.stdout.strip(), '')
        self.assertFalse((self.fixture.log_root / 'usage').exists())

    def test_self_hmac_without_independent_permit_cannot_authorize(self):
        self.permit_path.unlink()
        result = self.fixture.ingest()
        self.assertEqual(result.stdout.strip(), '')
        self.assertFalse((self.fixture.log_root / 'usage').exists())


if __name__ == '__main__':
    unittest.main()
