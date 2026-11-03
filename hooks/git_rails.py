"""Decide whether one agent shell command crosses a git safety rail.

The core validates a PreToolUse event, reads the project registry as one snapshot,
parses the Bash command with a deliberately small shell grammar, resolves every git
and gh invocation to its program, effective directory and effective repository, and
combines per-invocation results so that the most severe one decides the command.

Everything is a pure function over the event except one sanitized, read-only git layer
with a per-read time limit. The module uses only the standard library and runs under
``python3 -I``. It never writes files, caches, logs or git state, never runs gh and
never runs a network git command. Restack recovery journals under the git common
directory are read as bounded regular files.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import fnmatch
import hashlib
import json
import os
import posixpath
import re
import signal
import stat
import subprocess
from typing import Callable, Iterable, Mapping, Sequence
import urllib.parse

RULE_PATH = 'rules/git-flow.md → ## Safety rails'

GOVERNED_GIT_SUBCOMMANDS = frozenset({
    'add', 'stage', 'commit', 'push', 'reset', 'clean', 'branch', 'update-ref',
    'checkout', 'switch', 'rebase', 'merge', 'pull'})
GOVERNED_GH_COMMANDS = frozenset({('pr', 'merge'), ('api',)})

# Git ignores an alias whose name is a builtin, so only other names are looked up.
GIT_BUILTINS = frozenset((
    'add am annotate apply archive backfill bisect blame branch bugreport bundle cat-file '
    'check-attr check-ignore check-mailmap check-ref-format checkout checkout--worker '
    'checkout-index cherry cherry-pick clean clone column commit commit-graph commit-tree '
    'config count-objects credential credential-cache credential-cache--daemon '
    'credential-store describe diagnose diff diff-files diff-index diff-pairs diff-tree '
    'difftool fast-export fast-import fetch fetch-pack fmt-merge-msg for-each-ref '
    'for-each-repo format-patch fsck fsck-objects fsmonitor--daemon gc get-tar-commit-id '
    'grep hash-object help hook index-pack init init-db interpret-trailers last-modified log '
    'ls-files ls-remote ls-tree mailinfo mailsplit maintenance merge merge-base merge-file '
    'merge-index merge-ours merge-recursive merge-recursive-ours merge-recursive-theirs '
    'merge-subtree merge-tree mktag mktree multi-pack-index mv name-rev notes pack-objects '
    'pack-redundant pack-refs patch-id pickaxe prune prune-packed pull push range-diff '
    'read-tree rebase receive-pack reflog refs remote remote-ext remote-fd repack replace '
    'replay repo rerere reset restore rev-list rev-parse revert rm send-pack shortlog show '
    'show-branch show-index show-ref sparse-checkout stage stash status stripspace '
    'submodule--helper switch symbolic-ref tag unpack-file unpack-objects update-index '
    'update-ref update-server-info upload-archive upload-archive--writer upload-pack var '
    'verify-commit verify-pack verify-tag version whatchanged worktree write-tree').split())

MAX_DEPTH = 3
MAX_TOKENS = 4096
GIT_READ_SECONDS = 2.0

ACCEPTED_GLOBAL_FLAGS = frozenset({'--no-pager', '-P', '-p', '--paginate', '--no-optional-locks',
                                   '--literal-pathspecs'})
GLOBAL_VALUE_OPTIONS = frozenset({'-C', '-c', '--git-dir', '--work-tree', '--namespace',
                                  '--config-env', '--super-prefix', '--attr-source'})
GLOBAL_ATTACHED_PREFIXES = ('--git-dir=', '--work-tree=', '--namespace=', '--config-env=',
                            '--super-prefix=', '--attr-source=', '--exec-path=', '--list-cmds=')
GLOBAL_FLAGS = ACCEPTED_GLOBAL_FLAGS | frozenset({
    '--bare', '--no-replace-objects', '--glob-pathspecs', '--noglob-pathspecs',
    '--icase-pathspecs', '--no-lazy-fetch', '--no-advice', '--exec-path', '--html-path',
    '--man-path', '--info-path', '--version', '-v', '--help', '-h'})

SANITIZED_GIT_VARIABLES = ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR')

# Programs that run another command, change what runs, or defer execution.
OPAQUE_PROGRAMS = frozenset({
    'eval', 'source', '.', 'sudo', 'doas', 'su', 'runuser', 'xargs', 'parallel', 'watch',
    'nice', 'ionice', 'stdbuf', 'setsid', 'chroot', 'flock', 'unbuffer', 'script', 'strace',
    'ltrace', 'nsenter', 'unshare', 'chrt', 'taskset', 'builtin', 'trap', 'alias', 'hash',
    'enable', 'fc', 'coproc'})
FIND_EXECUTION = frozenset({'-exec', '-execdir', '-ok', '-okdir'})
COMMAND_SHELLS = frozenset({'bash', 'sh'})
OTHER_SHELLS = frozenset({'zsh', 'dash', 'ksh', 'mksh', 'pdksh', 'oksh', 'ash', 'yash', 'fish',
                          'csh', 'tcsh', 'rbash', 'busybox', 'elvish', 'nu', 'xonsh'})
SIMPLE_WRAPPERS = frozenset({'command', 'exec', 'nohup', 'time'})
EXPORTING_BUILTINS = frozenset({'export', 'declare', 'typeset', 'readonly', 'local'})
RESERVED_WORDS = frozenset({'if', 'then', 'else', 'elif', 'fi', 'for', 'while', 'until', 'do',
                            'done', 'case', 'esac', 'select', 'function', '[[', ']]', '}'})

WORD_BREAK = frozenset(' \t\n;&|<>()')
ASSIGNMENT = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\+?=')
VARIABLE_NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
REDIRECT = re.compile(r'(\d*)(<<<|<<-|<<|<>|<&|<|>>|>&|>\||>|&>>|&>)')
BRACE_EXPANSION = re.compile(r'\{[^{}]*(,|\.\.)[^{}]*\}')
BRACKET_GLOB = re.compile(r'\[[^\]]*\]')
DURATION = re.compile(r'\d+(\.\d+)?[smhd]?')
DYNAMIC_NAME = '$'
SENSITIVE_NAMES = frozenset({'HOME', 'XDG_CONFIG_HOME', 'PATH'})
STACK_ROTATION = re.compile(r'[+-]\d+')
SHELL_VALUE_OPTIONS = frozenset({'-o', '+o', '-O', '+O', '--rcfile', '--init-file'})
GH_VALUE_FLAGS = frozenset({'-R', '--repo'})
REDIRECTING_GLOBAL_OPTIONS = ('--git-dir', '--work-tree')

# Programs that never execute their arguments; any other program given a git or gh
# program word may run it, so that command is opaque inside a registered project.
DATA_PROGRAMS = frozenset({'echo', 'printf', 'grep', 'egrep', 'fgrep', 'rg', 'cat', 'head', 'tail',
                           'less', 'more', 'man', 'which', 'type', 'wc', 'file', 'ls', 'test', '['})

SEVERITY = {'not_applicable': 0, 'allow': 1, 'ask': 2, 'deny': 3}

# Redirections that write a file, and the devices whose writes no later read can observe.
WRITE_OPERATORS = frozenset({'>', '>>', '>|', '<>', '&>', '&>>'})
DESCRIPTOR_TARGET = re.compile(r'\d+-?|-')
UNOBSERVABLE_TARGETS = frozenset({'/dev/null', '/dev/stdout', '/dev/stderr'})
# Git subcommands that only read; with no write redirection they leave state unchanged.
READ_ONLY_GIT_SUBCOMMANDS = frozenset({
    'status', 'diff', 'show', 'log', 'ls-files', 'ls-tree', 'rev-parse', 'rev-list', 'cat-file',
    'show-ref', 'for-each-ref', 'describe', 'blame', 'annotate', 'grep', 'merge-base', 'shortlog',
    'check-ignore', 'check-attr', 'check-mailmap', 'name-rev', 'var', 'version', 'help', 'whatchanged',
    'diff-files', 'diff-index', 'diff-tree', 'count-objects', 'show-branch', 'cherry', 'range-diff',
    'verify-commit', 'verify-tag'})
# Read-only subcommand options that write a file or run another program.
WRITING_GIT_OPTIONS = ('--output', '--open-files-in-pager', '-O')

BLANKET_STAGING = 'blanket-staging'
STAGING_NOT_FILE = 'staging-not-file'
UNVERIFIABLE_MESSAGE = 'commit-message-unverifiable'
MAX_MESSAGE_FILE_BYTES = 1024 * 1024
MAX_OPTION_VARIANTS = 64
GLOB_CHARACTERS = frozenset('*?[')
INTERACTIVE_OPTIONS = ('interactive', 'patch', 'edit')
REUSED_MESSAGE_OPTIONS = ('reedit-message', 'reuse-message', 'fixup', 'squash', 'template')
# Shell words cannot contain NUL, so a NUL-led placeholder never equals a literal argument.
MESSAGE_PLACEHOLDER = '\x00'

# Forbidden commit-message patterns, applied to the full checked text: a co-author trailer
# line, a task identifier and a decision-record identifier.
FORBIDDEN_PATTERNS = (
    re.compile(r'(?im)^[ \t]*co-authored-by[ \t]*:'),
    re.compile(r'(?<![A-Za-z0-9_-])T-[0-9]+[A-Za-z]*(?![A-Za-z0-9_])'),
    re.compile(r'(?<![A-Za-z0-9_-])ADR-[0-9]+'),
)


# ── Decisions and records ──────────────────────────────────────────────

@dataclass(frozen=True)
class Decision:
    """One result: not_applicable, allow, deny or ask, with its reason and rule, and for a
    journal verification the check that failed."""
    decision: str
    reason_code: str | None = None
    rule_id: str | None = None
    failure: str | None = None


NOT_APPLICABLE = Decision('not_applicable')
ALLOW = Decision('allow')


def denial(reason: str, rule: str | None = None) -> Decision:
    return Decision('deny', reason, rule)


@dataclass(frozen=True)
class Word:
    """A shell word after quote removal; a dynamic word keeps its source spelling."""
    text: str
    dynamic: bool = False
    form: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class Context:
    """The canonical event directory, the registry snapshot and the hook environment."""
    cwd: str
    roots: tuple[str, ...]
    environ: Mapping[str, str]


@dataclass(frozen=True)
class GitLayout:
    """Where the git global options end and the subcommand word sits."""
    globals_end: int
    index: int | None
    unknown: bool


@dataclass(frozen=True)
class Invocation:
    """One resolved git or gh simple command inside a registered work tree."""
    program: str
    words: tuple[Word, ...]
    directory: str
    repository: str | None
    common_dir: str | None
    project: str
    environment: tuple[Word, ...] = ()
    inherited: tuple[str, ...] = ()
    stdin: Word | None = None
    alias: bool = False
    state_changed: bool = False

    @property
    def layout(self: Invocation) -> GitLayout:
        if self.program == 'git':
            return git_layout(self.words)
        positions = gh_positionals(self.words)
        if not positions:
            return GitLayout(len(self.words), None, False)
        return GitLayout(positions[0], positions[0], False)

    @property
    def global_options(self: Invocation) -> tuple[str, ...]:
        return tuple(word.text for word in self.words[:self.layout.globals_end])

    @property
    def subcommand(self: Invocation) -> str | None:
        index = self.layout.index
        return None if index is None else self.words[index].text

    @property
    def arguments(self: Invocation) -> tuple[Word, ...]:
        index = self.layout.index
        return () if index is None else self.words[index + 1:]

    @property
    def argv(self: Invocation) -> tuple[str, ...]:
        return tuple(word.text for word in self.arguments)

    @property
    def assignments(self: Invocation) -> tuple[str, ...]:
        return tuple(assignment_name(word) for word in self.environment)

    @property
    def governed(self: Invocation) -> bool:
        return rule_key(self) is not None


@dataclass(frozen=True)
class Resolution:
    """Resolved invocations and, when the command itself cannot be verified, a decision."""
    invocations: tuple[Invocation, ...]
    decision: Decision | None = None


def combine(decisions: Iterable[Decision]) -> Decision:
    """The most severe result wins; among equals the first in command order wins."""
    best = NOT_APPLICABLE
    for decision in decisions:
        if SEVERITY[decision.decision] > SEVERITY[best.decision]:
            best = decision
    return best


def assignment_name(word: Word) -> str:
    match = ASSIGNMENT.match(word.text)
    return match.group(1) if match else DYNAMIC_NAME


# ── Registry snapshot ──────────────────────────────────────────────────

class RegistryError(Exception):
    """The registry exists but cannot be read or holds an invalid line."""


def registry_path(environ: Mapping[str, str]) -> str | None:
    base = environ.get('XDG_CONFIG_HOME') or ''
    if not base:
        home = environ.get('HOME') or ''
        if not home:
            return None
        base = os.path.join(home, '.config')
    return os.path.join(base, 'orchestrail', 'projects')


def valid_root(line: str) -> bool:
    """The registration predicate: absolute, canonical, no CR or NUL."""
    if not line or '\r' in line or '\x00' in line or not os.path.isabs(line):
        return False
    return os.path.realpath(line) == line


def read_registry(environ: Mapping[str, str]) -> tuple[str, ...] | None:
    """Registered roots, or None when no registry file exists."""
    path = registry_path(environ)
    if path is None:
        return None
    try:
        with open(path, 'rb') as stream:
            data = stream.read()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise RegistryError(path) from error
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError as error:
        raise RegistryError(path) from error
    lines = text.split('\n') if text else []
    if lines and lines[-1] == '':
        lines.pop()
    if not all(valid_root(line) for line in lines):
        raise RegistryError(path)
    return tuple(lines)


def project_for(directory: str, roots: Sequence[str]) -> str | None:
    """The most specific registered root containing the directory; '/' contains all."""
    best: str | None = None
    for root in roots:
        inside = root == '/' or directory == root or directory.startswith(root + '/')
        if inside and (best is None or len(root) > len(best)):
            best = root
    return best


# ── Event validation ───────────────────────────────────────────────────

@dataclass(frozen=True)
class Request:
    """The validated parts of a Bash PreToolUse event."""
    command: str
    cwd: str


def read_request(event: object) -> Request | Decision:
    malformed = denial('malformed-input')
    if not isinstance(event, dict) or event.get('hook_event_name') != 'PreToolUse':
        return malformed
    tool = event.get('tool_name')
    if not isinstance(tool, str):
        return malformed
    if tool != 'Bash':
        return NOT_APPLICABLE
    tool_input = event.get('tool_input')
    command = tool_input.get('command') if isinstance(tool_input, dict) else None
    cwd = event.get('cwd')
    if not isinstance(command, str) or not isinstance(cwd, str):
        return malformed
    if not os.path.isabs(cwd) or '\x00' in cwd:
        return malformed
    return Request(command, os.path.realpath(cwd))


# ── Git parse-options semantics ────────────────────────────────────────

@dataclass(frozen=True)
class OptionSpec:
    """One option of a governed subcommand; the key is the long name, else the short one.

    takes is 'none', 'required', 'optional' (attached value only) or 'last': the next word
    is the value unless the option is the last word, which git reads as its default."""
    long: str | None = None
    short: str | None = None
    takes: str = 'none'
    repeatable: bool = False
    negatable: bool = True

    @property
    def key(self: OptionSpec) -> str:
        return self.long or self.short or ''


OptionValue = str | bool


@dataclass(frozen=True)
class ParsedOptions:
    """Options in order, operands, and the first error with any ambiguous candidates."""
    options: tuple[tuple[str, OptionValue], ...]
    operands: tuple[str, ...]
    error: str | None = None
    candidates: tuple[str, ...] = ()

    def last(self: ParsedOptions, key: str) -> OptionValue | None:
        values = [value for name, value in self.options if name == key]
        return values[-1] if values else None

    def every(self: ParsedOptions, key: str) -> tuple[OptionValue, ...]:
        """Values since the last negation, which resets an accumulating option."""
        values: list[OptionValue] = []
        for name, value in self.options:
            if name == key:
                values = [] if value is False else [*values, value]
        return tuple(values)


class OptionError(Exception):
    def __init__(self: OptionError, code: str, candidates: tuple[str, ...] = ()) -> None:
        super().__init__(code)
        self.code = code
        self.candidates = candidates


@dataclass
class OptionCursor:
    words: Sequence[str]
    specs: Sequence[OptionSpec]
    index: int = 0
    options: list[tuple[str, OptionValue]] = field(default_factory=list)

    def at_last(self: OptionCursor) -> bool:
        """Whether the current word is the last one, where a 'last' option takes its default."""
        return self.index + 1 >= len(self.words)

    def following(self: OptionCursor) -> str:
        """The separate value of the current option."""
        if self.index + 1 >= len(self.words):
            raise OptionError('missing-value')
        self.index += 1
        return self.words[self.index]


def parse_options(words: Sequence[str], specs: Sequence[OptionSpec]) -> ParsedOptions:
    """Parse arguments the way git's parse-options does."""
    cursor = OptionCursor(words, specs)
    operands: list[str] = []
    try:
        while cursor.index < len(words):
            word = words[cursor.index]
            if word == '--':
                operands.extend(words[cursor.index + 1:])
                break
            if word.startswith('--'):
                parse_long(cursor, word[2:])
            elif word.startswith('-') and word != '-':
                parse_short(cursor, word[1:])
            else:
                operands.append(word)
            cursor.index += 1
    except OptionError as error:
        return ParsedOptions(tuple(cursor.options), tuple(operands), error.code, error.candidates)
    return ParsedOptions(tuple(cursor.options), tuple(operands))


def long_matches(name: str, specs: Sequence[OptionSpec]) -> list[tuple[OptionSpec, bool]]:
    """Exact matches first, then every abbreviation, each with its negation flag."""
    negated = name[3:] if name.startswith('no-') else None
    exact = [(spec, False) for spec in specs if spec.long == name]
    exact += [(spec, True) for spec in specs if negated and spec.negatable and spec.long == negated]
    if exact:
        return exact[:1]
    found = [(spec, False) for spec in specs if spec.long and spec.long.startswith(name)]
    if negated:
        found += [(spec, True) for spec in specs
                  if spec.negatable and spec.long and spec.long.startswith(negated)]
    return found


def parse_long(cursor: OptionCursor, body: str) -> None:
    name, equals, value = body.partition('=')
    matches = long_matches(name, cursor.specs)
    if not matches:
        raise OptionError('unknown-option')
    if len(matches) > 1:
        names = tuple(dict.fromkeys(spec.long or '' for spec, _ in matches))
        raise OptionError('ambiguous-option', names)
    spec, negated = matches[0]
    if negated or spec.takes == 'none':
        if equals:
            raise OptionError('unexpected-value')
        cursor.options.append((spec.key, not negated))
    elif equals:
        cursor.options.append((spec.key, value))
    elif spec.takes == 'required' or (spec.takes == 'last' and not cursor.at_last()):
        cursor.options.append((spec.key, cursor.following()))
    else:
        cursor.options.append((spec.key, True))


def parse_short(cursor: OptionCursor, bundle: str) -> None:
    for position, letter in enumerate(bundle):
        spec = next((item for item in cursor.specs if item.short == letter), None)
        if spec is None:
            raise OptionError('unknown-option')
        rest = bundle[position + 1:]
        if spec.takes == 'none':
            cursor.options.append((spec.key, True))
            continue
        if rest:
            cursor.options.append((spec.key, rest))
        elif spec.takes == 'required' or (spec.takes == 'last' and not cursor.at_last()):
            cursor.options.append((spec.key, cursor.following()))
        else:
            cursor.options.append((spec.key, True))
        return


# ── Shell grammar ──────────────────────────────────────────────────────

class ParseError(Exception):
    """The command uses syntax outside the supported grammar."""


class LimitExceeded(Exception):
    """The command exceeds a recursion, token or git-read limit."""


@dataclass
class Budget:
    tokens: int = 0

    def spend(self: Budget) -> None:
        self.tokens += 1
        if self.tokens > MAX_TOKENS:
            raise LimitExceeded('tokens')


@dataclass
class Simple:
    """A simple command: leading assignments, words, stdin and nested commands."""
    depth: int
    assignments: list[Word] = field(default_factory=list)
    words: list[Word] = field(default_factory=list)
    stdin: Word | None = None
    stdin_kind: str | None = None
    redirects: int = 0
    inputs: int = 0
    writes: bool = False
    nested: list[Script] = field(default_factory=list)
    opaque: bool = False


@dataclass
class Group:
    """A ( … ) subshell or a { …; } group with its trailing redirections."""
    body: Script
    subshell: bool
    redirections: Simple


@dataclass
class Pipeline:
    elements: list[Simple | Group]
    background: bool = False


@dataclass
class Script:
    pipelines: list[Pipeline]


@dataclass
class PendingHeredoc:
    delimiter: str
    strip_tabs: bool
    quoted: bool
    owner: Simple
    position: int | None = None


@dataclass
class Source:
    """One command text, its cursor and the heredocs awaiting their bodies."""
    text: str
    pos: int = 0
    pending: list[PendingHeredoc] = field(default_factory=list)


class Parser:
    """Recursive-descent parser over one source at one recursion depth."""

    def __init__(self: Parser, source: Source, budget: Budget, depth: int) -> None:
        self.src = source
        self.budget = budget
        self.depth = depth

    # Cursor helpers.
    def peek(self: Parser, offset: int = 0) -> str:
        index = self.src.pos + offset
        return self.src.text[index] if index < len(self.src.text) else ''

    def starts(self: Parser, token: str) -> bool:
        return self.src.text.startswith(token, self.src.pos)

    def advance(self: Parser, count: int = 1) -> None:
        self.src.pos += count

    def child(self: Parser, source: Source | None = None) -> Parser:
        if self.depth + 1 > MAX_DEPTH:
            raise LimitExceeded('depth')
        return Parser(source or self.src, self.budget, self.depth + 1)

    def skip_blanks(self: Parser) -> None:
        while True:
            char = self.peek()
            if char in (' ', '\t'):
                self.advance()
            elif char == '\\' and self.peek(1) == '\n':
                self.advance(2)
            elif char == '#':
                end = self.src.text.find('\n', self.src.pos)
                self.src.pos = len(self.src.text) if end < 0 else end
            else:
                return

    def newline(self: Parser) -> None:
        self.advance()
        self.read_heredocs()

    def skip_layout(self: Parser) -> None:
        while True:
            self.skip_blanks()
            if self.peek() != '\n':
                return
            self.newline()

    # Lists, pipelines and commands.
    def parse_top(self: Parser) -> Script:
        script = self.parse_list('')
        self.read_heredocs()
        return script

    def at_close(self: Parser, closer: str) -> bool:
        char = self.peek()
        if char == '':
            if closer:
                raise ParseError('unterminated ' + closer)
            return True
        if closer == ')' and char == ')':
            return True
        return closer == '}' and char == '}' and self.peek(1) in ('', ' ', '\t', '\n', ';', '&', '|', ')')

    def parse_list(self: Parser, closer: str) -> Script:
        pipelines: list[Pipeline] = []
        while True:
            self.skip_layout()
            if self.at_close(closer):
                return Script(pipelines)
            pipeline = self.parse_pipeline()
            pipelines.append(pipeline)
            self.skip_blanks()
            operator = self.read_operator()
            pipeline.background = operator == '&'
            if operator in ('&&', '||'):
                self.skip_layout()
                if self.at_close(closer):
                    raise ParseError('missing command after ' + operator)
            elif operator == '' and not self.at_close(closer):
                raise ParseError('unexpected ' + self.peek())

    def read_operator(self: Parser) -> str:
        for token in ('&&', '||', ';;', ';', '&', '\n'):
            if self.starts(token):
                if token == ';;':
                    raise ParseError('case terminator')
                self.budget.spend()
                if token == '\n':
                    self.newline()
                else:
                    self.advance(len(token))
                return token
        return ''

    def parse_pipeline(self: Parser) -> Pipeline:
        self.skip_blanks()
        if self.peek() == '!' and self.peek(1) in (' ', '\t'):
            self.advance()
            self.budget.spend()
        elements = [self.parse_command()]
        while True:
            self.skip_blanks()
            if self.starts('||') or not self.starts('|'):
                return Pipeline(elements)
            self.advance(2 if self.starts('|&') else 1)
            self.budget.spend()
            self.skip_layout()
            elements.append(self.parse_command())

    def parse_command(self: Parser) -> Simple | Group:
        self.skip_blanks()
        if self.starts('(('):
            raise ParseError('arithmetic command')
        if self.peek() == '(':
            return self.parse_group(')', True)
        if self.peek() == '{' and self.peek(1) in (' ', '\t', '\n'):
            return self.parse_group('}', False)
        return self.parse_simple()

    def parse_group(self: Parser, closer: str, subshell: bool) -> Group:
        self.advance()
        self.budget.spend()
        body = self.child().parse_list(closer)
        self.advance()
        self.budget.spend()
        redirections = Simple(self.depth)
        while True:
            self.skip_blanks()
            if not self.try_redirect(redirections):
                break
        if self.peek() not in ('', '\n', ';', '&', '|', ')'):
            raise ParseError('word after group')
        return Group(body, subshell, redirections)

    def parse_simple(self: Parser) -> Simple:
        node = Simple(self.depth)
        while True:
            self.skip_blanks()
            if self.try_process_substitution(node) or self.try_redirect(node):
                continue
            char = self.peek()
            if char in ('', '\n', ';', '&', '|', ')'):
                break
            if char == '(':
                raise ParseError('function definition or misplaced parenthesis')
            word, raw = self.read_word(node)
            if not raw:
                continue
            if not node.words and ASSIGNMENT.match(raw):
                node.assignments.append(word)
            elif not node.words and raw in RESERVED_WORDS:
                raise ParseError('compound command ' + raw)
            else:
                node.words.append(word)
        if not (node.words or node.assignments or node.redirects):
            raise ParseError('empty command')
        return node

    def try_process_substitution(self: Parser, node: Simple) -> bool:
        if not (self.starts('<(') or self.starts('>(')):
            return False
        self.advance(2)
        self.budget.spend()
        node.nested.append(self.child().parse_list(')'))
        self.advance()
        node.opaque = True
        return True

    def try_redirect(self: Parser, node: Simple) -> bool:
        match = REDIRECT.match(self.src.text, self.src.pos)
        if match is None:
            return False
        operator = match.group(2)
        self.src.pos = match.end()
        self.budget.spend()
        self.skip_blanks()
        if self.peek() in ('', '\n', ';', '&', '|', '(', ')', '<', '>'):
            raise ParseError('missing redirection target')
        word, raw = self.read_word(node)
        node.redirects += 1
        node.writes |= writes_file(operator, word)
        standard = operator.startswith('<') and match.group(1) in ('', '0')
        if standard:
            node.inputs += 1
        if operator in ('<<', '<<-'):
            if word.dynamic:
                raise ParseError('dynamic heredoc delimiter')
            quoted = any(char in raw for char in '\'"\\')
            position = node.inputs if standard else None
            self.src.pending.append(PendingHeredoc(word.text, operator == '<<-', quoted, node, position))
        elif standard and operator == '<<<':
            node.stdin, node.stdin_kind = Word(word.text + '\n', word.dynamic), 'herestring'
        elif standard:
            node.stdin, node.stdin_kind = None, 'file'
        return True

    # Heredoc bodies.
    def read_heredocs(self: Parser) -> None:
        pending, self.src.pending = self.src.pending, []
        for document in pending:
            body = self.read_heredoc_body(document)
            dynamic = not document.quoted and any(char in body for char in '$`\\')
            if document.position is not None and document.position == document.owner.inputs:
                document.owner.stdin, document.owner.stdin_kind = Word(body, dynamic), 'heredoc'
            if not document.quoted:
                self.scan_expansions(document.owner, body)

    def read_heredoc_body(self: Parser, document: PendingHeredoc) -> str:
        text = self.src.text
        lines: list[str] = []
        while self.src.pos < len(text):
            end = text.find('\n', self.src.pos)
            stop = len(text) if end < 0 else end
            line = text[self.src.pos:stop]
            self.src.pos = stop if end < 0 else stop + 1
            if document.strip_tabs:
                line = line.lstrip('\t')
            if line == document.delimiter:
                break
            lines.append(line + '\n')
        return ''.join(lines)

    def scan_expansions(self: Parser, node: Simple, body: str) -> None:
        """Parse the substitutions an unquoted heredoc body would run."""
        scanner = Parser(Source(body), self.budget, self.depth)
        while scanner.peek():
            char = scanner.peek()
            if char == '\\':
                scanner.advance(2)
            elif char == '$':
                scanner.read_dollar(node, True)
            elif char == '`':
                scanner.read_backtick(node)
            else:
                scanner.advance()

    # Words.
    def read_word(self: Parser, node: Simple) -> tuple[Word, str]:
        start = self.src.pos
        state = WordState(start)
        while True:
            char = self.peek()
            if char == '' or char in WORD_BREAK:
                break
            if char == '\\' and self.peek(1) == '\n':
                self.advance(2)
                continue
            state.segments += 1
            self.read_segment(node, state)
        raw = self.src.text[start:self.src.pos]
        if raw:
            self.budget.spend()
        plain = ''.join(state.plain)
        if BRACE_EXPANSION.search(plain) or BRACKET_GLOB.search(plain):
            state.dynamic = True
        return state.word(raw), raw

    def read_segment(self: Parser, node: Simple, state: WordState) -> None:
        char = self.peek()
        if char == '\\':
            state.literal(self.peek(1) or '\\', quoted=True)
            self.advance(2)
        elif char == "'":
            state.literal(self.read_single_quoted(), quoted=True)
        elif char == '"':
            value, dynamic, only = self.read_double_quoted(node)
            state.literal(value, quoted=True)
            state.dynamic |= dynamic
            state.candidate = only if state.segments == 1 else None
        elif char == '$':
            kind = self.read_dollar(node, False)
            if kind is None:
                state.literal('$', quoted=False)
            else:
                state.expansion()
        elif char == '`':
            self.read_backtick(node)
            state.expansion()
        else:
            if char in '*?' or (char == '~' and self.src.pos == state.start):
                state.dynamic = True
            state.literal(char, quoted=False)
            self.advance()

    def read_single_quoted(self: Parser) -> str:
        end = self.src.text.find("'", self.src.pos + 1)
        if end < 0:
            raise ParseError('unterminated single quote')
        value = self.src.text[self.src.pos + 1:end]
        self.src.pos = end + 1
        return value

    def read_double_quoted(self: Parser, node: Simple) -> tuple[str, bool, Script | None]:
        """Value, dynamic flag, and the script when the content is one $( … ) only."""
        self.advance()
        state = QuotedState()
        while True:
            char = self.peek()
            if char == '':
                raise ParseError('unterminated double quote')
            if char == '"':
                self.advance()
                break
            if char == '\\' and self.peek(1) == '\n':
                self.advance(2)
                continue
            self.read_quoted_char(node, state)
        only = state.substitutions[0] if len(state.substitutions) == 1 and not state.others else None
        return ''.join(state.value), state.dynamic, only

    def read_quoted_char(self: Parser, node: Simple, state: QuotedState) -> None:
        char = self.peek()
        if char == '\\':
            escaped = self.peek(1) in ('$', '`', '"', '\\')
            state.text(self.peek(1) if escaped else '\\')
            self.advance(2 if escaped else 1)
        elif char == '$':
            kind = self.read_dollar(node, True)
            if kind is None:
                state.text('$')
            elif isinstance(kind, Script):
                state.dynamic = True
                state.substitutions.append(kind)
            else:
                state.dynamic, state.others = True, state.others + 1
        elif char == '`':
            self.read_backtick(node)
            state.dynamic, state.others = True, state.others + 1
        else:
            state.text(char)
            self.advance()

    def read_dollar(self: Parser, node: Simple, quoted: bool) -> Script | str | None:
        """Consume one expansion; None means a literal dollar sign."""
        following = self.peek(1)
        if self.starts('$(('):
            self.skip_balanced(node, '(', ')')
            return 'arithmetic'
        if following == '(':
            self.advance(2)
            self.budget.spend()
            script = self.child().parse_list(')')
            self.advance()
            node.nested.append(script)
            return script
        if following == '{':
            self.skip_balanced(node, '{', '}')
            return 'parameter'
        if following in ("'", '"') and not quoted:
            self.advance()
            if following == "'":
                self.skip_ansi_string()
            else:
                self.read_double_quoted(node)
            return 'string'
        return self.read_parameter(following)

    def read_parameter(self: Parser, following: str) -> str | None:
        if following and (following.isalpha() or following == '_'):
            match = VARIABLE_NAME.match(self.src.text, self.src.pos + 1)
            self.src.pos = match.end() if match else self.src.pos + 2
            return 'parameter'
        if following and (following.isdigit() or following in '@*#?-$!'):
            self.advance(2)
            return 'parameter'
        self.advance()
        return None

    def skip_balanced(self: Parser, node: Simple, opening: str, closing: str) -> None:
        """Skip ${ … } or $(( … )); quoted and escaped braces do not close it, as in bash."""
        text, start = self.src.text, self.src.pos + 1
        level, index = 0, start
        while index < len(text):
            char = text[index]
            if char in ('\\', "'", '"'):
                index = skip_quoted(text, index)
                continue
            level += (char == opening) - (char == closing)
            if level == 0:
                break
            index += 1
        if index >= len(text):
            raise ParseError('unterminated expansion')
        content = text[start:index + 1]
        if '$(' in content or '`' in content:
            node.opaque = True
        self.src.pos = index + 1

    def skip_ansi_string(self: Parser) -> None:
        text, index = self.src.text, self.src.pos + 1
        while index < len(text) and text[index] != "'":
            index += 2 if text[index] == '\\' else 1
        if index >= len(text):
            raise ParseError('unterminated ANSI-C string')
        self.src.pos = index + 1

    def read_backtick(self: Parser, node: Simple) -> None:
        text, index = self.src.text, self.src.pos + 1
        chunks: list[str] = []
        while index < len(text) and text[index] != '`':
            if text[index] == '\\' and index + 1 < len(text):
                following = text[index + 1]
                chunks.append(following if following in '$`\\' else '\\' + following)
                index += 2
                continue
            chunks.append(text[index])
            index += 1
        if index >= len(text):
            raise ParseError('unterminated backtick')
        self.src.pos = index + 1
        node.nested.append(self.child(Source(''.join(chunks))).parse_top())


@dataclass
class WordState:
    """Pieces of one word while it is read."""
    start: int
    parts: list[str] = field(default_factory=list)
    plain: list[str] = field(default_factory=list)
    dynamic: bool = False
    segments: int = 0
    candidate: Script | None = None

    def literal(self: WordState, value: str, quoted: bool) -> None:
        self.parts.append(value)
        self.plain.append('\x00' if quoted else value)

    def expansion(self: WordState) -> None:
        self.dynamic = True
        self.plain.append('\x00')

    def word(self: WordState, raw: str) -> Word:
        if self.candidate is not None and self.segments == 1:
            form, message = commit_message(self.candidate)
            if form is not None:
                return Word(raw, True, form, message)
        return Word(raw, True) if self.dynamic else Word(''.join(self.parts))


@dataclass
class QuotedState:
    """Pieces of one double-quoted string while it is read."""
    value: list[str] = field(default_factory=list)
    dynamic: bool = False
    others: int = 0
    substitutions: list[Script] = field(default_factory=list)

    def text(self: QuotedState, value: str) -> None:
        self.value.append(value)
        self.others += 1


def writes_file(operator: str, target: Word) -> bool:
    """Whether a redirection can change a file that a later read observes."""
    if operator == '>&':
        return target.dynamic or not DESCRIPTOR_TARGET.fullmatch(target.text)
    if operator not in WRITE_OPERATORS:
        return False
    return target.dynamic or target.text not in UNOBSERVABLE_TARGETS


def commit_message(script: Script) -> tuple[str | None, str | None]:
    """Recognise "$(cat <<D … D)": the form, and its message when the body is literal."""
    if len(script.pipelines) != 1 or script.pipelines[0].background:
        return None, None
    elements = script.pipelines[0].elements
    node = elements[0] if len(elements) == 1 else None
    if not isinstance(node, Simple) or node.assignments or node.redirects != 1:
        return None, None
    if [word.text for word in node.words] != ['cat'] or node.words[0].dynamic:
        return None, None
    if node.stdin_kind != 'heredoc' or node.stdin is None:
        return None, None
    return 'commit-message', None if node.stdin.dynamic else node.stdin.text.rstrip('\n')


def parse_script(command: str, budget: Budget, depth: int = 0) -> Script:
    return Parser(Source(command), budget, depth).parse_top()


# ── Effective directory and invocation discovery ───────────────────────

Place = tuple[str | None, str, bool]


@dataclass
class Scope:
    """Shell state that later commands of the same list inherit.

    ``directory`` is None after a dynamic cd: every later invocation is opaque.
    ``uncertain`` marks a directory the walk cannot follow (a failed cd, stack rotation);
    ``sticky`` marks shell features that keep every later directory uncertain (CDPATH,
    shopt). Governed invocations in an uncertain directory cannot be verified.
    """
    directory: str | None
    logical: str
    last_known: str
    uncertain: bool = False
    sticky: bool = False
    stack: list[Place] = field(default_factory=list)
    names: tuple[str, ...] = ()

    def copy(self: Scope) -> Scope:
        return replace(self, stack=list(self.stack))

    @property
    def unsure(self: Scope) -> bool:
        return self.uncertain or self.sticky


@dataclass(frozen=True)
class Found:
    """An invocation before repository resolution."""
    program: str
    words: tuple[Word, ...]
    environment: tuple[Word, ...]
    directory: str
    inherited: tuple[str, ...]
    stdin: Word | None
    anchors: tuple[str, ...] = ()
    uncertain: bool = False
    changed: bool = False


@dataclass(frozen=True)
class Command:
    """A simple command after wrapper removal, with the program word first."""
    name: str
    words: list[Word]
    environment: list[Word]
    node: Simple

    @property
    def base(self: Command) -> str:
        return self.name.rsplit('/', 1)[-1]


@dataclass(frozen=True)
class Opaque:
    """An unsupported construct and the directories known before it."""
    anchors: tuple[str, ...]


class Walker:
    """Walk the parsed command, tracking directories and environment statements.

    ``anchors`` lists every directory the command has named so far, in any scope: the
    event directory, cd/pushd targets, CDPATH entries and absolute assignment values.
    An unverifiable construct matters when any anchor recorded before it is registered.
    ``changed`` is the state-may-change mark: once any command that may write has been
    walked, in any scope, later invocations cannot trust repository or file reads.
    """

    def __init__(self: Walker, budget: Budget, cwd: str) -> None:
        self.budget = budget
        self.items: list[Found | Opaque] = []
        self.anchors: list[str] = [cwd]
        self.changed = False

    def walk_script(self: Walker, script: Script, scope: Scope) -> None:
        for pipeline in script.pipelines:
            isolated = pipeline.background or len(pipeline.elements) > 1
            for element in pipeline.elements:
                self.walk_node(element, scope.copy() if isolated else scope)

    def walk_node(self: Walker, node: Simple | Group, scope: Scope) -> None:
        if isinstance(node, Group):
            self.walk_nested(node.redirections, scope)
            self.walk_script(node.body, scope.copy() if node.subshell else scope)
            self.changed |= node.redirections.writes
            return
        self.walk_nested(node, scope)
        if node.opaque:
            self.opaque(scope)
        if node.words:
            self.walk_command(node, scope)
        else:
            self.assign(node.assignments, scope)
        self.changed |= may_write(node)

    def walk_nested(self: Walker, node: Simple, scope: Scope) -> None:
        for script in node.nested:
            self.walk_script(script, scope.copy())

    def opaque(self: Walker, scope: Scope) -> None:
        self.items.append(Opaque(tuple(self.anchors)))

    def anchor_values(self: Walker, word: Word) -> None:
        """Record absolute directories named by a literal NAME=value or export word."""
        if word.dynamic or '=' not in word.text:
            return
        for part in word.text.split('=', 1)[1].split(':'):
            if os.path.isabs(part):
                self.anchors.append(os.path.realpath(part))

    def assign(self: Walker, words: Sequence[Word], scope: Scope) -> None:
        for word in words:
            self.anchor_values(word)
        note_names([assignment_name(word) for word in words], scope)

    def walk_command(self: Walker, node: Simple, scope: Scope) -> None:
        stripped = strip_wrappers(list(node.words), list(node.assignments))
        if stripped is None:
            self.opaque(scope)
            return
        words, environment = stripped
        for word in environment:
            self.anchor_values(word)
        if not words:
            return
        if words[0].dynamic:
            self.opaque(scope)
            return
        self.dispatch(Command(words[0].text, words, environment, node), scope)

    def dispatch(self: Walker, command: Command, scope: Scope) -> None:
        name, base, arguments = command.name, command.base, command.words[1:]
        if base in ('git', 'gh'):
            self.invocation(command, scope)
        elif is_opaque_program(name, base, arguments):
            self.opaque(scope)
        elif base in COMMAND_SHELLS:
            self.shell(command, scope)
        elif name in ('cd', 'pushd', 'popd'):
            self.change_directory(command, scope)
        elif name in EXPORTING_BUILTINS:
            self.export(arguments, scope)
        elif name == 'shopt':
            scope.sticky = True
        elif runs_git_word(base, arguments):
            self.opaque(scope)

    def invocation(self: Walker, command: Command, scope: Scope) -> None:
        relative = '/' in command.name and not command.name.startswith('/')
        if relative or scope.directory is None:
            self.opaque(scope)
            return
        self.items.append(Found(command.base, tuple(command.words[1:]), tuple(command.environment),
                                scope.directory, scope.names, command.node.stdin,
                                tuple(self.anchors), scope.unsure, self.changed))

    def shell(self: Walker, command: Command, scope: Scope) -> None:
        """Parse `bash -c '<literal>'` recursively; other ways of feeding a shell are opaque."""
        arguments = command.words[1:]
        if arguments and not arguments[0].dynamic and arguments[0].text == '-c':
            if len(arguments) < 2 or arguments[1].dynamic:
                self.opaque(scope)
                return
            inner = scope.copy()
            note_names([assignment_name(word) for word in command.environment], inner)
            depth = child_depth(command.node.depth)
            self.walk_script(parse_script(arguments[1].text, self.budget, depth), inner)
        elif shell_runs_string(arguments) or shell_reads_stdin(arguments):
            self.opaque(scope)
        elif runs_git_word(command.base, arguments):
            self.opaque(scope)

    def export(self: Walker, arguments: Sequence[Word], scope: Scope) -> None:
        names: list[str] = []
        for word in arguments:
            if not word.dynamic and word.text.startswith('-'):
                continue
            self.anchor_values(word)
            names.append(exported_name(word))
        note_names(names, scope)

    def change_directory(self: Walker, command: Command, scope: Scope) -> None:
        """Literal cd/pushd/popd move the directory; other forms make it unknown."""
        if any(assignment_name(word) == 'CDPATH' for word in command.environment):
            scope.sticky = True
        arguments = command.words[1:]
        if arguments and not arguments[0].dynamic and arguments[0].text == '--':
            arguments = arguments[1:]
        single = arguments[0] if len(arguments) == 1 and not arguments[0].dynamic else None
        if command.name == 'popd':
            pop_directory(arguments, scope)
        elif single is not None and STACK_ROTATION.fullmatch(single.text):
            scope.uncertain = True
        elif single is None or not single.text or single.text.startswith('-'):
            scope.directory = None
        else:
            if command.name == 'pushd':
                scope.stack.append((scope.directory, scope.logical, scope.uncertain))
            self.move(scope, single.text)

    def move(self: Walker, scope: Scope, target: str) -> None:
        """Follow bash's logical cd: join, fold `..` lexically, then require a directory."""
        absolute = os.path.isabs(target)
        if scope.directory is None and not absolute:
            return
        logical = os.path.normpath(os.path.join(scope.logical, target))
        canonical = os.path.realpath(logical)
        self.anchors.append(canonical)
        if scope.sticky or (scope.uncertain and not absolute) or not accessible_directory(canonical):
            scope.uncertain = True
            return
        scope.directory, scope.logical, scope.last_known = canonical, logical, canonical
        scope.uncertain = False


def may_write(node: Simple) -> bool:
    """Whether a simple command may change files, the index, refs or configuration.

    Directory changes, assignments and exports, data programs and read-only git only
    write through a write redirection; a literal shell string is judged by its contents.
    """
    if node.writes:
        return True
    stripped = strip_wrappers(list(node.words), list(node.assignments))
    if stripped is None:
        return True
    words = stripped[0]
    if not words:
        return False
    if words[0].dynamic:
        return True
    name, arguments = words[0].text, words[1:]
    base = name.rsplit('/', 1)[-1]
    if name in ('cd', 'pushd', 'popd') or name in EXPORTING_BUILTINS or base in DATA_PROGRAMS:
        return False
    if base == 'git':
        return not read_only_git(arguments)
    if base in COMMAND_SHELLS:
        return not (len(arguments) > 1 and arguments[0].text == '-c' and not arguments[0].dynamic)
    return True


def read_only_git(arguments: Sequence[Word]) -> bool:
    """A git command that only reads: a listed subcommand without a file-writing option."""
    layout = git_layout(arguments)
    if layout.unknown:
        return False
    if layout.index is None:
        return True
    subcommand = arguments[layout.index]
    if subcommand.dynamic or subcommand.text not in READ_ONLY_GIT_SUBCOMMANDS:
        return False
    return not any(word.dynamic or word.text.startswith(WRITING_GIT_OPTIONS)
                   for word in arguments[layout.index + 1:])


def pop_directory(arguments: Sequence[Word], scope: Scope) -> None:
    if arguments or not scope.stack:
        scope.uncertain = True
        return
    directory, logical, uncertain = scope.stack.pop()
    scope.directory, scope.logical, scope.uncertain = directory, logical, uncertain
    scope.last_known = directory or scope.last_known


def accessible_directory(path: str) -> bool:
    return os.path.isdir(path) and os.access(path, os.X_OK)


def note_names(names: Iterable[str], scope: Scope) -> None:
    """Remember assigned or exported names that redirect git; CDPATH defeats the walk."""
    listed = tuple(names)
    scope.names += tuple(name for name in listed if is_sensitive_name(name))
    if 'CDPATH' in listed or DYNAMIC_NAME in listed:
        scope.sticky = True


def exported_name(word: Word) -> str:
    match = VARIABLE_NAME.match(word.text)
    complete = match is not None and word.text[match.end():match.end() + 1] in ('', '=', '+')
    return match.group(0) if match and complete else DYNAMIC_NAME


def child_depth(depth: int) -> int:
    if depth + 1 > MAX_DEPTH:
        raise LimitExceeded('depth')
    return depth + 1


def is_git_name(name: str) -> bool:
    return name.startswith('GIT_') or name == DYNAMIC_NAME


def is_sensitive_name(name: str) -> bool:
    """Names that decide which repository, configuration or git binary is used."""
    return is_git_name(name) or name in SENSITIVE_NAMES


def strip_wrappers(words: list[Word], environment: list[Word]) -> tuple[list[Word], list[Word]] | None:
    """Remove supported wrappers, matched by basename; None for an unsupported use."""
    while words and not words[0].dynamic:
        name, rest = words[0].text.rsplit('/', 1)[-1], words[1:]
        if name in SIMPLE_WRAPPERS:
            if rest and (rest[0].dynamic or rest[0].text.startswith('-')):
                return None
        elif name == 'env':
            while rest and ASSIGNMENT.match(rest[0].text):
                environment.append(rest.pop(0))
            if rest and rest[0].text.startswith('-'):
                return None
        elif name == 'timeout':
            if not rest or rest[0].dynamic or not DURATION.fullmatch(rest[0].text):
                return None
            rest = rest[1:]
        else:
            break
        words = rest
    return words, environment


def is_opaque_program(name: str, base: str, arguments: list[Word]) -> bool:
    if name in OPAQUE_PROGRAMS or base in OPAQUE_PROGRAMS:
        return True
    if base == 'find' and any(word.text in FIND_EXECUTION for word in arguments):
        return True
    return base in OTHER_SHELLS and (shell_runs_string(arguments) or shell_reads_stdin(arguments))


def runs_git_word(base: str, arguments: Sequence[Word]) -> bool:
    """A program that may execute its arguments is given a git or gh program word."""
    if base in DATA_PROGRAMS:
        return False
    return any(not word.dynamic and word.text.rsplit('/', 1)[-1] in ('git', 'gh') for word in arguments)


def shell_runs_string(arguments: list[Word]) -> bool:
    """Whether leading shell options include -c in any spelling, or cannot be read."""
    index = 0
    while index < len(arguments):
        word = arguments[index]
        if word.dynamic:
            return True
        if not word.text.startswith(('-', '+')) or word.text in ('-', '--'):
            return False
        if word.text[0] == '-' and not word.text.startswith('--') and 'c' in word.text[1:]:
            return True
        index += 2 if word.text in SHELL_VALUE_OPTIONS else 1
    return False


def shell_reads_stdin(arguments: Sequence[Word]) -> bool:
    """Whether the shell takes its commands from stdin: no script operand, `-s` or `-`."""
    index = 0
    while index < len(arguments):
        word = arguments[index]
        if word.dynamic or word.text == '-':
            return True
        if word.text == '--':
            return index + 1 >= len(arguments)
        if word.text in SHELL_VALUE_OPTIONS:
            index += 2
        elif word.text.startswith('--'):
            index += 1
        elif word.text[:1] in ('-', '+') and len(word.text) > 1:
            if word.text[0] == '-' and 's' in word.text[1:]:
                return True
            index += 1
        else:
            return False
    return True


def skip_quoted(text: str, index: int) -> int:
    """The index after the escape, single-quoted or double-quoted span at index."""
    char = text[index]
    if char == '\\':
        return index + 2
    position = index + 1
    while position < len(text) and text[position] != char:
        position += 2 if char == '"' and text[position] == '\\' else 1
    if position >= len(text):
        raise ParseError('unterminated quote in expansion')
    return position + 1


def gh_positionals(words: Sequence[Word]) -> list[int]:
    """Indexes of the first two gh command words, skipping flags and --repo values."""
    positions: list[int] = []
    index = 0
    while index < len(words) and len(positions) < 2:
        word = words[index]
        if not word.dynamic and word.text in GH_VALUE_FLAGS:
            index += 2
            continue
        if word.dynamic or not word.text.startswith('-') or word.text == '-':
            positions.append(index)
        index += 1
    return positions


# ── Git command layout ─────────────────────────────────────────────────

def git_layout(words: Sequence[Word]) -> GitLayout:
    index = 0
    while index < len(words):
        word = words[index]
        if word.dynamic:
            return GitLayout(index, index, False)
        text = word.text
        if text in GLOBAL_VALUE_OPTIONS:
            if index + 1 >= len(words):
                return GitLayout(len(words), None, False)
            index += 2
        elif text in GLOBAL_FLAGS or text.startswith(GLOBAL_ATTACHED_PREFIXES):
            index += 1
        elif text.startswith('-'):
            return GitLayout(index, None, True)
        else:
            return GitLayout(index, index, False)
    return GitLayout(len(words), None, False)


def unsupported_global_options(words: Sequence[Word]) -> bool:
    index = 0
    while index < len(words):
        word = words[index]
        if word.dynamic:
            return True
        if word.text == '-C':
            if index + 1 < len(words) and words[index + 1].dynamic:
                return True
            index += 2
            continue
        if word.text not in ACCEPTED_GLOBAL_FLAGS:
            return True
        index += 1
    return False


def effective_directory(found: Found) -> str:
    """Apply every literal `git -C`; a dynamic value leaves the directory before it."""
    directory = found.directory
    if found.program != 'git':
        return directory
    layout = git_layout(found.words)
    index = 0
    while index < layout.globals_end:
        word = found.words[index]
        if word.text == '-C' and index + 1 < len(found.words):
            value = found.words[index + 1]
            if value.dynamic:
                break
            if value.text:
                directory = os.path.realpath(os.path.join(directory, value.text))
            index += 2
        else:
            index += 2 if word.text in GLOBAL_VALUE_OPTIONS else 1
    return directory


def rule_key(invocation: Invocation) -> str | None:
    """The dispatch-table key of a governed invocation, or None."""
    words = invocation.words
    if invocation.program == 'gh':
        command = [words[index] for index in gh_positionals(words)]
        if not command or command[0].dynamic:
            return None
        if command[0].text == 'api':
            return 'gh api'
        literal = len(command) == 2 and not command[1].dynamic
        return 'gh pr merge' if literal and [word.text for word in command] == ['pr', 'merge'] else None
    index = git_layout(words).index
    if index is None or words[index].dynamic or words[index].text not in GOVERNED_GIT_SUBCOMMANDS:
        return None
    return words[index].text


def needs_verification(invocation: Invocation) -> bool:
    """Governed, or possibly governed: a dynamic subcommand or a name that may be an alias."""
    if invocation.governed:
        return True
    words = invocation.words
    if invocation.program == 'gh':
        command = [words[index] for index in gh_positionals(words)]
        return bool(command) and (command[0].dynamic or (command[0].text == 'pr' and len(command) > 1
                                                         and command[1].dynamic))
    layout = git_layout(words)
    if layout.unknown:
        return True
    if layout.index is None:
        return False
    subcommand = words[layout.index]
    return subcommand.dynamic or subcommand.text not in GIT_BUILTINS


# ── Sanitized git reads ────────────────────────────────────────────────

class GitReadTimeout(Exception):
    """A git read exceeded its time limit."""


@dataclass(frozen=True)
class GitRead:
    returncode: int
    stdout: str


def git_environment(environ: Mapping[str, str]) -> dict[str, str]:
    environment = {key: value for key, value in environ.items() if key not in SANITIZED_GIT_VARIABLES}
    environment['GIT_OPTIONAL_LOCKS'] = '0'
    environment['GIT_TERMINAL_PROMPT'] = '0'
    return environment


def read_git(arguments: Sequence[str], directory: str, environ: Mapping[str, str]) -> GitRead:
    """Run one read-only git command; the whole process group is killed on timeout."""
    process = subprocess.Popen(['git', '-c', 'core.fsmonitor=false', *arguments], cwd=directory,
                               env=git_environment(environ), stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               start_new_session=True)
    try:
        output, _ = process.communicate(timeout=GIT_READ_SECONDS)
    except subprocess.TimeoutExpired:
        stop_process_group(process)
        raise GitReadTimeout(' '.join(arguments)) from None
    return GitRead(process.returncode, output.decode('utf-8', 'surrogateescape'))


def stop_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        process.kill()
    process.communicate()


def read_repository(directory: str, environ: Mapping[str, str]) -> tuple[str, str] | None:
    """Top level and common directory, or None outside a work tree."""
    result = read_git(['rev-parse', '--path-format=absolute', '--show-toplevel', '--git-common-dir'],
                      directory, environ)
    lines = result.stdout.split('\n')
    if result.returncode != 0 or len(lines) < 2 or not lines[0] or not lines[1]:
        return None
    return lines[0], lines[1]


def is_alias(name: str, directory: str, environ: Mapping[str, str]) -> bool:
    return read_git(['config', '--get', 'alias.' + name], directory, environ).returncode == 0


# ── Resolution ─────────────────────────────────────────────────────────

def resolve(command: str, context: Context) -> Resolution:
    """Parse the command and resolve every git/gh invocation inside registered work trees."""
    registered = project_for(context.cwd, context.roots) is not None
    budget = Budget()
    try:
        walker = Walker(budget, context.cwd)
        walker.walk_script(parse_script(command, budget), Scope(context.cwd, context.cwd, context.cwd))
    except ParseError:
        return Resolution((), denial('unsupported-form') if registered else NOT_APPLICABLE)
    except LimitExceeded:
        return Resolution((), denial('limit-exceeded') if registered else NOT_APPLICABLE)
    try:
        return resolve_items(walker.items, context)
    except GitReadTimeout:
        return Resolution((), denial('limit-exceeded'))
    except OSError:
        return Resolution((), denial('internal-error'))


def resolve_items(items: Sequence[Found | Opaque], context: Context) -> Resolution:
    invocations: list[Invocation] = []
    denials: list[Decision] = []
    for item in items:
        if isinstance(item, Opaque):
            if anchored(item.anchors, context):
                denials.append(denial('unsupported-form'))
            continue
        result = resolve_found(item, context)
        if isinstance(result, Decision):
            denials.append(result)
        elif result is not None:
            invocations.append(result)
    return Resolution(tuple(invocations), combine(denials) if denials else None)


def anchored(paths: Iterable[str], context: Context) -> bool:
    return any(project_for(path, context.roots) is not None for path in paths)


def resolve_found(found: Found, context: Context) -> Invocation | Decision | None:
    directory = effective_directory(found)
    project = project_for(directory, context.roots)
    draft = Invocation(found.program, found.words, directory, None, None, project or '',
                       found.environment, found.inherited, found.stdin)
    if found.uncertain:
        verify = needs_verification(draft) and anchored((*found.anchors, directory), context)
        return denial('unsupported-form') if verify else None
    if project is None:
        return redirected(draft, found, context)
    if not os.path.isdir(directory):
        return denial('unsupported-form') if needs_verification(draft) else None
    location = read_repository(directory, context.environ)
    if location is None:
        if found.changed and needs_verification(draft):
            return denial('unsupported-form')
        return redirected(draft, found, context)
    subcommand = draft.subcommand if found.program == 'git' else None
    alias = (subcommand is not None and not draft.words[draft.layout.index or 0].dynamic
             and subcommand not in GIT_BUILTINS and is_alias(subcommand, directory, context.environ))
    return replace(draft, repository=location[0], common_dir=location[1], alias=alias,
                   state_changed=found.changed)


# ── Rules ──────────────────────────────────────────────────────────────

Rule = Callable[[Invocation, Context], Decision | None]

# Options of the governed subcommands, as git's parse-options declares them.
ADD_OPTIONS = (
    OptionSpec('dry-run', 'n'), OptionSpec('verbose', 'v'), OptionSpec('interactive', 'i'),
    OptionSpec('patch', 'p'), OptionSpec('unified', 'U', 'required', negatable=False),
    OptionSpec('inter-hunk-context', None, 'required', negatable=False), OptionSpec('edit', 'e'),
    OptionSpec('force', 'f'), OptionSpec('update', 'u'), OptionSpec('renormalize'),
    OptionSpec('intent-to-add', 'N'), OptionSpec('all', 'A'), OptionSpec('ignore-removal'),
    OptionSpec('refresh'), OptionSpec('ignore-errors'), OptionSpec('ignore-missing'), OptionSpec('sparse'),
    OptionSpec('chmod', None, 'required'), OptionSpec('pathspec-from-file', None, 'required'),
    OptionSpec('pathspec-file-nul'))
COMMIT_OPTIONS = (
    OptionSpec('quiet', 'q'), OptionSpec('verbose', 'v'), OptionSpec('file', 'F', 'required'),
    OptionSpec('author', None, 'required'), OptionSpec('date', None, 'required'),
    OptionSpec('message', 'm', 'required', repeatable=True), OptionSpec('reedit-message', 'c', 'required'),
    OptionSpec('reuse-message', 'C', 'required'), OptionSpec('fixup', None, 'required'),
    OptionSpec('squash', None, 'required'), OptionSpec('reset-author'),
    OptionSpec('trailer', None, 'required', repeatable=True, negatable=False), OptionSpec('signoff', 's'),
    OptionSpec('template', 't', 'required'), OptionSpec('edit', 'e'), OptionSpec('cleanup', None, 'required'),
    OptionSpec('status'), OptionSpec('gpg-sign', 'S', 'optional'), OptionSpec('all', 'a'),
    OptionSpec('include', 'i'), OptionSpec('interactive'), OptionSpec('patch', 'p'),
    OptionSpec('unified', 'U', 'required', negatable=False),
    OptionSpec('inter-hunk-context', None, 'required', negatable=False), OptionSpec('only', 'o'),
    OptionSpec('no-verify', 'n', negatable=False), OptionSpec('verify'), OptionSpec('dry-run'),
    OptionSpec('short'), OptionSpec('branch'), OptionSpec('ahead-behind'), OptionSpec('porcelain'),
    OptionSpec('long'), OptionSpec('null', 'z'), OptionSpec('amend'),
    OptionSpec('no-post-rewrite', negatable=False), OptionSpec('post-rewrite'),
    OptionSpec('untracked-files', 'u', 'optional'), OptionSpec('pathspec-from-file', None, 'required'),
    OptionSpec('pathspec-file-nul'), OptionSpec('allow-empty'), OptionSpec('allow-empty-message'))


# ── Option variants ────────────────────────────────────────────────────

def option_variants(words: Sequence[str], specs: Sequence[OptionSpec]) -> list[ParsedOptions] | None:
    """Every reading of the words: an ambiguous long prefix stands for each candidate.

    None means the readings exceed MAX_OPTION_VARIANTS and cannot all be checked.
    """
    pending, done = [list(words)], []
    while pending:
        current = pending.pop(0)
        parsed = parse_options(current, specs)
        if parsed.error != 'ambiguous-option':
            done.append(parsed)
            continue
        index = ambiguous_index(current, specs)
        pending.extend(spelled_out(current, index, name) for name in parsed.candidates)
        if len(pending) + len(done) > MAX_OPTION_VARIANTS:
            return None
    return done


def ambiguous_index(words: Sequence[str], specs: Sequence[OptionSpec]) -> int:
    """The index of the first word that parse-options reports as ambiguous."""
    for end in range(1, len(words) + 1):
        if parse_options(words[:end], specs).error == 'ambiguous-option':
            return end - 1
    return len(words) - 1


def spelled_out(words: Sequence[str], index: int, name: str) -> list[str]:
    """The words with the ambiguous prefix replaced by one full candidate name."""
    prefix, equals, value = words[index][2:].partition('=')
    option = name if name.startswith(prefix) else 'no-' + name
    return [*words[:index], '--' + option + equals + value, *words[index + 1:]]


def state_changed(invocation: Invocation) -> bool:
    """Call before reading repository or file state: an earlier part of the same command
    may have written, so the read would describe state the invocation will not see."""
    return invocation.state_changed


def usable(variants: list[ParsedOptions] | None) -> list[ParsedOptions]:
    return [parsed for parsed in variants or [] if parsed.error is None]


def asking(reason: str, rule: str, failure: str | None = None) -> Decision:
    return Decision('ask', reason, rule, failure)


# ── Path operands ──────────────────────────────────────────────────────

def operand_reason(parsed: ParsedOptions, invocation: Invocation, context: Context) -> str | None:
    """The staging reason an operand list fails with, or None when every operand is a file."""
    if '.' in parsed.operands:
        return BLANKET_STAGING
    if parsed.last('pathspec-from-file') not in (None, False):
        return STAGING_NOT_FILE
    if parsed.operands and state_changed(invocation):
        return 'unsupported-form'
    return None if literal_files(parsed.operands, invocation, context) else STAGING_NOT_FILE


def path_kind(operand: str, directory: str) -> str:
    """'file' (including any symlink), 'missing', or 'other' for directories and patterns."""
    if not operand or operand.startswith(':') or '\x00' in operand:
        return 'other'
    if any(char in GLOB_CHARACTERS for char in operand):
        return 'other'
    path = os.path.join(directory, operand)
    if os.path.islink(path):
        return 'file'
    if os.path.isdir(path):
        return 'other'
    return 'file' if os.path.lexists(path) else 'missing'


def literal_files(operands: Sequence[str], invocation: Invocation, context: Context) -> bool:
    """Every operand exists as a file or symlink, or is a tracked path deleted from the work tree."""
    missing: list[str] = []
    for operand in operands:
        kind = path_kind(operand, invocation.directory)
        if kind == 'other':
            return False
        if kind == 'missing':
            missing.append(operand)
    return not missing or tracked_paths(missing, invocation, context)


def tracked_paths(paths: Sequence[str], invocation: Invocation, context: Context) -> bool:
    result = read_git(['--literal-pathspecs', 'ls-files', '-z', '--', *paths], invocation.directory,
                      context.environ)
    if result.returncode != 0:
        return False
    directory = invocation.directory
    listed = {os.path.normpath(os.path.join(directory, entry)) for entry in result.stdout.split('\x00') if entry}
    return all(os.path.normpath(os.path.join(directory, path)) in listed for path in paths)


# ── Staging rules ──────────────────────────────────────────────────────

def staging_options(invocation: Invocation) -> list[ParsedOptions] | None:
    return option_variants(invocation.argv, ADD_OPTIONS)


def adds_everything(parsed: ParsedOptions) -> bool:
    """--all and --ignore-removal share one setting in git; the last of them decides."""
    removal: OptionValue | None = None
    for name, value in parsed.options:
        if name == 'all':
            removal = value
        elif name == 'ignore-removal':
            removal = not value
    return removal is True or parsed.last('update') is True or parsed.last('renormalize') is True


def check_staging_options(invocation: Invocation, context: Context) -> Decision | None:
    """Options git would reject, or more readings than can be checked, cannot be verified."""
    variants = staging_options(invocation)
    if variants is None or any(parsed.error for parsed in variants):
        return denial('unsupported-form')
    return None


def check_blanket_staging(invocation: Invocation, context: Context) -> Decision | None:
    """R01: update-all flags or the current directory as an operand."""
    for parsed in usable(staging_options(invocation)):
        if adds_everything(parsed) or '.' in parsed.operands:
            return denial(BLANKET_STAGING, 'R01')
    return None


def check_staging_not_file(invocation: Invocation, context: Context) -> Decision | None:
    """R02: directories, patterns, pathspec magic, unknown paths or a pathspec file."""
    for parsed in usable(staging_options(invocation)):
        reason = operand_reason(parsed, invocation, context)
        if reason in (STAGING_NOT_FILE, 'unsupported-form'):
            return denial(reason, 'R02')
    return None


def check_interactive_staging(invocation: Invocation, context: Context) -> Decision | None:
    """R03: interactive forms choose content that cannot be checked in advance."""
    for parsed in usable(staging_options(invocation)):
        if any(parsed.last(key) is True for key in INTERACTIVE_OPTIONS):
            return denial('unsupported-form', 'R03')
    return None


def check_ignored_path(invocation: Invocation, context: Context) -> Decision | None:
    """R04: forcing a path the repository's own ignore rules exclude needs the owner."""
    for parsed in usable(staging_options(invocation)):
        if parsed.last('force') is not True or not parsed.operands:
            continue
        if state_changed(invocation):
            return denial('unsupported-form', 'R04')
        result = read_git(['check-ignore', '--', *parsed.operands], invocation.directory, context.environ)
        if result.returncode == 0:
            return asking('staging-ignored-path', 'R04')
        if result.returncode != 1:
            return denial('unsupported-form', 'R04')
    return None


# ── Commit rules ───────────────────────────────────────────────────────

def option_words(invocation: Invocation) -> list[str]:
    """Argument texts; the commit-message heredoc word becomes a NUL-led placeholder."""
    return [MESSAGE_PLACEHOLDER + str(index) if word.form == 'commit-message' else word.text
            for index, word in enumerate(invocation.arguments)]


def placeholder_messages(invocation: Invocation) -> dict[str, str | None]:
    return {MESSAGE_PLACEHOLDER + str(index): word.message
            for index, word in enumerate(invocation.arguments) if word.form == 'commit-message'}


def commit_options(invocation: Invocation) -> list[ParsedOptions] | None:
    return option_variants(option_words(invocation), COMMIT_OPTIONS)


def check_commit_options(invocation: Invocation, context: Context) -> Decision | None:
    """Rejected options, too many readings, or a message heredoc used as anything but -m."""
    variants = commit_options(invocation)
    if variants is None or any(parsed.error for parsed in variants):
        return denial('unsupported-form')
    placeholders = set(placeholder_messages(invocation))
    for parsed in variants:
        if placeholders - set(parsed.every('message')):
            return denial('unsupported-form', 'R31')
    return None


def check_commit_all(invocation: Invocation, context: Context) -> Decision | None:
    """R06: -a and --all, alone or bundled."""
    if any(parsed.last('all') is True for parsed in usable(commit_options(invocation))):
        return denial('commit-all', 'R06')
    return None


def check_commit_paths(invocation: Invocation, context: Context) -> Decision | None:
    """R07: commit path operands, with or without -i/-o, are checked like staging operands."""
    for parsed in usable(commit_options(invocation)):
        reason = operand_reason(parsed, invocation, context)
        if reason is not None:
            return denial(reason, 'R07')
    return None


def check_commit_message(invocation: Invocation, context: Context) -> Decision | None:
    """R08 and R09: the message must be readable statically and free of forbidden patterns."""
    results: list[Decision] = []
    for parsed in usable(commit_options(invocation)):
        text = commit_text(parsed, invocation, context)
        if text is None:
            results.append(denial(UNVERIFIABLE_MESSAGE, 'R08'))
        elif forbidden_message(text):
            results.append(denial('commit-message-forbidden', 'R09'))
    return combine(results) if results else None


def check_rewrite_published(invocation: Invocation, context: Context) -> Decision | None:
    """R10: amending a commit that any remote-tracking ref already contains."""
    if not any(parsed.last('amend') is True for parsed in usable(commit_options(invocation))):
        return None
    if state_changed(invocation):
        return denial('unsupported-form', 'R10')
    result = read_git(['for-each-ref', '--contains', 'HEAD', '--format=%(refname)', 'refs/remotes/'],
                      invocation.directory, context.environ)
    if result.returncode != 0:
        return denial('unsupported-form', 'R10')
    return asking('rewrite-published', 'R10') if result.stdout.strip() else None


# ── Commit messages ────────────────────────────────────────────────────

def commit_text(parsed: ParsedOptions, invocation: Invocation, context: Context) -> str | None:
    """The full text git would record, or None when it cannot be read statically."""
    if any(parsed.last(key) not in (None, False) for key in REUSED_MESSAGE_OPTIONS):
        return None
    if parsed.last('edit') is True:
        return None
    body = message_body(parsed, invocation, context)
    trailers = [str(value) for value in parsed.every('trailer')]
    if body is None or (trailers and trailers_configured(invocation, context)):
        return None
    return join_message([body], trailers)


def message_body(parsed: ParsedOptions, invocation: Invocation, context: Context) -> str | None:
    """-F text, then every -m value; --amend --no-edit alone keeps the HEAD message."""
    parts: list[str | None] = []
    source = parsed.last('file')
    if isinstance(source, str):
        parts.append(message_file(source, invocation))
    known = placeholder_messages(invocation)
    parts.extend(known.get(value, value) if isinstance(value, str) else None
                 for value in parsed.every('message'))
    if not parts and parsed.last('amend') is True and parsed.last('edit') is False:
        parts.append(head_message(invocation, context))
    if not parts or any(part is None for part in parts):
        return None
    return '\n\n'.join(part for part in parts if part is not None)


def message_file(value: str, invocation: Invocation) -> str | None:
    """-F text: the literal heredoc or here-string for '-', else the file's bytes."""
    if MESSAGE_PLACEHOLDER in value:
        return None
    if value == '-':
        stdin = invocation.stdin
        return None if stdin is None or stdin.dynamic else stdin.text
    if state_changed(invocation):
        return None
    return read_message_file(os.path.join(invocation.directory, value))


def read_message_file(path: str) -> str | None:
    """A regular file of at most MAX_MESSAGE_FILE_BYTES; opening never blocks on a FIFO."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    except OSError:
        return None
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        return None
    with os.fdopen(descriptor, 'rb') as stream:
        data = stream.read(MAX_MESSAGE_FILE_BYTES + 1)
    if len(data) > MAX_MESSAGE_FILE_BYTES:
        return None
    return data.decode('utf-8', 'surrogateescape')


def head_message(invocation: Invocation, context: Context) -> str | None:
    if state_changed(invocation):
        return None
    result = read_git(['log', '-1', '--format=%B', 'HEAD'], invocation.directory, context.environ)
    return result.stdout if result.returncode == 0 else None


def trailers_configured(invocation: Invocation, context: Context) -> bool:
    """Trailer configuration can rename or generate trailers, so any of it is unverifiable."""
    if state_changed(invocation):
        return True
    result = read_git(['config', '--get-regexp', r'^trailer\.'], invocation.directory, context.environ)
    return result.returncode != 1


def trailer_line(value: str) -> str:
    """A --trailer value in the 'token: value' form git records."""
    cuts = [index for index in (value.find('='), value.find(':')) if index >= 0]
    if not cuts:
        return value.strip() + ':'
    cut = min(cuts)
    return f'{value[:cut].strip()}: {value[cut + 1:].strip()}'.rstrip()


def join_message(messages: Sequence[str], trailers: Sequence[str]) -> str:
    """Message values as paragraphs, as git joins repeated -m, then the trailers."""
    text = '\n\n'.join(messages)
    if trailers:
        text += '\n\n' + '\n'.join(trailer_line(value) for value in trailers)
    return text


def forbidden_message(text: str) -> bool:
    return any(pattern.search(text) for pattern in FORBIDDEN_PATTERNS)


# ── Protected refs ─────────────────────────────────────────────────────

DEFAULT_PROTECTED = ('main', 'master', 'release/*')
BRANCH_PREFIX = 'refs/heads/'
TAG_PREFIX = 'refs/tags/'
PARTIAL_PREFIXES = ('heads/', 'tags/')


def protected_branches(remote: str | None, invocation: Invocation, context: Context) -> tuple[str, ...] | None:
    """Protected branch names and patterns for a target remote, or None when the remote's
    default branch is unknown. Without a remote only the fixed and configured entries apply.
    Callers check state_changed(invocation) first."""
    names: list[str] = []
    if remote is not None:
        default = remote_default_branch(remote, invocation, context)
        if default is None:
            return None
        names.append(default)
    result = read_git(['config', '--get-all', 'orchestrail.protectedBranch'], invocation.directory,
                      context.environ)
    if result.returncode not in (0, 1):
        return None
    configured = [line for line in result.stdout.split('\n') if line] if result.returncode == 0 else []
    return tuple(dict.fromkeys([*names, *DEFAULT_PROTECTED, *configured]))


def remote_default_branch(remote: str, invocation: Invocation, context: Context) -> str | None:
    """The branch refs/remotes/<remote>/HEAD points to, or None when it is not a symbolic ref."""
    prefix = f'refs/remotes/{remote}/'
    result = read_git(['symbolic-ref', '-q', prefix + 'HEAD'], invocation.directory, context.environ)
    target = result.stdout.strip()
    if result.returncode != 0 or not target.startswith(prefix) or target == prefix:
        return None
    return target[len(prefix):]


def local_protected_branches(invocation: Invocation, context: Context) -> tuple[str, ...] | None:
    """The set for operations on local branches: origin's, or the fixed and configured
    entries when origin is not configured; None when origin has no known default branch."""
    result = read_git(['config', '--get', 'remote.origin.url'], invocation.directory, context.environ)
    if result.returncode not in (0, 1):
        return None
    return protected_branches('origin' if result.returncode == 0 else None, invocation, context)


def is_protected(ref: str, patterns: Sequence[str]) -> bool:
    """A branch ref whose short name matches any protected name or pattern."""
    if not ref.startswith(BRANCH_PREFIX):
        return False
    name = ref[len(BRANCH_PREFIX):]
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


# ── Push targets ───────────────────────────────────────────────────────

PUSH_OPTIONS = (
    OptionSpec('verbose', 'v'), OptionSpec('quiet', 'q'), OptionSpec('repo', None, 'required'),
    OptionSpec('all'), OptionSpec('branches'), OptionSpec('mirror'), OptionSpec('delete', 'd'),
    OptionSpec('tags'), OptionSpec('dry-run', 'n'), OptionSpec('porcelain'), OptionSpec('force', 'f'),
    OptionSpec('force-with-lease', None, 'optional', repeatable=True), OptionSpec('force-if-includes'),
    OptionSpec('recurse-submodules', None, 'required'), OptionSpec('thin'),
    OptionSpec('receive-pack', None, 'required'), OptionSpec('exec', None, 'required'),
    OptionSpec('set-upstream', 'u'), OptionSpec('progress'), OptionSpec('prune'),
    OptionSpec('no-verify', negatable=False), OptionSpec('verify'), OptionSpec('follow-tags'),
    OptionSpec('signed', None, 'optional'), OptionSpec('atomic'),
    OptionSpec('push-option', 'o', 'required', repeatable=True), OptionSpec('ipv4', '4', negatable=False),
    OptionSpec('ipv6', '6', negatable=False))
# Options that push refs no refspec names; the first four also replace push.default.
BULK_PUSH_OPTIONS = ('all', 'branches', 'mirror', 'tags', 'follow-tags')
PROGRAM_PUSH_OPTIONS = ('receive-pack', 'exec')
SAFE_SUBMODULE_MODES = (None, False, 'check', 'no')
FALSE_CONFIG_VALUES = frozenset({'false', 'no', 'off', '0', ''})
LEASE_SHA = re.compile(r'[0-9a-f]{40}([0-9a-f]{24})?')
PUSH_TARGET_UNKNOWN = 'push-target-unknown'
LEASE_UNVERIFIED = 'push-lease-unverified'


@dataclass(frozen=True)
class PushState:
    """The configuration snapshot and the current branch (None when detached) a push reads."""
    config: Mapping[str, tuple[str, ...]]
    branch: str | None


@dataclass(frozen=True)
class Refspec:
    """One refspec: forced by '+', its source, and its destination; both empty means matching."""
    forced: bool
    source: str
    destination: str

    @property
    def matching(self: Refspec) -> bool:
        return not self.source and not self.destination

    @property
    def deletion(self: Refspec) -> bool:
        return not self.source and bool(self.destination)


@dataclass(frozen=True)
class PushPlan:
    """The resolved target remote, every refspec with a full destination ref, and whether
    the remote's configuration pushes refs beyond them."""
    remote: str
    refspecs: tuple[Refspec, ...]
    bulk: bool


def read_push_state(invocation: Invocation, context: Context) -> PushState | None:
    listing = read_git(['config', '-z', '--list'], invocation.directory, context.environ)
    head = read_git(['symbolic-ref', '-q', 'HEAD'], invocation.directory, context.environ)
    if listing.returncode != 0 or head.returncode not in (0, 1):
        return None
    ref = head.stdout.strip()
    branch = ref[len(BRANCH_PREFIX):] if head.returncode == 0 and ref.startswith(BRANCH_PREFIX) else None
    return PushState(parse_config(listing.stdout), branch)


def parse_config(text: str) -> dict[str, tuple[str, ...]]:
    """`git config -z --list` entries; a key without a value is the boolean true."""
    values: dict[str, tuple[str, ...]] = {}
    for entry in text.split('\x00'):
        if entry:
            key, newline, value = entry.partition('\n')
            values[key] = (*values.get(key, ()), value if newline else 'true')
    return values


def setting(state: PushState, key: str) -> str | None:
    """The last value of a key whose section and variable names are lower case."""
    values = state.config.get(key)
    return values[-1] if values else None


def config_true(value: str | None) -> bool:
    return value is not None and value.lower() not in FALSE_CONFIG_VALUES


def push_remote(parsed: ParsedOptions, state: PushState) -> str | None:
    """The configured remote the push targets; a URL, a path, an unknown name or a remote
    with configured push refspecs cannot be resolved."""
    repository = parsed.last('repo')
    if parsed.operands:
        name = parsed.operands[0]
    elif isinstance(repository, str):
        name = repository
    else:
        name = default_remote(state)
    if setting(state, f'remote.{name}.url') is None or setting(state, f'remote.{name}.push') is not None:
        return None
    return name


def default_remote(state: PushState) -> str:
    """branch.<current>.pushRemote, remote.pushDefault, branch.<current>.remote, then origin."""
    branch = state.branch
    keys = [f'branch.{branch}.pushremote'] if branch else []
    keys += ['remote.pushdefault', *([f'branch.{branch}.remote'] if branch else [])]
    for key in keys:
        value = setting(state, key)
        if value:
            return value
    return 'origin'


def refspec_words(parsed: ParsedOptions) -> list[str] | None:
    """Refspec operands after the remote; `tag <name>` is a tag ref, and --delete names refs."""
    words: list[str] = []
    index, operands = 0, parsed.operands[1:]
    while index < len(operands):
        if operands[index] == 'tag':
            if index + 1 >= len(operands):
                return None
            words.append(TAG_PREFIX + operands[index + 1])
            index += 2
            continue
        words.append(operands[index])
        index += 1
    if parsed.last('delete') is not True:
        return words
    if any(':' in word or word.startswith('+') for word in words):
        return None
    return [':' + word for word in words]


def split_refspec(text: str, state: PushState) -> Refspec | None:
    """`[+]<src>[:<dst>]`; HEAD is the current branch, and a pattern cannot be resolved."""
    forced = text.startswith('+')
    body = text[1:] if forced else text
    if not body or body.startswith('^') or any(char in GLOB_CHARACTERS for char in body):
        return None
    source, colon, destination = body.partition(':')
    if colon and source and not destination:
        return None
    source, destination = full_name(source), full_name(destination)
    if source in ('HEAD', '@'):
        if state.branch is None:
            return None
        source = BRANCH_PREFIX + state.branch
    return Refspec(forced, source, destination if colon else source)


def full_name(name: str) -> str:
    """git matches refs/<name> first, so a short name under heads/ or tags/ names that ref.
    Where git would instead create refs/heads/heads/<name>, this reading fails closed."""
    return 'refs/' + name if name.startswith(PARTIAL_PREFIXES) else name


def default_refspecs(parsed: ParsedOptions, state: PushState) -> tuple[Refspec, ...] | None:
    """The refspec push.default (unset means simple) gives a push without refspecs."""
    if any(parsed.last(key) is True for key in BULK_PUSH_OPTIONS[:4]):
        return ()
    mode = setting(state, 'push.default') or 'simple'
    if mode == 'matching':
        return (Refspec(False, '', ''),)
    branch = state.branch
    if branch is None or mode not in ('simple', 'current', 'upstream', 'tracking'):
        return None
    current = BRANCH_PREFIX + branch
    if mode in ('simple', 'current'):
        return (Refspec(False, current, current),)
    merge = setting(state, f'branch.{branch}.merge')
    return (Refspec(False, current, merge),) if merge else None


def requested_refspecs(parsed: ParsedOptions, state: PushState) -> tuple[Refspec, ...] | None:
    words = refspec_words(parsed)
    if words is None:
        return None
    if not words:
        return default_refspecs(parsed, state)
    specs = [split_refspec(word, state) for word in words]
    resolved = tuple(spec for spec in specs if spec is not None)
    return resolved if len(resolved) == len(specs) else None


def tag_only_sources(specs: Sequence[Refspec], invocation: Invocation, context: Context) -> frozenset[str] | None:
    """Short source names that name a tag and no branch."""
    names = sorted({spec.source for spec in specs if spec.source and not spec.source.startswith('refs/')})
    if not names:
        return frozenset()
    patterns = [prefix + name for name in names for prefix in (BRANCH_PREFIX, TAG_PREFIX)]
    result = read_git(['for-each-ref', '--format=%(refname)', *patterns], invocation.directory,
                      context.environ)
    if result.returncode != 0:
        return None
    refs = set(result.stdout.split('\n'))
    return frozenset(name for name in names if TAG_PREFIX + name in refs and BRANCH_PREFIX + name not in refs)


def qualified(spec: Refspec, tags: frozenset[str]) -> Refspec:
    """A short destination is a branch, or a tag when the source is only a tag."""
    destination = spec.destination
    if spec.matching or destination.startswith('refs/'):
        return spec
    tag = spec.source.startswith(TAG_PREFIX) or spec.source in tags
    return replace(spec, destination=(TAG_PREFIX if tag else BRANCH_PREFIX) + destination)


def push_plan(parsed: ParsedOptions, invocation: Invocation, context: Context) -> PushPlan | None:
    """The target remote and every destination, or None when any cannot be resolved."""
    state = read_push_state(invocation, context)
    remote = None if state is None else push_remote(parsed, state)
    if state is None or remote is None:
        return None
    specs = requested_refspecs(parsed, state)
    tags = None if specs is None else tag_only_sources(specs, invocation, context)
    if specs is None or tags is None:
        return None
    bulk = config_true(setting(state, 'push.followtags')) or config_true(setting(state, f'remote.{remote}.mirror'))
    return PushPlan(remote, tuple(qualified(spec, tags) for spec in specs), bulk)


# ── Restack recovery journals ──────────────────────────────────────────

JOURNAL_DIRECTORY = 'orchestrail-restack'
JOURNAL_FILE = re.compile(r'[0-9a-f]{64}\.json')
MAX_JOURNAL_BYTES = MAX_MESSAGE_FILE_BYTES
JOURNAL_SHA = re.compile(r'[0-9a-f]{40}|[0-9a-f]{64}')
ABSENT = 'absent'
JOURNAL_MISSING = 'journal-missing'
JOURNAL_UNREADABLE = 'journal-unreadable'
INVALID_JSON = 'journal-invalid-json'
INVALID_SCHEMA = 'journal-invalid-schema'
INVALID_BRANCH = re.compile(r'(^|/)\.|\.lock(/|$)|\.\.|[\x00-\x20\x7f~^:?*\[\\]|^[-/]|/$|//|\.$|@\{')


@dataclass(frozen=True)
class JournalBranch:
    """One stacked branch as /restack recorded it."""
    original_base_commit: str
    original_tip: str
    replayed_tip: str | None
    expected_remote_tip: str | None


@dataclass(frozen=True)
class Journal:
    """A recovery journal that passed the schema and file-name checks."""
    repository: str
    task_path: str
    target: str
    publication_authorized: bool
    order: tuple[str, ...]
    branches: Mapping[str, JournalBranch]


@dataclass(frozen=True)
class JournalScan:
    """Every journal of a common directory, or the check that made the set unusable."""
    journals: tuple[Journal, ...]
    failure: str | None = None


JournalCheck = tuple[str, Callable[[Journal], bool]]


class JournalError(Exception):
    """A journal file that cannot count as evidence; the message names the failed check."""


def valid_branch_name(name: object) -> bool:
    """A branch name git accepts (check-ref-format --branch rules), never an option or HEAD."""
    return isinstance(name, str) and name not in ('', '@', 'HEAD') and INVALID_BRANCH.search(name) is None


def field_value(document: object, key: str) -> object:
    if not isinstance(document, dict) or key not in document:
        raise JournalError(INVALID_SCHEMA)
    return document[key]


def sha_value(document: object, key: str, allowed: tuple[str | None, ...] = ()) -> str | None:
    """A required SHA field; a value listed in allowed (null, "absent") is kept as it is."""
    value = field_value(document, key)
    if value is None and None in allowed:
        return None
    if isinstance(value, str) and (value in allowed or JOURNAL_SHA.fullmatch(value)):
        return value
    raise JournalError(INVALID_SCHEMA)


def required_sha(document: object, key: str) -> str:
    value = sha_value(document, key)
    if value is None:
        raise JournalError(INVALID_SCHEMA)
    return value


def path_value(document: object, key: str) -> str:
    value = field_value(document, key)
    if not isinstance(value, str) or not value.startswith('/'):
        raise JournalError(INVALID_SCHEMA)
    return value


def journal_branch(document: object) -> JournalBranch:
    return JournalBranch(required_sha(document, 'original_base_commit'), required_sha(document, 'original_tip'),
                         sha_value(document, 'replayed_tip', (None,)),
                         sha_value(document, 'expected_remote_tip', (None, ABSENT)))


def journal_order(document: object) -> tuple[str, ...]:
    value = field_value(document, 'order')
    names = [name for name in value if valid_branch_name(name)] if isinstance(value, list) else []
    if not isinstance(value, list) or len(names) != len(value) or len(set(names)) != len(names):
        raise JournalError(INVALID_SCHEMA)
    return tuple(str(name) for name in names)


def journal_branches(document: object, order: Sequence[str]) -> dict[str, JournalBranch]:
    value = field_value(document, 'branches')
    if not isinstance(value, dict) or not all(valid_branch_name(name) for name in value):
        raise JournalError(INVALID_SCHEMA)
    branches = {str(name): journal_branch(entry) for name, entry in value.items()}
    if any(name not in branches for name in order):
        raise JournalError(INVALID_SCHEMA)
    return branches


def journal_record(document: object) -> Journal:
    """The minimum schema: version 1, absolute paths, target, flag, order and branch records."""
    version = field_value(document, 'schema_version')
    target = field_value(document, 'target')
    publication = field_value(document, 'publication_authorized')
    if type(version) is not int or version != 1 or not isinstance(publication, bool):
        raise JournalError(INVALID_SCHEMA)
    if not valid_branch_name(field_value(target, 'branch')):
        raise JournalError(INVALID_SCHEMA)
    order = journal_order(document)
    return Journal(path_value(document, 'repository_common_dir'), path_value(document, 'task_path'),
                   required_sha(target, 'sha'), publication, order, journal_branches(document, order))


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    if len({key for key, _ in pairs}) != len(pairs):
        raise ValueError('duplicate key')
    return dict(pairs)


def read_journal_bytes(path: str) -> bytes | None:
    """A regular file, not a symbolic link, of at most MAX_JOURNAL_BYTES; opening never blocks."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    except OSError:
        return None
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        return None
    with os.fdopen(descriptor, 'rb') as stream:
        data = stream.read(MAX_JOURNAL_BYTES + 1)
    return data if len(data) <= MAX_JOURNAL_BYTES else None


def load_journal(directory: str, name: str) -> Journal:
    """One journal file: bounded read, strict UTF-8 JSON without duplicate keys, the schema,
    and a file name that is the SHA-256 of its task path."""
    data = read_journal_bytes(os.path.join(directory, name))
    if data is None:
        raise JournalError(JOURNAL_UNREADABLE)
    try:
        document = json.loads(data.decode('utf-8'), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise JournalError(INVALID_JSON) from None
    journal = journal_record(document)
    digest = hashlib.sha256(journal.task_path.encode('utf-8', 'surrogatepass')).hexdigest()
    if name != digest + '.json':
        raise JournalError('journal-name')
    return journal


def journal_names(directory: str) -> list[str] | None:
    """Journal file names in sorted order, [] without the directory, None when unreadable."""
    try:
        if not stat.S_ISDIR(os.lstat(directory).st_mode):
            return None
        return sorted(name for name in os.listdir(directory) if JOURNAL_FILE.fullmatch(name))
    except FileNotFoundError:
        return []
    except OSError:
        return None


def scan_journals(common_dir: str) -> JournalScan:
    """Every journal under the common directory; any unusable journal file makes the set unusable."""
    directory = os.path.join(common_dir, JOURNAL_DIRECTORY)
    names = journal_names(directory)
    if names is None:
        return JournalScan((), JOURNAL_UNREADABLE)
    try:
        journals = tuple(load_journal(directory, name) for name in names)
    except JournalError as error:
        return JournalScan((), str(error))
    return JournalScan(journals, None if journals else JOURNAL_MISSING)


def first_failure(journal: Journal, checks: Sequence[JournalCheck]) -> int:
    for index, (_, holds) in enumerate(checks):
        if not holds(journal):
            return index
    return len(checks)


def matching_failure(scan: JournalScan, checks: Sequence[JournalCheck]) -> str | None:
    """None when exactly one journal passes every check; otherwise the ambiguity, or the check
    failed by the journal that got furthest."""
    if scan.failure is not None:
        return scan.failure
    reached = [first_failure(journal, checks) for journal in scan.journals]
    matches = reached.count(len(checks))
    if matches == 1:
        return None
    return 'journal-ambiguous' if matches else checks[max(reached)][0]


def branch_tip(name: str, invocation: Invocation, context: Context) -> str | None:
    """The commit refs/heads/<name> holds, None when it is missing, symbolic or unreadable.
    Callers check state_changed(invocation) first."""
    if not valid_branch_name(name):
        return None
    ref = BRANCH_PREFIX + name
    result = read_git(['for-each-ref', '--format=%(refname)%00%(objectname)%00%(symref)', ref],
                      invocation.directory, context.environ)
    for line in result.stdout.split('\n') if result.returncode == 0 else []:
        fields = line.split('\x00')
        if len(fields) == 3 and fields[0] == ref and not fields[2]:
            return fields[1]
    return None


def object_name(revision: str, invocation: Invocation, context: Context) -> str | None:
    result = read_git(['rev-parse', '--verify', '--quiet', revision], invocation.directory, context.environ)
    name = result.stdout.strip()
    return name if result.returncode == 0 and name else None


def common_directory(invocation: Invocation) -> str:
    return os.path.realpath(invocation.common_dir or invocation.directory)


# ── Lease verification ─────────────────────────────────────────────────

@dataclass(frozen=True)
class LeaseRequest:
    """What a lease verifier checks: the target remote, every destination ref with its
    explicit expected value ('' for a ref recorded as absent), whether force is also set,
    and the source each destination is pushed from, as the refspec names it."""
    remote: str
    destinations: tuple[str, ...]
    leases: tuple[tuple[str, str], ...]
    forced: bool
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class LeaseVerdict:
    """Whether the leased push is proven safe, and otherwise the check that failed."""
    verified: bool
    failure: str | None = None


LeaseVerifier = Callable[[LeaseRequest, Invocation, Context], LeaseVerdict]


def no_journal_verifier(request: LeaseRequest, invocation: Invocation, context: Context) -> LeaseVerdict:
    """The result without a restack journal: nothing proves a lease safe."""
    return LeaseVerdict(False, JOURNAL_MISSING)


@dataclass(frozen=True)
class LeaseTarget:
    """One leased destination as the journal checks read it: the branch, its explicit lease,
    the local tip, and the object pushed when the source names that branch itself."""
    destination: str
    branch: str
    lease: str | None
    tip: str | None
    pushed: str | None


def lease_targets(request: LeaseRequest, invocation: Invocation, context: Context) -> list[LeaseTarget] | None:
    if len(request.sources) != len(request.destinations):
        return None
    leases = dict(request.leases)
    targets: list[LeaseTarget] = []
    for destination, source in zip(request.destinations, request.sources):
        branch = destination[len(BRANCH_PREFIX):] if destination.startswith(BRANCH_PREFIX) else ''
        named = valid_branch_name(branch) and source in (branch, destination)
        pushed = object_name(source, invocation, context) if named else None
        tip = branch_tip(branch, invocation, context)
        targets.append(LeaseTarget(destination, branch, leases.get(destination), tip, pushed))
    return targets


def lease_matches(lease: str | None, expected: str | None) -> bool:
    """The explicit lease equals the captured remote tip; an empty lease means recorded absent."""
    return expected is not None and lease == ('' if expected == ABSENT else expected)


def every_target(targets: Sequence[LeaseTarget],
                 holds: Callable[[LeaseTarget, JournalBranch], bool]) -> Callable[[Journal], bool]:
    """A journal check that holds when it holds for the branch record of every destination."""
    return lambda journal: all(holds(target, journal.branches[target.branch]) for target in targets)


def lease_checks(request: LeaseRequest, invocation: Invocation, context: Context) -> list[JournalCheck] | str:
    """The publication checks, each over every destination, in the order they are reported."""
    patterns = protected_branches(request.remote, invocation, context)
    targets = lease_targets(request, invocation, context)
    if patterns is None:
        return 'protected-set'
    if targets is None:
        return 'source'
    common = common_directory(invocation)
    return [('repository', lambda journal: journal.repository == common),
            ('branch-in-order', lambda journal: all(target.branch in journal.order for target in targets)),
            ('branch-protected', lambda journal: not any(is_protected(target.destination, patterns)
                                                         for target in targets)),
            ('publication-authorized', lambda journal: journal.publication_authorized),
            ('branch-not-replayed', every_target(targets, lambda target, entry: entry.replayed_tip is not None)),
            ('branch-tip', every_target(targets, lambda target, entry: target.tip == entry.replayed_tip)),
            ('source', every_target(targets, lambda target, entry: target.pushed == entry.replayed_tip)),
            ('lease', every_target(targets, lambda target, entry: lease_matches(target.lease,
                                                                                entry.expected_remote_tip))),
            ('forced', lambda journal: not request.forced)]


def journal_lease_verifier(request: LeaseRequest, invocation: Invocation, context: Context) -> LeaseVerdict:
    """A lease is proven safe when exactly one restack journal passes every publication check."""
    scan = scan_journals(common_directory(invocation))
    if scan.failure == JOURNAL_MISSING:
        return no_journal_verifier(request, invocation, context)
    checks = lease_checks(request, invocation, context)
    failure = checks if isinstance(checks, str) else matching_failure(scan, checks)
    return LeaseVerdict(failure is None, failure)


# The lease rule calls this name at decision time, so a replacement verifier keeps the interface.
LEASE_VERIFIER: LeaseVerifier = journal_lease_verifier


def explicit_leases(values: Sequence[OptionValue]) -> tuple[tuple[str, str], ...] | None:
    """Every --force-with-lease as (ref, full sha or ''), or None when any is not explicit."""
    leases: list[tuple[str, str]] = []
    for value in values:
        if not isinstance(value, str):
            return None
        ref, colon, expected = value.partition(':')
        if not ref or not colon or (expected and not LEASE_SHA.fullmatch(expected)):
            return None
        leases.append((ref, expected))
    return tuple(leases)


def lease_for(destination: str, leases: Sequence[tuple[str, str]]) -> str | None:
    """The expected value of the last lease whose ref names the destination."""
    found: str | None = None
    for ref, expected in leases:
        if destination in (ref, 'refs/' + ref, TAG_PREFIX + ref, BRANCH_PREFIX + ref):
            found = expected
    return found


# ── Push rules ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PushView:
    """One reading of a push with its resolved plan and the target's protected set."""
    parsed: ParsedOptions
    plan: PushPlan
    protected: tuple[str, ...]
    invocation: Invocation
    context: Context

    @property
    def forced(self: PushView) -> bool:
        return self.parsed.last('force') is True or any(spec.forced for spec in self.plan.refspecs)


def lease_request(view: PushView) -> LeaseRequest | None:
    """The request for a lease covering every destination explicitly, else None."""
    leases = explicit_leases(view.parsed.every('force-with-lease'))
    destinations = tuple(spec.destination for spec in view.plan.refspecs)
    if leases is None or not destinations or '' in destinations:
        return None
    expected = [lease_for(destination, leases) for destination in destinations]
    known = [value for value in expected if value is not None]
    if len(known) != len(expected):
        return None
    sources = tuple(spec.source for spec in view.plan.refspecs)
    return LeaseRequest(view.plan.remote, destinations, tuple(zip(destinations, known)), view.forced, sources)


def check_push_bulk(view: PushView) -> Decision | None:
    """R14: bulk options or configuration, a matching push, or a tag destination."""
    flags = any(view.parsed.last(key) is True for key in BULK_PUSH_OPTIONS)
    refs = any(spec.matching or spec.destination.startswith(TAG_PREFIX) for spec in view.plan.refspecs)
    return asking('push-bulk-or-tags', 'R14') if flags or refs or view.plan.bulk else None


def check_push_delete(view: PushView) -> Decision | None:
    """R15: --delete, an empty source, or --prune, which deletes remote refs."""
    flags = any(view.parsed.last(key) is True for key in ('delete', 'prune'))
    deletes = any(spec.deletion for spec in view.plan.refspecs)
    return asking('push-delete', 'R15') if flags or deletes else None


def check_push_protected(view: PushView) -> Decision | None:
    """R16: any destination is a protected branch."""
    if any(is_protected(spec.destination, view.protected) for spec in view.plan.refspecs):
        return asking('push-protected-target', 'R16')
    return None


def check_push_force(view: PushView) -> Decision | None:
    """R17: --force, a '+' refspec, or --force-if-includes without any lease."""
    includes = view.parsed.last('force-if-includes') is True and not view.parsed.every('force-with-lease')
    return asking('push-force', 'R17') if view.forced or includes else None


def check_push_lease(view: PushView) -> Decision | None:
    """R18: a lease is accepted only when explicit for every destination and verified."""
    if not view.parsed.every('force-with-lease'):
        return None
    request = lease_request(view)
    if request is None:
        return asking(LEASE_UNVERIFIED, 'R18', 'explicit-lease')
    verdict = LEASE_VERIFIER(request, view.invocation, view.context)
    return None if verdict.verified else asking(LEASE_UNVERIFIED, 'R18', verdict.failure)


PUSH_ASKS: tuple[Callable[[PushView], Decision | None], ...] = (
    check_push_bulk, check_push_delete, check_push_protected, check_push_force, check_push_lease)


def push_options(invocation: Invocation) -> list[ParsedOptions] | None:
    return option_variants(invocation.argv, PUSH_OPTIONS)


def runs_program(parsed: ParsedOptions) -> bool:
    """A receive-pack program, or a submodule push the rules cannot follow."""
    if any(parsed.last(key) not in (None, False) for key in PROGRAM_PUSH_OPTIONS):
        return True
    return parsed.last('recurse-submodules') not in SAFE_SUBMODULE_MODES


def check_push_options(invocation: Invocation, context: Context) -> Decision | None:
    """Options git would reject, too many readings, or options that run other programs."""
    variants = push_options(invocation)
    if variants is None or any(parsed.error or runs_program(parsed) for parsed in variants):
        return denial('unsupported-form')
    return None


def push_decision(parsed: ParsedOptions, invocation: Invocation, context: Context) -> Decision:
    """R11 to R19 for one reading of the options; matching rows apply in matrix order."""
    if parsed.last('dry-run') is True:
        return ALLOW
    if state_changed(invocation):
        return denial(PUSH_TARGET_UNKNOWN, 'R12')
    plan = push_plan(parsed, invocation, context)
    if plan is None:
        return denial(PUSH_TARGET_UNKNOWN, 'R12')
    protected = protected_branches(plan.remote, invocation, context)
    if protected is None:
        return denial('default-branch-unknown', 'R13')
    view = PushView(parsed, plan, protected, invocation, context)
    asks = [check(view) for check in PUSH_ASKS]
    return combine([ALLOW, *[result for result in asks if result is not None]])


def check_push(invocation: Invocation, context: Context) -> Decision | None:
    """Every reading of the options is decided; the most severe reading wins."""
    variants = usable(push_options(invocation))
    return combine(push_decision(parsed, invocation, context) for parsed in variants) if variants else None


# ── Destructive, ref-rewrite and merge operations ──────────────────────

UNSUPPORTED = 'unsupported-form'
BRANCH_DELETE = 'branch-delete'
REWRITE = 'protected-ref-rewrite'
INTO_PROTECTED = 'merge-into-protected'
PR_MERGE = 'pr-merge'
REMOTE_PREFIX = 'refs/remotes/'
RESET_MODES = ('mixed', 'soft', 'hard', 'merge', 'keep')
REBASE_ACTIONS = ('continue', 'skip', 'abort', 'quit', 'edit-todo', 'show-current-patch')
REBASE_STATE_DIRECTORIES = ('rebase-merge', 'rebase-apply')
MAX_HEAD_NAME_BYTES = 4096


def flags(*names: str) -> tuple[OptionSpec, ...]:
    """Negatable long flags; a one-letter name is a short-only flag."""
    return tuple(OptionSpec(None, name) if len(name) == 1 else OptionSpec(name) for name in names)


def fixed(*names: str) -> tuple[OptionSpec, ...]:
    """Long flags git declares without a --no- form."""
    return tuple(OptionSpec(name, negatable=False) for name in names)


RESET_OPTIONS = (
    OptionSpec('quiet', 'q'), *flags('refresh', 'pathspec-file-nul'), *fixed(*RESET_MODES),
    OptionSpec('recurse-submodules', None, 'optional'), OptionSpec('patch', 'p'),
    OptionSpec('unified', 'U', 'required', negatable=False),
    OptionSpec('inter-hunk-context', None, 'required', negatable=False), OptionSpec('intent-to-add', 'N'),
    OptionSpec('pathspec-from-file', None, 'required'))
CLEAN_OPTIONS = (
    OptionSpec('quiet', 'q'), OptionSpec('dry-run', 'n'), OptionSpec('force', 'f'), OptionSpec('interactive', 'i'),
    *flags('d', 'x', 'X'), OptionSpec('exclude', 'e', 'required', repeatable=True, negatable=False))
BRANCH_OPTIONS = (
    OptionSpec('verbose', 'v'), OptionSpec('quiet', 'q'), OptionSpec('track', 't', 'optional'),
    OptionSpec('set-upstream-to', 'u', 'required'), *flags('unset-upstream', 'omit-empty', 'show-current'),
    OptionSpec('color', None, 'optional'), OptionSpec('remotes', 'r', negatable=False),
    *(OptionSpec(name, None, 'last', negatable=False)
      for name in ('contains', 'no-contains', 'with', 'without', 'merged', 'no-merged')),
    OptionSpec('abbrev', None, 'optional'), OptionSpec('all', 'a', negatable=False), OptionSpec('delete', 'd'),
    OptionSpec('move', 'm'), OptionSpec('copy', 'c'), OptionSpec('list', 'l'), *flags('D', 'M', 'C'),
    *flags('create-reflog', 'edit-description', 'recurse-submodules', 'set-upstream'), OptionSpec('force', 'f'),
    OptionSpec('column', None, 'optional'), OptionSpec('sort', None, 'required'),
    OptionSpec('points-at', None, 'required'), OptionSpec('ignore-case', 'i'),
    OptionSpec('format', None, 'required'))
UPDATE_REF_OPTIONS = (
    OptionSpec(None, 'm', 'required'), *flags('d', 'z', 'stdin', 'create-reflog'), *fixed('no-deref', 'deref'),
    OptionSpec('batch-updates', '0'))
BRANCH_SWITCH_OPTIONS = (
    *flags('guess', 'progress', 'overwrite-ignore', 'ignore-other-worktrees'), OptionSpec('quiet', 'q'),
    OptionSpec('recurse-submodules', None, 'optional'), OptionSpec('merge', 'm'),
    OptionSpec('conflict', None, 'required'), OptionSpec('detach', 'd'), OptionSpec('track', 't', 'optional'),
    OptionSpec('force', 'f'), OptionSpec('orphan', None, 'required'))
CHECKOUT_OPTIONS = (
    *BRANCH_SWITCH_OPTIONS, OptionSpec(None, 'b', 'required'), OptionSpec(None, 'B', 'required'),
    *flags('l', 'overlay', 'ignore-skip-worktree-bits', 'pathspec-file-nul'),
    OptionSpec('ours', '2', negatable=False), OptionSpec('theirs', '3', negatable=False), OptionSpec('patch', 'p'),
    OptionSpec('unified', 'U', 'required', negatable=False),
    OptionSpec('inter-hunk-context', None, 'required', negatable=False),
    OptionSpec('pathspec-from-file', None, 'required'))
SWITCH_OPTIONS = (
    *BRANCH_SWITCH_OPTIONS, OptionSpec('create', 'c', 'required'), OptionSpec('force-create', 'C', 'required'),
    *flags('discard-changes'))
REBASE_OPTIONS = (
    OptionSpec('onto', None, 'required'), *fixed('no-verify', 'verify', 'stat', 'no-ff', 'ff', *REBASE_ACTIONS),
    OptionSpec('quiet', 'q'), OptionSpec('verbose', 'v'), OptionSpec('no-stat', 'n', negatable=False),
    *flags('keep-base', 'signoff', 'committer-date-is-author-date', 'reset-author-date', 'ignore-date',
           'ignore-whitespace', 'rerere-autoupdate', 'autosquash', 'update-refs', 'autostash', 'fork-point',
           'root', 'reschedule-failed-exec', 'reapply-cherry-picks', 'allow-empty-message'),
    OptionSpec(None, 'C', 'required', negatable=False), OptionSpec('whitespace', None, 'required'),
    OptionSpec('force-rebase', 'f'), *fixed('apply'), OptionSpec('merge', 'm', negatable=False),
    OptionSpec('interactive', 'i', negatable=False), OptionSpec('empty', None, 'required', negatable=False),
    OptionSpec('gpg-sign', 'S', 'optional'), OptionSpec('exec', 'x', 'required'),
    OptionSpec('rebase-merges', 'r', 'optional'), OptionSpec('strategy', 's', 'required'),
    OptionSpec('strategy-option', 'X', 'required'), OptionSpec('preserve-merges', 'p'),
    OptionSpec('keep-empty', 'k'))
MERGE_TAIL_OPTIONS = (
    *flags('n', 'stat', 'summary', 'compact-summary', 'squash', 'commit', 'ff', 'rerere-autoupdate',
           'verify-signatures', 'autostash', 'allow-unrelated-histories', 'progress', 'signoff'),
    OptionSpec('log', None, 'optional'), OptionSpec('cleanup', None, 'required'), *fixed('ff-only'),
    OptionSpec('strategy', 's', 'required'), OptionSpec('strategy-option', 'X', 'required'),
    OptionSpec('gpg-sign', 'S', 'optional'), OptionSpec('verbose', 'v'), OptionSpec('quiet', 'q'))
MERGE_OPTIONS = (
    *MERGE_TAIL_OPTIONS, OptionSpec('edit', 'e'), OptionSpec('message', 'm', 'required', repeatable=True),
    OptionSpec('file', 'F', 'required', negatable=False), OptionSpec('into-name', None, 'required'),
    *flags('abort', 'quit', 'continue', 'overwrite-ignore'), *fixed('no-verify', 'verify'))
PULL_OPTIONS = (
    *(spec for spec in MERGE_TAIL_OPTIONS if spec.long != 'signoff'), *flags('edit', 'verify', 'all', 'dry-run'),
    OptionSpec('recurse-submodules', None, 'optional'), OptionSpec('rebase', 'r', 'optional'),
    OptionSpec('signoff', None, 'optional'), OptionSpec('append', 'a'),
    OptionSpec('upload-pack', None, 'required'), OptionSpec('force', 'f'), OptionSpec('tags', 't'),
    OptionSpec('prune', 'p'), OptionSpec('jobs', 'j', 'optional'), OptionSpec('keep', 'k'),
    *(OptionSpec(name, None, 'required') for name in ('depth', 'shallow-since', 'shallow-exclude', 'deepen',
                                                      'negotiation-tip')),
    *fixed('unshallow'), *flags('update-shallow', 'show-forced-updates', 'set-upstream'),
    OptionSpec('refmap', None, 'required', negatable=False), OptionSpec('server-option', 'o', 'required'),
    OptionSpec('ipv4', '4'), OptionSpec('ipv6', '6'))

ReadingDecider = Callable[[ParsedOptions, Invocation, Context], Decision | None]


def reading_rule(specs: tuple[OptionSpec, ...], decide: ReadingDecider) -> Rule:
    """A rule that rejects options git would refuse and decides every reading of the rest."""
    def check(invocation: Invocation, context: Context) -> Decision | None:
        variants = option_variants(invocation.argv, specs)
        if variants is None or any(parsed.error for parsed in variants):
            return denial(UNSUPPORTED)
        found = [result for result in (decide(parsed, invocation, context) for parsed in variants)
                 if result is not None]
        return combine(found) if found else None
    return check


def current_branch(invocation: Invocation, context: Context) -> str | None:
    """The full ref HEAD names, '' when HEAD is detached, None when it cannot be read.
    Callers check state_changed(invocation) first."""
    result = read_git(['symbolic-ref', '-q', 'HEAD'], invocation.directory, context.environ)
    if result.returncode == 1:
        return ''
    target = result.stdout.strip()
    return target if result.returncode == 0 and target else None


def local_protection(invocation: Invocation, context: Context, rule: str) -> tuple[str, ...] | Decision:
    """The local protected set, or the denial when it cannot be read."""
    if state_changed(invocation):
        return denial(UNSUPPORTED, rule)
    patterns = local_protected_branches(invocation, context)
    return denial('default-branch-unknown', rule) if patterns is None else patterns


def protected_head(invocation: Invocation, context: Context, rule: str) -> Decision | None:
    """R27/R28: ask when the current branch is protected; a detached HEAD is no branch."""
    if state_changed(invocation):
        return denial(UNSUPPORTED, rule)
    branch = current_branch(invocation, context)
    if branch is None:
        return denial(UNSUPPORTED, rule)
    if not branch:
        return None
    patterns = local_protection(invocation, context, rule)
    if isinstance(patterns, Decision):
        return patterns
    return asking(INTO_PROTECTED, rule) if is_protected(branch, patterns) else None


def rewrite_decision(refs: Sequence[str], invocation: Invocation, context: Context) -> Decision | None:
    """R24: ask when any rewritten branch ref is protected."""
    if any('@{' in ref or ref == BRANCH_PREFIX + '@' for ref in refs):
        return denial(UNSUPPORTED, 'R24')
    if not any(ref.startswith(BRANCH_PREFIX) for ref in refs):
        return None
    patterns = local_protection(invocation, context, 'R24')
    if isinstance(patterns, Decision):
        return patterns
    return asking(REWRITE, 'R24') if any(is_protected(ref, patterns) for ref in refs) else None


# ── Branch-deletion exception verification ─────────────────────────────

@dataclass(frozen=True)
class DeletionRequest:
    """What a deletion exception verifier checks: every deleted ref in command order, its
    expected old value when the command names one, and whether unmerged work may be dropped."""
    refs: tuple[str, ...]
    expected: tuple[str | None, ...]
    forced: bool


@dataclass(frozen=True)
class DeletionVerdict:
    """Whether the deletion is a proven exception, and otherwise the check that failed."""
    exception: bool
    failure: str | None = None


DeletionVerifier = Callable[[DeletionRequest, Invocation, Context], DeletionVerdict]


def no_exception_verifier(request: DeletionRequest, invocation: Invocation, context: Context) -> DeletionVerdict:
    """The verifier used until temporary child-branch deletions can be proven: none is."""
    return DeletionVerdict(False, 'no branch-deletion exception is implemented')


# Branch deletion calls this name at decision time, so a replacement verifier keeps the interface.
# It may be called after an earlier part of the command changed state; a replacement that reads
# repository state checks state_changed(invocation) first.
DELETION_VERIFIER: DeletionVerifier = no_exception_verifier


def excepted(request: DeletionRequest, invocation: Invocation, context: Context) -> bool:
    return DELETION_VERIFIER(request, invocation, context).exception


# ── Rebase replay verification ─────────────────────────────────────────

@dataclass(frozen=True)
class ReplayRequest:
    """What a replay verifier checks: the rebase arguments as written, the (new, old, branch)
    operands when they are exactly --onto <new> <old> <branch>, the rebase action, whether a
    rebase is in progress with the branch its head-name records, and the canonical common dir."""
    arguments: tuple[str, ...]
    replay: tuple[str, str, str] | None
    action: str | None
    in_progress: bool
    rebase_head: str | None
    common_dir: str


@dataclass(frozen=True)
class ReplayVerdict:
    """Whether the rebase is a verified replay, and otherwise the check that failed."""
    verified: bool
    failure: str | None = None


ReplayVerifier = Callable[[ReplayRequest, Invocation, Context], ReplayVerdict]


def no_journal_replay_verifier(request: ReplayRequest, invocation: Invocation, context: Context) -> ReplayVerdict:
    """The result without a restack journal: nothing proves a replay."""
    return ReplayVerdict(False, JOURNAL_MISSING)


def expected_base(journal: Journal, branch: str) -> str | None:
    """The first branch of the order replays onto the target; every later one onto the
    replayed tip of the branch before it."""
    index = journal.order.index(branch)
    return journal.target if index == 0 else journal.branches[journal.order[index - 1]].replayed_tip


def pending_checks(common: str, branch: str, patterns: Sequence[str]) -> list[JournalCheck]:
    """The branch belongs to this repository's stack, is unprotected and is not yet replayed."""
    return [('repository', lambda journal: journal.repository == common),
            ('branch-in-order', lambda journal: branch in journal.order),
            ('branch-protected', lambda journal: not is_protected(BRANCH_PREFIX + branch, patterns)),
            ('branch-replayed', lambda journal: journal.branches[branch].replayed_tip is None)]


def replay_checks(request: ReplayRequest, invocation: Invocation, context: Context) -> list[JournalCheck] | str:
    """The exact replay, or --continue/--skip while a rebase of a stack branch is in progress."""
    head = request.rebase_head or ''
    if request.replay is None and request.arguments not in (('--continue',), ('--skip',)):
        return 'replay-form'
    if request.replay is None and not (request.in_progress and head.startswith(BRANCH_PREFIX)):
        return 'rebase-head'
    patterns = local_protected_branches(invocation, context)
    if patterns is None:
        return 'protected-set'
    if request.replay is None:
        return pending_checks(request.common_dir, head[len(BRANCH_PREFIX):], patterns)
    new, old, branch = request.replay
    tip = branch_tip(branch, invocation, context)
    return [*pending_checks(request.common_dir, branch, patterns),
            ('old-sha', lambda journal: journal.branches[branch].original_base_commit == old),
            ('branch-tip', lambda journal: journal.branches[branch].original_tip == tip),
            ('new-sha', lambda journal: expected_base(journal, branch) == new)]


def journal_replay_verifier(request: ReplayRequest, invocation: Invocation, context: Context) -> ReplayVerdict:
    """A rebase is a verified replay when exactly one restack journal passes every replay check."""
    scan = scan_journals(request.common_dir)
    if scan.failure == JOURNAL_MISSING:
        return no_journal_replay_verifier(request, invocation, context)
    checks = replay_checks(request, invocation, context)
    failure = checks if isinstance(checks, str) else matching_failure(scan, checks)
    return ReplayVerdict(failure is None, failure)


# The rebase rule calls this name at decision time, so a replacement verifier keeps the interface.
# It is never called after a same-command state change; that rebase is denied first.
REPLAY_VERIFIER: ReplayVerifier = journal_replay_verifier


def read_head_name(directory: str) -> str | None:
    path = os.path.join(directory, 'head-name')
    if not os.path.isfile(path):
        return None
    with open(path, 'rb') as handle:
        text = handle.read(MAX_HEAD_NAME_BYTES).decode('utf-8', 'surrogateescape').strip()
    return text or None


def rebase_state(invocation: Invocation, context: Context) -> tuple[bool, str | None] | None:
    """Whether a rebase is in progress and its head-name, or None when the git dir is unreadable."""
    result = read_git(['rev-parse', '--path-format=absolute', '--git-dir'], invocation.directory, context.environ)
    git_dir = result.stdout.strip()
    if result.returncode != 0 or not git_dir:
        return None
    in_progress, head = False, None
    try:
        for name in REBASE_STATE_DIRECTORIES:
            directory = os.path.join(git_dir, name)
            if os.path.isdir(directory):
                in_progress, head = True, head or read_head_name(directory)
    except OSError:
        return None
    return in_progress, head


def rebase_actions(parsed: ParsedOptions) -> list[str]:
    return [name for name, value in parsed.options if name in REBASE_ACTIONS and value is True]


def replay_request(parsed: ParsedOptions, invocation: Invocation, context: Context) -> ReplayRequest | None:
    state = rebase_state(invocation, context)
    if state is None:
        return None
    words = invocation.argv
    replay = (words[1], words[2], words[3]) if len(words) == 4 and words[0] == '--onto' else None
    actions = rebase_actions(parsed)
    return ReplayRequest(words, replay, actions[-1] if actions else None, state[0], state[1],
                         os.path.realpath(invocation.common_dir or invocation.directory))


# ── Reading deciders ───────────────────────────────────────────────────

def reset_reading(parsed: ParsedOptions, invocation: Invocation, context: Context) -> Decision | None:
    """R20: the last mode option decides, as in git."""
    modes = [name for name, value in parsed.options if name in RESET_MODES and value is True]
    return asking('reset-hard', 'R20') if modes and modes[-1] == 'hard' else None


def clean_reading(parsed: ParsedOptions, invocation: Invocation, context: Context) -> Decision | None:
    """R21: interactive cleaning cannot be checked; anything but a dry run removes files."""
    if parsed.last('interactive') is True:
        return denial(UNSUPPORTED, 'R21')
    return None if parsed.last('dry-run') is True else asking('clean', 'R21')


def branch_deletion(parsed: ParsedOptions) -> DeletionRequest | None:
    forced = parsed.last('D') is True
    if parsed.last('delete') is not True and not forced:
        return None
    prefix = REMOTE_PREFIX if parsed.last('remotes') is True else BRANCH_PREFIX
    refs = tuple(prefix + name for name in parsed.operands)
    return DeletionRequest(refs, (None,) * len(refs), forced or parsed.last('force') is True)


def renamed_refs(parsed: ParsedOptions, invocation: Invocation, context: Context) -> list[str] | Decision:
    """The source and destination of a move or copy; one operand renames the current branch."""
    refs = [BRANCH_PREFIX + name for name in parsed.operands]
    if len(refs) != 1:
        return refs
    if state_changed(invocation):
        return denial(UNSUPPORTED, 'R24')
    current = current_branch(invocation, context)
    if current is None:
        return denial(UNSUPPORTED, 'R24')
    return [current, *refs] if current else refs


def branch_reading(parsed: ParsedOptions, invocation: Invocation, context: Context) -> Decision | None:
    """R22 deletion through the exception verifier, else R24 for moved or copied branches (the
    symbolic ref itself) and forced ones (the branch a symbolic ref points to)."""
    request = branch_deletion(parsed)
    if request is not None:
        return None if excepted(request, invocation, context) else asking(BRANCH_DELETE, 'R22')
    if any(parsed.last(key) is True for key in ('move', 'M', 'copy', 'C')):
        refs = renamed_refs(parsed, invocation, context)
        return refs if isinstance(refs, Decision) else rewrite_decision(refs, invocation, context)
    if parsed.last('force') is True:
        return forced_rewrite([BRANCH_PREFIX + name for name in parsed.operands[:1]], invocation, context)
    return None


def dereferences(parsed: ParsedOptions) -> bool:
    """update-ref follows a symbolic ref unless the last of --no-deref/--deref is --no-deref."""
    choice = [name for name, value in parsed.options if name in ('no-deref', 'deref') and value is True]
    return not choice or choice[-1] == 'deref'


def symbolic_target(ref: str, invocation: Invocation, context: Context) -> str | None:
    """The ref a write to ref reaches after following symbolic refs; None when unreadable.
    Callers check state_changed(invocation) first."""
    if ref.startswith('-'):
        return None
    result = read_git(['symbolic-ref', '-q', ref], invocation.directory, context.environ)
    if result.returncode == 1:
        return ref
    target = result.stdout.strip()
    return target if result.returncode == 0 and target else None


def update_target(parsed: ParsedOptions, invocation: Invocation, context: Context) -> str | None:
    """The ref update-ref writes or deletes, after following symbolic refs unless --no-deref."""
    ref = parsed.operands[0]
    return symbolic_target(ref, invocation, context) if dereferences(parsed) else ref


def forced_rewrite(refs: list[str], invocation: Invocation, context: Context) -> Decision | None:
    """R24 for forced creation, which writes the branch a symbolic branch ref points to."""
    if not refs or any('@{' in ref for ref in refs):
        return rewrite_decision(refs, invocation, context)
    if state_changed(invocation):
        return denial(UNSUPPORTED, 'R24')
    targets = [symbolic_target(ref, invocation, context) for ref in refs]
    resolved = [target for target in targets if target is not None]
    if len(resolved) != len(targets):
        return denial(UNSUPPORTED, 'R24')
    return rewrite_decision(resolved, invocation, context)


def update_ref_reading(parsed: ParsedOptions, invocation: Invocation, context: Context) -> Decision | None:
    """R23 deletion of a branch through the exception verifier, --stdin unsupported; R24 writes."""
    if parsed.last('stdin') is True:
        return denial(UNSUPPORTED, 'R23')
    if not parsed.operands:
        return None
    rule = 'R23' if parsed.last('d') is True else 'R24'
    if dereferences(parsed) and state_changed(invocation):
        return denial(UNSUPPORTED, rule)
    target = update_target(parsed, invocation, context)
    if target is None:
        return denial(UNSUPPORTED, rule)
    if rule == 'R24':
        return rewrite_decision([target], invocation, context)
    if not target.startswith(BRANCH_PREFIX):
        return None
    expected = parsed.operands[1] if len(parsed.operands) > 1 else None
    request = DeletionRequest((target,), (expected,), False)
    return None if excepted(request, invocation, context) else asking(BRANCH_DELETE, 'R23')


def forced_creation(parsed: ParsedOptions, key: str) -> list[str]:
    value = parsed.last(key)
    return [BRANCH_PREFIX + value] if isinstance(value, str) else []


def checkout_reading(parsed: ParsedOptions, invocation: Invocation, context: Context) -> Decision | None:
    """R24: checkout -B resets the named branch, or the branch a symbolic one points to."""
    return forced_rewrite(forced_creation(parsed, 'B'), invocation, context)


def switch_reading(parsed: ParsedOptions, invocation: Invocation, context: Context) -> Decision | None:
    """R24: switch -C/--force-create resets the named branch, or the one it points to."""
    return forced_rewrite(forced_creation(parsed, 'force-create'), invocation, context)


def rebase_reading(parsed: ParsedOptions, invocation: Invocation, context: Context) -> Decision | None:
    """R25 abort and show-current-patch; R26 every other rebase through the replay verifier."""
    if set(rebase_actions(parsed)) in ({'abort'}, {'show-current-patch'}):
        return None
    if state_changed(invocation):
        return denial(UNSUPPORTED, 'R26')
    request = replay_request(parsed, invocation, context)
    if request is None:
        return denial(UNSUPPORTED, 'R26')
    verdict = REPLAY_VERIFIER(request, invocation, context)
    return None if verdict.verified else asking('rebase-outside-restack', 'R26', verdict.failure)


def merge_reading(parsed: ParsedOptions, invocation: Invocation, context: Context) -> Decision | None:
    """R27: every merge form except --abort changes a protected current branch."""
    return None if parsed.last('abort') is True else protected_head(invocation, context, 'R27')


def fast_forward_only(parsed: ParsedOptions) -> bool:
    """--ff, --no-ff and --ff-only share one setting in git; the last of them decides."""
    choice = [name for name, _ in parsed.options if name in ('ff', 'ff-only')]
    return bool(choice) and choice[-1] == 'ff-only'


def pull_reading(parsed: ParsedOptions, invocation: Invocation, context: Context) -> Decision | None:
    """R28: only --ff-only from the configured upstream leaves a protected branch unrewritten."""
    if fast_forward_only(parsed) and not parsed.operands:
        return None
    return protected_head(invocation, context, 'R28')


# ── gh ─────────────────────────────────────────────────────────────────

GH_API_SHORT_VALUES = {'X': 'method', 'H': 'header', 'f': 'raw-field', 'F': 'field', 'q': 'jq', 't': 'template',
                       'p': 'preview'}
GH_API_LONG_VALUES = frozenset({*GH_API_SHORT_VALUES.values(), 'input', 'cache', 'hostname'})
GH_API_SHORT_FLAGS = frozenset('ih')
GH_API_LONG_FLAGS = frozenset({'include', 'paginate', 'slurp', 'silent', 'verbose', 'help'})
MERGE_ENDPOINT = re.compile(r'/pulls/[0-9]+/merge$|/merges$')
GRAPHQL_ENDPOINT = re.compile(r'/+(api/)?graphql')
# GraphQL string literals (block and quoted) and comments, which never name a field.
GRAPHQL_INERT_TEXT = re.compile(r'"""[\s\S]*?(?<!\\)"""|"(?:\\.|[^"\\\n])*"|#[^\n]*')
GRAPHQL_NAME = re.compile(r'[_A-Za-z][_0-9A-Za-z]*')
GRAPHQL_MERGE_FIELDS = frozenset({'mergepullrequest', 'enablepullrequestautomerge', 'mergebranch',
                                  'enqueuepullrequest'})


@dataclass(frozen=True)
class GhApiCall:
    """The endpoint operands of gh api and its value flags as (long name, value)."""
    endpoints: tuple[str, ...]
    values: tuple[tuple[str, str], ...]


def gh_long(words: Sequence[str], index: int, values: list[tuple[str, str]]) -> int:
    """Words consumed by one long flag, 0 for an unknown flag or a missing value."""
    name, equals, value = words[index][2:].partition('=')
    if name in GH_API_LONG_FLAGS:
        return 1
    if name not in GH_API_LONG_VALUES or (not equals and index + 1 >= len(words)):
        return 0
    values.append((name, value if equals else words[index + 1]))
    return 1 if equals else 2


def gh_short(words: Sequence[str], index: int, values: list[tuple[str, str]]) -> int:
    """Words consumed by one shorthand bundle, 0 for an unknown letter or a missing value."""
    letters = words[index][1:]
    for position, letter in enumerate(letters):
        if letter in GH_API_SHORT_FLAGS:
            continue
        name = GH_API_SHORT_VALUES.get(letter)
        rest = letters[position + 1:]
        if name is None or (not rest and index + 1 >= len(words)):
            return 0
        values.append((name, rest.removeprefix('=') if rest else words[index + 1]))
        return 1 if rest else 2
    return 1


def parse_gh_api(words: Sequence[str]) -> GhApiCall | None:
    """gh api arguments read the way gh's flag parser reads them; flags may follow operands."""
    endpoints: list[str] = []
    values: list[tuple[str, str]] = []
    index = 0
    while index < len(words):
        word = words[index]
        if word == '--':
            endpoints.extend(words[index + 1:])
            break
        if word.startswith('--'):
            consumed = gh_long(words, index, values)
        elif word.startswith('-') and word != '-':
            consumed = gh_short(words, index, values)
        else:
            endpoints.append(word)
            consumed = 1
        if consumed == 0:
            return None
        index += consumed
    return GhApiCall(tuple(endpoints), tuple(values))


def api_path(endpoint: str) -> str:
    """The decoded, normalized, lower-case request path of an endpoint or URL."""
    path = urllib.parse.urlsplit(endpoint).path if '://' in endpoint else endpoint.partition('?')[0]
    return posixpath.normpath('/' + urllib.parse.unquote(path.partition('#')[0]).lower())


def merge_mutation(query: str) -> bool:
    """A merge mutation named as a field of the document, outside strings and comments."""
    names = GRAPHQL_NAME.findall(GRAPHQL_INERT_TEXT.sub(' ', query))
    return any(name.lower() in GRAPHQL_MERGE_FIELDS for name in names)


def graphql_decision(call: GhApiCall) -> Decision | None:
    """R30 for GraphQL: a body or query read from a file cannot be checked."""
    fields = [(name, value.partition('=')) for name, value in call.values if name in ('field', 'raw-field')]
    if any(name == 'input' for name, _ in call.values):
        return denial(UNSUPPORTED, 'R30')
    if any(name == 'field' and value.startswith('@') for name, (_, _, value) in fields):
        return denial(UNSUPPORTED, 'R30')
    if any(key == 'query' and merge_mutation(value) for _, (key, _, value) in fields):
        return asking(PR_MERGE, 'R30')
    return None


def check_pr_merge(invocation: Invocation, context: Context) -> Decision | None:
    """R29: merging a pull request always needs the owner."""
    return asking(PR_MERGE, 'R29')


def check_gh_api(invocation: Invocation, context: Context) -> Decision | None:
    """R30: a pull-request or branch merge endpoint, or a GraphQL merge mutation."""
    call = parse_gh_api(invocation.argv)
    if call is None:
        return denial(UNSUPPORTED)
    paths = [api_path(endpoint) for endpoint in call.endpoints]
    if any(MERGE_ENDPOINT.search(path) for path in paths):
        return asking(PR_MERGE, 'R30')
    if any(GRAPHQL_ENDPOINT.fullmatch(path) for path in paths):
        return graphql_decision(call)
    return None


STAGING_RULES: tuple[Rule, ...] = (check_staging_options, check_blanket_staging, check_staging_not_file,
                                   check_interactive_staging, check_ignored_path)
COMMIT_RULES: tuple[Rule, ...] = (check_commit_options, check_commit_all, check_commit_paths,
                                  check_commit_message, check_rewrite_published)
PUSH_RULES: tuple[Rule, ...] = (check_push_options, check_push)


# Per-subcommand rules, evaluated after the opaque-invocation rule has passed. Every
# governed key is present; an empty tuple means the invocation is allowed.
RULES: dict[str, tuple[Rule, ...]] = {
    **{name: () for name in sorted(GOVERNED_GIT_SUBCOMMANDS)},
    'add': STAGING_RULES,
    'stage': STAGING_RULES,
    'commit': COMMIT_RULES,
    'push': PUSH_RULES,
    'reset': (reading_rule(RESET_OPTIONS, reset_reading),),
    'clean': (reading_rule(CLEAN_OPTIONS, clean_reading),),
    'branch': (reading_rule(BRANCH_OPTIONS, branch_reading),),
    'update-ref': (reading_rule(UPDATE_REF_OPTIONS, update_ref_reading),),
    'checkout': (reading_rule(CHECKOUT_OPTIONS, checkout_reading),),
    'switch': (reading_rule(SWITCH_OPTIONS, switch_reading),),
    'rebase': (reading_rule(REBASE_OPTIONS, rebase_reading),),
    'merge': (reading_rule(MERGE_OPTIONS, merge_reading),),
    'pull': (reading_rule(PULL_OPTIONS, pull_reading),),
    'gh pr merge': (check_pr_merge,),
    'gh api': (check_gh_api,),
}


def check_opaque_invocation(invocation: Invocation) -> Decision | None:
    """R31: a git environment assignment, unsupported global option, alias or dynamic word."""
    names = (*invocation.assignments, *invocation.inherited)
    if any(is_sensitive_name(name) for name in names):
        return denial('opaque-environment', 'R31')
    unsupported = denial('unsupported-form', 'R31')
    if any(word.dynamic for word in invocation.environment):
        return unsupported
    layout = invocation.layout
    if any(word.dynamic for word in invocation.words[:layout.globals_end]):
        return unsupported
    if invocation.program == 'git' and (layout.unknown or
                                        unsupported_global_options(invocation.words[:layout.globals_end])):
        return unsupported
    if invocation.alias or (invocation.program == 'git' and not invocation.governed
                            and needs_verification(invocation) and state_changed(invocation)):
        return unsupported
    if layout.index is not None and invocation.words[layout.index].dynamic:
        return unsupported
    if invocation.program == 'gh' and needs_verification(invocation) and not invocation.governed:
        return unsupported
    if invocation.governed and any(word.dynamic and not exempt_word(invocation, word)
                                   for word in invocation.arguments):
        return unsupported
    return None


def redirected(draft: Invocation, found: Found, context: Context) -> Decision | None:
    """Outside a registered work tree, deny only options and variables that point back in."""
    targets = (*found.anchors, *redirect_targets(draft))
    if not needs_verification(draft) or not anchored(targets, context):
        return None
    if any(is_git_name(name) for name in (*draft.assignments, *draft.inherited)):
        return denial('opaque-environment', 'R31')
    if draft.program == 'git' and redirect_targets(draft, every=True):
        return denial('unsupported-form', 'R31')
    return None


def redirect_targets(invocation: Invocation, every: bool = False) -> tuple[str, ...]:
    """Literal --git-dir/--work-tree values; with every=True, any such option at all."""
    if invocation.program != 'git':
        return ()
    words = invocation.words[:invocation.layout.globals_end]
    targets: list[str] = []
    for index, word in enumerate(words):
        name, equals, value = word.text.partition('=')
        if name not in REDIRECTING_GLOBAL_OPTIONS:
            continue
        if not equals:
            value = words[index + 1].text if index + 1 < len(words) else ''
        targets.append(os.path.realpath(value) if value and os.path.isabs(value) else value)
    return tuple(targets) if every else tuple(target for target in targets if os.path.isabs(target))


def exempt_word(invocation: Invocation, word: Word) -> bool:
    """The commit-message heredoc is the only dynamic word a governed invocation accepts."""
    return invocation.program == 'git' and invocation.subcommand == 'commit' and word.form == 'commit-message'


# Git subcommands that run a command given on their own command line.
FILTER_BRANCH_RUNNERS = ('--setup', '--tree-filter', '--index-filter', '--msg-filter', '--env-filter',
                         '--commit-filter', '--parent-filter', '--tag-name-filter')
EXTCMD = 'extcmd'


def first_word(words: Sequence[str]) -> str | None:
    """The action word of git submodule or git bisect, after any leading options."""
    return next((word for word in words if not word.startswith('-')), None)


def difftool_runner(words: Sequence[str]) -> bool:
    """-x in any short bundle, or --extcmd or a prefix of it, before --."""
    for word in words:
        if word == '--':
            return False
        name = word[2:].partition('=')[0]
        if word.startswith('--') and name and EXTCMD.startswith(name):
            return True
        if not word.startswith('--') and word.startswith('-') and 'x' in word[1:]:
            return True
    return False


def command_runner(invocation: Invocation) -> bool:
    """git submodule foreach, git bisect run, filter-branch filters and difftool --extcmd run
    a command the core cannot see, so they are opaque."""
    if invocation.program != 'git' or invocation.layout.index is None:
        return False
    subcommand, words = invocation.subcommand, invocation.argv
    if subcommand in ('submodule', 'bisect'):
        return first_word(words) == ('foreach' if subcommand == 'submodule' else 'run')
    if subcommand == 'filter-branch':
        return any(word.partition('=')[0] in FILTER_BRANCH_RUNNERS for word in words)
    return subcommand == 'difftool' and difftool_runner(words)


def evaluate_invocation(invocation: Invocation, context: Context) -> Decision:
    if command_runner(invocation):
        return denial(UNSUPPORTED)
    if not needs_verification(invocation):
        return NOT_APPLICABLE
    finding = check_opaque_invocation(invocation)
    if finding is not None:
        return finding
    key = rule_key(invocation)
    if key is None:
        return NOT_APPLICABLE
    try:
        results = [rule(invocation, context) for rule in RULES.get(key, ())]
    except GitReadTimeout:
        return denial('limit-exceeded')
    return combine([ALLOW, *[result for result in results if result is not None]])


def decide(event: object, environ: Mapping[str, str]) -> Decision:
    """Decide one hook event as a whole; any unexpected failure denies."""
    try:
        request = read_request(event)
        if isinstance(request, Decision):
            return request
        try:
            roots = read_registry(environ)
        except RegistryError:
            return denial('registry-error')
        if roots is None:
            return NOT_APPLICABLE
        context = Context(request.cwd, roots, environ)
        resolution = resolve(request.command, context)
        if resolution.decision is not None:
            return resolution.decision
        return combine(evaluate_invocation(item, context) for item in resolution.invocations)
    except Exception:  # fail closed: an unverified command is never allowed
        return denial('internal-error')
