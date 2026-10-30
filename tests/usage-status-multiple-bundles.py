#!/usr/bin/env python3
"""Current-owner status resolves receipts as observations, not additive totals."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('status_fixture', ROOT / 'tests/usage-status-integration.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
contract = fixture.contract


def split(duplicate=False):
    snapshot, extra, allowed = fixture.inputs()
    original = snapshot['bundles'][0]
    first = copy.deepcopy(original)
    second = copy.deepcopy(original)
    if not duplicate:
        first['observations'] = [first['observations'][0]]
        second['observations'] = [second['observations'][1]]
    second['inventories'] = []
    receipts = []
    allowed = [entry for entry in allowed if entry[0] != 'receipt']
    for bundle in (first, second):
        receipt = {'schema_version': 1, 'kind': 'usage_accepted',
                   'bundle_sha256': contract.content_id(bundle),
                   'observation_ids': [contract.observation_id(obs) for obs in bundle['observations']],
                   'scope': snapshot['owner_scope'] | {'attribution_quality': 'verified'},
                   'duplicate': False, 'validator_version': '1'}
        receipts.append(receipt)
        allowed.append(('receipt', snapshot['owner_scope'], receipt, bundle))
    snapshot['bundles'] = [first, second]
    snapshot['accepted_receipts'] = receipts
    contract.validate_current_run_snapshot(snapshot)
    return snapshot, extra, allowed


class MultipleBundleStatusTests(unittest.TestCase):
    def evaluate(self, snapshot, extra, allowed):
        return fixture.alerts.evaluate_status(snapshot, fixture.policy(), observed_at=fixture.NOW,
                    analysis_inputs=extra, verifier=fixture.resolution.Verifier(allowed))

    def test_explicit_receipts_share_one_identity_aware_resolution(self):
        snapshot, extra, allowed = split()
        result = self.evaluate(snapshot, extra, allowed)
        self.assertEqual(result['measurements']['tokens']['value'], 2200)
        self.assertEqual(result['measurements']['cost_usd']['value'], '0.00289')
        self.assertEqual({entry['metric'] for entry in result['candidates']}, {'tokens', 'cost_usd'})
        contract.validate_current_run_snapshot(result['proposed_snapshot'])

    def test_same_observations_across_receipts_are_not_counted_twice(self):
        snapshot, extra, allowed = split(duplicate=True)
        result = self.evaluate(snapshot, extra, allowed)
        self.assertEqual(result['measurements']['tokens']['value'], 2200)
        self.assertEqual(result['measurements']['cost_usd']['value'], '0.00289')

    def test_untrusted_receipt_never_joins_the_owner_report(self):
        snapshot, extra, allowed = split()
        second = snapshot['accepted_receipts'][1]
        allowed = [entry for entry in allowed if not (entry[0] == 'receipt' and entry[2] == second)]
        result = self.evaluate(snapshot, extra, allowed)
        self.assertEqual(result['candidates'], [])
        self.assertNotEqual(result['measurements'].get('tokens', {}).get('state'), 'final')


if __name__ == '__main__':
    unittest.main()
