#!/usr/bin/env python3
"""Propose owner-scoped collection boundaries without side effects.

The caller must independently establish authorization and profile validity.
This module does not load history, persist proposals, or publish usage.
"""
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location('usage_telemetry_contract',
                                Path(__file__).with_name('usage_telemetry_contract.py'))
_contract = module_from_spec(_spec)
_spec.loader.exec_module(_contract)


def transition_collection(snapshot, mode, when, *, authorized, profile_verified):
    """Return a validated snapshot proposal and its collection decision.

    ``authorized`` and ``profile_verified`` are caller-supplied decisions, not
    proofs. The owner controls persistence and validates provenance separately.
    """
    _contract.validate_current_run_snapshot(snapshot)
    _contract._timestamp(when)
    if type(authorized) is not bool or type(profile_verified) is not bool:
        raise ValueError('invalid collection authorization')
    if mode is not None and not isinstance(mode, str):
        raise ValueError('invalid collection mode')

    segments = snapshot['segments']
    ids = [item['segment_id'] for item in segments]
    if len(ids) != len(set(ids)):
        raise ValueError('conflicting collection segment identities')
    opened = [item for item in segments if item['end'] is None]
    if len(opened) > 1 or any(item['mode'] != 'on' for item in opened):
        raise ValueError('ambiguous open collection segment')
    if snapshot['mode'] == 'off' and opened:
        raise ValueError('disabled collection has an open segment')
    if snapshot['mode'] == 'on' and len(opened) != 1:
        raise ValueError('active collection has no open segment')
    ordered = sorted(segments, key=lambda item: (
        _contract._instant(item['start']), item['end'] is None,
        _contract._instant(item['end']) if item['end'] is not None else ('', '')))
    for previous, current in zip(ordered, ordered[1:]):
        if previous['end'] is None or _contract._instant(previous['end']) > _contract._instant(current['start']):
            raise ValueError('overlapping collection segments')
    boundary = _contract._instant(when)
    for item in segments:
        if _contract._instant(item['start']) > boundary or (
                item['end'] is not None and _contract._instant(item['end']) > boundary):
            raise ValueError('collection boundary precedes existing segment')

    invalid = mode not in (None, 'on', 'off')
    allowed = mode == 'on' and authorized and profile_verified
    desired = 'on' if allowed else 'off'
    if invalid:
        reason = 'invalid_collection_mode'
    elif mode == 'on' and not (authorized and profile_verified):
        reason = 'collection_not_authorized'
    elif desired == 'off':
        reason = 'collection_disabled'
    else:
        reason = None
    if desired == snapshot['mode']:
        return {'snapshot': deepcopy(snapshot), 'reason': reason, 'changed': False}

    proposal = deepcopy(snapshot)
    proposal['mode'] = desired
    proposal['revision'] += 1
    if desired == 'off':
        if opened:
            segment_id = opened[0]['segment_id']
            next(item for item in proposal['segments'] if item['segment_id'] == segment_id)['end'] = when
    else:
        closed = [item for item in segments
                  if item['mode'] == 'on' and item['end'] is not None]
        if closed:
            last = max(closed, key=lambda item: _contract._instant(item['end']))
            gap = {'state': 'present', 'start': last['end'], 'end': when}
        else:
            gap = {'state': 'unknown', 'start': None, 'end': None}
        identity = {'owner_scope': proposal['owner_scope'], 'start': when,
                    'previous_segments': sorted(item['segment_id'] for item in segments)}
        segment = {'schema_version': 1, 'kind': 'collection_segment',
                   'segment_id': 'sha256:' + _contract.content_id(identity),
                   'owner_scope': deepcopy(proposal['owner_scope']), 'mode': 'on',
                   'start': when, 'end': None, 'gap_before': gap}
        proposal['segments'].append(segment)
    _contract.validate_current_run_snapshot(proposal)
    return {'snapshot': proposal, 'reason': reason, 'changed': True}
