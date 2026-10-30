"""Normalize explicitly selected source records without retaining their payloads.

The caller must independently establish the profile's provenance, applicability,
privacy, and the authorized owner scope. Opaque identifiers are derived with a
private key; the key and selection are never included in the returned result.
"""
import hashlib
import hmac
import json
import math

import usage_telemetry_sources as sources
from usage_telemetry_contract import (
    content_id, normalize_source_counters, validate_source_profile,
    validate_source_selection, validate_usage_bundle,
)


def _opaque(key, domain, value):
    encoded = value.encode('utf-8')
    digest = hmac.new(key, b'usage-telemetry-v1\0' + domain.encode('ascii') + b'\0' + encoded,
                      hashlib.sha256).hexdigest()
    return 'sha256:' + digest


class _RecordLimit(ValueError):
    """A source record exceeded a structural or byte limit."""


def _check_tree(value, depth=0):
    if depth > 32:
        raise _RecordLimit('source record depth exceeds limit')
    if isinstance(value, dict):
        if len(value) > 256:
            raise _RecordLimit('source record keys exceed limit')
        for child in value.values():
            _check_tree(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _check_tree(child, depth + 1)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError('invalid source record number')


def _record(line):
    if len(line) > sources.RECORD_LIMIT:
        raise _RecordLimit('source record exceeds limit')
    try:
        result = json.loads(line.decode('utf-8'), object_pairs_hook=sources._unique_pairs,
                            parse_constant=sources._invalid_constant)
        _check_tree(result)
        if not isinstance(result, dict):
            raise ValueError('invalid source record')
        return result
    except RecursionError:
        raise _RecordLimit('source record depth exceeds limit') from None
    except _RecordLimit:
        raise
    except (ValueError, UnicodeError):
        raise ValueError('invalid source record') from None


def normalize_selection(selection, *, profile, expected_owner_scope, project_identifier,
                        provider_identifier, run_id, key):
    """Return sanitized bundle and bounded quarantine for a fixed local selection.

    Trusted callers supply an independently verified profile and private mapping
    key. Source, project, provider and candidate identifiers are domain-separated
    keyed digests, not evidence of ownership or profile authenticity.
    """
    validate_source_profile(profile)
    validate_source_selection(selection)
    if (not isinstance(key, bytes) or len(key) < 32 or
            not isinstance(project_identifier, str) or not project_identifier or
            not isinstance(provider_identifier, str) or not provider_identifier):
        raise ValueError('invalid private identity material')
    scopes = {field['counter_scope'] for field in profile['counter_fields']}
    if len(scopes) != 1:
        raise ValueError('profile counter scopes cannot be combined')
    selected = sources.read_selected_sources(
        selection, expected_profile=(profile['profile_id'], profile['profile_version']),
        expected_owner_scope=expected_owner_scope)
    source_entries = {item['source_id']: item for item in selection['sources']}
    mappings = {item['source_id']: item for item in selection['attribution_map']}
    bundle = {'schema_version': 1, 'kind': 'usage_bundle',
              'profile_id': profile['profile_id'], 'profile_version': profile['profile_version'],
              'project_id': _opaque(key, 'project', project_identifier), 'run_id': run_id,
              'sources': [], 'observations': [], 'evidence_objects': [],
              'inventories': [], 'segments': [], 'diagnostics': []}
    quarantine = []
    partial = False
    record_count = 0
    evidence = {}
    for source in selected:
        entry = source_entries[source['source_id']]
        mapped_id = _opaque(key, 'source', source['source_id'])
        bundle['sources'].append({'source_id': mapped_id, 'sha256': entry['sha256']})
        mapping = mappings[source['source_id']]
        attribution = {'owner_kind': mapping['owner_kind'],
                       'quality': 'asserted' if mapping['quality'] == 'verified' else mapping['quality'],
                       'candidates': [_opaque(key, 'owner-candidate', value)
                                      for value in mapping['candidates']]}
        partial |= source['partial']
        if source['partial']:
            bundle['diagnostics'].append({
                'schema_version': 1, 'kind': 'source_issue', 'source_id': mapped_id,
                'source_hash': entry['sha256'], 'record_number': None,
                'reason': 'incomplete_source', 'completeness': 'partial',
            })
        for number, line in enumerate(source['data'].splitlines(), 1):
            if not line.strip():
                continue
            record_count += 1
            if record_count > selection['max_records']:
                raise ValueError('source record limit exceeded')
            try:
                record = _record(line)
                converted = normalize_source_counters(
                    profile, record, profile_version=selection['profile_version'],
                    source_hash=entry['sha256'], record_number=number)
                observation = {'schema_version': 1, 'kind': 'request_usage',
                               'profile_id': profile['profile_id'],
                               'profile_version': profile['profile_version'],
                               'source_hash': entry['sha256'], 'record_number': number,
                               'counter_scope': next(iter(scopes)),
                               'provider_scope': _opaque(key, 'provider-account', provider_identifier),
                               'source_time': None, 'source_time_quality': 'unknown',
                               'observed_at': selection['observed_at'], 'state': 'partial',
                               'outcome': 'unknown', 'attribution': attribution,
                               'measurements': converted['measurements']}
                # Check record-specific output bounds before accepting siblings.
                from usage_telemetry_contract import validate_observation
                validate_observation(observation)
                bundle['observations'].append(observation)
                for item in converted['evidence_objects']:
                    evidence[content_id(item)] = item
            except (ValueError, UnicodeError, RecursionError, OverflowError) as error:
                reason = 'input_limit_exceeded' if isinstance(error, (_RecordLimit, RecursionError)) else 'source_record_quarantined'
                quarantine.append({'source_id': mapped_id, 'record_number': number,
                                   'reason': reason})
                bundle['diagnostics'].append({
                    'schema_version': 1, 'kind': 'source_issue', 'source_id': mapped_id,
                    'source_hash': entry['sha256'], 'record_number': number,
                    'reason': reason, 'completeness': 'partial',
                })
                partial = True
    bundle['evidence_objects'] = list(evidence.values())
    validate_usage_bundle(bundle)
    return {'bundle': bundle, 'partial': partial, 'quarantine': quarantine}
