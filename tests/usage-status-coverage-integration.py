#!/usr/bin/env python3
"""Current coverage warnings from verified, explicit inventory evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('status_fixture', ROOT / 'tests/usage-status-integration.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
contract = fixture.contract


def incomplete():
    snapshot, extra, allowed = fixture.inputs()
    bundle = snapshot['bundles'][0]
    removed = bundle['observations'].pop()
    removed_id = contract.observation_id(removed)
    extra['contexts'] = [item for item in extra['contexts'] if item['observation_id'] != removed_id]
    extra['ownership_evidence'] = [item for item in extra['ownership_evidence'] if item['observation_id'] != removed_id]
    receipt = snapshot['accepted_receipts'][0]
    receipt['bundle_sha256'] = contract.content_id(bundle)
    receipt['observation_ids'] = [contract.observation_id(item) for item in bundle['observations']]
    allowed = [entry for entry in allowed if entry[0] != 'receipt']
    allowed.append(('receipt', snapshot['owner_scope'], copy.deepcopy(receipt), copy.deepcopy(bundle)))
    contract.validate_current_run_snapshot(snapshot)
    return snapshot, extra, allowed


class StatusCoverageIntegrationTests(unittest.TestCase):
    def test_incomplete_inventory_yields_strict_coverage_warning(self):
        snapshot, extra, allowed = incomplete()
        policy = fixture.policy()
        policy.update(token_threshold=None, money_threshold=None,
                      minimum_completeness={'value': '0.8', 'unit': 'fraction'})
        result = fixture.alerts.evaluate_status(snapshot, policy, observed_at=fixture.NOW,
                    analysis_inputs=extra, verifier=fixture.resolution.Verifier(allowed))
        self.assertEqual(result['measurements']['completeness'], {'state': 'final', 'value': '0.5', 'unit': 'fraction'})
        self.assertEqual([item['metric'] for item in result['candidates']], ['completeness'])
        policy['minimum_completeness']['value'] = '0.5'
        result = fixture.alerts.evaluate_status(snapshot, policy, observed_at=fixture.NOW,
                    analysis_inputs=extra, verifier=fixture.resolution.Verifier(allowed))
        self.assertEqual(result['candidates'], [])

    def test_missing_inventory_authority_has_unknown_coverage_without_percentage(self):
        snapshot, extra, allowed = incomplete()
        policy = fixture.policy()
        policy.update(token_threshold=None, money_threshold=None,
                      minimum_completeness={'value': '0.8', 'unit': 'fraction'})
        allowed = [entry for entry in allowed if entry[0] != 'inventory']
        result = fixture.alerts.evaluate_status(snapshot, policy, observed_at=fixture.NOW,
                    analysis_inputs=extra, verifier=fixture.resolution.Verifier(allowed))
        self.assertEqual(result['candidates'], [])
        self.assertIn('coverage_unknown', result['diagnostics'])
        self.assertNotIn('completeness', result['measurements'])


if __name__ == '__main__':
    unittest.main()
