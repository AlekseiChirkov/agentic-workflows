#!/usr/bin/env python3
"""Caller token totals must include proven cache writes exactly once."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

lifecycle = load('lifecycle', 'tests/usage-lifecycle-projection.py')
states = load('states', 'tests/usage-lifecycle-projection-states.py')
contract = lifecycle.contract


class TokenScalarTests(unittest.TestCase):
    def setUp(self):
        self.fixture = lifecycle.LifecycleProjectionTests('test_valid_exact_projection_and_replay_preserve_first_payload')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.env = self.fixture.authority_env

    def bind(self, value):
        value['scope'] = copy.deepcopy(self.fixture.value['scope'])
        self.fixture.write(value)
        permit = {'schema_version': 1, 'kind': 'lifecycle_authority_permit',
                  'projection_sha256': hashlib.sha256(contract.canonical_bytes(value)).hexdigest(),
                  'scope': value['scope'], 'run_id': self.fixture.run}
        message = b'orchestrail:lifecycle-authority:v1\0' + contract.canonical_bytes(permit)
        signature = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(self.fixture.private_key)],
                                   input=message, capture_output=True, check=True).stdout.hex()
        self.fixture.permit_path.write_bytes(contract.canonical_bytes(permit | {'signature': signature}))

    def test_split_writes_must_be_included_in_input_scalar(self):
        value = states.cache_projection()
        self.bind(value)
        before = self.fixture.snapshot()
        self.fixture.correlated('--usage-file', str(self.fixture.path), '--tokens-in', '750000')
        self.assertEqual(self.fixture.snapshot(), before)
        self.fixture.correlated('--usage-file', str(self.fixture.path), '--tokens-in', '750200')
        self.assertNotEqual(self.fixture.snapshot(), before)

    def test_unsplit_write_counts_as_tokens_even_when_pricing_unknown(self):
        value = states.cache_projection()
        first = value['contributors'][0]
        del first['measurements']['input_cache_write']
        proof = {'schema_version': 1, 'kind': 'measurement_evidence', 'profile_id': 'profile',
                 'source_hash': 'a' * 64, 'record_number': 1, 'field': 'input_cache_write_unsplit', 'value': 200}
        value['evidence_objects'].append(proof)
        first['measurements']['input_cache_write_unsplit'] = {'measurement_state': 'final', 'value': 200,
                                                               'reasons': [], 'evidence': contract.content_id(proof)}
        first['price_snapshot_id'] = first['priced_usd'] = None
        value.pop('cost_usd')
        value['completeness']['pricing'] = 'partial'
        value.update(priced_subtotal_usd='0.5', subtotal_quality='subtotal_only')
        self.bind(value)
        before = self.fixture.snapshot()
        self.fixture.correlated('--usage-file', str(self.fixture.path), '--tokens-in', '750000')
        self.assertEqual(self.fixture.snapshot(), before)
        self.fixture.correlated('--usage-file', str(self.fixture.path), '--tokens-in', '750200')
        self.assertNotEqual(self.fixture.snapshot(), before)

    def test_nonempty_scope_cannot_claim_inventory_not_applicable(self):
        value = states.unpriced_projection()
        value['completeness']['inventory'] = 'not_applicable'
        self.bind(value)
        before = self.fixture.snapshot()
        self.fixture.correlated('--usage-file', str(self.fixture.path), '--tokens-in', '750000')
        self.assertEqual(self.fixture.snapshot(), before)

    def test_nonempty_dimensions_cannot_claim_not_applicable(self):
        for name in ('identity', 'measurements', 'attribution'):
            with self.subTest(dimension=name):
                value = states.unpriced_projection()
                value['completeness'][name] = 'not_applicable'
                self.bind(value)
                before = self.fixture.snapshot()
                self.fixture.step('--session-id', 'session-a', '--agent-id', 'worker-a',
                                  '--checkpoint-id', 'checkpoint-' + name, '--span-start-ms', '1000',
                                  '--span-end-ms', '2000', '--timing-source', 'hook', '--boundary', 'session',
                                  '--usage-file', str(self.fixture.path), '--tokens-in', '750000')
                self.assertEqual(self.fixture.snapshot(), before)

    def test_not_applicable_is_allowed_for_proven_empty_scope(self):
        value = states.empty_projection()
        self.assertEqual(contract.validate_lifecycle_projection(value), value)

    def test_split_and_unsplit_same_counter_cannot_be_double_counted(self):
        value = states.cache_projection()
        first = value['contributors'][0]
        proof = {'schema_version': 1, 'kind': 'measurement_evidence', 'profile_id': 'profile',
                 'source_hash': 'a' * 64, 'record_number': 1, 'field': 'input_cache_write_unsplit', 'value': 200}
        value['evidence_objects'].append(proof)
        first['measurements']['input_cache_write_unsplit'] = {'measurement_state': 'final', 'value': 200,
                                                               'reasons': [], 'evidence': contract.content_id(proof)}
        first['price_snapshot_id'] = first['priced_usd'] = None
        value.pop('cost_usd')
        value['completeness']['pricing'] = 'partial'
        value.update(priced_subtotal_usd='0.5', subtotal_quality='subtotal_only')
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(value)


if __name__ == '__main__':
    unittest.main()
