"""Build offline reports from explicitly selected and verified evidence.

Digest matching does not authorize inputs or prove their provenance. The
caller supplies independent authorities for both selection and resolution.
"""

import copy
from fractions import Fraction

import usage_telemetry_contract as contract
import usage_telemetry_corpus as corpus
import usage_telemetry_resolution as resolution
import usage_telemetry_duration as duration
import usage_telemetry_exact_cost as exact_cost
import usage_telemetry_group_statistics as statistics
import usage_telemetry_outcomes as outcomes


def _coverage_status(value):
    if value.get('state') == 'not_applicable':
        return 'not_applicable'
    numerator, denominator = value.get('numerator'), value.get('denominator')
    if denominator is None or numerator is None:
        return 'unknown'
    if denominator == 0:
        return 'not_applicable'
    return 'complete' if numerator == denominator else 'partial'


def _selected(frozen, kind):
    return [item['value'] for item in frozen['inputs'] if item['kind'] == kind]


def _dimension_slices(frozen, resolved, scope, verify, conditional):
    records = _selected(frozen, 'dimension_evidence')
    by_observation = {}
    for record in records:
        if record['scope'] != scope:
            raise ValueError('dimension evidence scope mismatch')
        if not (verify('dimension_evidence', scope, record, record) and
                verify('dimension_privacy', scope, record, record)):
            continue
        key = record['observation_id']
        previous = by_observation.get(key)
        if previous is not None and previous['dimensions'] != record['dimensions']:
            raise ValueError('conflicting verified dimensions')
        by_observation[key] = record
    dimensions = ('run', 'opportunity', 'root_approach', 'stage', 'role', 'effort', 'attempt')
    responses = resolved.get('responses', [])
    groups = {}
    complete_dimensions = set(dimensions)
    for response in responses:
        associated = [by_observation[item.removeprefix('sha256:')]
                      for item in response['observation_ids'] if item.removeprefix('sha256:') in by_observation]
        for name in dimensions:
            values = {item['dimensions'][name] for item in associated if name in item['dimensions']}
            if len(values) != 1:
                complete_dimensions.discard(name)
                continue
            groups.setdefault((name, next(iter(values))), []).append(response)
    rows = []
    names = ('input_uncached', 'input_cache_read', 'input_cache_write', 'output', 'reasoning')
    for (dimension, value), members in sorted(groups.items()):
        prices = [item['model_cost'].get('cost_usd') for item in members]
        amount = (exact_cost._decimal_string(sum((Fraction(item) for item in prices), Fraction(0)))
                  if all(item is not None for item in prices) else None)
        complete = (dimension in complete_dimensions and len(members) == len(responses) and
                    amount is not None and resolved['cost'].get('cost_usd') == amount)
        row = {'dimension': dimension, 'value': value, 'count': len(members),
               'cost_usd': amount, 'coverage': 'complete' if complete else 'subtotal_only',
               'request_count': len(members), 'retry_count': None, 'escalation_count': None,
               'wall_ms': None}
        for name in names:
            tokens = [item.get('token_components', {}).get(name, {}) for item in members]
            row[name + '_tokens'] = (str(sum(int(item['value']) for item in tokens))
                                     if all(item.get('quality') == 'complete' and 'value' in item for item in tokens)
                                     else None)
        if conditional:
            row['conditional'] = True
        rows.append(row)
    available = {dimension for dimension, _ in groups} if responses else set()
    return rows, [name for name in dimensions if name not in available]


def _build_outcomes(frozen, resolved, scope, as_of, verify, *, tool_scope_complete):
    selected_opportunities = _selected(frozen, 'outcome_opportunity')
    selected_attempts = _selected(frozen, 'outcome_attempt')
    labels = _selected(frozen, 'acceptance_revision')
    if not selected_opportunities and not selected_attempts and not labels:
        return None
    opportunities = []
    known = set()
    for record in selected_opportunities:
        if verify('outcome_opportunity', scope, record, record):
            key = contract.canonical_bytes(record['identity'])
            if key not in known:
                opportunities.append(record['identity'])
                known.add(key)
    response_map = {}
    for response in resolved.get('responses', []):
        identifier = response['identity']['id']
        if identifier in response_map:
            raise ValueError('ambiguous response identity')
        response_map[identifier] = response
    attempts = []
    used = set()
    any_known_cost = False
    any_experimental_cost = False
    experimental_attempts = set()
    untrusted_work = False
    for record in selected_attempts:
        if (contract.canonical_bytes(record['opportunity']) not in known or
                not verify('outcome_attempt', scope, record, record)):
            untrusted_work = True
            continue
        references = record['response_ids']
        if any(reference in used for reference in references):
            raise ValueError('response belongs to multiple attempts')
        used.update(references)
        known_values = []
        fully_priced = bool(references)
        for reference in references:
            response = response_map.get(reference)
            cost = response.get('model_cost', {}) if response else {}
            if 'cost_usd' in cost:
                known_values.append(cost['cost_usd'])
            elif (cost.get('subtotal_quality') == 'proven_lower_bound' and
                  cost.get('priced_subtotal_usd') not in (None, '0')):
                known_values.append(cost['priced_subtotal_usd'])
                fully_priced = False
            else:
                fully_priced = False
        amount = (exact_cost._decimal_string(sum((Fraction(value) for value in known_values), Fraction(0)))
                  if known_values else None)
        if record['category'] != 'experimental_evaluation' and amount is not None:
            any_known_cost = True
        elif record['category'] == 'experimental_evaluation':
            experimental_attempts.add(record['attempt_id'])
            any_experimental_cost |= amount is not None
        attempts.append({'attempt_id': record['attempt_id'], 'opportunity': record['opportunity'],
                         'category': record['category'], 'observed_at': record['observed_at'],
                         'cost': amount, 'complete': (record['complete'] and fully_priced and
                                                      'cost_usd' in resolved['cost'])})
    # A complete run may contain verified responses or other billable work that
    # no selected attempt accounts for. Their absence cannot establish a
    # complete workload numerator or a complete cost-per-acceptance ratio.
    untrusted_work |= bool(set(response_map) - used)
    finality = resolved['completeness']['finality']
    if (finality.get('denominator') is not None and
            len(response_map) != finality['denominator']):
        untrusted_work = True
    total = resolved['cost'].get('cost_usd')
    accounted = None
    if total is not None:
        accounted = sum((Fraction(item['cost']) for item in attempts if item['cost'] is not None), Fraction(0))
        if any(item['cost'] is None for item in attempts):
            untrusted_work = True
    summary = outcomes.summarize_outcomes(attempts, labels, as_of=as_of, opportunities=opportunities,
        verify_acceptance=lambda label: verify('acceptance_revision', scope, label, label))
    inventories = _selected(frozen, 'experimental_inventory')
    if len(inventories) > 1:
        raise ValueError('ambiguous experimental inventory')
    verified_empty = False
    empty_inventory = None
    if inventories:
        inventory = inventories[0]
        if inventory['scope'] != scope:
            raise ValueError('experimental inventory scope mismatch')
        authorized = verify('experimental_inventory', scope, inventory, inventory)
        if authorized and inventory['state'] == 'complete':
            expected = set(inventory['expected_attempt_ids'])
            if not experimental_attempts <= expected:
                raise ValueError('experimental inventory conflicts with attempts')
            verified_empty = not expected and not experimental_attempts
            if verified_empty:
                empty_inventory = inventory
    if not any_experimental_cost and not verified_empty:
        summary['experimental_evaluation_cost'] = None
    tools = _selected(frozen, 'tool_usage')
    tools_classified = (tool_scope_complete and verified_empty and
                        all(verify('experimental_tool_exclusion', scope, tool, empty_inventory)
                            for tool in tools))
    if not tool_scope_complete or (tools and not tools_classified):
        # A complete inventory of attempts alone does not classify separate
        # tool usage, so neither zero nor a known experimental subtotal is a
        # complete experimental cost.
        summary['experimental_evaluation_cost'] = None
    if total is not None and verified_empty and tools_classified and not (set(response_map) - used):
        # Every model response is assigned, and each selected tool is
        # independently excluded from the complete experimental scope.
        summary['observed_workload_cost'] = total
        if summary['accepted_count']:
            summary['cost_per_accepted'] = outcomes._ratio_text(outcomes._amount(total), summary['accepted_count'])
        any_known_cost = True
        model_costs = [item.get('model_cost', {}).get('cost_usd') for item in resolved.get('responses', [])]
        if any(item is None for item in model_costs) or accounted != sum((Fraction(item) for item in model_costs if item is not None), Fraction(0)):
            untrusted_work = True
    elif total is not None and accounted != Fraction(total):
        untrusted_work = True
    if untrusted_work:
        summary['coverage'] = 'incomplete'
        if summary['combined_coverage'] is not None:
            summary['combined_coverage'] = 'incomplete'
        if summary['accepted_count']:
            summary['ratio_quality'] = 'descriptive_incomplete'
    if not any_known_cost:
        summary['observed_workload_cost'] = None
        summary['cost_per_accepted'] = None
        summary['ratio_quality'] = 'unavailable'
        summary['coverage'] = 'incomplete'
    return summary


def _build_durations(frozen, scope, verify):
    graphs = _selected(frozen, 'duration_graph')
    if not graphs:
        return None, []
    event_values = _selected(frozen, 'lifecycle_event')
    events = {contract.content_id(event): event for event in event_values}
    output = []
    groups = {}
    claimed = {}
    seen_graphs = set()
    for graph in sorted(graphs, key=contract.canonical_bytes):
        graph_id = contract.content_id(graph)
        if graph_id in seen_graphs:
            continue
        seen_graphs.add(graph_id)
        hashes = graph['event_hashes']
        if any(key not in events for key in hashes):
            raise ValueError('duration graph is missing selected events')
        members = [events[key] for key in hashes]
        if any(event.get('run_id') != graph['run_id'] or event.get('event') != 'step' or
               'checkpoint_id' not in event or 'span_start_ms' not in event or
               'span_end_ms' not in event or 'session_id' not in event or
               event.get('timing_source') != 'hook' for event in members):
            raise ValueError('invalid graph events')
        identifiers = {event['checkpoint_id'] for event in members}
        if any(event.get('run_id') == graph['run_id'] and
               (event.get('parent_checkpoint_id') in identifiers or event.get('checkpoint_id') in identifiers) and
               contract.content_id(event) not in hashes for event in event_values):
            raise ValueError('duration graph omits a selected or conflicting event')
        roots = [event for event in members if event['checkpoint_id'] == graph['root_checkpoint_id']]
        if len(roots) != 1:
            raise ValueError('invalid graph root')
        previous = claimed.setdefault(graph['group'], set())
        if previous.intersection(hashes):
            raise ValueError('overlapping duration group samples')
        previous.update(hashes)
        authorized = verify('duration_graph', scope, graph, graph)
        def interval(event):
            return {'id': event['checkpoint_id'], 'parent_id': event.get('parent_checkpoint_id'),
                    'start_ms': event['span_start_ms'], 'end_ms': event['span_end_ms'],
                    'clock': event['timing_source'] + ':' + event['session_id']}
        measured = duration.analyze_intervals(interval(roots[0]),
            [interval(event) for event in members if event is not roots[0]],
            complete=authorized and graph['complete'])
        output.append({'group': graph['group'], 'wall_ms': (None if measured['wall_ms'] is None else str(measured['wall_ms'])),
                       'worker_sum_ms': (None if measured['worker_sum_ms'] is None else str(measured['worker_sum_ms'])),
                       'coverage_ms': (None if measured['coverage_ms'] is None else str(measured['coverage_ms'])),
                       'exclusive_ms': (None if measured['exclusive_ms'] is None else str(measured['exclusive_ms'])),
                       'coverage_complete': measured['coverage_complete'], 'unit': 'ms',
                       'diagnostics': measured['diagnostics']})
        quality = ('unavailable' if measured['wall_ms'] is None else
                   'complete' if measured['coverage_complete'] else 'subtotal_only')
        groups.setdefault(graph['group'], []).append({'coverage': quality,
            'value': None if measured['wall_ms'] is None else str(measured['wall_ms'])})
    summaries = []
    for name, records in sorted(groups.items()):
        values = statistics.calculate_group_statistics(records, max_records=frozen['manifest']['max_records'])
        for quality, item in values.items():
            if item['n']:
                summaries.append({'name': name if quality == 'complete' else name + '_' + quality,
                                  'count': item['n'], 'median': item['median'], 'p90': item['p90'],
                                  'small_sample': item['small_sample']})
    return output, summaries


def _merge_bundle_group(bundles):
    """Merge canonical siblings before resolving shared response identities."""
    first = copy.deepcopy(bundles[0])
    collections = ('sources', 'observations', 'evidence_objects', 'inventories', 'segments', 'diagnostics')
    headers = ('schema_version', 'kind', 'profile_id', 'profile_version', 'project_id', 'run_id')
    for bundle in bundles:
        if any(bundle[field] != first[field] for field in headers):
            raise ValueError('incompatible bundle group')
    for field in collections:
        members = {}
        for bundle in bundles:
            for item in bundle[field]:
                members[contract.canonical_bytes(item)] = copy.deepcopy(item)
        first[field] = [members[key] for key in sorted(members)]
    contract.validate_usage_bundle(first)
    return first


def _combine_resolved(results, inventories, scope, verify, *, tools_nonoverlap=True):
    """Combine verified inventories and deduplicate only proven matching responses."""
    if len(results) == 1:
        return results[0]
    inventory_ids = sorted(contract.content_id(item) for item in inventories)
    if len(set(inventory_ids)) != len(inventory_ids):
        raise ValueError('repeated inventory across independent groups')
    # The exact set is independently authorized; each member is also verified
    # by the resolver, and overlapping identities are reconciled below.
    union = {'inventory_ids': inventory_ids}
    union_verified = verify('inventory_union', scope, union, union)
    expected = {}
    by_group = []
    for index, (inventory, result) in enumerate(zip(inventories, results)):
        current = {}
        for response in result.get('responses', []):
            identifier = response['identity']['id']
            if identifier in current:
                raise ValueError('ambiguous response identity')
            current[identifier] = response
        by_group.append(current)
        for item in inventory['expected_responses']:
            expected.setdefault(item['response_id'], []).append((index, item['call_id']))
    duplicate_adjustments = []
    responses = []
    response_ids = {}
    for index, current in enumerate(by_group):
        for identifier, response in current.items():
            previous = response_ids.get(identifier)
            if previous is None:
                response_ids[identifier] = response
                responses.append(response)
                continue
            members = expected.get(identifier, [])
            if len(members) < 2 or index not in {member[0] for member in members}:
                raise ValueError('unproved overlapping response')
            if (contract.canonical_bytes(previous['identity']) != contract.canonical_bytes(response['identity']) or
                    previous['tokens'] != response['tokens'] or previous['model_cost'] != response['model_cost'] or
                    previous.get('token_components') != response.get('token_components') or
                    previous.get('terms') != response.get('terms')):
                raise ValueError('conflicting overlapping response')
    for identifier, members in expected.items():
        if len(members) < 2:
            continue
        if len({call_id for _, call_id in members}) != 1:
            raise ValueError('ambiguous overlapping call identity')
        matched = [by_group[index].get(identifier) for index, _ in members]
        if any(item is None for item in matched):
            raise ValueError('overlapping response lacks identity evidence')
        first = matched[0]
        if any(contract.canonical_bytes(item['identity']) != contract.canonical_bytes(first['identity']) or
               item['tokens'] != first['tokens'] or item['model_cost'] != first['model_cost'] or
               item.get('token_components') != first.get('token_components') or
               item.get('terms') != first.get('terms') for item in matched[1:]):
            raise ValueError('conflicting overlapping response')
        if any(first['tokens'].get(name, {}).get('quality') != 'complete' or
               'value' not in first['tokens'][name] for name in ('input', 'output')):
            raise ValueError('overlapping response measurements are incomplete')
        model_cost = first['model_cost']
        if ('cost_usd' not in model_cost and
                (model_cost.get('subtotal_quality') != 'proven_lower_bound' or
                 'priced_subtotal_usd' not in model_cost)):
            raise ValueError('overlapping response cost is ambiguous')
        duplicate_adjustments.append((first, len(members) - 1))

    def combine_fraction(values, *, price=False):
        if not union_verified:
            return {'numerator': None, 'denominator': None}
        numerator = denominator = 0
        for value in values:
            if value.get('state') == 'not_applicable':
                continue
            if value.get('numerator') is None or value.get('denominator') is None:
                return {'numerator': None, 'denominator': None}
            numerator += value['numerator']
            denominator += value['denominator']
        for response, repeats in duplicate_adjustments:
            denominator -= repeats
            if not price or 'cost_usd' in response['model_cost']:
                numerator -= repeats
        if numerator < 0 or denominator < 0 or numerator > denominator:
            raise ValueError('inconsistent overlapping coverage')
        if denominator == 0:
            return {'state': 'not_applicable', 'numerator': None, 'denominator': None}
        return {'numerator': numerator, 'denominator': denominator}

    coverages = [item['completeness'] for item in results]
    coverage = {'finality': combine_fraction([item['finality'] for item in coverages]),
                'measurements': {name: combine_fraction([item['measurements'][name] for item in coverages])
                                 for name in ('input', 'output')},
                'priced': combine_fraction([item['priced'] for item in coverages], price=True),
                'zero_cost_proven': union_verified and tools_nonoverlap and all(item['zero_cost_proven'] for item in coverages)}
    tokens = {}
    for name in ('input', 'output'):
        values = [item.get('tokens', {}).get(name, {}) for item in results]
        if (union_verified and all(value.get('quality') == 'complete' and 'value' in value for value in values)):
            total = sum(int(value['value']) for value in values)
            total -= sum(int(response['tokens'][name]['value']) * repeats
                         for response, repeats in duplicate_adjustments)
            if total < 0:
                raise ValueError('inconsistent overlapping token totals')
            tokens[name] = {'value': str(total), 'quality': ('complete' if _coverage_status(
                coverage['measurements'][name]) == 'complete' else 'subtotal_only')}
        else:
            tokens[name] = {'quality': 'unavailable'}
    costs = [item['cost'] for item in results]
    cost = {'unpriced_ids': sorted({value for item in costs for value in item.get('unpriced_ids', [])})}
    if any(item.get('conditional') is True for item in costs):
        cost['conditional'] = True
    adjustments = sum((Fraction(response['model_cost'].get('cost_usd',
                                response['model_cost'].get('priced_subtotal_usd'))) * repeats
                       for response, repeats in duplicate_adjustments), Fraction(0))
    if union_verified and tools_nonoverlap and all('cost_usd' in item for item in costs):
        total = sum((Fraction(item['cost_usd']) for item in costs), Fraction(0)) - adjustments
        if total < 0:
            raise ValueError('inconsistent overlapping costs')
        cost['cost_usd'] = exact_cost._decimal_string(total)
    elif union_verified and tools_nonoverlap and all('cost_usd' in item or item.get('subtotal_quality') == 'proven_lower_bound'
                                for item in costs):
        amounts = [item['cost_usd'] if 'cost_usd' in item else item['priced_subtotal_usd'] for item in costs]
        total = sum((Fraction(value) for value in amounts), Fraction(0)) - adjustments
        if total < 0:
            raise ValueError('inconsistent overlapping costs')
        cost['priced_subtotal_usd'] = exact_cost._decimal_string(total)
        cost['subtotal_quality'] = 'proven_lower_bound'
    identity = ('complete' if union_verified and all(item.get('identity', {}).get('state') == 'complete'
                                                     for item in results) else 'partial')
    combined_ownership = []
    if union_verified and all('ownership' in item for item in results):
        ownership = [{contract.canonical_bytes(item['scope']): item for item in result['ownership']}
                     for result in results]
        common = set.intersection(*(set(items) for items in ownership))
        for key in sorted(common):
            items = [items[key] for items in ownership]
            amounts = [item['model_cost'].get('cost_usd') for item in items]
            complete = all(item['attribution'] == 'complete' for item in items)
            model_cost = {}
            members = [{entry['response_id'] for entry in item['contributors']} for item in items]
            reduction = Fraction(0)
            if complete:
                for response, repeats in duplicate_adjustments:
                    identifier = response['identity']['id']
                    group_indexes = [index for index, group in enumerate(by_group) if identifier in group]
                    assigned = [identifier in members[index] for index in group_indexes]
                    if any(assigned) and not all(assigned):
                        raise ValueError('conflicting overlapping ownership')
                    if all(assigned):
                        amount = response['model_cost'].get('cost_usd')
                        if amount is None:
                            complete = False
                            break
                        reduction += Fraction(amount) * repeats
            if complete and all(amount is not None for amount in amounts):
                total = sum((Fraction(amount) for amount in amounts), Fraction(0)) - reduction
                if total < 0:
                    raise ValueError('inconsistent overlapping ownership costs')
                model_cost['cost_usd'] = exact_cost._decimal_string(total)
            else:
                model_cost['subtotal_quality'] = 'subtotal_only'
            contributors = {}
            for item in items:
                for entry in item['contributors']:
                    identifier = (entry['provider'], entry['provider_scope'], entry['response_id'])
                    contributors.setdefault(identifier, entry)
            combined_ownership.append({'scope': items[0]['scope'], 'attribution': 'complete' if complete else 'partial',
                                       'model_cost': model_cost,
                                       'contributors': [contributors[identifier] for identifier in sorted(contributors)]})
    return {'completeness': coverage, 'cost': cost, 'tokens': tokens,
            'identity': {'state': identity}, 'ownership': combined_ownership,
            'union_verified': union_verified,
            'responses': responses if union_verified else []}


def analyze_corpus(manifest, *, verify_input, verify_evidence=None):
    """Freeze selection, then resolve only its independently authorized data."""
    frozen = corpus.freeze_corpus(manifest, verify_input=verify_input)
    selected = frozen['manifest']
    exclusions = [{'id': item['input_sha256'], 'reason': item['reason']}
                  for item in frozen['exclusions']]
    late = sorted({item['input_sha256'] for item in frozen['exclusions']
                   if item['reason'] == 'late_evidence'})
    result = {
        'schema_version': 1, 'kind': 'retrospective_report',
        'corpus_id': 'sha256:' + frozen['corpus_id'],
        'scenario_id': selected['scenario_id'], 'as_of': selected['as_of'],
        'versions': {'normalizer': selected['versions']['normalizer_version'],
                     'prices': 'unknown'},
        'source_hash': None, 'expanded_hash': None,
        'completeness': {'inventory': 'unknown', 'identity': 'unknown',
                         'measurements': 'unknown', 'pricing': 'unknown',
                         'attribution': 'unknown'},
        'coverage': {'measurements': {'numerator': None, 'denominator': None},
                     'pricing': {'numerator': None, 'denominator': None}},
        'metrics': [], 'groups': [], 'exclusions': exclusions,
        'contributors': [], 'terms': [],
        'totals': {'total_cost': None, 'derived_sum': None, 'total': None,
                   'sum_count': None},
        'late_data': late, 'identity_conflicts': [], 'unpriced': [],
        'slices': [], 'unavailable_dimensions': ['run', 'opportunity', 'root_approach', 'stage',
                                               'role', 'effort', 'attempt'],
        'top_leaves': [], 'partial_leaves': [],
    }
    if verify_evidence is None:
        return result
    if not callable(verify_evidence):
        raise ValueError('independent evidence verification is required')
    decisions = {}
    inconsistent = []
    def verify(kind, scope, subject, evidence):
        binding = {'kind': kind, 'scope': scope, 'subject': subject, 'evidence': evidence}
        digest = contract.content_id(binding)
        try:
            authorized = verify_evidence(kind, copy.deepcopy(scope), copy.deepcopy(subject),
                                         copy.deepcopy(evidence)) is True
        except Exception:
            authorized = False
        if digest in decisions and decisions[digest] != authorized:
            inconsistent.append(digest)
            return False
        decisions[digest] = authorized
        return authorized


    bundles = _selected(frozen, 'usage_bundle')
    profiles = _selected(frozen, 'source_profile')
    scenarios = _selected(frozen, 'pricing_scenario')
    snapshots = _selected(frozen, 'price_snapshot')
    contexts = _selected(frozen, 'resolution_context')
    price_evidence = _selected(frozen, 'price_evidence')
    if not bundles or not profiles:
        unresolved = {'responses': [], 'cost': {},
                      'completeness': {'finality': {'denominator': None}}}
        summary = _build_outcomes(frozen, unresolved, selected['scope'], selected['as_of'],
                                  verify, tool_scope_complete=False)
        if summary is not None:
            result['outcomes'] = summary
        durations, duration_groups = _build_durations(frozen, selected['scope'], verify)
        if durations is not None:
            result['durations'] = durations
            result['groups'] = duration_groups
        if inconsistent:
            raise ValueError('inconsistent independent verification')
        result['corpus_id'] = 'sha256:' + contract.content_id({
            'frozen_corpus_id': frozen['corpus_id'],
            'verification_decisions': [{'binding': key, 'authorized': decisions[key]}
                                       for key in sorted(decisions)]})
        return result
    if len(scenarios) > 1:
        raise ValueError('ambiguous resolution selection')
    profile_map = {}
    for profile in profiles:
        key = (profile['profile_id'], profile['profile_version'])
        previous = profile_map.get(key)
        if previous is not None and contract.canonical_bytes(previous) != contract.canonical_bytes(profile):
            raise ValueError('conflicting selected source profiles')
        profile_map[key] = profile
    groups = {}
    for bundle in bundles:
        key = (bundle['profile_id'], bundle['profile_version'], bundle['project_id'], bundle['run_id'])
        if key[:2] not in profile_map:
            raise ValueError('selected bundle has no matching profile')
        groups.setdefault(key, []).append(bundle)
    merged = [(key, _merge_bundle_group(groups[key])) for key in sorted(groups)]
    scenario = scenarios[0] if scenarios else None
    pricing_ready = False
    if scenario is not None:
        if scenario['scenario_id'] != selected['scenario_id']:
            raise ValueError('selected scenario does not match manifest')
        supplied = {contract.price_snapshot_id(item) for item in snapshots}
        expected = set(scenario['snapshot_ids'])
        if supplied - expected:
            raise ValueError('selected price snapshots do not match scenario')
        pricing_ready = bool(snapshots) and supplied == expected
    if not pricing_ready:
        snapshots = []
        price_evidence = []
    by_observation = {}
    for context in contexts + [item['context'] for _, bundle in merged for item in bundle['evidence_objects']
                               if item.get('kind') == 'resolution_context_evidence']:
        identifier = context['observation_id']
        previous = by_observation.get(identifier)
        def context_bytes(value):
            return contract.canonical_bytes({'schema_version': 1, 'kind': 'resolution_context_evidence',
                                             'context': value})
        if previous is not None and context_bytes(previous) != context_bytes(context):
            raise ValueError('conflicting selected resolution contexts')
        by_observation[identifier] = context
    contexts = [by_observation[key] for key in sorted(by_observation)]


    metadata = _selected(frozen, 'revision_metadata')
    trusted_revisions = []
    for record in metadata:
        if record['scope'] != selected['scope']:
            raise ValueError('revision metadata scope mismatch')
        if verify('revision_metadata', selected['scope'], record, record):
            trusted_revisions.append((record['source_hash'], record['expanded_hash']))
    if len(set(trusted_revisions)) > 1:
        raise ValueError('conflicting verified revisions')
    if trusted_revisions:
        result['source_hash'], result['expanded_hash'] = trusted_revisions[0]

    resolved_groups = []
    selected_inventories = []
    ownership_selections = _selected(frozen, 'ownership_selection')
    if len(ownership_selections) > 1:
        raise ValueError('ambiguous ownership selection')
    ownership_selection = ownership_selections[0] if ownership_selections else None
    tools = _selected(frozen, 'tool_usage')
    assigned_tools = {}
    for tool in tools:
        matches = [index for index, (key, bundle) in enumerate(merged)
                   if (tool['profile_id'], tool['profile_version']) == key[:2] and
                   tool['source_hash'] in {source['sha256'] for source in bundle['sources']}]
        if len(matches) != 1:
            raise ValueError('tool usage has no unique selected bundle')
        assigned_tools.setdefault(matches[0], []).append(tool)
    for index, (key, bundle) in enumerate(merged):
        inventories = [item for item in bundle['inventories'] if item['owner_scope'] == selected['scope']]
        if len(inventories) != 1:
            raise ValueError('bundle inventory is unavailable or ambiguous')
        selected_inventories.append(inventories[0])
        group_contexts = [item for item in contexts
                          if (item['profile_id'], item['profile_version']) == key[:2]]
        ownership_args = {}
        if ownership_selection is not None:
            ids = {contract.observation_id(item) for item in bundle['observations']}
            ownership_args = {'owner_scopes': ownership_selection['owner_scopes'],
                              'ownership_inputs': [item for item in ownership_selection['entries']
                                                   if item['observation_id'] in ids]}
        if tools:
            ownership_args['tool_inputs'] = assigned_tools.get(index, [])
        epoch_packs = [item['pack'] for item in bundle['evidence_objects']
                       if item.get('kind') == 'epoch_interval_evidence']
        if epoch_packs:
            ownership_args['epoch_inputs'] = epoch_packs
        resolved_groups.append(resolution.resolve_usage(bundle=bundle, profile=profile_map[key[:2]],
            contexts=group_contexts, snapshots=snapshots, scenario=scenario, price_evidence=price_evidence,
            scope=selected['scope'], as_of=selected['as_of'], verifier=verify, **ownership_args))
    for group in resolved_groups:
        for interval in group.get('epochs', {}).get('intervals', []):
            if 'id' in interval:
                result['metrics'].append({'name': 'cumulative_interval_input',
                    'value': interval['interval_aggregate'], 'unit': 'tokens',
                    'scope': 'interval', 'source': interval['id'],
                    'quality': 'complete' if interval['interval_aggregate'] is not None else 'unavailable'})
    tools_nonoverlap = True
    if tools and len(resolved_groups) > 1:
        tool_groups = []
        seen = set()
        for index, inventory in enumerate(selected_inventories):
            identities = sorted({tool['usage_id'] for tool in assigned_tools.get(index, [])})
            if seen.intersection(identities):
                raise ValueError('ambiguous tool usage across selected bundles')
            seen.update(identities)
            tool_groups.append({'inventory_id': contract.content_id(inventory), 'tool_usage_ids': identities})
        declaration = {'groups': sorted(tool_groups, key=lambda item: item['inventory_id'])}
        tools_nonoverlap = verify('tool_inventory_union', selected['scope'], declaration, declaration)
    resolved = _combine_resolved(resolved_groups, selected_inventories, selected['scope'], verify,
                                 tools_nonoverlap=tools_nonoverlap)
    conditional = resolved['cost'].get('conditional') is True
    if len(resolved_groups) == 1 or resolved.get('union_verified'):
        rows, unavailable = _dimension_slices(frozen, resolved, selected['scope'], verify, conditional)
        result['slices'].extend(rows)
        result['unavailable_dimensions'] = unavailable
    coverage = resolved['completeness']
    input_coverage = coverage['measurements']['input']
    output_coverage = coverage['measurements']['output']
    # Equal partial counts do not prove that the same responses have both fields.
    if (input_coverage == output_coverage and
            _coverage_status(input_coverage) in ('complete', 'not_applicable')):
        result['coverage']['measurements'] = {
            'numerator': input_coverage['numerator'], 'denominator': input_coverage['denominator']}
        result['completeness']['measurements'] = _coverage_status(input_coverage)
    priced = coverage['priced']
    result['coverage']['pricing'] = {'numerator': priced['numerator'],
                                      'denominator': priced['denominator']}
    result['completeness']['pricing'] = _coverage_status(priced)
    result['completeness']['inventory'] = ('unknown' if _coverage_status(coverage['finality']) == 'unknown'
                                            else 'complete')
    if len(resolved_groups) == 1 or resolved.get('union_verified'):
        result['completeness']['identity'] = resolved.get('identity', {}).get('state', 'unknown')
        result['unpriced'] = sorted(set(resolved['cost'].get('unpriced_ids', [])))
        for response in resolved.get('responses', []):
            result['terms'].extend(response.get('terms', []))
        ownership = resolved.get('ownership', [])
        root = next((item for item in ownership if item['scope'] == selected['scope']), None)
        if root is not None:
            result['completeness']['attribution'] = 'partial' if tools else root['attribution']
            response_map = {item['identity']['id']: item for item in resolved.get('responses', [])}
            for contributor in root['contributors']:
                response = response_map.get(contributor['response_id'])
                amount = response.get('model_cost', {}).get('cost_usd') if response else None
                if amount is not None:
                    row = {'id': contract.content_id(contributor), 'amount': amount}
                    if conditional:
                        row['conditional'] = True
                    result['contributors'].append(row)
        scoped_proofs = [(inventory, next((item for item in bundle['evidence_objects']
                         if contract.content_id(item) == inventory.get('evidence')), None))
                         for inventory, (_, bundle) in zip(selected_inventories, merged)]
        for item in ownership:
            scope = item['scope']
            if scope['owner_kind'] not in ('task', 'span'):
                continue
            if not verify('owner_privacy', scope, scope, scope):
                continue
            amount = item['model_cost'].get('cost_usd')
            complete = (not tools and amount is not None and item['attribution'] == 'complete' and
                        all(proof is not None and verify('leaf_billable_scope', scope, inventory, proof)
                            for inventory, proof in scoped_proofs))
            row = {'owner_id': scope['owner_id'], 'cost_usd': amount,
                   'coverage': 'complete' if complete else 'subtotal_only'}
            if conditional:
                row['conditional'] = True
            (result['top_leaves'] if complete else result['partial_leaves']).append(row)
        result['top_leaves'].sort(key=lambda row: (-Fraction(row['cost_usd']), row['owner_id']))
        result['top_leaves'] = result['top_leaves'][:5]
        observations = {contract.observation_id(item): item for _, bundle in merged for item in bundle['observations']}
        model_rows = {}
        for response in resolved.get('responses', []):
            models = set()
            for identifier in response['observation_ids']:
                identifier = identifier.removeprefix('sha256:')
                observation, context = observations.get(identifier), by_observation.get(identifier)
                if observation is None or context is None or not verify('context', selected['scope'], observation, context):
                    continue
                model = context['parameters'].get('model')
                proofs = [item for item in context['evidence_objects']
                          if item.get('kind') == 'source_parameter_evidence' and
                          item.get('field') == 'model' and item.get('value') == model]
                if (model is not None and len(proofs) == 1 and
                        verify('pricing_context', selected['scope'], observation, proofs[0]) and
                        verify('model_privacy', selected['scope'], context, model)):
                    models.add(model)
            amount = response['model_cost'].get('cost_usd')
            if len(models) == 1 and amount is not None:
                row = model_rows.setdefault(next(iter(models)), [])
                row.append(amount)
        for model, amounts in sorted(model_rows.items()):
            amount = exact_cost._decimal_string(sum((Fraction(item) for item in amounts), Fraction(0)))
            full = (len(amounts) == len(resolved.get('responses', [])) and
                    resolved['cost'].get('cost_usd') == amount)
            row = {'dimension': 'model', 'value': model, 'count': len(amounts),
                   'cost_usd': amount, 'coverage': 'complete' if full else 'subtotal_only'}
            if conditional:
                row['conditional'] = True
            result['slices'].append(row)
    if pricing_ready:
        result['versions']['prices'] = str(selected['versions']['price_schema_version'])
    for name, token in resolved.get('tokens', {}).items():
        result['metrics'].append({'name': name + '_tokens', 'value': token.get('value'),
                                  'unit': 'tokens', 'scope': selected['scope']['owner_kind'],
                                  'source': 'selected', 'quality': token['quality']})
    cost = resolved['cost']
    result['totals']['total_cost'] = None if conditional else cost.get('cost_usd')
    subtotal = (cost.get('priced_subtotal_usd', cost.get('cost_usd') if conditional else None)
                if pricing_ready else None)
    quality = (cost.get('subtotal_quality', 'complete' if conditional and subtotal is not None else 'unavailable')
               if pricing_ready else 'unavailable')
    # A sum over no priced responses is not a measured zero. Preserve an exact
    # zero when at least one response was independently and fully priced.
    if (subtotal == '0' and not any('cost_usd' in response.get('model_cost', {})
                                    for response in resolved.get('responses', []))):
        subtotal, quality = None, 'unavailable'
    result['pricing'] = {'priced_subtotal_cost': subtotal, 'subtotal_quality': quality}
    if conditional:
        result['pricing']['conditional'] = True
    tool_scope_complete = tools_nonoverlap and (len(merged) == 1 or resolved.get('union_verified') is True)
    for index, (inventory, (_, bundle)) in enumerate(zip(selected_inventories, merged)):
        proof = next((item for item in bundle['evidence_objects']
                      if contract.content_id(item) == inventory.get('evidence')), None)
        if proof is None or not verify('inventory', selected['scope'], inventory, proof):
            tool_scope_complete = False
            continue
        identities = sorted({item['usage_id'] for item in assigned_tools.get(index, [])})
        if identities:
            declaration = {'inventory_evidence': proof, 'tool_usage_ids': identities}
            if not verify('tool_inventory', selected['scope'], inventory, declaration):
                tool_scope_complete = False
        elif not verify('tool_scope_empty', selected['scope'], inventory, proof):
            if not tools or not verify('tool_inventory', selected['scope'], inventory,
                                       {'inventory_evidence': proof, 'tool_usage_ids': []}):
                tool_scope_complete = False
    summary = _build_outcomes(frozen, resolved, selected['scope'], selected['as_of'], verify,
                              tool_scope_complete=tool_scope_complete)
    if summary is not None:
        if conditional:
            summary['conditional'] = True
        result['outcomes'] = summary
    durations, groups = _build_durations(frozen, selected['scope'], verify)
    if durations is not None:
        result['durations'] = durations
        result['groups'] = groups
    if inconsistent:
        raise ValueError('inconsistent independent verification')
    result['corpus_id'] = 'sha256:' + contract.content_id({
        'frozen_corpus_id': frozen['corpus_id'],
        'verification_decisions': [{'binding': key, 'authorized': decisions[key]}
                                   for key in sorted(decisions)]})
    return result
