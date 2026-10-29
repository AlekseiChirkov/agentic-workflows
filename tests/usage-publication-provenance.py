#!/usr/bin/env python3
"""Verify that a caller-held signing key does not authorize forged provenance."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication_cli_tests', ROOT / 'tests/usage-publication-cli.py')
cli_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli_tests)
contract = cli_tests.contract


class ProvenanceAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = cli_tests.PublicationCliTests(methodName='test_authorized_bundle_is_visible_before_receipt_and_exact_repeat')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.original = copy.deepcopy(self.fixture.bundle)

    def reject_forgery(self, changed):
        contract.validate_usage_bundle(changed)
        self.fixture.bundle = changed
        self.fixture.output.write_bytes(contract.canonical_bytes(changed))
        # The candidate author controls this existing key. A valid MAC from the
        # author must never establish independent source provenance.
        self.fixture.sign()
        result = self.fixture.ingest()
        self.assertEqual(result.stdout.strip(), '', 'self-signed forgery received acceptance')
        self.assertFalse((self.fixture.log_root / 'usage').exists())

    def test_forged_project_with_valid_mac(self):
        changed = copy.deepcopy(self.original)
        changed['project_id'] = 'sha256:' + '1' * 64
        self.reject_forgery(changed)

    def test_forged_source_with_valid_mac(self):
        changed = copy.deepcopy(self.original)
        changed['sources'][0]['source_id'] = 'sha256:' + '2' * 64
        self.reject_forgery(changed)

    def test_forged_provider_with_valid_mac(self):
        changed = copy.deepcopy(self.original)
        changed['observations'][0]['provider_scope'] = 'sha256:' + '3' * 64
        self.reject_forgery(changed)

    def test_forged_measurement_and_consistent_evidence_with_valid_mac(self):
        changed = copy.deepcopy(self.original)
        observation = changed['observations'][0]
        fake_record = copy.deepcopy(self.fixture.raw)
        fake_record['usage']['output'] += 1
        forged = contract.normalize_source_counters(self.fixture.profile, fake_record,
            profile_version=observation['profile_version'], source_hash=observation['source_hash'],
            record_number=observation['record_number'])
        observation['measurements'] = forged['measurements']
        changed['evidence_objects'] = forged['evidence_objects']
        self.reject_forgery(changed)

    def test_forged_evidence_path_with_valid_mac(self):
        changed = copy.deepcopy(self.original)
        measurement = changed['observations'][0]['measurements']['output_total']
        old = measurement['evidence']
        proof = next(item for item in changed['evidence_objects'] if contract.content_id(item) == old)
        proof['path'] = ['usage', 'unrelated_field']
        measurement['evidence'] = contract.content_id(proof)
        self.reject_forgery(changed)

    def test_genuine_normalization_is_accepted(self):
        result = self.fixture.ingest()
        self.assertTrue(result.stdout.strip(), 'authorized normalization did not receive a receipt')
        self.assertEqual(self.fixture.artifact().read_bytes(), contract.canonical_bytes(self.original))


if __name__ == '__main__':
    unittest.main()
