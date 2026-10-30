#!/usr/bin/env python3
"""Verify signed offline analysis with an isolated synthetic trust anchor."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract
import usage_telemetry_ingest as ingest
import usage_telemetry_exports as exports


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixtures = load('evidence_report', ROOT / 'tests/usage-report-evidence-fields.py')
cli = load('usage_cli', ROOT / 'scripts/usage-telemetry.py')
synthetic_rsa = load('synthetic_rsa', ROOT / 'tests/usage-rsa-fixture.py')


class AnalyzeCliEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.EvidenceBackedReportTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.base = self.fixture.base
        self.manifest = self.base.directory / 'manifest.json'
        self.authority = self.base.directory / 'authority.json'
        self.key_path = self.base.directory / 'user-key.pem'
        self.output = self.base.directory / 'report'
        self.manifest.write_bytes(contract.canonical_bytes(self.base.manifest))
        inputs = []
        for item in self.base.manifest['inputs']:
            value = contract.parse_json(Path(item['local_path']).read_bytes())
            inputs.append({'sha256': item['sha256'],
                           'proof': self.fixture.verify_input(item, value, self.fixture.scope)})
        decisions = [{'kind': kind, 'scope': scope, 'subject': subject, 'evidence': evidence}
                     for kind, scope, subject, evidence in self.base.authority.allowed]
        self.document = {'schema_version': 1, 'kind': 'analysis_authority',
                         'manifest_sha256': contract.content_id(self.base.manifest),
                         'inputs': inputs, 'evidence': decisions}
        self.public = synthetic_rsa.PUBLIC_KEY
        self.key_path.write_bytes(self.public)
        self.write_authority()

    def write_authority(self, *, invalid_signature=False):
        body = copy.deepcopy(self.document)
        signature = synthetic_rsa.sign(b'orchestrail:analysis-authority:v1\0' + contract.canonical_bytes(body))
        if invalid_signature:
            signature = bytes([signature[0] ^ 1]) + signature[1:]
        body['signature'] = signature.hex()
        self.authority.write_bytes(contract.canonical_bytes(body))
        self.authority.chmod(0o600)

    def args(self, *, scenario='baseline'):
        return ['analyze', '--corpus-manifest', str(self.manifest), '--scenario', scenario,
                '--authority', str(self.authority),
                '--authority-key', str(self.key_path)]

    def invoke_synthetic_anchor(self, *, scenario='baseline', public=None):
        import io
        import tarfile
        class Stream:
            def __init__(self, fd):
                self.buffer = io.BytesIO()
                self.fd = fd
            def fileno(self):
                return self.fd
        read_fd, write_fd = os.pipe()
        self.addCleanup(os.close, read_fd)
        self.addCleanup(os.close, write_fd)
        stream = Stream(write_fd)
        with patch.object(ingest, 'trusted_authority_key', return_value=public or self.public), \
                patch.object(sys, 'stdout', stream):
            cli.main(self.args(scenario=scenario))
        with tarfile.open(fileobj=io.BytesIO(stream.buffer.getvalue())) as archive:
            return {member.name: archive.extractfile(member).read() for member in archive.getmembers()}

    def test_signed_synthetic_authority_builds_reproducible_report(self):
        expected = self.fixture.analyze()
        first = self.invoke_synthetic_anchor()
        report = json.loads(first['report.json'])
        self.assertEqual(report['corpus_id'], expected['corpus_id'])
        self.assertEqual(report['totals']['total_cost'], '0.00578')
        self.assertEqual(report['coverage']['pricing'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(set(first), {'report.json', 'report.csv', 'report.md'})
        self.assertEqual(first, self.invoke_synthetic_anchor())

    def test_regular_file_stdout_is_rejected_without_writes(self):
        with tempfile.TemporaryFile() as output:
            process = subprocess.run([sys.executable, str(ROOT / 'scripts/usage-telemetry.py'), *self.args()],
                                     stdout=output, stderr=subprocess.PIPE, check=False)
            self.assertNotEqual(process.returncode, 0)
            output.seek(0)
            self.assertEqual(output.read(), b'')

    def test_self_signed_user_owned_key_is_rejected_by_real_cli(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/usage-telemetry.py'), *self.args()],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertNotIn(str(self.base.directory).encode(), result.stderr)

    def test_signed_rsa_authority_works_without_optional_crypto_module(self):
        import builtins
        original = builtins.__import__
        def no_crypto(name, *args, **kwargs):
            if name.startswith('cryptography'):
                raise ImportError('optional crypto unavailable')
            return original(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=no_crypto):
            report = self.invoke_synthetic_anchor()
        self.assertEqual(json.loads(report['report.json'])['totals']['total_cost'], '0.00578')

    def test_optional_ed25519_authority(self):
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        except ImportError:
            self.skipTest('optional Ed25519 verifier unavailable')
        private = Ed25519PrivateKey.generate()
        public = private.public_key().public_bytes(serialization.Encoding.PEM,
                                                    serialization.PublicFormat.SubjectPublicKeyInfo)
        signature = private.sign(b'orchestrail:analysis-authority:v1\0' + contract.canonical_bytes(self.document))
        self.authority.write_bytes(contract.canonical_bytes(dict(self.document, signature=signature.hex())))
        report = self.invoke_synthetic_anchor(public=public)
        self.assertEqual(json.loads(report['report.json'])['totals']['total_cost'], '0.00578')

    def test_signature_and_exact_scope_are_required(self):
        self.write_authority(invalid_signature=True)
        with self.assertRaises(ValueError):
            self.invoke_synthetic_anchor()
        self.assertFalse(self.output.exists())
        self.document['inputs'][0]['proof']['scope'] = {'owner_kind': 'run', 'owner_id': 'sha256:' + 'f' * 64}
        self.write_authority()
        with self.assertRaises(ValueError):
            self.invoke_synthetic_anchor()
        self.assertFalse(self.output.exists())

    def test_scenario_must_match_explicit_corpus(self):
        with self.assertRaises(ValueError):
            self.invoke_synthetic_anchor(scenario='different')
        self.assertFalse(self.output.exists())

    def test_authority_binds_manifest_cutoff_and_selection(self):
        manifest = copy.deepcopy(self.base.manifest)
        manifest['as_of'] = '2029-01-03T00:00:00Z'
        self.manifest.write_bytes(contract.canonical_bytes(manifest))
        with self.assertRaises(ValueError):
            self.invoke_synthetic_anchor()
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
