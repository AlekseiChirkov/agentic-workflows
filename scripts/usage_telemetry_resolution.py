"""Resolve explicit offline telemetry with independently authorized evidence.

No file, network, history, or environment discovery occurs here. Content
hashes identify records only; verifier decisions must authenticate the exact
scope, subject and evidence. Unsupported combinations remain unavailable.
"""
import copy
from fractions import Fraction
import importlib.util
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contract = _load('usage_telemetry_contract')
identity = _load('usage_telemetry_identity')
stream = _load('usage_telemetry_stream')
epochs = _load('usage_telemetry_epochs')
ownership = _load('usage_telemetry_ownership')
completeness = _load('usage_telemetry_completeness')
applicability = _load('usage_telemetry_applicability')
exact_cost = _load('usage_telemetry_exact_cost')


def _authorized(verifier, kind, scope, subject, evidence):
    try:
        # A verifier must explicitly return true, not an input-provided flag.
        return verifier(kind, scope, subject, evidence) is True
    except Exception:
        return False


def _measurement(observation, field, measurement, ttl, objects, profile, scope, verifier):
    if measurement.get('measurement_state') not in ('final', 'partial') or 'evidence' not in measurement:
        return False
    proof = objects.get(measurement['evidence'])
    if not proof or any(proof.get(k) != observation[k] for k in ('profile_id', 'source_hash', 'record_number')):
        return False
    if proof.get('field') != field or proof.get('value') != measurement.get('value'):
        return False
    if ttl is not None and proof.get('ttl') != ttl:
        return False
    subject = {'observation': observation, 'field': field}
    if ttl is not None:
        subject['ttl'] = ttl
    if not _authorized(verifier, 'measurement', scope, subject, proof):
        return False
    if proof.get('kind') != 'derived_measurement_evidence':
        definitions = [item for item in profile['counter_fields'] if item.get('path') == proof.get('path')
                       and item.get('measurement') == field and item.get('counter_scope') == observation['counter_scope']
                       and item.get('semantics_status') == 'verified'
                       and (ttl is None or item.get('ttl') == ttl)]
        return (proof.get('kind') == 'measurement_evidence' and len(definitions) == 1
                and contract.verify_measurement_evidence(observation, field, proof, ttl))
    if not contract.verify_derived_measurement_evidence(measurement, proof, list(objects.values()), profile):
        return False
    active = set()

    def authorize_operand(item):
        digest = contract.content_id(item)
        if digest in active:
            return False
        active.add(digest)
        try:
            if any(item.get(k) != observation[k] for k in ('profile_id', 'source_hash', 'record_number')):
                return False
            if item.get('kind') == 'derived_measurement_evidence':
                return all(ref in objects and authorize_operand(objects[ref]) for ref in item['operands'])
            if item.get('kind') != 'measurement_evidence':
                return False
            field_name = item['field']
            declaration = {'observation': observation, 'field': field_name}
            if 'ttl' in item:
                declaration['ttl'] = item['ttl']
            definitions = [entry for entry in profile['counter_fields'] if entry.get('path') == item.get('path')
                           and entry.get('measurement') == field_name
                           and entry.get('counter_scope') == observation['counter_scope']
                           and entry.get('semantics_status') == 'verified'
                           and ('ttl' not in item or item['ttl'] == entry.get('ttl'))]
            return len(definitions) == 1 and _authorized(verifier, 'measurement', scope, declaration, item)
        finally:
            active.remove(digest)
    return all(ref in objects and authorize_operand(objects[ref]) for ref in proof['operands'])


def _context(observation, context, profile, scope, verifier):
    try:
        contract.validate_resolution_context(context)
        if context['observation_id'] != contract.observation_id(observation):
            return False
        if any(context[k] != observation[k] for k in ('profile_id', 'profile_version', 'source_hash',
                                                       'record_number', 'provider_scope', 'counter_scope')):
            return False
        if context['provider'] != profile['provider'] or observation['counter_scope'] not in ('response_total', 'incremental_delta'):
            return False
        expected_scope = 'response_total' if context['event']['kind'] == 'snapshot' else 'incremental_delta'
        if observation['counter_scope'] != expected_scope:
            return False
        return _authorized(verifier, 'context', scope, observation, context)
    except (ValueError, KeyError, TypeError, RecursionError):
        return False


def _rate(observation, context, field, ttl, snapshots, scenario, price_evidence, scope, verifier, as_of, objects, profile, quantities, input_total):
    if scenario is None or not snapshots or any(
            contract._instant(snapshot['retrieved_at']) > contract._instant(as_of) for snapshot in snapshots):
        return None
    proofs = list(price_evidence) + list(context['evidence_objects'])
    trusted = set()
    for proof in price_evidence:
        kind = proof.get('kind')
        if kind == 'model_alias_evidence':
            continue
        if kind in ('price_snapshot_evidence', 'price_period_evidence'):
            for snapshot in snapshots:
                if _authorized(verifier, 'price', scope, snapshot, proof):
                    trusted.add(contract.content_id(proof))
        elif kind in ('multiplier_evidence', 'rate_parameter_evidence', 'source_parameter_evidence',
                      'execution_time_evidence'):
            if _authorized(verifier, 'pricing_context', scope, observation, proof):
                trusted.add(contract.content_id(proof))
    for proof in context['evidence_objects']:
        if _authorized(verifier, 'pricing_context', scope, observation, proof):
            trusted.add(contract.content_id(proof))
    by_kind = {}
    for proof in context['evidence_objects']:
        by_kind.setdefault((proof['kind'], proof.get('field'), proof.get('value')), []).append(proof)

    def find(kind, name, value):
        candidates = by_kind.get((kind, name, value), [])
        if len(candidates) != 1:
            return None
        return {'value': value, 'evidence': contract.content_id(candidates[0])}

    execution = find('execution_time_evidence', None, context['execution_time'])
    selected_scenario = copy.deepcopy(scenario)
    for name, value in context['parameters'].items():
        original = scenario['source_parameters'][name]
        # Explicit scenario dimensions constrain every record; only the evidence
        # reference is rebound to the verified record-specific declaration.
        if original is not None and original['value'] != value:
            return None
        selected_scenario['source_parameters'][name] = find('source_parameter_evidence', name, value)
    ttl_value = None if ttl is None else context['cache_ttl_seconds'].get(ttl)
    ttl_declaration = None if ttl is None else find('rate_parameter_evidence', 'cache_ttl_seconds', ttl_value)
    aliases = []
    for proof in price_evidence:
        if proof.get('kind') != 'model_alias_evidence':
            continue
        for snapshot in snapshots:
            bindings = [candidate for candidate in price_evidence
                        if candidate.get('kind') == 'price_snapshot_evidence' and
                        candidate.get('snapshot_id') == contract.price_snapshot_id(snapshot) and
                        contract.content_id(candidate) in trusted]
            declaration = {'alias': proof['alias'], 'model': proof['model'], 'evidence': contract.content_id(proof)}
            if (len(bindings) == 1 and bindings[0]['source_hash'] == proof['source_hash'] and
                    proof['model'] == snapshot['model'] and
                    {'alias': proof['alias'], 'evidence': declaration['evidence']} in snapshot['aliases'] and
                    _authorized(verifier, 'alias', scope, snapshot, proof)):
                trusted.add(declaration['evidence'])
                aliases.append(declaration)
    component = 'output' if field == 'output_total' else field
    operands = {}
    for rule in scenario['threshold_rules']:
        if component not in rule['components']:
            continue
        operand = rule['operand']
        measurement = observation.get('measurements', {}).get(operand)
        if not isinstance(measurement, dict) or 'evidence' not in measurement:
            continue
        resolved = input_total if operand == 'tokens_in' else quantities.get((operand, None))
        value = measurement.get('value')
        try:
            same_value = resolved is not None and int(value) == resolved
        except (TypeError, ValueError, OverflowError):
            same_value = False
        if not same_value or not _measurement(observation, operand, measurement, None, objects, profile, scope, verifier):
            continue
        evidence = objects.get(measurement['evidence'])
        if evidence is None:
            continue
        operands[operand] = {'value': value, 'evidence': measurement['evidence']}
        if all(contract.content_id(item) != measurement['evidence'] for item in proofs):
            proofs.append(evidence)
        trusted.add(measurement['evidence'])
    tool_id = find('rate_parameter_evidence', 'tool_id', observation['tool_id']) if field == 'tool' else None
    request = {'component': component,
               'unit': observation['unit'] if field == 'tool' else 'tokens',
               'cache_ttl_seconds': ttl_declaration, 'tool_id': tool_id,
               'execution_time': execution, 'profile_id': observation['profile_id'],
               'source_hash': observation['source_hash'], 'record_number': observation['record_number'],
               'operands': operands, 'verified_aliases': aliases}
    result = applicability.select_rate(snapshots, selected_scenario, request, proofs, trusted)
    if result.get('state') != 'priced':
        return None
    price = Fraction(result['rate']['usd']) * Fraction(result['factor'])
    if not exact_cost._is_terminating(price):
        return None
    return exact_cost._decimal_string(price), result['rate']['unit_quantity']


def _resolve_epochs(inputs, scope, as_of, verifier):
    """Resolve separately scoped interval evidence without adding it to responses."""
    if not isinstance(inputs, list) or len(inputs) > 10000:
        raise ValueError('invalid cumulative inputs')
    unique = {}
    for pack in inputs:
        contract._fields(pack, {'profile', 'observations', 'evidence_objects', 'interval', 'observed_at'})
        contract._bounded_tree(pack)
        contract._timestamp(pack['observed_at'])
        if len(contract.canonical_bytes(pack)) > contract.BUNDLE_LIMIT:
            raise ValueError('cumulative input exceeds limit')
        unique[contract.content_id(pack)] = pack
    rows = []
    aggregates = []
    for digest, pack in sorted(unique.items()):
        row = {'request_usage': {}, 'interval_aggregate': None}
        rows.append(row)
        try:
            profile = pack['profile']
            contract.validate_source_profile(profile)
            observations = pack['observations']
            objects = pack['evidence_objects']
            interval = pack['interval']
            if (not isinstance(observations, list) or len(observations) != 2 or
                    not isinstance(objects, list) or len(objects) > 10000):
                continue
            contract._fields(interval, {'before', 'after', 'coverage'})
            identity_fields = {'provider', 'account', 'model', 'units', 'epoch'}
            for snapshot in (interval['before'], interval['after']):
                contract._fields(snapshot, identity_fields | {'sequence', 'position', 'value'})
                contract._identifier(snapshot['provider'])
                contract._private_identifier(snapshot['account'])
                contract._identifier(snapshot['units'])
                contract._private_identifier(snapshot['epoch'])
                if not isinstance(snapshot['model'], str) or len(snapshot['model']) > 256:
                    raise ValueError('invalid model')
                for field in ('sequence', 'position', 'value'):
                    contract.validate_counter(snapshot[field])
            coverage = interval['coverage']
            contract._fields(coverage, {'complete', 'before_clear', 'after_clear', 'atomic_on_completion', 'requests'})
            for flag in ('complete', 'before_clear', 'after_clear', 'atomic_on_completion'):
                if type(coverage[flag]) is not bool:
                    raise ValueError('invalid interval flag')
            if not isinstance(coverage['requests'], list) or len(coverage['requests']) > 10000:
                raise ValueError('invalid interval requests')
            for request in coverage['requests']:
                contract._fields(request, {'id', 'start', 'end'})
                contract._private_identifier(request['id'])
                contract.validate_counter(request['start'])
                contract.validate_counter(request['end'])
            objects_by_id = {}
            for item in objects:
                contract.validate_evidence_object(item)
                identity = contract.content_id(item)
                if identity in objects_by_id:
                    raise ValueError('duplicate interval evidence')
                objects_by_id[identity] = item
            if contract._instant(pack['observed_at']) > contract._instant(as_of):
                continue
            subject = {'profile': profile, 'observations': observations}
            if not _authorized(verifier, 'epoch_privacy', scope, subject, pack):
                continue
            row['id'] = digest
            if not (_authorized(verifier, 'profile', scope, profile, profile) and
                    _authorized(verifier, 'epoch_interval', scope, subject, interval) and
                    _authorized(verifier, 'epoch_inventory', scope, subject, coverage) and
                    _authorized(verifier, 'epoch_boundary', scope, subject, coverage)):
                continue
            valid = True
            for observation, snapshot in zip(observations, (interval['before'], interval['after'])):
                contract.validate_observation(observation)
                if (observation['counter_scope'] != 'cumulative_epoch' or
                        observation['profile_id'] != profile['profile_id'] or
                        observation['profile_version'] != profile['profile_version'] or
                        contract._instant(observation['observed_at']) > contract._instant(as_of) or
                        snapshot['provider'] != profile['provider'] or
                        snapshot['account'] != observation['provider_scope'] or
                        snapshot['units'] != 'input_uncached_tokens'):
                    valid = False
                    break
                measurement = observation['measurements'].get('input_uncached', {})
                if (snapshot['value'] != measurement.get('value') or
                        not _measurement(observation, 'input_uncached', measurement, None,
                                         objects_by_id, profile, scope, verifier) or
                        not _authorized(verifier, 'epoch_snapshot', scope, observation, snapshot)):
                    valid = False
                    break
            if not valid:
                continue
            safe_interval = copy.deepcopy(interval)
            if safe_interval['coverage']['atomic_on_completion'] and not _authorized(
                    verifier, 'epoch_atomic', scope, subject, coverage):
                safe_interval['coverage']['atomic_on_completion'] = False
            resolved = epochs.resolve_interval(safe_interval)
            row['request_usage'] = {key: str(value) for key, value in resolved['request_usage'].items()}
            if resolved['interval_aggregate'] is not None:
                amount = resolved['interval_aggregate']
                row['interval_aggregate'] = str(amount)
                before, after = interval['before'], interval['after']
                aggregates.append({'id': digest, **{key: before[key] for key in identity_fields},
                                   'start': before['position'], 'end': after['position'],
                                   'value': amount, 'boundaries_proven': True})
        except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
            continue
    aggregate = epochs.aggregate_intervals(aggregates)
    if aggregate['total'] is not None:
        aggregate['total'] = str(aggregate['total'])
    return {'intervals': rows, 'aggregate': aggregate}


def _resolve_tools(inputs, bundle, profile, scope, inventory, inventory_proof, snapshots, scenario,
                   price_evidence, as_of, verifier):
    """Price independently authorized, separately inventoried tool units."""
    if not isinstance(inputs, list) or len(inputs) > 10000:
        raise ValueError('invalid tool inputs')
    unique, conflicts = {}, set()
    for item in inputs:
        if not isinstance(item, dict):
            raise ValueError('invalid tool input')
        identity = item.get('usage_id')
        try:
            contract._private_identifier(identity)
            encoded = contract.canonical_bytes(item)
        except (ValueError, TypeError, RecursionError):
            raise ValueError('invalid tool input') from None
        if identity in unique and unique[identity][0] != encoded:
            conflicts.add(identity)
        else:
            unique[identity] = (encoded, item)
    declaration = {'inventory_evidence': inventory_proof, 'tool_usage_ids': sorted(unique)}
    timely = contract._instant(inventory['observed_at']) <= contract._instant(as_of)
    complete = timely and _authorized(verifier, 'tool_inventory', scope, inventory, declaration)
    nonoverlap = timely and _authorized(verifier, 'tool_nonoverlap', scope, inventory, declaration)
    result, components = [], []
    quantities_known = True
    prices_known = True
    source_hashes = {source['sha256'] for source in bundle['sources']}
    for identity in sorted(unique):
        item = unique[identity][1]
        if identity in conflicts:
            result.append({'state': 'unavailable'})
            quantities_known = False
            continue
        try:
            contract.validate_tool_usage(item)
            if (item['profile_id'] != profile['profile_id'] or item['profile_version'] != profile['profile_version'] or
                    item['source_hash'] not in source_hashes or
                    contract._instant(item['observed_at']) > contract._instant(as_of) or
                    item['execution_time'] is not None and contract._instant(item['execution_time']) > contract._instant(as_of)):
                raise ValueError('tool scope is unavailable')
            quantity_proof = next(proof for proof in item['evidence_objects'] if proof['kind'] == 'tool_quantity_evidence')
            if not (_authorized(verifier, 'tool_privacy', scope, item, item) and
                    _authorized(verifier, 'tool_usage', scope, item, quantity_proof)):
                raise ValueError('tool evidence is unavailable')
            context = {'execution_time': item['execution_time'], 'parameters': item['parameters'],
                       'cache_ttl_seconds': {}, 'evidence_objects': item['evidence_objects']}
            price = _rate(item, context, 'tool', None, snapshots, scenario, price_evidence,
                          scope, verifier, as_of, {}, profile, {}, None)
            component = {'id': 'tool_' + identity[7:], 'quantity': item['quantity'],
                         'price_usd': None if price is None else price[0],
                         'unit': None if price is None else price[1]}
            components.append(component)
            if price is None:
                prices_known = False
                result.append({'usage_id': identity, 'state': 'unpriced'})
            else:
                priced = exact_cost.calculate_cost([component], {
                    'inventory_complete': True, 'identities_resolved': True, 'quantities_final': True,
                    'prices_applicable': True, 'scope_proven': True, 'nonoverlapping': True,
                    'excluded_cannot_reduce': True, 'contradiction': False,
                    'historical_substitution': False, 'unknown_signed_components': False})
                if 'cost_usd' not in priced:
                    prices_known = False
                    result.append({'usage_id': identity, 'state': 'unpriced'})
                else:
                    row = {'usage_id': identity, 'state': 'priced', 'cost_usd': priced['cost_usd']}
                    if scenario is not None and scenario['basis'] == 'reprice':
                        row['conditional'] = True
                    result.append(row)
        except (ValueError, TypeError, KeyError, StopIteration, RecursionError, OverflowError):
            quantities_known = False
            result.append({'state': 'unavailable'})
    if conflicts:
        quantities_known = False
        nonoverlap = False
    return {'tools': result, 'components': components,
            'complete': complete and quantities_known and not conflicts,
            'nonoverlap': nonoverlap and quantities_known and not conflicts,
            'quantities_known': quantities_known, 'prices_known': prices_known}


def _resolve_ownership(owner_scopes, entries, details, observations, inventory, inventory_proof,
                       coverage, as_of, verifier):
    """Resolve explicitly attested ownership over already priced model responses."""
    if (not isinstance(owner_scopes, list) or len(owner_scopes) > 256 or
            not isinstance(entries, list) or len(entries) > 10000):
        raise ValueError('invalid ownership inputs')
    scopes = {}
    for scope in owner_scopes:
        contract._fields(scope, {'owner_kind', 'owner_id'})
        contract._choice(scope['owner_kind'], frozenset({'run', 'session', 'task', 'span', 'shared_pool'}))
        contract._private_identifier(scope['owner_id'])
        key = contract.canonical_bytes(scope)
        if key in scopes:
            raise ValueError('duplicate ownership scope')
        scopes[key] = scope
    grouped = {}
    for entry in entries:
        contract._fields(entry, {'observation_id', 'observed_at', 'attribution'})
        contract._bounded_tree(entry)
        contract._hash(entry['observation_id'])
        contract._timestamp(entry['observed_at'])
        attr = entry['attribution']
        contract._fields(attr, {'response_id', 'provider', 'provider_scope', 'owner_kind', 'owner_id',
                                'candidates', 'basis'})
        for name in ('response_id', 'provider_scope', 'owner_id'):
            contract._private_identifier(attr[name])
        contract._identifier(attr['provider'])
        contract._choice(attr['owner_kind'], frozenset({'task', 'span', 'shared_pool', 'unattributed'}))
        contract._choice(attr['basis'], frozenset({'submission', 'correlation', 'verified_import'}))
        if not isinstance(attr['candidates'], list) or len(attr['candidates']) > 64:
            raise ValueError('invalid attribution candidates')
        for candidate in attr['candidates']:
            contract._private_identifier(candidate)
        if len(set(attr['candidates'])) != len(attr['candidates']):
            raise ValueError('duplicate attribution candidate')
        grouped.setdefault(entry['observation_id'], {})[contract.canonical_bytes(entry)] = entry
    observations_by_id = {contract.observation_id(item): item for item in observations}
    results = []
    for _, scope in sorted(scopes.items()):
        scope_verified = (contract._instant(inventory['observed_at']) <= contract._instant(as_of) and
                          _authorized(verifier, 'ownership_inventory', scope, inventory, inventory_proof))
        pending = not scope_verified
        contributors, trusted, descendants = [], [], []
        for detail in details:
            candidates = []
            for prefixed in detail['observation_ids']:
                identifier = prefixed[7:]
                for entry in grouped.get(identifier, {}).values():
                    if contract._instant(entry['observed_at']) <= contract._instant(as_of):
                        candidates.append(entry)
            if len(candidates) != 1:
                pending = True
                continue
            entry = candidates[0]
            observation = observations_by_id.get(entry['observation_id'])
            attr = entry['attribution']
            ident = detail['identity']
            if (observation is None or attr['response_id'] != ident['id'] or
                    attr['provider'] != ident['provider'] or attr['provider_scope'] != ident['provider_scope'] or
                    not _authorized(verifier, 'ownership', scope, observation, entry)):
                pending = True
                continue
            kind, owner = attr['owner_kind'], attr['owner_id']
            belongs = owner == scope['owner_id'] and kind in ('task', 'span', 'shared_pool')
            shared_candidate = kind == 'shared_pool' and scope['owner_id'] in attr['candidates']
            descendant = False
            if kind == 'unattributed' or shared_candidate:
                pending = True
            elif not belongs:
                descendant = _authorized(verifier, 'ownership_descendant', scope, observation, entry)
                if not descendant and not _authorized(verifier, 'ownership_exclusion', scope, observation, entry):
                    pending = True
            amount = detail['model_cost'].get('cost_usd')
            if amount is None:
                if belongs or shared_candidate or descendant:
                    pending = True
                continue
            if descendant:
                descendants.append((ident, amount))
            proof_id = contract.content_id(attr)
            contributors.append({'response_id': ident['id'], 'provider': ident['provider'],
                                 'provider_scope': ident['provider_scope'], 'observed_at': entry['observed_at'],
                                 'cost_usd': amount, 'attribution': attr, 'attribution_evidence': proof_id})
            trusted.append(proof_id)
        finality = coverage['finality']
        model_inventory_complete = (finality.get('state') == 'not_applicable' or
                                    (finality.get('denominator') is not None and
                                     finality['numerator'] == finality['denominator']))
        complete = scope_verified and model_inventory_complete and not pending
        report = ownership.build_ownership_report(contributors, scope['owner_id'], as_of, complete, trusted)
        if pending:
            report['attribution'] = 'partial'
        model_cost = {}
        if 'cost_usd' in report:
            amount = Fraction(report.pop('cost_usd')) + sum((Fraction(item[1]) for item in descendants), Fraction(0))
            model_cost['cost_usd'] = exact_cost._decimal_string(amount)
        else:
            model_cost['subtotal_quality'] = 'subtotal_only'
        report['contributors'].extend({'provider': ident['provider'], 'provider_scope': ident['provider_scope'],
                                       'response_id': ident['id']} for ident, _ in descendants)
        report['contributors'].sort(key=lambda item: (item['provider'], item['provider_scope'], item['response_id']))
        report['scope'] = scope
        report['model_cost'] = model_cost
        results.append(report)
    return results



def _resolve_tool_ownership(reports, entries, inputs, tool_result, inventory, inventory_proof, as_of, verifier, conditional):
    """Attribute independently priced tool usage only with scope-specific evidence."""
    if not isinstance(entries, list) or len(entries) > 10000:
        raise ValueError('invalid tool ownership inputs')
    grouped = {}
    for entry in entries:
        contract._fields(entry, {'usage_id', 'observed_at', 'attribution'})
        contract._bounded_tree(entry)
        contract._private_identifier(entry['usage_id'])
        contract._timestamp(entry['observed_at'])
        attr = entry['attribution']
        contract._fields(attr, {'owner_kind', 'owner_id', 'candidates', 'basis'})
        contract._choice(attr['owner_kind'], frozenset({'task', 'span', 'shared_pool', 'unattributed'}))
        contract._private_identifier(attr['owner_id'])
        contract._choice(attr['basis'], frozenset({'submission', 'correlation', 'verified_import'}))
        if not isinstance(attr['candidates'], list) or len(attr['candidates']) > 64:
            raise ValueError('invalid attribution candidates')
        for candidate in attr['candidates']:
            contract._private_identifier(candidate)
        if len(set(attr['candidates'])) != len(attr['candidates']):
            raise ValueError('duplicate attribution candidate')
        grouped.setdefault(entry['usage_id'], {})[contract.canonical_bytes(entry)] = entry
    raw = {item['usage_id']: item for item in inputs} if isinstance(inputs, list) else {}
    declaration = {'inventory_evidence': inventory_proof, 'tool_usage_ids': sorted(raw)}
    for report in reports:
        scope = report['scope']
        pending = (tool_result is None or not tool_result['complete'] or not tool_result['nonoverlap'] or
                   contract._instant(inventory['observed_at']) > contract._instant(as_of) or
                   not _authorized(verifier, 'tool_ownership_inventory', scope, inventory, declaration))
        contributors, total = [], Fraction(0)
        for row in tool_result['tools'] if tool_result is not None else []:
            identifier = row.get('usage_id')
            candidates = [entry for entry in grouped.get(identifier, {}).values()
                          if contract._instant(entry['observed_at']) <= contract._instant(as_of)]
            item = raw.get(identifier)
            if len(candidates) != 1 or item is None:
                pending = True
                continue
            entry = candidates[0]
            if not _authorized(verifier, 'tool_ownership', scope, item, entry):
                pending = True
                continue
            attr = entry['attribution']
            kind, owner = attr['owner_kind'], attr['owner_id']
            belongs = owner == scope['owner_id'] and kind in ('task', 'span', 'shared_pool')
            shared = kind == 'shared_pool' and scope['owner_id'] in attr['candidates']
            if kind == 'unattributed' or shared:
                pending = True
                continue
            if not belongs:
                belongs = _authorized(verifier, 'tool_ownership_descendant', scope, item, entry)
                if not belongs and not _authorized(verifier, 'tool_ownership_exclusion', scope, item, entry):
                    pending = True
                    continue
            if belongs:
                if row.get('state') != 'priced' or 'cost_usd' not in row:
                    pending = True
                    continue
                total += Fraction(row['cost_usd'])
                contributors.append({'usage_id': identifier})
        report['tool_contributors'] = contributors
        report['tool_cost'] = ({'subtotal_quality': 'subtotal_only'} if pending else
                               {'cost_usd': exact_cost._decimal_string(total)})
        if pending:
            report['attribution'] = 'partial'
        model_amount = report['model_cost'].get('cost_usd')
        report['cost'] = ({'subtotal_quality': 'subtotal_only'} if pending or model_amount is None else
                          {'cost_usd': exact_cost._decimal_string(Fraction(model_amount) + total)})
        if conditional:
            report['tool_cost']['conditional'] = True
            report['cost']['conditional'] = True

def resolve_usage(*, bundle, profile, contexts, snapshots, scenario, price_evidence, scope, as_of, verifier, epoch_inputs=None, owner_scopes=None, ownership_inputs=None, tool_inputs=None, tool_ownership_inputs=None):
    """Return scoped completeness and exact cost using only explicit evidence."""
    contract.validate_usage_bundle(bundle)
    contract.validate_source_profile(profile)
    if scenario is not None:
        contract.validate_pricing_scenario(scenario)
    contract._timestamp(as_of)
    if not callable(verifier) or not isinstance(contexts, list) or len(contexts) > 10000:
        raise ValueError('invalid resolution inputs')
    if not isinstance(snapshots, list) or len(snapshots) > 10000 or not isinstance(price_evidence, list) or len(price_evidence) > 10000:
        raise ValueError('invalid pricing inputs')
    if profile['profile_id'] != bundle['profile_id'] or profile['profile_version'] != bundle['profile_version']:
        raise ValueError('profile mismatch')
    for snapshot in snapshots:
        contract.validate_price_snapshot(snapshot)
    for proof in price_evidence:
        applicability._validate_applicability_evidence(proof)
    inventory = next((item for item in bundle['inventories'] if item['owner_scope'] == scope), None)
    if inventory is None or sum(item['owner_scope'] == scope for item in bundle['inventories']) != 1:
        raise ValueError('scope inventory is unavailable or ambiguous')
    objects = {contract.content_id(item): item for item in bundle['evidence_objects']}
    inventory_proof = objects.get(inventory['evidence'])
    profile_verified = _authorized(verifier, 'profile', scope, profile, profile)
    context_map = {}
    for context in contexts:
        if not isinstance(context, dict) or not isinstance(context.get('observation_id'), str):
            raise ValueError('invalid resolution context')
        key = context['observation_id']
        if key in context_map:
            raise ValueError('duplicate resolution context')
        context_map[key] = context
    obs = [item for item in bundle['observations'] if contract._instant(item['observed_at']) <= contract._instant(as_of)]
    obs.sort(key=contract.observation_id)
    identity_records = []
    trusted_contexts = {}
    uncertain = not profile_verified
    for item in obs:
        if not _authorized(verifier, 'response_privacy', scope, item, item):
            uncertain = True
            continue
        digest = contract.observation_id(item)
        context = context_map.get(digest)
        verified = profile_verified and context is not None and _context(item, context, profile, scope, verifier)
        if verified:
            trusted_contexts[digest] = context
        else:
            uncertain = True
        if item['kind'] != 'request_usage' or item['counter_scope'] not in ('response_total', 'incremental_delta'):
            uncertain = True
            continue
        try:
            for key in ('response_id', 'call_id'):
                if key in item:
                    contract._private_identifier(item[key])
            identity_records.append({'observation_id': 'sha256:' + digest, 'provider': profile['provider'],
                                     'provider_scope': item['provider_scope'], 'response_id': item.get('response_id'),
                                     'call_id': item.get('call_id'),
                                     'session_id': context['session_id'] if verified else 'sha256:' + '0' * 64})
        except ValueError:
            uncertain = True
    groups = identity.resolve_response_identities(identity_records, [])
    uncertain |= bool(groups['unresolved']) or any(not group['additive'] for group in groups['responses'])
    identity_uncertain = uncertain
    by_digest = {contract.observation_id(item): item for item in obs}
    responses = []
    response_details = []
    components = []
    token_values = {'input': [], 'output': []}
    all_quantities = True
    all_prices = True
    for group in groups['responses']:
        records = [by_digest[key[7:]] for key in group['observation_ids']]
        response_id = group['identity']['id']
        calls = {record.get('call_id') for record in records}
        if len(calls) != 1 or None in calls or group['identity']['kind'] != 'response':
            uncertain = True
            identity_uncertain = True
            continue
        measures = {}
        partial_measures = {}
        finality_events = []
        event_sources = {}
        terminal_events = []
        pricing_dimensions = set()
        unverified = False
        for record in records:
            digest = contract.observation_id(record)
            context = trusted_contexts.get(digest)
            if context is None:
                unverified = True
                continue
            pricing_dimensions.add(contract.canonical_bytes({
                'execution_time': context['execution_time'], 'parameters': context['parameters'],
                'cache_ttl_seconds': context['cache_ttl_seconds']}))
            event_data = dict(context['event'])
            if 'correction_of' in event_data:
                # Only the trusted verifier may authorize the revision edge.
                event_data['correction_verified'] = _authorized(verifier, 'revision', scope, record, context['event'])
            marker = {'response_id': response_id, 'observation_id': 'sha256:' + digest, **event_data}
            if marker['kind'] != 'terminal':
                marker['value'] = 0
            else:
                terminal_events.append(marker)
            finality_events.append(marker)
            event_sources[marker['observation_id']] = (record, context)
            for field, value in record['measurements'].items():
                entries = [(part['ttl'], part['tokens']) for part in value] if field == 'input_cache_write' else [(None, value)]
                for ttl, measured in entries:
                    if field == 'tokens_in' or event_data['kind'] == 'terminal':
                        continue
                    if not _measurement(record, field, measured, ttl, objects, profile, scope, verifier):
                        continue
                    event = {'response_id': response_id, 'observation_id': 'sha256:' + digest,
                             **event_data, 'value': measured['value']}
                    partial_measures.setdefault((field, ttl), []).append((event, record, context))
                    # A final snapshot does not finalize a partial counter. Delta
                    # parts are independently finalized by a verified terminal.
                    if event_data['kind'] == 'snapshot' and measured.get('measurement_state') != 'final':
                        continue
                    measures.setdefault((field, ttl), []).append((event, record, context))
        try:
            finality_result = stream.resolve_stream(finality_events)
        except ValueError:
            finality_result = {'measurement_state': 'conflicted'}
        final = not unverified and finality_result['measurement_state'] == 'final'
        ambiguous_context = len(pricing_dimensions) > 1 or finality_result['measurement_state'] == 'conflicted'
        anchors = [event for event in finality_events if event['kind'] == 'terminal' or
                   event['kind'] == 'snapshot' and event.get('final')]
        corrected = {event['correction_of'] for event in anchors
                     if event.get('correction_verified') is True and 'correction_of' in event}
        tips = [event for event in anchors if event['observation_id'] not in corrected]
        anchor = max(tips, key=lambda event: (event.get('sequence', 0), event['observation_id'])) if tips else None
        values = {}
        for key, events in measures.items():
            try:
                event_list = [entry[0] for entry in events]
                # Finality has already validated revision edges across all snapshots.
                # Resolve each quantity from the surviving final records only.
                if final and anchor is not None and anchor['kind'] == 'snapshot':
                    tip_ids = {event['observation_id'] for event in tips}
                    event_list = [{key: value for key, value in event.items()
                                   if key not in ('correction_of', 'correction_verified')}
                                  for event in event_list if event['observation_id'] in tip_ids]
                if any(item['kind'] == 'delta' for item in event_list):
                    event_list += terminal_events
                resolved = stream.resolve_stream(event_list)
                if resolved['measurement_state'] == 'conflicted':
                    ambiguous_context = True
                if resolved['measurement_state'] == 'final' and anchor is not None:
                    # Snapshot quantities must come from the same proven final
                    # record, preventing mixtures of incompatible revisions.
                    if anchor['kind'] == 'snapshot' and not any(
                            item['observation_id'] == anchor['observation_id'] for item in event_list):
                        continue
                    record, context = event_sources[anchor['observation_id']]
                    values[key] = (resolved['value'], record, context)
            except ValueError:
                unverified = True
        partial_values = {}
        if not unverified and finality_result['measurement_state'] != 'conflicted':
            snapshots_seen = [event for event in finality_events if event['kind'] == 'snapshot']
            latest_snapshot = None
            if snapshots_seen and all('sequence' in event for event in snapshots_seen):
                latest_number = max(event['sequence'] for event in snapshots_seen)
                latest = [event for event in snapshots_seen if event['sequence'] == latest_number]
                if len(latest) == 1:
                    latest_snapshot = latest[0]['observation_id']
            elif len(snapshots_seen) == 1:
                latest_snapshot = snapshots_seen[0]['observation_id']
            for key, entries in partial_measures.items():
                events = [entry[0] for entry in entries]
                try:
                    if snapshots_seen:
                        matching = [event for event in events if event['observation_id'] == latest_snapshot]
                        if len(matching) == 1:
                            partial_values[key] = matching[0]['value']
                    else:
                        outcome = stream.resolve_stream(events + terminal_events)
                        if outcome['measurement_state'] == 'partial' and 'value' in outcome:
                            partial_values[key] = outcome['value']
                except ValueError:
                    pass
        uncertain |= ambiguous_context
        component_start = len(components)
        required = [('input_uncached', None), ('output_total', None)]
        definitions = profile['counter_fields']
        split_writes = [(entry['measurement'], entry['ttl']) for entry in definitions
                        if entry['measurement'] == 'input_cache_write']
        has_cache_fields = any(entry['measurement'] in ('input_cache_read', 'input_cache_write',
                                                        'input_cache_write_unsplit') for entry in definitions)
        cache_unsupported = profile['capabilities']['cache'] == 'unsupported' and not has_cache_fields
        if not cache_unsupported:
            required.append(('input_cache_read', None))
            # Unknown or unsplit TTL is still a measured quantity, but cannot
            # select one of the time-specific prices.
            required.extend(split_writes or [('input_cache_write_unsplit', None)])
        conflict_events = finality_events
        if finality_result['measurement_state'] == 'final' and anchor is not None and anchor['kind'] == 'snapshot':
            conflict_events = tips
        elif finality_result['measurement_state'] == 'partial':
            event_snapshots = [event for event in finality_events if event['kind'] == 'snapshot']
            if event_snapshots and len(event_snapshots) == len(finality_events) and all('sequence' in event for event in event_snapshots):
                latest_sequence = max(event['sequence'] for event in event_snapshots)
                conflict_events = [event for event in event_snapshots if event['sequence'] == latest_sequence]
        write_conflict = any(
            event_sources[event['observation_id']][0]['measurements'].get(
                'input_cache_write_unsplit', {}).get('measurement_state') == 'conflicted'
            for event in conflict_events if event['kind'] != 'terminal')
        input_known = (all(key in values for key in required if key[0] != 'output_total') and
                       not unverified and not write_conflict)
        output_known = ('output_total', None) in values and not unverified
        final = final and not unverified
        record_priced = final and input_known and output_known and group['additive'] and not ambiguous_context
        all_quantities &= input_known and output_known
        if final and input_known:
            token_values['input'].append(sum(values[key][0] for key in required if key[0] != 'output_total'))
        if final and output_known:
            token_values['output'].append(values[('output_total', None)][0])
        for index, key in enumerate(required):
            if key not in values:
                record_priced = False
                continue
            quantity, record, context = values[key]
            known_quantities = {name: amount[0] for name, amount in values.items()}
            input_total = (sum(values[name][0] for name in required if name[0] != 'output_total')
                           if input_known else None)
            price = None if ambiguous_context or key[0] == 'input_cache_write_unsplit' else _rate(
                record, context, key[0], key[1], snapshots, scenario, price_evidence, scope, verifier, as_of,
                objects, profile, known_quantities, input_total)
            if price is None:
                record_priced = False
                all_prices = False
            components.append({'id': contract.content_id(group['identity'])[7:] + '_' + str(index), 'quantity': quantity,
                               'price_usd': None if price is None else price[0],
                               'unit': None if price is None else price[1]})
        responses.append({'response_id': response_id, 'provider': group['identity']['provider'],
                          'provider_scope': group['identity']['provider_scope'],
                          'call_id': next(iter(calls)), 'final': final,
                          'measurements': {'input': input_known, 'output': output_known}, 'priced': record_priced})
        per_tokens = {}
        for name, known, value in (
                ('input', input_known, sum(values[key][0] for key in required if key[0] != 'output_total' and key in values)),
                ('output', output_known, values.get(('output_total', None), (0,))[0])):
            keys = [key for key in required if (key[0] == 'output_total') == (name == 'output')]
            if known and final:
                per_tokens[name] = {'value': str(value), 'quality': 'complete'}
            elif keys and not (name == 'input' and write_conflict) and all(key in partial_values for key in keys):
                per_tokens[name] = {'value': str(sum(partial_values[key] for key in keys)), 'quality': 'partial'}
            else:
                per_tokens[name] = {'quality': 'unavailable'}
        component_keys = {
            'input_uncached': [('input_uncached', None)],
            'input_cache_read': [('input_cache_read', None)] if not cache_unsupported else [],
            'input_cache_write': (split_writes or [('input_cache_write_unsplit', None)])
                                 if not cache_unsupported else [],
            'output': [('output_total', None)],
            'reasoning': [('reasoning_subset', None)],
        }
        token_components = {}
        for name, keys in component_keys.items():
            if keys and final and all(key in values for key in keys):
                token_components[name] = {'value': str(sum(values[key][0] for key in keys)),
                                          'quality': 'complete'}
            elif keys and all(key in partial_values for key in keys):
                token_components[name] = {'value': str(sum(partial_values[key] for key in keys)),
                                          'quality': 'partial'}
            else:
                token_components[name] = {'quality': 'unavailable'}
        response_details.append({'identity': group['identity'], 'observation_ids': group['observation_ids'],
                                 'tokens': per_tokens, 'token_components': token_components,
                                 '_components': components[component_start:],
                                 '_final': final, '_quantities': input_known and output_known,
                                 '_priced': record_priced, '_verified': not unverified})
    timely = contract._instant(inventory['observed_at']) <= contract._instant(as_of)
    tools_empty = (not tool_inputs and timely and
                   _authorized(verifier, 'tool_scope_empty', scope, inventory, inventory_proof))
    nonnegative = timely and _authorized(verifier, 'nonnegative_scope', scope, inventory, inventory_proof)
    tool_result = None
    if tool_inputs is not None:
        if not tool_inputs and tools_empty and isinstance(tool_inputs, list):
            tool_result = {'tools': [], 'components': [], 'complete': True, 'nonoverlap': True,
                           'quantities_known': True, 'prices_known': True}
        else:
            tool_result = _resolve_tools(tool_inputs, bundle, profile, scope, inventory, inventory_proof,
                                         snapshots, scenario, price_evidence, as_of, verifier)
        components.extend(tool_result['components'])
        all_prices &= tool_result['prices_known']
        uncertain |= not tool_result['nonoverlap']
    def verify_inventory(candidate, evidence, requested):
        verified = (contract._instant(candidate['observed_at']) <= contract._instant(as_of)
                    and _authorized(verifier, 'inventory', requested, candidate, evidence))
        # Tool emptiness is independently authorized for this exact scope and inventory.
        return {'inventory_verified': verified, 'billable_scope_empty': verified and tools_empty}
    coverage = completeness.calculate_completeness(inventory, inventory_proof, responses,
                                                   scope=scope, verify_inventory=verify_inventory,
                                                   tool_costs=[item['cost_usd'] for item in tool_result['tools']
                                                               if 'cost_usd' in item] if tool_result else [])
    # A response inventory does not enumerate or prove absence of tool spend.
    model_complete = (coverage['finality'].get('state') == 'not_applicable' or
                      (coverage['finality'].get('denominator') is not None and
                       coverage['finality']['numerator'] == coverage['finality']['denominator']))
    tool_complete = tools_empty or bool(tool_result and tool_result['complete'] and tool_result['nonoverlap'])
    inventory_complete = model_complete and tool_complete
    model_quantities = coverage['finality'].get('state') == 'not_applicable' or bool(responses) and all_quantities
    tool_quantities = tool_result is None or tool_result['quantities_known']
    no_overlap = not uncertain
    cost = exact_cost.calculate_cost(components, {
        'inventory_complete': inventory_complete, 'identities_resolved': no_overlap,
        'quantities_final': model_quantities and tool_quantities, 'prices_applicable': all_prices,
        'scope_proven': profile_verified and scope.get('owner_kind') == 'run',
        'nonoverlapping': no_overlap, 'excluded_cannot_reduce': True,
        'contradiction': False, 'historical_substitution': False,
        'unknown_signed_components': not nonnegative})
    conditional = scenario is not None and scenario['basis'] == 'reprice'
    if conditional:
        cost['conditional'] = True
    tokens = {}
    for name, values in token_values.items():
        fraction = coverage['measurements'][name]
        if not values:
            tokens[name] = {'quality': 'unavailable'}
        else:
            complete = (fraction.get('denominator') is not None and
                        fraction['numerator'] == fraction['denominator'] and no_overlap)
            quality = 'complete' if complete else ('proven_lower_bound' if no_overlap else 'subtotal_only')
            tokens[name] = {'value': str(sum(values)), 'quality': quality}
    for detail in response_details:
        verified = detail.pop('_verified')
        final = detail.pop('_final')
        quantities = detail.pop('_quantities')
        priced = detail.pop('_priced')
        scoped_components = detail.pop('_components')
        safe = no_overlap and verified
        detail['model_cost'] = exact_cost.calculate_cost(scoped_components, {
            'inventory_complete': final and quantities,
            'identities_resolved': safe, 'quantities_final': quantities,
            'prices_applicable': priced, 'scope_proven': safe,
            'nonoverlapping': safe, 'excluded_cannot_reduce': True,
            'contradiction': not safe, 'historical_substitution': False,
            'unknown_signed_components': False})
        detail['terms'] = []
        if safe and final:
            for component in scoped_components:
                if component['price_usd'] is None or component['unit'] is None:
                    continue
                rate = exact_cost._rate(component['price_usd'], component['unit'])
                if not exact_cost._is_terminating(rate):
                    continue
                term = {'id': component['id'],
                        'amount': exact_cost._decimal_string(component['quantity'] * rate)}
                if conditional:
                    term['conditional'] = True
                detail['terms'].append(term)
        if conditional:
            detail['model_cost']['conditional'] = True
        if not safe:
            for item in (*detail['tokens'].values(), *detail['token_components'].values()):
                if 'value' in item:
                    item['quality'] = 'subtotal_only'
    inventory_verified, _ = completeness._verified(inventory, inventory_proof, scope, verify_inventory)
    expected = {item['response_id']: item['call_id'] for item in inventory.get('expected_responses', [])}
    actual = {item['response_id']: item['call_id'] for item in responses}
    identities_complete = (inventory_verified and inventory['state'] == 'complete' and
                           not inventory['unresolved_slots'] and
                           all(inventory['coverage'][name] == 'included' for name in ('children', 'internal_checks')) and
                           not identity_uncertain and len(actual) == len(responses) and expected == actual)
    result = {'completeness': coverage, 'cost': cost, 'tokens': tokens, 'responses': response_details,
              'identity': {'state': 'complete' if identities_complete else 'partial'}}
    if tool_result is not None:
        result['tools'] = tool_result['tools']
    if epoch_inputs is not None:
        if not isinstance(epoch_inputs, list) or len(epoch_inputs) > 10000:
            raise ValueError('invalid cumulative inputs')
        contained = {contract.canonical_bytes(item['pack']) for item in bundle['evidence_objects']
                     if item.get('kind') == 'epoch_interval_evidence'}
        selected_epochs = [item for item in epoch_inputs if contract.canonical_bytes(item) in contained]
        result['epochs'] = _resolve_epochs(selected_epochs, scope, as_of, verifier)
    if owner_scopes is not None or ownership_inputs is not None or tool_ownership_inputs is not None:
        result['ownership'] = _resolve_ownership(owner_scopes, ownership_inputs, response_details, obs,
                                                  inventory, inventory_proof, coverage, as_of, verifier)
        if tool_ownership_inputs is not None:
            _resolve_tool_ownership(result['ownership'], tool_ownership_inputs, tool_inputs, tool_result,
                                    inventory, inventory_proof, as_of, verifier, conditional)
        if conditional:
            for item in result['ownership']:
                item['model_cost']['conditional'] = True
    return result
