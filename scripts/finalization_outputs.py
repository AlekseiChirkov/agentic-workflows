"""Immutable exact-byte outputs keep the authoritative journal bounded."""
from __future__ import annotations

import os
from pathlib import Path
import re

from finalization_support import digest, fsync_dir, require, safe_path


def normalized(row: dict, directory: Path, root: Path) -> tuple[dict, list[tuple[Path, bytes]]]:
    result = dict(row)
    artifacts: list[tuple[Path, bytes]] = []
    for key in ('stdout', 'stderr'):
        data = row[key].encode('utf-8')
        if len(data) > 64 * 1024:
            sha = digest(data)
            path = safe_path(directory / 'outputs' / (sha + '.utf8'), root)
            result[key] = {'path': str(path), 'sha256': sha, 'bytes': len(data), 'encoding': 'utf-8'}
            artifacts.append((path, data))
    return result, artifacts


def persist(artifacts: list[tuple[Path, bytes]], root: Path) -> None:
    for path, data in artifacts:
        safe_path(path, root)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            require(path.is_file() and path.read_bytes() == data, 'output-artifact-changed', 'Existing immutable output differs')
            continue
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        fsync_dir(path.parent)


def integrity(root: Path, journal: dict) -> None:
    directory = Path(journal['snapshot_path']).parent / 'outputs'
    for row in journal.get('command_attempts', []):
        for key in ('stdout', 'stderr'):
            value = row.get(key)
            if isinstance(value, str):
                continue
            require(isinstance(value, dict) and set(value) == {'path', 'sha256', 'bytes', 'encoding'}
                    and isinstance(value['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', value['sha256'])
                    and type(value['bytes']) is int and value['bytes'] > 64 * 1024 and value['encoding'] == 'utf-8',
                    'output-artifact-changed', 'Invalid immutable output reference')
            path = safe_path(Path(value['path']), root)
            require(path == directory / (value['sha256'] + '.utf8') and path.is_file()
                    and path.stat().st_size == value['bytes'] and digest(path.read_bytes()) == value['sha256'],
                    'output-artifact-changed', 'Immutable output is missing or changed')
