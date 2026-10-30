#!/usr/bin/env python3
"""Untrusted response identifiers must not escape the resolution boundary."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class ResponsePrivacyTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = base.fixture()
        self.allowed = [item for item in self.allowed if item[0] != 'response_privacy']
        self.privacy = [('response_privacy', self.data['scope'], item, item)
                        for item in self.data['bundle']['observations']]

    def assert_hidden(self, result, observations, *, shared_scope=False):
        encoded = json.dumps(result, sort_keys=True)
        for item in observations:
            values = [item['response_id'], item['call_id'], item['response_id'][7:],
                      'sha256:' + base.contract.observation_id(item)]
            if not shared_scope:
                values.append(item['provider_scope'])
            for value in values:
                self.assertNotIn(value, encoded)

    def test_rejected_authority_cannot_disclose_identifiers(self):
        result = base.resolve(self.data, base.Verifier([]))
        self.assert_hidden(result, self.data['bundle']['observations'])
        self.assertEqual(result['responses'], [])
        self.assertNotEqual(result['identity']['state'], 'complete')

    def test_privacy_requires_independent_exact_scope_and_record(self):
        first, second = self.data['bundle']['observations']
        verifier = base.Verifier(self.allowed + self.privacy[:1])
        result = base.resolve(self.data, verifier)
        self.assert_hidden(result, [second], shared_scope=True)
        self.assertTrue(any(row['identity']['id'] == first['response_id'] for row in result['responses']))
        self.assertIn(('response_privacy', self.data['scope'], first, first), verifier.calls)
        wrong_scope = copy.deepcopy(self.privacy[0])
        wrong_scope[1]['owner_id'] = base.opaque('f')
        result = base.resolve(self.data, base.Verifier(self.allowed + [wrong_scope]))
        self.assert_hidden(result, [first, second])

    def test_exact_authorization_discloses_verified_records(self):
        result = base.resolve(self.data, base.Verifier(self.allowed + self.privacy))
        self.assertEqual({row['identity']['id'] for row in result['responses']},
                         {item['response_id'] for item in self.data['bundle']['observations']})
        self.assertEqual(result['identity']['state'], 'complete')


if __name__ == '__main__':
    unittest.main()
