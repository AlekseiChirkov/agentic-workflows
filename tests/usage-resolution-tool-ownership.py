#!/usr/bin/env python3
"""Causal ownership of independently priced tool expenditures."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tools = load('tool_fixtures', 'tests/usage-resolution-tools.py')
owner = load('owner_fixtures', 'tests/usage-resolution-ownership.py')
base = tools.base
PARENT, LEAF = owner.PARENT, owner.LEAF_A


def fixture(empty_model=True):
    data, allowed = tools.fixture(empty_model=empty_model)
    data['owner_scopes'] = [{'owner_kind': 'task', 'owner_id': value} for value in (PARENT, LEAF)]
    data['ownership_inputs'] = ([] if empty_model else [owner.attribution(item, data['profile'])
                                                        for item in data['bundle']['observations']])
    owner.authorize(data, allowed)
    data['tool_ownership_inputs'] = [{'usage_id': data['tool_inputs'][0]['usage_id'],
                                      'observed_at': '2029-01-01T12:00:00Z',
                                      'attribution': {'owner_kind': 'shared_pool', 'owner_id': PARENT,
                                                      'candidates': [LEAF], 'basis': 'correlation'}}]
    authorize(data, allowed)
    return data, allowed


def authorize(data, allowed):
    inventory = data['bundle']['inventories'][0]
    proof = next(item for item in data['bundle']['evidence_objects'] if item['kind'] == 'inventory_evidence')
    declaration = {'inventory_evidence': proof, 'tool_usage_ids': sorted({item['usage_id'] for item in data['tool_inputs']})}
    tool = data['tool_inputs'][0]
    for scope in data['owner_scopes']:
        allowed.append(('tool_ownership_inventory', scope, inventory, declaration))
        for entry in data['tool_ownership_inputs']:
            if entry['usage_id'] == tool['usage_id']:
                allowed.append(('tool_ownership', scope, tool, entry))


class ToolOwnershipTests(unittest.TestCase):
    def report(self, data, allowed):
        result = base.resolve(data, base.Verifier(allowed))
        return {item['scope']['owner_id']: item for item in result['ownership']}

    def test_shared_tool_pool_is_counted_once_at_parent_and_not_allocated_to_leaf(self):
        data, allowed = fixture()
        scopes = self.report(data, allowed)
        self.assertEqual(scopes[PARENT]['model_cost']['cost_usd'], '0')
        self.assertEqual(scopes[PARENT]['tool_cost']['cost_usd'], '0.02')
        self.assertEqual(scopes[PARENT]['cost']['cost_usd'], '0.02')
        self.assertEqual(len(scopes[PARENT]['tool_contributors']), 1)
        self.assertEqual(scopes[LEAF]['attribution'], 'partial')
        self.assertNotIn('cost_usd', scopes[LEAF]['tool_cost'])
        self.assertNotIn('cost_usd', scopes[LEAF]['cost'])
        data['tool_ownership_inputs'].append(copy.deepcopy(data['tool_ownership_inputs'][0]))
        self.assertEqual(self.report(data, allowed)[PARENT], scopes[PARENT])

    def test_model_and_tool_contributors_combine_only_after_scope_proof(self):
        data, allowed = fixture(empty_model=False)
        parent = self.report(data, allowed)[PARENT]
        self.assertEqual(parent['model_cost']['cost_usd'], '0.00578')
        self.assertEqual(parent['tool_cost']['cost_usd'], '0.02')
        self.assertEqual(parent['cost']['cost_usd'], '0.02578')
        self.assertEqual(len(parent['contributors']), 2)
        self.assertEqual(len(parent['tool_contributors']), 1)

    def test_untrusted_tool_ownership_or_inventory_never_proves_full_cost(self):
        data, allowed = fixture()
        for kind in ('tool_ownership', 'tool_ownership_inventory', 'tool_nonoverlap'):
            with self.subTest(kind=kind):
                scope = self.report(data, [item for item in allowed if item[0] != kind])[PARENT]
                self.assertEqual(scope['model_cost']['cost_usd'], '0')
                self.assertNotIn('cost_usd', scope['tool_cost'])
                self.assertNotIn('cost_usd', scope['cost'])

    def test_late_or_forged_attribution_is_not_inherited_by_scope(self):
        data, allowed = fixture()
        data['tool_ownership_inputs'][0]['attribution']['owner_id'] = base.opaque('a')
        scope = self.report(data, allowed)[PARENT]
        self.assertNotIn('cost_usd', scope['tool_cost'])
        data, allowed = fixture()
        data['tool_ownership_inputs'][0]['observed_at'] = '2029-01-03T00:00:00Z'
        allowed = [item for item in allowed if not item[0].startswith('tool_ownership')]
        authorize(data, allowed)
        before = self.report(data, allowed)[PARENT]
        frozen = copy.deepcopy(before)
        self.assertNotIn('cost_usd', before['cost'])
        data['as_of'] = '2029-01-04T00:00:00Z'
        after = self.report(data, allowed)[PARENT]
        self.assertEqual(after['cost']['cost_usd'], '0.02')
        self.assertEqual(before, frozen)

    def test_tool_descendant_and_exclusion_require_exact_separate_proof(self):
        data, allowed = fixture()
        entry = data['tool_ownership_inputs'][0]
        entry['attribution'].update(owner_kind='task', owner_id=LEAF, candidates=[])
        allowed = [item for item in allowed if not item[0].startswith('tool_ownership')]
        authorize(data, allowed)
        parent = self.report(data, allowed)[PARENT]
        self.assertNotIn('cost_usd', parent['cost'])
        parent_scope = next(scope for scope in data['owner_scopes'] if scope['owner_id'] == PARENT)
        allowed.append(('tool_ownership_descendant', parent_scope, data['tool_inputs'][0], entry))
        parent = self.report(data, allowed)[PARENT]
        self.assertEqual(parent['cost']['cost_usd'], '0.02')
        allowed = [item for item in allowed if item[0] != 'tool_ownership_descendant']
        allowed.append(('tool_ownership_exclusion', parent_scope, data['tool_inputs'][0], entry))
        parent = self.report(data, allowed)[PARENT]
        self.assertEqual(parent['tool_cost']['cost_usd'], '0')
        self.assertEqual(parent['cost']['cost_usd'], '0')

    def test_conditional_tool_reprice_is_marked_at_every_owner_level(self):
        data, allowed = fixture()
        data['scenario']['basis'] = 'reprice'
        parent = self.report(data, allowed)[PARENT]
        self.assertEqual(parent['cost']['cost_usd'], '0.02')
        self.assertIs(parent['tool_cost']['conditional'], True)
        self.assertIs(parent['cost']['conditional'], True)


if __name__ == '__main__':
    unittest.main()
