#!/usr/bin/env python3
"""Explicit local status command and separate operator authority."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('status_fixture', ROOT / 'tests/usage-status-integration.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class StatusCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        snapshot, extra, allowed = fixture.inputs()
        snapshot['analysis_inputs'] = extra
        self.snapshot = self.write('snapshot.json', snapshot)
        self.policy = self.write('policy.json', fixture.policy())
        self.authority = self.write('authority.json', {
            'schema_version': 1, 'kind': 'status_authority',
            'bindings': [{'kind': kind, 'scope': scope, 'subject': subject, 'evidence': evidence}
                         for kind, scope, subject, evidence in allowed]})
        self.output = self.root / 'output.json'

    def write(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding='utf-8')
        path.chmod(0o600)
        return path

    def run_status(self, authority=True):
        args = ['python3', str(ROOT / 'scripts/usage-telemetry.py'), 'status',
                '--receipt-snapshot', str(self.snapshot), '--policy', str(self.policy),
                '--observed-at', fixture.NOW, '--output', str(self.output)]
        if authority:
            args.extend(['--authority', str(self.authority)])
        return subprocess.run(args, cwd=self.root, capture_output=True, text=True,
                              env={**os.environ, 'ORCHESTRAIL_USAGE_MODE': 'off'}, timeout=20)

    def test_explicit_inputs_and_separate_authority_produce_stable_candidates_offline(self):
        initial = self.snapshot.read_bytes()
        first = self.run_status()
        self.assertEqual(first.returncode, 0, first.stderr)
        one = json.loads(self.output.read_text())
        self.assertEqual({entry['metric'] for entry in one['candidates']}, {'tokens', 'cost_usd'})
        self.assertEqual(self.snapshot.read_bytes(), initial)
        self.output.unlink()
        again = self.run_status()
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(json.loads(self.output.read_text()), one)
        self.assertNotIn(str(self.root), json.dumps(one))

    def test_absent_authority_cannot_promote_snapshot_claims_to_proof(self):
        result = self.run_status(authority=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(self.output.read_text())
        self.assertEqual(output['candidates'], [])
        self.assertNotEqual(output['measurements'].get('tokens', {}).get('state'), 'final')

    def test_authority_requires_private_permissions(self):
        self.authority.chmod(0o644)
        result = self.run_status()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertNotIn(str(self.root), result.stderr)


if __name__ == '__main__':
    unittest.main()
