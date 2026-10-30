#!/usr/bin/env python3
"""Epoch resolution is bound to the exact normalized source bundle."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('producer_epochs', ROOT / 'tests/usage-producer-epochs.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
base, contract = fixture.base, fixture.contract


class EpochBundleTests(unittest.TestCase):
    def setUp(self):
        self.producer = fixture.ProducerEpochTests('test_explicit_source_epochs_survive_bundle_and_resolve_without_double_count')
        self.producer.setUp()
        self.addCleanup(self.producer.doCleanups)
        self.bundle = self.producer.produce()['bundle']
        self.pack = next(item['pack'] for item in self.bundle['evidence_objects']
                         if item['kind'] == 'epoch_interval_evidence')
        inventory, _ = base.inventories.inventory(())
        inventory.update(profile_id=self.producer.profile['profile_id'], profile_version=self.producer.profile['profile_version'],
                         source_hash=self.bundle['sources'][0]['sha256'], owner_scope=self.producer.scope)
        inventory, proof = base.inventories.bind(inventory)
        self.bundle['inventories'] = [inventory]
        self.bundle['evidence_objects'].append(proof)
        self.data = {'bundle': self.bundle, 'profile': self.producer.profile, 'contexts': [],
                     'snapshots': [], 'scenario': None, 'price_evidence': [], 'scope': self.producer.scope,
                     'as_of': '2029-01-02T00:00:00Z', 'epoch_inputs': [self.pack]}
        self.allowed = [('inventory', self.producer.scope, inventory, proof)]
        fixture.epochs.authorize(self.data, self.allowed, self.pack)

    def test_exact_producer_bundle_resolves_its_own_authorized_interval(self):
        self.assertEqual(contract.validate_usage_bundle(self.bundle), self.bundle)
        result = base.resolve(self.data, base.Verifier(self.allowed))
        self.assertEqual(result['epochs']['aggregate']['total'], '20')
        self.assertEqual(result['epochs']['intervals'][0]['request_usage'], {base.opaque('9'): '20'})
        self.assertNotIn('cost_usd', result['cost'])
        self.assertEqual(result['responses'], [])

    def test_foreign_or_modified_interval_is_not_authorized_by_another_bundle(self):
        for change in ('foreign', 'modified'):
            with self.subTest(change=change):
                data = copy.deepcopy(self.data)
                if change == 'foreign':
                    data['bundle']['evidence_objects'] = [item for item in data['bundle']['evidence_objects']
                                                           if item.get('kind') != 'epoch_interval_evidence']
                else:
                    data['epoch_inputs'][0]['interval']['after']['position'] += 1
                result = base.resolve(data, base.Verifier(self.allowed))
                self.assertNotEqual(result['epochs']['aggregate'].get('total'), '20')


if __name__ == '__main__':
    unittest.main()
