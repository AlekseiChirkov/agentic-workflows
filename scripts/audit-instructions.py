#!/usr/bin/env python3
"""Read-only audit tool for the instruction files of this repository.

The audited set is every non-directory entry under rules/ and workflows/ (primary) and
under harness/ plus templates/codex-global-AGENTS.md (adapter). Readers are the other
classified files of the root that may refer to audited files.

Usage:
  python3 -I scripts/audit-instructions.py extract [--root DIR] --out FILE
      Write the inventory (audited files with their text structure, readers, git state
      and a digest over both lists) as canonical JSON to FILE. FILE is written to a
      temporary file in its own directory and moved into place.
      --root defaults to the parent of the scripts/ directory that holds this file.

Exit codes:
  0  the inventory was written
  2  usage error, root-invalid (no rules/ or workflows/ directory), root-unreadable,
     out-unwritable, or an interpreter older than Python 3.11; one `ERROR:` line on
     standard error

Read-only contract: the tool writes nothing but the --out file. It never follows a
symbolic link, never executes or imports repository content and opens no network
connection. The only programs it runs are the git read commands
`rev-parse --verify HEAD`, `ls-files -z` and
`status --porcelain=v1 -z --untracked-files=all`, with LC_ALL=C, GIT_OPTIONAL_LOCKS=0,
no pager and no inherited GIT_* variables; a missing or failing git yields null or
`unknown` values, never an error. Standard library only.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    sys.stderr.write("ERROR: Python 3.11 or newer is required\n")
    raise SystemExit(2)

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

SCHEMA_VERSION = 1
METHOD_VERSION = "08-extract-1"

PRIMARY_DIRECTORIES = ("rules", "workflows")
ADAPTER_DIRECTORIES = ("harness",)
ADAPTER_FILES = ("templates/codex-global-AGENTS.md",)
SKIPPED_DIRECTORIES = frozenset({".git", "logs", "output", "__pycache__"})
SKIPPED_SUFFIXES = (".pyc",)
OWN_SCRIPTS = frozenset({"scripts/audit-instructions.py", "scripts/check-audit-instructions.py"})
AUDIT_OUTPUT_RE = re.compile(
    r"docs/audits/[^/]*-rules-workflows-audit\.(md|inventory\.json|assessment\.json)")

# Reader classes in precedence order: the first class with a matching pattern wins.
READER_CLASS_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = tuple(
    (name, tuple(re.compile(pattern) for pattern in patterns)) for name, patterns in (
        ("frozen", (r"tests/fixtures/validator-runtime/.+",)),
        ("active", (r"CLAUDE\.md", r"README\.md", r"(principles|templates|hooks|scripts|tests)/.+",
                    r"docs/[^/]+", r"\.ai/(principles|context)/[^/]+\.md",
                    r"\.ai/memory/architecture\.md")),
        ("planning", (r"\.ai/README\.md", r"\.ai/memory/state\.md", r"\.ai/specs/[^/]+",
                      r"\.ai/tasks/todo/.+")),
        ("history", (r"\.ai/adr/.+", r"\.ai/specs/completed/.+", r"\.ai/tasks/completed/.+",
                     r"\.ai/memory/progress\.md", r"docs/[^/]+/.+")),
    )
)

CONTROL_CHARACTER_RE = re.compile("[\u001c-\u001f]")
FRONT_MATTER_DELIMITER = "---"
FRONT_MATTER_KEY_RE = re.compile(r"([a-z_]+):( .*)?")
FENCE_OPEN_RE = re.compile(r" *(`{3,}|~{3,})")
HEADING_RE = re.compile(r"(#{1,6}) ")
INVOCATION_PREFIX = "Invocation: "
PREAMBLE_HEADING = "(preamble)"

ZONE_FRONT_MATTER = "front-matter"
ZONE_FENCE = "fence"
ZONE_BODY = "body"

GIT_READ_ENVIRONMENT = {"LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0", "GIT_PAGER": "cat",
                        "PAGER": "cat"}

JsonObject = dict[str, object]


class UsageError(Exception):
    """A command line that the argument parser rejects."""


class ToolError(Exception):
    """A failure reported as one `ERROR: <code>: <message>` line with exit 2."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")


# ---------------------------------------------------------------------------
# Text model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Line:
    """One LF-terminated line; `text` drops the LF and one trailing CR for matching."""

    number: int
    raw: str
    text: str
    zone: str


@dataclass(frozen=True)
class Heading:
    """An ATX heading outside fences and front matter."""

    line: int
    level: int
    text: str


@dataclass(frozen=True)
class TextModel:
    """The line, front-matter, fence and heading structure of one Markdown text."""

    lines: tuple[Line, ...]
    front_matter: JsonObject
    headings: tuple[Heading, ...]


def raw_lines(data: bytes) -> list[bytes]:
    """Split bytes into LF-terminated lines; a final line without LF still counts."""
    pieces = data.split(b"\n")
    lines = [piece + b"\n" for piece in pieces[:-1]]
    if pieces[-1]:
        lines.append(pieces[-1])
    return lines


def matching_text(raw: str) -> str:
    text = raw[:-1] if raw.endswith("\n") else raw
    return text[:-1] if text.endswith("\r") else text


def empty_front_matter(status: str) -> JsonObject:
    return {"status": status, "keys": [], "trigger": None, "description": None,
            "continuation_lines": 0}


def summarize_front_matter(texts: Sequence[str]) -> JsonObject:
    summary = empty_front_matter("present")
    keys: list[str] = []
    continuation_lines = 0
    for text in texts:
        match = FRONT_MATTER_KEY_RE.fullmatch(text)
        if match is None:
            continuation_lines += 1 if text.strip() else 0
            continue
        key = match.group(1)
        keys.append(key)
        if key in ("trigger", "description") and summary[key] is None:
            summary[key] = (match.group(2) or " ")[1:].rstrip()
    summary["keys"] = keys
    summary["continuation_lines"] = continuation_lines
    return summary


def front_matter_extent(texts: Sequence[str]) -> tuple[JsonObject, int]:
    """Return the front-matter summary and the number of lines it occupies."""
    if not texts or texts[0] != FRONT_MATTER_DELIMITER:
        return empty_front_matter("absent"), 0
    for index in range(1, len(texts)):
        if texts[index] == FRONT_MATTER_DELIMITER:
            return summarize_front_matter(texts[1:index]), index + 1
    return empty_front_matter("unclosed"), 0


def closes_fence(text: str, fence: str) -> bool:
    stripped = text.lstrip(" ")
    run = len(stripped) - len(stripped.lstrip(fence[0]))
    return run >= len(fence) and not stripped[run:].strip()


def line_zones(texts: Sequence[str], body_start: int) -> list[str]:
    """Mark every line as front matter, fence (opening and closing lines included) or body."""
    zones = [ZONE_FRONT_MATTER] * body_start
    fence: str | None = None
    for text in texts[body_start:]:
        if fence is not None:
            zones.append(ZONE_FENCE)
            fence = None if closes_fence(text, fence) else fence
            continue
        opening = FENCE_OPEN_RE.match(text)
        if opening is not None:
            fence = opening.group(1)
            zones.append(ZONE_FENCE)
        else:
            zones.append(ZONE_BODY)
    return zones


def find_headings(lines: Sequence[Line]) -> tuple[Heading, ...]:
    headings = []
    for line in lines:
        match = HEADING_RE.match(line.text) if line.zone == ZONE_BODY else None
        if match is not None:
            headings.append(Heading(line.number, len(match.group(1)), line.text.rstrip()))
    return tuple(headings)


def build_text_model(data: bytes) -> TextModel:
    raws = [piece.decode("utf-8") for piece in raw_lines(data)]
    texts = [matching_text(raw) for raw in raws]
    front_matter, body_start = front_matter_extent(texts)
    zones = line_zones(texts, body_start)
    lines = tuple(Line(index + 1, raw, text, zone)
                  for index, (raw, text, zone) in enumerate(zip(raws, texts, zones)))
    return TextModel(lines, front_matter, find_headings(lines))


def section_entry(heading: str, lines: Sequence[Line]) -> JsonObject:
    text = "".join(line.raw for line in lines)
    return {"heading": heading, "line": lines[0].number, "words": len(text.split()),
            "bytes": len(text.encode("utf-8"))}


def sections(model: TextModel) -> list[JsonObject]:
    """Partition the file at its level-2 headings; leading lines form the preamble."""
    starts = [heading for heading in model.headings if heading.level == 2]
    boundaries = [(PREAMBLE_HEADING, 1)] + [(heading.text, heading.line) for heading in starts]
    entries = []
    for index, (title, first) in enumerate(boundaries):
        last = boundaries[index + 1][1] - 1 if index + 1 < len(boundaries) else len(model.lines)
        if last >= first:
            entries.append(section_entry(title, model.lines[first - 1:last]))
    return entries


def invocation_line_count(model: TextModel) -> int:
    return sum(1 for line in model.lines
               if line.zone != ZONE_FENCE and line.text.startswith(INVOCATION_PREFIX))


# ---------------------------------------------------------------------------
# File system
# ---------------------------------------------------------------------------

def entry_kind(path: Path) -> str:
    mode = os.lstat(path).st_mode
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISLNK(mode):
        return "symlink"
    return "other"


def is_real_directory(path: Path) -> bool:
    try:
        return stat.S_ISDIR(os.lstat(path).st_mode)
    except (FileNotFoundError, NotADirectoryError):
        return False


def read_regular_file(path: Path) -> bytes:
    """Read a regular file without following a symbolic link or blocking on a special file."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ToolError("root-unreadable", "an entry stopped being a regular file")
        return handle.read()


def entries_below(root: Path, top: str) -> Iterator[str]:
    """Yield every non-directory entry below `top`, recursing into real directories only."""
    with os.scandir(root / top) as iterator:
        children = sorted(iterator, key=lambda child: child.name)
    for child in children:
        relative = f"{top}/{child.name}"
        if child.is_dir(follow_symlinks=False):
            yield from entries_below(root, relative)
        else:
            yield relative


def audited_paths(root: Path) -> dict[str, str]:
    """Map every audited path found on disk to its set."""
    found: dict[str, str] = {}
    for set_name, directories in (("primary", PRIMARY_DIRECTORIES),
                                  ("adapter", ADAPTER_DIRECTORIES)):
        for directory in directories:
            if is_real_directory(root / directory):
                found.update((path, set_name) for path in entries_below(root, directory))
    for path in ADAPTER_FILES:
        if os.path.lexists(root / path) and not is_real_directory(root / path):
            found[path] = "adapter"
    return found


def audited_set_of(path: str) -> str | None:
    """The set a path belongs to by its location, whether or not it exists."""
    top = path.split("/", 1)[0]
    if "/" in path and top in PRIMARY_DIRECTORIES:
        return "primary"
    if ("/" in path and top in ADAPTER_DIRECTORIES) or path in ADAPTER_FILES:
        return "adapter"
    return None


def reader_class_of(path: str) -> str | None:
    """The reader class of a path after the skip rules and exclusions, or None."""
    directories = path.split("/")[:-1]
    if any(name in SKIPPED_DIRECTORIES for name in directories):
        return None
    if path.endswith(SKIPPED_SUFFIXES) or path in OWN_SCRIPTS:
        return None
    if AUDIT_OUTPUT_RE.fullmatch(path) or audited_set_of(path) is not None:
        return None
    for name, patterns in READER_CLASS_PATTERNS:
        if any(pattern.fullmatch(path) for pattern in patterns):
            return name
    return None


def reader_paths(root: Path) -> dict[str, str]:
    """Map every regular reader file to its class."""
    found: dict[str, str] = {}
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if name not in SKIPPED_DIRECTORIES]
        base = Path(directory).relative_to(root).as_posix()
        for name in filenames:
            relative = name if base == "." else f"{base}/{name}"
            reader_class = reader_class_of(relative)
            if reader_class is not None and entry_kind(root / relative) == "file":
                found[relative] = reader_class
    return found


# ---------------------------------------------------------------------------
# Entries
# ---------------------------------------------------------------------------

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_strict(data: bytes) -> str | None:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def encoding_of(data: bytes) -> tuple[str, str | None]:
    """Return the encoding verdict and the text when it is word-countable."""
    text = decode_strict(data)
    if text is None:
        return "invalid", None
    if CONTROL_CHARACTER_RE.search(text):
        return "control-character", None
    return "utf-8", text


def markdown_fields(data: bytes) -> JsonObject:
    model = build_text_model(data)
    return {"front_matter": model.front_matter,
            "invocation_lines": invocation_line_count(model),
            "sections": sections(model)}


def content_fields(path: str, data: bytes) -> JsonObject:
    encoding, text = encoding_of(data)
    fields: JsonObject = {"sha256": sha256_hex(data), "bytes": len(data),
                          "lines": len(raw_lines(data)), "encoding": encoding,
                          "words": None if text is None else len(text.split()),
                          "front_matter": None, "invocation_lines": None, "sections": []}
    if text is not None and path.endswith(".md"):
        fields.update(markdown_fields(data))
    return fields


def null_content_fields() -> JsonObject:
    return {"sha256": None, "bytes": None, "lines": None, "encoding": None, "words": None,
            "front_matter": None, "invocation_lines": None, "sections": []}


def file_entry(root: Path, path: str, set_name: str, tracked: frozenset[str] | None
               ) -> JsonObject:
    kind = entry_kind(root / path)
    entry: JsonObject = {"path": path, "set": set_name, "entry": kind,
                         "tracked": None if tracked is None else path in tracked}
    if kind == "file":
        entry.update(content_fields(path, read_regular_file(root / path)))
    else:
        entry.update(null_content_fields())
    return entry


def reader_entry(root: Path, path: str, reader_class: str) -> JsonObject:
    data = read_regular_file(root / path)
    return {"path": path, "class": reader_class, "sha256": sha256_hex(data),
            "lines": len(raw_lines(data)), "decoded": decode_strict(data) is not None}


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------

def git_environment() -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("GIT_")}
    environment.update(GIT_READ_ENVIRONMENT)
    return environment


def run_git(root: Path, *arguments: str) -> bytes | None:
    """Run one git read command; None when git is missing or the command fails."""
    try:
        result = subprocess.run(["git", "--no-pager", "-C", str(root), *arguments],
                                stdin=subprocess.DEVNULL, capture_output=True,
                                env=git_environment(), check=False)
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def source_revision(root: Path) -> str | None:
    output = run_git(root, "rev-parse", "--verify", "HEAD")
    return None if output is None else output.decode("ascii", "replace").strip() or None


def tracked_paths(root: Path) -> frozenset[str] | None:
    output = run_git(root, "ls-files", "-z")
    if output is None:
        return None
    return frozenset(os.fsdecode(item) for item in output.split(b"\0") if item)


def status_paths(output: bytes) -> list[str]:
    """Paths of porcelain v1 -z records; a rename or copy also names its original path."""
    records = output.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if len(record) < 4:
            continue
        paths.append(os.fsdecode(record[3:]))
        if b"R" in record[:2] or b"C" in record[:2]:
            if index < len(records) and records[index]:
                paths.append(os.fsdecode(records[index]))
            index += 1
    return paths


def counts_for_worktree(root: Path, path: str, listed: frozenset[str]) -> bool:
    """Listed audited and reader paths count; a path gone from disk counts by its location."""
    if path in listed:
        return True
    if os.path.lexists(root / path):
        return False
    return audited_set_of(path) is not None or reader_class_of(path) is not None


def worktree_state(root: Path, listed: frozenset[str]) -> JsonObject:
    output = run_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if output is None:
        return {"state": "unknown", "paths": []}
    paths = sorted({path for path in status_paths(output)
                    if counts_for_worktree(root, path, listed)})
    return {"state": "dirty" if paths else "clean", "paths": paths}


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

def inventory_digest(files: Sequence[JsonObject], readers: Sequence[JsonObject]) -> str:
    rows = [(str(entry["path"]), str(entry["set"]), entry["sha256"]) for entry in files]
    rows += [(str(entry["path"]), str(entry["class"]), entry["sha256"]) for entry in readers]
    text = "".join(f"{path}\t{label}\t{digest or '-'}\n" for path, label, digest in sorted(rows))
    return sha256_hex(text.encode("utf-8"))


def validate_root(root: Path) -> None:
    missing = [name for name in PRIMARY_DIRECTORIES if not is_real_directory(root / name)]
    if missing:
        named = " or ".join(f"{name}/" for name in missing)
        raise ToolError("root-invalid", f"the root has no {named} directory")


def build_inventory(root: Path) -> JsonObject:
    tracked = tracked_paths(root)
    audited = audited_paths(root)
    readers_found = reader_paths(root)
    files = [file_entry(root, path, audited[path], tracked) for path in sorted(audited)]
    readers = [reader_entry(root, path, readers_found[path]) for path in sorted(readers_found)]
    listed = frozenset(audited) | frozenset(readers_found)
    return {
        "schema_version": SCHEMA_VERSION,
        "method_version": METHOD_VERSION,
        "source_revision": source_revision(root),
        "worktree": worktree_state(root, listed),
        "inventory_digest": inventory_digest(files, readers),
        "files": files,
        "readers": readers,
        "edges": [],
        "repeat_loads": [],
        "full_output": [],
        "harness_names": [],
        "legacy_mentions": [],
        "duplicate_clusters": [],
    }


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def current_umask() -> int:
    mask = os.umask(0)
    os.umask(mask)
    return mask


def write_atomically(target: Path, text: str) -> None:
    """Write to a temporary file beside the target and move it into place."""
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp",
                                                 dir=target.parent)
    except OSError as error:
        raise ToolError("out-unwritable",
                        f"cannot write the --out file ({error.strerror})") from error
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            os.fchmod(handle.fileno(), 0o666 & ~current_umask())
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except OSError as error:
        with suppress(FileNotFoundError):
            os.unlink(temporary)
        raise ToolError("out-unwritable",
                        f"cannot write the --out file ({error.strerror})") from error


def run_extract(root: Path, out: Path) -> int:
    validate_root(root)
    try:
        inventory = build_inventory(root)
    except OSError as error:
        raise ToolError("root-unreadable", f"cannot read the root ({error.strerror})") from error
    write_atomically(out, canonical_json(inventory))
    return 0


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

class UsageParser(argparse.ArgumentParser):
    """An argument parser that reports errors as one line instead of usage text."""

    def error(self, message: str) -> NoReturn:
        raise UsageError(message)


def default_root() -> Path:
    return Path(__file__).resolve().parent.parent


def argument_parser() -> UsageParser:
    parser = UsageParser(prog="audit-instructions.py",
                         description="Read-only audit tool for instruction files.")
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract", help="write the inventory")
    extract.add_argument("--root", type=Path, default=None)
    extract.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: Sequence[str]) -> int:
    try:
        arguments = argument_parser().parse_args(list(argv))
        root = arguments.root if arguments.root is not None else default_root()
        return run_extract(root, arguments.out)
    except UsageError as error:
        sys.stderr.write(f"ERROR: usage: {error}\n")
    except ToolError as error:
        sys.stderr.write(f"ERROR: {error}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
