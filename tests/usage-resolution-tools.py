#!/usr/bin/env python3
"""Separately verified tool units contribute to scoped exact cost once."""
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


base = load('integration', 'tests/usage-resolution-integration.py')
empty = load('empty', 'tests/usage-resolution-empty-scope.py')
ownership = load('owner', 'tests/usage-resolution-ownership.py')
contract = base.contract


def fixture(empty_model=True):
    if empty_model:
        data, allowed = empty.empty_fixture()
    else:
        data, allowed = base.fixture()
        ownership.pricing_through_2029(data, allowed)
    allowed = [item for item in allowed if item[0] != 'tool_scope_empty']
    snapshot = data['snapshots'][0]
    snapshot['rates'].append({'component': 'tool', 'usd': '0.01', 'unit': 'request',
                              'unit_quantity': 1, 'cache_ttl_seconds': None, 'threshold': None,
                              'tool_id': 'search', 'multiplier': {'state': 'none'}})
    data['scenario']['snapshot_ids'] = [contract.price_snapshot_id(snapshot)]
    for proof in data['price_evidence']:
        if proof['kind'] == 'price_snapshot_evidence':
            proof['snapshot_id'] = contract.price_snapshot_id(snapshot)
    allowed = [item for item in allowed if item[0] != 'price']
    allowed.extend(('price', data['scope'], snapshot, proof) for proof in data['price_evidence'])
    scope = {'profile_id': data['profile']['profile_id'], 'source_hash': 'a' * 64, 'record_number': 1}
    params = {'model': 'vendor/model', 'service_tier': 'standard', 'region': 'example-region', 'modality': 'text'}
    proofs = [{'schema_version': 1, 'kind': 'execution_time_evidence', **scope, 'value': '2026-01-01T00:00:00Z'}]
    proofs += [{'schema_version': 1, 'kind': 'source_parameter_evidence', **scope, 'field': name, 'value': value}
               for name, value in params.items()]
    proofs.append({'schema_version': 1, 'kind': 'rate_parameter_evidence', **scope, 'field': 'tool_id', 'value': 'search'})
    quantity = {'schema_version': 1, 'kind': 'tool_quantity_evidence', **scope,
                'tool_id': 'search', 'unit': 'request', 'value': 2}
    proofs.append(quantity)
    tool = {'schema_version': 1, 'kind': 'tool_usage', 'usage_id': base.opaque('f'),
            'profile_id': scope['profile_id'], 'profile_version': data['profile']['profile_version'],
            'source_hash': scope['source_hash'], 'record_number': 1, 'provider_scope': base.opaque('c'),
            'tool_id': 'search', 'unit': 'request', 'quantity': 2, 'observed_at': '2026-01-02T00:00:00Z',
            'execution_time': '2026-01-01T00:00:00Z', 'parameters': params, 'evidence_objects': proofs}
    data['tool_inputs'] = [tool]
    inv = data['bundle']['inventories'][0]
    inv_proof = next(item for item in data['bundle']['evidence_objects'] if item['kind'] == 'inventory_evidence')
    completeness = {'inventory_evidence': inv_proof, 'tool_usage_ids': [tool['usage_id']]}
    allowed += [('tool_privacy', data['scope'], tool, tool),
                ('tool_usage', data['scope'], tool, quantity),
                ('tool_inventory', data['scope'], inv, completeness),
                ('tool_nonoverlap', data['scope'], inv, completeness)]
    for proof in proofs:
        if proof['kind'] != 'tool_quantity_evidence':
            allowed.append(('pricing_context', data['scope'], tool, proof))
    return data, allowed


class ToolCostTests(unittest.TestCase):
    def report(self, data, allowed):
        return base.resolve(data, base.Verifier(allowed))

    def test_empty_model_inventory_and_known_tool_expense_is_not_zero(self):
        data, allowed = fixture()
        result = self.report(data, allowed)
        self.assertEqual(result['completeness']['finality']['state'], 'not_applicable')
        self.assertFalse(result['completeness']['zero_cost_proven'])
        self.assertEqual(result['cost']['cost_usd'], '0.02')
        self.assertEqual(result['tools'][0]['cost_usd'], '0.02')
        self.assertEqual(contract.validate_tool_usage(data['tool_inputs'][0]), data['tool_inputs'][0])

    def test_explicit_empty_tool_inputs_preserve_proven_empty_scope(self):
        data, allowed = empty.empty_fixture()
        data['tool_inputs'] = []
        result = self.report(data, allowed)
        self.assertTrue(result['completeness']['zero_cost_proven'])
        self.assertEqual(result['cost']['cost_usd'], '0')
        self.assertEqual(result['tools'], [])

    def test_tool_and_response_model_costs_add_without_overlap(self):
        data, allowed = fixture(empty_model=False)
        result = self.report(data, allowed)
        self.assertEqual(result['cost']['cost_usd'], '0.02578')
        self.assertEqual(result['completeness']['priced'], {'numerator': 2, 'denominator': 2})
        self.assertEqual([item['model_cost']['cost_usd'] for item in result['responses']], ['0.00289', '0.00289'])
        self.assertEqual(result['tools'][0]['cost_usd'], '0.02')

    def test_repriced_tools_remain_conditional(self):
        data, allowed = fixture()
        data['scenario']['basis'] = 'reprice'
        result = self.report(data, allowed)
        self.assertEqual(result['cost']['cost_usd'], '0.02')
        self.assertIs(result['cost']['conditional'], True)
        self.assertIs(result['tools'][0]['conditional'], True)

    def test_missing_provenance_inventory_or_nonoverlap_prevents_total(self):
        data, allowed = fixture()
        for kind in ('tool_privacy', 'tool_usage', 'tool_inventory', 'tool_nonoverlap', 'pricing_context'):
            with self.subTest(kind=kind):
                result = self.report(data, [item for item in allowed if item[0] != kind])
                self.assertNotIn('cost_usd', result['cost'])
                self.assertFalse(result['completeness']['zero_cost_proven'])

    def test_identical_tool_input_is_counted_once_conflicting_id_is_not_added(self):
        data, allowed = fixture()
        data['tool_inputs'].append(copy.deepcopy(data['tool_inputs'][0]))
        result = self.report(data, allowed)
        self.assertEqual(result['cost']['cost_usd'], '0.02')
        bad = copy.deepcopy(data['tool_inputs'][0])
        bad['quantity'] = 3
        data['tool_inputs'].append(bad)
        result = self.report(data, allowed)
        self.assertNotIn('cost_usd', result['cost'])
        self.assertNotEqual(result['cost'].get('subtotal_quality'), 'proven_lower_bound')

    def test_wrong_source_quantity_or_unavailable_price_cannot_be_assumed(self):
        data, allowed = fixture()
        data['tool_inputs'][0]['quantity'] = 3
        result = self.report(data, allowed)
        self.assertNotIn('cost_usd', result['cost'])
        data, allowed = fixture()
        data.update(scenario=None, snapshots=[], price_evidence=[])
        result = self.report(data, allowed)
        self.assertNotIn('cost_usd', result['cost'])
        self.assertTrue(result['cost']['unpriced_ids'])

    def test_closed_tool_schema_binds_quantity_and_sanitizes_errors(self):
        data, _ = fixture()
        tool = data['tool_inputs'][0]
        self.assertEqual(contract.validate_tool_usage(tool), tool)
        for mutation in ({'quantity': True}, {'quantity': -1}, {'source_hash': '/PRIVATE_PATH'},
                         {'raw_payload': 'PRIVATE_SENTINEL'}, {'schema_version': 2}):
            with self.subTest(fields=list(mutation)), self.assertRaises(ValueError) as caught:
                contract.validate_tool_usage(tool | mutation)
            self.assertNotIn('PRIVATE_SENTINEL', str(caught.exception))
            self.assertNotIn('/PRIVATE_PATH', str(caught.exception))
        changed = copy.deepcopy(tool)
        next(item for item in changed['evidence_objects'] if item['kind'] == 'tool_quantity_evidence')['value'] = 3
        with self.assertRaises(ValueError):
            contract.validate_tool_usage(changed)

    def test_late_tool_evidence_is_not_imported_into_an_old_scope(self):
        data, allowed = fixture()
        data['tool_inputs'][0]['observed_at'] = '2030-01-01T00:00:00Z'
        result = self.report(data, allowed)
        self.assertNotIn('cost_usd', result['cost'])
        self.assertFalse(result['completeness']['zero_cost_proven'])

    def test_unverified_tool_id_and_private_values_are_not_exposed(self):
        data, allowed = fixture()
        data['tool_inputs'][0]['tool_id'] = 'PRIVATE_TOOL_SECRET'
        result = self.report(data, allowed)
        self.assertNotIn('PRIVATE_TOOL_SECRET', str(result))
        self.assertNotIn('cost_usd', result['cost'])


if __name__ == '__main__':
    unittest.main()
