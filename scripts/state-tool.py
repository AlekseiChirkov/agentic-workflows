#!/usr/bin/env python3
"""Read the subtask-progress section of one task state.md through a structural parser.

Usage:
  python3 scripts/state-tool.py get --root R --task T [--block ID] [--field NAME]

Contract: stdout carries exactly one JSON object (schema_version 1); diagnostics go to
stderr only. Read commands create, modify and delete no file. Python 3.11 or newer and
the standard library only; no input value is ever passed to a shell or interpreter.

Exit codes: 0 read; 1 internal-error; 2 invalid invocation (invalid-arguments,
unknown-command, path-outside-root); 3 structure refused (state-missing, section-missing,
section-duplicate, block-missing, block-duplicate, malformed-block, unsupported-encoding);
7 file system or runtime (io-error, unsafe-state-file, python-too-old).
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
import hashlib
import json
import os
import re
import stat
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

# Per command: options taking one value, repeatable options and required options.
COMMANDS: dict[str, dict[str, frozenset[str]]] = {
    "get": {"single": frozenset({"--root", "--task", "--block", "--field"}),
            "repeatable": frozenset(),
            "required": frozenset({"--root", "--task"})},
}


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

def parse_arguments(argv: list[str]) -> tuple[str, dict[str, list[str]]]:
    """Split argv into a known command and its options; refuse anything else."""
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
    missing = sorted(spec["required"] - options.keys())
    if missing:
        raise ToolError(2, "invalid-arguments", "missing required option: " + ", ".join(missing))
    for block_id in options.get("--block", []):
        if not BLOCK_ID.fullmatch(block_id):
            raise ToolError(2, "invalid-arguments", f"invalid block id: {block_id}")
    for name in options.get("--field", []):
        if not name:
            raise ToolError(2, "invalid-arguments", "field name must not be empty")
    return command, options


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
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ToolError(7, "unsafe-state-file", "state.md must be a regular file")
        return handle.read()


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


def fence_flags(lines: list[str]) -> list[bool]:
    """Mark every line that opens, lies inside or closes a fenced code block."""
    flags: list[bool] = []
    marker: str | None = None
    for line in lines:
        text = content(line)
        if marker is None:
            opened = FENCE_OPEN.match(text)
            if opened:
                marker = opened.group(1)
            flags.append(opened is not None)
            continue
        flags.append(True)
        if re.match(r" {0,3}" + re.escape(marker), text):
            marker = None
    return flags


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


def parse_blocks(lines: list[str], fenced: list[bool], start: int, end: int) -> list[Block]:
    """Parse the section body into blocks; lines outside blocks are foreign and kept as is."""
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
        if header is not None:
            close(index)
            current = header
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
        known = KNOWN_FIELDS[block.kind]
        seen: set[str] = set()
        for item in block.groups:
            if item.name in known and item.name not in REPEATABLE_FIELDS and item.name in seen:
                block.malformed.append((item.start + 1, f"repeated field {item.name}"))
            seen.add(item.name)
    return blocks


def parse_document(text: str) -> Document:
    lines = split_lines(text)
    fenced = fence_flags(lines)
    start, end = locate_section(lines, fenced)
    return Document(lines, fenced, start, end, parse_blocks(lines, fenced, start, end))


# ---------------------------------------------------------------- block reporting

def receipts_problem(block: Block) -> bool:
    """True when a state_receipts line breaks the 1-20 unique well-formed entry rule."""
    for item in (group for group in block.groups if group.name == "state_receipts"):
        entries = item.value.split(", ") if item.value else []
        if item.continuation or not 1 <= len(entries) <= MAX_RECEIPTS:
            return True
        identifiers = []
        for entry in entries:
            match = RECEIPT_ENTRY.fullmatch(entry)
            if match is None:
                return True
            identifiers.append(match.group(1))
        if len(set(identifiers)) != len(identifiers):
            return True
    return False


def block_warnings(block: Block) -> list[str]:
    warnings = []
    if block.prefix is not None and block.prefix != COMPOSITE_PREFIX:
        warnings.append("unrecognized-prefix")
    known_header = KNOWN_HEADER_FIELDS[block.kind]
    if any(name not in known_header for name, _ in block.header_fields):
        warnings.append("unknown-header-field")
    names = {group.name for group in block.groups}
    if any(name not in names for name in REQUIRED_FIELDS[block.kind]):
        warnings.append("required-field-missing")
    if receipts_problem(block):
        warnings.append("malformed-receipts")
    return warnings


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


# ---------------------------------------------------------------- commands

def command_get(options: dict[str, list[str]], report: dict[str, Any]) -> int:
    """Fill the report for get; raise ToolError for a refusal of the whole read."""
    paths = resolve_paths(options["--root"][0], options["--task"][0])
    report["task"] = paths.relative_task
    report["stale_temp_files"] = stale_temp_files(paths.task)
    data = read_state(paths.state)
    report["source_revision"] = revision(data)
    text = decode_state(data)
    lines = split_lines(text)
    version = task_contract_version(lines, fence_flags(lines))
    report["contract_version"] = version[0] if version else None
    warnings: list[str] = []
    if not contract_version_supported(version[1] if version else None):
        warnings.append("unsupported-contract-version")
    document = parse_document(text)
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


HANDLERS = {"get": command_get}


def emit(report: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(report) + "\n")
    for error in report["errors"]:
        location = f" (line {error['line']})" if "line" in error else ""
        sys.stderr.write(f"state-tool: {error['code']}: {error['message']}{location}\n")
    for warning in report["warnings"]:
        sys.stderr.write(f"state-tool: warning: {warning}\n")


def main(argv: list[str]) -> int:
    report: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "command": None,
                              "result": "rejected", "task": None, "source_revision": None,
                              "errors": [], "warnings": [], "stale_temp_files": []}
    try:
        if argv and argv[0] in COMMANDS:
            report["command"] = argv[0]
        if report["command"] == "get":
            report["contract_version"] = None
        command, options = parse_arguments(argv)
        exit_code = HANDLERS[command](options, report)
    except ToolError as error:
        report["result"] = "rejected"
        report["errors"] = [error.as_error()]
        exit_code = error.exit_code
    except Exception as error:  # Any unexpected failure still yields one JSON object.
        report["result"] = "rejected"
        report["errors"] = [{"code": "internal-error", "message": f"{type(error).__name__}: {error}"}]
        exit_code = 1
    if exit_code != 0:
        report["result"] = "rejected"
        report.pop("blocks", None)
    emit(report)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
