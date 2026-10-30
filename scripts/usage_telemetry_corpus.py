"""Freeze explicitly selected retrospective inputs without discovering history.

The verifier is a caller-supplied trust boundary. It must independently check
access, provenance, event validity and first-observed times (including nested
observation timestamps) against durable local evidence, rather than echoing
claims in a manifest or selected file. A digest establishes byte integrity
only; it does not establish provenance or authorization.
"""

import copy
import hashlib
import os
from pathlib import Path
import subprocess

import usage_telemetry_contract as contract
from usage_telemetry_sources import _open_regular, _path_parts



def _validate_lifecycle(data):
    """Run the producer's journal validator over exactly one selected event."""
    value = contract.parse_json(data)
    contract._bounded_tree(value)
    if not isinstance(value, dict):
        raise ValueError('invalid lifecycle event')
    encoded = contract.canonical_bytes(value)
    try:
        checked = subprocess.run(['bash', str(Path(__file__).with_name('log-step.sh')),
                                  'lint', '--stdin'], input=encoded + b'\n',
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 timeout=30, check=False)
        result = contract.parse_json(checked.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        raise ValueError('lifecycle validator unavailable') from None
    if (checked.returncode != 0 or not isinstance(result, dict) or
            result.get('kind') != 'summary' or result.get('status') != 'ok' or
            result.get('files') != 1 or result.get('lines') != 1 or
            result.get('violations') != 0 or result.get('invalid_lines') != 0):
        raise ValueError('invalid lifecycle event')
    return value



def _validate_resolution_context(data):
    try:
        validator = contract.validate_resolution_context
    except AttributeError:
        raise ValueError('resolution validator unavailable') from None
    return contract._validate_json(data, contract.OBSERVATION_LIMIT, validator)


def _validate_price_evidence(data):
    try:
        from usage_telemetry_applicability import _validate_applicability_evidence
    except ImportError:
        raise ValueError('price evidence validator unavailable') from None
    def validate(value):
        _validate_applicability_evidence(value)
        return value
    return contract._validate_json(data, contract.OBSERVATION_LIMIT, validate)


_VALIDATORS = {
    'lifecycle_event': _validate_lifecycle,
    'source_profile': contract.validate_source_profile_json,
    'pricing_scenario': contract.validate_pricing_scenario_json,
    'resolution_context': _validate_resolution_context,
    'price_evidence': _validate_price_evidence,
    'usage_bundle': contract.validate_usage_bundle_json,
    'inventory': contract.validate_inventory_json,
    'price_snapshot': contract.validate_price_snapshot_json,
    'acceptance_revision': contract.validate_acceptance_revision_json,
    'outcome_opportunity': contract.validate_outcome_opportunity_json,
    'outcome_attempt': contract.validate_outcome_attempt_json,
    'duration_graph': contract.validate_duration_graph_json,
    'experimental_inventory': contract.validate_experimental_inventory_json,
    'revision_metadata': contract.validate_revision_metadata_json,
    'ownership_selection': contract.validate_ownership_selection_json,
    'dimension_evidence': contract.validate_dimension_evidence_json,
    'tool_usage': contract.validate_tool_usage_json,
}


def _read_entry(item):
    prefix = item.get('verified_prefix_bytes')
    size = item['size_bytes'] if prefix is None else prefix
    descriptor = _open_regular(item['local_path'])
    try:
        metadata = os.fstat(descriptor)
        if ((prefix is None and metadata.st_size != item['size_bytes']) or
                (prefix is not None and metadata.st_size < size)):
            raise ValueError('selected input size changed')
        chunks = []
        remaining = size
        while remaining:
            part = os.read(descriptor, min(remaining, 1024 * 1024))
            if not part:
                raise ValueError('selected input ended prematurely')
            chunks.append(part)
            remaining -= len(part)
        if prefix is None and os.fstat(descriptor).st_size != size:
            raise ValueError('selected input size changed')
        data = b''.join(chunks)
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('selected input digest mismatch')
        return data
    except (OSError, OverflowError):
        raise ValueError('cannot read selected input') from None
    finally:
        os.close(descriptor)


def _cutoff(timestamp, as_of):
    contract._timestamp(timestamp)
    return contract._instant(timestamp) > contract._instant(as_of)


def freeze_corpus(manifest, *, verify_input):
    """Validate, authorize, and freeze a selection before report calculations.

    ``verify_input(entry, decoded_value, scope)`` must return a dictionary
    containing its independently verified scope and first observation time.
    Optional member_times maps each undated segment, diagnostic, epoch wrapper,
    or nested epoch evidence content hash
    to its independently verified first observation time. Unproved members are
    excluded. Decisions are included in the resulting corpus identity.
    It must raise for any untrusted record or unverifiable nested timestamps.
    Unknown formats are refused rather than silently joined or treated as
    trusted evidence. Lifecycle events also pass the existing journal validator.
    """
    frozen = copy.deepcopy(manifest)
    contract.validate_analysis_corpus(frozen)
    if not callable(verify_input):
        raise ValueError('independent input verification is required')
    for item in frozen['inputs']:
        _path_parts(item['local_path'])
        if item['kind'] not in _VALIDATORS:
            raise ValueError('input validator is unavailable')

    excluded_hashes = {item['input_sha256'] for item in frozen['exclusions']}
    if any(item['sha256'] in excluded_hashes for item in frozen['inputs']):
        raise ValueError('selected input is explicitly excluded')
    inputs = []
    exclusions = copy.deepcopy(frozen['exclusions'])
    decisions = []
    records = 0
    for item in sorted(frozen['inputs'], key=contract.canonical_bytes):
        data = _read_entry(item)
        try:
            value = _VALIDATORS[item['kind']](data)
        except (ValueError, UnicodeError, RecursionError):
            raise ValueError('invalid selected input') from None
        try:
            proof = verify_input(copy.deepcopy(item), copy.deepcopy(value),
                                 copy.deepcopy(frozen['scope']))
        except Exception:
            raise ValueError('input verification failed') from None
        if (not isinstance(proof, dict) or
                not {'scope', 'observed_at'} <= set(proof) or
                set(proof) - {'scope', 'observed_at', 'member_times'} or
                proof['scope'] != frozen['scope']):
            raise ValueError('input verification failed')
        times = proof.get('member_times', {})
        if not isinstance(times, dict):
            raise ValueError('invalid member verification')
        eligible_members = {}
        if item['kind'] == 'usage_bundle':
            for field in ('segments', 'diagnostics'):
                for member in value[field]:
                    eligible_members[contract.content_id(member)] = member
            for member in value['evidence_objects']:
                if member.get('kind') == 'epoch_interval_evidence':
                    eligible_members[contract.content_id(member)] = member
                    for nested in member['pack']['evidence_objects']:
                        eligible_members[contract.content_id(nested)] = nested
                if member.get('kind') == 'resolution_context_evidence':
                    eligible_members[contract.content_id(member)] = member
                    for nested in member['context']['evidence_objects']:
                        eligible_members[contract.content_id(nested)] = nested
        elif item['kind'] == 'resolution_context':
            for member in value['evidence_objects']:
                eligible_members[contract.content_id(member)] = member
        elif item['kind'] == 'ownership_selection':
            for member in value['entries']:
                eligible_members[contract.content_id(member)] = member
        elif item['kind'] == 'tool_usage':
            for member in value['evidence_objects']:
                eligible_members[contract.content_id(member)] = member
        for key, timestamp in times.items():
            if key not in eligible_members:
                raise ValueError('invalid member verification')
            contract._timestamp(timestamp)
        decisions.append({'input_sha256': item['sha256'], 'proof': copy.deepcopy(proof)})
        records += 1
        if item['kind'] == 'usage_bundle':
            records += sum(len(value[field]) for field in
                           ('observations', 'inventories', 'segments', 'diagnostics', 'evidence_objects'))
            records += sum(len(member['context']['evidence_objects'])
                           for member in value['evidence_objects']
                           if member.get('kind') == 'resolution_context_evidence')
            records += sum(len(member['pack']['observations']) + len(member['pack']['evidence_objects'])
                           for member in value['evidence_objects']
                           if member.get('kind') == 'epoch_interval_evidence')
        elif item['kind'] == 'resolution_context':
            records += len(value['evidence_objects'])
        elif item['kind'] == 'ownership_selection':
            records += len(value['entries']) + len(value['owner_scopes'])
        elif item['kind'] == 'tool_usage':
            records += len(value['evidence_objects'])
        if records > frozen['max_records']:
            raise ValueError('selected input record limit exceeded')
        late = _cutoff(proof['observed_at'], frozen['as_of'])
        if late:
            exclusions.append({'input_sha256': item['sha256'], 'reason': 'late_evidence'})
            continue
        if item['kind'] == 'usage_bundle':
            filtered = []
            for observation in value['observations']:
                if _cutoff(observation['observed_at'], frozen['as_of']):
                    late = True
                else:
                    filtered.append(observation)
            value['observations'] = filtered
            inventories = []
            for inventory in value['inventories']:
                if _cutoff(inventory['observed_at'], frozen['as_of']):
                    late = True
                else:
                    inventories.append(inventory)
            value['inventories'] = inventories
            references = set()
            for observation in filtered:
                for field, measurement in observation['measurements'].items():
                    if field == 'input_cache_write':
                        references.update(part['tokens']['evidence'] for part in measurement
                                          if 'evidence' in part['tokens'])
                    elif 'evidence' in measurement:
                        references.add(measurement['evidence'])
            references.update(inventory['evidence'] for inventory in inventories
                              if inventory['evidence'] is not None)
            by_hash = {contract.content_id(evidence): evidence
                       for evidence in value['evidence_objects']}
            pending = list(references)
            while pending:
                evidence = by_hash.get(pending.pop())
                if evidence and evidence['kind'] == 'derived_measurement_evidence':
                    for operand in evidence['operands']:
                        if operand not in references:
                            references.add(operand)
                            pending.append(operand)
            retained = [evidence for evidence in value['evidence_objects']
                        if contract.content_id(evidence) in references]
            unknown_members = False
            observation_ids = {contract.observation_id(observation) for observation in filtered}
            for wrapper in value['evidence_objects']:
                if wrapper.get('kind') != 'resolution_context_evidence':
                    continue
                if wrapper['context']['observation_id'] not in observation_ids:
                    continue
                timestamp = times.get(contract.content_id(wrapper))
                if timestamp is None:
                    unknown_members = True
                    continue
                if _cutoff(timestamp, frozen['as_of']):
                    late = True
                    continue
                wrapper = copy.deepcopy(wrapper)
                nested = []
                for member in wrapper['context']['evidence_objects']:
                    member_time = times.get(contract.content_id(member))
                    if member_time is None:
                        unknown_members = True
                    elif _cutoff(member_time, frozen['as_of']):
                        late = True
                    else:
                        nested.append(member)
                wrapper['context']['evidence_objects'] = nested
                retained.append(wrapper)
            for wrapper in value['evidence_objects']:
                if wrapper.get('kind') != 'epoch_interval_evidence':
                    continue
                pack = wrapper['pack']
                hashes = [contract.content_id(wrapper)] + [contract.content_id(member)
                          for member in pack['evidence_objects']]
                observed = [times.get(digest) for digest in hashes]
                if any(timestamp is None for timestamp in observed):
                    unknown_members = True
                    continue
                if (_cutoff(pack['observed_at'], frozen['as_of']) or
                        any(_cutoff(timestamp, frozen['as_of']) for timestamp in observed)):
                    late = True
                    continue
                if any(contract.observation_id(item) not in observation_ids for item in pack['observations']):
                    continue
                retained_hashes = {contract.content_id(item) for item in retained}
                if any(contract.content_id(item) not in retained_hashes for item in pack['evidence_objects']):
                    unknown_members = True
                    continue
                retained.append(wrapper)
            value['evidence_objects'] = retained
            for field in ('segments', 'diagnostics'):
                members = []
                for member in value[field]:
                    timestamp = times.get(contract.content_id(member))
                    if timestamp is None:
                        unknown_members = True
                    elif _cutoff(timestamp, frozen['as_of']):
                        late = True
                    else:
                        members.append(member)
                value[field] = members
            if unknown_members:
                exclusions.append({'input_sha256': item['sha256'],
                                   'reason': 'timing_unavailable'})
            if late:
                exclusions.append({'input_sha256': item['sha256'], 'reason': 'late_evidence'})
            contract.validate_usage_bundle(value)
        elif item['kind'] == 'resolution_context':
            retained = []
            unknown_members = False
            late_members = False
            for member in value['evidence_objects']:
                timestamp = times.get(contract.content_id(member))
                if timestamp is None:
                    unknown_members = True
                elif _cutoff(timestamp, frozen['as_of']):
                    late_members = True
                else:
                    retained.append(member)
            value['evidence_objects'] = retained
            if unknown_members:
                exclusions.append({'input_sha256': item['sha256'], 'reason': 'timing_unavailable'})
            if late_members:
                exclusions.append({'input_sha256': item['sha256'], 'reason': 'late_evidence'})
            contract.validate_resolution_context(value)
        elif item['kind'] == 'tool_usage':
            if _cutoff(value['observed_at'], frozen['as_of']):
                exclusions.append({'input_sha256': item['sha256'], 'reason': 'late_evidence'})
                continue
            reasons = set()
            for member in value['evidence_objects']:
                timestamp = times.get(contract.content_id(member))
                if timestamp is None:
                    reasons.add('timing_unavailable')
                elif _cutoff(timestamp, frozen['as_of']):
                    reasons.add('late_evidence')
            if reasons:
                for reason in sorted(reasons):
                    exclusions.append({'input_sha256': item['sha256'], 'reason': reason})
                continue
        elif item['kind'] == 'ownership_selection':
            if _cutoff(value['observed_at'], frozen['as_of']):
                exclusions.append({'input_sha256': item['sha256'], 'reason': 'late_evidence'})
                continue
            retained = []
            reasons = set()
            for member in value['entries']:
                timestamp = times.get(contract.content_id(member))
                if timestamp is None:
                    reasons.add('timing_unavailable')
                elif _cutoff(timestamp, frozen['as_of']) or _cutoff(member['observed_at'], frozen['as_of']):
                    reasons.add('late_evidence')
                else:
                    retained.append(member)
            value['entries'] = retained
            for reason in sorted(reasons):
                exclusions.append({'input_sha256': item['sha256'], 'reason': reason})
            contract.validate_ownership_selection(value)
        elif (item['kind'] in ('inventory', 'outcome_opportunity', 'outcome_attempt',
                                'acceptance_revision', 'duration_graph', 'experimental_inventory', 'revision_metadata',
                                'dimension_evidence') and
                _cutoff(value['observed_at'], frozen['as_of'])):
            exclusions.append({'input_sha256': item['sha256'], 'reason': 'late_evidence'})
            continue
        inputs.append({'kind': item['kind'], 'sha256': item['sha256'], 'value': value})
    # Exclusions are a set, even when several late records share one input.
    unique_exclusions = {contract.canonical_bytes(item): item for item in exclusions}
    identity = {'manifest_id': contract.analysis_corpus_id(frozen),
                'verified_decisions': sorted(decisions, key=contract.canonical_bytes)}
    return {'manifest': frozen, 'corpus_id': contract.content_id(identity),
            'verified_decisions': identity['verified_decisions'], 'inputs': inputs,
            'exclusions': [unique_exclusions[key] for key in sorted(unique_exclusions)]}
