#!/usr/bin/env python3
"""Lifecycle projections preserve empty, unpriced and cache-write evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixtures', ROOT / 'tests/usage-lifecycle-projection-schema.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
contract = fixtures.contract


def empty_projection():
    value = fixtures.projection()
    owner = {key: value['scope'][key] for key in ('owner_kind', 'owner_id')}
    inventory = {'schema_version': 1, 'kind': 'inventory', 'profile_id': 'profile',
                 'profile_version': '1', 'source_hash': 'a' * 64, 'owner_scope': owner,
                 'window': {'start': '2026-01-01T00:00:00Z', 'end': '2026-01-01T01:00:00Z'},
                 'observed_at': '2026-01-01T01:01:00Z', 'state': 'complete', 'evidence': None,
                 'expected_calls': [], 'expected_responses': [], 'unresolved_slots': [],
                 'coverage': {'children': 'included', 'internal_checks': 'included', 'tools': 'included'}}
    proof = {'schema_version': 1, 'kind': 'inventory_evidence', 'profile_id': 'profile',
             'profile_version': '1', 'source_hash': 'a' * 64,
             'inventory_digest': contract.content_id({k: v for k, v in inventory.items() if k != 'evidence'})}
    inventory['evidence'] = contract.content_id(proof)
    value.update(inventory=inventory, contributors=[], cost_usd='0',
                 completeness={'inventory': 'complete', 'identity': 'not_applicable',
                               'measurements': 'not_applicable', 'pricing': 'not_applicable',
                               'attribution': 'not_applicable'})
    value['evidence_objects'].append(proof)
    return value


def unpriced_projection():
    value = fixtures.projection()
    del value['cost_usd']
    value['completeness']['pricing'] = 'partial'
    value['contributors'][0]['price_snapshot_id'] = None
    value['contributors'][0]['priced_usd'] = None
    value.update(priced_subtotal_usd='0.5', subtotal_quality='subtotal_only')
    return value


def cache_projection():
    value = fixtures.projection()
    snapshot = value['price_snapshots'][0]
    short = next(rate for rate in snapshot['rates'] if rate['component'] == 'input_cache_write')
    short.update(threshold=None, multiplier={'state': 'none'})
    long = copy.deepcopy(short)
    long.update(cache_ttl_seconds=3600, usd='4')
    snapshot['rates'].append(long)
    price_id = contract.content_id(snapshot)
    value['scenario']['snapshot_ids'] = [price_id]
    for contributor in value['contributors']:
        contributor['price_snapshot_id'] = price_id
    first = value['contributors'][0]
    first['measurements']['input_cache_write'] = []
    for ttl, amount in (('5m', 100), ('1h', 100)):
        proof = {'schema_version': 1, 'kind': 'measurement_evidence', 'profile_id': 'profile',
                 'source_hash': 'a' * 64, 'record_number': 1, 'field': 'input_cache_write',
                 'value': amount, 'ttl': ttl}
        value['evidence_objects'].append(proof)
        first['measurements']['input_cache_write'].append({'ttl': ttl, 'tokens': {'measurement_state': 'final',
                'value': amount, 'reasons': [], 'evidence': contract.content_id(proof)}})
    first['priced_usd'] = '1.00065'
    value['cost_usd'] = '1.50065'
    return value


class ProjectionStatesTests(unittest.TestCase):
    def test_verified_empty_inventory_is_self_contained_and_zero(self):
        value = empty_projection()
        self.assertEqual(contract.validate_lifecycle_projection(value), value)
        bad = copy.deepcopy(value)
        del bad['inventory']
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(bad)
        bad = copy.deepcopy(value)
        bad['inventory']['coverage']['tools'] = 'unknown'
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(bad)

    def test_unpriced_response_and_known_subtotal_remain_partial(self):
        value = unpriced_projection()
        self.assertEqual(contract.validate_lifecycle_projection(value), value)
        bad = copy.deepcopy(value)
        bad['cost_usd'] = '1.5'
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(bad)
        bad = copy.deepcopy(value)
        bad['subtotal_quality'] = 'proven_lower_bound'
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(bad)

    def test_ttl_split_write_uses_matching_independent_evidence_and_rate(self):
        value = cache_projection()
        self.assertEqual(contract.validate_lifecycle_projection(value), value)
        bad = copy.deepcopy(value)
        bad['contributors'][0]['measurements']['input_cache_write'][0]['ttl'] = '1h'
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(bad)
        bad = copy.deepcopy(value)
        bad['cost_usd'] = '1.5'
        with self.assertRaises(ValueError):
            contract.validate_lifecycle_projection(bad)


if __name__ == '__main__':
    unittest.main()
