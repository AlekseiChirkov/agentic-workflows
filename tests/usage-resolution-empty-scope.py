#!/usr/bin/env python3
"""An empty response inventory is zero only with complete billable scope proof."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)


def empty_fixture():
    data, allowed = integration.fixture()
    inventory = copy.deepcopy(data['bundle']['inventories'][0])
    inventory['expected_calls'] = []
    inventory['expected_responses'] = []
    inventory, evidence = integration.inventories.bind(inventory)
    data['bundle']['inventories'] = [inventory]
    data['bundle']['observations'] = []
    data['bundle']['evidence_objects'] = [evidence]
    data['contexts'] = []
    allowed = [item for item in allowed if item[0] not in ('inventory', 'nonnegative_scope',
                                                            'measurement', 'context', 'pricing_context')]
    for kind in ('inventory', 'nonnegative_scope', 'tool_scope_empty'):
        allowed.append((kind, data['scope'], inventory, evidence))
    integration.contract.validate_usage_bundle(data['bundle'])
    return data, allowed


class EmptyScopeTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = empty_fixture()

    def report(self, allowed=None):
        return integration.resolve(self.data, integration.Verifier(self.allowed if allowed is None else allowed))

    def test_complete_billable_scope_has_exact_zero_and_not_applicable_fractions(self):
        result = self.report()
        self.assertTrue(result['completeness']['zero_cost_proven'])
        self.assertEqual(result['completeness']['finality'],
                         {'state': 'not_applicable', 'numerator': None, 'denominator': None})
        self.assertEqual(result['completeness']['priced']['state'], 'not_applicable')
        self.assertEqual(result['cost']['cost_usd'], '0')

    def test_empty_model_inventory_without_tool_proof_is_not_zero(self):
        allowed = [entry for entry in self.allowed if entry[0] != 'tool_scope_empty']
        result = self.report(allowed)
        self.assertFalse(result['completeness']['zero_cost_proven'])
        self.assertNotIn('cost_usd', result['cost'])

    def test_untrusted_or_late_inventory_never_proves_empty_scope(self):
        allowed = [entry for entry in self.allowed if entry[0] != 'inventory']
        result = self.report(allowed)
        self.assertFalse(result['completeness']['zero_cost_proven'])
        self.assertNotIn('cost_usd', result['cost'])
        self.data['as_of'] = '2028-12-31T23:59:59Z'
        result = self.report()
        self.assertFalse(result['completeness']['zero_cost_proven'])
        self.assertNotIn('cost_usd', result['cost'])

    def test_tool_proof_cannot_be_inferred_from_an_input_dictionary(self):
        allowed = [entry for entry in self.allowed if entry[0] != 'tool_scope_empty']
        delegate = integration.Verifier(allowed)
        def verifier(kind, scope, subject, proof):
            return {'verified': True} if kind == 'tool_scope_empty' else delegate(kind, scope, subject, proof)
        result = integration.resolve(self.data, verifier)
        self.assertFalse(result['completeness']['zero_cost_proven'])
        self.assertNotIn('cost_usd', result['cost'])


if __name__ == '__main__':
    unittest.main()
