"""Strict path, Markdown, JSON and durable journal primitives for finalization."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import tempfile
from typing import Iterator


class Refusal(Exception):
    """A named fail-closed result suitable for the CLI's JSON failure list."""
    def __init__(self, check: str, reason: str) -> None:
        super().__init__(reason)
        self.check = check
        self.reason = reason


def require(condition: object, check: str, reason: str) -> None:
    if not condition:
        raise Refusal(check, reason)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(document: dict) -> bytes:
    return (json.dumps(document, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dated(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.tzinfo is not None and parsed <= datetime.now(timezone.utc)
    except ValueError:
        return False


def pairs_unique(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        require(key not in result, 'invalid-json', f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise Refusal('invalid-json', f'Invalid JSON constant: {value}')


def read_json(path: Path) -> dict:
    safe_path(path)
    try:
        require(path.stat().st_size <= 4 * 1024 * 1024, 'invalid-json', 'JSON input exceeds 4 MiB')
        result = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs_unique,
                            parse_constant=reject_constant)
        require(isinstance(result, dict), 'invalid-json', 'Expected a JSON object')
        return result
    except (OSError, ValueError) as error:
        raise Refusal('invalid-json', f'Cannot read {path}: {error}') from error


def safe_path(path: Path, root: Path | None = None) -> Path:
    """Reject symlinks, traversal spellings and special files before following paths."""
    require('..' not in path.parts, 'unsafe-path', f'Parent traversal is not permitted: {path}')
    absolute = Path(os.path.abspath(path))
    if root is not None:
        require(absolute.is_relative_to(root), 'unsafe-path', f'Path escapes project: {path}')
    for part in (absolute, *absolute.parents):
        try:
            mode = part.lstat().st_mode
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(mode), 'unsafe-path', f'Symlink is not permitted: {part}')
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'unsafe-path', f'Special file is not permitted: {part}')
    return absolute


def text(path: Path) -> str:
    safe_path(path)
    try:
        return path.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        raise Refusal('input-unreadable', f'Cannot read {path}: {error}') from error


def visible_lines(value: str) -> list[str]:
    """Fenced examples are never executable status or audit evidence."""
    result: list[str] = []
    fence: tuple[str, int] | None = None
    for line in value.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = (marker[0], len(marker))
            elif marker[0] == fence[0] and len(marker) >= fence[1]:
                fence = None
            continue
        if fence is None:
            result.append(line)
    return result


def section(value: str, heading: str) -> str:
    lines = visible_lines(value)
    matches = [i for i, line in enumerate(lines) if line.strip() == heading]
    require(len(matches) <= 1, 'state-ambiguous', f'Duplicate section: {heading}')
    if not matches:
        return ''
    level = len(heading) - len(heading.lstrip('#'))
    result: list[str] = []
    for line in lines[matches[0] + 1:]:
        if re.match(r'^#{1,' + str(level) + r'}\s', line):
            break
        result.append(line)
    return '\n'.join(result).strip()


def field(value: str, key: str, *, top: bool = False) -> str | None:
    lines = visible_lines(value)
    if top:
        lines = lines[:next((i for i, line in enumerate(lines) if line.startswith('## ')), len(lines))]
    matches = [match.group(1).strip() for line in lines
               if (match := re.match(r'^\s*' + re.escape(key) + r':\s*(.*?)\s*$', line))]
    require(len(matches) <= 1, 'state-ambiguous', f'Duplicate field: {key}')
    return matches[0] if matches else None


def manifest(directory: Path) -> dict[str, str]:
    safe_path(directory)
    require(directory.is_dir(), 'input-unreadable', f'Not a directory: {directory}')
    result: dict[str, str] = {}
    for path in sorted(directory.rglob('*')):
        safe_path(path, directory)
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = digest(path.read_bytes())
    return result


def current_state_lines(value: str) -> tuple[list[str], int | None, int | None, int]:
    """Locate only active top-level pointers/phase fields, preserving fenced history."""
    lines = value.splitlines(keepends=True)
    pointer: int | None = None
    marker: int | None = None
    phase_start = -1
    phase_end = len(lines)
    top = True
    in_phase = False
    fence: tuple[str, int] | None = None
    for index, line in enumerate(lines):
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            run = match.group(1)
            if fence is None:
                fence = (run[0], len(run))
            elif run[0] == fence[0] and len(run) >= fence[1]:
                fence = None
            continue
        if fence:
            continue
        if line.startswith('## '):
            top = False
            if in_phase:
                phase_end = index
            in_phase = line.strip() == '## Phases'
            if in_phase:
                require(phase_start == -1, 'state-ambiguous', 'Duplicate active Phases section')
                phase_start = index
        if top and line.startswith('spec_path:'):
            require(pointer is None, 'state-ambiguous', 'Duplicate active spec pointer')
            pointer = index
        if in_phase and line.startswith('- finalization:'):
            require(marker is None and line.strip() in {'- finalization: not-started', '- finalization: in-progress', '- finalization: complete'},
                    'protected-content-changed', 'Invalid active finalization phase marker')
            marker = index
    require(phase_start >= 0, 'validation-evidence-missing', 'Missing active Phases section')
    return lines, pointer, marker, phase_end


def normalized_state(value: str) -> bytes:
    """Only the active spec pointer and active additive phase marker are mutable."""
    lines, pointer, marker, _ = current_state_lines(value)
    if pointer is not None:
        lines[pointer] = 'spec_path: <current-location>\n'
    if marker is not None:
        lines[marker] = ''
    return ''.join(lines).encode()


def edit_current_state(value: str, *, spec: str | None = None, phase: str | None = None) -> bytes:
    lines, pointer, marker, end = current_state_lines(value)
    if spec is not None:
        require(pointer is not None, 'spec-not-recorded', 'Missing active spec pointer')
        lines[pointer] = 'spec_path: ' + spec + '\n'
    if phase is not None:
        require(phase in {'not-started', 'in-progress', 'complete'}, 'phase-invalid', 'Unknown finalization marker')
        if marker is not None:
            lines[marker] = '- finalization: ' + phase + '\n'
        else:
            lines.insert(end, '- finalization: ' + phase + '\n')
    return ''.join(lines).encode()


def fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def fault(name: str, root: Path) -> None:
    # A test fault can only interrupt an operation; it cannot grant permissions.
    if (os.environ.get('FINALIZATION_TEST_ROOT') == str(root)
            and root.is_relative_to(Path(tempfile.gettempdir()))
            and os.environ.get('FINALIZATION_TEST_FAULT') == name):
        os.kill(os.getpid(), signal.SIGKILL)


def atomic_write(path: Path, data: bytes, root: Path, *, journal: bool = False) -> None:
    require(not journal or len(data) <= 1024 * 1024, 'journal-too-large',
            'Journal exceeds the shared 1 MiB helper/hook limit; previous revision is preserved')
    safe_path(path, root)
    descriptor, temporary_name = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if journal:
            fault('before-journal-replace', root)
        os.replace(temporary, path)
        fsync_dir(path.parent)
        if journal:
            fault('after-journal-replace', root)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def locked(path: Path, root: Path) -> Iterator[None]:
    safe_path(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise Refusal('journal-locked', f'Another writer holds {path}') from error
        yield
    finally:
        os.close(descriptor)


def expect_revision(path: Path, expected: str | None) -> str:
    actual = digest(path.read_bytes()) if path.exists() else 'absent'
    require(expected == actual, 'revision-conflict', f'Expected journal revision {expected}; actual {actual}')
    return actual
