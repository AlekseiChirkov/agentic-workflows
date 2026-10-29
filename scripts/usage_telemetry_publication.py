"""Publish independently authorized usage bundles without overwriting evidence.

The Python caller is a trusted boundary: it must establish registration, profile
provenance, authorized source, identity and measurement evidence independently.
A bundle or a hash-shaped identifier cannot authorize its own publication. The
caller's verifier must reject any bundle it has not independently established.
"""
import copy
import hashlib
import os
from pathlib import Path
import secrets
import stat

from usage_telemetry_contract import (canonical_bytes, observation_id,
    validate_usage_bundle, validate_usage_receipt)

_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK


def _directory(parent, name):
    try:
        os.mkdir(name, 0o700, dir_fd=parent)
    except FileExistsError:
        pass
    return os.open(name, _DIR_FLAGS, dir_fd=parent)


def _verify_directory(parent, name, child):
    current = os.stat(name, dir_fd=parent, follow_symlinks=False)
    opened = os.fstat(child)
    if not stat.S_ISDIR(current.st_mode) or (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
        raise ValueError('publication directory changed')


def _verify_file(directory, name, expected):
    fd = os.open(name, _FILE_FLAGS, dir_fd=directory)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size != len(expected):
            raise ValueError('publication conflict')
        offset = 0
        while offset < len(expected):
            chunk = os.read(fd, min(1024 * 1024, len(expected) - offset))
            if not chunk or chunk != expected[offset:offset + len(chunk)]:
                raise ValueError('publication conflict')
            offset += len(chunk)
        if os.read(fd, 1):
            raise ValueError('publication conflict')
        after = os.fstat(fd)
        named = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if ((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) !=
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                or (named.st_dev, named.st_ino) != (info.st_dev, info.st_ino)
                or not stat.S_ISREG(named.st_mode)):
            raise ValueError('publication changed')
    finally:
        os.close(fd)


def publish_usage(bundle, *, root, mode, scope, authorize):
    """Install a whole, verified bundle and return a receipt, or None when off.

    ``scope`` is the registered owner supplied by trusted caller code; ``None``
    means no registered owner. ``authorize`` is a trusted callable accepting
    the candidate and scope. It must verify the profile and all provenance; it
    must return exactly True only for explicitly authorized content.
    """
    if mode != 'on' or scope is None:
        return None
    candidate = copy.deepcopy(bundle)
    owner = copy.deepcopy(scope)
    validate_usage_bundle(candidate)
    encoded = canonical_bytes(candidate)
    digest = hashlib.sha256(encoded).hexdigest()
    receipt = {'schema_version': 1, 'kind': 'usage_accepted',
               'bundle_sha256': digest,
               'observation_ids': sorted(observation_id(item) for item in candidate['observations']),
               'scope': owner, 'duplicate': False, 'validator_version': '1'}
    validate_usage_receipt(receipt)
    if not callable(authorize) or authorize(candidate, owner) is not True:
        raise ValueError('publication provenance not authorized')
    if canonical_bytes(candidate) != encoded or owner != scope:
        raise ValueError('publication authorization changed input')

    root_fd = usage_fd = target_fd = None
    temp_name = None
    try:
        # Resolve the configured root once, then use directory-relative operations.
        root_fd = os.open(str(Path(root).resolve(strict=True)), _DIR_FLAGS)
        usage_fd = _directory(root_fd, 'usage')
        target_fd = _directory(usage_fd, 'v1')
        _verify_directory(root_fd, 'usage', usage_fd)
        _verify_directory(usage_fd, 'v1', target_fd)
        name = digest + '.json'
        try:
            _verify_file(target_fd, name, encoded)
        except FileNotFoundError:
            pass
        else:
            receipt['duplicate'] = True
            _verify_directory(root_fd, 'usage', usage_fd)
            _verify_directory(usage_fd, 'v1', target_fd)
            return receipt

        temp_name = '.usage-' + secrets.token_hex(16) + '.tmp'
        fd = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                     0o600, dir_fd=target_fd)
        try:
            view = memoryview(encoded)
            while view:
                count = os.write(fd, view)
                if count <= 0:
                    raise OSError('publication write failed')
                view = view[count:]
            os.fsync(fd)
        finally:
            os.close(fd)
        _verify_directory(root_fd, 'usage', usage_fd)
        _verify_directory(usage_fd, 'v1', target_fd)
        try:
            os.link(temp_name, name, src_dir_fd=target_fd, dst_dir_fd=target_fd,
                    follow_symlinks=False)
        except FileExistsError:
            _verify_file(target_fd, name, encoded)
            receipt['duplicate'] = True
        else:
            os.fsync(target_fd)
            _verify_file(target_fd, name, encoded)
        _verify_directory(root_fd, 'usage', usage_fd)
        _verify_directory(usage_fd, 'v1', target_fd)
        return receipt
    finally:
        if target_fd is not None and temp_name is not None:
            try:
                os.unlink(temp_name, dir_fd=target_fd)
            except FileNotFoundError:
                pass
        for fd in (target_fd, usage_fd, root_fd):
            if fd is not None:
                os.close(fd)
