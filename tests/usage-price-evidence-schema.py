#!/usr/bin/env python3
"""Shared closed schemas for pricing attestations."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)
contract = integration.contract


class PricingEvidenceSchemaTests(unittest.TestCase):
    def test_pricing_attestations_are_accepted_by_shared_schema(self):
        data, _ = integration.fixture()
        proofs = [data['price_evidence'][1], *[obj for obj in data['contexts'][0]['evidence_objects']
                                              if obj['kind'] == 'rate_parameter_evidence']]
        self.assertGreaterEqual(len(proofs), 3)
        for proof in proofs:
            with self.subTest(kind=proof['kind']):
                self.assertEqual(contract.validate_evidence_object(proof), proof)
                with self.assertRaises(ValueError):
                    contract.validate_evidence_object(proof | {'private': 'PRIVATE_SENTINEL'})
                with self.assertRaises(ValueError):
                    contract.validate_evidence_object(proof | {'schema_version': 2})

    def test_multiplier_attestation_is_closed_and_record_scoped(self):
        proof = {'schema_version': 1, 'kind': 'multiplier_evidence', 'snapshot_id': 'a' * 64,
                 'rate_id': 'b' * 64, 'scope': 'standard', 'factor': '1.2', 'applies': True,
                 'profile_id': 'profile', 'source_hash': 'c' * 64, 'record_number': 1}
        self.assertEqual(contract.validate_evidence_object(proof), proof)
        for invalid in ({'record_number': True}, {'factor': '-1'}, {'applies': 'true'},
                        {'source_hash': '/private'}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                contract.validate_evidence_object(proof | invalid)


if __name__ == '__main__':
    unittest.main()
