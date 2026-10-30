#!/usr/bin/env python3
"""Closed, bounded analysis inputs and independent authority for owner status."""
import copy
import importlib.util
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture = load('status_integration', 'tests/usage-status-integration.py')
contract = fixture.contract
alerts = fixture.alerts


def snapshot_with_inputs():
    snapshot, extra, allowed = fixture.inputs()
    snapshot['analysis_inputs'] = extra
    return snapshot, extra, allowed


class StatusInputSchemaTests(unittest.TestCase):
    def test_valid_self_contained_inputs_are_offline_and_byte_bounded(self):
        snapshot, _, _ = snapshot_with_inputs()
        with patch('builtins.open', side_effect=AssertionError('unexpected filesystem read')), \
             patch.object(socket, 'socket', side_effect=AssertionError('unexpected network access')):
            self.assertEqual(contract.validate_current_run_snapshot(snapshot), snapshot)
        too_small = copy.deepcopy(snapshot)
        too_small['bounds']['max_bytes'] = 10
        with self.assertRaises(ValueError):
            contract.validate_current_run_snapshot(too_small)

    def test_closed_inputs_reject_unknown_and_missing_fields_without_disclosing_payload(self):
        snapshot, _, _ = snapshot_with_inputs()
        secret = 'PRIVATE_CONTENT_SENTINEL'
        for key in snapshot['analysis_inputs']:
            invalid = copy.deepcopy(snapshot)
            del invalid['analysis_inputs'][key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                contract.validate_current_run_snapshot(invalid)
        for change in ({'raw_content': secret}, {'local_path': '/private/' + secret}):
            invalid = copy.deepcopy(snapshot)
            invalid['analysis_inputs'].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError) as error:
                contract.validate_current_run_snapshot(invalid)
            self.assertNotIn(secret, str(error.exception))

    def test_nested_entries_count_toward_explicit_snapshot_limit(self):
        snapshot, _, _ = snapshot_with_inputs()
        contract.validate_current_run_snapshot(snapshot)
        limited = copy.deepcopy(snapshot)
        top_level = sum(len(limited[name]) for name in ('segments', 'accepted_receipts', 'bundles',
                         'inventories', 'inventory_evidence', 'warning_delivery'))
        limited['bounds']['max_entries'] = top_level
        with self.assertRaises(ValueError):
            contract.validate_current_run_snapshot(limited)

    def test_nested_lists_have_independent_hard_limits_and_no_duplicate_bindings(self):
        snapshot, _, _ = snapshot_with_inputs()
        contract.validate_current_run_snapshot(snapshot)
        for field in ('contexts', 'snapshots', 'price_evidence', 'ownership_evidence'):
            with self.subTest(field=field):
                invalid = copy.deepcopy(snapshot)
                invalid['analysis_inputs'][field] = invalid['analysis_inputs'][field] * 10001
                with self.assertRaises(ValueError):
                    contract.validate_current_run_snapshot(invalid)
                invalid = copy.deepcopy(snapshot)
                invalid['analysis_inputs'][field].append(copy.deepcopy(invalid['analysis_inputs'][field][0]))
                with self.assertRaises(ValueError):
                    contract.validate_current_run_snapshot(invalid)

    def test_context_and_ownership_must_bind_selected_observation(self):
        snapshot, _, _ = snapshot_with_inputs()
        contract.validate_current_run_snapshot(snapshot)
        for field in ('contexts', 'ownership_evidence'):
            invalid = copy.deepcopy(snapshot)
            invalid['analysis_inputs'][field][0]['observation_id'] = 'f' * 64
            with self.subTest(field=field), self.assertRaises(ValueError):
                contract.validate_current_run_snapshot(invalid)
        invalid = copy.deepcopy(snapshot)
        invalid['analysis_inputs']['ownership_evidence'][0]['owner_scope']['owner_id'] = 'sha256:' + 'f' * 64
        with self.assertRaises(ValueError):
            contract.validate_current_run_snapshot(invalid)

    def test_duplicate_argument_must_match_snapshot_or_be_rejected(self):
        snapshot, extra, allowed = snapshot_with_inputs()
        verifier = fixture.resolution.Verifier(allowed)
        expected = alerts.evaluate_status(snapshot, fixture.policy(), observed_at=fixture.NOW,
                                          analysis_inputs=extra, verifier=verifier)
        self.assertIsInstance(expected, dict)
        altered = copy.deepcopy(extra)
        altered['contexts'][0]['record_number'] += 1
        with self.assertRaises(ValueError):
            alerts.evaluate_status(snapshot, fixture.policy(), observed_at=fixture.NOW,
                                   analysis_inputs=altered, verifier=verifier)

    def test_missing_or_untrusted_context_never_produces_owned_values(self):
        snapshot, extra, allowed = snapshot_with_inputs()
        for altered, permitted in (({**extra, 'contexts': []}, allowed),
                                   (extra, [entry for entry in allowed if entry[0] != 'context'])):
            candidate = copy.deepcopy(snapshot)
            candidate['analysis_inputs'] = altered
            result = alerts.evaluate_status(candidate, fixture.policy(), observed_at=fixture.NOW,
                                            verifier=fixture.resolution.Verifier(permitted))
            self.assertEqual(result['candidates'], [])
            self.assertNotEqual(result['measurements'].get('tokens', {}).get('state'), 'final')


if __name__ == '__main__':
    unittest.main()
