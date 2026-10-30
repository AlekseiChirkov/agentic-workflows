"""Resolve explicitly supplied response identities without discovering sources.

Link evidence must be verified by the caller against its source profile and
scope before it is marked one-to-one. An evidence identifier is a reference,
not proof of authenticity or privacy by itself.
"""
import re

_PRIVATE_ID = re.compile(r'^sha256:[0-9a-f]{64}$')
_PROVIDER = re.compile(r'^[a-z][a-z0-9_-]{0,63}$')
_LIMIT = 10000


def _private(value):
    if not isinstance(value, str) or not _PRIVATE_ID.fullmatch(value):
        raise ValueError('invalid opaque identity')


def _scope(value):
    if not isinstance(value, str) or not _PROVIDER.fullmatch(value):
        raise ValueError('invalid provider')


def _record(value, fields):
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('invalid identity record')


def resolve_response_identities(observations, call_links, *, max_observations=_LIMIT):
    """Group observations, retaining ambiguity without double-counting.

    The caller supplies a bounded sequence of sanitized identity records and
    independently verified links. No content, path, source discovery or network
    access is accepted. A resolved response can be marked non-additive if an
    unresolved observation could overlap it.
    """
    if (type(max_observations) is not int or not 0 <= max_observations <= _LIMIT or
            not isinstance(observations, (list, tuple)) or
            not isinstance(call_links, (list, tuple)) or
            len(observations) > max_observations or len(call_links) > _LIMIT):
        raise ValueError('identity input exceeds limits or is invalid')

    unique = {}
    for item in observations:
        _record(item, {'observation_id', 'provider', 'provider_scope', 'response_id',
                       'call_id', 'session_id'})
        _scope(item['provider'])
        _private(item['observation_id'])
        _private(item['provider_scope'])
        _private(item['session_id'])
        for field in ('response_id', 'call_id'):
            if item[field] is not None:
                _private(item[field])
        previous = unique.get(item['observation_id'])
        if previous is not None and previous != item:
            raise ValueError('conflicting observation identity')
        unique[item['observation_id']] = item

    aliases = {}
    for item in call_links:
        _record(item, {'provider', 'provider_scope', 'call_id', 'response_id',
                       'evidence_id', 'one_to_one_verified'})
        _scope(item['provider'])
        for field in ('provider_scope', 'call_id', 'evidence_id'):
            _private(item[field])
        if item['response_id'] is not None:
            _private(item['response_id'])
        if type(item['one_to_one_verified']) is not bool:
            raise ValueError('invalid verification state')
        if item['one_to_one_verified']:
            call = (item['provider'], item['provider_scope'], item['call_id'])
            aliases.setdefault(call, set()).add(item['response_id'])

    responses = {}
    call_responses = {}
    call_only = []
    unresolved = []
    uncertain_scopes = set()
    for item in unique.values():
        provider, scope = item['provider'], item['provider_scope']
        response, call = item['response_id'], item['call_id']
        if response is not None:
            key = (provider, scope, 'response', response)
            responses.setdefault(key, set()).add(item['observation_id'])
            if call is not None:
                call_responses.setdefault((provider, scope, call), set()).add(response)
        elif call is not None:
            call_only.append(item)
        else:
            uncertain_scopes.add((provider, scope))
            unresolved.append({'observation_id': item['observation_id'],
                               'reason': 'identity_unavailable'})

    excluded = set()
    for item in call_only:
        call = (item['provider'], item['provider_scope'], item['call_id'])
        observed = call_responses.get(call, set())
        verified = aliases.get(call, set())
        # An explicitly verified unique link must agree with all observed
        # responses; no arrival order may settle a conflicting relationship.
        valid = len(verified) == 1
        if valid:
            target = next(iter(verified))
            valid = (not observed if target is None else not (observed - {target}))
        if valid:
            kind, value = ('call', call[2]) if target is None else ('response', target)
            key = (call[0], call[1], kind, value)
            responses.setdefault(key, set()).add(item['observation_id'])
        else:
            uncertain_scopes.add(call[:2])
            unresolved.append({'observation_id': item['observation_id'],
                               'reason': 'identity_ambiguous'})
            for response in observed | {v for v in verified if v is not None}:
                excluded.add((call[0], call[1], 'response', response))

    result = []
    for key, ids in sorted(responses.items()):
        provider, scope, kind, value = key
        result.append({'identity': {'provider': provider, 'provider_scope': scope,
                                    'kind': kind, 'id': value},
                       'observation_ids': sorted(ids),
                       'additive': key not in excluded and key[:2] not in uncertain_scopes})
    unresolved.sort(key=lambda item: (item['observation_id'], item['reason']))
    return {'responses': result, 'unresolved': unresolved}
