#!/usr/bin/env python3
"""Check finalization hook safety and provider staging in disposable fixtures.

Run: python3 scripts/check-finalization-safety.py [unittest selection ...].
No live consumer configuration, network service, or source Git state is modified.
Staging always uses a copied source, controlled HOME, and instrumented preflight.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from types import ModuleType
import unittest

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parent.parent


def module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


FIXTURE = module('finalization_safety_fixture', SOURCE / 'scripts/check-phase-finalize.py')
CORE = module('finalization_safety_core', SOURCE / 'hooks/git_rails.py')


def encoded(document: dict) -> bytes:
    return (json.dumps(document, sort_keys=True, indent=2) + '\n').encode()


def files(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*')
            if path.is_file() and not path.is_symlink()}


class SafetyChecks(FIXTURE.FinalizationChecks):
    """Use the core helper's public fixture so tests consume actual published receipts."""

    def setUp(self) -> None:
        super().setUp()
        self.home = self.root / '.ai/fixture-home'
        self.home.mkdir()
        self.config = self.home / '.config'
        registry = self.config / 'orchestrail/projects'
        registry.parent.mkdir(parents=True)
        registry.write_text(str(self.repo) + '\n')
        self.remote = self.root / '.ai/origin.git'
        self.git(self.repo, 'init', '--bare', str(self.remote))
        self.git(self.repo, 'remote', 'add', 'origin', str(self.remote))
        self.git(self.repo, 'push', 'origin', 'main', 'feat/delivery')
        self.git(self.remote, 'symbolic-ref', 'HEAD', 'refs/heads/main')
        self.git(self.repo, 'symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        self.git(self.repo, 'branch', '--set-upstream-to=origin/main', 'main')

    def hook_environment(self) -> dict[str, str]:
        environment = self.environment()
        environment.update({'HOME': str(self.home), 'XDG_CONFIG_HOME': str(self.config)})
        return environment

    def event(self, command: str) -> dict:
        return {'session_id': 'isolated-finalization', 'hook_event_name': 'PreToolUse',
                'tool_name': 'Bash', 'tool_input': {'command': command},
                'cwd': str(self.repo), 'permission_mode': 'default'}

    def decision(self, command: str) -> str:
        before = files(self.root)
        result = CORE.decide(self.event(command), self.hook_environment())
        self.assertEqual(before, files(self.root), 'Hook decisions must be read-only')
        return result.decision

    def assert_allowed(self, command: str) -> None:
        self.assertEqual('allow', self.decision(command), command)

    def assert_guarded(self, command: str) -> None:
        self.assertIn(self.decision(command), ('ask', 'deny'), command)

    def prepared(self) -> dict:
        prior = self.prepare()
        self.receipt_path = Path(prior['hook_receipts'][0])
        self.journal_path = Path(prior['journal_path'])
        return prior

    def action(self, prior: dict, kind: str) -> str:
        return shlex.join(next(row['command'] for row in prior['actions'] if row['kind'] == kind))

    def rebind(self, journal: dict, receipt: dict) -> None:
        journal['plan_digest'] = hashlib.sha256(encoded({key: journal[key] for key in ('repositories', 'actions')})).hexdigest()
        self.journal_path.write_bytes(encoded(journal))
        receipt['journal_revision'] = hashlib.sha256(self.journal_path.read_bytes()).hexdigest()
        receipt['plan_digest'] = journal['plan_digest']
        self.receipt_path.write_bytes(encoded(receipt))

    def test_bound_normal_local_deletion_is_allowed_and_entrypoint_agrees(self) -> None:
        prior = self.prepared()
        command = self.action(prior, 'local-delete')
        self.assert_allowed(command)
        before = files(self.root)
        result = subprocess.run([sys.executable, '-I', str(SOURCE / 'hooks/git_rails.py')],
                                input=json.dumps(self.event(command)), text=True, capture_output=True,
                                env=self.hook_environment(), timeout=10)
        self.assertEqual((0, '', ''), (result.returncode, result.stdout, result.stderr))
        self.assertEqual(before, files(self.root))

    def test_bound_explicit_empty_source_remote_deletion_is_allowed(self) -> None:
        prior = self.prepared()
        self.assert_allowed(self.action(prior, 'remote-delete'))
        self.git(self.repo, 'branch', '-d', 'feat/delivery')
        self.assert_allowed(self.action(prior, 'remote-delete'))

    def test_receipts_never_authorize_broader_mutations(self) -> None:
        self.prepared()
        for command in ('git branch -D feat/delivery', 'git branch --delete --force feat/delivery',
                        'git branch -d feat/delivery unrelated', 'git branch -d main',
                        'git update-ref -d refs/heads/feat/delivery', 'git reset --hard',
                        'git rebase main', 'git merge feat/delivery', 'gh pr merge 1'):
            with self.subTest(command=command):
                self.assert_guarded(command)

    def test_remote_receipt_never_authorizes_update_force_or_implicit_lease(self) -> None:
        self.prepared()
        lease = '--force-with-lease=refs/heads/feat/delivery:' + self.tip
        for tail in (f'{lease} origin feat/delivery:refs/heads/feat/delivery',
                     f'--force {lease} origin :refs/heads/feat/delivery',
                     '--force-with-lease origin :refs/heads/feat/delivery',
                     f'{lease} origin --delete feat/delivery',
                     f'{lease} origin :refs/heads/feat/delivery :refs/heads/unrelated',
                     f'{lease} {lease} origin :refs/heads/feat/delivery',
                     '--force-with-lease=refs/heads/feat/delivery:' + self.base + ' origin :refs/heads/feat/delivery'):
            with self.subTest(tail=tail):
                self.assert_guarded('git push ' + tail)

    def test_missing_stale_and_unbound_receipts_cannot_authorize_deletion(self) -> None:
        prior = self.prepared()
        command = self.action(prior, 'local-delete')
        original = self.receipt_path.read_bytes()
        for field, value in (('task_path', str(self.task.parent / 'unrelated')),
                             ('repository', str(self.remote)), ('id', '0' * 64),
                             ('journal_revision', '0' * 64), ('plan_digest', '0' * 64),
                             ('authorization', {'cleanup': True}), ('candidates', [])):
            with self.subTest(field=field):
                receipt = json.loads(original)
                receipt[field] = value
                self.receipt_path.write_bytes(encoded(receipt))
                self.assert_guarded(command)
        self.receipt_path.unlink()
        self.assert_guarded(command)

    def test_journal_scope_and_authorization_are_checked_after_hash_binding(self) -> None:
        prior = self.prepared()
        original_journal = json.loads(self.journal_path.read_bytes())
        original_receipt = json.loads(self.receipt_path.read_bytes())
        for change in ('no-action', 'no-authorization', 'wrong-task', 'candidate-drift', 'integration-drift'):
            with self.subTest(change=change):
                journal, receipt = copy.deepcopy(original_journal), copy.deepcopy(original_receipt)
                if change == 'no-action':
                    journal['actions'] = []
                elif change == 'no-authorization':
                    journal['authorization']['cleanup'] = False
                    receipt['authorization'] = journal['authorization']
                elif change == 'wrong-task':
                    journal['task_original'] = str(self.task.parent / 'other')
                elif change == 'candidate-drift':
                    journal['repositories'][0]['candidates'][0]['expected_tip'] = self.base
                else:
                    journal['repositories'][0]['integration']['tip'] = self.base
                    receipt['integration'] = journal['repositories'][0]['integration']
                self.rebind(journal, receipt)
                self.assert_guarded(self.action(prior, 'local-delete'))

    def test_pack_change_missing_or_symlink_blocks_otherwise_valid_receipt(self) -> None:
        prior = self.prepared()
        receipt = json.loads(self.receipt_path.read_bytes())
        pack = Path(receipt['recovery']['pack_path'])
        original = pack.read_bytes()
        for state in ('changed', 'missing', 'symlink'):
            with self.subTest(state=state):
                if pack.exists() or pack.is_symlink():
                    pack.unlink()
                if state == 'changed':
                    pack.write_bytes(original + b'changed')
                elif state == 'symlink':
                    other = pack.with_suffix('.copy')
                    other.write_bytes(original)
                    pack.symlink_to(other)
                self.assert_guarded(self.action(prior, 'local-delete'))

    def test_changed_local_tip_integration_tip_and_worktrees_block(self) -> None:
        prior = self.prepared()
        command = self.action(prior, 'local-delete')
        self.git(self.repo, 'branch', '-f', 'feat/delivery', self.base)
        self.assert_guarded(command)
        self.git(self.repo, 'branch', '-f', 'feat/delivery', self.tip)
        worktree = self.root / '.ai/linked-worktree'
        self.git(self.repo, 'worktree', 'add', str(worktree), 'feat/delivery')
        self.assert_guarded(command)
        self.git(self.repo, 'worktree', 'remove', str(worktree))
        self.git(self.repo, 'commit', '--allow-empty', '-m', 'chore: advance integration')
        self.assert_guarded(command)

    def test_current_protection_and_prior_same_command_write_block(self) -> None:
        prior = self.prepared()
        self.assert_guarded('touch .ai/earlier-write; ' + self.action(prior, 'local-delete'))
        self.git(self.repo, 'config', '--add', 'orchestrail.protectedBranch', 'feat/*')
        self.assert_guarded(self.action(prior, 'local-delete'))
        self.assert_guarded(self.action(prior, 'remote-delete'))

    def test_checkout_plan_uses_safe_switch_and_configured_upstream_only(self) -> None:
        self.git(self.repo, 'checkout', 'feat/delivery')
        self.git(self.repo, 'branch', '-f', 'main', self.base)
        broad_switch = 'git switch --discard-changes main'
        baseline = self.decision(broad_switch)
        prior = self.prepared()
        self.assertEqual(['git', '-C', str(self.repo), 'switch', '--no-overwrite-ignore', 'main'],
                         next(row['command'] for row in prior['actions'] if row['kind'] == 'checkout'))
        self.assertEqual(baseline, self.decision(broad_switch), 'Receipts must not expand generic permissions')
        self.assert_allowed(self.action(prior, 'checkout'))
        self.git(self.repo, 'switch', '--no-overwrite-ignore', 'main')
        self.assert_allowed(self.action(prior, 'refresh'))
        for command in ('git pull --ff-only origin main', 'git pull --ff-only --no-ff',
                        'git pull --rebase', 'git switch -C main'):
            with self.subTest(command=command):
                self.assert_guarded(command)

    def test_generic_verifier_interfaces_are_preserved(self) -> None:
        self.assertIs(CORE.DELETION_VERIFIER, CORE.no_exception_verifier)
        self.assertIs(CORE.LEASE_VERIFIER, CORE.journal_lease_verifier)


class StagingChecks(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile
        self.temporary = tempfile.TemporaryDirectory(prefix='finalization-staging-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        for name in ('scripts', 'hooks', 'workflows', 'rules', 'principles', 'templates', 'harness'):
            shutil.copytree(SOURCE / name, self.source / name, ignore=shutil.ignore_patterns('__pycache__'))
        self.home = self.root / 'home'
        project = self.home / 'projects/product'
        (project / '.devin/rules').mkdir(parents=True)
        (project / '.devin/rules/sentinel').write_text('preserve live project\n')
        (project / '.windsurf/workflows').mkdir(parents=True)
        (project / '.windsurf/workflows/phase-discovery.md').write_text('preserve local copy\n')
        self.stage = self.root / 'stage'
        self.calls = self.root / 'calls'
        self.environment = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / '.config'),
                                ORCHESTRAIL_HOME=str(self.source), FIXTURE_CALLS=str(self.calls))
        self.preflights = ('check-phase-finalize.py', 'check-finalization-safety.py', 'check-finalization-workflow.py')
        validator = self.source / 'scripts/validate-contracts.sh'
        validator.write_text('#!/bin/bash\nprintf "validator\\n" >> "$FIXTURE_CALLS"\n')
        for name in self.preflights:
            (self.source / 'scripts' / name).write_text('import os\nfrom pathlib import Path\n'
                f'with Path(os.environ["FIXTURE_CALLS"]).open("a") as output:\n    output.write("{name}\\n")\n')
        (self.source / 'scripts/install-hooks.sh').write_text('#!/bin/bash\nprintf "HOOK-INSTALL\\n" >> "$FIXTURE_CALLS"\n')

    def sync(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(['bash', str(self.source / 'scripts/sync.sh'), '--from', str(self.source),
                               '--stage', str(self.stage), *extra], cwd=self.root,
                              capture_output=True, text=True, env=self.environment, timeout=30)

    def test_staging_generates_every_provider_without_live_writes_or_hook_install(self) -> None:
        before = files(self.home)
        result = self.sync()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, files(self.home), 'Staging must not deploy or scan/update live projects')
        self.assertEqual(['validator', *self.preflights], self.calls.read_text().splitlines())
        for source in (self.source / 'workflows').glob('*.md'):
            for destination in (self.stage / '.codeium/windsurf/global_workflows' / source.name,
                                self.stage / '.claude/skills' / source.stem / 'SKILL.md',
                                self.stage / '.codex/skills' / source.stem / 'SKILL.md'):
                self.assertEqual(source.read_bytes(), destination.read_bytes(), str(destination))
        for folder, prefix in (('rules', 'rule-'), ('principles', 'principle-')):
            for source in (self.source / folder).glob('*.md'):
                for destination in (self.stage / '.codeium/windsurf/global_rules' / source.name,
                                    self.stage / '.claude/skills' / (prefix + source.stem) / 'SKILL.md',
                                    self.stage / '.codex/skills' / (prefix + source.stem) / 'SKILL.md'):
                    self.assertEqual(source.read_bytes(), destination.read_bytes())
        for destination in (self.stage / '.claude/CLAUDE.md', self.stage / '.codex/AGENTS.md'):
            self.assertIn('installation-result:', destination.read_text())
            self.assertNotIn('"status":"installed"', destination.read_text())

    def test_missing_or_failing_mandatory_preflight_blocks_all_output(self) -> None:
        for name in self.preflights:
            with self.subTest(name=name):
                path = self.source / 'scripts' / name
                original = path.read_bytes()
                path.unlink()
                result = self.sync()
                self.assertNotEqual(0, result.returncode, result.stdout)
                self.assertFalse(self.stage.exists())
                path.write_text('raise SystemExit(7)\n')
                result = self.sync()
                self.assertNotEqual(0, result.returncode, result.stdout)
                self.assertFalse(self.stage.exists())
                path.write_bytes(original)

    def test_unknown_options_and_unsafe_staging_destinations_fail_before_writes(self) -> None:
        before = files(self.home)
        for arguments in (('--unknown',), ('--stage', str(self.home)), ('--stage', str(self.source)),
                          ('--stage', str(self.source / 'nested-output'))):
            with self.subTest(arguments=arguments):
                result = self.sync(*arguments)
                self.assertNotEqual(0, result.returncode, result.stdout)
                self.assertEqual(before, files(self.home))

    def test_project_setup_and_refresh_lists_include_finalization_context(self) -> None:
        for name in ('setup-new-project.sh', 'sync.sh'):
            text = (SOURCE / 'scripts' / name).read_text()
            self.assertEqual(2, text.count('phase-finalize.md'), name)


if __name__ == '__main__':
    # The reused fixture also owns its separate evidence suite; run only this suite's tests.
    suite = unittest.TestSuite()
    selected = sys.argv[1:]
    for case in (SafetyChecks, StagingChecks):
        for name in sorted(case.__dict__):
            if name.startswith('test_') and (not selected or name in selected or case.__name__ in selected):
                suite.addTest(case(name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
