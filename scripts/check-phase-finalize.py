#!/usr/bin/env python3
"""Behavioral finalization checks; creates and mutates disposable repositories only.

Run: python3 scripts/check-phase-finalize.py [unittest selection ...]
The standalone suite is intentionally outside the frozen validator inventory.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone

HELPER = Path(__file__).with_name('phase-finalize.py')
SUPPORT = '''## Solution Design
### Invariants
- Preserve original product history.
### Off-limits
- Unrelated local work.
### Acceptance Criteria
- Product delivery is integrated.
## Contract Check
### Invariants
| Invariant | Status |
|---|---|
| Preserve original product history. | PASS: original commit is reachable. |
### Acceptance Criteria
| Criterion | Status |
|---|---|
| Product delivery is integrated. | PASS: integration fixture verified. |
### Off-limits
| Constraint | Status |
|---|---|
| Unrelated local work. | PASS: fixture baseline is intact. |
## Code Review
### Findings
None
### Summary
0 critical, 0 important, 0 optional; independently reviewed.
## Issue List
### Approved
None
### Deferred
None
## Fix-Tasks
fixes-created: complete
fixes-count: 0
Created: none
## Execution Report
Final verification: PASS — isolated product behavior checks after the final change.
'''
QUICK = '''## Contract (quick)
### Invariants
- Preserve original product history.
### Off-limits
- Unrelated local work.
### Acceptance Criteria
- Product delivery is integrated.
## TDD (quick)
level: integration
tests: product_delivery_is_integrated
red-observed: yes — product assertion failed before implementation
green-observed: yes — product assertion passed after implementation
## Inline Fixes
Approved: none
Review: complete — no unresolved findings
'''



class FinalizationChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='finalization-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root
        self.init_repo(self.repo)
        self.base = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'checkout', '-b', 'feat/delivery')
        (self.repo / 'product').write_text('delivered\n')
        self.git(self.repo, 'add', 'product')
        self.git(self.repo, 'commit', '-m', 'feat: deliver product')
        self.tip = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'checkout', 'main')
        self.git(self.repo, 'merge', '--no-ff', 'feat/delivery', '-m', 'merge: integrate product')
        self.task = self.root / '.ai/tasks/todo/task-delivery'
        self.task.mkdir(parents=True)
        self.spec = self.root / '.ai/specs/delivery.md'
        self.spec.parent.mkdir(parents=True)
        self.spec.write_text('# Delivery\n\n## Requirements\n- Preserve product scope.\n')
        self.write_state()
        (self.task / 'plan.md').write_text('## Subtasks\n| ID | Name | Depends On | Status |\n|---|---|---|---|\n| T-01 | Deliver | — | reviewed |\n')
        leaf = self.task / 'T-01-deliver'
        leaf.mkdir()
        (leaf / 'description.md').write_text('## Goal\nDeliver product.\n')
        (self.task / 'state-archive.md').write_text('Historical review and failing-test evidence.\n')
        memory = self.root / '.ai/memory'
        memory.mkdir()
        (memory / 'state.md').write_text('## Active Tasks\n- [Delivery](../tasks/todo/task-delivery/state.md)\n')
        self.evidence = self.root / 'evidence.json'
        self.put_evidence()

    def init_repo(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self.git(path, 'init', '-b', 'main')
        self.git(path, 'config', 'user.name', 'Fixture Author')
        self.git(path, 'config', 'user.email', 'fixture@example.invalid')
        self.git(path, 'config', 'orchestrail.fixture', 'true')
        (path / '.gitignore').write_text('.ai/\nevidence.json\n')
        (path / 'baseline').write_text('original\n')
        self.git(path, 'add', '.gitignore', 'baseline')
        self.git(path, 'commit', '-m', 'chore: establish baseline')

    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(['git', *args], cwd=repo, text=True, capture_output=True,
                                env=self.environment())
        if result.returncode:
            self.fail(f'fixture git {args}: {result.stderr}')
        return result.stdout.strip()

    def environment(self) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        env.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
                    'FINALIZATION_TEST_ROOT': str(self.root)})
        return env

    def write_state(self, extra: str = '', flow: str = 'full') -> None:
        self.state_text = f'''spec_path: .ai/specs/delivery.md
flow: {flow}
base_branch: main
## Phases
- discovery: complete
- execution: complete
- validation: complete
## Subtask Progress
T-01 | Deliver product | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independently reviewed
  target_files: product
  blocker: none
  notes: tdd: red digest — product behavior verified
  branch: feat/delivery
  base_branch: main
  base_commit: {self.base}
  commits: {self.tip} feat: deliver product
{extra}''' + SUPPORT
        (self.task / 'state.md').write_text(self.state_text)

    def put_evidence(self, **fields: object) -> None:
        data = {'schema_version': 1, 'provenance': {'kind': 'controlled-fixture',
                'root': str(self.root), 'observed_at': datetime.now(timezone.utc).isoformat()},
                'pull_requests': [], 'attestations': []}
        data.update(fields)
        self.evidence.write_text(json.dumps(data))

    def call(self, command: str = 'inspect', target: Path | None = None,
             args: tuple[str, ...] = (), fault: str = '') -> dict:
        env = self.environment()
        if fault:
            env['FINALIZATION_TEST_FAULT'] = fault
        result = subprocess.run([sys.executable, str(HELPER), command,
                                 str(target or self.task), '--root', str(self.root),
                                 '--evidence', str(self.evidence), *args], text=True,
                                capture_output=True, env=env)
        if fault and result.returncode < 0:
            return {'status': 'interrupted'}
        try:
            document = json.loads(result.stdout)
        except ValueError:
            self.fail(f'helper must return JSON: {result.returncode}: {result.stderr}: {result.stdout}')
        self.assertIn('status', document)
        return document

    def blocked(self, result: dict, code: str) -> None:
        self.assertEqual('blocked', result['status'], result)
        self.assertIn(code, [item['check'] for item in result['failures']], result)

    def prepare(self) -> dict:
        result = self.call('prepare', args=('--authorize', '--expected-revision', 'absent'))
        self.assertEqual('prepared', result['status'], result)
        return result

    def checkpoint(self, command: str, prior: dict, *args: str, fault: str = '') -> dict:
        return self.call(command, args=('--authorize', '--expected-revision', prior['revision'], *args), fault=fault)

    def clean_actions(self, prior: dict) -> dict:
        for action in prior['actions']:
            if action['kind'] == 'local-delete':
                self.git(Path(action['repository']), 'branch', '-d', action['branch'])
        return self.checkpoint('record', prior)

    def attested(self, prior: dict) -> dict:
        self.put_evidence(attestations=[{'kind': kind, 'observed_at': datetime.now(timezone.utc).isoformat(),
            'task_path': str(self.task), 'state_sha256': hashlib.sha256((self.task / 'state.md').read_bytes()).hexdigest(),
            'result': 'pass', 'provenance': 'independent fixture reviewer'} for kind in ('knowledge', 'audit')])
        result = self.checkpoint('knowledge', prior)
        self.assertEqual('recorded', result['status'], result)
        return result

    def test_integrated_original_commit_returns_exact_deletion_plan(self) -> None:
        result = self.call()
        self.assertEqual('ready', result['status'], result)
        action = next(item for item in result['actions'] if item['kind'] == 'local-delete')
        self.assertEqual(['git', '-C', str(self.repo), 'branch', '-d', 'feat/delivery'], action['command'])
        self.assertEqual(self.tip, action['expected_tip'])
        self.assertEqual(self.tip, result['repositories'][0]['candidates'][0]['original_tip'])
        self.assertEqual('unverified', result['outcomes']['deployment'])
        self.assertEqual(self.tip, self.git(self.repo, 'rev-parse', 'feat/delivery'))

    def test_dry_run_prepare_is_byte_for_byte_read_only(self) -> None:
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = self.call('prepare', args=('--dry-run',))
        self.assertEqual('ready', result['status'], result)
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_spec_input_selects_exact_task_without_guessing(self) -> None:
        result = self.call(target=self.spec)
        self.assertEqual('ready', result['status'], result)
        self.assertEqual(str(self.task), result['resolution']['task_path'])

    def test_duplicate_task_spec_mapping_is_ambiguous(self) -> None:
        other = self.task.parent / 'other-delivery'
        other.mkdir()
        (other / 'state.md').write_text(self.state_text)
        self.blocked(self.call(target=self.spec), 'task-ambiguous')

    def test_validation_not_complete_blocks_mutation(self) -> None:
        (self.task / 'state.md').write_text(self.state_text.replace('- validation: complete', '- validation: in-progress'))
        self.blocked(self.call('prepare', args=('--authorize', '--expected-revision', 'absent')), 'validation-incomplete')

    def test_composite_without_integration_review_blocks(self) -> None:
        self.write_state(extra='[composite] T-02 | Bundle | rollup: done | integration-validation: not-started\n  children: T-01\n')
        self.blocked(self.call(), 'composite-incomplete')

    def test_quick_flow_requires_its_independent_review(self) -> None:
        self.write_state(flow='quick')
        self.blocked(self.call(), 'quick-contract-missing')

    def test_recorded_short_original_sha_is_not_accepted(self) -> None:
        (self.task / 'state.md').write_text(self.state_text.replace(self.tip, self.tip[:8]))
        self.blocked(self.call(), 'original-sha-invalid')

    def test_unmerged_original_commit_blocks_even_with_missing_branch(self) -> None:
        self.git(self.repo, 'checkout', '-b', 'feat/unmerged', self.base)
        (self.repo / 'undelivered').write_text('scope\n')
        self.git(self.repo, 'add', 'undelivered')
        self.git(self.repo, 'commit', '-m', 'feat: add pending scope')
        pending = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'checkout', 'main')
        self.git(self.repo, 'branch', '-D', 'feat/unmerged')
        (self.task / 'state.md').write_text(self.state_text.replace(self.tip, pending).replace('feat/delivery', 'feat/unmerged'))
        self.blocked(self.call(), 'integration-unverified')

    def test_changed_branch_tip_is_not_candidate_for_deletion(self) -> None:
        self.git(self.repo, 'checkout', 'feat/delivery')
        (self.repo / 'later').write_text('unrelated\n')
        self.git(self.repo, 'add', 'later')
        self.git(self.repo, 'commit', '-m', 'feat: retain later work')
        self.git(self.repo, 'checkout', 'main')
        self.blocked(self.call(), 'branch-tip-changed')

    def test_dirty_tracked_tree_blocks_cleanup(self) -> None:
        (self.repo / 'baseline').write_text('local edits\n')
        self.blocked(self.call(), 'worktree-dirty')

    def test_checked_out_candidate_in_other_worktree_blocks(self) -> None:
        self.git(self.repo, 'worktree', 'add', str(self.root / 'linked'), 'feat/delivery')
        self.blocked(self.call(), 'branch-in-worktree')

    def test_protected_candidate_cannot_be_deleted(self) -> None:
        self.git(self.repo, 'config', 'orchestrail.protectedBranch', 'feat/delivery')
        self.blocked(self.call(), 'branch-protected')

    def test_prepare_requires_explicit_invocation_authorization(self) -> None:
        self.blocked(self.call('prepare', args=('--expected-revision', 'absent')), 'authorization-required')

    def test_prepare_writes_recovery_and_bound_hook_receipt(self) -> None:
        result = self.prepare()
        journal = Path(result['journal_path'])
        self.assertEqual(self.root / '.ai/context/finalization' / result['id'] / 'journal.json', journal)
        document = json.loads(journal.read_text())
        self.assertEqual(self.tip, document['repositories'][0]['candidates'][0]['original_tip'])
        self.assertEqual(['git', '-C', str(self.repo), 'branch', 'feat/delivery', self.tip], document['repositories'][0]['candidates'][0]['recovery_command'])
        receipt = json.loads(Path(result['hook_receipts'][0]).read_text())
        self.assertEqual(hashlib.sha256(journal.read_bytes()).hexdigest(), receipt['journal_revision'])
        self.assertEqual(result['plan_digest'], receipt['plan_digest'])
        self.assertEqual(self.tip, self.git(self.repo, 'rev-parse', 'feat/delivery'))

    def test_stale_expected_revision_rejects_replay(self) -> None:
        self.prepare()
        self.blocked(self.call('record', args=('--authorize', '--expected-revision', '0' * 64)), 'revision-conflict')

    def test_record_rechecks_surviving_refs_instead_of_claiming_cleanup(self) -> None:
        prior = self.prepare()
        result = self.checkpoint('record', prior)
        self.assertEqual('recorded', result['status'], result)
        self.assertEqual('incomplete', result['outcomes']['cleanup'])
        self.assertFalse(result['complete'])

    def test_deleted_ref_is_recorded_only_after_actual_postcondition(self) -> None:
        result = self.clean_actions(self.prepare())
        self.assertEqual('recorded', result['status'], result)
        self.assertEqual('complete', result['outcomes']['cleanup'])
        self.assertFalse(result['complete'])

    def test_original_audit_field_change_rejects_resume(self) -> None:
        prior = self.prepare()
        (self.task / 'state.md').write_text(self.state_text.replace('tdd: red digest', 'tdd: rewritten digest'))
        self.blocked(self.checkpoint('record', prior), 'protected-content-changed')

    def test_journal_lock_serializes_writers(self) -> None:
        prior = self.prepare()
        lock = Path(prior['journal_path']).with_name('journal.lock')
        with lock.open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.blocked(self.checkpoint('record', prior), 'journal-locked')

    def test_archive_collision_preserves_original_and_destination(self) -> None:
        prior = self.attested(self.clean_actions(self.prepare()))
        destination = self.root / '.ai/tasks/completed' / self.task.name
        destination.mkdir(parents=True)
        (destination / 'retain').write_text('existing\n')
        self.blocked(self.checkpoint('archive', prior), 'archive-collision')
        self.assertTrue((self.task / 'state.md').exists())
        self.assertEqual('existing\n', (destination / 'retain').read_text())

    def test_archive_preserves_manifest_audit_and_relocates_current_links(self) -> None:
        original = {str(p.relative_to(self.task)): p.read_bytes() for p in self.task.rglob('*') if p.is_file()}
        spec_original = self.spec.read_bytes()
        prior = self.attested(self.clean_actions(self.prepare()))
        result = self.checkpoint('archive', prior)
        self.assertEqual('archived', result['status'], result)
        destination = self.root / '.ai/tasks/completed' / self.task.name
        self.assertFalse(self.task.exists())
        for name, content in original.items():
            expected = content.replace(b'spec_path: .ai/specs/delivery.md', b'spec_path: .ai/specs/completed/delivery.md') if name == 'state.md' else content
            self.assertEqual(expected, (destination / name).read_bytes())
        snapshot = Path(result['snapshot_path'])
        for name, content in original.items():
            self.assertEqual(content, (snapshot / 'task' / name).read_bytes())
        self.assertEqual(spec_original, (self.root / '.ai/specs/completed/delivery.md').read_bytes())
        self.assertIn('../tasks/completed/task-delivery/state.md', (self.root / '.ai/memory/state.md').read_text())
        self.assertEqual(set(original), set(result['manifest']['task_files']))
        self.assertFalse(result['complete'])
        finished = self.checkpoint('finish', result)
        self.assertEqual('complete', finished['status'], finished)
        self.assertEqual('unverified', finished['outcomes']['deployment'])

    def test_old_task_path_resumes_after_archive_and_repeated_finish(self) -> None:
        prior = self.attested(self.clean_actions(self.prepare()))
        result = self.checkpoint('archive', prior)
        self.assertEqual('archived', result['status'], result)
        resumed = self.call()
        self.assertEqual('ready', resumed['status'], resumed)
        self.assertEqual(str(self.root / '.ai/tasks/completed' / self.task.name), resumed['resolution']['task_path'])
        first = self.checkpoint('finish', result)
        self.assertEqual('complete', first['status'], first)
        again = self.checkpoint('finish', first)
        self.assertEqual('complete', again['status'], again)
        self.assertEqual(first['revision'], again['revision'])

    def test_unfinished_other_phase_keeps_whole_spec_active(self) -> None:
        other = self.task.parent / 'task-later-phase'
        other.mkdir()
        (other / 'state.md').write_text('spec_path: .ai/specs/delivery.md\nflow: full\n## Phases\n- validation: not-started\n')
        prior = self.attested(self.clean_actions(self.prepare()))
        result = self.checkpoint('archive', prior)
        self.assertEqual('archived', result['status'], result)
        self.assertTrue(self.spec.exists())
        self.assertEqual('active-other-phases', result['outcomes']['spec_archival'])

    def test_symlink_in_task_is_refused_without_following_it(self) -> None:
        outside = self.root / 'outside'
        outside.write_text('retain\n')
        (self.task / 'linked').symlink_to(outside)
        self.blocked(self.call(), 'unsafe-path')

    def test_interrupted_atomic_journal_write_leaves_previous_valid_revision(self) -> None:
        prior = self.prepare()
        before = Path(prior['journal_path']).read_bytes()
        result = self.checkpoint('record', prior, fault='before-journal-replace')
        self.assertEqual('interrupted', result['status'], result)
        self.assertEqual(before, Path(prior['journal_path']).read_bytes())
        self.assertEqual('recorded', self.checkpoint('record', prior)['status'])

    def test_interrupted_task_archive_resumes_from_old_path(self) -> None:
        prior = self.attested(self.clean_actions(self.prepare()))
        result = self.checkpoint('archive', prior, fault='after-task-rename')
        self.assertEqual('interrupted', result['status'], result)
        current = self.call()
        self.assertEqual('ready', current['status'], current)
        resumed = self.call('archive', args=('--authorize', '--expected-revision', current['revision']))
        self.assertEqual('archived', resumed['status'], resumed)

    def test_finish_refuses_unattested_knowledge_and_audit(self) -> None:
        prior = self.clean_actions(self.prepare())
        self.blocked(self.checkpoint('finish', prior), 'required-operation-incomplete')

    def test_remote_plan_uses_exact_live_lease_and_failed_delete_stays_incomplete(self) -> None:
        remote = self.root / 'origin.git'
        self.git(self.root, 'init', '--bare', str(remote))
        self.git(self.repo, 'remote', 'add', 'origin', str(remote))
        self.git(self.repo, 'push', 'origin', 'main', 'feat/delivery')
        self.git(remote, 'symbolic-ref', 'HEAD', 'refs/heads/main')
        result = self.prepare()
        action = next(a for a in result['actions'] if a['kind'] == 'remote-delete')
        self.assertEqual(['git', '-C', str(self.repo), 'push', f'--force-with-lease=refs/heads/feat/delivery:{self.tip}', 'origin', ':refs/heads/feat/delivery'], action['command'])
        self.git(self.repo, 'branch', '-d', 'feat/delivery')
        recorded = self.checkpoint('record', result)
        self.assertEqual('recorded', recorded['status'], recorded)
        self.assertEqual('incomplete', recorded['outcomes']['cleanup'])
        self.assertIn('remote-delete', [r['kind'] for r in recorded['action_receipts'] if not r['satisfied']])

    def test_remote_tip_drift_is_not_hidden_by_stale_tracking_ref(self) -> None:
        remote = self.root / 'origin.git'
        self.git(self.root, 'init', '--bare', str(remote))
        self.git(self.repo, 'remote', 'add', 'origin', str(remote))
        self.git(self.repo, 'push', 'origin', 'main', 'feat/delivery')
        self.git(remote, 'symbolic-ref', 'HEAD', 'refs/heads/main')
        prior = self.prepare()
        self.git(self.repo, 'push', 'origin', 'main:feat/delivery')
        self.blocked(self.checkpoint('record', prior), 'remote-tip-changed')

    def test_caller_pr_claim_without_authority_cannot_prove_squash(self) -> None:
        self.git(self.repo, 'checkout', '-b', 'feat/squash', self.base)
        (self.repo / 'squash').write_text('rewrite\n')
        self.git(self.repo, 'add', 'squash')
        self.git(self.repo, 'commit', '-m', 'feat: deliver rewritten product')
        original = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'checkout', 'main')
        self.git(self.repo, 'merge', '--squash', 'feat/squash')
        self.git(self.repo, 'commit', '-m', 'feat: integrate rewritten product')
        merged = self.git(self.repo, 'rev-parse', 'HEAD')
        (self.task / 'state.md').write_text(self.state_text.replace(self.tip, original).replace('feat/delivery', 'feat/squash').replace('## Solution Design', '  pr: https://example.invalid/pull/1\n## Solution Design'))
        self.put_evidence(provenance={'kind': 'caller'}, pull_requests=[{'url': 'https://example.invalid/pull/1', 'repository': str(self.repo), 'head_ref': 'feat/squash', 'head_sha': original, 'base_ref': 'main', 'state': 'MERGED', 'merge_commit': merged}])
        self.blocked(self.call(), 'pr-authority-unverified')

    def test_authoritative_matching_squash_receipt_requires_reachable_merge(self) -> None:
        self.git(self.repo, 'checkout', '-b', 'feat/squash', self.base)
        (self.repo / 'squash').write_text('rewrite\n')
        self.git(self.repo, 'add', 'squash')
        self.git(self.repo, 'commit', '-m', 'feat: deliver rewritten product')
        original = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'checkout', 'main')
        self.git(self.repo, 'merge', '--squash', 'feat/squash')
        self.git(self.repo, 'commit', '-m', 'feat: integrate rewritten product')
        merged = self.git(self.repo, 'rev-parse', 'HEAD')
        (self.task / 'state.md').write_text(self.state_text.replace(self.tip, original).replace('feat/delivery', 'feat/squash').replace('## Solution Design', '  pr: https://example.invalid/pull/1\n## Solution Design'))
        receipt = {'url': 'https://example.invalid/pull/1', 'repository': str(self.repo), 'head_ref': 'feat/squash', 'head_sha': original, 'base_ref': 'main', 'state': 'MERGED', 'merge_commit': merged, 'merged_at': datetime.now(timezone.utc).isoformat()}
        self.put_evidence(pull_requests=[receipt])
        result = self.call()
        self.assertEqual('ready', result['status'], result)
        self.assertEqual('pr', result['repositories'][0]['candidates'][0]['integration_method'])
        receipt['merge_commit'] = original
        self.put_evidence(pull_requests=[receipt])
        self.blocked(self.call(), 'integration-unverified')

    def test_missing_supporting_review_sections_block_completed_phase_marker(self) -> None:
        (self.task / 'state.md').write_text(self.state_text.split('## Code Review')[0])
        self.blocked(self.call(), 'validation-evidence-missing')

    def test_approved_unresolved_fix_blocks_completed_phase_marker(self) -> None:
        text = self.state_text.replace('### Approved\nNone', '### Approved\n1. Repair missing delivery.')
        text = text.replace('fixes-count: 0\nCreated: none', 'fixes-count: 1\nCreated: T-02-fix-delivery')
        (self.task / 'state.md').write_text(text)
        self.blocked(self.call(), 'approved-fix-unresolved')

    def test_failed_acceptance_criterion_blocks_despite_recorded_deferral(self) -> None:
        text = self.state_text.replace('PASS: integration fixture verified.', 'FAIL: delivery is absent.')
        text = text.replace('### Deferred\nNone', '### Deferred\n1. Missing delivery; owner deferred.')
        (self.task / 'state.md').write_text(text)
        self.blocked(self.call(), 'contract-failed')

    def test_open_issue_decision_blocks_completed_phase_marker(self) -> None:
        text = self.state_text.replace('### Findings\nNone', '### Findings\n1. Missing delivery, important.')
        text = text.replace('0 critical, 0 important, 0 optional', '0 critical, 1 important, 0 optional')
        (self.task / 'state.md').write_text(text)
        self.blocked(self.call(), 'issue-decision-incomplete')

    def test_unmatched_normative_requirement_does_not_count_as_verified(self) -> None:
        text = self.state_text.replace('### Acceptance Criteria\n- Product delivery is integrated.', '### Acceptance Criteria\n- Product delivery is integrated.\n- Owner receives a delivery receipt.')
        (self.task / 'state.md').write_text(text)
        self.blocked(self.call(), 'contract-coverage-incomplete')

    def test_full_quick_contract_and_review_allow_explicit_delivery_record(self) -> None:
        self.write_state(flow='quick')
        text = self.state_text.replace('## Subtask Progress\nT-01 | Deliver product | atomic-tests: green | atomic-execution: complete | atomic-validation: complete', '## Delivery')
        text = text.replace('## Fix-Tasks\nfixes-created: complete\nfixes-count: 0\nCreated: none\n', '')
        (self.task / 'state.md').write_text(text + QUICK)
        result = self.call()
        self.assertEqual('ready', result['status'], result)
        self.assertEqual('complete', result['outcomes']['validation'])

    def test_composite_with_all_children_and_integration_review_is_ready(self) -> None:
        self.write_state(extra='[composite] T-02 | Bundle | rollup: done | integration-validation: complete\n  children: T-01\n  blocker: none\n  notes: integration checks passed independently\n')
        (self.task / 'plan.md').write_text('## Subtasks\n| ID | Name | Depends On | Status |\n|---|---|---|---|\n| T-01 | Deliver | — | reviewed |\n| T-02 | Bundle | T-01 | reviewed |\n')
        self.assertEqual('ready', self.call()['status'])

    def test_stack_pr_merged_into_feature_is_not_integration_delivery(self) -> None:
        self.git(self.repo, 'checkout', '-b', 'feat/next', 'feat/delivery')
        (self.repo / 'next').write_text('second stack leaf\n')
        self.git(self.repo, 'add', 'next')
        self.git(self.repo, 'commit', '-m', 'feat: extend delivery')
        tip = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'checkout', 'feat/delivery')
        self.git(self.repo, 'merge', '--no-ff', 'feat/next', '-m', 'merge: integrate stacked leaf')
        feature_merge = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'checkout', 'main')
        text = self.state_text.replace(self.tip, tip).replace('branch: feat/delivery', 'branch: feat/next')
        (self.task / 'state.md').write_text(text.replace('## Solution Design', '  pr: https://example.invalid/pull/2\n## Solution Design'))
        self.put_evidence(pull_requests=[{'url': 'https://example.invalid/pull/2', 'repository': str(self.repo), 'head_ref': 'feat/next', 'head_sha': tip, 'base_ref': 'feat/delivery', 'state': 'MERGED', 'merge_commit': feature_merge, 'merged_at': datetime.now(timezone.utc).isoformat()}])
        self.blocked(self.call(), 'integration-unverified')

    def test_required_deployment_without_dated_revision_environment_evidence_blocks_finish(self) -> None:
        self.spec.write_text(self.spec.read_text() + '\n## Delivery Contract\ndeployment: required\n')
        prior = self.attested(self.clean_actions(self.prepare()))
        prior = self.checkpoint('archive', prior)
        self.assertEqual('archived', prior['status'], prior)
        self.blocked(self.checkpoint('finish', prior), 'deployment-unverified')

    def test_recorded_multi_repository_set_checks_every_stack(self) -> None:
        # Turn this fixture into an umbrella while retaining the first repository intact.
        source = self.root / 'service'
        source.mkdir()
        for name in ('.git', '.gitignore', 'baseline', 'product'):
            (self.root / name).rename(source / name)
        second = self.root / 'client'
        self.init_repo(second)
        base = self.git(second, 'rev-parse', 'HEAD')
        self.git(second, 'checkout', '-b', 'feat/client')
        (second / 'client').write_text('pending\n')
        self.git(second, 'add', 'client')
        self.git(second, 'commit', '-m', 'feat: deliver client')
        tip = self.git(second, 'rev-parse', 'HEAD')
        self.git(second, 'checkout', 'main')
        state = self.state_text.replace('## Phases', '## Repositories\n- repo: service | base_branch: main\n- repo: client | base_branch: main\n## Phases').replace('  branch: feat/delivery', '  repo: service\n  branch: feat/delivery')
        second_block = f'T-02 | Client | atomic-tests: green | atomic-execution: complete | atomic-validation: complete\n  repo: client\n  branch: feat/client\n  base_branch: main\n  base_commit: {base}\n  commits: {tip} feat: deliver client\n  blocker: none\n  notes: reviewed\n'
        state = state.replace('## Solution Design', second_block + '## Solution Design')
        (self.task / 'state.md').write_text(state)
        (self.task / 'plan.md').write_text('## Subtasks\n| ID | Name | Depends On | Status |\n|---|---|---|---|\n| T-01 | Deliver | — | reviewed |\n| T-02 | Client | T-01 | reviewed |\n')
        self.blocked(self.call(), 'integration-unverified')
        self.git(second, 'merge', '--no-ff', 'feat/client', '-m', 'merge: integrate client')
        result = self.call()
        self.assertEqual('ready', result['status'], result)
        self.assertEqual({'service', 'client'}, {r['name'] for r in result['repositories']})


if __name__ == '__main__':
    unittest.main(verbosity=2)
