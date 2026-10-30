"""Publish independently authorized usage bundles without overwriting evidence.

The Python caller is a trusted boundary: it must establish registration, profile
provenance, authorized source, identity and measurement evidence independently.
A bundle or a hash-shaped identifier cannot authorize its own publication. The
caller's verifier must reject any bundle it has not independently established.
"""
import copy
import ctypes
import errno
import hashlib
import os
from pathlib import Path
import secrets
import stat

from usage_telemetry_contract import (canonical_bytes, observation_id,
    validate_usage_bundle, validate_usage_receipt, validate_decimal,
    validate_lifecycle_projection)

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
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size != len(expected):
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
                or after.st_nlink != 1 or named.st_nlink != 1
                or not stat.S_ISREG(named.st_mode)):
            raise ValueError('publication changed')
    finally:
        os.close(fd)


def _install(temporary_fd, directory, name):
    """Link an unnamed file without replacement; unsupported systems fail closed."""
    library = ctypes.CDLL(None, use_errno=True)
    link = getattr(library, 'linkat', None)
    if link is None:
        raise OSError(errno.ENOTSUP, 'atomic publication unavailable')
    link.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                     ctypes.c_char_p, ctypes.c_int)
    link.restype = ctypes.c_int
    # AT_EMPTY_PATH links the already-open anonymous file, not a replaceable path.
    if link(temporary_fd, b'', directory, os.fsencode(name), 0x1000) != 0:
        code = ctypes.get_errno()
        raise OSError(code, 'atomic publication failed')


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
    if not callable(authorize):
        raise ValueError('publication provenance not authorized')
    try:
        authorized = authorize(candidate, owner)
    except Exception:
        raise ValueError('publication provenance not authorized') from None
    if authorized is not True:
        raise ValueError('publication provenance not authorized')
    if canonical_bytes(candidate) != encoded or owner != scope:
        raise ValueError('publication authorization changed input')

    root_fd = usage_fd = target_fd = temporary_fd = None
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

        if not hasattr(os, 'O_TMPFILE'):
            raise OSError(errno.ENOTSUP, 'anonymous publication unavailable')
        temporary_fd = os.open('.', os.O_TMPFILE | os.O_RDWR | os.O_CLOEXEC,
                               0o600, dir_fd=target_fd)
        os.fchmod(temporary_fd, 0o600)
        view = memoryview(encoded)
        while view:
            count = os.write(temporary_fd, view)
            if count <= 0:
                raise OSError('publication write failed')
            view = view[count:]
        os.fsync(temporary_fd)
        _verify_directory(root_fd, 'usage', usage_fd)
        _verify_directory(usage_fd, 'v1', target_fd)
        try:
            _install(temporary_fd, target_fd, name)
        except FileExistsError:
            _verify_file(target_fd, name, encoded)
            receipt['duplicate'] = True
        else:
            os.fsync(target_fd)
            _verify_file(target_fd, name, encoded)
            installed = os.stat(name, dir_fd=target_fd, follow_symlinks=False)
            staged = os.fstat(temporary_fd)
            if ((installed.st_dev, installed.st_ino) != (staged.st_dev, staged.st_ino)
                    or staged.st_nlink != 1):
                raise ValueError('publication changed')
        _verify_directory(root_fd, 'usage', usage_fd)
        _verify_directory(usage_fd, 'v1', target_fd)
        return receipt
    finally:
        for fd in (temporary_fd, target_fd, usage_fd, root_fd):
            if fd is not None:
                os.close(fd)


def validate_lifecycle_projection_for_owner(projection, *, scope, authorize, cost_usd=None):
    """Validate a projection using an independently supplied trust boundary.

    The trusted caller supplies the registered owner and a verifier that checks
    profile, source, inventory, contributor identity, scope, privacy, pricing
    applicability and each evidence association independently. Structural
    validation and content hashes alone do not establish any of these facts.
    The verifier must return exactly True for the original candidate and owner.
    The caller must protect the verifier from control by the candidate's author.
    """
    candidate = copy.deepcopy(projection)
    owner = copy.deepcopy(scope)
    validate_lifecycle_projection(candidate)
    if candidate['scope'] != owner:
        raise ValueError('projection owner mismatch')
    if cost_usd is not None:
        validate_decimal(cost_usd)
        if candidate.get('cost_usd') != cost_usd:
            raise ValueError('projection scalar mismatch')
    encoded = canonical_bytes(candidate)
    if not callable(authorize):
        raise ValueError('projection provenance not authorized')
    try:
        accepted = authorize(candidate, owner)
    except Exception:
        raise ValueError('projection provenance not authorized') from None
    if accepted is not True:
        raise ValueError('projection provenance not authorized')
    if canonical_bytes(candidate) != encoded or owner != scope:
        raise ValueError('projection authorization changed input')
    return candidate
