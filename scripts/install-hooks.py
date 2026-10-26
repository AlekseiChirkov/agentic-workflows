#!/usr/bin/env python3
"""Own exact user hook occurrences and recover interrupted settings replacements.

Called by install-hooks.sh. Settings numbers retain their original JSON tokens;
ownership control numbers are independently validated before they affect quotas.
"""

import copy
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


EVENTS = ('Stop', 'SubagentStop')
MAX_COUNT = 9007199254740991
if hasattr(sys, 'set_int_max_str_digits'):
    sys.set_int_max_str_digits(0)


class Unavailable(Exception):
    """A safe reason code, never settings or exception text."""


class Number:
    """A JSON numeric lexeme, with exact mathematical comparison."""

    def __init__(self, token):
        self.token = token

    def key(self):
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


def pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def reject_constant(_token):
    raise ValueError('non-JSON number')


def decode(data, reason):
    try:
        return json.loads(data, parse_int=Number, parse_float=Number,
                          parse_constant=reject_constant, object_pairs_hook=pairs_unique)
    except (ValueError, UnicodeError, RecursionError):
        raise Unavailable(reason) from None


def encode(value):
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


def key(value):
    if isinstance(value, Number):
        return ('number', value.key())
    if type(value) is int:
        return ('number', Number(str(value)).key())
    if isinstance(value, dict):
        return ('object', tuple((name, key(item)) for name, item in sorted(value.items())))
    if isinstance(value, list):
        return ('array', tuple(key(item) for item in value))
    return (type(value).__name__, value)


def equal(left, right):
    return key(left) == key(right)


def require(condition, reason='invalid-ownership'):
    if not condition:
        raise Unavailable(reason)


def control(value, version=False):
    token = value.token if isinstance(value, Number) else str(value) if type(value) is int else ''
    if version:
        require(token == '1')
        return 1
    require(bool(re.fullmatch(r'[1-9][0-9]*', token)) and len(token) <= len(str(MAX_COUNT)))
    parsed = int(token)
    require(parsed <= MAX_COUNT)
    return parsed


def fields(value, names):
    require(isinstance(value, dict) and set(value) == set(names))


def selector(group):
    return {name: value for name, value in group.items() if name != 'hooks'}


def validate_settings(settings):
    require(isinstance(settings, dict), 'invalid-settings')
    if 'hooks' not in settings:
        return
    require(isinstance(settings['hooks'], dict), 'invalid-settings')
    for groups in settings['hooks'].values():
        require(isinstance(groups, list), 'invalid-settings')
        for group in groups:
            require(isinstance(group, dict) and isinstance(group.get('hooks'), list), 'invalid-settings')
            require(all(isinstance(handler, dict) for handler in group['hooks']), 'invalid-settings')


def validate_committed(receipt):
    if receipt is None:
        return
    fields(receipt, ('schema_version', 'state', 'owned', 'created_groups'))
    control(receipt['schema_version'], version=True)
    require(receipt['state'] == 'committed')
    for name in ('owned', 'created_groups'):
        require(isinstance(receipt[name], list))
        seen = set()
        for claim in receipt[name]:
            names = ('event', 'selector', 'handler', 'count') if name == 'owned' else ('event', 'selector', 'count')
            fields(claim, names)
            require(claim['event'] in EVENTS and isinstance(claim['selector'], dict))
            require('hooks' not in claim['selector'])
            if name == 'owned':
                require(isinstance(claim['handler'], dict))
            control(claim['count'])
            identity = (claim['event'], key(claim['selector']))
            if name == 'owned':
                identity += (key(claim['handler']),)
            require(identity not in seen)
            seen.add(identity)


def validate_image(image):
    fields(image, ('present', 'sha256'))
    require(type(image['present']) is bool)
    if image['present']:
        require(isinstance(image['sha256'], str) and
                re.fullmatch(r'[0-9a-f]{64}', image['sha256']) is not None)
    else:
        require(image['sha256'] is None)


def validate_receipt(receipt):
    if receipt is None:
        return
    require(isinstance(receipt, dict))
    if receipt.get('state') != 'prepared':
        validate_committed(receipt)
        return
    fields(receipt, ('schema_version', 'state', 'previous', 'next', 'before', 'after'))
    control(receipt['schema_version'], version=True)
    validate_committed(receipt['previous'])
    validate_committed(receipt['next'])
    validate_image(receipt['before'])
    validate_image(receipt['after'])


def read_bytes(path):
    require(not path.is_symlink(), 'unsafe-settings-path')
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def image(data):
    return {'present':data is not None,
            'sha256':hashlib.sha256(data).hexdigest() if data is not None else None}


def stage(path, data, mode=0o600):
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


def replace_receipt(path, value):
    if value is None:
        path.unlink(missing_ok=True)
        return
    temporary = stage(path, (encode(value) + '\n').encode('ascii'))
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def empty_receipt():
    return {'schema_version':1, 'state':'committed', 'owned':[], 'created_groups':[]}


def remove_owned(settings, receipt):
    if receipt is None:
        return
    hooks = settings.get('hooks', {})
    quotas = {(claim['event'], key(claim['selector']), key(claim['handler'])):control(claim['count'])
              for claim in receipt['owned']}
    group_quotas = {(claim['event'], key(claim['selector'])):control(claim['count'])
                    for claim in receipt['created_groups']}
    for event, groups in hooks.items():
        retained = []
        for group in groups:
            group_key = (event, key(selector(group)))
            handlers = []
            removed = False
            for handler in group['hooks']:
                identity = group_key + (key(handler),)
                if quotas.get(identity, 0) > 0:
                    quotas[identity] -= 1
                    removed = True
                else:
                    handlers.append(handler)
            group['hooks'] = handlers
            if removed and not handlers and group_quotas.get(group_key, 0) > 0:
                group_quotas[group_key] -= 1
            else:
                retained.append(group)
        hooks[event] = retained


def load_manifest(source):
    try:
        source = Path(source).resolve(strict=True)
        require(source.is_dir() and (source / 'hooks/log-step-hook.sh').is_file() and
                (source / 'scripts/log-step.sh').is_file(), 'invalid-source')
        document = decode((source / 'harness/claude/hooks.json').read_bytes(), 'invalid-manifest')
    except (OSError, ValueError):
        raise Unavailable('invalid-source') from None
    require(isinstance(document, dict) and set(document) == {'hooks'}, 'invalid-manifest')
    hooks = document['hooks']
    require(isinstance(hooks, dict) and set(hooks) == set(EVENTS), 'invalid-manifest')
    expected = {'type':'command', 'command':'bash', 'args':['@ORCHESTRAIL_HOME@/hooks/log-step-hook.sh'],
                'timeout':10, 'onFailure':'continue'}
    for groups in hooks.values():
        require(isinstance(groups, list) and len(groups) == 1, 'invalid-manifest')
        group = groups[0]
        require(isinstance(group, dict) and isinstance(group.get('hooks'), list) and
                len(group['hooks']) == 1 and equal(group['hooks'][0], expected), 'invalid-manifest')
        group['hooks'][0]['args'] = [str(source / 'hooks/log-step-hook.sh')]
    return hooks


def insert_manifest(settings, manifest):
    receipt = empty_receipt()
    hooks = settings.setdefault('hooks', {})
    for event, manifest_groups in manifest.items():
        groups = hooks.setdefault(event, [])
        for desired in manifest_groups:
            desired_selector = selector(desired)
            matching = [group for group in groups if equal(selector(group), desired_selector)]
            for handler in desired['hooks']:
                if any(equal(existing, handler) for group in matching for existing in group['hooks']):
                    continue
                if not matching:
                    group = copy.deepcopy(desired_selector)
                    group['hooks'] = []
                    groups.append(group)
                    matching.append(group)
                    receipt['created_groups'].append({'event':event, 'selector':copy.deepcopy(desired_selector), 'count':1})
                matching[0]['hooks'].append(copy.deepcopy(handler))
                receipt['owned'].append({'event':event, 'selector':copy.deepcopy(desired_selector),
                                         'handler':copy.deepcopy(handler), 'count':1})
    return receipt


def acquire_lock(path):
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


def apply(operation, source, settings_path, receipt_path):
    settings_data = read_bytes(settings_path)
    settings = decode(settings_data, 'invalid-settings') if settings_data is not None else {}
    validate_settings(settings)
    receipt_data = read_bytes(receipt_path)
    receipt = decode(receipt_data, 'invalid-ownership') if receipt_data is not None else None
    if receipt_data is not None:
        require(isinstance(receipt, dict))
    validate_receipt(receipt)

    if receipt is not None and receipt['state'] == 'prepared':
        current_image = image(settings_data)
        if equal(current_image, receipt['before']):
            recovered = receipt['previous']
        elif equal(current_image, receipt['after']):
            recovered = receipt['next']
        else:
            raise Unavailable('settings-changed-during-transaction')
        replace_receipt(receipt_path, recovered)
        receipt = recovered
        # Recovery never rewrites settings; refresh them before the new operation.
        settings_data = read_bytes(settings_path)
        settings = decode(settings_data, 'invalid-settings') if settings_data is not None else {}
        validate_settings(settings)

    result = copy.deepcopy(settings)
    remove_owned(result, receipt)
    next_receipt = insert_manifest(result, load_manifest(source)) if operation == 'install' else empty_receipt()
    validate_settings(result)
    validate_committed(next_receipt)
    if equal(result, settings) and (equal(next_receipt, receipt) or
                                   (receipt is None and operation == 'uninstall')):
        return

    # Keep exact bytes if only ownership changes or numbers are spelled differently.
    next_data = settings_data if equal(result, settings) else (encode(result) + '\n').encode('ascii')
    settings_temporary = None
    ownership_temporary = None
    try:
        if next_data is not None:
            mode = stat.S_IMODE(settings_path.stat().st_mode) if settings_data is not None else 0o600
            settings_temporary = stage(settings_path, next_data, mode)
        ownership_temporary = stage(receipt_path, (encode(next_receipt) + '\n').encode('ascii'))
        prepared = {'schema_version':1, 'state':'prepared', 'previous':receipt, 'next':next_receipt,
                    'before':image(settings_data), 'after':image(next_data)}
        validate_receipt(prepared)
        replace_receipt(receipt_path, prepared)
        require(equal(image(read_bytes(settings_path)), prepared['before']), 'settings-changed-during-transaction')
        if settings_temporary is not None:
            os.replace(settings_temporary, settings_path)
        else:
            settings_path.unlink(missing_ok=True)
        os.replace(ownership_temporary, receipt_path)
    finally:
        for temporary in (settings_temporary, ownership_temporary):
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def main():
    operation, source = sys.argv[1:]
    lock = None
    try:
        home = Path(os.environ['HOME'])
        config = Path(os.environ.get('XDG_CONFIG_HOME') or home / '.config').absolute()
        settings = home.absolute() / '.claude/settings.json'
        receipt = config / 'orchestrail/hooks-installed.json'
        lock = acquire_lock(config / 'orchestrail/hooks-installed.lock')
        apply(operation, source, settings, receipt)
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
