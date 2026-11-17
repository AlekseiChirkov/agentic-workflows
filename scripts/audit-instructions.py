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
      the work-tree state, and every per-item rule of the assessment. Prints one
      `<code> <location> <message>` line per violation in string order of code and
      location. A location is `<path>:<line>` (`0` for a whole file) or
      `<json file>#<id, key or key[index]>`, with paths relative to the root.

Exit codes:
  0  extract: the inventory was written; verify: no diagnostic
  1  verify: at least one diagnostic was printed
  2  usage error, root-invalid (no rules/ or workflows/ directory), root-unreadable
     (a directory or file that cannot be read, or a file name that is not valid UTF-8),
     out-unwritable, or an interpreter older than Python 3.11; one `ERROR:` line on
     standard error, and no --out file is written

Read-only contract: the tool writes nothing but the --out file, and verify writes
nothing. It never follows a symbolic link of the audited tree, never executes or
imports repository content and opens no network
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
import datetime
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
from typing import NoReturn, cast

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
        **candidate_lists(audited_files, edges),
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
        raise JsonRejected(f"duplicate key {json.dumps(duplicates[0], ensure_ascii=False)}")
    return dict(pairs)


def reject_constant(name: str) -> NoReturn:
    raise JsonRejected(f"non-standard constant {name}")


def parse_json(text: str) -> object:
    return json.loads(text, object_pairs_hook=reject_duplicate_keys,
                      parse_constant=reject_constant)


def display_name(path: Path, root: Path) -> str:
    """The path relative to the root, or its base name when it lies outside the root."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


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
    except (JsonRejected, RecursionError) as error:
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
    "map": is_list,
    "req21": is_object,
    "findings": ListSchema(record({
        "id": AUDIT_ID, "type": one_of(*FINDING_OWNERS),
        "severity": one_of("blocker", "major", "minor"), "source": is_str, "section": is_str,
        "sha256": nullable(DIGEST), "lines": list_of(is_int), "observation": is_str,
        "consequence": is_str, "owner": is_str, "closure": is_str, "blocks_09": is_bool,
        "status": is_str, "evidence": list_of(is_str), "edges": list_of(LINE_REF)}), "id"),
    "amendments": ListSchema(is_object),
    "installed": ListSchema(record({
        "path": is_str, "location": is_str, "source_sha256": is_str,
        "installed_sha256": is_str})),
}


def fragment(text: str) -> str:
    """A location fragment that keeps a diagnostic line free of spaces and line breaks."""
    return text if SAFE_FRAGMENT_RE.fullmatch(text) else json.dumps(text).replace(" ", "\\u0020")


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
                yield Diagnostic(code, location, f"duplicate {schema.unique} {identity}")
            seen.add(identity)


def schema_diagnostics(document: Document, schema: Schema, code: str) -> list[Diagnostic]:
    """Unknown, missing and malformed keys, malformed rows and repeated ids of a document."""
    value = document.value
    if not isinstance(value, dict):
        return [Diagnostic(code, f"{document.name}:0", "the top level is not a JSON object")]
    found = [Diagnostic(code, f"{document.name}#{fragment(key)}", "unknown key")
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


def verification(inventory: Document, assessment: Document) -> Verification:
    inv, doc = cast(JsonObject, inventory.value), cast(JsonObject, assessment.value)
    ids, cited = amendment_lookups(doc)
    return Verification(
        inventory, assessment,
        files={str(entry["path"]): entry for entry in objects(inv["files"])},
        readers={str(entry["path"]): entry for entry in objects(inv["readers"])},
        findings={str(entry["id"]): entry for entry in objects(doc["findings"])},
        amendment_ids=ids, cited=cited,
        defects={edge_key(edge): edge for edge in objects(inv["edges"])
                 if is_defect_edge(edge)})


def first_rows(check: Verification, key: str) -> dict[str, tuple[int, JsonObject]]:
    """The first row of `key` for each audited path, with its index."""
    found: dict[str, tuple[int, JsonObject]] = {}
    for index, row in enumerate(check.rows(key)):
        path = str(row["path"])
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


def row_rules(check: Verification) -> Iterator[Diagnostic]:
    for key in ("files", "coverage"):
        seen: set[str] = set()
        for index, row in enumerate(check.rows(key)):
            path, location = str(row["path"]), check.at(f"{key}[{index}]")
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
        faults.append(f"status {json.dumps(finding['status'])} is not open or historical-fixed")
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
        faults.append(f"section {json.dumps(finding['section'])} is not a section of the source")
    return faults


def evidence_faults(finding: JsonObject) -> list[str]:
    evidence = cast(list[str], finding["evidence"])
    faults = [] if evidence else ["evidence is empty"]
    faults += [f"evidence {json.dumps(item)} is not path:line, a path or an amendment id"
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


def strings_in(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings_in(item)


def economic_claims(location: str, value: object) -> Iterator[Diagnostic]:
    for text in strings_in(value):
        for pattern in ECONOMICS_PATTERNS:
            found = pattern.search(text)
            if found is not None:
                amount = json.dumps(found.group(0), ensure_ascii=False)
                yield Diagnostic("economics-claim", location, f"names an amount: {amount}")
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
    installed_rules, economics_rules,
)


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


def verify_diagnostics(root: Path, report: Path, strict: bool) -> list[Diagnostic]:
    stem = str(report)[:-len(".md")]
    paths = [Path(stem + suffix) for suffix in (".inventory.json", ".assessment.json")]
    inventory, found = checked_document(
        load_document(paths[0], display_name(paths[0], root), "inventory"),
        INVENTORY_SCHEMA, "inventory-invalid")
    assessment, problems = checked_document(
        load_document(paths[1], display_name(paths[1], root), "assessment"),
        ASSESSMENT_SCHEMA, "assessment-invalid")
    found += problems
    if inventory is not None:
        found += worktree_diagnostics(inventory) + stale_diagnostics(root, inventory)
        if strict:
            found += strict_diagnostics(root, inventory)
    if inventory is not None and assessment is not None:
        check = verification(inventory, assessment)
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
    sys.stdout.write("".join(f"{item.code} {item.location} {item.message}\n"
                             for item in diagnostics))
    return 1 if diagnostics else 0


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
    return parser


def main(argv: Sequence[str]) -> int:
    try:
        arguments = argument_parser().parse_args(list(argv))
        root = arguments.root if arguments.root is not None else default_root()
        if arguments.command == "verify":
            return run_verify(root, arguments.report, arguments.strict)
        return run_extract(root, arguments.out)
    except UsageError as error:
        sys.stderr.write(f"ERROR: usage: {error}\n")
    except ToolError as error:
        sys.stderr.write(f"ERROR: {error}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
