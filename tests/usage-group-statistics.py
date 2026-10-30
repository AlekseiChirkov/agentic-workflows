#!/usr/bin/env python3
"""Offline tests for exact and coverage-separated group statistics."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'scripts/usage_telemetry_group_statistics.py'
if MODULE.exists():
    spec = importlib.util.spec_from_file_location('group_statistics', MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
else:
    module = None


def calculate(records, limit=100):
    fn = getattr(module, 'calculate_group_statistics', lambda *args, **kwargs: None)
    return fn(records, max_records=limit)


def entry(coverage, value):
    return {'coverage': coverage, 'value': value}


def distribution(n, median, p90, small_sample):
    return {'n': n, 'median': median, 'p90': p90, 'small_sample': small_sample}


class GroupStatisticsTests(unittest.TestCase):
    def test_four_values_produce_exact_even_median_and_nearest_rank_p90(self):
        rows = [entry('complete', str(n)) for n in (1, 2, 3, 4)]
        result = calculate(rows)
        self.assertEqual(result['complete'], distribution(4, '2.5', '4', True))

    def test_empty_coverage_classes_are_explicitly_unavailable(self):
        result = calculate([])
        self.assertEqual(set(result), {'complete', 'proven_lower_bound', 'subtotal_only', 'unavailable'})
        for stats in result.values():
            self.assertEqual(stats, distribution(0, None, None, True))

    def test_partial_classes_never_enter_complete_distribution_or_each_other(self):
        rows = [entry('complete', '10'), entry('complete', '20'),
                entry('proven_lower_bound', '100'), entry('proven_lower_bound', '200'),
                entry('subtotal_only', '3'), entry('unavailable', None)]
        result = calculate(rows)
        self.assertEqual(result['complete'], distribution(2, '15', '20', True))
        self.assertEqual(result['proven_lower_bound'], distribution(2, '150', '200', True))
        self.assertEqual(result['subtotal_only'], distribution(1, '3', '3', True))
        self.assertEqual(result['unavailable'], distribution(1, None, None, True))

    def test_odd_ties_five_samples_and_nearest_rank_boundary(self):
        rows = [entry('complete', str(n)) for n in (1, 2, 2, 8, 10)]
        self.assertEqual(calculate(rows)['complete'], distribution(5, '2', '10', False))
        rows = [entry('complete', str(n)) for n in range(1, 11)]
        self.assertEqual(calculate(rows)['complete'], distribution(10, '5.5', '9', False))

    def test_large_and_high_precision_values_remain_exact_decimal_strings(self):
        rows = [entry('complete', '9007199254740993.0000000000000000000000000001'),
                entry('complete', '9007199254740993.0000000000000000000000000003')]
        self.assertEqual(calculate(rows)['complete'], distribution(
            2, '9007199254740993.0000000000000000000000000002',
            '9007199254740993.0000000000000000000000000003', True))
        self.assertEqual(calculate([entry('complete', '0'), entry('complete', '0.0000000000000000000000000001')])['complete']['median'],
                         '0.00000000000000000000000000005')

    def test_permutations_do_not_change_results_and_inputs_are_not_mutated(self):
        rows = [entry('complete', '10'), entry('subtotal_only', '0.2'),
                entry('complete', '1'), entry('proven_lower_bound', '9'),
                entry('unavailable', None), entry('complete', '2')]
        before = json.dumps(rows, sort_keys=True)
        self.assertEqual(calculate(rows), calculate(list(reversed(rows))))
        self.assertEqual(json.dumps(rows, sort_keys=True), before)

    def test_rejects_invalid_noncanonical_or_inconsistent_values(self):
        invalid = [entry('complete', None), entry('unavailable', '1'), entry('complete', -1),
                   entry('complete', True), entry('complete', '1e3'), entry('complete', '-1'),
                   entry('complete', '+1'), entry('complete', '01'), entry('complete', '1.0'),
                   entry('complete', 'NaN'), entry('complete', ''), entry('other', '1'),
                   {'coverage': 'complete'}, {'value': '1'}, None]
        for row in invalid:
            with self.subTest(row=row), self.assertRaises(ValueError):
                calculate([row])

    def test_record_limit_is_explicit_and_excess_is_rejected_not_truncated(self):
        rows = [entry('complete', '1'), entry('complete', '2')]
        self.assertEqual(calculate(rows, 2)['complete']['n'], 2)
        for limit in (1, -1, True, '2'):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                calculate(rows, limit)
        self.assertEqual(calculate([], 0)['complete']['n'], 0)
        with self.assertRaises(TypeError):
            getattr(module, 'calculate_group_statistics', lambda *args: None)(rows)

    def test_forbidden_fields_and_invalid_values_do_not_echo_private_input(self):
        secret = '/private/path/example-secret'
        for row in ({'coverage': 'complete', 'value': '1', 'path': secret},
                    entry('complete', secret), entry(secret, '1')):
            with self.subTest(row=row):
                with self.assertRaises(ValueError) as error:
                    calculate([row])
                self.assertNotIn(secret, str(error.exception))

    def test_statistics_perform_no_file_access(self):
        rows = [entry('complete', '1')]
        with patch('builtins.open', side_effect=AssertionError('unexpected file access')):
            self.assertEqual(calculate(rows)['complete']['median'], '1')


if __name__ == '__main__':
    unittest.main()
