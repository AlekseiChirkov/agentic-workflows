#!/usr/bin/env python3
"""Preserve verified report evidence across explicitly selected profiles."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract
import usage_telemetry_exports as exports


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tests' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


multi = load('multi', 'usage-multibundle-report.py')
evidence = load('evidence', 'usage-report-evidence-fields.py')


class ReportMultiBundleFieldsTests(unittest.TestCase):
    def setUp(self):
        self.fixture = multi.MultiBundleReportTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.base = self.fixture.base
        for context in self.base.data['contexts']:
            self.authorize_model(context)

    def authorize_model(self, context):
        self.base.authority.allowed.append(('model_privacy', multi.canonical(self.base.data['scope']),
                                            multi.canonical(context), context['parameters']['model']))

    def test_single_profile_exposes_unpriced_components_without_private_paths(self):
        report = self.base.analyze()
        self.assertEqual(report['coverage']['pricing'], {'numerator': 1, 'denominator': 2})
        self.assertEqual(report['pricing']['priced_subtotal_cost'], '0.00289')
        self.assertTrue(report['unpriced'])
        for content in exports.render_exports(report).values():
            self.assertNotIn(str(self.base.directory), content)

    def test_two_verified_profiles_retain_identity_terms_and_model_breakdown(self):
        alternate = self.fixture.add_second_profile()
        for context in alternate['contexts']:
            self.authorize_model(context)
        report = self.base.analyze()
        self.assertEqual(report['coverage']['pricing'], {'numerator': 2, 'denominator': 4})
        self.assertEqual(report['pricing']['priced_subtotal_cost'], '0.00578')
        self.assertEqual(report['completeness']['identity'], 'complete')
        self.assertEqual(len(report['terms']), 10)
        self.assertTrue(report['unpriced'])
        model = next(item for item in report['slices'] if item['dimension'] == 'model' and item['value'] == 'vendor/model')
        self.assertEqual(model['count'], 2)
        self.assertEqual(model['cost_usd'], '0.00578')
        self.assertEqual(model['coverage'], 'subtotal_only')
        reverse = copy.deepcopy(self.base.manifest)
        reverse['inputs'].reverse()
        from usage_telemetry_report import analyze_corpus
        again = analyze_corpus(reverse, verify_input=self.base.verify_input, verify_evidence=self.base.authority)
        self.assertEqual(exports.render_exports(report), exports.render_exports(again))

    def test_unverified_union_or_response_privacy_never_claims_completeness(self):
        alternate = self.fixture.add_second_profile()
        for context in alternate['contexts']:
            self.authorize_model(context)
        positive = self.base.analyze()
        self.assertEqual(positive['completeness']['identity'], 'complete')
        self.base.authority.allowed = [entry for entry in self.base.authority.allowed if entry[0] != 'inventory_union']
        denied = self.base.analyze()
        self.assertNotEqual(denied['completeness']['identity'], 'complete')
        self.assertEqual(denied['terms'], [])
        self.assertEqual(denied['slices'], [])
        self.assertNotEqual(positive['corpus_id'], denied['corpus_id'])


class VerifiedMultiOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.fixture = evidence.EvidenceBackedReportTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.base = self.fixture.base
        helper = multi.MultiBundleReportTests()
        helper.base = self.base
        alternate = helper.add_second_profile()
        self.alternate = alternate
        scope = self.fixture.scope
        inventory = alternate['bundle']['inventories'][0]
        proof = next(item for item in alternate['bundle']['evidence_objects'] if item['kind'] == 'inventory_evidence')
        self.fixture.authorize('tool_scope_empty', scope, inventory, proof)
        entries = []
        for observation, leaf in zip(alternate['bundle']['observations'], self.fixture.leaves):
            entry = {'observation_id': contract.observation_id(observation), 'observed_at': '2028-01-03T00:00:00Z',
                     'attribution': {'response_id': observation['response_id'], 'provider': alternate['profile']['provider'],
                                     'provider_scope': observation['provider_scope'], 'owner_kind': 'task',
                                     'owner_id': leaf['owner_id'], 'candidates': [], 'basis': 'correlation'}}
            entries.append(entry)
        for owner in [scope, *self.fixture.leaves]:
            self.fixture.authorize('ownership_inventory', owner, inventory, proof)
            if owner != scope:
                self.fixture.authorize('leaf_billable_scope', owner, inventory, proof)
            for observation, entry in zip(alternate['bundle']['observations'], entries):
                self.fixture.authorize('ownership', owner, observation, entry)
                if owner == scope:
                    self.fixture.authorize('ownership_descendant', owner, observation, entry)
                elif owner['owner_id'] != entry['attribution']['owner_id']:
                    self.fixture.authorize('ownership_exclusion', owner, observation, entry)
        for context in alternate['contexts']:
            self.fixture.authorize('model_privacy', scope, context, context['parameters']['model'])
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
                                       if item['kind'] != 'ownership_selection']
        selection = copy.deepcopy(self.fixture.ownership)
        selection['entries'].extend(entries)
        self.fixture.add('combined-ownership', 'ownership_selection', selection)

    def test_independently_verified_ownership_and_contributors_are_combined_once(self):
        report = self.fixture.analyze()
        self.assertEqual(report['coverage']['pricing'], {'numerator': 4, 'denominator': 4})
        self.assertEqual(report['totals']['total_cost'], '0.01156')
        self.assertEqual(report['completeness']['identity'], 'complete')
        self.assertEqual(report['completeness']['attribution'], 'complete')
        self.assertEqual(len(report['contributors']), 4)
        self.assertEqual(sorted(item['amount'] for item in report['contributors']), ['0.00289'] * 4)
        self.assertEqual(sorted(item['cost_usd'] for item in report['top_leaves']), ['0.00578', '0.00578'])
        self.assertEqual(len(report['terms']), 20)

    def test_missing_independent_ownership_does_not_gain_full_attribution(self):
        positive = self.fixture.analyze()
        self.assertEqual(positive['completeness']['attribution'], 'complete')
        self.base.authority.allowed = [entry for entry in self.base.authority.allowed
                                       if entry[0] != 'ownership']
        denied = self.fixture.analyze()
        self.assertNotEqual(denied['completeness']['attribution'], 'complete')
        self.assertEqual(denied['top_leaves'], [])
        self.assertNotEqual(positive['corpus_id'], denied['corpus_id'])


if __name__ == '__main__':
    unittest.main()
