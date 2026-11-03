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


CLASSES = (CoreSurface, DecisionCombination, OptionParsing, EventValidation, DecisionTable,
           ResolutionTable, InvocationDetails, GitReadIsolation, SlowGitRead, FailClosedTable,
           DecidedTable)


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
