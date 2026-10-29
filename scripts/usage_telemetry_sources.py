"""Bounded access to explicitly selected local telemetry sources.

The caller remains responsible for proving ownership and interpreting source
formats. A matching declared owner is an authorization boundary, not proof of
attribution. These helpers never discover neighboring files.
"""

import hashlib
import json
import os
import stat

from usage_telemetry_contract import _bounded_tree, validate_counter, validate_source_selection

RECORD_LIMIT = 16 * 1024 * 1024


def _path_parts(path):
    parts = path.split('/')
    if any(part in ('.', '..') for part in parts):
        raise ValueError('invalid local source path')
    parts = [part for part in parts if part]
    if not parts:
        raise ValueError('invalid local source path')
    return parts


def _open_regular(path):
    """Open each path component without following symlinks, including races."""
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise ValueError('safe local file access is unavailable')
    parts = _path_parts(path)
    directory = None
    try:
        directory = os.open('/' if path.startswith('/') else '.',
                            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=directory)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            os.close(descriptor)
            raise ValueError('selected source is not a regular file')
        return descriptor
    except (OSError, OverflowError):
        raise ValueError('cannot safely open selected source') from None
    finally:
        if directory is not None:
            os.close(directory)


def read_selected_sources(selection, *, expected_profile, expected_owner_scope):
    """Verify selection and read only its fixed full contents or hashed prefixes.

    Prefix digests cover exactly the selected prefix; full digests cover the
    entire declared file. All bytes returned are verified against the manifest.
    The consumer must apply its profile-specific record limits across sources.
    """
    validate_source_selection(selection)
    if ((selection['profile_id'], selection['profile_version']) != expected_profile or
            selection['owner_scope'] != expected_owner_scope):
        raise ValueError('selection profile or owner scope mismatch')
    for source in selection['sources']:
        _path_parts(source['local_path'])
    result = []
    for source in selection['sources']:
        prefix = source.get('verified_prefix_bytes')
        size = source['size_bytes'] if prefix is None else prefix
        descriptor = _open_regular(source['local_path'])
        try:
            metadata = os.fstat(descriptor)
            if ((prefix is None and metadata.st_size != source['size_bytes']) or
                    (prefix is not None and metadata.st_size < size)):
                raise ValueError('selected source size changed')
            chunks = []
            remaining = size
            while remaining:
                chunk = os.read(descriptor, min(remaining, 1024 * 1024))
                if not chunk:
                    raise ValueError('selected source ended prematurely')
                chunks.append(chunk)
                remaining -= len(chunk)
            if prefix is None and os.fstat(descriptor).st_size != size:
                raise ValueError('selected source size changed')
            data = b''.join(chunks)
            if hashlib.sha256(data).hexdigest() != source['sha256']:
                raise ValueError('selected source digest mismatch')
            result.append({'source_id': source['source_id'], 'data': data,
                           'partial': prefix is not None})
        except (OSError, OverflowError):
            raise ValueError('cannot read selected source') from None
        finally:
            os.close(descriptor)
    return result


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate record key')
        value[key] = item
    return value


def _invalid_constant(_value):
    raise ValueError('invalid record number')


def parse_json_records(data, *, max_records):
    """Parse bounded UTF-8 JSON lines; reject the batch on limit violations."""
    validate_counter(max_records)
    if not max_records or not isinstance(data, bytes):
        raise ValueError('invalid record input or limit')
    records = []
    for line in data.splitlines():
        if not line.strip():
            continue
        if len(line) > RECORD_LIMIT or len(records) >= max_records:
            raise ValueError('record limit exceeded')
        try:
            value = json.loads(line.decode('utf-8'), object_pairs_hook=_unique_pairs,
                               parse_constant=_invalid_constant)
            _bounded_tree(value)
        except (ValueError, UnicodeError, RecursionError):
            raise ValueError('invalid source record') from None
        records.append(value)
    return records
