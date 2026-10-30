#!/usr/bin/env python3
"""Offline response identity and overlap behavior."""
import importlib.util
import itertools
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'usage_telemetry_identity.py'
if MODULE.exists():
    spec = importlib.util.spec_from_file_location('usage_telemetry_identity', MODULE)
    identity = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(identity)
else:
    identity = None


def opaque(char):
    return 'sha256:' + char * 64


def observation(char, response=None, call=None, session='e', provider='openai', account='a'):
    return {'observation_id': opaque(char), 'provider': provider,
            'provider_scope': opaque(account), 'response_id': response,
            'call_id': call, 'session_id': opaque(session)}


def link(call, response, proof='f'):
    return {'provider': 'openai', 'provider_scope': opaque('a'), 'call_id': call,
            'response_id': response, 'evidence_id': opaque(proof),
            'one_to_one_verified': True}


class ResponseIdentityTests(unittest.TestCase):
    def resolve(self, observations, links=(), **kwargs):
        self.assertIsNotNone(identity, 'response identity resolver is required')
        return identity.resolve_response_identities(observations, list(links), **kwargs)

    def test_branched_copies_are_one_response(self):
        a = observation('1', opaque('b'), session='c')
        b = observation('2', opaque('b'), session='d')
        result = self.resolve([a, b])
        self.assertEqual(len(result['responses']), 1)
        group = result['responses'][0]
        self.assertEqual(group['identity'], {'provider': 'openai', 'provider_scope': opaque('a'),
                                             'kind': 'response', 'id': opaque('b')})
        self.assertEqual(group['observation_ids'], [opaque('1'), opaque('2')])
        self.assertTrue(group['additive'])
        self.assertEqual(result['unresolved'], [])

    def test_response_identity_is_provider_and_account_scoped(self):
        data = [observation('1', opaque('b')), observation('2', opaque('b'), account='c'),
                observation('3', opaque('b'), provider='anthropic')]
        self.assertEqual(len(self.resolve(data)['responses']), 3)

    def test_two_responses_for_one_call_remain_distinct(self):
        call = opaque('c')
        data = [observation('1', opaque('b'), call), observation('2', opaque('d'), call)]
        groups = self.resolve(data)['responses']
        self.assertEqual(len(groups), 2)
        self.assertTrue(all(group['additive'] for group in groups))

    def test_verified_unique_call_alias_merges_with_response(self):
        call, response = opaque('c'), opaque('b')
        data = [observation('1', response, call), observation('2', call=call)]
        result = self.resolve(data, [link(call, response)])
        self.assertEqual(len(result['responses']), 1)
        self.assertEqual(result['responses'][0]['observation_ids'], [opaque('1'), opaque('2')])
        self.assertEqual(result['unresolved'], [])

    def test_two_responses_and_call_only_record_leave_overlap_unresolved(self):
        call = opaque('c')
        data = [observation('1', opaque('b'), call), observation('2', opaque('d'), call),
                observation('3', call=call)]
        result = self.resolve(data)
        self.assertEqual(len(result['responses']), 2)
        self.assertTrue(all(not group['additive'] for group in result['responses']))
        self.assertEqual([item['observation_id'] for item in result['unresolved']], [opaque('3')])

    def test_call_alone_requires_verified_stable_unique_alias(self):
        result = self.resolve([observation('1', call=opaque('c'))])
        self.assertEqual(result['responses'], [])
        self.assertEqual(result['unresolved'][0]['observation_id'], opaque('1'))
        malformed = link(opaque('c'), opaque('b'))
        malformed['one_to_one_verified'] = False
        result = self.resolve([observation('1', call=opaque('c'))], [malformed])
        self.assertEqual(result['responses'], [])
        self.assertEqual(len(result['unresolved']), 1)

    def test_verified_stable_call_can_identify_response_when_response_id_absent(self):
        call = opaque('c')
        result = self.resolve([observation('1', call=call)], [link(call, None)])
        self.assertEqual(result['responses'][0]['identity'],
                         {'provider': 'openai', 'provider_scope': opaque('a'),
                          'kind': 'call', 'id': call})
        self.assertTrue(result['responses'][0]['additive'])
        self.assertEqual(result['unresolved'], [])

    def test_missing_identity_never_uses_time_or_token_coincidence(self):
        data = [observation('1'), observation('2')]
        result = self.resolve(data)
        self.assertEqual(result['responses'], [])
        self.assertEqual(len(result['unresolved']), 2)

    def test_unidentified_observation_excludes_same_scope_from_additive_totals(self):
        data = [observation('1', opaque('b')), observation('2'),
                observation('3', opaque('d'), account='c')]
        result = self.resolve(data)
        groups = {group['identity']['provider_scope']: group for group in result['responses']}
        self.assertFalse(groups[opaque('a')]['additive'])
        self.assertTrue(groups[opaque('c')]['additive'])
        self.assertEqual([item['observation_id'] for item in result['unresolved']], [opaque('2')])

    def test_unlinked_call_may_overlap_response_without_call_id(self):
        data = [observation('1', opaque('b')), observation('2', call=opaque('c')),
                observation('3', opaque('d'), account='c')]
        result = self.resolve(data)
        groups = {group['identity']['provider_scope']: group for group in result['responses']}
        self.assertFalse(groups[opaque('a')]['additive'])
        self.assertTrue(groups[opaque('c')]['additive'])
        self.assertEqual([item['observation_id'] for item in result['unresolved']], [opaque('2')])

    def test_conflicting_verified_aliases_do_not_pick_first(self):
        call = opaque('c')
        links = [link(call, opaque('b')), link(call, opaque('d'), 'e')]
        data = [observation('1', call=call)]
        result = self.resolve(data, links)
        self.assertEqual(result['responses'], [])
        self.assertEqual(len(result['unresolved']), 1)
        self.assertEqual(result, self.resolve(data, list(reversed(links))))

    def test_input_permutations_and_repeated_observations_are_stable(self):
        data = [observation('1', opaque('b')), observation('2', opaque('b')),
                observation('3', opaque('d'))]
        expected = self.resolve(data)
        for permutation in itertools.permutations(data):
            self.assertEqual(self.resolve(list(permutation)), expected)
        self.assertEqual(self.resolve(data + [data[0]]), expected)

    def test_duplicate_observation_id_with_different_content_is_invalid(self):
        with self.assertRaises(ValueError):
            self.resolve([observation('1', opaque('b')), observation('1', opaque('d'))])

    def test_limits_and_bool_are_checked_before_processing(self):
        data = [observation('1', opaque('b')), observation('2', opaque('d'))]
        with self.assertRaises(ValueError):
            self.resolve(data, max_observations=1)
        with self.assertRaises(ValueError):
            self.resolve(data, max_observations=True)
        self.assertEqual(len(self.resolve(data, max_observations=2)['responses']), 2)

    def test_raw_paths_secrets_and_unknown_fields_are_rejected_without_echo(self):
        bad = observation('1', opaque('b'))
        bad['provider_scope'] = '/private/token-secret'
        with self.assertRaises(ValueError) as caught:
            self.resolve([bad])
        self.assertNotIn('/private/token-secret', str(caught.exception))
        bad = observation('1', opaque('b'))
        bad['prompt'] = 'private prompt'
        with self.assertRaises(ValueError) as caught:
            self.resolve([bad])
        self.assertNotIn('private prompt', str(caught.exception))

    def test_empty_input_has_no_fabricated_responses(self):
        self.assertEqual(self.resolve([]), {'responses': [], 'unresolved': []})


if __name__ == '__main__':
    unittest.main()
