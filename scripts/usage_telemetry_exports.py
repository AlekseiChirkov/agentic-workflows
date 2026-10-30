"""Deterministic offline renderers for already computed retrospective reports."""
from __future__ import annotations

import ctypes
import errno
import csv
import datetime
import io
import json
import os
from pathlib import Path
import re
import secrets
import stat

_SET_FIELDS = frozenset(('metrics', 'groups', 'exclusions', 'contributors', 'terms',
                         'late_data', 'identity_conflicts', 'unpriced', 'durations', 'diagnostics',
                         'slices', 'unavailable_dimensions', 'partial_leaves'))
_KEY = re.compile(r'[a-z][a-z0-9_]*\Z')
_DECIMAL = re.compile(r'(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?\Z')
_FILES = {'json': 'report.json', 'csv': 'report.csv', 'markdown': 'report.md'}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _normalize(value, field=None):
    if isinstance(value, dict):
        if any(not isinstance(key, str) or not _KEY.fullmatch(key) for key in value):
            raise ValueError('invalid report field')
        return {key: _normalize(item, key) for key, item in value.items()}
    if isinstance(value, list):
        items = [_normalize(item) for item in value]
        if field in _SET_FIELDS:
            items.sort(key=lambda item: _json(item).encode('utf-8'))
        return items
    if value is None or isinstance(value, (str, bool)):
        return value
    if (type(value) is int and value >= 0 and field is not None
            and (field in ('schema_version', 'count', 'n')
                 or field in ('numerator', 'denominator')
                 or field.endswith(('_count', '_version')))):
        return value
    raise ValueError('invalid report value')


def _shape(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError('invalid report structure')


def _label(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', value):
        raise ValueError('invalid report identifier')


def _decimal(value, nullable=False):
    if value is None and nullable:
        return
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value):
        raise ValueError('report amounts must be canonical decimal strings')


def _validate(value):
    fields = ('schema_version', 'kind', 'corpus_id', 'scenario_id', 'as_of',
              'versions', 'source_hash', 'expanded_hash', 'completeness',
              'metrics', 'groups', 'exclusions', 'contributors', 'terms',
              'totals', 'late_data', 'identity_conflicts', 'unpriced')
    optional = tuple(name for name in ('coverage', 'pricing', 'outcomes', 'durations', 'slices',
                                       'unavailable_dimensions', 'top_leaves', 'partial_leaves') if name in value)
    _shape(value, fields + optional)
    for field in ('top_leaves', 'partial_leaves'):
        if field in value:
            if not isinstance(value[field], list) or (field == 'top_leaves' and len(value[field]) > 5):
                raise ValueError('invalid owner collection')
            for row in value[field]:
                _shape(row, ('owner_id', 'cost_usd', 'coverage', 'conditional') if 'conditional' in row
                       else ('owner_id', 'cost_usd', 'coverage'))
                if 'conditional' in row and type(row['conditional']) is not bool:
                    raise ValueError('invalid conditional owner cost')
                if not isinstance(row['owner_id'], str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', row['owner_id']):
                    raise ValueError('invalid owner identifier')
                _decimal(row['cost_usd'], nullable=True)
                if row['coverage'] not in ('complete', 'proven_lower_bound', 'subtotal_only'):
                    raise ValueError('invalid owner coverage')
    if 'unavailable_dimensions' in value:
        if not isinstance(value['unavailable_dimensions'], list):
            raise ValueError('invalid unavailable dimensions')
        for dimension in value['unavailable_dimensions']:
            _label(dimension)
    if 'slices' in value:
        if not isinstance(value['slices'], list):
            raise ValueError('invalid cost slices')
        for row in value['slices']:
            fields = ('dimension', 'value', 'count', 'cost_usd', 'coverage')
            if row.get('dimension') != 'model':
                fields += ('request_count', 'retry_count', 'escalation_count', 'wall_ms',
                           'input_uncached_tokens', 'input_cache_read_tokens', 'input_cache_write_tokens',
                           'output_tokens', 'reasoning_tokens')
            if 'conditional' in row:
                fields += ('conditional',)
            _shape(row, fields)
            if 'conditional' in row and type(row['conditional']) is not bool:
                raise ValueError('invalid conditional cost slice')
            _label(row['dimension'])
            if (not isinstance(row['value'], str) or not
                    (re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.\-/]{0,127}', row['value']) or
                     re.fullmatch(r'sha256:[0-9a-f]{64}', row['value']))):
                raise ValueError('invalid slice value')
            if type(row['count']) is not int or row['count'] < 0:
                raise ValueError('invalid slice count')
            _decimal(row['cost_usd'], nullable=True)
            if row['dimension'] != 'model':
                for field in ('request_count', 'retry_count', 'escalation_count'):
                    if row[field] is not None and (type(row[field]) is not int or row[field] < 0):
                        raise ValueError('invalid slice count')
                for field in ('wall_ms', 'input_uncached_tokens', 'input_cache_read_tokens',
                              'input_cache_write_tokens', 'output_tokens', 'reasoning_tokens'):
                    _decimal(row[field], nullable=True)
            if row['coverage'] not in ('complete', 'proven_lower_bound', 'subtotal_only'):
                raise ValueError('invalid slice coverage')
    if 'outcomes' in value:
        summary = value['outcomes']
        fields = ('opportunity_count', 'accepted_count', 'observed_workload_cost',
                         'experimental_evaluation_cost', 'combined_cost', 'combined_coverage',
                         'cost_per_accepted', 'coverage', 'ratio_quality', 'diagnostics')
        _shape(summary, fields + (('conditional',) if 'conditional' in summary else ()))
        if 'conditional' in summary and type(summary['conditional']) is not bool:
            raise ValueError('invalid conditional outcome')
        for field in ('opportunity_count', 'accepted_count'):
            if type(summary[field]) is not int or summary[field] < 0:
                raise ValueError('invalid outcome count')
        if summary['accepted_count'] > summary['opportunity_count']:
            raise ValueError('invalid acceptance count')
        for field in ('observed_workload_cost', 'experimental_evaluation_cost', 'combined_cost'):
            _decimal(summary[field], nullable=True)
        ratio = summary['cost_per_accepted']
        if ratio is not None and not (_DECIMAL.fullmatch(ratio) or
                re.fullmatch(r'(?:0|[1-9][0-9]*)/[1-9][0-9]*', ratio)):
            raise ValueError('invalid accepted cost')
        if summary['coverage'] not in ('complete', 'incomplete') or summary['combined_coverage'] not in (None, 'complete', 'incomplete'):
            raise ValueError('invalid outcome coverage')
        if summary['ratio_quality'] not in ('complete', 'descriptive_incomplete', 'unavailable'):
            raise ValueError('invalid outcome quality')
        if not isinstance(summary['diagnostics'], list):
            raise ValueError('invalid outcome diagnostics')
        for item in summary['diagnostics']:
            _label(item)
    if 'durations' in value:
        if not isinstance(value['durations'], list):
            raise ValueError('invalid duration collection')
        for item in value['durations']:
            _shape(item, ('group', 'wall_ms', 'worker_sum_ms', 'coverage_ms', 'exclusive_ms',
                          'coverage_complete', 'unit', 'diagnostics'))
            _label(item['group'])
            if item['unit'] != 'ms' or type(item['coverage_complete']) is not bool:
                raise ValueError('invalid duration metadata')
            for field in ('wall_ms', 'worker_sum_ms', 'coverage_ms', 'exclusive_ms'):
                amount = item[field]
                if amount is not None and (not isinstance(amount, str) or
                                           re.fullmatch(r'(?:0|[1-9][0-9]*)', amount) is None):
                    raise ValueError('invalid duration amount')
            if not isinstance(item['diagnostics'], list):
                raise ValueError('invalid duration diagnostics')
            for diagnostic in item['diagnostics']:
                _label(diagnostic)
    if 'pricing' in value:
        _shape(value['pricing'], ('priced_subtotal_cost', 'subtotal_quality', 'conditional')
               if 'conditional' in value['pricing'] else ('priced_subtotal_cost', 'subtotal_quality'))
        if 'conditional' in value['pricing'] and type(value['pricing']['conditional']) is not bool:
            raise ValueError('invalid conditional pricing')
        _decimal(value['pricing']['priced_subtotal_cost'], nullable=True)
        if value['pricing']['subtotal_quality'] not in ('unavailable', 'complete', 'proven_lower_bound', 'subtotal_only'):
            raise ValueError('invalid subtotal quality')
    if 'coverage' in value:
        _shape(value['coverage'], ('measurements', 'pricing'))
        for measure in value['coverage'].values():
            _shape(measure, ('numerator', 'denominator'))
            for count in measure.values():
                if count is not None and (type(count) is not int or count < 0):
                    raise ValueError('invalid coverage count')
            if (measure['denominator'] is not None and measure['numerator'] is not None
                    and measure['numerator'] > measure['denominator']):
                raise ValueError('coverage exceeds denominator')
    if type(value['schema_version']) is not int or value['schema_version'] != 1 or value['kind'] != 'retrospective_report':
        raise ValueError('invalid report version')
    if not isinstance(value['corpus_id'], str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', value['corpus_id']):
        raise ValueError('invalid corpus identifier')
    _label(value['scenario_id'])
    for field in ('source_hash', 'expanded_hash'):
        if value[field] is not None and (not isinstance(value[field], str) or not re.fullmatch(r'[0-9a-f]{64}', value[field])):
            raise ValueError('invalid revision hash')
    stamp = value['as_of']
    if not isinstance(stamp, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z', stamp) or len(stamp) > 256:
        raise ValueError('invalid report timestamp')
    try:
        datetime.datetime.fromisoformat(stamp[:-1] + '+00:00')
    except ValueError:
        raise ValueError('invalid report timestamp') from None
    _shape(value['versions'], ('normalizer', 'prices'))
    for version in value['versions'].values():
        _label(version)
    _shape(value['completeness'], ('inventory', 'identity', 'measurements', 'pricing', 'attribution'))
    if any(status not in ('complete', 'partial', 'unknown', 'not_applicable')
           for status in value['completeness'].values()):
        raise ValueError('invalid completeness')
    for field in ('metrics', 'groups', 'exclusions', 'contributors', 'terms',
                  'late_data', 'identity_conflicts', 'unpriced'):
        if not isinstance(value[field], list):
            raise ValueError('invalid report collection')
    for metric in value['metrics']:
        _shape(metric, ('name', 'value', 'unit', 'scope', 'source', 'quality'))
        for key in ('name', 'unit', 'scope', 'quality'):
            _label(metric[key])
        if metric['source'] is not None:
            _label(metric['source'])
        _decimal(metric['value'], nullable=True)
    for group in value['groups']:
        _shape(group, ('name', 'count', 'median', 'p90', 'small_sample'))
        _label(group['name'])
        if type(group['count']) is not int or group['count'] < 0 or type(group['small_sample']) is not bool:
            raise ValueError('invalid report sample')
        _decimal(group['median'], nullable=True)
        _decimal(group['p90'], nullable=True)
    for exclusion in value['exclusions']:
        _shape(exclusion, ('id', 'reason'))
        _label(exclusion['id'])
        _label(exclusion['reason'])
    for field in ('contributors', 'terms'):
        for entry in value[field]:
            _shape(entry, ('id', 'amount', 'conditional') if 'conditional' in entry else ('id', 'amount'))
            if 'conditional' in entry and type(entry['conditional']) is not bool:
                raise ValueError('invalid conditional term')
            _label(entry['id'])
            _decimal(entry['amount'], nullable=True)
    _shape(value['totals'], ('total_cost', 'derived_sum', 'total', 'sum_count'))
    for amount in value['totals'].values():
        _decimal(amount, nullable=True)
    for field in ('late_data', 'identity_conflicts', 'unpriced'):
        for entry in value[field]:
            _label(entry)


def _rows(value, path=''):
    if isinstance(value, dict):
        if not value and path:
            yield path, {}
        for key in sorted(value):
            yield from _rows(value[key], f'{path}/{key}' if path else key)
    elif isinstance(value, list):
        if not value:
            yield path, []
        for index, item in enumerate(value):
            yield from _rows(item, f'{path}/{index}')
    else:
        yield path, value


def render_exports(report):
    """Return equivalent JSON, CSV and Markdown strings without I/O.

    CSV cells contain JSON scalars, so text round-trips exactly and spreadsheet
    applications do not interpret formula-like text as an executable formula.
    """
    value = _normalize(report)
    if (not isinstance(value, dict) or type(value.get('schema_version')) is not int
            or value.get('schema_version') != 1
            or value.get('kind') != 'retrospective_report'
            or not all(key in value for key in ('corpus_id', 'scenario_id', 'as_of'))):
        raise ValueError('invalid report header')
    _validate(value)
    rows = list(_rows(value))
    csv_buffer = io.StringIO(newline='')
    writer = csv.writer(csv_buffer, lineterminator='\n')
    writer.writerow(('path', 'value'))
    writer.writerows((path, _json(item)) for path, item in rows)
    markdown = ['# Retrospective report', '', '| Field | Value (JSON) |', '| --- | --- |']
    for path, item in rows:
        encoded = _json(item).replace('\\', '\\\\').replace('|', '\\|').replace('`', '\\`')
        markdown.append(f'| {path} | {encoded} |')
    return {'json': _json(value) + '\n', 'csv': csv_buffer.getvalue(),
            'markdown': '\n'.join(markdown) + '\n'}


def archive_exports(artifacts):
    """Return a deterministic tar archive for delivery through a pipe or socket."""
    import tarfile
    if set(artifacts) != set(_FILES) or any(not isinstance(x, str) for x in artifacts.values()):
        raise ValueError('invalid export artifacts')
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for key, name in _FILES.items():
            data = artifacts[key].encode('utf-8')
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            entry.mode = 0o600
            entry.mtime = 0
            archive.addfile(entry, io.BytesIO(data))
    return output.getvalue()
