#!/usr/bin/env python3
"""Offline status episode checks against independently evaluated measurements."""
import copy
import importlib.util
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    path = ROOT / path
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contract = load('status_contract', 'scripts/usage_telemetry_contract.py')
fixtures = load('status_fixtures', 'tests/usage-current-run-snapshot-schema.py')
policies = load('status_policies', 'tests/usage-warning-policy-schema.py')
alerts = load('status_alerts', 'scripts/usage_telemetry_alerts.py')
NOW = '2026-01-15T00:00:00Z'


def snapshot():
    value = fixtures.snapshot()
    value.update(mode='off', segments=[], accepted_receipts=[], bundles=[],
                 inventories=[], inventory_evidence=[], warning_delivery=[])
    contract.validate_current_run_snapshot(value)
    return value


def policy():
    value = policies.policy()
    value['historical_cohort'] = None
    contract.validate_warning_policy(value)
    return value


def evaluated(value, state='final', metric='tokens'):
    # This stub represents the trusted, independently validated analyzer output;
    # arbitrary fields added to a snapshot must never become this result.
    units = {'tokens': 'tokens', 'cost_usd': 'USD', 'completeness': 'fraction'}
    return {'scope': snapshot()['owner_scope'], 'metrics': {
        metric: {'state': state, 'value': value, 'unit': units[metric]}}}


class StatusEpisodeTests(unittest.TestCase):
    def status(self, snap, pol, analysis, now=NOW):
        self.assertIsNotNone(alerts, 'status module is required')
        with patch.object(alerts, '_evaluate_snapshot', return_value=analysis), \
             patch('builtins.open', side_effect=AssertionError('unexpected filesystem read')), \
             patch.object(Path, 'open', side_effect=AssertionError('unexpected filesystem read')), \
             patch.object(socket, 'socket', side_effect=AssertionError('unexpected network access')):
            return alerts.evaluate_status(snap, pol, observed_at=now)

    def test_repeated_status_is_pure_and_has_stable_candidate(self):
        snap, pol = snapshot(), policy()
        original_snap, original_pol = copy.deepcopy(snap), copy.deepcopy(pol)
        first = self.status(snap, pol, evaluated(1001))
        second = self.status(snap, pol, evaluated(1001))
        self.assertEqual(first, second)
        self.assertEqual(snap, original_snap)
        self.assertEqual(pol, original_pol)
        self.assertEqual(len(first['candidates']), 1)
        warning = first['candidates'][0]
        self.assertEqual(warning['metric'], 'tokens')
        self.assertEqual(warning['episode'], 1)
        self.assertEqual(warning['crossing_state'], 'crossed')
        self.assertEqual(warning['delivery_state'], 'pending')
        contract.validate_current_run_snapshot(first['proposed_snapshot'])
        self.assertEqual(first['proposed_snapshot']['warning_delivery'], [warning])

    def test_strict_boundary_and_lower_bound(self):
        self.assertEqual(self.status(snapshot(), policy(), evaluated(1000))['candidates'], [])
        lower = self.status(snapshot(), policy(), evaluated(1001, 'proven_lower_bound'))
        self.assertEqual(len(lower['candidates']), 1)
        self.assertEqual(lower['candidates'][0]['metric'], 'tokens')
        self.assertEqual(self.status(snapshot(), policy(), evaluated('1.25', metric='cost_usd'))['candidates'], [])
        self.assertEqual(len(self.status(snapshot(), policy(), evaluated('1.25000000000000000001', metric='cost_usd'))['candidates']), 1)

    def test_expiry_scope_and_invalid_completeness(self):
        self.assertEqual(self.status(snapshot(), policy(), evaluated(9999), '2026-02-01T00:00:00Z')['candidates'], [])
        incompatible = policy(); incompatible['scope'] = 'request'
        self.assertEqual(self.status(snapshot(), incompatible, evaluated(9999))['candidates'], [])
        bad = policy(); bad['minimum_completeness']['value'] = '1.01'
        with self.assertRaises(ValueError):
            self.status(snapshot(), bad, evaluated(9999))
        self.assertEqual(self.status(snapshot(), None, evaluated(9999))['candidates'], [])

    def test_unknown_does_not_reset_but_observed_below_does(self):
        pol = policy()
        crossing = self.status(snapshot(), pol, evaluated(1001))
        ongoing = crossing['proposed_snapshot']
        unknown = self.status(ongoing, pol, evaluated(None, 'unknown'))
        self.assertEqual(unknown['proposed_snapshot']['warning_delivery'][0]['crossing_state'], 'crossed')
        self.assertEqual(unknown['proposed_snapshot']['warning_delivery'][0]['warning_id'], crossing['candidates'][0]['warning_id'])
        cleared = self.status(unknown['proposed_snapshot'], pol, evaluated(1000))
        self.assertEqual(cleared['proposed_snapshot']['warning_delivery'][0]['crossing_state'], 'cleared')
        again = self.status(cleared['proposed_snapshot'], pol, evaluated(1001))
        self.assertEqual(again['candidates'][0]['episode'], 2)
        self.assertNotEqual(again['candidates'][0]['warning_id'], crossing['candidates'][0]['warning_id'])
        self.assertEqual(len(again['proposed_snapshot']['warning_delivery']), 2)

    def test_late_correction_does_not_erase_delivered_warning(self):
        first = self.status(snapshot(), policy(), evaluated(1001))
        delivered = first['proposed_snapshot']
        delivered['warning_delivery'][0]['delivery_state'] = 'delivered'
        corrected = self.status(delivered, policy(), evaluated(999))
        self.assertEqual(corrected['candidates'], [])
        previous = corrected['proposed_snapshot']['warning_delivery'][0]
        self.assertEqual(previous['delivery_state'], 'delivered')
        self.assertEqual(previous['crossing_state'], 'cleared')
        self.assertEqual(previous['warning_id'], first['candidates'][0]['warning_id'])

    def test_unknown_and_conflicting_values_never_guess_money(self):
        for state in ('unknown', 'conflict', 'unpriced'):
            with self.subTest(state=state):
                result = self.status(snapshot(), policy(), evaluated(None, state, 'cost_usd'))
                self.assertEqual(result['candidates'], [])
        wrong_owner = evaluated(9000)
        wrong_owner['scope'] = {'owner_kind': 'run', 'owner_id': 'sha256:' + 'f' * 64}
        self.assertEqual(self.status(snapshot(), policy(), wrong_owner)['candidates'], [])

    def test_completeness_strict_boundary_and_unknown_denominator(self):
        self.assertEqual(self.status(snapshot(), policy(), evaluated('0.80', metric='completeness'))['candidates'], [])
        self.assertEqual(len(self.status(snapshot(), policy(), evaluated('0.79', metric='completeness'))['candidates']), 1)
        unknown = self.status(snapshot(), policy(), evaluated(None, 'unknown', 'completeness'))
        self.assertEqual(unknown['candidates'], [])
        self.assertNotIn('%', json.dumps(unknown))

    def test_invalid_snapshot_fields_cannot_inject_proof_or_leak(self):
        private = 'PRIVATE_CONTENT_SENTINEL'
        bad = snapshot(); bad['raw_content'] = private
        with self.assertRaises(ValueError) as exc:
            self.status(bad, policy(), evaluated(9999))
        self.assertNotIn(private, str(exc.exception))


    def test_missing_and_malformed_metrics_keep_pending_episode(self):
        original = self.status(snapshot(), policy(), evaluated(1001))
        prior = original['proposed_snapshot']
        warning_id = original['candidates'][0]['warning_id']
        for metrics in ({}, {'tokens': {}}, {'tokens': {'state': 'final', 'value': None, 'unit': 'tokens'}}):
            analysis = {'scope': prior['owner_scope'], 'metrics': metrics}
            with self.subTest(metrics=metrics):
                result = self.status(prior, policy(), analysis)
                self.assertEqual(result['candidates'][0]['warning_id'], warning_id)
                self.assertEqual(result['proposed_snapshot']['warning_delivery'][0]['crossing_state'], 'crossed')

    def test_request_and_span_require_trusted_membership_and_preserve_owner(self):
        for kind in ('request', 'span'):
            with self.subTest(kind=kind):
                pol = policy(); pol['scope'] = kind
                owner = snapshot()['owner_scope']
                target = {'owner_kind': kind, 'owner_id': 'sha256:' + 'f' * 64}
                scoped = {'scope': target, 'owner_scope': owner, 'membership': 'verified',
                          'metrics': {'tokens': {'state': 'final', 'value': 1001, 'unit': 'tokens'}}}
                analysis = {'scope': owner, 'metrics': {}, 'scoped_metrics': [scoped]}
                result = self.status(snapshot(), pol, analysis)
                self.assertEqual(len(result['candidates']), 1)
                self.assertEqual(result['candidates'][0]['scope'], target)
                self.assertEqual(result['candidates'][0]['owner_scope'], owner)
                contract.validate_current_run_snapshot(result['proposed_snapshot'])
                for membership in ('unknown', 'conflict'):
                    invalid = copy.deepcopy(analysis)
                    invalid['scoped_metrics'][0]['membership'] = membership
                    self.assertEqual(self.status(snapshot(), pol, invalid)['candidates'], [])
                foreign = copy.deepcopy(analysis)
                foreign['scoped_metrics'][0]['owner_scope']['owner_id'] = 'sha256:' + '1' * 64
                self.assertEqual(self.status(snapshot(), pol, foreign)['candidates'], [])

    def test_unknown_completeness_has_own_diagnostic_and_no_invented_percentage(self):
        observed = self.status(snapshot(), policy(), evaluated('0.79', metric='completeness'))
        self.assertEqual(len(observed['candidates']), 1)
        unknown = self.status(snapshot(), policy(), evaluated(None, 'unknown', 'completeness'))
        self.assertIn('coverage_unknown', unknown['diagnostics'])
        self.assertNotIn('%', json.dumps(unknown))
        self.assertEqual(unknown['candidates'], [])

    def test_status_returns_verified_current_measurements_and_completeness(self):
        analysis = evaluated(1001)
        analysis['metrics']['completeness'] = {'state': 'final', 'value': '0.90', 'unit': 'fraction'}
        result = self.status(snapshot(), policy(), analysis)
        self.assertEqual(result['measurements']['tokens'], analysis['metrics']['tokens'])
        self.assertEqual(result['measurements']['completeness'], analysis['metrics']['completeness'])
        self.assertEqual(len(result['candidates']), 1)
        foreign = copy.deepcopy(analysis); foreign['scope']['owner_id'] = 'sha256:' + 'f' * 64
        rejected = self.status(snapshot(), policy(), foreign)
        self.assertNotIn('tokens', rejected['measurements'])

    def test_output_capacity_exhaustion_preserves_old_episode_without_candidate(self):
        old = self.status(snapshot(), policy(), evaluated(1001))['proposed_snapshot']
        old['warning_delivery'][0]['crossing_state'] = 'cleared'
        old['warning_delivery'][0]['delivery_state'] = 'delivered'
        old['bounds']['max_entries'] = 1
        contract.validate_current_run_snapshot(old)
        baseline = copy.deepcopy(old)
        result = self.status(old, policy(), evaluated(1001))
        self.assertEqual(result['proposed_snapshot']['warning_delivery'], baseline['warning_delivery'])
        self.assertEqual(old, baseline)
        self.assertEqual(result['candidates'], [])
        self.assertIn('input_limit_exceeded', result['diagnostics'])
        contract.validate_current_run_snapshot(result['proposed_snapshot'])

    def test_output_byte_exhaustion_does_not_raise_or_drop_prior(self):
        old = self.status(snapshot(), policy(), evaluated(1001))['proposed_snapshot']
        old['warning_delivery'][0]['crossing_state'] = 'cleared'
        old['warning_delivery'][0]['delivery_state'] = 'delivered'
        old['bounds']['max_bytes'] = len(contract.canonical_bytes(old)) + 5
        contract.validate_current_run_snapshot(old)
        baseline = copy.deepcopy(old)
        result = self.status(old, policy(), evaluated(1001))
        self.assertEqual(result['proposed_snapshot']['warning_delivery'], baseline['warning_delivery'])
        self.assertEqual(result['candidates'], [])
        self.assertIn('input_limit_exceeded', result['diagnostics'])
        contract.validate_current_run_snapshot(result['proposed_snapshot'])



    def test_prior_scoped_pending_survives_missing_new_measurements(self):
        for kind in ('request', 'span'):
            with self.subTest(kind=kind):
                pol = policy(); pol['scope'] = kind
                owner = snapshot()['owner_scope']
                target = {'owner_kind': kind, 'owner_id': 'sha256:' + 'f' * 64}
                item = {'scope': target, 'owner_scope': owner, 'membership': 'verified',
                        'metrics': {'tokens': {'state': 'final', 'value': 1001, 'unit': 'tokens'}}}
                analysis = {'scope': owner, 'metrics': {}, 'scoped_metrics': [item]}
                first = self.status(snapshot(), pol, analysis)
                self.assertEqual(len(first['candidates']), 1)
                pending = first['proposed_snapshot']
                new = self.status(pending, pol, {'scope': owner, 'metrics': {}, 'scoped_metrics': []})
                self.assertEqual(new['candidates'][0]['warning_id'], first['candidates'][0]['warning_id'])
                self.assertEqual(new['proposed_snapshot']['warning_delivery'][0]['crossing_state'], 'crossed')
                self.assertNotIn('policy_unavailable', new['diagnostics'])
                self.assertIn('measurement_unavailable', new['diagnostics'])



    def test_pending_survives_unavailable_or_foreign_analysis_without_accepting_values(self):
        first = self.status(snapshot(), policy(), evaluated(1001))
        self.assertEqual(len(first['candidates']), 1)
        prior = first['proposed_snapshot']
        foreign = evaluated(9999)
        foreign['scope']['owner_id'] = 'sha256:' + 'f' * 64
        for analysis in (None, foreign):
            with self.subTest(analysis=analysis):
                result = self.status(prior, policy(), analysis)
                self.assertEqual(result['candidates'][0]['warning_id'], first['candidates'][0]['warning_id'])
                self.assertEqual(result['proposed_snapshot']['warning_delivery'][0]['crossing_state'], 'crossed')
                self.assertNotIn('tokens', result['measurements'])
                self.assertIn('measurement_unavailable', result['diagnostics'])


if __name__ == '__main__':
    unittest.main()
