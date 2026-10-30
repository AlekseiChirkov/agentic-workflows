#!/usr/bin/env python3
"""Model-only scoped zero needs an independently verified empty inventory."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('empty', ROOT / 'tests/usage-resolution-empty-scope.py')
empty = importlib.util.module_from_spec(spec)
spec.loader.exec_module(empty)


class EmptyOwnerTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = empty.empty_fixture()
        self.scope = {'owner_kind': 'task', 'owner_id': empty.integration.opaque('7')}
        self.data.update(owner_scopes=[self.scope], ownership_inputs=[])
        inventory = self.data['bundle']['inventories'][0]
        proof = self.data['bundle']['evidence_objects'][0]
        self.allowed.append(('ownership_inventory', self.scope, inventory, proof))

    def report(self, allowed=None):
        return empty.integration.resolve(self.data, empty.integration.Verifier(
            self.allowed if allowed is None else allowed))['ownership'][0]

    def test_verified_empty_model_scope_is_zero_even_when_tools_are_unknown(self):
        allowed = [item for item in self.allowed if item[0] != 'tool_scope_empty']
        result = self.report(allowed)
        self.assertEqual(result['attribution'], 'complete')
        self.assertEqual(result['model_cost']['cost_usd'], '0')
        self.assertEqual(result['contributors'], [])

    def test_unverified_owner_or_model_inventory_cannot_prove_zero(self):
        for kind in ('ownership_inventory', 'inventory'):
            with self.subTest(kind=kind):
                result = self.report([item for item in self.allowed if item[0] != kind])
                self.assertNotIn('cost_usd', result['model_cost'])


if __name__ == '__main__':
    unittest.main()
