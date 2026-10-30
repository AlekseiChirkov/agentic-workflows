#!/usr/bin/env python3
"""Selected, verified tool expenses belong in observed workload cost."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract
import usage_telemetry_resolution as resolution

spec = importlib.util.spec_from_file_location('workload', ROOT / 'tests/usage-outcome-unattributed-workload.py')
workload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workload)


class OutcomeToolCostTests(unittest.TestCase):
    def setUp(self):
        self.case = workload.UnattributedWorkloadTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.fixture = self.case.fixture
        self.base = self.fixture.base
        self.scope = self.fixture.scope
        data = self.base.data
        snapshot = data['snapshots'][0]
        snapshot['rates'].append({'component': 'tool', 'usd': '0.01', 'unit': 'request',
                                  'unit_quantity': 1, 'cache_ttl_seconds': None, 'threshold': None,
                                  'tool_id': 'search', 'multiplier': {'state': 'none'}})
        identity = contract.price_snapshot_id(snapshot)
        data['scenario']['snapshot_ids'] = [identity]
        for proof in data['price_evidence']:
            if proof['kind'] == 'price_snapshot_evidence':
                proof['snapshot_id'] = identity
        self.base.authority.allowed = [item for item in self.base.authority.allowed
                                       if item[0] not in ('price', 'tool_scope_empty')]
        for proof in data['price_evidence']:
            self.fixture.authorize('price', self.scope, snapshot, proof)
        for item in self.base.manifest['inputs']:
            if item['kind'] == 'price_snapshot':
                value = snapshot
            elif item['kind'] == 'pricing_scenario':
                value = data['scenario']
            elif item['kind'] == 'price_evidence':
                old = contract.parse_json(Path(item['local_path']).read_bytes())
                value = next(proof for proof in data['price_evidence'] if proof['kind'] == old['kind'])
            else:
                continue
            self.base.selected.remove(item['sha256'])
            raw = contract.canonical_bytes(value)
            Path(item['local_path']).write_bytes(raw)
            item.update(sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
            self.base.selected.add(item['sha256'])
        profile = data['profile']
        source = {'profile_id': profile['profile_id'], 'source_hash': 'a' * 64, 'record_number': 1}
        params = {'model': 'vendor/model', 'service_tier': 'standard', 'region': 'example-region', 'modality': 'text'}
        proofs = [{'schema_version': 1, 'kind': 'execution_time_evidence', **source, 'value': '2026-01-01T00:00:00Z'}]
        proofs += [{'schema_version': 1, 'kind': 'source_parameter_evidence', **source, 'field': name, 'value': value}
                   for name, value in params.items()]
        proofs.append({'schema_version': 1, 'kind': 'rate_parameter_evidence', **source, 'field': 'tool_id', 'value': 'search'})
        quantity = {'schema_version': 1, 'kind': 'tool_quantity_evidence', **source,
                    'tool_id': 'search', 'unit': 'request', 'value': 2}
        proofs.append(quantity)
        self.tool = {'schema_version': 1, 'kind': 'tool_usage', 'usage_id': 'sha256:' + 'f' * 64,
                     'profile_id': profile['profile_id'], 'profile_version': profile['profile_version'],
                     'source_hash': source['source_hash'], 'record_number': 1,
                     'provider_scope': data['bundle']['observations'][0]['provider_scope'],
                     'tool_id': 'search', 'unit': 'request', 'quantity': 2, 'observed_at': '2026-01-02T00:00:00Z',
                     'execution_time': '2026-01-01T00:00:00Z', 'parameters': params, 'evidence_objects': proofs}
        self.fixture.add('selected-tool', 'tool_usage', self.tool)
        inventory = data['bundle']['inventories'][0]
        inv_proof = next(item for item in data['bundle']['evidence_objects'] if item['kind'] == 'inventory_evidence')
        total_proof = {'inventory_evidence': inv_proof, 'tool_usage_ids': [self.tool['usage_id']]}
        self.fixture.authorize('tool_privacy', self.scope, self.tool, self.tool)
        self.fixture.authorize('tool_usage', self.scope, self.tool, quantity)
        for kind in ('tool_inventory', 'tool_nonoverlap'):
            self.fixture.authorize(kind, self.scope, inventory, total_proof)
        for proof in proofs[:-1]:
            self.fixture.authorize('pricing_context', self.scope, self.tool, proof)
        empty = {'schema_version': 1, 'kind': 'experimental_inventory', 'scope': self.scope,
                 'state': 'complete', 'expected_attempt_ids': [], 'observed_at': '2028-01-02T00:00:00Z'}
        self.case.add('empty-experimental', 'experimental_inventory', empty)
        self.fixture.authorize('experimental_tool_exclusion', self.scope, self.tool, empty)
        # Exercise actual core rates, quantities and independent verifier first.
        def verify(kind, scope, subject, proof):
            canonical = self.fixture.authorize.__globals__['canonical']
            return self.base.authority(kind, canonical(scope), canonical(subject), canonical(proof))
        result = resolution.resolve_usage(**copy.deepcopy(data), tool_inputs=[self.tool], verifier=verify)
        self.assertEqual(result['cost']['cost_usd'], '0.02578')
        self.assertEqual(result['tools'][0]['cost_usd'], '0.02')

    def analyze(self):
        from usage_telemetry_report import analyze_corpus
        def verify_input(item, value, scope):
            proof = self.fixture.verify_input(item, value, scope)
            if item['kind'] == 'tool_usage':
                proof['member_times'] = {contract.content_id(entry): '2029-01-01T00:00:00Z'
                                         for entry in value['evidence_objects']}
            return proof
        return analyze_corpus(copy.deepcopy(self.base.manifest), verify_input=verify_input,
                              verify_evidence=self.base.authority)

    def test_verified_tool_expense_is_included_once_in_observed_workload(self):
        report = self.analyze()
        self.assertEqual(report['totals']['total_cost'], '0.02578')
        self.assertEqual(report['outcomes']['observed_workload_cost'], '0.02578')
        self.assertEqual(report['outcomes']['cost_per_accepted'], '0.02578')
        self.assertEqual(report['outcomes']['coverage'], 'complete')
        self.assertEqual(report['outcomes']['experimental_evaluation_cost'], '0')

    def test_unverified_tool_inventory_does_not_claim_complete_total(self):
        positive = self.analyze()
        self.assertEqual(positive['totals']['total_cost'], '0.02578')
        self.base.authority.allowed = [item for item in self.base.authority.allowed if item[0] != 'tool_inventory']
        report = self.analyze()
        self.assertIsNone(report['totals']['total_cost'])
        self.assertEqual(report['outcomes']['coverage'], 'incomplete')
        self.assertIsNone(report['outcomes']['experimental_evaluation_cost'])
        self.assertNotEqual(report['corpus_id'], positive['corpus_id'])

    def test_unknown_experimental_scope_does_not_claim_tool_as_workload(self):
        positive = self.analyze()
        self.assertEqual(positive['outcomes']['observed_workload_cost'], '0.02578')
        self.base.authority.allowed = [item for item in self.base.authority.allowed
                                       if item[0] != 'experimental_inventory']
        report = self.analyze()
        self.assertEqual(report['totals']['total_cost'], '0.02578')
        self.assertEqual(report['outcomes']['observed_workload_cost'], '0.00578')
        self.assertEqual(report['outcomes']['coverage'], 'incomplete')
        self.assertIsNone(report['outcomes']['experimental_evaluation_cost'])

    def test_tool_requires_its_own_experimental_exclusion_proof(self):
        positive = self.analyze()
        self.assertEqual(positive['outcomes']['observed_workload_cost'], '0.02578')
        self.assertEqual(positive['outcomes']['experimental_evaluation_cost'], '0')
        self.base.authority.allowed = [item for item in self.base.authority.allowed
                                       if item[0] != 'experimental_tool_exclusion']
        denied = self.analyze()
        self.assertEqual(denied['totals']['total_cost'], '0.02578')
        self.assertEqual(denied['outcomes']['observed_workload_cost'], '0.00578')
        self.assertIsNone(denied['outcomes']['experimental_evaluation_cost'])
        self.assertEqual(denied['outcomes']['coverage'], 'incomplete')
        self.assertNotEqual(positive['corpus_id'], denied['corpus_id'])

    def test_missing_tool_scope_does_not_prove_zero_experimental_cost(self):
        positive = self.analyze()
        self.assertEqual(positive['outcomes']['experimental_evaluation_cost'], '0')
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
                                       if item['kind'] != 'tool_usage']
        unknown = self.analyze()
        self.assertIsNone(unknown['totals']['total_cost'])
        self.assertEqual(unknown['outcomes']['coverage'], 'incomplete')
        self.assertIsNone(unknown['outcomes']['experimental_evaluation_cost'])
        inventory = self.base.data['bundle']['inventories'][0]
        proof = next(item for item in self.base.data['bundle']['evidence_objects']
                     if item['kind'] == 'inventory_evidence')
        self.fixture.authorize('tool_scope_empty', self.scope, inventory, proof)
        verified = self.analyze()
        self.assertEqual(verified['totals']['total_cost'], '0.00578')
        self.assertEqual(verified['outcomes']['experimental_evaluation_cost'], '0')
        self.assertNotEqual(verified['corpus_id'], unknown['corpus_id'])

    def test_tool_with_late_nested_evidence_is_excluded_from_fixed_corpus(self):
        from usage_telemetry_report import analyze_corpus
        def verify_input(item, value, scope):
            proof = self.fixture.verify_input(item, value, scope)
            if item['kind'] == 'tool_usage':
                proof['member_times'] = {contract.content_id(entry): '2029-01-01T00:00:00Z'
                                         for entry in value['evidence_objects']}
                quantity = next(entry for entry in value['evidence_objects'] if entry['kind'] == 'tool_quantity_evidence')
                proof['member_times'][contract.content_id(quantity)] = '2030-01-01T00:00:00Z'
            return proof
        report = analyze_corpus(copy.deepcopy(self.base.manifest), verify_input=verify_input,
                                verify_evidence=self.base.authority)
        self.assertIsNone(report['totals']['total_cost'])
        self.assertEqual(report['outcomes']['coverage'], 'incomplete')
        self.assertIn('late_evidence', {item['reason'] for item in report['exclusions']})

    def test_model_only_leaf_costs_do_not_hide_selected_tool_expenses(self):
        report = self.analyze()
        self.assertEqual(report['totals']['total_cost'], '0.02578')
        self.assertEqual(report['top_leaves'], [])
        self.assertTrue(report['partial_leaves'])
        self.assertTrue(all(item['coverage'] in ('subtotal_only', 'proven_lower_bound')
                            for item in report['partial_leaves']))


if __name__ == '__main__':
    unittest.main()
