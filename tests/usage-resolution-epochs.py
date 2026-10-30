#!/usr/bin/env python3
"""Scoped, independently evidenced cumulative intervals at the resolver boundary."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


base = load('integration', 'tests/usage-resolution-integration.py')
epoch_fixture = load('epoch_fixture', 'tests/usage-cumulative-epochs.py')
contract = base.contract


def epoch_pack():
    profile = base.profiles.profile(False)
    profile['counter_fields'] = [profile['counter_fields'][0] | {'counter_scope': 'cumulative_epoch'}]
    profile['capabilities']['cache'] = 'unknown'
    del profile['capability_evidence']['cache']
    scope = base.opaque('c')
    observations, objects = [], []
    for number, value in ((10, 90), (11, 110)):
        proof = {'schema_version': 1, 'kind': 'measurement_evidence', 'profile_id': profile['profile_id'],
                 'source_hash': 'a' * 64, 'record_number': number, 'field': 'input_uncached',
                 'value': value, 'path': ['usage', 'input']}
        observation = base.profiles.split_bundle()['observations'][0]
        observation.update(record_number=number, counter_scope='cumulative_epoch', provider_scope=scope,
                           measurements={'input_uncached': {'measurement_state': 'partial', 'value': value,
                                                            'reasons': [], 'evidence': contract.content_id(proof)}})
        observations.append(observation)
        objects.append(proof)
    interval = epoch_fixture.interval()
    for boundary in (interval['before'], interval['after']):
        boundary.update(provider=profile['provider'], account=scope, model='vendor/model',
                        units='input_uncached_tokens', epoch=base.opaque('7'))
    interval['coverage']['requests'][0]['id'] = base.opaque('9')
    return {'profile': profile, 'observations': observations, 'evidence_objects': objects,
            'interval': interval, 'observed_at': '2026-01-02T03:04:05Z'}


def authorize(data, allowed, pack):
    scope = data['scope']
    subject = {'profile': pack['profile'], 'observations': pack['observations']}
    allowed.append(('profile', scope, pack['profile'], pack['profile']))
    for observation, proof, snapshot in zip(pack['observations'], pack['evidence_objects'],
                                            (pack['interval']['before'], pack['interval']['after'])):
        allowed.append(('measurement', scope, {'observation': observation, 'field': 'input_uncached'}, proof))
        allowed.append(('epoch_snapshot', scope, observation, snapshot))
    allowed.append(('epoch_privacy', scope, subject, pack))
    allowed.append(('epoch_interval', scope, subject, pack['interval']))
    allowed.append(('epoch_inventory', scope, subject, pack['interval']['coverage']))
    allowed.append(('epoch_boundary', scope, subject, pack['interval']['coverage']))


def own_bundle(data):
    """Place exact interval packs and their source observations in one bundle."""
    packs = data['epoch_inputs']
    if not packs:
        return
    bundle = data['bundle']
    profile = packs[0]['profile']
    data.update(profile=profile, contexts=[], snapshots=[], scenario=None, price_evidence=[])
    bundle['observations'] = []
    bundle['evidence_objects'] = [item for item in bundle['evidence_objects'] if item['kind'] == 'inventory_evidence']
    observations, objects = {}, {}
    for pack in packs:
        for observation in pack['observations']:
            observations[contract.observation_id(observation)] = observation
        for item in pack['evidence_objects']:
            objects[contract.content_id(item)] = item
        wrapper = {'schema_version': 1, 'kind': 'epoch_interval_evidence', 'pack': pack}
        objects[contract.content_id(wrapper)] = wrapper
    bundle['observations'] = list(observations.values())
    bundle['evidence_objects'].extend(objects.values())


class EpochIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = base.fixture()
        self.pack = epoch_pack()
        self.data['epoch_inputs'] = [self.pack]
        authorize(self.data, self.allowed, self.pack)

    def report(self, allowed=None):
        own_bundle(self.data)
        return base.resolve(self.data, base.Verifier(self.allowed if allowed is None else allowed))

    def test_exact_adjacent_delta_is_separate_from_response_accounting(self):
        report = self.report()
        self.assertEqual(report['tokens']['input'], {'quality': 'unavailable'})
        self.assertNotIn('cost_usd', report['cost'])
        item = report['epochs']['intervals'][0]
        self.assertEqual(item['request_usage'], {base.opaque('9'): '20'})
        self.assertEqual(item['interval_aggregate'], '20')
        self.assertEqual(report['epochs']['aggregate']['total'], '20')
        self.assertFalse(report['epochs']['aggregate']['complete_request_accounting'])

    def test_partial_interval_is_only_aggregate_and_untrusted_evidence_is_unknown(self):
        self.pack['interval']['before']['value'] = 100
        proof = self.pack['evidence_objects'][0]
        proof['value'] = 100
        obs = self.pack['observations'][0]
        obs['measurements']['input_uncached']['value'] = 100
        obs['measurements']['input_uncached']['evidence'] = contract.content_id(proof)
        self.pack['interval']['coverage']['before_clear'] = False
        self.pack['interval']['coverage']['requests'][0]['start'] = 5
        self.allowed = [item for item in self.allowed if not item[0].startswith('epoch_') and
                        not (item[0] == 'profile' and item[2] == self.pack['profile']) and
                        not (item[0] == 'measurement' and item[2]['observation'].get('counter_scope') == 'cumulative_epoch')]
        authorize(self.data, self.allowed, self.pack)
        result = self.report()['epochs']['intervals'][0]
        self.assertEqual(result['request_usage'], {})
        self.assertEqual(result['interval_aggregate'], '10')
        untrusted = [item for item in self.allowed if item[0] != 'epoch_inventory']
        result = self.report(untrusted)['epochs']['intervals'][0]
        self.assertEqual(result['request_usage'], {})
        self.assertIsNone(result['interval_aggregate'])

    def test_atomic_completion_requires_separate_independent_authority(self):
        self.pack['interval']['coverage']['before_clear'] = False
        self.pack['interval']['coverage']['requests'][0]['start'] = 5
        self.pack['interval']['coverage']['atomic_on_completion'] = True
        self.allowed = [item for item in self.allowed if not item[0].startswith('epoch_')]
        authorize(self.data, self.allowed, self.pack)
        item = self.report()['epochs']['intervals'][0]
        self.assertEqual(item['request_usage'], {})
        subject = {'profile': self.pack['profile'], 'observations': self.pack['observations']}
        self.allowed.append(('epoch_atomic', self.data['scope'], subject, self.pack['interval']['coverage']))
        item = self.report()['epochs']['intervals'][0]
        self.assertEqual(item['request_usage'], {base.opaque('9'): '20'})

    def test_scope_tampering_or_future_evidence_cannot_be_used(self):
        self.pack['interval']['after']['account'] = base.opaque('f')
        with self.assertRaises(ValueError):
            self.report()
        self.pack = epoch_pack()
        self.data['epoch_inputs'] = [self.pack]
        self.pack['observed_at'] = '2030-01-01T00:00:00Z'
        authorize(self.data, self.allowed, self.pack)
        result = self.report()['epochs']['intervals'][0]
        self.assertEqual(result['request_usage'], {})
        self.assertIsNone(result['interval_aggregate'])

    def test_large_disjoint_epoch_sum_is_exported_exactly_as_decimal_string(self):
        maximum = 9007199254740991
        packs = []
        for index in range(1025):
            pack = epoch_pack()
            before, after = pack['interval']['before'], pack['interval']['after']
            before.update(sequence=1, position=2 * index, value=0)
            after.update(sequence=2, position=2 * index + 2, value=maximum)
            pack['interval']['coverage']['requests'] = [
                {'id': 'sha256:' + format(index + 1, '064x'), 'start': 2 * index + 1, 'end': 2 * index + 2}]
            for offset, value in enumerate((0, maximum)):
                observation = pack['observations'][offset]
                proof = pack['evidence_objects'][offset]
                observation['record_number'] = 2 * index + 10 + offset
                proof['record_number'] = observation['record_number']
                proof['value'] = value
                observation['measurements']['input_uncached']['value'] = value
                observation['measurements']['input_uncached']['evidence'] = contract.content_id(proof)
            packs.append(pack)
            authorize(self.data, self.allowed, pack)
        self.data['epoch_inputs'] = packs
        trusted = {(kind, contract.canonical_bytes(scope), contract.canonical_bytes(subject),
                    contract.canonical_bytes(proof)) for kind, scope, subject, proof in self.allowed}
        def verifier(kind, scope, subject, proof):
            return (kind, contract.canonical_bytes(scope), contract.canonical_bytes(subject),
                    contract.canonical_bytes(proof)) in trusted
        own_bundle(self.data)
        result = base.resolve(self.data, verifier)
        self.assertEqual(result['epochs']['aggregate']['total'], str(1025 * maximum))
        self.assertEqual(len(result['epochs']['aggregate']['included_ids']), 1025)
        self.assertEqual(result['tokens']['input']['quality'], 'unavailable')

    def test_unverified_pack_hash_is_not_exported_as_proof_of_privacy(self):
        self.pack['interval']['before']['model'] = 'PRIVATE_SECRET'
        self.pack['interval']['after']['model'] = 'PRIVATE_SECRET'
        self.allowed = [entry for entry in self.allowed if not entry[0].startswith('epoch_')]
        authorize(self.data, self.allowed, self.pack)
        self.allowed = [entry for entry in self.allowed if entry[0] != 'epoch_privacy']
        result = self.report()
        self.assertNotIn('PRIVATE_SECRET', str(result))
        interval = result['epochs']['intervals'][0]
        self.assertNotIn('id', interval)
        self.assertEqual(interval['request_usage'], {})
        self.assertIsNone(interval['interval_aggregate'])
        self.assertEqual(result['epochs']['aggregate']['included_ids'], [])

    def test_duplicate_interval_is_deduplicated_and_not_added_to_response_totals(self):
        self.data['epoch_inputs'].append(copy.deepcopy(self.pack))
        result = self.report()
        self.assertEqual(len(result['epochs']['intervals']), 1)
        self.assertEqual(result['epochs']['aggregate']['total'], '20')
        self.assertEqual(result['tokens']['input']['quality'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
