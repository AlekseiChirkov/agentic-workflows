#!/usr/bin/env python3
"""Resolve explicitly evidenced, offline price applicability.

The caller supplies an independently verified evidence trust set. Hashes identify
content but do not prove its provenance. This module does not read sources,
retrieve prices, or calculate monetary amounts.
"""
from pathlib import Path
import importlib.util

_spec = importlib.util.spec_from_file_location(
    'usage_telemetry_contract', Path(__file__).with_name('usage_telemetry_contract.py'))
_contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_contract)


def _unpriced(reason):
    return {'state': 'unpriced', 'reason': reason}


def _evidence(items, trusted, identity, kind):
    if identity not in trusted:
        return None
    item = items.get(identity)
    if item is None or item.get('kind') != kind:
        return None
    return item


def _validate_applicability_evidence(item):
    """Validate structure without making an authenticity claim."""
    _contract.validate_evidence_object(item)


def _work_parameter(items, trusted, declaration, field, request):
    if not isinstance(declaration, dict) or set(declaration) != {'value', 'evidence'}:
        return None
    item = _evidence(items, trusted, declaration['evidence'], 'rate_parameter_evidence')
    if (item is None or item['field'] != field or item['value'] != declaration['value'] or
            any(item[key] != request[key] for key in ('profile_id', 'source_hash', 'record_number'))):
        return None
    return item['value']


def _source_evidence(items, trusted, declaration, field, request):
    if not isinstance(declaration, dict) or set(declaration) != {'value', 'evidence'}:
        return None
    item = _evidence(items, trusted, declaration['evidence'], 'source_parameter_evidence')
    if (item is None or item['field'] != field or item['value'] != declaration['value'] or
            any(item[key] != request[key] for key in ('profile_id', 'source_hash', 'record_number'))):
        return None
    return item['value']


def _measure(items, trusted, declaration, field, request):
    if not isinstance(declaration, dict) or set(declaration) != {'value', 'evidence'}:
        return None
    item = _evidence(items, trusted, declaration['evidence'], 'measurement_evidence')
    if item is None:
        item = _evidence(items, trusted, declaration['evidence'], 'derived_measurement_evidence')
    if (item is None or item['field'] != field or item['value'] != declaration['value'] or
            any(item[key] != request[key] for key in ('profile_id', 'source_hash', 'record_number'))):
        return None
    value = item['value']
    if type(value) is int:
        return value
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        return int(value)
    return None


def _threshold_state(rule, request, items, trusted):
    value = _measure(items, trusted, request['operands'].get(rule['operand']), rule['operand'], request)
    if value is None:
        return None
    return value > rule['value'] if rule['operator'] == '>' else value >= rule['value']


def select_rate(snapshots, scenario, request, evidence_objects, trusted_evidence_ids):
    """Return a unique supported rate, or an unpriced reason.

    `trusted_evidence_ids` must be established by the caller independently of
    these objects. An alias additionally requires a verified alias declaration
    in the request, with its evidence identifier in that trust set. Operand
    evidence is scoped to the same record as execution and source parameters.
    A reprice result is always marked conditional.
    """
    try:
        return _select_rate(snapshots, scenario, request, evidence_objects, trusted_evidence_ids)
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError):
        return _unpriced('invalid_or_unverified_input')


def _select_rate(snapshots, scenario, request, evidence_objects, trusted_evidence_ids):
    _contract.validate_pricing_scenario(scenario)
    if not isinstance(snapshots, list) or not snapshots or len(snapshots) > 10000:
        return _unpriced('invalid_snapshots')
    identities = [_contract.price_snapshot_id(snapshot) for snapshot in snapshots]
    if len(set(identities)) != len(identities) or set(identities) != set(scenario['snapshot_ids']):
        return _unpriced('snapshot_mismatch')
    if not isinstance(evidence_objects, list) or len(evidence_objects) > 10000:
        return _unpriced('invalid_evidence')
    trusted = set(trusted_evidence_ids)
    items = {}
    for item in evidence_objects:
        _validate_applicability_evidence(item)
        identity = _contract.content_id(item)
        if identity in items:
            return _unpriced('duplicate_evidence')
        items[identity] = item
    required = {'component', 'unit', 'cache_ttl_seconds', 'tool_id', 'execution_time',
                'profile_id', 'source_hash', 'record_number', 'operands', 'verified_aliases'}
    if not isinstance(request, dict) or set(request) != required:
        return _unpriced('invalid_request')
    execution = request['execution_time']
    if not isinstance(execution, dict) or set(execution) != {'value', 'evidence'}:
        return _unpriced('execution_time_unavailable')
    time_evidence = _evidence(items, trusted, execution['evidence'], 'execution_time_evidence')
    if (time_evidence is None or time_evidence['value'] != execution['value'] or
            any(time_evidence[key] != request[key] for key in ('profile_id', 'source_hash', 'record_number'))):
        return _unpriced('execution_time_unavailable')
    selected = {}
    for field in ('model', 'service_tier', 'region', 'modality'):
        assumption = scenario['assumptions'].get(field)
        if assumption is not None:
            selected[field] = assumption
        else:
            selected[field] = _source_evidence(items, trusted, scenario['source_parameters'][field], field, request)
        if selected[field] is None:
            return _unpriced('source_parameter_unavailable')
    if not isinstance(request['operands'], dict) or not isinstance(request['verified_aliases'], list):
        return _unpriced('invalid_request')
    component = request['component']
    rules = [rule for rule in scenario['threshold_rules'] if component in rule['components']]
    if len(rules) > 1:
        return _unpriced('ambiguous_threshold')
    if rules:
        hit = _threshold_state(rules[0], request, items, trusted)
        if hit is None:
            return _unpriced('threshold_operand_unavailable')
    else:
        hit = False
    candidates = []
    possible_unknown = False
    for snapshot in snapshots:
        snapshot_id = _contract.price_snapshot_id(snapshot)
        model = snapshot['model']
        if selected['model'] != model:
            alias = next((item for item in snapshot['aliases'] if item['alias'] == selected['model']), None)
            if alias is None:
                continue
            declaration = {'alias': selected['model'], 'model': model, 'evidence': alias['evidence']}
            if declaration not in request['verified_aliases'] or alias['evidence'] not in trusted:
                possible_unknown = True
                continue
        different = False
        unknown = False
        for field in ('service_tier', 'region', 'modality'):
            if snapshot[field] is None:
                unknown = True
            elif selected[field] != snapshot[field]:
                different = True
        if different:
            continue
        bindings = [item for digest, item in items.items()
                    if digest in trusted and item.get('kind') == 'price_snapshot_evidence'
                    and item['snapshot_id'] == snapshot_id]
        if len(bindings) != 1:
            unknown = True
        period = snapshot['effective_period']
        if scenario['basis'] == 'at_execution':
            if period['state'] == 'unknown':
                unknown = True
            else:
                proof = _evidence(items, trusted, period['evidence'], 'price_period_evidence')
                if (proof is None or proof['start'] != period['start'] or proof['end'] != period['end'] or
                        len(bindings) != 1 or proof['source_hash'] != bindings[0]['source_hash']):
                    unknown = True
                elif not (_contract._instant(period['start']) <= _contract._instant(execution['value']) < _contract._instant(period['end'])):
                    continue
        applicable = []
        for rate in snapshot['rates']:
            if rate['component'] != component or rate['unit'] != request['unit']:
                continue
            if component == 'input_cache_write':
                ttl = _work_parameter(items, trusted, request['cache_ttl_seconds'], 'cache_ttl_seconds', request)
                if ttl is None or rate['cache_ttl_seconds'] is None:
                    unknown = True
                    continue
                if rate['cache_ttl_seconds'] != ttl:
                    continue
            elif rate['cache_ttl_seconds'] is not None:
                continue
            if component == 'tool':
                tool_id = _work_parameter(items, trusted, request['tool_id'], 'tool_id', request)
                if tool_id is None or 'tool_id' not in rate:
                    unknown = True
                    continue
                if tool_id != rate['tool_id']:
                    continue
            threshold = rate['threshold']
            if threshold is not None:
                if not rules or any(threshold[key] != rules[0][key] for key in ('operand', 'operator', 'value')):
                    unknown = True
                    continue
                if not hit:
                    continue
            elif rules and hit:
                continue
            multiplier = rate.get('multiplier')
            if multiplier is None or multiplier['state'] == 'unknown':
                unknown = True
                continue
            if multiplier['state'] == 'none':
                factor = '1'
            else:
                multiplier_proofs = [item for digest, item in items.items()
                                     if digest in trusted and item.get('kind') == 'multiplier_evidence'
                                     and item['snapshot_id'] == snapshot_id
                                     and item['rate_id'] == _contract.content_id(rate)
                                     and item['scope'] == multiplier['scope']
                                     and item['factor'] == multiplier['factor']
                                     and all(item[key] == request[key] for key in ('profile_id', 'source_hash', 'record_number'))]
                if len(multiplier_proofs) != 1:
                    unknown = True
                    continue
                factor = multiplier['factor'] if multiplier_proofs[0]['applies'] else '1'
            applicable.append((rate, factor))
        if unknown:
            possible_unknown = True
        candidates.extend(applicable)
    if possible_unknown or len(candidates) != 1:
        return _unpriced('rate_unavailable_or_ambiguous')
    rate, factor = candidates[0]
    return {'state': 'priced', 'rate': rate, 'factor': factor, 'conditional': scenario['basis'] == 'reprice'}
