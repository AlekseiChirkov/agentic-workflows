"""Immutable command observations; recording is independent of Git availability."""
from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime

from finalization_support import dated, digest, encoded, require
from finalization_outputs import normalized, persist

CHECKPOINTS = {'pending', 'prepared', 'applied', 'verified', 'blocked', 'preserved'}
CHECK_OPERATIONS = {'validation', 'integration', 'recovery', 'verification', 'knowledge', 'audit', 'deployment', 'archival'}


def receipt_is_newer(journal: dict | None, kind: str, row: dict) -> bool:
    if not dated(row.get('observed_at')):
        return False
    observed = datetime.fromisoformat(row['observed_at'].replace('Z', '+00:00'))
    return all(observed > datetime.fromisoformat(attempt['observed_at'].replace('Z', '+00:00'))
               for attempt in (journal or {}).get('command_attempts', []) if attempt['operation_id'] == kind)


def operations(journal: dict) -> dict:
    """Add operation entries without discarding earlier attempts or observations."""
    result = journal.setdefault('operations', {})
    require(isinstance(result, dict), 'journal-invalid', 'Operation checkpoints must be an object')
    for action in journal['actions']:
        result.setdefault(action['id'], {'checkpoint': 'prepared', 'attempts': []})
    for operation in result.values():
        require(isinstance(operation, dict) and operation.get('checkpoint') in CHECKPOINTS
                and isinstance(operation.get('attempts'), list), 'journal-invalid', 'Invalid operation checkpoint')
    return result


def observe_operations(journal: dict, receipts: list[dict]) -> None:
    current = operations(journal)
    for row in receipts:
        operation = current[row['id']]
        if row['satisfied']:
            operation['checkpoint'] = 'verified'
        elif operation['checkpoint'] == 'verified':
            operation['checkpoint'] = 'blocked'
        operation['observation'] = row


def record_attempt(journal: dict, row: object, path: Path, root: Path) -> None:
    """Accept exact execution observations, never caller-asserted postconditions."""
    require(journal.get('authorization') == {'invocation': 'phase-finalize',
            'task_path': journal['task_original'], 'cleanup': True},
            'authorization-required', 'Attempt recording requires the task-bound invocation authorization')
    require(journal.get('plan_digest') == digest(encoded({key: journal[key] for key in ('repositories', 'actions')})),
            'journal-invalid', 'Attempt journal plan digest differs')
    expected = {repo['path']: repo['integration']['tip'] for repo in journal['repositories']}
    require(all(isinstance(repo.get('remote_identity'), dict) for repo in journal['repositories']),
            'journal-invalid', 'Journal lacks original transport identity; automatic migration is unavailable')
    fields = {'attempt_id', 'operation_id', 'checkpoint', 'repository', 'argv', 'exit_code',
              'stdout', 'stderr', 'observed_at', 'provenance', 'source_tips'}
    require(isinstance(row, dict) and set(row) == fields, 'attempt-invalid', 'Command attempt needs the exact documented fields')
    require(isinstance(row['attempt_id'], str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', row['attempt_id'])
            and isinstance(row['operation_id'], str) and isinstance(row['repository'], str)
            and isinstance(row['argv'], list) and row['argv'] and all(isinstance(word, str) and '\0' not in word for word in row['argv'])
            and type(row['exit_code']) is int and -2147483648 <= row['exit_code'] <= 2147483647
            and isinstance(row['stdout'], str) and isinstance(row['stderr'], str)
            and dated(row['observed_at']) and isinstance(row['provenance'], str) and len(row['provenance'].strip()) >= 8
            and row['source_tips'] == expected, 'attempt-invalid', 'Attempt lacks exact command/result and dated source provenance')
    require(row['checkpoint'] in {'applied', 'blocked', 'preserved'}
            and (row['checkpoint'] != 'applied' or row['exit_code'] == 0),
            'attempt-invalid', 'Execution can record applied, blocked or preserved; only fresh postconditions verify an operation')
    action = next((item for item in journal['actions'] if item['id'] == row['operation_id']), None)
    require((action is not None and row['repository'] == action['repository'] and row['argv'] == action['command'])
            or (action is None and row['operation_id'] in CHECK_OPERATIONS
                and row['repository'] in {str(root), *expected}),
            'attempt-invalid', 'Git action must match the exact bound plan; checks need a supported operation id')
    row, artifacts = normalized(row, path.parent, root)
    attempts = journal.setdefault('command_attempts', [])
    require(isinstance(attempts, list), 'journal-invalid', 'Command attempts must be an array')
    matches = [prior for prior in attempts if prior.get('attempt_id') == row['attempt_id']]
    require(not matches or len(matches) == 1 and matches[0] == row,
            'attempt-conflict', 'Attempt identity was already used for different immutable evidence')
    if matches:
        return
    attempts.append(dict(row))
    current = operations(journal)
    operation = current.setdefault(row['operation_id'], {'checkpoint': 'pending', 'attempts': []})
    operation['attempts'].append(row['attempt_id'])
    operation['checkpoint'] = row['checkpoint']
    # An execution observation invalidates completion until fresh reconciliation.
    journal['complete'] = False
    if row['operation_id'] in {'verification', 'knowledge', 'audit', 'deployment'}:
        journal.setdefault('attestations', {}).pop(row['operation_id'], None)
        journal['outcomes'][row['operation_id']] = 'unverified'
    require(len(encoded(journal)) <= 1024 * 1024, 'journal-too-large', 'Journal exceeds the shared 1 MiB limit; previous revision is preserved')
    persist(artifacts, root)
