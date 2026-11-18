#!/usr/bin/env python3
"""Evidence-backed finalization mechanics (Python 3.11+, standard library).

Public workflow: /phase-finalize TARGET [--dry-run]. This internal CLI is its
required mechanics, not a Git policy bypass. It never mutates project Git state.
Project Git mutations are returned as argv arrays for explicit hook-governed execution.
Recovery verification initializes/writes only disposable isolated temporary Git storage.

CLI (one JSON object on stdout, exit 0 success / 1 blocked / 2 usage):
  phase-finalize.py inspect TARGET --root ROOT [--evidence JSON] [--dry-run]
  phase-finalize.py prepare|record|knowledge|archive|finish TARGET --root ROOT
      [--evidence JSON] --authorize --expected-revision absent|SHA256 [--dry-run]
No implicit project root/repository discovery, project Git initialization, checkout, fetch, PR/history merge,
push, branch deletion, reset, stash, clean, worktree removal or logging occurs.
Explicit safe checkout plans may include literal pull --ff-only on the recorded
existing origin/integration upstream. No PR or history merge is permitted.
The caller's ordinary workflow invocation authorizes --authorize only for this task.
Dry-run always performs inspection only: no project/Git/telemetry writes or locks.
Read-only ls-remote obtains current remote refs; stale remote-tracking refs are not
merge/lease proof. Missing local objects block; no automatic fetch occurs.

JSON result schema v1: schema_version, command, status, failures[{check,reason}],
resolution{task_path,spec_path,original_task_path}, id, journal_path, revision (sha256
of actual journal bytes; 'absent' initially), plan_digest, repositories, actions,
outcomes{validation,integration,checkout,cleanup,recovery,knowledge,archival,audit,deployment,
spec_archival?}, complete, validation_evidence, action_receipts and trust_limitations.
Statuses: ready, recovery-required, prepared, recorded, archived, complete, blocked. A ready inspection
is not completion. record rechecks each actual ref/checkout postcondition; command
exit codes or caller success flags never establish cleanup. Surviving remote refs
remain incomplete. Local branch -d refusal MUST preserve that branch; never use -D.

Journal: ROOT/.ai/context/finalization/<stable-id>/journal.json, stable-id = sha256
(absolute physical root + NUL + original task path relative to root). The journal
stores original full SHA/ref/recovery commands, immutable original-state/spec/tree
hashes, complete manifests (empty directories included), byte-exact snapshots,
current paths, explicit action plan, independently attributed attestations, phase
outcomes, archive intent and per-action observations. flock serializes writers;
expected revisions are mandatory even on replay. Writes fsync files, atomically
replace, then fsync the directory. Archive uses renameat2(RENAME_NOREPLACE) with
same-device checks and no copy/delete fallback. Interrupted intents resolve old
paths and resume; unknown/missing destinations never prove success. Current
spec_path and the additive finalization phase marker are the only state edits.
Original snapshots never change. Markdown relocation journals exact destination edits for moved current task/spec files and explicit current indexes; historical state-archive/progress/snapshot bytes stay exact. Protected state links requiring relocation block archival explicitly rather than silently breaking. Sparse/duplicate phase numbering keeps the spec active with an ambiguity report. finish writes/verifies '- finalization: complete'
only after required postconditions; deployment remains unverified unless required
by '## Delivery Contract / deployment: required' and independently evidenced.

Recovery gating: first prepare returns recovery-required with recovery_actions[].
Each action has repository, pack_path/stdout_path, exact read-only pack-objects argv,
stdin containing only original maximal full tips, restore_command, restore_stdin,
and branch_recovery_commands. The caller writes stdout to the exact pack_path,
then reruns prepare with the returned revision. No deletion-authorizing receipt is
published until every self-contained pack is verified. No --all or unrelated ref
selection occurs. Verification runs Git init/index-pack/fsck ONLY in isolated /tmp
object storage (30-second subprocess bounds), without templates, global/system
config, alternate objects, replacements, lazy fetch or network. Project Git objects,
refs, index and worktree remain unchanged. Dry-run emits this plan without writes.
Journal recovery[] records repository, immutable pack_path/sha256, original tips,
closure_verified, verified_at, verification provenance, restore_command and explicit
restore_stdin path plus original branch recreation commands. Existing corrupt or
incomplete material is preserved and blocks authorization; it is never replaced by
chmod/removal/regeneration. Every published receipt additionally includes its exact
repository recovery record; hooks must check the journal-bound pack SHA before any
deletion. Explicit restore uses index-pack --stdin --strict < PACK followed by the
recorded branch command; original object existence alone is not durable recovery.

Hook receipt v1: <git-common-dir>/orchestrail-finalize/<stable-id>.json, with exact
fields schema_version=1, kind='task-finalization', id, task_path(original absolute),
project_root, repository(absolute), common_dir, journal_path, journal_revision,
plan_digest, authorization={invocation:'phase-finalize',task_path,cleanup:true},
integration={branch,ref,tip}, candidates (same canonical candidate objects as journal),
and recovery (the exact verified repository recovery record from the journal).
Each candidate has leaf, branch, local_ref, original_tip, expected_tip, base_commit,
original_commits, remote, remote_ref, expected_remote_tip, integration_method,
pr, pr_receipt and recovery_command. plan_digest = sha256(canonical JSON bytes
of {repositories,actions}); canonical bytes are sorted-key indent=2 JSON + newline.
Candidates additionally retain members[] with each original audit range and pr_receipts[] with every actual PR outcome, including closed/unmerged states.
The journal is authoritative for scope, not a free-standing receipt. Hooks MUST
independently validate journal hash and plan digest, exact candidate membership,
authorization, current full tips/integration/protection/worktrees, original ancestry
or matching authoritative reachable PR evidence, and explicit remote compare/delete.
Receipts never authorize any other mutation. Old-path resolution requires the exact
original identity; no branch/task names are guessed.

Evidence JSON v1: schema_version=1, provenance object, pull_requests[],
attestations[], optional delivery_records[]. Caller PR claims are not authoritative:
canonical pr: none means no PR. #N draft/#N ready resolve via this repository's exact configured GitHub origin; explicit GitHub URLs must match that identity. Production re-reads gh pr view N --repo OWNER/REPO, verifies returned URL identity, and preserves the original pr audit string unchanged.
Rewritten history requires exact original head/ref, intended integration base,
MERGED state, dated merge and reachable merge object. An ordinary closed PR or a
merge only into a stack feature does not qualify. Ancestry checks all original
commits, not just a missing ref. Offline controlled-fixture PR data is accepted only
under the explicit FINALIZATION_TEST_ROOT temporary fixture root, dated matching
provenance and git config orchestrail.fixture=true; never a production authority.

Attestations: {kind:'knowledge'|'audit'|'verification'|'deployment', task_path,
state_sha256 (original raw state hash or current raw hash), observed_at (dated ISO
with timezone), result:'pass', provenance (named independent source), source_tips:
{absolute repo: current integration full SHA}}. Verification additionally supplies
commands:[{argv:[...],exit_code:0,stdout,stderr}], coverage, and optional
reuse:{permitted:true,original_state_sha256,validated_tips:{repo: original SHA},
limitations}. The helper never runs arbitrary receipt commands: external attestation
trust is disclosed explicitly, not mislabeled as observed fresh test execution.
Verification coverage must cover the changed surface; a reused prior result needs
explicit prior-tip/state provenance and runtime/dependency limits. Knowledge/audit
attestations attest semantic reconciliation/review; they never rewrite history.
Deployment additionally needs revision (one of current source tips), environment,
and dated provenance. Caller checkpoint flags alone have no success semantics.
A required deployment without evidence blocks finish; unknown optional deployment
is reported as unverified and does not block. Missing optional tools/logging never
become successful measurements; no telemetry is emitted here.

Quick tasks retain their ordinary state without synthetic leaves. An optional
## Delivery section can hold original branch/base_branch/base_commit/commits/pr
(and repo in umbrellas). Equivalent explicit delivery_records input receipts may
supply those fields with task_path, observed_at and ownership provenance; they are
persisted in this journal only. Missing ownership evidence blocks, never guesses.
Full tasks require supporting normative contract PASS tables, issue decisions,
reviewed plan/leaf/fix/composite progress and final verification. Recorded prior
validation remains labeled prior evidence; finish additionally requires source-bound
verification with honest fresh/reuse provenance. Future undiscovered spec phases
keep the whole spec active even when all existing tasks have validated.

Test fault seams FINALIZATION_TEST_FAULT=before-journal-replace|after-journal-replace|
after-task-rename only terminate a process under FINALIZATION_TEST_ROOT in /tmp;
they cannot grant authorization or change evidence. Fixtures mutate disposable Git
repositories directly; the helper writes Git objects only inside isolated temporary recovery verification storage.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path
import re
import sys

from finalization_archive import (apply_moving_links, apply_pointer_plans, identity, integrity, move_no_replace, moving_link_plans,
                                  pointer_plans, resolve, snapshot, spec_eligible)
from finalization_evidence import assess, commit, evidence_file, git, remote_refs
from finalization_recovery import check_verified, prepare_recovery, recovery_plan
from finalization_support import (Refusal, atomic_write, dated, digest, encoded, expect_revision,
                                  edit_current_state, fault, field, locked, manifest, normalized_state, now, read_json, require, safe_path, section, text)


def plan_digest(document: dict) -> str:
    return digest(encoded({'repositories': document['repositories'], 'actions': document['actions']}))


def publish(journal: dict, path: Path, root: Path) -> list[str]:
    if journal['outcomes'].get('recovery') != 'verified':
        return []
    require(check_verified(journal, root, path), 'recovery-required', 'Verified self-contained recovery material is required before deletion receipts')
    revision = digest(path.read_bytes())
    receipts: list[str] = []
    for repository in journal['repositories']:
        common = safe_path(Path(repository['common_dir']))
        directory = safe_path(common / 'orchestrail-finalize')
        directory.mkdir(exist_ok=True)
        destination = safe_path(directory / (journal['id'] + '.json'))
        receipt = {'schema_version': 1, 'kind': 'task-finalization', 'id': journal['id'],
                   'task_path': journal['task_original'], 'project_root': str(root),
                   'repository': repository['path'], 'common_dir': str(common), 'journal_path': str(path),
                   'journal_revision': revision, 'plan_digest': journal['plan_digest'],
                   'authorization': journal['authorization'], 'integration': repository['integration'],
                   'candidates': repository['candidates'],
                   'recovery': next(record for record in journal['recovery'] if record['repository'] == repository['path'])}
        atomic_write(destination, encoded(receipt), common)
        receipts.append(str(destination))
    return receipts


def store(journal: dict, path: Path, root: Path) -> list[str]:
    if journal['outcomes'].get('recovery') == 'verified':
        require(check_verified(journal, root, path), 'recovery-required', 'Verified recovery material is unavailable')
    journal['plan_digest'] = plan_digest(journal)
    data = encoded(journal)
    if not path.exists() or path.read_bytes() != data:
        atomic_write(path, data, root, journal=True)
    return publish(journal, path, root)


def postconditions(journal: dict) -> list[dict]:
    receipts: list[dict] = []
    advertised: dict[str, dict[str, str]] = {}
    for action in journal['actions']:
        repo = Path(action['repository'])
        kind = action['kind']
        if kind == 'local-delete':
            actual = commit(repo, 'refs/heads/' + action['branch'])
            satisfied = actual is None
        elif kind == 'remote-delete':
            if str(repo) not in advertised:
                advertised[str(repo)] = remote_refs(repo)[0]
            actual = advertised[str(repo)].get(action['remote_ref'])
            satisfied = actual is None
        elif kind == 'refresh':
            actual = commit(repo, 'refs/heads/' + action['branch'])
            satisfied = actual == action['expected_tip']
        elif kind == 'checkout':
            actual = git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD', codes=(0, 1))
            satisfied = actual == action['branch'] and commit(repo, 'HEAD') == action['expected_tip']
        else:
            raise Refusal('journal-invalid', 'Unknown planned action kind')
        receipts.append({'id': action['id'], 'kind': kind, 'repository': str(repo), 'satisfied': satisfied,
                         'actual': actual, 'observed_at': now(), 'provenance': 'fresh read-only Git postcondition'})
    return receipts


def update_postconditions(journal: dict) -> None:
    fresh = postconditions(journal)
    previous = journal.get('action_receipts', [])
    without_time = lambda rows: [{key: value for key, value in row.items() if key != 'observed_at'} for row in rows]
    if previous and without_time(previous) != without_time(fresh):
        journal.setdefault('action_history', []).append(previous)
    journal['action_receipts'] = previous if without_time(previous) == without_time(fresh) else fresh
    journal['outcomes']['cleanup'] = 'complete' if all(row['satisfied'] for row in journal['action_receipts'] if row['kind'].endswith('delete')) else 'incomplete'
    journal['outcomes']['checkout'] = 'complete' if all(row['satisfied'] for row in journal['action_receipts'] if row['kind'] in {'checkout', 'refresh'}) else 'incomplete'


def accept_attestations(journal: dict, evidence: dict, task: Path) -> None:
    expected = {repo['path']: repo['integration']['tip'] for repo in journal['repositories']}
    current_hash = digest((task / 'state.md').read_bytes())
    saved_hash = digest((Path(journal['snapshot_path']) / 'task/state.md').read_bytes())
    accepted: dict = dict(journal.get('attestations', {}))
    stale: list[str] = []
    for row in evidence.get('attestations', []):
        require(isinstance(row, dict), 'attestation-invalid', 'Attestation must be an object')
        kind = row.get('kind')
        require(kind in {'knowledge', 'audit', 'verification', 'deployment'}, 'attestation-invalid', 'Unknown attestation kind')
        if row.get('source_tips') != expected:
            stale.append(str(kind) + ' source binding is stale; new verification/reconciliation evidence required')
            continue
        require(row.get('task_path') in {journal['task_original'], str(task)} and row.get('state_sha256') in {current_hash, saved_hash}
                and dated(row.get('observed_at')) and row.get('result') == 'pass' and isinstance(row.get('provenance'), str)
                and len(row['provenance'].strip()) >= 8 and row.get('source_tips') == expected,
                'attestation-invalid', f'{kind} attestation lacks dated task/state/source provenance')
        if kind == 'verification':
            commands = row.get('commands')
            require(isinstance(commands, list) and commands and isinstance(row.get('coverage'), str) and row['coverage'].strip(),
                    'verification-unverified', 'Verification needs command/results and stated coverage')
            for command in commands:
                require(isinstance(command, dict) and isinstance(command.get('argv'), list) and command['argv']
                        and all(isinstance(word, str) for word in command['argv']) and type(command.get('exit_code')) is int
                        and command['exit_code'] == 0 and isinstance(command.get('stdout'), str) and isinstance(command.get('stderr'), str),
                        'verification-unverified', 'Verification command/result is incomplete or failed')
            reuse = row.get('reuse')
            if reuse is not None:
                original_tips = {repo['path']: repo['candidates'][-1]['original_tip'] for repo in journal['repositories']}
                require(isinstance(reuse, dict) and reuse.get('permitted') is True and reuse.get('original_state_sha256') == saved_hash
                        and reuse.get('validated_tips') == original_tips and isinstance(reuse.get('limitations'), str) and len(reuse['limitations']) >= 12,
                        'verification-unverified', 'Reused prior evidence lacks original tips/state or runtime/dependency limits')
        if kind == 'deployment':
            require(row.get('revision') in expected.values() and isinstance(row.get('environment'), str) and row['environment'].strip(),
                    'deployment-unverified', 'Deployment needs dated revision and environment evidence')
        accepted[kind] = row
    # Existing receipts do not silently attest newly advanced source tips.
    accepted = {kind: row for kind, row in accepted.items() if row.get('source_tips') == expected}
    journal['attestations'] = accepted
    for kind in ('knowledge', 'audit', 'deployment'):
        journal['outcomes'][kind] = 'attested' if kind in accepted else 'unverified'
    journal['outcomes']['verification'] = 'attested' if 'verification' in accepted else 'unverified'
    journal['trust_limitations'] = [
        'Validation was recorded earlier; the helper has not rerun product tests.',
        'Semantic knowledge/audit, verification commands and deployment are externally attested; the helper verifies bindings and postconditions, not execution of arbitrary receipt commands.',
        'No telemetry is emitted. Optional unavailable logging/tools are not measured successes.',
        *(['Adopted preexisting archive: snapshots cover observed adoption bytes; earlier raw state is unavailable.'] if journal.get('adoption') else []),
    ]
    journal['trust_limitations'].extend(stale)
    if any(journal['outcomes'].get(kind) != 'attested' for kind in ('knowledge', 'audit', 'verification')):
        journal['complete'] = False
    for kind, row in accepted.items():
        if row.get('reuse'):
            journal['trust_limitations'].append(kind + ' prior evidence reuse: ' + row['reuse']['limitations'])


def archive(journal: dict, path: Path, root: Path, task: Path, spec: Path) -> tuple[Path, Path]:
    require(journal['outcomes']['cleanup'] == 'complete' and journal['outcomes']['checkout'] == 'complete'
            and journal['outcomes']['knowledge'] == 'attested' and journal['outcomes']['audit'] == 'attested',
            'required-operation-incomplete', 'Finish cleanup, knowledge reconciliation and independent audit before archival')
    task_destination = root / '.ai/tasks/completed' / Path(journal['task_original']).name
    spec_destination = root / '.ai/specs/completed' / Path(journal['spec_original']).name
    intent = journal.get('archive_intent')
    if not intent:
        eligible, reason = spec_eligible(root, task, spec, journal)
        safe_path(task_destination, root)
        safe_path(spec_destination, root)
        require(task == task_destination or not task_destination.exists(), 'archive-collision', 'Task archive destination already exists')
        require(spec == spec_destination or not eligible or not spec_destination.exists(), 'archive-collision', 'Spec archive destination already exists')
        # Destination directories are created only after all collision checks.
        task_destination.parent.mkdir(parents=True, exist_ok=True)
        if eligible:
            spec_destination.parent.mkdir(parents=True, exist_ok=True)
        pointers = pointer_plans(root, journal, task_destination, spec_destination, eligible)
        moving_links = moving_link_plans(root, journal, task, spec, task_destination, spec_destination if eligible else spec)
        intent = {'task_destination': str(task_destination), 'spec_destination': str(spec_destination),
                  'move_spec': eligible, 'spec_status': reason, 'current_links': pointers, 'moving_links': moving_links}
        journal['archive_intent'] = intent
        store(journal, path, root)
    else:
        require(intent['task_destination'] == str(task_destination) and intent['spec_destination'] == str(spec_destination), 'journal-invalid', 'Archive intent escapes canonical destinations')
    if task != task_destination:
        move_no_replace(task, task_destination, root)
        task = task_destination
        fault('after-task-rename', root)
    journal['task_current'] = str(task)
    if intent['move_spec'] and spec != spec_destination:
        eligible_now, reason_now = spec_eligible(root, task, spec, journal)
        if not eligible_now:
            # The task rename is durable progress; only downgrade the now-unsafe spec move.
            intent['move_spec'] = False
            intent['spec_status'] = reason_now
            intent['current_links'] = pointer_plans(root, journal, task_destination, spec_destination, False)
            intent['moving_links'] = moving_link_plans(root, journal, task, spec, task_destination, spec)
            store(journal, path, root)
    if intent['move_spec']:
        if spec != spec_destination:
            move_no_replace(spec, spec_destination, root)
            spec = spec_destination
        # Only this current-location pointer changes; original raw state is recoverable.
        state_path = task / 'state.md'
        value = text(state_path)
        pointer = field(value, 'spec_path', top=True)
        require(pointer in {Path(journal['spec_original']).relative_to(root).as_posix(), spec.relative_to(root).as_posix()},
                'protected-content-changed', 'Unexpected current spec pointer')
        updated = edit_current_state(value, spec=spec.relative_to(root).as_posix())
        if updated != value.encode():
            atomic_write(state_path, updated, root)
    apply_moving_links(root, journal, task, spec)
    apply_pointer_plans(root, intent['current_links'])
    journal['spec_current'] = str(spec)
    journal['outcomes']['archival'] = 'complete'
    journal['outcomes']['spec_archival'] = intent['spec_status']
    integrity(root, task, spec, journal)
    return task, spec


def finish(journal: dict, root: Path, task: Path, spec: Path) -> None:
    required = {'validation': 'complete', 'integration': 'complete', 'checkout': 'complete', 'cleanup': 'complete',
                'knowledge': 'attested', 'archival': 'complete', 'audit': 'attested', 'verification': 'attested', 'recovery': 'verified'}
    require(all(journal['outcomes'].get(key) == value for key, value in required.items()),
            'required-operation-incomplete', 'Required finalization operations remain incomplete')
    contract = section(text(spec), '## Delivery Contract')
    if field(contract, 'deployment') == 'required':
        require(journal['outcomes']['deployment'] == 'attested', 'deployment-unverified', 'Required deployment has no dated revision/environment evidence')
    for plan in journal.get('archive_intent', {}).get('current_links', []):
        require(digest((root / plan['path']).read_bytes()) == plan['after_sha256'], 'current-link-changed', 'Current links no longer match archive receipt')
    integrity(root, task, spec, journal)
    state_path = task / 'state.md'
    value = text(state_path)
    updated = edit_current_state(value, phase='complete')
    if updated != value.encode():
        atomic_write(state_path, updated, root)
    require(re.search(r'^- finalization: complete$', section(text(state_path), '## Phases'), re.M), 'required-operation-incomplete', 'Finalization phase marker was not persisted')
    integrity(root, task, spec, journal)
    journal['complete'] = True


def response(command: str, status: str, root: Path, task: Path, spec: Path, path: Path,
             current: dict, journal: dict | None = None, receipts: list[str] | None = None) -> dict:
    original_task = Path(journal['task_original']) if journal else root / '.ai/tasks/todo' / task.name if task.parent.name == 'completed' else task
    result = {'schema_version': 1, 'command': command, 'status': status, 'failures': [],
              'resolution': {'task_path': str(task), 'spec_path': str(spec),
                             'original_task_path': str(original_task)},
              'id': journal['id'] if journal else identity(root, original_task), 'journal_path': str(path),
              'revision': digest(path.read_bytes()) if path.exists() else 'absent', 'complete': False}
    result.update(current)
    if journal:
        for key in ('repositories', 'actions', 'outcomes', 'manifest', 'snapshot_path', 'plan_digest', 'action_receipts',
                    'validation_evidence', 'trust_limitations', 'attestations', 'action_history', 'recovery', 'recovery_actions'):
            if key in journal:
                result[key] = journal[key]
        result['complete'] = journal.get('complete', False) if command == 'finish' else False
    else:
        result['plan_digest'] = plan_digest(current)
    if 'recovery_actions' not in result:
        result['recovery_actions'] = recovery_plan(path, result['repositories'])
    result['outcomes'].setdefault('recovery', 'required')
    if receipts is not None:
        result['hook_receipts'] = receipts
    return result


def execute(args: argparse.Namespace) -> dict:
    root = safe_path(Path(args.root))
    require(root.is_dir(), 'root-invalid', 'Explicit project root does not exist')
    evidence = evidence_file(Path(args.evidence) if args.evidence else None)
    selected = Path(args.target)
    selected_absolute = safe_path(selected if selected.is_absolute() else root / selected, root)
    adoption = evidence.get('adoption')
    if isinstance(adoption, dict) and str(selected_absolute) == adoption.get('original_task_path') and not selected_absolute.exists():
        selected = Path(adoption.get('task_path', ''))
    task, spec, path, prior = resolve(root, selected)
    if prior is None and task.parent == root / '.ai/tasks/completed':
        require(isinstance(adoption, dict) and adoption.get('task_path') == str(task)
                and adoption.get('original_task_path') == str(root / '.ai/tasks/todo' / task.name)
                and adoption.get('original_spec_path') == str(root / '.ai/specs' / spec.name)
                and dated(adoption.get('observed_at')) and isinstance(adoption.get('provenance'), str)
                and len(adoption['provenance']) >= 8 and adoption.get('task_files') == manifest(task)
                and adoption.get('spec_sha256') == digest(spec.read_bytes()),
                'adoption-evidence-missing', 'Preexisting archives need explicit dated original-path/manifest/provenance evidence')
    if prior:
        integrity(root, task, spec, prior)
        if prior['outcomes'].get('recovery') == 'verified':
            require(check_verified(prior, root, path), 'recovery-required', 'Recovery material is unavailable')
    current = assess(root, task, spec, evidence, prior)
    if args.command == 'inspect' or args.dry_run:
        observed = copy.deepcopy(prior) if prior else None
        if observed:
            observed.update({key: current[key] for key in ('repositories', 'actions', 'validation_evidence')})
            update_postconditions(observed)
            accept_attestations(observed, evidence, task)
        return response(args.command, 'ready', root, task, spec, path, current, observed)
    require(args.authorize, 'authorization-required', 'An explicit invocation of phase-finalize for this task is required')
    with locked(path.with_name('journal.lock'), root):
        expect_revision(path, args.expected_revision)
        # Re-resolve and re-read under the lock; stale snapshots cannot authorize writes.
        task, spec, path, prior = resolve(root, selected)
        if prior:
            integrity(root, task, spec, prior)
        current = assess(root, task, spec, evidence, prior)
        if args.command == 'prepare':
            if prior:
                require(prior['authorization']['task_path'] == prior['task_original'], 'authorization-required', 'Journal scope authorization differs')
                journal = prior
                journal.update({key: current[key] for key in ('repositories', 'actions', 'validation_evidence')})
            else:
                snapshot_path = path.parent / 'snapshot'
                stored_manifest = snapshot(root, task, spec, snapshot_path)
                original_task = Path(adoption['original_task_path']) if isinstance(adoption, dict) and task.parent.name == 'completed' else task
                original_spec = Path(adoption['original_spec_path']) if original_task != task else spec
                journal = {'schema_version': 1, 'id': identity(root, original_task), 'project_root': str(root),
                           'task_original': str(original_task), 'task_current': str(task), 'spec_original': str(original_spec), 'spec_current': str(spec),
                           'snapshot_path': str(snapshot_path), 'manifest': stored_manifest,
                           'original_state_sha256': digest(normalized_state(text(task / 'state.md'))),
                           'authorization': {'invocation': 'phase-finalize', 'task_path': str(original_task), 'cleanup': True},
                           'created_at': now(), 'complete': False, **current}
            if isinstance(adoption, dict) and task.parent.name == 'completed':
                journal['adoption'] = adoption
                journal['trust_limitations'] = ['Adopted preexisting archive: snapshots preserve bytes observed at adoption; pre-archive raw bytes and prior execution are not independently recoverable or verified.']
            update_postconditions(journal)
            recovered = prepare_recovery(journal, root, path)
            receipts = store(journal, path, root)
            return response(args.command, 'prepared' if recovered else 'recovery-required', root, task, spec, path, current, journal, receipts)
        require(prior is not None, 'journal-missing', 'Run prepare before recording or archiving')
        require(prior['outcomes'].get('recovery') == 'verified' and check_verified(prior, root, path), 'recovery-required', 'Create and verify the exact recovery pack plan before cleanup or archival')
        journal = prior
        journal.update({key: current[key] for key in ('repositories', 'actions', 'validation_evidence')})
        update_postconditions(journal)
        accept_attestations(journal, evidence, task)
        if args.command == 'knowledge':
            require(journal['outcomes']['knowledge'] == 'attested' and journal['outcomes']['audit'] == 'attested',
                    'knowledge-unverified', 'Dated independent reconciliation and audit evidence are required')
        if args.command == 'archive':
            task, spec = archive(journal, path, root, task, spec)
        elif args.command == 'finish':
            finish(journal, root, task, spec)
        receipts = store(journal, path, root)
        status = 'complete' if args.command == 'finish' else 'archived' if args.command == 'archive' else 'recorded'
        return response(args.command, status, root, task, spec, path, current, journal, receipts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('inspect', 'prepare', 'record', 'knowledge', 'archive', 'finish'))
    parser.add_argument('target')
    parser.add_argument('--root', required=True)
    parser.add_argument('--evidence')
    parser.add_argument('--authorize', action='store_true')
    parser.add_argument('--expected-revision')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        result = execute(args)
    except Refusal as error:
        result = {'schema_version': 1, 'command': args.command, 'status': 'blocked', 'complete': False,
                  'failures': [{'check': error.check, 'reason': error.reason}]}
    except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
        result = {'schema_version': 1, 'command': args.command, 'status': 'blocked', 'complete': False,
                  'failures': [{'check': 'invalid-or-unavailable-state', 'reason': str(error)}]}
    sys.stdout.buffer.write(encoded(result))
    return 1 if result['status'] == 'blocked' else 0


if __name__ == '__main__':
    raise SystemExit(main())
