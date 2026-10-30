#!/usr/bin/env python3
"""Explicit stream-profile extraction through selected source and resolver."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


producer = load('producer', 'tests/usage-producer-resolution.py')
revisions = load('revisions', 'tests/usage-resolution-revisions.py')
contract = producer.contract


class ProducerStreamTests(unittest.TestCase):
    def setUp(self):
        self.fixture = producer.ProducerResolutionTests(methodName='test_verified_profile_produces_sanitized_bound_context_usable_by_resolver')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.profile = revisions.base.profiles.profile(False)
        self.profile['counter_fields'] = [field for field in self.profile['counter_fields']
                                          if field['measurement'] in ('input_uncached', 'output_total')]
        for field in self.profile['counter_fields']:
            field['counter_scope'] = 'incremental_delta'
        self.profile['capabilities']['cache'] = 'unsupported'
        self.profile['resolution_fields'] = copy.deepcopy(producer.profile()['resolution_fields'])
        self.profile['resolution_fields']['finality'] = {
            'kind': 'stream', 'kind_path': ['metadata', 'kind'], 'sequence_path': ['metadata', 'sequence'],
            'final_path': ['metadata', 'complete'], 'correction_record_path': ['metadata', 'corrects_record'],
            'kinds': {'snapshot': 'snapshot', 'delta': 'delta', 'terminal': 'terminal'}}
        self.accepted_observations = {}
        self.records = []
        for sequence, kind, counts in ((1, 'delta', (10, 1)), (2, 'delta', (20, 2)), (3, 'terminal', None)):
            raw = copy.deepcopy(self.fixture.raw)
            raw['metadata'].update(kind=kind, sequence=sequence)
            raw['usage'] = {} if counts is None else {'input': counts[0], 'output': counts[1]}
            self.records.append(raw)
        content = b''.join((json.dumps(item) + '\n').encode() for item in self.records)
        self.fixture.path.write_bytes(content)
        self.fixture.selection = producer.source.manifest(self.fixture.path, content, owner_scope=self.fixture.scope)

    def verify(self, kind, selected_profile, observation, proof):
        if selected_profile != self.profile or observation['source_hash'] != self.fixture.selection['sources'][0]['sha256']:
            return False
        index = observation['record_number'] - 1
        if not 0 <= index < len(self.records):
            return False
        metadata = self.records[index]['metadata']
        if kind == 'measurement_finality':
            value = observation['measurements'].get(proof['field'])
            if isinstance(value, list):
                value = next((part['tokens'] for part in value if part['ttl'] == proof.get('ttl')), None)
            return value == proof['measurement'] and value is not None and value['measurement_state'] == 'partial'
        if kind == 'parameter':
            return (proof.get('field') in ('model', 'service_tier', 'region', 'modality') and
                    proof['value'] == metadata[proof['field']] and
                    all(proof[key] == observation[key] for key in ('profile_id', 'source_hash', 'record_number')))
        if kind == 'context':
            expected_reference = metadata.get('corrects_record')
            correction = proof['event'].get('correction_of')
            if expected_reference is not None and correction != self.accepted_observations.get(expected_reference):
                return False
            if expected_reference is None and correction is not None:
                return False
            verified = (proof['event']['kind'] == metadata['kind'] and proof['event']['sequence'] == metadata['sequence'] and
                        all(proof[key] == observation[key] for key in ('profile_id', 'source_hash', 'record_number',
                                                                        'provider_scope', 'counter_scope')))
            if verified:
                self.accepted_observations[observation['record_number']] = 'sha256:' + contract.observation_id(observation)
            return verified
        return False

    def produce(self):
        return producer.adapter.normalize_selection(
            self.fixture.selection, profile=self.profile, expected_owner_scope=self.fixture.scope,
            project_identifier='PRIVATE_PROJECT', provider_identifier='PRIVATE_ACCOUNT', run_id='run',
            key=b'private-mapping-key-that-is-long-enough-for-tests', verify_resolution=self.verify)

    def test_delta_stream_producer_retains_scoped_evidence_for_resolver(self):
        result = self.produce()
        self.assertEqual(len(result['contexts']), 3)
        self.assertEqual([context['event']['kind'] for context in result['contexts']], ['delta', 'delta', 'terminal'])
        self.assertEqual([context['event']['sequence'] for context in result['contexts']], [1, 2, 3])
        observations = result['bundle']['observations']
        self.assertEqual(len({item['response_id'] for item in observations}), 1)
        self.assertTrue(all(item['counter_scope'] == 'incremental_delta' for item in observations))
        self.assertEqual(observations[0]['measurements']['input_uncached']['value'], 10)
        self.assertEqual(observations[1]['measurements']['input_uncached']['value'], 20)
        self.assertNotIn('PRIVATE_RESPONSE', json.dumps(result))
        self.assertEqual(contract.validate_usage_bundle(result['bundle']), result['bundle'])
        data, _ = revisions.base.fixture()
        inventory = data['bundle']['inventories'][0]
        inventory.update(source_hash=observations[0]['source_hash'], owner_scope=self.fixture.scope,
                         expected_calls=[{'call_id': observations[0]['call_id']}],
                         expected_responses=[{'call_id': observations[0]['call_id'],
                                              'response_id': observations[0]['response_id']}])
        inventory, proof = revisions.base.inventories.bind(inventory)
        result['bundle']['inventories'] = [inventory]
        result['bundle']['evidence_objects'].append(proof)
        data.update(bundle=result['bundle'], contexts=result['contexts'], profile=self.profile, scope=self.fixture.scope)
        report = revisions.base.resolve(data, revisions.base.Verifier(revisions.authorize(data)))
        self.assertEqual(report['tokens']['input'], {'value': '30', 'quality': 'complete'})
        self.assertEqual(report['tokens']['output'], {'value': '3', 'quality': 'complete'})
        self.assertEqual(report['responses'][0]['model_cost']['cost_usd'], '0.00009')

    def test_producer_explicit_record_correction_requires_separate_revision_authority(self):
        self.profile = revisions.base.profiles.profile()
        self.profile['resolution_fields'] = copy.deepcopy(producer.profile()['resolution_fields'])
        self.profile['resolution_fields']['finality'] = {
            'kind': 'stream', 'kind_path': ['metadata', 'kind'], 'sequence_path': ['metadata', 'sequence'],
            'final_path': ['metadata', 'complete'], 'correction_record_path': ['metadata', 'corrects_record'],
            'kinds': {'snapshot': 'snapshot', 'delta': 'delta', 'terminal': 'terminal'}}
        self.records = []
        for sequence, total in ((1, 1000), (2, 1100)):
            raw = copy.deepcopy(self.fixture.raw)
            raw['metadata'].update(kind='snapshot', sequence=sequence, complete=True)
            if sequence == 2:
                raw['metadata']['corrects_record'] = 1
            raw['usage'] = {'input': total, 'read': 200, 'write': 200, 'short': 100,
                            'long': 100, 'output': 100, 'reasoning': 25}
            self.records.append(raw)
        content = b''.join((json.dumps(item) + '\n').encode() for item in self.records)
        self.fixture.path.write_bytes(content)
        self.fixture.selection = producer.source.manifest(self.fixture.path, content, owner_scope=self.fixture.scope)
        result = self.produce()
        observations = result['bundle']['observations']
        contexts = result['contexts']
        self.assertEqual(contexts[1]['event']['correction_of'], 'sha256:' + contract.observation_id(observations[0]))
        data, _ = revisions.base.fixture()
        inventory = data['bundle']['inventories'][0]
        inventory.update(source_hash=observations[0]['source_hash'], owner_scope=self.fixture.scope,
                         expected_calls=[{'call_id': observations[0]['call_id']}],
                         expected_responses=[{'call_id': observations[0]['call_id'],
                                              'response_id': observations[0]['response_id']}])
        inventory, proof = revisions.base.inventories.bind(inventory)
        result['bundle']['inventories'] = [inventory]
        result['bundle']['evidence_objects'].append(proof)
        data.update(bundle=result['bundle'], contexts=contexts, profile=self.profile, scope=self.fixture.scope)
        allowed = revisions.authorize(data)
        untrusted = revisions.base.resolve(data, revisions.base.Verifier(allowed))
        self.assertNotEqual(untrusted['tokens']['input'].get('quality'), 'complete')
        allowed.append(('revision', self.fixture.scope, observations[1], contexts[1]['event']))
        report = revisions.base.resolve(data, revisions.base.Verifier(allowed))
        self.assertEqual(report['tokens']['input'], {'value': '1100', 'quality': 'complete'})
        self.assertEqual(report['responses'][0]['model_cost']['cost_usd'], '0.00309')

    def test_unknown_event_mapping_does_not_assume_snapshot_or_finality(self):
        self.records[1]['metadata']['kind'] = 'unexpected'
        content = b''.join((json.dumps(item) + '\n').encode() for item in self.records)
        self.fixture.path.write_bytes(content)
        self.fixture.selection = producer.source.manifest(self.fixture.path, content, owner_scope=self.fixture.scope)
        result = self.produce()
        self.assertEqual([item['record_number'] for item in result['contexts']], [1, 3])
        self.assertNotIn('PRIVATE_PAYLOAD_SENTINEL', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
