#!/usr/bin/env python3
"""Read and edit the subtask-progress section of one task state.md through a structural parser.

Usage:
  python3 scripts/state-tool.py get      --root R --task T [--block ID] [--field NAME]
  python3 scripts/state-tool.py validate --root R --task T [--block ID]
  python3 scripts/state-tool.py set      --root R --task T --block ID --expected-revision REV
                                         --operation-id OP --field NAME=VALUE [--field ...]
                                         [--lock-wait-seconds N]

Contract: stdout carries exactly one JSON object (schema_version 1); diagnostics go to
stderr only. Read commands create, modify and delete no file. A write holds the per-task
lock file .state-tool.lock, checks the expected revision, changes only the lines of the
named fields plus the state_receipts line, and replaces state.md with one rename of its
own temporary file. Python 3.11 or newer and the standard library only; no input value is
ever passed to a shell or interpreter.

Exit codes: 0 read, valid, applied or unchanged; 1 internal-error; 2 invalid invocation
(invalid-arguments, unknown-command, malformed-revision, invalid-operation-id,
path-outside-root); 3 structure or version refused (state-missing, section-missing,
section-duplicate, block-missing, block-duplicate, malformed-block, malformed-receipts,
unrecognized-prefix, unknown-header-field, unsupported-contract-version,
unsupported-encoding); 4 revision conflict (revision-conflict, state-file-changed); 5 lock
busy (lock-busy); 6 field, value or invariant refused (invalid-value, read-only-field,
field-not-applicable, and for validate n-a-unjustified, completion-without-tests,
required-field-missing); 7 file system or runtime (io-error, unsafe-state-file,
unsafe-lock-path, locking-unavailable, python-too-old). validate exits 3 before 6 when
both kinds of error exist and lists every error.
"""
import sys

if sys.version_info < (3, 11):
    sys.stdout.write('{"schema_version": 1, "command": null, "result": "rejected", "task": null, '
                     '"source_revision": null, "errors": [{"code": "python-too-old", '
                     '"message": "Python 3.11 or newer is required"}], "warnings": [], '
                     '"stale_temp_files": []}\n')
    sys.stderr.write("state-tool: python-too-old: Python 3.11 or newer is required\n")
    sys.exit(7)

from dataclasses import dataclass, field
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
import re
import secrets
import socket
import stat
import time
from typing import Any

try:
    import fcntl  # Needed only by write commands; reads must work without it.
except ImportError:
    fcntl = None

SCHEMA_VERSION = 1

ATOMIC_STATUS_VALUES = ("not-started", "in-progress", "complete", "blocked", "skipped", "failed")
ATOMIC_TESTS_VALUES = ("not-started", "red", "pinned", "green", "n-a", "failed")
ROLLUP_VALUES = ("not-started", "in-progress", "done", "blocked")
INTEGRATION_VALIDATION_VALUES = ("not-started", "in-progress", "complete", "failed")

SECTION_HEADING = "## Subtask Progress"
COMPOSITE_PREFIX = "[composite]"
BLOCK_ID_PATTERN = r"T-[0-9]{2,}[a-z]?(?:-fix-[a-z0-9]+(?:-[a-z0-9]+)*)?"
BLOCK_ID = re.compile(BLOCK_ID_PATTERN)
HEADER = re.compile(r"(\[[^\]]+\] )?(" + BLOCK_ID_PATTERN + r") \| ([^|]+?) \|"
                    r"((?: [a-z][a-z-]*: [^|]*\|)*(?: [a-z][a-z-]*: [^|]*))")
FIELD_LINE = re.compile(r"  ([a-z][a-z0-9_-]*):( .*)?")
FENCE_OPEN = re.compile(r" {0,3}(```|~~~)")
SECTION_END = re.compile(r"#{1,2} ")
CONTRACT_VERSION = re.compile(r"contract_version: ([0-9]+)\.([0-9]+)\.([0-9]+)")
TOOL_VERSION = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")
RECEIPT_ENTRY = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]{0,63})#[0-9a-f]{16}")
STALE_TEMP = re.compile(r"\.state\.md\..+\.tmp")
BOM = b"\xef\xbb\xbf"
MAX_RECEIPTS = 20
REVISION = re.compile(r"sha256:[0-9a-f]{64}")
OPERATION_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
LOCK_WAIT = re.compile(r"[0-9]+")
MAX_LOCK_WAIT_SECONDS = 600
DEFAULT_LOCK_WAIT_SECONDS = 5
LOCK_RETRY_SECONDS = 0.025
LOCK_NAME = ".state-tool.lock"
NO_BYPASS = "Do not edit state.md by hand to bypass this refusal."
NO_BYPASS_EXITS = frozenset({4, 5, 6, 8})

KNOWN_HEADER_FIELDS = {
    "leaf": ("atomic-tests", "atomic-execution", "atomic-validation"),
    "composite": ("rollup", "integration-validation"),
}
KNOWN_FIELDS = {
    "leaf": ("last_action", "target_files", "blocker", "notes", "branch", "base_branch",
             "base_commit", "commits", "pr", "state_receipts"),
    "composite": ("children", "blocker", "notes", "state_receipts"),
}
REQUIRED_FIELDS = {
    "leaf": ("notes", "target_files"),
    "composite": ("children", "blocker", "notes"),
}
REPEATABLE_FIELDS = frozenset({"notes"})
STATUS_VOCABULARY = {
    "atomic-tests": ATOMIC_TESTS_VALUES,
    "atomic-execution": ATOMIC_STATUS_VALUES,
    "atomic-validation": ATOMIC_STATUS_VALUES,
    "rollup": ROLLUP_VALUES,
    "integration-validation": INTEGRATION_VALIDATION_VALUES,
}
N_A_JUSTIFICATION = "tdd: none — "
PRE_TDD_NOTE = "pre-TDD task, TDD step skipped"
COMPLETION_TEST_VALUES = ("green", "n-a")
# Fields set may change per block kind; every other field is read-only or not applicable.
SET_WRITABLE_FIELDS = {
    "leaf": ("atomic-tests", "atomic-execution", "atomic-validation", "last_action", "blocker"),
    "composite": ("rollup", "integration-validation", "blocker"),
}
NON_EMPTY_FIELDS = ("last_action", "blocker")
SINGLE_LINE_FORBIDDEN = ("\r", "\n", "\x00")

# Per command: options taking one value, repeatable options and required options.
COMMANDS: dict[str, dict[str, frozenset[str]]] = {
    "get": {"single": frozenset({"--root", "--task", "--block", "--field"}),
            "repeatable": frozenset(),
            "required": frozenset({"--root", "--task"})},
    "validate": {"single": frozenset({"--root", "--task", "--block"}),
                 "repeatable": frozenset(),
                 "required": frozenset({"--root", "--task"})},
    "set": {"single": frozenset({"--root", "--task", "--block", "--expected-revision",
                                 "--operation-id", "--lock-wait-seconds"}),
            "repeatable": frozenset({"--field"}),
            "required": frozenset({"--root", "--task", "--block", "--expected-revision",
                                   "--operation-id", "--field"})},
}
WRITE_COMMANDS = frozenset({"set"})
# The result a command reports for any non-zero exit.
REFUSED_RESULT = {"get": "rejected", "validate": "invalid", "set": "rejected"}


class ToolError(Exception):
    """A refusal carrying its exit code, error code, message and optional line number."""

    def __init__(self, exit_code: int, code: str, message: str, line: int | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.code = code
        self.message = message
        self.line = line

    def as_error(self) -> dict[str, Any]:
        error: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.line is not None:
            error["line"] = self.line
        return error


@dataclass
class FieldGroup:
    """A field line plus its continuation lines; indexes are positions in the line list."""
    name: str
    value: str
    start: int
    continuation: list[str] = field(default_factory=list)
    end: int = 0


@dataclass
class Block:
    """One progress block: header, field groups and the problems found while parsing it."""
    block_id: str
    prefix: str | None
    name: str
    header_fields: list[tuple[str, str]]
    start: int
    end: int = 0
    groups: list[FieldGroup] = field(default_factory=list)
    malformed: list[tuple[int, str]] = field(default_factory=list)

    @property
    def kind(self) -> str:
        return "composite" if self.prefix == COMPOSITE_PREFIX else "leaf"


@dataclass
class Document:
    """Lines of state.md (each with its own terminator) and the parsed progress section."""
    lines: list[str]
    fenced: list[bool]
    section_start: int
    section_end: int
    blocks: list[Block]


@dataclass
class TaskPaths:
    root: str
    task: str
    relative_task: str
    state: str


# ---------------------------------------------------------------- argument parsing

def split_arguments(argv: list[str]) -> tuple[str, dict[str, list[str]]]:
    """Split argv into a known command and its options; refuse unknown commands and options."""
    if not argv or argv[0] not in COMMANDS:
        shown = argv[0] if argv else "<none>"
        raise ToolError(2, "unknown-command", f"unknown command: {shown}")
    command, spec = argv[0], COMMANDS[argv[0]]
    options: dict[str, list[str]] = {}
    index = 1
    while index < len(argv):
        option = argv[index]
        if option not in spec["single"] | spec["repeatable"]:
            raise ToolError(2, "invalid-arguments", f"unknown option for {command}: {option}")
        if index + 1 >= len(argv):
            raise ToolError(2, "invalid-arguments", f"option {option} requires a value")
        if option in spec["single"] and option in options:
            raise ToolError(2, "invalid-arguments", f"option {option} given more than once")
        options.setdefault(option, []).append(argv[index + 1])
        index += 2
    return command, options


def check_arguments(command: str, options: dict[str, list[str]]) -> None:
    """Refuse missing required options and malformed option values with exit 2."""
    missing = sorted(COMMANDS[command]["required"] - options.keys())
    if missing:
        raise ToolError(2, "invalid-arguments", "missing required option: " + ", ".join(missing))
    for block_id in options.get("--block", []):
        if not BLOCK_ID.fullmatch(block_id):
            raise ToolError(2, "invalid-arguments", f"invalid block id: {block_id}")
    if command in WRITE_COMMANDS:
        check_write_arguments(options)
        return
    for name in options.get("--field", []):
        if not name:
            raise ToolError(2, "invalid-arguments", "field name must not be empty")


def check_write_arguments(options: dict[str, list[str]]) -> None:
    expected = options["--expected-revision"][0]
    if not REVISION.fullmatch(expected):
        raise ToolError(2, "malformed-revision",
                        f"expected revision must be sha256: and 64 lowercase hex digits: {expected}")
    operation_id = options["--operation-id"][0]
    if not OPERATION_ID.fullmatch(operation_id):
        raise ToolError(2, "invalid-operation-id", f"invalid operation id: {operation_id}")
    field_pairs(options)
    lock_wait_seconds(options)


def field_pairs(options: dict[str, list[str]]) -> list[tuple[str, str]]:
    """Split every --field at its first '='; a missing '=', an empty or repeated name is refused."""
    pairs: list[tuple[str, str]] = []
    for item in options.get("--field", []):
        name, separator, value = item.partition("=")
        if not separator or not name:
            raise ToolError(2, "invalid-arguments", f"--field needs NAME=VALUE: {item}")
        if name in (seen for seen, _ in pairs):
            raise ToolError(2, "invalid-arguments", f"field {name} given more than once")
        pairs.append((name, value))
    return pairs


def lock_wait_seconds(options: dict[str, list[str]]) -> int:
    text = options.get("--lock-wait-seconds", [str(DEFAULT_LOCK_WAIT_SECONDS)])[0]
    if not LOCK_WAIT.fullmatch(text) or int(text) > MAX_LOCK_WAIT_SECONDS:
        raise ToolError(2, "invalid-arguments",
                        f"--lock-wait-seconds must be an integer from 0 to {MAX_LOCK_WAIT_SECONDS}")
    return int(text)


def note_write_identity(options: dict[str, list[str]], report: dict[str, Any]) -> None:
    """Report the operation id and block id when they are present and well formed."""
    operation_id = options.get("--operation-id", [None])[0]
    if operation_id is not None and OPERATION_ID.fullmatch(operation_id):
        report["operation_id"] = operation_id
    block_id = options.get("--block", [None])[0]
    if block_id is not None and BLOCK_ID.fullmatch(block_id):
        report["block_id"] = block_id


# ---------------------------------------------------------------- paths and file reads

def resolve_paths(root_argument: str, task_argument: str) -> TaskPaths:
    """Resolve root and task physically and require the task inside the root."""
    root = os.path.realpath(root_argument)
    if not os.path.isdir(root):
        raise ToolError(2, "invalid-arguments", f"root is not a directory: {root_argument}")
    task = os.path.realpath(task_argument)
    if task != root and not task.startswith(root.rstrip(os.sep) + os.sep):
        raise ToolError(2, "path-outside-root", f"task {task_argument} is outside root {root_argument}")
    relative = os.path.relpath(task, root).replace(os.sep, "/")
    return TaskPaths(root, task, relative, os.path.join(task, "state.md"))


def stale_temp_files(task: str) -> list[str]:
    """List leftover temporary candidates by name; they are never opened or removed."""
    try:
        names = os.listdir(task)
    except OSError:
        return []
    return sorted(name for name in names if STALE_TEMP.fullmatch(name))


def read_state(path: str) -> bytes:
    """Read state.md without following a symbolic link and require a regular file."""
    return read_state_file(path)[0]


def read_state_file(path: str) -> tuple[bytes, os.stat_result]:
    """Read state.md like read_state and return its bytes with the status of the open file."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        raise ToolError(3, "state-missing", f"state.md is missing: {path}") from None
    except OSError as error:
        raise ToolError(7, "io-error", f"cannot inspect state.md: {error.strerror}") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ToolError(7, "unsafe-state-file", "state.md must be a regular file, not a link")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ToolError(7, "unsafe-state-file" if os.path.islink(path) else "io-error",
                        f"cannot open state.md: {error.strerror}") from None
    with os.fdopen(descriptor, "rb") as handle:
        opened = os.fstat(handle.fileno())
        if not stat.S_ISREG(opened.st_mode):
            raise ToolError(7, "unsafe-state-file", "state.md must be a regular file")
        return handle.read(), opened


def revision(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def decode_state(data: bytes) -> str:
    """Accept only UTF-8 without a byte order mark and without carriage returns."""
    if data.startswith(BOM):
        raise ToolError(3, "unsupported-encoding", "state.md starts with a byte order mark")
    if b"\r" in data:
        raise ToolError(3, "unsupported-encoding", "state.md contains carriage returns")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ToolError(3, "unsupported-encoding",
                        f"state.md is not valid UTF-8 at byte {error.start}") from None


# ---------------------------------------------------------------- contract version

def split_lines(text: str) -> list[str]:
    """Split on LF only, keeping each terminator so the bytes can be reassembled exactly."""
    lines = text.split("\n")
    result = [line + "\n" for line in lines[:-1]]
    if lines[-1]:
        result.append(lines[-1])
    return result


def content(line: str) -> str:
    return line[:-1] if line.endswith("\n") else line


def fence_openers(lines: list[str]) -> list[int | None]:
    """For every line that opens, lies inside or closes a fence, the index of its opening line."""
    openers: list[int | None] = []
    marker: str | None = None
    opener = 0
    for index, line in enumerate(lines):
        text = content(line)
        if marker is None:
            opened = FENCE_OPEN.match(text)
            if opened:
                marker, opener = opened.group(1), index
            openers.append(index if opened else None)
            continue
        openers.append(opener)
        if re.match(r" {0,3}" + re.escape(marker), text):
            marker = None
    return openers


def fence_flags(lines: list[str]) -> list[bool]:
    """Mark every line that opens, lies inside or closes a fenced code block."""
    return [opener is not None for opener in fence_openers(lines)]


def task_contract_version(lines: list[str], fenced: list[bool]) -> tuple[str, tuple[int, ...]] | None:
    """Return the first well-formed contract_version line before the first level-2 heading."""
    for line, is_fenced in zip(lines, fenced):
        text = content(line)
        if is_fenced:
            continue
        if text.startswith("## "):
            return None
        match = CONTRACT_VERSION.fullmatch(text)
        if match:
            return text.split(": ", 1)[1], tuple(int(part) for part in match.groups())
    return None


def tool_contract_version() -> tuple[int, ...] | None:
    """Read VERSION from the parent of this script's directory; None when unusable."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "VERSION")
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read().strip()
    except (OSError, UnicodeDecodeError):
        return None
    match = TOOL_VERSION.fullmatch(text)
    return tuple(int(part) for part in match.groups()) if match else None


def contract_version_supported(task_version: tuple[int, ...] | None) -> bool:
    if task_version is None:
        return True
    tool_version = tool_contract_version()
    return tool_version is not None and task_version <= tool_version


# ---------------------------------------------------------------- document parsing

def locate_section(lines: list[str], fenced: list[bool]) -> tuple[int, int]:
    """Return the heading index and the exclusive end index of the progress section."""
    starts = [index for index, line in enumerate(lines)
              if not fenced[index] and content(line) == SECTION_HEADING]
    if not starts:
        raise ToolError(3, "section-missing", f"no '{SECTION_HEADING}' section")
    if len(starts) > 1:
        raise ToolError(3, "section-duplicate", f"'{SECTION_HEADING}' occurs {len(starts)} times",
                        starts[1] + 1)
    start = starts[0]
    for index in range(start + 1, len(lines)):
        if not fenced[index] and SECTION_END.match(content(lines[index])):
            return start, index
    return start, len(lines)


def parse_header(text: str, index: int) -> Block | None:
    match = HEADER.fullmatch(text)
    if not match:
        return None
    segments = [segment.strip() for segment in match.group(4).split("|")]
    header_fields = []
    for segment in segments:
        name, _, value = segment.partition(":")
        header_fields.append((name, value.strip()))
    prefix = match.group(1).strip() if match.group(1) else None
    return Block(match.group(2), prefix, match.group(3), header_fields, index)


def indentation(text: str) -> int:
    return len(text) - len(text.lstrip(" "))


def continues_after_blanks(lines: list[str], fenced: list[bool], index: int, end: int) -> bool:
    """True when blank lines at index are followed by a continuation-indented line."""
    while index < end and content(lines[index]) == "":
        index += 1
    return (index < end and not fenced[index]
            and indentation(content(lines[index])) >= 3)


def parse_blocks(lines: list[str], openers: list[int | None], start: int, end: int) -> list[Block]:
    """Parse the section body into blocks; lines outside blocks are foreign and kept as is.

    A fence opened at column 0 ends the current block. A fence opened at 1-3 spaces inside a
    block is opaque block content: its lines are neither field, continuation nor malformed
    lines, and a continuation line after it still belongs to the preceding field line.
    """
    fenced = [opener is not None for opener in openers]
    blocks: list[Block] = []
    current: Block | None = None
    group: FieldGroup | None = None

    def close(at: int) -> None:
        nonlocal current, group
        if current is not None:
            current.end = at
            blocks.append(current)
        current, group = None, None

    index = start + 1
    while index < end:
        text = content(lines[index])
        header = None if fenced[index] else parse_header(text, index)
        opener = openers[index]
        if header is not None:
            close(index)
            current = header
        elif current is not None and opener is not None and indentation(content(lines[opener])):
            pass  # A line of a fence opened inside this block: opaque block content.
        elif current is None or fenced[index]:
            close(index)
        elif text == "":
            if not continues_after_blanks(lines, fenced, index, end):
                close(index)
            elif group is not None:
                group.continuation.append(text)
                group.end = index + 1
        elif text.startswith("\t"):
            current.malformed.append((index + 1, "tab-indented line"))
        elif indentation(text) >= 3:
            if group is None:
                current.malformed.append((index + 1, "continuation line without a field line"))
            else:
                group.continuation.append(text)
                group.end = index + 1
        elif indentation(text) == 2:
            match = FIELD_LINE.fullmatch(text)
            if match is None:
                current.malformed.append((index + 1, "two-space line that is not a field line"))
                group = None
            else:
                value = match.group(2)[1:] if match.group(2) else ""
                group = FieldGroup(match.group(1), value, index, end=index + 1)
                current.groups.append(group)
        elif indentation(text) == 1:
            current.malformed.append((index + 1, "line indented by one space"))
        else:
            close(index)
        index += 1
    close(end)
    for block in blocks:
        statuses = [name for name, _ in block.header_fields
                    if name in KNOWN_HEADER_FIELDS[block.kind]]
        for name in unique([name for name in statuses if statuses.count(name) > 1]):
            block.malformed.append((block.start + 1, f"repeated header field {name}"))
        known = KNOWN_FIELDS[block.kind]
        seen: set[str] = set()
        for item in block.groups:
            if item.name in known and item.name not in REPEATABLE_FIELDS and item.name in seen:
                block.malformed.append((item.start + 1, f"repeated field {item.name}"))
            seen.add(item.name)
    return blocks


def parse_document(text: str) -> Document:
    lines = split_lines(text)
    openers = fence_openers(lines)
    fenced = [opener is not None for opener in openers]
    start, end = locate_section(lines, fenced)
    return Document(lines, fenced, start, end, parse_blocks(lines, openers, start, end))


# ---------------------------------------------------------------- block reporting

def receipts_problem(block: Block) -> int | None:
    """Return the 1-based line of the first state_receipts line that breaks the 1-20 unique
    well-formed entry rule, or None when every such line is well formed."""
    for item in (group for group in block.groups if group.name == "state_receipts"):
        entries = item.value.split(", ") if item.value else []
        matches = [RECEIPT_ENTRY.fullmatch(entry) for entry in entries]
        identifiers = [match.group(1) for match in matches if match is not None]
        if (item.continuation or not 1 <= len(entries) <= MAX_RECEIPTS
                or len(identifiers) != len(entries)
                or len(set(identifiers)) != len(identifiers)):
            return item.start + 1
    return None


def missing_required_fields(block: Block) -> list[str]:
    names = {group.name for group in block.groups}
    return [name for name in REQUIRED_FIELDS[block.kind] if name not in names]


def advisory_warnings(block: Block) -> list[str]:
    """Warnings every read reports for a block: an unrecognized prefix or header field."""
    warnings = []
    if block.prefix is not None and block.prefix != COMPOSITE_PREFIX:
        warnings.append("unrecognized-prefix")
    known_header = KNOWN_HEADER_FIELDS[block.kind]
    if any(name not in known_header for name, _ in block.header_fields):
        warnings.append("unknown-header-field")
    return warnings


def block_warnings(block: Block) -> list[str]:
    warnings = advisory_warnings(block)
    if missing_required_fields(block):
        warnings.append("required-field-missing")
    if receipts_problem(block):
        warnings.append("malformed-receipts")
    return warnings


# ---------------------------------------------------------------- invariants

def value_in_vocabulary(name: str, value: str) -> bool:
    """True when a known header status value is in that field's vocabulary; a value outside
    it is reported as invalid-value."""
    return value in STATUS_VOCABULARY[name]


def n_a_justified(notes: str) -> bool:
    """True when the notes text holds the test-level gate's justification, which an n-a test
    status needs; without it the block is reported as n-a-unjustified."""
    return N_A_JUSTIFICATION in notes


def completion_allowed(tests: str | None, notes: str) -> bool:
    """True when a leaf may record complete execution without a previous value to compare:
    its tests are green or n-a, or it has no tests segment and its notes text holds the
    pre-TDD note; otherwise the block is reported as completion-without-tests."""
    if tests is None:
        return PRE_TDD_NOTE in notes
    return tests in COMPLETION_TEST_VALUES


def notes_text(block: Block) -> str:
    """Every notes field group of the block in file order, continuation lines included."""
    parts: list[str] = []
    for group in block.groups:
        if group.name == "notes":
            parts.append(group.value)
            parts.extend(group.continuation)
    return "\n".join(parts)


def invariant_errors(block: Block) -> list[ToolError]:
    """Rule violations of one block that need no previous value, each an exit-6 error:
    header status values outside their vocabulary, an unjustified n-a test status,
    completion without passing or justified tests, and missing required field lines."""
    errors: list[ToolError] = []
    line = block.start + 1
    known_header = KNOWN_HEADER_FIELDS[block.kind]
    for name, value in block.header_fields:
        if name in known_header and not value_in_vocabulary(name, value):
            errors.append(ToolError(6, "invalid-value",
                                    f"block {block.block_id}: {name} value '{value}' is not "
                                    "in its vocabulary", line))
    if block.kind == "leaf":
        header = dict(block.header_fields)
        notes = notes_text(block)
        if header.get("atomic-tests") == "n-a" and not n_a_justified(notes):
            errors.append(ToolError(6, "n-a-unjustified",
                                    f"block {block.block_id}: atomic-tests n-a without a notes "
                                    f"line containing '{N_A_JUSTIFICATION}'", line))
        if (header.get("atomic-execution") == "complete"
                and not completion_allowed(header.get("atomic-tests"), notes)):
            errors.append(ToolError(6, "completion-without-tests",
                                    f"block {block.block_id}: atomic-execution complete without "
                                    "green or n-a tests or the pre-TDD note", line))
    missing = missing_required_fields(block)
    if missing:
        errors.append(ToolError(6, "required-field-missing",
                                f"block {block.block_id}: missing " + ", ".join(missing), line))
    return errors


def pre_tdd_exception(block: Block) -> str | None:
    if block.kind != "leaf":
        return None
    header = dict(block.header_fields)
    applicable = "atomic-tests" not in header and header.get("atomic-execution") == "in-progress"
    return "applicable" if applicable else "not-applicable"


def describe_block(block: Block, field_name: str | None) -> dict[str, Any]:
    known = KNOWN_FIELDS[block.kind]
    header_fields = [{"name": name, "value": value} for name, value in block.header_fields
                     if field_name is None or name == field_name]
    fields = [{"name": group.name, "value": group.value, "continuation": list(group.continuation),
               "known": group.name in known}
              for group in block.groups if field_name is None or group.name == field_name]
    return {"block_id": block.block_id, "block_kind": block.kind, "prefix": block.prefix,
            "name": block.name, "header_fields": header_fields, "fields": fields,
            "pre_tdd_exception": pre_tdd_exception(block)}


def structure_problems(blocks: list[Block]) -> list[tuple[str, ToolError]]:
    """Return (block id, error) for every duplicated id and every malformed block."""
    problems: list[tuple[str, ToolError]] = []
    counts: dict[str, int] = {}
    for block in blocks:
        counts[block.block_id] = counts.get(block.block_id, 0) + 1
    reported: set[str] = set()
    for block in blocks:
        if counts[block.block_id] > 1 and block.block_id not in reported:
            reported.add(block.block_id)
            problems.append((block.block_id, ToolError(
                3, "block-duplicate", f"block {block.block_id} occurs {counts[block.block_id]} times",
                block.start + 1)))
    for block in blocks:
        for line, reason in block.malformed:
            problems.append((block.block_id, ToolError(
                3, "malformed-block", f"block {block.block_id}: {reason}", line)))
    return problems


def unique(codes: list[str]) -> list[str]:
    return list(dict.fromkeys(codes))


# ---------------------------------------------------------------- field edits

def writable_problem(block: Block, name: str) -> ToolError | None:
    """Refuse a field set may not change on this block kind: one that belongs only to the other
    kind is not applicable; any other field outside the writable list is read-only."""
    kind = block.kind
    if name in SET_WRITABLE_FIELDS[kind]:
        return None
    own = KNOWN_HEADER_FIELDS[kind] + KNOWN_FIELDS[kind]
    other = "composite" if kind == "leaf" else "leaf"
    if name not in own and name in KNOWN_HEADER_FIELDS[other] + KNOWN_FIELDS[other]:
        return ToolError(6, "field-not-applicable",
                         f"field {name} does not apply to {kind} block {block.block_id}")
    return ToolError(6, "read-only-field", f"field {name} cannot be changed by set")


def value_problem(name: str, value: str) -> str | None:
    """Return why a value breaks the content rules, or None: values are single-line UTF-8
    text, last_action and blocker are non-empty, and header statuses are in their vocabulary."""
    if any(character in value for character in SINGLE_LINE_FORBIDDEN):
        return "must be a single line without CR, LF or NUL"
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return "must be valid UTF-8"
    if name in NON_EMPTY_FIELDS and not value.strip():
        return "must not be empty"
    if name in STATUS_VOCABULARY and not value_in_vocabulary(name, value):
        return "is not in its vocabulary"
    return None


def check_field_changes(block: Block, pairs: list[tuple[str, str]]) -> None:
    """Check writability of every named field first, then the content of every value."""
    for name, _ in pairs:
        problem = writable_problem(block, name)
        if problem is not None:
            raise problem
    for name, value in pairs:
        reason = value_problem(name, value)
        if reason is not None:
            raise ToolError(6, "invalid-value", f"block {block.block_id}: {name} value {reason}")


def changed_pairs(block: Block, pairs: list[tuple[str, str]]) -> dict[str, str]:
    """The requested fields whose value differs from the block, an absent field included."""
    header = dict(block.header_fields)
    lines = {group.name: group.value for group in block.groups}
    changes: dict[str, str] = {}
    for name, value in pairs:
        current = header.get(name) if name in KNOWN_HEADER_FIELDS[block.kind] else lines.get(name)
        if current != value:
            changes[name] = value
    return changes


def edit_header(text: str, kind: str, changes: dict[str, str]) -> tuple[str, list[str]]:
    """Replace the values of changed status segments in place and insert absent ones before the
    first present segment that follows them in canonical order; return the new header text and
    the changed names in header order."""
    parts = text.split("|")
    names = [""] * 2 + [part.partition(":")[0].strip() for part in parts[2:]]
    order = KNOWN_HEADER_FIELDS[kind]
    for name in order:
        if name not in changes:
            continue
        value = changes[name]
        if name in names[2:]:
            index = names.index(name, 2)
            label, _, raw = parts[index].partition(":")
            stripped = raw.strip()
            lead = len(raw) - len(raw.lstrip())
            parts[index] = label + ":" + raw[:lead] + value + raw[lead + len(stripped):]
            continue
        later = order[order.index(name) + 1:]
        index = next((position for position in range(2, len(parts)) if names[position] in later),
                     len(parts))
        if index == len(parts):
            parts[-1] = parts[-1].rstrip() + " "
            parts.append(f" {name}: {value}")
        else:
            parts.insert(index, f" {name}: {value} ")
        names.insert(index, name)
    return "|".join(parts), [name for name in names[2:] if name in changes]


def insertion_anchor(block: Block, name: str, planned: list[tuple[tuple[int, int], str]]) -> int:
    """Index of the line a missing known field goes after: the last line of the last field
    group, in file order, whose name precedes it in canonical order (planned insertions
    included); the header when there is none. A fence is never part of a field group."""
    order = KNOWN_FIELDS[block.kind]
    earlier = set(order[:order.index(name)])
    keys = [(group.end - 1, 0) for group in block.groups if group.name in earlier]
    keys += [key for key, planned_name in planned if planned_name in earlier]
    return max(keys)[0] if keys else block.start


def build_candidate(document: Document, block: Block, changes: dict[str, str],
                    receipt: str) -> tuple[str, list[str]]:
    """Return the candidate text and the changed field names. Unchanged lines are copied
    byte for byte; changed lines are replaced in place; missing fields and the receipts line
    are inserted at their canonical positions; the final-newline state is kept."""
    contents = [content(line) for line in document.lines]
    replacements: dict[int, str] = {}
    insertions: dict[int, list[str]] = {}
    planned: list[tuple[tuple[int, int], str]] = []

    def put(name: str, line: str) -> None:
        groups = [group for group in block.groups if group.name == name]
        if groups:
            replacements[groups[0].start] = line
            return
        anchor = insertion_anchor(block, name, planned)
        insertions.setdefault(anchor, []).append(line)
        planned.append(((anchor, len(insertions[anchor])), name))

    header_changes = {name: value for name, value in changes.items()
                      if name in KNOWN_HEADER_FIELDS[block.kind]}
    changed: list[str] = []
    if header_changes:
        replacements[block.start], changed = edit_header(contents[block.start], block.kind,
                                                         header_changes)
    for name in KNOWN_FIELDS[block.kind]:
        if name in changes and name not in header_changes:
            put(name, f"  {name}: {changes[name]}")
            changed.append(name)
    existing = [group for group in block.groups if group.name == "state_receipts"]
    entries = existing[0].value + ", " + receipt if existing else receipt
    put("state_receipts", f"  state_receipts: {entries}")
    changed.append("state_receipts")
    output: list[str] = []
    for index, text in enumerate(contents):
        output.append(replacements.get(index, text))
        output.extend(insertions.get(index, []))
    final_newline = "\n" if "".join(document.lines).endswith("\n") else ""
    return "\n".join(output) + final_newline, changed


def verify_candidate(document: Document, block: Block, candidate: str,
                     changes: dict[str, str]) -> None:
    """Re-parse the candidate and confirm that lines outside the block and every unchanged
    line of the block are identical and that the block reads back the written values."""
    original = [content(line) for line in document.lines]
    lines = split_lines(candidate)
    new = [content(line) for line in lines]
    try:
        reparsed = parse_document(candidate)
    except ToolError as error:
        raise ToolError(1, "internal-error", f"candidate does not parse: {error.message}") from None
    matches = [item for item in reparsed.blocks if item.block_id == block.block_id]
    tail = len(original) - block.end
    problems = []
    if len(matches) != 1 or matches[0].malformed or receipts_problem(matches[0]) is not None:
        problems.append("target block does not read back")
    if new[:block.start] != original[:block.start] or new[len(new) - tail:] != original[block.end:]:
        problems.append("lines outside the block changed")
    replaced = ({group.start for group in block.groups if group.name in changes
                 or group.name == "state_receipts"} | {block.start})
    kept = [text for index, text in enumerate(original[block.start:block.end], block.start)
            if index not in replaced]
    remaining = iter(new[block.start:len(new) - tail])
    if not all(any(text == other for other in remaining) for text in kept):
        problems.append("an unchanged block line changed")
    if not problems:
        target = matches[0]
        values = dict(target.header_fields) | {group.name: group.value for group in target.groups}
        if any(values.get(name) != value for name, value in changes.items()):
            problems.append("a written value does not read back")
    if problems:
        raise ToolError(1, "internal-error", "candidate check failed: " + "; ".join(problems))


# ---------------------------------------------------------------- receipts

def input_digest(command: str, block_id: str, inputs: dict[str, Any]) -> str:
    """First 16 hex characters of SHA-256 over the canonical UTF-8 JSON of an operation."""
    payload = json.dumps({"command": command, "block_id": block_id, "inputs": inputs},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def set_inputs(pairs: list[tuple[str, str]]) -> dict[str, Any]:
    """Inputs of set for the digest: field pairs sorted by name, notes in argument order."""
    return {"fields": [[name, value] for name, value in sorted(pairs)], "notes": []}


# ---------------------------------------------------------------- write transaction

def require_locking() -> None:
    if fcntl is None:
        raise ToolError(7, "locking-unavailable", "the fcntl module is unavailable; writes need it")


def acquire_lock(task: str, wait_seconds: int) -> int:
    """Open the task lock file without following links, take the exclusive lock within the wait
    bound and record owner metadata; return the descriptor whose closing releases the lock."""
    path = os.path.join(task, LOCK_NAME)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as error:
        if os.path.islink(path) or error.errno in (errno.ELOOP, errno.EISDIR):
            raise ToolError(7, "unsafe-lock-path", f"{LOCK_NAME} must be a regular file") from None
        raise ToolError(7, "io-error", f"cannot open {LOCK_NAME}: {error.strerror}") from None
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ToolError(7, "unsafe-lock-path", f"{LOCK_NAME} must be a regular file")
        deadline = time.monotonic() + wait_seconds
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as error:
                if error.errno not in (errno.EAGAIN, errno.EWOULDBLOCK, errno.EACCES):
                    raise ToolError(7, "io-error",
                                    f"cannot lock {LOCK_NAME}: {error.strerror}") from None
                if time.monotonic() >= deadline:
                    raise ToolError(5, "lock-busy",
                                    f"{LOCK_NAME} is held by another writer") from None
                time.sleep(LOCK_RETRY_SECONDS)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def write_lock_owner(descriptor: int, owner_token: str) -> None:
    metadata = {"owner_token": owner_token, "pid": os.getpid(), "host": socket.gethostname(),
                "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    try:
        os.ftruncate(descriptor, 0)
        os.lseek(descriptor, 0, os.SEEK_SET)
        os.write(descriptor, (json.dumps(metadata) + "\n").encode("utf-8"))
    except OSError as error:
        raise ToolError(7, "io-error", f"cannot write {LOCK_NAME}: {error.strerror}") from None


def remove_own(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def replace_state(paths: TaskPaths, data: bytes, owner_token: str, source: str,
                  identity: tuple[int, int], mode: int, report: dict[str, Any]) -> list[str]:
    """Write the candidate to this process's own temporary file, re-check that state.md is the
    file that was read, rename over it and sync the directory; return write warnings."""
    temporary = os.path.join(paths.task, f".state.md.{owner_token}.tmp")
    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
             | getattr(os, "O_CLOEXEC", 0))
    created = False
    try:
        descriptor = os.open(temporary, flags, mode)
        created = True
        try:
            os.fchmod(descriptor, mode)
            view = memoryview(data)
            while view:
                view = view[os.write(descriptor, view):]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as error:
        if created:
            remove_own(temporary)
        raise ToolError(7, "io-error", f"cannot write the temporary file: {error.strerror}") from None
    try:
        current, opened = read_state_file(paths.state)
        info = os.lstat(paths.state)
    except (ToolError, OSError):
        remove_own(temporary)
        raise ToolError(4, "state-file-changed", "state.md changed during the write") from None
    if ((opened.st_dev, opened.st_ino) != identity or (info.st_dev, info.st_ino) != identity
            or revision(current) != source):
        remove_own(temporary)
        report["result_revision"] = revision(current)
        raise ToolError(4, "state-file-changed", "state.md changed during the write")
    try:
        os.replace(temporary, paths.state)
    except OSError as error:
        remove_own(temporary)
        raise ToolError(7, "io-error", f"cannot replace state.md: {error.strerror}") from None
    try:
        directory = os.open(paths.task, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError:
        return ["directory-sync-failed"]
    return []


def write_target(document: Document, block_id: str) -> Block:
    """Locate the block a write may change; refuse a missing, duplicated or malformed block, a
    malformed receipts line, an unrecognized prefix or an unknown header field with exit 3."""
    matches = [block for block in document.blocks if block.block_id == block_id]
    if not matches:
        raise ToolError(3, "block-missing", f"block {block_id} not found")
    if len(matches) > 1:
        raise ToolError(3, "block-duplicate", f"block {block_id} occurs {len(matches)} times",
                        matches[1].start + 1)
    block = matches[0]
    if block.malformed:
        line, reason = block.malformed[0]
        raise ToolError(3, "malformed-block", f"block {block_id}: {reason}", line)
    receipts_line = receipts_problem(block)
    if receipts_line is not None:
        raise ToolError(3, "malformed-receipts",
                        f"block {block_id}: state_receipts needs 1-{MAX_RECEIPTS} well-formed "
                        "entries with unique operation ids", receipts_line)
    if block.prefix is not None and block.prefix != COMPOSITE_PREFIX:
        raise ToolError(3, "unrecognized-prefix", f"block {block_id} has prefix {block.prefix}",
                        block.start + 1)
    unknown = [name for name, _ in block.header_fields if name not in KNOWN_HEADER_FIELDS[block.kind]]
    if unknown:
        raise ToolError(3, "unknown-header-field",
                        f"block {block_id} has unknown header field {unknown[0]}", block.start + 1)
    return block


# ---------------------------------------------------------------- commands

def load_document(options: dict[str, list[str]], report: dict[str, Any],
                  report_version: bool) -> tuple[Document, list[str]]:
    """Resolve and read state.md for a read command, filling task, stale files, revision and,
    when asked, contract_version; return the parsed document and the version warnings."""
    paths = resolve_paths(options["--root"][0], options["--task"][0])
    report["task"] = paths.relative_task
    report["stale_temp_files"] = stale_temp_files(paths.task)
    data = read_state(paths.state)
    report["source_revision"] = revision(data)
    text = decode_state(data)
    lines = split_lines(text)
    version = task_contract_version(lines, fence_flags(lines))
    if report_version:
        report["contract_version"] = version[0] if version else None
    warnings: list[str] = []
    if not contract_version_supported(version[1] if version else None):
        warnings.append("unsupported-contract-version")
    return parse_document(text), warnings


def command_get(options: dict[str, list[str]], report: dict[str, Any]) -> int:
    """Fill the report for get; raise ToolError for a refusal of the whole read."""
    document, warnings = load_document(options, report, report_version=True)
    problems = structure_problems(document.blocks)
    field_name = options.get("--field", [None])[0]
    target = options.get("--block", [None])[0]
    if target is None:
        if problems:
            report["warnings"] = warnings
            report["errors"] = [error.as_error() for _, error in problems]
            return 3
        selected = document.blocks
    else:
        selected = [block for block in document.blocks if block.block_id == target]
        if not selected:
            raise ToolError(3, "block-missing", f"block {target} not found")
        own = [error for block_id, error in problems if block_id == target]
        if own:
            report["warnings"] = warnings
            report["errors"] = [error.as_error() for error in own]
            return 3
        warnings.extend(error.code for block_id, error in problems if block_id != target)
    for block in selected:
        warnings.extend(block_warnings(block))
    report["warnings"] = unique(warnings)
    report["blocks"] = [describe_block(block, field_name) for block in selected]
    report["result"] = "read"
    return 0


def command_validate(options: dict[str, list[str]], report: dict[str, Any]) -> int:
    """Check structure and static invariants of every block, or of the --block one only.

    Exit 3 when any structure error exists, otherwise 6 when any invariant error exists,
    otherwise 0; every error found is listed.
    """
    document, warnings = load_document(options, report, report_version=False)
    problems = structure_problems(document.blocks)
    target = options.get("--block", [None])[0]
    if target is None:
        selected = document.blocks
        structure = [error for _, error in problems]
    else:
        selected = [block for block in document.blocks if block.block_id == target]
        if not selected:
            raise ToolError(3, "block-missing", f"block {target} not found")
        structure = [error for block_id, error in problems if block_id == target]
    invariants: list[ToolError] = []
    for block in selected:
        receipts_line = receipts_problem(block)
        if receipts_line is not None:
            structure.append(ToolError(3, "malformed-receipts",
                                       f"block {block.block_id}: state_receipts needs 1-"
                                       f"{MAX_RECEIPTS} well-formed entries with unique "
                                       "operation ids", receipts_line))
        invariants.extend(invariant_errors(block))
        warnings.extend(advisory_warnings(block))
    report["warnings"] = unique(warnings)
    report["errors"] = [error.as_error() for error in structure + invariants]
    if structure:
        return 3
    if invariants:
        return 6
    report["result"] = "valid"
    return 0


def command_set(options: dict[str, list[str]], report: dict[str, Any]) -> int:
    """Change the named fields of one block under the task lock in one atomic replace."""
    require_locking()
    pairs = field_pairs(options)
    paths = resolve_paths(options["--root"][0], options["--task"][0])
    report["task"] = paths.relative_task
    report["stale_temp_files"] = stale_temp_files(paths.task)
    read_state_file(paths.state)  # Refuse a missing or unsafe state.md before taking the lock.
    owner_token = secrets.token_hex(16)
    descriptor = acquire_lock(paths.task, lock_wait_seconds(options))
    try:
        write_lock_owner(descriptor, owner_token)
        data, opened = read_state_file(paths.state)
        source = revision(data)
        report["source_revision"] = source
        text = decode_state(data)
        lines = split_lines(text)
        version = task_contract_version(lines, fence_flags(lines))
        if not contract_version_supported(version[1] if version else None):
            raise ToolError(3, "unsupported-contract-version",
                            "the task records a contract version this tool does not support")
        document = parse_document(text)
        block_id = options["--block"][0]
        matches = [block for block in document.blocks if block.block_id == block_id]
        if matches:
            report["block_kind"] = matches[0].kind
        block = write_target(document, block_id)
        if options["--expected-revision"][0] != source:
            raise ToolError(4, "revision-conflict",
                            "state.md changed since the expected revision was read")
        check_field_changes(block, pairs)
        changes = changed_pairs(block, pairs)
        if not changes:
            report["result"] = "unchanged"
            return 0
        receipt = f"{options['--operation-id'][0]}#{input_digest('set', block_id, set_inputs(pairs))}"
        candidate, changed = build_candidate(document, block, changes, receipt)
        verify_candidate(document, block, candidate, changes)
        candidate_bytes = candidate.encode("utf-8")
        report["warnings"] = replace_state(paths, candidate_bytes, owner_token, source,
                                           (opened.st_dev, opened.st_ino),
                                           stat.S_IMODE(opened.st_mode), report)
        report["result_revision"] = revision(candidate_bytes)
        report["changed_fields"] = changed
        report["result"] = "applied"
        return 0
    finally:
        os.close(descriptor)


HANDLERS = {"get": command_get, "validate": command_validate, "set": command_set}


def emit(report: dict[str, Any], exit_code: int) -> None:
    sys.stdout.write(json.dumps(report) + "\n")
    for error in report["errors"]:
        location = f" (line {error['line']})" if "line" in error else ""
        sys.stderr.write(f"state-tool: {error['code']}: {error['message']}{location}\n")
    for warning in report["warnings"]:
        sys.stderr.write(f"state-tool: warning: {warning}\n")
    if report["command"] in WRITE_COMMANDS and exit_code in NO_BYPASS_EXITS:
        sys.stderr.write(f"state-tool: {NO_BYPASS}\n")


def main(argv: list[str]) -> int:
    report: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "command": None,
                              "result": "rejected", "task": None, "source_revision": None,
                              "errors": [], "warnings": [], "stale_temp_files": []}
    try:
        if argv and argv[0] in COMMANDS:
            report["command"] = argv[0]
        if report["command"] == "get":
            report["contract_version"] = None
        if report["command"] in WRITE_COMMANDS:
            report.update({"operation_id": None, "block_id": None, "block_kind": None,
                           "result_revision": None, "changed_fields": []})
        command, options = split_arguments(argv)
        if command in WRITE_COMMANDS:
            note_write_identity(options, report)
        check_arguments(command, options)
        exit_code = HANDLERS[command](options, report)
    except ToolError as error:
        report["errors"] = [error.as_error()]
        exit_code = error.exit_code
    except Exception as error:  # Any unexpected failure still yields one JSON object.
        report["errors"] = [{"code": "internal-error", "message": f"{type(error).__name__}: {error}"}]
        exit_code = 1
    if exit_code != 0:
        report["result"] = REFUSED_RESULT.get(report["command"], "rejected")
        report.pop("blocks", None)
        if report["command"] in WRITE_COMMANDS:
            report["changed_fields"] = []
    if report["command"] in WRITE_COMMANDS and report["result_revision"] is None:
        report["result_revision"] = report["source_revision"]
    emit(report, exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
