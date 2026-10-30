#!/usr/bin/env python3
"""Offline tests for deterministic, lossless retrospective exports."""
import copy
import csv
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'scripts/usage_telemetry_exports.py'
if MODULE.exists():
    spec = importlib.util.spec_from_file_location('usage_telemetry_exports', MODULE)
    exports = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exports)
else:
    exports = None


def report():
    return {
        'schema_version': 1, 'kind': 'retrospective_report',
        'corpus_id': 'sha256:' + '1' * 64, 'scenario_id': 'scenario-1',
        'as_of': '2026-01-02T03:04:05Z',
        'versions': {'normalizer': '1', 'prices': '1'},
        'source_hash': '2' * 64, 'expanded_hash': '3' * 64,
        'completeness': {'inventory': 'complete', 'identity': 'partial',
                         'measurements': 'unknown', 'pricing': 'not_applicable',
                         'attribution': 'complete'},
        'metrics': [
            {'name': 'input_tokens', 'value': '123456789012345678901234567890',
             'unit': 'tokens', 'scope': 'run', 'source': 'synthetic', 'quality': 'measured'},
            {'name': 'cost', 'value': '0.0000000000000000000123',
             'unit': 'USD', 'scope': 'run', 'source': 'synthetic', 'quality': 'estimated'},
            {'name': 'output_tokens', 'value': '0', 'unit': 'tokens',
             'scope': 'run', 'source': 'synthetic', 'quality': 'measured'},
            {'name': 'quality', 'value': None, 'unit': 'score',
             'scope': 'run', 'source': None, 'quality': 'unknown'},
        ],
        'groups': [{'name': 'complete', 'count': 4, 'median': '2.5', 'p90': '4',
                    'small_sample': True},
                   {'name': 'partial', 'count': 0, 'median': None, 'p90': None,
                    'small_sample': True}],
        'exclusions': [{'id': 'observation-1', 'reason': 'late'},
                       {'id': 'observation-2', 'reason': 'conflict'}],
        'contributors': [{'id': 'contributor-1', 'amount': '1'},
                         {'id': 'contributor-2', 'amount': '2'}],
        'terms': [{'id': 'term-1', 'amount': '0.015'},
                  {'id': 'term-2', 'amount': '0.015'}],
        'totals': {'total_cost': '0.03', 'derived_sum': '3', 'total': '0.03', 'sum_count': '3'},
        'late_data': ['observation-1'], 'identity_conflicts': ['observation-2'],
        'unpriced': ['model-unknown'],
    }


def render(value):
    if exports is None:
        raise AssertionError('report exports implementation is missing')
    return exports.render_exports(value)


class ExportTests(unittest.TestCase):
    def test_json_csv_markdown_preserve_report_semantics(self):
        data = report()
        result = render(data)
        self.assertEqual(set(result), {'json', 'csv', 'markdown'})
        decoded = json.loads(result['json'])
        self.assertEqual(decoded['schema_version'], 1)
        self.assertEqual(decoded['corpus_id'], data['corpus_id'])
        self.assertEqual(decoded['scenario_id'], data['scenario_id'])
        self.assertEqual(decoded['as_of'], data['as_of'])
        self.assertEqual(decoded['versions'], data['versions'])
        csv_rows = list(csv.DictReader(io.StringIO(result['csv'], newline='')))
        self.assertTrue(csv_rows)
        self.assertEqual(set(csv_rows[0]), {'path', 'value'})
        csv_data = {row['path']: json.loads(row['value']) for row in csv_rows}
        for path, expected in [('corpus_id', data['corpus_id']),
                               ('scenario_id', data['scenario_id']),
                               ('as_of', data['as_of']),
                               ('completeness/inventory', 'complete'),
                               ('completeness/pricing', 'not_applicable')]:
            self.assertEqual(csv_data[path], expected)
        for marker in ('observation-1', 'observation-2', 'late', 'conflict',
                       'model-unknown', 'contributor-1', 'term-1', '0.015',
                       '2.5', 'USD', 'measured', 'unknown'):
            for name in ('json', 'csv', 'markdown'):
                with self.subTest(marker=marker, format=name):
                    self.assertIn(marker, result[name])

    def test_exact_decimal_strings_and_unknown_are_not_rounded_or_filled(self):
        result = render(report())
        parsed = json.loads(result['json'])
        metrics = {item['name']: item for item in parsed['metrics']}
        self.assertEqual(metrics['cost']['value'], '0.0000000000000000000123')
        self.assertEqual(metrics['input_tokens']['value'], '123456789012345678901234567890')
        self.assertEqual(metrics['output_tokens']['value'], '0')
        self.assertIsNone(metrics['quality']['value'])
        rows = list(csv.DictReader(io.StringIO(result['csv'], newline='')))
        values = [json.loads(row['value']) for row in rows]
        for value in ('0.0000000000000000000123', '123456789012345678901234567890', '0', None):
            self.assertIn(value, values)

    def test_input_sets_are_order_independent_without_mutation(self):
        first = report()
        original = copy.deepcopy(first)
        second = copy.deepcopy(first)
        for name in ('metrics', 'groups', 'exclusions', 'contributors', 'terms',
                     'late_data', 'identity_conflicts', 'unpriced'):
            second[name].reverse()
        self.assertEqual(render(first), render(second))
        self.assertEqual(first, original)

    def test_csv_rejects_formula_and_private_paths_without_publishing_them(self):
        for dangerous in ('=1+1', '+1', '-2', '@SUM(A1)', '\t=1+1',
                          '\r=1+1', '/private/path', 'secret/path'):
            item = report()
            item['contributors'][0]['id'] = dangerous
            with self.subTest(value=dangerous), self.assertRaises(ValueError):
                render(item)

    def test_closed_report_shape_and_header_reject_private_data(self):
        value = report()
        self.assertTrue(render(value))
        for field in value:
            item = copy.deepcopy(value)
            del item[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                render(item)
        for field in ('prompt', 'raw_content', 'local_path'):
            item = copy.deepcopy(value)
            item[field] = '/private/secret'
            with self.subTest(field=field):
                with self.assertRaises(ValueError) as error:
                    render(item)
                self.assertNotIn('/private/secret', str(error.exception))
        for collection in ('metrics', 'groups', 'exclusions', 'contributors', 'terms'):
            item = copy.deepcopy(value)
            item[collection][0]['prompt'] = 'secret content'
            with self.subTest(collection=collection):
                with self.assertRaises(ValueError) as error:
                    render(item)
                self.assertNotIn('secret content', str(error.exception))
        for field, bad in [('corpus_id', 'not-a-hash'), ('source_hash', 'x' * 64),
                           ('expanded_hash', '/private/path'), ('scenario_id', '/tmp/file'),
                           ('as_of', '2026-99-99T03:04:05Z'), ('as_of', '2026-01-02')]:
            item = copy.deepcopy(value)
            item[field] = bad
            with self.subTest(field=field, value=bad), self.assertRaises(ValueError):
                render(item)

    def test_every_derived_total_is_a_canonical_decimal_string(self):
        value = report()
        result = json.loads(render(value)['json'])
        self.assertEqual(result['totals'], value['totals'])
        for field, bad in [('total_cost', '1e6'), ('derived_sum', '+5'),
                           ('total', '01.00'), ('sum_count', 5),
                           ('total_cost', '1.0'), ('total', '-0')]:
            item = copy.deepcopy(value)
            item['totals'][field] = bad
            with self.subTest(field=field, value=bad), self.assertRaises(ValueError):
                render(item)

    def test_all_scalar_values_survive_all_three_formats(self):
        result = render(report())
        decoded = json.loads(result['json'])
        expected = dict(exports._rows(decoded))
        csv_rows = list(csv.DictReader(io.StringIO(result['csv'], newline='')))
        self.assertEqual({row['path']: json.loads(row['value']) for row in csv_rows}, expected)
        lines = result['markdown'].splitlines()[4:]
        cells = [line[2:-2].split(' | ', 1) for line in lines]
        self.assertEqual(len(cells), len(expected))
        for path, value in cells:
            self.assertEqual(json.loads(value), expected[path])

    def test_fractional_utc_timestamps_and_five_completeness_dimensions(self):
        value = report()
        value['as_of'] = '2026-01-02T03:04:05.123456789Z'
        result = render(value)
        decoded = json.loads(result['json'])
        self.assertEqual(decoded['as_of'], value['as_of'])
        self.assertEqual(decoded['completeness'], value['completeness'])
        rows = list(csv.DictReader(io.StringIO(result['csv'], newline='')))
        fields = {row['path']: json.loads(row['value']) for row in rows}
        for name, status in value['completeness'].items():
            self.assertEqual(fields['completeness/' + name], status)
            self.assertIn('completeness/' + name, result['markdown'])
            self.assertIn(status, result['markdown'])
        for axis in value['completeness']:
            bad = copy.deepcopy(value)
            del bad['completeness'][axis]
            with self.subTest(missing=axis), self.assertRaises(ValueError):
                render(bad)
        bad = copy.deepcopy(value)
        bad['completeness']['pricing'] = 'invented'
        with self.assertRaises(ValueError):
            render(bad)

    def test_archive_is_deterministic_and_contains_all_formats(self):
        import tarfile
        artifacts = render(report())
        encoded = exports.archive_exports(artifacts)
        self.assertEqual(encoded, exports.archive_exports(artifacts))
        with tarfile.open(fileobj=io.BytesIO(encoded)) as archive:
            self.assertEqual(set(archive.getnames()), {'report.json', 'report.csv', 'report.md'})
            for key, name in exports._FILES.items():
                self.assertEqual(archive.extractfile(name).read().decode(), artifacts[key])

    def test_render_does_not_read_history_or_use_network(self):
        with (patch('socket.create_connection', side_effect=AssertionError('network')),
              patch('pathlib.Path.open', side_effect=AssertionError('implicit read'))):
            self.assertTrue(render(report()))


if __name__ == '__main__':
    unittest.main()
