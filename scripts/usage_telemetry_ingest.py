#!/usr/bin/env python3
"""Register trusted local collection keys and ingest authorized usage bundles."""
import hashlib
import hmac
import importlib.util
import json
import os
import re
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


def ingest(path, root):
    bundle = read_bundle(path)
    config, profile, key = config_and_key(os.environ.get('USAGE_TELEMETRY_CONFIG'), bundle['profile_id'])
    if (bundle['profile_version'] != profile['profile_version'] or bundle['run_id'] != config['run_id']):
        raise ValueError('profile or run mismatch')
    registration(root, bundle['run_id'], config, key)
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
    scope = config['owner_scope'] | {'attribution_quality': 'asserted'}
    return publication.publish_usage(bundle, root=root, mode='on', scope=scope,
                                     authorize=lambda candidate, owner: candidate == bundle and owner == scope)


def main():
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
