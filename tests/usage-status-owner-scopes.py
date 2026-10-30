#!/usr/bin/env python3
"""Request and span status from independently bound owner evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('status_fixture', ROOT / 'tests/usage-status-integration.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class ScopedStatusTests(unittest.TestCase):
    def test_verified_request_and_span_use_only_their_own_resolved_response(self):
        for kind in ('request', 'span'):
            snapshot, extra, allowed = fixture.inputs()
            owner = snapshot['owner_scope']
            target = {'owner_kind': kind, 'owner_id': 'sha256:' + 'f' * 64}
            observation = snapshot['bundles'][0]['observations'][0]
            proof = extra['ownership_evidence'][0]
            old = copy.deepcopy(proof)
            allowed.remove(('ownership', owner, observation, old))
            proof['target_scope'] = target
            if kind == 'span':
                proof['completion'] = {'scope': target, 'state': 'complete', 'observed_at': fixture.NOW}
                allowed.append(('scope_completion', owner, target, proof['completion']))
            allowed.append(('ownership', owner, observation, proof))
            selected = fixture.policy()
            selected['scope'] = kind
            selected['money_threshold'] = None
            result = fixture.alerts.evaluate_status(snapshot, selected, observed_at=fixture.NOW,
                        analysis_inputs=extra, verifier=fixture.resolution.Verifier(allowed))
            with self.subTest(kind=kind):
                self.assertEqual(len(result['candidates']), 1)
                self.assertEqual(result['candidates'][0]['scope'], target)
                self.assertEqual(result['candidates'][0]['owner_scope'], owner)
                item = next(item for item in result['scoped_measurements'] if item['scope'] == target)
                self.assertEqual(item['metrics']['tokens']['value'], 1100)
                fixture.contract.validate_current_run_snapshot(result['proposed_snapshot'])
            denied = [entry for entry in allowed if not (entry[0] == 'ownership' and entry[3] == proof)]
            result = fixture.alerts.evaluate_status(snapshot, selected, observed_at=fixture.NOW,
                        analysis_inputs=extra, verifier=fixture.resolution.Verifier(denied))
            self.assertEqual(result['candidates'], [])


if __name__ == '__main__':
    unittest.main()
