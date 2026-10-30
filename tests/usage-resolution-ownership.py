#!/usr/bin/env python3
"""Verified ownership over actual response model costs and immutable cutoffs."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
contract = base.contract
PARENT, LEAF_A, LEAF_B = [base.opaque(char) for char in '789']


def pricing_through_2029(data, allowed):
    snapshot = data['snapshots'][0]
    period = data['price_evidence'][0]
    period['end'] = '2029-01-01T00:00:00Z'
    snapshot['effective_period']['end'] = period['end']
    snapshot['effective_period']['evidence'] = contract.content_id(period)
    identity = contract.price_snapshot_id(snapshot)
    data['scenario']['snapshot_ids'] = [identity]
    data['price_evidence'][1]['snapshot_id'] = identity
    allowed[:] = [item for item in allowed if item[0] != 'price']
    allowed.extend(('price', data['scope'], snapshot, proof) for proof in data['price_evidence'])


def attribution(observation, profile, observed_at='2029-01-01T12:00:00Z'):
    return {'observation_id': contract.observation_id(observation), 'observed_at': observed_at,
            'attribution': {'response_id': observation['response_id'], 'provider': profile['provider'],
                            'provider_scope': observation['provider_scope'], 'owner_kind': 'shared_pool',
                            'owner_id': PARENT, 'candidates': [LEAF_A, LEAF_B], 'basis': 'correlation'}}


def authorize(data, allowed):
    inventory = data['bundle']['inventories'][0]
    proof = next(item for item in data['bundle']['evidence_objects'] if item.get('kind') == 'inventory_evidence')
    by_id = {contract.observation_id(obs): obs for obs in data['bundle']['observations']}
    for scope in data['owner_scopes']:
        allowed.append(('ownership_inventory', scope, inventory, proof))
        for entry in data['ownership_inputs']:
            obs = by_id.get(entry['observation_id'])
            if obs is not None:
                allowed.append(('ownership', scope, obs, entry))


class OwnershipIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = base.fixture()
        pricing_through_2029(self.data, self.allowed)
        self.data['owner_scopes'] = [{'owner_kind': 'task', 'owner_id': value} for value in (PARENT, LEAF_A, LEAF_B)]
        self.data['ownership_inputs'] = [attribution(obs, self.data['profile']) for obs in self.data['bundle']['observations']]
        authorize(self.data, self.allowed)

    def report(self, allowed=None):
        return base.resolve(self.data, base.Verifier(self.allowed if allowed is None else allowed))

    @staticmethod
    def scopes(report):
        return {entry['scope']['owner_id']: entry for entry in report['ownership']}

    def test_shared_parent_pool_is_counted_once_without_leaf_allocation(self):
        result = self.report()
        parent, first_leaf, second_leaf = [self.scopes(result)[item] for item in (PARENT, LEAF_A, LEAF_B)]
        self.assertEqual(parent['attribution'], 'complete')
        self.assertEqual(parent['model_cost']['cost_usd'], '0.00578')
        self.assertEqual(len(parent['contributors']), 2)
        for leaf in (first_leaf, second_leaf):
            self.assertEqual(leaf['attribution'], 'partial')
            self.assertNotIn('cost_usd', leaf['model_cost'])
        self.data['ownership_inputs'].append(copy.deepcopy(self.data['ownership_inputs'][0]))
        repeated = self.scopes(self.report())[PARENT]
        self.assertEqual(parent, repeated)

    def test_missing_provenance_or_inventory_keeps_scope_incomplete(self):
        allowed = [entry for entry in self.allowed if not (
            entry[0] == 'ownership' and entry[1]['owner_id'] == PARENT and entry[2]['record_number'] == 2)]
        parent = self.scopes(self.report(allowed))[PARENT]
        self.assertEqual(parent['attribution'], 'partial')
        self.assertNotIn('cost_usd', parent['model_cost'])
        allowed = [entry for entry in self.allowed if entry[0] != 'ownership_inventory']
        parent = self.scopes(self.report(allowed))[PARENT]
        self.assertNotIn('cost_usd', parent['model_cost'])

    def test_forged_record_or_provider_cannot_inherit_other_proof(self):
        self.data['ownership_inputs'][0]['attribution']['provider_scope'] = base.opaque('f')
        parent = self.scopes(self.report())[PARENT]
        self.assertEqual(parent['attribution'], 'partial')
        self.assertNotIn('cost_usd', parent['model_cost'])

    def test_late_attribution_changes_only_new_report(self):
        self.data['ownership_inputs'][1]['observed_at'] = '2029-01-03T00:00:00Z'
        self.allowed = [item for item in self.allowed if item[0] not in ('ownership', 'ownership_inventory')]
        authorize(self.data, self.allowed)
        before = self.report()
        frozen = copy.deepcopy(before)
        self.assertNotIn('cost_usd', self.scopes(before)[PARENT]['model_cost'])
        self.data['as_of'] = '2029-01-04T00:00:00Z'
        after = self.report()
        self.assertEqual(self.scopes(after)[PARENT]['model_cost']['cost_usd'], '0.00578')
        self.assertEqual(before, frozen)

    def test_proven_descendant_rolls_up_without_guessed_ancestry(self):
        entry = self.data['ownership_inputs'][0]
        entry['attribution'].update(owner_kind='task', owner_id=LEAF_A, candidates=[])
        self.allowed = [item for item in self.allowed if item[0] not in ('ownership', 'ownership_inventory')]
        authorize(self.data, self.allowed)
        scope = next(value for value in self.data['owner_scopes'] if value['owner_id'] == PARENT)
        observation = self.data['bundle']['observations'][0]
        self.allowed.append(('ownership_descendant', scope, observation, entry))
        parent = self.scopes(self.report())[PARENT]
        self.assertEqual(parent['attribution'], 'complete')
        self.assertEqual(parent['model_cost']['cost_usd'], '0.00578')
        self.assertEqual(len(parent['contributors']), 2)
        without_hierarchy = [item for item in self.allowed if item[0] != 'ownership_descendant']
        parent = self.scopes(self.report(without_hierarchy))[PARENT]
        self.assertEqual(parent['attribution'], 'partial')
        self.assertNotIn('cost_usd', parent['model_cost'])

    def test_foreign_owner_may_be_excluded_only_by_separate_scope_proof(self):
        entry = self.data['ownership_inputs'][0]
        entry['attribution'].update(owner_kind='task', owner_id=base.opaque('a'), candidates=[])
        self.allowed = [item for item in self.allowed if item[0] not in ('ownership', 'ownership_inventory')]
        authorize(self.data, self.allowed)
        parent = self.scopes(self.report())[PARENT]
        self.assertNotIn('cost_usd', parent['model_cost'])
        scope = next(value for value in self.data['owner_scopes'] if value['owner_id'] == PARENT)
        self.allowed.append(('ownership_exclusion', scope, self.data['bundle']['observations'][0], entry))
        parent = self.scopes(self.report())[PARENT]
        self.assertEqual(parent['model_cost']['cost_usd'], '0.00289')
        self.assertEqual(len(parent['contributors']), 1)

    def test_unattributed_external_pool_does_not_complete_parent(self):
        entry = self.data['ownership_inputs'][0]
        entry['attribution'].update(owner_kind='unattributed', owner_id=base.opaque('a'), candidates=[])
        self.allowed = [item for item in self.allowed if item[0] not in ('ownership', 'ownership_inventory')]
        authorize(self.data, self.allowed)
        parent = self.scopes(self.report())[PARENT]
        self.assertNotIn('cost_usd', parent['model_cost'])
        self.assertEqual(parent['attribution'], 'partial')


if __name__ == '__main__':
    unittest.main()
