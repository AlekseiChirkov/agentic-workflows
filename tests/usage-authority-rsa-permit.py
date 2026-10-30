#!/usr/bin/env python3
"""Offline permit integration using an explicitly untrusted test-only key."""
import builtins
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('publication_cli', ROOT / 'tests/usage-publication-cli.py')
cli_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli_tests)
import usage_telemetry_ingest as ingest

# This private key is public test data, never a production trust anchor.
PUBLIC = b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4tnAxwMRVgfe5CVDVfWv\nqGPy65z/AnBBBOfk7wpgo4UNGCP2yYXxdD3JKyNIXl9MqSaOHze8ds0CR/zDcYV4\nfXiUwudakEMU/2+iA5G9ET4FCNBh8QwRumRq0P2LCJe8iNRRKOU60ZxW/0ze05n4\nL5Sbs7RAGZ7qIf9SHCujJA8JffiY1cUtTPzqPJ9ghfR2KG43ZCxH8vulENGQqToj\nCFlm0FXQmBezF/rXkFWN4ybmFk8UOSO/NdLATqG6HWvJnS+f01OVJDjrva5ev0VN\nbCP/8rizXdGsl7EjxX9RPdRO6h70C2cR/g+/2Nm2UbnSGpjnB/JCmW6E06OXuZAV\nNQIDAQAB\n-----END PUBLIC KEY-----\n'
MODULUS = 28637234946750856940269291971611360600378819823323593145280496584313791637770336785509356566968628447389762428074082098385608494130546256401295544507972935798134610818668689395241971432954022603170407762794345974826857861262970499946462197998014853820903499052615276981307834711512558317049061075489555375596900020081280093327574734652808094436241220792232055207921997062580866785785448075943715176503893074276775778054267817786038249687415371046294552106088736402329470053272382729681248642332029501322301197730815388208763543351085155516064878618951539482813432911928851045776209401649229476577683566047708098598197
PRIVATE_EXPONENT = 5405449057918145105506832420385710916077729994116674687637401513591616330546682808263171878659160752070358059058095924410320427798677425954990715677188141085048510049778613945768662093342047036216481212592084728956095719559234883647217764321443501368562594183901876556712522228645896251904350367492310370841162396841578644655563267791538205393767558626363410316720822968549710093401452724591987315786821354971617041025188595913749970619419258986741726836338709350075131913760747232666303900221153015881226697299430028923280797873029953630202823026848651168594112956237265261437138275802159450902613335482194711875137


def sign(message):
    digest = bytes.fromhex('3031300d060960864801650304020105000420') + hashlib.sha256(message).digest()
    encoded = b'\x00\x01' + b'\xff' * (256 - len(digest) - 3) + b'\x00' + digest
    return pow(int.from_bytes(encoded, 'big'), PRIVATE_EXPONENT, MODULUS).to_bytes(256, 'big').hex()


class RsaPermitTests(unittest.TestCase):
    def setUp(self):
        self.fixture = cli_tests.PublicationCliTests(methodName='test_authorized_bundle_is_visible_before_receipt_and_exact_repeat')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.permit_path = self.fixture.root / 'rsa-permit.json'
        self.fixture.env.update(USAGE_TELEMETRY_AUTHORITY_KEY=str(self.fixture.root / 'test-public.pem'),
                                USAGE_TELEMETRY_AUTHORITY_PERMIT=str(self.permit_path))
        with self.fixture.lifecycle.open('ab') as stream:
            stream.write(('usage_authority_key_sha256=' + hashlib.sha256(PUBLIC).hexdigest() + '\n').encode())
        self.body = {'schema_version': 1, 'kind': 'usage_authority_permit',
                      'bundle_sha256': hashlib.sha256(cli_tests.contract.canonical_bytes(self.fixture.bundle)).hexdigest(),
                      'profile_id': self.fixture.bundle['profile_id'],
                      'profile_version': self.fixture.bundle['profile_version'],
                      'run_id': self.fixture.bundle['run_id'], 'scope': self.fixture.config['owner_scope']}

    def write_permit(self, body):
        permit = copy.deepcopy(body)
        permit['signature'] = sign(b'orchestrail:usage-authority:v1\0' + cli_tests.contract.canonical_bytes(body))
        self.permit_path.write_bytes(cli_tests.contract.canonical_bytes(permit))
        self.permit_path.chmod(0o600)

    def invoke(self):
        original_import = builtins.__import__
        def without_crypto(name, *args, **kwargs):
            if name.startswith('cryptography'):
                raise ImportError('not installed')
            return original_import(name, *args, **kwargs)
        with patch.dict(os.environ, self.fixture.env, clear=True), \
             patch.object(ingest, 'trusted_authority_key', return_value=PUBLIC), \
             patch('builtins.__import__', side_effect=without_crypto):
            return ingest.ingest(str(self.fixture.output), str(self.fixture.log_root))

    def test_valid_permit_publishes_without_external_libraries(self):
        self.write_permit(self.body)
        receipt = self.invoke()
        self.assertFalse(receipt['duplicate'])
        self.assertEqual(self.fixture.artifact().read_bytes(), cli_tests.contract.canonical_bytes(self.fixture.bundle))

    def test_signed_permit_for_another_bundle_scope_or_profile_is_rejected(self):
        for field, value in (('bundle_sha256', '0' * 64), ('scope', {'owner_kind': 'run', 'owner_id': 'other'}),
                             ('profile_version', 999), ('run_id', 'other')):
            with self.subTest(field=field):
                body = copy.deepcopy(self.body)
                body[field] = value
                self.write_permit(body)
                with self.assertRaises(ValueError):
                    self.invoke()
        self.assertFalse((self.fixture.log_root / 'usage').exists())


if __name__ == '__main__':
    unittest.main()
