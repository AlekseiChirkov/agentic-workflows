#!/usr/bin/env python3
"""Own exact user hook occurrences and recover interrupted settings replacements.

Called by install-hooks.sh. The manifest declares every event and its one handler;
each group is validated against the handler shape before placeholder substitution.
The permission fragment adds deny rules, owned by exact counts like handlers.
Settings numbers retain their original JSON tokens; ownership control numbers are
independently validated before they affect quotas.
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


EVENT_NAME = re.compile(r'[A-Z][A-Za-z]*')
GROUP_FIELDS = frozenset({'matcher', 'hooks'})
HANDLER_FIELDS = frozenset({'type', 'command', 'args', 'timeout', 'onFailure'})
SCRIPT_ARGUMENT = re.compile(r'@ORCHESTRAIL_HOME@/(hooks/[a-z][a-z0-9-]*\.sh)')
TIMEOUT_SECONDS = re.compile(r'[1-9][0-9]{0,3}')
# The one failure mode each event's handler may declare. A tool-gating handler decides
# whether a tool call runs, so it must block when it cannot answer; a logging handler must
# never stop a session. A handler for any other event is not registered.
FAILURE_MODES: dict[str, str] = {'PreToolUse':'block', 'Stop':'continue', 'SubagentStop':'continue'}
# A tool-gating handler also needs a matcher naming the tools it gates.
TOOL_GATING_EVENTS = ('PreToolUse',)
# Files the registered hooks load beside themselves or call at run time.
SOURCE_DEPENDENCIES = ('hooks/git_rails.py', 'scripts/log-step.sh')
PERMISSION_FRAGMENT = 'harness/claude/permissions.json'
# A fragment rule is one exact Bash command: no control characters, no `*` wildcard and
# no `)` before the closing parenthesis.
PERMISSION_RULE = re.compile(r'Bash\([^\x00-\x1f\x7f*)]+\)')
PERMISSIONS = 'permissions'
PERMISSION_LIST = 'deny'
RECEIPT_FIELDS: dict[int, tuple[str, ...]] = {
    1: ('schema_version', 'state', 'owned', 'created_groups'),
    2: ('schema_version', 'state', 'owned', 'created_groups', 'owned_permissions', 'created_permissions')}
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
        require(token in tuple(str(number) for number in RECEIPT_FIELDS))
        return int(token)
    require(bool(re.fullmatch(r'[1-9][0-9]*', token)) and len(token) <= len(str(MAX_COUNT)))
    parsed = int(token)
    require(parsed <= MAX_COUNT)
    return parsed


def fields(value: JsonValue, names: tuple[str, ...]) -> JsonObject:
    require(isinstance(value, dict) and set(value) == set(names))
    return cast(JsonObject, value)


def selector(group: JsonObject) -> JsonObject:
    return {name: value for name, value in group.items() if name != 'hooks'}


def is_event_name(value: JsonValue) -> bool:
    return isinstance(value, str) and EVENT_NAME.fullmatch(value) is not None


def validate_permissions(record: JsonObject) -> None:
    if PERMISSIONS not in record:
        return
    permissions = record[PERMISSIONS]
    require(isinstance(permissions, dict), 'invalid-settings')
    if PERMISSION_LIST in cast(JsonObject, permissions):
        rules = cast(JsonObject, permissions)[PERMISSION_LIST]
        require(isinstance(rules, list) and all(isinstance(rule, str) for rule in rules), 'invalid-settings')


def validate_settings(settings: JsonValue) -> None:
    require(isinstance(settings, dict), 'invalid-settings')
    record = cast(JsonObject, settings)
    validate_permissions(record)
    if 'hooks' not in record:
        return
    require(isinstance(record['hooks'], dict), 'invalid-settings')
    for groups in cast(JsonObject, record['hooks']).values():
        require(isinstance(groups, list), 'invalid-settings')
        for group in cast(list[JsonValue], groups):
            require(isinstance(group, dict) and isinstance(group.get('hooks'), list), 'invalid-settings')
            handlers = cast(list[JsonValue], cast(JsonObject, group)['hooks'])
            require(all(isinstance(handler, dict) for handler in handlers), 'invalid-settings')


def validate_permission_claims(record: JsonObject) -> None:
    claims, created = record['owned_permissions'], record['created_permissions']
    require(isinstance(claims, list) and isinstance(created, list))
    seen: set[str] = set()
    for raw_claim in cast(list[JsonValue], claims):
        claim = fields(raw_claim, ('list', 'rule', 'count'))
        require(claim['list'] == PERMISSION_LIST and isinstance(claim['rule'], str))
        control(claim['count'])
        require(claim['rule'] not in seen)
        seen.add(cast(str, claim['rule']))
    containers = cast(list[JsonValue], created)
    require(all(name in (PERMISSIONS, PERMISSION_LIST) for name in containers))
    require(len(set(containers)) == len(containers))
    # The installer creates the deny list whenever it creates the permissions object.
    require(PERMISSIONS not in containers or PERMISSION_LIST in containers)


def validate_committed(receipt: JsonValue) -> None:
    if receipt is None:
        return
    require(isinstance(receipt, dict))
    version = control(cast(JsonObject, receipt).get('schema_version'), version=True)
    record = fields(receipt, RECEIPT_FIELDS[version])
    require(record['state'] == 'committed')
    if version > 1:
        validate_permission_claims(record)
    for name in ('owned', 'created_groups'):
        require(isinstance(record[name], list))
        seen: set[QuotaKey] = set()
        for raw_claim in cast(list[JsonValue], record[name]):
            names = ('event', 'selector', 'handler', 'count') if name == 'owned' else ('event', 'selector', 'count')
            claim = fields(raw_claim, names)
            require(is_event_name(claim['event']) and isinstance(claim['selector'], dict))
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
    return {'schema_version':max(RECEIPT_FIELDS), 'state':'committed', 'owned':[], 'created_groups':[],
            'owned_permissions':[], 'created_permissions':[]}


def compatible_receipt(receipt: JsonObject) -> JsonObject:
    """Keep the version 1 form without permission state, so earlier installers can still read it."""
    if receipt['owned_permissions'] or receipt['created_permissions']:
        return receipt
    return dict({name: receipt[name] for name in RECEIPT_FIELDS[1]}, schema_version=1)


def receipt_version(receipt: JsonValue) -> int:
    return control(cast(JsonObject, receipt)['schema_version'], version=True) if receipt is not None else 1


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


def remove_permissions(settings: JsonObject, receipt: JsonObject) -> None:
    """Delete one occurrence per owned count, then created containers that are left empty."""
    quotas = {cast(str, claim['rule']):control(claim['count'])
              for claim in cast(list[JsonObject], receipt.get('owned_permissions', []))}
    created = cast(list[JsonValue], receipt.get('created_permissions', []))
    permissions = settings.get(PERMISSIONS)
    if not isinstance(permissions, dict):
        return
    if PERMISSION_LIST in permissions:
        retained: list[JsonValue] = []
        for rule in cast(list[JsonValue], permissions[PERMISSION_LIST]):
            if quotas.get(cast(str, rule), 0) > 0:
                quotas[cast(str, rule)] -= 1
            else:
                retained.append(rule)
        permissions[PERMISSION_LIST] = retained
    if PERMISSION_LIST in created and permissions.get(PERMISSION_LIST) == []:
        del permissions[PERMISSION_LIST]
    if PERMISSIONS in created and not permissions:
        del settings[PERMISSIONS]


def remove_owned(settings: JsonObject, receipt: JsonObject | None) -> None:
    if receipt is None:
        return
    remove_permissions(settings, receipt)
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


def regular_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def substitute_script(arguments: JsonValue, source_path: Path) -> list[JsonValue]:
    require(isinstance(arguments, list) and len(arguments) == 1, 'invalid-manifest')
    argument = cast(list[JsonValue], arguments)[0]
    match = SCRIPT_ARGUMENT.fullmatch(argument) if isinstance(argument, str) else None
    require(match is not None, 'invalid-manifest')
    script = source_path / cast(re.Match[str], match).group(1)
    require(regular_file(script), 'invalid-source')
    return [str(physical_script(script))]


def physical_script(script: Path) -> Path:
    """Register the readable physical file: an entrypoint finds its core beside its own path,
    and bash reads a script it cannot open as a failure on every call."""
    try:
        physical = script.resolve(strict=True)
    except (OSError, RuntimeError):
        raise Unavailable('invalid-source') from None
    require(regular_file(physical) and os.access(physical, os.R_OK), 'invalid-source')
    return physical


def validate_manifest_handler(value: JsonValue, event: str, source_path: Path) -> JsonObject:
    require(isinstance(value, dict) and set(value) == HANDLER_FIELDS, 'invalid-manifest')
    handler = cast(JsonObject, value)
    timeout = handler['timeout']
    require(handler['type'] == 'command' and handler['command'] == 'bash', 'invalid-manifest')
    require(isinstance(timeout, Number) and TIMEOUT_SECONDS.fullmatch(timeout.token) is not None,
            'invalid-manifest')
    require(event in FAILURE_MODES and handler['onFailure'] == FAILURE_MODES[event], 'invalid-manifest')
    handler['args'] = substitute_script(handler['args'], source_path)
    return handler


def validate_manifest_group(value: JsonValue, event: str, source_path: Path) -> JsonObject:
    require(isinstance(value, dict) and set(value) <= GROUP_FIELDS, 'invalid-manifest')
    group = cast(JsonObject, value)
    handlers = group.get('hooks')
    require(isinstance(handlers, list) and len(handlers) == 1, 'invalid-manifest')
    if 'matcher' in group or event in TOOL_GATING_EVENTS:
        require(isinstance(group.get('matcher'), str), 'invalid-manifest')
    validate_manifest_handler(cast(list[JsonValue], handlers)[0], event, source_path)
    return group


def load_manifest(source: str) -> Hooks:
    try:
        source_path = Path(source).resolve(strict=True)
        require(source_path.is_dir() and all((source_path / name).is_file() for name in SOURCE_DEPENDENCIES),
                'invalid-source')
        document = decode((source_path / 'harness/claude/hooks.json').read_bytes(), 'invalid-manifest')
    except (OSError, ValueError):
        raise Unavailable('invalid-source') from None
    require(isinstance(document, dict) and set(document) == {'hooks'}, 'invalid-manifest')
    hooks_value = cast(JsonObject, document)['hooks']
    require(isinstance(hooks_value, dict) and bool(hooks_value), 'invalid-manifest')
    hooks = cast(Hooks, hooks_value)
    for event, groups in hooks.items():
        require(is_event_name(event) and isinstance(groups, list) and len(groups) == 1, 'invalid-manifest')
        validate_manifest_group(groups[0], event, source_path)
    return hooks


def load_fragment(source: str) -> list[str]:
    try:
        data = (Path(source).resolve(strict=True) / PERMISSION_FRAGMENT).read_bytes()
    except (OSError, ValueError):
        raise Unavailable('invalid-source') from None
    document = decode(data, 'invalid-manifest')
    require(isinstance(document, dict) and set(document) == {PERMISSIONS}, 'invalid-manifest')
    permissions = cast(JsonObject, document)[PERMISSIONS]
    require(isinstance(permissions, dict) and set(permissions) == {PERMISSION_LIST}, 'invalid-manifest')
    rules = cast(JsonObject, permissions)[PERMISSION_LIST]
    require(isinstance(rules, list) and bool(rules), 'invalid-manifest')
    require(all(isinstance(rule, str) and PERMISSION_RULE.fullmatch(rule) is not None for rule in rules),
            'invalid-manifest')
    require(len(set(cast(list[str], rules))) == len(rules), 'invalid-manifest')
    return cast(list[str], rules)


def insert_permissions(settings: JsonObject, rules: list[str], receipt: JsonObject) -> None:
    """Append each fragment rule not already present; an identical user rule stays unowned."""
    created = cast(list[JsonValue], receipt['created_permissions'])
    if PERMISSIONS not in settings:
        settings[PERMISSIONS] = {}
        created.append(PERMISSIONS)
    permissions = cast(JsonObject, settings[PERMISSIONS])
    if PERMISSION_LIST not in permissions:
        permissions[PERMISSION_LIST] = []
        created.append(PERMISSION_LIST)
    present = cast(list[JsonValue], permissions[PERMISSION_LIST])
    owned = cast(list[JsonValue], receipt['owned_permissions'])
    for rule in rules:
        if rule not in present:
            present.append(rule)
            owned.append({'list':PERMISSION_LIST, 'rule':rule, 'count':1})


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
    if installation.operation == 'install':
        next_receipt = insert_manifest(result, load_manifest(installation.source))
        insert_permissions(result, load_fragment(installation.source), next_receipt)
    else:
        next_receipt = empty_receipt()
    next_receipt = compatible_receipt(next_receipt)
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
    # The envelope takes the highest version of the receipts it holds.
    version = max(receipt_version(update.previous.receipt), receipt_version(update.receipt))
    prepared: JsonObject = {'schema_version':version, 'state':'prepared', 'previous':update.previous.receipt,
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
