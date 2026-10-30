#!/usr/bin/env python3
"""Persist owner-approved warning delivery and recover interrupted notes.

The caller acts for the sole authorized owner. The owner scope and destination map
must come from its private authorization context, not from the proposal. State
and note writers must cooperate with the same advisory locks and respect file
and directory ownership. Same-user writers that ignore locks can race path
replacement; ordinary filesystem operations cannot guarantee exclusion of them.
"""
import contextlib
import copy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import secrets
import stat

_spec = importlib.util.spec_from_file_location(
    '_usage_delivery_contract', Path(__file__).with_name('usage_telemetry_contract.py'))
_contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_contract)

_LIMIT = 1024 * 1024


def _check_destinations(state_path, destinations):
    """Reject obvious shared-store targets before opening the owner lock."""
    if not isinstance(destinations, dict):
        raise ValueError('invalid destinations')
    log_root = os.environ.get('ORCHESTRAIL_LOG_ROOT') or str(Path(__file__).resolve().parents[1] / 'logs')
    shared = os.path.realpath(os.path.join(log_root, 'usage', 'v1'))
    for path in [state_path, *destinations.values()]:
        resolved = os.path.realpath(os.fspath(path))
        if os.path.commonpath((resolved, shared)) == shared:
            raise ValueError('destination is in shared storage')


def _directory(path):
    path = os.path.abspath(os.fspath(path))
    parent, name = os.path.split(path)
    if not name or name in ('.', '..'):
        raise ValueError('invalid destination')
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parent.split('/'):
            if part:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                os.close(directory)
                directory = child
        info = os.fstat(directory)
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o022:
            raise ValueError('uncontrolled directory')
        return directory, name
    except BaseException:
        os.close(directory)
        raise


def _regular(fd):
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
            info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o022):
        raise ValueError('invalid file')
    return info


def _read(fd):
    info = _regular(fd)
    if info.st_size > _LIMIT:
        raise ValueError('state exceeds limit')
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = []
    remaining = _LIMIT + 1
    while remaining:
        part = os.read(fd, min(65536, remaining))
        if not part:
            break
        chunks.append(part)
        remaining -= len(part)
    data = b''.join(chunks)
    if len(data) > _LIMIT:
        raise ValueError('state exceeds limit')
    return data


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate state key')
        result[key] = value
    return result


def _load(directory, name):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
    try:
        data = _read(fd)
        info = os.fstat(fd)
    finally:
        os.close(fd)
    try:
        value = json.loads(data.decode('utf-8'), object_pairs_hook=_unique_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        _contract.validate_current_run_snapshot(value)
        return value, info
    except (ValueError, TypeError, UnicodeError, RecursionError, KeyError):
        raise ValueError('invalid owner state') from None


def _save(directory, name, state, previous):
    data = _contract.canonical_bytes(state)
    if len(data) > _LIMIT:
        raise ValueError('state exceeds limit')
    current = os.stat(name, dir_fd=directory, follow_symlinks=False)
    if (current.st_dev, current.st_ino, current.st_mtime_ns, current.st_size) != (
            previous.st_dev, previous.st_ino, previous.st_mtime_ns, previous.st_size):
        raise ValueError('owner state changed')
    temp = '.' + name + '.' + secrets.token_hex(16) + '.tmp'
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 stat.S_IMODE(previous.st_mode), dir_fd=directory)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if (current.st_dev, current.st_ino, current.st_mtime_ns, current.st_size, current.st_ctime_ns) != (
                previous.st_dev, previous.st_ino, previous.st_mtime_ns, previous.st_size, previous.st_ctime_ns):
            raise ValueError('owner state changed')
        os.replace(temp, name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        try:
            os.unlink(temp, dir_fd=directory)
        except FileNotFoundError:
            pass


@contextlib.contextmanager
def _locked(path):
    directory, name = _directory(path)
    try:
        lock_name = '.' + name + '.lock'
        lock = os.open(lock_name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600,
                       dir_fd=directory)
        try:
            info = _regular(lock)
            if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise ValueError('invalid owner lock')
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield directory, name
        finally:
            os.close(lock)
    finally:
        os.close(directory)


def _check_owner(state, owner):
    if not isinstance(owner, dict) or state['owner_scope'] != owner:
        raise ValueError('owner scope mismatch')


def _append_note(path, warning, protected):
    """Replace one cooperatively locked note after verifying its current bytes.

    The path's owner and all writers must obey the owner lock protocol; no
    portable operation atomically compares the old inode while replacing it.
    """
    directory = None
    temp = None
    try:
        directory, name = _directory(path)
        fd = os.open(name, os.O_RDWR | os.O_NOFOLLOW, dir_fd=directory)
        try:
            info = _regular(fd)
            if (info.st_dev, info.st_ino) in protected:
                return None
            fcntl.flock(fd, fcntl.LOCK_EX)
            info = _regular(fd)
            data = _read(fd)
            marker = ('- Telemetry warning (' + warning['metric'] + ') ' +
                      warning['warning_id']).encode('ascii')
            current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
                return None
            if any(line == marker or line.startswith(marker + b' ') for line in data.splitlines()):
                os.fsync(fd)
                os.fsync(directory)
                return (info.st_dev, info.st_ino)
            payload = {'scope': warning['scope'], 'details': warning.get('details')}
            addition = ((b'' if not data or data.endswith(b'\n') else b'\n') + marker + b' ' +
                        _contract.canonical_bytes(payload) + b'\n')
            if len(data) + len(addition) > _LIMIT:
                return None
            temp = '.' + name + '.' + secrets.token_hex(16) + '.tmp'
            new_fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             stat.S_IMODE(info.st_mode), dir_fd=directory)
            try:
                payload = data + addition
                if os.write(new_fd, payload) != len(payload):
                    return None
                os.fsync(new_fd)
            finally:
                os.close(new_fd)
            current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            after = _regular(fd)
            if ((current.st_dev, current.st_ino, current.st_mtime_ns, current.st_size, current.st_ctime_ns) !=
                    (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size, info.st_ctime_ns) or
                    (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size, after.st_ctime_ns) !=
                    (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size, info.st_ctime_ns) or _read(fd) != data):
                return None
            os.replace(temp, name, src_dir_fd=directory, dst_dir_fd=directory)
            temp = None
            os.fsync(directory)
            replaced = os.stat(name, dir_fd=directory, follow_symlinks=False)
            return (replaced.st_dev, replaced.st_ino)
        finally:
            os.close(fd)
    except (OSError, ValueError, TypeError):
        return None
    finally:
        if directory is not None:
            if temp is not None:
                try:
                    os.unlink(temp, dir_fd=directory)
                except FileNotFoundError:
                    pass
            os.close(directory)


def _destination_unchanged(path, identity):
    directory = None
    try:
        directory, name = _directory(path)
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        try:
            info = _regular(fd)
            return (info.st_dev, info.st_ino) == identity
        finally:
            os.close(fd)
    except (OSError, ValueError, TypeError):
        return False
    finally:
        if directory is not None:
            os.close(directory)


def _deliver(directory, name, state, destinations, checkpoint):
    state_info = os.stat(name, dir_fd=directory, follow_symlinks=False)
    lock_info = os.stat('.' + name + '.lock', dir_fd=directory, follow_symlinks=False)
    protected = {(state_info.st_dev, state_info.st_ino), (lock_info.st_dev, lock_info.st_ino)}
    for warning in state['warning_delivery']:
        if warning['delivery_state'] != 'pending':
            continue
        scope = warning['scope']
        current, _ = _load(directory, name)
        if current != state:
            raise ValueError('owner state changed')
        destination = destinations.get((scope['owner_kind'], scope['owner_id']))
        identity = None if destination is None else _append_note(destination, warning, protected)
        if identity is None:
            continue
        if checkpoint is not None:
            checkpoint('after_note')
        if not _destination_unchanged(destination, identity):
            continue
        current, info = _load(directory, name)
        if current != state:
            raise ValueError('owner state changed')
        state = copy.deepcopy(state)
        selected = next(item for item in state['warning_delivery']
                        if item['warning_id'] == warning['warning_id'])
        selected['delivery_state'] = 'delivered'
        state['revision'] += 1
        _contract.validate_current_run_snapshot(state)
        _save(directory, name, state, info)
        state_info = os.stat(name, dir_fd=directory, follow_symlinks=False)
        protected.add((state_info.st_dev, state_info.st_ino))
    return {'warnings': [{'warning_id': item['warning_id'], 'scope': copy.deepcopy(item['scope']),
                          'metric': item['metric'], 'details': copy.deepcopy(item.get('details')),
                          'delivery_state': item['delivery_state'],
                          'reason': 'destination_unavailable' if item['delivery_state'] == 'pending' else None}
                         for item in state['warning_delivery']]}


def apply_revision(state_path, expected_revision, proposal, *, owner_scope, destinations,
                   checkpoint=None):
    """Accept one revision from a trusted owner, then attempt pending notes."""
    try:
        _contract.validate_current_run_snapshot(proposal)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise ValueError('invalid proposed state') from None
    _check_destinations(state_path, destinations)
    with _locked(state_path) as (directory, name):
        current, info = _load(directory, name)
        _check_owner(current, owner_scope)
        _check_owner(proposal, owner_scope)
        if (type(expected_revision) is not int or current['revision'] != expected_revision or
                proposal['revision'] != expected_revision + 1):
            raise ValueError('stale owner state')
        protected = lambda state: {key: value for key, value in state.items()
                                   if key not in ('revision', 'warning_delivery')}
        expected = _contract.sanitized_snapshot(current)
        if _contract.canonical_bytes(protected(expected)) != _contract.canonical_bytes(protected(proposal)):
            raise ValueError('status proposal changed owner evidence')
        previous = {item['warning_id']: item for item in current['warning_delivery']}
        if any(part['kind'] == 'warning_delivery' for part in current.get('parts', [])):
            spec = importlib.util.spec_from_file_location('_usage_status_cli', Path(__file__).with_name('usage-telemetry.py'))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            materialized, _, _ = module._snapshot_with_parts(_contract.canonical_bytes(current))
            previous.update({item['warning_id']: item for item in materialized['warning_delivery']})
        proposed = {item['warning_id']: item for item in proposal['warning_delivery']}
        if not previous.keys() <= proposed.keys():
            raise ValueError('warning history cannot be removed')
        for warning_id, item in proposed.items():
            old = previous.get(warning_id)
            if old is None:
                if item['delivery_state'] != 'pending':
                    raise ValueError('new warning must be pending')
            else:
                if old.get('details') != item.get('details'):
                    raise ValueError('warning details cannot change')
                if any(old[key] != item[key] for key in ('warning_id', 'policy_id', 'policy_version',
                        'scope', 'owner_scope', 'metric', 'episode')):
                    raise ValueError('warning identity changed')
                if old['delivery_state'] == 'delivered' and item['delivery_state'] != 'delivered':
                    raise ValueError('confirmed warning cannot be reset')
                if old['delivery_state'] == 'pending' and item['delivery_state'] != 'pending':
                    raise ValueError('pending warning cannot be reset')
                if old['delivery_state'] != 'delivered' and item['delivery_state'] == 'delivered':
                    raise ValueError('warning confirmation requires delivery')
        accepted = copy.deepcopy(current)
        accepted['revision'] = proposal['revision']
        accepted['warning_delivery'] = copy.deepcopy(proposal['warning_delivery'])
        _contract.validate_current_run_snapshot(accepted)
        _save(directory, name, accepted, info)
        if checkpoint is not None:
            checkpoint('after_accept')
        return _deliver(directory, name, accepted, destinations, checkpoint)


def resume_delivery(state_path, *, owner_scope, destinations, checkpoint=None):
    """Retry pending notes without accepting a new status proposal."""
    _check_destinations(state_path, destinations)
    with _locked(state_path) as (directory, name):
        state, _ = _load(directory, name)
        _check_owner(state, owner_scope)
        return _deliver(directory, name, state, destinations, checkpoint)
