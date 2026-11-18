"""Journal-owned self-contained recovery packs; project Git mutations stay explicit.

Pack creation is a returned read-only command with explicit stdin/stdout destinations.
Verification writes Git objects only in a disposable, isolated temporary repository.
No project refs, objects, index or worktree are modified by this module.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

from finalization_support import Refusal, digest, now, require, safe_path


VERIFY_TIMEOUT_SECONDS = 30


def pack_digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as handle:
        while chunk := handle.read(1024 * 1024):
            result.update(chunk)
    return result.hexdigest()


def recovery_plan(journal_path: Path, repositories: list[dict]) -> list[dict]:
    result: list[dict] = []
    for repository in repositories:
        repo = repository['path']
        tips = list(dict.fromkeys(candidate['original_tip'] for candidate in repository['candidates']))
        pack = journal_path.parent / 'recovery' / (digest(repo.encode())[:24] + '.pack')
        result.append({'repository': repo, 'pack_path': str(pack), 'tips': tips,
                       'command': ['git', '-C', repo, 'pack-objects', '--stdout', '--revs'],
                       'stdin': ''.join(tip + '\n' for tip in tips), 'stdout_path': str(pack),
                       'restore_command': ['git', '-C', repo, 'index-pack', '--stdin', '--strict'],
                       'restore_stdin': str(pack),
                       'branch_recovery_commands': [candidate['recovery_command'] for candidate in repository['candidates']]})
    return result


def isolated_environment() -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    environment.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
                        'GIT_TERMINAL_PROMPT': '0', 'GIT_NO_REPLACE_OBJECTS': '1',
                        'GIT_NO_LAZY_FETCH': '1', 'GIT_OPTIONAL_LOCKS': '0', 'LC_ALL': 'C'})
    return environment


def isolated_run(arguments: list[str], *, stdin: object = subprocess.DEVNULL) -> subprocess.CompletedProcess[bytes]:
    # stdin is a binary file handle or subprocess.DEVNULL; no caller command executes here.
    try:
        return subprocess.run(arguments, stdin=stdin, capture_output=True,
                              timeout=VERIFY_TIMEOUT_SECONDS, env=isolated_environment())
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Refusal('recovery-verification-unavailable', f'Isolated recovery verification failed: {error}') from error


def verify_pack(action: dict, root: Path) -> dict:
    pack = safe_path(Path(action['pack_path']), root)
    require(pack.is_file(), 'recovery-pack-missing', 'Recovery artifact is missing')
    with pack.open('rb') as handle:
        require(handle.read(4) == b'PACK', 'recovery-pack-invalid', 'Recovery artifact is not a Git pack')
    initial_digest = pack_digest(pack)
    object_format = 'sha256' if len(action['tips'][0]) == 64 else 'sha1'
    with tempfile.TemporaryDirectory(prefix='finalization-object-evidence-') as temporary:
        isolated = Path(temporary) / 'objects.git'
        initialized = isolated_run(['git', 'init', '--bare', '--template=', '--object-format=' + object_format, str(isolated)])
        require(initialized.returncode == 0, 'recovery-verification-unavailable', initialized.stderr.decode(errors='replace'))
        require(not (isolated / 'objects/info/alternates').exists(), 'recovery-verification-unavailable', 'Isolated evidence cannot use alternate object stores')
        prefix = ['git', '--no-replace-objects', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', '--git-dir=' + str(isolated)]
        with pack.open('rb') as handle:
            indexed = isolated_run([*prefix, 'index-pack', '--stdin', '--strict'], stdin=handle)
        if indexed.returncode:
            diagnostic = indexed.stderr.decode(errors='replace')
            incomplete = any(fragment in diagnostic.casefold() for fragment in ('did not receive expected object', 'missing', 'not found'))
            raise Refusal('recovery-pack-incomplete' if incomplete else 'recovery-pack-invalid', diagnostic.strip())
        for tip in action['tips']:
            present = isolated_run([*prefix, 'cat-file', '-e', tip + '^{commit}'])
            require(present.returncode == 0, 'recovery-pack-incomplete', f'Recovery artifact does not contain original commit {tip}')
        closed = isolated_run([*prefix, 'fsck', '--full', '--strict', '--no-reflogs', '--no-dangling', *action['tips']])
        require(closed.returncode == 0, 'recovery-pack-incomplete', 'Original object closure is incomplete: ' + closed.stderr.decode(errors='replace').strip())
    require(pack_digest(pack) == initial_digest, 'recovery-pack-changed', 'Recovery artifact changed during isolated verification')
    return {'repository': action['repository'], 'pack_path': str(pack), 'sha256': initial_digest,
            'tips': action['tips'], 'closure_verified': True, 'verified_at': now(),
            'verification': 'index-pack --stdin --strict; fsck --full --strict; original commit checks in isolated object storage without alternates, replacements or lazy fetch',
            'restore_command': action['restore_command'], 'restore_stdin': str(pack),
            'branch_recovery_commands': action['branch_recovery_commands']}


def check_verified(journal: dict, root: Path, journal_path: Path) -> bool:
    plan = recovery_plan(journal_path, journal['repositories'])
    records = journal.get('recovery', [])
    if not records:
        return False
    require(isinstance(records, list) and len(records) == len(plan), 'recovery-record-invalid', 'Recovery repository inventory differs')
    for action in plan:
        matches = [record for record in records if record.get('repository') == action['repository']]
        require(len(matches) == 1, 'recovery-record-invalid', 'Recovery repository coverage is ambiguous')
        record = matches[0]
        require(record.get('pack_path') == action['pack_path'] and record.get('tips') == action['tips']
                and record.get('closure_verified') is True and record.get('restore_command') == action['restore_command']
                and record.get('restore_stdin') == action['pack_path'], 'recovery-record-invalid', 'Recovery coverage or restore command differs from the original plan')
        pack = safe_path(Path(action['pack_path']), root)
        require(pack.is_file(), 'recovery-pack-missing', 'Verified recovery artifact is missing; no deletion is authorized')
        require(pack_digest(pack) == record.get('sha256'), 'recovery-pack-changed', 'Verified recovery artifact changed; preserve it for diagnosis')
    return True


def prepare_recovery(journal: dict, root: Path, journal_path: Path) -> bool:
    journal['recovery_actions'] = recovery_plan(journal_path, journal['repositories'])
    if check_verified(journal, root, journal_path):
        journal['outcomes']['recovery'] = 'verified'
        return True
    if not all(safe_path(Path(action['pack_path']), root).is_file() for action in journal['recovery_actions']):
        journal['outcomes']['recovery'] = 'required'
        return False
    verified = [verify_pack(action, root) for action in journal['recovery_actions']]
    journal['recovery'] = verified
    journal['outcomes']['recovery'] = 'verified'
    return True
