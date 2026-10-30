#!/usr/bin/env python3
"""Offline tests for evidenced cumulative intervals and aggregate coverage."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'scripts/usage_telemetry_epochs.py'
if MODULE.exists():
    spec = importlib.util.spec_from_file_location('usage_telemetry_epochs', MODULE)
    epochs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(epochs)
else:
    epochs = None


def interval():
    identity = {'provider': 'provider', 'account': 'account', 'model': 'model',
                'units': 'input_tokens', 'epoch': 'epoch-1'}
    return {
        'before': dict(identity, sequence=4, position=10, value=90),
        'after': dict(identity, sequence=5, position=20, value=110),
        # This API accepts evidence already verified by its caller; it does not
        # authenticate an assertion or discover sources itself.
        'coverage': {'complete': True, 'before_clear': True, 'after_clear': True,
                     'atomic_on_completion': False,
                     'requests': [{'id': 'request-1', 'start': 11, 'end': 19}]},
    }


def aggregate(start, end, value, **changes):
    result = {'id': 'interval-%s-%s' % (start, end), 'provider': 'provider',
              'account': 'account', 'model': 'model', 'units': 'input_tokens',
              'epoch': 'epoch-1', 'start': start, 'end': end,
              'value': value, 'boundaries_proven': True}
    result.update(changes)
    return result


class CumulativeEpochTests(unittest.TestCase):
    def resolve(self, value):
        self.assertIsNotNone(epochs, 'cumulative epoch resolver is missing')
        return epochs.resolve_interval(value)

    def aggregate(self, items):
        self.assertIsNotNone(epochs, 'aggregate coverage resolver is missing')
        return epochs.aggregate_intervals(items)

    def test_single_fully_enclosed_request_has_exact_delta(self):
        result = self.resolve(interval())
        self.assertEqual(result['request_usage'], {'request-1': 20})
        self.assertEqual(result['interval_aggregate'], 20)

    def test_mid_request_snapshot_is_not_full_request_usage(self):
        value = interval()
        value['before']['value'] = 100
        value['coverage']['before_clear'] = False
        value['coverage']['requests'][0]['start'] = 5
        result = self.resolve(value)
        self.assertEqual(result['request_usage'], {})
        self.assertEqual(result['interval_aggregate'], 10)

    def test_two_requests_are_not_assigned_individual_usage(self):
        value = interval()
        value['coverage']['requests'].append({'id': 'request-2', 'start': 12, 'end': 18})
        result = self.resolve(value)
        self.assertEqual(result['request_usage'], {})
        self.assertEqual(result['interval_aggregate'], 20)

    def test_atomic_completion_profile_can_prove_one_request(self):
        value = interval()
        value['coverage']['before_clear'] = False
        value['coverage']['requests'][0]['start'] = 5
        value['coverage']['atomic_on_completion'] = True
        result = self.resolve(value)
        self.assertEqual(result['request_usage'], {'request-1': 20})

    def test_completion_at_initial_boundary_is_not_attributed_to_interval(self):
        for atomic in (False, True):
            with self.subTest(atomic=atomic):
                value = interval()
                value['coverage']['atomic_on_completion'] = atomic
                value['coverage']['requests'][0]['start'] = 10 if not atomic else 5
                value['coverage']['requests'][0]['end'] = 10
                self.assertEqual(self.resolve(value)['request_usage'], {})

    def test_completion_just_after_initial_boundary_can_be_attributed(self):
        for atomic in (False, True):
            with self.subTest(atomic=atomic):
                value = interval()
                value['coverage']['atomic_on_completion'] = atomic
                value['coverage']['requests'][0]['start'] = 10 if not atomic else 5
                value['coverage']['requests'][0]['end'] = 11
                self.assertEqual(self.resolve(value)['request_usage'], {'request-1': 20})

    def test_each_identity_dimension_must_match_and_be_known(self):
        for field in ('provider', 'account', 'model', 'units', 'epoch'):
            for changed in ('different', None, ''):
                with self.subTest(field=field, changed=changed):
                    value = interval()
                    value['after'][field] = changed
                    result = self.resolve(value)
                    self.assertEqual(result['request_usage'], {})
                    self.assertIsNone(result['interval_aggregate'])

    def test_unknown_baseline_reset_gap_and_repeated_prefix_are_unresolved(self):
        for change in ('missing', 'reset', 'gap', 'duplicate', 'reverse'):
            with self.subTest(change=change):
                value = interval()
                if change == 'missing': value['before']['value'] = None
                if change == 'reset': value['after']['value'] = 89
                if change == 'gap': value['after']['sequence'] = 6
                if change == 'duplicate': value['after']['sequence'] = 4
                if change == 'reverse': value['after']['position'] = 9
                result = self.resolve(value)
                self.assertEqual(result['request_usage'], {})
                self.assertIsNone(result['interval_aggregate'])

    def test_complete_inventory_is_required_for_interval_delta(self):
        value = interval()
        value['coverage']['complete'] = False
        result = self.resolve(value)
        self.assertEqual(result['request_usage'], {})
        self.assertIsNone(result['interval_aggregate'])

    def test_missing_end_boundary_or_request_extent_never_proves_usage(self):
        for change in ('after_busy', 'missing_end', 'after_end', 'unknown_start'):
            with self.subTest(change=change):
                value = interval()
                if change == 'after_busy': value['coverage']['after_clear'] = False
                if change == 'missing_end': value['coverage']['requests'][0]['end'] = None
                if change == 'after_end': value['coverage']['requests'][0]['end'] = 21
                if change == 'unknown_start': value['coverage']['requests'][0]['start'] = None
                result = self.resolve(value)
                self.assertEqual(result['request_usage'], {})

    def test_zero_is_evidenced_but_missing_is_not_zero(self):
        value = interval()
        value['before']['value'] = value['after']['value']
        self.assertEqual(self.resolve(value)['request_usage'], {'request-1': 0})
        value['after']['value'] = None
        result = self.resolve(value)
        self.assertEqual(result['request_usage'], {})
        self.assertIsNone(result['interval_aggregate'])

    def test_disjoint_aggregate_intervals_have_a_separate_total(self):
        items = [aggregate(10, 20, 20), aggregate(20, 30, 7)]
        result = self.aggregate(items)
        self.assertEqual(result['total'], 27)
        self.assertEqual(result['included_ids'], ['interval-10-20', 'interval-20-30'])
        self.assertEqual(result['reconciliation_ids'], [])
        self.assertFalse(result['complete_request_accounting'])

    def test_large_nonoverlapping_derived_sum_remains_exact(self):
        maximum = 9007199254740991
        items = [aggregate(index * 2, index * 2 + 1, maximum) for index in range(1025)]
        result = self.aggregate(items)
        self.assertEqual(result['total'], 1025 * maximum)
        self.assertEqual(len(result['included_ids']), 1025)
        self.assertEqual(result['reconciliation_ids'], [])

    def test_overlap_unknown_bounds_or_units_are_only_reconciliation(self):
        cases = [
            [aggregate(10, 20, 20), aggregate(19, 30, 7)],
            [aggregate(10, 20, 20, boundaries_proven=False)],
            [aggregate(10, 20, 20, units=None)],
        ]
        for items in cases:
            with self.subTest(items=items):
                result = self.aggregate(items)
                self.assertIsNone(result['total'])
                self.assertEqual(result['included_ids'], [])
                self.assertEqual(result['reconciliation_ids'], sorted(item['id'] for item in items))
                self.assertFalse(result['complete_request_accounting'])

    def test_aggregate_permutation_is_deterministic_and_duplicate_is_not_added(self):
        a, b = aggregate(10, 20, 20), aggregate(20, 30, 7)
        first = self.aggregate([a, b, copy.deepcopy(a)])
        second = self.aggregate([b, a])
        self.assertEqual(first, second)
        self.assertEqual(first['total'], 27)

    def test_empty_aggregate_set_is_unknown_not_zero(self):
        result = self.aggregate([])
        self.assertIsNone(result['total'])
        self.assertEqual(result['included_ids'], [])
        self.assertFalse(result['complete_request_accounting'])

    def test_invalid_numeric_values_are_never_treated_as_valid_usage(self):
        for bad in (-1, True, 1.5, '110'):
            with self.subTest(bad=bad):
                value = interval()
                value['after']['value'] = bad
                result = self.resolve(value)
                self.assertEqual(result['request_usage'], {})
                self.assertIsNone(result['interval_aggregate'])


if __name__ == '__main__':
    unittest.main()
