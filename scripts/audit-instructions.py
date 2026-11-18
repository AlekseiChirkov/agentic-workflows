#!/usr/bin/env python3
"""Read-only audit tool for the instruction files of this repository.

The audited set is every non-directory entry under rules/ and workflows/ (primary) and
under harness/ plus templates/codex-global-AGENTS.md (adapter). Readers are the other
classified files of the root that may refer to audited files.

Usage:
  python3 -I scripts/audit-instructions.py extract [--root DIR] --out FILE
      Write the inventory (audited files with their text structure, readers, git state,
      a digest over both lists, and every reference edge from a decoded audited file or
      reader to audited files, with its form, context, status, flags and targets; then
      the candidates: loads repeated by a workflow and a workflow it calls, full-output
      and harness-name lines, legacy-integration mentions and verbatim duplicate text
      units; text copied from audited files writes `/home/<name>/` and `/Users/<name>/`
      as `~/`) as canonical JSON to FILE. FILE is written to a temporary file in its own directory
      and moved into place. `is_defect_edge` is the defect predicate over one edge.
      --root defaults to the parent of the scripts/ directory that holds this file.
  python3 -I scripts/audit-instructions.py verify [--root DIR] --report FILE [--strict]
      Check the inventory and the assessment whose paths replace the `.md` of FILE with
      `.inventory.json` and `.assessment.json`: their schemas, the audited files of the
      root against the inventory (with --strict, a fresh extraction against its bytes),
      the work-tree state, and every per-item rule of the assessment, including the
      migration map, its deviation from the recorded migration defaults, the amendments
      against the single `.ai/specs/09-*.md` file (read as strict UTF-8 without following a
      symbolic link) and the statement coverage of the statement units of
      `## Codebase Reading Rules` and `## Decision Protocol` in rules/phase-discovery.md.
      Then the report FILE itself: its layout (title, the five `##` headings and the
      generated-region markers in order, one review and one acceptance line in their
      grammars), that the reviewed commit exists (`cat-file`), amounts anywhere in it,
      and, when the JSON files meet their schemas, its file-name date and title date
      against run_date, every blocking finding under its blockers heading, and the
      generated region against fresh render output. The report is read as strict UTF-8,
      at most 64 MiB, without following a symbolic link.
      Prints one `<code> <location> <message>` line per violation in string order of
      code and location. A location is `<path>:<line>` (`0` for a whole file) or
      `<json file>#<id, key or key[index]>`, with paths relative to the root.
  python3 -I scripts/audit-instructions.py render [--root DIR] --report FILE [--write]
      Render the generated region of the report from the inventory and the assessment
      named as for verify: both marker lines and the eighteen `###` subsections, written
      to standard output as UTF-8 bytes. The output depends on the two JSON files only.
      With --write, FILE is read as for verify and the lines from its begin marker to its
      end marker are replaced by the region in a temporary file beside it that is moved
      into place, keeping FILE's permission bits; nothing is printed.

Exit codes:
  0  extract: the inventory was written; verify: no diagnostic; render: rendered
  1  verify: at least one diagnostic was printed; render: the inventory or the
     assessment is missing or breaks its schema (its diagnostics are printed, nothing
     is written)
  2  usage error, root-invalid (no rules/ or workflows/ directory), root-unreadable
     (a directory or file that cannot be read, or a file name that is not valid UTF-8),
     out-unwritable, render --write refusals report-unreadable (absent, not a regular
     file, a symbolic link, larger than 64 MiB or not valid UTF-8), report-markers (not
     exactly one begin marker line followed by one end marker line) and
     report-unwritable, or an interpreter older than Python 3.11; one `ERROR:` line on
     standard error, and no --out file or report is written

Read-only contract: the tool writes nothing but the --out file and, under
render --write, the generated region of the report; verify writes nothing. It
never follows a symbolic link of the audited tree, never executes or
imports repository content and opens no network
connection itself. The only programs it runs are the git read commands
`rev-parse --verify HEAD`, `ls-files -z` and
`status --porcelain=v1 -z --untracked-files=all` and, in verify,
`cat-file -e <sha>^{commit}`, with LC_ALL=C, GIT_OPTIONAL_LOCKS=0,
no pager, no inherited GIT_* variables, the file-system monitor disabled and hooks
pointed at an empty location; a missing or failing git yields null or `unknown`
values, never an error. Every git read also runs with lazy fetching disabled
(GIT_NO_LAZY_FETCH, git 2.45 or later) and rename detection off (status.renames,
git 2.18 or later), and reads neither the user's nor the system's attributes file. The
root is taken as the top level of its git work tree, and its `.git` directory or file
locates the repository: when its configuration names the SHA-1 or the SHA-256 object
format, git reads attributes from that format's empty tree instead of the committed and
work-tree .gitattributes files (GIT_ATTR_SOURCE, git 2.41 or later), and every filter
driver that the repository's info/attributes file names, within git's own limits of
2048 bytes a line and 100 MiB a file, is given an empty clean and process program
(GIT_CONFIG_COUNT, git 2.31 or later). With git 2.45 or later and a root that is that
top level, therefore, no attribute-selected clean or process filter of the repository
runs and no object missing from a partial clone is fetched. Each of these settings is
one that an older git ignores rather than rejects, so it still answers, with less
isolation. The cases left open are exactly these: with git older than 2.41 a filter
selected by a .gitattributes file of the tree can still run, and with git older than
2.31 one named by info/attributes; with git older than 2.45 `status` or `cat-file` in a
partial clone can still fetch a missing object from its promisor remote; a filter named
by a submodule's own info/attributes file can run when `status` inspects that
submodule; only the first 1000 names of info/attributes in name order, at most 64 KiB
of names, are blanked; a root without its own `.git` (a directory below the top
level, or a link to one) gets neither the empty attribute source nor the blanked names;
and a repository whose configuration cannot be read or names another object format
gets no empty attribute source. Because the attributes of the tree, the user and the
system do not apply, a file whose stored form differs from its work-tree form through
attributes (text, eol, ident, working-tree-encoding or a filter) can read as changed
when git hashes it again. Below the top level `status` also
reports paths relative to that top level, so such a root yields mismatched work-tree
paths.
Standard library only.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    sys.stderr.write("ERROR: Python 3.11 or newer is required\n")
    raise SystemExit(2)

import argparse
import datetime
import errno
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import unicodedata
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, TextIO, cast

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

# The empty tree of each object format, keyed by the value of extensions.objectFormat.
EMPTY_TREES = {"sha1": "4b825dc642cb6eb9a060e54bf8d69288fbee4904",
               "sha256": "6ef19b41225c5369f1c104d45d8d85efa9b057b53b14b4b9b939dd74decc5321"}
# Every setting below is one that a git too old to know it ignores instead of rejecting,
# so an older git still answers; only the guarantee the setting adds is lost. The
# attribute source (GIT_ATTR_SOURCE) is added per repository, because its empty tree
# depends on the object format.
GIT_READ_ENVIRONMENT = {"LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0", "GIT_PAGER": "cat",
                        "PAGER": "cat", "GIT_NO_LAZY_FETCH": "1", "GIT_ATTR_NOSYSTEM": "1"}
# Configuration that would otherwise let git start a program the repository names, read
# attributes that select a filter driver, or need an object a partial clone lacks.
GIT_INERT_CONFIGURATION = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null",
                           "-c", "core.attributesFile=/dev/null",
                           "-c", "status.renames=false")
# Settings that make a filter driver run nothing, applied to each driver that the
# repository's info/attributes file names, because git reads that file in any case.
BLANK_FILTER_SETTINGS = (("clean", ""), ("process", ""), ("required", "false"))
# git separates attribute tokens by space, tab, CR and LF only.
FILTER_ATTRIBUTE_RE = re.compile(r"(?<![^ \t\r\n])filter=([^ \t\r\n\x00]+)")
# git ignores an attributes line of 2048 bytes or more and an attributes file of 100 MiB
# or more; a line of exactly 2048 bytes is still read here, which only blanks more.
ATTRIBUTE_LINE_LIMIT = 2048
ATTRIBUTE_FILE_LIMIT = 100 * 1024 * 1024
# Bounds on the blanked names that keep the environment of every git read small.
BLANKED_NAME_LIMIT = 1000
BLANKED_BYTES_LIMIT = 64 * 1024
# Bound on the `.git` file, `commondir` and the repository configuration read here.
GIT_METADATA_LIMIT = 1024 * 1024
CONFIG_SECTION_RE = re.compile(r'\[\s*([A-Za-z0-9.-]+)\s*("(?:[^"\\]|\\.)*")?\s*\]')
CONFIG_ENTRY_RE = re.compile(r"([A-Za-z][A-Za-z0-9-]*)\s*(?:=\s*(.*))?")

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
    """True for a directory that is not a link; a permission error propagates."""
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


def sorted_children(root: Path, top: str) -> list[tuple[str, bool]]:
    """The entries directly below `top` in name order, with whether each is a real directory."""
    with os.scandir(root / top) as iterator:
        children = sorted(iterator, key=lambda child: child.name)
    return [(f"{top}/{child.name}", child.is_dir(follow_symlinks=False)) for child in children]


def tree_below(root: Path, top: str) -> Iterator[tuple[str, bool]]:
    """Yield every entry below `top` depth first in name order; links stay unfollowed.

    The walk keeps its own stack, so directory depth is not limited by recursion.
    """
    pending = [iter(sorted_children(root, top))]
    while pending:
        entry = next(pending[-1], None)
        if entry is None:
            pending.pop()
            continue
        yield entry
        if entry[1]:
            pending.append(iter(sorted_children(root, entry[0])))


def audited_paths(root: Path) -> tuple[dict[str, str], frozenset[str]]:
    """Map every audited path found on disk to its set, and list the directories walked."""
    found: dict[str, str] = {}
    directories: set[str] = set()
    for set_name, tops in (("primary", PRIMARY_DIRECTORIES), ("adapter", ADAPTER_DIRECTORIES)):
        for top in tops:
            if not is_real_directory(root / top):
                continue
            directories.add(top)
            for path, is_directory in tree_below(root, top):
                if is_directory:
                    directories.add(path)
                else:
                    found[path] = set_name
    for path in ADAPTER_FILES:
        if os.path.lexists(root / path) and not is_real_directory(root / path):
            found[path] = "adapter"
    return found, frozenset(directories)


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


def raise_walk_error(error: OSError) -> NoReturn:
    raise error


def reader_paths(root: Path) -> dict[str, str]:
    """Map every regular reader file to its class; an unreadable directory is an error."""
    found: dict[str, str] = {}
    for directory, dirnames, filenames in os.walk(root, onerror=raise_walk_error,
                                                  followlinks=False):
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


@dataclass(frozen=True)
class AuditedFile:
    """One audited entry as found on disk; `data` is None unless it is a regular file."""

    path: str
    set_name: str
    kind: str
    data: bytes | None


def read_audited(root: Path, path: str, set_name: str) -> AuditedFile:
    kind = entry_kind(root / path)
    data = read_regular_file(root / path) if kind == "file" else None
    return AuditedFile(path, set_name, kind, data)


def file_entry(audited: AuditedFile, tracked: frozenset[str] | None) -> JsonObject:
    entry: JsonObject = {"path": audited.path, "set": audited.set_name, "entry": audited.kind,
                         "tracked": None if tracked is None else audited.path in tracked}
    if audited.data is not None:
        entry.update(content_fields(audited.path, audited.data))
    else:
        entry.update(null_content_fields())
    return entry


def reader_entry(path: str, reader_class: str, data: bytes) -> JsonObject:
    return {"path": path, "class": reader_class, "sha256": sha256_hex(data),
            "lines": len(raw_lines(data)), "decoded": decode_strict(data) is not None}


def require_utf8_paths(paths: Iterable[str]) -> None:
    """Refuse a file name that cannot be written as a UTF-8 JSON string."""
    for path in sorted(paths):
        try:
            path.encode("utf-8")
        except UnicodeEncodeError:
            raise ToolError("root-unreadable",
                            f"a file name is not valid UTF-8: {path}") from None


# ---------------------------------------------------------------------------
# Reference edges: node names
# ---------------------------------------------------------------------------

RULE_FILE_RE = re.compile(r"rules/([^/]+)\.md")
WORKFLOW_FILE_RE = re.compile(r"workflows/([^/]+)\.md")
GRAMMAR_SOURCE_RE = re.compile(r"(rules|workflows)/[^/]+\.md|harness/[^/]+/always-on\.md")
VALIDATOR_PATH = "scripts/validate-contracts.sh"


@dataclass(frozen=True)
class Outline:
    """The headings of a decoded Markdown file and its line count, for section references."""

    headings: tuple[Heading, ...]
    line_count: int


@dataclass(frozen=True)
class Nodes:
    """The names a reference can point at: stems, audited paths and walked directories."""

    rule_stems: frozenset[str]
    workflow_stems: frozenset[str]
    audited: tuple[str, ...]
    directories: frozenset[str]
    outlines: dict[str, Outline]


def stems_of(pattern: re.Pattern[str], paths: Iterable[str]) -> frozenset[str]:
    return frozenset(match.group(1) for match in map(pattern.fullmatch, paths) if match)


def outline_of(audited: AuditedFile) -> Outline | None:
    """Headings come only from decoded text; other entries have none."""
    if audited.data is None or encoding_of(audited.data)[0] != "utf-8":
        return None
    model = build_text_model(audited.data)
    return Outline(model.headings, len(model.lines))


def build_nodes(audited: Sequence[AuditedFile], directories: frozenset[str]) -> Nodes:
    paths = tuple(sorted(item.path for item in audited))
    rule_stems, workflow_stems = stems_of(RULE_FILE_RE, paths), stems_of(WORKFLOW_FILE_RE, paths)
    candidates = {f"rules/{stem}.md" for stem in rule_stems}
    candidates |= {f"workflows/{stem}.md" for stem in workflow_stems}
    outlines = {item.path: outline for item in audited
                if item.path in candidates and (outline := outline_of(item)) is not None}
    return Nodes(rule_stems, workflow_stems, paths, directories, outlines)


def stem_candidates(nodes: Nodes, stem: str, rules: bool = True, workflows: bool = True
                    ) -> list[str]:
    """The rule and workflow files with this stem, in path order."""
    found = [f"rules/{stem}.md"] if rules and stem in nodes.rule_stems else []
    found += [f"workflows/{stem}.md"] if workflows and stem in nodes.workflow_stems else []
    return found


# ---------------------------------------------------------------------------
# Reference edges: matches
# ---------------------------------------------------------------------------

HeadingStatus = str | None
Targets = tuple[tuple[str, HeadingStatus], ...]


@dataclass(frozen=True)
class Match:
    """One reference found on a line; `grammar_form` marks span forms the migration reads."""

    start: int
    raw: str
    form: str
    status: str
    targets: Targets
    md_suffix: bool = False
    grammar_form: bool = False


@dataclass(frozen=True)
class Verdict:
    """A form matched the text; `match` is None when that form yields no edge."""

    match: Match | None


def plain_targets(paths: Iterable[str]) -> Targets:
    return tuple((path, None) for path in paths)


def candidate_status(candidates: Sequence[str]) -> str:
    return "ambiguous-stem" if len(candidates) > 1 else "resolved"


def glob_pattern(raw: str) -> re.Pattern[str]:
    """A glob whose `*` matches any run of characters other than `/`."""
    return re.compile("".join("[^/]*" if char == "*" else re.escape(char) for char in raw))


def path_reference(nodes: Nodes, start: int, raw: str, grammar_form: bool) -> Match | None:
    """Resolve a repository path or glob; placeholders, directories and templates yield none."""
    if "<" in raw:
        return None
    if "*" in raw:
        pattern = glob_pattern(raw)
        matched = [path for path in nodes.audited if pattern.fullmatch(path)]
        return Match(start, raw, "glob", "resolved" if matched else "glob-empty",
                     plain_targets(matched))
    if raw in nodes.audited:
        return Match(start, raw, "path", "resolved", plain_targets([raw]),
                     grammar_form=grammar_form)
    if raw.rstrip("/") in nodes.directories or raw.startswith("templates/"):
        return None
    return Match(start, raw, "path", "missing-path", (), grammar_form=grammar_form)


# ---------------------------------------------------------------------------
# Reference edges: section references and heading resolution
# ---------------------------------------------------------------------------

SECTION_SEPARATOR = " → "
MARKED_COMPONENT_RE = re.compile(r"#{1,6} .+")
RULE_HEAD_RE = re.compile(r"rule-([^/\s]+)")
PATH_HEAD_RE = re.compile(r"(rules|workflows)/([^/\s]+)\.md")
STEM_HEAD_RE = re.compile(r"([^/\s]+?)(\.md)?")
BARE_HEAD_RE = re.compile(r"[a-z0-9-]+")
MIGRATION_HEAD_RE = re.compile(r"[a-z0-9][a-z0-9-]*(\.md)?")
MIGRATION_COMPONENT_RE = re.compile(r"#{2,3} .+")
UNMARKED_SUFFIXES = (" — ", " (", ":")
HEADING_STATUS_RANK = {"resolved": 0, "resolved-prefix": 1, "heading-unmarked": 2,
                       "missing-heading": 3}

Extent = tuple[int, int, int | None]


def section_candidates(nodes: Nodes, head: str) -> tuple[list[str], bool] | None:
    """Candidates and the `.md` flag for a section-reference head; None for another shape."""
    if match := RULE_HEAD_RE.fullmatch(head):
        return stem_candidates(nodes, match.group(1), workflows=False), False
    if match := PATH_HEAD_RE.fullmatch(head):
        kind_is_rule = match.group(1) == "rules"
        return stem_candidates(nodes, match.group(2), rules=kind_is_rule,
                               workflows=not kind_is_rule), False
    if match := STEM_HEAD_RE.fullmatch(head):
        return stem_candidates(nodes, match.group(1)), match.group(2) is not None
    return None


def headings_in(outline: Outline, extent: Extent) -> list[Heading]:
    first, last, own = extent
    return [heading for heading in outline.headings
            if first <= heading.line <= last and heading.line != own]


def heading_extent(outline: Outline, heading: Heading) -> Extent:
    """From the heading to the line before the next heading of the same or a higher level."""
    for later in outline.headings:
        if later.line > heading.line and later.level <= heading.level:
            return heading.line, later.line - 1, heading.line
    return heading.line, outline.line_count, heading.line


def marked_heading(outline: Outline, extent: Extent, component: str
                   ) -> tuple[Heading | None, str]:
    """An exact heading first, then one that continues with ` — `; first in line order."""
    inside = headings_in(outline, extent)
    for heading in inside:
        if heading.text == component:
            return heading, "resolved"
    for heading in inside:
        if heading.text.startswith(component + " — "):
            return heading, "resolved-prefix"
    return None, "missing-heading"


def unmarked_heading(outline: Outline, extent: Extent, component: str
                     ) -> tuple[Heading | None, str]:
    """A heading of level 2 or deeper whose title is or starts the component's text."""
    prefixes = tuple(component + suffix for suffix in UNMARKED_SUFFIXES)
    for heading in headings_in(outline, extent):
        title = heading.text[heading.level + 1:]
        if heading.level >= 2 and (title == component or title.startswith(prefixes)):
            return heading, "heading-unmarked"
    return None, "missing-heading"


def heading_status(outline: Outline | None, components: Sequence[str]) -> str:
    """The worst component status of one candidate, resolving from the start of the file."""
    if outline is None:
        outline = Outline((), 0)
    extent: Extent = (1, outline.line_count, None)
    worst = "resolved"
    for index, component in enumerate(components):
        marked = MARKED_COMPONENT_RE.fullmatch(component) is not None
        if not marked and index > 0:
            continue
        finder = marked_heading if marked else unmarked_heading
        heading, status = finder(outline, extent, component)
        if heading is None:
            return "missing-heading"
        worst = max(worst, status, key=HEADING_STATUS_RANK.__getitem__)
        extent = heading_extent(outline, heading)
    return worst


def section_reference(nodes: Nodes, start: int, content: str) -> Verdict | None:
    head, *components = content.split(SECTION_SEPARATOR)
    head = head[1:] if head.startswith("/") else head
    shape = section_candidates(nodes, head)
    if shape is None:
        return None
    candidates, md_suffix = shape
    grammar_form = (MIGRATION_HEAD_RE.fullmatch(head) is not None
                    and MIGRATION_COMPONENT_RE.fullmatch(components[0]) is not None)
    if not candidates:
        if BARE_HEAD_RE.fullmatch(head) and MARKED_COMPONENT_RE.fullmatch(components[0]):
            return Verdict(Match(start, content, "section-ref", "missing-target", (),
                                 md_suffix, grammar_form))
        return Verdict(None)
    targets = tuple((path, heading_status(nodes.outlines.get(path), components))
                    for path in candidates)
    status = "ambiguous-stem" if len(candidates) > 1 else str(targets[0][1])
    return Verdict(Match(start, content, "section-ref", status, targets, md_suffix,
                         grammar_form))


# ---------------------------------------------------------------------------
# Reference edges: span grammar
# ---------------------------------------------------------------------------

COMMAND_SPAN_RE = re.compile(r"/([a-z0-9][a-z0-9-]*)(\.md)?( .*)?")
RULE_PREFIX_SPAN_RE = re.compile(r"rule-([a-z0-9-]+)")
NAME_SPAN_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
RULE_WORD_AFTER_RE = re.compile(r" rules?(?![A-Za-z0-9_-])")
PATH_SPAN_RE = re.compile(r"(rules|workflows|harness|templates)/[A-Za-z0-9_./*<>-]+")


@dataclass(frozen=True)
class Span:
    """A single-backtick span: the backtick positions and the text between them."""

    open: int
    close: int
    content: str


def spans_of(text: str) -> list[Span]:
    """Pair backticks in order; a double backtick is two empty spans, a lone one none."""
    ticks = [index for index, char in enumerate(text) if char == "`"]
    return [Span(first, second, text[first + 1:second])
            for first, second in zip(ticks[0::2], ticks[1::2])]


def command_span(nodes: Nodes, span: Span, after: str) -> Verdict | None:
    match = COMMAND_SPAN_RE.fullmatch(span.content)
    if SECTION_SEPARATOR in span.content or match is None:
        return None
    name, start = match.group(1), span.open + 1
    md_suffix = match.group(2) is not None
    if name in nodes.workflow_stems:
        return Verdict(Match(start, span.content, "command", "resolved",
                             plain_targets([f"workflows/{name}.md"]), md_suffix, True))
    return Verdict(Match(start, span.content, "command", "unknown-command", (), md_suffix,
                         True))


def section_span(nodes: Nodes, span: Span, after: str) -> Verdict | None:
    if SECTION_SEPARATOR not in span.content:
        return None
    return section_reference(nodes, span.open + 1, span.content)


def rule_name_span(nodes: Nodes, span: Span, after: str) -> Verdict | None:
    """`rule-<stem>`, or a name followed by the word "rule", which names the rule only."""
    prefixed = RULE_PREFIX_SPAN_RE.fullmatch(span.content)
    if prefixed is not None:
        stem = prefixed.group(1)
    elif NAME_SPAN_RE.fullmatch(span.content) and RULE_WORD_AFTER_RE.match(after):
        stem = span.content
    else:
        return None
    found = stem_candidates(nodes, stem, workflows=False)
    return Verdict(Match(span.open + 1, span.content, "rule-name",
                         "resolved" if found else "missing-target", plain_targets(found),
                         grammar_form=True))


def path_span(nodes: Nodes, span: Span, after: str) -> Verdict | None:
    if PATH_SPAN_RE.fullmatch(span.content) is None:
        return None
    return Verdict(path_reference(nodes, span.open + 1, span.content, True))


def bare_name_span(nodes: Nodes, span: Span, after: str) -> Verdict | None:
    if NAME_SPAN_RE.fullmatch(span.content) is None:
        return None
    found = stem_candidates(nodes, span.content)
    if not found:
        return None
    return Verdict(Match(span.open + 1, span.content, "bare-name", candidate_status(found),
                         plain_targets(found)))


SPAN_FORMS = (command_span, section_span, rule_name_span, path_span, bare_name_span)


def span_verdict(nodes: Nodes, span: Span, line_text: str) -> Verdict | None:
    """The first span form that matches, or None when the token grammar must scan the span."""
    after = line_text[span.close + 1:]
    for form in SPAN_FORMS:
        verdict = form(nodes, span, after)
        if verdict is not None:
            return verdict
    return None


# ---------------------------------------------------------------------------
# Reference edges: token grammar
# ---------------------------------------------------------------------------

TOKEN_PATH_RE = re.compile(r"(?<![A-Za-z0-9_./-])(?:(?:rules|workflows|harness)/"
                           r"[A-Za-z0-9_*./-]*[A-Za-z0-9_*]|templates/codex-global-AGENTS\.md)")
TOKEN_MD_NAME_RE = re.compile(r"(?<![A-Za-z0-9_-])([A-Za-z0-9_-]+)\.md(?![A-Za-z0-9_-])")
TOKEN_SKILL_RE = re.compile(r"(?<![A-Za-z0-9_-])rule-([a-z0-9]+(?:-[a-z0-9]+)*)"
                            r"(?![A-Za-z0-9_-])")
TOKEN_COMMAND_RE = re.compile(r"(?<![A-Za-z0-9_./-])/([A-Za-z0-9_-]+)(?![A-Za-z0-9_/-])")
TOKEN_BARE_RE = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]+(?![A-Za-z0-9_-])")


def path_token(nodes: Nodes, found: re.Match[str]) -> Verdict | None:
    return Verdict(path_reference(nodes, found.start(), found.group(0), False))


def md_name_token(nodes: Nodes, found: re.Match[str]) -> Verdict | None:
    candidates = stem_candidates(nodes, found.group(1))
    if not candidates:
        return None
    return Verdict(Match(found.start(), found.group(0), "md-name", candidate_status(candidates),
                         plain_targets(candidates), md_suffix=True))


def skill_name_token(nodes: Nodes, found: re.Match[str]) -> Verdict | None:
    candidates = stem_candidates(nodes, found.group(1), workflows=False)
    return Verdict(Match(found.start(), found.group(0), "skill-name",
                         "resolved" if candidates else "missing-target",
                         plain_targets(candidates)))


def command_token(nodes: Nodes, found: re.Match[str]) -> Verdict | None:
    name = found.group(1)
    if name not in nodes.workflow_stems:
        return None
    return Verdict(Match(found.start(), found.group(0), "command", "resolved",
                         plain_targets([f"workflows/{name}.md"])))


def bare_name_token(nodes: Nodes, found: re.Match[str]) -> Verdict | None:
    """Only stems with a hyphen; shorter stems are found by the other forms alone."""
    name = found.group(0)
    candidates = stem_candidates(nodes, name) if "-" in name else []
    if not candidates:
        return None
    return Verdict(Match(found.start(), name, "bare-name", candidate_status(candidates),
                         plain_targets(candidates)))


TokenResolver = Callable[[Nodes, re.Match[str]], Verdict | None]
TOKEN_FORMS: tuple[tuple[re.Pattern[str], TokenResolver], ...] = (
    (TOKEN_PATH_RE, path_token), (TOKEN_MD_NAME_RE, md_name_token),
    (TOKEN_SKILL_RE, skill_name_token), (TOKEN_COMMAND_RE, command_token),
    (TOKEN_BARE_RE, bare_name_token),
)


def token_matches(nodes: Nodes, text: str, masked: list[bool]) -> list[Match]:
    """Apply the token forms in order; each match masks its characters from later forms."""
    found: list[Match] = []
    for pattern, resolve in TOKEN_FORMS:
        position = 0
        while (candidate := pattern.search(text, position)) is not None:
            start, end = candidate.span()
            if any(masked[start:end]):
                position = start + 1
                continue
            position = end
            verdict = resolve(nodes, candidate)
            if verdict is None:
                continue
            masked[start:end] = [True] * (end - start)
            if verdict.match is not None:
                found.append(verdict.match)
    return found


# ---------------------------------------------------------------------------
# Reference edges: sources, contexts and the load flag
# ---------------------------------------------------------------------------

LOAD_WORD_RE = re.compile(r"\b(load|loads|loaded|loading|read|reads|reading)\b", re.IGNORECASE)
CHECK_DESCRIPTION_RE = re.compile(r'[ \t]*check [^"]*"((?:[^"\\]|\\.)*)')
CONTEXT_FOR_ZONE = {ZONE_FRONT_MATTER: "front-matter", ZONE_FENCE: "fence"}
NON_DEFECT_STATUSES = frozenset({"resolved", "resolved-prefix"})


@dataclass(frozen=True)
class Source:
    """A decoded file whose references become edges."""

    path: str
    reader_class: str
    data: bytes
    audited: bool


@dataclass(frozen=True)
class LineEdges:
    """The matches of one line with the context of each and the line's load flag."""

    matches: tuple[tuple[Match, str], ...]
    load_line: bool


def edge_entry(source: Source, line: int, match: Match, context: str, load_line: bool
               ) -> JsonObject:
    in_grammar = (match.grammar_form and context == "span"
                  and GRAMMAR_SOURCE_RE.fullmatch(source.path) is not None
                  and match.status != "heading-unmarked")
    return {"source": source.path, "class": source.reader_class, "line": line,
            "column": match.start, "context": context, "form": match.form, "raw": match.raw,
            "load": load_line and context == "span", "md_suffix": match.md_suffix,
            "in_spec09_grammar": in_grammar, "status": match.status,
            "targets": [{"path": path, "heading_status": status}
                        for path, status in match.targets]}


def is_load_line(text: str, spans: Sequence[Span]) -> bool:
    """Whether the line, with every span replaced by a space, names loading or reading."""
    pieces, position = [], 0
    for span in spans:
        pieces.append(text[position:span.open])
        position = span.close + 1
    pieces.append(text[position:])
    return LOAD_WORD_RE.search(" ".join(pieces)) is not None


def body_line_edges(nodes: Nodes, text: str, audited_markdown: bool) -> LineEdges:
    """Spans first by the span grammar, then the rest of the line by the token grammar."""
    masked = [False] * len(text)
    matches: list[tuple[Match, str]] = []
    open_spans: list[Span] = []
    spans = spans_of(text)
    for span in spans:
        verdict = span_verdict(nodes, span, text)
        if verdict is None:
            open_spans.append(span)
            continue
        masked[span.open:span.close + 1] = [True] * (span.close + 1 - span.open)
        if verdict.match is not None:
            matches.append((verdict.match, "span"))
    for match in token_matches(nodes, text, masked):
        inside = any(span.open < match.start < span.close for span in open_spans)
        matches.append((match, "span" if inside else "text"))
    return LineEdges(tuple(matches), audited_markdown and is_load_line(text, spans))


def by_column(matches: Iterable[tuple[Match, str]]) -> list[tuple[Match, str]]:
    return sorted(matches, key=lambda pair: pair[0].start)


def zone_line_edges(nodes: Nodes, text: str, context: str) -> LineEdges:
    found = token_matches(nodes, text, [False] * len(text))
    return LineEdges(tuple((match, context) for match in found), False)


def markdown_edges(nodes: Nodes, source: Source) -> list[JsonObject]:
    edges: list[JsonObject] = []
    for line in build_text_model(source.data).lines:
        if line.zone == ZONE_BODY:
            found = body_line_edges(nodes, line.text, source.audited)
        else:
            found = zone_line_edges(nodes, line.text, CONTEXT_FOR_ZONE[line.zone])
        edges += [edge_entry(source, line.number, match, context, found.load_line)
                  for match, context in by_column(found.matches)]
    return edges


def validator_context(text: str, position: int) -> str:
    """`comment` for a `#` line, `check-description` inside the first quoted check string."""
    if text.lstrip().startswith("#"):
        return "comment"
    described = CHECK_DESCRIPTION_RE.match(text)
    if described is not None and described.start(1) <= position < described.end(1):
        return "check-description"
    return "text"


def plain_edges(nodes: Nodes, source: Source) -> list[JsonObject]:
    """Sources other than Markdown use the token grammar only."""
    edges: list[JsonObject] = []
    for number, raw in enumerate(raw_lines(source.data), start=1):
        text = matching_text(raw.decode("utf-8"))
        for match in sorted(token_matches(nodes, text, [False] * len(text)),
                            key=lambda found: found.start):
            context = (validator_context(text, match.start)
                       if source.path == VALIDATOR_PATH else "text")
            edges.append(edge_entry(source, number, match, context, False))
    return edges


def edge_sources(audited: Sequence[AuditedFile], readers: dict[str, str],
                 reader_data: dict[str, bytes]) -> list[Source]:
    """Decoded audited files (class active) and decoded readers; nothing else has edges."""
    sources = [Source(item.path, "active", item.data, True) for item in audited
               if item.data is not None and encoding_of(item.data)[0] == "utf-8"]
    sources += [Source(path, readers[path], data, False) for path, data in reader_data.items()
                if decode_strict(data) is not None]
    return sources


def reference_edges(nodes: Nodes, sources: Iterable[Source]) -> list[JsonObject]:
    """Every edge, ordered by source path, then line, then column."""
    edges: list[JsonObject] = []
    for source in sorted(sources, key=lambda item: item.path):
        extractor = markdown_edges if source.path.endswith(".md") else plain_edges
        edges += extractor(nodes, source)
    return edges


def is_defect_edge(edge: Mapping[str, object]) -> bool:
    """An active, non-fence, non-bare-name edge that is unresolved or carries a `.md` suffix."""
    return (edge["class"] == "active" and edge["context"] != "fence"
            and edge["form"] != "bare-name"
            and (edge["status"] not in NON_DEFECT_STATUSES or edge["md_suffix"] is True))


# ---------------------------------------------------------------------------
# Candidates: repeated loads through workflow calls
# ---------------------------------------------------------------------------

CALL_VERB_RE = re.compile(r"\b(run|runs|invoke|invokes|call|calls|execute|executes|delegate|"
                          r"delegates|spawn|spawns)\b", re.IGNORECASE)
NEGATION_RE = re.compile(r"\b(not|never|no)\b|n't\b", re.IGNORECASE)
CLAUSE_DELIMITERS = ".;:,—→()"
STOP_MARKER = "**stop**"
CALL_CONTEXTS = frozenset({"span", "text"})


@dataclass(frozen=True)
class MarkdownFile:
    """A decoded audited Markdown file with its text model."""

    path: str
    model: TextModel


def markdown_files(audited: Sequence[AuditedFile]) -> list[MarkdownFile]:
    """Audited `.md` files whose encoding is `utf-8`, in path order."""
    return [MarkdownFile(item.path, build_text_model(item.data))
            for item in sorted(audited, key=lambda found: found.path)
            if item.path.endswith(".md") and item.data is not None
            and encoding_of(item.data)[0] == "utf-8"]


def without_spans(text: str) -> str:
    """The line with every span, backticks included, replaced by spaces of equal length."""
    characters = list(text)
    for span in spans_of(text):
        characters[span.open:span.close + 1] = [" "] * (span.close + 1 - span.open)
    return "".join(characters)


def call_clause(text: str, column: int) -> str:
    """The span-free text after the last clause delimiter before `column`, up to it."""
    before = without_spans(text)[:column]
    start = max(before.rfind(delimiter) for delimiter in CLAUSE_DELIMITERS) + 1
    return before[start:]


def is_call(text: str, column: int) -> bool:
    """A call verb in the clause, no negation before it, and no earlier stop marker."""
    if STOP_MARKER in text[:column]:
        return False
    clause = call_clause(text, column)
    verb = CALL_VERB_RE.search(clause)
    return verb is not None and NEGATION_RE.search(clause[:verb.start()]) is None


def invocable_workflows(files: Sequence[MarkdownFile]) -> dict[str, MarkdownFile]:
    """Top-level workflows with at least one `Invocation:` line, by path."""
    return {item.path: item for item in files
            if WORKFLOW_FILE_RE.fullmatch(item.path) and invocation_line_count(item.model) > 0}


def target_paths(edge: Mapping[str, object]) -> list[str]:
    targets = edge["targets"]
    return [str(target["path"]) for target in targets] if isinstance(targets, list) else []


def is_call_edge(edge: Mapping[str, object], callers: Mapping[str, MarkdownFile]) -> bool:
    """A resolved span or text command from an invocable workflow to another workflow."""
    caller = callers.get(str(edge["source"]))
    if (caller is None or edge["form"] != "command" or edge["status"] != "resolved"
            or edge["context"] not in CALL_CONTEXTS or caller.path in target_paths(edge)):
        return False
    text = caller.model.lines[int(str(edge["line"])) - 1].text
    return is_call(text, int(str(edge["column"])))


def call_pairs(edges: Sequence[JsonObject], callers: Mapping[str, MarkdownFile]
               ) -> set[tuple[str, str]]:
    return {(str(edge["source"]), callee) for edge in edges if is_call_edge(edge, callers)
            for callee in target_paths(edge)}


def single_target_loads(edges: Sequence[JsonObject]) -> dict[str, set[str]]:
    """The targets each source loads through load edges that have exactly one target."""
    loads: dict[str, set[str]] = {}
    for edge in edges:
        targets = target_paths(edge)
        if edge["load"] is True and len(targets) == 1:
            loads.setdefault(str(edge["source"]), set()).add(targets[0])
    return loads


def repeat_loads(files: Sequence[MarkdownFile], edges: Sequence[JsonObject]
                 ) -> list[JsonObject]:
    """One entry per call pair and target both workflows load, ordered and numbered."""
    loads = single_target_loads(edges)
    rows = [(caller, callee, target)
            for caller, callee in call_pairs(edges, invocable_workflows(files))
            for target in loads.get(caller, set()) & loads.get(callee, set())]
    return [{"id": f"RL-{number:03d}", "caller": caller, "callee": callee, "target": target}
            for number, (caller, callee, target) in enumerate(sorted(rows), start=1)]


# ---------------------------------------------------------------------------
# Candidates: full-output and harness-name lines, legacy mentions
# ---------------------------------------------------------------------------

FULL_WORD_RE = re.compile(r"\b(full|entire|complete|whole|verbatim|raw|unabridged)\b",
                          re.IGNORECASE)
OUTPUT_WORD_RE = re.compile(r"\b(outputs?|logs?|diffs?|transcripts?|stdout|stderr)\b",
                            re.IGNORECASE)
HARNESS_NAME_RE = re.compile(r"\b(claude code|claude|codex)\b", re.IGNORECASE)
LEGACY_TERM_RE = re.compile(r"windsurf|codeium|\bdevin\b", re.IGNORECASE)
LEGACY_SUFFIXES = (".md", ".json")
CANDIDATE_TEXT_LIMIT = 160
# A home directory prefix `/home/<name>/` or `/Users/<name>/` that starts a path.
HOME_PREFIX_RE = re.compile(r"(?<![\w./~-])/(?:home|Users)/[^/\s]+/")


def home_relative(text: str) -> str:
    """Text copied from an audited file, with home directory prefixes written as `~/`."""
    return HOME_PREFIX_RE.sub("~/", text)


def candidate_text(text: str) -> str:
    """The line made home-relative, whitespace runs collapsed, cut to the text limit."""
    return " ".join(home_relative(text).split())[:CANDIDATE_TEXT_LIMIT]


def is_full_output_line(text: str) -> bool:
    return FULL_WORD_RE.search(text) is not None and OUTPUT_WORD_RE.search(text) is not None


def is_harness_name_line(text: str) -> bool:
    return HARNESS_NAME_RE.search(text) is not None


def line_candidates(files: Sequence[MarkdownFile], prefix: str,
                    matches: Callable[[str], bool]) -> list[JsonObject]:
    """Matching lines outside fences and front matter, numbered in path then line order."""
    found = [(item.path, line) for item in files for line in item.model.lines
             if line.zone == ZONE_BODY and matches(line.text)]
    return [{"id": f"{prefix}-{number:03d}", "source": path, "line": line.number,
             "text": candidate_text(line.text)}
            for number, (path, line) in enumerate(found, start=1)]


def legacy_mentions(audited: Sequence[AuditedFile]) -> list[JsonObject]:
    """Every legacy term in decoded audited Markdown and JSON files, fences included."""
    mentions: list[JsonObject] = []
    for item in sorted(audited, key=lambda found: found.path):
        if (not item.path.endswith(LEGACY_SUFFIXES) or item.data is None
                or encoding_of(item.data)[0] != "utf-8"):
            continue
        for number, raw in enumerate(raw_lines(item.data), start=1):
            text = matching_text(raw.decode("utf-8"))
            mentions += [{"source": item.path, "line": number, "column": found.start(),
                          "term": found.group(0).lower(), "text": candidate_text(text)}
                         for found in LEGACY_TERM_RE.finditer(text)]
    return mentions


# ---------------------------------------------------------------------------
# Candidates: verbatim duplicate clusters
# ---------------------------------------------------------------------------

TABLE_SEPARATOR_RE = re.compile(r"\|[-:| ]+\|")
LINE_PREFIX_RE = re.compile(r"\s*>?\s*(?:[-*+] |\d+[.)] )?")
SENTENCE_END = (".", "!", "?")
MINIMUM_UNIT_WORDS = 8

Word = tuple[str, int]


@dataclass(frozen=True)
class Unit:
    """One text unit: its text, location and reading order within the audited set."""

    text: str
    path: str
    line_start: int
    line_end: int
    order: int


def sentences(words: Sequence[Word]) -> list[list[Word]]:
    """Split a paragraph's words after each word that ends a sentence."""
    found: list[list[Word]] = [[]]
    for word in words:
        found[-1].append(word)
        if word[0].endswith(SENTENCE_END):
            found.append([])
    return [sentence for sentence in found if sentence]


def paragraph_text(text: str) -> str:
    """A paragraph line without a leading quote marker, indentation and list marker."""
    prefix = LINE_PREFIX_RE.match(text)
    return text[prefix.end():] if prefix is not None else text


def unit_lines(model: TextModel) -> Iterator[tuple[str, list[Word]]]:
    """Yield table rows and paragraphs as words with line numbers, in line order."""
    heading_lines = {heading.line for heading in model.headings}
    paragraph: list[Word] = []
    for line in model.lines:
        text = line.text
        in_paragraph = (line.zone == ZONE_BODY and line.number not in heading_lines
                        and text.strip() != "" and not text.startswith("|"))
        if in_paragraph:
            paragraph += [(word, line.number)
                          for word in home_relative(paragraph_text(text)).split()]
            continue
        if paragraph:
            yield "paragraph", paragraph
            paragraph = []
        if (line.zone == ZONE_BODY and text.startswith("|")
                and TABLE_SEPARATOR_RE.fullmatch(text) is None):
            yield "row", [(word, line.number) for word in home_relative(text).split()]
    if paragraph:
        yield "paragraph", paragraph


def text_units(files: Sequence[MarkdownFile]) -> list[Unit]:
    """Every unit of at least the minimum word count, in path then reading order."""
    units: list[Unit] = []
    for item in files:
        for kind, words in unit_lines(item.model):
            for piece in ([words] if kind == "row" else sentences(words)):
                if len(piece) >= MINIMUM_UNIT_WORDS:
                    units.append(Unit(" ".join(word for word, _ in piece), item.path,
                                      piece[0][1], piece[-1][1], len(units)))
    return units


def member_key(unit: Unit) -> tuple[str, int, int, int]:
    return unit.path, unit.line_start, unit.line_end, unit.order


def duplicate_clusters(files: Sequence[MarkdownFile]) -> list[JsonObject]:
    """Units equal in two or more places, ordered by first member and numbered."""
    groups: dict[str, list[Unit]] = {}
    for unit in text_units(files):
        groups.setdefault(unit.text, []).append(unit)
    clusters = sorted((sorted(members, key=member_key) for members in groups.values()
                       if len(members) > 1), key=lambda members: member_key(members[0]))
    return [{"id": f"DUP-{number:03d}", "sha256": sha256_hex(members[0].text.encode("utf-8")),
             "words": len(members[0].text.split()), "text": members[0].text,
             "members": [{"path": unit.path, "line_start": unit.line_start,
                          "line_end": unit.line_end} for unit in members]}
            for number, members in enumerate(clusters, start=1)]


def candidate_lists(audited: Sequence[AuditedFile], edges: Sequence[JsonObject]
                    ) -> JsonObject:
    """The five candidate lists in inventory key order."""
    files = markdown_files(audited)
    return {"repeat_loads": repeat_loads(files, edges),
            "full_output": line_candidates(files, "FO", is_full_output_line),
            "harness_names": line_candidates(files, "HN", is_harness_name_line),
            "legacy_mentions": legacy_mentions(audited),
            "duplicate_clusters": duplicate_clusters(files)}


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------

def read_git_metadata(path: Path, limit: int) -> bytes | None:
    """A regular file of fewer than limit bytes, links followed as git follows them; None
    when it is absent, not a regular file, too large or unreadable. A first-in first-out
    entry is never waited on."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    except (OSError, ValueError):
        return None
    with os.fdopen(descriptor, "rb") as handle:
        try:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size >= limit:
                return None
            return handle.read(limit)
        except OSError:
            return None


def metadata_text(data: bytes) -> str:
    """The text git takes from a one-line metadata file: up to a NUL, without trailing
    white space."""
    return data.split(b"\0", 1)[0].decode("utf-8", "surrogateescape").rstrip()


def git_common_directory(root: Path) -> Path | None:
    """The repository directory that holds info/ and the configuration for the root's
    `.git` directory or file; None when there is none or it cannot be read."""
    dot_git = root / ".git"
    try:
        is_directory = stat.S_ISDIR(os.stat(dot_git).st_mode)
    except (OSError, ValueError):
        return None
    if is_directory:
        git_directory = dot_git
    else:
        data = read_git_metadata(dot_git, GIT_METADATA_LIMIT)
        if data is None or not data.startswith(b"gitdir: "):
            return None
        target = metadata_text(data[len(b"gitdir: "):])
        if not target:
            return None
        git_directory = root / target
    common = read_git_metadata(git_directory / "commondir", GIT_METADATA_LIMIT)
    target = metadata_text(common) if common is not None else ""
    return git_directory / target if target else git_directory


def config_value(text: str) -> str:
    """A configuration value without its quotes and its trailing comment."""
    kept: list[str] = []
    quoted = False
    for character in text:
        if character == '"':
            quoted = not quoted
        elif character in "#;" and not quoted:
            break
        else:
            kept.append(character)
    return "".join(kept).strip()


def object_format(common: Path) -> str | None:
    """The repository's extensions.objectFormat, `sha1` when it is unset or there is no
    configuration file; None when the configuration cannot be read or names a format
    without a known empty tree."""
    config = common / "config"
    if not os.path.lexists(config):
        return "sha1"
    data = read_git_metadata(config, GIT_METADATA_LIMIT)
    if data is None:
        return None
    value = "sha1"
    section: str | None = None
    for raw in data.decode("utf-8", "surrogateescape").splitlines():
        line = raw.strip()
        header = CONFIG_SECTION_RE.match(line)
        if header is not None:
            section = header.group(1).lower() if header.group(2) is None else None
            line = line[header.end():].strip()
        if section != "extensions" or not line or line[0] in "#;":
            continue
        entry = CONFIG_ENTRY_RE.fullmatch(line)
        if entry is not None and entry.group(1).lower() == "objectformat":
            value = config_value(entry.group(2) or "")
    return value if value in EMPTY_TREES else None


def information_attribute_filters(common: Path) -> list[str]:
    """The filter driver names that the repository's info/attributes file sets, macros
    included, read within git's own line and file limits and kept within the blanking
    bounds in name order; empty when the file is absent or cannot be read."""
    data = read_git_metadata(common / "info" / "attributes", ATTRIBUTE_FILE_LIMIT)
    if data is None:
        return []
    names: set[str] = set()
    for line in data.split(b"\n"):
        if len(line.rstrip(b"\r")) <= ATTRIBUTE_LINE_LIMIT:
            text = line.decode("utf-8", "surrogateescape")
            names.update(found.group(1) for found in FILTER_ATTRIBUTE_RE.finditer(text))
    kept: list[str] = []
    used = 0
    for name in sorted(names):
        size = len(os.fsencode(name))
        if len(kept) == BLANKED_NAME_LIMIT or used + size > BLANKED_BYTES_LIMIT:
            break
        kept.append(name)
        used += size
    return kept


def blank_filter_environment(names: Sequence[str]) -> dict[str, str]:
    """Command-line scope configuration, by environment so that no name is parsed, that
    gives each named filter driver no clean or process program and makes it optional."""
    pairs = [(f"filter.{name}.{key}", value) for name in names
             for key, value in BLANK_FILTER_SETTINGS]
    if not pairs:
        return {}
    environment = {"GIT_CONFIG_COUNT": str(len(pairs))}
    for index, (key, value) in enumerate(pairs):
        environment[f"GIT_CONFIG_KEY_{index}"] = key
        environment[f"GIT_CONFIG_VALUE_{index}"] = value
    return environment


def git_environment(root: Path) -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("GIT_")}
    environment.update(GIT_READ_ENVIRONMENT)
    common = git_common_directory(root)
    if common is not None:
        found_format = object_format(common)
        if found_format is not None:
            environment["GIT_ATTR_SOURCE"] = EMPTY_TREES[found_format]
        environment.update(blank_filter_environment(information_attribute_filters(common)))
    return environment


def run_git(root: Path, *arguments: str) -> bytes | None:
    """Run one git read command; None when git is missing or the command fails."""
    try:
        result = subprocess.run(["git", "--no-pager", *GIT_INERT_CONFIGURATION,
                                 "-C", str(root), *arguments],
                                stdin=subprocess.DEVNULL, capture_output=True,
                                env=git_environment(root), check=False)
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
    require_utf8_paths(paths)
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
    audited, directories = audited_paths(root)
    readers_found = reader_paths(root)
    require_utf8_paths([*audited, *readers_found])
    tracked = tracked_paths(root)
    audited_files = [read_audited(root, path, audited[path]) for path in sorted(audited)]
    reader_data = {path: read_regular_file(root / path) for path in sorted(readers_found)}
    files = [file_entry(item, tracked) for item in audited_files]
    readers = [reader_entry(path, readers_found[path], data)
               for path, data in reader_data.items()]
    nodes = build_nodes(audited_files, directories)
    edges = reference_edges(nodes, edge_sources(audited_files, readers_found, reader_data))
    listed = frozenset(audited) | frozenset(readers_found)
    return {
        "schema_version": SCHEMA_VERSION,
        "method_version": METHOD_VERSION,
        "source_revision": source_revision(root),
        "worktree": worktree_state(root, listed),
        "inventory_digest": inventory_digest(files, readers),
        "files": files,
        "readers": readers,
        "edges": edges,
        **candidate_lists(audited_files, edges),
    }


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def current_umask() -> int:
    mask = os.umask(0)
    os.umask(mask)
    return mask


OUT_FAILURE = ("out-unwritable", "cannot write the --out file")


def write_atomically(target: Path, text: str, failure: tuple[str, str] = OUT_FAILURE,
                     mode: int | None = None) -> None:
    """Write to a temporary file beside the target and move it into place; on any failure
    the temporary file is removed and `failure` names the error code and message."""
    code, message = failure
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp",
                                                 dir=target.parent)
    except OSError as error:
        raise ToolError(code, f"{message} ({error.strerror})") from error
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            os.fchmod(handle.fileno(), mode if mode is not None else 0o666 & ~current_umask())
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except (OSError, UnicodeEncodeError) as error:
        with suppress(FileNotFoundError):
            os.unlink(temporary)
        reason = error.strerror if isinstance(error, OSError) else "text is not encodable"
        raise ToolError(code, f"{message} ({reason})") from error


def run_extract(root: Path, out: Path) -> int:
    try:
        validate_root(root)
        inventory = build_inventory(root)
    except OSError as error:
        raise ToolError("root-unreadable", f"cannot read the root ({error.strerror})") from error
    write_atomically(out, canonical_json(inventory))
    return 0


# ---------------------------------------------------------------------------
# Verify: diagnostics and document loading
# ---------------------------------------------------------------------------

@dataclass(frozen=True, order=True)
class Diagnostic:
    """One violation, printed as `<code> <location> <message>`."""

    code: str
    location: str
    message: str


@dataclass(frozen=True)
class Document:
    """A JSON file named by its root-relative (or base) name, with its text once parsed."""

    name: str
    value: object
    text: str


class JsonRejected(ValueError):
    """A JSON text with a duplicate key or a non-standard constant."""


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> JsonObject:
    keys = [key for key, _ in pairs]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise JsonRejected(f'duplicate key "{duplicates[0]}"')
    return dict(pairs)


def reject_constant(name: str) -> NoReturn:
    raise JsonRejected(f"non-standard constant {name}")


def parse_json(text: str) -> object:
    """Parse JSON text; the value must also be writable as UTF-8 (no unpaired surrogate)."""
    value = json.loads(text, object_pairs_hook=reject_duplicate_keys,
                       parse_constant=reject_constant)
    try:
        json.dumps(value, ensure_ascii=False).encode("utf-8")
    except UnicodeEncodeError:
        raise JsonRejected("a string holds an unpaired surrogate") from None
    return value


def display_name(path: Path, root: Path) -> str:
    """The path relative to the root, or its base name when it lies outside the root."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def link_name(path: Path, root: Path) -> str:
    """The root-relative name of a path whose last component may be a symbolic link,
    which is named itself rather than its target; the base name outside the root."""
    try:
        relative = path.parent.resolve().relative_to(root.resolve())
    except ValueError:
        return path.name
    return (relative / path.name).as_posix()


def load_document(path: Path, name: str, code: str) -> Document | Diagnostic:
    """Read and parse one JSON file; a missing or unparseable file is one diagnostic."""
    try:
        text = path.read_bytes().decode("utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return Diagnostic(f"{code}-missing", f"{name}:0", "the file does not exist")
    except (OSError, UnicodeDecodeError) as error:
        reason = error.strerror if isinstance(error, OSError) else "not valid UTF-8"
        return Diagnostic(f"{code}-invalid", f"{name}:0", f"cannot be read ({reason})")
    try:
        return Document(name, parse_json(text), text)
    except json.JSONDecodeError as error:
        return Diagnostic(f"{code}-invalid", f"{name}:{error.lineno}",
                          f"not parseable JSON ({error.msg})")
    except (ValueError, RecursionError) as error:
        return Diagnostic(f"{code}-invalid", f"{name}:0", f"rejected JSON ({error})")


# ---------------------------------------------------------------------------
# Verify: structural schemas
# ---------------------------------------------------------------------------

Check = Callable[[object], bool]

HEX_DIGEST_RE = re.compile(r"[0-9a-f]{64}")
ROLE_LABEL_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*")
SAFE_FRAGMENT_RE = re.compile(r"[A-Za-z0-9_.-]+")
EVIDENCE_LINE_RE = re.compile(r"[^\s:]+:\d+")
AMENDMENT_ID_RE = re.compile(r"AMD-08-\d{2}")
KINDS = ("bootstrap", "contract", "protocol", "procedure", "always-on", "workflow",
         "reference", "adapter-config")
PROPOSAL_TYPES = ("load-repeat", "conditional-context", "report-repeat", "checkpoint-repeat",
                  "review-repeat", "full-output")
REFERENCE_TYPES = ("reference-defect", "ambiguous-name", "mixed-kind", "naming",
                   "legacy-mention", "duplicate")
FINDING_OWNERS: dict[str, frozenset[str]] = {
    **{name: frozenset({"11", "12", "13", "15", "14"}) for name in PROPOSAL_TYPES},
    **{name: frozenset({"09", "11"}) for name in REFERENCE_TYPES},
    "contradiction": frozenset({"owner"}),
    "coverage-gap": frozenset({"09", "11", "12", "13", "15", "14", "owner"}),
    "other": frozenset({"09", "11", "12", "13", "15", "14", "owner"}),
    "accepted-observation": frozenset({"none"}),
}
EDGE_STATUSES = ("resolved", "resolved-prefix", "heading-unmarked", "missing-heading",
                 "missing-target", "missing-path", "unknown-command", "glob-empty",
                 "ambiguous-stem")
EDGE_FORMS = ("command", "section-ref", "rule-name", "path", "glob", "bare-name", "md-name",
              "skill-name")
EDGE_CONTEXTS = ("front-matter", "fence", "span", "text", "check-description", "comment")


def is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_str(value: object) -> bool:
    return isinstance(value, str)


def is_bool(value: object) -> bool:
    return isinstance(value, bool)


def is_object(value: object) -> bool:
    return isinstance(value, dict)


def is_list(value: object) -> bool:
    return isinstance(value, list)


def nullable(check: Check) -> Check:
    return lambda value: value is None or check(value)


def one_of(*values: str) -> Check:
    return lambda value: isinstance(value, str) and value in values


def matching(pattern: re.Pattern[str]) -> Check:
    return lambda value: isinstance(value, str) and pattern.fullmatch(value) is not None


def list_of(check: Check, non_empty: bool = False, unique: bool = False) -> Check:
    def checked(value: object) -> bool:
        if not isinstance(value, list) or (non_empty and not value):
            return False
        if unique and len({json.dumps(item) for item in value}) != len(value):
            return False
        return all(check(item) for item in value)
    return checked


def record(fields: Mapping[str, Check]) -> Check:
    return lambda value: (isinstance(value, dict) and set(value) == set(fields)
                          and all(check(value[key]) for key, check in fields.items()))


def is_date(value: object) -> bool:
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def is_repository_path(value: object) -> bool:
    return (isinstance(value, str) and bool(value) and not value.startswith("/")
            and not any(part in ("", ".", "..") for part in value.split("/"))
            and not any(character.isspace() for character in value))


DIGEST = matching(HEX_DIGEST_RE)
ROLE = matching(ROLE_LABEL_RE)
LINE_REF = record({"source": is_str, "line": is_int, "column": is_int})
SPAN = record({"path": is_str, "line_start": is_int, "line_end": is_int})
AUDIT_ID = matching(re.compile(r"AUD-08-\d{3}"))
AMENDMENT_ID = matching(AMENDMENT_ID_RE)
MAP_DECISIONS = ("keep", "rename", "move", "split", "merge")
MAP_TARGET = record({"path": is_repository_path, "sections": nullable(list_of(is_str)),
                     "merge_reason": nullable(is_str)})
DEFAULT_TARGET = record({"path": is_repository_path, "sections": nullable(list_of(is_str))})
STATEMENT = record({"source": is_str, "text": is_str,
                    "covered_by": nullable(matching(EVIDENCE_LINE_RE))})


@dataclass(frozen=True)
class ListSchema:
    """A list whose rows each satisfy `row`; `unique` names a field that may not repeat."""

    row: Check
    unique: str | None = None


Schema = Mapping[str, "Check | ListSchema"]

INVENTORY_SCHEMA: Schema = {
    "schema_version": lambda value: is_int(value) and value == SCHEMA_VERSION,
    "method_version": lambda value: value == METHOD_VERSION,
    "source_revision": nullable(is_str),
    "worktree": record({"state": one_of("clean", "dirty", "unknown"),
                        "paths": list_of(is_str)}),
    "inventory_digest": DIGEST,
    "files": ListSchema(record({
        "path": is_str, "set": one_of("primary", "adapter"),
        "entry": one_of("file", "symlink", "other"), "tracked": nullable(is_bool),
        "sha256": nullable(DIGEST), "bytes": nullable(is_int), "lines": nullable(is_int),
        "encoding": nullable(one_of("utf-8", "invalid", "control-character")),
        "words": nullable(is_int), "front_matter": nullable(is_object),
        "invocation_lines": nullable(is_int),
        "sections": list_of(record({"heading": is_str, "line": is_int, "words": is_int,
                                    "bytes": is_int}))}), "path"),
    "readers": ListSchema(record({
        "path": is_str, "class": one_of("active", "frozen", "planning", "history"),
        "sha256": DIGEST, "lines": is_int, "decoded": is_bool}), "path"),
    "edges": ListSchema(record({
        "source": is_str, "class": one_of("active", "frozen", "planning", "history"),
        "line": is_int, "column": is_int, "context": one_of(*EDGE_CONTEXTS),
        "form": one_of(*EDGE_FORMS), "raw": is_str, "load": is_bool, "md_suffix": is_bool,
        "in_spec09_grammar": is_bool, "status": one_of(*EDGE_STATUSES),
        "targets": list_of(record({"path": is_str, "heading_status": nullable(one_of(
            "resolved", "resolved-prefix", "heading-unmarked", "missing-heading"))}))})),
    "repeat_loads": ListSchema(record({
        "id": matching(re.compile(r"RL-\d{3}")), "caller": is_str, "callee": is_str,
        "target": is_str}), "id"),
    "full_output": ListSchema(record({
        "id": matching(re.compile(r"FO-\d{3}")), "source": is_str, "line": is_int,
        "text": is_str}), "id"),
    "harness_names": ListSchema(record({
        "id": matching(re.compile(r"HN-\d{3}")), "source": is_str, "line": is_int,
        "text": is_str}), "id"),
    "legacy_mentions": ListSchema(record({
        "source": is_str, "line": is_int, "column": is_int, "term": is_str, "text": is_str})),
    "duplicate_clusters": ListSchema(record({
        "id": matching(re.compile(r"DUP-\d{3}")), "sha256": DIGEST, "words": is_int,
        "text": is_str, "members": list_of(SPAN)}), "id"),
}

ASSESSMENT_SCHEMA: Schema = {
    "schema_version": lambda value: is_int(value) and value == SCHEMA_VERSION,
    "inventory_digest": DIGEST,
    "run_date": is_date,
    "auditor": ROLE,
    "environment": record({"python": is_str, "git": is_str}),
    "installed_access": one_of("not-verified", "verified"),
    "files": ListSchema(record({
        "path": is_str, "sha256": nullable(DIGEST),
        "kinds": list_of(one_of(*KINDS), non_empty=True, unique=True),
        "sections": nullable(list_of(record({"heading": is_str, "kind": one_of(*KINDS),
                                             "proposed_home": is_repository_path}))),
        "evidence": list_of(matching(EVIDENCE_LINE_RE), non_empty=True),
        "repetition": nullable(record({"report": list_of(is_str),
                                       "checkpoint": list_of(is_str),
                                       "review": list_of(is_str)}))})),
    "coverage": ListSchema(record({
        "path": is_str, "sha256": nullable(DIGEST),
        "status": one_of("read", "unavailable", "changed", "not-a-file"), "reader": ROLE})),
    "loads": ListSchema(record({
        "source": is_str, "line": is_int, "column": is_int,
        "mode": one_of("mandatory", "conditional"), "condition": nullable(is_str)})),
    "candidates": ListSchema(record({
        "id": matching(re.compile(r"(RL|FO|HN)-\d{3}")),
        "disposition": one_of("finding", "guarded", "not-applicable"),
        "finding": nullable(is_str), "reason": nullable(is_str)}), "id"),
    "legacy": ListSchema(record({
        "source": is_str, "line": is_int, "column": is_int,
        "role": one_of("active-behavior", "legacy-detection", "historical", "example"),
        "note": is_str})),
    "duplicate_groups": ListSchema(record({
        "id": matching(re.compile(r"DG-\d{3}")), "clusters": list_of(is_str),
        "locations": list_of(SPAN),
        "normative_source": record({"path": is_str, "section": is_str}),
        "condition_differences": is_str,
        "disposition": one_of("consolidate", "intentional", "condition-specific",
                              "contradiction"),
        "owner": is_str, "finding": nullable(is_str), "rationale": is_str}), "id"),
    "map": ListSchema(record({
        "source": is_str, "decision": one_of(*MAP_DECISIONS), "targets": list_of(MAP_TARGET),
        "spec09_default": nullable(list_of(DEFAULT_TARGET)),
        "spec09_optional": list_of(is_repository_path), "amendment": nullable(AMENDMENT_ID)})),
    "req21": record({"verdict": one_of("covered", "not-covered"),
                     "statements": list_of(STATEMENT)}),
    "findings": ListSchema(record({
        "id": AUDIT_ID, "type": one_of(*FINDING_OWNERS),
        "severity": one_of("blocker", "major", "minor"), "source": is_str, "section": is_str,
        "sha256": nullable(DIGEST), "lines": list_of(is_int), "observation": is_str,
        "consequence": is_str, "owner": is_str, "closure": is_str, "blocks_09": is_bool,
        "status": is_str, "evidence": list_of(is_str), "edges": list_of(LINE_REF)}), "id"),
    "amendments": ListSchema(record({
        "id": AMENDMENT_ID, "target": is_str,
        "change": one_of("semantic", "editorial", "relocation"), "current": nullable(is_str),
        "proposed": is_str, "reason": is_str, "evidence": list_of(is_str),
        "affected": list_of(is_str), "depends_on": list_of(AMENDMENT_ID),
        "requires_adr": is_bool, "disposition": one_of("proposed")}), "id"),
    "installed": ListSchema(record({
        "path": is_str, "location": is_str, "source_sha256": is_str,
        "installed_sha256": is_str})),
}


def entry_location(key: str, index: int, entry: object) -> str:
    """The id of an entry that has a well-formed one, otherwise `<key>[<index>]`."""
    identifier = entry.get("id") if isinstance(entry, dict) else None
    if isinstance(identifier, str) and SAFE_FRAGMENT_RE.fullmatch(identifier):
        return identifier
    return f"{key}[{index}]"


def list_diagnostics(name: str, code: str, key: str, value: object, schema: ListSchema
                     ) -> Iterator[Diagnostic]:
    if not isinstance(value, list):
        yield Diagnostic(code, f"{name}#{key}", "is not a list")
        return
    seen: set[str] = set()
    for index, entry in enumerate(value):
        location = f"{name}#{entry_location(key, index, entry)}"
        if not schema.row(entry):
            yield Diagnostic(code, location, f"{key} entry breaks its schema")
        elif schema.unique is not None:
            identity = json.dumps(cast(JsonObject, entry)[schema.unique])
            if identity in seen:
                value = cast(JsonObject, entry)[schema.unique]
                yield Diagnostic(code, location, f'duplicate {schema.unique} "{value}"')
            seen.add(identity)


def schema_diagnostics(document: Document, schema: Schema, code: str) -> list[Diagnostic]:
    """Unknown, missing and malformed keys, malformed rows and repeated ids of a document."""
    value = document.value
    if not isinstance(value, dict):
        return [Diagnostic(code, f"{document.name}:0", "the top level is not a JSON object")]
    found = [Diagnostic(code, f"{document.name}#{key}", "unknown key")
             for key in value if key not in schema]
    for key, check in schema.items():
        location = f"{document.name}#{key}"
        if key not in value:
            found.append(Diagnostic(code, location, "missing key"))
        elif isinstance(check, ListSchema):
            found.extend(list_diagnostics(document.name, code, key, value[key], check))
        elif not check(value[key]):
            found.append(Diagnostic(code, location, "value breaks its schema"))
    return found


# ---------------------------------------------------------------------------
# Verify: the inventory against the root
# ---------------------------------------------------------------------------

def objects(value: object) -> list[JsonObject]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def number(value: object) -> int:
    return value if isinstance(value, int) else 0


def edge_key(item: Mapping[str, object]) -> tuple[str, int, int]:
    return str(item["source"]), number(item["line"]), number(item["column"])


def worktree_diagnostics(inventory: Document) -> list[Diagnostic]:
    state = cast(JsonObject, cast(JsonObject, inventory.value)["worktree"])["state"]
    if state == "clean":
        return []
    return [Diagnostic("worktree-dirty", f"{inventory.name}#worktree",
                       f"the inventory was extracted from a {state} work tree")]


def audited_digests(root: Path) -> dict[str, str | None]:
    """The audited paths on disk now, with the digest of each regular file."""
    audited, _ = audited_paths(root)
    require_utf8_paths(audited)
    return {path: sha256_hex(read_regular_file(root / path))
            if entry_kind(root / path) == "file" else None for path in audited}


def stale_diagnostics(root: Path, inventory: Document) -> list[Diagnostic]:
    recorded = {str(entry["path"]): entry["sha256"]
                for entry in objects(cast(JsonObject, inventory.value)["files"])}
    current = audited_digests(root)
    found: list[Diagnostic] = []
    for path in sorted(recorded.keys() | current.keys()):
        if path not in current:
            found.append(Diagnostic("inventory-stale", f"{path}:0", "removed from the root"))
        elif path not in recorded:
            found.append(Diagnostic("inventory-stale", f"{path}:0", "added to the root"))
        elif current[path] != recorded[path]:
            found.append(Diagnostic("inventory-stale", f"{path}:0", "changed in the root"))
    return found


def first_difference(left: str, right: str) -> int:
    """The 1-based number of the first line on which two texts differ."""
    left_lines, right_lines = left.splitlines(), right.splitlines()
    for line, (one, other) in enumerate(zip(left_lines, right_lines), start=1):
        if one != other:
            return line
    return min(len(left_lines), len(right_lines)) + 1


def strict_diagnostics(root: Path, inventory: Document) -> list[Diagnostic]:
    fresh = canonical_json(build_inventory(root))
    if fresh == inventory.text:
        return []
    line = first_difference(fresh, inventory.text)
    return [Diagnostic("inventory-stale", f"{inventory.name}:{line}",
                       "a fresh extraction differs from the inventory")]


# ---------------------------------------------------------------------------
# Verify: the assessment against the inventory
# ---------------------------------------------------------------------------

ALWAYS_SECTIONED = frozenset({"rules/phase-atomic-execution.md", "rules/phase-discovery.md"})
REPETITION_TYPES = (("report", "report-repeat"), ("checkpoint", "checkpoint-repeat"),
                    ("review", "review-repeat"))
CANDIDATE_TYPES = (("repeat_loads", PROPOSAL_TYPES), ("full_output", PROPOSAL_TYPES),
                   ("harness_names", ("naming",)))
GROUP_OWNERS: dict[str, frozenset[str]] = {"consolidate": frozenset({"11", "09"}),
                                            "contradiction": frozenset({"owner"})}
NO_OWNER = frozenset({"none"})
GAP_STATUSES = ("unavailable", "changed")
ECONOMICS_PATTERNS = (re.compile(r"(?i)\b\d[\d,.]*\s*k?\s*tokens?\b"),
                      re.compile(r"[$€£]\s?\d"), re.compile(r"\b(USD|EUR)\b"))


@dataclass(frozen=True)
class Verification:
    """A schema-valid inventory and assessment with the lookups the rules share."""

    inventory: Document
    assessment: Document
    files: dict[str, JsonObject]
    readers: dict[str, JsonObject]
    findings: dict[str, JsonObject]
    amendment_ids: frozenset[str]
    cited: frozenset[str]
    defects: dict[tuple[str, int, int], JsonObject]
    migration: MigrationText | None
    units: frozenset[int]

    @property
    def inv(self) -> JsonObject:
        return cast(JsonObject, self.inventory.value)

    @property
    def doc(self) -> JsonObject:
        return cast(JsonObject, self.assessment.value)

    def at(self, fragment_text: str) -> str:
        return f"{self.assessment.name}#{fragment_text}"

    def inventory_at(self, fragment_text: str) -> str:
        return f"{self.inventory.name}#{fragment_text}"

    def entry(self, path: str) -> JsonObject | None:
        return self.files.get(path) or self.readers.get(path)

    def rows(self, key: str) -> list[JsonObject]:
        return objects(self.doc[key])


def amendment_lookups(assessment: JsonObject) -> tuple[frozenset[str], frozenset[str]]:
    """Amendment ids and every string their `evidence` lists hold."""
    amendments = objects(assessment["amendments"])
    ids = frozenset(item["id"] for item in amendments if isinstance(item.get("id"), str))
    cited = frozenset(entry for item in amendments
                      for entry in (item.get("evidence") if isinstance(item.get("evidence"), list)
                                    else []) if isinstance(entry, str))
    return cast(frozenset[str], ids), cast(frozenset[str], cited)


def verification(inventory: Document, assessment: Document, migration: MigrationText | None,
                 units: frozenset[int]) -> Verification:
    inv, doc = cast(JsonObject, inventory.value), cast(JsonObject, assessment.value)
    ids, cited = amendment_lookups(doc)
    return Verification(
        inventory, assessment,
        files={str(entry["path"]): entry for entry in objects(inv["files"])},
        readers={str(entry["path"]): entry for entry in objects(inv["readers"])},
        findings={str(entry["id"]): entry for entry in objects(doc["findings"])},
        amendment_ids=ids, cited=cited,
        defects={edge_key(edge): edge for edge in objects(inv["edges"])
                 if is_defect_edge(edge)},
        migration=migration, units=units)


def first_rows(check: Verification, key: str, field: str = "path"
               ) -> dict[str, tuple[int, JsonObject]]:
    """The first row of `key` for each audited path named by `field`, with its index."""
    found: dict[str, tuple[int, JsonObject]] = {}
    for index, row in enumerate(check.rows(key)):
        path = str(row[field])
        if path in check.files and path not in found:
            found[path] = (index, row)
    return found


def section_valid(check: Verification, path: str, section: str) -> bool:
    """A heading of an audited source or `(file)`; any non-blank text for a reader."""
    if path in check.files:
        headings = {str(item["heading"]) for item in objects(check.files[path]["sections"])}
        return section == "(file)" or section in headings
    return path in check.readers and bool(section.strip())


def digest_rule(check: Verification) -> Iterator[Diagnostic]:
    if check.doc["inventory_digest"] != check.inv["inventory_digest"]:
        yield Diagnostic("digest-mismatch", check.at("inventory_digest"),
                         "differs from the inventory's inventory_digest")


ROW_KEYS = (("files", "path"), ("coverage", "path"), ("map", "source"))


def row_rules(check: Verification) -> Iterator[Diagnostic]:
    for key, field in ROW_KEYS:
        seen: set[str] = set()
        for index, row in enumerate(check.rows(key)):
            path, location = str(row[field]), check.at(f"{key}[{index}]")
            if path not in check.files:
                yield Diagnostic("row-extra", location, f"{path} is not an audited path")
            elif path in seen:
                yield Diagnostic("row-duplicate", location, f"second {key} row for {path}")
            seen.add(path)
        for path in check.files:
            if path not in seen:
                yield Diagnostic("row-missing", f"{path}:0", f"no {key} row")


def stale_row_rules(check: Verification) -> Iterator[Diagnostic]:
    for key in ("files", "coverage"):
        for path, (index, row) in first_rows(check, key).items():
            if row["sha256"] != check.files[path]["sha256"]:
                yield Diagnostic("assessment-stale", check.at(f"{key}[{index}]"),
                                 f"sha256 of {path} differs from the inventory")


def section_rules(check: Verification) -> Iterator[Diagnostic]:
    for path, (index, row) in first_rows(check, "files").items():
        expected = sorted(str(item["heading"]) for item in objects(check.files[path]["sections"]))
        sections = row["sections"]
        location = check.at(f"files[{index}]")
        if sections is None:
            if len(cast(list[str], row["kinds"])) > 1 or path in ALWAYS_SECTIONED:
                yield Diagnostic("sections-incomplete", location, "sections are required")
        elif sorted(str(item["heading"]) for item in objects(sections)) != expected:
            yield Diagnostic("sections-incomplete", location,
                             "sections do not cover each section of the file once")


def repetition_ids(check: Verification, location: str, repetition: JsonObject
                   ) -> Iterator[Diagnostic]:
    for key, kind in REPETITION_TYPES:
        for finding_id in cast(list[str], repetition[key]):
            finding = check.findings.get(finding_id)
            if finding is None or finding["type"] != kind:
                yield Diagnostic("repetition-invalid", location,
                                 f"{key} id {finding_id} is not a {kind} finding")


def repetition_rules(check: Verification) -> Iterator[Diagnostic]:
    for path, (index, row) in first_rows(check, "files").items():
        location = check.at(f"files[{index}]")
        invocable = (WORKFLOW_FILE_RE.fullmatch(path) is not None
                     and number(check.files[path]["invocation_lines"]) > 0)
        repetition = row["repetition"]
        if invocable and repetition is None:
            yield Diagnostic("repetition-invalid", location,
                             "a workflow with an Invocation: line needs repetition")
        elif not invocable and repetition is not None:
            yield Diagnostic("repetition-invalid", location,
                             "only a workflow with an Invocation: line has repetition")
        if isinstance(repetition, dict):
            yield from repetition_ids(check, location, repetition)


def condition_matches(row: JsonObject) -> bool:
    condition = row["condition"]
    if row["mode"] == "conditional":
        return isinstance(condition, str) and bool(condition.strip())
    return condition is None


def load_rules(check: Verification) -> Iterator[Diagnostic]:
    load_edges = {edge_key(edge) for edge in objects(check.inv["edges"])
                  if edge["load"] is True and edge["source"] in check.files}
    seen: set[tuple[str, int, int]] = set()
    for index, row in enumerate(check.rows("loads")):
        location, key = check.at(f"loads[{index}]"), edge_key(row)
        if key not in load_edges:
            yield Diagnostic("load-unclassified", location, "names no load edge")
        elif key in seen:
            yield Diagnostic("load-unclassified", location, "second entry for one load edge")
        seen.add(key)
        if not condition_matches(row):
            yield Diagnostic("load-unclassified", location,
                             "a condition is required exactly for a conditional load")
    for source, line, column in sorted(load_edges - seen):
        yield Diagnostic("load-unclassified", f"{source}:{line}",
                         f"the load edge at column {column} has no loads entry")


def candidate_types(check: Verification) -> dict[str, tuple[str, ...]]:
    return {str(item["id"]): types for key, types in CANDIDATE_TYPES
            for item in objects(check.inv[key])}


def disposition_rules(check: Verification, location: str, row: JsonObject,
                      types: tuple[str, ...]) -> Iterator[Diagnostic]:
    finding_id = row["finding"]
    if finding_id is not None and finding_id not in check.findings:
        yield Diagnostic("reference-unknown", location, f"finding {finding_id} does not exist")
    elif row["disposition"] == "finding" and finding_id is None:
        yield Diagnostic("candidate-undisposed", location, "a finding disposition names none")
    elif row["disposition"] == "finding" and check.findings[str(finding_id)]["type"] not in types:
        yield Diagnostic("candidate-undisposed", location,
                         f"finding {finding_id} has a type this candidate does not take")
    elif row["disposition"] != "finding" and not str(row["reason"] or "").strip():
        yield Diagnostic("candidate-undisposed", location, "the disposition needs a reason")


def candidate_rules(check: Verification) -> Iterator[Diagnostic]:
    types = candidate_types(check)
    seen: set[str] = set()
    for row in check.rows("candidates"):
        candidate_id = str(row["id"])
        seen.add(candidate_id)
        if candidate_id not in types:
            yield Diagnostic("reference-unknown", check.at(candidate_id),
                             "no such candidate in the inventory")
        else:
            yield from disposition_rules(check, check.at(candidate_id), row,
                                         types[candidate_id])
    for candidate_id in types:
        if candidate_id not in seen:
            yield Diagnostic("candidate-undisposed", check.inventory_at(candidate_id),
                             "no candidates entry")


def legacy_rules(check: Verification) -> Iterator[Diagnostic]:
    mentions = {edge_key(item) for item in objects(check.inv["legacy_mentions"])}
    seen: set[tuple[str, int, int]] = set()
    for index, row in enumerate(check.rows("legacy")):
        key = edge_key(row)
        if key not in mentions or key in seen:
            yield Diagnostic("legacy-role-missing", check.at(f"legacy[{index}]"),
                             "names no mention, or a mention that already has a role")
        seen.add(key)
    for source, line, column in sorted(mentions - seen):
        yield Diagnostic("legacy-role-missing", f"{source}:{line}",
                         f"the mention at column {column} has no legacy entry")


def span_fits(check: Verification, span: JsonObject) -> bool:
    entry = check.entry(str(span["path"]))
    start, end = number(span["line_start"]), number(span["line_end"])
    return entry is not None and 1 <= start <= end <= number(entry["lines"])


def group_locations(row: JsonObject, clusters: Mapping[str, JsonObject]
                    ) -> set[tuple[str, int, int]]:
    """Distinct locations of a group: members of its known clusters and read-detected ones."""
    spans = [member for cluster_id in cast(list[str], row["clusters"])
             if cluster_id in clusters for member in objects(clusters[cluster_id]["members"])]
    spans += objects(row["locations"])
    return {(str(span["path"]), number(span["line_start"]), number(span["line_end"]))
            for span in spans}


def group_role_faults(row: JsonObject) -> list[str]:
    disposition = str(row["disposition"])
    faults: list[str] = []
    if row["owner"] not in GROUP_OWNERS.get(disposition, NO_OWNER):
        faults.append(f"owner {row['owner']} is not allowed for {disposition}")
    if disposition in GROUP_OWNERS and row["finding"] is None:
        faults.append(f"a {disposition} group needs a finding")
    if not str(row["rationale"]).strip():
        faults.append("the rationale is empty")
    if disposition == "condition-specific" and not str(row["condition_differences"]).strip():
        faults.append("a condition-specific group needs its condition differences")
    return faults


def group_location_faults(check: Verification, row: JsonObject,
                          clusters: Mapping[str, JsonObject]) -> list[str]:
    faults = [f"location {span['path']}:{span['line_start']}-{span['line_end']} lies outside "
              "its file" for span in objects(row["locations"]) if not span_fits(check, span)]
    if len(group_locations(row, clusters)) < 2:
        faults.append("a group needs at least two locations")
    source = cast(JsonObject, row["normative_source"])
    if not section_valid(check, str(source["path"]), str(source["section"])):
        faults.append("the normative source names no inventory path and section")
    return faults


def group_references(check: Verification, row: JsonObject,
                     clusters: Mapping[str, JsonObject]) -> Iterator[Diagnostic]:
    location = check.at(str(row["id"]))
    for cluster_id in cast(list[str], row["clusters"]):
        if cluster_id not in clusters:
            yield Diagnostic("reference-unknown", location, f"cluster {cluster_id} does not exist")
    if row["finding"] is not None and row["finding"] not in check.findings:
        yield Diagnostic("reference-unknown", location, f"finding {row['finding']} does not exist")


def group_rules(check: Verification) -> Iterator[Diagnostic]:
    clusters = {str(item["id"]): item for item in objects(check.inv["duplicate_clusters"])}
    membership: dict[str, set[str]] = {cluster_id: set() for cluster_id in clusters}
    for row in check.rows("duplicate_groups"):
        yield from group_references(check, row, clusters)
        for message in group_role_faults(row) + group_location_faults(check, row, clusters):
            yield Diagnostic("group-invalid", check.at(str(row["id"])), message)
        for cluster_id in cast(list[str], row["clusters"]):
            membership.get(cluster_id, set()).add(str(row["id"]))
    for cluster_id, groups in membership.items():
        if not groups:
            yield Diagnostic("duplicate-ungrouped", check.inventory_at(cluster_id), "in no group")
        elif len(groups) > 1:
            yield Diagnostic("duplicate-multigrouped", check.inventory_at(cluster_id),
                             f"in groups {', '.join(sorted(groups))}")


def blocks_spec09(check: Verification, finding: JsonObject) -> bool:
    """The blocking predicate: cited by an amendment, a contradiction, or an audited gap."""
    kind = finding["type"]
    return (finding["id"] in check.cited or kind == "contradiction"
            or (kind == "coverage-gap" and finding["source"] in check.files))


def ownership_faults(check: Verification, finding: JsonObject) -> list[str]:
    kind, owner = str(finding["type"]), finding["owner"]
    faults: list[str] = []
    if owner not in FINDING_OWNERS[kind]:
        faults.append(f"owner {owner} is not allowed for {kind}")
    if finding["blocks_09"] != blocks_spec09(check, finding):
        faults.append("blocks_09 differs from the blocking predicate")
    if finding["severity"] == "blocker" and finding["blocks_09"] is not True:
        faults.append("severity blocker needs blocks_09 true")
    if kind == "accepted-observation" and (finding["severity"] != "minor" or finding["blocks_09"]):
        faults.append("an accepted observation is minor and does not block")
    if finding["status"] not in ("open", "historical-fixed"):
        faults.append(f"status \"{finding['status']}\" is not open or historical-fixed")
    return faults


def source_faults(check: Verification, finding: JsonObject) -> list[str]:
    source = str(finding["source"])
    entry = check.entry(source)
    if entry is None:
        return [f"source {source} is not an inventory path"]
    limit = number(entry["lines"])
    faults = [f"line {line} lies outside the source" for line in cast(list[int], finding["lines"])
              if not 1 <= line <= limit]
    if not section_valid(check, source, str(finding["section"])):
        faults.append(f"section \"{finding['section']}\" is not a section of the source")
    return faults


def evidence_faults(finding: JsonObject) -> list[str]:
    evidence = cast(list[str], finding["evidence"])
    faults = [] if evidence else ["evidence is empty"]
    faults += [f"evidence \"{item}\" is not path:line, a path or an amendment id"
               for item in evidence if not (EVIDENCE_LINE_RE.fullmatch(item)
                                            or AMENDMENT_ID_RE.fullmatch(item)
                                            or is_repository_path(item))]
    return faults


def edge_faults(check: Verification, finding: JsonObject) -> list[str]:
    keys = [edge_key(ref) for ref in objects(finding["edges"])]
    faults = [f"edge {source}:{line}:{column} is not a defect edge"
              for source, line, column in keys if (source, line, column) not in check.defects]
    outside = any(check.defects[key]["in_spec09_grammar"] is False
                  for key in keys if key in check.defects)
    migration_owned = finding["owner"] == "09" and "09" in FINDING_OWNERS[str(finding["type"])]
    cites_amendment = any(AMENDMENT_ID_RE.fullmatch(item)
                          for item in cast(list[str], finding["evidence"]))
    if migration_owned and outside and not cites_amendment:
        faults.append("a 09-owned finding on an edge outside the migration grammar cites "
                      "no amendment in its evidence")
    return faults


def finding_rules(check: Verification) -> Iterator[Diagnostic]:
    for finding_id, finding in check.findings.items():
        location = check.at(finding_id)
        for message in (ownership_faults(check, finding) + source_faults(check, finding)
                        + evidence_faults(finding) + edge_faults(check, finding)):
            yield Diagnostic("finding-invalid", location, message)
        entry = check.entry(str(finding["source"]))
        if entry is not None and finding["sha256"] != entry["sha256"]:
            yield Diagnostic("finding-stale", location, "sha256 differs from its source")
        for item in cast(list[str], finding["evidence"]):
            if AMENDMENT_ID_RE.fullmatch(item) and item not in check.amendment_ids:
                yield Diagnostic("reference-unknown", location, f"amendment {item} does not exist")


def defect_rules(check: Verification) -> Iterator[Diagnostic]:
    named = {edge_key(ref) for finding in check.findings.values()
             for ref in objects(finding["edges"])}
    for (source, line, column), edge in sorted(check.defects.items()):
        if (source, line, column) not in named:
            yield Diagnostic("defect-unrecorded", f"{source}:{line}",
                             f"the {edge['status']} edge at column {column} is in no finding")


def coverage_rules(check: Verification) -> Iterator[Diagnostic]:
    gaps = {str(finding["source"]) for finding in check.findings.values()
            if finding["type"] == "coverage-gap"}
    for path, (index, row) in first_rows(check, "coverage").items():
        is_file, status = check.files[path]["entry"] == "file", row["status"]
        location = check.at(f"coverage[{index}]")
        if is_file and status == "not-a-file":
            yield Diagnostic("coverage-inconsistent", location, "not-a-file for a regular file")
        elif not is_file and status != "not-a-file":
            yield Diagnostic("coverage-inconsistent", location, "a non-file needs not-a-file")
        if status in GAP_STATUSES and path not in gaps:
            yield Diagnostic("coverage-inconsistent", location,
                             f"{status} needs a coverage-gap finding on {path}")


def installed_faults(check: Verification, row: JsonObject) -> list[str]:
    faults = [] if str(row["location"]).startswith("~/") else ["the location does not start ~/"]
    entry = check.files.get(str(row["path"]))
    if entry is None:
        faults.append(f"{row['path']} is not an audited path")
    elif row["source_sha256"] != entry["sha256"]:
        faults.append("source_sha256 differs from the inventory")
    return faults


def installed_rules(check: Verification) -> Iterator[Diagnostic]:
    entries = check.rows("installed")
    if check.doc["installed_access"] == "not-verified" and entries:
        yield Diagnostic("installed-invalid", check.at("installed"),
                         "entries are listed although installed_access is not-verified")
    for index, row in enumerate(entries):
        for message in installed_faults(check, row):
            yield Diagnostic("installed-invalid", check.at(f"installed[{index}]"), message)


# ---------------------------------------------------------------------------
# Verify: the migration specification and the statement units of the discovery rule
# ---------------------------------------------------------------------------

SPEC09_DIRECTORY = ".ai/specs"
SPEC09_NAME_RE = re.compile(r"09-.*\.md", re.DOTALL)
SPEC09_ANY = f"{SPEC09_DIRECTORY}/09-*.md"
SPEC09_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]+")
DISCOVERY_RULE = "rules/phase-discovery.md"
COVERAGE_SECTIONS = ("## Codebase Reading Rules", "## Decision Protocol")
LIST_ITEM_RE = re.compile(r"\s*([-*+]|\d+[.)])\s")


@dataclass(frozen=True)
class MigrationText:
    """The migration specification: its text, whole tokens, `###` headings and table rows."""

    text: str
    tokens: frozenset[str]
    notes: frozenset[str]
    table_rows: tuple[str, ...]


def migration_text(text: str) -> MigrationText:
    lines = [matching_text(line) for line in text.split("\n")]
    return MigrationText(text, frozenset(SPEC09_TOKEN_RE.findall(text)),
                         frozenset(line[4:] for line in lines if line.startswith("### ")),
                         tuple(line for line in lines if line.startswith("| ")))


def spec09_matches(root: Path) -> list[str]:
    """Names of the non-directory entries of the specification directory that match
    `09-*.md`; raises ValueError when that directory is absent, a link or unreadable."""
    directory = root / SPEC09_DIRECTORY
    try:
        if not is_real_directory(directory):
            raise ValueError("the specification directory is absent or a symbolic link")
        with os.scandir(directory) as iterator:
            return sorted(entry.name for entry in iterator
                          if SPEC09_NAME_RE.fullmatch(entry.name)
                          and not entry.is_dir(follow_symlinks=False))
    except OSError as error:
        raise ValueError(f"the specification directory cannot be listed ({error.strerror})"
                         ) from None


def read_spec09(path: Path) -> str:
    """The strict UTF-8 text of a regular file; raises ValueError naming why it is unusable."""
    try:
        if entry_kind(path) == "symlink":
            raise ValueError("is a symbolic link and is not followed")
        data = read_regular_file(path)
    except OSError as error:
        raise ValueError(f"cannot be read ({error.strerror})") from None
    except ToolError:
        raise ValueError("is not a regular file") from None
    text = decode_strict(data)
    if text is None:
        raise ValueError("is not valid UTF-8")
    return text


def load_migration(root: Path) -> tuple[MigrationText | None, list[Diagnostic]]:
    """The single migration specification under the root, or one spec09-unavailable."""
    try:
        names = spec09_matches(root)
    except ValueError as error:
        return None, [Diagnostic("spec09-unavailable", f"{SPEC09_ANY}:0", str(error))]
    if len(names) != 1:
        reason = "no file matches" if not names else f"{len(names)} files match"
        return None, [Diagnostic("spec09-unavailable", f"{SPEC09_ANY}:0", reason)]
    relative = f"{SPEC09_DIRECTORY}/{names[0]}"
    try:
        return migration_text(read_spec09(root / relative)), []
    except ValueError as error:
        return None, [Diagnostic("spec09-unavailable", f"{relative}:0", f"the file {error}")]


def section_units(lines: Sequence[Line]) -> set[int]:
    """Unit start lines of one section body: list items, table rows other than the
    separator, fence openings (a fenced block is one unit) and the first non-blank line
    after a blank line or after the heading."""
    starts: set[int] = set()
    fence: str | None = None
    after_blank = True
    for line in lines:
        text = line.text
        if fence is not None:
            fence = None if closes_fence(text, fence) else fence
            continue
        if not text.strip():
            after_blank = True
            continue
        opening = FENCE_OPEN_RE.match(text)
        row = text.strip()
        is_row = row.startswith("|") and TABLE_SEPARATOR_RE.fullmatch(row) is None
        if after_blank or opening or is_row or LIST_ITEM_RE.match(text):
            starts.add(line.number)
        fence = opening.group(1) if opening else None
        after_blank = False
    return starts


def statement_units(model: TextModel) -> frozenset[int]:
    """Unit start lines of the two coverage sections of the discovery rule."""
    level_two = [heading for heading in model.headings if heading.level == 2]
    units: set[int] = set()
    for index, heading in enumerate(level_two):
        if heading.text in COVERAGE_SECTIONS:
            end = level_two[index + 1].line - 1 if index + 1 < len(level_two) else len(model.lines)
            units |= section_units(model.lines[heading.line:end])
    return frozenset(units)


def discovery_units(root: Path) -> frozenset[int]:
    """Statement units of the discovery rule in the root; none when it is absent, not a
    regular file, or not decodable text."""
    path = root / DISCOVERY_RULE
    try:
        if entry_kind(path) != "file":
            return frozenset()
    except (FileNotFoundError, NotADirectoryError):
        return frozenset()
    data = read_regular_file(path)
    if encoding_of(data)[1] is None:
        return frozenset()
    return statement_units(build_text_model(data))


# ---------------------------------------------------------------------------
# Verify: the migration map
# ---------------------------------------------------------------------------

KIND_PREFIXES = ("bootstrap-", "contract-", "protocol-", "procedure-")
CONDUCT_RULE = "rules/protocol-discovery-conduct.md"
AUTONOMOUS_RULE = "rules/protocol-autonomous-decision.md"


def mapped_rows(check: Verification) -> dict[str, tuple[int, JsonObject]]:
    return first_rows(check, "map", "source")


def targets_of(row: JsonObject) -> list[JsonObject]:
    return objects(row["targets"])


def target_owners(check: Verification) -> dict[str, set[str]]:
    """Every target path of the checked entries with the sources that name it."""
    owners: dict[str, set[str]] = {}
    for source, (_, row) in mapped_rows(check).items():
        for target in targets_of(row):
            owners.setdefault(str(target["path"]), set()).add(source)
    return owners


def source_headings(check: Verification, source: str) -> list[str]:
    return [str(item["heading"]) for item in objects(check.files[source]["sections"])]


def parent_of(path: str) -> str:
    return path.rpartition("/")[0]


def decision_fits(source: str, row: JsonObject, owners: Mapping[str, set[str]]) -> bool:
    paths = [str(target["path"]) for target in targets_of(row)]
    decision, single = row["decision"], len(paths) == 1
    if decision == "keep":
        return single and paths[0] == source
    if decision == "rename":
        return single and parent_of(paths[0]) == parent_of(source) and paths[0] != source
    if decision == "move":
        return single and parent_of(paths[0]) != parent_of(source)
    if decision == "split":
        return len(paths) >= 2
    return single and len(owners.get(paths[0], ())) > 1


def shape_faults(check: Verification, source: str, row: JsonObject,
                 owners: Mapping[str, set[str]]) -> list[str]:
    targets = targets_of(row)
    if not targets:
        return ["the entry has no target"]
    paths = [str(target["path"]) for target in targets]
    faults = [] if decision_fits(source, row, owners) else [
        f"the targets do not have the shape of a {row['decision']} decision"]
    if len(set(paths)) != len(paths):
        faults.append("a target path is listed twice")
    headings = set(source_headings(check, source))
    for target in targets:
        reason, listed = target["merge_reason"], target["sections"]
        if isinstance(reason, str) and not reason.strip():
            faults.append(f"the merge_reason of {target['path']} is blank")
        if row["decision"] != "split" and isinstance(listed, list) and not set(listed) <= headings:
            faults.append(f"the sections of {target['path']} are not headings of the source")
    return faults


def shape_rules(check: Verification) -> Iterator[Diagnostic]:
    owners = target_owners(check)
    for source, (index, row) in mapped_rows(check).items():
        for message in shape_faults(check, source, row, owners):
            yield Diagnostic("map-invalid", check.at(f"map[{index}]"), message)


def split_rules(check: Verification) -> Iterator[Diagnostic]:
    for source, (index, row) in mapped_rows(check).items():
        if row["decision"] != "split":
            continue
        listed = sorted(str(heading) for target in targets_of(row)
                        if isinstance(target["sections"], list) for heading in target["sections"])
        if listed != sorted(source_headings(check, source)):
            yield Diagnostic("split-sections-incomplete", check.at(f"map[{index}]"),
                             "the targets do not hold every section of the source exactly once")


def collision_rules(check: Verification) -> Iterator[Diagnostic]:
    owners = target_owners(check)
    for source, (index, row) in mapped_rows(check).items():
        for target in targets_of(row):
            path = str(target["path"])
            if len(owners[path]) > 1 and target["merge_reason"] is None:
                yield Diagnostic("map-collision", check.at(f"map[{index}]"),
                                 f"{path} is shared and has no merge_reason here")


def installed_name(path: str) -> str | None:
    """`rule-<stem>` for a top-level rule, `<stem>` for a top-level workflow, else None."""
    rule = RULE_FILE_RE.fullmatch(path)
    if rule is not None:
        return f"rule-{rule.group(1)}"
    workflow = WORKFLOW_FILE_RE.fullmatch(path)
    return workflow.group(1) if workflow is not None else None


def entry_target_rule(check: Verification, code: str, faulty: Mapping[str, str]
                      ) -> Iterator[Diagnostic]:
    """One diagnostic per checked entry and distinct target path listed in `faulty`."""
    for _, (index, row) in mapped_rows(check).items():
        for path in sorted({str(target["path"]) for target in targets_of(row)}):
            if path in faulty:
                yield Diagnostic(code, check.at(f"map[{index}]"), faulty[path])


def installed_name_rules(check: Verification) -> Iterator[Diagnostic]:
    folded: dict[str, set[str]] = {}
    for path in target_owners(check):
        name = installed_name(path)
        if name is not None:
            folded.setdefault(name.casefold(), set()).add(path)
    faulty = {path: f"the installed name of {path} equals that of "
                    f"{', '.join(sorted(paths - {path}))} under casefolding"
              for paths in folded.values() if len(paths) > 1 for path in paths}
    yield from entry_target_rule(check, "installed-name-collision", faulty)


def stem_rules(check: Verification) -> Iterator[Diagnostic]:
    paths = target_owners(check)
    rules = {match.group(1) for path in paths if (match := RULE_FILE_RE.fullmatch(path))}
    workflows = {match.group(1) for path in paths if (match := WORKFLOW_FILE_RE.fullmatch(path))}
    faulty: dict[str, str] = {}
    for stem in rules & workflows:
        for path in (f"rules/{stem}.md", f"workflows/{stem}.md"):
            faulty[path] = f"the stem {stem} is both a rule and a workflow"
    yield from entry_target_rule(check, "stem-overlap", faulty)


def prefix_rules(check: Verification) -> Iterator[Diagnostic]:
    faulty = {path: f"the rule {path} has no kind prefix" for path in target_owners(check)
              if (match := RULE_FILE_RE.fullmatch(path))
              and not match.group(1).startswith(KIND_PREFIXES)}
    yield from entry_target_rule(check, "kind-prefix-invalid", faulty)


# ---------------------------------------------------------------------------
# Verify: deviation from the migration defaults
# ---------------------------------------------------------------------------

def compared_targets(check: Verification, source: str, row: JsonObject) -> list[JsonObject]:
    """The targets, with the autonomous-decision rule read as the conduct rule it replaces
    when the discovery rule's statements are covered."""
    targets = targets_of(row)
    defaults = {str(item["path"]) for item in objects(row["spec09_default"])}
    paths = {str(target["path"]) for target in targets}
    if (source == DISCOVERY_RULE and check.doc["req21"]["verdict"] == "covered"
            and CONDUCT_RULE in defaults and CONDUCT_RULE not in paths):
        return [target | {"path": CONDUCT_RULE} if target["path"] == AUTONOMOUS_RULE else target
                for target in targets]
    return targets


def deviates(check: Verification, source: str, row: JsonObject) -> bool:
    if row["spec09_default"] is None:
        return True
    defaults = objects(row["spec09_default"])
    targets = compared_targets(check, source, row)
    default_paths = {str(item["path"]) for item in defaults}
    target_paths = {str(item["path"]) for item in targets}
    optional = {str(path) for path in cast(list[str], row["spec09_optional"])}
    if not default_paths <= target_paths or not target_paths - default_paths <= optional:
        return True
    return any(listed_sections(targets, str(default["path"])) != sorted(default["sections"])
               for default in defaults if default["sections"] is not None)


def listed_sections(targets: Sequence[JsonObject], path: str) -> list[str]:
    """The sections that the targets with one path list together, in sorted order."""
    return sorted(str(heading) for target in targets
                  if target["path"] == path and isinstance(target["sections"], list)
                  for heading in target["sections"])


def deviation_rules(check: Verification) -> Iterator[Diagnostic]:
    for source, (index, row) in mapped_rows(check).items():
        amendment, location = row["amendment"], check.at(f"map[{index}]")
        known = amendment in check.amendment_ids
        if amendment is not None and not known:
            yield Diagnostic("reference-unknown", location, f"amendment {amendment} does not exist")
        if not known and deviates(check, source, row):
            yield Diagnostic("deviation-unamended", location,
                             "the targets deviate from the migration default without an amendment")


# ---------------------------------------------------------------------------
# Verify: amendments
# ---------------------------------------------------------------------------

NEW_TARGETS = ("new-REQ", "new-AC")
IDENTIFIER_TARGET_RE = re.compile(r"(REQ|AC|DM|A|Q)-\d+")
CRITERION_ID_RE = re.compile(r"AC-\d+")
FINDING_ID_RE = re.compile(r"AUD-08-\d{3}")
NOTES_PREFIX = "Notes:"
TERMINOLOGY_PREFIX = "Terminology:"


def target_exists(migration: MigrationText, target: str) -> bool:
    """Whether a target satisfies one of the amendment target forms against the text."""
    if IDENTIFIER_TARGET_RE.fullmatch(target):
        return target in migration.tokens
    if target.startswith(NOTES_PREFIX):
        heading = target[len(NOTES_PREFIX):]
        return bool(heading) and heading in migration.notes
    if target.startswith(TERMINOLOGY_PREFIX):
        term = target[len(TERMINOLOGY_PREFIX):]
        return bool(term) and any(row.startswith(f"| {term} |") for row in migration.table_rows)
    return False


def current_faults(migration: MigrationText | None, row: JsonObject) -> list[str]:
    current = row["current"]
    if row["target"] in NEW_TARGETS:
        return [] if current is None else ["a new requirement or criterion has no current text"]
    if current is None:
        return ["current is null for an existing target"]
    if migration is not None and current not in migration.text:
        return ["current is not the exact text of the migration specification"]
    return []


def amendment_faults(migration: MigrationText | None, row: JsonObject) -> list[str]:
    evidence = cast(list[str], row["evidence"])
    faults = [] if evidence else ["evidence is empty"]
    faults += [f'evidence "{item}" is not a finding id or path:line' for item in evidence
               if not (FINDING_ID_RE.fullmatch(item) or EVIDENCE_LINE_RE.fullmatch(item))]
    faults += current_faults(migration, row)
    faults += [f"{key} is blank" for key in ("proposed", "reason") if not str(row[key]).strip()]
    faults += [f'affected "{item}" is not an acceptance criterion id'
               for item in cast(list[str], row["affected"]) if not CRITERION_ID_RE.fullmatch(item)]
    return faults


def target_faults(migration: MigrationText, row: JsonObject) -> list[str]:
    target = str(row["target"])
    faults = [] if target in NEW_TARGETS or target_exists(migration, target) else [
        f'target "{target}" is not found in the migration specification']
    faults += [f"affected {item} is not a whole token of the migration specification"
               for item in cast(list[str], row["affected"])
               if CRITERION_ID_RE.fullmatch(item) and item not in migration.tokens]
    return faults


def amendment_references(check: Verification, row: JsonObject) -> list[str]:
    missing = [f"finding {item} does not exist" for item in cast(list[str], row["evidence"])
               if FINDING_ID_RE.fullmatch(item) and item not in check.findings]
    return missing + [f"amendment {item} does not exist"
                      for item in cast(list[str], row["depends_on"])
                      if item not in check.amendment_ids]


def amendment_rules(check: Verification) -> Iterator[Diagnostic]:
    for row in check.rows("amendments"):
        location = check.at(str(row["id"]))
        for message in amendment_faults(check.migration, row):
            yield Diagnostic("amendment-invalid", location, message)
        if check.migration is not None:
            for message in target_faults(check.migration, row):
                yield Diagnostic("amendment-target-unknown", location, message)
        for message in amendment_references(check, row):
            yield Diagnostic("reference-unknown", location, message)


# ---------------------------------------------------------------------------
# Verify: statement coverage of the discovery rule
# ---------------------------------------------------------------------------

STATEMENT_SOURCE_RE = re.compile(re.escape(DISCOVERY_RULE) + r":([1-9]\d{0,8})")


def statement_line(source: str) -> int | None:
    found = STATEMENT_SOURCE_RE.fullmatch(source)
    return int(found.group(1)) if found is not None else None


def statement_rules(check: Verification) -> Iterator[Diagnostic]:
    record = cast(JsonObject, check.doc["req21"])
    statements = objects(record["statements"])
    seen: set[int] = set()
    for index, item in enumerate(statements):
        line, location = statement_line(str(item["source"])), check.at(f"req21.statements[{index}]")
        if line is None or line not in check.units:
            yield Diagnostic("req21-invalid", location,
                             f"{item['source']} is not a statement unit of the two sections")
        elif line in seen:
            yield Diagnostic("req21-invalid", location, f"{item['source']} is listed twice")
        if line is not None:
            seen.add(line)
    for line in sorted(check.units - seen):
        yield Diagnostic("req21-invalid", f"{DISCOVERY_RULE}:{line}",
                         "the statement unit has no statement")
    covered = all(item["covered_by"] is not None for item in statements)
    if (record["verdict"] == "covered") != covered:
        yield Diagnostic("req21-invalid", check.at("req21"),
                         "the verdict contradicts the covered_by values")


def strings_in(value: object) -> Iterator[str]:
    """Every string in a JSON value in document order, walked with an explicit stack."""
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, str):
            yield item
        elif isinstance(item, dict):
            pending.extend(reversed(list(item.values())))
        elif isinstance(item, list):
            pending.extend(reversed(item))


def economic_claims(location: str, value: object) -> Iterator[Diagnostic]:
    for text in strings_in(value):
        for pattern in ECONOMICS_PATTERNS:
            found = pattern.search(text)
            if found is not None:
                yield Diagnostic("economics-claim", location,
                                 f'names an amount: "{found.group(0)}"')
                break


def economics_rules(check: Verification) -> Iterator[Diagnostic]:
    for key, value in check.doc.items():
        if isinstance(value, list):
            for index, item in enumerate(value):
                yield from economic_claims(check.at(entry_location(key, index, item)), item)
        else:
            yield from economic_claims(check.at(key), value)


ASSESSMENT_RULES: tuple[Callable[[Verification], Iterable[Diagnostic]], ...] = (
    digest_rule, row_rules, stale_row_rules, section_rules, repetition_rules, load_rules,
    candidate_rules, legacy_rules, group_rules, finding_rules, defect_rules, coverage_rules,
    installed_rules, shape_rules, split_rules, collision_rules, installed_name_rules,
    stem_rules, prefix_rules, deviation_rules, amendment_rules, statement_rules,
    economics_rules,
)


# ---------------------------------------------------------------------------
# Render: the generated region of the report
# ---------------------------------------------------------------------------

REPORT_BEGIN = "<!-- audit:generated:begin -->"
REPORT_END = "<!-- audit:generated:end -->"
CELL_BREAKING_CATEGORIES = frozenset({"Cc", "Zl", "Zp"})
READER_CLASSES = ("active", "frozen", "planning", "history")
IMPACT_CONTEXTS = ("text", "check-description", "comment")
IMPACT_GROUPS = (*IMPACT_CONTEXTS, "tests", "frozen", "hooks", "active")
SCOPE_TEXT = (
    "primary {primary} (`rules/`, `workflows/`); adapter {adapter} (`harness/`, "
    "`templates/codex-global-AGENTS.md`); readers {readers} (active {active}, "
    "frozen {frozen}, planning {planning}, history {history}); excluded "
    "`docs/audits/*-rules-workflows-audit.md`, "
    "`docs/audits/*-rules-workflows-audit.inventory.json`, "
    "`docs/audits/*-rules-workflows-audit.assessment.json`, "
    "`scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`; skipped "
    "`.git/`, `logs/`, `output/`, `__pycache__/`, `*.pyc`")
TABLE_HEADERS: dict[str, tuple[str, ...]] = {
    "Inventory": ("Path", "Set", "Entry", "Tracked", "Words", "Bytes", "Kinds", "Coverage",
                  "Decision", "Findings"),
    "Sections": ("Path", "Section", "Line", "Words", "Bytes", "Kind", "Proposed home"),
    "References": ("Class", *EDGE_STATUSES),
    "Defect edges": ("Source:line:column", "Raw", "Form", "Context", "Status", "Candidates",
                     "Findings"),
    "Loads": ("Source:line", "Targets", "Mode", "Condition"),
    "Repeated loads": ("ID", "Caller", "Callee", "Target", "Disposition", "Finding"),
    "Line candidates": ("ID", "Source:line", "Text", "Disposition", "Finding"),
    "Repetition review": ("Workflow", "Report findings", "Checkpoint findings",
                          "Review findings"),
    "Legacy mentions": ("Source:line", "Term", "Role", "Note"),
    "Duplicates": ("Group", "Clusters", "Locations", "Normative source",
                   "Condition differences", "Disposition", "Owner", "Finding"),
    "Migration map": ("Source", "Decision", "Targets", "Spec 09 default", "Deviation",
                      "Amendment"),
    "Validator and test impact": ("Source", "Decision", "Validator text",
                                  "Validator check-description", "Validator comment",
                                  "Other tests", "Frozen", "Hooks", "Other active"),
    "Spec 09 inputs": ("Source", "Decision", "Targets", "Amendment"),
    "Statements": ("Statement", "Text", "Covered by"),
    "Findings": ("ID", "Type", "Severity", "Source", "Section", "Owner", "Blocks 09",
                 "Status", "Observation", "Closure"),
    "Amendments to spec 09": ("ID", "Target", "Change", "Proposed", "Reason", "Evidence",
                              "Affected", "Depends on", "Requires ADR", "Disposition"),
    "Read coverage": ("Path", "Status", "SHA-256", "Reader"),
    "Installed comparison": ("Path", "Location", "Source SHA-256", "Installed SHA-256",
                             "Match"),
}

Rows = list[list[object]]
Body = list[str]
Position = tuple[str, int, int]


def cell(value: object) -> str:
    """Cell text: `-` for null, true or false, `none` for an empty list, list items joined
    by commas, `|` escaped and every line-breaking or control character a space."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(cell(item) for item in value) if value else "none"
    text = "".join(" " if unicodedata.category(character) in CELL_BREAKING_CATEGORIES
                   else character for character in str(value))
    return text.replace("|", "\\|")


def table_row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def table(name: str, rows: Rows) -> Body:
    """A table with its header and separator rows, even when it has no other row."""
    header = TABLE_HEADERS[name]
    return [table_row(header), "|" + "---|" * len(header),
            *(table_row([cell(value) for value in row]) for row in rows)]


def first_by(rows: object, key: Callable[[JsonObject], object]) -> dict[object, JsonObject]:
    """The first row for each key value, in row order."""
    found: dict[object, JsonObject] = {}
    for row in objects(rows):
        found.setdefault(key(row), row)
    return found


def position(item: Mapping[str, object]) -> Position:
    return str(item["source"]), number(item["line"]), number(item["column"])


def target_text(target: JsonObject) -> str:
    sections = target["sections"]
    if not isinstance(sections, list):
        return str(target["path"])
    return f"{target['path']} [{', '.join(str(item) for item in sections)}]"


def targets_text(targets: object) -> str | None:
    if targets is None:
        return None
    return "; ".join(target_text(item) for item in objects(targets)) or "none"


def by_field(rows: object, field: str) -> list[JsonObject]:
    return sorted(objects(rows), key=lambda row: str(row[field]))


def passport_body(check: Verification) -> Body:
    inv, doc = check.inv, check.doc
    gaps = sum(1 for row in check.rows("coverage") if row["status"] in GAP_STATUSES)
    findings = check.rows("findings")
    opened = sum(1 for item in findings if item["status"] == "open")
    blocking = sum(1 for item in findings if item["blocks_09"] is True)
    sets = {name: sum(1 for entry in check.files.values() if entry["set"] == name)
            for name in ("primary", "adapter")}
    classes = {name: sum(1 for entry in check.readers.values() if entry["class"] == name)
               for name in READER_CLASSES}
    scope = SCOPE_TEXT.format(readers=len(check.readers), **sets, **classes)
    environment = "; ".join(cell(value) for value in cast(JsonObject,
                                                          doc["environment"]).values())
    worktree = cast(JsonObject, inv["worktree"])
    coverage = "complete" if not gaps else f"partial ({gaps} gaps)"
    return [
        f"- source_revision: {cell(inv['source_revision'])}",
        f"- worktree: {cell(worktree['state'])}",
        f"- inventory_digest: {cell(inv['inventory_digest'])}",
        f"- method_version: {cell(inv['method_version'])}",
        f"- scope: {scope}",
        f"- installed_access: {cell(doc['installed_access'])}",
        f"- read_coverage: {coverage}",
        f"- findings: {len(findings)} total, {opened} open, {blocking} blocking spec 09",
        f"- run_date: {cell(doc['run_date'])}",
        f"- environment: {environment}",
    ]


def finding_ids_by_source(check: Verification) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for item in check.rows("findings"):
        found.setdefault(str(item["source"]), []).append(str(item["id"]))
    return {source: sorted(ids) for source, ids in found.items()}


def inventory_body(check: Verification) -> Body:
    files_rows = first_by(check.doc["files"], lambda row: row["path"])
    coverage = first_by(check.doc["coverage"], lambda row: row["path"])
    mapped = first_by(check.doc["map"], lambda row: row["source"])
    findings = finding_ids_by_source(check)
    rows: Rows = []
    for path, entry in check.files.items():
        files_row, covered, entry_map = files_rows.get(path), coverage.get(path), mapped.get(path)
        rows.append([path, entry["set"], entry["entry"], entry["tracked"], entry["words"],
                     entry["bytes"], files_row["kinds"] if files_row else None,
                     covered["status"] if covered else None,
                     entry_map["decision"] if entry_map else None, findings.get(path, [])])
    return table("Inventory", rows)


def sections_body(check: Verification) -> Body:
    files_rows = first_by(check.doc["files"], lambda row: row["path"])
    rows: Rows = []
    for path, entry in check.files.items():
        files_row = files_rows.get(path)
        listed = first_by(files_row["sections"] if files_row else None,
                          lambda row: row["heading"])
        for section in objects(entry["sections"]):
            match = listed.get(section["heading"])
            rows.append([path, section["heading"], section["line"], section["words"],
                         section["bytes"], match["kind"] if match else None,
                         match["proposed_home"] if match else None])
    return table("Sections", rows)


def naming_findings(check: Verification) -> dict[Position, list[str]]:
    """The ids of the findings that name each edge position."""
    found: dict[Position, list[str]] = {}
    for item in check.rows("findings"):
        for edge_ref in objects(item["edges"]):
            found.setdefault(position(edge_ref), []).append(str(item["id"]))
    return {key: sorted(set(ids)) for key, ids in found.items()}


def edge_target_text(target: JsonObject) -> str:
    status = target["heading_status"]
    return str(target["path"]) + (f" ({status})" if status else "")


def references_body(check: Verification) -> Body:
    edges = objects(check.inv["edges"])
    counts: dict[tuple[str, str], int] = {}
    for item in edges:
        key = (str(item["class"]), str(item["status"]))
        counts[key] = counts.get(key, 0) + 1
    count_rows: Rows = [[name, *(counts.get((name, status), 0) for status in EDGE_STATUSES)]
                        for name in READER_CLASSES]
    named = naming_findings(check)
    defect_rows: Rows = [
        ["{}:{}:{}".format(*position(item)), item["raw"], item["form"], item["context"],
         item["status"], [edge_target_text(target) for target in objects(item["targets"])],
         named.get(position(item), [])]
        for item in edges if is_defect_edge(item)]
    return table("References", count_rows) + [""] + table("Defect edges", defect_rows)


def loads_body(check: Verification) -> Body:
    loads = first_by(check.doc["loads"], position)
    rows: Rows = []
    for item in objects(check.inv["edges"]):
        if item["load"] is True and item["source"] in check.files:
            row = loads.get(position(item))
            rows.append([f"{item['source']}:{item['line']}",
                         [target["path"] for target in objects(item["targets"])],
                         row["mode"] if row else None, row["condition"] if row else None])
    return table("Loads", rows)


def dispositions(check: Verification) -> Callable[[object], list[object]]:
    candidates = first_by(check.doc["candidates"], lambda row: row["id"])

    def of(identifier: object) -> list[object]:
        row = candidates.get(identifier)
        return [row["disposition"], row["finding"]] if row else [None, None]
    return of


def repeated_loads_body(check: Verification) -> Body:
    of = dispositions(check)
    return table("Repeated loads", [
        [item["id"], item["caller"], item["callee"], item["target"], *of(item["id"])]
        for item in objects(check.inv["repeat_loads"])])


def line_candidates_body(check: Verification, key: str) -> Body:
    of = dispositions(check)
    return table("Line candidates", [
        [item["id"], f"{item['source']}:{item['line']}", item["text"], *of(item["id"])]
        for item in objects(check.inv[key])])


def repetition_body(check: Verification) -> Body:
    files_rows = first_by(check.doc["files"], lambda row: row["path"])
    rows: Rows = []
    for path, entry in check.files.items():
        if WORKFLOW_FILE_RE.fullmatch(path) and number(entry["invocation_lines"]) > 0:
            files_row = files_rows.get(path)
            repetition = files_row["repetition"] if files_row else None
            rows.append([path, *(cast(JsonObject, repetition)[key] if repetition else None
                                 for key, _ in REPETITION_TYPES)])
    return table("Repetition review", rows)


def legacy_body(check: Verification) -> Body:
    roles = first_by(check.doc["legacy"], position)
    rows: Rows = []
    for item in objects(check.inv["legacy_mentions"]):
        row = roles.get(position(item))
        rows.append([f"{item['source']}:{item['line']}", item["term"],
                     row["role"] if row else None, row["note"] if row else None])
    return table("Legacy mentions", rows)


def span_text(span: JsonObject) -> str:
    return f"{span['path']}:{span['line_start']}-{span['line_end']}"


def duplicates_body(check: Verification) -> Body:
    clusters = first_by(check.inv["duplicate_clusters"], lambda row: row["id"])
    rows: Rows = []
    for group in by_field(check.doc["duplicate_groups"], "id"):
        members = [member for identifier in cast(list[object], group["clusters"])
                   if identifier in clusters
                   for member in objects(clusters[identifier]["members"])]
        normative = cast(JsonObject, group["normative_source"])
        rows.append([group["id"], group["clusters"],
                     [span_text(span) for span in members + objects(group["locations"])],
                     f"{normative['path']} → {normative['section']}",
                     group["condition_differences"], group["disposition"], group["owner"],
                     group["finding"]])
    return table("Duplicates", rows)


def map_body(check: Verification) -> Body:
    return table("Migration map", [
        [row["source"], row["decision"], targets_text(row["targets"]),
         targets_text(row["spec09_default"]),
         "yes" if deviates(check, str(row["source"]), row) else "no", row["amendment"]]
        for row in by_field(check.doc["map"], "source")])


def impact_group(item: JsonObject) -> str | None:
    """The impact column of an edge: validator context, other tests, frozen, hooks or
    other active; planning and history edges have none."""
    source, reader_class = str(item["source"]), item["class"]
    if source == VALIDATOR_PATH:
        return str(item["context"]) if item["context"] in IMPACT_CONTEXTS else None
    if reader_class == "frozen":
        return "frozen"
    if reader_class != "active":
        return None
    if source.startswith("tests/"):
        return "tests"
    return "hooks" if source.startswith("hooks/") else "active"


def impact_counts(check: Verification) -> dict[str, dict[str, int]]:
    """For each target path, the number of edges naming it in each impact column."""
    counts: dict[str, dict[str, int]] = {}
    for item in objects(check.inv["edges"]):
        group = impact_group(item)
        if group is None:
            continue
        for path in {str(target["path"]) for target in objects(item["targets"])}:
            column = counts.setdefault(path, {})
            column[group] = column.get(group, 0) + 1
    return counts


def impact_body(check: Verification) -> Body:
    counts = impact_counts(check)
    return table("Validator and test impact", [
        [row["source"], row["decision"],
         *(counts.get(str(row["source"]), {}).get(group, 0) for group in IMPACT_GROUPS)]
        for row in by_field(check.doc["map"], "source") if row["decision"] != "keep"])


def spec09_body(check: Verification) -> Body:
    record = cast(JsonObject, check.doc["req21"])
    nulls: Rows = [[row["source"], row["decision"], targets_text(row["targets"]),
                    row["amendment"]]
                   for row in by_field(check.doc["map"], "source")
                   if row["spec09_default"] is None]
    statements: Rows = [[item["source"], item["text"], item["covered_by"]]
                        for item in objects(record["statements"])]
    return (table("Spec 09 inputs", nulls) + ["", f"req21 verdict: {cell(record['verdict'])}",
                                              ""] + table("Statements", statements))


def findings_body(check: Verification) -> Body:
    return table("Findings", [
        [item["id"], item["type"], item["severity"], item["source"], item["section"],
         item["owner"], item["blocks_09"], item["status"], item["observation"],
         item["closure"]] for item in by_field(check.doc["findings"], "id")])


def amendments_body(check: Verification) -> Body:
    return table("Amendments to spec 09", [
        [item["id"], item["target"], item["change"], item["proposed"], item["reason"],
         item["evidence"], item["affected"], item["depends_on"], item["requires_adr"],
         item["disposition"]] for item in by_field(check.doc["amendments"], "id")])


def coverage_body(check: Verification) -> Body:
    return table("Read coverage", [
        [item["path"], item["status"], item["sha256"], item["reader"]]
        for item in by_field(check.doc["coverage"], "path")])


def installed_body(check: Verification) -> Body:
    if check.doc["installed_access"] == "not-verified":
        return ["Not verified."]
    return table("Installed comparison", [
        [item["path"], item["location"], item["source_sha256"], item["installed_sha256"],
         "yes" if item["source_sha256"] == item["installed_sha256"] else "no"]
        for item in by_field(check.doc["installed"], "path")])


SUBSECTIONS: tuple[tuple[str, Callable[[Verification], Body]], ...] = (
    ("Passport", passport_body),
    ("Inventory", inventory_body),
    ("Sections", sections_body),
    ("References", references_body),
    ("Loads", loads_body),
    ("Repeated loads", repeated_loads_body),
    ("Full-output candidates", lambda check: line_candidates_body(check, "full_output")),
    ("Harness-name candidates", lambda check: line_candidates_body(check, "harness_names")),
    ("Repetition review", repetition_body),
    ("Legacy mentions", legacy_body),
    ("Duplicates", duplicates_body),
    ("Migration map", map_body),
    ("Validator and test impact", impact_body),
    ("Spec 09 inputs", spec09_body),
    ("Findings", findings_body),
    ("Amendments to spec 09", amendments_body),
    ("Read coverage", coverage_body),
    ("Installed comparison", installed_body),
)


def render_region(inventory: Document, assessment: Document) -> str:
    """The generated region: both marker lines and each `###` subsection with its body,
    blank lines between; every line ends with LF. It depends on the two documents only."""
    check = verification(inventory, assessment, None, frozenset())
    lines = [REPORT_BEGIN, ""]
    for name, body in SUBSECTIONS:
        lines += [f"### {name}", "", *body(check), ""]
    lines.append(REPORT_END)
    return "".join(f"{line}\n" for line in lines)


# ---------------------------------------------------------------------------
# Report file: reading, markers and layout
# ---------------------------------------------------------------------------

REPORT_SIZE_LIMIT = 64 * 1024 * 1024
REPORT_TITLE_PREFIX = "# Rules and workflows audit — "
SUMMARY_HEADING = "## Summary"
METHOD_HEADING = "## Method"
BLOCKERS_HEADING = "## Blockers for spec 09"
REVIEW_HEADING = "## Independent review"
ACCEPTANCE_HEADING = "## Acceptance"
REPORT_HEADINGS = (SUMMARY_HEADING, METHOD_HEADING, BLOCKERS_HEADING, REVIEW_HEADING,
                   ACCEPTANCE_HEADING)
REVIEW_LINE_RE = re.compile(
    r"Reviewed: (?:pending|[A-Za-z][A-Za-z0-9-]* (\d{4}-\d{2}-\d{2}) (?:pass|fail) "
    r"([0-9a-f]{40}))")
ACCEPTANCE_LINE_RE = re.compile(r"Accepted: (?:pending|owner (\d{4}-\d{2}-\d{2}))")
FILE_NAME_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-")


class ReportUnusable(ValueError):
    """A report that is absent or cannot be read as text."""

    def __init__(self, message: str, missing: bool = False) -> None:
        super().__init__(message)
        self.missing = missing


@dataclass(frozen=True)
class ReportText:
    """The text of a regular report file and its permission bits."""

    text: str
    mode: int


def read_bounded(descriptor: int) -> ReportText:
    with os.fdopen(descriptor, "rb") as handle:
        status = os.fstat(handle.fileno())
        if not stat.S_ISREG(status.st_mode):
            raise ReportUnusable("is not a regular file")
        if status.st_size > REPORT_SIZE_LIMIT:
            raise ReportUnusable(f"is larger than {REPORT_SIZE_LIMIT} bytes")
        data = handle.read(REPORT_SIZE_LIMIT + 1)
    if len(data) > REPORT_SIZE_LIMIT:
        raise ReportUnusable(f"is larger than {REPORT_SIZE_LIMIT} bytes")
    text = decode_strict(data)
    if text is None:
        raise ReportUnusable("is not valid UTF-8")
    return ReportText(text, stat.S_IMODE(status.st_mode))


def read_report(path: Path) -> ReportText:
    """The strict UTF-8 text of a regular report file of bounded size, read without
    following a symbolic link or blocking on a special file."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except (FileNotFoundError, NotADirectoryError):
        raise ReportUnusable("does not exist", missing=True) from None
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise ReportUnusable("is a symbolic link and is not followed") from None
        raise ReportUnusable(f"cannot be read ({error.strerror})") from None
    try:
        return read_bounded(descriptor)
    except OSError as error:
        raise ReportUnusable(f"cannot be read ({error.strerror})") from None


def report_lines(text: str) -> list[str]:
    """The LF-separated lines of the report; a final LF ends the last line."""
    lines = text.split("\n")
    return lines[:-1] if lines[-1] == "" else lines


def marker_indexes(lines: Sequence[str], marker: str) -> list[int]:
    return [index for index, line in enumerate(lines) if line == marker]


def region_bounds(lines: Sequence[str]) -> tuple[int, int] | None:
    """The indexes of the begin and end marker lines when each occurs once, in order."""
    begins, ends = marker_indexes(lines, REPORT_BEGIN), marker_indexes(lines, REPORT_END)
    if len(begins) != 1 or len(ends) != 1 or ends[0] < begins[0]:
        return None
    return begins[0], ends[0]


def top_headings(lines: Sequence[str]) -> list[tuple[int, int, str]]:
    """Level-1 and level-2 headings outside fences and the generated region, as
    (index, level, text with trailing whitespace removed)."""
    zones = line_zones(lines, 0)
    bounds = region_bounds(lines)
    found = []
    for index, line in enumerate(lines):
        inside = bounds is not None and bounds[0] <= index <= bounds[1]
        match = HEADING_RE.match(line) if zones[index] == ZONE_BODY and not inside else None
        if match is not None and len(match.group(1)) <= 2:
            found.append((index, len(match.group(1)), line.rstrip()))
    return found


def title_faults(lines: Sequence[str], run_date: str | None) -> list[tuple[int, str]]:
    first = lines[0] if lines else ""
    if not first.startswith(REPORT_TITLE_PREFIX):
        return [(1, "the first line is not the report title")]
    if run_date is not None and first != REPORT_TITLE_PREFIX + run_date:
        return [(1, f"the title does not name the run date {run_date}")]
    return []


def repeated_faults(name: str, indexes: Sequence[int]) -> list[tuple[int, str]]:
    if not indexes:
        return [(0, f"{name} is missing")]
    return [(index + 1, f"{name} is repeated") for index in indexes[1:]]


def heading_faults(headings: Sequence[tuple[int, int, str]]) -> list[tuple[int, str]]:
    faults = [(index + 1, f'unexpected heading "{text}"') for index, level, text in headings
              if index > 0 and (level == 1 or text not in REPORT_HEADINGS)]
    for expected in REPORT_HEADINGS:
        found = [index for index, _, text in headings if text == expected]
        faults += repeated_faults(f'the heading "{expected}"', found)
    return faults


def heading_index(headings: Sequence[tuple[int, int, str]], text: str) -> int | None:
    found = [index for index, _, heading in headings if heading == text]
    return found[0] if len(found) == 1 else None


def order_faults(lines: Sequence[str], headings: Sequence[tuple[int, int, str]]
                 ) -> list[tuple[int, str]]:
    """The documented order of the five headings and the marker pair, checked once
    each occurs exactly once."""
    begins, ends = marker_indexes(lines, REPORT_BEGIN), marker_indexes(lines, REPORT_END)
    places = [heading_index(headings, text) for text in REPORT_HEADINGS[:2]]
    places += [begins[0] if len(begins) == 1 else None, ends[0] if len(ends) == 1 else None]
    places += [heading_index(headings, text) for text in REPORT_HEADINGS[2:]]
    if any(place is None for place in places):
        return []
    known = cast(list[int], places)
    for previous, current in zip(known, known[1:]):
        if current < previous:
            return [(current + 1, "the headings and markers are out of the documented order")]
    return []


def section_body(lines: Sequence[str], headings: Sequence[tuple[int, int, str]],
                 text: str) -> tuple[int, list[int]] | None:
    """The heading index of a section that occurs once and the indexes of its non-blank
    lines up to the next level-1 or level-2 heading."""
    start = heading_index(headings, text)
    if start is None:
        return None
    later = [index for index, _, _ in headings if index > start]
    end = later[0] if later else len(lines)
    return start, [index for index in range(start + 1, end) if lines[index].strip()]


def line_matches(line: str, pattern: re.Pattern[str]) -> bool:
    found = pattern.fullmatch(line)
    return found is not None and (found.group(1) is None or is_date(found.group(1)))


def single_line_faults(lines: Sequence[str], headings: Sequence[tuple[int, int, str]],
                       text: str, pattern: re.Pattern[str]) -> list[tuple[int, str]]:
    """A section that must hold exactly one non-blank line in its grammar."""
    body = section_body(lines, headings, text)
    if body is None:
        return []
    start, filled = body
    if not filled:
        return [(start + 1, f'"{text}" holds no line in its grammar')]
    faults = [(filled[0] + 1, f'"{text}" holds a malformed line')
              ] if not line_matches(lines[filled[0]], pattern) else []
    return faults + [(index + 1, f'"{text}" holds more than one line') for index in filled[1:]]


def layout_faults(lines: Sequence[str], headings: Sequence[tuple[int, int, str]],
                  run_date: str | None) -> list[tuple[int, str]]:
    """Title, headings, markers, their order and the review and acceptance lines; the
    title date is checked only when the run date is known."""
    faults = title_faults(lines, run_date) + heading_faults(headings)
    faults += repeated_faults("the begin marker", marker_indexes(lines, REPORT_BEGIN))
    faults += repeated_faults("the end marker", marker_indexes(lines, REPORT_END))
    faults += order_faults(lines, headings)
    faults += single_line_faults(lines, headings, REVIEW_HEADING, REVIEW_LINE_RE)
    faults += single_line_faults(lines, headings, ACCEPTANCE_HEADING, ACCEPTANCE_LINE_RE)
    return faults


# ---------------------------------------------------------------------------
# Verify: the report
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReportCheck:
    """One readable report with its display name, lines and top-level headings."""

    name: str
    lines: list[str]
    headings: list[tuple[int, int, str]]

    def at(self, index: int) -> str:
        return f"{self.name}:{index}"


def review_commit_rules(root: Path, report: ReportCheck) -> Iterator[Diagnostic]:
    """The commit of a well-formed review line must exist in the root's repository."""
    body = section_body(report.lines, report.headings, REVIEW_HEADING)
    for index in body[1] if body is not None else []:
        found = REVIEW_LINE_RE.fullmatch(report.lines[index])
        if found is None or found.group(2) is None or not is_date(found.group(1)):
            continue
        if run_git(root, "cat-file", "-e", f"{found.group(2)}^{{commit}}") is None:
            yield Diagnostic("review-commit-unknown", report.at(index + 1),
                             f"the commit {found.group(2)} does not exist in the repository")


def report_economics_rules(report: ReportCheck) -> Iterator[Diagnostic]:
    for index, line in enumerate(report.lines):
        for pattern in ECONOMICS_PATTERNS:
            found = pattern.search(line)
            if found is not None:
                yield Diagnostic("economics-claim", report.at(index + 1),
                                 f'names an amount: "{found.group(0)}"')
                break


def name_date_rules(path: Path, report: ReportCheck, run_date: str) -> Iterator[Diagnostic]:
    found = FILE_NAME_DATE_RE.match(path.name)
    named = found.group(1) if found is not None else None
    if named != run_date:
        yield Diagnostic("report-name-date", report.at(0),
                         f"the file name date {named or '(none)'} differs from run_date "
                         f"{run_date}")


def blocker_rules(report: ReportCheck, assessment: JsonObject) -> Iterator[Diagnostic]:
    body = section_body(report.lines, report.headings, BLOCKERS_HEADING)
    if body is None:
        return
    start, filled = body
    text = "\n".join(report.lines[index] for index in filled)
    for item in sorted(objects(assessment["findings"]), key=lambda row: str(row["id"])):
        identifier = str(item["id"])
        token = re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(identifier)}(?![A-Za-z0-9_-])")
        if item["blocks_09"] is True and token.search(text) is None:
            yield Diagnostic("blocker-unlisted", report.at(start + 1),
                             f"the blocking finding {identifier} is not listed")


def region_rules(report: ReportCheck, inventory: Document, assessment: Document
                 ) -> Iterator[Diagnostic]:
    bounds = region_bounds(report.lines)
    if bounds is None:
        return
    begin, end = bounds
    written = report.lines[begin:end + 1]
    rendered = report_lines(render_region(inventory, assessment))
    if written == rendered:
        return
    offset = next((index for index, (left, right) in enumerate(zip(written, rendered))
                   if left != right), min(len(written), len(rendered)))
    yield Diagnostic("report-generated-mismatch", report.at(begin + offset + 1),
                     "the generated region differs from the render output")


def report_diagnostics(root: Path, path: Path, inventory: Document | None,
                       assessment: Document | None) -> list[Diagnostic]:
    """Rules over the report. Those that need no valid input always run; the name date,
    the title date and the blockers need the assessment, the region needs both."""
    name = link_name(path, root)
    try:
        text = read_report(path).text
    except ReportUnusable as error:
        code = "report-missing" if error.missing else "report-layout"
        message = "the file does not exist" if error.missing else f"the report {error}"
        return [Diagnostic(code, f"{name}:0", message)]
    lines = report_lines(text)
    report = ReportCheck(name, lines, top_headings(lines))
    doc = cast(JsonObject, assessment.value) if assessment is not None else None
    run_date = str(doc["run_date"]) if doc is not None else None
    found = [Diagnostic("report-layout", report.at(line), message)
             for line, message in layout_faults(lines, report.headings, run_date)]
    found += list(review_commit_rules(root, report)) + list(report_economics_rules(report))
    if doc is not None and run_date is not None:
        found += list(name_date_rules(path, report, run_date)) + list(blocker_rules(report, doc))
    if inventory is not None and assessment is not None:
        found += list(region_rules(report, inventory, assessment))
    return found


# ---------------------------------------------------------------------------
# Verify: command
# ---------------------------------------------------------------------------

def checked_document(document: Document | Diagnostic, schema: Schema, code: str
                     ) -> tuple[Document | None, list[Diagnostic]]:
    """The document when it parsed and meets its schema, and every diagnostic found."""
    if isinstance(document, Diagnostic):
        return None, [document]
    problems = schema_diagnostics(document, schema, code)
    return (None if problems else document), problems


def load_inputs(root: Path, report: Path
                ) -> tuple[Document | None, Document | None, list[Diagnostic]]:
    """The inventory and the assessment derived from the report path, each None when it
    is missing or breaks its schema, with every diagnostic found."""
    stem = str(report)[:-len(".md")]
    paths = [Path(stem + suffix) for suffix in (".inventory.json", ".assessment.json")]
    inventory, found = checked_document(
        load_document(paths[0], display_name(paths[0], root), "inventory"),
        INVENTORY_SCHEMA, "inventory-invalid")
    assessment, problems = checked_document(
        load_document(paths[1], display_name(paths[1], root), "assessment"),
        ASSESSMENT_SCHEMA, "assessment-invalid")
    return inventory, assessment, found + problems


def verify_diagnostics(root: Path, report: Path, strict: bool) -> list[Diagnostic]:
    inventory, assessment, found = load_inputs(root, report)
    migration, unavailable = load_migration(root)
    found += unavailable + report_diagnostics(root, report, inventory, assessment)
    if inventory is not None:
        found += worktree_diagnostics(inventory) + stale_diagnostics(root, inventory)
        if strict:
            found += strict_diagnostics(root, inventory)
    if inventory is not None and assessment is not None:
        check = verification(inventory, assessment, migration, discovery_units(root))
        found += [item for rule in ASSESSMENT_RULES for item in rule(check)]
    return found


def run_verify(root: Path, report: Path, strict: bool) -> int:
    if report.suffix != ".md":
        raise UsageError("--report must name the report's .md file")
    try:
        validate_root(root)
        diagnostics = sorted(verify_diagnostics(root, report, strict))
    except OSError as error:
        raise ToolError("root-unreadable", f"cannot read the root ({error.strerror})") from error
    write_lines(sys.stdout, [diagnostic_line(item) for item in diagnostics])
    return 1 if diagnostics else 0


# ---------------------------------------------------------------------------
# Render: command
# ---------------------------------------------------------------------------

REPORT_FAILURE = ("report-unwritable", "cannot write the report")


def report_for_write(report: Path) -> ReportText:
    """The report to update, refused unless it is readable and holds one marker pair."""
    try:
        current = read_report(report)
    except ReportUnusable as error:
        raise ToolError("report-unreadable", f"the report {error}") from None
    if region_bounds(report_lines(current.text)) is None:
        raise ToolError("report-markers", "the report needs exactly one begin marker line "
                        "followed by exactly one end marker line")
    return current


def replace_region(text: str, region: str) -> str:
    """The text with the lines from the begin marker to the end marker replaced."""
    pieces = text.split("\n")
    begin, end = cast(tuple[int, int], region_bounds(report_lines(text)))
    start = sum(len(piece) + 1 for piece in pieces[:begin])
    stop = min(len(text), sum(len(piece) + 1 for piece in pieces[:end + 1]))
    return text[:start] + region + text[stop:]


def write_region(region: str) -> None:
    """Write the region as UTF-8 bytes whatever the locale, as --write stores it."""
    sys.stdout.flush()
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is None:
        sys.stdout.write(region)
        return
    buffer.write(region.encode("utf-8"))
    buffer.flush()


def run_render(root: Path, report: Path, write: bool) -> int:
    if report.suffix != ".md":
        raise UsageError("--report must name the report's .md file")
    current = report_for_write(report) if write else None
    inventory, assessment, problems = load_inputs(root, report)
    if inventory is None or assessment is None:
        write_lines(sys.stdout, [diagnostic_line(item) for item in sorted(problems)])
        return 1
    region = render_region(inventory, assessment)
    if current is None:
        write_region(region)
    else:
        write_atomically(report, replace_region(current.text, region), REPORT_FAILURE,
                         current.mode)
    return 0


# ---------------------------------------------------------------------------
# Output boundary
# ---------------------------------------------------------------------------

LINE_BREAKING_CATEGORIES = frozenset({"Cc", "Cs", "Zl", "Zp"})


def escaped_character(character: str) -> str:
    code = ord(character)
    if code < 0x100:
        return f"\\x{code:02x}"
    return f"\\u{code:04x}" if code < 0x10000 else f"\\U{code:08x}"


def encodable(character: str, encoding: str) -> bool:
    try:
        character.encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return False
    return True


def needs_escape(character: str, encoding: str, in_location: bool) -> bool:
    """Backslash, control, surrogate and separator characters, and what the stream cannot hold."""
    if character == "\\" or (in_location and character == " "):
        return True
    return (unicodedata.category(character) in LINE_BREAKING_CATEGORIES
            or not encodable(character, encoding))


def output_text(text: str, encoding: str, in_location: bool = False) -> str:
    """Text that encodes on the stream, holds no line break and, in a location, no space."""
    return "".join(escaped_character(character)
                   if needs_escape(character, encoding, in_location) else character
                   for character in text)


def stream_encoding(stream: TextIO) -> str:
    return getattr(stream, "encoding", None) or "ascii"


def diagnostic_line(item: Diagnostic) -> tuple[str, str, str]:
    return item.code, item.location, item.message


def write_lines(stream: TextIO, lines: Sequence[str | tuple[str, str, str]]) -> None:
    """Write each line escaped: an error line as text, a diagnostic as code, location, message."""
    encoding = stream_encoding(stream)
    rendered: list[str] = []
    for line in lines:
        if isinstance(line, tuple):
            code, location, message = line
            rendered.append(" ".join((output_text(code, encoding, True),
                                      output_text(location, encoding, True),
                                      output_text(message, encoding))))
        else:
            rendered.append(output_text(line, encoding))
    stream.write("".join(f"{line}\n" for line in rendered))


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
    verify = commands.add_parser("verify", help="check the inventory and the assessment")
    verify.add_argument("--root", type=Path, default=None)
    verify.add_argument("--report", type=Path, required=True)
    verify.add_argument("--strict", action="store_true")
    render = commands.add_parser("render", help="render the generated region of the report")
    render.add_argument("--root", type=Path, default=None)
    render.add_argument("--report", type=Path, required=True)
    render.add_argument("--write", action="store_true")
    return parser


def main(argv: Sequence[str]) -> int:
    try:
        arguments = argument_parser().parse_args(list(argv))
        root = arguments.root if arguments.root is not None else default_root()
        if arguments.command == "verify":
            return run_verify(root, arguments.report, arguments.strict)
        if arguments.command == "render":
            return run_render(root, arguments.report, arguments.write)
        return run_extract(root, arguments.out)
    except UsageError as error:
        write_lines(sys.stderr, [f"ERROR: usage: {error}"])
    except ToolError as error:
        write_lines(sys.stderr, [f"ERROR: {error}"])
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
