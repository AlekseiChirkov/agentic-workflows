"""Decide whether one agent shell command crosses a git safety rail.

The core validates a PreToolUse event, reads the project registry as one snapshot,
parses the Bash command with a deliberately small shell grammar, resolves every git
and gh invocation to its program, effective directory and effective repository, and
combines per-invocation results so that the most severe one decides the command.

Everything is a pure function over the event except one sanitized, read-only git layer
with a per-read time limit. The module uses only the standard library and runs under
``python3 -I``. It never writes files, caches, logs or git state, never runs gh and
never runs a network git command.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import os
import re
import signal
import stat
import subprocess
from typing import Callable, Iterable, Mapping, Sequence

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
    """One result: not_applicable, allow, deny or ask, with its reason and rule."""
    decision: str
    reason_code: str | None = None
    rule_id: str | None = None


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
    """One option of a governed subcommand; the key is the long name, else the short one."""
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
    elif spec.takes == 'required':
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
        elif spec.takes == 'required':
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


def asking(reason: str, rule: str) -> Decision:
    return Decision('ask', reason, rule)


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


STAGING_RULES: tuple[Rule, ...] = (check_staging_options, check_blanket_staging, check_staging_not_file,
                                   check_interactive_staging, check_ignored_path)
COMMIT_RULES: tuple[Rule, ...] = (check_commit_options, check_commit_all, check_commit_paths,
                                  check_commit_message, check_rewrite_published)


# Per-subcommand rules, evaluated after the opaque-invocation rule has passed. Every
# governed key is present; an empty tuple means the invocation is allowed.
RULES: dict[str, tuple[Rule, ...]] = {
    **{name: () for name in sorted(GOVERNED_GIT_SUBCOMMANDS)},
    'add': STAGING_RULES,
    'stage': STAGING_RULES,
    'commit': COMMIT_RULES,
    'gh pr merge': (),
    'gh api': (),
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


def evaluate_invocation(invocation: Invocation, context: Context) -> Decision:
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
