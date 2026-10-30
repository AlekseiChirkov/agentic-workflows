#!/usr/bin/env python3
"""Reconcile ownership across independently authorized overlapping profiles."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tests' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


evidence = load('evidence', 'usage-report-evidence-fields.py')
multi = load('multi', 'usage-multibundle-report.py')


class OverlapOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.fixture = evidence.EvidenceBackedReportTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.base = self.fixture.base
        self.scope = self.fixture.scope
        self.positive = self.fixture.analyze()
        self.assertEqual(self.positive['totals']['total_cost'], '0.00578')
        self.assertEqual(self.positive['completeness']['attribution'], 'complete')

    def add_overlap(self, *, conflict=False):
        helper = multi.MultiBundleReportTests()
        helper.base = self.base
        data = helper.add_second_profile(overlap=True)
        inventory = data['bundle']['inventories'][0]
        proof = next(item for item in data['bundle']['evidence_objects'] if item['kind'] == 'inventory_evidence')
        self.fixture.authorize('tool_scope_empty', self.scope, inventory, proof)
        leaves = list(reversed(self.fixture.leaves)) if conflict else self.fixture.leaves
        entries = []
        for observation, leaf in zip(data['bundle']['observations'], leaves):
            entry = {'observation_id': contract.observation_id(observation), 'observed_at': '2028-01-03T00:00:00Z',
                     'attribution': {'response_id': observation['response_id'], 'provider': data['profile']['provider'],
                                     'provider_scope': observation['provider_scope'], 'owner_kind': 'task',
                                     'owner_id': leaf['owner_id'], 'candidates': [], 'basis': 'correlation'}}
            entries.append(entry)
        for owner in [self.scope, *self.fixture.leaves]:
            self.fixture.authorize('ownership_inventory', owner, inventory, proof)
            if owner != self.scope:
                self.fixture.authorize('leaf_billable_scope', owner, inventory, proof)
            for observation, entry in zip(data['bundle']['observations'], entries):
                self.fixture.authorize('ownership', owner, observation, entry)
                if owner == self.scope:
                    self.fixture.authorize('ownership_descendant', owner, observation, entry)
                elif owner['owner_id'] != entry['attribution']['owner_id']:
                    self.fixture.authorize('ownership_exclusion', owner, observation, entry)
        for context in data['contexts']:
            self.fixture.authorize('model_privacy', self.scope, context, context['parameters']['model'])
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
                                       if item['kind'] != 'ownership_selection']
        selected = copy.deepcopy(self.fixture.ownership)
        selected['entries'].extend(entries)
        self.fixture.add('overlap-ownership', 'ownership_selection', selected)

    def test_equivalent_verified_ownership_is_deduplicated_once(self):
        self.add_overlap()
        report = self.fixture.analyze()
        self.assertEqual(report['totals']['total_cost'], '0.00578')
        self.assertEqual(report['completeness']['identity'], 'complete')
        self.assertEqual(report['completeness']['attribution'], 'complete')
        self.assertEqual(len(report['contributors']), 2)
        self.assertEqual(len(report['terms']), 10)
        self.assertEqual(sorted(item['cost_usd'] for item in report['top_leaves']), ['0.00289', '0.00289'])

    def test_conflicting_verified_owners_are_not_silently_selected(self):
        self.add_overlap(conflict=True)
        try:
            report = self.fixture.analyze()
        except ValueError:
            return
        self.assertNotEqual(report['completeness']['attribution'], 'complete')
        self.assertEqual(report['top_leaves'], [])


if __name__ == '__main__':
    unittest.main()
