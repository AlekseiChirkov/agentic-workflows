#!/usr/bin/env python3
"""Current-owner time-only status with independently authenticated clocks."""
import copy
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture = load('status_fixture', 'tests/usage-status-integration.py')
contract = fixture.contract
NOW = '2029-01-02T00:00:00Z'


def time_only(seconds=7201, quality='measured', closed=True):
    snapshot = fixture.snapshots.snapshot()
    snapshot.update(mode='off', segments=[], accepted_receipts=[], bundles=[], inventories=[],
                    inventory_evidence=[], warning_delivery=[])
    owner = snapshot['owner_scope']
    candidate = {'id': 'sha256:' + 'd' * 64, 'seconds': seconds, 'closed': closed,
                 'clock_quality': quality, 'collection': 'off',
                 'group': {'stage': 'execution', 'duration_kind': 'work', 'clock_quality': quality,
                           'environment': 'local', 'profile': 'standard', 'contract': 'default',
                           'configuration': 'default'}}
    proof = {'owner_scope': owner, 'candidate_id': candidate['id'], 'clock_source': 'monotonic',
             'observed_at': NOW}
    snapshot['duration_inputs'] = [{'candidate': candidate, 'evidence': proof, 'history': None}]
    allowed = [('duration', owner, candidate, proof)]
    return snapshot, allowed


def evaluate(snapshot, allowed):
    verifier = fixture.resolution.Verifier(allowed)
    with patch('builtins.open', side_effect=AssertionError('unexpected history read')), \
         patch.object(Path, 'open', side_effect=AssertionError('unexpected history read')), \
         patch.object(socket, 'socket', side_effect=AssertionError('unexpected network access')):
        return fixture.alerts.evaluate_status(snapshot, None, observed_at=NOW, verifier=verifier)


class TimeOnlyStatusTests(unittest.TestCase):
    def test_default_duration_crossing_is_pure_and_stable_when_collection_is_off(self):
        snapshot, allowed = time_only()
        original = copy.deepcopy(snapshot)
        first = evaluate(snapshot, allowed)
        second = evaluate(snapshot, allowed)
        self.assertEqual(snapshot, original)
        self.assertEqual(first, second)
        self.assertEqual(first['measurements']['duration_ms'], {'state': 'final', 'value': 7201000, 'unit': 'ms'})
        self.assertEqual(len(first['candidates']), 1)
        self.assertEqual(first['candidates'][0]['metric'], 'duration_ms')
        self.assertEqual(first['candidates'][0]['delivery_state'], 'pending')
        self.assertEqual(first['candidates'][0]['scope'], snapshot['owner_scope'])
        contract.validate_current_run_snapshot(first['proposed_snapshot'])
        retry = evaluate(first['proposed_snapshot'], allowed)
        self.assertEqual(retry['candidates'][0]['warning_id'], first['candidates'][0]['warning_id'])

    def test_equal_boundary_unverified_open_and_unknown_clocks_do_not_warn(self):
        snapshot, allowed = time_only(7200)
        self.assertEqual(evaluate(snapshot, allowed)['candidates'], [])
        snapshot, allowed = time_only()
        self.assertEqual(evaluate(snapshot, [])['candidates'], [])
        snapshot, allowed = time_only(closed=False)
        self.assertEqual(evaluate(snapshot, allowed)['candidates'], [])
        snapshot, allowed = time_only(seconds=None, quality='unknown')
        result = evaluate(snapshot, allowed)
        self.assertEqual(result['candidates'], [])
        self.assertIn('timing_unavailable', result['diagnostics'])
        self.assertNotIn('duration_ms', result['measurements'])

    def test_time_only_cli_uses_explicit_owner_authority_without_history(self):
        snapshot, allowed = time_only()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'snapshot.json'
            authority = root / 'authority.json'
            output = root / 'output.json'
            source.write_text(json.dumps(snapshot), encoding='utf-8')
            authority.write_text(json.dumps({'schema_version': 1, 'kind': 'status_authority',
                'bindings': [{'kind': kind, 'scope': scope, 'subject': subject, 'evidence': evidence}
                             for kind, scope, subject, evidence in allowed]}), encoding='utf-8')
            authority.chmod(0o600)
            result = subprocess.run(['python3', str(ROOT / 'scripts/usage-telemetry.py'), 'status',
                    '--receipt-snapshot', str(source), '--authority', str(authority),
                    '--observed-at', NOW, '--output', str(output)],
                    cwd=root, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            status = json.loads(output.read_text())
            self.assertEqual([item['metric'] for item in status['candidates']], ['duration_ms'])
            self.assertEqual(status['measurements']['duration_ms']['value'], 7201000)
            self.assertNotIn(str(root), json.dumps(status))


if __name__ == '__main__':
    unittest.main()
