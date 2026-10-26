#!/usr/bin/env python3
"""Own exact user hook occurrences and recover interrupted settings replacements.

Called by install-hooks.sh. Settings numbers retain their original JSON tokens;
ownership control numbers are independently validated before they affect quotas.
"""

from __future__ import annotations

import copy
from collections.abc import Hashable
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import time
from typing import NoReturn, TypeAlias, cast


EVENTS = ('Stop', 'SubagentStop')
MAX_COUNT = 9007199254740991
NumericKey: TypeAlias = tuple[bool, str, int]
if hasattr(sys, 'set_int_max_str_digits'):
    sys.set_int_max_str_digits(0)


class Unavailable(Exception):
    """A safe reason code, never settings or exception text."""


class Number:
    """A JSON numeric lexeme, with exact mathematical comparison."""

    token: str

    def __init__(self, token: str) -> None:
        self.token = token

    def key(self) -> NumericKey:
        mantissa, _, exponent = self.token.lower().partition('e')
        negative = mantissa.startswith('-')
        mantissa = mantissa.lstrip('-')
        integer, _, fraction = mantissa.partition('.')
        digits = (integer + fraction).lstrip('0')
        if not digits:
            return (False, '0', 0)
        trimmed = digits.rstrip('0')
        power = int(exponent or '0') - len(fraction) + len(digits) - len(trimmed)
        return (negative, trimmed, power)


JsonValue: TypeAlias = Number | str | int | bool | None | list['JsonValue'] | dict[str, 'JsonValue']
JsonObject: TypeAlias = dict[str, JsonValue]
JsonKey: TypeAlias = tuple[str, Hashable]
Hooks: TypeAlias = dict[str, list[JsonObject]]
QuotaKey: TypeAlias = tuple[Hashable, ...]


@dataclass(frozen=True)
class Installation:
    operation: str
    source: str
    settings_path: Path
    receipt_path: Path


@dataclass(frozen=True)
class Snapshot:
    settings_data: bytes | None
    settings: JsonObject
    receipt: JsonObject | None


@dataclass(frozen=True)
class Update:
    previous: Snapshot
    settings_data: bytes | None
    receipt: JsonObject


def pairs_unique(pairs: list[tuple[str, JsonValue]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def reject_constant(_token: str) -> NoReturn:
    raise ValueError('non-JSON number')


def decode(data: bytes, reason: str) -> JsonValue:
    try:
        return cast(JsonValue, json.loads(data, parse_int=Number, parse_float=Number,
                                         parse_constant=reject_constant, object_pairs_hook=pairs_unique))
    except (ValueError, UnicodeError, RecursionError):
        raise Unavailable(reason) from None


def encode(value: JsonValue) -> str:
    """Serialize without sending existing numbers through binary floats."""
    if isinstance(value, Number):
        return value.token
    if value is None or isinstance(value, (str, bool)) or type(value) is int:
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, list):
        return '[' + ','.join(encode(item) for item in value) + ']'
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(key, ensure_ascii=True) + ':' + encode(value[key])
                              for key in sorted(value)) + '}'
    raise Unavailable('invalid-json-value')


def key(value: JsonValue) -> JsonKey:
    if isinstance(value, Number):
        return ('number', value.key())
    if type(value) is int:
        return ('number', Number(str(value)).key())
    if isinstance(value, dict):
        return ('object', tuple((name, key(item)) for name, item in sorted(value.items())))
    if isinstance(value, list):
        return ('array', tuple(key(item) for item in value))
    return (type(value).__name__, value)


def equal(left: JsonValue, right: JsonValue) -> bool:
    return key(left) == key(right)


def require(condition: bool, reason: str = 'invalid-ownership') -> None:
    if not condition:
        raise Unavailable(reason)


def control(value: JsonValue, version: bool = False) -> int:
    token = value.token if isinstance(value, Number) else str(value) if type(value) is int else ''
    if version:
        require(token == '1')
        return 1
    require(bool(re.fullmatch(r'[1-9][0-9]*', token)) and len(token) <= len(str(MAX_COUNT)))
    parsed = int(token)
    require(parsed <= MAX_COUNT)
    return parsed


def fields(value: JsonValue, names: tuple[str, ...]) -> JsonObject:
    require(isinstance(value, dict) and set(value) == set(names))
    return cast(JsonObject, value)


def selector(group: JsonObject) -> JsonObject:
    return {name: value for name, value in group.items() if name != 'hooks'}


def validate_settings(settings: JsonValue) -> None:
    require(isinstance(settings, dict), 'invalid-settings')
    record = cast(JsonObject, settings)
    if 'hooks' not in record:
        return
    require(isinstance(record['hooks'], dict), 'invalid-settings')
    for groups in cast(JsonObject, record['hooks']).values():
        require(isinstance(groups, list), 'invalid-settings')
        for group in cast(list[JsonValue], groups):
            require(isinstance(group, dict) and isinstance(group.get('hooks'), list), 'invalid-settings')
            handlers = cast(list[JsonValue], cast(JsonObject, group)['hooks'])
            require(all(isinstance(handler, dict) for handler in handlers), 'invalid-settings')


def validate_committed(receipt: JsonValue) -> None:
    if receipt is None:
        return
    record = fields(receipt, ('schema_version', 'state', 'owned', 'created_groups'))
    control(record['schema_version'], version=True)
    require(record['state'] == 'committed')
    for name in ('owned', 'created_groups'):
        require(isinstance(record[name], list))
        seen: set[QuotaKey] = set()
        for raw_claim in cast(list[JsonValue], record[name]):
            names = ('event', 'selector', 'handler', 'count') if name == 'owned' else ('event', 'selector', 'count')
            claim = fields(raw_claim, names)
            require(claim['event'] in EVENTS and isinstance(claim['selector'], dict))
            require('hooks' not in cast(JsonObject, claim['selector']))
            if name == 'owned':
                require(isinstance(claim['handler'], dict))
            control(claim['count'])
            identity: QuotaKey = (cast(str, claim['event']), key(claim['selector']))
            if name == 'owned':
                identity += (key(claim['handler']),)
            require(identity not in seen)
            seen.add(identity)


def validate_image(image_value: JsonValue) -> None:
    record = fields(image_value, ('present', 'sha256'))
    require(type(record['present']) is bool)
    if record['present']:
        digest = record['sha256']
        require(isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest) is not None)
    else:
        require(record['sha256'] is None)


def validate_receipt(receipt: JsonValue) -> None:
    if receipt is None:
        return
    require(isinstance(receipt, dict))
    record = cast(JsonObject, receipt)
    if record.get('state') != 'prepared':
        validate_committed(record)
        return
    fields(record, ('schema_version', 'state', 'previous', 'next', 'before', 'after'))
    control(record['schema_version'], version=True)
    validate_committed(record['previous'])
    validate_committed(record['next'])
    validate_image(record['before'])
    validate_image(record['after'])


def read_bytes(path: Path) -> bytes | None:
    require(not path.is_symlink(), 'unsafe-settings-path')
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def image(data: bytes | None) -> JsonObject:
    return {'present':data is not None,
            'sha256':hashlib.sha256(data).hexdigest() if data is not None else None}


def stage(path: Path, data: bytes, mode: int = 0o600) -> Path:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, filename = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    temporary = Path(filename)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        return temporary
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def replace_receipt(path: Path, value: JsonObject | None) -> None:
    if value is None:
        path.unlink(missing_ok=True)
        return
    temporary = stage(path, (encode(value) + '\n').encode('ascii'))
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def empty_receipt() -> JsonObject:
    return {'schema_version':1, 'state':'committed', 'owned':[], 'created_groups':[]}


def remove_group_handlers(group: JsonObject, event: str, quotas: dict[QuotaKey, int]) -> bool:
    group_key = (event, key(selector(group)))
    handlers: list[JsonValue] = []
    removed = False
    for handler in cast(list[JsonValue], group['hooks']):
        identity = group_key + (key(handler),)
        if quotas.get(identity, 0) > 0:
            quotas[identity] -= 1
            removed = True
        else:
            handlers.append(handler)
    group['hooks'] = handlers
    return removed


def remove_owned(settings: JsonObject, receipt: JsonObject | None) -> None:
    if receipt is None:
        return
    hooks = cast(Hooks, settings.get('hooks', {}))
    quotas: dict[QuotaKey, int] = {
        (cast(str, claim['event']), key(claim['selector']), key(claim['handler'])):control(claim['count'])
        for claim in cast(list[JsonObject], receipt['owned'])}
    group_quotas: dict[QuotaKey, int] = {
        (cast(str, claim['event']), key(claim['selector'])):control(claim['count'])
        for claim in cast(list[JsonObject], receipt['created_groups'])}
    for event, groups in hooks.items():
        retained = []
        for group in groups:
            group_key = (event, key(selector(group)))
            removed = remove_group_handlers(group, event, quotas)
            if removed and not group['hooks'] and group_quotas.get(group_key, 0) > 0:
                group_quotas[group_key] -= 1
            else:
                retained.append(group)
        hooks[event] = retained


def validate_manifest_group(group: JsonValue, expected: JsonObject) -> JsonObject:
    require(isinstance(group, dict) and isinstance(group.get('hooks'), list), 'invalid-manifest')
    record = cast(JsonObject, group)
    handlers = cast(list[JsonValue], record['hooks'])
    require(len(handlers) == 1 and equal(handlers[0], expected), 'invalid-manifest')
    return record


def load_manifest(source: str) -> Hooks:
    try:
        source_path = Path(source).resolve(strict=True)
        require(source_path.is_dir() and (source_path / 'hooks/log-step-hook.sh').is_file() and
                (source_path / 'scripts/log-step.sh').is_file(), 'invalid-source')
        document = decode((source_path / 'harness/claude/hooks.json').read_bytes(), 'invalid-manifest')
    except (OSError, ValueError):
        raise Unavailable('invalid-source') from None
    require(isinstance(document, dict) and set(document) == {'hooks'}, 'invalid-manifest')
    hooks_value = cast(JsonObject, document)['hooks']
    require(isinstance(hooks_value, dict) and set(hooks_value) == set(EVENTS), 'invalid-manifest')
    hooks = cast(Hooks, hooks_value)
    expected: JsonObject = {'type':'command', 'command':'bash', 'args':['@ORCHESTRAIL_HOME@/hooks/log-step-hook.sh'],
                            'timeout':10, 'onFailure':'continue'}
    for groups in hooks.values():
        require(isinstance(groups, list) and len(groups) == 1, 'invalid-manifest')
        group = validate_manifest_group(groups[0], expected)
        handler = cast(list[JsonObject], group['hooks'])[0]
        handler['args'] = [str(source_path / 'hooks/log-step-hook.sh')]
    return hooks


def insert_manifest(settings: JsonObject, manifest: Hooks) -> JsonObject:
    receipt = empty_receipt()
    owned = cast(list[JsonObject], receipt['owned'])
    created = cast(list[JsonObject], receipt['created_groups'])
    hooks = cast(Hooks, settings.setdefault('hooks', {}))
    for event, manifest_groups in manifest.items():
        groups = hooks.setdefault(event, [])
        for desired in manifest_groups:
            desired_selector = selector(desired)
            matching = [group for group in groups if equal(selector(group), desired_selector)]
            for handler in cast(list[JsonValue], desired['hooks']):
                if any(equal(existing, handler) for group in matching for existing in cast(list[JsonValue], group['hooks'])):
                    continue
                if not matching:
                    group = copy.deepcopy(desired_selector)
                    group['hooks'] = []
                    groups.append(group)
                    matching.append(group)
                    created.append({'event':event, 'selector':copy.deepcopy(desired_selector), 'count':1})
                cast(list[JsonValue], matching[0]['hooks']).append(copy.deepcopy(handler))
                owned.append({'event':event, 'selector':copy.deepcopy(desired_selector),
                              'handler':copy.deepcopy(handler), 'count':1})
    return receipt


def acquire_lock(path: Path) -> int:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    require(not path.is_symlink(), 'unsafe-lock-path')
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        deadline = time.monotonic() + 5
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return descriptor
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise Unavailable('installer-busy') from None
                time.sleep(0.025)
    except BaseException:
        os.close(descriptor)
        raise


def read_settings(path: Path) -> tuple[bytes | None, JsonObject]:
    settings_data = read_bytes(path)
    settings = decode(settings_data, 'invalid-settings') if settings_data is not None else {}
    validate_settings(settings)
    return settings_data, cast(JsonObject, settings)


def load_snapshot(installation: Installation) -> Snapshot:
    settings_data, settings = read_settings(installation.settings_path)
    receipt_data = read_bytes(installation.receipt_path)
    receipt = decode(receipt_data, 'invalid-ownership') if receipt_data is not None else None
    if receipt_data is not None:
        require(isinstance(receipt, dict))
    validate_receipt(receipt)
    return Snapshot(settings_data, settings, cast(JsonObject | None, receipt))


def recover_snapshot(installation: Installation, snapshot: Snapshot) -> Snapshot:
    receipt = snapshot.receipt
    if receipt is None or receipt['state'] != 'prepared':
        return snapshot
    current_image = image(snapshot.settings_data)
    if equal(current_image, receipt['before']):
        recovered = receipt['previous']
    elif equal(current_image, receipt['after']):
        recovered = receipt['next']
    else:
        raise Unavailable('settings-changed-during-transaction')
    recovered_receipt = cast(JsonObject | None, recovered)
    replace_receipt(installation.receipt_path, recovered_receipt)
    # Recovery never rewrites settings; refresh them before the new operation.
    settings_data, settings = read_settings(installation.settings_path)
    return Snapshot(settings_data, settings, recovered_receipt)


def plan_update(installation: Installation, snapshot: Snapshot) -> Update | None:
    result = copy.deepcopy(snapshot.settings)
    remove_owned(result, snapshot.receipt)
    next_receipt = (insert_manifest(result, load_manifest(installation.source))
                    if installation.operation == 'install' else empty_receipt())
    validate_settings(result)
    validate_committed(next_receipt)
    if equal(result, snapshot.settings) and (equal(next_receipt, snapshot.receipt) or
                                           (snapshot.receipt is None and installation.operation == 'uninstall')):
        return None
    # Keep exact bytes if only ownership changes or numbers are spelled differently.
    next_data = snapshot.settings_data if equal(result, snapshot.settings) else (encode(result) + '\n').encode('ascii')
    return Update(snapshot, next_data, next_receipt)


def stage_settings(installation: Installation, update: Update) -> Path | None:
    if update.settings_data is None:
        return None
    mode = (stat.S_IMODE(installation.settings_path.stat().st_mode)
            if update.previous.settings_data is not None else 0o600)
    return stage(installation.settings_path, update.settings_data, mode)


def build_prepared_receipt(update: Update) -> JsonObject:
    prepared: JsonObject = {'schema_version':1, 'state':'prepared', 'previous':update.previous.receipt,
                            'next':update.receipt, 'before':image(update.previous.settings_data),
                            'after':image(update.settings_data)}
    validate_receipt(prepared)
    return prepared


def replace_settings(path: Path, temporary: Path | None) -> None:
    if temporary is not None:
        os.replace(temporary, path)
    else:
        path.unlink(missing_ok=True)


def commit_update(installation: Installation, update: Update) -> None:
    settings_temporary: Path | None = None
    ownership_temporary: Path | None = None
    try:
        settings_temporary = stage_settings(installation, update)
        ownership_temporary = stage(installation.receipt_path, (encode(update.receipt) + '\n').encode('ascii'))
        prepared = build_prepared_receipt(update)
        replace_receipt(installation.receipt_path, prepared)
        require(equal(image(read_bytes(installation.settings_path)), prepared['before']),
                'settings-changed-during-transaction')
        replace_settings(installation.settings_path, settings_temporary)
        os.replace(ownership_temporary, installation.receipt_path)
    finally:
        for temporary in (settings_temporary, ownership_temporary):
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def apply(installation: Installation) -> None:
    snapshot = recover_snapshot(installation, load_snapshot(installation))
    update = plan_update(installation, snapshot)
    if update is not None:
        commit_update(installation, update)


def main() -> None:
    operation, source = sys.argv[1:]
    lock: int | None = None
    try:
        home = Path(os.environ['HOME'])
        config = Path(os.environ.get('XDG_CONFIG_HOME') or home / '.config').absolute()
        settings = home.absolute() / '.claude/settings.json'
        receipt = config / 'orchestrail/hooks-installed.json'
        lock = acquire_lock(config / 'orchestrail/hooks-installed.lock')
        apply(Installation(operation, source, settings, receipt))
        output = {'status':'installed' if operation == 'install' else 'uninstalled'}
    except Unavailable as error:
        output = {'status':'unavailable', 'reason':str(error)}
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        output = {'status':'unavailable', 'reason':'installer-io-or-data-error'}
    finally:
        if lock is not None:
            os.close(lock)
    if output['status'] == 'unavailable':
        print('orchestrail hooks unavailable: ' + output['reason'], file=sys.stderr)
    print(json.dumps(output, sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
