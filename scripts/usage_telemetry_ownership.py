"""Pure resolution of explicitly authorized usage ownership evidence.

Trusted source and attribution references are supplied by the caller after
independent verification; identifiers and hashes are not authenticity proofs.
"""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import importlib.util
from pathlib import Path
import re

_spec = importlib.util.spec_from_file_location(
    '_usage_contract', Path(__file__).with_name('usage_telemetry_contract.py'))
_contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_contract)


def measurement_is_verified(observation, field, evidence_objects, authorized_sources):
    """Resolve a measurement against an independently authorized scope attestation.

    An attestation binds profile, source hash, provider account scope,
    counter scope, record number, field and the measurement evidence digest.
    It is separate from measurement evidence, avoiding a hash
    cycle; the caller must authenticate this binding before supplying it. The
    shared evidence schema binds profile, source, record, field and value only,
    so it cannot authenticate or establish either scope by itself.
    """
    try:
        if not isinstance(evidence_objects, list) or not isinstance(authorized_sources, list):
            return False
        source = {key: observation[key] for key in
                  ('profile_id', 'source_hash', 'provider_scope', 'counter_scope',
                   'record_number')}
        source['field'] = field
        source['evidence'] = observation['measurements'][field]['evidence']
        if source not in authorized_sources:
            return False
        return any(_contract.verify_measurement_evidence(observation, field, evidence)
                   for evidence in evidence_objects)
    except (KeyError, TypeError, ValueError, RecursionError):
        return False


def _time(value):
    if not isinstance(value, str) or not re.fullmatch(
        r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z', value
    ):
        raise ValueError('invalid observation time')
    try:
        return datetime.fromisoformat(value[:-1] + '+00:00').astimezone(timezone.utc)
    except ValueError:
        raise ValueError('invalid observation time') from None


def _opaque(value):
    return isinstance(value, str) and re.fullmatch(r'sha256:[0-9a-f]{64}', value) is not None


def _amount(value):
    if not isinstance(value, str) or re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?', value) is None:
        raise ValueError('invalid exact amount')
    if len(value) > 1024:
        raise ValueError('invalid exact amount')
    return Decimal(value)


def build_ownership_report(contributors, scope, as_of, inventory_complete, trusted_attributions):
    """Derive one immutable scope report from the explicit, bounded inputs.

    The caller is responsible for proving pricing and inventory completeness,
    and authorizing each attribution evidence digest before invoking this helper.
    """
    cutoff = _time(as_of)
    if (not _opaque(scope) or not isinstance(inventory_complete, bool) or
            not isinstance(contributors, list) or len(contributors) > 10000 or
            not isinstance(trusted_attributions, list) or len(trusted_attributions) > 10000):
        raise ValueError('invalid report input')
    trusted = set()
    for digest in trusted_attributions:
        if not isinstance(digest, str) or re.fullmatch(r'[0-9a-f]{64}', digest) is None:
            raise ValueError('invalid authorized reference')
        trusted.add(digest)
    seen = {}
    pending = False
    included = []
    for item in contributors:
        if not isinstance(item, dict) or set(item) != {
            'response_id', 'provider', 'provider_scope', 'observed_at', 'cost_usd',
            'attribution', 'attribution_evidence'
        }:
            raise ValueError('invalid contributor')
        observed = _time(item['observed_at'])
        if observed > cutoff:
            continue
        response = item['response_id']
        if not isinstance(response, str) or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,255}', response) is None:
            raise ValueError('invalid response identity')
        provider = item['provider']
        account = item['provider_scope']
        if (not isinstance(provider, str) or
                re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,255}', provider) is None or
                not _opaque(account)):
            raise ValueError('invalid provider identity')
        identity = (provider, account, response)
        amount = _amount(item['cost_usd'])
        attribution = item['attribution']
        if not isinstance(attribution, dict) or set(attribution) != {
            'response_id', 'provider', 'provider_scope', 'owner_kind', 'owner_id',
            'candidates', 'basis'
        }:
            raise ValueError('invalid attribution evidence')
        candidates = attribution['candidates']
        if (attribution['response_id'] != response or attribution['provider'] != provider or
                attribution['provider_scope'] != account or not _opaque(attribution['owner_id']) or
                attribution['owner_kind'] not in ('task', 'span', 'shared_pool', 'unattributed') or
                attribution['basis'] not in ('submission', 'correlation', 'verified_import') or
                not isinstance(candidates, list) or len(candidates) > 64 or
                any(not _opaque(candidate) for candidate in candidates) or
                len(set(candidates)) != len(candidates)):
            raise ValueError('invalid attribution evidence')
        digest = item['attribution_evidence']
        if not isinstance(digest, str) or re.fullmatch(r'[0-9a-f]{64}', digest) is None:
            raise ValueError('invalid attribution reference')
        # Reject conflicting representations; neither is safe to add.
        representation = _contract.canonical_bytes(item)
        if identity in seen:
            if seen[identity] != representation:
                raise ValueError('conflicting response identity')
            continue
        seen[identity] = representation
        if digest not in trusted or digest != _contract.content_id(attribution):
            pending = True
            continue
        kind = attribution['owner_kind']
        owner = attribution['owner_id']
        if kind == 'shared_pool' and scope in candidates:
            pending = True
        elif owner == scope:
            if kind == 'unattributed':
                pending = True
            else:
                included.append((identity, amount))
    included.sort(key=lambda pair: pair[0])
    result = {'as_of': as_of, 'scope': scope,
              'attribution': 'partial' if pending else 'complete',
              'contributors': [{'provider': identity[0], 'provider_scope': identity[1],
                                'response_id': identity[2]} for identity, _ in included]}
    if inventory_complete and not pending:
        # The precision is derived from all operands, preventing decimal rounding.
        precision = max(1, sum(len(amount.as_tuple().digits) + abs(amount.as_tuple().exponent)
                               for _, amount in included) + len(str(len(included))) + 1)
        with localcontext() as ctx:
            ctx.prec = precision
            total = sum((amount for _, amount in included), Decimal(0))
        value = format(total, 'f')
        if '.' in value:
            value = value.rstrip('0').rstrip('.')
        result['cost_usd'] = value
    return result
