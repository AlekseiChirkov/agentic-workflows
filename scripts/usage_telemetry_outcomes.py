#!/usr/bin/env python3
"""Pure calculations over explicitly selected, independently verified outcomes.

The caller supplies an independent acceptance verifier and is responsible for
verifying workload provenance, price applicability, and completeness before
calling this module. No files or historical records are discovered here.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
import re

_IDENTITY = ('task_revision', 'input_revision', 'acceptance_contract', 'strategy', 'repetition')
_DECIMAL = re.compile(r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z')


def _identity(value):
    if not isinstance(value, dict) or set(value) != set(_IDENTITY):
        raise ValueError('invalid opportunity identity')
    parts = tuple(value[key] for key in _IDENTITY)
    if any(not isinstance(item, str) or not item for item in parts[:-1]):
        raise ValueError('invalid opportunity identity')
    if not isinstance(parts[-1], int) or isinstance(parts[-1], bool) or parts[-1] < 1:
        raise ValueError('invalid repetition')
    return parts


def _amount(value, *, max_length=256):
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value) or len(value) > max_length:
        raise ValueError('invalid decimal amount')
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('invalid decimal amount') from exc


def _text(value):
    if not value:
        return '0'
    return format(value, 'f').rstrip('0').rstrip('.') if '.' in format(value, 'f') else format(value, 'f')


def _ratio_text(numerator, denominator):
    """Use a reduced fraction when no finite decimal representation exists."""
    value = Fraction(numerator) / denominator
    rest = value.denominator
    powers = []
    for factor in (2, 5):
        count = 0
        while rest % factor == 0:
            rest //= factor
            count += 1
        powers.append(count)
    if rest != 1:
        return f'{value.numerator}/{value.denominator}'
    scale = max(powers)
    digits = str(value.numerator * 2 ** (scale - powers[0]) * 5 ** (scale - powers[1]))
    if not scale:
        return digits
    digits = digits.zfill(scale + 1)
    return (digits[:-scale] + '.' + digits[-scale:]).rstrip('0').rstrip('.')


def _comparison_amount(value):
    if isinstance(value, str) and '/' in value:
        parts = value.split('/')
        if (len(parts) != 2 or not all(part.isascii() and part.isdigit() and
                                       len(part) <= 512 for part in parts)
                or int(parts[1]) == 0):
            raise ValueError('invalid rational amount')
        return Fraction(int(parts[0]), int(parts[1]))
    return Fraction(_amount(value, max_length=512))


def _time(value):
    if not isinstance(value, str) or not value.endswith('Z'):
        raise ValueError('expected UTC timestamp')
    try:
        result = datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError as exc:
        raise ValueError('invalid timestamp') from exc
    if result.tzinfo != timezone.utc:
        raise ValueError('expected UTC timestamp')
    return result


def summarize_outcomes(attempts, labels, *, as_of, verify_acceptance,
                       include_experimental=False, opportunities=None):
    """Summarize observed work and independently validated acceptance revisions."""
    if not isinstance(attempts, list) or not isinstance(labels, list):
        raise ValueError('attempts and labels must be lists')
    if not callable(verify_acceptance) or not isinstance(include_experimental, bool):
        raise ValueError('invalid verifier or combined option')
    cutoff = _time(as_of)
    unique = {}
    if opportunities is not None and not isinstance(opportunities, list):
        raise ValueError('invalid opportunities')
    identities = {_identity(item) for item in (opportunities or [])}
    attempted_identities = set()
    complete = True
    experimental_complete = True
    workload = Decimal(0)
    experimental = Decimal(0)
    # Ensure addition is exact even when differently scaled amounts are combined.
    with localcontext() as context:
        context.prec = 1024 + len(str(len(attempts)))
        for item in attempts:
            if not isinstance(item, dict):
                raise ValueError('invalid attempt')
            if _time(item.get('observed_at')) > cutoff:
                continue
            identifier = item.get('attempt_id')
            if not isinstance(identifier, str) or not identifier:
                raise ValueError('invalid attempt identifier')
            if identifier in unique:
                if item != unique[identifier]:
                    raise ValueError('conflicting attempt identifier')
                continue
            unique[identifier] = item
            identity = _identity(item.get('opportunity'))
            category = item.get('category')
            if category not in ('workload', 'production_verification', 'experimental_evaluation'):
                raise ValueError('invalid attempt category')
            if not isinstance(item.get('complete'), bool):
                raise ValueError('invalid completeness')
            if category != 'experimental_evaluation':
                identities.add(identity)
                attempted_identities.add(identity)
                complete = complete and item['complete'] and item.get('cost') is not None
            else:
                experimental_complete = experimental_complete and item['complete'] and item.get('cost') is not None
            cost = item.get('cost')
            if cost is not None:
                if category == 'experimental_evaluation':
                    experimental += _amount(cost)
                else:
                    workload += _amount(cost)
        latest = {}
        seen_revisions = {}
        for label in labels:
            if not isinstance(label, dict):
                raise ValueError('invalid acceptance revision')
            identity = _identity(label.get('opportunity'))
            timestamp = _time(label.get('observed_at'))
            if timestamp > cutoff or identity not in identities:
                continue
            if label.get('acceptance_contract') != identity[2]:
                continue
            revision = label.get('revision')
            if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
                raise ValueError('invalid acceptance revision')
            if label.get('status') not in ('accepted', 'rejected', 'defect'):
                raise ValueError('invalid acceptance status')
            # Verification must be supplied by the caller's independent boundary;
            # a field in an untrusted label does not establish independence.
            try:
                verified = verify_acceptance(dict(label)) is True
            except Exception:
                verified = False
            if not verified:
                continue
            revision_key = (identity, revision)
            prior_revision = seen_revisions.get(revision_key)
            if prior_revision is not None and label != prior_revision:
                raise ValueError('conflicting acceptance revisions')
            seen_revisions[revision_key] = label
            previous = latest.get(identity)
            if previous is None or revision > previous['revision']:
                latest[identity] = label
        complete = complete and not (identities - attempted_identities)
        accepted = sum(label['status'] == 'accepted' for label in latest.values())
        diagnostics = [] if accepted else ['accepted_denominator_zero']
        ratio = _ratio_text(workload, accepted) if accepted else None
        return {'opportunity_count': len(identities), 'accepted_count': accepted,
                'observed_workload_cost': _text(workload),
                'experimental_evaluation_cost': _text(experimental),
                'combined_cost': _text(workload + experimental) if include_experimental else None,
                'combined_coverage': ('complete' if complete and experimental_complete else 'incomplete') if include_experimental else None,
                'cost_per_accepted': ratio,
                'coverage': 'complete' if complete else 'incomplete',
                'ratio_quality': ('complete' if complete else 'descriptive_incomplete') if accepted else 'unavailable',
                'diagnostics': diagnostics}


def compare_outcome_groups(left, right):
    """Compare only compatible root-level groups with complete independent quality."""
    dimensions = ('task_revision', 'input_revision', 'acceptance_contract',
                  'repetitions', 'quality_policy', 'price_basis')
    eligible = isinstance(left, dict) and isinstance(right, dict)
    if eligible:
        eligible = all(left.get(key) is not None and left.get(key) == right.get(key)
                       for key in dimensions)
        eligible = eligible and all(group.get('scope') == 'root'
                                    and group.get('coverage') == 'complete'
                                    and group.get('independent_quality') is True
                                    and group.get('cost_per_accepted') is not None
                                    for group in (left, right))
    if eligible:
        try:
            first, second = _comparison_amount(left['cost_per_accepted']), _comparison_amount(right['cost_per_accepted'])
        except ValueError:
            eligible = False
    if not eligible:
        return {'winner': None, 'diagnostics': ['comparison_ineligible']}
    return {'winner': 'left' if first < second else 'right' if second < first else None,
            'diagnostics': []}
