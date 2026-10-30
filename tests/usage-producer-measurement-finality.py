#!/usr/bin/env python3
"""Source measurement finality requires independent exact authorization."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('producer', ROOT / 'tests/usage-producer-resolution.py')
producer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(producer)


class ProducerFinalityTests(unittest.TestCase):
    def setUp(self):
        self.fixture = producer.ProducerResolutionTests('test_verified_profile_produces_sanitized_bound_context_usable_by_resolver')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.calls = []

    def produce(self, denied=None):
        def verify(kind, profile, observation, proof):
            if kind == 'measurement_finality':
                self.calls.append((profile, observation, proof))
                return proof['field'] != denied
            return self.fixture.verify_resolution(kind, profile, observation, proof)
        return producer.adapter.normalize_selection(
            self.fixture.selection, profile=producer.profile(), expected_owner_scope=self.fixture.scope,
            project_identifier='PRIVATE_PROJECT', provider_identifier='PRIVATE_ACCOUNT', run_id='run',
            key=b'private-mapping-key-that-is-long-enough-for-tests', verify_resolution=verify)

    def test_authorized_exact_measurements_become_final_before_context_binding(self):
        result = self.produce()
        observation = result['bundle']['observations'][0]
        for field in ('input_uncached', 'output_total'):
            self.assertEqual(observation['measurements'][field]['measurement_state'], 'final')
            self.assertTrue(any(proof['field'] == field and proof['measurement']['value'] == observation['measurements'][field]['value']
                                and proof['measurement']['measurement_state'] == 'partial'
                                and observed['record_number'] == observation['record_number']
                                and observed['source_hash'] == observation['source_hash']
                                for _, observed, proof in self.calls))
        self.assertEqual(result['contexts'][0]['observation_id'], producer.contract.observation_id(observation))

    def test_denied_measurement_remains_partial_despite_final_event(self):
        result = self.produce(denied='input_uncached')
        observation = result['bundle']['observations'][0]
        self.assertEqual(observation['measurements']['input_uncached']['measurement_state'], 'partial')
        self.assertEqual(observation['measurements']['output_total']['measurement_state'], 'final')
        self.assertTrue(result['contexts'][0]['event']['final'])


if __name__ == '__main__':
    unittest.main()
