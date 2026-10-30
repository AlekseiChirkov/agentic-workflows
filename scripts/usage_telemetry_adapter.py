"""Normalize explicitly selected source records without retaining their payloads.

The caller must independently establish the profile's provenance, applicability,
privacy, and the authorized owner scope. Opaque identifiers are derived with a
private key; the key and selection are never included in the returned result.
"""
import copy
import hashlib
import hmac
import json
import math

import usage_telemetry_sources as sources
from usage_telemetry_contract import (
    content_id, normalize_source_counters, observation_id, validate_source_profile,
    validate_resolution_context, validate_source_selection, validate_usage_bundle,
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


def _resolution_context(record, observation, profile, key, verifier, prior):
    """Extract only fields named by a verified, explicitly supplied profile."""
    mapping = profile.get('resolution_fields', {})
    if mapping.get('status') != 'verified' or not callable(verifier):
        return None
    def read(path):
        value = record
        for part in path:
            if not isinstance(value, dict) or part not in value:
                raise ValueError('required source field is unavailable')
            value = value[part]
        return value
    def read_optional(path):
        try:
            return read(path)
        except ValueError:
            return None
    try:
        identities = {}
        for name in ('response_id', 'call_id', 'session_id'):
            raw = read(mapping[name])
            if not isinstance(raw, str) or not raw or len(raw.encode('utf-8')) > 4096:
                raise ValueError('invalid source identity')
            identities[name] = _opaque(key, name, raw)
        execution_time = read_optional(mapping['execution_time'])
        event_mapping = mapping['finality']
        if event_mapping['kind'] == 'snapshot':
            status = read(event_mapping['path'])
            if type(status) is not bool:
                raise ValueError('source finality unavailable')
            event = {'kind': 'snapshot', 'final': status == event_mapping['final_value']}
        else:
            raw_kind = read(event_mapping['kind_path'])
            choices = {source: target for target, source in event_mapping['kinds'].items()}
            kind = choices.get(raw_kind) if isinstance(raw_kind, str) else None
            if kind is None:
                raise ValueError('unknown source event')
            sequence = read(event_mapping['sequence_path'])
            if type(sequence) is not int or sequence < 1:
                raise ValueError('source sequence unavailable')
            event = {'kind': kind, 'sequence': sequence}
            if kind == 'snapshot':
                status = read(event_mapping['final_path'])
                if type(status) is not bool:
                    raise ValueError('source finality unavailable')
                event['final'] = status
                predecessor = read_optional(event_mapping['correction_record_path'])
                if predecessor is not None:
                    if type(predecessor) is not int or predecessor not in prior:
                        raise ValueError('source correction unavailable')
                    original = prior[predecessor]
                    if original['response_id'] != identities['response_id'] or original['call_id'] != identities['call_id']:
                        raise ValueError('source correction identity mismatch')
                    event['correction_of'] = original['observation_id']
            elif read_optional(event_mapping['correction_record_path']) is not None:
                raise ValueError('invalid source correction')
        if (event['kind'] == 'delta' and observation['counter_scope'] != 'incremental_delta' or
                event['kind'] == 'snapshot' and observation['counter_scope'] != 'response_total'):
            raise ValueError('source event scope mismatch')
        parameters = {name: read_optional(path) for name, path in mapping['parameters'].items()}
        scope = {name: observation[name] for name in ('profile_id', 'source_hash', 'record_number')}
        proofs = []
        if execution_time is not None:
            proofs.append({'schema_version': 1, 'kind': 'execution_time_evidence', **scope,
                           'value': execution_time})
        proofs.extend({'schema_version': 1, 'kind': 'source_parameter_evidence', **scope,
                       'field': name, 'value': value} for name, value in parameters.items() if value is not None)
        proofs.extend({'schema_version': 1, 'kind': 'rate_parameter_evidence', **scope,
                       'field': 'cache_ttl_seconds', 'value': seconds}
                      for seconds in mapping['cache_ttl_seconds'].values())
        # Build and validate a detached copy before exposing any metadata.
        candidate = dict(observation, response_id=identities['response_id'], call_id=identities['call_id'])
        context = {'observation_id': observation_id(candidate), 'profile_id': profile['profile_id'],
                   'profile_version': profile['profile_version'], 'source_hash': observation['source_hash'],
                   'record_number': observation['record_number'], 'provider_scope': observation['provider_scope'],
                   'counter_scope': observation['counter_scope'], 'provider': profile['provider'],
                   'session_id': identities['session_id'],
                   'event': event,
                   'execution_time': execution_time, 'parameters': parameters,
                   'cache_ttl_seconds': dict(mapping['cache_ttl_seconds']), 'evidence_objects': proofs}
        validate_resolution_context(context)
        # A syntactically safe value or a digest cannot establish privacy or
        # provenance. The caller independently authorizes every exact binding.
        for proof in proofs:
            if proof['kind'] == 'source_parameter_evidence':
                if verifier('parameter', copy.deepcopy(profile), copy.deepcopy(candidate), copy.deepcopy(proof)) is not True:
                    return None
        if verifier('context', copy.deepcopy(profile), copy.deepcopy(candidate), copy.deepcopy(context)) is not True:
            return None
        observation.update(response_id=identities['response_id'], call_id=identities['call_id'])
        return context
    except Exception:
        return None


def normalize_selection(selection, *, profile, expected_owner_scope, project_identifier,
                        provider_identifier, run_id, key, verify_resolution=None, epoch_coverages=None):
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
    if epoch_coverages is None:
        epoch_coverages = []
    if not isinstance(epoch_coverages, list) or len(epoch_coverages) > 10000:
        raise ValueError('invalid epoch coverages')
    if epoch_coverages and len(selection['sources']) != 1:
        raise ValueError('epoch coverage requires one explicitly selected source')
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
    contexts = []
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
        prior = {}
        epoch_records = {}
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
                # Finality belongs to each exact counter, not the stream event.
                # Preserve partial values unless an independent authority verifies
                # that measurement's finality for this source record.
                if observation['counter_scope'] == 'response_total' and callable(verify_resolution):
                    for field, value in observation['measurements'].items():
                        parts = [(part['ttl'], part['tokens']) for part in value] if isinstance(value, list) else [(None, value)]
                        for ttl, measurement in parts:
                            if measurement.get('measurement_state') != 'partial':
                                continue
                            declaration = {'field': field, 'measurement': copy.deepcopy(measurement)}
                            if ttl is not None:
                                declaration['ttl'] = ttl
                            try:
                                accepted = verify_resolution('measurement_finality', copy.deepcopy(profile),
                                                             copy.deepcopy(observation), declaration) is True
                            except Exception:
                                accepted = False
                            if accepted:
                                measurement['measurement_state'] = 'final'
                context = _resolution_context(record, observation, profile, key, verify_resolution, prior)
                # Check record-specific output bounds before accepting siblings.
                from usage_telemetry_contract import validate_observation
                validate_observation(observation)
                bundle['observations'].append(observation)
                epoch_mapping = profile.get('epoch_fields', {})
                if (epoch_mapping.get('status') == 'verified' and callable(verify_resolution) and
                        observation['counter_scope'] == 'cumulative_epoch' and not source['partial']):
                    try:
                        def epoch_read(path):
                            result = record
                            for part in path:
                                result = result[part]
                            return result
                        raw_epoch = epoch_read(epoch_mapping['epoch'])
                        model = epoch_read(epoch_mapping['model'])
                        if (not isinstance(raw_epoch, str) or not raw_epoch or len(raw_epoch.encode('utf-8')) > 4096 or
                                not isinstance(model, str) or not model or len(model) > 256):
                            raise ValueError('invalid epoch identity')
                        measurement = observation['measurements']['input_uncached']
                        snapshot = {'provider': profile['provider'], 'account': observation['provider_scope'],
                                    'model': model, 'units': 'input_uncached_tokens',
                                    'epoch': _opaque(key, 'epoch', raw_epoch),
                                    'sequence': epoch_read(epoch_mapping['sequence']),
                                    'position': epoch_read(epoch_mapping['position']), 'value': measurement['value']}
                        for field in ('sequence', 'position', 'value'):
                            from usage_telemetry_contract import validate_counter
                            validate_counter(snapshot[field])
                        if verify_resolution('epoch_snapshot', copy.deepcopy(profile), copy.deepcopy(observation),
                                             copy.deepcopy(snapshot)) is True:
                            epoch_records[number] = (copy.deepcopy(observation), snapshot,
                                                     copy.deepcopy(converted['evidence_objects']))
                    except Exception:
                        pass
                if context is not None:
                    prior[number] = {'observation_id': 'sha256:' + context['observation_id'],
                                     'response_id': observation['response_id'], 'call_id': observation['call_id']}
                    contexts.append(context)
                    wrapper = {'schema_version': 1, 'kind': 'resolution_context_evidence', 'context': context}
                    evidence[content_id(wrapper)] = wrapper
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
        if epoch_records and callable(verify_resolution):
            for coverage in epoch_coverages:
                try:
                    from usage_telemetry_contract import _fields, validate_counter, validate_evidence_object
                    _fields(coverage, {'before_record', 'after_record', 'coverage'})
                    before_number = validate_counter(coverage['before_record'])
                    after_number = validate_counter(coverage['after_record'])
                    if before_number >= after_number or before_number not in epoch_records or after_number not in epoch_records:
                        continue
                    before, after = epoch_records[before_number], epoch_records[after_number]
                    observations = [before[0], after[0]]
                    try:
                        accepted = verify_resolution('epoch_coverage', copy.deepcopy(profile),
                                                     copy.deepcopy(observations), copy.deepcopy(coverage)) is True
                    except Exception:
                        accepted = False
                    if not accepted:
                        continue
                    objects = {content_id(item): item for item in before[2] + after[2]}
                    pack = {'profile': copy.deepcopy(profile), 'observations': observations,
                            'evidence_objects': list(objects.values()),
                            'interval': {'before': before[1], 'after': after[1],
                                         'coverage': copy.deepcopy(coverage['coverage'])},
                            'observed_at': selection['observed_at']}
                    try:
                        privacy_accepted = verify_resolution('epoch_privacy', copy.deepcopy(profile),
                                                             copy.deepcopy(observations), copy.deepcopy(pack)) is True
                    except Exception:
                        privacy_accepted = False
                    if not privacy_accepted:
                        continue
                    wrapper = {'schema_version': 1, 'kind': 'epoch_interval_evidence', 'pack': pack}
                    validate_evidence_object(wrapper)
                    evidence[content_id(wrapper)] = wrapper
                except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
                    continue
    bundle['evidence_objects'] = list(evidence.values())
    validate_usage_bundle(bundle)
    return {'bundle': bundle, 'partial': partial, 'quarantine': quarantine, 'contexts': contexts}
