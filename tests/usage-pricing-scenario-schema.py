#!/usr/bin/env python3
"""Offline checks for named, evidence-aware pricing scenarios."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contract', ROOT / 'scripts/usage_telemetry_contract.py')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def call(name, *args):
    return getattr(contract, name, lambda *args: None)(*args)


def scenario():
    return {
        'schema_version': 1, 'kind': 'pricing_scenario', 'scenario_id': 'baseline',
        'basis': 'at_execution', 'currency': 'USD', 'display_precision': 4,
        'snapshot_ids': ['a' * 64, 'b' * 64],
        'source_parameters': {
            'model': {'value': 'vendor/model', 'evidence': 'c' * 64},
            'service_tier': {'value': 'standard', 'evidence': 'd' * 64},
            'region': {'value': 'example-region', 'evidence': 'e' * 64},
            'modality': {'value': 'text', 'evidence': 'f' * 64},
        },
        'assumptions': {},
        'threshold_rules': [
            {'operand': 'input_tokens', 'operator': '>=', 'value': 200000,
             'components': ['input_uncached', 'output']},
        ],
    }


class PricingScenarioSchemaTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_pricing_scenario', value), value)

    def test_named_scenarios_and_explicit_unknowns(self):
        value = scenario()
        self.assert_valid(value)
        value['source_parameters']['region'] = None
        self.assert_valid(value)
        value['basis'] = 'reprice'
        value['assumptions'] = {'service_tier': 'standard', 'region': 'example-region',
                                'modality': 'text'}
        self.assert_valid(value)
        value['threshold_rules'] = []
        self.assert_valid(value)

    def test_version_identity_currency_basis_and_precision_are_strict(self):
        value = scenario()
        self.assert_valid(value)
        for field in value:
            with self.subTest(missing=field), self.assertRaises(ValueError):
                call('validate_pricing_scenario', {k: v for k, v in value.items() if k != field})
        for change in ({'schema_version': True}, {'schema_version': 2}, {'kind': 'invoice'},
                       {'scenario_id': ''}, {'scenario_id': '/private/file'},
                       {'scenario_id': 'x' * 257}, {'basis': 'historic'}, {'currency': 'EUR'},
                       {'display_precision': -1}, {'display_precision': True},
                       {'display_precision': 9007199254740992}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_pricing_scenario', value | change)

    def test_reprice_assumptions_are_explicit_and_cannot_replace_work(self):
        value = scenario()
        value['basis'] = 'reprice'
        value['assumptions'] = {'region': 'example-region'}
        self.assert_valid(value)
        for key in ('model', 'quantity', 'cache_ttl_seconds', 'threshold_operand',
                    'inventory', 'attribution', 'other'):
            invalid = copy.deepcopy(value)
            invalid['assumptions'][key] = 'invented'
            with self.subTest(key=key), self.assertRaises(ValueError):
                call('validate_pricing_scenario', invalid)
        for bad in ('', '/private/path', True, None):
            invalid = copy.deepcopy(value)
            invalid['assumptions']['region'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                call('validate_pricing_scenario', invalid)
        value['basis'] = 'at_execution'
        with self.assertRaises(ValueError):
            call('validate_pricing_scenario', value)

    def test_source_parameters_require_evidence_or_explicit_unknown(self):
        value = scenario()
        self.assert_valid(value)
        for field in value['source_parameters']:
            invalid = copy.deepcopy(value)
            del invalid['source_parameters'][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                call('validate_pricing_scenario', invalid)
        for bad in ({'value': 'actual'}, {'evidence': 'a' * 64},
                    {'value': '', 'evidence': 'a' * 64},
                    {'value': 'actual', 'evidence': '/secret'},
                    {'value': 'actual', 'evidence': 'a' * 64, 'raw': 'secret'},
                    'unknown', False):
            invalid = copy.deepcopy(value)
            invalid['source_parameters']['model'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                call('validate_pricing_scenario', invalid)

    def test_snapshot_references_and_threshold_rules_are_typed(self):
        value = scenario()
        self.assert_valid(value)
        for ids in ([], ['a' * 63], ['/private'], ['A' * 64], ['a' * 64, 'a' * 64], True):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                call('validate_pricing_scenario', value | {'snapshot_ids': ids})
        for change in ({'operand': ''}, {'operator': '='}, {'value': -1}, {'value': True},
                       {'value': 9007199254740992}, {'components': []},
                       {'components': ['input_uncached', 'input_uncached']},
                       {'components': ['not_a_component']}):
            invalid = copy.deepcopy(value)
            invalid['threshold_rules'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_pricing_scenario', invalid)

    def test_forbidden_fields_do_not_leak(self):
        value = scenario()
        self.assert_valid(value)
        secret = 'PRIVATE_CONTENT_SENTINEL'
        with self.assertRaises(ValueError) as error:
            call('validate_pricing_scenario', value | {'raw_content': secret})
        self.assertNotIn(secret, str(error.exception))

    def test_identity_uses_schema_sets_and_is_sensitive_to_semantics(self):
        value = scenario()
        self.assert_valid(value)
        identity = call('pricing_scenario_id', value)
        self.assertRegex(identity, r'^[0-9a-f]{64}$')
        reordered = copy.deepcopy(value)
        reordered['snapshot_ids'].reverse()
        reordered['threshold_rules'][0]['components'].reverse()
        self.assertEqual(call('pricing_scenario_id', reordered), identity)
        reordered['display_precision'] = 3
        self.assertNotEqual(call('pricing_scenario_id', reordered), identity)

    def test_json_limits_duplicates_and_bounded_tree(self):
        value = scenario()
        self.assert_valid(value)
        data = json.dumps(value, separators=(',', ':')).encode()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'PRICING_SCENARIO_LIMIT', size, create=True):
            self.assert_valid(value)
        with patch.object(contract, 'PRICING_SCENARIO_LIMIT', size - 1, create=True):
            with self.assertRaises(ValueError):
                call('validate_pricing_scenario', value)
        with patch.object(contract, 'PRICING_SCENARIO_LIMIT', len(data), create=True):
            self.assertEqual(call('validate_pricing_scenario_json', data), value)
            with self.assertRaises(ValueError):
                call('validate_pricing_scenario_json', data + b' ')
        with self.assertRaises(ValueError):
            call('validate_pricing_scenario_json', b'{"schema_version":1,"schema_version":1}')
        oversized = copy.deepcopy(value)
        oversized['assumptions'] = {str(i): 'value' for i in range(257)}
        with self.assertRaises(ValueError):
            call('validate_pricing_scenario', oversized)


if __name__ == '__main__':
    unittest.main()
