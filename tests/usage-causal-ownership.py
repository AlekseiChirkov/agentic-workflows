#!/usr/bin/env python3
"""Offline checks for explicitly evidenced ownership and immutable reports."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

contract = load('contract', 'scripts/usage_telemetry_contract.py')
envelope = load('envelope', 'tests/usage-observation-bundle-schema.py')
try:
    ownership = load('ownership', 'scripts/usage_telemetry_ownership.py')
except FileNotFoundError:
    ownership = None


def invoke(name, *args):
    return getattr(ownership, name, lambda *args: None)(*args)


def opaque(ch):
    return 'sha256:' + ch * 64


PARENT, LEAF_A, LEAF_B, FOREIGN = map(opaque, '1234')
OLD = '2026-01-02T00:00:00Z'
NEW = '2026-01-04T00:00:00Z'


def claim(response='response-a', kind='shared_pool', owner=PARENT,
          candidates=None, observed_at=OLD, cost='0.1', provider='provider-a',
          provider_scope=None):
    provider_scope = provider_scope or opaque('a')
    attribution = {'response_id': response, 'provider': provider, 'provider_scope': provider_scope,
                   'owner_kind': kind, 'owner_id': owner,
                   'candidates': [LEAF_A, LEAF_B] if candidates is None else candidates,
                   'basis': 'correlation'}
    return {'response_id': response, 'provider': provider, 'provider_scope': provider_scope,
            'observed_at': observed_at, 'cost_usd': cost,
            'attribution': attribution, 'attribution_evidence': contract.content_id(attribution)}


def report(contributors, scope=PARENT, cutoff=NEW, trusted=None, complete=True):
    if trusted is None:
        trusted = [item['attribution_evidence'] for item in contributors]
    return invoke('build_ownership_report', contributors, scope, cutoff, complete, trusted)


class OwnershipTests(unittest.TestCase):
    def test_measurement_evidence_requires_matching_and_authorized_source(self):
        observation, evidence = envelope.observation(), envelope.evidence()
        allowed = [{'profile_id': 'profile', 'source_hash': 'a' * 64,
                    'provider_scope': observation['provider_scope'],
                    'counter_scope': observation['counter_scope'],
                    'record_number': observation['record_number'],
                    'field': 'input_uncached',
                    'evidence': contract.content_id(evidence)}]
        check = lambda obs, ev, auth: invoke('measurement_is_verified', obs, 'input_uncached', ev, auth)
        self.assertIs(check(observation, [evidence], allowed), True)
        self.assertIs(check(observation, [], allowed), False)
        self.assertIs(check(observation, [evidence], []), False)
        for key, wrong in [('profile_id', 'other'), ('source_hash', 'b' * 64),
                           ('record_number', 2), ('field', 'output'), ('value', 1)]:
            altered = evidence | {key: wrong}
            modified = copy.deepcopy(observation)
            modified['measurements']['input_uncached']['evidence'] = contract.content_id(altered)
            with self.subTest(key=key):
                self.assertIs(check(modified, [altered], allowed), False)
        modified = copy.deepcopy(observation)
        modified['measurements']['input_uncached']['evidence'] = 'f' * 64
        self.assertIs(check(modified, [evidence], allowed), False)

    def test_authorized_measurement_scope_is_explicit_and_exact(self):
        observation, evidence = envelope.observation(), envelope.evidence()
        scope_attestation = {'profile_id': observation['profile_id'],
                             'source_hash': observation['source_hash'],
                             'provider_scope': observation['provider_scope'],
                             'counter_scope': observation['counter_scope'],
                             'record_number': observation['record_number'],
                             'field': 'input_uncached',
                             'evidence': contract.content_id(evidence)}
        check = lambda item, trust: invoke('measurement_is_verified', item, 'input_uncached',
                                           [evidence], trust)
        self.assertIs(check(observation, [scope_attestation]), True)
        for key, value in [('provider_scope', opaque('f')), ('counter_scope', 'request_delta')]:
            altered = copy.deepcopy(observation)
            altered[key] = value
            with self.subTest(key=key):
                self.assertIs(check(altered, [scope_attestation]), False)
        incomplete = {key: value for key, value in scope_attestation.items()
                      if key not in ('provider_scope', 'counter_scope')}
        self.assertIs(check(observation, [incomplete]), False)

    def test_scope_attestation_is_bound_to_record_and_measurement(self):
        observation, evidence = envelope.observation(), envelope.evidence()
        def attestation(item, field, obj):
            return {'profile_id': item['profile_id'], 'source_hash': item['source_hash'],
                    'provider_scope': item['provider_scope'], 'counter_scope': item['counter_scope'],
                    'record_number': item['record_number'], 'field': field,
                    'evidence': contract.content_id(obj)}
        authorized = attestation(observation, 'input_uncached', evidence)
        # Both records were independently admitted, but to different scopes.
        other = copy.deepcopy(observation)
        other['record_number'] = 2
        other['provider_scope'] = opaque('f')
        other_evidence = evidence | {'record_number': 2}
        other['measurements']['input_uncached']['evidence'] = contract.content_id(other_evidence)
        trusted = [authorized, attestation(other, 'input_uncached', other_evidence)]
        check = lambda item, field, objects: invoke('measurement_is_verified', item, field, objects, trusted)
        self.assertIs(check(observation, 'input_uncached', [evidence]), True)
        self.assertIs(check(other, 'input_uncached', [other_evidence]), True)
        switched = copy.deepcopy(observation)
        switched['provider_scope'] = other['provider_scope']
        self.assertIs(check(switched, 'input_uncached', [evidence]), False)
        switched = copy.deepcopy(other)
        switched['provider_scope'] = observation['provider_scope']
        self.assertIs(check(switched, 'input_uncached', [other_evidence]), False)
        changed_value = evidence | {'value': 1}
        altered = copy.deepcopy(observation)
        altered['measurements']['input_uncached']['value'] = 1
        altered['measurements']['input_uncached']['evidence'] = contract.content_id(changed_value)
        self.assertIs(check(altered, 'input_uncached', [changed_value]), False)
        changed_field = evidence | {'field': 'output'}
        altered = copy.deepcopy(observation)
        altered['measurements'] = {'output': {'measurement_state': 'final', 'value': 0,
                                             'reasons': [], 'evidence': contract.content_id(changed_field)}}
        self.assertIs(check(altered, 'output', [changed_field]), False)

    def test_response_identity_includes_provider_and_account_scope(self):
        first = claim()
        other_provider = claim(provider='provider-b', cost='0.2')
        other_account = claim(provider_scope=opaque('b'), cost='0.3')
        combined = report([first, copy.deepcopy(first), other_provider, other_account])
        self.assertEqual(combined['cost_usd'], '0.6')
        self.assertEqual(len(combined['contributors']), 3)
        self.assertEqual(combined, report([other_account, first, other_provider, first]))

    def test_shared_pool_is_counted_once_and_leaves_remain_incomplete(self):
        item = claim()
        parent = report([item])
        self.assertEqual(parent['cost_usd'], '0.1')
        self.assertEqual(parent['attribution'], 'complete')
        self.assertEqual(len(parent['contributors']), 1)
        for leaf in (LEAF_A, LEAF_B):
            child = report([item], leaf)
            self.assertEqual(child['attribution'], 'partial')
            self.assertNotIn('cost_usd', child)
            self.assertNotIn('0.05', json.dumps(child))

    def test_unknown_or_unauthorized_ownership_is_not_promoted(self):
        item = claim()
        for altered, trusted in [(item, []), (item | {'attribution_evidence': 'f' * 64}, [item['attribution_evidence']]),
                                 (item | {'attribution': item['attribution'] | {'owner_id': FOREIGN}}, [item['attribution_evidence']])]:
            result = report([altered], trusted=trusted)
            self.assertEqual(result['attribution'], 'partial')
            self.assertNotIn('cost_usd', result)

    def test_external_unattributed_pool_is_not_included_in_complete_parent(self):
        shared = claim()
        outside = claim('foreign', 'unattributed', FOREIGN, candidates=[], cost='0.2')
        result = report([shared, outside])
        self.assertEqual(result['cost_usd'], '0.1')
        self.assertEqual(result['attribution'], 'complete')
        self.assertNotIn('foreign', json.dumps(result['contributors']))

    def test_late_evidence_only_affects_new_report_and_order_is_deterministic(self):
        first = claim()
        late = claim('response-b', 'task', PARENT, candidates=[],
                     observed_at='2026-01-03T00:00:00Z', cost='0.2')
        original_input = copy.deepcopy([first, late])
        old = report([first, late], cutoff=OLD)
        frozen = json.dumps(old, sort_keys=True)
        new = report([first, late])
        self.assertEqual(old['cost_usd'], '0.1')
        self.assertEqual(new['cost_usd'], '0.3')
        self.assertEqual(frozen, json.dumps(old, sort_keys=True))
        self.assertEqual([first, late], original_input)
        self.assertEqual(new, report([late, first]))

    def test_no_history_read_or_private_payload_leak(self):
        sentinel = 'PRIVATE_PAYLOAD_SENTINEL'
        item = claim()
        with patch('builtins.open', side_effect=AssertionError('unexpected read')):
            result = report([item])
        self.assertEqual(result['cost_usd'], '0.1')
        bad = copy.deepcopy(item)
        bad['attribution']['raw_content'] = sentinel
        try:
            value = report([bad])
        except ValueError as error:
            self.assertNotIn(sentinel, str(error))
        else:
            self.assertNotIn(sentinel, json.dumps(value))
            self.assertNotIn('cost_usd', value)


if __name__ == '__main__':
    unittest.main()
