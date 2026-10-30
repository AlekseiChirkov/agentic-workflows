"""Pure current-owner threshold episode evaluation.

The measurement adapter is deliberately fail-closed until connected to the
verified retrospective evaluator. Status never reads history or writes state.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib
import re
import sys
from fractions import Fraction

sys.path.insert(0, str(Path(__file__).resolve().parent))
import usage_telemetry_contract as contract
import usage_telemetry_resolution as resolution
import usage_telemetry_exact_cost as exact_cost
import usage_telemetry_duration_warning as duration_warning


def _evaluate_snapshot(snapshot, *, analysis_inputs=None, verifier=None, observed_at=None):
    """Resolve a selected owner using only explicit, independently authorized facts."""
    owner = snapshot['owner_scope']
    result = {'scope': owner, 'metrics': {}}
    selected = analysis_inputs if analysis_inputs is not None else snapshot.get('analysis_inputs')
    if snapshot.get('parts') or snapshot.get('part_references'):
        return result
    if selected is None or not callable(verifier):
        return result
    bundles = snapshot['bundles']
    receipts = snapshot['accepted_receipts']
    if not bundles or not receipts:
        return result
    try:
        by_digest = {contract.content_id(item): item for item in bundles}
        for receipt in receipts:
            accepted = by_digest.get(receipt['bundle_sha256'])
            if accepted is None or not resolution._authorized(verifier, 'receipt', owner, receipt, accepted):
                return result
        base = bundles[0]
        if any(any(item[key] != base[key] for key in ('profile_id', 'profile_version', 'project_id', 'run_id'))
               for item in bundles):
            return result
        bundle = deepcopy(base)
        for name in ('sources', 'observations', 'evidence_objects', 'inventories', 'segments', 'diagnostics'):
            unique = {}
            for item in bundles:
                for member in item[name]:
                    key = contract.canonical_bytes(member)
                    unique[key] = member
            bundle[name] = list(unique.values())
        source_ids = {}
        for source in bundle['sources']:
            if source['source_id'] in source_ids and source_ids[source['source_id']] != source:
                return result
            source_ids[source['source_id']] = source
        inventories = [item for item in bundle['inventories'] if item['owner_scope'] == owner]
        if len(inventories) != 1:
            return result
        contract.validate_usage_bundle(bundle)
        owners = {item['observation_id']: item for item in selected['ownership_evidence']}
        for observation in bundle['observations']:
            proof = owners.get(contract.observation_id(observation))
            if proof is None or resolution._authorized(verifier, 'ownership', owner, observation, proof) is not True:
                return result
        report = resolution.resolve_usage(bundle=bundle, profile=selected['profile'],
                    contexts=selected['contexts'], snapshots=selected['snapshots'],
                    scenario=selected['scenario'], price_evidence=selected['price_evidence'],
                    scope=owner, as_of=observed_at, verifier=verifier)
    except (ValueError, KeyError, TypeError, OverflowError, RecursionError):
        return result
    scoped = {}
    for response in report.get('responses', []):
        response_proofs = [owners.get(identity[7:]) for identity in response.get('observation_ids', [])]
        if not response_proofs or any(proof is None for proof in response_proofs):
            continue
        targets = [proof.get('target_scope') for proof in response_proofs]
        if not targets[0] or any(target != targets[0] for target in targets):
            continue
        target = targets[0]
        if target['owner_kind'] == 'span':
            if any(not proof.get('completion') or
                   contract._instant(proof['completion']['observed_at']) > contract._instant(observed_at) or
                   not resolution._authorized(verifier, 'scope_completion', owner, target, proof['completion'])
                   for proof in response_proofs):
                continue
        key = (target['owner_kind'], target['owner_id'])
        entry = scoped.setdefault(key, {'scope': target, 'owner_scope': owner, 'membership': 'verified',
                                        'quantities': [], 'costs': []})
        quantities = [response['tokens'].get(name, {}) for name in ('input', 'output')]
        if all(item.get('quality') == 'complete' and isinstance(item.get('value'), str) and
               re.fullmatch(r'(?:0|[1-9][0-9]*)', item['value']) and len(item['value']) <= 256
               for item in quantities):
            entry['quantities'].append(sum(int(item['value']) for item in quantities))
        else:
            entry['quantities'].append(None)
        tool_verified = all(proof.get('tool_coverage') and
                            contract._instant(proof['tool_coverage']['observed_at']) <= contract._instant(observed_at) and
                            resolution._authorized(verifier, 'scope_tools_empty', owner, target, proof['tool_coverage'])
                            for proof in response_proofs)
        model_cost = response.get('model_cost', {})
        if tool_verified and 'cost_usd' in model_cost:
            entry['costs'].append(Fraction(model_cost['cost_usd']))
        else:
            entry['costs'].append(None)
    result['scoped_metrics'] = []
    for entry in scoped.values():
        values = entry.pop('quantities')
        costs = entry.pop('costs')
        entry['metrics'] = {}
        if values and all(value is not None for value in values):
            total = sum(values)
            entry['metrics']['tokens'] = {'state': 'proven_lower_bound',
                 'value': total if total <= contract.MAX_COUNTER else str(total), 'unit': 'tokens'}
        if costs and all(value is not None for value in costs):
            total_cost = sum(costs, Fraction(0))
            entry['metrics']['cost_usd'] = {'state': 'proven_lower_bound',
                'value': exact_cost._decimal_string(total_cost), 'unit': 'USD'}
        result['scoped_metrics'].append(entry)
    quantities = [report['tokens'].get(name, {}) for name in ('input', 'output')]
    if all(item.get('quality') in ('complete', 'proven_lower_bound') and
           isinstance(item.get('value'), str) and re.fullmatch(r'(?:0|[1-9][0-9]*)', item['value'])
           and len(item['value']) <= 256 for item in quantities):
        total = sum(int(item['value']) for item in quantities)
        state = 'final' if all(item['quality'] == 'complete' for item in quantities) else 'proven_lower_bound'
        result['metrics']['tokens'] = {'state': state, 'value': total if total <= contract.MAX_COUNTER else str(total),
                                        'unit': 'tokens'}
    cost = report['cost']
    if 'cost_usd' in cost:
        result['metrics']['cost_usd'] = {'state': 'final', 'value': cost['cost_usd'], 'unit': 'USD'}
    elif cost.get('subtotal_quality') == 'proven_lower_bound' and cost.get('priced_subtotal_usd') != '0':
        result['metrics']['cost_usd'] = {'state': 'proven_lower_bound',
                                         'value': cost['priced_subtotal_usd'], 'unit': 'USD'}
    else:
        result['metrics']['cost_usd'] = {'state': 'unpriced', 'value': None, 'unit': 'USD'}
    coverage = report['completeness']['finality']
    numerator, denominator = coverage.get('numerator'), coverage.get('denominator')
    if type(numerator) is int and type(denominator) is int and denominator > 0 and 0 <= numerator <= denominator:
        fraction = Fraction(numerator, denominator)
        value = (exact_cost._decimal_string(fraction) if exact_cost._is_terminating(fraction)
                 else {'numerator': fraction.numerator, 'denominator': fraction.denominator})
        result['metrics']['completeness'] = {'state': 'final', 'value': value, 'unit': 'fraction'}
    return result


def _instant(value):
    contract._timestamp(value)
    return contract._instant(value)


def _numeric(value, metric):
    if metric == 'tokens':
        if isinstance(value, str) and len(value) <= 256 and re.fullmatch(r'(?:0|[1-9][0-9]*)', value):
            return int(value)
        try:
            return contract.validate_counter(value)
        except ValueError:
            return None
    if metric == 'completeness' and isinstance(value, dict):
        if set(value) != {'numerator', 'denominator'}:
            return None
        numerator, denominator = value['numerator'], value['denominator']
        if (type(numerator) is not int or type(denominator) is not int or
                not 0 <= numerator <= denominator or denominator <= 0 or denominator > 10000):
            return None
        return Fraction(numerator, denominator)
    if (not isinstance(value, str) or len(value) > 256 or
            re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?', value) is None):
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    if not number.is_finite() or number < 0:
        return None
    if metric == 'completeness' and number > 1:
        return None
    return number


def _warning_id(owner, policy, scope, metric, episode):
    identity = {'owner_scope': owner, 'policy_id': policy['policy_id'],
                'policy_version': policy['policy_version'], 'scope': scope,
                'metric': metric, 'episode': episode}
    return 'sha256:' + hashlib.sha256(contract.canonical_bytes(identity)).hexdigest()


def _scope_completeness(metrics):
    value = metrics.get('completeness', {})
    return deepcopy(value if value.get('state') == 'final' else
                    {'state': 'unknown', 'value': None, 'unit': 'fraction'})


def _evaluate_duration_status(snapshot, result, observed_at, verifier):
    """Propose distinct duration episodes from independently authorized clocks."""
    entries = snapshot.get('duration_inputs', [])
    owner = snapshot['owner_scope']
    if not entries or owner['owner_kind'] != 'run':
        result['diagnostics'].append('timing_unavailable')
    seen_scopes = set()
    seen_measurements = set()
    if entries:
        result['duration_measurements'] = []
    for entry in entries if owner['owner_kind'] == 'run' else []:
        target = entry.get('scope', owner)
        candidate, evidence, history = entry['candidate'], entry['evidence'], entry['history']
        kind = candidate['group']['duration_kind']
        policy_id = 'duration-fallback' if kind == 'work' else 'duration-run'
        seen_scopes.add((target['owner_kind'], target['owner_id'], policy_id))
        authorized = (callable(verifier) and evidence['clock_source'] != 'unknown'
                      and contract._instant(evidence['observed_at']) <= contract._instant(observed_at)
                      and resolution._authorized(verifier, 'duration', owner, candidate, evidence))
        if history is not None and not (callable(verifier) and
                resolution._authorized(verifier, 'duration_history', owner, candidate, history)):
            history = None
        decision = (duration_warning.evaluate_duration(candidate, history, observed_at) if authorized
                    else {'available': False, 'reason': 'clock_unavailable'})
        proposal = result['proposed_snapshot']
        previous = [item for item in proposal['warning_delivery'] if item['policy_id'] == policy_id
                    and item['policy_version'] == 1 and item['scope'] == target and item['metric'] == 'duration_ms']
        latest = max(previous, key=lambda item: item['episode']) if previous else None
        if not decision.get('available'):
            result['diagnostics'].append('timing_unavailable')
            if latest and latest['crossing_state'] == 'crossed' and latest['delivery_state'] == 'pending':
                result['candidates'].append(deepcopy(latest))
                result['candidate_details'].append({'warning_id': latest['warning_id'], 'measurement_state': 'unknown'})
            continue
        milliseconds = Fraction(candidate['seconds']) * 1000
        if milliseconds.denominator != 1:
            result['diagnostics'].append('timing_unavailable')
            continue
        milliseconds = milliseconds.numerator
        measurement = {'state': 'partial' if decision['approximate'] else 'final',
                'value': milliseconds if milliseconds <= contract.MAX_COUNTER else str(milliseconds), 'unit': 'ms'}
        result['duration_measurements'].append({'scope': deepcopy(target), 'duration_kind': kind,
                                                'measurement': deepcopy(measurement)})
        scope_key = (target['owner_kind'], target['owner_id'])
        duplicate_kind_scope = scope_key in seen_measurements
        seen_measurements.add(scope_key)
        if target == owner:
            if duplicate_kind_scope:
                result['measurements'].pop('duration_ms', None)
            else:
                result['measurements']['duration_ms'] = measurement
        else:
            scoped = next((item for item in result['scoped_measurements'] if item['scope'] == target), None)
            if scoped is None:
                result['scoped_measurements'].append({'scope': deepcopy(target), 'metrics': {'duration_ms': measurement}})
            elif duplicate_kind_scope:
                scoped['metrics'].pop('duration_ms', None)
        before = deepcopy(proposal)
        if decision['warn']:
            if latest is None or latest['crossing_state'] in ('cleared', 'below'):
                episode = latest['episode'] + 1 if latest else 1
                identity_policy = {'policy_id': policy_id, 'policy_version': 1}
                latest = {'warning_id': _warning_id(owner, identity_policy, target, 'duration_ms', episode),
                          'policy_id': policy_id, 'policy_version': 1, 'scope': deepcopy(target),
                          'owner_scope': deepcopy(owner), 'metric': 'duration_ms', 'episode': episode,
                          'crossing_state': 'crossed', 'delivery_state': 'pending',
                          'details': {'measurement': deepcopy(measurement),
                              'threshold': {'state': 'final', 'value': exact_cost._decimal_string(
                                  max(Fraction(7200000), 3000 * duration_warning._eligible_history(history, candidate, observed_at))
                                  if decision['historical'] else Fraction(7200000)), 'unit': 'ms'},
                              'completeness': _scope_completeness(result['measurements'] if target == owner else
                                  next((item['metrics'] for item in result['scoped_measurements']
                                        if item['scope'] == target), {}))}}
                proposal['warning_delivery'].append(latest)
            else:
                latest['crossing_state'] = 'crossed'
        elif latest and latest['crossing_state'] == 'crossed':
            latest['crossing_state'] = 'cleared'
        try:
            contract.validate_current_run_snapshot(proposal)
        except ValueError:
            result['proposed_snapshot'] = before
            result['diagnostics'].append('input_limit_exceeded')
            continue
        if decision['warn'] and latest['delivery_state'] == 'pending':
            result['candidates'].append(deepcopy(latest))
            result['candidate_details'].append({'warning_id': latest['warning_id'],
                    'measurement_state': 'partial' if decision['approximate'] else 'final',
                    'historical': decision['historical'], 'approximate': decision['approximate']})
    latest_missing = {}
    for warning in result['proposed_snapshot']['warning_delivery']:
        if warning['policy_id'] not in ('duration-fallback', 'duration-run') or warning['metric'] != 'duration_ms':
            continue
        key = (warning['scope']['owner_kind'], warning['scope']['owner_id'], warning['policy_id'])
        if key not in seen_scopes and (key not in latest_missing or
                warning['episode'] > latest_missing[key]['episode']):
            latest_missing[key] = warning
    for warning in latest_missing.values():
        if warning['crossing_state'] == 'crossed' and warning['delivery_state'] == 'pending':
            result['candidates'].append(deepcopy(warning))
            result['candidate_details'].append({'warning_id': warning['warning_id'], 'measurement_state': 'unknown'})


def evaluate_status(snapshot, policy, *, observed_at, analysis_inputs=None, verifier=None,
                    _materialized_limit=None, _proposal=None):
    """Return verified values and bounded proposed episode state without writes."""
    contract.validate_current_run_snapshot(snapshot, materialized_limit=_materialized_limit)
    if _proposal is not None:
        contract.validate_current_run_snapshot(_proposal)
        if _proposal['revision'] != snapshot['revision'] or _proposal['owner_scope'] != snapshot['owner_scope']:
            raise ValueError('proposal owner or revision mismatch')
    next_revision = contract.validate_counter(snapshot['revision'] + 1)
    now = _instant(observed_at)
    if policy is not None:
        contract.validate_warning_policy(policy)
    owner = snapshot['owner_scope']
    result = {'candidates': [], 'candidate_details': [], 'proposed_snapshot': deepcopy(snapshot if _proposal is None else _proposal),
              'measurements': {}, 'scoped_measurements': [], 'diagnostics': []}
    result['proposed_snapshot']['revision'] = next_revision
    contract.validate_current_run_snapshot(result['proposed_snapshot'], materialized_limit=(_materialized_limit if _proposal is None else None))
    embedded = snapshot.get('analysis_inputs')
    if analysis_inputs is not None and embedded is not None and analysis_inputs != embedded:
        raise ValueError('conflicting analysis inputs')
    if analysis_inputs is not None and embedded is None:
        candidate = deepcopy(snapshot)
        candidate['analysis_inputs'] = analysis_inputs
        contract.validate_current_run_snapshot(candidate)
    if analysis_inputs is None and embedded is None and verifier is None:
        analysis = _evaluate_snapshot(snapshot)
    else:
        analysis = _evaluate_snapshot(snapshot, analysis_inputs=analysis_inputs, verifier=verifier, observed_at=observed_at)
    if not isinstance(analysis, dict) or analysis.get('scope') != owner:
        result['diagnostics'].append('measurement_unavailable')
        analysis = {'scope': owner, 'metrics': {}}
    metrics = analysis.get('metrics')
    if not isinstance(metrics, dict):
        metrics = {}
    choices = (('tokens', 'token_threshold', 'tokens'),
               ('cost_usd', 'money_threshold', 'USD'),
               ('completeness', 'minimum_completeness', 'fraction'))

    def safe_metrics(items):
        safe = {}
        if not isinstance(items, dict):
            return safe
        for metric, _, unit in choices:
            item = items.get(metric)
            if not isinstance(item, dict) or item.get('unit') != unit:
                continue
            state = item.get('state')
            value = item.get('value')
            if state in ('final', 'proven_lower_bound') and _numeric(value, metric) is not None:
                safe[metric] = {'state': state, 'value': value, 'unit': unit}
            elif state in ('unknown', 'conflict', 'unpriced') and value is None:
                safe[metric] = {'state': state, 'value': None, 'unit': unit}
        return safe

    result['measurements'] = safe_metrics(metrics)
    contexts = [(owner, result['measurements'])] if owner['owner_kind'] == 'run' else []
    scoped = analysis.get('scoped_metrics', [])
    if isinstance(scoped, list):
        valid = []
        for entry in scoped:
            if not isinstance(entry, dict) or entry.get('owner_scope') != owner or entry.get('membership') != 'verified':
                continue
            scope = entry.get('scope')
            if not isinstance(scope, dict) or set(scope) != {'owner_kind', 'owner_id'}:
                continue
            if scope.get('owner_kind') not in ('request', 'span'):
                continue
            try:
                contract._private_identifier(scope.get('owner_id'))
            except ValueError:
                continue
            key = (scope['owner_kind'], scope['owner_id'])
            values = safe_metrics(entry.get('metrics'))
            valid.append((key, scope, values))
        counts = {}
        for key, _, _ in valid:
            counts[key] = counts.get(key, 0) + 1
        for key, scope, values in valid:
            if counts[key] != 1:
                result['diagnostics'].append('measurement_unavailable')
                continue
            contexts.append((scope, values))
            existing = next((item for item in result['scoped_measurements'] if item['scope'] == scope), None)
            if existing is None:
                result['scoped_measurements'].append({'scope': deepcopy(scope), 'metrics': deepcopy(values)})
            else:
                existing['metrics'].update(deepcopy(values))
    _evaluate_duration_status(snapshot, result, observed_at, verifier)
    if (policy is None or now < _instant(policy['created_at']) or
            now >= _instant(policy['expires_at'])):
        result['diagnostics'].append('policy_unavailable')
        return result
    matching = [(scope, values) for scope, values in contexts if scope['owner_kind'] == policy['scope']]
    # An earlier closed owner state already records the warning scope. A missing
    # new measurement must preserve its pending episode, not clear or hide it.
    matched = {(scope['owner_kind'], scope['owner_id']) for scope, _ in matching}
    for warning in snapshot['warning_delivery']:
        scope = warning['scope']
        key = (scope['owner_kind'], scope['owner_id'])
        if (warning['policy_id'] == policy['policy_id'] and
                warning['policy_version'] == policy['policy_version'] and
                scope['owner_kind'] == policy['scope'] and key not in matched):
            matching.append((scope, {}))
            matched.add(key)
    if not matching:
        result['diagnostics'].append('policy_unavailable')
        return result
    for scope, values in matching:
        for metric, threshold_name, unit in choices:
            threshold = policy[threshold_name]
            if threshold is None:
                continue
            proposed = result['proposed_snapshot']
            relevant = [entry for entry in proposed['warning_delivery']
                        if entry['policy_id'] == policy['policy_id'] and
                        entry['policy_version'] == policy['policy_version'] and
                        entry['scope'] == scope and entry['metric'] == metric]
            latest = max(relevant, key=lambda entry: entry['episode']) if relevant else None
            item = values.get(metric, {})
            state = item.get('state')
            number = _numeric(item.get('value'), metric)
            boundary = _numeric(threshold['value'], metric)
            observed = state == 'final' and number is not None
            lower_crossing = (state == 'proven_lower_bound' and number is not None and
                              metric != 'completeness' and number > boundary)
            if not observed and not lower_crossing:
                result['diagnostics'].append('coverage_unknown' if metric == 'completeness' else 'measurement_unavailable')
                if latest and latest['crossing_state'] == 'crossed' and latest['delivery_state'] == 'pending':
                    result['candidates'].append(deepcopy(latest))
                    result['candidate_details'].append({'warning_id': latest['warning_id'],
                                                        'measurement_state': 'unknown'})
                continue
            before = deepcopy(proposed)
            crossing = lower_crossing or (number < boundary if metric == 'completeness' else number > boundary)
            if crossing:
                if latest is None or latest['crossing_state'] in ('cleared', 'below'):
                    episode = latest['episode'] + 1 if latest else 1
                    latest = {'warning_id': _warning_id(owner, policy, scope, metric, episode),
                              'policy_id': policy['policy_id'], 'policy_version': policy['policy_version'],
                              'scope': deepcopy(scope), 'owner_scope': deepcopy(owner), 'metric': metric,
                              'episode': episode, 'crossing_state': 'crossed', 'delivery_state': 'pending',
                              'details': {'measurement': deepcopy(item),
                                  'threshold': {'state': 'final', **deepcopy(threshold)},
                                  'completeness': _scope_completeness(values)}}
                    proposed['warning_delivery'].append(latest)
                else:
                    latest['crossing_state'] = 'crossed'
            elif latest and latest['crossing_state'] == 'crossed':
                latest['crossing_state'] = 'cleared'
            try:
                contract.validate_current_run_snapshot(proposed)
            except ValueError:
                result['proposed_snapshot'] = before
                result['diagnostics'].append('input_limit_exceeded')
                continue
            if crossing and latest['delivery_state'] == 'pending':
                result['candidates'].append(deepcopy(latest))
                result['candidate_details'].append({'warning_id': latest['warning_id'],
                                                    'measurement_state': state})
    return result
