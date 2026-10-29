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
import hmac
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


def trusted_authority_key(path):
    """Read a root-controlled public key without trusting writable ancestors."""
    # Only the administrator-owned authority registry confers trust. A merely
    # root-owned file elsewhere may be a public example key with a known secret.
    registry = '/etc/orchestrail/usage-authorities/'
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
    if not isinstance(signature, str) or re.fullmatch(r'[0-9a-f]{128}', signature) is None:
        raise ValueError('invalid authority signature')
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        raise ValueError('authority verifier unavailable') from None
    trusted_key = trusted_authority_key(key_path)
    if not re.fullmatch(r'[0-9a-f]{64}', registered_key) or not hmac.compare_digest(
            hashlib.sha256(trusted_key).hexdigest(), registered_key):
        raise ValueError('authority key is not registered')
    try:
        public_key = serialization.load_pem_public_key(trusted_key)
        if not isinstance(public_key, Ed25519PublicKey):
            raise ValueError('invalid authority key')
        public_key.verify(bytes.fromhex(signature),
                          b'orchestrail:usage-authority:v1\0' + canonical_bytes(expected))
    except (InvalidSignature, ValueError, TypeError):
        raise ValueError('invalid authority permit') from None
    return True


def ingest(path, root):
    bundle = read_bundle(path)
    config, profile, key = config_and_key(os.environ.get('USAGE_TELEMETRY_CONFIG'), bundle['profile_id'])
    if (bundle['profile_version'] != profile['profile_version'] or bundle['run_id'] != config['run_id']):
        raise ValueError('profile or run mismatch')
    registered_key = registration(root, bundle['run_id'], config, key)
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
    return publication.publish_usage(bundle, root=root, mode='on', scope=scope,
        authorize=lambda candidate, owner: candidate == bundle and owner == scope)


def main():
    if len(sys.argv) == 2 and sys.argv[1] == 'register-authority':
        trusted_key = trusted_authority_key(os.environ.get('USAGE_TELEMETRY_AUTHORITY_KEY'))
        print(hashlib.sha256(trusted_key).hexdigest())
        return
    if len(sys.argv) == 2 and sys.argv[1] == 'register':
        _, _, key = config_and_key(os.environ.get('USAGE_TELEMETRY_CONFIG'))
        print(key_fingerprint(key))
        return
    if len(sys.argv) != 4 or sys.argv[1] != 'ingest':
        raise ValueError('invalid invocation')
    print(json.dumps(ingest(sys.argv[2], sys.argv[3]), separators=(',', ':'), sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError, TypeError, KeyError, IndexError, RecursionError, OverflowError):
        print('log-step: usage ingestion unavailable', file=sys.stderr)
        sys.exit(1)
