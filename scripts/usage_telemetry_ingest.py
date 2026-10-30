#!/usr/bin/env python3
"""Validate usage candidates without accepting self-authorized provenance.

The local configuration key and its MAC are controlled by the bundle author;
they do not independently establish either source provenance or authorization.
A future authority must be isolated from that author and bind the exact bundle,
profile, run and owner to independently verified sanitized source evidence. It
must establish that evidence before issuing its authorization and be protected
against forgery or substitution. Ingest must verify that authority without
reading source records or discovering history. Until such an authority is
available, ingestion fails closed before any shared storage is modified.
"""
import hashlib
import fcntl
import hmac
import base64
import binascii
import importlib.util
import json
import os
import re
import stat
import sys

import usage_telemetry_adapter as adapter
import usage_telemetry_publication as publication
import usage_telemetry_sources as sources
from usage_telemetry_contract import BUNDLE_LIMIT, canonical_bytes, validate_usage_bundle_json

spec = importlib.util.spec_from_file_location('usage_cli', os.path.join(os.path.dirname(__file__), 'usage-telemetry.py'))
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def config_and_key(path, profile_id=None):
    if profile_id is None:
        raw = json.loads(cli._read_file(path, private=True), object_pairs_hook=sources._unique_pairs,
                         parse_constant=sources._invalid_constant)
        profile_id = raw['profiles'][0]['profile']['profile_id']
    return cli._config(path, profile_id)


def key_fingerprint(key):
    return hmac.new(key, b'orchestrail:usage-registration:v1\0', hashlib.sha256).hexdigest()


def read_bundle(path):
    fd = sources._open_regular(path)
    try:
        if os.fstat(fd).st_size > BUNDLE_LIMIT:
            raise ValueError('bundle too large')
        chunks = []
        remaining = BUNDLE_LIMIT + 1
        while remaining:
            chunk = os.read(fd, min(remaining, 65536))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b''.join(chunks)
        if len(data) > BUNDLE_LIMIT:
            raise ValueError('bundle too large')
        return validate_usage_bundle_json(data)
    finally:
        os.close(fd)


def registration(root, run_id, config, key):
    # Metadata is an explicitly addressed active registration, never history.
    path = os.path.join(root, '.active', run_id)
    fd = sources._open_regular(path)
    try:
        meta = os.fstat(fd)
        if meta.st_uid != os.geteuid() or meta.st_size > cli.LIMIT:
            raise ValueError('invalid registration')
        data = os.read(fd, cli.LIMIT + 1)
        if len(data) > cli.LIMIT or b'\0' in data:
            raise ValueError('invalid registration')
    finally:
        os.close(fd)
    lines = data.decode('utf-8').splitlines()
    if not lines or lines[0] != '# run-log-metadata percent-v1':
        raise ValueError('invalid registration')
    values = {}
    for line in lines[1:]:
        if '=' not in line:
            raise ValueError('invalid registration')
        name, value = line.split('=', 1)
        if name in values:
            raise ValueError('duplicate registration field')
        values[name] = value.replace('%0A', '\n').replace('%25', '%')
    if (not hmac.compare_digest(values.get('usage_key_fingerprint', ''), key_fingerprint(key)) or
            values.get('project') != config['project_identifier']):
        raise ValueError('registration mismatch')
    if config['owner_scope'] != {'owner_kind': 'run', 'owner_id': adapter._opaque(key, 'run', run_id)}:
        raise ValueError('unregistered scope')
    return values.get('usage_authority_key_sha256', '')


def check_active_registration(root, run_id, config, key, expected):
    """Check registration under the lifecycle event lock without delaying closure."""
    path = os.path.join(root, '.active', run_id)
    fd = sources._open_regular(path)
    try:
        data = os.read(fd, cli.LIMIT + 1)
    finally:
        os.close(fd)
    lines = data.decode('utf-8').splitlines()
    files = [line[5:] for line in lines if line.startswith('file=')]
    if len(files) != 1:
        raise ValueError('invalid registration event path')
    event_path = files[0].replace('%0A', '\n').replace('%25', '%')
    runs_dir = os.path.realpath(os.path.join(root, 'runs'))
    if os.path.dirname(os.path.abspath(event_path)) != runs_dir:
        raise ValueError('invalid registration event path')
    event_fd = sources._open_regular(event_path)
    try:
        fcntl.flock(event_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not hmac.compare_digest(registration(root, run_id, config, key), expected):
            raise ValueError('registration changed')
    finally:
        os.close(event_fd)


def _trusted_key(path, registry):
    """Read an administrator-controlled registry key without writable ancestors."""
    if (not isinstance(path, str) or not path.startswith(registry) or
            re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.pem', path[len(registry):]) is None):
        raise ValueError('independent authority key unavailable')
    parts = sources._path_parts(path)
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    file_fd = None
    try:
        for index, part in enumerate(parts):
            parent = os.fstat(directory)
            if parent.st_uid != 0 or stat.S_IMODE(parent.st_mode) & 0o022:
                raise ValueError('untrusted authority directory')
            if index == len(parts) - 1:
                file_fd = os.open(part, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                                  dir_fd=directory)
                break
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        info = os.fstat(file_fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or
                stat.S_IMODE(info.st_mode) & 0o022 or info.st_size > 16384):
            raise ValueError('untrusted authority key')
        data = os.read(file_fd, 16385)
        if len(data) > 16384:
            raise ValueError('untrusted authority key')
        return data
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(directory)


def trusted_authority_key(path):
    return _trusted_key(path, '/etc/orchestrail/usage-authorities/')


def trusted_registration_key(path):
    return _trusted_key(path, '/etc/orchestrail/usage-registration-authorities/')


def _rsa_public_numbers(public_key):
    """Parse a strict RSA SPKI into canonical modulus and exponent."""
    def tlv(data, position, tag):
        if position >= len(data) or data[position] != tag:
            raise ValueError('invalid DER tag')
        position += 1
        if position >= len(data):
            raise ValueError('invalid DER length')
        length = data[position]
        position += 1
        if length & 0x80:
            count = length & 0x7f
            if not 1 <= count <= 2 or position + count > len(data) or data[position] == 0:
                raise ValueError('invalid DER length')
            length = int.from_bytes(data[position:position + count], 'big')
            position += count
            if length < 128 or (count == 2 and length < 256):
                raise ValueError('noncanonical DER length')
        end = position + length
        if end > len(data):
            raise ValueError('truncated DER')
        return data[position:end], end

    try:
        if not isinstance(public_key, bytes):
            return None
        lines = public_key.splitlines()
        if (len(lines) < 3 or lines[0] != b'-----BEGIN PUBLIC KEY-----' or
                lines[-1] != b'-----END PUBLIC KEY-----' or
                any(not line or len(line) > 64 for line in lines[1:-1])):
            return None
        der = base64.b64decode(b''.join(lines[1:-1]), validate=True)
        sequence, end = tlv(der, 0, 0x30)
        if end != len(der):
            return None
        algorithm, pos = tlv(sequence, 0, 0x30)
        if algorithm != bytes.fromhex('06092a864886f70d0101010500'):
            return None
        bits, end = tlv(sequence, pos, 0x03)
        if end != len(sequence) or not bits or bits[0] != 0:
            return None
        encoded_key, end = tlv(bits[1:], 0, 0x30)
        if end != len(bits) - 1:
            return None
        modulus_bytes, pos = tlv(encoded_key, 0, 0x02)
        exponent_bytes, end = tlv(encoded_key, pos, 0x02)
        if (end != len(encoded_key) or len(modulus_bytes) not in (257, 385, 513) or
                modulus_bytes[0] != 0 or not modulus_bytes[1] & 0x80 or
                exponent_bytes != b'\x01\x00\x01'):
            return None
        modulus = int.from_bytes(modulus_bytes, 'big')
        if not modulus & 1:
            return None
        return modulus, int.from_bytes(exponent_bytes, 'big')
    except (ValueError, TypeError, binascii.Error, IndexError):
        return None


def verify_rsa_sha256(public_key, message, signature):
    """Verify a strict RSA SPKI and PKCS#1 v1.5 SHA-256 signature."""
    if not isinstance(message, bytes) or not isinstance(signature, bytes):
        return False
    numbers = _rsa_public_numbers(public_key)
    if numbers is None:
        return False
    modulus, exponent = numbers
    size = (modulus.bit_length() + 7) // 8
    if len(signature) != size:
        return False
    value = int.from_bytes(signature, 'big')
    if value >= modulus:
        return False
    digest_info = bytes.fromhex('3031300d060960864801650304020105000420') + hashlib.sha256(message).digest()
    expected = b'\x00\x01' + b'\xff' * (size - len(digest_info) - 3) + b'\x00' + digest_info
    actual = pow(value, exponent, modulus).to_bytes(size, 'big')
    return hmac.compare_digest(actual, expected)


def authorized_by_independent_authority(bundle, config, registered_key):
    """Verify an exact signed permit; callers cannot supply the trust anchor."""
    path = os.environ.get('USAGE_TELEMETRY_AUTHORITY_PERMIT')
    key_path = os.environ.get('USAGE_TELEMETRY_AUTHORITY_KEY')
    if not path or not key_path:
        raise ValueError('independent authority unavailable')
    permit = json.loads(cli._read_file(path, private=True), object_pairs_hook=sources._unique_pairs,
                        parse_constant=sources._invalid_constant)
    sources._bounded_raw_tree(permit)
    expected = {'schema_version': 1, 'kind': 'usage_authority_permit',
                'bundle_sha256': hashlib.sha256(canonical_bytes(bundle)).hexdigest(),
                'profile_id': bundle['profile_id'], 'profile_version': bundle['profile_version'],
                'run_id': bundle['run_id'], 'scope': config['owner_scope']}
    if not isinstance(permit, dict) or set(permit) != set(expected) | {'signature'}:
        raise ValueError('invalid authority permit')
    if {key: permit[key] for key in expected} != expected:
        raise ValueError('authority permit mismatch')
    signature = permit['signature']
    if not isinstance(signature, str) or re.fullmatch(r'(?:[0-9a-f]{128}|[0-9a-f]{512}|[0-9a-f]{768}|[0-9a-f]{1024})', signature) is None:
        raise ValueError('invalid authority signature')
    trusted_key = trusted_authority_key(key_path)
    if not re.fullmatch(r'[0-9a-f]{64}', registered_key) or not hmac.compare_digest(
            hashlib.sha256(trusted_key).hexdigest(), registered_key):
        raise ValueError('authority key is not registered')
    message = b'orchestrail:usage-authority:v1\0' + canonical_bytes(expected)
    if len(signature) == 128:
        # Keep legacy permits usable when the optional verifier is installed.
        # RSA permits above remain usable with Python's standard library alone.
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            from cryptography.exceptions import InvalidSignature
        except ImportError:
            raise ValueError('authority verifier unavailable') from None
        try:
            key = serialization.load_pem_public_key(trusted_key)
            if not isinstance(key, Ed25519PublicKey):
                raise ValueError('invalid authority key')
            key.verify(bytes.fromhex(signature), message)
        except (ValueError, TypeError, InvalidSignature):
            raise ValueError('invalid authority permit') from None
    elif not verify_rsa_sha256(trusted_key, message, bytes.fromhex(signature)):
        raise ValueError('invalid authority permit')
    return True


def _verify_signed_certificate(key, domain, candidate, expected, *, rsa_only=False):
    if not isinstance(candidate, dict) or set(candidate) != set(expected) | {'signature'}:
        raise ValueError('invalid certificate')
    if {name: candidate[name] for name in expected} != expected:
        raise ValueError('certificate scope mismatch')
    signature = candidate['signature']
    if not isinstance(signature, str) or re.fullmatch(r'(?:[0-9a-f]{128}|[0-9a-f]{512}|[0-9a-f]{768}|[0-9a-f]{1024})', signature) is None:
        raise ValueError('invalid certificate signature')
    message = domain + canonical_bytes(expected)
    if len(signature) != 128:
        if not verify_rsa_sha256(key, message, bytes.fromhex(signature)):
            raise ValueError('invalid certificate signature')
        return
    if rsa_only:
        raise ValueError('invalid certificate signature')
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        raise ValueError('certificate verifier unavailable') from None
    try:
        public = serialization.load_pem_public_key(key)
        if not isinstance(public, Ed25519PublicKey):
            raise ValueError('invalid certificate key')
        public.verify(bytes.fromhex(signature), message)
    except (InvalidSignature, TypeError, ValueError):
        raise ValueError('invalid certificate signature') from None


def certified_late_registration(path, bundle, config, key):
    """Verify explicitly authorized late import without reading lifecycle history.

    A distinct root-controlled registration issuer certifies the original run,
    owner and authority key. The registered run authority then signs a separate
    domain-bound authorization for the exact late bundle. Neither assertion can
    be replaced by the bundle author's MAC or by a run authority self-attestation.
    """
    if config['owner_scope'] != {'owner_kind': 'run', 'owner_id': adapter._opaque(key, 'run', bundle['run_id'])}:
        raise ValueError('unregistered scope')
    raw = json.loads(cli._read_file(path, private=True), object_pairs_hook=sources._unique_pairs,
                     parse_constant=sources._invalid_constant)
    sources._bounded_raw_tree(raw)
    if not isinstance(raw, dict) or set(raw) != {'registration', 'authorization'}:
        raise ValueError('invalid late import certificate')
    registration_key = trusted_registration_key(os.environ.get('USAGE_TELEMETRY_REGISTRATION_KEY'))
    authority_key = trusted_authority_key(os.environ.get('USAGE_TELEMETRY_AUTHORITY_KEY'))
    fingerprint = hashlib.sha256(authority_key).hexdigest()
    registration_numbers = _rsa_public_numbers(registration_key)
    if registration_numbers is None:
        raise ValueError('invalid registration issuer key')
    authority_numbers = _rsa_public_numbers(authority_key)
    if authority_numbers is not None and authority_numbers == registration_numbers:
        raise ValueError('registration issuer must be independent')
    common = {'run_id': bundle['run_id'], 'scope': config['owner_scope'],
              'project_sha256': hashlib.sha256(config['project_identifier'].encode('utf-8')).hexdigest(),
              'registration_key_fingerprint': key_fingerprint(key), 'authority_key_sha256': fingerprint}
    expected_registration = {'schema_version': 1, 'kind': 'usage_registration_certificate', **common}
    _verify_signed_certificate(registration_key, b'orchestrail:usage-registration-certificate:v1\0',
                               raw['registration'], expected_registration, rsa_only=True)
    expected_late = {'schema_version': 1, 'kind': 'usage_late_import_certificate', **common,
                     'profile_id': bundle['profile_id'], 'profile_version': bundle['profile_version'],
                     'bundle_sha256': hashlib.sha256(canonical_bytes(bundle)).hexdigest(),
                     'registration_sha256': hashlib.sha256(canonical_bytes(raw['registration'])).hexdigest()}
    _verify_signed_certificate(authority_key, b'orchestrail:usage-late-import:v1\0',
                               raw['authorization'], expected_late)
    return fingerprint


def authorize_lifecycle_projection(projection, *, scope, run_id, registered_key, permit, key_path):
    """Verify an independently issued permit bound to a projection and run."""
    expected = {'schema_version': 1, 'kind': 'lifecycle_authority_permit',
                'projection_sha256': hashlib.sha256(canonical_bytes(projection)).hexdigest(),
                'scope': scope, 'run_id': run_id}
    if (not isinstance(permit, dict) or set(permit) != set(expected) | {'signature'} or
            {key: permit[key] for key in expected} != expected or projection.get('scope') != scope):
        raise ValueError('invalid lifecycle authority permit')
    signature = permit['signature']
    if not isinstance(signature, str) or re.fullmatch(r'(?:[0-9a-f]{512}|[0-9a-f]{768}|[0-9a-f]{1024})', signature) is None:
        raise ValueError('invalid lifecycle authority signature')
    trusted = trusted_authority_key(key_path)
    if (not isinstance(registered_key, str) or not re.fullmatch(r'[0-9a-f]{64}', registered_key) or
            not hmac.compare_digest(hashlib.sha256(trusted).hexdigest(), registered_key)):
        raise ValueError('lifecycle authority is not registered')
    message = b'orchestrail:lifecycle-authority:v1\0' + canonical_bytes(expected)
    if not verify_rsa_sha256(trusted, message, bytes.fromhex(signature)):
        raise ValueError('invalid lifecycle authority signature')
    return True


def lifecycle_projection(path, run_id, registered_key, tokens_in, tokens_out, cost, root):
    from usage_telemetry_contract import (validate_lifecycle_projection_json, validate_decimal)
    candidate = validate_lifecycle_projection_json(cli._read_file(path))
    permit_path = os.environ.get('USAGE_TELEMETRY_LIFECYCLE_PERMIT')
    key_path = os.environ.get('USAGE_TELEMETRY_AUTHORITY_KEY')
    if not permit_path or not key_path:
        raise ValueError('lifecycle authority unavailable')
    permit = json.loads(cli._read_file(permit_path, private=True), object_pairs_hook=sources._unique_pairs,
                        parse_constant=sources._invalid_constant)
    sources._bounded_raw_tree(permit)
    config, _, key = config_and_key(os.environ.get('USAGE_TELEMETRY_CONFIG'))
    if config['run_id'] != run_id:
        raise ValueError('lifecycle registration run mismatch')
    registered_authority = registration(root, run_id, config, key)
    if not hmac.compare_digest(registered_authority, registered_key):
        raise ValueError('lifecycle authority registration mismatch')
    declared = candidate['scope']
    scope = config['owner_scope'] | {'attribution_quality': declared['attribution_quality']}
    if declared != scope:
        raise ValueError('lifecycle owner scope mismatch')
    authorize_lifecycle_projection(candidate, scope=scope, run_id=run_id,
                                   registered_key=registered_key, permit=permit, key_path=key_path)
    projection = publication.validate_lifecycle_projection_for_owner(
        candidate, scope=scope, cost_usd=None if cost == '-' else cost,
        authorize=lambda item, owner: item == candidate and owner == scope)
    if cost != '-':
        validate_decimal(cost)
    for scalar, fields in ((tokens_in, {'input_uncached', 'input_cache_read', 'input_cache_write',
                                      'input_cache_write_unsplit'}),
                           (tokens_out, {'output_total'})):
        if scalar != '-':
            dimensions = ('inventory', 'identity', 'measurements', 'attribution')
            if any(projection['completeness'][name] not in ('complete', 'not_applicable') for name in dimensions):
                raise ValueError('incomplete projection scalar')
            amount = 0
            for contributor in projection['contributors']:
                for field, measurement in contributor['measurements'].items():
                    if field in fields:
                        if isinstance(measurement, list):
                            amount += sum(part['tokens']['value'] for part in measurement)
                        else:
                            amount += measurement['value']
            if str(amount) != scalar:
                raise ValueError('projection scalar mismatch')
    encoded = canonical_bytes(projection)
    return hashlib.sha256(encoded).hexdigest() + '\n' + encoded.decode('utf-8')



def ingest(path, root, *, late_certificate=None):
    bundle = read_bundle(path)
    config, profile, key = config_and_key(os.environ.get('USAGE_TELEMETRY_CONFIG'), bundle['profile_id'])
    if (bundle['profile_version'] != profile['profile_version'] or bundle['run_id'] != config['run_id']):
        raise ValueError('profile or run mismatch')
    registered_key = (registration(root, bundle['run_id'], config, key) if late_certificate is None else
                      certified_late_registration(late_certificate, bundle, config, key))
    proof_path = os.environ.get('USAGE_TELEMETRY_PROVENANCE')
    if not proof_path:
        raise ValueError('provenance missing')
    proof = json.loads(cli._read_file(proof_path, private=True), object_pairs_hook=sources._unique_pairs,
                       parse_constant=sources._invalid_constant)
    sources._bounded_raw_tree(proof)
    expected = {'schema_version': 1, 'kind': 'usage_provenance',
                'bundle_sha256': hashlib.sha256(canonical_bytes(bundle)).hexdigest(),
                'profile_id': bundle['profile_id'], 'profile_version': bundle['profile_version'],
                'scope': config['owner_scope']}
    mac = hmac.new(key, b'orchestrail:usage-provenance:v1\0' + canonical_bytes(expected), hashlib.sha256).hexdigest()
    if not isinstance(proof, dict) or set(proof) != set(expected) | {'mac'}:
        raise ValueError('invalid provenance')
    if {k: proof[k] for k in expected} != expected or not isinstance(proof['mac'], str) or not hmac.compare_digest(proof['mac'], mac):
        raise ValueError('invalid provenance')
    authorized_by_independent_authority(bundle, config, registered_key)
    scope = config['owner_scope'] | {'attribution_quality': 'asserted'}
    if late_certificate is None:
        check_active_registration(root, bundle['run_id'], config, key, registered_key)
    receipt = publication.publish_usage(bundle, root=root, mode='on', scope=scope,
        authorize=lambda candidate, owner: candidate == bundle and owner == scope)
    if late_certificate is None:
        check_active_registration(root, bundle['run_id'], config, key, registered_key)
    return receipt


def main():
    if len(sys.argv) == 9 and sys.argv[1] == 'lifecycle-projection':
        print(lifecycle_projection(*sys.argv[2:]))
        return
    if len(sys.argv) == 2 and sys.argv[1] == 'register-authority':
        trusted_key = trusted_authority_key(os.environ.get('USAGE_TELEMETRY_AUTHORITY_KEY'))
        print(hashlib.sha256(trusted_key).hexdigest())
        return
    if len(sys.argv) == 2 and sys.argv[1] == 'register':
        _, _, key = config_and_key(os.environ.get('USAGE_TELEMETRY_CONFIG'))
        print(key_fingerprint(key))
        return
    if sys.argv[1:2] != ['ingest'] or len(sys.argv) not in (4, 5):
        raise ValueError('invalid invocation')
    late_certificate = sys.argv[4] if len(sys.argv) == 5 else None
    print(json.dumps(ingest(sys.argv[2], sys.argv[3], late_certificate=late_certificate), separators=(',', ':'), sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError, TypeError, KeyError, IndexError, RecursionError, OverflowError):
        print('log-step: usage ingestion unavailable', file=sys.stderr)
        sys.exit(1)
