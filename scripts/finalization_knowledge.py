"""Exact, predeclared current-record reconciliation without broader Git authority."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
import re
from typing import Callable

from finalization_support import dated, digest, require, safe_path

CURRENT = {'.ai/memory/architecture.md', '.ai/memory/state.md', '.ai/project_state.md',
           '.ai/principles/domain.md', '.ai/context/runbook.md', '.ai/context/environment.md',
           '.ai/context/integrations.md', '.ai/specs/README.md'}
KINDS = {'current-record': CURRENT, 'progress': {'.ai/memory/progress.md'},
         'adr-index': {'.ai/adr/index.md'}, 'guidance': {'README.md', 'CLAUDE.md', 'AGENTS.md'},
         'roadmap': {'.ai/roadmap.md', '.ai/memory/roadmap.md'}, 'delivery-notes': set()}


def allowed(relative: str, kind: str) -> bool:
    return relative in KINDS[kind] or kind == 'delivery-notes' and bool(
        re.fullmatch(r'\.ai/context/[A-Za-z0-9][A-Za-z0-9._-]*-delivery\.md', relative))


def capture(root: Path, directory: Path, inventory: object, repositories: list[dict]) -> list[dict]:
    require(isinstance(inventory, list) and len(inventory) <= 128, 'knowledge-change-invalid', 'Knowledge inventory must be a bounded typed array')
    result: list[dict] = []
    seen: set[str] = set()
    for row in inventory:
        require(isinstance(row, dict) and set(row) == {'path', 'kind'} and isinstance(row['path'], str)
                and row['kind'] in KINDS, 'knowledge-change-invalid', 'Knowledge inventory needs path and established record kind')
        relative = row['path']
        require(not Path(relative).is_absolute() and relative not in seen, 'knowledge-change-invalid', 'Knowledge paths must be unique and project relative')
        seen.add(relative)
        path = safe_path(root / relative, root)
        scopes = [root, *(Path(repo['path']) for repo in repositories)]
        require(any(path.is_relative_to(scope) and allowed(path.relative_to(scope).as_posix(), row['kind']) for scope in scopes)
                and path.is_file(), 'knowledge-change-invalid', 'Only existing established current Markdown records may be inventoried')
        data = path.read_bytes()
        data.decode('utf-8')
        snapshot = safe_path(directory / 'knowledge' / (digest(relative.encode()) + '.md'), root)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        if snapshot.exists():
            require(snapshot.read_bytes() == data, 'snapshot-conflict', 'Original knowledge snapshot differs')
        else:
            from finalization_support import atomic_write
            atomic_write(snapshot, data, root)
        result.append({**row, 'before_sha256': digest(data), 'snapshot_path': str(snapshot)})
    return result


def integrity(root: Path, journal: dict, *, current: bool = True, indexes: bool = True) -> None:
    changes = {row['path']: row['after_sha256'] for row in journal.get('knowledge_changes', [])}
    for row in journal.get('knowledge_files', []):
        path = safe_path(Path(row['snapshot_path']), root)
        expected = Path(journal['snapshot_path']).parent / 'knowledge' / (digest(row['path'].encode()) + '.md')
        require(path == expected and path.is_file() and digest(path.read_bytes()) == row['before_sha256'],
                'snapshot-conflict', 'Original knowledge snapshot changed')
        if current:
            path = safe_path(root / row['path'], root)
            bound = changes.get(row['path'], row['before_sha256'])
            permitted = {bound}
            for plan in journal.get('archive_intent', {}).get('current_links', []):
                if plan['path'] == row['path'] and plan['before_sha256'] == bound:
                    require(digest(plan['after_text'].encode()) == plan['after_sha256'],
                            'journal-invalid', 'Current-link operation digest differs')
                    permitted.add(plan['after_sha256'])
            require(path.is_file() and digest(path.read_bytes()) in permitted,
                    'knowledge-content-changed', 'Inventoried current record differs from its independently accepted binding')
    for row in journal.get('knowledge_indexes', {}).values() if indexes else []:
        index = safe_path(Path(row['path']))
        require((digest(index.read_bytes()) if index.is_file() else 'absent') == row['sha256'],
                'knowledge-index-changed', 'The index changed after the clean reconciliation baseline; no staging is authorized')


def index_observations(journal: dict, git: Callable[..., str]) -> dict:
    """Read canonical index entries without refreshing the index or writing trees."""
    result: dict = {}
    for repo in journal['repositories'] if journal.get('knowledge_files') else []:
        directory = Path(repo['path'])
        path = safe_path(Path(git(directory, 'rev-parse', '--path-format=absolute', '--git-path', 'index')))
        head = git(directory, 'rev-parse', '--verify', 'HEAD^{commit}')
        staged = git(directory, 'ls-files', '--stage', '-z')
        tree = git(directory, 'ls-tree', '-r', '--full-tree', '-z', head)
        entries = []
        for item in staged.split('\0'):
            if not item:
                continue
            metadata, name = item.split('\t', 1)
            mode, sha, stage = metadata.split(' ')
            require(stage == '0', 'knowledge-index-changed', 'Unmerged index entries cannot establish a clean baseline')
            entries.append((name, mode, sha))
        committed = []
        for item in tree.split('\0'):
            if item:
                metadata, name = item.split('\t', 1)
                mode, _, sha = metadata.split(' ')
                committed.append((name, mode, sha))
        require(sorted(entries) == sorted(committed), 'knowledge-index-changed',
                'Staged index content differs from HEAD; no staging or index repair is authorized')
        result[repo['path']] = {'path': str(path), 'sha256': digest(path.read_bytes()) if path.is_file() else 'absent',
                                'head': head, 'entries_sha256': digest(repr(sorted(entries)).encode())}
    return result


def reconcile_indexes(journal: dict, observations: dict, repositories: list[dict], git: Callable[..., str]) -> None:
    previous = journal.get('knowledge_indexes', {})
    if not previous:
        return
    require(set(previous) == set(observations), 'knowledge-index-changed', 'Knowledge index repository inventory differs')
    for repo in repositories:
        current, old = observations[repo['path']], previous[repo['path']]
        require(isinstance(old.get('head'), str) and isinstance(old.get('entries_sha256'), str),
                'knowledge-index-changed', 'Index generation binding is missing; automatic migration is unavailable')
        require(repo['current_branch'] == repo['integration']['branch'] and current['head'] == repo['integration']['tip'],
                'knowledge-index-changed', 'Only a freshly verified integration checkout may refresh the index baseline')
        require(git(Path(repo['path']), 'merge-base', old['head'], current['head'], codes=(0, 1)) == old['head'],
                'knowledge-index-changed', 'Integration source rewound or diverged from the recorded index generation')
        if current['head'] == old['head']:
            require(current['entries_sha256'] == old['entries_sha256'], 'knowledge-index-changed',
                    'Same-generation index content changed')
    if previous != observations:
        journal.setdefault('knowledge_index_history', []).append(deepcopy(previous))
        journal['knowledge_indexes'] = observations


def capture_indexes(journal: dict, git: Callable[..., str]) -> None:
    if not journal.get('knowledge_files') or journal.get('knowledge_indexes') or journal['outcomes']['checkout'] != 'complete':
        return
    indexes = index_observations(journal, git)
    require(all(indexes[repo['path']]['head'] == repo['integration']['tip']
                and repo['current_branch'] == repo['integration']['branch'] for repo in journal['repositories']),
            'knowledge-index-changed', 'The clean baseline must bind the verified integration checkout')
    journal['knowledge_indexes'] = indexes
    journal['knowledge_indexes_original'] = deepcopy(indexes)


def changes(journal: dict, evidence: dict, root: Path, task: Path) -> None:
    rows = [row for row in evidence.get('attestations', []) if isinstance(row, dict)
            and row.get('kind') == 'knowledge' and 'file_changes' in row]
    if not rows:
        return
    require(len(rows) == 1, 'knowledge-change-invalid', 'Knowledge changes need one independent attestation')
    row = rows[0]
    source = {repo['path']: repo['integration']['tip'] for repo in journal['repositories']}
    hashes = {digest((task / 'state.md').read_bytes()), digest((Path(journal['snapshot_path']) / 'task/state.md').read_bytes())}
    require(row.get('source_tips') == source and row.get('task_path') in {str(task), journal['task_original']}
            and row.get('state_sha256') in hashes and row.get('result') == 'pass' and dated(row.get('observed_at'))
            and isinstance(row.get('provenance'), str) and len(row['provenance'].strip()) >= 8,
            'knowledge-change-invalid', 'Knowledge changes lack independent dated task/state/source provenance')
    require(journal.get('knowledge_indexes') and journal['outcomes']['checkout'] == 'complete',
            'knowledge-change-invalid', 'Record a clean integration checkout/index baseline before knowledge edits')
    integrity(root, journal, current=False, indexes=False)
    inventory = {item['path']: item for item in journal.get('knowledge_files', [])}
    declared = row['file_changes']
    require(isinstance(declared, list) and len(declared) <= 128, 'knowledge-change-invalid', 'Knowledge changes must be a bounded array')
    seen: set[str] = set()
    for change in declared:
        require(isinstance(change, dict) and set(change) == {'path', 'before_sha256', 'after_sha256'}
                and isinstance(change['path'], str) and change['path'] in inventory and change['path'] not in seen,
                'knowledge-change-invalid', 'Knowledge delta is not in the original current-record inventory')
        seen.add(change['path'])
        original = inventory[change['path']]
        path = safe_path(root / change['path'], root)
        require(change['before_sha256'] == original['before_sha256'] and path.is_file()
                and digest(path.read_bytes()) == change['after_sha256'],
                'knowledge-change-invalid', 'Knowledge delta does not match immutable before and exact current after bytes')
        before = Path(original['snapshot_path']).read_bytes()
        after = path.read_bytes()
        after.decode('utf-8')
        if original['kind'] == 'progress':
            require(after.startswith(before), 'knowledge-change-invalid', 'Progress history is append-only')
        if original['kind'] == 'adr-index':
            # Existing decision titles, links and historical rows remain exact. Only
            # current status cells and appended dated pointers/rows may change.
            old, new = before.decode().splitlines(), after.decode().splitlines()
            require(len(new) >= len(old), 'knowledge-change-invalid', 'ADR index history cannot be removed')
            for previous, current in zip(old, new):
                if previous == current:
                    continue
                a, b = previous.split('|'), current.split('|')
                require(len(a) == len(b) == 7 and a[:3] == b[:3] and a[4:] == b[4:]
                        and a[1].strip().isdigit() and b[3].strip() in {'Provisional', 'Accepted', 'Superseded', 'Deprecated'},
                        'knowledge-change-invalid', 'ADR decision content is immutable; only indexed status pointers may reconcile')
    require({item['path'] for item in journal.get('knowledge_changes', [])} <= seen,
            'knowledge-change-invalid', 'Previously bound changes cannot disappear from the reconciliation attestation')
    previous = journal.get('knowledge_changes', [])
    provenance = journal.get('knowledge_change_provenance')
    if previous != declared and provenance:
        require(datetime.fromisoformat(row['observed_at'].replace('Z', '+00:00')) >
                datetime.fromisoformat(provenance['observed_at'].replace('Z', '+00:00')),
                'knowledge-change-invalid', 'A changed knowledge binding needs strictly newer independent evidence')
    if previous and previous != declared:
        journal.setdefault('knowledge_change_history', []).append(previous)
    journal['knowledge_changes'] = declared
    journal['knowledge_change_provenance'] = {key: row[key] for key in ('observed_at', 'provenance', 'source_tips')}


def owns(root: Path, path: Path, journal: dict) -> bool:
    return any(path == root / row['path'] and path.is_file() and digest(path.read_bytes()) == row['after_sha256']
               for row in journal.get('knowledge_changes', []))
