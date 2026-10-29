#!/usr/bin/env python3
"""Offline contract checks for self-contained lifecycle usage projections."""
import copy
import hashlib
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
price_fixtures = load('price_fixtures', 'tests/usage-price-snapshot-schema.py')
scenario_fixtures = load('scenario_fixtures', 'tests/usage-pricing-scenario-schema.py')

def call(name, *args):
    return getattr(contract, name, lambda *args: None)(*args)

def projection():
    price = price_fixtures.snapshot()
    scenario = scenario_fixtures.scenario()
    price['rates'][0]['multiplier'] = {'state': 'none'}
    scenario['source_parameters']['model']['value'] = price['model']
    scenario['threshold_rules'] = []
    price_id = contract.content_id(price)
    scenario['snapshot_ids'] = [price_id]
    contributors = []
    evidence_objects = []
    for index, quantity in enumerate((500000, 250000), 1):
        evidence = {'schema_version': 1, 'kind': 'measurement_evidence',
                    'profile_id': 'profile', 'source_hash': 'a' * 64,
                    'record_number': index, 'field': 'input_uncached', 'value': quantity}
        evidence_objects.append(evidence)
        contributors.append({'contributor_id': 'sha256:' + str(index) * 64,
                             'observation_ids': [str(index) * 64],
                             'profile_id': 'profile', 'profile_version': '1',
                             'measurements': {'input_uncached': {
                                 'measurement_state': 'final', 'value': quantity,
                                 'reasons': [], 'evidence': hashlib.sha256(
                                     contract.canonical_bytes(evidence)).hexdigest()}},
                             'price_snapshot_id': price_id,
                             'priced_usd': '1' if index == 1 else '0.5'})
    return {'schema_version': 1, 'kind': 'lifecycle_projection',
            'scope': {'owner_kind': 'run', 'owner_id': 'sha256:' + '3' * 64,
                      'attribution_quality': 'verified'},
            'as_of': '2026-01-02T03:04:05Z',
            'contributors': contributors, 'evidence_objects': evidence_objects,
            'price_snapshots': [price], 'scenario': scenario,
            'completeness': {'inventory': 'complete', 'identity': 'complete',
                             'measurements': 'complete', 'pricing': 'complete',
                             'attribution': 'complete'},
            'cost_usd': '1.5'}

class LifecycleProjectionSchemaTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_lifecycle_projection', value), value)

    def test_complete_projection_is_self_contained(self):
        value = projection()
        self.assert_valid(value)
        self.assertEqual(value['cost_usd'], '1.5')
        self.assertEqual(value['contributors'][0]['measurements']['input_uncached']['value'], 500000)
        self.assert_valid(value | {'display_cost_usd': '1.50'})

    def test_partial_projection_preserves_explicit_unknowns_without_full_cost(self):
        value = projection()
        del value['cost_usd']
        value['completeness']['inventory'] = 'unknown'
        value['priced_subtotal_usd'] = '1.5'
        value['subtotal_quality'] = 'subtotal_only'
        self.assert_valid(value)
        value['subtotal_quality'] = 'proven_lower_bound'
        self.assert_valid(value)
        value['cost_usd'] = '1.5'
        with self.assertRaises(ValueError):
            call('validate_lifecycle_projection', value)
        for dimension in ('identity', 'measurements', 'pricing', 'attribution'):
            value = projection()
            value['completeness'][dimension] = 'partial'
            with self.subTest(dimension=dimension), self.assertRaises(ValueError):
                call('validate_lifecycle_projection', value)

    def test_required_fields_closed_shape_and_decimal_format(self):
        value = projection()
        self.assert_valid(value)
        for key in value:
            with self.subTest(key=key), self.assertRaises(ValueError):
                call('validate_lifecycle_projection', {k: v for k, v in value.items() if k != key})
        for bad in (True, 1.5, '', 'unknown', '-1', '+1', '1e3', '01', '1.50', 'NaN'):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                call('validate_lifecycle_projection', value | {'cost_usd': bad})
        for change in ({'schema_version': True}, {'schema_version': 2},
                       {'kind': 'usage_bundle'}, {'as_of': '2026-02-30T00:00:00Z'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_lifecycle_projection', value | change)

    def test_contributors_evidence_and_exact_total_must_agree(self):
        value = projection()
        self.assert_valid(value)
        variants = []
        for change in ({'cost_usd': '1.4'}, {'cost_usd': '1.5001'}):
            variants.append(value | change)
        bad = copy.deepcopy(value); bad['contributors'][0]['priced_usd'] = '0.9'; variants.append(bad)
        bad = copy.deepcopy(value); bad['contributors'][0]['priced_usd'] = '0.9'; bad['contributors'][1]['priced_usd'] = '0.6'; variants.append(bad)
        bad = copy.deepcopy(value); bad['contributors'][0]['measurements']['input_uncached']['value'] = 1; variants.append(bad)
        bad = copy.deepcopy(value); bad['evidence_objects'] = []; variants.append(bad)
        bad = copy.deepcopy(value); bad['contributors'][0]['measurements']['input_uncached']['evidence'] = 'f' * 64; variants.append(bad)
        bad = copy.deepcopy(value); bad['contributors'][1]['contributor_id'] = bad['contributors'][0]['contributor_id']; variants.append(bad)
        bad = copy.deepcopy(value); bad['contributors'][1]['observation_ids'] = bad['contributors'][0]['observation_ids']; variants.append(bad)
        for index, bad in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(ValueError):
                call('validate_lifecycle_projection', bad)

    def test_price_definitions_and_scenario_must_match_hashes(self):
        value = projection()
        self.assert_valid(value)
        variants = []
        bad = copy.deepcopy(value); bad['price_snapshots'] = []; variants.append(bad)
        bad = copy.deepcopy(value); bad['price_snapshots'][0]['rates'][0]['usd'] = '3'; variants.append(bad)
        bad = copy.deepcopy(value); bad['scenario']['snapshot_ids'] = ['f' * 64]; variants.append(bad)
        bad = copy.deepcopy(value); bad['contributors'][0]['price_snapshot_id'] = 'f' * 64; variants.append(bad)
        for index, bad in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(ValueError):
                call('validate_lifecycle_projection', bad)

    def test_complete_cost_requires_known_multiplier_applicability(self):
        value = projection()
        self.assert_valid(value)
        for multiplier in (None, {'state': 'unknown', 'scope': 'service_tier',
                                   'reason': 'missing_applicability_evidence'}):
            bad = copy.deepcopy(value)
            if multiplier is None:
                del bad['price_snapshots'][0]['rates'][0]['multiplier']
            else:
                bad['price_snapshots'][0]['rates'][0]['multiplier'] = multiplier
            # Update all references so the failure is about applicability, not hashes.
            price_id = contract.content_id(bad['price_snapshots'][0])
            bad['scenario']['snapshot_ids'] = [price_id]
            for contributor in bad['contributors']:
                contributor['price_snapshot_id'] = price_id
            with self.subTest(multiplier=multiplier), self.assertRaises(ValueError):
                call('validate_lifecycle_projection', bad)

    def test_private_fields_are_rejected_without_echo(self):
        value = projection()
        self.assert_valid(value)
        secret = 'PRIVATE_CONTENT_SENTINEL'
        for change in ({'raw_content': secret}, {'source_path': secret},
                       {'scope': {'owner_kind': 'run', 'owner_id': secret,
                                  'attribution_quality': 'verified'}}):
            with self.subTest(change=change), self.assertRaises(ValueError) as error:
                call('validate_lifecycle_projection', value | change)
            self.assertNotIn(secret, str(error.exception))

    def test_canonical_order_and_identity_are_stable(self):
        value = projection()
        self.assert_valid(value)
        reordered = copy.deepcopy(value)
        reordered['contributors'].reverse()
        reordered['evidence_objects'].reverse()
        self.assert_valid(reordered)
        self.assertEqual(contract.canonical_bytes(value), contract.canonical_bytes(reordered))
        self.assertEqual(contract.content_id(value), contract.content_id(reordered))
        with self.assertRaises(ValueError):
            contract.canonical_bytes(value, set_keys={('contributors',): lambda x: x['contributor_id'][::-1]})

    def test_raw_canonical_limits_duplicate_keys_and_count_bounds(self):
        value = projection()
        self.assert_valid(value)
        raw = json.dumps(value, separators=(',', ':')).encode()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'LIFECYCLE_PROJECTION_LIMIT', size, create=True):
            self.assert_valid(value)
        with patch.object(contract, 'LIFECYCLE_PROJECTION_LIMIT', size - 1, create=True):
            with self.assertRaises(ValueError):
                call('validate_lifecycle_projection', value)
        with patch.object(contract, 'LIFECYCLE_PROJECTION_LIMIT', len(raw), create=True):
            self.assertEqual(call('validate_lifecycle_projection_json', raw), value)
            with self.assertRaises(ValueError):
                call('validate_lifecycle_projection_json', raw + b' ')
        with self.assertRaises(ValueError):
            call('validate_lifecycle_projection_json', b'{"schema_version":1,"schema_version":1}')
        invalid = copy.deepcopy(value)
        invalid['contributors'] = invalid['contributors'] * 5001
        with self.assertRaises(ValueError):
            call('validate_lifecycle_projection', invalid)

if __name__ == '__main__':
    unittest.main()
