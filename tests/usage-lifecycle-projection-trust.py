#!/usr/bin/env python3
"""Checks the explicit trusted boundary for self-contained projections."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

publication = load('publication', 'scripts/usage_telemetry_publication.py')
fixtures = load('lifecycle_integration', 'tests/usage-lifecycle-projection.py')

class TrustedProjectionTests(unittest.TestCase):
    def setUp(self):
        self.value = fixtures.exact_projection()
        self.scope = copy.deepcopy(self.value['scope'])
        self.verify = publication.validate_lifecycle_projection_for_owner

    def test_exact_projection_is_checked_before_authorization(self):
        seen = []
        result = self.verify(self.value, scope=self.scope, cost_usd='0.00264',
                             authorize=lambda projection, owner: seen.append((projection, owner)) or True)
        self.assertEqual(result, self.value)
        self.assertEqual(seen, [(self.value, self.scope)])
        self.assertIsNot(result, self.value)

    def test_untrusted_evidence_or_scope_and_mismatched_amount_are_rejected(self):
        for verifier in (None, lambda projection, owner: False, lambda projection, owner: 1):
            with self.subTest(verifier=verifier), self.assertRaises(ValueError):
                self.verify(self.value, scope=self.scope, cost_usd='0.00264', authorize=verifier)
        with self.assertRaises(ValueError):
            self.verify(self.value, scope=self.scope | {'owner_id': 'sha256:' + '4' * 64},
                        cost_usd='0.00264', authorize=lambda *_: True)
        for amount in ('0', '0.002640', '0.00263'):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                self.verify(self.value, scope=self.scope, cost_usd=amount, authorize=lambda *_: True)
        changed = copy.deepcopy(self.value)
        changed['evidence_objects'][0]['value'] += 1
        with self.assertRaises(ValueError):
            self.verify(changed, scope=self.scope, cost_usd='0.00264', authorize=lambda *_: True)

    def test_verifier_cannot_change_projection_or_owner_and_exceptions_are_sanitized(self):
        def mutate_projection(candidate, owner):
            candidate['cost_usd'] = '0'
            return True
        def mutate_owner(candidate, owner):
            owner['owner_id'] = 'sha256:' + '4' * 64
            return True
        def broken(candidate, owner):
            raise RuntimeError('private source path')
        for verifier in (mutate_projection, mutate_owner, broken):
            with self.subTest(verifier=verifier), self.assertRaises(ValueError) as raised:
                self.verify(self.value, scope=self.scope, authorize=verifier)
            self.assertNotIn('private source path', str(raised.exception))
        self.assertEqual(self.value['cost_usd'], '0.00264')
        self.assertEqual(self.scope, self.value['scope'])

if __name__ == '__main__':
    unittest.main()
