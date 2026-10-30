#!/usr/bin/env python3
"""Check fixed retrospective selection of pricing and identity evidence."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract
import usage_telemetry_corpus as corpus


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tests' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


profiles = load('profiles', 'usage-source-profiles.py')
scenarios = load('scenarios', 'usage-pricing-scenario-schema.py')
prices = load('prices', 'usage-price-snapshot-schema.py')


class FrozenPricingInputsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.scope = {'owner_kind': 'run', 'owner_id': 'sha256:' + '1' * 64}
        self.manifest = {'schema_version': 1, 'kind': 'analysis_corpus',
                         'as_of': '2026-01-03T00:00:00Z', 'scope': self.scope,
                         'scenario_id': 'baseline',
                         'versions': {'bundle_schema_version': 1, 'receipt_schema_version': 1,
                                      'price_schema_version': 1, 'normalizer_version': '1'},
                         'identifier_mappings': [], 'inputs': [], 'exclusions': [],
                         'max_source_bytes': 100000, 'max_total_bytes': 500000,
                         'max_records': 100}
        self.bundle = profiles.split_bundle()
        self.snapshot = prices.snapshot()
        self.scenario = scenarios.scenario()
        self.scenario['snapshot_ids'] = [contract.price_snapshot_id(self.snapshot)]
        observation = self.bundle['observations'][0]
        self.context = {
            'observation_id': contract.observation_id(observation),
            'profile_id': observation['profile_id'], 'profile_version': observation['profile_version'],
            'source_hash': observation['source_hash'], 'record_number': observation['record_number'],
            'provider_scope': observation['provider_scope'], 'counter_scope': observation['counter_scope'],
            'provider': profiles.profile()['provider'], 'session_id': 'sha256:' + 'e' * 64,
            'event': {'kind': 'snapshot', 'final': True},
            'execution_time': '2026-01-01T00:00:00Z',
            'parameters': {'model': 'vendor/model', 'service_tier': 'standard',
                           'region': 'example-region', 'modality': 'text'},
            'cache_ttl_seconds': {'5m': 300, '1h': 3600}, 'evidence_objects': [],
        }
        self.price_evidence = {'schema_version': 1, 'kind': 'price_snapshot_evidence',
                               'snapshot_id': contract.price_snapshot_id(self.snapshot),
                               'source_hash': 'b' * 64}
        for kind, value in [('usage_bundle', self.bundle), ('source_profile', profiles.profile()),
                            ('price_snapshot', self.snapshot), ('pricing_scenario', self.scenario),
                            ('resolution_context', self.context), ('price_evidence', self.price_evidence)]:
            self.add(kind, value)
        # The fixture authority is separately held by the caller and matches exact
        # selected bytes. The input document does not authorize itself.
        self.allowed = {item['sha256'] for item in self.manifest['inputs']}

    def add(self, kind, value):
        data = contract.canonical_bytes(value)
        path = self.directory / (kind + '.json')
        path.write_bytes(data)
        item = {'kind': kind, 'schema_version': 1, 'local_path': str(path),
                'sha256': hashlib.sha256(data).hexdigest(), 'size_bytes': len(data)}
        self.manifest['inputs'].append(item)
        return item

    def verify(self, entry, value, scope):
        if entry['sha256'] not in self.allowed or scope != self.scope:
            raise ValueError('untrusted input')
        return {'scope': copy.deepcopy(scope), 'observed_at': '2026-01-02T00:00:00Z'}

    def freeze(self, verifier=None):
        return corpus.freeze_corpus(copy.deepcopy(self.manifest), verify_input=verifier or self.verify)

    def test_each_resolution_input_is_selected_validated_and_frozen(self):
        result = self.freeze()
        self.assertEqual({item['kind'] for item in result['inputs']},
                         {'usage_bundle', 'source_profile', 'price_snapshot', 'pricing_scenario',
                          'resolution_context', 'price_evidence'})
        selected = {item['kind']: item['value'] for item in result['inputs']}
        self.assertEqual(contract.canonical_bytes(selected['source_profile']),
                         contract.canonical_bytes(profiles.profile()))
        self.assertEqual(contract.canonical_bytes(selected['pricing_scenario']),
                         contract.canonical_bytes(self.scenario))
        self.assertEqual(selected['resolution_context'], self.context)
        self.assertEqual(selected['price_evidence'], self.price_evidence)
        self.assertEqual(result, self.freeze())

    def test_each_selected_file_is_bound_by_its_digest(self):
        self.freeze()
        for item in self.manifest['inputs']:
            path = Path(item['local_path'])
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            with self.subTest(kind=item['kind']), self.assertRaises(ValueError):
                self.freeze()
            path.write_bytes(original)

    def test_untrusted_selected_input_and_scope_fail_closed(self):
        self.freeze()
        removed = self.manifest['inputs'][-1]['sha256']
        self.allowed.remove(removed)
        with self.assertRaises(ValueError):
            self.freeze()
        self.allowed.add(removed)
        def wrong_scope(entry, value, scope):
            return {'scope': {'owner_kind': 'run', 'owner_id': 'sha256:' + '2' * 64},
                    'observed_at': '2026-01-02T00:00:00Z'}
        with self.assertRaises(ValueError):
            self.freeze(wrong_scope)

    def test_changed_authority_decisions_change_frozen_identity(self):
        first = self.freeze()
        def alternate(entry, value, scope):
            proof = self.verify(entry, value, scope)
            if entry['kind'] == 'resolution_context':
                proof['observed_at'] = '2026-01-02T00:00:01Z'
            return proof
        second = self.freeze(alternate)
        self.assertNotEqual(first['corpus_id'], second['corpus_id'])
        self.assertEqual(first['inputs'], second['inputs'])

    def test_late_context_is_excluded_without_rewriting_older_corpus(self):
        before = self.freeze()
        def late(entry, value, scope):
            proof = self.verify(entry, value, scope)
            if entry['kind'] == 'resolution_context':
                proof['observed_at'] = '2026-01-04T00:00:00Z'
            return proof
        later = self.freeze(late)
        self.assertEqual(before, self.freeze())
        self.assertNotEqual(before['corpus_id'], later['corpus_id'])
        self.assertNotIn('resolution_context', [item['kind'] for item in later['inputs']])
        digest = next(item['sha256'] for item in self.manifest['inputs']
                      if item['kind'] == 'resolution_context')
        self.assertIn({'input_sha256': digest, 'reason': 'late_evidence'}, later['exclusions'])

    def test_unvalidated_extra_private_fields_are_rejected_even_with_matching_digest(self):
        self.freeze()
        for kind, value in [('source_profile', profiles.profile()), ('pricing_scenario', self.scenario),
                            ('resolution_context', self.context), ('price_evidence', self.price_evidence)]:
            entry = next(item for item in self.manifest['inputs'] if item['kind'] == kind)
            original = Path(entry['local_path']).read_bytes()
            old_entry, old_allowed = copy.deepcopy(entry), self.allowed.copy()
            data = contract.canonical_bytes(value | {'prompt': 'private data'})
            Path(entry['local_path']).write_bytes(data)
            entry.update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
            self.allowed.add(entry['sha256'])
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.freeze()
            Path(entry['local_path']).write_bytes(original)
            entry.clear()
            entry.update(old_entry)
            self.allowed = old_allowed


if __name__ == '__main__':
    unittest.main()
