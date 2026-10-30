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
            'overlap_state': 'unknown', 'warning_delivery': [warning()],
            'bounds': {'max_bytes': 1048576, 'max_entries': 10000,
                       'max_source_bytes': 1048576, 'max_total_bytes': 1048576,
                       'max_records': 10000}}

def warning():
    return {'warning_id': opaque('d'), 'policy_id': 'policy', 'policy_version': 1,
            'scope': {'owner_kind': 'run', 'owner_id': opaque('b')},
            'owner_scope': {'owner_kind': 'run', 'owner_id': opaque('b')},
            'metric': 'duration_ms', 'episode': 1, 'crossing_state': 'unknown',
            'delivery_state': 'unknown'}

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
        value.update(mode='off', segments=[], accepted_receipts=[], bundles=[], inventories=[], inventory_evidence=[], warning_delivery=[])
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

    def test_warning_policy_scope_metric_and_episode_survive_clear_and_recross(self):
        value = snapshot()
        value['warning_delivery'][0].update(crossing_state='cleared', delivery_state='delivered')
        self.assert_valid(value)
        self.assertEqual(value['warning_delivery'][0]['episode'], 1)
        reopened = copy.deepcopy(value)
        reopened['warning_delivery'][0].update(warning_id=opaque('e'), episode=2,
                                                crossing_state='crossed', delivery_state='pending')
        self.assert_valid(reopened)
        self.assertEqual(reopened['warning_delivery'][0]['episode'], 2)
        self.assertNotEqual(value['warning_delivery'][0]['warning_id'], reopened['warning_delivery'][0]['warning_id'])
        for key in ('policy_id', 'policy_version', 'scope', 'metric', 'episode'):
            bad = copy.deepcopy(value); del bad['warning_delivery'][0][key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                call('validate_current_run_snapshot', bad)
        variants = []
        bad = copy.deepcopy(value); bad['warning_delivery'][0]['scope']['owner_id'] = opaque('f'); variants.append(bad)
        for change in ({'episode': 0}, {'episode': -1}, {'episode': True},
                       {'metric': 'unknown'}, {'policy_id': ''}, {'policy_version': 0},
                       {'policy_version': '1'}):
            bad = copy.deepcopy(value); bad['warning_delivery'][0].update(change); variants.append(bad)
        for index, bad in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(ValueError):
                call('validate_current_run_snapshot', bad)

    def test_warning_subscopes_and_multiple_episodes_preserve_independent_delivery(self):
        value = snapshot()
        warning_one = value['warning_delivery'][0]
        warning_one.update(scope={'owner_kind': 'request', 'owner_id': opaque('1')},
                           metric='completeness', episode=1,
                           crossing_state='cleared', delivery_state='failed')
        warning_two = copy.deepcopy(warning_one)
        warning_two.update(warning_id=opaque('e'), episode=2,
                           crossing_state='crossed', delivery_state='pending')
        value['warning_delivery'].append(warning_two)
        self.assert_valid(value)
        self.assertEqual([item['delivery_state'] for item in value['warning_delivery']], ['failed', 'pending'])
        span = copy.deepcopy(value)
        for item in span['warning_delivery']:
            item['scope'] = {'owner_kind': 'span', 'owner_id': opaque('2')}
        self.assert_valid(span)
        foreign = copy.deepcopy(value)
        foreign['warning_delivery'][0]['owner_scope']['owner_id'] = opaque('f')
        with self.assertRaises(ValueError):
            call('validate_current_run_snapshot', foreign)
        duplicate = copy.deepcopy(value)
        duplicate['warning_delivery'].append(copy.deepcopy(duplicate['warning_delivery'][0]))
        with self.assertRaises(ValueError):
            call('validate_current_run_snapshot', duplicate)
        missing = copy.deepcopy(value)
        del missing['warning_delivery'][0]['owner_scope']
        with self.assertRaises(ValueError):
            call('validate_current_run_snapshot', missing)

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

    def test_explicit_private_part_manifest_is_valid_without_opening_files(self):
        value = snapshot()
        value.update(segments=[], accepted_receipts=[], bundles=[], inventories=[],
                     inventory_evidence=[], warning_delivery=[])
        value['parts'] = [{'kind': 'usage_bundle', 'local_path': '/selected/bundle.json',
                           'sha256': 'a' * 64, 'size_bytes': 123}]
        with patch('builtins.open', side_effect=AssertionError('part opened')), \
             patch.object(Path, 'open', side_effect=AssertionError('part opened')):
            self.assert_valid(value)
        self.assertEqual(value['parts'][0]['sha256'], 'a' * 64)
        self.assertEqual(value['parts'][0]['local_path'], '/selected/bundle.json')

    def test_part_manifest_rejects_implicit_or_unbounded_inputs(self):
        value = snapshot()
        value.update(segments=[], accepted_receipts=[], bundles=[], inventories=[],
                     inventory_evidence=[], warning_delivery=[])
        part = {'kind': 'usage_bundle', 'local_path': '/selected/bundle.json',
                'sha256': 'a' * 64, 'size_bytes': 123}
        value['parts'] = [part]
        self.assert_valid(value)
        variants = []
        for key in part:
            bad = copy.deepcopy(value); del bad['parts'][0][key]; variants.append(bad)
        for change in ({'local_path': '/selected/*.json'}, {'local_path': ''},
                       {'sha256': 'a' * 63}, {'size_bytes': -1}, {'size_bytes': True},
                       {'kind': 'history'}, {'raw_content': 'private'}):
            bad = copy.deepcopy(value); bad['parts'][0].update(change); variants.append(bad)
        bad = copy.deepcopy(value); bad['parts'] *= 2; variants.append(bad)
        bad = copy.deepcopy(value); bad['parts'] = [part] * 10001; variants.append(bad)
        bad = copy.deepcopy(value); bad['bounds']['max_entries'] = 1
        bad['parts'].append(part | {'local_path': '/selected/second.json', 'sha256': 'b' * 64})
        variants.append(bad)
        for index, bad in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(ValueError):
                call('validate_current_run_snapshot', bad)

    def test_part_read_limits_must_be_explicit_and_cover_the_selected_total(self):
        value = snapshot()
        value.update(segments=[], accepted_receipts=[], bundles=[], inventories=[],
                     inventory_evidence=[], warning_delivery=[])
        value['parts'] = [{'kind': 'usage_bundle', 'local_path': '/selected/one.json',
                           'sha256': 'a' * 64, 'size_bytes': 73},
                          {'kind': 'usage_bundle', 'local_path': '/selected/two.json',
                           'sha256': 'b' * 64, 'size_bytes': 50}]
        value['bounds'].update(max_source_bytes=73, max_total_bytes=123, max_records=1)
        with patch('builtins.open', side_effect=AssertionError('part opened')):
            self.assert_valid(value)
        for key in ('max_source_bytes', 'max_total_bytes', 'max_records'):
            bad = copy.deepcopy(value); del bad['bounds'][key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                call('validate_current_run_snapshot', bad)
        for change in ({'max_source_bytes': 72}, {'max_total_bytes': 122},
                       {'max_records': 0}, {'max_source_bytes': True},
                       {'max_total_bytes': -1}, {'max_records': True}):
            bad = copy.deepcopy(value); bad['bounds'].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_current_run_snapshot', bad)

    def test_snapshot_schema_sets_have_stable_canonical_identity(self):
        value = snapshot()
        value['warning_delivery'].append(warning() | {'warning_id': opaque('e'),
                                                        'policy_id': 'second_policy',
                                                        'crossing_state': 'below', 'delivery_state': 'pending'})
        value['bundles'][0]['sources'].append({'source_id': opaque('f'), 'sha256': 'b' * 64})
        value['accepted_receipts'][0]['bundle_sha256'] = contract.content_id(value['bundles'][0])
        self.assert_valid(value)
        other = copy.deepcopy(value)
        other['warning_delivery'].reverse()
        other['bundles'][0]['sources'].reverse()
        other['inventories'][0]['expected_responses'].reverse()
        self.assert_valid(other)
        self.assertEqual(contract.canonical_bytes(value), contract.canonical_bytes(other))
        self.assertEqual(contract.content_id(value), contract.content_id(other))
        with self.assertRaises(ValueError):
            contract.canonical_bytes(value, set_keys={('warning_delivery',): lambda item: item['warning_id']})

if __name__ == '__main__':
    unittest.main()
