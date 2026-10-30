#!/usr/bin/env python3
"""End-to-end current-owner status with explicit, independently trusted inputs."""
import copy
import importlib.util
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    target = ROOT / path
    if not target.exists():
        return None
    spec = importlib.util.spec_from_file_location(name, target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contract = load('status_contract', 'scripts/usage_telemetry_contract.py')
alerts = load('status_alerts', 'scripts/usage_telemetry_alerts.py')
snapshots = load('status_snapshots', 'tests/usage-current-run-snapshot-schema.py')
policies = load('status_policies', 'tests/usage-warning-policy-schema.py')
resolution = load('status_resolution_fixtures', 'tests/usage-status-fixtures.py')
NOW = '2029-01-02T00:00:00Z'


def inputs():
    if resolution is None:
        raise AssertionError('status fixtures are required')
    data, allowed = resolution.fixture()
    bundle = data['bundle']
    scope = data['scope']
    snapshot = snapshots.snapshot()
    snapshot.update(owner_scope=scope, mode='off', segments=[], warning_delivery=[],
                    bundles=[bundle], inventories=bundle['inventories'],
                    inventory_evidence=[item for item in bundle['evidence_objects']
                                        if item['kind'] == 'inventory_evidence'])
    receipt = {'schema_version': 1, 'kind': 'usage_accepted',
               'bundle_sha256': contract.content_id(bundle),
               'observation_ids': [contract.observation_id(item) for item in bundle['observations']],
               'scope': scope | {'attribution_quality': 'verified'},
               'duplicate': False, 'validator_version': '1'}
    snapshot['accepted_receipts'] = [receipt]
    contract.validate_current_run_snapshot(snapshot)
    allowed.append(('receipt', scope, receipt, bundle))
    allowed.append(('nonnegative_scope', scope, bundle['inventories'][0],
                    snapshot['inventory_evidence'][0]))
    ownership_evidence = []
    for observation in bundle['observations']:
        ownership = {'owner_scope': scope, 'observation_id': contract.observation_id(observation),
                     'basis': 'verified_import'}
        allowed.append(('ownership', scope, observation, ownership))
        ownership_evidence.append(ownership)
    extra = {key: copy.deepcopy(data[key]) for key in
             ('profile', 'contexts', 'snapshots', 'scenario', 'price_evidence')}
    extra['ownership_evidence'] = ownership_evidence
    return snapshot, extra, allowed


def policy():
    value = policies.policy()
    value.update(created_at='2028-01-01T00:00:00Z', expires_at='2030-01-01T00:00:00Z',
                 historical_cohort=None, token_threshold={'value': 1000, 'unit': 'tokens'},
                 money_threshold={'value': '0.002', 'unit': 'USD'}, minimum_completeness=None)
    contract.validate_warning_policy(value)
    return value


class StatusIntegrationTests(unittest.TestCase):
    def evaluate(self, snapshot, extra, allowed, pol=None):
        verifier = resolution.Verifier(allowed)
        with patch('builtins.open', side_effect=AssertionError('unexpected filesystem read')), \
             patch.object(Path, 'open', side_effect=AssertionError('unexpected history read')), \
             patch.object(socket, 'socket', side_effect=AssertionError('unexpected network access')):
            result = alerts.evaluate_status(snapshot, policy() if pol is None else pol,
                                            observed_at=NOW, analysis_inputs=extra,
                                            verifier=verifier)
        return result, verifier.calls

    def test_bounded_snapshot_accepts_explicit_pricing_inputs_without_reading(self):
        snapshot, extra, _ = inputs()
        snapshot['analysis_inputs'] = extra
        with patch('builtins.open', side_effect=AssertionError('unexpected history read')), \
             patch.object(socket, 'socket', side_effect=AssertionError('unexpected network access')):
            self.assertEqual(contract.validate_current_run_snapshot(snapshot), snapshot)
        too_small = copy.deepcopy(snapshot)
        too_small['bounds']['max_bytes'] = 10
        with self.assertRaises(ValueError):
            contract.validate_current_run_snapshot(too_small)

    def test_real_receipts_produce_verified_threshold_candidates_and_stable_retry(self):
        snapshot, extra, allowed = inputs()
        original = copy.deepcopy((snapshot, extra))
        first, calls = self.evaluate(snapshot, extra, allowed)
        second, _ = self.evaluate(snapshot, extra, allowed)
        self.assertEqual(first, second)
        self.assertEqual((snapshot, extra), original)
        self.assertTrue(any(call[0] == 'receipt' for call in calls))
        self.assertTrue(any(call[0] == 'measurement' for call in calls))
        self.assertTrue(any(call[0] == 'ownership' for call in calls))
        self.assertTrue(any(call[0] == 'price' for call in calls))
        self.assertEqual(first['measurements']['tokens']['value'], 2200)
        self.assertEqual(first['measurements']['tokens']['state'], 'final')
        self.assertEqual(first['measurements']['cost_usd']['value'], '0.00289')
        self.assertEqual(first['measurements']['cost_usd']['state'], 'proven_lower_bound')
        self.assertEqual({item['metric'] for item in first['candidates']}, {'tokens', 'cost_usd'})
        contract.validate_current_run_snapshot(first['proposed_snapshot'])

    def test_equality_does_not_cross_exact_money_boundary(self):
        snapshot, extra, allowed = inputs()
        selected = policy()
        selected['token_threshold'] = None
        selected['money_threshold']['value'] = '0.00289'
        result, _ = self.evaluate(snapshot, extra, allowed, selected)
        self.assertEqual(result['candidates'], [])

    def test_untrusted_receipt_or_measurements_cannot_trigger(self):
        snapshot, extra, allowed = inputs()
        for rejected in ('receipt', 'measurement', 'context', 'ownership'):
            with self.subTest(rejected=rejected):
                result, _ = self.evaluate(snapshot, extra, [item for item in allowed if item[0] != rejected])
                self.assertEqual(result['candidates'], [])
                self.assertNotEqual(result['measurements'].get('tokens', {}).get('state'), 'final')

    def test_missing_price_authority_or_inputs_is_unknown_not_zero(self):
        snapshot, extra, allowed = inputs()
        for altered, authority in ((extra, [item for item in allowed if item[0] != 'price']),
                                   ({**extra, 'snapshots': [], 'scenario': None, 'price_evidence': []}, allowed)):
            with self.subTest(pricing=altered['snapshots']):
                result, _ = self.evaluate(snapshot, altered, authority)
                self.assertFalse(any(item['metric'] == 'cost_usd' for item in result['candidates']))
                money = result['measurements'].get('cost_usd', {})
                self.assertIn(money.get('state', 'unknown'), ('unknown', 'unpriced'))
                self.assertIsNone(money.get('value'))

    def test_unproved_nonnegative_scope_cannot_establish_money_lower_bound(self):
        snapshot, extra, allowed = inputs()
        allowed = [entry for entry in allowed if entry[0] != 'nonnegative_scope']
        result, _ = self.evaluate(snapshot, extra, allowed)
        self.assertFalse(any(entry['metric'] == 'cost_usd' for entry in result['candidates']))
        self.assertNotEqual(result['measurements'].get('cost_usd', {}).get('state'),
                            'proven_lower_bound')

    def test_exact_token_equality_does_not_cross(self):
        snapshot, extra, allowed = inputs()
        selected = policy()
        selected['money_threshold'] = None
        selected['token_threshold']['value'] = 2200
        result, _ = self.evaluate(snapshot, extra, allowed, selected)
        self.assertEqual(result['candidates'], [])

    def test_pending_episode_survives_lost_evidence_without_clearing(self):
        snapshot, extra, allowed = inputs()
        first, _ = self.evaluate(snapshot, extra, allowed)
        prior = first['proposed_snapshot']
        result, _ = self.evaluate(prior, extra, [])
        self.assertEqual({item['warning_id'] for item in result['candidates']},
                         {item['warning_id'] for item in first['candidates']})
        self.assertTrue(all(item['crossing_state'] == 'crossed'
                            for item in result['proposed_snapshot']['warning_delivery']))

    def test_absent_scope_evidence_never_creates_request_or_span_warning(self):
        snapshot, extra, allowed = inputs()
        for kind in ('request', 'span'):
            selected = policy(); selected['scope'] = kind
            result, _ = self.evaluate(snapshot, extra, allowed, selected)
            self.assertEqual(result['candidates'], [])


if __name__ == '__main__':
    unittest.main()
