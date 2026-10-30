#!/usr/bin/env python3
"""Selected cumulative sources produce bounded independently verified intervals."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

producer = load('producer', 'tests/usage-producer-resolution.py')
epochs = load('epochs', 'tests/usage-resolution-epochs.py')
base, contract = epochs.base, epochs.contract


class ProducerEpochTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'private-epoch.jsonl'
        self.scope = {'owner_kind': 'run', 'owner_id': base.opaque('b')}
        self.profile = base.profiles.profile(False)
        self.profile['counter_fields'] = [self.profile['counter_fields'][0] | {'counter_scope': 'cumulative_epoch'}]
        self.profile['capabilities']['cache'] = 'unknown'
        self.profile['capability_evidence'].pop('cache', None)
        self.profile['epoch_fields'] = {'status': 'verified', 'epoch': ['metadata', 'epoch'],
                                        'model': ['metadata', 'model'], 'sequence': ['metadata', 'sequence'],
                                        'position': ['metadata', 'position']}
        self.rows = [{'usage': {'input': value}, 'metadata': {'epoch': 'PRIVATE_EPOCH', 'model': 'vendor/model',
                       'sequence': sequence, 'position': position}, 'secret': 'PRIVATE_PAYLOAD'}
                     for value, sequence, position in ((90, 4, 10), (110, 5, 20))]
        self.coverage = [{'before_record': 1, 'after_record': 2,
                          'coverage': {'complete': True, 'before_clear': True, 'after_clear': True,
                                       'atomic_on_completion': False,
                                       'requests': [{'id': base.opaque('9'), 'start': 11, 'end': 19}]}}]
        self.calls = []

    def produce(self, *, deny=None, provide_coverage=True):
        content = b''.join((json.dumps(row) + '\n').encode() for row in self.rows)
        self.path.write_bytes(content)
        selection = producer.source.manifest(self.path, content, owner_scope=self.scope)
        def verify(kind, profile, observation, proof):
            self.calls.append((kind, copy.deepcopy(profile), copy.deepcopy(observation), copy.deepcopy(proof)))
            if kind == deny:
                return False
            if kind == 'epoch_snapshot':
                record = self.rows[observation['record_number'] - 1]
                return (profile == self.profile and observation['source_hash'] == selection['sources'][0]['sha256'] and
                        proof['sequence'] == record['metadata']['sequence'] and
                        proof['position'] == record['metadata']['position'] and
                        proof['value'] == record['usage']['input'] and proof['model'] == record['metadata']['model'])
            if kind == 'epoch_coverage':
                return profile == self.profile and proof in self.coverage
            if kind == 'epoch_privacy':
                return (profile == self.profile and isinstance(observation, list) and
                        proof['interval']['before']['model'] == 'vendor/model' and
                        proof['interval']['after']['model'] == 'vendor/model' and
                        proof['observations'] == observation)
            return False
        options = {'epoch_coverages': self.coverage if provide_coverage else [], 'verify_resolution': verify}
        with patch('socket.socket', side_effect=AssertionError('network access')):
            return producer.adapter.normalize_selection(selection, profile=self.profile,
                expected_owner_scope=self.scope, project_identifier='PRIVATE_PROJECT',
                provider_identifier='PRIVATE_ACCOUNT', run_id='run',
                key=b'private-mapping-key-that-is-long-enough-for-tests', **options)

    def resolve(self, produced, *, deny=None):
        bundle = copy.deepcopy(produced['bundle'])
        inventory, _ = base.inventories.inventory(())
        inventory.update(profile_id=self.profile['profile_id'], profile_version=self.profile['profile_version'],
                         source_hash=bundle['sources'][0]['sha256'], owner_scope=self.scope)
        inventory, proof = base.inventories.bind(inventory)
        bundle['inventories'] = [inventory]
        bundle['evidence_objects'].append(proof)
        packs = [item['pack'] for item in bundle['evidence_objects']
                 if item.get('kind') == 'epoch_interval_evidence']
        data = {'bundle': bundle, 'profile': self.profile, 'contexts': [], 'snapshots': [],
                'scenario': None, 'price_evidence': [], 'scope': self.scope,
                'as_of': '2029-01-02T00:00:00Z', 'epoch_inputs': packs}
        allowed = [('inventory', self.scope, inventory, proof)]
        for pack in packs:
            epochs.authorize(data, allowed, pack)
        allowed = [item for item in allowed if item[0] != deny]
        return base.resolve(data, base.Verifier(allowed))

    def test_explicit_source_epochs_survive_bundle_and_resolve_without_double_count(self):
        result = self.produce()
        bundle = result['bundle']
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        wrappers = [item for item in bundle['evidence_objects'] if item.get('kind') == 'epoch_interval_evidence']
        self.assertEqual(len(wrappers), 1)
        self.assertEqual(len([call for call in self.calls if call[0] == 'epoch_snapshot']), 2)
        self.assertEqual(len([call for call in self.calls if call[0] == 'epoch_coverage']), 1)
        report = self.resolve(result)
        self.assertEqual(report['epochs']['aggregate']['total'], '20')
        self.assertEqual(report['epochs']['intervals'][0]['request_usage'], {base.opaque('9'): '20'})
        self.assertEqual(report['tokens']['input']['quality'], 'unavailable')
        for secret in ('PRIVATE_EPOCH', 'PRIVATE_ACCOUNT', 'PRIVATE_PROJECT', 'PRIVATE_PAYLOAD', str(self.path)):
            self.assertNotIn(secret, json.dumps(result))

    def test_reset_or_gap_does_not_invent_interval_usage(self):
        for change in ('reset', 'gap'):
            with self.subTest(change=change):
                original = copy.deepcopy(self.rows)
                if change == 'reset':
                    self.rows[1]['metadata']['epoch'] = 'OTHER_PRIVATE_EPOCH'
                else:
                    self.rows[1]['metadata']['sequence'] = 6
                result = self.produce()
                report = self.resolve(result)
                self.assertNotEqual(report['epochs']['aggregate'].get('total'), '20')
                self.assertTrue(all(not item['request_usage'] for item in report['epochs']['intervals']))
                self.rows = original

    def test_epoch_provenance_alone_does_not_authorize_private_model_disclosure(self):
        for row in self.rows:
            row['metadata']['model'] = 'PRIVATE_SECRET_MODEL'
        result = self.produce()
        self.assertNotIn('PRIVATE_SECRET_MODEL', json.dumps(result))
        self.assertTrue(any(call[0] == 'epoch_snapshot' for call in self.calls))
        self.assertTrue(any(call[0] == 'epoch_privacy' for call in self.calls))
        self.assertFalse(any(item.get('kind') == 'epoch_interval_evidence'
                             for item in result['bundle']['evidence_objects']))

    def test_unverified_source_or_resolver_evidence_remains_unknown(self):
        for kind in ('epoch_snapshot', 'epoch_coverage'):
            result = self.produce(deny=kind)
            report = self.resolve(result)
            self.assertNotEqual(report['epochs']['aggregate'].get('total'), '20')
        report = self.resolve(self.produce(), deny='epoch_inventory')
        self.assertNotEqual(report['epochs']['aggregate'].get('total'), '20')
        report = self.resolve(self.produce(provide_coverage=False))
        self.assertNotEqual(report['epochs']['aggregate'].get('total'), '20')


if __name__ == '__main__':
    unittest.main()
