"""Synthetic independently authorized owner, usage and price evidence."""
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

contract = load('contract', 'scripts/usage_telemetry_contract.py')
profiles = load('profiles', 'tests/usage-source-profiles.py')

def opaque(char):
    return 'sha256:' + char * 64

def inventory(responses=('1', '2'), *, coverage='included'):
    calls = [{'call_id': opaque(char)} for char in responses]
    value = {
        'schema_version': 1, 'kind': 'inventory', 'profile_id': 'fixture',
        'profile_version': '1', 'source_hash': 'a' * 64,
        'owner_scope': {'owner_kind': 'run', 'owner_id': opaque('b')},
        'window': {'start': '2026-01-01T00:00:00Z', 'end': '2026-01-01T01:00:00Z'},
        'observed_at': '2026-01-01T01:01:00Z', 'state': 'complete', 'evidence': None,
        'expected_calls': calls,
        'expected_responses': [{'call_id': opaque(char), 'response_id': opaque(char)} for char in responses],
        'unresolved_slots': [],
        'coverage': {'children': 'included', 'internal_checks': 'included', 'tools': coverage},
    }
    return bind(value)


def bind(value):
    evidence = {'schema_version': 1, 'kind': 'inventory_evidence',
                'profile_id': value['profile_id'], 'profile_version': value['profile_version'],
                'source_hash': value['source_hash'],
                'inventory_digest': contract.content_id({k: v for k, v in value.items() if k != 'evidence'})}
    value['evidence'] = contract.content_id(evidence)
    contract.validate_inventory(value)
    contract.validate_evidence_object(evidence)
    return value, evidence



def price_fixture():
    source = 'a' * 64
    period = {'schema_version': 1, 'kind': 'price_period_evidence', 'source_hash': 'b' * 64,
              'start': '2025-01-01T00:00:00Z', 'end': '2027-01-01T00:00:00Z'}
    time = {'schema_version': 1, 'kind': 'execution_time_evidence', 'profile_id': 'profile',
            'source_hash': source, 'record_number': 1, 'value': '2026-01-01T00:00:00Z'}
    params = {}
    evidence = [period, time]
    for field, value in {'model': 'vendor/model', 'service_tier': 'standard',
                         'region': 'example-region', 'modality': 'text'}.items():
        obj = {'schema_version': 1, 'kind': 'source_parameter_evidence', 'profile_id': 'profile',
               'source_hash': source, 'record_number': 1, 'field': field, 'value': value}
        evidence.append(obj)
        params[field] = {'value': value, 'evidence': contract.content_id(obj)}
    rate = {'component': 'input_uncached', 'usd': '2', 'unit': 'tokens', 'unit_quantity': 1000000,
            'cache_ttl_seconds': None, 'threshold': None, 'multiplier': {'state': 'none'}}
    snapshot = {'schema_version': 1, 'kind': 'price_snapshot', 'currency': 'USD',
                'retrieved_at': '2026-02-01T00:00:00Z', 'model': 'vendor/model', 'aliases': [],
                'modality': 'text', 'service_tier': 'standard', 'region': 'example-region',
                'effective_period': {'state': 'known', 'start': period['start'], 'end': period['end'],
                                     'evidence': contract.content_id(period)},
                'rates': [rate], 'primary_sources': ['https://example.org/pricing']}
    scenario = {'schema_version': 1, 'kind': 'pricing_scenario', 'scenario_id': 'baseline',
                'basis': 'at_execution', 'currency': 'USD', 'display_precision': 4,
                'snapshot_ids': [contract.price_snapshot_id(snapshot)],
                'source_parameters': params, 'assumptions': {}, 'threshold_rules': []}
    request = {'component': 'input_uncached', 'unit': 'tokens', 'cache_ttl_seconds': None,
               'tool_id': None, 'execution_time': {'value': time['value'], 'evidence': contract.content_id(time)},
               'profile_id': 'profile', 'source_hash': source, 'record_number': 1,
               'operands': {}, 'verified_aliases': []}
    trusted = {contract.content_id(item) for item in evidence}
    return [snapshot], scenario, request, evidence, trusted


class Verifier:
    """Explicit independent authority: exact binding, never an input flag."""
    def __init__(self, allowed):
        self.allowed = copy.deepcopy(allowed)
        self.calls = []

    def __call__(self, kind, scope, subject, evidence):
        binding = (kind, scope, subject, evidence)
        self.calls.append(copy.deepcopy(binding))
        return binding in self.allowed


def fixture():
    profile = profiles.profile()
    inventory_value, _ = inventory()
    inventory_value['profile_id'] = profile['profile_id']
    inventory_value['window']['end'] = '2029-01-01T00:00:00Z'
    inventory_value['observed_at'] = '2029-01-01T00:00:01Z'
    inventory_value, inventory_evidence = bind(inventory_value)
    scope = inventory_value['owner_scope']
    bundle = profiles.split_bundle()
    bundle['observations'] = []
    bundle['evidence_objects'] = [inventory_evidence]
    bundle['inventories'] = [inventory_value]
    contexts = []
    raw = {'input': 1000, 'read': 200, 'write': 200, 'short': 100,
           'long': 100, 'output': 100, 'reasoning': 25}
    for record, char in ((1, '1'), (2, '2')):
        normalized = contract.normalize_source_counters(
            profile, {'usage': raw}, profile_version='1', source_hash='a' * 64,
            record_number=record)
        for measurement in normalized['measurements'].values():
            parts = [item['tokens'] for item in measurement] if isinstance(measurement, list) else [measurement]
            for part in parts:
                if part['measurement_state'] == 'partial':
                    part['measurement_state'] = 'final'
        observation = profiles.split_bundle()['observations'][0]
        observation.update(record_number=record, response_id=opaque(char), call_id=opaque(char),
                           source_time=('2026-01-01T00:00:00Z' if record == 1 else '2028-01-01T00:00:00Z'),
                           source_time_quality='verified',
                           observed_at=('2026-01-02T03:04:05Z' if record == 1 else '2028-01-02T03:04:05Z'),
                           measurements=normalized['measurements'])
        bundle['observations'].append(observation)
        bundle['evidence_objects'].extend(normalized['evidence_objects'])
        # All supplemental facts are exact, per-observation evidence declarations.
        context = {'observation_id': contract.observation_id(observation),
                   'profile_id': profile['profile_id'], 'profile_version': '1',
                   'source_hash': observation['source_hash'], 'record_number': record,
                   'provider_scope': observation['provider_scope'], 'counter_scope': 'response_total',
                   'provider': profile['provider'], 'session_id': opaque('e'),
                   'event': {'kind': 'snapshot', 'final': True},
                   'execution_time': '2026-01-01T00:00:00Z' if record == 1 else '2028-01-01T00:00:00Z',
                   'parameters': {'model': 'vendor/model', 'service_tier': 'standard',
                                  'region': 'example-region', 'modality': 'text'},
                   'cache_ttl_seconds': {'5m': 300, '1h': 3600}}
        context['evidence_objects'] = [
            {'schema_version': 1, 'kind': 'execution_time_evidence', 'profile_id': profile['profile_id'],
             'source_hash': observation['source_hash'], 'record_number': record, 'value': context['execution_time']},
            *[{'schema_version': 1, 'kind': 'source_parameter_evidence', 'profile_id': profile['profile_id'],
               'source_hash': observation['source_hash'], 'record_number': record, 'field': field, 'value': value}
              for field, value in context['parameters'].items()],
            *[{'schema_version': 1, 'kind': 'rate_parameter_evidence', 'profile_id': profile['profile_id'],
               'source_hash': observation['source_hash'], 'record_number': record,
               'field': 'cache_ttl_seconds', 'value': value}
              for value in context['cache_ttl_seconds'].values()]]
        contexts.append(context)
    snapshots, scenario, _, evidence, _ = price_fixture()
    snapshot = snapshots[0]
    snapshot['rates'] = [
        {'component': name, 'usd': amount, 'unit': 'tokens', 'unit_quantity': 1000000,
         'cache_ttl_seconds': ttl, 'threshold': None, 'multiplier': {'state': 'none'}}
        for name, amount, ttl in [('input_uncached', '2', None), ('input_cache_read', '0.2', None),
                                   ('input_cache_write', '2.5', 300), ('input_cache_write', '4', 3600),
                                   ('output', '10', None)]]
    scenario['snapshot_ids'] = [contract.price_snapshot_id(snapshot)]
    # Existing applicability evidence schema is itself per-record. Additional
    # context attestations bind the profile, source, scope, record and value.
    price_evidence = [item for item in evidence if item['kind'] == 'price_period_evidence']
    price_evidence.append({'schema_version': 1, 'kind': 'price_snapshot_evidence',
                           'snapshot_id': contract.price_snapshot_id(snapshot), 'source_hash': 'b' * 64})
    allowed = []
    allowed.append(('inventory', scope, inventory_value, inventory_evidence))
    allowed.append(('profile', scope, profile, profile))
    for observation, context in zip(bundle['observations'], contexts):
        allowed.append(('response_privacy', scope, observation, observation))
        allowed.append(('context', scope, observation, context))
        for proof in context['evidence_objects']:
            allowed.append(('pricing_context', scope, observation, proof))
        for field, measurement in observation['measurements'].items():
            if field == 'input_cache_write':
                for part in measurement:
                    proof = next(e for e in bundle['evidence_objects']
                                 if contract.content_id(e) == part['tokens']['evidence'])
                    allowed.append(('measurement', scope, {'observation': observation, 'field': field,
                                                          'ttl': part['ttl']}, proof))
            elif 'evidence' in measurement:
                proof = next(e for e in bundle['evidence_objects']
                             if contract.content_id(e) == measurement['evidence'])
                allowed.append(('measurement', scope, {'observation': observation, 'field': field}, proof))
    # A derived value is trustworthy only when each source operand has an
    # independently authorized record and scope binding of its own.
    objects = {contract.content_id(item): item for item in bundle['evidence_objects']}
    for observation in bundle['observations']:
        def authorize_operand(digest):
            proof = objects[digest]
            if proof['kind'] == 'derived_measurement_evidence':
                for operand in proof['operands']:
                    authorize_operand(operand)
            else:
                subject = {'observation': observation, 'field': proof['field']}
                if 'ttl' in proof:
                    subject['ttl'] = proof['ttl']
                binding = ('measurement', scope, subject, proof)
                if binding not in allowed:
                    allowed.append(binding)
        for measurement in observation['measurements'].values():
            parts = [part['tokens'] for part in measurement] if isinstance(measurement, list) else [measurement]
            for part in parts:
                if 'evidence' in part:
                    authorize_operand(part['evidence'])
    for proof in price_evidence:
        allowed.append(('price', scope, snapshot, proof))
    contract.validate_source_profile(profile)
    contract.validate_usage_bundle(bundle)
    contract.validate_price_snapshot(snapshot)
    contract.validate_pricing_scenario(scenario)
    return {'bundle': bundle, 'profile': profile, 'contexts': contexts,
            'snapshots': [snapshot], 'scenario': scenario, 'price_evidence': price_evidence,
            'scope': scope, 'as_of': '2029-01-02T00:00:00Z'}, allowed
