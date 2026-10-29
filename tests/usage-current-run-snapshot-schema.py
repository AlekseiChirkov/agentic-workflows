#!/usr/bin/env python3
"""Offline checks for bounded, owner-scoped current run snapshots."""
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
fixtures = load('fixtures', 'tests/usage-observation-bundle-schema.py')
inventories = load('inventories', 'tests/usage-inventory-schema.py')

def call(name, *args):
    return getattr(contract, name, lambda *args: None)(*args)

def opaque(digit):
    return 'sha256:' + digit * 64

def snapshot():
    owner = {'owner_kind': 'run', 'owner_id': opaque('b')}
    bundle = fixtures.bundle()
    observation_id = contract.observation_id(bundle['observations'][0])
    receipt = {'schema_version': 1, 'kind': 'usage_accepted',
               'bundle_sha256': contract.content_id(bundle), 'observation_ids': [observation_id],
               'scope': owner | {'attribution_quality': 'asserted'},
               'duplicate': False, 'validator_version': '1'}
    segment = {'schema_version': 1, 'kind': 'collection_segment',
               'segment_id': opaque('c'), 'owner_scope': owner, 'mode': 'on',
               'start': '2026-01-02T03:00:00Z', 'end': None,
               'gap_before': {'state': 'unknown', 'start': None, 'end': None}}
    return {'schema_version': 1, 'kind': 'current_run_snapshot', 'owner_scope': owner,
            'revision': 1, 'mode': 'on', 'segments': [segment],
            'accepted_receipts': [receipt], 'bundles': [bundle],
            'inventories': [inventories.inventory()],
            'inventory_evidence': [inventories.inventory_evidence(inventories.inventory())],
            'overlap_state': 'unknown', 'warning_delivery': [
                {'warning_id': opaque('d'), 'crossing_state': 'unknown',
                 'delivery_state': 'unknown'}],
            'bounds': {'max_bytes': 1048576, 'max_entries': 10000}}

class CurrentRunSnapshotTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_current_run_snapshot', value), value)

    def test_complete_snapshot_preserves_receipts_observations_and_unknowns(self):
        value = snapshot()
        with patch('builtins.open', side_effect=AssertionError('history read')), \
             patch.object(Path, 'open', side_effect=AssertionError('history read')):
            self.assert_valid(value)
        self.assertEqual(value['overlap_state'], 'unknown')
        self.assertEqual(value['warning_delivery'][0]['delivery_state'], 'unknown')
        self.assertEqual(value['segments'][0]['gap_before']['state'], 'unknown')
        self.assertEqual(value['bundles'][0]['observations'][0]['measurements']['input_uncached']['value'], 0)

    def test_session_scope_and_time_only_disabled_snapshot(self):
        value = snapshot()
        value['owner_scope'] = {'owner_kind': 'session', 'owner_id': opaque('e')}
        value.update(mode='off', segments=[], accepted_receipts=[], bundles=[], inventories=[], inventory_evidence=[])
        self.assert_valid(value)

    def test_required_fields_closed_shape_and_private_payload(self):
        value = snapshot()
        self.assert_valid(value)
        for key in value:
            with self.subTest(key=key), self.assertRaises(ValueError):
                call('validate_current_run_snapshot', {k: v for k, v in value.items() if k != key})
        secret = 'PRIVATE_CONTENT_SENTINEL'
        for change in ({'raw_content': secret}, {'source_path': secret},
                       {'owner_scope': {'owner_kind': 'run', 'owner_id': secret}}):
            with self.subTest(change=change), self.assertRaises(ValueError) as error:
                call('validate_current_run_snapshot', value | change)
            self.assertNotIn(secret, str(error.exception))

    def test_scope_revision_mode_and_bounds_are_strict(self):
        value = snapshot()
        self.assert_valid(value)
        variants = [value | change for change in (
            {'schema_version': True}, {'schema_version': 2}, {'kind': 'other'},
            {'revision': -1}, {'revision': True}, {'revision': '1'},
            {'mode': 'auto'}, {'bounds': {}}, {'bounds': {'max_bytes': 0, 'max_entries': 10000}},
            {'bounds': {'max_bytes': 1048577, 'max_entries': 10000}},
            {'bounds': {'max_bytes': 1048576, 'max_entries': 10001}})]
        for section in ('segments', 'accepted_receipts', 'inventories'):
            bad = copy.deepcopy(value)
            scope = 'scope' if section == 'accepted_receipts' else 'owner_scope'
            bad[section][0][scope]['owner_id'] = opaque('f')
            variants.append(bad)
        for index, bad in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(ValueError):
                call('validate_current_run_snapshot', bad)

    def test_receipt_bundle_and_inventory_evidence_are_self_contained(self):
        value = snapshot()
        self.assert_valid(value)
        variants = []
        for section in ('bundles', 'inventory_evidence'):
            bad = copy.deepcopy(value); bad[section] = []; variants.append(bad)
        bad = copy.deepcopy(value); bad['accepted_receipts'][0]['bundle_sha256'] = 'f' * 64; variants.append(bad)
        bad = copy.deepcopy(value); bad['accepted_receipts'][0]['observation_ids'] = ['f' * 64]; variants.append(bad)
        bad = copy.deepcopy(value); bad['inventories'][0]['expected_calls'] = []; variants.append(bad)
        for index, bad in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(ValueError):
                call('validate_current_run_snapshot', bad)

    def test_delivery_state_is_closed_bounded_and_unique(self):
        value = snapshot()
        self.assert_valid(value)
        variants = []
        bad = copy.deepcopy(value); bad['warning_delivery'][0]['delivery_state'] = 'maybe'; variants.append(bad)
        bad = copy.deepcopy(value); bad['warning_delivery'][0]['crossing_state'] = 'maybe'; variants.append(bad)
        bad = copy.deepcopy(value); bad['warning_delivery'] *= 2; variants.append(bad)
        bad = copy.deepcopy(value); bad['warning_delivery'][0]['message'] = 'private'; variants.append(bad)
        for index, bad in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(ValueError):
                call('validate_current_run_snapshot', bad)

    def test_json_duplicate_keys_and_declared_limits(self):
        value = snapshot()
        self.assert_valid(value)
        raw = json.dumps(value, separators=(',', ':')).encode()
        self.assertEqual(call('validate_current_run_snapshot_json', raw), value)
        with self.assertRaises(ValueError):
            call('validate_current_run_snapshot_json', b'{"schema_version":1,"schema_version":1}')
        bad = copy.deepcopy(value); bad['bounds']['max_bytes'] = 10
        with self.assertRaises(ValueError):
            call('validate_current_run_snapshot', bad)
        bad = copy.deepcopy(value); bad['bounds']['max_entries'] = 1
        with self.assertRaises(ValueError):
            call('validate_current_run_snapshot', bad)

if __name__ == '__main__':
    unittest.main()
