#!/usr/bin/env python3
"""Offline helpers for explicitly selected, private usage telemetry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys

import usage_telemetry_adapter as adapter
import usage_telemetry_sources as sources
from usage_telemetry_contract import (canonical_bytes, validate_source_profile,
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


def _config(path, profile_id):
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
            if entry['sha256'] != digest or digest not in PUBLIC_PROFILE_DIGESTS:
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


def _output_directory(path):
    """Open a destination directory without following symlinks or shared-store aliases."""
    path = os.path.abspath(path)
    parent, name = os.path.split(path)
    if not name or name in ('.', '..'):
        raise ValueError('invalid output')
    log_root = os.environ.get('ORCHESTRAIL_LOG_ROOT') or str(Path(__file__).resolve().parents[1] / 'logs')
    shared = os.path.realpath(os.path.join(log_root, 'usage', 'v1'))
    if os.path.commonpath((os.path.realpath(parent), shared)) == shared:
        raise ValueError('output is in shared storage')
    parts = [part for part in parent.split('/') if part]
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        return directory, name, parent, log_root
    except BaseException:
        os.close(directory)
        raise


def _check_destination(directory, parent, log_root):
    # Fail closed if the opened directory was moved or the kernel cannot expose
    # its current location. The operator must still prevent concurrent renames.
    actual = os.readlink('/proc/self/fd/' + str(directory))
    shared = os.path.realpath(os.path.join(log_root, 'usage', 'v1'))
    if actual != parent or os.path.commonpath((actual, shared)) == shared:
        raise ValueError('output directory changed')


def _publish(directory, name, parent, log_root, data):
    temp = '.usage-' + secrets.token_hex(16) + '.tmp'
    fd = None
    try:
        _check_destination(directory, parent, log_root)
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        with os.fdopen(fd, 'wb') as stream:
            fd = None
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        _check_destination(directory, parent, log_root)
        os.replace(temp, name, src_dir_fd=directory, dst_dir_fd=directory)
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(temp, dir_fd=directory)
        except FileNotFoundError:
            pass


def main(argv=None):
    parser = Parser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    normalize = commands.add_parser('normalize')
    normalize.add_argument('--profile', required=True)
    normalize.add_argument('--input-manifest', required=True)
    normalize.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    config, profile, key = _config(os.environ.get('USAGE_TELEMETRY_CONFIG'), args.profile)
    selection = validate_source_selection_json(_read_file(args.input_manifest))
    if (selection['profile_id'] != args.profile or selection['profile_version'] != profile['profile_version'] or
            selection['owner_scope'] != config['owner_scope']):
        raise ValueError('selection does not match trusted configuration')
    directory, name, parent, log_root = _output_directory(args.output)
    try:
        result = adapter.normalize_selection(selection, profile=profile,
                    expected_owner_scope=config['owner_scope'], project_identifier=config['project_identifier'],
                    provider_identifier=config['provider_identifier'], run_id=config['run_id'], key=key)
        _publish(directory, name, parent, log_root, canonical_bytes(result['bundle']))
    finally:
        os.close(directory)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError, RecursionError, OverflowError, TypeError):
        print('usage telemetry: normalization failed', file=sys.stderr)
        sys.exit(1)
