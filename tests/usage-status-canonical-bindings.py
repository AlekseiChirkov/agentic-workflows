#!/usr/bin/env python3
"""Canonical status inputs and authority bindings survive declared set permutations."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture = load('status_fixture', 'tests/usage-status-integration.py')
cli = load('status_cli', 'scripts/usage-telemetry.py')
contract = fixture.contract


class CanonicalStatusBindingsTests(unittest.TestCase):
    def test_snapshot_analysis_sets_preserve_identity_when_reordered(self):
        snapshot, extra, _ = fixture.inputs()
        snapshot['analysis_inputs'] = extra
        contract.validate_current_run_snapshot(snapshot)
        other = copy.deepcopy(snapshot)
        inputs = other['analysis_inputs']
        for key in ('contexts', 'snapshots', 'price_evidence', 'ownership_evidence'):
            inputs[key].reverse()
        inputs['profile']['counter_fields'].reverse()
        inputs['contexts'][0]['evidence_objects'].reverse()
        inputs['snapshots'][0]['rates'].reverse()
        contract.validate_current_run_snapshot(other)
        self.assertEqual(contract.canonical_bytes(snapshot), contract.canonical_bytes(other))
        self.assertEqual(contract.content_id(snapshot), contract.content_id(other))

    def test_authority_recognizes_nested_observation_set_permutations(self):
        snapshot, _, _ = fixture.inputs()
        observation = copy.deepcopy(snapshot['bundles'][0]['observations'][0])
        observation['attribution']['candidates'] = ['sha256:' + '1' * 64, 'sha256:' + '2' * 64]
        changed = copy.deepcopy(observation)
        changed['attribution']['candidates'].reverse()
        self.assertEqual(contract.observation_id(observation), contract.observation_id(changed))
        owner = snapshot['owner_scope']
        evidence = {'schema_version': 1, 'kind': 'measurement_evidence', 'profile_id': observation['profile_id'],
                    'source_hash': observation['source_hash'], 'record_number': observation['record_number'],
                    'field': 'input_uncached', 'value': 600}
        authority = {'schema_version': 1, 'kind': 'status_authority', 'bindings': [{
            'kind': 'measurement', 'scope': owner,
            'subject': {'observation': observation, 'field': 'input_uncached'}, 'evidence': evidence}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'authority.json'
            path.write_text(json.dumps(authority), encoding='utf-8')
            path.chmod(0o600)
            verify = cli._status_authority(str(path))
            self.assertTrue(verify('measurement', owner,
                                  {'observation': changed, 'field': 'input_uncached'}, evidence))


if __name__ == '__main__':
    unittest.main()
