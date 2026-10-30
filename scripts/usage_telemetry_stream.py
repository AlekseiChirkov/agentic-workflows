"""Resolve one already verified response's usage stream without side effects.

The caller must independently verify the response identity, profile, evidence,
source order and correction links before constructing these bounded records.
This module does not verify provider provenance or establish shared identity.
"""
import re

MAX_EVENTS = 10000
MAX_COUNTER = 9007199254740991
_OPAQUE = re.compile(r'sha256:[0-9a-f]{64}\Z')


def _invalid():
    raise ValueError('invalid stream event')


def _event(event):
    if not isinstance(event, dict):
        _invalid()
    kind = event.get('kind')
    required = {'response_id', 'observation_id', 'kind'}
    optional = set()
    if kind == 'snapshot':
        required |= {'value', 'final'}
        optional = {'sequence', 'correction_of', 'correction_verified'}
    elif kind == 'delta':
        required |= {'value', 'sequence'}
    elif kind == 'terminal':
        required |= {'sequence'}
    else:
        _invalid()
    if not required <= event.keys() or event.keys() - required - optional:
        _invalid()
    for field in ('response_id', 'observation_id'):
        if not isinstance(event[field], str) or not _OPAQUE.fullmatch(event[field]):
            _invalid()
    if 'value' in event and (type(event['value']) is not int or
                             not 0 <= event['value'] <= MAX_COUNTER):
        _invalid()
    if 'sequence' in event and (type(event['sequence']) is not int or
                                not 1 <= event['sequence'] <= MAX_COUNTER):
        _invalid()
    if kind == 'snapshot' and type(event['final']) is not bool:
        _invalid()
    if ('correction_of' in event) != ('correction_verified' in event):
        _invalid()
    if 'correction_of' in event:
        if (not event['final'] or not isinstance(event['correction_of'], str) or
                not _OPAQUE.fullmatch(event['correction_of']) or
                type(event['correction_verified']) is not bool):
            _invalid()
    return event


def _result(state, value=None, reason=None):
    result = {'measurement_state': state, 'reasons': [reason] if reason else []}
    if value is not None:
        result['value'] = value
    return result


def _conflict():
    return _result('conflicted', reason='revision_conflict')


def _final_snapshot(snapshots):
    finals = {item['observation_id']: item for item in snapshots if item['final']}
    if not finals:
        return None
    children = {}
    for identity, item in finals.items():
        if 'correction_of' not in item:
            continue
        parent = item['correction_of']
        if not item['correction_verified'] or parent not in finals or parent == identity:
            return _conflict()
        if ('sequence' in item and 'sequence' in finals[parent] and
                item['sequence'] <= finals[parent]['sequence']):
            return _conflict()
        if parent in children and children[parent] != identity:
            return _conflict()
        children[parent] = identity
    roots = [identity for identity, item in finals.items() if 'correction_of' not in item]
    if not roots:
        return _conflict()
    # Different independently recorded, equal final snapshots are consistent;
    # distinct correction trees or unequal finals have no proven replacement.
    if len(roots) != 1:
        if children or len({item['value'] for item in finals.values()}) != 1:
            return _conflict()
        return _result('final', next(iter(finals.values()))['value'])
    seen = set()
    current = roots[0]
    while current in children:
        if current in seen:
            return _conflict()
        seen.add(current)
        current = children[current]
    seen.add(current)
    if len(seen) != len(finals):
        return _conflict()
    return _result('final', finals[current]['value'])


def resolve_stream(events):
    """Resolve a bounded collection of sanitized events for one response.

    Sequence numbers represent verified source order, beginning at one. A
    correction flag is trusted only as a caller-supplied verification result;
    it is not a substitute for validating the provider's evidence.
    """
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        _invalid()
    if not events:
        return _result('unavailable', reason='stream_incomplete')
    unique = {}
    response = None
    for raw in events:
        item = _event(raw)
        if response is None:
            response = item['response_id']
        elif response != item['response_id']:
            _invalid()
        identity = item['observation_id']
        if identity in unique and unique[identity] != item:
            return _conflict()
        unique[identity] = item
    snapshots = [item for item in unique.values() if item['kind'] == 'snapshot']
    deltas = [item for item in unique.values() if item['kind'] == 'delta']
    terminals = [item for item in unique.values() if item['kind'] == 'terminal']
    numbers = {}
    for item in deltas:
        number = item['sequence']
        if number in numbers and numbers[number] != item['value']:
            return _conflict()
        numbers[number] = item['value']
    terminal_numbers = {item['sequence'] for item in terminals}
    if len(terminal_numbers) > 1 or any(number in numbers for number in terminal_numbers):
        return _conflict()
    final = _final_snapshot(snapshots)
    if final is not None:
        if final['measurement_state'] == 'final':
            numbered_finals = [item['sequence'] for item in snapshots if item['final'] and 'sequence' in item]
            if numbered_finals:
                latest_final = max(numbered_finals)
                later_partial = any(not item['final'] and item.get('sequence', 0) > latest_final
                                    for item in snapshots)
                later_delta = any(item['sequence'] > latest_final for item in deltas)
                if later_partial or later_delta:
                    return _result('partial', reason='stream_incomplete')
        return final
    if snapshots and numbers:
        # Partial snapshots and increments do not establish a common basis.
        return _result('partial', reason='stream_incomplete')
    if numbers:
        total = sum(numbers.values())
        terminal_number = next(iter(terminal_numbers), None)
        if (terminal_number is not None and len(numbers) == terminal_number - 1 and
                min(numbers) == 1 and max(numbers) == terminal_number - 1):
            return _result('final', total)
        return _result('partial', total, 'stream_incomplete')
    if snapshots:
        if any('sequence' not in item for item in snapshots):
            if len(snapshots) == 1:
                return _result('partial', snapshots[0]['value'], 'stream_incomplete')
            return _result('partial', reason='stream_incomplete')
        latest = max(item['sequence'] for item in snapshots)
        latest_values = {item['value'] for item in snapshots if item['sequence'] == latest}
        if len(latest_values) != 1:
            return _conflict()
        return _result('partial', latest_values.pop(), 'stream_incomplete')
    return _result('unavailable', reason='stream_incomplete')
