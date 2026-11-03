#!/usr/bin/env bash
# Exercise the git-rails decision core in disposable repositories only.
# Contract: every case runs offline against fixture repositories and registry files
# under a temporary root with isolated HOME and XDG_CONFIG_HOME, and asserts that the
# core leaves .git/, the work tree, .ai/ and the registry byte-identical.
# Usage: bash tests/git-rails.sh [test-name ...]. Exit 0 = all pass, 1 = failures.
set -uo pipefail
git_rails_source="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
python3 - "$git_rails_source" "$@" <<'PY'
from __future__ import annotations

import ast
from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from types import ModuleType
from typing import Any, Callable
import unittest

# Any types values read from the dynamically loaded core; the tests assert their shape.

SOURCE = Path(sys.argv[1])
SELECTED = sys.argv[2:]
CORE_PATH = SOURCE / 'hooks/git_rails.py'
RULE_PATH_TEXT = 'rules/git-flow.md → ## Safety rails'
REAL_GIT = shutil.which('git') or '/usr/bin/git'
Snapshot = dict[str, tuple[str, int, int, bytes]]
Record = tuple[str, 'str | None', tuple[str, ...], str, 'str | None']


def load_core() -> tuple[ModuleType | None, str]:
    if not CORE_PATH.is_file():
        return None, 'hooks/git_rails.py does not exist'
    spec = importlib.util.spec_from_file_location('git_rails', CORE_PATH)
    if spec is None or spec.loader is None:
        return None, 'hooks/git_rails.py cannot be loaded as a module'
    module = importlib.util.module_from_spec(spec)
    sys.modules['git_rails'] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:  # every test reports the load failure as its assertion
        sys.modules.pop('git_rails', None)
        return None, f'{type(error).__name__}: {error}'
    return module, ''


CORE, CORE_LOAD_ERROR = load_core()


def snapshot(root: Path) -> Snapshot:
    """Content, mode and modification time of every entry below root."""
    entries: Snapshot = {}
    for directory, folders, files in os.walk(root):
        folders.sort()
        for name in sorted(folders + files):
            path = Path(directory) / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                kind, data = 'link', os.readlink(path).encode()
            elif stat.S_ISREG(info.st_mode):
                kind = 'file'
                try:
                    data = path.read_bytes()
                except PermissionError:
                    data = b'<unreadable>'
            else:
                kind, data = 'directory', b''
            entries[str(path.relative_to(root))] = (kind, info.st_mode, info.st_mtime_ns, data)
    return entries


@dataclass(frozen=True)
class DecisionCase:
    """One table row: setup, cwd, command, permission mode, expected decision."""
    name: str
    command: str
    decision: str
    reason: str | None = None
    rule: str | None = None
    cwd: str = 'project'
    setup: str = 'standard'
    mode: str = 'default'


@dataclass(frozen=True)
class ResolutionCase:
    """One table row: the invocation records a command resolves to."""
    name: str
    command: str
    expected: tuple[Record, ...]
    cwd: str = 'project'
    setup: str = 'standard'


class RailsFixture(unittest.TestCase):
    scratch: tempfile.TemporaryDirectory[str]
    world: Path
    probe: Path
    home: Path
    config: Path
    registry: Path
    project: Path
    outside: Path
    plain: Path
    inner: Path
    roots: tuple[str, ...]
    environ: dict[str, str]
    git_environ: dict[str, str]

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory(prefix='git rails ')
        self.addCleanup(self.scratch.cleanup)
        base = Path(os.path.realpath(self.scratch.name))
        self.world = base / 'world'
        self.probe = base / 'probe'
        (self.probe / 'bin').mkdir(parents=True)
        self.home = self.world / 'home'
        self.config = self.world / 'config'
        self.registry = self.config / 'orchestrail/projects'
        self.project = self.world / 'project one'
        self.outside = self.world / 'outside'
        self.plain = self.world / 'plain'
        self.inner = self.project / 'inner'
        self.home.mkdir(parents=True)
        self.registry.parent.mkdir(parents=True)
        self.git_environ = {'HOME': str(self.home), 'XDG_CONFIG_HOME': str(self.config),
                            'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'LC_ALL': 'C',
                            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_AUTHOR_NAME': 'Fixture',
                            'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
                            'GIT_COMMITTER_NAME': 'Fixture',
                            'GIT_COMMITTER_EMAIL': 'fixture@example.invalid'}
        self.make_repository(self.project, {'a.txt': 'a\n', 'b.txt': 'b\n', 'sub/a.txt': 'sub\n',
                                            'sub/deeper/b.txt': 'deep\n', '.ai/state.md': 'state\n'})
        self.make_repository(self.outside, {'a.txt': 'outside\n'})
        self.plain.mkdir()
        (self.plain / 'note.txt').write_text('not a repository\n')
        self.write_registry([self.project, self.plain])
        self.environ = {key: self.git_environ[key]
                        for key in ('HOME', 'XDG_CONFIG_HOME', 'PATH', 'LC_ALL', 'GIT_CONFIG_NOSYSTEM')}

    def git(self, directory: Path, *arguments: str) -> None:
        subprocess.run([REAL_GIT, *arguments], cwd=directory, env=self.git_environ, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def make_repository(self, directory: Path, files: dict[str, str]) -> None:
        directory.mkdir(parents=True)
        self.git(directory, 'init', '-q', '-b', 'main')
        for name, text in files.items():
            (directory / name).parent.mkdir(parents=True, exist_ok=True)
            (directory / name).write_text(text)
        self.git(directory, 'add', '--', *files)
        self.git(directory, 'commit', '-q', '-m', 'initial')

    def write_registry(self, roots: list[Path]) -> None:
        self.roots = tuple(str(root) for root in roots)
        self.registry.write_text(''.join(root + '\n' for root in self.roots))

    def location(self, key: str) -> str:
        places = {'project': self.project, 'sub': self.project / 'sub',
                  'deeper': self.project / 'sub/deeper', 'outside': self.outside,
                  'plain': self.plain, 'inner': self.inner}
        return str(places[key])

    def render(self, command: str) -> str:
        for key in ('project', 'outside', 'plain', 'inner'):
            command = command.replace('@' + key + '@', shlex.quote(self.location(key)))
        return command.replace('@git@', shlex.quote(REAL_GIT))

    def api(self, name: str) -> Any:
        if CORE is None:
            self.fail('decision core is not importable: ' + CORE_LOAD_ERROR)
        if not hasattr(CORE, name):
            self.fail('decision core must expose ' + name)
        return getattr(CORE, name)

    def event(self, command: str, cwd: str, mode: str = 'default') -> dict[str, object]:
        return {'session_id': 'fixture', 'hook_event_name': 'PreToolUse', 'tool_name': 'Bash',
                'tool_input': {'command': command, 'description': 'fixture'},
                'cwd': cwd, 'permission_mode': mode}

    def decide(self, event: object, environ: dict[str, str] | None = None) -> tuple[str, str | None, str | None]:
        decide = self.api('decide')
        before = snapshot(self.world)
        result = decide(event, dict(self.environ if environ is None else environ))
        self.assertEqual(before, snapshot(self.world),
                         'deciding must leave .git, the work tree, .ai and the registry unchanged')
        return result.decision, result.reason_code, result.rule_id

    def resolve(self, command: str, cwd: str) -> Any:
        resolve = self.api('resolve')
        context = self.api('Context')(cwd=cwd, roots=self.roots, environ=dict(self.environ))
        before = snapshot(self.world)
        resolution = resolve(command, context)
        self.assertEqual(before, snapshot(self.world),
                         'resolving must leave .git, the work tree, .ai and the registry unchanged')
        return resolution

    def records(self, resolution: Any) -> tuple[Record, ...]:
        return tuple((item.program, item.subcommand, tuple(item.argv), item.directory, item.repository)
                     for item in resolution.invocations)

    # Named setups referenced by the case tables.
    def setup_standard(self) -> None:
        return None

    def setup_nested(self) -> None:
        self.make_repository(self.inner, {'c.txt': 'inner\n'})
        self.write_registry([self.project, self.project / 'inner', self.plain])

    def setup_alias(self) -> None:
        self.git(self.project, 'config', 'alias.p', 'status')

    def setup_symlinks(self) -> None:
        for name in ('lnk', 'lnk2'):
            (self.project / name).symlink_to(self.outside, target_is_directory=True)

    def setup_registry_missing(self) -> None:
        self.registry.unlink()

    def setup_registry_directory(self) -> None:
        self.registry.unlink()
        self.registry.mkdir()

    def setup_registry_unreadable(self) -> None:
        if os.geteuid() == 0:
            self.skipTest('file permissions do not restrict the superuser')
        self.registry.chmod(0)
        self.addCleanup(self.registry.chmod, 0o600)

    def setup_registry_not_utf8(self) -> None:
        self.registry.write_bytes(f'{self.project}\n'.encode() + b'/\xff\xfe\n')

    def setup_registry_empty_line(self) -> None:
        self.registry.write_text(f'{self.project}\n\n{self.plain}\n')

    def setup_registry_carriage_return(self) -> None:
        self.registry.write_text(f'{self.project}\r\n{self.plain}\n')

    def setup_registry_nul(self) -> None:
        self.registry.write_text(f'{self.project}\n{self.plain}\x00tail\n')

    def setup_registry_relative(self) -> None:
        self.registry.write_text(f'{self.project}\nrelative/root\n')

    def setup_registry_symlink(self) -> None:
        link = self.world / 'project link'
        link.symlink_to(self.project, target_is_directory=True)
        self.registry.write_text(f'{link}\n')

    def setup_registry_dot_segment(self) -> None:
        self.registry.write_text(f'{self.project}/../{self.project.name}\n')

    def setup_registry_trailing_slash(self) -> None:
        self.registry.write_text(f'{self.project}/\n')

    def setup_registry_nonexistent_root(self) -> None:
        self.registry.write_text(f'{self.world / "removed project"}\n{self.project}\n')

    def setup_registry_without_final_newline(self) -> None:
        self.registry.write_text(f'{self.plain}\n{self.project}')

    def setup_registry_zero_bytes(self) -> None:
        self.registry.write_bytes(b'')

    def setup_registry_filesystem_root(self) -> None:
        self.registry.write_text('/\n')

    def setup_registry_home_fallback(self) -> None:
        self.registry.unlink()
        fallback = self.home / '.config/orchestrail/projects'
        fallback.parent.mkdir(parents=True)
        fallback.write_text(f'{self.project}\n')
        del self.environ['XDG_CONFIG_HOME']

    def setup_registry_empty_config_home(self) -> None:
        self.setup_registry_home_fallback()
        self.environ['XDG_CONFIG_HOME'] = ''

    def apply_setup(self, name: str) -> None:
        getattr(self, 'setup_' + name.replace('-', '_'))()


TOKENS_AT_LIMIT = 'git status ' + ' '.join(['x'] * 4094)
TOKENS_OVER_LIMIT = TOKENS_AT_LIMIT + ' x'
COMMIT_HEREDOC = "git commit -m \"$(cat <<'EOF'\nSubject line\n\nBody text.\nEOF\n)\""

DECISION_CASES: tuple[DecisionCase, ...] = (
    # Registry gate.
    DecisionCase('unregistered_cwd_without_registered_target_is_not_applicable',
                 'git -c x=y push', 'not_applicable', cwd='outside'),
    DecisionCase('registered_target_from_unregistered_cwd_is_decided_in_that_project',
                 'git -C @project@ -c x=y push', 'deny', 'unsupported-form', 'R31', cwd='outside'),
    DecisionCase('target_outside_registered_projects_is_dropped',
                 'git -C @outside@ -c x=y push', 'not_applicable'),
    DecisionCase('cd_to_unregistered_directory_drops_the_invocation',
                 'cd @outside@ && git -c x=y push', 'not_applicable'),
    DecisionCase('registered_directory_outside_a_work_tree_is_not_applicable',
                 'cd @plain@ && git -c x=y push', 'not_applicable'),
    DecisionCase('missing_registry_is_not_applicable',
                 'git -c x=y push', 'not_applicable', setup='registry-missing'),
    DecisionCase('registry_that_is_a_directory_is_a_registry_error',
                 'git status', 'deny', 'registry-error', setup='registry-directory'),
    DecisionCase('unreadable_registry_is_a_registry_error',
                 'git status', 'deny', 'registry-error', setup='registry-unreadable'),
    DecisionCase('non_utf8_registry_is_a_registry_error',
                 'git status', 'deny', 'registry-error', setup='registry-not-utf8'),
    DecisionCase('registry_with_empty_line_is_a_registry_error',
                 'git status', 'deny', 'registry-error', setup='registry-empty-line'),
    DecisionCase('registry_with_carriage_return_is_a_registry_error',
                 'git status', 'deny', 'registry-error', setup='registry-carriage-return'),
    DecisionCase('registry_with_nul_is_a_registry_error',
                 'git status', 'deny', 'registry-error', setup='registry-nul'),
    DecisionCase('registry_with_relative_line_is_a_registry_error',
                 'git status', 'deny', 'registry-error', setup='registry-relative'),
    DecisionCase('registry_with_symlinked_root_is_a_registry_error',
                 'git status', 'deny', 'registry-error', setup='registry-symlink'),
    DecisionCase('registry_with_dot_segment_is_a_registry_error',
                 'git status', 'deny', 'registry-error', setup='registry-dot-segment'),
    DecisionCase('registry_with_trailing_slash_is_a_registry_error',
                 'git status', 'deny', 'registry-error', setup='registry-trailing-slash'),
    DecisionCase('invalid_registry_denies_relevant_commands_in_any_directory',
                 'git status', 'deny', 'registry-error', cwd='outside', setup='registry-empty-line'),
    DecisionCase('nonexistent_canonical_root_is_not_malformed',
                 'git -c x=y push', 'deny', 'unsupported-form', 'R31', setup='registry-nonexistent-root'),
    DecisionCase('registry_without_final_newline_is_valid',
                 'git -c x=y push', 'deny', 'unsupported-form', 'R31',
                 setup='registry-without-final-newline'),
    DecisionCase('zero_byte_registry_registers_nothing',
                 'git -c x=y push', 'not_applicable', setup='registry-zero-bytes'),
    DecisionCase('filesystem_root_registers_every_directory',
                 'git -c x=y push', 'deny', 'unsupported-form', 'R31', cwd='outside',
                 setup='registry-filesystem-root'),
    DecisionCase('registry_falls_back_to_home_config_without_config_home',
                 'git -c x=y push', 'deny', 'unsupported-form', 'R31', setup='registry-home-fallback'),
    DecisionCase('registry_falls_back_to_home_config_for_empty_config_home',
                 'git -c x=y push', 'deny', 'unsupported-form', 'R31',
                 setup='registry-empty-config-home'),
    # Supported grammar decisions that no later rule changes.
    DecisionCase('pipeline_of_read_only_git_is_not_applicable', 'git status | head', 'not_applicable'),
    DecisionCase('subshell_staging_of_existing_file_is_allowed', '(cd sub; git add a.txt)', 'allow'),
    DecisionCase('empty_command_is_not_applicable', '', 'not_applicable'),
    DecisionCase('whitespace_command_is_not_applicable', ' \t\n ', 'not_applicable'),
    DecisionCase('quoted_git_word_in_other_program_is_not_an_invocation',
                 "echo 'git -c x=y push'", 'not_applicable'),
    DecisionCase('dynamic_argument_of_other_program_is_accepted',
                 'echo "$HOME" ~ *.txt; git status', 'not_applicable'),
    DecisionCase('dynamic_argument_of_read_only_git_is_accepted',
                 'git log "$REF"', 'not_applicable'),
    DecisionCase('unsupported_global_option_on_read_only_git_is_accepted',
                 'git -c x=y status', 'not_applicable'),
    DecisionCase('unsupported_global_option_on_read_only_builtin_skips_alias_check',
                 'git -c x=y log', 'not_applicable'),
    DecisionCase('git_assignment_on_read_only_git_is_accepted',
                 'GIT_DIR=x git status', 'not_applicable'),
    DecisionCase('accepted_global_options_on_governed_git_are_supported',
                 'git --no-pager -P -p --no-optional-locks --literal-pathspecs add a.txt', 'allow'),
    DecisionCase('literal_leading_assignment_on_governed_git_is_supported',
                 'LC_ALL=C git add a.txt', 'allow'),
    DecisionCase('commit_message_heredoc_form_is_supported', COMMIT_HEREDOC, 'allow'),
    DecisionCase('undefined_unlisted_subcommand_is_not_applicable', 'git p', 'not_applicable'),
    DecisionCase('quoted_program_word_is_an_invocation', "'git' -c x=y push",
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('escaped_program_word_is_an_invocation', '\\git -c x=y push',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('absolute_git_path_is_an_invocation', '@git@ -c x=y push',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('wrapped_invocation_is_analyzed', 'command env X=1 nohup time git -c x=y push',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('timeout_duration_wrapper_is_analyzed', 'timeout 2m git -c x=y push',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('exec_wrapper_is_analyzed', 'exec git -c x=y push', 'deny', 'unsupported-form', 'R31'),
    DecisionCase('literal_shell_string_is_analyzed', "bash -c 'git -c x=y push'",
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('command_substitution_is_analyzed', 'echo "$(git -c x=y push)"',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('backtick_substitution_is_analyzed', 'echo `git -c x=y push`',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('substitution_in_unquoted_heredoc_is_analyzed',
                 'cat <<EOF\n$(git -c x=y push)\nEOF', 'deny', 'unsupported-form', 'R31'),
    DecisionCase('whole_command_takes_the_most_severe_result',
                 'git add a.txt; git status; git -c x=y push', 'deny', 'unsupported-form', 'R31'),
    # Opaque forms.
    DecisionCase('eval_is_unsupported', 'eval "git push"', 'deny', 'unsupported-form'),
    DecisionCase('dynamic_shell_string_is_unsupported', 'sh -c "$C"', 'deny', 'unsupported-form'),
    DecisionCase('substituted_shell_string_is_unsupported', 'bash -c "$(echo git push)"',
                 'deny', 'unsupported-form'),
    DecisionCase('dynamic_program_word_is_unsupported', '$G push', 'deny', 'unsupported-form'),
    DecisionCase('substituted_program_word_is_unsupported', '"$(which git)" push',
                 'deny', 'unsupported-form'),
    DecisionCase('xargs_is_unsupported', 'xargs git add', 'deny', 'unsupported-form'),
    DecisionCase('for_loop_is_unsupported', 'for f in a; do git add "$f"; done',
                 'deny', 'unsupported-form'),
    DecisionCase('while_loop_is_unsupported', 'while true; do git status; done',
                 'deny', 'unsupported-form'),
    DecisionCase('if_statement_is_unsupported', 'if true; then git status; fi',
                 'deny', 'unsupported-form'),
    DecisionCase('case_statement_is_unsupported', 'case x in x) git status;; esac',
                 'deny', 'unsupported-form'),
    DecisionCase('function_definition_is_unsupported', 'f() { git push; }; f',
                 'deny', 'unsupported-form'),
    DecisionCase('sudo_is_unsupported', 'sudo git push', 'deny', 'unsupported-form'),
    DecisionCase('relative_program_path_is_unsupported', './git push', 'deny', 'unsupported-form'),
    DecisionCase('source_is_unsupported', 'source env.sh; git status', 'deny', 'unsupported-form'),
    DecisionCase('dot_source_is_unsupported', '. env.sh; git status', 'deny', 'unsupported-form'),
    DecisionCase('find_exec_is_unsupported', 'find . -exec git add {} \\;', 'deny', 'unsupported-form'),
    DecisionCase('parallel_is_unsupported', 'parallel git add ::: a.txt', 'deny', 'unsupported-form'),
    DecisionCase('watch_is_unsupported', 'watch git status', 'deny', 'unsupported-form'),
    DecisionCase('process_substitution_is_unsupported', 'diff <(git show HEAD:a.txt) a.txt',
                 'deny', 'unsupported-form'),
    DecisionCase('opaque_construct_anywhere_in_the_command_is_unsupported',
                 'git status; eval x', 'deny', 'unsupported-form'),
    DecisionCase('env_with_options_is_unsupported', 'env -i git push', 'deny', 'unsupported-form'),
    DecisionCase('timeout_without_duration_is_unsupported', 'timeout git push',
                 'deny', 'unsupported-form'),
    DecisionCase('timeout_with_options_is_unsupported', 'timeout -s KILL 5 git push',
                 'deny', 'unsupported-form'),
    DecisionCase('dynamic_cd_makes_later_invocations_unsupported', 'cd "$D" && git status',
                 'deny', 'unsupported-form'),
    DecisionCase('cd_without_argument_makes_later_invocations_unsupported', 'cd && git status',
                 'deny', 'unsupported-form'),
    DecisionCase('governed_invocation_in_missing_directory_is_unsupported',
                 'cd missing; git add a.txt', 'deny', 'unsupported-form'),
    DecisionCase('read_only_invocation_in_missing_directory_is_not_applicable',
                 'cd missing; git status', 'not_applicable'),
    DecisionCase('login_shell_string_is_unsupported', "bash -lc 'git add a.txt'",
                 'deny', 'unsupported-form'),
    DecisionCase('shell_string_after_other_shell_option_is_unsupported', "bash -l -c 'git add a.txt'",
                 'deny', 'unsupported-form'),
    DecisionCase('command_lookup_is_unsupported', 'command -v git', 'deny', 'unsupported-form'),
    DecisionCase('zsh_string_is_unsupported', "zsh -c 'git status'", 'deny', 'unsupported-form'),
    DecisionCase('dash_string_is_unsupported', "dash -c 'git status'", 'deny', 'unsupported-form'),
    DecisionCase('ksh_string_is_unsupported', "ksh -c 'git status'", 'deny', 'unsupported-form'),
    DecisionCase('mksh_string_is_unsupported', "mksh -c 'git status'", 'deny', 'unsupported-form'),
    DecisionCase('absolute_other_shell_string_is_unsupported', "/usr/bin/zsh -c 'git status'",
                 'deny', 'unsupported-form'),
    DecisionCase('unterminated_single_quote_is_unsupported', "git push 'origin",
                 'deny', 'unsupported-form'),
    DecisionCase('unterminated_double_quote_is_unsupported', 'git push "origin',
                 'deny', 'unsupported-form'),
    DecisionCase('unbalanced_group_is_unsupported', '(git status', 'deny', 'unsupported-form'),
    DecisionCase('opaque_form_from_unregistered_cwd_is_not_applicable', 'eval "git push"',
                 'not_applicable', cwd='outside'),
    DecisionCase('parse_failure_from_unregistered_cwd_is_not_applicable', "git push 'origin",
                 'not_applicable', cwd='outside'),
    # Governed-invocation rule R31.
    DecisionCase('unsupported_global_option_on_governed_git_is_unsupported', 'git -c x=y push',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('git_dir_option_on_governed_git_is_unsupported', 'git --git-dir=x push',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('work_tree_option_on_governed_git_is_unsupported', 'git --work-tree x add a.txt',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('defined_alias_is_unsupported', 'git p', 'deny', 'unsupported-form', 'R31',
                 setup='alias'),
    DecisionCase('alias_defined_by_global_option_is_unsupported', 'git -c alias.p=push p',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('git_assignment_on_governed_git_is_opaque_environment', 'GIT_DIR=x git commit -m ok',
                 'deny', 'opaque-environment', 'R31'),
    DecisionCase('git_assignment_through_env_is_opaque_environment', 'env GIT_DIR=x git commit -m ok',
                 'deny', 'opaque-environment', 'R31'),
    DecisionCase('dynamic_argument_on_governed_git_is_unsupported', 'git push "$X"',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('dynamic_directory_option_on_governed_git_is_unsupported', 'git -C "$D" push',
                 'deny', 'unsupported-form'),
    DecisionCase('dynamic_subcommand_is_unsupported', 'git $SUB', 'deny', 'unsupported-form'),
    DecisionCase('dynamic_assignment_on_governed_git_is_unsupported', 'X=$Y git push',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('dynamic_git_assignment_on_governed_git_is_opaque_environment', 'GIT_DIR=$Y git push',
                 'deny', 'opaque-environment', 'R31'),
    DecisionCase('exported_git_variable_before_governed_git_is_opaque_environment',
                 'export GIT_DIR=x; git commit -m ok', 'deny', 'opaque-environment', 'R31'),
    DecisionCase('declared_git_export_before_governed_git_is_opaque_environment',
                 'declare -x GIT_DIR=x; git add a.txt', 'deny', 'opaque-environment', 'R31'),
    DecisionCase('typeset_git_export_before_governed_git_is_opaque_environment',
                 'typeset -x GIT_DIR=x; git add a.txt', 'deny', 'opaque-environment', 'R31'),
    DecisionCase('bare_git_assignment_before_governed_git_is_opaque_environment',
                 'GIT_WORK_TREE=y; git add a.txt', 'deny', 'opaque-environment', 'R31'),
    DecisionCase('git_export_inside_subshell_does_not_reach_later_commands',
                 '(export GIT_DIR=x); git add a.txt', 'allow'),
    DecisionCase('git_export_before_read_only_git_is_not_applicable',
                 'export GIT_DIR=x; git status', 'not_applicable'),
    DecisionCase('other_export_before_governed_git_is_supported',
                 'export FOO=1; git add a.txt', 'allow'),
    DecisionCase('brace_expansion_on_governed_git_is_unsupported', 'git add {a,b}.txt',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('heredoc_substitution_outside_commit_is_unsupported',
                 "git push origin \"$(cat <<'D'\nmain\nD\n)\"", 'deny', 'unsupported-form', 'R31'),
    DecisionCase('dynamic_governed_gh_argument_is_unsupported', 'gh api "$ENDPOINT"',
                 'deny', 'unsupported-form'),
    # Limits.
    DecisionCase('recursion_depth_at_limit_is_supported', '( ( ( git status ) ) )', 'not_applicable'),
    DecisionCase('recursion_depth_over_limit_is_limit_exceeded', '( ( ( ( git status ) ) ) )',
                 'deny', 'limit-exceeded'),
    DecisionCase('mixed_recursion_over_limit_is_limit_exceeded',
                 "bash -c 'echo $( ( { git status; } ) )'", 'deny', 'limit-exceeded'),
    DecisionCase('recursion_over_limit_from_unregistered_cwd_is_not_applicable',
                 '( ( ( ( git status ) ) ) )', 'not_applicable', cwd='outside'),
    DecisionCase('token_count_at_limit_is_supported', TOKENS_AT_LIMIT, 'not_applicable'),
    DecisionCase('token_count_over_limit_is_limit_exceeded', TOKENS_OVER_LIMIT,
                 'deny', 'limit-exceeded'),
)


def decision_test(case: DecisionCase) -> Callable[[RailsFixture], None]:
    def test(self: RailsFixture) -> None:
        self.apply_setup(case.setup)
        event = self.event(self.render(case.command), self.location(case.cwd), case.mode)
        decision, reason, rule = self.decide(event)
        self.assertEqual((decision, reason), (case.decision, case.reason), case.command)
        if case.rule is not None:
            self.assertEqual(rule, case.rule, case.command)
    return test


class DecisionTable(RailsFixture):
    """Table-driven decisions of the whole frame: event, registry, parse, resolve, R31."""


for decision_case in DECISION_CASES:
    setattr(DecisionTable, 'test_' + decision_case.name, decision_test(decision_case))


def status(directory: str, repository: str = 'project') -> Record:
    return ('git', 'status', (), directory, repository)


RESOLUTION_CASES: tuple[ResolutionCase, ...] = (
    ResolutionCase('cd_then_blanket_staging', 'cd sub && git add -A',
                   (('git', 'add', ('-A',), 'sub', 'project'),)),
    ResolutionCase('subshell_cd_applies_inside', '(cd sub; git add a.txt)',
                   (('git', 'add', ('a.txt',), 'sub', 'project'),)),
    ResolutionCase('subshell_cd_does_not_leak', '(cd sub; git add a.txt); git status',
                   (('git', 'add', ('a.txt',), 'sub', 'project'), status('project'))),
    ResolutionCase('brace_group_cd_leaks', '{ cd sub; }; git status', (status('sub'),)),
    ResolutionCase('pipeline_cd_does_not_leak', 'cd sub | true; git status', (status('project'),)),
    ResolutionCase('background_cd_does_not_leak', 'cd sub & git status', (status('project'),)),
    ResolutionCase('literal_shell_string', "bash -c 'git add .'",
                   (('git', 'add', ('.',), 'project', 'project'),)),
    ResolutionCase('literal_shell_string_has_its_own_directory', "sh -c 'cd sub && git status'; git status",
                   (status('sub'), status('project'))),
    ResolutionCase('command_wrapper', 'command git add --all',
                   (('git', 'add', ('--all',), 'project', 'project'),)),
    ResolutionCase('env_assignment_wrapper', 'env X=1 git commit -am x',
                   (('git', 'commit', ('-am', 'x'), 'project', 'project'),)),
    ResolutionCase('timeout_wrapper', 'timeout 30 git push -f',
                   (('git', 'push', ('-f',), 'project', 'project'),)),
    ResolutionCase('timeout_wrapper_with_unit', 'timeout 2m git status', (status('project'),)),
    ResolutionCase('nohup_time_and_exec_wrappers', 'nohup git status; time git log; exec git diff',
                   (status('project'), ('git', 'log', (), 'project', 'project'),
                    ('git', 'diff', (), 'project', 'project'))),
    ResolutionCase('pipeline_elements', 'git status | head', (status('project'),)),
    ResolutionCase('list_operators_and_newlines', 'git status && git log || git diff\ngit show & git status',
                   (status('project'), ('git', 'log', (), 'project', 'project'),
                    ('git', 'diff', (), 'project', 'project'), ('git', 'show', (), 'project', 'project'),
                    status('project'))),
    ResolutionCase('cd_parent', 'cd sub; cd ..; git status', (status('project'),)),
    ResolutionCase('directory_option_relative_to_cd', 'cd sub/deeper && git -C .. status', (status('sub'),)),
    ResolutionCase('directory_option_chain', 'git -C sub -C deeper status', (status('deeper'),)),
    ResolutionCase('pushd_and_popd', 'pushd sub && git status && popd && git status',
                   (status('sub'), status('project'))),
    ResolutionCase('command_substitution', 'echo "$(git rev-parse HEAD)"',
                   (('git', 'rev-parse', ('HEAD',), 'project', 'project'),)),
    ResolutionCase('backtick_substitution', 'echo `git log -1`',
                   (('git', 'log', ('-1',), 'project', 'project'),)),
    ResolutionCase('substitution_inside_unquoted_heredoc', 'cat <<EOF\n$(git push -f)\nEOF',
                   (('git', 'push', ('-f',), 'project', 'project'),)),
    ResolutionCase('absolute_program_path', '@git@ status', (status('project'),)),
    ResolutionCase('redirections_are_not_arguments', 'git status > out.txt 2>&1 </dev/null',
                   (status('project'),)),
    ResolutionCase('comment_is_ignored', 'git status # git push -f', (status('project'),)),
    ResolutionCase('line_continuation', 'git \\\n  status', (status('project'),)),
    ResolutionCase('quote_removal', "git log --format='%H %s' \"a b\" c\\ d",
                   (('git', 'log', ('--format=%H %s', 'a b', 'c d'), 'project', 'project'),)),
    ResolutionCase('quoted_git_text_is_not_an_invocation', "echo 'git push -f'", ()),
    ResolutionCase('unregistered_directory_option_is_dropped', 'git -C @outside@ status; git status',
                   (status('project'),)),
    ResolutionCase('registered_directory_option_from_unregistered_cwd', 'git -C @project@ status',
                   (status('project'),), cwd='outside'),
    ResolutionCase('non_work_tree_directory_is_dropped', 'cd @plain@ && git status', ()),
    ResolutionCase('nested_root_resolves_to_inner_repository', 'git status',
                   (status('inner', 'inner'),), cwd='inner', setup='nested'),
    ResolutionCase('gh_invocation', 'gh pr merge 1', (('gh', 'pr', ('merge', '1'), 'project', 'project'),)),
)


def resolution_test(case: ResolutionCase) -> Callable[[RailsFixture], None]:
    def test(self: RailsFixture) -> None:
        self.apply_setup(case.setup)
        resolution = self.resolve(self.render(case.command), self.location(case.cwd))
        self.assertIsNone(resolution.decision, case.command)
        expected = tuple((program, subcommand, argv, self.location(directory),
                          None if repository is None else self.location(repository))
                         for program, subcommand, argv, directory, repository in case.expected)
        self.assertEqual(self.records(resolution), expected, case.command)
    return test


class ResolutionTable(RailsFixture):
    """Table-driven invocation records: program, subcommand, argv, directory, repository."""


for resolution_case in RESOLUTION_CASES:
    setattr(ResolutionTable, 'test_resolves_' + resolution_case.name, resolution_test(resolution_case))


class InvocationDetails(RailsFixture):
    """Record fields that later rules read beyond the table columns."""

    def only(self, command: str, cwd: str | None = None) -> Any:
        resolution = self.resolve(command, cwd or str(self.project))
        self.assertIsNone(resolution.decision, command)
        self.assertEqual(len(resolution.invocations), 1, command)
        return resolution.invocations[0]

    def test_invocation_records_its_registered_project(self) -> None:
        self.setup_nested()
        self.assertEqual(self.only('git status', str(self.inner)).project, str(self.inner))
        self.assertEqual(self.only('git status').project, str(self.project))

    def test_invocation_records_the_common_directory(self) -> None:
        self.assertEqual(self.only('git -C sub status').common_dir, str(self.project / '.git'))

    def test_absolute_program_path_is_recorded_as_git(self) -> None:
        self.assertEqual(self.only(shlex.quote(REAL_GIT) + ' status').program, 'git')

    def test_leading_and_env_assignments_are_recorded_by_name(self) -> None:
        self.assertEqual(tuple(self.only('X=1 env Y=2 git status').assignments), ('X', 'Y'))

    def test_global_options_are_recorded_in_order(self) -> None:
        item = self.only('git --no-pager -C sub --literal-pathspecs status')
        self.assertEqual(tuple(item.global_options), ('--no-pager', '-C', 'sub', '--literal-pathspecs'))
        self.assertEqual(item.directory, str(self.project / 'sub'))

    def test_literal_arguments_are_not_dynamic(self) -> None:
        item = self.only("git log 'a b' c")
        self.assertEqual([word.dynamic for word in item.arguments], [False, False])

    def test_dynamic_argument_of_read_only_git_is_marked(self) -> None:
        item = self.only('git log "$REF" ~/x *.c')
        self.assertEqual([word.dynamic for word in item.arguments], [True, True, True])

    def test_commit_message_heredoc_word_carries_the_message(self) -> None:
        word = self.only(COMMIT_HEREDOC).arguments[1]
        self.assertTrue(word.dynamic)
        self.assertEqual(word.form, 'commit-message')
        self.assertEqual(word.message, 'Subject line\n\nBody text.')

    def test_commit_message_heredoc_with_unquoted_delimiter_and_plain_body(self) -> None:
        word = self.only('git commit -m "$(cat <<EOF\nPlain subject\nEOF\n)"').arguments[1]
        self.assertEqual((word.form, word.message), ('commit-message', 'Plain subject'))

    def test_commit_message_heredoc_with_expansion_has_no_static_message(self) -> None:
        word = self.only('git commit -m "$(cat <<EOF\nSubject $X\nEOF\n)"').arguments[1]
        self.assertEqual((word.form, word.message), ('commit-message', None))

    def test_quoted_heredoc_is_literal_stdin(self) -> None:
        stdin = self.only("git commit -F - <<'EOF'\nfirst line\n$NOT_EXPANDED\nEOF").stdin
        self.assertEqual((stdin.text, stdin.dynamic), ('first line\n$NOT_EXPANDED\n', False))

    def test_unquoted_heredoc_with_expansion_is_dynamic_stdin(self) -> None:
        stdin = self.only('git commit -F - <<EOF\nsubject $X\nEOF').stdin
        self.assertTrue(stdin.dynamic)

    def test_tab_stripping_heredoc_is_literal_stdin(self) -> None:
        stdin = self.only("git commit -F - <<-'EOF'\n\tindented\n\tEOF").stdin
        self.assertEqual((stdin.text, stdin.dynamic), ('indented\n', False))

    def test_here_string_is_literal_stdin(self) -> None:
        stdin = self.only("git commit -F - <<<'subject'").stdin
        self.assertEqual((stdin.text, stdin.dynamic), ('subject\n', False))

    def test_invocation_without_heredoc_has_no_stdin(self) -> None:
        self.assertIsNone(self.only('git commit -F msg.txt').stdin)

    def test_opaque_part_from_unregistered_cwd_does_not_hide_a_registered_invocation(self) -> None:
        command = 'eval x; git -C ' + shlex.quote(str(self.project)) + ' push -f'
        resolution = self.resolve(command, str(self.outside))
        self.assertIsNone(resolution.decision, 'the opaque part outside registered projects is ignored')
        self.assertEqual(self.records(resolution),
                         (('git', 'push', ('-f',), str(self.project), str(self.project)),))
        decision, _, _ = self.decide(self.event(command, str(self.outside)))
        self.assertNotEqual(decision, 'not_applicable', 'the registered invocation is still decided')

    def test_governed_classification_of_git_and_gh(self) -> None:
        self.assertTrue(self.only('git push').governed)
        self.assertFalse(self.only('git status').governed)
        self.assertTrue(self.only('gh pr merge 1').governed)
        self.assertTrue(self.only('gh api repos/o/r').governed)
        self.assertFalse(self.only('gh pr create').governed)


class EventValidation(RailsFixture):
    """Event shape is validated before the registry or the command is read."""

    def valid(self) -> dict[str, object]:
        return self.event('git -c x=y push', str(self.project))

    def changed(self, **fields: object) -> dict[str, object]:
        event = self.valid()
        for key, value in fields.items():
            if value is None:
                event.pop(key, None)
            else:
                event[key] = value
        return event

    def assert_decision(self, event: object, expected: tuple[str, str | None]) -> None:
        decision, reason, _ = self.decide(event)
        self.assertEqual((decision, reason), expected, repr(event)[:200])

    def test_non_object_events_are_malformed(self) -> None:
        for event in ([], 'git push', None, 7):
            with self.subTest(event=event):
                self.assert_decision(event, ('deny', 'malformed-input'))

    def test_event_name_must_be_pre_tool_use(self) -> None:
        for name in (None, 'PostToolUse', 7):
            with self.subTest(name=name):
                event = self.changed(hook_event_name=name)
                self.assert_decision(event, ('deny', 'malformed-input'))

    def test_tool_name_must_be_a_string(self) -> None:
        for name in (None, 7, ['Bash']):
            with self.subTest(name=name):
                self.assert_decision(self.changed(tool_name=name), ('deny', 'malformed-input'))

    def test_non_bash_tool_is_not_applicable(self) -> None:
        event = self.changed(tool_name='Write', tool_input={'file_path': 'a.txt', 'content': 'x'})
        self.assert_decision(event, ('not_applicable', None))

    def test_tool_input_must_be_an_object(self) -> None:
        for tool_input in ('git push', ['git push'], 7):
            with self.subTest(tool_input=tool_input):
                self.assert_decision(self.changed(tool_input=tool_input), ('deny', 'malformed-input'))

    def test_command_must_be_a_string(self) -> None:
        for tool_input in ({}, {'command': ['git', 'push']}, {'command': None}):
            with self.subTest(tool_input=tool_input):
                self.assert_decision(self.changed(tool_input=tool_input), ('deny', 'malformed-input'))

    def test_cwd_must_be_an_absolute_path(self) -> None:
        for cwd in (None, 'project one', '', 7):
            with self.subTest(cwd=cwd):
                event = self.valid()
                if cwd is None:
                    event.pop('cwd')
                else:
                    event['cwd'] = cwd
                self.assert_decision(event, ('deny', 'malformed-input'))

    def test_valid_event_reaches_the_rules(self) -> None:
        self.assert_decision(self.valid(), ('deny', 'unsupported-form'))


class SlowGitRead(RailsFixture):
    """A git read that exceeds its time limit denies instead of hanging."""

    def test_hanging_git_read_is_limit_exceeded(self) -> None:
        fake = self.probe / 'bin/git'
        fake.write_text('#!/bin/bash\n'
                        'case " $* " in *" rev-parse "*) sleep 30 ;; esac\n'
                        f'exec {shlex.quote(REAL_GIT)} "$@"\n')
        fake.chmod(0o755)
        self.environ['PATH'] = f'{self.probe / "bin"}{os.pathsep}{self.environ["PATH"]}'
        started = time.monotonic()
        decision = self.decide(self.event('git add a.txt', str(self.project)))
        elapsed = time.monotonic() - started
        self.assertEqual(decision[:2], ('deny', 'limit-exceeded'))
        self.assertGreaterEqual(elapsed, 1.5, 'the read limit is two seconds')
        self.assertLess(elapsed, 4.5, 'a timed-out read must be stopped, including its children')


class GitReadIsolation(RailsFixture):
    """Git reads are sanitized and never touch the network or gh."""

    def install_recorders(self) -> Path:
        log = self.probe / 'calls.log'
        git = self.probe / 'bin/git'
        git.write_text('#!/bin/bash\n'
                       f'printf "locks=%s prompt=%s dir=%s tree=%s index=%s common=%s args=%s\\n" '
                       '"${GIT_OPTIONAL_LOCKS-unset}" "${GIT_TERMINAL_PROMPT-unset}" "${GIT_DIR-unset}" '
                       '"${GIT_WORK_TREE-unset}" "${GIT_INDEX_FILE-unset}" "${GIT_COMMON_DIR-unset}" '
                       f'"$*" >> {shlex.quote(str(log))}\n'
                       f'exec {shlex.quote(REAL_GIT)} "$@"\n')
        gh = self.probe / 'bin/gh'
        gh.write_text(f'#!/bin/bash\nprintf "gh %s\\n" "$*" >> {shlex.quote(str(log))}\nexit 1\n')
        for tool in (git, gh):
            tool.chmod(0o755)
        self.environ['PATH'] = f'{self.probe / "bin"}{os.pathsep}{self.environ["PATH"]}'
        for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
            self.environ[name] = str(self.outside / '.git')
        return log

    def test_git_reads_are_sanitized(self) -> None:
        log = self.install_recorders()
        resolution = self.resolve('git -C sub status; git p', str(self.project))
        self.assertEqual(tuple(item.repository for item in resolution.invocations),
                         (str(self.project), str(self.project)))
        calls = log.read_text().splitlines()
        self.assertTrue(calls, 'resolution must read the effective repository')
        for call in calls:
            self.assertTrue(call.startswith('locks=0 prompt=0 dir=unset tree=unset index=unset common=unset '), call)
            self.assertIn('-c core.fsmonitor=false', call)

    def test_effective_repository_uses_absolute_path_format(self) -> None:
        log = self.install_recorders()
        self.resolve('git status', str(self.project))
        calls = log.read_text()
        self.assertIn('rev-parse --path-format=absolute --show-toplevel --git-common-dir', calls)

    def test_alias_lookup_reads_only_the_alias_key(self) -> None:
        log = self.install_recorders()
        self.resolve('git p', str(self.project))
        self.assertIn('config --get alias.p', log.read_text())

    def test_no_gh_or_network_command_is_run(self) -> None:
        log = self.install_recorders()
        self.decide(self.event('gh pr merge 1; gh api repos/o/r/pulls/1/merge; git push origin main; '
                               'git pull; git fetch', str(self.project)), self.environ)
        calls = log.read_text().splitlines() if log.exists() else []
        self.assertFalse([call for call in calls if call.startswith('gh ')], 'the core never runs gh')
        for call in calls:
            arguments = call.split('args=', 1)[1].split()
            for network in ('fetch', 'ls-remote', 'push', 'pull', 'clone', 'remote'):
                self.assertNotIn(network, arguments, call)


class OptionParsing(RailsFixture):
    """The git parse-options helper that rule evaluation builds on."""

    def specs(self) -> list[Any]:
        spec = self.api('OptionSpec')
        return [spec(long='all', short='A', negatable=False), spec(long='verbose', short='v'),
                spec(long='message', short='m', takes='required', repeatable=True),
                spec(long='cleanup', takes='required'), spec(long='force', short='f'),
                spec(long='force-with-lease', takes='optional'), spec(long='force-if-includes'),
                spec(long='verify'), spec(long=None, short='a')]

    def parse(self, *words: str) -> Any:
        return self.api('parse_options')(list(words), self.specs())

    def test_bundled_short_flags(self) -> None:
        parsed = self.parse('-Av')
        self.assertEqual((parsed.last('all'), parsed.last('verbose'), parsed.error), (True, True, None))

    def test_bundled_short_flag_with_attached_value(self) -> None:
        parsed = self.parse('-amfix')
        self.assertEqual((parsed.last('a'), parsed.every('message')), (True, ('fix',)))

    def test_bundled_short_flag_with_separate_value(self) -> None:
        parsed = self.parse('-am', 'fix', 'file')
        self.assertEqual((parsed.every('message'), parsed.operands), (('fix',), ('file',)))

    def test_long_value_spellings_accumulate_when_repeatable(self) -> None:
        self.assertEqual(self.parse('--message=one', '--message', 'two', '-m', 'three').every('message'),
                         ('one', 'two', 'three'))

    def test_last_occurrence_wins_for_single_valued_options(self) -> None:
        self.assertEqual(self.parse('--cleanup=strip', '--cleanup', 'verbatim').last('cleanup'), 'verbatim')

    def test_unique_long_prefix_is_accepted(self) -> None:
        parsed = self.parse('--verb', '--clean=strip')
        self.assertEqual((parsed.last('verbose'), parsed.last('cleanup')), (True, 'strip'))

    def test_exact_long_name_wins_over_longer_names(self) -> None:
        parsed = self.parse('--force')
        self.assertEqual((parsed.last('force'), parsed.last('force-with-lease')), (True, None))

    def test_ambiguous_long_prefix_is_an_error(self) -> None:
        self.assertEqual(self.parse('--for').error, 'ambiguous-option')
        self.assertEqual(self.parse('--forc').error, 'ambiguous-option')

    def test_ambiguous_long_prefix_lists_every_candidate_in_declaration_order(self) -> None:
        self.assertEqual(self.parse('--forc').candidates, ('force', 'force-with-lease', 'force-if-includes'))
        self.assertEqual(self.parse('--force-').candidates, ('force-with-lease', 'force-if-includes'))

    def test_unambiguous_parse_has_no_candidates(self) -> None:
        self.assertEqual(self.parse('--force', '--verb').candidates, ())

    def test_negation_and_last_wins(self) -> None:
        self.assertIs(self.parse('--verify', '--no-verify').last('verify'), False)
        self.assertIs(self.parse('--no-verify', '--verify').last('verify'), True)
        self.assertIs(self.parse('--no-verb').last('verbose'), False)

    def test_non_negatable_option_rejects_negation(self) -> None:
        self.assertEqual(self.parse('--no-all').error, 'unknown-option')

    def test_double_dash_ends_options(self) -> None:
        parsed = self.parse('--', '-v', 'file')
        self.assertEqual((parsed.last('verbose'), parsed.operands), (None, ('-v', 'file')))

    def test_options_may_follow_operands(self) -> None:
        parsed = self.parse('file', '-v', '-')
        self.assertEqual((parsed.last('verbose'), parsed.operands), (True, ('file', '-')))

    def test_unknown_options_are_errors(self) -> None:
        self.assertEqual(self.parse('--bogus').error, 'unknown-option')
        self.assertEqual(self.parse('-Z').error, 'unknown-option')

    def test_missing_values_are_errors(self) -> None:
        self.assertEqual(self.parse('-m').error, 'missing-value')
        self.assertEqual(self.parse('--message').error, 'missing-value')

    def test_value_on_flag_is_an_error(self) -> None:
        self.assertEqual(self.parse('--verbose=yes').error, 'unexpected-value')

    def test_optional_value_is_taken_only_when_attached(self) -> None:
        self.assertIs(self.parse('--force-with-lease').last('force-with-lease'), True)
        self.assertEqual(self.parse('--force-with-lease=main:abc').last('force-with-lease'), 'main:abc')
        parsed = self.parse('--force-with-lease', 'main')
        self.assertEqual((parsed.last('force-with-lease'), parsed.operands), (True, ('main',)))

    def test_no_words_parse_to_nothing(self) -> None:
        parsed = self.parse()
        self.assertEqual((parsed.operands, parsed.error, parsed.last('verbose'), parsed.every('message')),
                         ((), None, None, ()))


class DecisionCombination(RailsFixture):
    """The whole command takes the most severe result; ties keep command order."""

    def made(self, decision: str, reason: str | None = None) -> Any:
        return self.api('Decision')(decision=decision, reason_code=reason, rule_id=None)

    def outcome(self, *decisions: Any) -> tuple[str, str | None]:
        result = self.api('combine')(list(decisions))
        return result.decision, result.reason_code

    def test_severity_order(self) -> None:
        self.assertEqual(self.outcome(self.made('not_applicable'), self.made('allow'),
                                      self.made('ask', 'first-ask'), self.made('deny', 'only-deny')),
                         ('deny', 'only-deny'))
        self.assertEqual(self.outcome(self.made('allow'), self.made('ask', 'first-ask'),
                                      self.made('not_applicable')), ('ask', 'first-ask'))
        self.assertEqual(self.outcome(self.made('not_applicable'), self.made('allow')), ('allow', None))

    def test_ties_keep_the_first_result(self) -> None:
        self.assertEqual(self.outcome(self.made('deny', 'first'), self.made('deny', 'second')),
                         ('deny', 'first'))

    def test_no_results_are_not_applicable(self) -> None:
        self.assertEqual(self.outcome(), ('not_applicable', None))


class CoreSurface(RailsFixture):
    """Constants and module properties that other components rely on."""

    def test_rule_path_is_one_module_constant(self) -> None:
        self.assertEqual(self.api('RULE_PATH'), RULE_PATH_TEXT)
        self.assertEqual(CORE_PATH.read_text(encoding='utf-8').count(RULE_PATH_TEXT), 1)

    def test_governed_subcommands_are_a_closed_list(self) -> None:
        self.assertEqual(self.api('GOVERNED_GIT_SUBCOMMANDS'),
                         frozenset({'add', 'stage', 'commit', 'push', 'reset', 'clean', 'branch',
                                    'update-ref', 'checkout', 'switch', 'rebase', 'merge', 'pull'}))
        self.assertEqual(self.api('GOVERNED_GH_COMMANDS'), frozenset({('pr', 'merge'), ('api',)}))

    def test_core_loads_in_isolated_mode_without_site_packages(self) -> None:
        self.api('decide')
        probe = ('import importlib.util, sys\n'
                 'spec = importlib.util.spec_from_file_location("git_rails", sys.argv[1])\n'
                 'module = importlib.util.module_from_spec(spec)\n'
                 'sys.modules["git_rails"] = module\n'
                 'spec.loader.exec_module(module)\n'
                 'print(callable(module.decide))\n')
        result = subprocess.run([sys.executable, '-I', '-S', '-c', probe, str(CORE_PATH)],
                                capture_output=True, text=True, cwd=self.world, env=self.environ)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, 'True'), result.stderr)

    def test_core_functions_have_complete_annotations(self) -> None:
        self.api('decide')
        tree = ast.parse(CORE_PATH.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.assertIsNotNone(node.returns, node.name + ' requires a return annotation')
                arguments = (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
                             node.args.vararg, node.args.kwarg)
                for argument in arguments:
                    if argument is not None and argument.arg not in ('self', 'cls'):
                        self.assertIsNotNone(argument.annotation, node.name + '.' + argument.arg)

    def test_core_has_no_pipeline_identifiers(self) -> None:
        self.api('decide')
        text = CORE_PATH.read_text(encoding='utf-8')
        self.assertNotIn('.ai/', text)
        self.assertNotRegex(text, r'\bT-\d{2}[a-z]?\b')
        self.assertNotRegex(text, r'\bADR-\d{4}\b')


# Commands that run git in a registered project in ways the first grammar missed. Each
# is denied, or its invocation is decided instead of being dropped as not applicable.
FAIL_CLOSED_CASES: tuple[DecisionCase, ...] = (
    # A cd target that is not an accessible directory leaves the shell where it was.
    DecisionCase('failed_cd_to_missing_directory_makes_governed_git_unsupported',
                 'cd /nonexistent-rails-dir; git push -f', 'deny', 'unsupported-form'),
    DecisionCase('failed_cd_alternative_makes_governed_git_unsupported',
                 'cd /nonexistent-rails-dir || git push -f', 'deny', 'unsupported-form'),
    DecisionCase('cd_to_regular_file_makes_governed_git_unsupported',
                 'cd @outside@/a.txt; git push -f', 'deny', 'unsupported-form'),
    DecisionCase('read_only_git_after_failed_cd_stays_not_applicable',
                 'cd /nonexistent-rails-dir; git status', 'not_applicable'),
    # Programs that run their arguments are opaque when a git or gh word is passed.
    DecisionCase('ssh_agent_running_git_is_unsupported', 'ssh-agent git push -f', 'deny', 'unsupported-form'),
    DecisionCase('direnv_exec_running_git_is_unsupported', 'direnv exec . git push -f',
                 'deny', 'unsupported-form'),
    DecisionCase('systemd_run_running_git_is_unsupported', 'systemd-run --user git push -f',
                 'deny', 'unsupported-form'),
    DecisionCase('setpriv_running_git_is_unsupported', 'setpriv git push -f', 'deny', 'unsupported-form'),
    DecisionCase('fakeroot_running_git_is_unsupported', 'fakeroot git push -f', 'deny', 'unsupported-form'),
    DecisionCase('unlisted_program_running_gh_is_unsupported', 'ssh-agent gh pr merge 1',
                 'deny', 'unsupported-form'),
    DecisionCase('echo_of_git_word_stays_not_applicable', 'echo git', 'not_applicable'),
    DecisionCase('absolute_echo_of_git_word_stays_not_applicable', '/bin/echo git', 'not_applicable'),
    DecisionCase('grep_for_git_word_stays_not_applicable', 'grep git a.txt', 'not_applicable'),
    DecisionCase('manual_for_git_stays_not_applicable', 'man git', 'not_applicable'),
    DecisionCase('which_git_stays_not_applicable', 'which git', 'not_applicable'),
    DecisionCase('git_path_component_is_not_a_git_word', 'cat .git/config', 'not_applicable'),
    DecisionCase('git_prefixed_file_name_is_not_a_git_word', 'ls git-rails.sh', 'not_applicable'),
    # Shells that read the command from stdin.
    DecisionCase('command_piped_into_bash_is_unsupported', "echo 'git push -f' | bash",
                 'deny', 'unsupported-form'),
    DecisionCase('here_string_into_bash_is_unsupported', 'bash <<< "git push -f"', 'deny', 'unsupported-form'),
    DecisionCase('here_string_into_bash_stdin_mode_is_unsupported', 'bash -s <<< "git push -f"',
                 'deny', 'unsupported-form'),
    DecisionCase('command_piped_into_sh_is_unsupported', 'echo git push -f | sh', 'deny', 'unsupported-form'),
    # Environment prefixes reach a shell string's commands.
    DecisionCase('git_assignment_on_shell_string_is_opaque_environment', 'GIT_DIR=/x bash -c "git push -f"',
                 'deny', 'opaque-environment', 'R31'),
    DecisionCase('work_tree_assignment_on_sh_string_is_opaque_environment',
                 'GIT_WORK_TREE=/x sh -c "git add -A"', 'deny', 'opaque-environment', 'R31'),
    # Repository-redirecting options and variables pointing back into a registered project.
    DecisionCase('git_dir_and_work_tree_into_project_from_outside_directory_are_unsupported',
                 'git -C /tmp --git-dir=@project@/.git --work-tree=@project@ add -A',
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('git_dir_into_project_from_unregistered_repository_is_unsupported',
                 'git -C @outside@ --git-dir=@project@/.git push -f', 'deny', 'unsupported-form', 'R31'),
    DecisionCase('git_dir_assignment_into_project_from_unregistered_repository_is_opaque_environment',
                 'GIT_DIR=@project@/.git git -C @outside@ push -f', 'deny', 'opaque-environment', 'R31'),
    DecisionCase('git_dir_assignment_from_registered_non_work_tree_is_opaque_environment',
                 'cd @plain@ && GIT_DIR=@project@/.git git push -f', 'deny', 'opaque-environment', 'R31'),
    # Variables that decide which git runs and which configuration it reads.
    DecisionCase('home_assignment_on_possible_alias_is_opaque_environment', 'HOME=/tmp/elsewhere git p',
                 'deny', 'opaque-environment', 'R31'),
    DecisionCase('config_home_assignment_on_governed_git_is_opaque_environment',
                 'XDG_CONFIG_HOME=/tmp/elsewhere git push', 'deny', 'opaque-environment', 'R31'),
    DecisionCase('path_assignment_on_governed_git_is_opaque_environment', 'PATH=/tmp git push',
                 'deny', 'opaque-environment', 'R31'),
    DecisionCase('home_assignment_on_read_only_git_stays_not_applicable', 'HOME=/tmp/elsewhere git status',
                 'not_applicable'),
    # Bash directory features that move the shell where the walk cannot follow.
    DecisionCase('cdpath_makes_later_governed_git_unsupported', 'CDPATH=@project@; cd sub && git push -f',
                 'deny', 'unsupported-form', cwd='outside'),
    DecisionCase('directory_stack_rotation_makes_later_governed_git_unsupported',
                 'pushd @project@; pushd @outside@; pushd +1; git push -f', 'deny', 'unsupported-form',
                 cwd='outside'),
    DecisionCase('cdable_variables_make_later_governed_git_unsupported',
                 'shopt -s cdable_vars; RR=@project@; cd RR && git push -f', 'deny', 'unsupported-form',
                 cwd='outside'),
    DecisionCase('last_pipe_makes_later_governed_git_unsupported',
                 'shopt -s lastpipe; echo | cd @project@; git push -f', 'deny', 'unsupported-form',
                 cwd='outside'),
)


class FailClosedTable(RailsFixture):
    """Table-driven decisions for forms that must not be dropped as not applicable."""


for fail_closed_case in FAIL_CLOSED_CASES:
    setattr(FailClosedTable, 'test_' + fail_closed_case.name, decision_test(fail_closed_case))

# HOME, XDG_CONFIG_HOME and PATH are always exported, so a bare assignment or an export
# earlier in the same shell changes which git runs and which configuration it reads.
ENVIRONMENT_STATEMENT_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('bare_path_assignment_before_governed_git_is_opaque_environment',
                 'PATH=/tmp; git push', 'deny', 'opaque-environment', 'R31'),
    DecisionCase('exported_path_before_governed_git_is_opaque_environment',
                 'export PATH=/tmp; git push', 'deny', 'opaque-environment', 'R31'),
    DecisionCase('exported_home_before_governed_git_is_opaque_environment',
                 'export HOME=/x; git push -f', 'deny', 'opaque-environment', 'R31'),
    DecisionCase('bare_config_home_assignment_before_governed_git_is_opaque_environment',
                 'XDG_CONFIG_HOME=/x; git add a.txt', 'deny', 'opaque-environment', 'R31'),
    DecisionCase('path_export_inside_subshell_does_not_reach_later_commands',
                 '(export PATH=/tmp); git add a.txt', 'allow'),
    DecisionCase('path_export_before_read_only_git_stays_not_applicable',
                 'export PATH=/tmp; git status', 'not_applicable'),
)

for environment_case in ENVIRONMENT_STATEMENT_CASES:
    setattr(FailClosedTable, 'test_' + environment_case.name, decision_test(environment_case))


@dataclass(frozen=True)
class DecidedCase:
    """A command whose invocation must be decided, like its reference command when given."""
    name: str
    command: str
    reference: str | None
    setup: str = 'standard'


DECIDED_CASES: tuple[DecidedCase, ...] = (
    DecidedCase('logical_parent_of_symlink_stays_in_project', 'cd lnk/.. && git push -f', 'git push -f',
                setup='symlinks'),
    DecidedCase('logical_cd_back_from_symlink_returns_to_project', 'cd lnk2 && cd .. && git push -f',
                'git push -f', setup='symlinks'),
    DecidedCase('absolute_env_wrapper', '/usr/bin/env git push -f', 'git push -f'),
    DecidedCase('absolute_timeout_wrapper', '/usr/bin/timeout 5 git push -f', 'git push -f'),
    DecidedCase('absolute_nohup_wrapper', '/usr/bin/nohup git push -f', 'git push -f'),
    DecidedCase('absolute_time_wrapper', '/usr/bin/time git push -f', 'git push -f'),
    DecidedCase('absolute_env_wrapper_around_shell_string', '/usr/bin/env bash -c "git push -f"',
                'git push -f'),
    DecidedCase('quoted_brace_inside_parameter_expansion', "echo ${x:-'}'} ; git push -f ; echo \\'", None),
    DecidedCase('gh_short_repository_flag_before_command', 'gh -R o/r pr merge 5', 'gh pr merge 5'),
    DecidedCase('gh_long_repository_flag_before_command', 'gh --repo o/r pr merge 5', 'gh pr merge 5'),
    DecidedCase('gh_attached_repository_flag_before_command', 'gh --repo=o/r pr merge 5', 'gh pr merge 5'),
    DecidedCase('gh_repository_flag_inside_command', 'gh pr --repo o/r merge 5', 'gh pr merge 5'),
)


def decided_test(case: DecidedCase) -> Callable[[RailsFixture], None]:
    def test(self: RailsFixture) -> None:
        self.apply_setup(case.setup)
        decision = self.decide(self.event(self.render(case.command), self.location('project')))
        self.assertNotEqual(decision[0], 'not_applicable', case.command)
        if case.reference is not None:
            reference = self.decide(self.event(case.reference, self.location('project')))
            self.assertEqual(decision, reference, case.command)
    return test


class DecidedTable(RailsFixture):
    """Invocations that must reach rule evaluation exactly like their plain spelling."""


for decided_case in DECIDED_CASES:
    setattr(DecidedTable, 'test_decides_' + decided_case.name, decided_test(decided_case))


class RuleFixture(RailsFixture):
    """Repository states read by the staging and commit rules: ignore rules, deleted and
    linked paths, message files, trailer-bearing and published commits."""

    def setup_ignored_state(self) -> None:
        exclude = self.project / '.git/info/exclude'
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text('/.ai/state.md\n')
        self.git(self.project, 'rm', '--cached', '-q', '.ai/state.md')
        (self.project / '.ai/adr').mkdir()
        (self.project / '.ai/adr/x.md').write_text('decision\n')

    def setup_ignored_knowledge(self) -> None:
        exclude = self.project / '.git/info/exclude'
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text('/.ai/\n')
        self.git(self.project, 'rm', '--cached', '-r', '-q', '.ai')
        (self.project / '.ai/adr').mkdir()
        (self.project / '.ai/adr/x.md').write_text('decision\n')

    def setup_deleted(self) -> None:
        (self.project / 'b.txt').unlink()

    def setup_file_links(self) -> None:
        (self.project / 'link.txt').symlink_to('a.txt')
        (self.project / 'dangling.txt').symlink_to('nowhere.txt')

    def setup_source_tree(self) -> None:
        (self.project / 'src').mkdir()
        (self.project / 'src/main.py').write_text('main\n')
        (self.project / 'src/util.py').write_text('util\n')
        (self.project / 'list.txt').write_text('a.txt\n')

    def setup_message_files(self) -> None:
        trailer = f'Add parser\n\n{TRAILER}\n'
        (self.project / 'msg.txt').write_text('Add parser\n')
        (self.project / 'sub/msg.txt').write_text(trailer)
        (self.project / 'trailer.txt').write_text(trailer)
        (self.project / 'crlf.txt').write_bytes(trailer.replace('\n', '\r\n').encode())
        (self.project / 'tpl.txt').write_text('Template subject\n')
        head = b'Add parser\n'
        limit = 1024 * 1024
        (self.project / 'limit.txt').write_bytes(head + b'x' * (limit - len(head) - 1) + b'\n')
        (self.project / 'large.txt').write_bytes(head + b'x' * (limit - len(head)) + b'\n')

    def setup_unreadable_message(self) -> None:
        if os.geteuid() == 0:
            self.skipTest('file permissions do not restrict the superuser')
        locked = self.project / 'locked.txt'
        locked.write_text('Add parser\n')
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o600)

    def setup_trailer_head(self) -> None:
        self.git(self.project, 'commit', '-q', '--allow-empty', '-m', 'Add parser', '-m', TRAILER)

    def setup_published(self) -> None:
        self.git(self.project, 'update-ref', 'refs/remotes/origin/main', 'HEAD')

    def setup_published_ancestor(self) -> None:
        self.setup_published()
        self.git(self.project, 'commit', '-q', '--allow-empty', '-m', 'Local work')

    def setup_published_elsewhere(self) -> None:
        self.git(self.project, 'update-ref', 'refs/remotes/upstream/feature', 'HEAD')

    def setup_trailer_alias(self) -> None:
        self.git(self.project, 'config', 'trailer.cab.key', 'Co-authored-by')


TRAILER = 'Co-authored-by: Someone <someone@example.invalid>'
STAGE = 'staging-not-file'
BLANKET = 'blanket-staging'
UNVERIFIABLE = 'commit-message-unverifiable'
FORBIDDEN = 'commit-message-forbidden'

# git add and git stage: blanket flags, non-file operands, interactive forms, forced
# ignored paths, and the operand kinds that are allowed.
STAGING_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('all_short_flag_is_blanket_staging', 'git add -A', 'deny', BLANKET, 'R01'),
    DecisionCase('all_flag_in_a_bundle_is_blanket_staging', 'git add -Av', 'deny', BLANKET, 'R01'),
    DecisionCase('all_long_flag_is_blanket_staging', 'git add --all', 'deny', BLANKET, 'R01'),
    DecisionCase('unique_prefix_of_all_is_blanket_staging', 'git add --al', 'deny', BLANKET, 'R01'),
    DecisionCase('update_short_flag_is_blanket_staging', 'git add -u', 'deny', BLANKET, 'R01'),
    DecisionCase('update_long_flag_with_file_is_blanket_staging', 'git add --update a.txt',
                 'deny', BLANKET, 'R01'),
    DecisionCase('no_ignore_removal_is_blanket_staging', 'git add --no-ignore-removal', 'deny', BLANKET, 'R01'),
    DecisionCase('renormalize_implies_update_and_is_blanket_staging', 'git add --renormalize',
                 'deny', BLANKET, 'R01'),
    DecisionCase('current_directory_operand_is_blanket_staging', 'git add .', 'deny', BLANKET, 'R01'),
    DecisionCase('current_directory_after_separator_is_blanket_staging', 'git add -- .',
                 'deny', BLANKET, 'R01'),
    DecisionCase('stage_spelling_of_all_is_blanket_staging', 'git stage -A', 'deny', BLANKET, 'R01'),
    DecisionCase('blanket_staging_after_cd_is_denied', 'cd sub && git add -A', 'deny', BLANKET, 'R01'),
    DecisionCase('blanket_staging_in_literal_shell_string_is_denied', "bash -c 'git add .'",
                 'deny', BLANKET, 'R01'),
    DecisionCase('blanket_staging_behind_command_wrapper_is_denied', 'command git add --all',
                 'deny', BLANKET, 'R01'),
    DecisionCase('blanket_staging_in_directory_option_target_is_denied', 'git -C sub add .',
                 'deny', BLANKET, 'R01'),
    DecisionCase('first_matching_row_names_the_reason', 'git add -A sub', 'deny', BLANKET, 'R01'),
    DecisionCase('negated_all_after_all_stages_only_the_file', 'git add -A --no-all a.txt', 'allow'),
    DecisionCase('existing_file_is_allowed', 'git add a.txt', 'allow'),
    DecisionCase('several_existing_files_are_allowed', 'git add a.txt b.txt sub/a.txt', 'allow'),
    DecisionCase('existing_file_after_separator_is_allowed', 'git add -- a.txt', 'allow'),
    DecisionCase('existing_file_with_verbose_flag_is_allowed', 'git add -v a.txt', 'allow'),
    DecisionCase('stage_spelling_of_existing_file_is_allowed', 'git stage a.txt', 'allow'),
    DecisionCase('dot_relative_existing_file_is_allowed', 'git add ./a.txt', 'allow'),
    DecisionCase('absolute_path_with_spaces_is_allowed', 'git add @project@/a.txt', 'allow'),
    DecisionCase('existing_file_in_directory_option_target_is_allowed', 'git -C sub add a.txt', 'allow'),
    DecisionCase('directory_operand_is_not_a_file', 'git add sub', 'deny', STAGE, 'R02'),
    DecisionCase('directory_operand_with_trailing_slash_is_not_a_file', 'git add src/',
                 'deny', STAGE, 'R02', setup='source-tree'),
    DecisionCase('normalized_directory_operand_is_not_a_file', 'git add sub/..', 'deny', STAGE, 'R02'),
    DecisionCase('glob_operand_is_not_a_file', "git add '*.py'", 'deny', STAGE, 'R02', setup='source-tree'),
    DecisionCase('question_mark_glob_is_not_a_file', "git add 'a?txt'", 'deny', STAGE, 'R02'),
    DecisionCase('bracket_glob_is_not_a_file', "git add '[ab].txt'", 'deny', STAGE, 'R02'),
    DecisionCase('top_level_pathspec_magic_is_not_a_file', 'git add :/', 'deny', STAGE, 'R02'),
    DecisionCase('long_pathspec_magic_is_not_a_file', "git add ':(literal)a.txt'", 'deny', STAGE, 'R02'),
    DecisionCase('exclude_pathspec_magic_is_not_a_file', "git add ':!a.txt'", 'deny', STAGE, 'R02'),
    DecisionCase('missing_untracked_operand_is_not_a_file', 'git add missing.txt', 'deny', STAGE, 'R02'),
    DecisionCase('one_bad_operand_denies_the_invocation', 'git add a.txt sub', 'deny', STAGE, 'R02'),
    DecisionCase('pathspec_from_file_is_not_a_file', 'git add --pathspec-from-file=list.txt',
                 'deny', STAGE, 'R02', setup='source-tree'),
    DecisionCase('separate_pathspec_from_file_value_is_not_a_file', 'git add --pathspec-from-file list.txt',
                 'deny', STAGE, 'R02', setup='source-tree'),
    DecisionCase('stage_spelling_of_directory_is_not_a_file', 'git stage sub', 'deny', STAGE, 'R02'),
    DecisionCase('directory_relative_to_directory_option_is_not_a_file', 'git -C sub add deeper',
                 'deny', STAGE, 'R02'),
    DecisionCase('file_relative_to_directory_option_must_exist_there', 'git -C sub add b.txt',
                 'deny', STAGE, 'R02'),
    DecisionCase('source_file_is_allowed', 'git add src/main.py', 'allow', setup='source-tree'),
    DecisionCase('patch_short_flag_is_unsupported', 'git add -p', 'deny', 'unsupported-form', 'R03'),
    DecisionCase('patch_long_flag_is_unsupported', 'git add --patch a.txt', 'deny', 'unsupported-form', 'R03'),
    DecisionCase('unique_prefix_of_patch_is_unsupported', 'git add --patc a.txt',
                 'deny', 'unsupported-form', 'R03'),
    DecisionCase('patch_flag_in_a_bundle_is_unsupported', 'git add -vp a.txt', 'deny', 'unsupported-form', 'R03'),
    DecisionCase('interactive_short_flag_is_unsupported', 'git add -i', 'deny', 'unsupported-form', 'R03'),
    DecisionCase('interactive_long_flag_is_unsupported', 'git add --interactive',
                 'deny', 'unsupported-form', 'R03'),
    DecisionCase('edit_short_flag_is_unsupported', 'git add -e a.txt', 'deny', 'unsupported-form', 'R03'),
    DecisionCase('edit_long_flag_is_unsupported', 'git add --edit a.txt', 'deny', 'unsupported-form', 'R03'),
    DecisionCase('ambiguous_prefix_takes_its_most_severe_candidate', 'git add --i a.txt',
                 'deny', 'unsupported-form', 'R03'),
    DecisionCase('negated_patch_is_allowed', 'git add --no-patch a.txt', 'allow'),
    DecisionCase('unknown_staging_option_is_unsupported', 'git add --bogus a.txt', 'deny', 'unsupported-form'),
    DecisionCase('forced_ignored_knowledge_file_needs_owner_approval', 'git add -f .ai/state.md',
                 'ask', 'staging-ignored-path', 'R04', setup='ignored-state'),
    DecisionCase('long_force_on_ignored_file_needs_owner_approval', 'git add --force .ai/state.md',
                 'ask', 'staging-ignored-path', 'R04', setup='ignored-state'),
    DecisionCase('force_in_a_bundle_on_ignored_file_needs_owner_approval', 'git add -vf .ai/state.md',
                 'ask', 'staging-ignored-path', 'R04', setup='ignored-state'),
    DecisionCase('one_forced_ignored_operand_needs_owner_approval', 'git add -f a.txt .ai/state.md',
                 'ask', 'staging-ignored-path', 'R04', setup='ignored-state'),
    DecisionCase('forced_ignored_file_relative_to_directory_option_needs_owner_approval',
                 'git -C .ai add -f state.md', 'ask', 'staging-ignored-path', 'R04', setup='ignored-state'),
    DecisionCase('forced_file_in_ignored_knowledge_directory_needs_owner_approval', 'git add -f .ai/adr/x.md',
                 'ask', 'staging-ignored-path', 'R04', setup='ignored-knowledge'),
    DecisionCase('unforced_ignored_file_is_left_to_git', 'git add .ai/state.md', 'allow', setup='ignored-state'),
    DecisionCase('unignored_new_knowledge_file_is_allowed', 'git add .ai/adr/x.md', 'allow',
                 setup='ignored-state'),
    DecisionCase('forced_unignored_new_file_is_allowed', 'git add -f .ai/adr/x.md', 'allow',
                 setup='ignored-state'),
    DecisionCase('forced_tracked_file_is_allowed', 'git add -f a.txt', 'allow', setup='ignored-state'),
    DecisionCase('tracked_knowledge_file_is_allowed', 'git add .ai/state.md', 'allow'),
    DecisionCase('blanket_staging_beside_forced_ignored_file_is_denied', 'git add -f .ai/state.md; git add -A',
                 'deny', BLANKET, 'R01', setup='ignored-state'),
    DecisionCase('symlink_to_directory_is_allowed', 'git add lnk', 'allow', setup='symlinks'),
    DecisionCase('symlink_to_file_is_allowed', 'git add link.txt', 'allow', setup='file-links'),
    DecisionCase('dangling_symlink_is_allowed', 'git add dangling.txt', 'allow', setup='file-links'),
    DecisionCase('symlinked_directory_with_trailing_slash_is_not_a_file', 'git add lnk/',
                 'deny', STAGE, 'R02', setup='symlinks'),
    DecisionCase('deleted_tracked_file_is_allowed', 'git add b.txt', 'allow', setup='deleted'),
    DecisionCase('stage_spelling_of_deleted_tracked_file_is_allowed', 'git stage -- b.txt', 'allow',
                 setup='deleted'),
    DecisionCase('deleted_tracked_file_beside_missing_file_is_not_a_file', 'git add b.txt missing.txt',
                 'deny', STAGE, 'R02', setup='deleted'),
)

# git commit: every-change flags, path operands, message sources, forbidden patterns and
# amending a commit that a remote-tracking ref already contains.
COMMIT_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('all_short_flag_commits_everything', 'git commit -a -m ok', 'deny', 'commit-all', 'R06'),
    DecisionCase('all_flag_bundled_with_message_commits_everything', 'git commit -am ok',
                 'deny', 'commit-all', 'R06'),
    DecisionCase('all_long_flag_commits_everything', 'git commit --all -m ok', 'deny', 'commit-all', 'R06'),
    DecisionCase('all_flag_in_a_longer_bundle_commits_everything', 'git commit -qam ok',
                 'deny', 'commit-all', 'R06'),
    DecisionCase('ambiguous_prefix_including_all_commits_everything', 'git commit --a -m ok',
                 'deny', 'commit-all', 'R06'),
    DecisionCase('all_flag_through_env_wrapper_commits_everything', 'env X=1 git commit -am x',
                 'deny', 'commit-all', 'R06'),
    DecisionCase('negated_all_after_all_is_allowed', 'git commit -a --no-all -m ok', 'allow'),
    DecisionCase('message_value_that_reads_like_a_flag_is_allowed', 'git commit -ma', 'allow'),
    DecisionCase('plain_message_commit_is_allowed', 'git commit -m ok', 'allow'),
    DecisionCase('current_directory_commit_operand_is_blanket_staging', 'git commit -m ok .',
                 'deny', BLANKET, 'R07'),
    DecisionCase('only_flag_with_current_directory_is_blanket_staging', 'git commit -o -m ok -- .',
                 'deny', BLANKET, 'R07'),
    DecisionCase('directory_commit_operand_is_not_a_file', 'git commit -m ok sub', 'deny', STAGE, 'R07'),
    DecisionCase('include_flag_with_directory_is_not_a_file', 'git commit -i -m ok sub', 'deny', STAGE, 'R07'),
    DecisionCase('glob_commit_operand_is_not_a_file', "git commit -m ok '*.txt'", 'deny', STAGE, 'R07'),
    DecisionCase('pathspec_magic_commit_operand_is_not_a_file', 'git commit -m ok :/', 'deny', STAGE, 'R07'),
    DecisionCase('missing_commit_operand_is_not_a_file', 'git commit -m ok missing.txt', 'deny', STAGE, 'R07'),
    DecisionCase('commit_pathspec_from_file_is_not_a_file', 'git commit -m ok --pathspec-from-file=list.txt',
                 'deny', STAGE, 'R07', setup='source-tree'),
    DecisionCase('existing_file_commit_operand_is_allowed', 'git commit -m ok a.txt', 'allow'),
    DecisionCase('only_flag_with_existing_file_is_allowed', 'git commit -o -m ok a.txt', 'allow'),
    DecisionCase('include_flag_with_existing_file_is_allowed', 'git commit -i -m ok -- a.txt', 'allow'),
    DecisionCase('deleted_tracked_commit_operand_is_allowed', 'git commit -m ok b.txt', 'allow',
                 setup='deleted'),
    DecisionCase('editor_commit_is_unverifiable', 'git commit', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('reedit_message_is_unverifiable', 'git commit -c HEAD', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('reuse_message_is_unverifiable', 'git commit -C HEAD', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('long_reuse_message_is_unverifiable', 'git commit --reuse-message=HEAD',
                 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('long_reedit_message_is_unverifiable', 'git commit --reedit-message HEAD',
                 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('fixup_is_unverifiable', 'git commit --fixup HEAD', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('fixup_amend_form_is_unverifiable', 'git commit --fixup=amend:HEAD',
                 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('squash_is_unverifiable', 'git commit --squash HEAD', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('template_is_unverifiable', 'git commit -t tpl.txt', 'deny', UNVERIFIABLE, 'R08',
                 setup='message-files'),
    DecisionCase('long_template_beside_message_is_unverifiable', 'git commit --template=tpl.txt -m ok',
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('edit_flag_with_message_is_unverifiable', 'git commit -m ok -e', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('long_edit_flag_with_message_is_unverifiable', 'git commit --edit -m ok',
                 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('amend_without_message_opens_the_editor', 'git commit --amend', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('no_edit_without_amend_or_message_is_unverifiable', 'git commit --no-edit',
                 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('standard_input_without_literal_text_is_unverifiable', 'git commit -F -',
                 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('piped_standard_input_is_unverifiable', 'echo ok | git commit -F -',
                 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('redirected_standard_input_file_is_unverifiable', 'git commit -F - < msg.txt',
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('heredoc_to_another_descriptor_is_unverifiable', "echo ok | git commit -F - 3<<'EOF'\nok\nEOF",
                 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('file_redirection_after_heredoc_is_unverifiable',
                 "git commit -F - <<'EOF' < msg.txt\nok\nEOF", 'deny', UNVERIFIABLE, 'R08',
                 setup='message-files'),
    DecisionCase('expanding_here_string_is_unverifiable', 'git commit -F - <<< "$MSG"',
                 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('unquoted_heredoc_substitution_with_expansion_is_unverifiable',
                 'git commit -m "$(cat <<EOF\nSubject $X\nEOF\n)"', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('unquoted_heredoc_input_with_expansion_is_unverifiable',
                 'git commit -F - <<EOF\nSubject $X\nEOF', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('unquoted_heredoc_input_with_backtick_is_unverifiable',
                 'git commit -F - <<EOF\nSubject `date`\nEOF', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('unquoted_heredoc_input_with_backslash_is_unverifiable',
                 'git commit -F - <<EOF\nSubject \\\\ x\nEOF', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('missing_message_file_is_unverifiable', 'git commit -F missing.txt', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('directory_message_file_is_unverifiable', 'git commit -F sub', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('unreadable_message_file_is_unverifiable', 'git commit -F locked.txt',
                 'deny', UNVERIFIABLE, 'R08', setup='unreadable-message'),
    DecisionCase('message_file_over_the_limit_is_unverifiable', 'git commit -F large.txt',
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('message_file_at_the_limit_is_allowed', 'git commit -F limit.txt', 'allow',
                 setup='message-files'),
    DecisionCase('configured_trailer_alias_is_unverifiable', 'git commit -m ok --trailer cab=Someone',
                 'deny', UNVERIFIABLE, 'R08', setup='trailer-alias'),
    DecisionCase('trailer_without_configuration_is_allowed', 'git commit -m ok --trailer Reviewed-by=Someone',
                 'allow'),
    DecisionCase('amend_without_edit_on_clean_head_is_allowed', 'git commit --amend --no-edit', 'allow'),
    DecisionCase('literal_heredoc_input_is_allowed',
                 "git commit -F - <<'EOF'\nAdd parser\n\nBody $NOT_EXPANDED.\nEOF", 'allow'),
    DecisionCase('literal_here_string_input_is_allowed', "git commit --file=- <<<'Add parser'", 'allow'),
    DecisionCase('plain_unquoted_heredoc_input_is_allowed', 'git commit -F - <<EOF\nAdd parser\nEOF', 'allow'),
    DecisionCase('trailer_in_message_option_is_forbidden', f"git commit -m 'Add parser\n\n{TRAILER}'",
                 'deny', FORBIDDEN, 'R09'),
    DecisionCase('trailer_in_repeated_message_option_is_forbidden', f"git commit -m 'Add parser' -m '{TRAILER}'",
                 'deny', FORBIDDEN, 'R09'),
    DecisionCase('trailer_in_long_message_option_is_forbidden', f"git commit --message='Add parser\n\n{TRAILER}'",
                 'deny', FORBIDDEN, 'R09'),
    DecisionCase('trailer_in_heredoc_substitution_is_forbidden',
                 f"git commit -m \"$(cat <<'EOF'\nAdd parser\n\n{TRAILER}\nEOF\n)\"", 'deny', FORBIDDEN, 'R09'),
    DecisionCase('trailer_in_message_file_is_forbidden', 'git commit -F trailer.txt', 'deny', FORBIDDEN, 'R09',
                 setup='message-files'),
    DecisionCase('trailer_in_attached_message_file_is_forbidden', 'git commit -Ftrailer.txt',
                 'deny', FORBIDDEN, 'R09', setup='message-files'),
    DecisionCase('trailer_in_long_message_file_is_forbidden', 'git commit --file=trailer.txt',
                 'deny', FORBIDDEN, 'R09', setup='message-files'),
    DecisionCase('crlf_trailer_in_message_file_is_forbidden', 'git commit -F crlf.txt', 'deny', FORBIDDEN, 'R09',
                 setup='message-files'),
    DecisionCase('message_file_resolves_from_the_directory_option', 'git -C sub commit -F msg.txt',
                 'deny', FORBIDDEN, 'R09', setup='message-files'),
    DecisionCase('message_file_resolves_from_the_cd_target', 'cd sub && git commit -F msg.txt',
                 'deny', FORBIDDEN, 'R09', setup='message-files'),
    DecisionCase('clean_message_file_is_allowed', 'git commit -F msg.txt', 'allow', setup='message-files'),
    DecisionCase('trailer_in_heredoc_input_is_forbidden', f"git commit -F - <<'EOF'\nAdd parser\n\n{TRAILER}\nEOF",
                 'deny', FORBIDDEN, 'R09'),
    DecisionCase('trailer_in_here_string_input_is_forbidden', f"git commit -F - <<<'{TRAILER}'",
                 'deny', FORBIDDEN, 'R09'),
    DecisionCase('trailer_option_is_forbidden', f"git commit -m ok --trailer '{TRAILER}'", 'deny', FORBIDDEN, 'R09'),
    DecisionCase('attached_trailer_option_with_equals_is_forbidden',
                 'git commit -m ok --trailer=Co-authored-by=Someone', 'deny', FORBIDDEN, 'R09'),
    DecisionCase('trailer_option_without_value_is_forbidden', 'git commit -m ok --trailer co-authored-by',
                 'deny', FORBIDDEN, 'R09'),
    DecisionCase('lowercase_trailer_without_space_is_forbidden', "git commit -m 'Add parser' -m 'co-authored-by:x'",
                 'deny', FORBIDDEN, 'R09'),
    DecisionCase('indented_trailer_is_forbidden', "git commit -m 'Add parser\n\n   Co-Authored-By: Someone'",
                 'deny', FORBIDDEN, 'R09'),
    DecisionCase('tab_indented_trailer_is_forbidden', "git commit -m 'Add parser\n\n\tCo-Authored-By: Someone'",
                 'deny', FORBIDDEN, 'R09'),
    DecisionCase('task_identifier_in_subject_is_forbidden', "git commit -m 'Fix T-04b parser'",
                 'deny', FORBIDDEN, 'R09'),
    DecisionCase('task_fix_identifier_in_subject_is_forbidden', "git commit -m 'Finish T-09-fix-x'",
                 'deny', FORBIDDEN, 'R09'),
    DecisionCase('decision_identifier_in_body_is_forbidden',
                 "git commit -m 'Add parser' -m 'See ADR-0007 for context.'", 'deny', FORBIDDEN, 'R09'),
    DecisionCase('short_decision_identifier_is_forbidden', "git commit -m 'see ADR-12'", 'deny', FORBIDDEN, 'R09'),
    DecisionCase('amend_without_edit_keeps_a_forbidden_head_message', 'git commit --amend --no-edit',
                 'deny', FORBIDDEN, 'R09', setup='trailer-head'),
    DecisionCase('model_version_is_allowed', "git commit -m 'fix GPT-4 parsing'", 'allow'),
    DecisionCase('t_shirt_wording_is_allowed', "git commit -m 'Bump T-shirt sizes'", 'allow'),
    DecisionCase('device_name_is_allowed', "git commit -m 'Support IoT-1 sensors'", 'allow'),
    DecisionCase('identifier_inside_a_longer_word_is_allowed', "git commit -m 'Tune HADR-1 failover'", 'allow'),
    DecisionCase('decision_prefix_without_digits_is_allowed', "git commit -m 'Explain the ADR- prefix'", 'allow'),
    DecisionCase('body_sentence_mentioning_the_trailer_is_allowed',
                 "git commit -m 'Remove trailer parsing' -m 'Remove Co-Authored-By handling from the parser.'",
                 'allow'),
    DecisionCase('amend_with_new_message_replaces_a_forbidden_head_message', 'git commit --amend -m ok', 'allow',
                 setup='trailer-head'),
    DecisionCase('amending_a_published_commit_needs_owner_approval', 'git commit --amend -m ok',
                 'ask', 'rewrite-published', 'R10', setup='published'),
    DecisionCase('amending_a_published_commit_without_edit_needs_owner_approval', 'git commit --amend --no-edit',
                 'ask', 'rewrite-published', 'R10', setup='published'),
    DecisionCase('unique_prefix_of_amend_needs_owner_approval', 'git commit --am -m ok',
                 'ask', 'rewrite-published', 'R10', setup='published'),
    DecisionCase('commit_reachable_from_any_remote_needs_owner_approval', 'git commit --amend -m ok',
                 'ask', 'rewrite-published', 'R10', setup='published-elsewhere'),
    DecisionCase('amending_an_unpushed_commit_is_allowed', 'git commit --amend -m ok', 'allow',
                 setup='published-ancestor'),
    DecisionCase('new_commit_on_published_head_is_allowed', 'git commit -m ok', 'allow', setup='published'),
    DecisionCase('forbidden_message_outranks_published_amend', "git commit --amend -m 'Fix T-04b parser'",
                 'deny', FORBIDDEN, 'R09', setup='published'),
    DecisionCase('negated_amend_is_a_new_commit', 'git commit --amend --no-amend -m ok', 'allow',
                 setup='published'),
)


class StagingTable(RuleFixture):
    """Table-driven decisions of git add and git stage."""


for staging_case in STAGING_CASES:
    setattr(StagingTable, 'test_' + staging_case.name, decision_test(staging_case))


class CommitTable(RuleFixture):
    """Table-driven decisions of git commit."""


for commit_case in COMMIT_CASES:
    setattr(CommitTable, 'test_' + commit_case.name, decision_test(commit_case))


class MessagePatterns(RuleFixture):
    """The forbidden commit-message patterns, the checked text and the message file limit."""

    DOCUMENTED = (r'(?im)^[ \t]*co-authored-by[ \t]*:',
                  r'(?<![A-Za-z0-9_-])T-[0-9]+[A-Za-z]*(?![A-Za-z0-9_])',
                  r'(?<![A-Za-z0-9_-])ADR-[0-9]+')

    def patterns(self) -> tuple[Any, ...]:
        return tuple(self.api('FORBIDDEN_PATTERNS'))

    def assert_pattern(self, index: int, blocked: tuple[str, ...], passed: tuple[str, ...]) -> None:
        pattern = self.patterns()[index]
        for text in blocked:
            with self.subTest(blocked=text):
                self.assertIsNotNone(pattern.search(text))
        for text in passed:
            with self.subTest(passed=text):
                self.assertIsNone(pattern.search(text))

    def test_patterns_are_the_documented_expressions(self) -> None:
        self.assertEqual(tuple(pattern.pattern for pattern in self.patterns()), self.DOCUMENTED)

    def test_trailer_pattern_blocks_trailer_lines_only(self) -> None:
        self.assert_pattern(0, ('Co-Authored-By: Name <mail>', 'co-authored-by:x', 'Subject\n\n  Co-authored-by: x'),
                            ('Remove Co-Authored-By handling', 'Subject\n\nSee Co-authored-by: x'))

    def test_task_identifier_pattern_uses_word_boundaries_and_digits(self) -> None:
        self.assert_pattern(1, ('T-01', 'T-04b', 'T-09-fix-x', 'Fix T-04b parser'), ('GPT-4', 'T-shirt', 'IoT-1'))

    def test_decision_identifier_pattern_requires_digits(self) -> None:
        self.assert_pattern(2, ('ADR-0007', 'see ADR-12'), ('HADR-1', 'ADR-'))

    def test_forbidden_message_checks_the_full_text(self) -> None:
        forbidden = self.api('forbidden_message')
        self.assertTrue(forbidden('Add parser\n\nCo-authored-by: x'))
        self.assertTrue(forbidden('Add parser\n\nFollows T-01.'))
        self.assertFalse(forbidden('Add parser\n\nRemove Co-Authored-By handling.'))

    def test_message_values_join_as_paragraphs(self) -> None:
        join = self.api('join_message')
        self.assertEqual(join(['one', 'two'], []), 'one\n\ntwo')
        self.assertEqual(join(['one'], []), 'one')

    def test_trailers_follow_a_blank_line_in_colon_form(self) -> None:
        joined = self.api('join_message')(['Subject'], ['Reviewed-by=Someone', 'Acked-by: Other', 'Co-authored-by'])
        self.assertEqual(joined, 'Subject\n\nReviewed-by: Someone\nAcked-by: Other\nCo-authored-by:')

    def test_message_file_limit_is_one_mebibyte(self) -> None:
        self.assertEqual(self.api('MAX_MESSAGE_FILE_BYTES'), 1024 * 1024)


class CommitDecisionOutput(RuleFixture):
    """Commit-message text never reaches a decision."""

    def test_forbidden_message_text_is_not_in_the_decision(self) -> None:
        marker = 'Distinctive-Marker-Words'
        command = f"git commit -m '{marker}' -m 'Co-authored-by: {marker} <m@example.invalid>'"
        result = self.api('decide')(self.event(command, str(self.project)), dict(self.environ))
        self.assertEqual((result.decision, result.reason_code), ('deny', FORBIDDEN))
        rendered = repr(result) + ' '.join(str(value) for value in vars(result).values())
        self.assertNotIn(marker, rendered)


class SlowRuleRead(RuleFixture):
    """A git read made by a rule that exceeds its time limit denies instead of hanging."""

    def test_hanging_staging_read_is_limit_exceeded(self) -> None:
        fake = self.probe / 'bin/git'
        fake.write_text('#!/bin/bash\n'
                        'case " $* " in *" ls-files "*) sleep 30 ;; esac\n'
                        f'exec {shlex.quote(REAL_GIT)} "$@"\n')
        fake.chmod(0o755)
        self.environ['PATH'] = f'{self.probe / "bin"}{os.pathsep}{self.environ["PATH"]}'
        started = time.monotonic()
        decision = self.decide(self.event('git add missing.txt', str(self.project)))
        elapsed = time.monotonic() - started
        self.assertEqual(decision[:2], ('deny', 'limit-exceeded'))
        self.assertLess(elapsed, 4.5, 'a timed-out read must be stopped, including its children')


class StateFixture(RuleFixture):
    """Repository states where an earlier part of the command can change what a rule reads."""

    def setup_published_main_on_feature(self) -> None:
        self.setup_published()
        self.git(self.project, 'switch', '-q', '-c', 'feature')
        self.git(self.project, 'commit', '-q', '--allow-empty', '-m', 'Local work')

    def setup_trailer_branch(self) -> None:
        self.git(self.project, 'switch', '-q', '-c', 'trailered')
        self.git(self.project, 'commit', '-q', '--allow-empty', '-m', 'Add parser', '-m', TRAILER)
        self.git(self.project, 'switch', '-q', 'main')

    def setup_clean_sub_message(self) -> None:
        (self.project / 'sub/msg.txt').write_text('Add parser\n')


# An earlier part of the same command that may write makes every later read of repository
# or file state unverifiable; commands that read no state keep their decision.
STATE_CHANGE_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('message_file_written_by_printf_is_unverifiable',
                 "printf 'Add parser\\n\\nCo-authored-by: X\\n' > msg.txt && git commit -F msg.txt",
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('message_file_written_by_heredoc_is_unverifiable',
                 "cat > msg.txt <<'EOF'\nAdd parser\n\nCo-authored-by: X\nEOF\ngit commit -F msg.txt",
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('message_file_appended_by_echo_is_unverifiable',
                 "echo 'Co-authored-by: X' >> msg.txt; git commit -F msg.txt",
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('message_file_replaced_by_copy_is_unverifiable', 'cp trailer.txt msg.txt && git commit -F msg.txt',
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('message_file_written_in_a_subshell_is_unverifiable', '(printf x > msg.txt); git commit -F msg.txt',
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('message_file_written_in_a_substitution_is_unverifiable',
                 'echo "$(printf x > msg.txt)" && git commit -F msg.txt',
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('message_file_written_by_a_pipeline_element_is_unverifiable',
                 "echo 'Co-authored-by: X' | tee msg.txt && git commit -F msg.txt",
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('message_file_written_in_the_background_is_unverifiable', 'printf x > msg.txt & git commit -F msg.txt',
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('message_file_written_by_a_shell_string_is_unverifiable',
                 "bash -c 'printf x > msg.txt'; git commit -F msg.txt",
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('message_file_written_by_read_only_git_output_is_unverifiable',
                 'git log -1 > msg.txt && git commit -F msg.txt', 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('message_file_after_governed_git_is_unverifiable', 'git add a.txt && git commit -F msg.txt',
                 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
    DecisionCase('amend_after_switching_to_a_published_branch_is_unsupported',
                 'git switch main && git commit --amend -m ok', 'deny', 'unsupported-form', 'R10',
                 setup='published-main-on-feature'),
    DecisionCase('amend_without_edit_after_switching_to_a_trailer_branch_is_unverifiable',
                 'git switch trailered && git commit --amend --no-edit', 'deny', UNVERIFIABLE, 'R08',
                 setup='trailer-branch'),
    DecisionCase('amend_without_edit_after_governed_staging_is_unverifiable',
                 'git add a.txt && git commit --amend --no-edit', 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('amend_after_a_file_write_is_unsupported', 'echo x > a.txt && git commit --amend -m ok',
                 'deny', 'unsupported-form', 'R10'),
    DecisionCase('trailer_after_configuration_change_is_unverifiable',
                 'git config trailer.cab.key Co-authored-by && git commit -m ok --trailer cab=Someone',
                 'deny', UNVERIFIABLE, 'R08'),
    DecisionCase('alias_after_configuration_change_is_unsupported', "git config alias.p 'push -f' && git p",
                 'deny', 'unsupported-form', 'R31'),
    DecisionCase('governed_git_after_repository_creation_is_unsupported',
                 'git -C @plain@ init -q && git -C @plain@ add note.txt', 'deny', 'unsupported-form'),
    DecisionCase('staging_a_file_created_earlier_is_unsupported', 'touch new.txt && git add new.txt',
                 'deny', 'unsupported-form', 'R02'),
    DecisionCase('staging_a_file_written_earlier_is_unsupported', 'echo x > a.txt && git add a.txt',
                 'deny', 'unsupported-form', 'R02'),
    DecisionCase('second_staging_command_is_unsupported', 'git add a.txt && git add b.txt',
                 'deny', 'unsupported-form', 'R02'),
    DecisionCase('commit_path_written_earlier_is_unsupported', 'touch a.txt && git commit -m ok a.txt',
                 'deny', 'unsupported-form', 'R07'),
    DecisionCase('message_option_after_governed_staging_is_allowed', 'git add a.txt && git commit -m ok', 'allow'),
    DecisionCase('message_file_after_cd_is_allowed', 'cd sub && git commit -F msg.txt', 'allow',
                 setup='clean-sub-message'),
    DecisionCase('message_file_after_echo_without_redirection_is_allowed', 'echo hi && git commit -F msg.txt',
                 'allow', setup='message-files'),
    DecisionCase('message_file_after_heredoc_into_a_data_program_is_allowed',
                 "cat <<'EOF'\nx\nEOF\ngit commit -F msg.txt", 'allow', setup='message-files'),
    DecisionCase('message_file_after_read_only_git_is_allowed', 'git status && git commit -F msg.txt', 'allow',
                 setup='message-files'),
    DecisionCase('message_file_after_plain_assignments_is_allowed', 'X=1; export FOO=2; git commit -F msg.txt',
                 'allow', setup='message-files'),
    DecisionCase('amend_without_edit_after_cd_is_allowed', 'cd sub && git commit --amend --no-edit', 'allow'),
    DecisionCase('literal_message_input_after_a_write_is_allowed',
                 "printf x > a.txt && git commit -F - <<'EOF'\nAdd parser\nEOF", 'allow'),
    DecisionCase('message_heredoc_after_a_write_is_allowed', 'printf x > a.txt && ' + COMMIT_HEREDOC, 'allow'),
    DecisionCase('write_after_the_commit_does_not_change_it', 'git commit -F msg.txt && echo x > msg.txt', 'allow',
                 setup='message-files'),
    DecisionCase('blanket_staging_after_a_write_keeps_its_reason', 'touch new.txt && git add -A',
                 'deny', BLANKET, 'R01'),
    DecisionCase('message_file_after_read_only_git_into_null_device_is_allowed',
                 'git status 2>/dev/null; git commit -F msg.txt', 'allow', setup='message-files'),
    DecisionCase('amend_without_edit_after_output_to_null_device_is_allowed',
                 'git log -1 >/dev/null && git commit --amend --no-edit', 'allow'),
    DecisionCase('message_file_after_read_only_git_into_a_file_is_unverifiable',
                 'git status > out.txt; git commit -F msg.txt', 'deny', UNVERIFIABLE, 'R08', setup='message-files'),
)


class StateChangeTable(StateFixture):
    """Table-driven decisions after an earlier part of the command may change state."""


for state_case in STATE_CHANGE_CASES:
    setattr(StateChangeTable, 'test_' + state_case.name, decision_test(state_case))


CLASSES = (CoreSurface, DecisionCombination, OptionParsing, EventValidation, DecisionTable,
           ResolutionTable, InvocationDetails, GitReadIsolation, SlowGitRead, FailClosedTable,
           DecidedTable, StagingTable, CommitTable, MessagePatterns, CommitDecisionOutput, SlowRuleRead,
           StateChangeTable)


PROTECTED = 'push-protected-target'
FORCE = 'push-force'
LEASE = 'push-lease-unverified'
DELETE = 'push-delete'
BULK = 'push-bulk-or-tags'
TARGET = 'push-target-unknown'
DEFAULT_UNKNOWN = 'default-branch-unknown'
LEASE_SHA = '0123456789abcdef0123456789abcdef01234567'
NETWORK_SUBCOMMANDS = ('fetch', 'ls-remote', 'push', 'pull', 'clone', 'remote', 'send-pack', 'receive-pack')


class PushFixture(RailsFixture):
    """The project with local bare remotes, remote-tracking default branches and the push
    configuration that decides each destination. Fixture pushes run before the snapshot."""

    def add_remote(self, name: str, branches: tuple[str, ...], default: str | None) -> None:
        bare = self.world / f'{name}.git'
        self.git(self.world, 'init', '-q', '--bare', str(bare))
        self.git(self.project, 'remote', 'add', name, str(bare))
        self.git(self.project, 'push', '-q', name, *branches)
        if default is not None:
            self.git(self.project, 'remote', 'set-head', name, default)

    def set_config(self, key: str, value: str) -> None:
        self.git(self.project, 'config', '--add', key, value)

    def setup_push(self) -> None:
        for branch in ('feat/x', 'feat/y', 'develop'):
            self.git(self.project, 'branch', branch)
        self.git(self.project, 'tag', 'v1')
        self.add_remote('origin', ('main', 'feat/x', 'develop'), 'main')

    def setup_push_feature(self) -> None:
        self.setup_push()
        self.git(self.project, 'switch', '-q', 'feat/x')

    def setup_push_simple(self) -> None:
        self.setup_push()
        self.set_config('push.default', 'simple')

    def setup_push_current(self) -> None:
        self.setup_push_feature()
        self.set_config('push.default', 'current')

    def setup_push_matching(self) -> None:
        self.setup_push_feature()
        self.set_config('push.default', 'matching')

    def setup_push_nothing(self) -> None:
        self.setup_push_feature()
        self.set_config('push.default', 'nothing')

    def setup_push_upstream_main(self) -> None:
        self.setup_push_feature()
        self.set_config('push.default', 'upstream')
        self.set_config('branch.feat/x.remote', 'origin')
        self.set_config('branch.feat/x.merge', 'refs/heads/main')

    def setup_push_upstream_feature(self) -> None:
        self.setup_push_feature()
        self.set_config('push.default', 'upstream')
        self.set_config('branch.feat/x.remote', 'origin')
        self.set_config('branch.feat/x.merge', 'refs/heads/feat/x')

    def setup_push_upstream_missing(self) -> None:
        self.setup_push_feature()
        self.set_config('push.default', 'upstream')

    def setup_push_detached(self) -> None:
        self.setup_push()
        self.git(self.project, 'switch', '-q', '--detach', 'HEAD')

    def setup_push_configured_refspec(self) -> None:
        self.setup_push_feature()
        self.set_config('remote.origin.push', 'refs/heads/feat/x:refs/heads/feat/x')

    def setup_push_mirror_remote(self) -> None:
        self.setup_push_feature()
        self.set_config('remote.origin.mirror', 'true')

    def setup_push_follow_tags(self) -> None:
        self.setup_push_feature()
        self.set_config('push.followTags', 'true')

    def setup_push_no_default_head(self) -> None:
        self.setup_push_feature()
        self.git(self.project, 'remote', 'set-head', 'origin', '-d')

    def setup_push_develop_head(self) -> None:
        self.setup_push_feature()
        self.git(self.project, 'remote', 'set-head', 'origin', 'develop')

    def setup_push_extra_pattern(self) -> None:
        self.setup_push_feature()
        self.set_config('orchestrail.protectedBranch', 'stable/*')
        self.set_config('orchestrail.protectedBranch', 'hotfix')

    def setup_push_without_origin(self) -> None:
        for branch in ('feat/x', 'trunk'):
            self.git(self.project, 'branch', branch)
        self.add_remote('upstream', ('main', 'trunk'), 'trunk')
        self.git(self.project, 'switch', '-q', 'feat/x')

    def setup_push_without_origin_pattern(self) -> None:
        self.setup_push_without_origin()
        self.set_config('orchestrail.protectedBranch', 'stable/*')

    def setup_push_backup(self) -> None:
        self.setup_push_feature()
        self.add_remote('backup', ('feat/x',), None)

    def setup_push_branch_push_remote(self) -> None:
        self.setup_push_backup()
        self.set_config('branch.feat/x.pushRemote', 'backup')

    def setup_push_push_default(self) -> None:
        self.setup_push_backup()
        self.set_config('remote.pushDefault', 'backup')

    def setup_push_branch_remote(self) -> None:
        self.setup_push_backup()
        self.set_config('branch.feat/x.remote', 'backup')

    def setup_push_push_remote_first(self) -> None:
        self.setup_push_backup()
        self.set_config('branch.feat/x.pushRemote', 'origin')
        self.set_config('remote.pushDefault', 'backup')
        self.set_config('branch.feat/x.remote', 'backup')

    def setup_push_push_default_before_branch_remote(self) -> None:
        self.setup_push_backup()
        self.set_config('remote.pushDefault', 'origin')
        self.set_config('branch.feat/x.remote', 'backup')

    def setup_push_branch_remote_before_origin(self) -> None:
        self.setup_push_without_origin()
        self.set_config('branch.feat/x.remote', 'upstream')


# git push: destinations resolved from operands, refspecs and push configuration, checked
# against the protected set of the target remote; every destination counts.
PUSH_CASES: tuple[DecisionCase, ...] = (
    # Protected destinations.
    DecisionCase('push_of_main_to_origin_needs_owner_approval', 'git push origin main',
                 'ask', PROTECTED, 'R16', setup='push'),
    DecisionCase('push_of_a_feature_onto_main_needs_owner_approval', 'git push origin feat/x:main',
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('push_of_head_to_a_release_ref_needs_owner_approval',
                 'git push origin HEAD:refs/heads/release/1.2', 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('push_of_head_on_main_needs_owner_approval', 'git push origin HEAD',
                 'ask', PROTECTED, 'R16', setup='push'),
    DecisionCase('bare_push_on_main_with_default_configuration_needs_owner_approval', 'git push',
                 'ask', PROTECTED, 'R16', setup='push'),
    DecisionCase('bare_push_on_main_with_simple_default_needs_owner_approval', 'git push',
                 'ask', PROTECTED, 'R16', setup='push-simple'),
    DecisionCase('push_to_a_configured_protected_pattern_needs_owner_approval', 'git push origin feat/x:stable/2',
                 'ask', PROTECTED, 'R16', setup='push-extra-pattern'),
    DecisionCase('push_to_a_configured_protected_name_needs_owner_approval', 'git push origin feat/x:hotfix',
                 'ask', PROTECTED, 'R16', setup='push-extra-pattern'),
    DecisionCase('push_to_a_name_the_pattern_does_not_match_is_allowed', 'git push origin feat/x:stablex',
                 'allow', setup='push-extra-pattern'),
    DecisionCase('one_protected_refspec_among_several_needs_owner_approval', 'git push origin feat/x feat/y:main',
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('several_unprotected_refspecs_are_allowed', 'git push origin feat/x feat/y',
                 'allow', setup='push-feature'),
    DecisionCase('explicit_branch_ref_destination_to_main_needs_owner_approval',
                 'git push origin feat/x:refs/heads/main', 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('explicit_branch_ref_destination_to_a_feature_is_allowed',
                 'git push origin feat/x:refs/heads/feat/z', 'allow', setup='push-feature'),
    DecisionCase('master_is_always_protected', 'git push origin feat/x:master', 'ask', PROTECTED, 'R16',
                 setup='push-feature'),
    DecisionCase('remote_default_branch_is_protected', 'git push origin feat/x:develop', 'ask', PROTECTED, 'R16',
                 setup='push-develop-head'),
    DecisionCase('main_stays_protected_when_the_remote_default_is_another_branch', 'git push origin feat/x:main',
                 'ask', PROTECTED, 'R16', setup='push-develop-head'),
    DecisionCase('develop_is_not_protected_while_the_remote_default_is_main', 'git push origin feat/x:develop',
                 'allow', setup='push-feature'),
    DecisionCase('upstream_default_onto_main_needs_owner_approval', 'git push', 'ask', PROTECTED, 'R16',
                 setup='push-upstream-main'),
    DecisionCase('other_remote_default_branch_is_protected', 'git push upstream feat/x:trunk',
                 'ask', PROTECTED, 'R16', setup='push-without-origin'),
    DecisionCase('push_from_unregistered_cwd_into_the_project_is_decided', 'git -C @project@ push origin main',
                 'ask', PROTECTED, 'R16', cwd='outside', setup='push-feature'),
    # Allowed pushes.
    DecisionCase('bare_push_on_a_feature_is_allowed', 'git push', 'allow', setup='push-feature'),
    DecisionCase('push_of_a_feature_to_origin_is_allowed', 'git push origin feat/x', 'allow', setup='push-feature'),
    DecisionCase('push_of_head_on_a_feature_is_allowed', 'git push origin HEAD', 'allow', setup='push-feature'),
    DecisionCase('bare_push_with_current_default_is_allowed', 'git push', 'allow', setup='push-current'),
    DecisionCase('upstream_default_onto_the_same_feature_is_allowed', 'git push', 'allow',
                 setup='push-upstream-feature'),
    DecisionCase('push_from_a_subdirectory_is_allowed', 'cd sub && git push origin feat/x', 'allow',
                 setup='push-feature'),
    DecisionCase('push_with_a_directory_option_is_allowed', 'git -C sub push origin feat/x', 'allow',
                 setup='push-feature'),
    DecisionCase('push_with_harmless_options_is_allowed', 'git push -u -v --atomic origin feat/x', 'allow',
                 setup='push-feature'),
    DecisionCase('push_to_another_configured_remote_is_allowed', 'git push upstream feat/x', 'allow',
                 setup='push-without-origin'),
    DecisionCase('push_after_read_only_git_is_allowed', 'git status && git push origin feat/x', 'allow',
                 setup='push-feature'),
    DecisionCase('timeout_wrapped_feature_push_is_allowed', 'timeout 30 git push origin feat/x', 'allow',
                 setup='push-feature'),
    # Force.
    DecisionCase('short_force_needs_owner_approval', 'git push -f', 'ask', FORCE, 'R17', setup='push-feature'),
    DecisionCase('timeout_wrapped_force_push_needs_owner_approval', 'timeout 30 git push -f',
                 'ask', FORCE, 'R17', setup='push-feature'),
    DecisionCase('long_force_needs_owner_approval', 'git push --force origin feat/x', 'ask', FORCE, 'R17',
                 setup='push-feature'),
    DecisionCase('ambiguous_force_prefix_needs_owner_approval', 'git push --forc', 'ask', FORCE, 'R17',
                 setup='push-feature'),
    DecisionCase('force_in_a_short_bundle_needs_owner_approval', 'git push -uf origin feat/x', 'ask', FORCE, 'R17',
                 setup='push-feature'),
    DecisionCase('plus_refspec_needs_owner_approval', 'git push origin +feat/x', 'ask', FORCE, 'R17',
                 setup='push-feature'),
    DecisionCase('force_if_includes_without_lease_needs_owner_approval', 'git push --force-if-includes origin feat/x',
                 'ask', FORCE, 'R17', setup='push-feature'),
    DecisionCase('negated_force_is_allowed', 'git push -f --no-force origin feat/x', 'allow', setup='push-feature'),
    DecisionCase('force_from_unregistered_cwd_into_the_project_needs_owner_approval', 'git -C @project@ push -f',
                 'ask', FORCE, 'R17', cwd='outside', setup='push-feature'),
    DecisionCase('protected_destination_outranks_force', 'git push -f origin main', 'ask', PROTECTED, 'R16',
                 setup='push-feature'),
    # Leases without a restack journal.
    DecisionCase('bare_lease_without_a_journal_is_unverified', 'git push --force-with-lease',
                 'ask', LEASE, 'R18', setup='push-feature'),
    DecisionCase('lease_on_a_ref_without_a_journal_is_unverified', 'git push --force-with-lease=feat/x origin feat/x',
                 'ask', LEASE, 'R18', setup='push-feature'),
    DecisionCase('explicit_lease_without_a_journal_is_unverified',
                 f'git push --force-with-lease=feat/x:{LEASE_SHA} origin feat/x', 'ask', LEASE, 'R18',
                 setup='push-feature'),
    DecisionCase('absent_lease_without_a_journal_is_unverified',
                 'git push --force-with-lease=feat/z: origin feat/x:feat/z', 'ask', LEASE, 'R18',
                 setup='push-feature'),
    DecisionCase('negated_lease_is_allowed', 'git push --force-with-lease --no-force-with-lease origin feat/x',
                 'allow', setup='push-feature'),
    DecisionCase('force_outranks_an_unverified_lease', 'git push -f --force-with-lease origin feat/x',
                 'ask', FORCE, 'R17', setup='push-feature'),
    # Deletion.
    DecisionCase('long_delete_needs_owner_approval', 'git push origin --delete feat/y', 'ask', DELETE, 'R15',
                 setup='push-feature'),
    DecisionCase('short_delete_needs_owner_approval', 'git push -d origin feat/y', 'ask', DELETE, 'R15',
                 setup='push-feature'),
    DecisionCase('empty_source_refspec_needs_owner_approval', 'git push origin :feat/y', 'ask', DELETE, 'R15',
                 setup='push-feature'),
    DecisionCase('deleting_main_is_reported_as_a_deletion', 'git push origin --delete main', 'ask', DELETE, 'R15',
                 setup='push-feature'),
    DecisionCase('ambiguous_delete_prefix_needs_owner_approval', 'git push --d origin feat/y', 'ask', DELETE, 'R15',
                 setup='push-feature'),
    DecisionCase('prune_needs_owner_approval', 'git push --prune origin feat/x', 'ask', DELETE, 'R15',
                 setup='push-feature'),
    DecisionCase('delete_among_allowed_refspecs_needs_owner_approval', 'git push origin feat/x :feat/y',
                 'ask', DELETE, 'R15', setup='push-feature'),
    # Bulk and tag pushes.
    DecisionCase('tags_flag_needs_owner_approval', 'git push --tags', 'ask', BULK, 'R14', setup='push-feature'),
    DecisionCase('mirror_flag_needs_owner_approval', 'git push --mirror', 'ask', BULK, 'R14', setup='push-feature'),
    DecisionCase('all_flag_needs_owner_approval', 'git push --all', 'ask', BULK, 'R14', setup='push-feature'),
    DecisionCase('branches_flag_needs_owner_approval', 'git push --branches origin', 'ask', BULK, 'R14',
                 setup='push-feature'),
    DecisionCase('follow_tags_flag_needs_owner_approval', 'git push --follow-tags origin feat/x', 'ask', BULK, 'R14',
                 setup='push-feature'),
    DecisionCase('tag_source_needs_owner_approval', 'git push origin v1', 'ask', BULK, 'R14', setup='push-feature'),
    DecisionCase('tag_source_with_short_destination_needs_owner_approval', 'git push origin v1:v2',
                 'ask', BULK, 'R14', setup='push-feature'),
    DecisionCase('explicit_tag_ref_needs_owner_approval', 'git push origin refs/tags/v1', 'ask', BULK, 'R14',
                 setup='push-feature'),
    DecisionCase('tag_destination_needs_owner_approval', 'git push origin feat/x:refs/tags/x', 'ask', BULK, 'R14',
                 setup='push-feature'),
    DecisionCase('tag_keyword_needs_owner_approval', 'git push origin tag v1', 'ask', BULK, 'R14',
                 setup='push-feature'),
    DecisionCase('matching_default_needs_owner_approval', 'git push', 'ask', BULK, 'R14', setup='push-matching'),
    DecisionCase('matching_refspec_needs_owner_approval', 'git push origin :', 'ask', BULK, 'R14',
                 setup='push-feature'),
    DecisionCase('mirror_remote_configuration_needs_owner_approval', 'git push', 'ask', BULK, 'R14',
                 setup='push-mirror-remote'),
    DecisionCase('follow_tags_configuration_needs_owner_approval', 'git push origin feat/x', 'ask', BULK, 'R14',
                 setup='push-follow-tags'),
    DecisionCase('negated_tags_flag_is_allowed', 'git push --tags --no-tags origin feat/x', 'allow',
                 setup='push-feature'),
    # Unresolvable targets.
    DecisionCase('url_remote_is_push_target_unknown', 'git push https://example.invalid/r.git feat/x',
                 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('path_remote_is_push_target_unknown', 'git push @outside@ feat/x', 'deny', TARGET, 'R12',
                 setup='push-feature'),
    DecisionCase('unknown_remote_name_is_push_target_unknown', 'git push nowhere feat/x', 'deny', TARGET, 'R12',
                 setup='push-feature'),
    DecisionCase('branch_name_in_the_remote_position_is_push_target_unknown', 'git push feat/x feat/y:main',
                 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('bare_push_on_detached_head_is_push_target_unknown', 'git push', 'deny', TARGET, 'R12',
                 setup='push-detached'),
    DecisionCase('head_refspec_on_detached_head_is_push_target_unknown', 'git push origin HEAD',
                 'deny', TARGET, 'R12', setup='push-detached'),
    DecisionCase('configured_remote_refspec_is_push_target_unknown', 'git push', 'deny', TARGET, 'R12',
                 setup='push-configured-refspec'),
    DecisionCase('configured_remote_refspec_with_explicit_refspec_is_push_target_unknown',
                 'git push origin feat/x', 'deny', TARGET, 'R12', setup='push-configured-refspec'),
    DecisionCase('nothing_default_is_push_target_unknown', 'git push', 'deny', TARGET, 'R12', setup='push-nothing'),
    DecisionCase('upstream_default_without_upstream_is_push_target_unknown', 'git push', 'deny', TARGET, 'R12',
                 setup='push-upstream-missing'),
    DecisionCase('wildcard_refspec_is_push_target_unknown', "git push origin 'refs/heads/*:refs/heads/*'",
                 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('negative_refspec_is_push_target_unknown', "git push origin '^refs/heads/feat/y'",
                 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('bare_push_without_origin_or_configured_remote_is_push_target_unknown', 'git push',
                 'deny', TARGET, 'R12', setup='push-without-origin'),
    DecisionCase('push_without_any_remote_is_push_target_unknown', 'git push origin main', 'deny', TARGET, 'R12'),
    # Missing remote default branch.
    DecisionCase('missing_remote_default_branch_is_default_branch_unknown', 'git push origin feat/x',
                 'deny', DEFAULT_UNKNOWN, 'R13', setup='push-no-default-head'),
    DecisionCase('remote_without_default_branch_is_default_branch_unknown', 'git push backup feat/x',
                 'deny', DEFAULT_UNKNOWN, 'R13', setup='push-backup'),
    DecisionCase('missing_default_branch_outranks_force', 'git push -f origin feat/x',
                 'deny', DEFAULT_UNKNOWN, 'R13', setup='push-no-default-head'),
    # Remote resolution order and the --repo option.
    DecisionCase('branch_push_remote_is_the_default_target', 'git push', 'deny', DEFAULT_UNKNOWN, 'R13',
                 setup='push-branch-push-remote'),
    DecisionCase('push_default_remote_is_the_default_target', 'git push', 'deny', DEFAULT_UNKNOWN, 'R13',
                 setup='push-push-default'),
    DecisionCase('branch_remote_is_the_default_target', 'git push', 'deny', DEFAULT_UNKNOWN, 'R13',
                 setup='push-branch-remote'),
    DecisionCase('branch_push_remote_wins_over_the_other_defaults', 'git push', 'allow',
                 setup='push-push-remote-first'),
    DecisionCase('push_default_remote_wins_over_the_branch_remote', 'git push', 'allow',
                 setup='push-push-default-before-branch-remote'),
    DecisionCase('branch_remote_wins_over_a_missing_origin', 'git push', 'allow',
                 setup='push-branch-remote-before-origin'),
    DecisionCase('explicit_remote_wins_over_configured_defaults', 'git push origin feat/x', 'allow',
                 setup='push-branch-push-remote'),
    DecisionCase('repo_option_names_the_remote', 'git push --repo=origin', 'allow', setup='push-feature'),
    DecisionCase('separate_repo_option_names_the_remote', 'git push --repo origin', 'allow', setup='push-feature'),
    DecisionCase('repo_option_on_main_needs_owner_approval', 'git push --repo=origin', 'ask', PROTECTED, 'R16',
                 setup='push'),
    DecisionCase('repo_option_with_a_url_is_push_target_unknown', 'git push --repo=https://example.invalid/r.git',
                 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('repo_option_naming_a_remote_without_default_branch_is_default_branch_unknown',
                 'git push --repo=backup', 'deny', DEFAULT_UNKNOWN, 'R13', setup='push-backup'),
    DecisionCase('operand_remote_wins_over_the_repo_option', 'git push --repo=backup origin feat/x', 'allow',
                 setup='push-backup'),
    # Dry runs skip every other push rule.
    DecisionCase('dry_run_of_a_protected_push_is_allowed', 'git push --dry-run origin main', 'allow',
                 setup='push-feature'),
    DecisionCase('short_dry_run_of_a_forced_push_is_allowed', 'git push -n -f origin main', 'allow',
                 setup='push-feature'),
    DecisionCase('dry_run_to_a_url_is_allowed', 'git push --dry-run https://example.invalid/r.git main', 'allow',
                 setup='push-feature'),
    DecisionCase('dry_run_with_missing_default_branch_is_allowed', 'git push --dry-run origin feat/x', 'allow',
                 setup='push-no-default-head'),
    DecisionCase('negated_dry_run_is_decided', 'git push --dry-run --no-dry-run origin main', 'ask', PROTECTED,
                 'R16', setup='push-feature'),
    # Options that cannot be verified.
    DecisionCase('unknown_push_option_is_unsupported', 'git push --bogus origin feat/x', 'deny', 'unsupported-form',
                 setup='push-feature'),
    DecisionCase('missing_option_value_is_unsupported', 'git push origin feat/x --repo', 'deny', 'unsupported-form',
                 setup='push-feature'),
    DecisionCase('receive_pack_program_is_unsupported', 'git push --receive-pack=evil origin feat/x',
                 'deny', 'unsupported-form', setup='push-feature'),
    DecisionCase('exec_program_is_unsupported', 'git push --exec evil origin feat/x', 'deny', 'unsupported-form',
                 setup='push-feature'),
    DecisionCase('on_demand_submodule_push_is_unsupported', 'git push --recurse-submodules=on-demand origin feat/x',
                 'deny', 'unsupported-form', setup='push-feature'),
    DecisionCase('submodule_check_is_allowed', 'git push --recurse-submodules=check origin feat/x', 'allow',
                 setup='push-feature'),
)

# An earlier part of the same command that may write makes every push-target read
# unverifiable; a dry run reads nothing and stays allowed.
PUSH_STATE_CHANGE_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('push_after_checkout_is_push_target_unknown', 'git checkout main && git push',
                 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('push_after_switch_is_push_target_unknown', 'git switch feat/x && git push origin feat/x',
                 'deny', TARGET, 'R12', setup='push'),
    DecisionCase('push_after_push_configuration_is_push_target_unknown',
                 'git config push.default matching && git push', 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('push_after_remote_change_is_push_target_unknown',
                 'git remote set-head origin feat/x; git push origin main', 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('push_after_a_file_write_is_push_target_unknown', 'echo x > a.txt && git push origin feat/x',
                 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('push_after_a_commit_is_push_target_unknown', 'git commit -m ok && git push origin feat/x',
                 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('second_push_is_push_target_unknown', 'git push origin feat/x && git push origin feat/y',
                 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('push_after_fetch_is_push_target_unknown', 'git fetch origin && git push origin feat/x',
                 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('push_after_a_write_in_a_subshell_is_push_target_unknown',
                 '(git switch -q main); git push origin HEAD', 'deny', TARGET, 'R12', setup='push-feature'),
    DecisionCase('dry_run_after_a_write_is_allowed', 'git checkout main && git push --dry-run origin main', 'allow',
                 setup='push-feature'),
    DecisionCase('push_after_cd_and_assignments_is_allowed', 'cd sub; X=1; export Y=2; git push origin feat/x',
                 'allow', setup='push-feature'),
    DecisionCase('write_after_the_push_does_not_change_it', 'git push origin feat/x && echo x > a.txt', 'allow',
                 setup='push-feature'),
)


class PushTable(PushFixture):
    """Table-driven decisions of git push."""


for push_case in (*PUSH_CASES, *PUSH_STATE_CHANGE_CASES):
    setattr(PushTable, 'test_' + push_case.name, decision_test(push_case))


class ProtectedRefs(PushFixture):
    """The protected branch set of a target remote and the local set shared with other rules."""

    def invocation(self) -> Any:
        return self.resolve('git status', str(self.project)).invocations[0]

    def context(self) -> Any:
        return self.api('Context')(cwd=str(self.project), roots=self.roots, environ=dict(self.environ))

    def remote_set(self, remote: str | None) -> Any:
        result = self.api('protected_branches')(remote, self.invocation(), self.context())
        return None if result is None else set(result)

    def local_set(self) -> Any:
        result = self.api('local_protected_branches')(self.invocation(), self.context())
        return None if result is None else set(result)

    def test_fixed_names_are_main_master_and_release(self) -> None:
        self.assertEqual(tuple(self.api('DEFAULT_PROTECTED')), ('main', 'master', 'release/*'))

    def test_remote_default_branch_joins_the_fixed_names(self) -> None:
        self.setup_push_develop_head()
        self.assertEqual(self.remote_set('origin'), {'develop', 'main', 'master', 'release/*'})

    def test_configured_patterns_join_the_set(self) -> None:
        self.setup_push_extra_pattern()
        self.assertEqual(self.remote_set('origin'), {'main', 'master', 'release/*', 'stable/*', 'hotfix'})

    def test_missing_remote_default_branch_cannot_be_computed(self) -> None:
        self.setup_push_no_default_head()
        self.assertIsNone(self.remote_set('origin'))

    def test_no_remote_gives_the_fixed_and_configured_names(self) -> None:
        self.setup_push_extra_pattern()
        self.assertEqual(self.remote_set(None), {'main', 'master', 'release/*', 'stable/*', 'hotfix'})

    def test_local_protection_uses_the_origin_default_branch(self) -> None:
        self.setup_push_develop_head()
        self.assertEqual(self.local_set(), {'develop', 'main', 'master', 'release/*'})

    def test_local_protection_without_origin_ignores_other_remotes(self) -> None:
        self.setup_push_without_origin_pattern()
        self.assertEqual(self.local_set(), {'main', 'master', 'release/*', 'stable/*'})

    def test_local_protection_with_origin_but_no_default_branch_cannot_be_computed(self) -> None:
        self.setup_push_no_default_head()
        self.assertIsNone(self.local_set())

    def test_protection_matches_branch_refs_by_short_name(self) -> None:
        is_protected = self.api('is_protected')
        patterns = ('main', 'release/*', 'stable/*')
        for ref, expected in (('refs/heads/main', True), ('refs/heads/release/1.2', True),
                              ('refs/heads/stable/a', True), ('refs/heads/feat/x', False),
                              ('refs/heads/mainline', False), ('refs/heads/Main', False),
                              ('refs/tags/main', False), ('refs/remotes/origin/main', False)):
            with self.subTest(ref=ref):
                self.assertIs(is_protected(ref, patterns), expected)


class LeaseVerifierInterface(PushFixture):
    """The force-with-lease rule hands explicit leases to a replaceable verifier."""

    def install(self, verified: bool) -> list[tuple[Any, Any, Any]]:
        calls: list[tuple[Any, Any, Any]] = []
        verdict = self.api('LeaseVerdict')
        original = self.api('LEASE_VERIFIER')

        def verifier(request: Any, invocation: Any, context: Any) -> Any:
            calls.append((request, invocation, context))
            return verdict(verified, None if verified else 'fixture verifier refused')
        setattr(CORE, 'LEASE_VERIFIER', verifier)
        self.addCleanup(setattr, CORE, 'LEASE_VERIFIER', original)
        return calls

    def tip(self, ref: str) -> str:
        return subprocess.run([REAL_GIT, 'rev-parse', ref], cwd=self.project, env=self.git_environ, check=True,
                              capture_output=True, text=True).stdout.strip()

    def push(self, arguments: str) -> tuple[str, str | None, str | None]:
        return self.decide(self.event('git push ' + arguments, str(self.project)))

    def test_default_verifier_is_the_no_journal_implementation(self) -> None:
        self.assertIs(self.api('LEASE_VERIFIER'), self.api('no_journal_verifier'))

    def test_explicit_lease_reaches_the_verifier(self) -> None:
        self.setup_push_feature()
        calls = self.install(True)
        sha = self.tip('refs/remotes/origin/feat/x')
        self.assertEqual(self.push(f'--force-with-lease=feat/x:{sha} origin feat/x'), ('allow', None, None))
        self.assertEqual(len(calls), 1)
        request, invocation, _ = calls[0]
        self.assertEqual((request.remote, tuple(request.destinations), tuple(request.leases), request.forced),
                         ('origin', ('refs/heads/feat/x',), (('refs/heads/feat/x', sha),), False))
        self.assertEqual(invocation.common_dir, str(self.project / '.git'))

    def test_lease_for_a_ref_recorded_as_absent_reaches_the_verifier(self) -> None:
        self.setup_push_feature()
        calls = self.install(True)
        self.assertEqual(self.push('--force-with-lease=refs/heads/feat/z: origin feat/x:feat/z'),
                         ('allow', None, None))
        self.assertEqual(tuple(calls[0][0].leases), (('refs/heads/feat/z', ''),))

    def test_refused_verification_asks(self) -> None:
        self.setup_push_feature()
        self.install(False)
        sha = self.tip('refs/remotes/origin/feat/x')
        self.assertEqual(self.push(f'--force-with-lease=feat/x:{sha} origin feat/x'), ('ask', LEASE, 'R18'))

    def test_no_journal_implementation_refuses_and_names_the_check(self) -> None:
        self.setup_push_feature()
        calls = self.install(True)
        sha = self.tip('refs/remotes/origin/feat/x')
        self.push(f'--force-with-lease=feat/x:{sha} origin feat/x')
        verdict = self.api('no_journal_verifier')(*calls[0])
        self.assertFalse(verdict.verified)
        self.assertIn('journal', verdict.failure)

    def test_lease_without_an_explicit_value_is_not_verified(self) -> None:
        self.setup_push_feature()
        self.install(True)
        for arguments in ('--force-with-lease origin feat/x', '--force-with-lease=feat/x origin feat/x',
                          '--force-with-lease=feat/x:HEAD~1 origin feat/x',
                          '--force-with-lease=feat/x:0123abc origin feat/x'):
            with self.subTest(arguments=arguments):
                self.assertEqual(self.push(arguments), ('ask', LEASE, 'R18'))

    def test_every_destination_needs_its_own_lease(self) -> None:
        self.setup_push_feature()
        self.install(True)
        sha = self.tip('refs/remotes/origin/feat/x')
        self.assertEqual(self.push(f'--force-with-lease=feat/x:{sha} origin feat/x feat/y'), ('ask', LEASE, 'R18'))

    def test_force_with_a_verified_lease_still_asks(self) -> None:
        self.setup_push_feature()
        self.install(True)
        sha = self.tip('refs/remotes/origin/feat/x')
        self.assertEqual(self.push(f'-f --force-with-lease=feat/x:{sha} origin feat/x'), ('ask', FORCE, 'R17'))
        self.assertEqual(self.push(f'--force-with-lease=feat/x:{sha} origin +feat/x'), ('ask', FORCE, 'R17'))

    def test_protected_destination_with_a_verified_lease_still_asks(self) -> None:
        self.setup_push_feature()
        self.install(True)
        sha = self.tip('refs/remotes/origin/main')
        self.assertEqual(self.push(f'--force-with-lease=main:{sha} origin feat/x:main'), ('ask', PROTECTED, 'R16'))

    def test_force_if_includes_with_a_verified_lease_is_allowed(self) -> None:
        self.setup_push_feature()
        self.install(True)
        sha = self.tip('refs/remotes/origin/feat/x')
        self.assertEqual(self.push(f'--force-with-lease=feat/x:{sha} --force-if-includes origin feat/x'),
                         ('allow', None, None))

    def test_negation_resets_earlier_leases(self) -> None:
        self.setup_push_feature()
        self.install(True)
        sha = self.tip('refs/remotes/origin/feat/x')
        command = f'--force-with-lease=feat/y --no-force-with-lease --force-with-lease=feat/x:{sha} origin feat/x'
        self.assertEqual(self.push(command), ('allow', None, None))


class PushReadIsolation(PushFixture):
    """Push decisions read only local configuration and refs, through the sanitized layer."""

    def test_push_decisions_never_run_network_git_or_gh(self) -> None:
        self.setup_push_extra_pattern()
        self.set_config('remote.web.url', 'https://example.invalid/r.git')
        log = self.probe / 'calls.log'
        git = self.probe / 'bin/git'
        git.write_text('#!/bin/bash\n'
                       'printf "locks=%s prompt=%s dir=%s args=%s\\n" "${GIT_OPTIONAL_LOCKS-unset}" '
                       f'"${{GIT_TERMINAL_PROMPT-unset}}" "${{GIT_DIR-unset}}" "$*" >> {shlex.quote(str(log))}\n'
                       f'exec {shlex.quote(REAL_GIT)} "$@"\n')
        git.chmod(0o755)
        self.environ['PATH'] = f'{self.probe / "bin"}{os.pathsep}{self.environ["PATH"]}'
        self.environ['GIT_DIR'] = str(self.outside / '.git')
        for command in ('git push', 'git push origin feat/x:stable/1', 'git push web feat/x', 'git push -f',
                        'git push --force-with-lease origin feat/x', 'git push origin v1 :feat/y',
                        'git push https://example.invalid/r.git main', 'git push --repo=origin --tags'):
            with self.subTest(command=command):
                self.assertNotEqual(self.decide(self.event(command, str(self.project)))[0], 'not_applicable')
        calls = log.read_text().splitlines()
        self.assertTrue(calls, 'push decisions must read the repository')
        for call in calls:
            self.assertTrue(call.startswith('locks=0 prompt=0 dir=unset '), call)
            arguments = call.split('args=', 1)[1].split()
            for network in NETWORK_SUBCOMMANDS:
                self.assertNotIn(network, arguments, call)


CLASSES = (*CLASSES, PushTable, ProtectedRefs, LeaseVerifierInterface, PushReadIsolation)


def selected_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case_class in CLASSES:
        for name in unittest.defaultTestLoader.getTestCaseNames(case_class):
            if not SELECTED or name in SELECTED:
                suite.addTest(case_class(name))
    return suite


result = unittest.TextTestRunner(verbosity=2).run(selected_suite())
sys.exit(not result.wasSuccessful())
PY
