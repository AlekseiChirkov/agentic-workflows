#!/usr/bin/env python3
"""Read-only audit tool for the instruction files of this repository.

The audited set is every non-directory entry under rules/ and workflows/ (primary) and
under harness/ plus templates/codex-global-AGENTS.md (adapter). Readers are the other
classified files of the root that may refer to audited files.

Usage:
  python3 -I scripts/audit-instructions.py extract [--root DIR] --out FILE
      Write the inventory (audited files with their text structure, readers, git state,
      a digest over both lists, and every reference edge from a decoded audited file or
      reader to audited files, with its form, context, status, flags and targets) as
      canonical JSON to FILE. FILE is written to a temporary file in its own directory
      and moved into place. `is_defect_edge` is the defect predicate over one edge.
      --root defaults to the parent of the scripts/ directory that holds this file.

Exit codes:
  0  the inventory was written
  2  usage error, root-invalid (no rules/ or workflows/ directory), root-unreadable
     (a directory or file that cannot be read, or a file name that is not valid UTF-8),
     out-unwritable, or an interpreter older than Python 3.11; one `ERROR:` line on
     standard error, and no --out file is written

Read-only contract: the tool writes nothing but the --out file. It never follows a
symbolic link, never executes or imports repository content and opens no network
connection. The only programs it runs are the git read commands
`rev-parse --verify HEAD`, `ls-files -z` and
`status --porcelain=v1 -z --untracked-files=all`, with LC_ALL=C, GIT_OPTIONAL_LOCKS=0,
no pager, no inherited GIT_* variables, the file-system monitor disabled and hooks
pointed at an empty location, so no program named by the repository's configuration
runs; a missing or failing git yields null or `unknown` values, never an error. The
root is taken as the top level of its git work tree: `status` reports paths relative
to that top level, so a root below it yields mismatched work-tree paths.
Standard library only.
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
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
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
# Configuration that would otherwise let git start a program the repository names.
GIT_INERT_CONFIGURATION = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")

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


def tree_below(root: Path, top: str) -> Iterator[tuple[str, bool]]:
    """Yield every entry below `top` with whether it is a real directory; links stay unfollowed."""
    with os.scandir(root / top) as iterator:
        children = sorted(iterator, key=lambda child: child.name)
    for child in children:
        relative = f"{top}/{child.name}"
        is_directory = child.is_dir(follow_symlinks=False)
        yield relative, is_directory
        if is_directory:
            yield from tree_below(root, relative)


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
            escaped = path.encode("utf-8", "surrogateescape").decode("ascii", "backslashreplace")
            raise ToolError("root-unreadable",
                            f"a file name is not valid UTF-8: {escaped}") from None


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
        result = subprocess.run(["git", "--no-pager", *GIT_INERT_CONFIGURATION,
                                 "-C", str(root), *arguments],
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
    try:
        validate_root(root)
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
