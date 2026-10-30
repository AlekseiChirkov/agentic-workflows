#!/usr/bin/env python3
"""Offline helpers for explicitly selected, private usage telemetry."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
import sys

import usage_telemetry_adapter as adapter
import usage_telemetry_sources as sources
import usage_telemetry_alerts as alerts
import usage_telemetry_contract as contract
from usage_telemetry_contract import (canonical_bytes, content_id, validate_source_profile,
                                      validate_source_selection_json, validate_usage_bundle)

LIMIT = 1024 * 1024
# This public synthetic format is the only profile reviewed for disclosure.
# Adding profiles requires reviewing every serialized field and its semantics.
PUBLIC_PROFILE_DIGESTS = frozenset({
    '9831e467f5491bde26960256791cf69bdf68bd4aad88d0e27380b1be19818f46',
})


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError('invalid command arguments')


def _read_file(path, *, private=False):
    fd = sources._open_regular(path)
    try:
        metadata = os.fstat(fd)
        if metadata.st_size > LIMIT:
            raise ValueError('input exceeds limit')
        if private and (stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_uid != os.geteuid()):
            raise ValueError('invalid private configuration permissions')
        chunks = []
        remaining = LIMIT + 1
        while remaining:
            data = os.read(fd, min(remaining, 65536))
            if not data:
                break
            chunks.append(data)
            remaining -= len(data)
        result = b''.join(chunks)
        if len(result) > LIMIT:
            raise ValueError('input exceeds limit')
        return result
    finally:
        os.close(fd)


def _config(path, profile_id, *, authorized_epoch_profile=None):
    if not path:
        raise ValueError('private configuration required')
    try:
        value = json.loads(_read_file(path, private=True).decode('utf-8'),
                           object_pairs_hook=sources._unique_pairs,
                           parse_constant=sources._invalid_constant)
        sources._bounded_raw_tree(value)
        if not isinstance(value, dict) or set(value) != {'schema_version', 'profiles', 'owner_scope',
                'project_identifier', 'provider_identifier', 'run_id', 'key_hex'} or type(value['schema_version']) is not int or value['schema_version'] != 1:
            raise ValueError('invalid private configuration')
        entries = value['profiles']
        if not isinstance(entries, list) or not entries or len(entries) > 256:
            raise ValueError('invalid trusted profiles')
        matches = []
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {'profile', 'sha256'}:
                raise ValueError('invalid trusted profile')
            profile = validate_source_profile(entry['profile'])
            digest = hashlib.sha256(canonical_bytes(profile)).hexdigest()
            if (entry['sha256'] != digest or
                    digest not in PUBLIC_PROFILE_DIGESTS and digest != authorized_epoch_profile):
                raise ValueError('trusted profile digest mismatch')
            if profile['profile_id'] == profile_id:
                matches.append(profile)
        if len(matches) != 1:
            raise ValueError('trusted profile not found')
        for field in ('project_identifier', 'provider_identifier'):
            if not isinstance(value[field], str) or not value[field]:
                raise ValueError('invalid private identity material')
        if not isinstance(value['run_id'], str) or re.fullmatch(r'[0-9a-f]{8}', value['run_id']) is None:
            raise ValueError('invalid run identifier')
        validate_usage_bundle({'schema_version': 1, 'kind': 'usage_bundle',
            'profile_id': matches[0]['profile_id'], 'profile_version': matches[0]['profile_version'],
            'project_id': 'sha256:' + '0' * 64, 'run_id': value['run_id'],
            'sources': [], 'observations': [], 'evidence_objects': [], 'inventories': [],
            'segments': [], 'diagnostics': []})
        key_hex = value['key_hex']
        if not isinstance(key_hex, str) or len(key_hex) < 64 or len(key_hex) > 512 or len(key_hex) % 2 or any(c not in '0123456789abcdef' for c in key_hex):
            raise ValueError('invalid private key')
        return value, matches[0], bytes.fromhex(key_hex)
    except (UnicodeError, RecursionError, TypeError, KeyError, OverflowError):
        raise ValueError('invalid private configuration') from None


def _epoch_permit(path):
    """Verify root-authorized exact epoch source decisions before using them."""
    import usage_telemetry_ingest as authority
    value = json.loads(_read_file(path, private=True), object_pairs_hook=sources._unique_pairs,
                       parse_constant=sources._invalid_constant)
    sources._bounded_raw_tree(value)
    fields = {'schema_version', 'kind', 'profile_sha256', 'scope', 'source_sha256',
              'run_id', 'epoch_coverages', 'attestations', 'signature'}
    if (not isinstance(value, dict) or set(value) != fields or type(value['schema_version']) is not int or
            value['schema_version'] != 1 or value['kind'] != 'epoch_source_authority_permit'):
        raise ValueError('invalid epoch authority permit')
    for name in ('profile_sha256', 'source_sha256'):
        if not isinstance(value[name], str) or re.fullmatch(r'[0-9a-f]{64}', value[name]) is None:
            raise ValueError('invalid epoch authority digest')
    if not isinstance(value['run_id'], str) or re.fullmatch(r'[0-9a-f]{8}', value['run_id']) is None:
        raise ValueError('invalid epoch authority run')
    for name in ('epoch_coverages', 'attestations'):
        if not isinstance(value[name], list) or len(value[name]) > 10000:
            raise ValueError('invalid epoch authority records')
    signatures = set()
    for item in value['attestations']:
        if (not isinstance(item, dict) or set(item) != {'kind', 'subject_sha256', 'proof_sha256'} or
                item['kind'] not in ('epoch_snapshot', 'epoch_coverage', 'epoch_privacy') or
                any(not isinstance(item[field], str) or re.fullmatch(r'[0-9a-f]{64}', item[field]) is None
                    for field in ('subject_sha256', 'proof_sha256'))):
            raise ValueError('invalid epoch authority decision')
        binding = (item['kind'], item['subject_sha256'], item['proof_sha256'])
        if binding in signatures:
            raise ValueError('duplicate epoch authority decision')
        signatures.add(binding)
    signature = value['signature']
    if not isinstance(signature, str) or re.fullmatch(r'(?:[0-9a-f]{512}|[0-9a-f]{768}|[0-9a-f]{1024})', signature) is None:
        raise ValueError('invalid epoch authority signature')
    trusted_key = authority.trusted_authority_key(os.environ.get('USAGE_TELEMETRY_AUTHORITY_KEY'))
    signed = {key: item for key, item in value.items() if key != 'signature'}
    message = b'orchestrail:epoch-source-authority:v1\0' + canonical_bytes(signed)
    if not authority.verify_rsa_sha256(trusted_key, message, bytes.fromhex(signature)):
        raise ValueError('invalid epoch authority signature')
    return signed, signatures, hashlib.sha256(trusted_key).hexdigest()


def _analysis_authority(path, key_path, manifest):
    """Verify an exact signed selection and scoped independent decisions."""
    import usage_telemetry_contract as contract
    import usage_telemetry_ingest as ingest
    if not path or not key_path:
        raise ValueError('independent authority unavailable')
    value = contract.parse_json(_read_file(path, private=True))
    if not isinstance(value, dict) or set(value) != {
            'schema_version', 'kind', 'manifest_sha256', 'inputs', 'evidence', 'signature'}:
        raise ValueError('invalid analysis authority')
    if (type(value['schema_version']) is not int or value['schema_version'] != 1 or
            value['kind'] != 'analysis_authority' or value['manifest_sha256'] != contract.content_id(manifest)):
        raise ValueError('analysis authority mismatch')
    signature = value['signature']
    if not isinstance(signature, str) or re.fullmatch(r'(?:[0-9a-f]{128}|[0-9a-f]{512}|[0-9a-f]{768}|[0-9a-f]{1024})', signature) is None:
        raise ValueError('invalid analysis signature')
    public = ingest.trusted_authority_key(key_path)
    body = {key: item for key, item in value.items() if key != 'signature'}
    message = b'orchestrail:analysis-authority:v1\0' + contract.canonical_bytes(body)
    if len(signature) == 128:
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            from cryptography.exceptions import InvalidSignature
        except ImportError:
            raise ValueError('analysis authority verifier unavailable') from None
        try:
            key = serialization.load_pem_public_key(public)
            if not isinstance(key, Ed25519PublicKey):
                raise ValueError('invalid analysis authority key')
            key.verify(bytes.fromhex(signature), message)
        except (ValueError, TypeError, InvalidSignature):
            raise ValueError('invalid analysis authority') from None
    elif not ingest.verify_rsa_sha256(public, message, bytes.fromhex(signature)):
        raise ValueError('invalid analysis authority')
    inputs = value['inputs']
    evidence = value['evidence']
    if not isinstance(inputs, list) or len(inputs) > 10000 or not isinstance(evidence, list) or len(evidence) > 10000:
        raise ValueError('invalid analysis decisions')
    input_proofs = {}
    for entry in inputs:
        if not isinstance(entry, dict) or set(entry) != {'sha256', 'proof'}:
            raise ValueError('invalid input decision')
        digest = entry['sha256']
        contract._hash(digest)
        if digest in input_proofs and input_proofs[digest] != entry['proof']:
            raise ValueError('conflicting input decisions')
        input_proofs[digest] = entry['proof']
    authorized = set()
    for entry in evidence:
        if not isinstance(entry, dict) or set(entry) != {'kind', 'scope', 'subject', 'evidence'}:
            raise ValueError('invalid evidence decision')
        authorized.add(contract.canonical_bytes(entry))
    def verify_input(entry, decoded, scope):
        proof = input_proofs.get(entry['sha256'])
        if not isinstance(proof, dict) or proof.get('scope') != scope:
            raise ValueError('input is not independently authorized')
        return proof
    def verify_evidence(kind, scope, subject, proof):
        return contract.canonical_bytes({'kind': kind, 'scope': scope, 'subject': subject,
                                         'evidence': proof}) in authorized
    return verify_input, verify_evidence


def _authority_binding_key(kind, scope, subject, evidence):
    # A measurement subject wraps a separately typed observation. Canonicalize
    # that object in its own schema so its declared sets retain their semantics.
    if isinstance(subject, dict) and 'observation' in subject:
        subject = dict(subject)
        subject['observation'] = contract.parse_json(contract.canonical_bytes(subject['observation']))
    if kind == 'context' and isinstance(evidence, dict):
        evidence = contract.parse_json(contract.canonical_bytes(evidence, set_paths=(('evidence_objects',),)))
    return tuple(contract.canonical_bytes(value) for value in (kind, scope, subject, evidence))


def _status_authority(path):
    """Load explicit owner-controlled authorizations; hashes alone are not trust.

    The operator supplies this private file independently after verifying each
    exact binding. It must never be derived automatically from the input.
    """
    if path is None:
        return None
    data = _read_file(path, private=True)
    authority = contract.parse_json(data)
    contract._bounded_tree(authority)
    contract._fields(authority, {'schema_version', 'kind', 'bindings'})
    contract._version(authority['schema_version'])
    contract._choice(authority['kind'], frozenset({'status_authority'}))
    bindings = authority['bindings']
    if not isinstance(bindings, list) or len(bindings) > 10000:
        raise ValueError('invalid authority')
    approved = set()
    approved_digests = set()
    for binding in bindings:
        if not isinstance(binding, dict):
            raise ValueError('invalid authority binding')
        digested = 'subject_sha256' in binding or 'evidence_sha256' in binding
        if digested:
            contract._fields(binding, {'kind', 'scope', 'subject_sha256', 'evidence_sha256'})
        else:
            contract._fields(binding, {'kind', 'scope', 'subject', 'evidence'})
        contract._choice(binding['kind'], frozenset({'receipt', 'ownership', 'profile', 'context',
                    'measurement', 'inventory', 'pricing_context', 'price', 'tool_scope_empty',
                    'nonnegative_scope', 'response_privacy', 'scope_tools_empty', 'scope_completion', 'duration', 'duration_history'}))
        if digested:
            contract._hash(binding['subject_sha256'])
            contract._hash(binding['evidence_sha256'])
            encoded = (contract.canonical_bytes(binding['kind']), contract.canonical_bytes(binding['scope']),
                       binding['subject_sha256'], binding['evidence_sha256'])
            if encoded in approved_digests:
                raise ValueError('duplicate authority binding')
            approved_digests.add(encoded)
        else:
            encoded = _authority_binding_key(*(binding[key] for key in ('kind', 'scope', 'subject', 'evidence')))
            if encoded in approved:
                raise ValueError('duplicate authority binding')
            approved.add(encoded)
    def verifier(kind, scope, subject, evidence):
        encoded = _authority_binding_key(kind, scope, subject, evidence)
        if encoded in approved:
            return True
        digest = (encoded[0], encoded[1], hashlib.sha256(encoded[2]).hexdigest(),
                  hashlib.sha256(encoded[3]).hexdigest())
        return digest in approved_digests
    return verifier


def _snapshot_with_parts(data):
    """Materialize only explicitly selected, pre-bounded and digest-bound parts."""
    snapshot = contract.parse_json(data)
    contract._bounded_tree(snapshot)
    if not isinstance(snapshot, dict):
        raise ValueError('invalid snapshot')
    if len(data) > LIMIT:
        raise ValueError('snapshot exceeds limit')
    declared = snapshot.get('bounds')
    if not isinstance(declared, dict) or type(declared.get('max_bytes')) is not int or len(data) > declared['max_bytes']:
        raise ValueError('snapshot exceeds declared limit')
    manifest = deepcopy(snapshot)
    preflight = deepcopy(snapshot)
    preflight.pop('analysis_inputs', None)
    for field in ('accepted_receipts', 'bundles', 'inventories', 'inventory_evidence'):
        if not isinstance(preflight.get(field), list):
            raise ValueError('invalid snapshot collection')
        preflight[field] = []
    contract.validate_current_run_snapshot(preflight)
    parts = snapshot.get('parts', [])
    sections = ('segments', 'accepted_receipts', 'bundles', 'inventories', 'inventory_evidence', 'warning_delivery')
    if sum(len(snapshot[field]) for field in sections) + len(parts) > declared['max_entries']:
        raise ValueError('snapshot entry limit exceeded')
    records = sum(len(bundle.get('observations', [])) for bundle in snapshot['bundles'] if isinstance(bundle, dict))
    if records > declared['max_records']:
        raise ValueError('selected record limit exceeded')
    destinations = {'usage_bundle': 'bundles', 'usage_accepted': 'accepted_receipts',
                    'inventory': 'inventories', 'inventory_evidence': 'inventory_evidence',
                    'collection_segment': 'segments', 'warning_delivery': 'warning_delivery'}
    for part in parts:
        fd = sources._open_regular(part['local_path'])
        try:
            metadata = os.fstat(fd)
            if metadata.st_size != part['size_bytes']:
                raise ValueError('selected part size changed')
            remaining = part['size_bytes']
            chunks = []
            while remaining:
                chunk = os.read(fd, min(remaining, 65536))
                if not chunk:
                    raise ValueError('selected part ended prematurely')
                chunks.append(chunk)
                remaining -= len(chunk)
            if os.read(fd, 1):
                raise ValueError('selected part size changed')
            encoded = b''.join(chunks)
        finally:
            os.close(fd)
        if hashlib.sha256(encoded).hexdigest() != part['sha256']:
            raise ValueError('selected part digest mismatch')
        item = contract.parse_json(encoded)
        contract._bounded_tree(item)
        if not isinstance(item, dict) or item.get('kind') != part['kind']:
            raise ValueError('selected part kind mismatch')
        if part['kind'] == 'usage_bundle':
            contract.validate_usage_bundle(item)
            records += max(1, len(item['observations']))
        else:
            records += 1
        if records > declared['max_records']:
            raise ValueError('selected record limit exceeded')
        snapshot[destinations[part['kind']]].append(item)
    snapshot.pop('parts', None)
    limit = declared['max_bytes'] + declared['max_total_bytes']
    contract.validate_current_run_snapshot(snapshot, materialized_limit=limit)
    if len(contract.canonical_bytes(snapshot)) <= declared['max_bytes']:
        return snapshot, None, None
    proposal = manifest
    proposal['part_references'] = [{key: part[key] for key in ('kind', 'sha256', 'size_bytes')}
                                   for part in proposal.pop('parts', [])
                                   if part['kind'] not in ('collection_segment', 'warning_delivery')]
    proposal['segments'] = deepcopy(snapshot['segments'])
    proposal['warning_delivery'] = deepcopy(snapshot['warning_delivery'])
    contract.validate_current_run_snapshot(proposal)
    return snapshot, proposal, limit


def _status(args):
    output = os.fstat(sys.stdout.fileno())
    if not (stat.S_ISFIFO(output.st_mode) or stat.S_ISSOCK(output.st_mode)):
        raise ValueError('output must be a pipe or socket')
    raw_snapshot = _read_file(args.receipt_snapshot)
    snapshot, proposal, materialized_limit = _snapshot_with_parts(raw_snapshot)
    policy = None if args.policy is None else contract.validate_warning_policy_json(_read_file(args.policy))
    verifier = _status_authority(args.authority)
    observed_at = args.observed_at or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    result = alerts.evaluate_status(snapshot, policy, observed_at=observed_at, verifier=verifier,
                                    _materialized_limit=materialized_limit, _proposal=proposal)
    sys.stdout.buffer.write(canonical_bytes(result))
    sys.stdout.buffer.flush()


def _owner_delivery(args):
    """Apply an explicit owner-authorized proposal or recover pending notes."""
    output = os.fstat(sys.stdout.fileno())
    if not (stat.S_ISFIFO(output.st_mode) or stat.S_ISSOCK(output.st_mode)):
        raise ValueError("output must be a pipe or socket")
    import usage_telemetry_delivery as delivery
    authority = contract.parse_json(_read_file(args.owner_authority, private=True))
    contract._fields(authority, {'schema_version', 'kind', 'owner_scope', 'destinations'})
    contract._version(authority['schema_version'])
    contract._choice(authority['kind'], frozenset({'warning_owner_authority'}))
    def validate_scope(scope, kinds):
        contract._fields(scope, {'owner_kind', 'owner_id'})
        contract._choice(scope['owner_kind'], frozenset(kinds))
        contract._private_identifier(scope['owner_id'])
    validate_scope(authority['owner_scope'], {'run', 'session'})
    entries = authority['destinations']
    if not isinstance(entries, list) or len(entries) > 256:
        raise ValueError('invalid destinations')
    destinations = {}
    for entry in entries:
        contract._fields(entry, {'scope', 'path'})
        validate_scope(entry['scope'], {'run', 'span', 'request'})
        if not isinstance(entry['path'], str) or not os.path.isabs(entry['path']):
            raise ValueError('invalid destination')
        key = (entry['scope']['owner_kind'], entry['scope']['owner_id'])
        if key in destinations:
            raise ValueError('duplicate destination')
        destinations[key] = entry['path']
    if args.proposal is None:
        report = delivery.resume_delivery(args.state, owner_scope=authority['owner_scope'], destinations=destinations)
    else:
        result = contract.parse_json(_read_file(args.proposal))
        proposal = result['proposed_snapshot']
        contract.validate_current_run_snapshot(proposal)
        report = delivery.apply_revision(args.state, proposal['revision'] - 1, proposal,
                                         owner_scope=authority['owner_scope'], destinations=destinations)
    sys.stdout.buffer.write(canonical_bytes(report))
    sys.stdout.buffer.flush()


def main(argv=None):
    parser = Parser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    normalize = commands.add_parser('normalize')
    normalize.add_argument('--profile', required=True)
    normalize.add_argument('--input-manifest', required=True)
    normalize.add_argument('--provenance-fd', type=int)
    normalize.add_argument('--epoch-permit')
    analyze = commands.add_parser('analyze')
    analyze.add_argument('--corpus-manifest', required=True)
    analyze.add_argument('--scenario', required=True)
    analyze.add_argument('--authority')
    analyze.add_argument('--authority-key')
    status = commands.add_parser('status')
    status.add_argument('--receipt-snapshot', required=True)
    status.add_argument('--policy')
    status.add_argument('--observed-at')
    status.add_argument('--authority')
    owner = commands.add_parser('owner-deliver')
    owner.add_argument('--state', required=True)
    owner.add_argument('--owner-authority', required=True)
    owner.add_argument('--proposal')
    args = parser.parse_args(argv)
    if args.command == 'analyze':
        import usage_telemetry_contract as contract
        import usage_telemetry_report as report
        import usage_telemetry_exports as exports
        manifest = contract.validate_analysis_corpus_json(_read_file(args.corpus_manifest))
        if args.scenario != manifest['scenario_id']:
            raise ValueError('analysis scenario mismatch')
        output = os.fstat(sys.stdout.fileno())
        if not (stat.S_ISFIFO(output.st_mode) or stat.S_ISSOCK(output.st_mode)):
            raise ValueError('output must be a pipe or socket')
        verify_input, verify_evidence = _analysis_authority(args.authority, args.authority_key, manifest)
        result = report.analyze_corpus(manifest, verify_input=verify_input, verify_evidence=verify_evidence)
        sys.stdout.buffer.write(exports.archive_exports(exports.render_exports(result)))
        sys.stdout.buffer.flush()
        return
    if args.command == 'owner-deliver':
        _owner_delivery(args)
        return
    if args.command == 'status':
        _status(args)
        return
    permit, decisions, authority_fingerprint = (_epoch_permit(args.epoch_permit) if args.epoch_permit
                                               else (None, set(), None))
    config, profile, key = _config(os.environ.get('USAGE_TELEMETRY_CONFIG'), args.profile,
                                   authorized_epoch_profile=permit['profile_sha256'] if permit else None)
    selection = validate_source_selection_json(_read_file(args.input_manifest))
    if (selection['profile_id'] != args.profile or selection['profile_version'] != profile['profile_version'] or
            selection['owner_scope'] != config['owner_scope']):
        raise ValueError('selection does not match trusted configuration')
    output_stat = os.fstat(sys.stdout.fileno())
    if not (stat.S_ISFIFO(output_stat.st_mode) or stat.S_ISSOCK(output_stat.st_mode)):
        raise ValueError('output must be a pipe or socket')
    if args.provenance_fd is not None:
        if args.provenance_fd < 3:
            raise ValueError('invalid provenance descriptor')
        proof_stat = os.fstat(args.provenance_fd)
        if not (stat.S_ISFIFO(proof_stat.st_mode) or stat.S_ISSOCK(proof_stat.st_mode)):
            raise ValueError('provenance must be a pipe or socket')
        if (proof_stat.st_dev, proof_stat.st_ino) == (output_stat.st_dev, output_stat.st_ino):
            raise ValueError('provenance and output must be separate')
    epoch_coverages = []
    verify_resolution = None
    if permit is not None:
        import usage_telemetry_ingest as authority
        log_root = os.environ.get('ORCHESTRAIL_LOG_ROOT') or str(Path(__file__).resolve().parents[1] / 'logs')
        registered_fingerprint = authority.registration(log_root, config['run_id'], config, key)
        if not hmac.compare_digest(registered_fingerprint, authority_fingerprint):
            raise ValueError('epoch authority is not registered for run')
        if (profile.get('epoch_fields', {}).get('status') != 'verified' or
                permit['profile_sha256'] != content_id(profile) or permit['scope'] != config['owner_scope'] or
                permit['run_id'] != config['run_id'] or len(selection['sources']) != 1 or
                permit['source_sha256'] != selection['sources'][0]['sha256']):
            raise ValueError('epoch authority scope mismatch')
        epoch_coverages = permit['epoch_coverages']
        def verify_resolution(kind, candidate_profile, subject, proof):
            return (candidate_profile == profile and
                    (kind, content_id(subject), content_id(proof)) in decisions)
    result = adapter.normalize_selection(selection, profile=profile,
                expected_owner_scope=config['owner_scope'], project_identifier=config['project_identifier'],
                provider_identifier=config['provider_identifier'], run_id=config['run_id'], key=key,
                verify_resolution=verify_resolution, epoch_coverages=epoch_coverages)
    bundle = result['bundle']
    encoded = canonical_bytes(bundle)
    if args.provenance_fd is not None:
        proof = {'schema_version': 1, 'kind': 'usage_provenance',
                 'bundle_sha256': hashlib.sha256(encoded).hexdigest(),
                 'profile_id': bundle['profile_id'], 'profile_version': bundle['profile_version'],
                 'scope': config['owner_scope']}
        proof['mac'] = hmac.new(key, b'orchestrail:usage-provenance:v1\0' +
                                canonical_bytes(proof), hashlib.sha256).hexdigest()
        data = memoryview(canonical_bytes(proof))
        while data:
            written = os.write(args.provenance_fd, data)
            if written <= 0:
                raise OSError('provenance write failed')
            data = data[written:]
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()




if __name__ == '__main__':
    try:
        main()
    except sources.SourceReadError:
        operation = {'analyze': 'analysis', 'status': 'status', 'owner-deliver': 'owner delivery'}.get(
            sys.argv[1] if len(sys.argv) > 1 else '', 'normalization')
        print('usage telemetry: ' + operation + ' failed', file=sys.stderr)
        sys.exit(3)
    except (ValueError, UnicodeError, RecursionError, OverflowError, TypeError, KeyError):
        operation = {'analyze': 'analysis', 'status': 'status', 'owner-deliver': 'owner delivery'}.get(
            sys.argv[1] if len(sys.argv) > 1 else '', 'normalization')
        print('usage telemetry: ' + operation + ' failed', file=sys.stderr)
        sys.exit(2)
    except OSError:
        operation = {'analyze': 'analysis', 'status': 'status', 'owner-deliver': 'owner delivery'}.get(
            sys.argv[1] if len(sys.argv) > 1 else '', 'normalization')
        print('usage telemetry: ' + operation + ' failed', file=sys.stderr)
        sys.exit(3)
