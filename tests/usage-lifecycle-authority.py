#!/usr/bin/env python3
"""Lifecycle projection permits require an independent scoped RSA authority."""
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('lifecycle', ROOT / 'tests/usage-lifecycle-projection.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
import usage_telemetry_ingest as ingest
contract = fixture.contract


class LifecycleAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        path = Path(cls.temp.name)
        cls.private = path / 'test-private.pem'
        cls.public = path / 'test-public.pem'
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048',
                        '-out', str(cls.private)], check=True, capture_output=True)
        subprocess.run(['openssl', 'pkey', '-in', str(cls.private), '-pubout', '-out', str(cls.public)],
                       check=True, capture_output=True)
        cls.key = cls.public.read_bytes()
        cls.fingerprint = hashlib.sha256(cls.key).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.projection = fixture.exact_projection()
        self.scope = copy.deepcopy(self.projection['scope'])
        self.body = {'schema_version': 1, 'kind': 'lifecycle_authority_permit',
                     'projection_sha256': hashlib.sha256(contract.canonical_bytes(self.projection)).hexdigest(),
                     'scope': self.scope, 'run_id': '12345678'}
        message = b'orchestrail:lifecycle-authority:v1\0' + contract.canonical_bytes(self.body)
        signature = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(self.private)],
                                   input=message, capture_output=True, check=True).stdout.hex()
        self.permit = self.body | {'signature': signature}

    def verify(self, projection=None, scope=None, run='12345678', fingerprint=None, permit=None):
        with patch.object(ingest, 'trusted_authority_key', return_value=self.key):
            return ingest.authorize_lifecycle_projection(
                self.projection if projection is None else projection,
                scope=self.scope if scope is None else scope, run_id=run,
                registered_key=self.fingerprint if fingerprint is None else fingerprint,
                permit=self.permit if permit is None else permit,
                key_path='/etc/orchestrail/usage-authorities/test.pem')

    def test_independent_permit_accepts_only_exact_projection_and_scope(self):
        self.assertIs(self.verify(), True)
        for kwargs in ({'run': '87654321'}, {'scope': self.scope | {'owner_id': 'sha256:' + 'f' * 64}},
                       {'fingerprint': '0' * 64}, {'projection': self.projection | {'cost_usd': '0'}},
                       {'permit': self.permit | {'signature': '00' * 256}}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.verify(**kwargs)

    def test_bundle_permit_domain_or_unsigned_declaration_cannot_authorize(self):
        for permit in (self.body, self.permit | {'kind': 'usage_authority_permit'},
                       self.permit | {'extra': True}):
            with self.subTest(permit=permit), self.assertRaises(ValueError):
                self.verify(permit=permit)


if __name__ == '__main__':
    unittest.main()
