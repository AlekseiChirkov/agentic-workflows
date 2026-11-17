#!/usr/bin/env python3
"""Check finalization orchestration contracts and behavior in disposable fixtures.

Run: python3 scripts/check-finalization-workflow.py [test name or case ...].
No live GitHub calls, consumer installation, or source Git mutations occur.
"""
from __future__ import annotations

from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('workflow_fixture', SOURCE / 'scripts/check-phase-finalize.py')
assert spec is not None and spec.loader is not None
FIXTURE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(FIXTURE)


def project_bytes(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*')
            if path.is_file() and not path.is_symlink()}


class WorkflowBehavior(FIXTURE.FinalizationChecks):
    def attempt(self, prior: dict, *, attempt_id: str = 'delete-first', exit_code: int = 128,
                checkpoint: str = 'blocked', **changes: object) -> dict:
        action = prior['actions'][0]
        row = {'attempt_id': attempt_id, 'operation_id': action['id'], 'checkpoint': checkpoint,
               'repository': action['repository'], 'argv': action['command'], 'exit_code': exit_code,
               'stdout': '', 'stderr': 'network unavailable' if exit_code else '',
               'observed_at': datetime.now(timezone.utc).isoformat(),
               'provenance': 'isolated explicit command execution',
               'source_tips': {repo['path']: repo['integration']['tip'] for repo in prior['repositories']}}
        row.update(changes)
        self.attempt_row = row
        self.put_evidence(command_attempt=row)
        return self.checkpoint('attempt', prior)

    def test_failed_attempt_is_persisted_when_git_observation_is_unavailable(self) -> None:
        prior = self.prepare()
        tools = self.root / '.ai/offline-tools'
        tools.mkdir()
        executable = tools / 'git'
        executable.write_text('#!/bin/sh\necho unavailable >&2\nexit 128\n')
        executable.chmod(0o755)
        self.fixture_path = str(tools) + os.pathsep + os.environ['PATH']
        recorded = self.attempt(prior)
        self.assertEqual('recorded', recorded['status'], recorded)
        journal = json.loads(Path(prior['journal_path']).read_bytes())
        self.assertEqual([self.attempt_row], journal['command_attempts'])
        self.assertEqual('blocked', journal['operations'][prior['actions'][0]['id']]['checkpoint'])
        self.assertFalse(journal['complete'])
        self.assertEqual('incomplete', journal['outcomes']['cleanup'])

    def test_attempt_replay_is_idempotent_and_conflicting_identity_is_rejected(self) -> None:
        prior = self.prepare()
        recorded = self.attempt(prior)
        self.assertEqual('recorded', recorded['status'], recorded)
        self.put_evidence(command_attempt=self.attempt_row)
        replay = self.checkpoint('attempt', recorded)
        self.assertEqual(recorded['revision'], replay['revision'])
        changed = dict(self.attempt_row, stderr='different execution')
        self.put_evidence(command_attempt=changed)
        self.blocked(self.checkpoint('attempt', replay), 'attempt-conflict')
        self.assertEqual(replay['revision'], hashlib.sha256(Path(replay['journal_path']).read_bytes()).hexdigest())

    def test_attempt_requires_cas_lock_authorization_and_exact_action_scope(self) -> None:
        prior = self.prepare()
        self.blocked(self.attempt(prior, argv=['git', 'branch', '-D', 'unrelated']), 'attempt-invalid')
        self.attempt(prior)
        self.blocked(self.checkpoint('attempt', prior), 'revision-conflict')
        current = json.loads(Path(prior['journal_path']).read_bytes())
        revision = hashlib.sha256(Path(prior['journal_path']).read_bytes()).hexdigest()
        self.blocked(self.call('attempt', args=('--expected-revision', revision)), 'authorization-required')
        with Path(prior['journal_path']).with_name('journal.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.blocked(self.call('attempt', args=('--authorize', '--expected-revision', revision)), 'journal-locked')
        self.assertEqual(current, json.loads(Path(prior['journal_path']).read_bytes()))

    def test_successful_command_cannot_claim_verified_postcondition(self) -> None:
        prior = self.prepare()
        recorded = self.attempt(prior, exit_code=0, checkpoint='applied')
        self.assertEqual('recorded', recorded['status'], recorded)
        self.assertEqual('applied', recorded['operations'][prior['actions'][0]['id']]['checkpoint'])
        self.assertEqual('incomplete', recorded['outcomes']['cleanup'])
        self.assertFalse(recorded['complete'])
        self.blocked(self.attempt(recorded, attempt_id='claim', exit_code=0, checkpoint='verified'), 'attempt-invalid')
        observed = self.checkpoint('record', recorded)
        self.assertNotEqual('verified', observed['operations'][prior['actions'][0]['id']]['checkpoint'])

    def test_failed_then_recovered_execution_keeps_error_and_fresh_postcondition(self) -> None:
        prior = self.attempt(self.prepare())
        self.assertEqual('recorded', prior['status'], prior)
        self.git(self.repo, 'branch', '-d', 'feat/delivery')
        recovered = self.attempt(prior, attempt_id='delete-retry', exit_code=0, checkpoint='applied')
        observed = self.checkpoint('record', recovered)
        self.assertEqual('complete', observed['outcomes']['cleanup'])
        self.assertEqual('verified', observed['operations'][prior['actions'][0]['id']]['checkpoint'])
        self.assertEqual([128, 0], [row['exit_code'] for row in observed['command_attempts']])
        self.assertIn('network unavailable', observed['command_attempts'][0]['stderr'])

    def test_failed_verification_and_recovered_teardown_keep_exact_evidence(self) -> None:
        prior = self.prepare()
        argv = ['python3', '-m', 'unittest', 'product_behavior']
        failed = self.attempt(prior, attempt_id='verification-first', operation_id='verification',
                              argv=argv, stdout='product assertion passed\n',
                              stderr='teardown failed: fixture resource unavailable\n', exit_code=1)
        self.assertEqual('recorded', failed['status'], failed)
        original = dict(self.attempt_row)
        recovered = self.attempt(failed, attempt_id='verification-retry', operation_id='verification',
                                 argv=argv, stdout='product assertion and teardown passed\n',
                                 stderr='', exit_code=0, checkpoint='applied')
        self.assertEqual('recorded', recovered['status'], recovered)
        self.assertEqual('unverified', recovered['outcomes'].get('verification', 'unverified'))
        self.assertEqual('incomplete', recovered['outcomes']['cleanup'])
        self.assertFalse(recovered['complete'])
        observed = self.attested(self.clean_actions(recovered))
        self.assertEqual(original, observed['command_attempts'][0])
        self.assertEqual([1, 0], [row['exit_code'] for row in observed['command_attempts']])
        self.assertEqual('attested', observed['outcomes']['verification'])
        self.assertIn('fixture product', observed['attestations']['verification']['coverage'])
        self.assertIn('prior', ' '.join(observed['trust_limitations']))
        self.assertEqual('unverified', observed['outcomes']['deployment'])

    def test_new_failed_verification_invalidates_older_pass_until_fresh_attestation(self) -> None:
        prior = self.attested(self.clean_actions(self.prepare()))
        earlier = json.loads(self.evidence.read_bytes())['attestations']
        failed = self.attempt(prior, attempt_id='later-check', operation_id='verification',
                              argv=['python3', '-m', 'unittest', 'product_behavior'],
                              exit_code=1, stderr='later teardown failed\n')
        self.assertEqual('recorded', failed['status'], failed)
        self.assertEqual('unverified', failed['outcomes']['verification'])
        self.assertNotIn('verification', failed.get('attestations', {}))
        self.put_evidence(attestations=earlier)
        replayed = self.checkpoint('record', failed)
        self.assertFalse(replayed['complete'])
        self.assertNotEqual('attested', replayed.get('outcomes', {}).get('verification'))
        revision = hashlib.sha256(Path(prior['journal_path']).read_bytes()).hexdigest()
        current = dict(failed, revision=revision)
        fresh = self.attested(current)
        self.assertEqual('attested', fresh['outcomes']['verification'])
        self.assertEqual('later teardown failed\n', fresh['command_attempts'][-1]['stderr'])

    def knowledge_fixture(self, *, kind: str = 'current-record',
                          relative: str = '.ai/memory/architecture.md',
                          original: str = '# Architecture\n\nOriginal current record.\n') -> tuple[dict, Path, bytes]:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(original)
        self.git(self.repo, 'add', '-f', str(path))
        self.git(self.repo, 'commit', '-m', 'docs: record current knowledge')
        self.put_evidence(knowledge_inventory=[{'path': relative, 'kind': kind}])
        prior = self.attested(self.clean_actions(self.prepare()))
        return prior, path, original.encode()

    def knowledge_delta(self, prior: dict, path: Path, original: bytes, updated: bytes) -> dict:
        rows = json.loads(self.evidence.read_bytes())['attestations']
        path.write_bytes(updated)
        knowledge = next(row for row in rows if row['kind'] == 'knowledge')
        knowledge['observed_at'] = datetime.now(timezone.utc).isoformat()
        knowledge['file_changes'] = [{'path': path.relative_to(self.root).as_posix(),
                                     'before_sha256': hashlib.sha256(original).hexdigest(),
                                     'after_sha256': hashlib.sha256(updated).hexdigest()}]
        self.put_evidence(attestations=rows)
        return self.checkpoint('knowledge', prior)

    def test_tracked_current_knowledge_uses_bound_before_after_changes_without_staging(self) -> None:
        prior, path, original = self.knowledge_fixture()
        updated = b'# Architecture\n\nVerified delivered current record.\n'
        changed = self.knowledge_delta(prior, path, original, updated)
        self.assertEqual('recorded', changed['status'], changed)
        entry = next(row for row in changed['knowledge_files'] if row['path'] == '.ai/memory/architecture.md')
        self.assertEqual(original, Path(entry['snapshot_path']).read_bytes())
        self.assertEqual(hashlib.sha256(updated).hexdigest(), changed['knowledge_changes'][0]['after_sha256'])
        self.assertEqual('', self.git(self.repo, 'diff', '--cached', '--name-only'))
        archived = self.checkpoint('archive', changed)
        self.assertEqual('archived', archived['status'], archived)
        self.assertTrue(self.checkpoint('finish', archived)['complete'])
        self.assertEqual(updated, path.read_bytes())

    def test_knowledge_inventory_rejects_product_protected_and_executable_paths(self) -> None:
        for relative, kind in (('product', 'current-record'), ('.ai/specs/delivery.md', 'current-record'),
                               ('.ai/tasks/todo/task-delivery/state.md', 'current-record'),
                               ('.ai/context/finalization/history.md', 'current-record'),
                               ('.ai/adr/accepted-decision.md', 'current-record'),
                               ('scripts/reconcile.py', 'current-record')):
            with self.subTest(path=relative):
                self.put_evidence(knowledge_inventory=[{'path': relative, 'kind': kind}])
                result = self.call('prepare', args=('--authorize', '--expected-revision', 'absent'))
                self.blocked(result, 'knowledge-change-invalid')

    def test_knowledge_change_cannot_accept_unrelated_or_staged_edits(self) -> None:
        prior, path, original = self.knowledge_fixture()
        updated = b'# Architecture\n\nVerified current record.\n'
        changed = self.knowledge_delta(prior, path, original, updated)
        self.assertEqual('recorded', changed['status'], changed)
        (self.repo / 'product').write_text('unrelated edit\n')
        self.blocked(self.checkpoint('record', changed), 'worktree-dirty')
        (self.repo / 'product').write_text('delivered\n')
        self.git(self.repo, 'add', '-f', str(path))
        self.blocked(self.checkpoint('record', changed), 'knowledge-index-changed')

    def test_knowledge_change_needs_exact_snapshot_and_independent_source_binding(self) -> None:
        prior, path, original = self.knowledge_fixture()
        updated = b'# Architecture\n\nVerified current record.\n'
        self.knowledge_delta(prior, path, original, updated)
        rows = json.loads(self.evidence.read_bytes())['attestations']
        knowledge = next(row for row in rows if row['kind'] == 'knowledge')
        knowledge['file_changes'][0]['before_sha256'] = '0' * 64
        self.put_evidence(attestations=rows)
        self.blocked(self.checkpoint('knowledge', prior), 'knowledge-change-invalid')
        knowledge['file_changes'][0]['before_sha256'] = hashlib.sha256(original).hexdigest()
        knowledge['source_tips'] = {str(self.repo): self.base}
        self.put_evidence(attestations=rows)
        rejected = self.checkpoint('knowledge', prior)
        self.assertEqual('blocked', rejected['status'], rejected)
        self.assertFalse(rejected['complete'])

    def test_progress_history_is_append_only_and_snapshot_is_immutable(self) -> None:
        prior, path, original = self.knowledge_fixture(kind='progress', relative='.ai/memory/progress.md',
                                                       original='# Progress\n\nHistorical delivery.\n')
        self.blocked(self.knowledge_delta(prior, path, original, b'# Progress\n\nRewritten history.\n'),
                     'knowledge-change-invalid')
        appended = original + b'\n2026-11-17: Verified task closure; deployment remains unknown.\n'
        changed = self.knowledge_delta(prior, path, original, appended)
        self.assertEqual('recorded', changed['status'], changed)
        entry = next(row for row in changed['knowledge_files'] if row['path'] == '.ai/memory/progress.md')
        Path(entry['snapshot_path']).write_bytes(b'changed original snapshot\n')
        self.blocked(self.checkpoint('record', changed), 'snapshot-conflict')

    def test_failed_attested_checks_invalidate_matching_older_evidence(self) -> None:
        for kind in ('knowledge', 'audit', 'deployment'):
            with self.subTest(kind=kind):
                if kind != 'knowledge':
                    self.doCleanups()
                    self.setUp()
                prior = self.attested(self.clean_actions(self.prepare()))
                rows = json.loads(self.evidence.read_bytes())['attestations']
                deployment = dict(next(row for row in rows if row['kind'] == 'knowledge'), kind='deployment',
                                  revision=prior['repositories'][0]['integration']['tip'], environment='isolated fixture')
                rows = [row for row in rows if row['kind'] != 'deployment'] + [deployment]
                self.put_evidence(attestations=rows)
                prior = self.checkpoint('record', prior)
                failed = self.attempt(prior, attempt_id='later-' + kind, operation_id=kind,
                                      argv=['fixture-check', kind], exit_code=1, stderr=kind + ' check failed\n')
                self.assertEqual('recorded', failed['status'], failed)
                self.assertEqual('unverified', failed['outcomes'][kind])
                self.assertNotIn(kind, failed.get('attestations', {}))
                self.put_evidence(attestations=rows)
                replayed = self.checkpoint('record', failed)
                self.assertNotEqual('attested', replayed.get('outcomes', {}).get(kind))
                actual = hashlib.sha256(Path(prior['journal_path']).read_bytes()).hexdigest()
                prior = self.attested(dict(failed, revision=actual))

    def final_verification_receipt(self) -> dict:
        source_tip = self.git(self.repo, 'rev-parse', 'main')
        output = self.git(self.repo, 'show', source_tip + ':product')
        return {'kind': 'verification', 'task_path': str(self.task),
                'state_sha256': hashlib.sha256((self.task / 'state.md').read_bytes()).hexdigest(),
                'observed_at': datetime.now(timezone.utc).isoformat(), 'result': 'pass',
                'provenance': 'independent executed final verification', 'source_tips': {str(self.repo): source_tip},
                'commands': [{'argv': ['git', 'show', source_tip + ':product'], 'exit_code': 0,
                              'stdout': output, 'stderr': ''}], 'coverage': 'Committed product after final repair.'}

    def canonical_final_verification(self) -> None:
        value = self.state_text.replace('## Execution Report\nFinal verification: PASS — isolated product behavior checks after the final change.\n',
                                        '## Final Verification\nIndependent dated product checks after the final repair; exact receipts supplied.\n')
        (self.task / 'state.md').write_text(value)

    def test_canonical_final_verification_accepts_exact_independent_receipt_without_hidden_phrase(self) -> None:
        self.canonical_final_verification()
        self.put_evidence(attestations=[self.final_verification_receipt()])
        result = self.call()
        self.assertEqual('ready', result['status'], result)
        self.assertFalse(result['validation_evidence']['fresh_tests'])
        self.assertIn('receipt', result['validation_evidence']['source'])

    def test_canonical_final_verification_rejects_missing_failed_or_unbound_receipt(self) -> None:
        self.canonical_final_verification()
        receipt = self.final_verification_receipt()
        for change in ('missing', 'failed', 'state', 'source', 'undated', 'coverage'):
            with self.subTest(change=change):
                row = json.loads(json.dumps(receipt))
                if change == 'failed': row['commands'][0]['exit_code'] = 1
                if change == 'state': row['state_sha256'] = '0' * 64
                if change == 'source': row['source_tips'] = {str(self.repo): self.base}
                if change == 'undated': row['observed_at'] = ''
                if change == 'coverage': row['coverage'] = ''
                self.put_evidence(attestations=[] if change == 'missing' else [row])
                self.assertEqual('blocked', self.call()['status'])

    def test_large_cumulative_outputs_keep_exact_artifacts_and_readable_journal(self) -> None:
        prior = self.prepare()
        outputs = []
        for number in range(3):
            output = 'line: ' + ('évidence\n' * 160000) + str(number)
            outputs.append(output.encode())
            prior = self.attempt(prior, attempt_id='large-' + str(number), stdout=output,
                                 stderr='retained failure ' + str(number))
            self.assertEqual('recorded', prior['status'], prior)
        journal_path = Path(prior['journal_path'])
        self.assertLessEqual(journal_path.stat().st_size, 1024 * 1024)
        for row, original in zip(prior['command_attempts'], outputs):
            artifact = row['stdout']
            self.assertIsInstance(artifact, dict, 'Large output must use an immutable exact-byte artifact')
            self.assertEqual({'path', 'sha256', 'bytes', 'encoding'}, set(artifact))
            self.assertEqual('utf-8', artifact['encoding'])
            self.assertEqual(len(original), artifact['bytes'])
            self.assertEqual(hashlib.sha256(original).hexdigest(), artifact['sha256'])
            self.assertTrue(Path(artifact['path']).is_relative_to(journal_path.parent / 'outputs'))
            self.assertEqual(original, Path(artifact['path']).read_bytes())
        self.assertEqual('ready', self.call()['status'])
        replay = self.checkpoint('attempt', prior)
        self.assertEqual(prior['revision'], replay['revision'])
        artifact_path = Path(prior['command_attempts'][0]['stdout']['path'])
        artifact_path.write_bytes(b'changed output\n')
        self.blocked(self.checkpoint('record', prior), 'output-artifact-changed')

    def test_oversized_journal_refusal_preserves_previous_revision_for_all_writers(self) -> None:
        prior = self.prepare()
        path = Path(prior['journal_path'])
        original = path.read_bytes()
        result = self.attempt(prior, provenance='independent named source ' + 'x' * (1024 * 1024))
        self.blocked(result, 'journal-too-large')
        self.assertEqual(original, path.read_bytes())
        support_spec = importlib.util.spec_from_file_location('workflow_support_bound', SOURCE / 'scripts/finalization_support.py')
        assert support_spec is not None and support_spec.loader is not None
        support = importlib.util.module_from_spec(support_spec)
        support_spec.loader.exec_module(support)
        with self.assertRaises(support.Refusal) as refused:
            support.atomic_write(path, b'x' * (1024 * 1024 + 1), self.root, journal=True)
        self.assertEqual('journal-too-large', refused.exception.check)
        self.assertEqual(original, path.read_bytes())

    def test_checkpoint_vocabulary_and_new_journal_initial_operation_state(self) -> None:
        prior = self.prepare()
        self.assertIn('operations', prior)
        self.assertEqual({row['id'] for row in prior['actions']}, set(prior['operations']))
        for row in prior['operations'].values():
            self.assertIn(row['checkpoint'], {'pending', 'prepared', 'applied', 'verified', 'blocked', 'preserved'})
        self.blocked(self.attempt(prior, checkpoint='complete'), 'attempt-invalid')
        preserved = self.attempt(prior, checkpoint='preserved')
        self.assertEqual('recorded', preserved['status'], preserved)

    def alias_fixture(self, *, returned_identity: str = 'fixture-org/product',
                      resolved_host: str = 'github.com', merged: str | None = None) -> Path:
        self.github_pr_fixture()
        remote = self.root / '.ai/fixture-origin.git'
        self.git(self.repo, 'remote', 'set-url', 'origin', 'git@github-personal:fixture-org/product.git')
        self.git(self.repo, 'config', 'url.' + remote.as_uri() + '.insteadOf', 'git@github-personal:fixture-org/product.git')
        tools = self.root / '.ai/fixture-tools'
        log = self.root / '.ai/alias-calls.jsonl'
        row = {'url': 'https://github.com/' + returned_identity + '/pull/142', 'state': 'CLOSED',
               'baseRefName': 'main', 'headRefName': 'feat/delivery', 'headRefOid': self.tip,
               'mergeCommit': None, 'mergedAt': None}
        if merged is not None:
            row.update(state='MERGED', mergeCommit={'oid': merged}, mergedAt=datetime.now(timezone.utc).isoformat())
        executable = tools / 'gh'
        executable.write_text('#!' + sys.executable + '\nimport json, sys\nfrom pathlib import Path\n'
                              + 'with Path(' + repr(str(log)) + ').open("a") as handle: handle.write(json.dumps(sys.argv[1:]) + "\\n")\n'
                              + 'print(json.dumps(' + repr({'url': 'https://github.com/' + returned_identity,
                                                           'nameWithOwner': returned_identity}) + ') if sys.argv[1:3] == ["repo", "view"] else '
                              + repr(json.dumps(row)) + ')\n')
        executable.chmod(0o755)
        ssh = tools / 'ssh'
        ssh.write_text('#!' + sys.executable + '\nimport json, sys\nfrom pathlib import Path\n'
                       + 'with Path(' + repr(str(log)) + ').open("a") as handle: handle.write(json.dumps(["ssh", *sys.argv[1:]]) + "\\n")\n'
                       + 'print(' + repr('hostname ' + resolved_host) + ')\n')
        ssh.chmod(0o755)
        return log

    def alias_pr(self, audit: str, *, returned_identity: str = 'fixture-org/product') -> tuple[dict, Path]:
        log = self.alias_fixture(returned_identity=returned_identity)
        (self.task / 'state.md').write_text(self.state_text.replace('## Solution Design', '  pr: ' + audit + '\n## Solution Design'))
        return self.call(), log

    def test_ssh_alias_resolves_numbered_and_url_pr_from_exact_origin(self) -> None:
        result, log = self.alias_pr('#142 ready')
        self.assertEqual('ready', result['status'], result)
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        resolve = next(row for row in calls if row[:2] == ['repo', 'view'])
        self.assertIn(['ssh', '-G', 'github-personal'], calls)
        self.assertIn('https://github.com/fixture-org/product', resolve)
        self.assertEqual('fixture-org/product', result['repositories'][0]['candidates'][0]['pr_receipt']['repository_identity'])
        self.assertEqual(['git@github-personal:fixture-org/product.git'], result['repositories'][0]['remote_identity']['configured_fetch_urls'])
        for audit in ('#142 draft', 'https://github.com/fixture-org/product/pull/142'):
            (self.task / 'state.md').write_text(self.state_text.replace('## Solution Design', '  pr: ' + audit + '\n## Solution Design'))
            observed = self.call()
            self.assertEqual('ready', observed['status'], observed)
            self.assertEqual(audit, observed['repositories'][0]['candidates'][0]['pr'])

    def test_ssh_alias_mismatched_authority_never_selects_other_repository(self) -> None:
        result, _ = self.alias_pr('#142 ready', returned_identity='unrelated-org/product')
        self.blocked(result, 'pr-repository-mismatch')

    def test_ssh_alias_option_spelling_cannot_become_ssh_arguments(self) -> None:
        log = self.alias_fixture()
        self.git(self.repo, 'remote', 'set-url', 'origin', 'git@-F:fixture-org/product.git')
        self.git(self.repo, 'config', 'url.' + (self.root / '.ai/fixture-origin.git').as_uri() + '.insteadOf',
                 'git@-F:fixture-org/product.git')
        (self.task / 'state.md').write_text(self.state_text.replace('## Solution Design', '  pr: #142 ready\n## Solution Design'))
        self.blocked(self.call(), 'pr-authority-unverified')
        self.assertFalse(log.exists(), 'Invalid SSH host must fail before invoking any resolver')

    def test_ssh_alias_without_github_translation_fails_closed(self) -> None:
        self.alias_fixture(resolved_host='other.invalid')
        (self.task / 'state.md').write_text(self.state_text.replace('## Solution Design', '  pr: #142 ready\n## Solution Design'))
        self.blocked(self.call(), 'pr-authority-unverified')

    def test_ssh_alias_environment_repository_overrides_are_rejected(self) -> None:
        self.alias_fixture()
        (self.task / 'state.md').write_text(self.state_text.replace('## Solution Design', '  pr: #142 ready\n## Solution Design'))
        original = self.environment
        for key, value in (('GH_REPO', 'other/project'), ('GH_HOST', 'other.invalid')):
            with self.subTest(key=key):
                self.environment = lambda: dict(original(), **{key: value})
                self.blocked(self.call(), 'pr-authority-unverified')
        self.environment = original

    def test_remote_identity_change_rejects_existing_journal_without_migration(self) -> None:
        prior = self.prepare()
        self.git(self.repo, 'remote', 'add', 'origin', 'git@github-personal:fixture-org/product.git')
        self.blocked(self.checkpoint('record', prior), 'remote-identity-changed')

    def test_dry_run_has_no_output_writes_or_operation_receipts(self) -> None:
        prior = self.prepare()
        before = project_bytes(self.root)
        self.put_evidence(command_attempt={'invalid': True})
        before = project_bytes(self.root)
        result = self.checkpoint('attempt', prior, '--dry-run')
        self.assertEqual('ready', result['status'], result)
        self.assertEqual(before, project_bytes(self.root))

    def test_archive_interruptions_preserve_old_path_resolution_and_audit(self) -> None:
        for fault in ('before-journal-replace', 'after-journal-replace', 'after-task-rename',
                      'after-spec-rename', 'after-pointer-update', 'after-moving-links', 'after-index-update'):
            with self.subTest(fault=fault):
                if fault != 'before-journal-replace':
                    self.tearDown() if hasattr(self, 'tearDown') else None
                    self.doCleanups()
                    self.setUp()
                original = (self.task / 'state-archive.md').read_bytes()
                prior = self.attested(self.clean_actions(self.prepare()))
                result = self.checkpoint('archive', prior, fault=fault)
                self.assertEqual('interrupted', result['status'], fault)
                revision = hashlib.sha256(Path(prior['journal_path']).read_bytes()).hexdigest()
                resumed = self.call('archive', args=('--authorize', '--expected-revision', revision))
                self.assertEqual('archived', resumed['status'], resumed)
                self.assertEqual(original, (Path(resumed['resolution']['task_path']) / 'state-archive.md').read_bytes())
                finished = self.checkpoint('finish', resumed)
                self.assertTrue(finished['complete'], finished)

    def test_umbrella_untracked_state_remains_local_after_closure(self) -> None:
        self.test_recorded_multi_repository_set_checks_every_stack()
        client = self.root / 'client'
        (client / 'product').write_text('delivered\n')
        self.git(client, 'add', 'product')
        self.git(client, 'commit', '-m', 'chore: expose delivered product')
        prior = self.attested(self.clean_actions(self.prepare()))
        archived = self.checkpoint('archive', prior)
        self.assertEqual('archived', archived['status'], archived)
        self.assertTrue(self.checkpoint('finish', archived)['complete'])
        self.assertFalse((self.root / '.git').exists())
        for repo in (self.root / 'service', client):
            self.assertEqual('', self.git(repo, 'ls-files', '.ai'))
        self.assertTrue((self.root / '.ai/context/finalization').is_dir())

    def test_all_repository_checkouts_precede_remote_then_local_cleanup(self) -> None:
        self.test_recorded_multi_repository_set_checks_every_stack()
        for name, branch in (('service', 'feat/delivery'), ('client', 'feat/client')):
            repo = self.root / name
            remote = self.root / '.ai' / (name + '-origin.git')
            self.git(repo, 'init', '--bare', str(remote))
            self.git(repo, 'remote', 'add', 'origin', str(remote))
            self.git(repo, 'push', 'origin', 'main', branch)
            self.git(remote, 'symbolic-ref', 'HEAD', 'refs/heads/main')
            self.git(repo, 'checkout', branch)
        result = self.call()
        self.assertEqual('ready', result['status'], result)
        actions = result['actions']
        self.assertEqual({'service', 'client'}, {repo['name'] for repo in result['repositories']})
        self.assertEqual(2, sum(row['kind'] == 'checkout' for row in actions))
        self.assertEqual(2, sum(row['kind'] == 'remote-delete' for row in actions))
        self.assertEqual(2, sum(row['kind'] == 'local-delete' for row in actions))
        order = {'checkout': 0, 'refresh': 0, 'remote-delete': 1, 'local-delete': 2}
        ranks = [order[row['kind']] for row in actions]
        self.assertEqual(sorted(ranks), ranks,
                         'Every integration checkout/refresh must precede any cleanup; remote deletion precedes local deletion')

    def test_pending_refresh_on_integration_checkout_is_incomplete(self) -> None:
        self.test_local_integration_behind_live_remote_gets_safe_refresh_plan()
        self.git(self.repo, 'checkout', 'main')
        result = self.call()
        self.assertEqual('ready', result['status'], result)
        self.assertTrue(any(row['kind'] == 'refresh' for row in result['actions']))
        self.assertFalse(any(row['kind'] == 'checkout' for row in result['actions']))
        self.assertEqual('incomplete', result['outcomes']['checkout'],
                         'An integration branch still awaiting FF refresh is not a completed checkout')

    def test_outstanding_scope_in_any_completed_phase_keeps_whole_spec_active(self) -> None:
        for heading in ('Deferred', 'Outstanding Scope'):
            with self.subTest(heading=heading):
                if heading != 'Deferred':
                    self.doCleanups()
                    self.setUp()
                self.spec.write_text('# Delivery\n\n## Phase 1\nFirst component.\n## Phase 2\nSecond component.\n')
                (self.task / 'state.md').write_text(self.state_text.replace('flow: full', 'active_phase: 2\nspec_phase_count: 2\nflow: full'))
                other = self.root / '.ai/tasks/completed/task-first-phase'
                other.mkdir(parents=True)
                (other / 'state.md').write_text('spec_path: .ai/specs/delivery.md\nactive_phase: 1\n'
                                                'flow: full\n## Phases\n- execution: complete\n- validation: complete\n'
                                                + '## ' + heading + '\n- Required report export remains outstanding.\n')
                prior = self.attested(self.clean_actions(self.prepare()))
                archived = self.checkpoint('archive', prior)
                self.assertEqual('archived', archived['status'], archived)
                self.assertTrue(self.spec.is_file(), 'Unfinished sibling phase scope keeps the whole spec active')
                self.assertEqual('unfinished-scope', archived['outcomes']['spec_archival'])
                self.assertTrue((other / 'state.md').is_file())

    def test_ssh_alias_merged_squash_receipt_authorizes_only_bound_hook_cleanup(self) -> None:
        self.git(self.repo, 'reset', '--hard', self.base)
        self.git(self.repo, 'cherry-pick', '--no-commit', 'feat/delivery')
        self.git(self.repo, 'commit', '-m', 'feat: integrate squashed delivery')
        merged = self.git(self.repo, 'rev-parse', 'HEAD')
        self.alias_fixture(merged=merged)
        (self.task / 'state.md').write_text(self.state_text.replace('## Solution Design', '  pr: #142 ready\n## Solution Design'))
        prior = self.prepare()
        self.assertEqual('pr', prior['repositories'][0]['candidates'][0]['integration_method'])
        home = self.root / '.ai/hook-home'
        config = home / '.config'
        registry = config / 'orchestrail/projects'
        registry.parent.mkdir(parents=True)
        registry.write_text(str(self.repo) + '\n')
        import shlex
        action = next(row for row in prior['actions'] if row['kind'] == 'local-delete')
        event = {'session_id': 'isolated-squash-alias', 'hook_event_name': 'PreToolUse',
                 'tool_name': 'Bash', 'tool_input': {'command': shlex.join(action['command'])},
                 'cwd': str(self.repo), 'permission_mode': 'default'}
        env = dict(self.environment(), HOME=str(home), XDG_CONFIG_HOME=str(config))
        result = subprocess.run([sys.executable, '-I', str(SOURCE / 'hooks/git_rails.py')],
                                input=json.dumps(event), text=True, capture_output=True, env=env, timeout=10)
        self.assertEqual((0, '', ''), (result.returncode, result.stdout, result.stderr),
                         'A helper-verified origin-bound SSH alias merged receipt must pass the independent hook checks')

    def test_required_deployment_unknown_remains_independent(self) -> None:
        self.test_required_deployment_without_dated_revision_environment_evidence_blocks_finish()

    def test_source_bound_verification_retains_honest_reuse_limits(self) -> None:
        prior = self.attested(self.clean_actions(self.prepare()))
        receipt = prior['attestations']['verification']
        self.assertTrue(receipt['reuse']['permitted'])
        self.assertIn('runtime', receipt['reuse']['limitations'])
        self.assertIn('prior', ' '.join(prior['trust_limitations']))
        self.assertEqual('unverified', prior['outcomes']['deployment'])


class InstructionContracts(unittest.TestCase):
    def test_public_interface_is_one_explicit_finalization_phase(self) -> None:
        path = SOURCE / 'workflows/phase-finalize.md'
        self.assertTrue(path.is_file(), 'The public finalization workflow must be installed')
        workflow = path.read_text()
        invocation = next(line for line in workflow.splitlines() if line.startswith('Invocation:'))
        self.assertEqual('Invocation: `/phase-finalize <task-directory|spec-path> [--dry-run]`', invocation)
        for needed in ('## Guard', '## Context Bootstrap', '## Run Logging', '## Execution', '**stop**',
                       'Finalization Git ownership', 'expected-revision', 'command_attempt', 'operations',
                       'source_tips', 'run-end', 'PHASE_OWNS_RUN', '--note approximate'):
            self.assertIn(needed, workflow)
        for forbidden in ('/pf-', '--cleanup', '--resume', '--phase ', '--force-with-lease'):
            self.assertNotIn(forbidden, workflow)

    def test_finalization_is_registered_in_canonical_contracts_and_bootstrap(self) -> None:
        expected = {'rules/workflow-globals.md': ('rule-phase-finalize', '- finalization: not-started', 'pending', 'preserved'),
                    'rules/workflow-reference.md': ('Finalization', 'current-location', 'original snapshots'),
                    'rules/orchestration.md': ('/phase-finalize',),
                    'rules/run-log.md': ('/phase-finalize',),
                    'rules/global-claude.md': ('/phase-finalize',),
                    'templates/codex-global-AGENTS.md': ('/phase-finalize',),
                    'templates/.ai/memory/state.md': ('finalization',),
                    'templates/.ai-umbrella/memory/state.md': ('finalization',)}
        for path, tokens in expected.items():
            value = (SOURCE / path).read_text()
            for token in tokens:
                self.assertIn(token, value, path)
        bootstrap = (SOURCE / 'rules/phase-finalize.md').read_text()
        for token in ('## Context Bootstrap', 'umbrella', 'environment.md', 'integrations.md', 'runbook.md',
                      'independent', 'validation', 'original', 'journal'):
            self.assertIn(token, bootstrap)

    def test_delivery_endpoints_only_suggest_finalization_after_owner_merge(self) -> None:
        for path in ('workflows/spec-run.md', 'workflows/phase-pipeline.md', 'workflows/pv-finalize.md'):
            text = (SOURCE / path).read_text()
            self.assertIn('/phase-finalize', text, path)
            self.assertIn('owner merges', text, path)
        for path in ('workflows/PIPELINE.md', 'docs/USAGE.md', 'docs/SPEC-RUN-QUICKSTART.md',
                     'scripts/README.md', 'README.md'):
            self.assertIn('phase-finalize', (SOURCE / path).read_text(), path)

    def validate_fixture(self, phase: str | None) -> subprocess.CompletedProcess:
        import tempfile
        self.temp = tempfile.TemporaryDirectory(prefix='finalization-validator-')
        self.addCleanup(self.temp.cleanup)
        task = Path(self.temp.name)
        marker = '' if phase is None else '- finalization: ' + phase + '\n'
        (task / 'state.md').write_text('spec_path: .ai/specs/product.md\nflow: quick\n## Phases\n'
                                     '- discovery: not-started\n- execution: not-started\n- validation: not-started\n'
                                     + marker + '## Contract (quick)\n### Off-limits\nNone\n### Invariants\nStable\n### Acceptance Criteria\nDelivered\n')
        return subprocess.run(['bash', str(SOURCE / 'scripts/validate-task.sh'), str(task)],
                              text=True, capture_output=True, env=dict(os.environ, PATH='/usr/bin:/bin'))

    def test_task_validator_accepts_legacy_absent_and_canonical_finalization_states(self) -> None:
        for phase in (None, 'not-started', 'in-progress', 'complete'):
            with self.subTest(phase=phase):
                result = self.validate_fixture(phase)
                self.assertEqual(0, result.returncode, result.stdout)

    def test_task_validator_rejects_invalid_or_duplicate_finalization_states(self) -> None:
        for phase in ('done', 'complete\n- finalization: in-progress'):
            with self.subTest(phase=phase):
                result = self.validate_fixture(phase)
                self.assertEqual(1, result.returncode, result.stdout)
                self.assertIn('finalization', result.stdout)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    selected = sys.argv[1:]
    for case in (WorkflowBehavior, InstructionContracts):
        for name in sorted(case.__dict__):
            if name.startswith('test_') and (not selected or name in selected or case.__name__ in selected):
                suite.addTest(case(name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
