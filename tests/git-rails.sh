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

# Loading the core must not leave a bytecode cache next to the source.
sys.dont_write_bytecode = True

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
        result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', probe, str(CORE_PATH)],
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


# git resolves a short ref name that starts with heads/ or tags/ through refs/<name>, so
# such a source or destination is the branch or tag it names (git 2.53, local bare remote).
PARTIAL_REF_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('partial_branch_destination_onto_main_needs_owner_approval', 'git push origin feat/x:heads/main',
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('partial_branch_source_alone_for_main_needs_owner_approval', 'git push origin heads/main',
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('partial_tag_source_alone_needs_owner_approval', 'git push origin tags/v1',
                 'ask', BULK, 'R14', setup='push-feature'),
    DecisionCase('partial_tag_destination_needs_owner_approval', 'git push origin feat/x:tags/v1',
                 'ask', BULK, 'R14', setup='push-feature'),
    DecisionCase('head_onto_partial_main_needs_owner_approval', 'git push origin HEAD:heads/main',
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('upstream_source_onto_partial_main_needs_owner_approval', "git push origin '@{u}:heads/main'",
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('partial_source_onto_partial_main_needs_owner_approval', 'git push origin heads/feat/x:heads/main',
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('full_source_onto_partial_release_needs_owner_approval',
                 'git push origin refs/heads/feat/x:heads/release/1.2', 'ask', PROTECTED, 'R16', setup='push-feature'),
    # Neighbours that name no protected branch and no tag, and forms already decided.
    DecisionCase('partial_branch_destination_onto_a_feature_is_allowed', 'git push origin feat/x:heads/feat/y',
                 'allow', setup='push-feature'),
    DecisionCase('full_branch_destination_onto_a_feature_is_allowed', 'git push origin feat/x:refs/heads/feat/y',
                 'allow', setup='push-feature'),
    DecisionCase('partial_branch_source_alone_for_a_feature_is_allowed', 'git push origin heads/feat/x',
                 'allow', setup='push-feature'),
    DecisionCase('capitalised_heads_prefix_is_an_ordinary_branch_name', 'git push origin feat/x:Heads/main',
                 'allow', setup='push-feature'),
    DecisionCase('full_ref_outside_heads_and_tags_is_allowed', 'git push origin feat/x:refs/main',
                 'allow', setup='push-feature'),
    DecisionCase('remote_tracking_source_alone_is_allowed', 'git push origin remotes/origin/main',
                 'allow', setup='push-feature'),
    DecisionCase('remote_tracking_short_destination_is_allowed', 'git push origin feat/x:remotes/origin/main',
                 'allow', setup='push-feature'),
    DecisionCase('remote_tracking_source_onto_main_needs_owner_approval', 'git push origin remotes/origin/main:main',
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('upstream_source_onto_main_needs_owner_approval', "git push origin '@{u}:main'",
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('partial_deletion_needs_owner_approval', 'git push origin :heads/feat/y',
                 'ask', DELETE, 'R15', setup='push-feature'),
)

for partial_case in PARTIAL_REF_CASES:
    setattr(PushTable, 'test_' + partial_case.name, decision_test(partial_case))


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
        self.assertIs(self.api('LEASE_VERIFIER'), self.api('journal_lease_verifier'))

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


RESET_HARD = 'reset-hard'
CLEAN = 'clean'
BRANCH_DELETE = 'branch-delete'
REWRITE = 'protected-ref-rewrite'
OUTSIDE_RESTACK = 'rebase-outside-restack'
INTO_PROTECTED = 'merge-into-protected'
PR_MERGE = 'pr-merge'
UNSUPPORTED = 'unsupported-form'
OTHER_SHA = 'fedcba9876543210fedcba9876543210fedcba98'


class OperationFixture(PushFixture):
    """Repository states read by the destructive, ref-rewrite, rebase and merge rules: the
    current branch, protected names, symbolic branch refs and rebases stopped on a conflict."""

    def git_may_fail(self, *arguments: str) -> None:
        subprocess.run([REAL_GIT, *arguments], cwd=self.project, env={**self.git_environ, 'GIT_EDITOR': 'true'},
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def setup_conflicting_feature(self) -> None:
        self.git(self.project, 'switch', '-q', '-c', 'feat/a')
        (self.project / 'a.txt').write_text('feature\n')
        self.git(self.project, 'commit', '-q', '-am', 'Change a on the feature')
        self.git(self.project, 'switch', '-q', 'main')
        (self.project / 'a.txt').write_text('main\n')
        self.git(self.project, 'commit', '-q', '-am', 'Change a on main')
        self.git(self.project, 'switch', '-q', 'feat/a')

    def setup_rebase_merge_in_progress(self) -> None:
        self.setup_conflicting_feature()
        self.git_may_fail('rebase', 'main')
        self.assertTrue((self.project / '.git/rebase-merge/head-name').is_file(), 'fixture rebase must stop')

    def setup_rebase_apply_in_progress(self) -> None:
        self.setup_conflicting_feature()
        self.git_may_fail('rebase', '--apply', 'main')
        self.assertTrue((self.project / '.git/rebase-apply/head-name').is_file(), 'fixture rebase must stop')

    def setup_symbolic_alias(self) -> None:
        self.setup_push()
        self.git(self.project, 'symbolic-ref', 'refs/heads/alias', 'refs/heads/main')

    def setup_on_master(self) -> None:
        self.setup_push()
        self.git(self.project, 'switch', '-q', '-c', 'master')

    def setup_on_release(self) -> None:
        self.setup_push()
        self.git(self.project, 'switch', '-q', '-c', 'release/1.2')

    def setup_on_configured_pattern(self) -> None:
        self.setup_push_extra_pattern()
        self.git(self.project, 'switch', '-q', '-c', 'stable/a')

    def setup_on_remote_default(self) -> None:
        self.setup_push_develop_head()
        self.git(self.project, 'switch', '-q', 'develop')

    def setup_on_trunk_without_origin(self) -> None:
        self.setup_push_without_origin()
        self.git(self.project, 'switch', '-q', 'trunk')


# git reset, clean, branch, update-ref, checkout, switch, rebase, merge, pull, gh pr merge
# and gh api: owner-authorizable operations, their allowed neighbours and read-only forms.
OPERATION_CASES: tuple[DecisionCase, ...] = (
    # R20 reset --hard; the last mode option wins, as in git.
    DecisionCase('reset_hard_needs_owner_approval', 'git reset --hard', 'ask', RESET_HARD, 'R20'),
    DecisionCase('reset_hard_to_a_commit_needs_owner_approval', 'git reset -q --hard HEAD~0',
                 'ask', RESET_HARD, 'R20'),
    DecisionCase('reset_hard_prefix_needs_owner_approval', 'git reset --har', 'ask', RESET_HARD, 'R20'),
    DecisionCase('reset_hard_after_soft_needs_owner_approval', 'git reset --soft --hard', 'ask', RESET_HARD, 'R20'),
    DecisionCase('reset_hard_from_a_subdirectory_needs_owner_approval', 'git -C sub reset --hard',
                 'ask', RESET_HARD, 'R20'),
    DecisionCase('reset_soft_is_allowed', 'git reset --soft HEAD~0', 'allow'),
    DecisionCase('reset_soft_after_hard_is_allowed', 'git reset --hard --soft', 'allow'),
    DecisionCase('reset_mixed_is_allowed', 'git reset', 'allow'),
    DecisionCase('reset_of_a_path_is_allowed', 'git reset -- a.txt', 'allow'),
    DecisionCase('reset_keep_is_allowed', 'git reset --keep HEAD~0', 'allow'),
    DecisionCase('reset_with_unknown_option_is_unsupported', 'git reset --bogus', 'deny', UNSUPPORTED),
    # R21 clean without a dry run; interactive cleaning cannot be checked.
    DecisionCase('clean_force_directories_needs_owner_approval', 'git clean -fd', 'ask', CLEAN, 'R21'),
    DecisionCase('clean_without_options_needs_owner_approval', 'git clean', 'ask', CLEAN, 'R21'),
    DecisionCase('clean_of_ignored_files_needs_owner_approval', 'git clean -fdx -e keep -- sub',
                 'ask', CLEAN, 'R21'),
    DecisionCase('clean_dry_run_negated_needs_owner_approval', 'git clean -n --no-dry-run -f', 'ask', CLEAN, 'R21'),
    DecisionCase('clean_dry_run_is_allowed', 'git clean -n', 'allow'),
    DecisionCase('clean_dry_run_bundled_first_is_allowed', 'git clean -nfd', 'allow'),
    DecisionCase('clean_dry_run_bundled_last_is_allowed', 'git clean -fdn', 'allow'),
    DecisionCase('clean_long_dry_run_is_allowed', 'git clean --dry-run -fdx', 'allow'),
    DecisionCase('clean_dry_run_prefix_is_allowed', 'git clean --dry -fd', 'allow'),
    DecisionCase('clean_interactive_is_unsupported', 'git clean -i', 'deny', UNSUPPORTED, 'R21'),
    DecisionCase('clean_interactive_bundled_is_unsupported', 'git clean -fdi', 'deny', UNSUPPORTED, 'R21'),
    DecisionCase('clean_interactive_with_dry_run_is_unsupported', 'git clean --interactive -n',
                 'deny', UNSUPPORTED, 'R21'),
    DecisionCase('clean_with_unknown_option_is_unsupported', 'git clean -fz', 'deny', UNSUPPORTED),
    # R22 branch deletion, local or remote-tracking.
    DecisionCase('branch_delete_needs_owner_approval', 'git branch -d feat/x', 'ask', BRANCH_DELETE, 'R22',
                 setup='push'),
    DecisionCase('branch_force_delete_needs_owner_approval', 'git branch -D feat/x', 'ask', BRANCH_DELETE, 'R22',
                 setup='push'),
    DecisionCase('remote_tracking_branch_delete_needs_owner_approval', 'git branch --delete -r origin/x',
                 'ask', BRANCH_DELETE, 'R22', setup='push'),
    DecisionCase('bundled_remote_branch_delete_needs_owner_approval', 'git branch -dr origin/feat/x',
                 'ask', BRANCH_DELETE, 'R22', setup='push'),
    DecisionCase('branch_delete_prefix_needs_owner_approval', 'git branch --del feat/x feat/y',
                 'ask', BRANCH_DELETE, 'R22', setup='push'),
    DecisionCase('branch_delete_with_force_needs_owner_approval', 'git branch -vdf feat/x',
                 'ask', BRANCH_DELETE, 'R22', setup='push'),
    DecisionCase('branch_delete_of_main_needs_owner_approval', 'git -C sub branch -D main',
                 'ask', BRANCH_DELETE, 'R22', setup='push-feature'),
    # R23 update-ref deletion of a branch, through a symbolic ref too; --stdin cannot be checked.
    DecisionCase('update_ref_delete_of_a_branch_needs_owner_approval', 'git update-ref -d refs/heads/x',
                 'ask', BRANCH_DELETE, 'R23'),
    DecisionCase('update_ref_delete_with_old_value_needs_owner_approval',
                 f'git update-ref -m drop -d refs/heads/feat/x {LEASE_SHA}', 'ask', BRANCH_DELETE, 'R23',
                 setup='push'),
    DecisionCase('update_ref_delete_of_head_deletes_the_current_branch', 'git update-ref -d HEAD',
                 'ask', BRANCH_DELETE, 'R23'),
    DecisionCase('update_ref_delete_through_a_symbolic_branch_needs_owner_approval',
                 'git update-ref -d refs/heads/alias', 'ask', BRANCH_DELETE, 'R23', setup='symbolic-alias'),
    DecisionCase('update_ref_delete_without_deref_needs_owner_approval',
                 'git update-ref --no-deref -d refs/heads/feat/x', 'ask', BRANCH_DELETE, 'R23', setup='push'),
    DecisionCase('update_ref_delete_of_a_tag_is_allowed', 'git update-ref -d refs/tags/v1', 'allow', setup='push'),
    DecisionCase('update_ref_delete_of_a_remote_tracking_ref_is_allowed',
                 'git update-ref -d refs/remotes/origin/feat/x', 'allow', setup='push'),
    DecisionCase('update_ref_stdin_is_unsupported',
                 "git update-ref --stdin <<'EOF'\ndelete refs/heads/feat/x\nEOF", 'deny', UNSUPPORTED, 'R23',
                 setup='push'),
    DecisionCase('update_ref_nul_stdin_is_unsupported', 'git update-ref -z --stdin < /dev/null',
                 'deny', UNSUPPORTED, 'R23', setup='push'),
    DecisionCase('update_ref_with_unknown_option_is_unsupported', 'git update-ref --bogus refs/heads/x HEAD',
                 'deny', UNSUPPORTED),
    # R24 rewriting a protected branch: forced creation, move, copy and update-ref.
    DecisionCase('branch_force_onto_main_needs_owner_approval', 'git branch -f main', 'ask', REWRITE, 'R24',
                 setup='push-feature'),
    DecisionCase('branch_force_onto_main_with_start_needs_owner_approval', 'git branch --force main feat/x',
                 'ask', REWRITE, 'R24', setup='push-feature'),
    DecisionCase('branch_force_onto_master_needs_owner_approval', 'git branch -f master', 'ask', REWRITE, 'R24',
                 setup='push-feature'),
    DecisionCase('branch_force_onto_release_needs_owner_approval', 'git branch -f release/1.2',
                 'ask', REWRITE, 'R24', setup='push-feature'),
    DecisionCase('branch_force_onto_configured_pattern_needs_owner_approval', 'git branch -f stable/a',
                 'ask', REWRITE, 'R24', setup='push-extra-pattern'),
    DecisionCase('branch_force_onto_remote_default_needs_owner_approval', 'git branch -f develop',
                 'ask', REWRITE, 'R24', setup='push-develop-head'),
    DecisionCase('branch_force_onto_main_without_origin_needs_owner_approval', 'git branch -f main',
                 'ask', REWRITE, 'R24', setup='push-without-origin'),
    DecisionCase('branch_move_of_main_needs_owner_approval', 'git branch -m main old-main', 'ask', REWRITE, 'R24',
                 setup='push-feature'),
    DecisionCase('branch_move_onto_main_needs_owner_approval', 'git branch -m feat/x main', 'ask', REWRITE, 'R24',
                 setup='push-feature'),
    DecisionCase('branch_forced_move_onto_main_needs_owner_approval', 'git branch -M feat/x main',
                 'ask', REWRITE, 'R24', setup='push-feature'),
    DecisionCase('branch_move_of_current_main_needs_owner_approval', 'git branch -m old-main',
                 'ask', REWRITE, 'R24', setup='push'),
    DecisionCase('branch_copy_of_main_needs_owner_approval', 'git branch -c main backup', 'ask', REWRITE, 'R24',
                 setup='push-feature'),
    DecisionCase('branch_forced_copy_onto_master_needs_owner_approval', 'git branch -C feat/x master',
                 'ask', REWRITE, 'R24', setup='push-feature'),
    DecisionCase('branch_copy_of_current_main_needs_owner_approval', 'git branch --copy backup',
                 'ask', REWRITE, 'R24', setup='push'),
    DecisionCase('branch_ambiguous_prefix_counts_as_copy', 'git branch --c feat/x main', 'ask', REWRITE, 'R24',
                 setup='push-feature'),
    DecisionCase('branch_force_with_previous_branch_shorthand_is_unsupported', 'git branch -f @{-1}',
                 'deny', UNSUPPORTED, 'R24', setup='push-feature'),
    DecisionCase('checkout_force_create_main_needs_owner_approval', 'git checkout -B main', 'ask', REWRITE, 'R24',
                 setup='push-feature'),
    DecisionCase('checkout_bundled_force_create_main_needs_owner_approval', 'git checkout -fBmain feat/x',
                 'ask', REWRITE, 'R24', setup='push-feature'),
    DecisionCase('switch_force_create_main_needs_owner_approval', 'git switch -C main', 'ask', REWRITE, 'R24',
                 setup='push-feature'),
    DecisionCase('switch_long_force_create_main_needs_owner_approval', 'git switch --force-create main',
                 'ask', REWRITE, 'R24', setup='push-feature'),
    DecisionCase('switch_attached_force_create_main_needs_owner_approval', 'git switch --force-create=main feat/x',
                 'ask', REWRITE, 'R24', setup='push-feature'),
    DecisionCase('switch_ambiguous_force_prefix_counts_as_force_create', 'git switch --f main',
                 'ask', REWRITE, 'R24', setup='push-feature'),
    DecisionCase('update_ref_of_main_needs_owner_approval', 'git update-ref refs/heads/main HEAD',
                 'ask', REWRITE, 'R24'),
    DecisionCase('update_ref_of_release_needs_owner_approval',
                 f'git update-ref -m move refs/heads/release/9 {LEASE_SHA}', 'ask', REWRITE, 'R24'),
    DecisionCase('update_ref_of_head_on_main_needs_owner_approval', f'git update-ref HEAD {LEASE_SHA}',
                 'ask', REWRITE, 'R24'),
    DecisionCase('update_ref_through_a_symbolic_branch_onto_main_needs_owner_approval',
                 'git update-ref refs/heads/alias HEAD', 'ask', REWRITE, 'R24', setup='symbolic-alias'),
    DecisionCase('branch_force_onto_a_feature_is_allowed', 'git branch -f feat/y', 'allow', setup='push-feature'),
    DecisionCase('branch_force_from_main_onto_a_feature_is_allowed', 'git branch -f feat/y main', 'allow',
                 setup='push-feature'),
    DecisionCase('branch_move_between_features_is_allowed', 'git branch -m feat/y feat/z', 'allow',
                 setup='push-feature'),
    DecisionCase('branch_move_of_current_feature_is_allowed', 'git branch -m feat/z', 'allow', setup='push-feature'),
    DecisionCase('branch_move_while_detached_is_allowed', 'git branch -m feat/z', 'allow', setup='push-detached'),
    DecisionCase('branch_copy_between_features_is_allowed', 'git branch -c feat/x feat/w', 'allow',
                 setup='push-feature'),
    DecisionCase('branch_force_onto_unprotected_develop_is_allowed', 'git branch -f develop', 'allow',
                 setup='push-feature'),
    DecisionCase('branch_force_onto_trunk_without_origin_is_allowed', 'git branch -f trunk', 'allow',
                 setup='push-without-origin'),
    DecisionCase('branch_creation_without_force_is_allowed', 'git branch feat/new main', 'allow',
                 setup='push-feature'),
    DecisionCase('checkout_force_create_feature_from_main_is_allowed', 'git checkout -B feat/x main', 'allow',
                 setup='push-feature'),
    DecisionCase('checkout_create_is_allowed', 'git checkout -b feat/new', 'allow', setup='push-feature'),
    DecisionCase('checkout_of_main_is_allowed', 'git checkout main', 'allow', setup='push-feature'),
    DecisionCase('checkout_of_a_path_is_allowed', 'git checkout -- a.txt', 'allow', setup='push-feature'),
    DecisionCase('switch_force_create_feature_is_allowed', 'git switch -C feat/x main', 'allow',
                 setup='push-feature'),
    DecisionCase('switch_create_is_allowed', 'git switch -c feat/new', 'allow', setup='push-feature'),
    DecisionCase('switch_to_main_is_allowed', 'git switch main', 'allow', setup='push-feature'),
    DecisionCase('update_ref_of_a_feature_is_allowed', 'git update-ref refs/heads/feat/x HEAD', 'allow',
                 setup='push'),
    DecisionCase('update_ref_of_a_tag_is_allowed', 'git update-ref refs/tags/v2 HEAD', 'allow', setup='push'),
    DecisionCase('update_ref_of_a_remote_tracking_ref_is_allowed', 'git update-ref refs/remotes/origin/main HEAD',
                 'allow', setup='push'),
    DecisionCase('update_ref_without_deref_of_head_is_allowed', f'git update-ref --no-deref HEAD {LEASE_SHA}',
                 'allow'),
    DecisionCase('update_ref_without_deref_of_a_symbolic_branch_is_allowed',
                 'git update-ref --no-deref refs/heads/alias HEAD', 'allow', setup='symbolic-alias'),
    DecisionCase('branch_with_unknown_option_is_unsupported', 'git branch --bogus', 'deny', UNSUPPORTED),
    DecisionCase('checkout_with_unknown_option_is_unsupported', 'git checkout --bogus main', 'deny', UNSUPPORTED),
    DecisionCase('switch_with_unknown_option_is_unsupported', 'git switch --bogus main', 'deny', UNSUPPORTED),
    # Read-only and listing forms of governed subcommands.
    DecisionCase('branch_listing_is_allowed', 'git branch', 'allow'),
    DecisionCase('branch_list_pattern_is_allowed', "git branch --list 'feat/*'", 'allow'),
    DecisionCase('branch_all_verbose_listing_is_allowed', 'git branch -avv', 'allow'),
    DecisionCase('branch_remote_listing_is_allowed', 'git branch -r', 'allow'),
    DecisionCase('branch_show_current_is_allowed', 'git branch --show-current', 'allow'),
    DecisionCase('branch_merged_as_last_word_is_allowed', 'git branch --merged', 'allow'),
    DecisionCase('branch_merged_with_commit_is_allowed', 'git branch --merged main -v', 'allow'),
    DecisionCase('branch_no_merged_is_allowed', 'git branch --no-merged', 'allow'),
    DecisionCase('branch_contains_is_allowed', 'git branch --contains HEAD', 'allow'),
    DecisionCase('branch_format_and_sort_is_allowed',
                 "git branch --format='%(refname:short)' --sort=-committerdate --points-at HEAD", 'allow'),
    DecisionCase('rebase_show_current_patch_is_allowed', 'git rebase --show-current-patch', 'allow'),
    DecisionCase('read_only_subcommands_stay_not_applicable',
                 'git status; git log -1; git show HEAD; git diff; git rev-parse HEAD; git ls-files', 'not_applicable'),
    # R25 abort and R26 replay outside a verified restack.
    DecisionCase('rebase_onto_main_needs_owner_approval', 'git rebase main', 'ask', OUTSIDE_RESTACK, 'R26'),
    DecisionCase('rebase_of_a_feature_needs_owner_approval', 'git rebase main', 'ask', OUTSIDE_RESTACK, 'R26',
                 setup='push-feature'),
    DecisionCase('rebase_exact_replay_form_without_journal_needs_owner_approval',
                 f'git rebase --onto {LEASE_SHA} {OTHER_SHA} feat/x', 'ask', OUTSIDE_RESTACK, 'R26',
                 setup='push-feature'),
    DecisionCase('interactive_rebase_needs_owner_approval', 'git rebase -i HEAD~0', 'ask', OUTSIDE_RESTACK, 'R26'),
    DecisionCase('rebase_continue_without_rebase_needs_owner_approval', 'git rebase --continue',
                 'ask', OUTSIDE_RESTACK, 'R26'),
    DecisionCase('rebase_continue_during_rebase_needs_owner_approval', 'git rebase --continue',
                 'ask', OUTSIDE_RESTACK, 'R26', setup='rebase-merge-in-progress'),
    DecisionCase('rebase_skip_during_rebase_needs_owner_approval', 'git rebase --skip',
                 'ask', OUTSIDE_RESTACK, 'R26', setup='rebase-apply-in-progress'),
    DecisionCase('rebase_quit_needs_owner_approval', 'git rebase --quit', 'ask', OUTSIDE_RESTACK, 'R26',
                 setup='rebase-merge-in-progress'),
    DecisionCase('rebase_edit_todo_needs_owner_approval', 'git rebase --edit-todo', 'ask', OUTSIDE_RESTACK, 'R26',
                 setup='rebase-merge-in-progress'),
    DecisionCase('rebase_ambiguous_prefix_counts_every_candidate', 'git rebase --a', 'ask', OUTSIDE_RESTACK, 'R26'),
    DecisionCase('rebase_with_exec_needs_owner_approval', "git rebase --exec 'true' main",
                 'ask', OUTSIDE_RESTACK, 'R26'),
    DecisionCase('rebase_abort_is_allowed', 'git rebase --abort', 'allow'),
    DecisionCase('rebase_abort_during_rebase_is_allowed', 'git rebase --abort', 'allow',
                 setup='rebase-merge-in-progress'),
    DecisionCase('rebase_abort_prefix_is_allowed', 'git rebase --ab', 'allow', setup='rebase-apply-in-progress'),
    DecisionCase('rebase_with_unknown_option_is_unsupported', 'git rebase --bogus main', 'deny', UNSUPPORTED),
    # R27 merge into a protected current branch.
    DecisionCase('merge_on_main_needs_owner_approval', 'git merge feat/x', 'ask', INTO_PROTECTED, 'R27',
                 setup='push'),
    DecisionCase('merge_continue_on_main_needs_owner_approval', 'git merge --continue', 'ask', INTO_PROTECTED, 'R27',
                 setup='push'),
    DecisionCase('merge_quit_on_main_needs_owner_approval', 'git merge --quit', 'ask', INTO_PROTECTED, 'R27',
                 setup='push'),
    DecisionCase('fast_forward_merge_on_main_needs_owner_approval', 'git merge --ff-only feat/x',
                 'ask', INTO_PROTECTED, 'R27', setup='push'),
    DecisionCase('squash_merge_on_main_needs_owner_approval', 'git merge --squash feat/x',
                 'ask', INTO_PROTECTED, 'R27', setup='push'),
    DecisionCase('merge_from_a_subdirectory_on_main_needs_owner_approval', 'git -C sub merge feat/x',
                 'ask', INTO_PROTECTED, 'R27', setup='push'),
    DecisionCase('merge_on_master_needs_owner_approval', 'git merge feat/x', 'ask', INTO_PROTECTED, 'R27',
                 setup='on-master'),
    DecisionCase('merge_on_release_needs_owner_approval', 'git merge feat/x', 'ask', INTO_PROTECTED, 'R27',
                 setup='on-release'),
    DecisionCase('merge_on_configured_pattern_needs_owner_approval', 'git merge feat/x', 'ask', INTO_PROTECTED,
                 'R27', setup='on-configured-pattern'),
    DecisionCase('merge_on_remote_default_needs_owner_approval', 'git merge feat/x', 'ask', INTO_PROTECTED, 'R27',
                 setup='on-remote-default'),
    DecisionCase('merge_ambiguous_prefix_counts_every_candidate', 'git merge --a', 'ask', INTO_PROTECTED, 'R27',
                 setup='push'),
    DecisionCase('merge_on_a_feature_is_allowed', 'git merge main', 'allow', setup='push-feature'),
    DecisionCase('merge_abort_on_main_is_allowed', 'git merge --abort', 'allow', setup='push'),
    DecisionCase('merge_while_detached_is_allowed', 'git merge feat/x', 'allow', setup='push-detached'),
    DecisionCase('merge_on_trunk_without_origin_is_allowed', 'git merge feat/x', 'allow',
                 setup='on-trunk-without-origin'),
    DecisionCase('merge_with_unknown_option_is_unsupported', 'git merge --bogus feat/x', 'deny', UNSUPPORTED,
                 setup='push'),
    # R28 pull into a protected current branch unless it can only fast-forward from the upstream.
    DecisionCase('pull_on_main_needs_owner_approval', 'git pull', 'ask', INTO_PROTECTED, 'R28'),
    DecisionCase('pull_rebase_on_main_needs_owner_approval', 'git pull --rebase', 'ask', INTO_PROTECTED, 'R28',
                 setup='push'),
    DecisionCase('pull_fast_forward_only_with_operands_needs_owner_approval', 'git pull --ff-only origin main',
                 'ask', INTO_PROTECTED, 'R28', setup='push'),
    DecisionCase('pull_fast_forward_only_with_repository_needs_owner_approval', 'git pull --ff-only origin',
                 'ask', INTO_PROTECTED, 'R28', setup='push'),
    DecisionCase('pull_fast_forward_only_overridden_needs_owner_approval', 'git pull --ff-only --no-ff',
                 'ask', INTO_PROTECTED, 'R28', setup='push'),
    DecisionCase('pull_ff_on_main_needs_owner_approval', 'git pull --ff', 'ask', INTO_PROTECTED, 'R28',
                 setup='push'),
    DecisionCase('pull_ambiguous_prefix_counts_every_candidate', 'git pull --f', 'ask', INTO_PROTECTED, 'R28',
                 setup='push'),
    DecisionCase('pull_on_remote_default_needs_owner_approval', 'git pull', 'ask', INTO_PROTECTED, 'R28',
                 setup='on-remote-default'),
    DecisionCase('pull_fast_forward_only_on_main_is_allowed', 'git pull --ff-only', 'allow', setup='push'),
    DecisionCase('pull_fast_forward_only_last_is_allowed', 'git pull --no-ff --ff-only', 'allow', setup='push'),
    DecisionCase('pull_fast_forward_only_prefix_is_allowed', 'git pull -q --ff-', 'allow', setup='push'),
    DecisionCase('pull_on_a_feature_is_allowed', 'git pull', 'allow', setup='push-feature'),
    DecisionCase('pull_of_main_into_a_feature_is_allowed', 'git pull origin main', 'allow', setup='push-feature'),
    DecisionCase('pull_while_detached_is_allowed', 'git pull', 'allow', setup='push-detached'),
    DecisionCase('pull_with_unknown_option_is_unsupported', 'git pull --bogus', 'deny', UNSUPPORTED, setup='push'),
    # R29 gh pr merge and R30 gh api merge endpoints; gh is parsed, never run.
    DecisionCase('gh_pr_merge_needs_owner_approval', 'gh pr merge 1', 'ask', PR_MERGE, 'R29'),
    DecisionCase('gh_pr_merge_without_number_needs_owner_approval', 'gh pr merge', 'ask', PR_MERGE, 'R29'),
    DecisionCase('gh_pr_merge_with_options_needs_owner_approval', 'gh pr merge 1 --squash --delete-branch',
                 'ask', PR_MERGE, 'R29'),
    DecisionCase('gh_pr_merge_with_repository_flag_needs_owner_approval', 'gh -R o/r pr merge 5',
                 'ask', PR_MERGE, 'R29'),
    DecisionCase('gh_api_put_pull_merge_needs_owner_approval', 'gh api -X PUT repos/o/r/pulls/1/merge',
                 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_method_flag_pull_merge_needs_owner_approval', 'gh api --method PUT repos/o/r/pulls/1/merge',
                 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_attached_method_pull_merge_needs_owner_approval', 'gh api -XPUT repos/o/r/pulls/1/merge',
                 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_method_equals_pull_merge_needs_owner_approval',
                 'gh api --method=PUT /repos/o/r/pulls/12/merge', 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_method_after_endpoint_needs_owner_approval', 'gh api repos/o/r/pulls/1/merge -X PUT',
                 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_merge_endpoint_with_fields_needs_owner_approval',
                 'gh api -i repos/o/r/pulls/1/merge -f merge_method=squash -H Accept:x', 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_merge_endpoint_with_query_needs_owner_approval',
                 "gh api -X PUT 'repos/o/r/pulls/1/merge?merge_method=squash'", 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_merge_endpoint_as_url_needs_owner_approval',
                 'gh api -X PUT https://api.github.com/repos/o/r/pulls/1/merge', 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_merge_endpoint_with_placeholders_needs_owner_approval',
                 "gh api -X PUT 'repos/{owner}/{repo}/pulls/3/merge'", 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_merge_endpoint_in_other_case_needs_owner_approval', 'gh api -X PUT repos/o/r/PULLS/1/MERGE',
                 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_merge_endpoint_after_double_dash_needs_owner_approval',
                 'gh api -X PUT -- repos/o/r/pulls/1/merge', 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_branch_merges_endpoint_needs_owner_approval',
                 'gh api repos/o/r/merges -f base=main -f head=feat/x', 'ask', PR_MERGE, 'R30'),
    DecisionCase('gh_api_with_unknown_flag_is_unsupported', 'gh api --bogus repos/o/r/pulls/1/merge',
                 'deny', UNSUPPORTED),
    DecisionCase('gh_api_with_dynamic_endpoint_is_unsupported', 'gh api -X PUT "repos/o/r/pulls/$N/merge"',
                 'deny', UNSUPPORTED),
    DecisionCase('gh_api_pull_request_read_is_allowed', 'gh api repos/o/r/pulls/1', 'allow'),
    DecisionCase('gh_api_pull_request_list_is_allowed', "gh api --paginate repos/o/r/pulls -q '.[].number'", 'allow'),
    DecisionCase('gh_api_merge_word_as_flag_value_is_allowed', 'gh api repos/o/r/issues -f title=/pulls/1/merge',
                 'allow'),
    DecisionCase('gh_pr_create_is_not_applicable', 'gh pr create --fill', 'not_applicable'),
    DecisionCase('gh_pr_view_is_not_applicable', 'gh pr view 1', 'not_applicable'),
)

# A missing remote default branch with origin present leaves the local protected set unknown.
OPERATION_DEFAULT_UNKNOWN_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('merge_without_origin_default_is_default_branch_unknown', 'git merge main',
                 'deny', DEFAULT_UNKNOWN, 'R27', setup='push-no-default-head'),
    DecisionCase('pull_without_origin_default_is_default_branch_unknown', 'git pull',
                 'deny', DEFAULT_UNKNOWN, 'R28', setup='push-no-default-head'),
    DecisionCase('branch_force_without_origin_default_is_default_branch_unknown', 'git branch -f feat/y',
                 'deny', DEFAULT_UNKNOWN, 'R24', setup='push-no-default-head'),
    DecisionCase('checkout_force_create_without_origin_default_is_default_branch_unknown', 'git checkout -B feat/y',
                 'deny', DEFAULT_UNKNOWN, 'R24', setup='push-no-default-head'),
    DecisionCase('update_ref_without_origin_default_is_default_branch_unknown', 'git update-ref refs/heads/feat/y HEAD',
                 'deny', DEFAULT_UNKNOWN, 'R24', setup='push-no-default-head'),
    DecisionCase('branch_delete_without_origin_default_still_asks', 'git branch -d feat/y',
                 'ask', BRANCH_DELETE, 'R22', setup='push-no-default-head'),
    DecisionCase('pull_fast_forward_only_without_origin_default_is_allowed', 'git pull --ff-only', 'allow',
                 setup='push-no-default-head'),
    DecisionCase('merge_abort_without_origin_default_is_allowed', 'git merge --abort', 'allow',
                 setup='push-no-default-head'),
    DecisionCase('reset_hard_without_origin_default_still_asks', 'git reset --hard',
                 'ask', RESET_HARD, 'R20', setup='push-no-default-head'),
)

# An earlier part of the same command that may write makes the current-branch, protected-set,
# symbolic-ref and rebase-state reads unverifiable; rules that read nothing keep their result.
OPERATION_STATE_CHANGE_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('merge_after_checkout_is_unsupported', 'git checkout main && git merge feat/x',
                 'deny', UNSUPPORTED, 'R27', setup='push-feature'),
    DecisionCase('pull_after_switch_is_unsupported', 'git switch main && git pull', 'deny', UNSUPPORTED, 'R28',
                 setup='push-feature'),
    DecisionCase('rename_of_current_branch_after_checkout_is_unsupported', 'git checkout main; git branch -m old',
                 'deny', UNSUPPORTED, 'R24', setup='push-feature'),
    DecisionCase('forced_branch_after_fetch_is_unsupported', 'git fetch origin && git branch -f feat/x origin/feat/x',
                 'deny', UNSUPPORTED, 'R24', setup='push-feature'),
    DecisionCase('forced_checkout_after_protection_change_is_unsupported',
                 "git config --add orchestrail.protectedBranch 'feat/*' && git checkout -B feat/x",
                 'deny', UNSUPPORTED, 'R24', setup='push-feature'),
    DecisionCase('update_ref_after_symbolic_ref_change_is_unsupported',
                 'git symbolic-ref refs/heads/alias refs/heads/main && git update-ref refs/heads/alias HEAD',
                 'deny', UNSUPPORTED, 'R24', setup='push'),
    DecisionCase('update_ref_delete_after_a_write_is_unsupported',
                 'git checkout main && git update-ref -d refs/heads/feat/x', 'deny', UNSUPPORTED, 'R23',
                 setup='push-feature'),
    DecisionCase('rebase_continue_after_a_switch_is_unsupported', 'git switch feat/x && git rebase --continue',
                 'deny', UNSUPPORTED, 'R26', setup='rebase-merge-in-progress'),
    DecisionCase('rebase_after_a_file_write_is_unsupported', 'echo x > a.txt && git rebase main',
                 'deny', UNSUPPORTED, 'R26', setup='push-feature'),
    DecisionCase('merge_in_subshell_after_a_write_is_unsupported', '(git switch -q main); git merge feat/x',
                 'deny', UNSUPPORTED, 'R27', setup='push-feature'),
    DecisionCase('reset_hard_after_checkout_still_asks', 'git checkout main && git reset --hard',
                 'ask', RESET_HARD, 'R20', setup='push-feature'),
    DecisionCase('clean_after_staging_still_asks', 'git add a.txt && git clean -fd', 'ask', CLEAN, 'R21'),
    DecisionCase('clean_dry_run_after_a_commit_is_allowed', 'git commit -m ok && git clean -n', 'allow'),
    DecisionCase('branch_delete_after_checkout_still_asks', 'git checkout main && git branch -d feat/x',
                 'ask', BRANCH_DELETE, 'R22', setup='push-feature'),
    DecisionCase('update_ref_delete_without_deref_after_a_write_still_asks',
                 'git checkout main && git update-ref --no-deref -d refs/heads/feat/x', 'ask', BRANCH_DELETE, 'R23',
                 setup='push-feature'),
    DecisionCase('merge_abort_after_staging_is_allowed', 'git add a.txt && git merge --abort', 'allow', setup='push'),
    DecisionCase('pull_fast_forward_only_after_switch_is_allowed', 'git switch main && git pull --ff-only', 'allow',
                 setup='push-feature'),
    DecisionCase('rebase_abort_after_checkout_is_allowed', 'git checkout main && git rebase --abort', 'allow',
                 setup='push-feature'),
    DecisionCase('pr_merge_after_checkout_still_asks', 'git checkout main && gh pr merge 1', 'ask', PR_MERGE, 'R29',
                 setup='push-feature'),
    DecisionCase('api_merge_after_checkout_still_asks', 'git checkout main && gh api -X PUT repos/o/r/pulls/1/merge',
                 'ask', PR_MERGE, 'R30', setup='push-feature'),
    DecisionCase('merge_after_read_only_git_still_asks', 'git status && git merge feat/x',
                 'ask', INTO_PROTECTED, 'R27', setup='push'),
    DecisionCase('merge_after_cd_still_asks', 'cd sub && git merge feat/x', 'ask', INTO_PROTECTED, 'R27',
                 setup='push'),
    DecisionCase('write_after_the_merge_does_not_change_it', 'git merge main && echo x > a.txt', 'allow',
                 setup='push-feature'),
)


class OperationTable(OperationFixture):
    """Table-driven decisions of the destructive, ref-rewrite, rebase and merge rules."""


for operation_case in (*OPERATION_CASES, *OPERATION_DEFAULT_UNKNOWN_CASES, *OPERATION_STATE_CHANGE_CASES):
    setattr(OperationTable, 'test_' + operation_case.name, decision_test(operation_case))


class DeletionVerifierInterface(OperationFixture):
    """Branch deletion hands the deleted refs to a replaceable exception verifier."""

    def install(self, exception: bool) -> list[tuple[Any, Any, Any]]:
        calls: list[tuple[Any, Any, Any]] = []
        verdict = self.api('DeletionVerdict')
        original = self.api('DELETION_VERIFIER')

        def verifier(request: Any, invocation: Any, context: Any) -> Any:
            calls.append((request, invocation, context))
            return verdict(exception, None if exception else 'fixture verifier refused')
        setattr(CORE, 'DELETION_VERIFIER', verifier)
        self.addCleanup(setattr, CORE, 'DELETION_VERIFIER', original)
        return calls

    def run_command(self, command: str) -> tuple[str, str | None, str | None]:
        return self.decide(self.event(command, str(self.project)))

    def request(self, calls: list[tuple[Any, Any, Any]]) -> tuple[Any, ...]:
        self.assertEqual(len(calls), 1)
        request = calls[0][0]
        return tuple(request.refs), tuple(request.expected), request.forced

    def test_default_verifier_is_the_no_exception_implementation(self) -> None:
        self.assertIs(self.api('DELETION_VERIFIER'), self.api('no_exception_verifier'))

    def test_branch_delete_reaches_the_verifier(self) -> None:
        self.setup_push()
        calls = self.install(True)
        self.assertEqual(self.run_command('git branch -d feat/x'), ('allow', None, None))
        self.assertEqual(self.request(calls), (('refs/heads/feat/x',), (None,), False))
        self.assertEqual(calls[0][1].common_dir, str(self.project / '.git'))

    def test_forced_branch_delete_is_marked_forced(self) -> None:
        self.setup_push()
        calls = self.install(True)
        self.run_command('git branch -D feat/x feat/y')
        self.assertEqual(self.request(calls), (('refs/heads/feat/x', 'refs/heads/feat/y'), (None, None), True))

    def test_remote_tracking_delete_names_the_remote_ref(self) -> None:
        self.setup_push()
        calls = self.install(True)
        self.run_command('git branch --delete -r origin/feat/x')
        self.assertEqual(self.request(calls), (('refs/remotes/origin/feat/x',), (None,), False))

    def test_update_ref_delete_carries_the_expected_value(self) -> None:
        self.setup_push()
        calls = self.install(True)
        self.assertEqual(self.run_command(f'git update-ref -d refs/heads/feat/x {LEASE_SHA}'), ('allow', None, None))
        self.assertEqual(self.request(calls), (('refs/heads/feat/x',), (LEASE_SHA,), False))

    def test_update_ref_delete_names_the_dereferenced_branch(self) -> None:
        self.setup_symbolic_alias()
        calls = self.install(True)
        self.run_command('git update-ref -d refs/heads/alias')
        self.assertEqual(self.request(calls), (('refs/heads/main',), (None,), False))

    def test_refused_exception_asks(self) -> None:
        self.setup_push()
        self.install(False)
        self.assertEqual(self.run_command('git branch -d feat/x'), ('ask', BRANCH_DELETE, 'R22'))
        self.assertEqual(self.run_command('git update-ref -d refs/heads/feat/x'), ('ask', BRANCH_DELETE, 'R23'))

    def test_no_exception_implementation_refuses(self) -> None:
        self.setup_push()
        calls = self.install(True)
        self.run_command('git branch -d feat/x')
        verdict = self.api('no_exception_verifier')(*calls[0])
        self.assertFalse(verdict.exception)
        self.assertTrue(verdict.failure)

    def test_forms_that_delete_no_branch_never_reach_the_verifier(self) -> None:
        self.setup_push()
        calls = self.install(True)
        for command in ('git update-ref -d refs/tags/v1', 'git branch -f feat/y', 'git branch --list',
                        "git update-ref --stdin <<'EOF'\ndelete refs/heads/feat/x\nEOF"):
            with self.subTest(command=command):
                self.run_command(command)
        self.assertEqual(calls, [])


class ReplayVerifierInterface(OperationFixture):
    """Every rebase other than abort or show-current-patch asks a replaceable replay verifier."""

    def install(self, verified: bool) -> list[tuple[Any, Any, Any]]:
        calls: list[tuple[Any, Any, Any]] = []
        verdict = self.api('ReplayVerdict')
        original = self.api('REPLAY_VERIFIER')

        def verifier(request: Any, invocation: Any, context: Any) -> Any:
            calls.append((request, invocation, context))
            return verdict(verified, None if verified else 'fixture verifier refused')
        setattr(CORE, 'REPLAY_VERIFIER', verifier)
        self.addCleanup(setattr, CORE, 'REPLAY_VERIFIER', original)
        return calls

    def tip(self, ref: str) -> str:
        return subprocess.run([REAL_GIT, 'rev-parse', ref], cwd=self.project, env=self.git_environ, check=True,
                              capture_output=True, text=True).stdout.strip()

    def rebase(self, arguments: str) -> tuple[str, str | None, str | None]:
        return self.decide(self.event('git rebase ' + arguments, str(self.project)))

    def only_request(self, calls: list[tuple[Any, Any, Any]]) -> Any:
        self.assertEqual(len(calls), 1)
        return calls[0][0]

    def test_default_verifier_is_the_no_journal_implementation(self) -> None:
        self.assertIs(self.api('REPLAY_VERIFIER'), self.api('journal_replay_verifier'))

    def test_exact_replay_form_reaches_the_verifier(self) -> None:
        self.setup_push_feature()
        calls = self.install(True)
        new, old = self.tip('main'), self.tip('feat/x')
        self.assertEqual(self.rebase(f'--onto {new} {old} feat/y'), ('allow', None, None))
        request = self.only_request(calls)
        self.assertEqual((tuple(request.arguments), request.replay, request.action),
                         (('--onto', new, old, 'feat/y'), (new, old, 'feat/y'), None))
        self.assertEqual((request.in_progress, request.rebase_head), (False, None))
        self.assertEqual(request.common_dir, str(self.project / '.git'))

    def test_other_forms_carry_no_replay(self) -> None:
        self.setup_push_feature()
        calls = self.install(True)
        new, old = self.tip('main'), self.tip('feat/x')
        for arguments in ('main', f'--onto={new} {old} feat/y', f'-q --onto {new} {old} feat/y',
                          f'--onto {new} {old}'):
            with self.subTest(arguments=arguments):
                calls.clear()
                self.rebase(arguments)
                request = self.only_request(calls)
                self.assertEqual(tuple(request.arguments), tuple(shlex.split(arguments)))
                self.assertIsNone(request.replay)

    def test_continue_reports_the_merge_backend_head_name(self) -> None:
        self.setup_rebase_merge_in_progress()
        calls = self.install(True)
        self.assertEqual(self.rebase('--continue'), ('allow', None, None))
        request = self.only_request(calls)
        self.assertEqual((request.action, request.in_progress, request.rebase_head),
                         ('continue', True, 'refs/heads/feat/a'))

    def test_skip_reports_the_apply_backend_head_name(self) -> None:
        self.setup_rebase_apply_in_progress()
        calls = self.install(True)
        self.rebase('--skip')
        request = self.only_request(calls)
        self.assertEqual((request.action, request.in_progress, request.rebase_head),
                         ('skip', True, 'refs/heads/feat/a'))

    def test_refused_verification_asks(self) -> None:
        self.setup_push_feature()
        self.install(False)
        self.assertEqual(self.rebase('main'), ('ask', OUTSIDE_RESTACK, 'R26'))

    def test_no_journal_implementation_refuses_and_names_the_check(self) -> None:
        self.setup_push_feature()
        calls = self.install(True)
        self.rebase('main')
        verdict = self.api('no_journal_replay_verifier')(*calls[0])
        self.assertFalse(verdict.verified)
        self.assertIn('journal', verdict.failure)

    def test_abort_and_show_current_patch_never_reach_the_verifier(self) -> None:
        self.setup_rebase_merge_in_progress()
        calls = self.install(False)
        for arguments in ('--abort', '--show-current-patch'):
            with self.subTest(arguments=arguments):
                self.assertEqual(self.rebase(arguments), ('allow', None, None))
        self.assertEqual(calls, [])

    def test_state_change_denies_before_the_verifier(self) -> None:
        self.setup_rebase_merge_in_progress()
        calls = self.install(True)
        decision = self.decide(self.event('git add a.txt && git rebase --continue', str(self.project)))
        self.assertEqual(decision, ('deny', UNSUPPORTED, 'R26'))
        self.assertEqual(calls, [])


class OperationReadIsolation(OperationFixture):
    """Destructive and merge decisions read only local state through the sanitized layer."""

    def test_operation_decisions_never_run_network_git_or_gh(self) -> None:
        self.setup_push_extra_pattern()
        log = self.probe / 'calls.log'
        git = self.probe / 'bin/git'
        git.write_text('#!/bin/bash\n'
                       'printf "locks=%s prompt=%s dir=%s args=%s\\n" "${GIT_OPTIONAL_LOCKS-unset}" '
                       f'"${{GIT_TERMINAL_PROMPT-unset}}" "${{GIT_DIR-unset}}" "$*" >> {shlex.quote(str(log))}\n'
                       f'exec {shlex.quote(REAL_GIT)} "$@"\n')
        git.chmod(0o755)
        gh = self.probe / 'bin/gh'
        gh.write_text(f'#!/bin/bash\nprintf "gh %s\\n" "$*" >> {shlex.quote(str(log))}\n')
        gh.chmod(0o755)
        self.environ['PATH'] = f'{self.probe / "bin"}{os.pathsep}{self.environ["PATH"]}'
        self.environ['GIT_DIR'] = str(self.outside / '.git')
        for command in ('git merge main', 'git pull', 'git pull --ff-only origin main', 'git rebase main',
                        'git rebase --continue', 'git branch -m feat/z', 'git branch -f stable/b',
                        'git update-ref -d refs/heads/feat/y', 'git checkout -B feat/y', 'git reset --hard',
                        'git clean -fd', 'gh pr merge 1', 'gh api -X PUT repos/o/r/pulls/1/merge'):
            with self.subTest(command=command):
                self.assertNotEqual(self.decide(self.event(command, str(self.project)))[0], 'not_applicable')
        calls = log.read_text().splitlines()
        self.assertFalse([call for call in calls if call.startswith('gh ')], 'the core never runs gh')
        for call in calls:
            self.assertTrue(call.startswith('locks=0 prompt=0 dir=unset '), call)
            arguments = call.split('args=', 1)[1].split()
            for network in NETWORK_SUBCOMMANDS:
                self.assertNotIn(network, arguments, call)


CLASSES = (*CLASSES, OperationTable, DeletionVerifierInterface, ReplayVerifierInterface, OperationReadIsolation)


# gh api graphql: a merge mutation is named as a field identifier of the query document, outside
# string literals and comments, in any letter case; a query read from a file or stdin cannot be checked.
GRAPHQL_MERGE_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('graphql_merge_pull_request_needs_owner_approval',
                 """gh api graphql -f query='mutation{mergePullRequest(input:{pullRequestId:"X"}){clientMutationId}}'""",
                 'ask', PR_MERGE, 'R30'),
    DecisionCase('graphql_enable_auto_merge_needs_owner_approval',
                 """gh api graphql -f query='mutation{enablePullRequestAutoMerge(input:{pullRequestId:"X"})"""
                 """{clientMutationId}}'""", 'ask', PR_MERGE, 'R30'),
    DecisionCase('graphql_merge_branch_needs_owner_approval',
                 """gh api graphql -f query='mutation{mergeBranch(input:{repositoryId:"X",base:"main",head:"x"})"""
                 """{clientMutationId}}'""", 'ask', PR_MERGE, 'R30'),
    DecisionCase('graphql_lowercase_merge_mutation_needs_owner_approval',
                 """gh api graphql -f query='mutation{mergepullrequest(input:{pullRequestId:"X"}){clientMutationId}}'""",
                 'ask', PR_MERGE, 'R30'),
    DecisionCase('graphql_query_from_a_file_is_unsupported', 'gh api graphql -F query=@q.graphql',
                 'deny', UNSUPPORTED),
    DecisionCase('graphql_body_from_a_file_is_unsupported', 'gh api graphql --input body.json',
                 'deny', UNSUPPORTED),
    DecisionCase('graphql_dynamic_query_is_unsupported', 'gh api graphql -f query="$Q"', 'deny', UNSUPPORTED),
    DecisionCase('graphql_read_query_is_allowed', "gh api graphql -f query='query{viewer{login}}'", 'allow'),
    DecisionCase('graphql_other_mutation_mentioning_merge_is_allowed',
                 """gh api graphql -f query='mutation{addComment(input:{subjectId:"X",body:"merge it"})"""
                 """{clientMutationId}}'""", 'allow'),
    DecisionCase('graphql_merge_mutation_name_inside_a_string_is_allowed',
                 """gh api graphql -f query='mutation{addComment(input:{subjectId:"X",body:"mergePullRequest"})"""
                 """{clientMutationId}}'""", 'allow'),
)

for graphql_case in GRAPHQL_MERGE_CASES:
    setattr(OperationTable, 'test_' + graphql_case.name, decision_test(graphql_case))


class SymbolicBranchFixture(OperationFixture):
    """Branch refs that are symbolic refs: forced creation writes the branch they point to."""

    def setup_symbolic_chain(self) -> None:
        self.setup_symbolic_alias()
        self.git(self.project, 'symbolic-ref', 'refs/heads/alias2', 'refs/heads/alias')

    def setup_symbolic_feature(self) -> None:
        self.setup_push()
        self.git(self.project, 'symbolic-ref', 'refs/heads/side', 'refs/heads/feat/x')


# Forced creation through a symbolic branch ref moves its target (git 2.53); move and copy
# replace the symbolic ref itself and leave the target unchanged.
SYMBOLIC_BRANCH_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('branch_force_through_symbolic_alias_needs_owner_approval', 'git branch -f alias feat/y',
                 'ask', REWRITE, 'R24', setup='symbolic-alias'),
    DecisionCase('checkout_force_create_through_symbolic_alias_needs_owner_approval', 'git checkout -B alias feat/y',
                 'ask', REWRITE, 'R24', setup='symbolic-alias'),
    DecisionCase('switch_force_create_through_symbolic_alias_needs_owner_approval', 'git switch -C alias feat/y',
                 'ask', REWRITE, 'R24', setup='symbolic-alias'),
    DecisionCase('switch_long_force_create_through_symbolic_alias_needs_owner_approval',
                 'git switch --force-create=alias feat/y', 'ask', REWRITE, 'R24', setup='symbolic-alias'),
    DecisionCase('branch_force_through_symbolic_chain_needs_owner_approval', 'git branch -f alias2 feat/y',
                 'ask', REWRITE, 'R24', setup='symbolic-chain'),
    DecisionCase('branch_force_through_symbolic_alias_after_read_only_git_needs_owner_approval',
                 'git status && git branch -f alias feat/y', 'ask', REWRITE, 'R24', setup='symbolic-alias'),
    DecisionCase('branch_force_through_symbolic_alias_after_a_write_is_unsupported',
                 'git checkout main && git branch -f alias feat/y', 'deny', UNSUPPORTED, 'R24', setup='symbolic-alias'),
    DecisionCase('branch_force_through_symbolic_feature_is_allowed', 'git branch -f side feat/y', 'allow',
                 setup='symbolic-feature'),
    DecisionCase('branch_move_of_symbolic_alias_is_allowed', 'git branch -m alias feat/z', 'allow',
                 setup='symbolic-alias'),
    DecisionCase('branch_forced_move_onto_symbolic_alias_is_allowed', 'git branch -M feat/x alias', 'allow',
                 setup='symbolic-alias'),
    DecisionCase('branch_forced_copy_onto_symbolic_alias_is_allowed', 'git branch -C feat/x alias', 'allow',
                 setup='symbolic-alias'),
)

# A merge-queue mutation merges a pull request like mergePullRequest; leaving the queue does not.
GRAPHQL_QUEUE_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('graphql_enqueue_pull_request_needs_owner_approval',
                 """gh api graphql -f query='mutation{enqueuePullRequest(input:{pullRequestId:"X"})"""
                 """{clientMutationId}}'""", 'ask', PR_MERGE, 'R30'),
    DecisionCase('graphql_lowercase_enqueue_mutation_needs_owner_approval',
                 """gh api graphql -f query='mutation{enqueuepullrequest(input:{pullRequestId:"X"})"""
                 """{clientMutationId}}'""", 'ask', PR_MERGE, 'R30'),
    DecisionCase('graphql_dequeue_pull_request_is_allowed',
                 """gh api graphql -f query='mutation{dequeuePullRequest(input:{id:"X"}){clientMutationId}}'""",
                 'allow'),
)

# Git subcommands that run another command are opaque command runners.
COMMAND_RUNNER_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('submodule_foreach_is_unsupported', "git submodule foreach 'git push -f'", 'deny', UNSUPPORTED),
    DecisionCase('quiet_recursive_submodule_foreach_is_unsupported', 'git submodule --quiet foreach --recursive true',
                 'deny', UNSUPPORTED),
    DecisionCase('submodule_foreach_from_a_subdirectory_is_unsupported', 'git -C sub submodule foreach true',
                 'deny', UNSUPPORTED),
    DecisionCase('bisect_run_is_unsupported', 'git bisect run make test', 'deny', UNSUPPORTED),
    DecisionCase('submodule_status_is_not_applicable', 'git submodule status', 'not_applicable'),
    DecisionCase('bare_submodule_is_not_applicable', 'git submodule', 'not_applicable'),
    DecisionCase('bisect_log_is_not_applicable', 'git bisect log', 'not_applicable'),
    DecisionCase('filter_branch_tree_filter_is_unsupported', "git filter-branch --tree-filter 'git push -f' HEAD",
                 'deny', UNSUPPORTED),
    DecisionCase('filter_branch_index_filter_is_unsupported', "git filter-branch --index-filter 'git push -f' HEAD",
                 'deny', UNSUPPORTED),
    DecisionCase('filter_branch_msg_filter_is_unsupported', "git filter-branch --msg-filter 'git push -f' HEAD",
                 'deny', UNSUPPORTED),
    DecisionCase('filter_branch_env_filter_is_unsupported', "git filter-branch --env-filter 'git push -f' HEAD",
                 'deny', UNSUPPORTED),
    DecisionCase('filter_branch_commit_filter_is_unsupported', "git filter-branch --commit-filter 'git push -f' HEAD",
                 'deny', UNSUPPORTED),
    DecisionCase('filter_branch_parent_filter_is_unsupported', "git filter-branch --parent-filter 'git push -f' HEAD",
                 'deny', UNSUPPORTED),
    DecisionCase('filter_branch_tag_name_filter_is_unsupported',
                 "git filter-branch --tag-name-filter 'git push -f' HEAD", 'deny', UNSUPPORTED),
    DecisionCase('filter_branch_setup_is_unsupported', "git filter-branch --setup 'git push -f' --tree-filter true HEAD",
                 'deny', UNSUPPORTED),
    DecisionCase('filter_branch_subdirectory_filter_stays_not_applicable',
                 'git filter-branch --subdirectory-filter sub HEAD', 'not_applicable'),
    DecisionCase('difftool_extcmd_is_unsupported', "git difftool -x 'cmd'", 'deny', UNSUPPORTED),
    DecisionCase('difftool_attached_long_extcmd_is_unsupported', 'git difftool --extcmd=cmd', 'deny', UNSUPPORTED),
    DecisionCase('difftool_bundled_extcmd_is_unsupported', 'git difftool -yx cmd HEAD', 'deny', UNSUPPORTED),
    DecisionCase('difftool_extcmd_prefix_is_unsupported', 'git difftool --ext cmd', 'deny', UNSUPPORTED),
    DecisionCase('difftool_tool_help_stays_not_applicable', 'git difftool --tool-help', 'not_applicable'),
    DecisionCase('difftool_of_a_commit_stays_not_applicable', 'git difftool HEAD', 'not_applicable'),
)


class SymbolicBranchTable(SymbolicBranchFixture):
    """Table-driven decisions for symbolic branch refs, merge-queue mutations and command runners."""


for repair_case in (*SYMBOLIC_BRANCH_CASES, *GRAPHQL_QUEUE_CASES, *COMMAND_RUNNER_CASES):
    setattr(SymbolicBranchTable, 'test_' + repair_case.name, decision_test(repair_case))

CLASSES = (*CLASSES, SymbolicBranchTable)


# Restack recovery journals: /restack records the stack it replays under the repository's
# common directory. Only one journal that proves every check allows the exact replay or the
# exact lease publication; anything else asks and names the check that failed.
import hashlib  # noqa: E402 - the journal block needs these only
import json  # noqa: E402

JOURNAL_DIRECTORY = 'orchestrail-restack'
JOURNAL_LIMIT = 1024 * 1024
REMOVE = '<remove>'
NO_FAILURE_FIELD = '<the decision carries no failure field>'
JournalEdit = tuple[tuple[str, ...], object]
ONTO_A = 'git rebase --onto {target} {a_base} feat/a'
PUSH_A = 'git push --force-with-lease=refs/heads/feat/a:{a_remote} origin feat/a'
SCHEMA = 'journal-invalid-schema'
FORCE_DEFAULT = 'push-force'


@dataclass(frozen=True)
class RestackCase:
    """One journal row: setup, edits of the first journal, a command with SHA placeholders,
    the expected decision, reason, rule and the failed check the result names."""
    name: str
    command: str
    decision: str
    reason: str | None = None
    rule: str | None = None
    failure: str | None = None
    edits: tuple[JournalEdit, ...] = ()
    setup: str = 'restack'
    cwd: str = 'project'
    environ: tuple[tuple[str, str], ...] = ()


def journal_name(task_path: str) -> str:
    return hashlib.sha256(task_path.encode()).hexdigest() + '.json'


class RestackFixture(OperationFixture):
    """A stack feat/a → feat/b cut from main, main advanced to the replay target, origin
    holding main and feat/a, and recovery journals written into the common directory."""
    shas: dict[str, str]
    journals: list[tuple[str, dict[str, Any]]]
    raw_journals: list[tuple[str, bytes]]
    journal_root: Path

    def setUp(self) -> None:
        super().setUp()
        self.shas = {'other': OTHER_SHA, 'long': 'ab' * 32}
        self.journals, self.raw_journals = [], []
        self.journal_root = self.project / '.git' / JOURNAL_DIRECTORY

    def location(self, key: str) -> str:
        extra = {'wt': self.project / 'wt', 'sha256': self.world / 'sha256 project'}
        return str(extra[key]) if key in extra else super().location(key)

    def tip_in(self, directory: Path, ref: str) -> str:
        return subprocess.run([REAL_GIT, 'rev-parse', ref], cwd=directory, env=self.git_environ, check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit_file(self, directory: Path, name: str, text: str) -> None:
        (directory / name).write_text(text)
        self.git(directory, 'add', '--', name)
        self.git(directory, 'commit', '-q', '-m', 'Change ' + name)

    def build_stack(self, directory: Path, conflict: bool = False, remote: bool = True) -> None:
        self.shas['a_base'] = self.tip_in(directory, 'main')
        self.git(directory, 'switch', '-q', '-c', 'feat/a')
        self.commit_file(directory, 'a.txt' if conflict else 'fa.txt', 'feature a\n')
        self.git(directory, 'switch', '-q', '-c', 'feat/b')
        self.commit_file(directory, 'fb.txt', 'feature b\n')
        self.git(directory, 'switch', '-q', 'main')
        if remote:
            self.add_remote('origin', ('main', 'feat/a'), 'main')
        self.commit_file(directory, 'a.txt' if conflict else 'm.txt', 'main advanced\n')
        shas = {'a_tip': 'feat/a', 'a_remote': 'feat/a', 'b_base': 'feat/a', 'b_tip': 'feat/b', 'target': 'main'}
        self.shas.update({key: self.tip_in(directory, ref) for key, ref in shas.items()})
        self.shas.update({'TARGET': self.shas['target'].upper(), 'target_short': self.shas['target'][:12],
                          'project_git': os.path.realpath(self.project / '.git'),
                          'outside_git': os.path.realpath(self.outside / '.git')})

    def journal(self, directory: Path, task: str) -> dict[str, Any]:
        shas = self.shas
        return {'schema_version': 1, 'repository_common_dir': os.path.realpath(directory / '.git'),
                'task_path': str(self.world / task), 'target': {'branch': 'main', 'sha': shas['target']},
                'publication_authorized': False, 'order': ['feat/a', 'feat/b'],
                'branches': {'feat/a': {'original_base_commit': shas['a_base'], 'original_tip': shas['a_tip'],
                                        'replayed_tip': None, 'expected_remote_tip': shas['a_remote']},
                             'feat/b': {'original_base_commit': shas['b_base'], 'original_tip': shas['b_tip'],
                                        'replayed_tip': None, 'expected_remote_tip': 'absent'}}}

    def add_journal(self, data: dict[str, Any]) -> None:
        self.journals.append((journal_name(data['task_path']), data))

    def formatted(self, value: object) -> object:
        if isinstance(value, str):
            return value.format(**self.shas)
        if isinstance(value, dict):
            return {key: self.formatted(item) for key, item in value.items()}
        if isinstance(value, tuple):
            return list(value)
        return value

    def edit_journal(self, path: tuple[str, ...], value: object) -> None:
        node = self.journals[0][1]
        for key in path[:-1]:
            node = node[key]
        if value == REMOVE:
            del node[path[-1]]
        else:
            node[path[-1]] = self.formatted(value)

    def write_journals(self) -> None:
        if not self.journals and not self.raw_journals:
            return
        self.journal_root.mkdir(parents=True, exist_ok=True)
        for name, data in self.journals:
            (self.journal_root / name).write_text(json.dumps(data, indent=2))
        for name, raw in self.raw_journals:
            (self.journal_root / name).write_bytes(raw)

    def outcome(self, command: str, cwd: str = 'project',
                environ: dict[str, str] | None = None) -> tuple[str, str | None, str | None, object]:
        decide = self.api('decide')
        before = snapshot(self.world)
        result = decide(self.event(command, self.location(cwd)), dict(self.environ if environ is None else environ))
        self.assertEqual(before, snapshot(self.world),
                         'deciding must leave .git, the journals, the work tree and the registry unchanged')
        return result.decision, result.reason_code, result.rule_id, getattr(result, 'failure', NO_FAILURE_FIELD)

    # Named setups referenced by the journal table.
    def setup_restack(self) -> None:
        self.build_stack(self.project)
        self.add_journal(self.journal(self.project, 'task one'))

    def setup_restack_replayed(self) -> None:
        self.setup_restack()
        self.git(self.project, 'rebase', '-q', '--onto', self.shas['target'], self.shas['a_base'], 'feat/a')
        self.git(self.project, 'switch', '-q', 'main')
        self.shas['a_new'] = self.tip_in(self.project, 'feat/a')
        self.edit_journal(('branches', 'feat/a', 'replayed_tip'), '{a_new}')
        self.edit_journal(('publication_authorized',), True)

    def setup_restack_replayed_on_a(self) -> None:
        self.setup_restack_replayed()
        self.git(self.project, 'switch', '-q', 'feat/a')

    def setup_restack_replayed_two(self) -> None:
        self.setup_restack_replayed()
        second = json.loads(json.dumps(self.journals[0][1]))
        second['task_path'] = str(self.world / 'task two')
        self.add_journal(second)

    def setup_restack_replayed_no_journal(self) -> None:
        self.setup_restack_replayed()
        self.journals.clear()

    def setup_restack_moved_tip(self) -> None:
        self.setup_restack()
        self.git(self.project, 'switch', '-q', 'feat/a')
        self.commit_file(self.project, 'more.txt', 'more\n')
        self.git(self.project, 'switch', '-q', 'main')

    def setup_restack_protected_pattern(self) -> None:
        self.setup_restack()
        self.set_config('orchestrail.protectedBranch', 'feat/a')

    def setup_restack_no_journal(self) -> None:
        self.setup_restack()
        self.journals.clear()

    def setup_restack_markers(self) -> None:
        self.setup_restack()
        valid = json.dumps(self.journals.pop()[1]).encode()
        self.raw_journals += [('RESTACK', b'1\n'), ('restack.json', valid), ('restack', b'')]
        for path in (self.project / '.git/RESTACK', self.project / '.git/RESTACK_IN_PROGRESS',
                     self.project / '.ai/restack', self.project / 'RESTACK'):
            path.write_text('1\n')

    def setup_restack_two(self) -> None:
        self.setup_restack()
        self.add_journal(self.journal(self.project, 'task two'))

    def setup_restack_foreign(self) -> None:
        self.setup_restack()
        foreign = self.journal(self.project, 'task foreign')
        foreign['repository_common_dir'] = self.shas['outside_git']
        self.add_journal(foreign)

    def setup_restack_progress(self) -> None:
        self.setup_restack_foreign()
        self.journals.pop(0)
        stale = self.journal(self.project, 'task stale')
        stale['branches']['feat/a']['original_base_commit'] = OTHER_SHA
        self.add_journal(stale)

    def setup_restack_invalid_json(self) -> None:
        self.setup_restack()
        self.journals.clear()
        self.raw_journals.append((journal_name(str(self.world / 'task one')), b'{"schema_version": 1,'))

    def setup_restack_invalid_beside_valid(self) -> None:
        self.setup_restack()
        self.raw_journals.append((journal_name(str(self.world / 'task broken')), b'{"schema_version": 1,'))

    def setup_restack_not_utf8(self) -> None:
        self.setup_restack()
        name, data = self.journals.pop()
        self.raw_journals.append((name, json.dumps(data).replace('task one', 'task \udcff').encode(
            'utf-8', 'surrogateescape')))

    def setup_restack_duplicate_key(self) -> None:
        self.setup_restack()
        name, data = self.journals.pop()
        self.raw_journals.append((name, ('{"schema_version": 2, ' + json.dumps(data)[1:]).encode()))

    def setup_restack_top_array(self) -> None:
        self.setup_restack()
        name, data = self.journals.pop()
        self.raw_journals.append((name, json.dumps([data]).encode()))

    def setup_restack_wrong_name(self) -> None:
        self.setup_restack()
        data = self.journals.pop()[1]
        self.journals.append((journal_name(str(self.world / 'task elsewhere')), data))

    def setup_restack_symlink(self) -> None:
        self.setup_restack()
        name, data = self.journals.pop()
        target = self.world / 'journal copy.json'
        target.write_text(json.dumps(data))
        self.journal_root.mkdir(parents=True)
        (self.journal_root / name).symlink_to(target)

    def setup_restack_fifo(self) -> None:
        self.setup_restack()
        name = self.journals.pop()[0]
        self.journal_root.mkdir(parents=True)
        os.mkfifo(self.journal_root / name)

    def setup_restack_directory_entry(self) -> None:
        self.setup_restack()
        name = self.journals.pop()[0]
        (self.journal_root / name).mkdir(parents=True)

    def setup_restack_directory_file(self) -> None:
        self.setup_restack()
        self.journal_root.write_text(json.dumps(self.journals.pop()[1]))

    def padded(self, size: int) -> None:
        self.setup_restack()
        name, data = self.journals.pop()
        text = json.dumps(data).encode()
        self.raw_journals.append((name, text + b' ' * (size - len(text))))

    def setup_restack_limit(self) -> None:
        self.padded(JOURNAL_LIMIT)

    def setup_restack_over_limit(self) -> None:
        self.padded(JOURNAL_LIMIT + 1)

    def setup_restack_temp_file(self) -> None:
        self.setup_restack()
        self.raw_journals.append((self.journals[0][0] + '.tmp', b'{"schema_version": 1,'))

    def setup_restack_conflict(self) -> None:
        self.build_stack(self.project, conflict=True)
        self.add_journal(self.journal(self.project, 'task one'))
        self.git_may_fail('rebase', '--onto', self.shas['target'], self.shas['a_base'], 'feat/a')
        self.assertTrue((self.project / '.git/rebase-merge/head-name').is_file(), 'fixture rebase must stop')

    def setup_restack_conflict_apply(self) -> None:
        self.build_stack(self.project, conflict=True)
        self.add_journal(self.journal(self.project, 'task one'))
        self.git_may_fail('rebase', '--apply', '--onto', self.shas['target'], self.shas['a_base'], 'feat/a')
        self.assertTrue((self.project / '.git/rebase-apply/head-name').is_file(), 'fixture rebase must stop')

    def setup_restack_worktree(self) -> None:
        self.setup_restack()
        self.git(self.project, 'worktree', 'add', '-q', '-b', 'side', 'wt', 'main')

    def setup_restack_worktree_private(self) -> None:
        self.setup_restack_worktree()
        self.journal_root = self.project / '.git/worktrees/wt' / JOURNAL_DIRECTORY

    def setup_restack_sha256(self) -> None:
        directory = Path(self.location('sha256'))
        directory.mkdir()
        self.git(directory, 'init', '-q', '-b', 'main', '--object-format=sha256')
        self.commit_file(directory, 'a.txt', 'a\n')
        self.write_registry([self.project, self.plain, directory])
        self.build_stack(directory, remote=False)
        self.add_journal(self.journal(directory, 'task sha256'))
        self.journal_root = directory / '.git' / JOURNAL_DIRECTORY


def restack_test(case: RestackCase) -> Callable[[RestackFixture], None]:
    def test(self: RestackFixture) -> None:
        self.apply_setup(case.setup)
        for path, value in case.edits:
            self.edit_journal(path, value)
        self.write_journals()
        command = case.command.format(**self.shas)
        decision, reason, rule, failure = self.outcome(command, case.cwd, {**self.environ, **dict(case.environ)})
        self.assertEqual((decision, reason, failure), (case.decision, case.reason, case.failure), command)
        if case.rule is not None:
            self.assertEqual(rule, case.rule, command)
    return test


def rebase_row(name: str, command: str, failure: str | None, **fields: Any) -> RestackCase:
    if failure is None:
        return RestackCase(name, command, 'allow', **fields)
    return RestackCase(name, command, 'ask', OUTSIDE_RESTACK, 'R26', failure, **fields)


def push_row(name: str, command: str, failure: str | None, **fields: Any) -> RestackCase:
    fields.setdefault('setup', 'restack-replayed')
    if failure is None:
        return RestackCase(name, command, 'allow', **fields)
    return RestackCase(name, command, 'ask', LEASE, 'R18', failure, **fields)


def schema_row(name: str, path: tuple[str, ...], value: object) -> RestackCase:
    return rebase_row('journal_schema_rejects_' + name, ONTO_A, SCHEMA, edits=((path, value),))


A_BRANCH = ('branches', 'feat/a')
MAIN_ENTRY = {'original_base_commit': '{a_base}', 'original_tip': '{target}', 'replayed_tip': None,
              'expected_remote_tip': None}
MAIN_REPLAYED = {'original_base_commit': '{a_base}', 'original_tip': '{a_base}', 'replayed_tip': '{target}',
                 'expected_remote_tip': '{a_base}'}
B_REPLAYED = ((('branches', 'feat/b', 'replayed_tip'), '{b_tip}'),)

REPLAY_CASES: tuple[RestackCase, ...] = (
    rebase_row('journal_allows_the_exact_replay_of_the_first_branch', ONTO_A, None),
    rebase_row('journal_allows_the_exact_replay_with_a_global_directory_option',
               'git -C sub rebase --onto {target} {a_base} feat/a', None),
    rebase_row('journal_allows_the_replay_from_a_subdirectory', ONTO_A, None, cwd='sub'),
    rebase_row('journal_of_another_repository_does_not_prove_a_replay', ONTO_A, 'repository',
               edits=((('repository_common_dir',), '{outside_git}'),)),
    rebase_row('journal_repository_must_be_the_canonical_common_dir', ONTO_A, 'repository',
               edits=((('repository_common_dir',), '{project_git}/'),)),
    rebase_row('journal_without_the_branch_in_order_does_not_prove_a_replay', ONTO_A, 'branch-in-order',
               edits=((('order',), ('feat/b',)),)),
    rebase_row('replay_of_an_unlisted_branch_asks', 'git rebase --onto {target} {a_base} feat/c', 'branch-in-order'),
    rebase_row('replay_of_a_protected_branch_in_order_asks', 'git rebase --onto {target} {a_base} main',
               'branch-protected', edits=((('order',), ('main', 'feat/a', 'feat/b')),
                                          (('branches', 'main'), MAIN_ENTRY))),
    rebase_row('replay_of_a_branch_matching_a_configured_pattern_asks', ONTO_A, 'branch-protected',
               setup='restack-protected-pattern'),
    rebase_row('replay_of_an_already_replayed_branch_asks', ONTO_A, 'branch-replayed',
               edits=(((*A_BRANCH, 'replayed_tip'), '{target}'),)),
    rebase_row('replay_after_the_local_tip_moved_asks', ONTO_A, 'branch-tip', setup='restack-moved-tip'),
    rebase_row('replay_with_a_wrong_old_sha_asks', 'git rebase --onto {target} {b_base} feat/a', 'old-sha'),
    rebase_row('replay_with_a_wrong_new_sha_asks', 'git rebase --onto {a_base} {a_base} feat/a', 'new-sha'),
    rebase_row('replay_with_an_abbreviated_new_sha_asks', 'git rebase --onto {target_short} {a_base} feat/a',
               'new-sha'),
    rebase_row('replay_with_an_uppercase_new_sha_asks', 'git rebase --onto {TARGET} {a_base} feat/a', 'new-sha'),
    rebase_row('replay_onto_a_branch_name_asks', 'git rebase --onto main {a_base} feat/a', 'new-sha'),
    rebase_row('second_branch_needs_the_first_replayed_tip', 'git rebase --onto {target} {b_base} feat/b',
               'new-sha'),
    rebase_row('second_branch_replays_onto_the_previous_replayed_tip', 'git rebase --onto {a_new} {b_base} feat/b',
               None, setup='restack-replayed'),
    rebase_row('second_branch_onto_the_target_after_the_first_replay_asks',
               'git rebase --onto {target} {b_base} feat/b', 'new-sha', setup='restack-replayed'),
    rebase_row('replayed_first_branch_cannot_be_replayed_again', ONTO_A, 'branch-replayed',
               setup='restack-replayed'),
    rebase_row('replay_with_an_attached_onto_value_is_not_the_exact_form',
               'git rebase --onto={target} {a_base} feat/a', 'replay-form'),
    rebase_row('replay_with_an_extra_option_is_not_the_exact_form',
               'git rebase -q --onto {target} {a_base} feat/a', 'replay-form'),
    rebase_row('replay_without_a_branch_is_not_the_exact_form', 'git rebase --onto {target} {a_base}',
               'replay-form'),
    rebase_row('interactive_replay_is_not_the_exact_form', 'git rebase -i --onto {target} {a_base} feat/a',
               'replay-form'),
    rebase_row('plain_rebase_with_a_journal_asks', 'git rebase main', 'replay-form'),
    rebase_row('restack_variable_on_the_command_is_no_evidence', 'RESTACK=1 ' + ONTO_A, 'journal-missing',
               setup='restack-no-journal'),
    rebase_row('restack_variable_in_the_environment_is_no_evidence', ONTO_A, 'journal-missing',
               setup='restack-no-journal', environ=(('RESTACK', '1'),)),
    rebase_row('restack_variable_does_not_rescue_a_failed_check', 'git rebase --onto {a_base} {a_base} feat/a',
               'new-sha', environ=(('RESTACK', '1'),)),
    rebase_row('restack_variable_does_not_change_a_verified_replay', 'RESTACK=1 ' + ONTO_A, None,
               environ=(('RESTACK', '1'),)),
    rebase_row('marker_files_are_no_evidence', ONTO_A, 'journal-missing', setup='restack-markers'),
    rebase_row('restack_word_in_the_command_is_no_evidence', 'echo restack && ' + ONTO_A, 'journal-missing',
               setup='restack-no-journal'),
    rebase_row('abort_with_a_journal_is_allowed', 'git rebase --abort', None),
    rebase_row('abort_during_a_journal_rebase_is_allowed', 'git rebase --abort', None, setup='restack-conflict'),
    rebase_row('continue_during_a_journal_branch_rebase_is_allowed', 'git rebase --continue', None,
               setup='restack-conflict'),
    rebase_row('skip_during_a_journal_branch_rebase_is_allowed', 'git rebase --skip', None,
               setup='restack-conflict-apply'),
    rebase_row('continue_during_a_rebase_of_a_branch_outside_order_asks', 'git rebase --continue',
               'branch-in-order', setup='restack-conflict', edits=((('order',), ('feat/b',)),)),
    rebase_row('continue_of_an_already_replayed_branch_asks', 'git rebase --continue', 'branch-replayed',
               setup='restack-conflict', edits=(((*A_BRANCH, 'replayed_tip'), '{target}'),)),
    rebase_row('continue_with_a_journal_of_another_repository_asks', 'git rebase --continue', 'repository',
               setup='restack-conflict', edits=((('repository_common_dir',), '{outside_git}'),)),
    rebase_row('continue_without_a_rebase_in_progress_asks', 'git rebase --continue', 'rebase-head'),
    rebase_row('quit_during_a_journal_rebase_asks', 'git rebase --quit', 'replay-form', setup='restack-conflict'),
    rebase_row('edit_todo_during_a_journal_rebase_asks', 'git rebase --edit-todo', 'replay-form',
               setup='restack-conflict'),
    RestackCase('replay_after_a_switch_in_the_same_command_is_unsupported', 'git switch main && ' + ONTO_A,
                'deny', UNSUPPORTED, 'R26'),
    rebase_row('two_matching_journals_are_ambiguous', ONTO_A, 'journal-ambiguous', setup='restack-two'),
    rebase_row('journal_of_another_repository_beside_a_valid_one_is_ignored', ONTO_A, None,
               setup='restack-foreign'),
    rebase_row('failed_check_is_named_from_the_closest_journal', ONTO_A, 'old-sha', setup='restack-progress'),
    rebase_row('invalid_json_asks', ONTO_A, 'journal-invalid-json', setup='restack-invalid-json'),
    rebase_row('invalid_json_beside_a_valid_journal_asks', ONTO_A, 'journal-invalid-json',
               setup='restack-invalid-beside-valid'),
    rebase_row('journal_that_is_not_utf8_is_invalid_json', ONTO_A, 'journal-invalid-json', setup='restack-not-utf8'),
    rebase_row('journal_with_a_duplicate_key_is_invalid_json', ONTO_A, 'journal-invalid-json',
               setup='restack-duplicate-key'),
    rebase_row('journal_that_is_not_an_object_has_an_invalid_schema', ONTO_A, SCHEMA, setup='restack-top-array'),
    rebase_row('journal_named_for_another_task_path_asks', ONTO_A, 'journal-name', setup='restack-wrong-name'),
    rebase_row('journal_symlink_is_not_read', ONTO_A, 'journal-unreadable', setup='restack-symlink'),
    rebase_row('journal_fifo_is_not_read', ONTO_A, 'journal-unreadable', setup='restack-fifo'),
    rebase_row('journal_directory_entry_is_not_read', ONTO_A, 'journal-unreadable',
               setup='restack-directory-entry'),
    rebase_row('journal_location_that_is_a_file_is_unreadable', ONTO_A, 'journal-unreadable',
               setup='restack-directory-file'),
    rebase_row('journal_at_the_size_limit_is_read', ONTO_A, None, setup='restack-limit'),
    rebase_row('journal_over_the_size_limit_is_not_read', ONTO_A, 'journal-unreadable', setup='restack-over-limit'),
    rebase_row('temporary_file_beside_a_journal_is_ignored', ONTO_A, None, setup='restack-temp-file'),
    rebase_row('journal_in_the_common_dir_proves_a_replay_from_a_linked_worktree', ONTO_A, None,
               setup='restack-worktree', cwd='wt'),
    rebase_row('journal_in_a_worktree_git_dir_is_not_read', ONTO_A, 'journal-missing',
               setup='restack-worktree-private', cwd='wt'),
    rebase_row('journal_with_64_hex_shas_proves_a_replay', ONTO_A, None, setup='restack-sha256', cwd='sha256'),
    rebase_row('journal_with_64_hex_shas_checks_the_old_sha', 'git rebase --onto {target} {b_base} feat/a',
               'old-sha', setup='restack-sha256', cwd='sha256'),
    rebase_row('journal_with_extra_fields_is_valid', ONTO_A, None,
               edits=((('notes',), 'restack notes'), ((*A_BRANCH, 'note'), 'kept'), (('target', 'remote'), 'origin'),
                      (('branches', 'feat/z'), {'original_base_commit': '{a_base}', 'original_tip': '{a_tip}',
                                                'replayed_tip': None, 'expected_remote_tip': None}))),
    rebase_row('journal_accepts_a_64_hex_target_in_a_sha1_repository', ONTO_A, 'new-sha',
               edits=((('target', 'sha'), '{long}'),)),
)

SCHEMA_CASES: tuple[RestackCase, ...] = (
    schema_row('another_schema_version', ('schema_version',), 2),
    schema_row('a_boolean_schema_version', ('schema_version',), True),
    schema_row('a_string_schema_version', ('schema_version',), '1'),
    schema_row('a_float_schema_version', ('schema_version',), 1.0),
    schema_row('a_missing_schema_version', ('schema_version',), REMOVE),
    schema_row('a_missing_repository', ('repository_common_dir',), REMOVE),
    schema_row('a_relative_repository', ('repository_common_dir',), 'relative/.git'),
    schema_row('a_numeric_repository', ('repository_common_dir',), 7),
    schema_row('a_missing_task_path', ('task_path',), REMOVE),
    schema_row('a_relative_task_path', ('task_path',), 'relative/task'),
    schema_row('a_missing_target', ('target',), REMOVE),
    schema_row('a_missing_target_branch', ('target', 'branch'), REMOVE),
    schema_row('an_empty_target_branch', ('target', 'branch'), ''),
    schema_row('an_uppercase_target_sha', ('target', 'sha'), '{TARGET}'),
    schema_row('an_abbreviated_target_sha', ('target', 'sha'), '{target_short}'),
    schema_row('a_null_target_sha', ('target', 'sha'), None),
    schema_row('a_string_publication_flag', ('publication_authorized',), 'true'),
    schema_row('a_numeric_publication_flag', ('publication_authorized',), 1),
    schema_row('a_missing_publication_flag', ('publication_authorized',), REMOVE),
    schema_row('a_string_order', ('order',), 'feat/a'),
    schema_row('a_numeric_order_entry', ('order',), (1,)),
    schema_row('a_duplicate_order_entry', ('order',), ('feat/a', 'feat/a')),
    schema_row('a_missing_order', ('order',), REMOVE),
    schema_row('an_order_entry_without_a_branch_record', ('order',), ('feat/a', 'feat/b', 'feat/c')),
    schema_row('an_option_like_branch_name', ('order',), ('-x', 'feat/a')),
    schema_row('a_branch_name_with_dots', ('order',), ('feat/a..b', 'feat/a')),
    schema_row('a_branch_name_with_a_glob', ('order',), ('feat/*', 'feat/a')),
    schema_row('missing_branches', ('branches',), REMOVE),
    schema_row('a_branches_list', ('branches',), ('feat/a',)),
    schema_row('a_missing_branch_record', A_BRANCH, REMOVE),
    schema_row('a_missing_original_base_commit', (*A_BRANCH, 'original_base_commit'), REMOVE),
    schema_row('an_uppercase_original_base_commit', (*A_BRANCH, 'original_base_commit'), '{TARGET}'),
    schema_row('a_null_original_tip', (*A_BRANCH, 'original_tip'), None),
    schema_row('an_absent_replayed_tip', (*A_BRANCH, 'replayed_tip'), 'absent'),
    schema_row('an_uppercase_replayed_tip', (*A_BRANCH, 'replayed_tip'), '{TARGET}'),
    schema_row('a_missing_replayed_tip', (*A_BRANCH, 'replayed_tip'), REMOVE),
    schema_row('an_uppercase_absent_marker', (*A_BRANCH, 'expected_remote_tip'), 'ABSENT'),
    schema_row('another_remote_tip_word', (*A_BRANCH, 'expected_remote_tip'), 'none'),
    schema_row('an_uppercase_remote_tip', (*A_BRANCH, 'expected_remote_tip'), '{TARGET}'),
    schema_row('a_missing_remote_tip', (*A_BRANCH, 'expected_remote_tip'), REMOVE),
    schema_row('a_malformed_record_outside_order', ('branches', 'feat/z'), {'original_tip': 'x'}),
)

PUBLICATION_CASES: tuple[RestackCase, ...] = (
    push_row('journal_allows_the_exact_lease_push', PUSH_A, None),
    push_row('journal_allows_a_short_lease_ref',
             'git push --force-with-lease=feat/a:{a_remote} origin feat/a', None),
    push_row('journal_allows_a_full_refspec',
             'git push --force-with-lease=refs/heads/feat/a:{a_remote} origin refs/heads/feat/a:refs/heads/feat/a',
             None),
    push_row('journal_allows_force_if_includes_with_the_lease',
             'git push --force-with-lease=refs/heads/feat/a:{a_remote} --force-if-includes origin feat/a', None),
    push_row('journal_allows_pushing_head_of_the_branch',
             'git push --force-with-lease=refs/heads/feat/a:{a_remote} origin HEAD', None,
             setup='restack-replayed-on-a'),
    push_row('journal_allows_the_default_push_of_the_branch',
             'git push --force-with-lease=refs/heads/feat/a:{a_remote}', None, setup='restack-replayed-on-a'),
    push_row('lease_different_from_the_expected_remote_tip_asks',
             'git push --force-with-lease=refs/heads/feat/a:{other} origin feat/a', 'lease'),
    push_row('lease_of_the_local_tip_asks', 'git push --force-with-lease=refs/heads/feat/a:{a_new} origin feat/a',
             'lease'),
    push_row('empty_lease_for_a_branch_present_on_the_remote_asks',
             'git push --force-with-lease=refs/heads/feat/a: origin feat/a', 'lease'),
    push_row('lease_without_a_captured_remote_tip_asks', PUSH_A, 'lease',
             edits=(((*A_BRANCH, 'expected_remote_tip'), None),)),
    push_row('unauthorized_publication_asks', PUSH_A, 'publication-authorized',
             edits=((('publication_authorized',), False),)),
    RestackCase('force_with_a_valid_journal_asks', 'git push -f --force-with-lease=refs/heads/feat/a:{a_remote} '
                'origin feat/a', 'ask', FORCE_DEFAULT, 'R17', 'forced', setup='restack-replayed'),
    RestackCase('forced_refspec_with_a_valid_journal_asks', 'git push --force-with-lease=refs/heads/feat/a:{a_remote} '
                'origin +feat/a', 'ask', FORCE_DEFAULT, 'R17', 'forced', setup='restack-replayed'),
    RestackCase('protected_destination_with_a_journal_asks',
                'git push --force-with-lease=refs/heads/main:{a_base} origin main', 'ask', PROTECTED, 'R16',
                'branch-protected',
                setup='restack-replayed', edits=((('order',), ('main', 'feat/a', 'feat/b')),
                                                 (('branches', 'main'), MAIN_REPLAYED))),
    push_row('destination_outside_order_asks', PUSH_A, 'branch-in-order', edits=((('order',), ('feat/b',)),)),
    push_row('local_tip_different_from_the_replayed_tip_asks', PUSH_A, 'branch-tip',
             edits=(((*A_BRANCH, 'replayed_tip'), '{target}'),)),
    push_row('branch_not_yet_replayed_asks', 'git push --force-with-lease=refs/heads/feat/b: origin feat/b',
             'branch-not-replayed'),
    push_row('empty_lease_for_a_branch_recorded_absent_is_allowed',
             'git push --force-with-lease=refs/heads/feat/b: origin feat/b', None, edits=B_REPLAYED),
    push_row('explicit_lease_for_a_branch_recorded_absent_asks',
             'git push --force-with-lease=refs/heads/feat/b:{b_tip} origin feat/b', 'lease', edits=B_REPLAYED),
    push_row('pushing_another_object_onto_the_branch_asks',
             'git push --force-with-lease=refs/heads/feat/a:{a_remote} origin main~0:feat/a', 'source'),
    push_row('pushing_the_replayed_sha_instead_of_the_branch_asks',
             'git push --force-with-lease=refs/heads/feat/a:{a_remote} origin {a_new}:feat/a', 'source'),
    push_row('pushing_another_branch_onto_the_branch_asks',
             'git push --force-with-lease=refs/heads/feat/a:{a_remote} origin feat/b:feat/a', 'source'),
    push_row('pushing_a_revision_of_the_branch_asks',
             'git push --force-with-lease=refs/heads/feat/a:{a_remote} origin feat/a~0:feat/a', 'source'),
    push_row('journal_allows_every_verified_destination',
             'git push --force-with-lease=refs/heads/feat/a:{a_remote} --force-with-lease=refs/heads/feat/b: '
             'origin feat/a feat/b', None, edits=B_REPLAYED),
    push_row('one_unverified_destination_asks',
             'git push --force-with-lease=refs/heads/feat/a:{a_remote} --force-with-lease=refs/heads/feat/b: '
             'origin feat/a feat/b', 'branch-not-replayed'),
    push_row('destination_without_its_own_lease_asks',
             'git push --force-with-lease=refs/heads/feat/a:{a_remote} origin feat/a feat/b', 'explicit-lease',
             edits=B_REPLAYED),
    push_row('bare_lease_with_a_journal_asks', 'git push --force-with-lease origin feat/a', 'explicit-lease'),
    push_row('lease_with_a_journal_of_another_repository_asks', PUSH_A, 'repository',
             edits=((('repository_common_dir',), '{outside_git}'),)),
    push_row('lease_without_a_journal_asks', PUSH_A, 'journal-missing', setup='restack-replayed-no-journal'),
    push_row('lease_with_invalid_json_beside_a_journal_asks', PUSH_A, 'journal-invalid-json',
             setup='restack-invalid-beside-valid'),
    push_row('lease_with_two_matching_journals_asks', PUSH_A, 'journal-ambiguous', setup='restack-replayed-two'),
    push_row('restack_variable_does_not_verify_a_lease', 'RESTACK=1 ' + PUSH_A, 'journal-missing',
             setup='restack-replayed-no-journal', environ=(('RESTACK', '1'),)),
    push_row('restack_variable_does_not_change_a_verified_lease', 'RESTACK=1 ' + PUSH_A, None,
             environ=(('RESTACK', '1'),)),
    push_row('marker_files_do_not_verify_a_lease', PUSH_A, 'journal-missing', setup='restack-markers'),
    RestackCase('lease_after_a_switch_in_the_same_command_is_unverifiable', 'git switch feat/a && ' + PUSH_A,
                'deny', 'push-target-unknown', 'R12', setup='restack-replayed'),
)


class RestackJournalTable(RestackFixture):
    """Table-driven replay and publication decisions with restack recovery journals."""


for restack_case in (*REPLAY_CASES, *SCHEMA_CASES, *PUBLICATION_CASES):
    setattr(RestackJournalTable, 'test_' + restack_case.name, restack_test(restack_case))


class RestackVerifierInterface(RestackFixture):
    """The shipped verifiers read restack journals; requests and decisions carry what they check."""

    def recorder(self, name: str, stub: bool) -> list[tuple[Any, Any]]:
        calls: list[tuple[Any, Any]] = []
        original = self.api(name)
        verdict = self.api('LeaseVerdict' if name == 'LEASE_VERIFIER' else 'ReplayVerdict')

        def verifier(request: Any, invocation: Any, context: Any) -> Any:
            result = verdict(False, 'fixture verifier refused') if stub else original(request, invocation, context)
            calls.append((request, result))
            return result
        setattr(CORE, name, verifier)
        self.addCleanup(setattr, CORE, name, original)
        return calls

    def test_shipped_verifiers_read_restack_journals(self) -> None:
        self.assertIs(self.api('LEASE_VERIFIER'), self.api('journal_lease_verifier'))
        self.assertIs(self.api('REPLAY_VERIFIER'), self.api('journal_replay_verifier'))

    def test_lease_request_carries_each_destination_source(self) -> None:
        self.setup_restack_replayed_on_a()
        self.write_journals()
        calls = self.recorder('LEASE_VERIFIER', True)
        lease = f'--force-with-lease=refs/heads/feat/a:{self.shas["a_remote"]}'
        both = f'{lease} --force-with-lease=refs/heads/feat/b:'
        for refspecs, sources in (('origin feat/a', ('feat/a',)), ('origin main~0:feat/a', ('main~0',)),
                                  ('origin refs/heads/feat/a:feat/a', ('refs/heads/feat/a',)),
                                  ('origin HEAD', ('refs/heads/feat/a',))):
            with self.subTest(refspecs=refspecs):
                calls.clear()
                self.outcome(f'git push {lease} {refspecs}')
                self.assertEqual(tuple(getattr(calls[0][0], 'sources', ())), sources)
        calls.clear()
        self.outcome(f'git push {both} origin feat/a feat/b')
        request = calls[0][0]
        self.assertEqual((tuple(request.destinations), tuple(getattr(request, 'sources', ()))),
                         (('refs/heads/feat/a', 'refs/heads/feat/b'), ('feat/a', 'feat/b')))

    def test_verifier_failure_is_named_in_the_decision(self) -> None:
        self.setup_restack_replayed()
        self.write_journals()
        self.recorder('LEASE_VERIFIER', True)
        self.recorder('REPLAY_VERIFIER', True)
        self.assertEqual(self.outcome(PUSH_A.format(**self.shas)), ('ask', LEASE, 'R18', 'fixture verifier refused'))
        self.assertEqual(self.outcome('git rebase main'),
                         ('ask', OUTSIDE_RESTACK, 'R26', 'fixture verifier refused'))

    def test_no_journal_decisions_name_the_missing_journal(self) -> None:
        self.setup_push_feature()
        self.assertEqual(self.outcome(f'git push --force-with-lease=feat/x:{LEASE_SHA} origin feat/x'),
                         ('ask', LEASE, 'R18', 'journal-missing'))
        self.assertEqual(self.outcome('git rebase main'), ('ask', OUTSIDE_RESTACK, 'R26', 'journal-missing'))

    def test_forced_lease_with_a_valid_journal_names_the_forced_check(self) -> None:
        self.setup_restack_replayed()
        self.write_journals()
        calls = self.recorder('LEASE_VERIFIER', False)
        for command in ('git push -f ' + PUSH_A[len('git push '):], PUSH_A.replace('origin feat/a', 'origin +feat/a')):
            with self.subTest(command=command):
                calls.clear()
                self.assertEqual(self.outcome(command.format(**self.shas))[:2], ('ask', FORCE_DEFAULT))
                self.assertEqual((calls[0][0].forced, calls[0][1].verified, calls[0][1].failure),
                                 (True, False, 'forced'))

    def test_protected_destination_with_a_valid_journal_names_the_protected_check(self) -> None:
        self.setup_restack_replayed()
        self.edit_journal(('order',), ('main', 'feat/a', 'feat/b'))
        self.edit_journal(('branches', 'main'), MAIN_REPLAYED)
        self.write_journals()
        calls = self.recorder('LEASE_VERIFIER', False)
        command = f'git push --force-with-lease=refs/heads/main:{self.shas["a_base"]} origin main'
        self.assertEqual(self.outcome(command)[:2], ('ask', PROTECTED))
        self.assertEqual((calls[0][1].verified, calls[0][1].failure), (False, 'branch-protected'))

    def test_verified_lease_is_reported_without_a_failure(self) -> None:
        self.setup_restack_replayed()
        self.write_journals()
        calls = self.recorder('LEASE_VERIFIER', False)
        self.assertEqual(self.outcome(PUSH_A.format(**self.shas)), ('allow', None, None, None))
        self.assertEqual((calls[0][1].verified, calls[0][1].failure), (True, None))

    def test_other_results_carry_no_failure(self) -> None:
        self.setup_restack_replayed()
        self.write_journals()
        for command, expected in (('git status', ('not_applicable', None, None, None)),
                                  ('git push origin feat/b', ('allow', None, None, None)),
                                  ('git push -f origin feat/b', ('ask', FORCE_DEFAULT, 'R17', None)),
                                  ('git add -A', ('deny', BLANKET, 'R01', None))):
            with self.subTest(command=command):
                self.assertEqual(self.outcome(command), expected)

    def repeated(self, setup: str) -> None:
        self.apply_setup(setup)
        self.write_journals()
        decide = self.api('decide')
        event = self.event(ONTO_A.format(**self.shas), str(self.project))
        results = [decide(event, dict(self.environ)) for _ in range(3)]
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])
        self.assertNotEqual(getattr(results[0], 'failure', NO_FAILURE_FIELD), NO_FAILURE_FIELD)

    def test_repeated_decisions_name_the_same_closest_failure(self) -> None:
        self.repeated('restack-progress')

    def test_repeated_decisions_name_the_same_ambiguity(self) -> None:
        self.repeated('restack-two')


CLASSES = (*CLASSES, RestackJournalTable, RestackVerifierInterface)


# rebase.updateRefs makes git also move every branch that points inside the replayed range,
# so a configured value, wherever git reads it from, takes a replay outside the journal's proof.
class UpdateRefsFixture(RestackFixture):
    """Journals together with rebase.updateRefs in the repository or the user's global config."""

    def update_refs(self, value: str, scope: str = '--local') -> None:
        self.git(self.project, 'config', scope, 'rebase.updateRefs', value)

    def setup_restack_update_refs(self) -> None:
        self.setup_restack()
        self.update_refs('true')

    def setup_restack_update_refs_yes(self) -> None:
        self.setup_restack()
        self.update_refs('yes')

    def setup_restack_update_refs_invalid(self) -> None:
        self.setup_restack()
        self.update_refs('sometimes')

    def setup_restack_update_refs_false(self) -> None:
        self.setup_restack()
        self.update_refs('false')

    def setup_restack_update_refs_global(self) -> None:
        self.setup_restack()
        self.update_refs('true', '--global')

    def setup_restack_update_refs_global_overridden(self) -> None:
        self.setup_restack_update_refs_global()
        self.update_refs('false')

    def setup_restack_conflict_update_refs(self) -> None:
        self.setup_restack_conflict()
        self.update_refs('true')

    def setup_restack_conflict_apply_update_refs(self) -> None:
        self.setup_restack_conflict_apply()
        self.update_refs('true')

    def setup_restack_replayed_update_refs(self) -> None:
        self.setup_restack_replayed()
        self.update_refs('true')


UPDATE_REFS_CASES: tuple[RestackCase, ...] = (
    rebase_row('replay_with_update_refs_configured_asks', ONTO_A, 'update-refs', setup='restack-update-refs'),
    rebase_row('replay_with_update_refs_spelled_yes_asks', ONTO_A, 'update-refs', setup='restack-update-refs-yes'),
    rebase_row('replay_with_an_invalid_update_refs_value_asks', ONTO_A, 'update-refs',
               setup='restack-update-refs-invalid'),
    rebase_row('replay_with_update_refs_in_the_global_config_asks', ONTO_A, 'update-refs',
               setup='restack-update-refs-global'),
    rebase_row('continue_with_update_refs_configured_asks', 'git rebase --continue', 'update-refs',
               setup='restack-conflict-update-refs'),
    rebase_row('skip_with_update_refs_configured_asks', 'git rebase --skip', 'update-refs',
               setup='restack-conflict-apply-update-refs'),
    rebase_row('replay_with_update_refs_false_is_allowed', ONTO_A, None, setup='restack-update-refs-false'),
    rebase_row('replay_with_global_update_refs_overridden_by_the_repository_is_allowed', ONTO_A, None,
               setup='restack-update-refs-global-overridden'),
    rebase_row('replay_without_update_refs_configured_is_allowed', ONTO_A, None),
    rebase_row('abort_with_update_refs_configured_is_allowed', 'git rebase --abort', None,
               setup='restack-conflict-update-refs'),
    RestackCase('update_refs_on_the_command_line_is_unsupported', 'git -c rebase.updateRefs=true ' + ONTO_A[4:],
                'deny', UNSUPPORTED, 'R31'),
    push_row('lease_push_with_update_refs_configured_is_allowed', PUSH_A, None,
             setup='restack-replayed-update-refs'),
)


class UpdateRefsTable(UpdateRefsFixture):
    """Table-driven replay decisions with rebase.updateRefs configured."""


for update_refs_case in UPDATE_REFS_CASES:
    setattr(UpdateRefsTable, 'test_' + update_refs_case.name, restack_test(update_refs_case))

CLASSES = (*CLASSES, UpdateRefsTable)


# git applies the first explicit lease that names a destination, so two leases for one branch are
# never read as one; a rebase stopped with stored update-refs moves other branches on --continue;
# JSON number constants outside the JSON grammar are not a journal.
class StoredUpdateRefsFixture(UpdateRefsFixture):
    """A journal-branch rebase stopped on a conflict, with or without stored update-refs."""

    def stopped_update_refs_rebase(self, side_branch: bool) -> None:
        self.build_stack(self.project, conflict=True)
        self.git(self.project, 'switch', '-q', 'feat/a')
        if side_branch:
            self.git(self.project, 'branch', 'side-a')
        self.commit_file(self.project, 'fa2.txt', 'feature a again\n')
        self.git(self.project, 'switch', '-q', 'main')
        self.shas['a_tip'] = self.tip_in(self.project, 'feat/a')
        self.add_journal(self.journal(self.project, 'task one'))
        self.git_may_fail('rebase', '--update-refs', '--onto', self.shas['target'], self.shas['a_base'], 'feat/a')
        self.assertTrue((self.project / '.git/rebase-merge/head-name').is_file(), 'fixture rebase must stop')
        stored = self.project / '.git/rebase-merge/update-refs'
        self.assertEqual(stored.is_file() and stored.stat().st_size > 0, side_branch, 'fixture update-refs state')

    def setup_restack_conflict_stored_update_refs(self) -> None:
        self.stopped_update_refs_rebase(True)

    def setup_restack_conflict_without_stored_update_refs(self) -> None:
        self.stopped_update_refs_rebase(False)


def double_lease(first: str, second: str) -> str:
    return f'git push --force-with-lease={first} --force-with-lease={second} origin feat/a'


VALIDATION_REPAIR_CASES: tuple[RestackCase, ...] = (
    push_row('second_lease_cannot_hide_a_first_short_lease',
             double_lease('feat/a:{other}', 'refs/heads/feat/a:{a_remote}'), 'explicit-lease'),
    push_row('second_lease_cannot_hide_a_first_full_lease',
             double_lease('refs/heads/feat/a:{other}', 'refs/heads/feat/a:{a_remote}'), 'explicit-lease'),
    push_row('first_lease_of_two_short_leases_is_not_trusted',
             double_lease('feat/a:{other}', 'feat/a:{a_remote}'), 'explicit-lease'),
    push_row('verified_lease_first_and_another_lease_second_asks',
             double_lease('refs/heads/feat/a:{a_remote}', 'feat/a:{other}'), 'explicit-lease'),
    push_row('partial_heads_lease_counts_as_a_lease_of_the_branch',
             double_lease('heads/feat/a:{other}', 'feat/a:{a_remote}'), 'explicit-lease'),
    push_row('two_identical_leases_for_one_destination_ask',
             double_lease('refs/heads/feat/a:{a_remote}', 'refs/heads/feat/a:{a_remote}'), 'explicit-lease'),
    push_row('lease_of_another_branch_beside_one_explicit_lease_is_allowed',
             double_lease('refs/heads/feat/b:', 'refs/heads/feat/a:{a_remote}'), None),
    push_row('negated_earlier_lease_leaves_one_explicit_lease',
             'git push --force-with-lease=feat/a:{other} --no-force-with-lease '
             '--force-with-lease=refs/heads/feat/a:{a_remote} origin feat/a', None),
    rebase_row('continue_with_stored_update_refs_asks', 'git rebase --continue', 'update-refs',
               setup='restack-conflict-stored-update-refs'),
    rebase_row('skip_with_stored_update_refs_asks', 'git rebase --skip', 'update-refs',
               setup='restack-conflict-stored-update-refs'),
    rebase_row('continue_of_an_update_refs_rebase_without_stored_refs_is_allowed', 'git rebase --continue', None,
               setup='restack-conflict-without-stored-update-refs'),
    rebase_row('abort_with_stored_update_refs_is_allowed', 'git rebase --abort', None,
               setup='restack-conflict-stored-update-refs'),
    rebase_row('journal_with_a_nan_constant_is_invalid_json', ONTO_A, 'journal-invalid-json',
               edits=((('notes',), float('nan')),)),
    rebase_row('journal_with_an_infinity_constant_is_invalid_json', ONTO_A, 'journal-invalid-json',
               edits=((('notes',), float('inf')),)),
    rebase_row('journal_with_a_negative_infinity_constant_is_invalid_json', ONTO_A, 'journal-invalid-json',
               edits=((('notes',), float('-inf')),)),
)


class ValidationRepairTable(StoredUpdateRefsFixture):
    """Table-driven decisions for repeated leases, stored update-refs and non-JSON constants."""


for validation_case in VALIDATION_REPAIR_CASES:
    setattr(ValidationRepairTable, 'test_' + validation_case.name, restack_test(validation_case))

CLASSES = (*CLASSES, ValidationRepairTable)


# git splits a push refspec at its last colon, qualifies a partial upstream merge value
# through refs/<name>, runs programs named by pull --upload-pack and by the target remote's
# receivepack or submodule recursion configuration, lets a rebasing pull move other
# branches under rebase.updateRefs, and resolves a relative repository redirect against
# the directory git runs in (git 2.53, local bare remote, dry-run evidence).
class ResolutionGapFixture(StoredUpdateRefsFixture):
    """Push, pull and journal states for the refspec, configuration and redirect cases."""

    def setup_push_upstream_partial_main(self) -> None:
        self.setup_push()
        self.git(self.project, 'switch', '-q', 'feat/y')
        self.set_config('push.default', 'upstream')
        self.set_config('branch.feat/y.remote', 'origin')
        self.set_config('branch.feat/y.merge', 'heads/main')

    def setup_push_upstream_partial_feature(self) -> None:
        self.setup_push()
        self.git(self.project, 'switch', '-q', 'feat/y')
        self.set_config('push.default', 'upstream')
        self.set_config('branch.feat/y.remote', 'origin')
        self.set_config('branch.feat/y.merge', 'heads/feat/y')

    def setup_pull_update_refs(self) -> None:
        self.setup_push_feature()
        self.set_config('rebase.updateRefs', 'true')

    def setup_pull_update_refs_false(self) -> None:
        self.setup_push_feature()
        self.set_config('rebase.updateRefs', 'false')

    def setup_pull_configured_rebase(self) -> None:
        self.setup_pull_update_refs()
        self.set_config('pull.rebase', 'true')

    def setup_pull_branch_rebase(self) -> None:
        self.setup_pull_update_refs()
        self.set_config('branch.feat/x.rebase', 'merges')

    def setup_pull_branch_rebase_off(self) -> None:
        self.setup_pull_configured_rebase()
        self.set_config('branch.feat/x.rebase', 'false')

    def setup_pull_configured_rebase_without_update_refs(self) -> None:
        self.setup_push_feature()
        self.set_config('pull.rebase', 'true')

    def setup_push_receive_pack(self) -> None:
        self.setup_push_feature()
        self.set_config('remote.origin.receivepack', 'git-receive-pack')

    def setup_push_backup_receive_pack(self) -> None:
        self.setup_push_backup()
        self.set_config('remote.backup.receivepack', 'git-receive-pack')

    def setup_push_recurse_on_demand(self) -> None:
        self.setup_push_feature()
        self.set_config('push.recurseSubmodules', 'on-demand')

    def setup_push_recurse_only(self) -> None:
        self.setup_push_feature()
        self.set_config('push.recurseSubmodules', 'only')

    def setup_push_recurse_check(self) -> None:
        self.setup_push_feature()
        self.set_config('push.recurseSubmodules', 'check')

    def setup_push_submodule_recurse(self) -> None:
        self.setup_push_feature()
        self.set_config('submodule.recurse', 'true')

    def setup_push_submodule_recurse_off(self) -> None:
        self.setup_push_feature()
        self.set_config('submodule.recurse', 'false')

    def setup_restack_replayed_receive_pack(self) -> None:
        self.setup_restack_replayed()
        self.set_config('remote.origin.receivepack', 'git-receive-pack')

    def setup_restack_replayed_recurse_on_demand(self) -> None:
        self.setup_restack_replayed()
        self.set_config('push.recurseSubmodules', 'on-demand')

    def setup_pull_upload_pack(self) -> None:
        self.setup_push_feature()
        self.set_config('remote.origin.uploadpack', 'git-upload-pack')

    def setup_pull_backup_upload_pack(self) -> None:
        self.setup_push_backup()
        self.set_config('remote.backup.uploadpack', 'git-upload-pack')

    def setup_restack_replayed_backup_receive_pack(self) -> None:
        self.setup_restack_replayed()
        self.add_remote('backup', ('main',), None)
        self.set_config('remote.backup.receivepack', 'git-receive-pack')


SIBLING_GIT_DIR = "'../project one/.git'"

RESOLUTION_GAP_CASES: tuple[DecisionCase, ...] = (
    # A refspec splits at its last colon: the source may hold colons, the destination cannot.
    DecisionCase('source_with_a_colon_onto_main_needs_owner_approval', "git push origin 'HEAD^{/fix:}:main'",
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('message_search_source_onto_main_needs_owner_approval', "git push origin ':/fix:main'",
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('forced_source_with_a_colon_onto_main_needs_owner_approval',
                 "git push origin '+HEAD^{/fix:}:main'", 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('refspec_with_several_colons_onto_main_needs_owner_approval', "git push origin 'a:b:main'",
                 'ask', PROTECTED, 'R16', setup='push-feature'),
    DecisionCase('message_search_source_onto_a_feature_is_allowed', "git push origin ':/fix:feat/x'",
                 'allow', setup='push-feature'),
    DecisionCase('forced_message_search_source_onto_a_feature_needs_owner_approval',
                 "git push origin '+:/fix:feat/x'", 'ask', FORCE, 'R17', setup='push-feature'),
    DecisionCase('source_with_a_colon_onto_a_feature_is_allowed', "git push origin 'HEAD^{/fix:}:feat/x'",
                 'allow', setup='push-feature'),
    DecisionCase('empty_source_still_deletes', 'git push origin :feat/x', 'ask', DELETE, 'R15',
                 setup='push-feature'),
    DecisionCase('lone_colon_still_pushes_matching_refs', 'git push origin :', 'ask', BULK, 'R14',
                 setup='push-feature'),
    DecisionCase('tag_source_onto_a_tag_still_asks', 'git push origin v1:refs/tags/v2', 'ask', BULK, 'R14',
                 setup='push-feature'),
    # A partial upstream merge value names refs/<value>.
    DecisionCase('upstream_push_with_a_partial_main_merge_needs_owner_approval', 'git push',
                 'ask', PROTECTED, 'R16', setup='push-upstream-partial-main'),
    DecisionCase('upstream_push_with_a_partial_feature_merge_is_allowed', 'git push', 'allow',
                 setup='push-upstream-partial-feature'),
    # pull --upload-pack runs a program on the fetch side.
    DecisionCase('pull_upload_pack_is_unsupported', 'git pull --upload-pack=x origin', 'deny', UNSUPPORTED,
                 setup='push-feature'),
    DecisionCase('pull_upload_pack_as_a_separate_value_is_unsupported', 'git pull --upload-pack x origin',
                 'deny', UNSUPPORTED, setup='push-feature'),
    DecisionCase('pull_upload_pack_prefix_is_unsupported', 'git pull --upload-p=x origin', 'deny', UNSUPPORTED,
                 setup='push-feature'),
    DecisionCase('pull_upload_pack_on_main_is_unsupported', 'git pull --ff-only --upload-pack=x', 'deny',
                 UNSUPPORTED, setup='push'),
    DecisionCase('pull_from_a_remote_with_a_configured_upload_pack_is_unsupported', 'git pull origin', 'deny',
                 UNSUPPORTED, setup='pull-upload-pack'),
    DecisionCase('pull_from_the_default_remote_with_a_configured_upload_pack_is_unsupported', 'git pull',
                 'deny', UNSUPPORTED, setup='pull-upload-pack'),
    DecisionCase('pull_from_origin_ignores_another_remote_upload_pack', 'git pull origin', 'allow',
                 setup='pull-backup-upload-pack'),
    # A rebasing pull with rebase.updateRefs may move other branches, protected ones included.
    DecisionCase('pull_rebase_with_update_refs_needs_owner_approval', 'git pull --rebase', 'ask', REWRITE, 'R28',
                 setup='pull-update-refs'),
    DecisionCase('pull_short_rebase_with_update_refs_needs_owner_approval', 'git pull -r', 'ask', REWRITE, 'R28',
                 setup='pull-update-refs'),
    DecisionCase('pull_bundled_rebase_with_update_refs_needs_owner_approval', 'git pull -qr', 'ask', REWRITE, 'R28',
                 setup='pull-update-refs'),
    DecisionCase('pull_rebase_merges_with_update_refs_needs_owner_approval', 'git pull --rebase=merges origin',
                 'ask', REWRITE, 'R28', setup='pull-update-refs'),
    DecisionCase('pull_with_configured_rebase_and_update_refs_needs_owner_approval', 'git pull', 'ask', REWRITE, 'R28',
                 setup='pull-configured-rebase'),
    DecisionCase('pull_with_branch_rebase_and_update_refs_needs_owner_approval', 'git pull', 'ask', REWRITE, 'R28',
                 setup='pull-branch-rebase'),
    DecisionCase('pull_rebase_without_update_refs_is_allowed', 'git pull --rebase', 'allow', setup='push-feature'),
    DecisionCase('pull_rebase_with_update_refs_false_is_allowed', 'git pull --rebase', 'allow',
                 setup='pull-update-refs-false'),
    DecisionCase('pull_without_rebase_and_with_update_refs_is_allowed', 'git pull', 'allow',
                 setup='pull-update-refs'),
    DecisionCase('pull_no_rebase_overrides_configured_rebase', 'git pull --no-rebase', 'allow',
                 setup='pull-configured-rebase'),
    DecisionCase('pull_rebase_false_overrides_configured_rebase', 'git pull --rebase=false', 'allow',
                 setup='pull-configured-rebase'),
    DecisionCase('pull_branch_rebase_off_overrides_configured_rebase', 'git pull', 'allow',
                 setup='pull-branch-rebase-off'),
    DecisionCase('pull_fast_forward_only_with_configured_rebase_is_allowed', 'git pull --ff-only', 'allow',
                 setup='pull-configured-rebase'),
    DecisionCase('pull_with_configured_rebase_without_update_refs_is_allowed', 'git pull', 'allow',
                 setup='pull-configured-rebase-without-update-refs'),
    # Configuration of the target remote and of submodule recursion runs programs on push.
    DecisionCase('push_with_a_configured_receive_pack_is_unsupported', 'git push origin feat/x', 'deny',
                 UNSUPPORTED, setup='push-receive-pack'),
    DecisionCase('push_to_origin_ignores_another_remote_receive_pack', 'git push origin feat/x',
                 'allow', setup='push-backup-receive-pack'),
    DecisionCase('dry_run_with_a_configured_receive_pack_is_unsupported', 'git push -n origin feat/x', 'deny',
                 UNSUPPORTED, setup='push-receive-pack'),
    DecisionCase('push_with_configured_on_demand_submodules_is_unsupported', 'git push origin feat/x', 'deny',
                 UNSUPPORTED, setup='push-recurse-on-demand'),
    DecisionCase('push_with_configured_submodules_only_is_unsupported', 'git push origin feat/x', 'deny',
                 UNSUPPORTED, setup='push-recurse-only'),
    DecisionCase('push_with_submodule_recurse_is_unsupported', 'git push origin feat/x', 'deny', UNSUPPORTED,
                 setup='push-submodule-recurse'),
    DecisionCase('submodule_check_option_overrides_configured_on_demand',
                 'git push --recurse-submodules=check origin feat/x', 'allow', setup='push-recurse-on-demand'),
    DecisionCase('no_submodules_option_overrides_configured_on_demand',
                 'git push --no-recurse-submodules origin feat/x', 'allow', setup='push-recurse-on-demand'),
    DecisionCase('push_with_configured_submodule_check_is_allowed', 'git push origin feat/x', 'allow',
                 setup='push-recurse-check'),
    DecisionCase('push_with_submodule_recurse_off_is_allowed', 'git push origin feat/x', 'allow',
                 setup='push-submodule-recurse-off'),
    # A relative redirect is resolved against the directory git runs in.
    DecisionCase('relative_git_dir_into_project_from_a_sibling_is_unsupported',
                 f'git --git-dir={SIBLING_GIT_DIR} push -f', 'deny', UNSUPPORTED, 'R31', cwd='outside'),
    DecisionCase('separate_relative_git_dir_into_project_from_a_sibling_is_unsupported',
                 f'git --git-dir {SIBLING_GIT_DIR} push -f', 'deny', UNSUPPORTED, 'R31', cwd='outside'),
    DecisionCase('relative_work_tree_into_project_from_a_sibling_is_unsupported',
                 "git --work-tree='../project one' add -A", 'deny', UNSUPPORTED, 'R31', cwd='outside'),
    DecisionCase('relative_git_dir_after_relative_directory_option_is_unsupported',
                 "git -C .. --git-dir='project one/.git' push -f", 'deny', UNSUPPORTED, 'R31', cwd='outside'),
    DecisionCase('relative_git_dir_assignment_from_a_sibling_is_opaque_environment',
                 f'GIT_DIR={SIBLING_GIT_DIR} git push -f', 'deny', 'opaque-environment', 'R31', cwd='outside'),
    DecisionCase('relative_work_tree_assignment_from_a_sibling_is_opaque_environment',
                 "GIT_WORK_TREE='../project one' git add -A", 'deny', 'opaque-environment', 'R31',
                 cwd='outside'),
    DecisionCase('relative_common_dir_assignment_from_a_sibling_is_opaque_environment',
                 f'GIT_COMMON_DIR={SIBLING_GIT_DIR} git push -f', 'deny', 'opaque-environment', 'R31',
                 cwd='outside'),
    DecisionCase('relative_index_file_assignment_from_a_sibling_is_opaque_environment',
                 "GIT_INDEX_FILE='../project one/.git/index' git add -A", 'deny', 'opaque-environment', 'R31',
                 cwd='outside'),
    DecisionCase('relative_git_dir_assignment_before_a_directory_option_is_opaque_environment',
                 "GIT_DIR='project one/.git' git -C .. push -f", 'deny', 'opaque-environment', 'R31',
                 cwd='outside'),
    DecisionCase('exported_relative_git_dir_from_a_sibling_is_opaque_environment',
                 f'export GIT_DIR={SIBLING_GIT_DIR}; git push -f', 'deny', 'opaque-environment', 'R31',
                 cwd='outside'),
    DecisionCase('relative_git_dir_of_the_sibling_itself_stays_not_applicable', 'git --git-dir=.git push -f',
                 'not_applicable', cwd='outside'),
    DecisionCase('relative_git_dir_assignment_of_the_sibling_itself_stays_not_applicable',
                 'GIT_DIR=.git git push -f', 'not_applicable', cwd='outside'),
    DecisionCase('relative_git_dir_assignment_on_read_only_git_stays_not_applicable',
                 f'GIT_DIR={SIBLING_GIT_DIR} git status', 'not_applicable', cwd='outside'),
    # A shell option before the command string leaves the string unparsed.
    DecisionCase('shell_option_before_the_command_string_is_unsupported', "bash -o pipefail -c 'git push -f'",
                 'deny', UNSUPPORTED),
    DecisionCase('bundled_shell_options_before_the_command_string_are_unsupported',
                 "bash -eo pipefail -c 'git push -f'", 'deny', UNSUPPORTED),
)

RESOLUTION_GAP_JOURNAL_CASES: tuple[RestackCase, ...] = (
    RestackCase('lease_push_with_a_configured_receive_pack_is_unsupported', PUSH_A, 'deny', UNSUPPORTED,
                setup='restack-replayed-receive-pack'),
    RestackCase('lease_push_with_configured_on_demand_submodules_is_unsupported', PUSH_A, 'deny', UNSUPPORTED,
                setup='restack-replayed-recurse-on-demand'),
    RestackCase('long_force_with_a_valid_journal_names_the_forced_check',
                'git push --force --force-with-lease=refs/heads/feat/a:{a_remote} origin feat/a',
                'ask', FORCE_DEFAULT, 'R17', 'forced', setup='restack-replayed'),
    RestackCase('forced_refspec_with_a_valid_journal_names_the_forced_check',
                'git push --force-with-lease=refs/heads/feat/a:{a_remote} origin +feat/a',
                'ask', FORCE_DEFAULT, 'R17', 'forced', setup='restack-replayed'),
    push_row('lease_push_with_another_remote_receive_pack_is_allowed', PUSH_A, None,
             setup='restack-replayed-backup-receive-pack'),
)


class ResolutionGapTable(ResolutionGapFixture):
    """Table-driven decisions for refspec splitting, pull programs, rebasing pulls, configured
    push programs, relative redirects, shell options and the forced-lease diagnostic."""


for gap_case in RESOLUTION_GAP_CASES:
    setattr(ResolutionGapTable, 'test_' + gap_case.name, decision_test(gap_case))
for gap_journal_case in RESOLUTION_GAP_JOURNAL_CASES:
    setattr(ResolutionGapTable, 'test_' + gap_journal_case.name, restack_test(gap_journal_case))

CLASSES = (*CLASSES, ResolutionGapTable)


class RefspecSplitting(PushFixture):
    """split_refspec reads `[+]<src>[:<dst>]` with the destination after the last colon."""

    def split(self, text: str) -> Any:
        state = self.api('PushState')({}, 'feat/x')
        return self.api('split_refspec')(text, state)

    def test_destination_follows_the_last_colon(self) -> None:
        for text, source, destination in (('HEAD^{/fix:}:main', 'HEAD^{/fix:}', 'main'),
                                          (':/fix:main', ':/fix', 'main'),
                                          ('a:b:refs/heads/main', 'a:b', 'refs/heads/main'),
                                          ('+:/x:y:feat/x', ':/x:y', 'feat/x')):
            with self.subTest(text=text):
                spec = self.split(text)
                self.assertEqual((spec.forced, spec.source, spec.destination),
                                 (text.startswith('+'), source, destination))

    def test_deletion_and_matching_forms_are_kept(self) -> None:
        deletion, matching, forced = self.split(':feat/x'), self.split(':'), self.split('+:')
        self.assertEqual((deletion.deletion, deletion.destination), (True, 'feat/x'))
        self.assertTrue(matching.matching)
        self.assertEqual((forced.forced, forced.matching), (True, True))

    def test_source_with_a_colon_and_no_destination_is_unresolved(self) -> None:
        self.assertIsNone(self.split(':/fix:'))


CLASSES = (*CLASSES, RefspecSplitting)


# bash and dash give one following word to every o or O in a short option bundle, wherever
# it sits; an R16 lease ask names the protected-destination check whichever journal check
# fails first; a failed cd keeps --git-dir and --work-tree values pointing back in.
FORCED_ONTO_MAIN = "'git push -f origin feat/y:main'"

SHELL_BUNDLE_CASES: tuple[DecisionCase, ...] = (
    DecisionCase('shell_value_option_first_in_a_bundle_is_unsupported',
                 f'bash -oe pipefail -c {FORCED_ONTO_MAIN}', 'deny', UNSUPPORTED, setup='push-feature'),
    DecisionCase('sh_value_option_first_in_a_bundle_is_unsupported',
                 f'sh -oe pipefail -c {FORCED_ONTO_MAIN}', 'deny', UNSUPPORTED, setup='push-feature'),
    DecisionCase('shell_value_option_inside_a_longer_bundle_is_unsupported',
                 f'bash -oex pipefail -c {FORCED_ONTO_MAIN}', 'deny', UNSUPPORTED, setup='push-feature'),
    DecisionCase('shell_option_name_first_in_a_bundle_is_unsupported',
                 f'bash -Oe extglob -c {FORCED_ONTO_MAIN}', 'deny', UNSUPPORTED, setup='push-feature'),
    DecisionCase('two_shell_value_options_in_one_bundle_are_unsupported',
                 f'bash -oo pipefail errexit -c {FORCED_ONTO_MAIN}', 'deny', UNSUPPORTED, setup='push-feature'),
    DecisionCase('stdin_shell_after_a_value_option_first_in_a_bundle_is_unsupported',
                 "echo 'git push -f' | bash -oe pipefail", 'deny', UNSUPPORTED, setup='push-feature'),
    DecisionCase('shell_option_before_a_read_only_command_string_stays_unsupported',
                 "bash -e -c 'git status'", 'deny', UNSUPPORTED),
    DecisionCase('shell_script_after_a_bundled_value_option_is_not_applicable',
                 'bash -oe pipefail build.sh', 'not_applicable'),
    # A failed cd leaves the shell where it was, so repository redirects still point back in.
    DecisionCase('absolute_git_dir_after_a_failed_cd_from_a_sibling_is_unsupported',
                 'cd /nonexistent-rails-dir; git --git-dir=@project@/.git push -f', 'deny', UNSUPPORTED,
                 cwd='outside'),
    DecisionCase('relative_git_dir_after_a_failed_cd_from_a_sibling_is_unsupported',
                 f'cd /nonexistent-rails-dir; git --git-dir={SIBLING_GIT_DIR} push -f', 'deny', UNSUPPORTED,
                 cwd='outside'),
)

PROTECTED_LEASE_CASES: tuple[RestackCase, ...] = (
    RestackCase('protected_destination_outside_the_journal_order_names_the_protected_check',
                'git push --force-with-lease=refs/heads/main:{a_base} origin main', 'ask', PROTECTED, 'R16',
                'branch-protected', setup='restack-replayed'),
)


class ShellBundleTable(ResolutionGapFixture):
    """Table-driven decisions for bundled shell value options, protected lease destinations
    and repository redirects after a failed cd."""


for bundle_case in SHELL_BUNDLE_CASES:
    setattr(ShellBundleTable, 'test_' + bundle_case.name, decision_test(bundle_case))
for protected_lease_case in PROTECTED_LEASE_CASES:
    setattr(ShellBundleTable, 'test_' + protected_lease_case.name, restack_test(protected_lease_case))

CLASSES = (*CLASSES, ShellBundleTable)


# ── Hook entrypoint: stdin to exit status, stdout and stderr ───────────

import atexit  # noqa: E402 - the entrypoint block needs these only
import re  # noqa: E402
import signal  # noqa: E402
from typing import Mapping  # noqa: E402

HOOK_PATH = SOURCE / 'hooks/git-rails.sh'
CAPABILITIES_PATH = SOURCE / 'harness/claude/capabilities.md'
BASH = shutil.which('bash') or '/bin/bash'
HOOK_TIMEOUT = 30.0
STDIN_LIMIT = 1024 * 1024
COMMAND_LIMIT = 64 * 1024
DIAGNOSTIC_LIMIT = 1024
FAULT_VARIABLE = 'ORCHESTRAIL_GIT_RAILS_FAULT'
ASK_PREFIX = ('{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask",'
              '"permissionDecisionReason":')
NO_RULE = 'none'
MISSING = object()
RELEVANT = re.compile(r'(^|[^A-Za-z0-9_.-])(git|gh)([^A-Za-z0-9_.-]|$)')
PIPELINE_IDENTIFIER = re.compile(r'\bT-\d{2}[a-z]?\b|\bADR-\d{4}\b|\.ai/')
SPEC_REASON_CODES = (
    'blanket-staging', 'staging-not-file', 'staging-ignored-path', 'commit-all',
    'commit-message-unverifiable', 'commit-message-forbidden', 'rewrite-published',
    'push-target-unknown', 'default-branch-unknown', 'push-bulk-or-tags', 'push-delete',
    'push-protected-target', 'push-force', 'push-lease-unverified', 'reset-hard', 'clean',
    'branch-delete', 'protected-ref-rewrite', 'rebase-outside-restack', 'merge-into-protected',
    'pr-merge', 'opaque-environment', 'unsupported-form', 'malformed-input', 'registry-error',
    'runtime-unavailable', 'limit-exceeded', 'internal-error', 'owner-approval-unavailable')
TOOLS: dict[str, str] = {}


@dataclass(frozen=True)
class HookRun:
    """One run of the entrypoint: exit status, raw stdout and stderr, and wall time."""
    status: int
    stdout: bytes
    stderr: bytes
    elapsed: float

    @property
    def output(self) -> tuple[int, bytes, bytes]:
        return self.status, self.stdout, self.stderr


@dataclass(frozen=True)
class Expected:
    """The harness-visible result one hook run must produce."""
    decision: str
    reason: str | None = None
    rule: str | None = None
    failure: str | None = None


def run_hook(payload: bytes, environ: Mapping[str, str], cwd: Path) -> HookRun:
    started = time.monotonic()
    try:
        result = subprocess.run([BASH, str(HOOK_PATH)], input=payload, capture_output=True,
                                env=dict(environ), cwd=cwd, timeout=HOOK_TIMEOUT)
    except subprocess.TimeoutExpired:
        return HookRun(-1, b'', b'the hook did not finish', HOOK_TIMEOUT)
    return HookRun(result.returncode, result.stdout, result.stderr, time.monotonic() - started)


def encode_event(event: object) -> bytes:
    """The event as the harness sends it: UTF-8 JSON with non-ASCII text unescaped."""
    return json.dumps(event, ensure_ascii=False).encode('utf-8')


def link_programs(directory: Path, target: Path) -> None:
    if not directory.is_dir():
        return
    for program in sorted(directory.iterdir()):
        link = target / program.name
        if program.name.startswith('python') or link.exists() or link.is_symlink():
            continue
        if program.is_file() and os.access(program, os.X_OK):
            link.symlink_to(program)


def python_free_path() -> str:
    """One directory linking every program on the current PATH except Python."""
    if 'path' not in TOOLS:
        root = Path(os.path.realpath(tempfile.mkdtemp(prefix='entry tools ')))
        atexit.register(shutil.rmtree, root, True)
        for directory in os.environ.get('PATH', '/usr/bin:/bin').split(os.pathsep):
            link_programs(Path(directory), root)
        TOOLS['path'] = str(root)
    return TOOLS['path']


def ask_capable_modes() -> tuple[str, ...]:
    """The anchored allowlist line of the Claude capability record."""
    prefix = 'git-rails ask-capable modes: '
    for line in CAPABILITIES_PATH.read_text(encoding='utf-8').splitlines():
        if line.startswith(prefix):
            return tuple(line[len(prefix):].split(', '))
    return ()


def registry_location(environ: Mapping[str, str]) -> str:
    base = environ.get('XDG_CONFIG_HOME') or os.path.join(environ.get('HOME', ''), '.config')
    return os.path.join(base, 'orchestrail', 'projects')


def harness_result(result: Any, event: object) -> Expected:
    """What the adapter must emit for a core decision: an ask outside the allowlist denies."""
    mode = event.get('permission_mode') if isinstance(event, dict) else None
    failure = getattr(result, 'failure', None)
    if result.decision == 'ask' and mode not in ask_capable_modes():
        return Expected('deny', 'owner-approval-unavailable', result.rule_id, failure)
    return Expected(result.decision, result.reason_code, result.rule_id, failure)


def sized_command(size: int, filler: str = 'x') -> str:
    """A staging command padded with one quoted echo word to at most size UTF-8 bytes."""
    head = "git add a.txt; echo '"
    count = (size - len(head.encode()) - 1) // len(filler.encode())
    return head + filler * count + "'"


def kill_recorded(pidfile: Path) -> None:
    try:
        os.kill(int(pidfile.read_text().strip()), signal.SIGKILL)
    except (OSError, ValueError):
        pass


class EntrypointChecks(RailsFixture):
    """Runs events through hooks/git-rails.sh twice and checks the harness protocol of the
    output against the core decision for the same event and environment."""

    def payload(self, command: str, cwd: str | None = None, mode: str = 'default') -> bytes:
        return encode_event(self.event(self.render(command), cwd or self.location('project'), mode))

    def hook_once(self, payload: bytes, environ: Mapping[str, str] | None = None) -> HookRun:
        run = run_hook(payload, dict(self.environ if environ is None else environ), self.world)
        self.assertNotIn(b'"allow"', run.stdout + run.stderr, 'the hook never emits an allow decision')
        return run

    def hook_twice(self, payload: bytes, environ: Mapping[str, str] | None = None) -> HookRun:
        first = self.hook_once(payload, environ)
        second = self.hook_once(payload, environ)
        self.assertEqual(first.output, second.output, 'the same event and state must give byte-identical output')
        return first

    def diagnostic_text(self, run: HookRun) -> str:
        try:
            text = run.stderr.decode('utf-8')
        except UnicodeDecodeError:
            self.fail('the diagnostic must be valid UTF-8: ' + repr(run.stderr[-200:]))
        self.assertTrue(text.endswith('\n'), 'stderr carries the diagnostic and one newline: ' + text[-300:])
        return text[:-1]

    def assert_diagnostic(self, text: str, expected: Expected) -> list[str]:
        verb = 'ask' if expected.decision == 'ask' else 'deny'
        self.assertLessEqual(len(text.encode('utf-8')), DIAGNOSTIC_LIMIT, text)
        lines = text.split('\n')
        self.assertEqual(len(lines), 4, text)
        self.assertEqual(lines[0], f'git-rails: {verb} {expected.reason} ({expected.rule or NO_RULE})')
        self.assertEqual(lines[1], 'rule: ' + RULE_PATH_TEXT)
        self.assertRegex(lines[2], r'^operation: \S')
        self.assertTrue(lines[3].startswith('next: '), text)
        if expected.failure is None:
            self.assertNotIn('failed check:', text)
        else:
            self.assertIn('failed check: ' + expected.failure, lines[2])
        return lines

    def next_step(self, reason: str, environ: Mapping[str, str]) -> str:
        if reason == 'registry-error':
            return 'fix or remove the invalid line in ' + registry_location(environ)
        return self.api('NEXT_STEPS')[reason]

    def assert_protocol(self, run: HookRun, expected: Expected,
                        environ: Mapping[str, str] | None = None) -> list[str]:
        environment = self.environ if environ is None else environ
        if expected.decision in ('allow', 'not_applicable'):
            self.assertEqual(run.output, (0, b'', b''), 'allow and not_applicable exit 0 without output')
            return []
        self.assertEqual(run.status, 2 if expected.decision == 'deny' else 0, run.stderr[-400:])
        text = self.diagnostic_text(run)
        if expected.decision == 'deny':
            self.assertEqual(run.stdout, b'', 'deny writes nothing to stdout')
        else:
            self.assertEqual(run.stdout.decode('utf-8'), ASK_PREFIX + json.dumps(text, ensure_ascii=False) + '}}')
        lines = self.assert_diagnostic(text, expected)
        self.assertEqual(lines[3], 'next: ' + self.next_step(str(expected.reason), environment))
        return lines

    def through_hook(self, event: object, environ: Mapping[str, str] | None = None) -> Any:
        """One hook run checked against the core: determinism is shown by two equal in-process
        decisions and a hook output byte-identical to the in-process adapter rendering."""
        environment = dict(self.environ if environ is None else environ)
        before = snapshot(self.world)
        decide = self.api('decide')
        result = decide(event, dict(environment))
        self.assertEqual(result, decide(event, dict(environment)), 'the core decides one event the same way twice')
        run = self.hook_once(encode_event(event), environment)
        self.assertEqual(before, snapshot(self.world),
                         'deciding through the hook must leave .git, the work tree, .ai and the registry unchanged')
        self.assert_protocol(run, harness_result(result, event), environment)
        rendered = tuple(self.api('respond')(result, event, dict(environment)))
        self.assertEqual(run.output, rendered, 'the hook output is the adapter rendering of the core decision')
        return result

    def decide(self, event: object, environ: dict[str, str] | None = None) -> tuple[str, str | None, str | None]:
        result = self.through_hook(event, environ)
        return result.decision, result.reason_code, result.rule_id

    def outcome(self, command: str, cwd: str = 'project',
                environ: dict[str, str] | None = None) -> tuple[str, str | None, str | None, object]:
        result = self.through_hook(self.event(command, self.location(cwd)), environ)
        return result.decision, result.reason_code, result.rule_id, getattr(result, 'failure', NO_FAILURE_FIELD)


# Every existing decision table also runs end to end through the entrypoint.
ENTRYPOINT_TABLES = (DecisionTable, FailClosedTable, DecidedTable, StagingTable, CommitTable, StateChangeTable,
                     PushTable, OperationTable, SymbolicBranchTable, RestackJournalTable, UpdateRefsTable,
                     ValidationRepairTable)
ENTRYPOINT_TABLE_CLASSES = tuple(
    type(table.__name__ + 'ThroughHook', (EntrypointChecks, table),
         {'__doc__': f'Every {table.__name__} case, run twice through the hook entrypoint.'})
    for table in ENTRYPOINT_TABLES)


class EntrypointFixture(EntrypointChecks, OperationFixture, RuleFixture):
    """Push, operation and rule repository states, plus a registered work tree whose path
    holds no git or gh word, so the relevance prefilter sees only the command."""
    clean: Path

    def setUp(self) -> None:
        super().setUp()
        scratch = tempfile.TemporaryDirectory(prefix='entry ')
        self.addCleanup(scratch.cleanup)
        self.clean = Path(os.path.realpath(scratch.name)) / 'work'
        if RELEVANT.search(str(self.clean)):
            self.skipTest('the temporary directory path contains a git or gh word')
        self.make_repository(self.clean, {'a.txt': 'a\n'})
        self.write_registry([self.project, self.plain, self.clean])

    def location(self, key: str) -> str:
        return str(self.clean) if key == 'clean' else super().location(key)

    def without_python(self, environ: Mapping[str, str] | None = None) -> dict[str, str]:
        return {**(self.environ if environ is None else environ), 'PATH': python_free_path()}

    def fake_git(self, script: str) -> None:
        fake = self.probe / 'bin/git'
        fake.write_text('#!/bin/bash\n' + script + f'exec {shlex.quote(REAL_GIT)} "$@"\n')
        fake.chmod(0o755)
        self.environ['PATH'] = f'{self.probe / "bin"}{os.pathsep}{self.environ["PATH"]}'

    def expect(self, command: str, expected: Expected, environ: Mapping[str, str] | None = None) -> list[str]:
        return self.assert_protocol(self.hook_twice(self.payload(command), environ), expected, environ)

    def padded(self, command: str, size: int) -> bytes:
        """An event for the project whose encoded size is exactly size bytes."""
        event = self.event(command, self.location('project'))
        base = len(encode_event(event))
        event['tool_input'] = {'command': command, 'description': 'fixture' + 'x' * (size - base)}
        payload = encode_event(event)
        self.assertEqual(len(payload), size)
        return payload


class EntrypointFastPath(EntrypointFixture):
    """Steps before Python: bounded read, registry gate, relevance prefilter, runtime check."""

    def test_missing_registry_exits_silently_without_python(self) -> None:
        self.registry.unlink()
        for command in ('git push -f', 'git reset --hard', 'gh pr merge 1', 'git add -A'):
            with self.subTest(command=command):
                run = self.hook_twice(self.payload(command), self.without_python())
                self.assertEqual(run.output, (0, b'', b''))

    def test_command_without_git_word_exits_silently_without_python(self) -> None:
        for command in ('ls -la', 'bash hooks/git-rails.sh', 'cat .git/config', 'curl https://github.com/o/r',
                        'echo legit digits ghost gh-pages git_x .gh', ''):
            with self.subTest(command=command):
                run = self.hook_twice(self.payload(command, self.location('clean')), self.without_python())
                self.assertEqual(run.output, (0, b'', b''))

    def test_git_word_reaches_the_runtime_check_without_python(self) -> None:
        environ = self.without_python()
        for command in ('git status', 'gh pr view 1', 'ls; git status', '(git status)', 'X=1 git status',
                        '\\git status', 'echo "$(gh pr view 1)"'):
            with self.subTest(command=command):
                run = self.hook_twice(self.payload(command, self.location('clean')), environ)
                self.assert_protocol(run, Expected('deny', 'runtime-unavailable'), environ)

    def test_json_escaped_separators_before_a_git_word_reach_the_core(self) -> None:
        environ = self.without_python()
        for command in ('true\ngit status', 'true;\tgit status', 'true\n\ngh pr view 1', 'true\r\ngit status',
                        'true;\x1bgit status', 'true\f\bgh pr view 1'):
            with self.subTest(command=command):
                run = self.hook_twice(self.payload(command, self.location('clean')), environ)
                self.assert_protocol(run, Expected('deny', 'runtime-unavailable'), environ)
        decision = self.decide(self.event('true\ngit add -A', self.location('clean')))
        self.assertEqual(decision, ('deny', 'blanket-staging', 'R01'))

    def test_missing_python_denies_in_any_directory_while_a_registry_exists(self) -> None:
        environ = self.without_python()
        run = self.hook_twice(self.payload('git push -f', self.location('outside')), environ)
        self.assert_protocol(run, Expected('deny', 'runtime-unavailable'), environ)

    def test_python_older_than_3_11_is_runtime_unavailable(self) -> None:
        shim_directory = self.probe / 'old python'
        shim_directory.mkdir()
        log = self.probe / 'old-python.log'
        shim = shim_directory / 'python3'
        shim.write_text('#!/bin/sh\n'
                        f'printf "%s\\n" "$*" >> {shlex.quote(str(log))}\n'
                        'case "$1" in --version|-V) echo "Python 3.10.12"; exit 0 ;; esac\n'
                        'exit 1\n')
        shim.chmod(0o755)
        environ = {**self.environ, 'PATH': f'{shim_directory}{os.pathsep}{python_free_path()}'}
        run = self.hook_twice(self.payload('git add a.txt'), environ)
        self.assert_protocol(run, Expected('deny', 'runtime-unavailable'), environ)
        calls = log.read_text() if log.exists() else ''
        self.assertNotIn('git_rails.py', calls, 'an interpreter older than 3.11 never runs the core')

    def test_core_runs_isolated_from_python_environment_variables(self) -> None:
        planted = self.probe / 'planted'
        planted.mkdir()
        marker = self.probe / 'planted-module-ran'
        body = f'open({str(marker)!r}, "w").close()\nraise SystemExit(0)\n'
        for name in ('sitecustomize.py', 'usercustomize.py', 'json.py', 're.py', 'dataclasses.py'):
            (planted / name).write_text(body)
        environ = {**self.environ, 'PYTHONPATH': str(planted), 'PYTHONHOME': str(planted),
                   'PYTHONSTARTUP': str(planted / 'json.py')}
        self.assertEqual(self.decide(self.event('git add -A', self.location('project')), environ),
                         ('deny', 'blanket-staging', 'R01'))
        self.assertFalse(marker.exists(), 'a module from the hook environment ran inside the hook')

    def test_entrypoint_is_a_strict_bash_script_with_a_header(self) -> None:
        self.assertTrue(HOOK_PATH.is_file(), 'hooks/git-rails.sh must exist')
        text = HOOK_PATH.read_text(encoding='utf-8')
        lines = text.splitlines()
        self.assertIn(lines[0], ('#!/usr/bin/env bash', '#!/bin/bash'))
        header: list[str] = []
        for line in lines[1:]:
            if not line.startswith('#'):
                break
            header.append(line.lower())
        for word in ('contract', 'usage', 'exit'):
            self.assertIn(word, '\n'.join(header), 'the header comment names the ' + word)
        self.assertIn('set -uo pipefail', lines)
        self.assertNotRegex(text, r'\bjq\b')
        self.assertNotIn(RULE_PATH_TEXT, text, 'the rule line is read from the core constant, not copied')
        self.assertNotRegex(text, PIPELINE_IDENTIFIER)
        checked = subprocess.run([BASH, '-n', str(HOOK_PATH)], capture_output=True, text=True)
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_hook_writes_nothing(self) -> None:
        self.setup_push()
        hooks = SOURCE / 'hooks'
        before = (snapshot(hooks), snapshot(self.world), snapshot(self.clean))
        for command, expected in (('git add a.txt', Expected('allow')),
                                  ('git add -A', Expected('deny', 'blanket-staging', 'R01')),
                                  ('git push origin main', Expected('ask', 'push-protected-target', 'R16')),
                                  ('ls', Expected('not_applicable'))):
            self.expect(command, expected)
        environ = self.without_python()
        run = self.hook_twice(self.payload('git status', self.location('clean')), environ)
        self.assert_protocol(run, Expected('deny', 'runtime-unavailable'), environ)
        self.assertEqual(before, (snapshot(hooks), snapshot(self.world), snapshot(self.clean)))


class EntrypointProtocol(EntrypointFixture):
    """Decision mapping of the harness protocol and the owner-approval allowlist."""

    def test_ask_reaches_the_owner_only_in_ask_capable_modes(self) -> None:
        allowed = ask_capable_modes()
        self.assertEqual(sorted(allowed), ['auto', 'default'])
        for mode in allowed:
            with self.subTest(mode=mode):
                self.assert_protocol(self.hook_twice(self.payload('git reset --hard', mode=mode)),
                                     Expected('ask', 'reset-hard', 'R20'))
        for other in ('plan', 'acceptEdits', 'dontAsk', 'bypassPermissions', 'manual', 'Default', '', 7, None,
                      MISSING):
            with self.subTest(mode=other if other is not MISSING else '<missing>'):
                event = self.event('git reset --hard', self.location('project'))
                if other is MISSING:
                    event.pop('permission_mode')
                else:
                    event['permission_mode'] = other
                self.assert_protocol(self.hook_twice(encode_event(event)),
                                     Expected('deny', 'owner-approval-unavailable', 'R20'))

    def test_deny_and_allow_do_not_depend_on_the_permission_mode(self) -> None:
        for mode in ('bypassPermissions', 'dontAsk', 'plan'):
            with self.subTest(mode=mode):
                self.assert_protocol(self.hook_twice(self.payload('git add -A', mode=mode)),
                                     Expected('deny', 'blanket-staging', 'R01'))
                self.assert_protocol(self.hook_twice(self.payload('git add a.txt', mode=mode)), Expected('allow'))

    def test_core_ask_modes_equal_the_capability_record(self) -> None:
        modes = tuple(self.api('ASK_CAPABLE_MODES'))
        self.assertTrue(ask_capable_modes(), 'the capability record must carry the allowlist line')
        self.assertEqual(sorted(modes), sorted(ask_capable_modes()))
        self.assertEqual(len(set(modes)), len(modes))

    def test_registered_target_from_unregistered_cwd_is_decided(self) -> None:
        self.setup_push_feature()
        run = self.hook_twice(self.payload('git -C @project@ push -f', self.location('outside')))
        self.assert_protocol(run, Expected('ask', 'push-force', 'R17'))

    def test_operation_names_the_subcommand_refs_and_remote(self) -> None:
        self.setup_push()
        lines = self.expect('git push origin main', Expected('ask', 'push-protected-target', 'R16'))
        self.assertEqual(lines[2], 'operation: git push to refs/heads/main on origin')


@dataclass(frozen=True)
class ReasonCase:
    """One reason code produced end to end. variant: plain, no-python (python3 absent from
    PATH) or fault (the test-only core fault seam set in the hook environment)."""
    reason: str
    command: str
    decision: str
    rule: str | None = None
    setup: str = 'standard'
    mode: str = 'default'
    failure: str | None = None
    raw: bytes | None = None
    variant: str = 'plain'


REASON_CASES: tuple[ReasonCase, ...] = (
    ReasonCase('blanket-staging', 'git add -A', 'deny', 'R01'),
    ReasonCase('staging-not-file', 'git add sub', 'deny', 'R02'),
    ReasonCase('staging-ignored-path', 'git add -f .ai/state.md', 'ask', 'R04', setup='ignored-state'),
    ReasonCase('commit-all', 'git commit -am x', 'deny', 'R06'),
    ReasonCase('commit-message-unverifiable', 'git commit', 'deny', 'R08'),
    ReasonCase('commit-message-forbidden', f"git commit -m 'Add parser' -m '{TRAILER}'", 'deny', 'R09'),
    ReasonCase('rewrite-published', 'git commit --amend -m ok', 'ask', 'R10', setup='published'),
    ReasonCase('push-target-unknown', 'git push https://example.invalid/r.git feat/x', 'deny', 'R12',
               setup='push-feature'),
    ReasonCase('default-branch-unknown', 'git push origin feat/x', 'deny', 'R13', setup='push-no-default-head'),
    ReasonCase('push-bulk-or-tags', 'git push --tags', 'ask', 'R14', setup='push-feature'),
    ReasonCase('push-delete', 'git push origin --delete feat/y', 'ask', 'R15', setup='push-feature'),
    ReasonCase('push-protected-target', 'git push origin main', 'ask', 'R16', setup='push'),
    ReasonCase('push-force', 'git push -f origin feat/x', 'ask', 'R17', setup='push-feature'),
    ReasonCase('push-lease-unverified', 'git push --force-with-lease origin feat/x', 'ask', 'R18',
               setup='push-feature', failure='explicit-lease'),
    ReasonCase('reset-hard', 'git reset --hard', 'ask', 'R20'),
    ReasonCase('clean', 'git clean -fd', 'ask', 'R21'),
    ReasonCase('branch-delete', 'git branch -d feat/x', 'ask', 'R22', setup='push'),
    ReasonCase('protected-ref-rewrite', 'git branch -f main', 'ask', 'R24', setup='push-feature'),
    ReasonCase('rebase-outside-restack', 'git rebase main', 'ask', 'R26', failure='journal-missing'),
    ReasonCase('merge-into-protected', 'git merge feat/x', 'ask', 'R27', setup='push'),
    ReasonCase('pr-merge', 'gh pr merge 1', 'ask', 'R29'),
    ReasonCase('opaque-environment', 'GIT_DIR=x git commit -m ok', 'deny', 'R31'),
    ReasonCase('unsupported-form', 'eval "git push"', 'deny'),
    ReasonCase('malformed-input', 'git push', 'deny', raw=b'{"tool_input": {"command": "git push"'),
    ReasonCase('registry-error', 'git status', 'deny', setup='registry-empty-line'),
    ReasonCase('runtime-unavailable', 'git status', 'deny', variant='no-python'),
    ReasonCase('limit-exceeded', TOKENS_OVER_LIMIT, 'deny'),
    ReasonCase('internal-error', 'git add a.txt', 'deny', variant='fault'),
    ReasonCase('owner-approval-unavailable', 'git reset --hard', 'deny', 'R20', mode='bypassPermissions'),
)


def reason_test(case: ReasonCase) -> Callable[[EntrypointFixture], None]:
    def test(self: EntrypointFixture) -> None:
        self.apply_setup(case.setup)
        environ = dict(self.environ)
        if case.variant == 'no-python':
            environ = self.without_python()
        elif case.variant == 'fault':
            environ[FAULT_VARIABLE] = 'exception'
        if case.variant == 'plain' and case.raw is None and case.mode == 'default':
            core = self.api('decide')(self.event(case.command, self.location('project')), dict(environ))
            self.assertEqual((core.decision, core.reason_code, core.rule_id, getattr(core, 'failure', None)),
                             (case.decision, case.reason, case.rule, case.failure), 'core sanity for the example')
        payload = case.raw if case.raw is not None else self.payload(case.command, mode=case.mode)
        run = self.hook_twice(payload, environ)
        self.assert_protocol(run, Expected(case.decision, case.reason, case.rule, case.failure), environ)
    return test


class EntrypointDiagnostics(EntrypointFixture):
    """Four-line diagnostics: one next step per reason code, size limit, no secrets."""

    def test_every_reason_code_has_a_next_step_and_an_end_to_end_case(self) -> None:
        table = self.api('NEXT_STEPS')
        self.assertEqual(len(SPEC_REASON_CODES), 29)
        self.assertEqual(sorted(table), sorted(SPEC_REASON_CODES))
        self.assertEqual(sorted(case.reason for case in REASON_CASES), sorted(SPEC_REASON_CODES))
        for reason, text in table.items():
            with self.subTest(reason=reason):
                self.assertIsInstance(text, str)
                self.assertTrue(text.strip(), 'a next step is one concrete action')
                self.assertNotIn('\n', text)
                self.assertNotIn('\r', text)
                self.assertLessEqual(len(text.encode('utf-8')), 400)
                self.assertNotRegex(text, PIPELINE_IDENTIFIER)

    def test_secrets_never_reach_the_hook_output(self) -> None:
        self.setup_push_feature()
        (self.project / 'secret-msg.txt').write_text('Add parser SECRET-FILE-7f3\n\nRefs T-04\n')
        environ = {**self.environ, 'GH_TOKEN': 'SECRET-HOOK-ENV-91c'}
        cases = ((f"git commit -m 'Subject SECRET-MSG-2a1' -m '{TRAILER}'",
                  Expected('deny', 'commit-message-forbidden', 'R09')),
                 ('git commit -F secret-msg.txt', Expected('deny', 'commit-message-forbidden', 'R09')),
                 ('API_TOKEN=SECRET-ASSIGN-5d2 git push -f origin feat/x', Expected('ask', 'push-force', 'R17')),
                 ('git push https://URLUSER-6b4:SECRET-URL-8e0@example.invalid/r.git feat/x',
                  Expected('deny', 'push-target-unknown', 'R12')))
        for command, expected in cases:
            with self.subTest(command=command):
                run = self.hook_twice(self.payload(command), environ)
                self.assert_protocol(run, expected, environ)
                output = run.stdout + run.stderr
                for secret in (b'SECRET-', b'URLUSER-', b'Co-authored-by', b'T-04', command.encode()):
                    self.assertNotIn(secret, output)

    def test_long_operation_is_truncated_and_keeps_the_next_step(self) -> None:
        self.setup_push()
        refs = ' '.join(f'HEAD:refs/heads/release/{"ü" * 40}-{index}' for index in range(40))
        self.assertEqual(self.decide(self.event('git push origin ' + refs, self.location('project'))),
                         ('ask', 'push-protected-target', 'R16'))

    def test_long_next_step_is_truncated_on_a_character_boundary(self) -> None:
        config = self.world.joinpath(*(['→' * 60, 'é' * 100] * 3))
        registry = config / 'orchestrail/projects'
        registry.parent.mkdir(parents=True)
        registry.write_text('relative/root\n')
        environ = {**self.environ, 'XDG_CONFIG_HOME': str(config)}
        full = 'fix or remove the invalid line in ' + str(registry)
        self.assertGreater(len(full.encode('utf-8')), DIAGNOSTIC_LIMIT)
        run = self.hook_twice(self.payload('git status'), environ)
        self.assertEqual((run.status, run.stdout), (2, b''), run.stderr[-300:])
        lines = self.assert_diagnostic(self.diagnostic_text(run), Expected('deny', 'registry-error'))
        body = lines[3][len('next: '):]
        self.assertLess(len(body), len(full))
        self.assertTrue(full.startswith(body.removesuffix('…')), body)


for reason_case in REASON_CASES:
    setattr(EntrypointDiagnostics, 'test_reason_' + reason_case.reason.replace('-', '_') + '_is_rendered',
            reason_test(reason_case))


class EntrypointFailureModes(EntrypointFixture):
    """Malformed events, registry and runtime failures, core exceptions and time limits."""

    def test_malformed_json_is_malformed_input(self) -> None:
        for payload in (b'{"tool_input": {"command": "git push"', b'git push -f', b'["git push"]',
                        b'{"tool_input": {"command": "git push"}} trailing',
                        b'{"hook_event_name": "PreToolUse", "tool_name": "Bash", '
                        b'"tool_input": {"command": "git push"}, "cwd": "/tmp", "cwd": 7}'):
            with self.subTest(payload=payload):
                self.assert_protocol(self.hook_twice(payload), Expected('deny', 'malformed-input'))

    def test_relative_or_missing_cwd_is_malformed_input(self) -> None:
        relative = self.event('git push -f', 'project one')
        missing = self.event('git push -f', self.location('project'))
        missing.pop('cwd')
        for event in (relative, missing):
            with self.subTest(event=event):
                self.assert_protocol(self.hook_twice(encode_event(event)), Expected('deny', 'malformed-input'))

    def test_non_utf8_input_is_malformed_input(self) -> None:
        payload = self.payload('git add a.txt').replace(b'"fixture"', b'"fix\xfeture"', 1)
        self.assertIn(b'\xfe', payload)
        self.assert_protocol(self.hook_twice(payload), Expected('deny', 'malformed-input'))

    def test_non_bash_tool_is_not_applicable(self) -> None:
        event = self.event('git push -f', self.location('project'))
        event['tool_name'] = 'Edit'
        event['tool_input'] = {'file_path': 'a.txt', 'old_string': 'git push', 'new_string': 'git push -f'}
        self.assertEqual(self.hook_twice(encode_event(event)).output, (0, b'', b''))

    def test_empty_registry_registers_nothing(self) -> None:
        self.registry.write_bytes(b'')
        self.assertEqual(self.hook_twice(self.payload('git push -f')).output, (0, b'', b''))

    def test_unreadable_registry_names_the_registry_path(self) -> None:
        self.setup_registry_unreadable()
        self.expect('git status', Expected('deny', 'registry-error'))

    def test_fifo_registry_is_a_registry_error_without_blocking(self) -> None:
        self.registry.unlink()
        os.mkfifo(self.registry)
        run = self.hook_twice(self.payload('git status'))
        self.assert_protocol(run, Expected('deny', 'registry-error'))
        self.assertLess(run.elapsed, 2.0, 'a registry that is not a regular file must not block the hook')

    def test_missing_python_in_a_registered_directory_is_runtime_unavailable(self) -> None:
        self.expect('git add a.txt', Expected('deny', 'runtime-unavailable'), self.without_python())

    def test_injected_core_exception_is_internal_error(self) -> None:
        environ = {**self.environ, FAULT_VARIABLE: 'exception'}
        for command in ('git add a.txt', 'git status', 'git reset --hard'):
            with self.subTest(command=command):
                self.expect(command, Expected('deny', 'internal-error'), environ)

    def test_fault_seam_cannot_be_triggered_by_event_content(self) -> None:
        command = f'{FAULT_VARIABLE}=exception git add a.txt'
        self.assertEqual(self.decide(self.event(command, self.location('project'))), ('allow', None, None))
        event = self.event('git add a.txt', self.location('project'))
        event[FAULT_VARIABLE] = 'exception'
        event['tool_input'] = {'command': 'git add a.txt', FAULT_VARIABLE: 'exception'}
        self.assertEqual(self.decide(event), ('allow', None, None))

    def test_git_read_timeout_is_limit_exceeded(self) -> None:
        self.fake_git('case " $* " in *" rev-parse "*) sleep 30 ;; esac\n')
        run = run_hook(self.payload('git add a.txt'), self.environ, self.world)
        self.assert_protocol(run, Expected('deny', 'limit-exceeded'))
        self.assertGreaterEqual(run.elapsed, 1.5, 'the read limit is two seconds')
        self.assertLess(run.elapsed, 4.5, 'a timed-out read must be stopped')

    def test_wall_clock_budget_is_limit_exceeded(self) -> None:
        self.fake_git('case " $* " in *" rev-parse "*) sleep 1.5 ;; esac\n')
        run = run_hook(self.payload('git add a.txt; git add b.txt; git add a.txt; git add b.txt'),
                       self.environ, self.world)
        self.assert_protocol(run, Expected('deny', 'limit-exceeded'))
        self.assertGreaterEqual(run.elapsed, 4.5, 'the core budget is five seconds')
        self.assertLess(run.elapsed, 5.9, 'the core stops at its five-second budget')

    def test_timed_out_read_stops_waiting_for_escaped_children(self) -> None:
        setsid = shutil.which('setsid')
        if setsid is None:
            self.skipTest('setsid is not available')
        pidfile = self.probe / 'escaped.pid'
        self.addCleanup(kill_recorded, pidfile)
        self.fake_git(f'case " $* " in *" rev-parse "*) {shlex.quote(setsid)} sleep 6 & '
                      f'echo $! > {shlex.quote(str(pidfile))}; sleep 30 ;; esac\n')
        started = time.monotonic()
        result = self.api('decide')(self.event('git add a.txt', self.location('project')), dict(self.environ))
        elapsed = time.monotonic() - started
        self.assertEqual((result.decision, result.reason_code), ('deny', 'limit-exceeded'))
        self.assertLess(elapsed, 4.5, 'output held open by an escaped child must not extend the read')


class EntrypointLimits(EntrypointFixture):
    """Hook stdin and command size limits."""

    def test_stdin_of_exactly_one_mebibyte_is_decided(self) -> None:
        self.assert_protocol(self.hook_twice(self.padded('git add a.txt', STDIN_LIMIT)), Expected('allow'))
        self.assert_protocol(self.hook_twice(self.padded('git add -A', STDIN_LIMIT)),
                             Expected('deny', 'blanket-staging', 'R01'))

    def test_stdin_over_one_mebibyte_is_malformed_input(self) -> None:
        for size in (STDIN_LIMIT + 1, 3 * STDIN_LIMIT):
            with self.subTest(size=size):
                self.assert_protocol(self.hook_twice(self.padded('git add a.txt', size)),
                                     Expected('deny', 'malformed-input'))

    def test_command_of_exactly_64_kib_is_decided(self) -> None:
        command = sized_command(COMMAND_LIMIT)
        self.assertEqual(len(command.encode('utf-8')), COMMAND_LIMIT)
        self.assertEqual(self.decide(self.event(command, self.location('project'))), ('allow', None, None))

    def test_command_over_64_kib_is_limit_exceeded(self) -> None:
        over = sized_command(COMMAND_LIMIT + 1)
        self.assertEqual(len(over.encode('utf-8')), COMMAND_LIMIT + 1)
        multibyte = sized_command(80000, 'é')
        self.assertLessEqual(len(multibyte), COMMAND_LIMIT, 'the limit counts UTF-8 bytes, not characters')
        for command in (over, multibyte):
            with self.subTest(size=len(command.encode('utf-8'))):
                self.assertEqual(self.decide(self.event(command, self.location('project'))),
                                 ('deny', 'limit-exceeded', None))


class EntrypointIndependence(EntrypointFixture):
    """Task records and test-state values never change a decision; the hook never reads them."""

    def outputs(self) -> list[tuple[int, bytes, bytes]]:
        cases = (('git add a.txt', Expected('allow')), ('git add -A', Expected('deny', 'blanket-staging', 'R01')),
                 ('git reset --hard', Expected('ask', 'reset-hard', 'R20')), ('git commit -m ok', Expected('allow')),
                 ('git push -f', Expected('deny', 'push-target-unknown', 'R12')),
                 ('git status', Expected('not_applicable')))
        runs = [self.hook_twice(self.payload(command)) for command, _ in cases]
        for run, (_, expected) in zip(runs, cases):
            self.assert_protocol(run, expected)
        return [run.output for run in runs]

    def test_task_records_and_test_states_do_not_change_decisions(self) -> None:
        baseline = self.outputs()
        tasks = self.project / '.ai/tasks/todo/task-example'
        tasks.mkdir(parents=True)
        (tasks / 'state.md').write_text('example | atomic-tests: red | atomic-execution: not-started\n')
        self.assertEqual(self.outputs(), baseline, 'adding task records')
        (tasks / 'state.md').write_text('example | atomic-tests: green | atomic-execution: complete\n')
        (self.project / '.ai/state.md').write_text('atomic-tests: green\n')
        self.assertEqual(self.outputs(), baseline, 'changing atomic-tests values')
        os.mkfifo(tasks / 'pipe.md')
        self.assertEqual(self.outputs(), baseline, 'a task file that would block any reader')
        shutil.rmtree(self.project / '.ai/tasks')
        self.assertEqual(self.outputs(), baseline, 'removing task records')


CLASSES = (*CLASSES, *ENTRYPOINT_TABLE_CLASSES, EntrypointFastPath, EntrypointProtocol, EntrypointDiagnostics,
           EntrypointFailureModes, EntrypointLimits, EntrypointIndependence)


# ── Hook entrypoint in a degraded environment ──────────────────────────

import io  # noqa: E402 - the degraded-environment block needs these only
from types import SimpleNamespace  # noqa: E402


def link_kept(directory: Path, target: Path, keep: Callable[[str], bool]) -> None:
    if not directory.is_dir():
        return
    for program in sorted(directory.iterdir()):
        link = target / program.name
        if not keep(program.name) or link.exists() or link.is_symlink():
            continue
        if program.is_file() and os.access(program, os.X_OK):
            link.symlink_to(program)


def filtered_path(excluded: frozenset[str], python: bool) -> str:
    """One directory linking every program on the current PATH except the excluded names,
    and except Python unless python is true."""
    key = ' '.join(sorted(excluded)) + (' +python' if python else ' -python')
    if key not in TOOLS:
        root = Path(os.path.realpath(tempfile.mkdtemp(prefix='entry tools ')))
        atexit.register(shutil.rmtree, root, True)

        def keep(name: str) -> bool:
            return name not in excluded and (python or not name.startswith('python'))

        for directory in os.environ.get('PATH', '/usr/bin:/bin').split(os.pathsep):
            link_kept(Path(directory), root, keep)
        TOOLS[key] = str(root)
    return TOOLS[key]


class EntrypointDegradedEnvironment(EntrypointFixture):
    """Missing shell tools, a registry behind an unsearchable directory and CDPATH never let
    a relevant command through undecided."""

    def tools_missing(self, *names: str, python: bool = True) -> dict[str, str]:
        return {**self.environ, 'PATH': filtered_path(frozenset(names), python)}

    def run_relative(self, payload: bytes, environ: Mapping[str, str]) -> HookRun:
        """The entrypoint started by a relative path from the source checkout."""
        started = time.monotonic()
        result = subprocess.run([BASH, 'hooks/git-rails.sh'], input=payload, capture_output=True,
                                env=dict(environ), cwd=SOURCE, timeout=HOOK_TIMEOUT)
        return HookRun(result.returncode, result.stdout, result.stderr, time.monotonic() - started)

    def test_missing_read_tools_leave_the_decision_to_the_core(self) -> None:
        for missing in (('head',), ('tr',), ('head', 'tr')):
            environ = self.tools_missing(*missing)
            with self.subTest(missing=missing):
                self.assert_protocol(self.hook_twice(self.payload('git add -A'), environ),
                                     Expected('deny', 'blanket-staging', 'R01'), environ)
                self.assert_protocol(self.hook_twice(self.payload('ls', self.location('clean')), environ),
                                     Expected('not_applicable'), environ)
                self.assert_protocol(self.hook_twice(self.padded('git add a.txt', STDIN_LIMIT + 1), environ),
                                     Expected('deny', 'malformed-input'), environ)

    def test_missing_read_tools_and_python_are_runtime_unavailable(self) -> None:
        for missing in (('head',), ('tr',)):
            environ = self.tools_missing(*missing, python=False)
            with self.subTest(missing=missing):
                self.assert_protocol(self.hook_twice(self.payload('git add -A'), environ),
                                     Expected('deny', 'runtime-unavailable'), environ)

    def test_registry_behind_an_unsearchable_directory_is_a_registry_error(self) -> None:
        if os.geteuid() == 0:
            self.skipTest('file permissions do not restrict the superuser')
        for directory in (self.registry.parent, self.config):
            with self.subTest(directory=directory.name):
                directory.chmod(0o600)
                try:
                    run = self.hook_twice(self.payload('git status'))
                finally:
                    directory.chmod(0o755)
                self.assert_protocol(run, Expected('deny', 'registry-error'))

    def test_runtime_diagnostic_without_sed_keeps_four_lines(self) -> None:
        environ = self.tools_missing('sed', python=False)
        run = self.hook_twice(self.payload('git add -A'), environ)
        self.assertEqual((run.status, run.stdout), (2, b''), run.stderr[-300:])
        lines = self.diagnostic_text(run).split('\n')
        self.assertEqual(len(lines), 4, lines)
        self.assertEqual(lines[0], 'git-rails: deny runtime-unavailable (none)')
        for index, prefix in ((1, 'rule'), (2, 'operation'), (3, 'next')):
            self.assertRegex(lines[index], rf'^{prefix}: \S')

    def test_relative_invocation_ignores_cdpath(self) -> None:
        decoys = self.probe / 'cdpath'
        (decoys / 'hooks').mkdir(parents=True)
        environ = {**self.environ, 'CDPATH': str(decoys)}
        self.assert_protocol(self.run_relative(self.payload('git add -A'), environ),
                             Expected('deny', 'blanket-staging', 'R01'), environ)
        no_python = {**self.without_python(), 'CDPATH': str(decoys)}
        self.assert_protocol(self.run_relative(self.payload('git add -A'), no_python),
                             Expected('deny', 'runtime-unavailable'), no_python)


class CoreEntryPoint(RailsFixture):
    """The core entry point denies even when its budget signal lands inside a failure handler."""

    def patch(self, name: str, value: object) -> None:
        self.addCleanup(setattr, CORE, name, getattr(CORE, name))
        setattr(CORE, name, value)

    def test_budget_signal_inside_the_failure_handler_still_denies(self) -> None:
        main, budget, denial = self.api('main'), self.api('BudgetExceeded'), self.api('denial')

        def failing_decide(event: object, environ: Mapping[str, str]) -> Any:
            raise RuntimeError('fault inside the decision')

        def late_denial(reason: str, rule: str | None = None) -> Any:
            if reason == 'internal-error':
                raise budget()  # the budget signal arriving while the failure is handled
            return denial(reason, rule)

        self.patch('decide', failing_decide)
        self.patch('denial', late_denial)
        self.addCleanup(signal.signal, signal.SIGALRM, signal.getsignal(signal.SIGALRM))
        stdout, stderr = io.BytesIO(), io.BytesIO()
        for name, stream in (('stdin', io.BytesIO(b'{}')), ('stdout', stdout), ('stderr', stderr)):
            self.addCleanup(setattr, sys, name, getattr(sys, name))
            setattr(sys, name, SimpleNamespace(buffer=stream))
        try:
            status = main()
        except BaseException as error:  # noqa: B902 - the escape itself is the failure under test
            self.fail(f'{type(error).__name__} escaped the core entry point')
        headline = stderr.getvalue().decode('utf-8').split('\n')[0]
        self.assertEqual((status, stdout.getvalue()), (2, b''))
        self.assertIn(headline, ('git-rails: deny limit-exceeded (none)', 'git-rails: deny internal-error (none)'))


CLASSES = (*CLASSES, EntrypointDegradedEnvironment, CoreEntryPoint)

# The refspec, pull, configuration, redirect and forced-lease decisions also run end to end.
RESOLUTION_GAP_THROUGH_HOOK = type('ResolutionGapTableThroughHook', (EntrypointChecks, ResolutionGapTable),
                                   {'__doc__': 'Every ResolutionGapTable case, run twice through the hook entrypoint.'})
CLASSES = (*CLASSES, RESOLUTION_GAP_THROUGH_HOOK)
SHELL_BUNDLE_THROUGH_HOOK = type('ShellBundleTableThroughHook', (EntrypointChecks, ShellBundleTable),
                                 {'__doc__': 'Every ShellBundleTable case, run twice through the hook entrypoint.'})
CLASSES = (*CLASSES, SHELL_BUNDLE_THROUGH_HOOK)


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
