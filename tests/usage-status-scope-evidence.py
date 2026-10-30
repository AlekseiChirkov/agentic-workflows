#!/usr/bin/env python3
"""Scoped money and duration thresholds require independently verified scope facts."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('status_fixture', ROOT / 'tests/usage-status-integration.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def scoped(kind):
    snapshot, extra, allowed = fixture.inputs()
    owner = snapshot['owner_scope']
    target = {'owner_kind': kind, 'owner_id': 'sha256:' + 'f' * 64}
    observation = snapshot['bundles'][0]['observations'][0]
    proof = extra['ownership_evidence'][0]
    allowed.remove(('ownership', owner, observation, copy.deepcopy(proof)))
    proof['target_scope'] = target
    proof['tool_coverage'] = {'scope': target, 'state': 'empty', 'observed_at': fixture.NOW}
    allowed.append(('scope_tools_empty', owner, target, proof['tool_coverage']))
    if kind == 'span':
        proof['completion'] = {'scope': target, 'state': 'complete', 'observed_at': fixture.NOW}
        allowed.append(('scope_completion', owner, target, proof['completion']))
    allowed.append(('ownership', owner, observation, proof))
    policy = fixture.policy()
    policy.update(scope=kind, token_threshold=None, minimum_completeness=None,
                  money_threshold={'value': '0.002', 'unit': 'USD'})
    return snapshot, extra, allowed, policy, target


def evaluate(snapshot, extra, allowed, policy):
    return fixture.alerts.evaluate_status(snapshot, policy, observed_at=fixture.NOW,
                  analysis_inputs=extra, verifier=fixture.resolution.Verifier(allowed))


class ScopedEvidenceTests(unittest.TestCase):
    def test_scope_money_requires_independent_tool_coverage_and_owner(self):
        for kind in ('request', 'span'):
            snapshot, extra, allowed, policy, target = scoped(kind)
            with self.subTest(kind=kind):
                result = evaluate(snapshot, extra, allowed, policy)
                self.assertEqual(len(result['candidates']), 1)
                self.assertEqual(result['candidates'][0]['scope'], target)
                self.assertEqual(result['candidates'][0]['metric'], 'cost_usd')
                metric = next(item['metrics']['cost_usd'] for item in result['scoped_measurements']
                              if item['scope'] == target)
                self.assertEqual(metric['value'], '0.00289')
                for rejected in ('scope_tools_empty', 'ownership', 'price'):
                    denied = [entry for entry in allowed if entry[0] != rejected]
                    self.assertEqual(evaluate(snapshot, extra, denied, policy)['candidates'], [])
                policy['money_threshold']['value'] = '0.00289'
                self.assertEqual(evaluate(snapshot, extra, allowed, policy)['candidates'], [])

    def test_repricing_does_not_create_factual_scoped_spend_warning(self):
        for kind in ('request', 'span'):
            with self.subTest(kind=kind):
                snapshot, extra, allowed, policy, target = scoped(kind)
                policy['money_threshold']['value'] = '0.004'
                self.assertEqual(evaluate(snapshot, extra, allowed, policy)['candidates'], [])
                extra['scenario']['basis'] = 'reprice'
                price = extra['snapshots'][0]
                for rate in price['rates']:
                    rate['usd'] = str(float(rate['usd']) * 2).rstrip('0').rstrip('.')
                price_id = fixture.contract.price_snapshot_id(price)
                extra['scenario']['snapshot_ids'] = [price_id]
                for proof in extra['price_evidence']:
                    if proof['kind'] == 'price_snapshot_evidence':
                        proof['snapshot_id'] = price_id
                allowed = [item for item in allowed if item[0] != 'price']
                allowed.extend(('price', snapshot['owner_scope'], price, proof)
                               for proof in extra['price_evidence'])
                result = evaluate(snapshot, extra, allowed, policy)
                self.assertEqual(result['candidates'], [])
                metrics = next(item['metrics'] for item in result['scoped_measurements'] if item['scope'] == target)
                self.assertNotIn('cost_usd', metrics)
                snapshot, extra, allowed, policy, target = scoped(kind)
                policy['money_threshold']['value'] = '0.002'
                self.assertEqual(evaluate(snapshot, extra, allowed, policy)['candidates'][0]['metric'], 'cost_usd')

    def test_span_needs_independently_verified_completion_for_token_warning(self):
        snapshot, extra, allowed, policy, _ = scoped('span')
        policy['money_threshold'] = None
        policy['token_threshold'] = {'value': 1000, 'unit': 'tokens'}
        self.assertEqual(len(evaluate(snapshot, extra, allowed, policy)['candidates']), 1)
        for denied in ([item for item in allowed if item[0] != 'scope_completion'],):
            self.assertEqual(evaluate(snapshot, extra, denied, policy)['candidates'], [])
        absent = copy.deepcopy(extra)
        del absent['ownership_evidence'][0]['completion']
        self.assertEqual(evaluate(snapshot, absent, allowed, policy)['candidates'], [])


if __name__ == '__main__':
    unittest.main()
