#!/usr/bin/env python3
"""Offline checks for explicit, bounded ownership metadata."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

contract = module('contract', 'scripts/usage_telemetry_contract.py')
envelope = module('envelope', 'tests/usage-observation-bundle-schema.py')


def call(name, *args):
    return getattr(contract, name, lambda *args: None)(*args)


def opaque(ch):
    return 'sha256:' + ch * 64


def attribution():
    return {'owner_kind': 'shared_pool', 'quality': 'verified',
            'candidates': [opaque('1'), opaque('2')],
            'owner_scope': {'owner_kind': 'task', 'owner_id': opaque('3')},
            'parent_span_id': opaque('4'), 'root_command': opaque('5'),
            'stage': opaque('6'), 'role': opaque('7'), 'execution_path': 'full',
            'attempt': 2, 'capability': opaque('8'),
            'basis': 'correlation', 'evidence': 'a' * 64}


class AttributionTests(unittest.TestCase):
    def valid(self, value):
        self.assertEqual(call('validate_attribution', value), value)

    def test_full_and_explicit_unknowns_are_preserved(self):
        value = attribution()
        self.valid(value)
        for quality in ('asserted', 'verified', 'inferred'):
            self.valid(value | {'quality': quality})
        unknown = value | {'owner_kind': 'unattributed', 'quality': 'unknown',
                           'candidates': [], 'owner_scope': None, 'parent_span_id': None,
                           'root_command': None, 'stage': None, 'role': None,
                           'execution_path': None, 'attempt': None, 'capability': None,
                           'basis': 'unknown', 'evidence': None}
        self.valid(unknown)
        self.assertIsNone(unknown['parent_span_id'])
        self.assertIsNone(unknown['attempt'])

    def test_compact_existing_form_and_valid_kinds(self):
        for kind in ('span', 'task', 'shared_pool', 'unattributed'):
            self.valid({'owner_kind': kind, 'quality': 'asserted', 'candidates': []})

    def test_invalid_fields_and_untrusted_identifiers(self):
        value = attribution()
        self.valid(value)
        secret = 'PRIVATE_PAYLOAD_SENTINEL'
        changes = ({'owner_kind': 'worker'}, {'quality': 'guessed'}, {'basis': 'timestamp'},
                   {'execution_path': 'automatic'}, {'evidence': '/private/path'},
                   {'evidence': 'A' * 64}, {'parent_span_id': '/private/path'},
                   {'root_command': secret}, {'owner_scope': {'owner_kind': 'task', 'owner_id': secret}},
                   {'attempt': -1}, {'attempt': True}, {'raw_content': secret})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError) as error:
                call('validate_attribution', value | change)
            self.assertNotIn(secret, str(error.exception))
        for key in ('owner_kind', 'quality', 'candidates'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                call('validate_attribution', {k: v for k, v in value.items() if k != key})

    def test_candidate_boundary_duplicates_and_types(self):
        value = attribution()
        self.valid(value)
        candidates = ['sha256:' + format(i, '064x') for i in range(64)]
        self.valid(value | {'candidates': candidates})
        for bad in (candidates + [opaque('f')], [opaque('1'), opaque('1')],
                    ['/private/path'], 'not-a-list', None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                call('validate_attribution', value | {'candidates': bad})

    def test_observation_and_bundle_accept_same_attribution_and_reject_bad(self):
        item = envelope.observation()
        item['attribution'] = attribution()
        self.assertEqual(call('validate_observation', item), item)
        bundle = envelope.bundle()
        bundle['observations'] = [item]
        self.assertEqual(call('validate_usage_bundle', bundle), bundle)
        for key, bad in (('owner_kind', 'bad'), ('evidence', 'not-a-digest'),
                         ('parent_span_id', '/private/path')):
            invalid = copy.deepcopy(bundle)
            invalid['observations'][0]['attribution'][key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                call('validate_usage_bundle', invalid)

    def test_canonical_candidates_are_order_independent(self):
        item = envelope.observation()
        item['attribution'] = attribution()
        other = copy.deepcopy(item)
        other['attribution']['candidates'].reverse()
        self.assertEqual(contract.observation_id(item), contract.observation_id(other))
        self.assertEqual(contract.canonical_bytes(item), contract.canonical_bytes(other))

    def test_json_rejects_duplicate_fields(self):
        payload = json.dumps(envelope.observation()).replace(
            '"owner_kind": "unattributed"',
            '"owner_kind": "unattributed", "owner_kind": "task"')
        with self.assertRaises(ValueError):
            call('validate_observation_json', payload)


if __name__ == '__main__':
    unittest.main()
