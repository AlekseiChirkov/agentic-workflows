#!/usr/bin/env python3
"""Verified per-response model quantities and prices for scoped consumers."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)
contract = integration.contract


class ResponseDetailTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = integration.fixture()

    def report(self, allowed=None):
        return integration.resolve(self.data, integration.Verifier(self.allowed if allowed is None else allowed))

    def details(self, report):
        return {entry['identity']['id']: entry for entry in report['responses']}

    def test_identity_tokens_and_model_cost_are_explicit_per_response(self):
        details = self.details(self.report())
        self.assertEqual(set(details), {integration.opaque('1'), integration.opaque('2')})
        first, second = details[integration.opaque('1')], details[integration.opaque('2')]
        self.assertEqual(first['identity']['provider'], self.data['profile']['provider'])
        self.assertEqual(first['identity']['provider_scope'], integration.opaque('c'))
        self.assertEqual(first['observation_ids'], ['sha256:' + contract.observation_id(self.data['bundle']['observations'][0])])
        self.assertEqual(first['tokens']['input'], {'value': '1000', 'quality': 'complete'})
        self.assertEqual(first['tokens']['output'], {'value': '100', 'quality': 'complete'})
        self.assertEqual(first['model_cost']['cost_usd'], '0.00289')
        self.assertNotIn('cost_usd', first)
        self.assertEqual(second['tokens']['input'], {'value': '1000', 'quality': 'complete'})
        self.assertNotIn('cost_usd', second['model_cost'])
        self.assertNotIn('cost_usd', second)

    def test_source_operand_rejection_never_exports_complete_input(self):
        allowed = [item for item in self.allowed if not (
            item[0] == 'measurement' and item[2]['field'] == 'input_total' and
            item[2]['observation']['record_number'] == 1)]
        first = self.details(self.report(allowed))[integration.opaque('1')]
        self.assertNotEqual(first['tokens']['input'].get('quality'), 'complete')
        self.assertNotIn('cost_usd', first['model_cost'])

    def test_unverified_identity_cannot_export_usable_per_response_cost(self):
        allowed = [item for item in self.allowed if not (
            item[0] == 'context' and item[2]['record_number'] == 1)]
        details = self.details(self.report(allowed))
        first = details.get(integration.opaque('1'))
        if first is not None:
            self.assertNotIn('cost_usd', first['model_cost'])
            self.assertNotEqual(first['tokens']['input'].get('quality'), 'complete')

    def test_conflicting_final_contexts_are_not_exported_as_one_priced_response(self):
        original = self.data['bundle']['observations'][0]
        duplicate = copy.deepcopy(original)
        duplicate['observed_at'] = '2026-01-02T04:04:05Z'
        self.data['bundle']['observations'].append(duplicate)
        context = copy.deepcopy(self.data['contexts'][0])
        context['observation_id'] = contract.observation_id(duplicate)
        context['parameters']['model'] = 'vendor/other'
        for proof in context['evidence_objects']:
            if proof.get('kind') == 'source_parameter_evidence' and proof.get('field') == 'model':
                proof['value'] = 'vendor/other'
        self.data['contexts'].append(context)
        self.allowed.append(('context', self.data['scope'], duplicate, context))
        self.allowed.append(('response_privacy', self.data['scope'], duplicate, duplicate))
        for proof in context['evidence_objects']:
            self.allowed.append(('pricing_context', self.data['scope'], duplicate, proof))
        for kind, scope, subject, proof in list(self.allowed):
            if kind == 'measurement' and subject['observation'] == original:
                self.allowed.append((kind, scope, subject | {'observation': duplicate}, proof))
        first = self.details(self.report())[integration.opaque('1')]
        self.assertNotIn('cost_usd', first['model_cost'])
        self.assertNotEqual(first['model_cost'].get('subtotal_quality'), 'proven_lower_bound')

    def test_unresolved_call_overlap_never_exports_additive_model_cost(self):
        observation = copy.deepcopy(self.data['bundle']['observations'][0])
        observation['record_number'] = 3
        del observation['response_id']
        observation['measurements'] = {'input_uncached': {'measurement_state': 'unavailable',
                                                           'reasons': ['source_unavailable']}}
        self.data['bundle']['observations'].append(observation)
        context = copy.deepcopy(self.data['contexts'][0])
        context.update(observation_id=contract.observation_id(observation), record_number=3)
        self.data['contexts'].append(context)
        self.allowed.append(('context', self.data['scope'], observation, context))
        self.allowed.append(('response_privacy', self.data['scope'], observation, observation))
        for item in self.details(self.report()).values():
            self.assertNotIn('cost_usd', item['model_cost'])
            self.assertNotEqual(item['model_cost'].get('subtotal_quality'), 'proven_lower_bound')


if __name__ == '__main__':
    unittest.main()
