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
                      resolved_host: str = 'github.com') -> Path:
        self.github_pr_fixture()
        remote = self.root / '.ai/fixture-origin.git'
        self.git(self.repo, 'remote', 'set-url', 'origin', 'git@github-personal:fixture-org/product.git')
        self.git(self.repo, 'config', 'url.' + remote.as_uri() + '.insteadOf', 'git@github-personal:fixture-org/product.git')
        tools = self.root / '.ai/fixture-tools'
        log = self.root / '.ai/alias-calls.jsonl'
        row = {'url': 'https://github.com/' + returned_identity + '/pull/142', 'state': 'CLOSED',
               'baseRefName': 'main', 'headRefName': 'feat/delivery', 'headRefOid': self.tip,
               'mergeCommit': None, 'mergedAt': None}
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
