#!/usr/bin/env python3
"""Offline completeness checks using independent synthetic inventory evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
contract_spec = importlib.util.spec_from_file_location('contract', ROOT / 'scripts/usage_telemetry_contract.py')
contract = importlib.util.module_from_spec(contract_spec)
contract_spec.loader.exec_module(contract)


def calculate(*args, **kwargs):
    path = ROOT / 'scripts/usage_telemetry_completeness.py'
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location('completeness', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.calculate_completeness(*args, **kwargs)


def opaque(char):
    return 'sha256:' + char * 64


def inventory(responses=('1', '2'), *, coverage='included'):
    calls = [{'call_id': opaque(char)} for char in responses]
    value = {
        'schema_version': 1, 'kind': 'inventory', 'profile_id': 'fixture',
        'profile_version': '1', 'source_hash': 'a' * 64,
        'owner_scope': {'owner_kind': 'run', 'owner_id': opaque('b')},
        'window': {'start': '2026-01-01T00:00:00Z', 'end': '2026-01-01T01:00:00Z'},
        'observed_at': '2026-01-01T01:01:00Z', 'state': 'complete', 'evidence': None,
        'expected_calls': calls,
        'expected_responses': [{'call_id': opaque(char), 'response_id': opaque(char)} for char in responses],
        'unresolved_slots': [],
        'coverage': {'children': 'included', 'internal_checks': 'included', 'tools': coverage},
    }
    return bind(value)


def bind(value):
    evidence = {'schema_version': 1, 'kind': 'inventory_evidence',
                'profile_id': value['profile_id'], 'profile_version': value['profile_version'],
                'source_hash': value['source_hash'],
                'inventory_digest': contract.content_id({k: v for k, v in value.items() if k != 'evidence'})}
    value['evidence'] = contract.content_id(evidence)
    contract.validate_inventory(value)
    contract.validate_evidence_object(evidence)
    return value, evidence


def response(char, *, priced=True, final=True, input_known=True, output_known=True):
    return {'response_id': opaque(char), 'call_id': opaque(char), 'final': final,
            'measurements': {'input': input_known, 'output': output_known}, 'priced': priced}


def trusted_verifier(expected_inventory, expected_evidence, *, empty_billable=False):
    """Represent a trusted integration boundary, not a claim from the input JSON."""
    def verify(candidate, evidence, scope):
        verified = (candidate == expected_inventory and evidence == expected_evidence
                    and scope == expected_inventory['owner_scope'])
        return {'inventory_verified': verified,
                'billable_scope_empty': verified and empty_billable}
    return verify


class CompletenessTests(unittest.TestCase):
    def setUp(self):
        self.inventory, self.evidence = inventory()
        self.scope = self.inventory['owner_scope']
        self.verifier = trusted_verifier(self.inventory, self.evidence)

    def run_report(self, records, *, value=None, evidence=None, verifier=None, scope=None, tools=()):
        return calculate(value if value is not None else self.inventory,
                         evidence if evidence is not None else self.evidence,
                         records, scope=scope if scope is not None else self.scope,
                         verify_inventory=verifier if verifier is not None else self.verifier,
                         tool_costs=list(tools))

    def test_tokens_and_pricing_are_separate_coverage_measures(self):
        report = self.run_report([response('1'), response('2', priced=False)])
        self.assertEqual(report['finality'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['measurements']['input'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['measurements']['output'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['priced'], {'numerator': 1, 'denominator': 2})
        self.assertFalse(report['zero_cost_proven'])

    def test_missing_inventory_has_unknown_denominator(self):
        unknown = copy.deepcopy(self.inventory)
        unknown.update(state='unknown', evidence=None, expected_calls=[], expected_responses=[])
        report = self.run_report([response('1'), response('2')], value=unknown,
                                 verifier=lambda *_: {'inventory_verified': False, 'billable_scope_empty': False})
        self.assertIsNone(report['finality']['denominator'])
        self.assertIsNone(report['priced']['denominator'])
        self.assertFalse(report['zero_cost_proven'])

    def test_matching_evidence_hash_without_independent_provenance_is_not_a_denominator(self):
        report = self.run_report([response('1'), response('2')], verifier=lambda *_: {
            'inventory_verified': False, 'billable_scope_empty': False})
        self.assertIsNone(report['finality']['denominator'])
        self.assertFalse(report['zero_cost_proven'])

    def test_wrong_scope_or_evidence_cannot_be_verified(self):
        wrong_scope = {'owner_kind': 'run', 'owner_id': opaque('c')}
        report = self.run_report([response('1')], scope=wrong_scope)
        self.assertIsNone(report['finality']['denominator'])
        wrong_evidence = self.evidence | {'source_hash': 'f' * 64}
        report = self.run_report([response('1')], evidence=wrong_evidence)
        self.assertIsNone(report['finality']['denominator'])

    def test_individually_missing_measurements_are_independent(self):
        report = self.run_report([response('1'), response('2', output_known=False)])
        self.assertEqual(report['measurements']['input'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['measurements']['output'], {'numerator': 1, 'denominator': 2})

    def test_partial_inventory_and_unresolved_branch_have_unknown_denominator(self):
        value = copy.deepcopy(self.inventory)
        value.update(state='partial', unresolved_slots=[{'call_id': opaque('1'), 'reason': 'identity_unresolved'}])
        value, evidence = bind(value)
        report = self.run_report([response('1'), response('2')], value=value, evidence=evidence,
                                 verifier=trusted_verifier(value, evidence))
        self.assertIsNone(report['finality']['denominator'])
        self.assertIsNone(report['priced']['denominator'])
        self.assertFalse(report['zero_cost_proven'])

    def test_duplicate_response_is_not_counted_twice(self):
        report = self.run_report([response('1'), response('1'), response('2')])
        self.assertEqual(report['finality'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['priced'], {'numerator': 2, 'denominator': 2})

    def test_two_responses_for_one_call_are_two_slots(self):
        value = copy.deepcopy(self.inventory)
        value['expected_calls'] = [{'call_id': opaque('1')}]
        value['expected_responses'][1]['call_id'] = opaque('1')
        value, evidence = bind(value)
        second = response('2') | {'call_id': opaque('1')}
        report = self.run_report([response('1'), second], value=value, evidence=evidence,
                                 verifier=trusted_verifier(value, evidence))
        self.assertEqual(report['finality'], {'numerator': 2, 'denominator': 2})

    def test_unexpected_response_does_not_produce_fraction_above_one(self):
        report = self.run_report([response('1'), response('2'), response('3')])
        self.assertIsNone(report['finality']['denominator'])
        self.assertFalse(report['zero_cost_proven'])

    def test_conflicting_duplicate_never_becomes_full_coverage(self):
        report = self.run_report([response('1'), response('1', priced=False), response('2')])
        self.assertNotEqual(report['priced'], {'numerator': 2, 'denominator': 2})
        self.assertFalse(report['zero_cost_proven'])

    def test_proven_empty_billable_scope_has_not_applicable_fraction(self):
        value, evidence = inventory(())
        report = self.run_report([], value=value, evidence=evidence,
                                 verifier=trusted_verifier(value, evidence, empty_billable=True))
        self.assertEqual(report['finality'], {'state': 'not_applicable', 'numerator': None, 'denominator': None})
        self.assertEqual(report['priced'], {'state': 'not_applicable', 'numerator': None, 'denominator': None})
        self.assertTrue(report['zero_cost_proven'])

    def test_empty_model_inventory_is_not_proof_of_empty_tool_spending(self):
        value, evidence = inventory(())
        report = self.run_report([], value=value, evidence=evidence,
                                 verifier=trusted_verifier(value, evidence))
        self.assertFalse(report['zero_cost_proven'])
        report = self.run_report([], value=value, evidence=evidence,
                                 verifier=trusted_verifier(value, evidence, empty_billable=True), tools=('0.02',))
        self.assertFalse(report['zero_cost_proven'])

    def test_unknown_tool_coverage_cannot_prove_zero(self):
        value, evidence = inventory((), coverage='unknown')
        report = self.run_report([], value=value, evidence=evidence,
                                 verifier=trusted_verifier(value, evidence, empty_billable=True))
        self.assertFalse(report['zero_cost_proven'])

    def test_unknown_model_coverage_cannot_supply_response_denominator(self):
        for dimension in ('children', 'internal_checks'):
            with self.subTest(dimension=dimension):
                value = copy.deepcopy(self.inventory)
                value['coverage'][dimension] = 'unknown'
                value, evidence = bind(value)
                report = self.run_report([response('1'), response('2')], value=value, evidence=evidence,
                                         verifier=trusted_verifier(value, evidence))
                self.assertIsNone(report['finality']['denominator'])
                self.assertIsNone(report['measurements']['input']['denominator'])
                self.assertIsNone(report['priced']['denominator'])

    def test_unknown_model_coverage_cannot_establish_empty_scope(self):
        for dimension in ('children', 'internal_checks'):
            with self.subTest(dimension=dimension):
                value, _ = inventory(())
                value['coverage'][dimension] = 'unknown'
                value, evidence = bind(value)
                report = self.run_report([], value=value, evidence=evidence,
                                         verifier=trusted_verifier(value, evidence, empty_billable=True))
                self.assertIsNone(report['finality']['denominator'])
                self.assertNotEqual(report['finality'].get('state'), 'not_applicable')
                self.assertFalse(report['zero_cost_proven'])

    def test_verified_model_coverage_keeps_denominator_with_unknown_tools(self):
        value = copy.deepcopy(self.inventory)
        value['coverage']['tools'] = 'unknown'
        value, evidence = bind(value)
        report = self.run_report([response('1'), response('2')], value=value, evidence=evidence,
                                 verifier=trusted_verifier(value, evidence))
        self.assertEqual(report['finality'], {'numerator': 2, 'denominator': 2})
        self.assertFalse(report['zero_cost_proven'])

    def test_excluded_tools_cannot_prove_empty_billable_scope(self):
        value, evidence = inventory((), coverage='excluded')
        report = self.run_report([], value=value, evidence=evidence,
                                 verifier=trusted_verifier(value, evidence, empty_billable=True))
        self.assertEqual(report['finality']['state'], 'not_applicable')
        self.assertFalse(report['zero_cost_proven'])

    def test_unfinished_response_does_not_count_as_final(self):
        report = self.run_report([response('1'), response('2', final=False)])
        self.assertEqual(report['finality'], {'numerator': 1, 'denominator': 2})
        self.assertNotEqual(report['priced'], {'numerator': 2, 'denominator': 2})


if __name__ == '__main__':
    unittest.main()
