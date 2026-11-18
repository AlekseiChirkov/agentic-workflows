"""Lossless, no-overwrite archival and exact task/journal location resolution."""
from __future__ import annotations

import ctypes
import errno
import os
from pathlib import Path
import re

from finalization_support import Refusal, atomic_write, digest, encoded, field, fsync_dir, manifest, normalized_state, read_json, require, safe_path, section, text
from finalization_knowledge import integrity as knowledge_integrity
from finalization_outputs import integrity as outputs_integrity


def identity(root: Path, original_task: Path) -> str:
    return digest((str(root) + '\0' + original_task.relative_to(root).as_posix()).encode())


def journal_path(root: Path, stable_id: str) -> Path:
    return root / '.ai/context/finalization' / stable_id / 'journal.json'


def validate_journal(root: Path, path: Path) -> dict:
    document = read_json(path)
    require(document.get('schema_version') == 1 and document.get('project_root') == str(root), 'journal-invalid', 'Journal schema or project identity differs')
    original = safe_path(Path(document.get('task_original', '')), root)
    stable_id = identity(root, original)
    require(document.get('id') == stable_id and path == journal_path(root, stable_id), 'journal-invalid', 'Journal filename does not match original task identity')
    require(original.parent == root / '.ai/tasks/todo', 'journal-invalid', 'Original task is not directly under tasks/todo')
    for key in ('task_current', 'spec_original', 'spec_current', 'snapshot_path'):
        require(isinstance(document.get(key), str), 'journal-invalid', 'Journal path is missing: ' + key)
        safe_path(Path(document[key]), root)
    require(Path(document['task_current']) in {original, root / '.ai/tasks/completed' / original.name}, 'journal-invalid', 'Invalid current task location')
    require(isinstance(document.get('repositories'), list) and isinstance(document.get('actions'), list), 'journal-invalid', 'Journal plan is missing')
    return document


def all_journals(root: Path) -> list[tuple[Path, dict]]:
    directory = root / '.ai/context/finalization'
    safe_path(directory, root)
    if not directory.exists():
        return []
    result: list[tuple[Path, dict]] = []
    for path in sorted(directory.glob('*/journal.json')):
        safe_path(path, root)
        result.append((path, validate_journal(root, path)))
    return result


def resolve(root: Path, selected: Path) -> tuple[Path, Path, Path, dict | None]:
    selected = safe_path(selected if selected.is_absolute() else root / selected, root)
    journals = all_journals(root)
    matched = [(path, document) for path, document in journals if str(selected) in {
        document['task_original'], document['task_current'], document['spec_original'], document['spec_current']}]
    is_spec = selected.parent in {root / '.ai/specs', root / '.ai/specs/completed'}
    if not is_spec:
        require(selected.parent in {root / '.ai/tasks/todo', root / '.ai/tasks/completed'}, 'task-invalid', 'Target must be one task directory or spec path')
    if is_spec:
        tasks: list[Path] = []
        for parent in (root / '.ai/tasks/todo', root / '.ai/tasks/completed'):
            safe_path(parent, root)
            for state in sorted(parent.glob('*/state.md')):
                safe_path(state, root)
                pointer = field(text(state), 'spec_path', top=True)
                if pointer and safe_path(root / pointer, root) == selected:
                    tasks.append(state.parent)
        for _, document in matched:
            task = Path(document['task_current'])
            moved = root / '.ai/tasks/completed' / Path(document['task_original']).name
            if not task.exists() and moved.exists() and document.get('archive_intent'):
                task = moved
            if task not in tasks:
                tasks.append(task)
        require(tasks, 'task-not-found', 'No task records this exact spec path')
        require(len(tasks) == 1, 'task-ambiguous', 'Several tasks record this spec; provide an exact task directory')
        task = tasks[0]
        matched = [(path, document) for path, document in journals if str(task) in {document['task_original'], document['task_current']}
                   or (document.get('archive_intent') and task == root / '.ai/tasks/completed' / Path(document['task_original']).name)]
    else:
        task = selected
    require(len(matched) <= 1, 'journal-ambiguous', 'Multiple journals claim the selected task')
    if matched:
        path, document = matched[0]
        task = Path(document['task_current'])
        moved = root / '.ai/tasks/completed' / Path(document['task_original']).name
        if not task.exists() and moved.exists() and document.get('archive_intent'):
            task = moved
        spec = Path(document['spec_current'])
        moved_spec = root / '.ai/specs/completed' / Path(document['spec_original']).name
        if not spec.exists() and moved_spec.exists() and document.get('archive_intent', {}).get('move_spec'):
            spec = moved_spec
        require(task.is_dir() and spec.is_file(), 'archive-recovery-incomplete', 'Neither recorded nor planned archive locations are available')
        return task, spec, path, document
    require(task.is_dir(), 'task-not-found', 'Task directory does not exist and no journal resolves its original path')
    pointer = field(text(task / 'state.md'), 'spec_path', top=True)
    require(pointer, 'spec-not-recorded', 'Task does not record spec_path')
    spec = safe_path(root / pointer, root)
    require(spec.parent in {root / '.ai/specs', root / '.ai/specs/completed'} and spec.is_file(), 'spec-not-found', 'Recorded spec path is unavailable')
    original_task = root / '.ai/tasks/todo' / task.name
    path = journal_path(root, identity(root, original_task))
    return task, spec, path, None


def copy_snapshot(source: Path, destination: Path, root: Path) -> None:
    safe_path(destination, root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        require(destination.read_bytes() == source.read_bytes(), 'snapshot-conflict', 'Existing recovery snapshot differs')
        return
    with destination.open('xb') as handle:
        handle.write(source.read_bytes())
        handle.flush()
        os.fsync(handle.fileno())
    fsync_dir(destination.parent)


def snapshot(root: Path, task: Path, spec: Path, directory: Path) -> dict:
    task_files = manifest(task)
    for name in task_files:
        copy_snapshot(task / name, directory / 'task' / name, root)
    copy_snapshot(spec, directory / 'spec.md', root)
    # Record empty directories as well as files; rename preserves the complete tree.
    task_directories = [p.relative_to(task).as_posix() for p in sorted(task.rglob('*')) if p.is_dir()]
    for name in task_directories:
        (directory / 'task' / name).mkdir(parents=True, exist_ok=True)
    return {'task_files': task_files, 'task_directories': task_directories, 'spec_sha256': digest(spec.read_bytes())}


def integrity(root: Path, task: Path, spec: Path, journal: dict, *, indexes: bool = True,
              current_knowledge: bool = True) -> None:
    knowledge_integrity(root, journal, indexes=indexes, current=current_knowledge)
    outputs_integrity(root, journal)
    recovery = safe_path(Path(journal['snapshot_path']), root)
    original = journal['manifest']['task_files']
    actual = manifest(task)
    require(set(actual) == set(original), 'protected-content-changed', 'Original task file inventory changed')
    directories = [p.relative_to(task).as_posix() for p in sorted(task.rglob('*')) if p.is_dir()]
    require(directories == journal['manifest'].get('task_directories', []), 'protected-content-changed', 'Original task directory inventory changed')
    for name, sha in original.items():
        saved = recovery / 'task' / name
        require(saved.is_file() and digest(saved.read_bytes()) == sha, 'snapshot-conflict', 'Original task recovery snapshot changed')
        if name == 'state.md':
            require(digest(normalized_state(text(task / name))) == journal['original_state_sha256'], 'protected-content-changed', 'Original state audit or protected fields changed')
        else:
            plans = [plan for plan in journal.get('archive_intent', {}).get('moving_links', []) if plan['kind'] == 'task' and plan['name'] == name]
            allowed = {sha, *(plan['after_sha256'] for plan in plans)}
            require(actual[name] in allowed, 'protected-content-changed', f'Original task file changed: {name}')
    allowed_spec = {journal['manifest']['spec_sha256'], *(plan['after_sha256'] for plan in journal.get('archive_intent', {}).get('moving_links', []) if plan['kind'] == 'spec')}
    require(digest(spec.read_bytes()) in allowed_spec
            and digest((recovery / 'spec.md').read_bytes()) == journal['manifest']['spec_sha256'],
            'requirements-changed', 'Original specification requirements or recovery snapshot changed')


def move_no_replace(source: Path, destination: Path, root: Path) -> None:
    """Linux renameat2 is atomic and refuses any existing destination. No copy fallback."""
    safe_path(source, root)
    safe_path(destination, root)
    require(source.stat().st_dev == destination.parent.stat().st_dev, 'archive-cross-device', 'Archive must remain on the same filesystem')
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, 'renameat2', None)
    require(rename is not None, 'archive-unavailable', 'Atomic no-overwrite rename is unavailable')
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1) != 0:
        code = ctypes.get_errno()
        check = 'archive-collision' if code in (errno.EEXIST, errno.ENOTEMPTY) else 'archive-cross-device' if code == errno.EXDEV else 'archive-unavailable'
        raise Refusal(check, f'No-overwrite rename failed: {os.strerror(code)}')
    fsync_dir(source.parent)
    fsync_dir(destination.parent)


def spec_eligible(root: Path, task: Path, spec: Path, journal: dict) -> tuple[bool, str]:
    phase_entries = [int(value) for value in re.findall(r'^#{2,3} Phase ([1-9][0-9]*)\b', text(spec), re.M)]
    phases = set(phase_entries)
    if len(phase_entries) != len(phases) or (phases and phases != set(range(1, max(phases) + 1))):
        return False, 'phase-manifest-ambiguous'
    count = field(text(task / 'state.md'), 'spec_phase_count', top=True)
    if count:
        require(count.isdigit() and int(count) > 0, 'spec-phase-invalid', 'Invalid recorded phase count')
        phases |= set(range(1, int(count) + 1))
    completed_phases: set[int] = set()
    original_spec = Path(journal['spec_original'])
    for parent in (root / '.ai/tasks/todo', root / '.ai/tasks/completed'):
        for state_path in sorted(parent.glob('*/state.md')):
            safe_path(state_path, root)
            state = text(state_path)
            pointer = field(state, 'spec_path', top=True)
            if not pointer or safe_path(root / pointer, root) not in {spec, original_spec, root / '.ai/specs/completed' / original_spec.name}:
                continue
            active = field(state, 'active_phase', top=True)
            if state_path.parent != task and state_path.parent.parent.name != 'completed':
                return False, 'active-other-phases'
            if active:
                require(active.isdigit(), 'spec-phase-invalid', 'Invalid recorded active phase')
            phases_section = section(state, '## Phases')
            for marker in ('execution', 'validation'):
                recorded = re.findall(r'^- ' + marker + r':\s*(.*?)\s*$', phases_section, re.M)
                if recorded != ['complete']:
                    return False, 'phase-completion-unverified'
            if active:
                completed_phases.add(int(active))
            if re.search(r'^- (?:execution|validation): (?!complete\s*$)', state, re.M):
                return False, 'active-other-phases'
            if re.search(r'^\s*\|.*\|\s*(?:deferred|blocked|not-reached)\s*\|', text(state_path.parent / 'plan.md') if (state_path.parent / 'plan.md').exists() else '', re.M):
                return False, 'unfinished-scope'
            for heading in ('## Deferred', '## Outstanding Scope'):
                if section_nonempty(state, heading):
                    return False, 'unfinished-scope'
    if phases and not phases <= completed_phases:
        return False, 'active-other-phases'
    # Explicit outstanding requirements remain product scope, even with validation complete.
    for heading in ('## Deferred', '## Outstanding Scope'):
        content = section_nonempty(text(task / 'state.md'), heading)
        if content:
            return False, 'unfinished-scope'
    return True, 'complete'


def section_nonempty(value: str, heading: str) -> bool:
    from finalization_support import section
    body = section(value, heading).strip().casefold()
    return body not in {'', 'none', '(none)', '- none', '- (none)'}


def pointer_plans(root: Path, journal: dict, task_destination: Path, spec_destination: Path, move_spec: bool) -> list[dict]:
    result: list[dict] = []
    original_task = Path(journal['task_original'])
    original_spec = Path(journal['spec_original'])
    for relative in ('.ai/memory/state.md', '.ai/memory/architecture.md', '.ai/specs/README.md', '.ai/README.md'):
        path = safe_path(root / relative, root)
        if not path.exists():
            continue
        before = path.read_bytes()
        after = relocated_document(path, path, before.decode(), root, original_task, task_destination, original_spec, spec_destination if move_spec else original_spec, current_index=True).encode()
        if after != before:
            recovery_path = Path(journal['snapshot_path']) / 'current-links' / relative
            copy_snapshot(path, recovery_path, root)
            result.append({'path': relative, 'before_sha256': digest(before), 'after_sha256': digest(after),
                           'after_text': after.decode(), 'snapshot': str(recovery_path)})
    return result


def apply_pointer_plans(root: Path, plans: list[dict]) -> None:
    for plan in plans:
        path = safe_path(root / plan['path'], root)
        current = digest(path.read_bytes())
        require(current in {plan['before_sha256'], plan['after_sha256']}, 'current-link-changed', 'Current knowledge pointer changed during archival')
        if current != plan['after_sha256']:
            require(digest(plan['after_text'].encode()) == plan['after_sha256'], 'journal-invalid', 'Pointer operation digest differs')
            atomic_write(path, plan['after_text'].encode(), root)


def relocated_document(source: Path, destination: Path, value: str, root: Path,
                       task_source: Path, task_destination: Path, spec_source: Path,
                       spec_destination: Path, *, current_index: bool = False) -> str:
    """Relocate Markdown destinations only; prose, fences and historical sections stay exact."""
    from urllib.parse import quote, unquote, urlsplit
    fence: str | None = None
    historical = False
    result: list[str] = []
    for line in value.splitlines(keepends=True):
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            run = marker.group(1)
            if fence is None:
                fence = run[0]
            elif run[0] == fence:
                fence = None
            result.append(line)
            continue
        if current_index and line.startswith('#'):
            historical = bool(re.search(r'\b(?:history|historical|snapshots?|archive log)\b', line, re.I))
        if fence or historical:
            result.append(line)
            continue

        def replace(match: re.Match[str]) -> str:
            raw = match.group(2)
            angled = raw.startswith('<') and raw.endswith('>')
            target = raw[1:-1] if angled else raw
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                return match.group(0)
            old_target = Path(os.path.abspath(source.parent / unquote(parsed.path)))
            mapped = old_target
            if old_target == spec_source:
                mapped = spec_destination
            elif old_target.is_relative_to(task_source):
                mapped = task_destination / old_target.relative_to(task_source)
            affected = mapped != old_target
            if current_index and not affected:
                return match.group(0)
            safe_path(old_target, root)
            require(old_target.exists() or mapped.exists(), 'archive-link-broken', f'Broken relative Markdown link in {source}: {target}')
            relative = os.path.relpath(mapped, destination.parent)
            replacement = quote(relative, safe='/._-~')
            if parsed.query:
                replacement += '?' + parsed.query
            if parsed.fragment:
                replacement += '#' + parsed.fragment
            return match.group(1) + ('<' + replacement + '>' if angled else replacement) + match.group(3)

        # Inline and reference-style Markdown links; titles/prose remain outside the destination group.
        line = re.sub(r'(\[[^\]\n]*\]\()(<[^>\n]+>|[^\s)\n]+)((?:[ \t]+[\"\'][^\n]*?[\"\'])?\))', replace, line)
        line = re.sub(r'(^\s*\[[^\]\n]+\]:\s*)(<[^>\n]+>|[^\s\n]+)()', replace, line)
        result.append(line)
    return ''.join(result)


def moving_link_plans(root: Path, journal: dict, task: Path, spec: Path,
                      task_destination: Path, spec_destination: Path) -> list[dict]:
    result: list[dict] = []
    sources = [(task / name, task_destination / name, 'task', name) for name in journal['manifest']['task_files']
               if name.endswith('.md') and name not in {'state.md', 'state-archive.md'}
               and not any(part.casefold() in {'history', 'archive', 'snapshots'} for part in Path(name).parts)]
    state = task / 'state.md'
    state_proposed = relocated_document(state, task_destination / 'state.md', text(state), root, task, task_destination, spec, spec_destination)
    require(state_proposed == text(state), 'protected-state-link-relocation-required', 'A protected state Markdown link needs relocation; preserve the audit and resolve its current pointer explicitly before archival')
    sources.append((spec, spec_destination, 'spec', 'spec.md'))
    for source, destination, kind, name in sources:
        before = text(source)
        origin = Path(journal['task_original']) / name if kind == 'task' else Path(journal['spec_original'])
        after = relocated_document(origin, destination, before, root, Path(journal['task_original']), task_destination, Path(journal['spec_original']), spec_destination)
        if after != before:
            result.append({'kind': kind, 'name': name, 'before_sha256': digest(before.encode()),
                           'after_sha256': digest(after.encode()), 'after_text': after})
    return result


def apply_moving_links(root: Path, journal: dict, task: Path, spec: Path) -> None:
    for plan in journal.get('archive_intent', {}).get('moving_links', []):
        path = task / plan['name'] if plan['kind'] == 'task' else spec
        current = digest(path.read_bytes())
        require(current in {plan['before_sha256'], plan['after_sha256']}, 'protected-content-changed', 'Moving Markdown source changed after its journaled link plan')
        require(digest(plan['after_text'].encode()) == plan['after_sha256'], 'journal-invalid', 'Moving link plan digest differs')
        if current != plan['after_sha256']:
            atomic_write(path, plan['after_text'].encode(), root)
