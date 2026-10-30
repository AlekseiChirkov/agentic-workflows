#!/usr/bin/env python3
"""Calculate exact statistics for separately classified observations."""

from decimal import Decimal, MAX_EMAX, MIN_EMIN, localcontext
import re

_COVERAGE = ('complete', 'proven_lower_bound', 'subtotal_only', 'unavailable')
_DECIMAL = re.compile(r'(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?\Z', re.ASCII)


def _canonical(value):
    text = format(value, 'f')
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    return text


def calculate_group_statistics(records, *, max_records):
    """Return exact distributions, excluding unavailable values and mixed coverage.

    The caller chooses comparable records and supplies the explicit record bound.
    Each record has only a coverage class and a canonical decimal string or null.
    """
    if (not isinstance(records, list) or type(max_records) is not int or
            max_records < 0 or len(records) > max_records):
        raise ValueError('invalid records or record limit')
    groups = {coverage: [] for coverage in _COVERAGE}
    whole_digits = 1
    fractional_digits = 0
    for record in records:
        if type(record) is not dict or set(record) != {'coverage', 'value'}:
            raise ValueError('invalid record')
        coverage, value = record['coverage'], record['value']
        if type(coverage) is not str or coverage not in groups:
            raise ValueError('invalid coverage')
        if coverage == 'unavailable':
            if value is not None:
                raise ValueError('invalid unavailable value')
            groups[coverage].append(None)
            continue
        if type(value) is not str or not _DECIMAL.fullmatch(value):
            raise ValueError('invalid decimal value')
        whole, _, fraction = value.partition('.')
        whole_digits = max(whole_digits, len(whole))
        fractional_digits = max(fractional_digits, len(fraction))
        groups[coverage].append(Decimal(value))

    result = {}
    for coverage, values in groups.items():
        count = len(values)
        median = p90 = None
        if count and coverage != 'unavailable':
            values.sort()
            middle = count // 2
            if count % 2:
                median = _canonical(values[middle])
            else:
                # A carry in the sum and a final half digit both need space.
                with localcontext() as context:
                    context.prec = whole_digits + fractional_digits + 3
                    context.Emax = MAX_EMAX
                    context.Emin = MIN_EMIN
                    median = _canonical((values[middle - 1] + values[middle]) / 2)
            p90 = _canonical(values[(9 * count + 9) // 10 - 1])
        result[coverage] = {
            'n': count, 'median': median, 'p90': p90,
            'small_sample': count < 5,
        }
    return result
