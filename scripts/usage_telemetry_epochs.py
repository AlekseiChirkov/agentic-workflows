"""Resolve verified cumulative intervals without inferring missing usage.

Callers must independently verify the provenance, completeness and scope of every
input assertion. This module performs consistency checks only; it does not read
sources or authenticate evidence. Aggregate totals remain separate from request
accounting and must not be added to overlapping response totals.
"""

_MAX_INTEGER = (1 << 63) - 1
_MAX_ITEMS = 10000
_IDENTITY_FIELDS = ('provider', 'account', 'model', 'units', 'epoch')


def _number(value):
    return type(value) is int and 0 <= value <= _MAX_INTEGER


def _identity(value):
    return (isinstance(value, dict) and all(
        isinstance(value.get(field), str) and bool(value[field])
        for field in _IDENTITY_FIELDS
    ))


def resolve_interval(value):
    """Return a delta only for adjacent, fully inventoried verified snapshots.

    ``coverage`` contains caller-verified evidence, including the complete
    request inventory and whether either boundary lies inside unfinished usage.
    Atomic completion is a caller-verified profile property, not a deduction
    from monotonicity. Unknown or contradictory values remain unavailable.
    """
    unavailable = {'request_usage': {}, 'interval_aggregate': None}
    if not isinstance(value, dict):
        return unavailable
    before, after, coverage = value.get('before'), value.get('after'), value.get('coverage')
    if not _identity(before) or not _identity(after) or not isinstance(coverage, dict):
        return unavailable
    if any(before[field] != after[field] for field in _IDENTITY_FIELDS):
        return unavailable
    if not all(_number(snapshot.get(field)) for snapshot in (before, after)
               for field in ('sequence', 'position', 'value')):
        return unavailable
    if (after['sequence'] != before['sequence'] + 1
            or after['position'] <= before['position']
            or after['value'] < before['value']
            or coverage.get('complete') is not True):
        return unavailable
    requests = coverage.get('requests')
    if not isinstance(requests, list) or len(requests) > _MAX_ITEMS:
        return unavailable
    delta = after['value'] - before['value']
    result = {'request_usage': {}, 'interval_aggregate': delta}
    if len(requests) != 1 or not isinstance(requests[0], dict):
        return result
    request = requests[0]
    request_id, start, end = request.get('id'), request.get('start'), request.get('end')
    if not isinstance(request_id, str) or not request_id or not _number(start) or not _number(end):
        return result
    if start > end or end <= before['position'] or end > after['position']:
        return result
    enclosed = (coverage.get('before_clear') is True and coverage.get('after_clear') is True
                and before['position'] <= start and end <= after['position'])
    atomic = coverage.get('atomic_on_completion') is True
    if enclosed or atomic:
        result['request_usage'] = {request_id: delta}
    return result


def aggregate_intervals(items):
    """Summarize proven, mutually nonoverlapping intervals as a separate total.

    Duplicate identical entries are counted once. Conflicting IDs, unknown
    boundaries, mixed identities and overlaps are retained for reconciliation.
    An empty or wholly unresolved set has an unavailable total, never zero.
    """
    result = {'total': None, 'included_ids': [], 'reconciliation_ids': [],
              'complete_request_accounting': False}
    if not isinstance(items, list) or len(items) > _MAX_ITEMS:
        return result
    unique = {}
    conflicts = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id']:
            return result
        item_id = item['id']
        if item_id in unique and unique[item_id] != item:
            conflicts.add(item_id)
        else:
            unique[item_id] = item
    candidates = []
    reconciliation = set(conflicts)
    for item_id, item in unique.items():
        if (item_id in conflicts or not _identity(item) or item.get('boundaries_proven') is not True
                or not _number(item.get('start')) or not _number(item.get('end'))
                or item['start'] >= item['end'] or not _number(item.get('value'))):
            reconciliation.add(item_id)
        else:
            candidates.append(item)
    identities = {tuple(item[field] for field in _IDENTITY_FIELDS) for item in candidates}
    if len(identities) > 1:
        reconciliation.update(item['id'] for item in candidates)
        candidates = []
    ordered = sorted(candidates, key=lambda item: (item['start'], item['end'], item['id']))
    farthest = None
    for item in ordered:
        if farthest is not None and item['start'] < farthest['end']:
            reconciliation.add(item['id'])
            reconciliation.add(farthest['id'])
        if farthest is None or item['end'] > farthest['end']:
            farthest = item
    included = [item for item in ordered if item['id'] not in reconciliation]
    total = sum(item['value'] for item in included)
    if included:
        result['total'] = total
        result['included_ids'] = sorted(item['id'] for item in included)
    else:
        reconciliation.update(item['id'] for item in included)
    result['reconciliation_ids'] = sorted(reconciliation)
    return result
