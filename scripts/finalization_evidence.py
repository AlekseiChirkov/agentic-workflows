"""Read-only task, validation, Git and explicitly attributed PR evidence."""
from __future__ import annotations

import fnmatch
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile

from finalization_support import Refusal, dated, digest, field, manifest, normalized_state, read_json, require, safe_path, section, text, visible_lines

SHA = re.compile(r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')
BRANCH = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._/\-]*$')


def process(arguments: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update({'GIT_OPTIONAL_LOCKS': '0', 'GIT_TERMINAL_PROMPT': '0', 'GIT_NO_REPLACE_OBJECTS': '1', 'GIT_NO_LAZY_FETCH': '1', 'LC_ALL': 'C'})
    # Fixture process isolation is explicit; production never inherits a GIT_* override.
    if os.environ.get('FINALIZATION_TEST_ROOT') and cwd.is_relative_to(Path(os.environ['FINALIZATION_TEST_ROOT'])):
        env.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'})
    try:
        return subprocess.run(arguments, cwd=cwd, text=True, capture_output=True, timeout=20,
                              env=env, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Refusal('evidence-unavailable', f'{arguments[0]} read failed: {error}') from error


def git(repo: Path, *arguments: str, codes: tuple[int, ...] = (0,)) -> str:
    """This allowlist cannot perform Git mutations, including through aliases."""
    require(bool(arguments) and arguments[0] in {'rev-parse', 'show-ref', 'merge-base', 'status', 'worktree',
            'symbolic-ref', 'config', 'ls-remote', 'remote', 'check-ref-format'}, 'internal-read-policy', 'Git mutation rejected')
    if arguments[0] == 'worktree':
        require(arguments[1:] == ('list', '--porcelain'), 'internal-read-policy', 'Only worktree listing is permitted')
    if arguments[0] == 'config':
        require(arguments[1] in {'--get', '--get-all'}, 'internal-read-policy', 'Only config reads are permitted')
    if arguments[0] == 'remote':
        require(len(arguments) == 1, 'internal-read-policy', 'Only remote listing is permitted')
    result = process(['git', '--no-replace-objects', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', *arguments], repo)
    require(result.returncode in codes, 'git-read-failed', f'{arguments[0]} failed: {result.stderr.strip()}')
    return result.stdout.strip()


def commit(repo: Path, revision: str) -> str | None:
    value = git(repo, 'rev-parse', '--verify', '--quiet', revision + '^{commit}', codes=(0, 1))
    return value or None


def ancestor(repo: Path, source: str, target: str) -> bool:
    result = process(['git', '--no-replace-objects', '-c', 'core.fsmonitor=false', 'merge-base', '--is-ancestor', source, target], repo)
    require(result.returncode in (0, 1), 'git-read-failed', result.stderr.strip())
    return result.returncode == 0


def valid_branch(repo: Path, name: object) -> str:
    require(isinstance(name, str) and BRANCH.fullmatch(name) is not None and '..' not in name,
            'branch-invalid', f'Invalid branch: {name}')
    git(repo, 'check-ref-format', 'refs/heads/' + name)
    return name


def blocks(value: str) -> list[dict]:
    result: list[dict] = []
    current: dict | None = None
    for line in section(value, '## Subtask Progress').splitlines():
        match = re.match(r'^(\[composite\] )?(T-\d+[a-z]?(?:-fix-[a-z0-9-]+)?) \|', line)
        if match:
            require(not any(item['id'] == match.group(2) for item in result), 'state-ambiguous', 'Duplicate progress block')
            current = {'id': match.group(2), 'composite': bool(match.group(1)), 'header': line, 'lines': []}
            result.append(current)
        elif current is not None:
            current['lines'].append(line)
    for item in result:
        item['body'] = '\n'.join(item.pop('lines'))
    return result


def plan_statuses(task: Path) -> dict[str, str]:
    require((task / 'plan.md').is_file(), 'validation-evidence-missing', 'Full flow requires plan.md')
    rows = [line for line in section(text(task / 'plan.md'), '## Subtasks').splitlines() if line.lstrip().startswith('|')]
    require(len(rows) >= 2, 'validation-evidence-missing', 'Missing plan table')
    cells = lambda line: [part.strip().strip('`') for part in line.strip().strip('|').split('|')]
    header = [item.lower() for item in cells(rows[0])]
    require('id' in header and 'status' in header, 'validation-evidence-missing', 'Plan table lacks status')
    result: dict[str, str] = {}
    for row in rows[2:]:
        values = cells(row)
        require(len(values) == len(header), 'validation-evidence-missing', 'Malformed plan row')
        identifier = values[header.index('id')].strip()
        require(identifier not in result, 'state-ambiguous', 'Duplicate plan leaf')
        result[identifier] = values[header.index('status')]
    return result


def normative(value: str) -> list[str]:
    return [re.sub(r'^(?:[-*]|\d+\.)\s+', '', line.strip()).strip('` ')
            for line in value.splitlines() if re.match(r'^\s*(?:[-*]|\d+\.)\s+', line)]


def norm(value: str) -> str:
    return re.sub(r'\s+', ' ', value.strip('` .')).casefold()


def validation(state: str, task: Path) -> dict:
    phases = section(state, '## Phases')
    for phase in ('execution', 'validation'):
        require(re.search(r'^- ' + phase + r': complete\s*$', phases, re.M), 'validation-incomplete', f'{phase} is not complete')
    flow = field(state, 'flow', top=True) or 'full'
    require(flow in {'full', 'quick'}, 'flow-invalid', f'Unknown flow {flow}')
    items = blocks(state)
    if flow == 'quick':
        contract = section(state, '## Contract (quick)')
        require(contract, 'quick-contract-missing', 'Quick flow requires an inline contract')
        tdd = section(state, '## TDD (quick)')
        require(tdd and field(tdd, 'level') and field(tdd, 'tests') and (field(tdd, 'green-observed') or '').startswith('yes'),
                'validation-evidence-missing', 'Quick TDD evidence is incomplete')
        red = field(tdd, 'red-observed') or ''
        require(red.startswith('yes') or (field(tdd, 'level') == 'none' and red.startswith('n-a') and len(red) > 12),
                'validation-evidence-missing', 'Quick RED evidence or justified exemption is missing')
    else:
        contract = section(state, '## Solution Design')
        require(contract, 'validation-evidence-missing', 'Full flow requires the recorded solution contract')
    check = section(state, '## Contract Check')
    review = section(state, '## Code Review')
    issues = section(state, '## Issue List')
    require(check and review and issues, 'validation-evidence-missing', 'Contract Check, Code Review and Issue List are required')
    for heading in ('Invariants', 'Acceptance Criteria', 'Off-limits'):
        expected = normative(section(contract, '### ' + heading))
        actual = section(check, '### ' + heading)
        require(expected and actual, 'validation-evidence-missing', f'Missing normative or verified {heading}')
        table: dict[str, str] = {}
        for line in actual.splitlines():
            if line.strip().startswith('|'):
                cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
                if len(cells) == 2 and cells[1].startswith(('PASS', 'FAIL')):
                    require(norm(cells[0]) not in table, 'state-ambiguous', 'Duplicate contract verification row')
                    table[norm(cells[0])] = cells[1]
        require(table, 'validation-evidence-missing', f'No verified {heading} table rows')
        require(not any(status.startswith('FAIL') for status in table.values()), 'contract-failed', f'Failed {heading} remain incomplete')
        require(all(norm(item) in table and table[norm(item)].startswith('PASS') for item in expected),
                'contract-coverage-incomplete', f'Unverified normative {heading}')
    require(not re.search(r'Critical Failures Decision:\s*pause', check), 'contract-failed', 'Critical gate remains paused')
    findings = section(review, '### Findings')
    summary = section(review, '### Summary')
    approved = section(issues, '### Approved')
    deferred = section(issues, '### Deferred')
    require(findings and summary and approved and deferred, 'validation-evidence-missing', 'Review findings, summary and issue decisions are required')
    numbers = set(re.findall(r'^\s*(\d+)\.', findings, re.M))
    decided = set(re.findall(r'^\s*(\d+)\.', approved + '\n' + deferred, re.M))
    require(numbers <= decided, 'issue-decision-incomplete', 'Review findings lack an approve/defer decision')
    require(not section(state, '## Open Questions (batch)') or norm(section(state, '## Open Questions (batch)')) in {'none', '(none)'},
            'issue-decision-incomplete', 'Open decisions remain')
    empty = {'none', '(none)', '—', '-'}
    if flow == 'full':
        fixes = section(state, '## Fix-Tasks')
        require(field(fixes, 'fixes-created') == 'complete', 'validation-evidence-missing', 'Fix creation is incomplete')
        count = field(fixes, 'fixes-count')
        created = field(fixes, 'Created')
        require(count is not None and count.isdigit() and created is not None, 'validation-evidence-missing', 'Fix inventory is missing')
        created_ids = [] if created.casefold() == 'none' else [item.strip() for item in created.split(',')]
        require(len(created_ids) == int(count) and len(set(created_ids)) == len(created_ids), 'validation-evidence-missing', 'Fix inventory count differs')
        statuses = plan_statuses(task)
        indexed = {item['id']: item for item in items}
        if norm(approved) not in empty:
            require(created_ids, 'approved-fix-unresolved', 'Approved issues have no reviewed repair')
        for identifier in created_ids:
            require(identifier in indexed and 'atomic-validation: complete' in indexed[identifier]['header'] and statuses.get(identifier) == 'reviewed',
                    'approved-fix-unresolved', f'Approved fix {identifier} is unresolved')
        require(items, 'validation-evidence-missing', 'Full flow has no progress evidence')
        for item in items:
            if item['composite']:
                combined = item['header'] + '\n' + item['body']
                children = field(item['body'], 'children')
                require('integration-validation: complete' in combined and 'rollup: done' in combined and children,
                        'composite-incomplete', f'Composite {item["id"]} integration has not passed')
                require(all(child.strip() in indexed for child in children.split(',')), 'composite-incomplete', 'Composite child is absent')
            else:
                require('atomic-execution: complete' in item['header'] and 'atomic-validation: complete' in item['header'],
                        'validation-incomplete', f'Leaf {item["id"]} has not passed validation')
                require('atomic-tests: green' in item['header'] or ('atomic-tests: n-a' in item['header'] and 'tdd: none' in item['body']),
                        'validation-incomplete', f'Leaf {item["id"]} lacks preserved TDD evidence')
            require(statuses.get(item['id']) == 'reviewed', 'validation-incomplete', f'Plan does not record {item["id"]} reviewed')
        require(all(identifier in indexed and status == 'reviewed' for identifier, status in statuses.items()),
                'validation-incomplete', 'Unreviewed plan scope remains')
    elif norm(approved) not in empty:
        inline = section(state, '## Inline Fixes')
        require(inline and re.search(r'^Review:\s*complete', inline, re.M) and 'unresolved' not in inline.casefold(),
                'approved-fix-unresolved', 'Quick approved inline fixes require independent resolution evidence')
    report = section(state, '## Execution Report')
    require(re.search(r'Final verification:\s*PASS\b', report), 'validation-evidence-missing', 'Final verification after the last change is not recorded')
    return {'flow': flow, 'source': 'recorded task contract/review/TDD evidence; no tests rerun', 'fresh_tests': False}


def evidence_file(path: Path | None) -> dict:
    if path is None:
        return {'pull_requests': [], 'attestations': [], 'provenance': {'kind': 'unavailable'}}
    result = read_json(path)
    require(result.get('schema_version') == 1 and isinstance(result.get('pull_requests', []), list)
            and isinstance(result.get('attestations', []), list), 'evidence-invalid', 'Unsupported evidence schema')
    return result


def fixture_authority(root: Path, repo: Path, evidence: dict) -> bool:
    provenance = evidence.get('provenance', {})
    return (isinstance(provenance, dict) and provenance.get('kind') == 'controlled-fixture'
            and provenance.get('root') == str(root) and dated(provenance.get('observed_at'))
            and os.environ.get('FINALIZATION_TEST_ROOT') == str(root)
            and root.is_relative_to(Path(tempfile.gettempdir()))
            and git(repo, 'config', '--get', 'orchestrail.fixture', codes=(0, 1)) == 'true')


def pr_evidence(root: Path, repo: Path, candidate: dict, target: dict, evidence: dict, *, proof_required: bool = True) -> dict | None:
    url = candidate.get('pr')
    if not url:
        return None
    if fixture_authority(root, repo, evidence):
        rows = [item for item in evidence.get('pull_requests', []) if isinstance(item, dict) and item.get('url') == url]
        require(len(rows) == 1, 'pr-authority-unverified', 'A unique controlled fixture PR receipt is required')
        receipt = dict(rows[0])
        receipt['provenance'] = 'controlled-fixture; isolated repository only'
    else:
        require(re.fullmatch(r'https://github\.com/[^/]+/[^/]+/pull/[1-9][0-9]*', url),
                'pr-authority-unverified', 'Caller PR data is not authoritative; a GitHub PR URL is required for a fresh read')
        observed = process(['gh', 'pr', 'view', url, '--json', 'url,state,baseRefName,headRefName,headRefOid,mergeCommit,mergedAt'], repo)
        require(observed.returncode == 0, 'pr-authority-unverified', 'Authoritative PR read unavailable: ' + observed.stderr.strip())
        import json
        try:
            row = json.loads(observed.stdout)
        except ValueError as error:
            raise Refusal('pr-authority-unverified', 'Invalid GitHub PR response') from error
        require(isinstance(row, dict), 'pr-authority-unverified', 'Invalid GitHub PR response')
        receipt = {'url': row.get('url'), 'repository': str(repo), 'head_ref': row.get('headRefName'),
                   'head_sha': row.get('headRefOid'), 'base_ref': row.get('baseRefName'), 'state': row.get('state'),
                   'merge_commit': (row.get('mergeCommit') or {}).get('oid'), 'merged_at': row.get('mergedAt'),
                   'provenance': 'fresh gh pr view against GitHub; caller fields ignored'}
    require(receipt.get('url') == url and receipt.get('repository') == str(repo) and receipt.get('state') in {'OPEN', 'CLOSED', 'MERGED'}, 'pr-authority-unverified', 'PR outcome identity is invalid')
    if not proof_required:
        return receipt
    require(receipt.get('repository') == str(repo) and receipt.get('head_ref') == candidate['branch']
            and receipt.get('head_sha') == candidate['original_tip'] and receipt.get('base_ref') == target['branch']
            and receipt.get('state') == 'MERGED' and dated(receipt.get('merged_at')),
            'integration-unverified', 'PR is not a matching merged delivery to the intended integration branch')
    merge = receipt.get('merge_commit')
    require(isinstance(merge, str) and SHA.fullmatch(merge) and commit(repo, merge) == merge
            and ancestor(repo, merge, target['tip']), 'integration-unverified', 'PR merge evidence is not reachable from integration')
    return receipt


def remote_refs(repo: Path) -> tuple[dict[str, str], str | None]:
    urls = git(repo, 'config', '--get-all', 'remote.origin.url', codes=(0, 1)).splitlines()
    require(len(urls) <= 1, 'remote-unsafe', 'Multiple origin URLs cannot establish an exact delete destination')
    remote = urls[0] if urls else ''
    if not remote:
        return {}, None
    require(not remote.startswith('-') and re.match(r'^[A-Za-z][A-Za-z0-9+.-]*::', remote) is None, 'remote-unsafe', 'External Git transports are not permitted')
    pushurls = git(repo, 'config', '--get-all', 'remote.origin.pushurl', codes=(0, 1)).splitlines()
    require(not pushurls or pushurls == [remote], 'remote-unsafe', 'Push destination differs from observed fetch destination')
    require(git(repo, 'config', '--get', 'remote.origin.mirror', codes=(0, 1)).casefold() not in {'true', 'yes', '1', 'on'}, 'remote-unsafe', 'Mirror remotes are not task scoped')
    for key in ('remote.origin.uploadpack', 'remote.origin.receivepack', 'remote.origin.vcs', 'core.sshCommand'):
        require(not git(repo, 'config', '--get', key, codes=(0, 1)), 'remote-unsafe', f'Executable transport configuration: {key}')
    output = git(repo, 'ls-remote', '--symref', 'origin', 'HEAD', 'refs/heads/*')
    refs: dict[str, str] = {}
    default: str | None = None
    for line in output.splitlines():
        value, separator, name = line.partition('\t')
        require(bool(separator), 'remote-unavailable', 'Malformed remote advertisement')
        if value.startswith('ref: ') and name == 'HEAD':
            require(value[5:].startswith('refs/heads/'), 'default-branch-unknown', 'Remote HEAD is not a branch')
            default = value[5:][len('refs/heads/'):]
        elif SHA.fullmatch(value):
            require(name not in refs, 'remote-unavailable', 'Duplicate remote ref')
            refs[name] = value
    require(default is not None and 'refs/heads/' + default in refs, 'default-branch-unknown', 'Current remote default branch is unknown')
    return refs, default


def repository_specs(root: Path, state: str, items: list[dict], evidence: dict) -> list[dict]:
    recorded = section(state, '## Repositories')
    if recorded:
        pairs: list[tuple[str, str]] = []
        for line in recorded.splitlines():
            if not line.strip() or line.startswith('cross_repo_dependencies:'):
                continue
            match = re.fullmatch(r'- repo: ([A-Za-z0-9][A-Za-z0-9._-]*) \| base_branch: (\S+)', line)
            require(match is not None, 'repository-set-invalid', 'Malformed recorded repository set')
            pairs.append(match.groups())
        require(pairs and len({name for name, _ in pairs}) == len(pairs), 'repository-set-invalid', 'Repository set is empty or duplicated')
        return [{'name': name, 'path': str(safe_path(root / name, root)), 'base_branch': base} for name, base in pairs]
    root_git = process(['git', 'rev-parse', '--show-toplevel'], root)
    require(root_git.returncode == 0 and Path(root_git.stdout.strip()) == root, 'repository-set-missing', 'Non-Git umbrella requires its recorded repository set')
    bases = {field(item['body'], 'base_branch') for item in items if not item['composite']}
    branches = {field(item['body'], 'branch') for item in items if not item['composite']}
    base = field(state, 'base_branch', top=True)
    if base is None:
        targets = bases - branches - {None}
        require(len(targets) == 1, 'integration-target-ambiguous', 'Record the intended integration branch explicitly')
        base = targets.pop()
    return [{'name': '.', 'path': str(root), 'base_branch': base}]


def grouped_items(repo: Path, items: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for item in items:
        branch = valid_branch(repo, field(item['body'], 'branch'))
        groups.setdefault(branch, []).append(item)
    result: list[dict] = []
    for branch, members in groups.items():
        records: list[dict] = []
        for member in members:
            base = field(member['body'], 'base_commit')
            commits = re.findall(r'(?:^|,)\s*([0-9a-f]+)(?=\s|$)', field(member['body'], 'commits') or '')
            require(base and SHA.fullmatch(base) and commits and all(SHA.fullmatch(sha) for sha in commits), 'original-sha-invalid', 'Original base and commits must be full SHAs')
            require(commit(repo, base) == base and all(commit(repo, sha) == sha for sha in commits), 'original-sha-unavailable', 'Original commit object is unavailable')
            require(all(ancestor(repo, base, sha) for sha in commits) and all(ancestor(repo, a, b) for a, b in zip(commits, commits[1:])), 'original-ancestry-invalid', 'Member original range is inconsistent')
            records.append({'leaf': member['id'], 'base_commit': base, 'original_commits': commits, 'original_tip': commits[-1], 'pr': field(member['body'], 'pr')})
        tips = list(dict.fromkeys(record['original_tip'] for record in records))
        maximal = [tip for tip in tips if all(ancestor(repo, other, tip) for other in tips)]
        require(len(maximal) == 1, 'original-ancestry-invalid', 'Shared branch has no unique maximal recorded tip')
        all_commits = list(dict.fromkeys(sha for record in records for sha in record['original_commits']))
        require(all(ancestor(repo, a, b) or ancestor(repo, b, a) for a in all_commits for b in all_commits), 'original-ancestry-invalid', 'Shared member histories diverge')
        ordered = sorted(all_commits, key=lambda tip: sum(ancestor(repo, other, tip) for other in all_commits))
        bases = list(dict.fromkeys(record['base_commit'] for record in records))
        oldest = [base for base in bases if all(ancestor(repo, base, other) for other in bases)]
        require(len(oldest) == 1, 'original-ancestry-invalid', 'Shared branch bases do not form one history')
        body = '  branch: ' + branch + '\n  base_commit: ' + oldest[0] + '\n  commits: ' + ', '.join(ordered)
        result.append({'id': members[0]['id'], 'body': body, 'members': records})
    return result


def dirty_paths(repo: Path) -> list[str]:
    output = process(['git', '--no-replace-objects', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', 'status', '--porcelain', '-z', '--untracked-files=no'], repo)
    require(output.returncode == 0, 'git-read-failed', output.stderr)
    entries = output.stdout.split('\0')
    paths: list[str] = []
    index = 0
    while index < len(entries):
        row = entries[index]
        index += 1
        if not row:
            continue
        require(len(row) >= 4, 'worktree-dirty', 'Malformed status record')
        paths.append(row[3:])
        if 'R' in row[:2] or 'C' in row[:2]:
            require(index < len(entries) and entries[index], 'worktree-dirty', 'Malformed renamed status record')
            paths.append(entries[index])
            index += 1
    return paths


def owned_metadata_change(root: Path, repo: Path, relative: str, journal: dict | None) -> bool:
    if not journal:
        return False
    path = safe_path(repo / relative, root)
    original_task = Path(journal['task_original'])
    current_task = Path(journal['task_current'])
    planned_task = root / '.ai/tasks/completed' / original_task.name
    for source in {original_task, current_task, planned_task}:
        if path.is_relative_to(source):
            name = path.relative_to(source).as_posix()
            original_sha = journal['manifest']['task_files'].get(name)
            if original_sha is None:
                return False
            if not path.exists():
                return bool(journal.get('archive_intent') and source == original_task and (planned_task / name).is_file())
            if name == 'state.md':
                return digest(normalized_state(text(path))) == journal['original_state_sha256']
            return digest(path.read_bytes()) == original_sha
    original_spec = Path(journal['spec_original'])
    current_spec = Path(journal['spec_current'])
    if path in {original_spec, current_spec}:
        if not path.exists():
            return bool(journal.get('archive_intent', {}).get('move_spec') and (root / '.ai/specs/completed' / original_spec.name).is_file())
        return digest(path.read_bytes()) == journal['manifest']['spec_sha256']
    for plan in journal.get('archive_intent', {}).get('current_links', []):
        if path == root / plan['path'] and path.is_file():
            return digest(path.read_bytes()) in {plan['before_sha256'], plan['after_sha256']}
    return False


def assess(root: Path, task: Path, spec: Path, evidence: dict, journal: dict | None = None) -> dict:
    state = text(task / 'state.md')
    manifest(task)
    validation_info = validation(state, task)
    items = blocks(state)
    if validation_info['flow'] == 'quick':
        delivery = section(state, '## Delivery')
        if delivery:
            items = [{'id': 'delivery', 'composite': False, 'body': delivery, 'header': ''}]
        else:
            # Optional additive evidence for manual quick work, never inferred branch ownership.
            rows = evidence.get('delivery_records', [])
            require(isinstance(rows, list) and rows, 'branch-evidence-missing', 'Quick delivery needs original-ref records in optional Delivery or explicit evidence')
            items = []
            for row in rows:
                require(isinstance(row, dict) and row.get('task_path') == str(task), 'branch-evidence-missing', 'Delivery receipt belongs to another task')
                require(dated(row.get('observed_at')) and row.get('provenance'), 'branch-evidence-missing', 'Delivery ownership receipt needs dated provenance')
                items.append({'id': row.get('id', 'delivery'), 'composite': False, 'header': '',
                              'body': '\n'.join('  ' + key + ': ' + str(value) for key, value in row.items() if key in {'repo', 'branch', 'base_branch', 'base_commit', 'commits', 'pr'})})
    specs = repository_specs(root, state, items, evidence)
    assigned: dict[str, list[dict]] = {item['name']: [] for item in specs}
    for item in items:
        if item['composite']:
            continue
        name = field(item['body'], 'repo') or ('.' if len(specs) == 1 and specs[0]['name'] == '.' else None)
        require(name in assigned, 'repository-set-invalid', f'Leaf {item["id"]} is not assigned to the recorded repository set')
        assigned[name].append(item)
    repositories: list[dict] = []
    actions: list[dict] = []
    for entry in specs:
        repo = safe_path(Path(entry['path']), root)
        require(repo.is_dir(), 'repository-unavailable', f'Missing repository {repo}')
        require(git(repo, 'rev-parse', '--show-toplevel') == str(repo), 'repository-set-invalid', 'Recorded repository path is not its root')
        require(git(repo, 'rev-parse', '--is-shallow-repository') == 'false', 'integration-unverified', 'Shallow ancestry is not sufficient evidence')
        common = safe_path(Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir')))
        gitdir = safe_path(Path(git(repo, 'rev-parse', '--absolute-git-dir')))
        for marker in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'BISECT_LOG', 'rebase-merge', 'rebase-apply'):
            require(not (gitdir / marker).exists(), 'operation-in-progress', f'Unfinished Git operation: {marker}')
        require(not (common / 'info/grafts').exists(), 'integration-unverified', 'Grafted ancestry is not authoritative')
        dirty = dirty_paths(repo)
        base = valid_branch(repo, entry['base_branch'])
        integration_ref = 'refs/heads/' + base
        integration_tip = commit(repo, integration_ref)
        local_integration_tip = integration_tip
        require(integration_tip, 'integration-unverified', f'Intended integration branch {base} is missing')
        refs, remote_default = remote_refs(repo)
        remote_configured = remote_default is not None
        refresh = False
        if remote_configured:
            advertised_tip = refs.get(integration_ref)
            require(advertised_tip and commit(repo, advertised_tip) == advertised_tip, 'integration-object-unavailable', 'Fetch the exact advertised integration commit explicitly before preparing')
            if advertised_tip != integration_tip:
                require(ancestor(repo, integration_tip, advertised_tip), 'integration-diverged', 'Local intended integration branch has diverged from live remote')
                require(git(repo, 'config', '--get', 'branch.' + base + '.remote', codes=(0, 1)) == 'origin'
                        and git(repo, 'config', '--get', 'branch.' + base + '.merge', codes=(0, 1)) == integration_ref,
                        'integration-upstream-unknown', 'FF refresh requires the exact existing origin/integration upstream')
                integration_tip = advertised_tip
                refresh = True
        configured = git(repo, 'config', '--get-all', 'orchestrail.protectedBranch', codes=(0, 1)).splitlines()
        protected = list(dict.fromkeys(['main', 'master', 'release/*', base, *configured, *([remote_default] if remote_default else [])]))
        current = git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD', codes=(0, 1))
        worktrees = git(repo, 'worktree', 'list', '--porcelain')
        locations: dict[str, list[str]] = {}
        location = ''
        for line in worktrees.splitlines():
            if line.startswith('worktree '):
                location = line[9:]
            elif line.startswith('branch refs/heads/'):
                locations.setdefault(line[len('branch refs/heads/'):], []).append(location)
        target = {'branch': base, 'ref': integration_ref, 'tip': integration_tip}
        candidates: list[dict] = []
        require(assigned[entry['name']], 'branch-evidence-missing', 'Recorded repository has no original branch evidence')
        for item in grouped_items(repo, assigned[entry['name']]):
            body = item['body']
            branch = valid_branch(repo, field(body, 'branch'))
            require(not any(fnmatch.fnmatchcase(branch, pattern) for pattern in protected), 'branch-protected', f'{branch} is protected')
            original_base = field(body, 'base_commit')
            commits_text = field(body, 'commits') or ''
            original_commits = re.findall(r'(?:^|,)\s*([0-9a-f]+)(?=\s|$)', commits_text)
            require(original_base and SHA.fullmatch(original_base) and original_commits and all(SHA.fullmatch(sha) for sha in original_commits),
                    'original-sha-invalid', 'Original base and commits must be recorded as full SHAs')
            original_tip = original_commits[-1]
            require(commit(repo, original_base) == original_base and all(commit(repo, sha) == sha for sha in original_commits),
                    'original-sha-unavailable', 'Original recorded commit objects are unavailable; absent refs prove nothing')
            require(all(ancestor(repo, original_base, sha) for sha in original_commits)
                    and all(ancestor(repo, earlier, later) for earlier, later in zip(original_commits, original_commits[1:])),
                    'original-ancestry-invalid', 'Recorded original commits do not form the original branch history')
            ref = 'refs/heads/' + branch
            local_tip = commit(repo, ref)
            require(local_tip is None or local_tip == original_tip, 'branch-tip-changed', f'{ref} moved from original tip {original_tip}')
            require(not any(Path(path) != repo for path in locations.get(branch, [])), 'branch-in-worktree', f'{branch} is checked out in another worktree')
            remote_tip = refs.get(ref)
            previous: dict | None = None
            if journal:
                matches = [candidate for repository in journal['repositories'] if repository['path'] == str(repo)
                           for candidate in repository['candidates'] if candidate['branch'] == branch]
                require(len(matches) == 1, 'protected-content-changed', 'Original branch set changed')
                previous = matches[0]
            expected_remote = previous['expected_remote_tip'] if previous else remote_tip
            require(remote_tip is None or remote_tip == expected_remote, 'remote-tip-changed', f'Current remote {ref} differs from recorded expected tip')
            require(expected_remote is None or expected_remote == original_tip, 'remote-tip-changed', f'Remote {ref} has unrelated work')
            candidate = {'leaf': item['id'], 'branch': branch, 'local_ref': ref, 'original_tip': original_tip,
                         'expected_tip': original_tip, 'base_commit': original_base, 'original_commits': original_commits,
                         'remote': 'origin' if remote_configured else None, 'remote_ref': ref,
                         'expected_remote_tip': expected_remote, 'pr': next((member['pr'] for member in reversed(item['members']) if member['pr']), None), 'pr_receipt': None, 'members': item['members'],
                         'recovery_command': ['git', '-C', str(repo), 'branch', branch, original_tip]}
            actual_receipts = []
            for member in item['members']:
                if member['pr']:
                    member_candidate = {**candidate, 'pr': member['pr'], 'original_tip': member['original_tip']}
                    actual_receipts.append(pr_evidence(root, repo, member_candidate, target, evidence, proof_required=False))
            candidate['pr_receipts'] = actual_receipts
            candidate['pr_receipt'] = actual_receipts[-1] if actual_receipts else None
            integrated = all(ancestor(repo, sha, integration_tip) for sha in original_commits)
            if integrated:
                candidate['integration_method'] = 'ancestry'
            else:
                receipt = pr_evidence(root, repo, candidate, target, evidence)
                require(receipt is not None, 'integration-unverified', f'Original commits from {branch} are not integrated')
                candidate['pr_receipt'] = receipt
                candidate['integration_method'] = 'pr'
            candidates.append(candidate)
        require(not dirty or (current == base and not refresh and all(owned_metadata_change(root, repo, name, journal) for name in dirty)), 'worktree-dirty', f'Unrelated tracked edits or unsafe checkout edits in {repo}')
        if current != base:
            require(current in {item['branch'] for item in candidates}, 'checkout-unowned', 'Current checkout is detached or unrelated; select the integration branch explicitly')
            actions.append({'id': entry['name'] + ':checkout', 'kind': 'checkout', 'repository': str(repo), 'branch': base,
                            'expected_tip': integration_tip, 'command': ['git', '-C', str(repo), 'switch', base]})
        elif journal:
            actions.extend({**action, 'expected_tip': integration_tip} for action in journal['actions'] if action['repository'] == str(repo) and action['kind'] == 'checkout')
        if refresh:
            require(not dirty, 'worktree-dirty', 'Cannot refresh an integration checkout over tracked edits')
            actions.append({'id': entry['name'] + ':refresh', 'kind': 'refresh', 'repository': str(repo), 'branch': base, 'expected_tip': integration_tip, 'before_tip': local_integration_tip, 'command': ['git', '-C', str(repo), 'pull', '--ff-only']})
        elif journal:
            actions.extend({**action, 'expected_tip': integration_tip} for action in journal['actions'] if action['repository'] == str(repo) and action['kind'] == 'refresh')
        for candidate in candidates:
            branch = candidate['branch']
            # Retain original planned actions across retries even after a ref disappears.
            old_actions = journal.get('actions', []) if journal else []
            if commit(repo, candidate['local_ref']) or any(a['repository'] == str(repo) and a.get('branch') == branch and a['kind'] == 'local-delete' for a in old_actions):
                actions.append({'id': entry['name'] + ':local:' + branch, 'kind': 'local-delete', 'repository': str(repo), 'branch': branch,
                                'expected_tip': candidate['original_tip'], 'command': ['git', '-C', str(repo), 'branch', '-d', branch]})
            if candidate['expected_remote_tip'] is not None:
                actions.append({'id': entry['name'] + ':remote:' + branch, 'kind': 'remote-delete', 'repository': str(repo), 'branch': branch,
                                'remote_ref': candidate['remote_ref'], 'expected_tip': candidate['expected_remote_tip'],
                                'command': ['git', '-C', str(repo), 'push', '--force-with-lease=' + candidate['remote_ref'] + ':' + candidate['expected_remote_tip'], 'origin', ':' + candidate['remote_ref']]})
        repositories.append({'name': entry['name'], 'path': str(repo), 'common_dir': str(common), 'integration': target,
                             'protected': protected, 'current_branch': current, 'remote_evidence': 'live ls-remote' if remote_configured else 'origin not configured',
                             'candidates': candidates})
    return {'repositories': repositories, 'actions': actions, 'validation_evidence': validation_info,
            'outcomes': {'validation': 'complete', 'integration': 'complete', 'checkout': 'complete' if not any(a['kind'] == 'checkout' for a in actions) else 'incomplete',
                         'cleanup': 'incomplete' if any(a['kind'].endswith('delete') for a in actions) else 'complete', 'knowledge': 'unverified', 'archival': 'incomplete',
                         'audit': 'unverified', 'deployment': 'unverified'}}
