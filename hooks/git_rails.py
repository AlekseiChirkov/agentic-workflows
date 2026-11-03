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

SEVERITY = {'not_applicable': 0, 'allow': 1, 'ask': 2, 'deny': 3}


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

    @property
    def layout(self: Invocation) -> GitLayout:
        if self.program == 'git':
            return git_layout(self.words)
        return GitLayout(0, 0 if self.words else None, False)

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
        if operator in ('<<', '<<-'):
            if word.dynamic:
                raise ParseError('dynamic heredoc delimiter')
            quoted = any(char in raw for char in '\'"\\')
            self.src.pending.append(PendingHeredoc(word.text, operator == '<<-', quoted, node))
        elif operator == '<<<':
            node.stdin, node.stdin_kind = Word(word.text + '\n', word.dynamic), 'herestring'
        elif operator == '<':
            node.stdin, node.stdin_kind = None, 'file'
        return True

    # Heredoc bodies.
    def read_heredocs(self: Parser) -> None:
        pending, self.src.pending = self.src.pending, []
        for document in pending:
            body = self.read_heredoc_body(document)
            dynamic = not document.quoted and any(char in body for char in '$`\\')
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
        text, start = self.src.text, self.src.pos + 1
        level, index = 0, start
        while index < len(text):
            level += (text[index] == opening) - (text[index] == closing)
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

@dataclass
class Scope:
    """Shell state that later commands of the same list inherit."""
    directory: str | None
    last_known: str
    stack: list[str | None] = field(default_factory=list)
    git_names: tuple[str, ...] = ()

    def copy(self: Scope) -> Scope:
        return replace(self, stack=list(self.stack))

    def move(self: Scope, target: str) -> None:
        if self.directory is None and not os.path.isabs(target):
            return
        self.directory = os.path.realpath(os.path.join(self.directory or '/', target))
        self.last_known = self.directory


@dataclass(frozen=True)
class Found:
    """An invocation before repository resolution."""
    program: str
    words: tuple[Word, ...]
    environment: tuple[Word, ...]
    directory: str
    inherited: tuple[str, ...]
    stdin: Word | None


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
    """An unsupported construct and the last directory known before it."""
    directory: str


class Walker:
    """Walk the parsed command, tracking directories and exported git variables."""

    def __init__(self: Walker, budget: Budget) -> None:
        self.budget = budget
        self.items: list[Found | Opaque] = []

    def walk_script(self: Walker, script: Script, scope: Scope) -> None:
        for pipeline in script.pipelines:
            isolated = pipeline.background or len(pipeline.elements) > 1
            for element in pipeline.elements:
                self.walk_node(element, scope.copy() if isolated else scope)

    def walk_node(self: Walker, node: Simple | Group, scope: Scope) -> None:
        if isinstance(node, Group):
            self.walk_nested(node.redirections, scope)
            self.walk_script(node.body, scope.copy() if node.subshell else scope)
            return
        self.walk_nested(node, scope)
        if node.opaque:
            self.opaque(scope)
        if node.words:
            self.walk_command(node, scope)
        else:
            self.assign(node.assignments, scope)

    def walk_nested(self: Walker, node: Simple, scope: Scope) -> None:
        for script in node.nested:
            self.walk_script(script, scope.copy())

    def opaque(self: Walker, scope: Scope) -> None:
        self.items.append(Opaque(scope.directory or scope.last_known))

    def assign(self: Walker, words: Iterable[Word], scope: Scope) -> None:
        names = [assignment_name(word) for word in words]
        scope.git_names += tuple(name for name in names if is_git_name(name))

    def walk_command(self: Walker, node: Simple, scope: Scope) -> None:
        stripped = strip_wrappers(list(node.words), list(node.assignments))
        if stripped is None:
            self.opaque(scope)
            return
        words, environment = stripped
        if not words:
            return
        head = words[0]
        if head.dynamic:
            self.opaque(scope)
            return
        self.dispatch(Command(head.text, words, environment, node), scope)

    def dispatch(self: Walker, command: Command, scope: Scope) -> None:
        name, base, arguments = command.name, command.base, command.words[1:]
        if base in ('git', 'gh'):
            self.invocation(command, scope)
        elif is_opaque_program(name, base, arguments):
            self.opaque(scope)
        elif base in COMMAND_SHELLS:
            self.shell(arguments, command.node.depth, scope)
        elif name in ('cd', 'pushd', 'popd'):
            change_directory(name, arguments, scope)
        elif name in EXPORTING_BUILTINS:
            scope.git_names += exported_git_names(arguments)

    def invocation(self: Walker, command: Command, scope: Scope) -> None:
        relative = '/' in command.name and not command.name.startswith('/')
        if relative or scope.directory is None:
            self.opaque(scope)
            return
        self.items.append(Found(command.base, tuple(command.words[1:]), tuple(command.environment),
                                scope.directory, scope.git_names, command.node.stdin))

    def shell(self: Walker, arguments: list[Word], depth: int, scope: Scope) -> None:
        """Parse `bash -c '<literal>'` recursively; any other -c spelling is opaque."""
        if arguments and not arguments[0].dynamic and arguments[0].text == '-c':
            if len(arguments) < 2 or arguments[1].dynamic:
                self.opaque(scope)
                return
            self.walk_script(parse_script(arguments[1].text, self.budget, child_depth(depth)),
                             scope.copy())
        elif shell_runs_string(arguments):
            self.opaque(scope)


def child_depth(depth: int) -> int:
    if depth + 1 > MAX_DEPTH:
        raise LimitExceeded('depth')
    return depth + 1


def is_git_name(name: str) -> bool:
    return name.startswith('GIT_') or name == DYNAMIC_NAME


def strip_wrappers(words: list[Word], environment: list[Word]) -> tuple[list[Word], list[Word]] | None:
    """Remove supported wrappers; None when a wrapper is used in an unsupported way."""
    while words and not words[0].dynamic:
        name, rest = words[0].text, words[1:]
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
    return base in OTHER_SHELLS and shell_runs_string(arguments)


def shell_runs_string(arguments: list[Word]) -> bool:
    """Whether leading shell options include -c in any spelling, or cannot be read."""
    for word in arguments:
        if word.dynamic:
            return True
        if not word.text.startswith('-') or word.text in ('-', '--'):
            return False
        if not word.text.startswith('--') and 'c' in word.text[1:]:
            return True
    return False


def change_directory(name: str, arguments: list[Word], scope: Scope) -> None:
    """Literal cd/pushd/popd move the directory; anything else makes it unknown."""
    if arguments and not arguments[0].dynamic and arguments[0].text == '--':
        arguments = arguments[1:]
    literal = (len(arguments) == 1 and not arguments[0].dynamic and arguments[0].text != ''
               and not arguments[0].text.startswith('-'))
    if name == 'popd':
        restored = scope.stack.pop() if scope.stack and not arguments else None
        scope.directory = restored
        scope.last_known = restored or scope.last_known
    elif literal:
        if name == 'pushd':
            scope.stack.append(scope.directory)
        scope.move(arguments[0].text)
    else:
        scope.directory = None


def exported_git_names(arguments: list[Word]) -> tuple[str, ...]:
    names: list[str] = []
    for word in arguments:
        if not word.dynamic and word.text.startswith('-'):
            continue
        match = VARIABLE_NAME.match(word.text)
        complete = match is not None and word.text[match.end():match.end() + 1] in ('', '=', '+')
        name = match.group(0) if match and complete else DYNAMIC_NAME
        if is_git_name(name):
            names.append(name)
    return tuple(names)


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
        if words and not words[0].dynamic and words[0].text == 'api':
            return 'gh api'
        literal = len(words) > 1 and not words[0].dynamic and not words[1].dynamic
        return 'gh pr merge' if literal and (words[0].text, words[1].text) == ('pr', 'merge') else None
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
        return bool(words) and (words[0].dynamic or (words[0].text == 'pr' and len(words) > 1
                                                     and words[1].dynamic))
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
        walker = Walker(budget)
        walker.walk_script(parse_script(command, budget), Scope(context.cwd, context.cwd))
    except ParseError:
        return Resolution((), denial('unsupported-form') if registered else NOT_APPLICABLE)
    except LimitExceeded:
        return Resolution((), denial('limit-exceeded') if registered else NOT_APPLICABLE)
    try:
        return resolve_items(walker.items, context, registered)
    except GitReadTimeout:
        return Resolution((), denial('limit-exceeded'))
    except OSError:
        return Resolution((), denial('internal-error'))


def resolve_items(items: Sequence[Found | Opaque], context: Context, registered: bool) -> Resolution:
    invocations: list[Invocation] = []
    denials: list[Decision] = []
    for item in items:
        if isinstance(item, Opaque):
            if registered or project_for(item.directory, context.roots) is not None:
                denials.append(denial('unsupported-form'))
            continue
        result = resolve_found(item, context)
        if isinstance(result, Decision):
            denials.append(result)
        elif result is not None:
            invocations.append(result)
    return Resolution(tuple(invocations), combine(denials) if denials else None)


def resolve_found(found: Found, context: Context) -> Invocation | Decision | None:
    directory = effective_directory(found)
    project = project_for(directory, context.roots)
    if project is None:
        return None
    draft = Invocation(found.program, found.words, directory, None, None, project,
                       found.environment, found.inherited, found.stdin)
    if not os.path.isdir(directory):
        return denial('unsupported-form') if needs_verification(draft) else None
    location = read_repository(directory, context.environ)
    if location is None:
        return None
    subcommand = draft.subcommand if found.program == 'git' else None
    alias = (subcommand is not None and not draft.words[draft.layout.index or 0].dynamic
             and subcommand not in GIT_BUILTINS and is_alias(subcommand, directory, context.environ))
    return replace(draft, repository=location[0], common_dir=location[1], alias=alias)


# ── Rules ──────────────────────────────────────────────────────────────

Rule = Callable[[Invocation, Context], Decision | None]

# Per-subcommand rules, evaluated after the opaque-invocation rule has passed. Every
# governed key is present; an empty tuple means the invocation is allowed.
RULES: dict[str, tuple[Rule, ...]] = {
    **{name: () for name in sorted(GOVERNED_GIT_SUBCOMMANDS)},
    'gh pr merge': (),
    'gh api': (),
}


def check_opaque_invocation(invocation: Invocation) -> Decision | None:
    """R31: a git environment assignment, unsupported global option, alias or dynamic word."""
    names = (*invocation.assignments, *invocation.inherited)
    if any(is_git_name(name) for name in names):
        return denial('opaque-environment', 'R31')
    unsupported = denial('unsupported-form', 'R31')
    if any(word.dynamic for word in invocation.environment):
        return unsupported
    layout = invocation.layout
    if invocation.program == 'git' and (layout.unknown or
                                        unsupported_global_options(invocation.words[:layout.globals_end])):
        return unsupported
    if invocation.alias:
        return unsupported
    if layout.index is not None and invocation.words[layout.index].dynamic:
        return unsupported
    if invocation.program == 'gh' and needs_verification(invocation) and not invocation.governed:
        return unsupported
    if invocation.governed and any(word.dynamic and not exempt_word(invocation, word)
                                   for word in invocation.arguments):
        return unsupported
    return None


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
    results = [rule(invocation, context) for rule in RULES.get(key, ())]
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
