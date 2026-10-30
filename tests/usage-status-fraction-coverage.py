#!/usr/bin/env python3
"""Exact coverage fractions need not have terminating decimal expansions."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('coverage', ROOT / 'tests/usage-status-coverage-integration.py')
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)
fixture, contract = coverage.fixture, coverage.contract


def one_of_three():
    snapshot, extra, allowed = coverage.incomplete()
    bundle = snapshot['bundles'][0]
    inventory = bundle['inventories'][0]
    third = 'sha256:' + '3' * 64
    inventory['expected_calls'].append({'call_id': third})
    inventory['expected_responses'].append({'call_id': third, 'response_id': third})
    old_digest = inventory['evidence']
    proof = next(item for item in bundle['evidence_objects'] if contract.content_id(item) == old_digest)
    proof['inventory_digest'] = contract.content_id({k: v for k, v in inventory.items() if k != 'evidence'})
    inventory['evidence'] = contract.content_id(proof)
    snapshot['inventories'] = [copy.deepcopy(inventory)]
    snapshot['inventory_evidence'] = [copy.deepcopy(proof)]
    receipt = snapshot['accepted_receipts'][0]
    receipt['bundle_sha256'] = contract.content_id(bundle)
    allowed = [item for item in allowed if item[0] not in ('receipt', 'inventory')]
    allowed += [('receipt', snapshot['owner_scope'], copy.deepcopy(receipt), copy.deepcopy(bundle)),
                ('inventory', snapshot['owner_scope'], copy.deepcopy(inventory), copy.deepcopy(proof))]
    contract.validate_current_run_snapshot(snapshot)
    return snapshot, extra, allowed


class ExactCoverageTests(unittest.TestCase):
    def test_fraction_is_exact_and_compared_without_decimal_rounding(self):
        snapshot, extra, allowed = one_of_three()
        policy = fixture.policy()
        policy.update(token_threshold=None, money_threshold=None,
                      minimum_completeness={'value': '0.34', 'unit': 'fraction'})
        def evaluate():
            return fixture.alerts.evaluate_status(snapshot, policy, observed_at=fixture.NOW,
                         analysis_inputs=extra, verifier=fixture.resolution.Verifier(allowed))
        result = evaluate()
        self.assertEqual(result['measurements']['completeness'], {'state': 'final',
                         'value': {'numerator': 1, 'denominator': 3}, 'unit': 'fraction'})
        self.assertEqual([item['metric'] for item in result['candidates']], ['completeness'])
        policy['minimum_completeness']['value'] = '0.3333333333333333333333333333333333333333'
        self.assertEqual(evaluate()['candidates'], [])
        allowed = [item for item in allowed if item[0] != 'inventory']
        unknown = evaluate()
        self.assertEqual(unknown['candidates'], [])
        self.assertIn('coverage_unknown', unknown['diagnostics'])


if __name__ == '__main__':
    unittest.main()
