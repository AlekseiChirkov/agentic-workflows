#!/usr/bin/env python3
"""Acceptance suite for scripts/audit-instructions.py.

Every case builds a disposable fixture root under a private temporary directory, with
minimal rules/, workflows/, harness/ and reader files and, where a case needs git, an
initialised repository whose git calls use a temporary HOME and XDG_CONFIG_HOME. The
tool runs as a subprocess with `python3 -I`, except that the defect predicate, a pure
function over one edge, and the readers of git's metadata and info/attributes files are
called after loading the tool's source as a module; no real
project file is read except the tool's own source and the two scripts that must not
name it.

Usage: python3 -I scripts/check-audit-instructions.py [-v] [unittest arguments]
Exit 0 = every case passed, 1 = at least one failure.
Standalone: it is not called by scripts/validate-contracts.sh or scripts/sync.sh.
Requires Python 3.11+ and, for the git cases, git.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from collections import Counter
from collections.abc import Callable, Sequence
from contextlib import suppress
from pathlib import Path
from unittest import mock

SOURCE_ROOT = Path(__file__).resolve().parents[1]
TOOL = SOURCE_ROOT / "scripts" / "audit-instructions.py"
REAL_GIT = shutil.which("git")
GUARD_MESSAGE = "ERROR: Python 3.11 or newer is required"

INVENTORY_KEYS = [
    "schema_version", "method_version", "source_revision", "worktree", "inventory_digest",
    "files", "readers", "edges", "repeat_loads", "full_output", "harness_names",
    "legacy_mentions", "duplicate_clusters",
]
LIST_KEYS_EMPTY_HERE = [
    "edges", "repeat_loads", "full_output", "harness_names", "legacy_mentions",
    "duplicate_clusters",
]
FILE_KEYS = [
    "path", "set", "entry", "tracked", "sha256", "bytes", "lines", "encoding", "words",
    "front_matter", "invocation_lines", "sections",
]
READER_KEYS = ["path", "class", "sha256", "lines", "decoded"]
FRONT_MATTER_KEYS = ["status", "keys", "trigger", "description", "continuation_lines"]
SECTION_KEYS = ["heading", "line", "words", "bytes"]
ABSENT_FRONT_MATTER = {
    "status": "absent", "keys": [], "trigger": None, "description": None,
    "continuation_lines": 0,
}
NULL_CONTENT_FIELDS = {
    "sha256": None, "bytes": None, "lines": None, "encoding": None, "words": None,
    "front_matter": None, "invocation_lines": None, "sections": [],
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise AssertionError(f"duplicate JSON keys: {duplicates}")
    return dict(pairs)


def parse_inventory(text: str) -> dict:
    return json.loads(text, object_pairs_hook=reject_duplicate_keys)


def git_env(home: Path) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Fixture Author",
        "GIT_AUTHOR_EMAIL": "author@example.invalid",
        "GIT_COMMITTER_NAME": "Fixture Author",
        "GIT_COMMITTER_EMAIL": "author@example.invalid",
        "LC_ALL": "C",
    })
    return env


def tree_digests(root: Path) -> dict[str, str]:
    """Digest every non-directory entry below root, .git included, without following links."""
    digests: dict[str, str] = {}
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        for name in dirnames + filenames:
            path = Path(directory) / name
            if path.is_symlink():
                digests[path.relative_to(root).as_posix()] = "link:" + os.readlink(path)
            elif path.is_file():
                digests[path.relative_to(root).as_posix()] = sha256(path.read_bytes())
    return digests


def digest_text(entries: dict[str, tuple[str, str | None]]) -> str:
    lines = [f"{path}\t{label}\t{digest or '-'}\n"
             for path, (label, digest) in sorted(entries.items())]
    return sha256("".join(lines).encode("utf-8"))


class FixtureRoot:
    """A disposable project root with helpers to write files and drive git."""

    def __init__(self, base: Path) -> None:
        self.base = base
        self.root = base / "root"
        self.root.mkdir()
        self.home = base / "home"
        self.home.mkdir()
        self.env = git_env(self.home)

    def write(self, relative: str, content: bytes | str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8") if isinstance(content, str) else content
        path.write_bytes(data)
        return path

    def minimal(self) -> None:
        self.write("rules/alpha-flow.md", "# Alpha flow\n")
        self.write("workflows/beta-step.md", "# Beta step\n")

    def git(self, *args: str) -> str:
        if REAL_GIT is None:
            raise unittest.SkipTest("git is not installed")
        result = subprocess.run([REAL_GIT, *args], cwd=self.root, env=self.env, text=True,
                                capture_output=True)
        if result.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
        return result.stdout.strip()

    def commit_all(self) -> str:
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "chore: fixture")
        return self.git("rev-parse", "HEAD")


def run_tool(arguments: list[str], env: dict[str, str], cwd: Path,
             tool: Path = TOOL) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-I", str(tool), *arguments], cwd=cwd, env=env,
                          text=True, capture_output=True, timeout=60)


class ToolCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="audit-instructions-")
        self.base = Path(self.temp.name)
        self.fx = FixtureRoot(self.base)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def require_tool(self) -> None:
        self.assertTrue(TOOL.is_file(), f"the tool {TOOL.relative_to(SOURCE_ROOT)} does not exist")

    def run_extract(self, out: Path | None = None, root: Path | None = None,
                    env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        out = out if out is not None else self.base / "inventory.json"
        root = root if root is not None else self.fx.root
        return run_tool(["extract", "--root", str(root), "--out", str(out)],
                        env if env is not None else self.fx.env, self.base)

    def extract(self, out: Path | None = None, env: dict[str, str] | None = None) -> dict:
        out = out if out is not None else self.base / "inventory.json"
        result = self.run_extract(out=out, env=env)
        self.assertEqual(result.returncode, 0,
                         f"extract failed: stdout={result.stdout!r} stderr={result.stderr!r}")
        return parse_inventory(out.read_text(encoding="utf-8"))

    def row(self, inventory: dict, path: str) -> dict:
        rows = [entry for entry in inventory["files"] if entry["path"] == path]
        self.assertEqual(len(rows), 1, f"{path} must have exactly one files row")
        return rows[0]

    def assert_single_error_line(self, result: subprocess.CompletedProcess[str]) -> str:
        self.assertEqual(result.returncode, 2, f"stderr={result.stderr!r}")
        lines = result.stderr.strip().splitlines()
        self.assertEqual(len(lines), 1, f"expected one stderr line, got {lines!r}")
        self.assertTrue(lines[0].startswith("ERROR: "), lines[0])
        return lines[0]


class AuditedSetTests(ToolCase):
    def test_extract_lists_exactly_the_audited_entries_of_a_four_file_root(self) -> None:
        self.fx.write("rules/a-b.md", "# A\n")
        self.fx.write("rules/reference/c.md", "# C\n")
        self.fx.write("workflows/d-e.md", "# D\n")
        self.fx.write("harness/x/y.json", "{}\n")
        (self.fx.root / "rules" / "empty-dir").mkdir()
        self.fx.write("templates/other.md", "# Template\n")
        self.fx.write("docs/GUIDE.md", "# Guide\n")

        inventory = self.extract()

        paths = [entry["path"] for entry in inventory["files"]]
        self.assertEqual(paths, ["harness/x/y.json", "rules/a-b.md", "rules/reference/c.md",
                                 "workflows/d-e.md"])
        sets = {entry["path"]: entry["set"] for entry in inventory["files"]}
        self.assertEqual(sets, {"harness/x/y.json": "adapter", "rules/a-b.md": "primary",
                                "rules/reference/c.md": "primary",
                                "workflows/d-e.md": "primary"})
        self.assertTrue(all(entry["entry"] == "file" for entry in inventory["files"]))

    def test_codex_global_template_is_the_only_audited_template(self) -> None:
        self.fx.minimal()
        self.fx.write("templates/codex-global-AGENTS.md", "# Essentials\n")
        self.fx.write("templates/project-AGENTS.md", "# Project\n")

        inventory = self.extract()

        self.assertEqual(self.row(inventory, "templates/codex-global-AGENTS.md")["set"],
                         "adapter")
        audited = {entry["path"] for entry in inventory["files"]}
        self.assertNotIn("templates/project-AGENTS.md", audited)
        readers = {entry["path"] for entry in inventory["readers"]}
        self.assertNotIn("templates/codex-global-AGENTS.md", readers)
        self.assertIn("templates/project-AGENTS.md", readers)

    def test_inventory_has_the_documented_keys_in_order_and_empty_later_lists(self) -> None:
        self.fx.minimal()
        self.fx.write("docs/GUIDE.md", "# Guide\n")

        inventory = self.extract()

        self.assertEqual(list(inventory), INVENTORY_KEYS)
        self.assertEqual(inventory["schema_version"], 1)
        self.assertEqual(inventory["method_version"], "08-extract-1")
        for key in LIST_KEYS_EMPTY_HERE:
            self.assertEqual(inventory[key], [], key)
        self.assertEqual(list(inventory["files"][0]), FILE_KEYS)
        self.assertEqual(list(inventory["files"][0]["front_matter"]), FRONT_MATTER_KEYS)
        self.assertEqual(list(inventory["readers"][0]), READER_KEYS)

    def test_default_root_is_the_parent_of_the_scripts_directory(self) -> None:
        self.require_tool()
        self.fx.minimal()
        copy = self.fx.write("scripts/audit-instructions.py", TOOL.read_bytes())
        out = self.base / "inventory.json"

        result = run_tool(["extract", "--out", str(out)], self.fx.env, self.base, tool=copy)

        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = parse_inventory(out.read_text(encoding="utf-8"))
        self.assertEqual([entry["path"] for entry in inventory["files"]],
                         ["rules/alpha-flow.md", "workflows/beta-step.md"])


class DeterminismTests(ToolCase):
    def build_mixed_root(self) -> dict[str, tuple[str, str | None]]:
        outside = self.base / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        written = {
            "rules/alpha-flow.md": ("primary", "---\ndescription: Alpha\n---\n## Überblick\n"),
            "workflows/beta-step.md": ("primary", "Invocation: `/beta-step`\n"),
            "harness/gamma/always-on.md": ("adapter", "## Essentials\n"),
            "docs/GUIDE.md": ("active", "See `rules/alpha-flow.md`.\n"),
            ".ai/memory/progress.md": ("history", "# Progress\n"),
        }
        entries: dict[str, tuple[str, str | None]] = {}
        for path, (label, text) in written.items():
            data = text.encode("utf-8")
            self.fx.write(path, data)
            entries[path] = (label, sha256(data))
        undecodable = b"\x1f\x8b\x08\x00\xff\xfe"
        self.fx.write("tests/fixtures/sample.gz", undecodable)
        entries["tests/fixtures/sample.gz"] = ("active", sha256(undecodable))
        os.symlink(outside, self.fx.root / "rules" / "link.md")
        entries["rules/link.md"] = ("primary", None)
        return entries

    def test_two_extractions_are_byte_identical_and_digest_is_independently_reproducible(
            self) -> None:
        entries = self.build_mixed_root()
        first, second = self.base / "first.json", self.base / "second.json"

        self.extract(out=first)
        self.extract(out=second)

        first_bytes = first.read_bytes()
        self.assertEqual(first_bytes, second.read_bytes())
        inventory = parse_inventory(first_bytes.decode("utf-8"))
        self.assertEqual(inventory["inventory_digest"], digest_text(entries))

    def test_inventory_text_is_canonical_json_with_relative_paths_only(self) -> None:
        self.build_mixed_root()
        out = self.base / "inventory.json"

        self.extract(out=out)

        text = out.read_text(encoding="utf-8")
        parsed = parse_inventory(text)
        self.assertEqual(text, json.dumps(parsed, ensure_ascii=False, indent=2) + "\n")
        self.assertIn("## Überblick", text)
        self.assertNotIn(str(self.base), text)
        paths = [entry["path"] for entry in parsed["files"]]
        self.assertEqual(paths, sorted(paths))
        readers = [entry["path"] for entry in parsed["readers"]]
        self.assertEqual(readers, sorted(readers))

    def test_digest_of_a_root_with_no_entries_is_the_digest_of_empty_text(self) -> None:
        (self.fx.root / "rules").mkdir()
        (self.fx.root / "workflows").mkdir()

        inventory = self.extract()

        self.assertEqual(inventory["files"], [])
        self.assertEqual(inventory["readers"], [])
        self.assertEqual(inventory["inventory_digest"], sha256(b""))


class NonRegularEntryTests(ToolCase):
    def test_symbolic_links_are_rows_with_null_digests_and_are_never_followed(self) -> None:
        self.fx.minimal()
        outside = self.base / "outside"
        (outside / "dir").mkdir(parents=True)
        (outside / "target.md").write_text("`rules/zz-missing.md`\n", encoding="utf-8")
        (outside / "dir" / "inner.md").write_text("# Inner\n", encoding="utf-8")
        os.symlink(outside / "target.md", self.fx.root / "rules" / "link.md")
        os.symlink(outside / "dir", self.fx.root / "workflows" / "sub")
        (self.fx.root / "docs").mkdir()
        os.symlink(outside / "target.md", self.fx.root / "docs" / "link.md")
        os.symlink(outside / "dir", self.fx.root / "docs" / "linked")
        out = self.base / "inventory.json"

        inventory = self.extract(out=out)

        for path in ("rules/link.md", "workflows/sub"):
            row = self.row(inventory, path)
            self.assertEqual(row["entry"], "symlink")
            self.assertEqual({key: row[key] for key in NULL_CONTENT_FIELDS}, NULL_CONTENT_FIELDS)
        all_paths = [entry["path"] for entry in inventory["files"] + inventory["readers"]]
        self.assertFalse([path for path in all_paths if path.startswith(("workflows/sub/",
                                                                          "docs/link"))])
        self.assertNotIn(str(outside), out.read_text(encoding="utf-8"))

    def test_other_entry_is_recorded_without_being_opened(self) -> None:
        self.fx.minimal()
        os.mkfifo(self.fx.root / "rules" / "pipe")

        inventory = self.extract()

        row = self.row(inventory, "rules/pipe")
        self.assertEqual(row["entry"], "other")
        self.assertEqual({key: row[key] for key in NULL_CONTENT_FIELDS}, NULL_CONTENT_FIELDS)


class ReaderTests(ToolCase):
    EXPECTED_CLASSES = {
        "tests/fixtures/validator-runtime/case.txt": "frozen",
        "tests/check-alpha.sh": "active",
        "CLAUDE.md": "active",
        "README.md": "active",
        "principles/alpha-standards.md": "active",
        "templates/.ai/memory/state.md": "active",
        "hooks/alpha-hook.sh": "active",
        "scripts/alpha-tool.sh": "active",
        "docs/GUIDE.md": "active",
        ".ai/principles/coding.md": "active",
        ".ai/context/runbook.md": "active",
        ".ai/memory/architecture.md": "active",
        ".ai/README.md": "planning",
        ".ai/memory/state.md": "planning",
        ".ai/specs/01-alpha-change.md": "planning",
        ".ai/tasks/todo/task-01-alpha/state.md": "planning",
        ".ai/adr/0001-alpha.md": "history",
        ".ai/specs/completed/00-alpha.md": "history",
        ".ai/tasks/completed/task-00-alpha/state.md": "history",
        ".ai/memory/progress.md": "history",
        "docs/analysis/2020-01-01-alpha.md": "history",
        "docs/audits/2020-01-01-other-audit.md": "history",
    }
    NOT_READ = [
        "VERSION", ".gitignore", ".ai/memory/notes.md", ".ai/context/sub/extra.md",
        ".ai/principles/extra.txt", "docs/audits/2020-01-01-rules-workflows-audit.md",
        "docs/audits/2020-01-01-rules-workflows-audit.inventory.json",
        "docs/audits/2020-01-01-rules-workflows-audit.assessment.json",
        "scripts/audit-instructions.py", "scripts/check-audit-instructions.py",
        "scripts/__pycache__/alpha.txt", "scripts/alpha.pyc", "logs/run.md", "output/x.md",
    ]

    def build_readers(self) -> None:
        self.fx.minimal()
        for path in self.EXPECTED_CLASSES:
            self.fx.write(path, "Mentions `rules/alpha-flow.md`.\n")
        for path in self.NOT_READ:
            self.fx.write(path, "Mentions `rules/zz-missing.md`.\n")

    def test_each_reader_gets_the_first_matching_class(self) -> None:
        self.build_readers()

        inventory = self.extract()

        classes = {entry["path"]: entry["class"] for entry in inventory["readers"]}
        self.assertEqual(classes, self.EXPECTED_CLASSES)

    def test_audit_outputs_own_scripts_skipped_and_unclassed_files_are_not_readers(
            self) -> None:
        self.build_readers()

        inventory = self.extract()

        readers = {entry["path"] for entry in inventory["readers"]}
        self.assertEqual(sorted(readers & set(self.NOT_READ)), [])
        self.assertEqual(sorted(readers & {"rules/alpha-flow.md", "workflows/beta-step.md"}),
                         [])

    def test_reader_that_is_not_utf8_is_recorded_as_not_decoded(self) -> None:
        self.fx.minimal()
        data = b"\x1f\x8b\x08\x00\xff\xfe\n"
        self.fx.write("tests/fixtures/sample.gz", data)
        self.fx.write("docs/GUIDE.md", "line one\nline two")

        inventory = self.extract()

        readers = {entry["path"]: entry for entry in inventory["readers"]}
        self.assertEqual(readers["tests/fixtures/sample.gz"],
                         {"path": "tests/fixtures/sample.gz", "class": "active",
                          "sha256": sha256(data), "lines": 1, "decoded": False})
        self.assertEqual(readers["docs/GUIDE.md"]["decoded"], True)
        self.assertEqual(readers["docs/GUIDE.md"]["lines"], 2)


class ReadOnlyTests(ToolCase):
    def test_extract_changes_nothing_but_the_out_file(self) -> None:
        self.fx.minimal()
        self.fx.write("docs/GUIDE.md", "# Guide\n")
        self.fx.write(".ai/memory/state.md", "# State\n")
        self.fx.commit_all()
        tracked = self.fx.root / "rules" / "alpha-flow.md"
        os.utime(tracked, ns=(tracked.stat().st_atime_ns, tracked.stat().st_mtime_ns + 10**9))
        before = tree_digests(self.fx.root)
        out_relative = "docs/audits/2020-01-02-rules-workflows-audit.inventory.json"
        (self.fx.root / "docs" / "audits").mkdir()

        self.extract(out=self.fx.root / out_relative)

        after = tree_digests(self.fx.root)
        self.assertEqual(sorted(set(after) - set(before)), [out_relative])
        self.assertEqual({path: after[path] for path in before}, before)

    def test_existing_out_file_is_replaced_without_leftover_temporary_files(self) -> None:
        self.fx.minimal()
        target = self.base / "outputs"
        target.mkdir()
        out = target / "inventory.json"
        out.write_text("stale\n", encoding="utf-8")

        inventory = self.extract(out=out)

        self.assertEqual(inventory["schema_version"], 1)
        self.assertEqual(sorted(path.name for path in target.iterdir()), ["inventory.json"])


class RuntimeGuardTests(ToolCase):
    def test_interpreter_older_than_three_eleven_gets_the_guard_message_and_exit_two(
            self) -> None:
        self.fx.minimal()
        out = self.base / "inventory.json"
        code = (
            "import runpy, sys\n"
            "sys.version_info = (3, 10, 12, 'final', 0)\n"
            f"sys.argv = [{str(TOOL)!r}, 'extract', '--root', {str(self.fx.root)!r},"
            f" '--out', {str(out)!r}]\n"
            f"runpy.run_path({str(TOOL)!r}, run_name='__main__')\n"
        )

        result = subprocess.run([sys.executable, "-I", "-c", code], cwd=self.base,
                                env=self.fx.env, text=True, capture_output=True, timeout=60)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stderr.strip().splitlines(), [GUARD_MESSAGE])
        self.assertFalse(out.exists())

    def test_tool_starts_with_docstring_future_import_sys_import_and_version_guard(
            self) -> None:
        self.require_tool()
        source = TOOL.read_text(encoding="utf-8")
        body = ast.parse(source).body

        self.assertTrue(source.startswith("#!/usr/bin/env python3\n"))
        self.assertIsInstance(body[0], ast.Expr)
        self.assertIsInstance(body[0].value, ast.Constant)
        self.assertIsInstance(body[0].value.value, str)
        future = body[1]
        self.assertIsInstance(future, ast.ImportFrom)
        self.assertEqual((future.module, [alias.name for alias in future.names]),
                         ("__future__", ["annotations"]))
        self.assertIsInstance(body[2], ast.Import)
        self.assertEqual([alias.name for alias in body[2].names], ["sys"])
        guard = body[3]
        self.assertIsInstance(guard, ast.If)
        compared = ast.unparse(guard.test)
        self.assertIn("sys.version_info", compared)
        self.assertIn("(3, 11)", compared)

    def test_tool_imports_only_standard_library_modules(self) -> None:
        self.require_tool()
        tree = ast.parse(TOOL.read_text(encoding="utf-8"))
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0, "relative imports are not allowed")
                modules.add((node.module or "").split(".")[0])

        self.assertTrue(modules)
        self.assertEqual(sorted(modules - set(sys.stdlib_module_names)), [])

    def test_every_tool_function_is_fully_annotated(self) -> None:
        self.require_tool()
        tree = ast.parse(TOOL.read_text(encoding="utf-8"))
        missing: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arguments = node.args
                every = (arguments.posonlyargs + arguments.args + arguments.kwonlyargs
                         + [item for item in (arguments.vararg, arguments.kwarg) if item])
                unannotated = [arg.arg for arg in every
                               if arg.annotation is None and arg.arg not in ("self", "cls")]
                if node.returns is None or unannotated:
                    missing.append(f"{node.name}:{node.lineno}")

        self.assertEqual(missing, [])


class TextModelTests(ToolCase):
    def row_for(self, data: bytes) -> dict:
        self.fx.write("rules/alpha-flow.md", data)
        (self.fx.root / "workflows").mkdir(exist_ok=True)
        return self.row(self.extract(), "rules/alpha-flow.md")

    def test_front_matter_fences_crlf_and_preamble_give_documented_sections(self) -> None:
        preamble = (b"---\r\n"
                    b"description: Alpha flow step  \r\n"
                    b"trigger: always_on\r\n"
                    b"  continued value\r\n"
                    b"trigger: second\r\n"
                    b"\r\n"
                    b"---\r\n"
                    b"Intro line one\r\n"
                    b"\r\n"
                    b"Invocation: `/alpha-flow`\r\n")
        first = (b"## First part\r\n"
                 b"text words here\r\n"
                 b"```markdown\r\n"
                 b"## Not a section\r\n"
                 b"Invocation: inside fence\r\n"
                 b"```\r\n"
                 b"##no-space\r\n"
                 b"### Deeper heading\r\n")
        second = b"## Second part   \r\nlast line without newline"
        data = preamble + first + second

        row = self.row_for(data)

        self.assertEqual(row["encoding"], "utf-8")
        self.assertEqual((row["bytes"], row["lines"]), (len(data), 20))
        self.assertEqual(row["words"], len(data.decode("utf-8").split()))
        self.assertEqual(row["front_matter"], {
            "status": "present", "keys": ["description", "trigger", "trigger"],
            "trigger": "always_on", "description": "Alpha flow step",
            "continuation_lines": 1,
        })
        self.assertEqual(row["invocation_lines"], 1)
        expected = [
            {"heading": "(preamble)", "line": 1, "words": len(preamble.decode().split()),
             "bytes": len(preamble)},
            {"heading": "## First part", "line": 11, "words": len(first.decode().split()),
             "bytes": len(first)},
            {"heading": "## Second part", "line": 19, "words": len(second.decode().split()),
             "bytes": len(second)},
        ]
        self.assertEqual(row["sections"], expected)
        self.assertEqual(list(row["sections"][0]), SECTION_KEYS)
        self.assertEqual(sum(section["words"] for section in row["sections"]), row["words"])
        self.assertEqual(sum(section["bytes"] for section in row["sections"]), row["bytes"])

    def test_file_starting_with_a_level_two_heading_has_no_preamble(self) -> None:
        row = self.row_for(b"## Only part\nbody\n")

        self.assertEqual(row["sections"], [
            {"heading": "## Only part", "line": 1, "words": 4, "bytes": 18}])

    def test_empty_file_has_zero_words_and_no_sections(self) -> None:
        row = self.row_for(b"")

        self.assertEqual((row["sha256"], row["bytes"], row["lines"], row["encoding"],
                          row["words"]), (sha256(b""), 0, 0, "utf-8", 0))
        self.assertEqual(row["sections"], [])
        self.assertEqual(row["front_matter"], ABSENT_FRONT_MATTER)
        self.assertEqual(row["invocation_lines"], 0)

    def test_final_line_without_newline_is_counted(self) -> None:
        row = self.row_for(b"first\nsecond")

        self.assertEqual(row["lines"], 2)
        self.assertEqual(row["sections"], [
            {"heading": "(preamble)", "line": 1, "words": 2, "bytes": 12}])

    def test_unclosed_front_matter_leaves_the_whole_file_as_body(self) -> None:
        row = self.row_for(b"---\ndescription: Alpha\n## Body heading\ntext\n")

        self.assertEqual(row["front_matter"], {
            "status": "unclosed", "keys": [], "trigger": None, "description": None,
            "continuation_lines": 0})
        self.assertEqual([section["heading"] for section in row["sections"]],
                         ["(preamble)", "## Body heading"])

    def test_unclosed_fence_runs_to_the_end_of_the_file(self) -> None:
        row = self.row_for(b"## Open\n```\n## Hidden\nInvocation: `/alpha-flow`\n")

        self.assertEqual([section["heading"] for section in row["sections"]], ["## Open"])
        self.assertEqual(row["invocation_lines"], 0)

    def test_indented_tilde_fence_closes_only_on_a_run_at_least_as_long(self) -> None:
        row = self.row_for(b"## Start\n  ~~~~\n## Inside one\n  ~~~\n## Inside two\n"
                           b"```\n## Inside three\n   ~~~~~  \n## After\n")

        self.assertEqual([section["heading"] for section in row["sections"]],
                         ["## Start", "## After"])

    def test_byte_order_mark_is_kept_and_front_matter_reads_absent(self) -> None:
        data = "﻿---\ndescription: Alpha\n---\n".encode("utf-8")

        row = self.row_for(data)

        self.assertEqual(row["encoding"], "utf-8")
        self.assertEqual(row["bytes"], len(data))
        self.assertEqual(row["front_matter"], ABSENT_FRONT_MATTER)

    def test_invalid_utf8_audited_file_has_digests_but_no_text_model(self) -> None:
        data = b"## Heading\n\xff\xfe\n"

        row = self.row_for(data)

        self.assertEqual((row["entry"], row["sha256"], row["bytes"], row["lines"],
                          row["encoding"]), ("file", sha256(data), len(data), 2, "invalid"))
        self.assertEqual((row["words"], row["front_matter"], row["invocation_lines"],
                          row["sections"]), (None, None, None, []))

    def test_control_character_audited_file_has_no_word_count(self) -> None:
        data = b"## Heading\nalpha\x1ebeta\n"

        row = self.row_for(data)

        self.assertEqual((row["encoding"], row["words"], row["front_matter"],
                          row["invocation_lines"], row["sections"]),
                         ("control-character", None, None, None, []))

    def test_decodable_non_markdown_file_has_words_but_no_markdown_fields(self) -> None:
        self.fx.minimal()
        self.fx.write("harness/gamma/capabilities.json", '{"name": "gamma tool"}\n')

        row = self.row(self.extract(), "harness/gamma/capabilities.json")

        self.assertEqual((row["encoding"], row["words"], row["lines"]), ("utf-8", 3, 1))
        self.assertEqual((row["front_matter"], row["invocation_lines"], row["sections"]),
                         (None, None, []))


class GitStateTests(ToolCase):
    def setUp(self) -> None:
        super().setUp()
        if REAL_GIT is None:
            self.skipTest("git is not installed")

    def test_clean_commit_records_revision_and_tracked_files_ignoring_excluded_changes(
            self) -> None:
        self.fx.minimal()
        self.fx.write("docs/GUIDE.md", "# Guide\n")
        self.fx.write("VERSION", "1\n")
        self.fx.write("docs/audits/2020-01-01-rules-workflows-audit.md", "# Report\n")
        head = self.fx.commit_all()
        self.fx.write("VERSION", "2\n")
        self.fx.write("docs/audits/2020-01-01-rules-workflows-audit.md", "# Changed\n")

        inventory = self.extract()

        self.assertEqual(inventory["source_revision"], head)
        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})
        self.assertTrue(all(entry["tracked"] is True for entry in inventory["files"]))

    def test_dirty_tree_lists_changed_audited_and_reader_paths_in_path_order(self) -> None:
        self.fx.minimal()
        self.fx.write("docs/GUIDE.md", "# Guide\n")
        self.fx.write("VERSION", "1\n")
        self.fx.commit_all()
        self.fx.write("rules/alpha-flow.md", "# Alpha flow changed\n")
        self.fx.write("workflows/gamma-step.md", "# Gamma step\n")
        self.fx.write(".ai/memory/state.md", "# State\n")
        self.fx.write("VERSION", "2\n")
        self.fx.write("notes.txt", "scratch\n")

        inventory = self.extract()

        self.assertEqual(inventory["worktree"], {
            "state": "dirty",
            "paths": [".ai/memory/state.md", "rules/alpha-flow.md", "workflows/gamma-step.md"],
        })
        self.assertEqual(self.row(inventory, "workflows/gamma-step.md")["tracked"], False)
        self.assertEqual(self.row(inventory, "rules/alpha-flow.md")["tracked"], True)

    def test_root_that_git_cannot_read_yields_null_revision_and_unknown_worktree(
            self) -> None:
        self.fx.minimal()
        self.fx.write(".git", "gitdir: missing-repository\n")

        inventory = self.extract()

        self.assertIsNone(inventory["source_revision"])
        self.assertEqual(inventory["worktree"], {"state": "unknown", "paths": []})
        self.assertTrue(all(entry["tracked"] is None for entry in inventory["files"]))

    def test_missing_git_program_yields_null_revision_and_unknown_worktree(self) -> None:
        self.fx.minimal()
        self.fx.commit_all()
        empty_bin = self.base / "empty-bin"
        empty_bin.mkdir()
        env = {**self.fx.env, "PATH": str(empty_bin)}

        inventory = self.extract(env=env)

        self.assertIsNone(inventory["source_revision"])
        self.assertEqual(inventory["worktree"], {"state": "unknown", "paths": []})
        self.assertTrue(all(entry["tracked"] is None for entry in inventory["files"]))


class FailureExitTests(ToolCase):
    def test_root_without_rules_directory_is_invalid(self) -> None:
        (self.fx.root / "workflows").mkdir()
        out = self.base / "inventory.json"

        result = self.run_extract(out=out)

        self.assertIn("root-invalid", self.assert_single_error_line(result))
        self.assertFalse(out.exists())

    def test_missing_root_is_invalid(self) -> None:
        out = self.base / "inventory.json"

        result = self.run_extract(out=out, root=self.base / "absent")

        self.assertIn("root-invalid", self.assert_single_error_line(result))
        self.assertFalse(out.exists())

    def test_out_in_a_missing_directory_is_unwritable(self) -> None:
        self.fx.minimal()
        out = self.base / "absent" / "inventory.json"

        result = self.run_extract(out=out)

        self.assert_single_error_line(result)
        self.assertFalse(out.parent.exists())

    def test_out_naming_a_directory_is_unwritable_and_leaves_no_temporary_file(self) -> None:
        self.fx.minimal()
        target = self.base / "outputs"
        (target / "inventory.json").mkdir(parents=True)

        result = self.run_extract(out=target / "inventory.json")

        self.assert_single_error_line(result)
        self.assertEqual([path.name for path in target.iterdir()], ["inventory.json"])
        self.assertTrue((target / "inventory.json").is_dir())

    def test_usage_errors_print_one_error_line_and_exit_two(self) -> None:
        self.fx.minimal()
        for arguments in ([], ["extract", "--root", str(self.fx.root)],
                          ["extract", "--out", "x.json", "--unknown"], ["unknown-command"]):
            with self.subTest(arguments=arguments):
                result = run_tool(arguments, self.fx.env, self.base)

                self.assert_single_error_line(result)


class StandaloneTests(ToolCase):
    def test_tool_exists_and_neither_validator_nor_sync_names_it(self) -> None:
        self.require_tool()
        for script in ("validate-contracts.sh", "sync.sh"):
            text = (SOURCE_ROOT / "scripts" / script).read_text(encoding="utf-8")
            self.assertNotIn("audit-instructions", text, script)


class UnreadableRootTests(ToolCase):
    def setUp(self) -> None:
        super().setUp()
        if os.geteuid() == 0:
            self.skipTest("permission bits do not restrict the superuser")

    def assert_root_unreadable(self, result: subprocess.CompletedProcess[str],
                               out: Path) -> str:
        line = self.assert_single_error_line(result)
        self.assertTrue(line.startswith("ERROR: root-unreadable: "), line)
        self.assertNotIn(str(self.base), result.stderr)
        self.assertFalse(out.exists())
        return line

    def test_root_that_cannot_be_searched_is_reported_as_unreadable(self) -> None:
        self.fx.minimal()
        out = self.base / "inventory.json"
        os.chmod(self.fx.root, 0)
        try:
            result = self.run_extract(out=out)
        finally:
            os.chmod(self.fx.root, 0o755)

        self.assert_root_unreadable(result, out)

    def test_unreadable_directory_among_readers_is_reported_instead_of_skipped(self) -> None:
        self.fx.minimal()
        self.fx.write("docs/b.md", "# Readable\n")
        self.fx.write("docs/sub/a.md", "# Hidden\n")
        out = self.base / "inventory.json"
        os.chmod(self.fx.root / "docs" / "sub", 0)
        try:
            result = self.run_extract(out=out)
        finally:
            os.chmod(self.fx.root / "docs" / "sub", 0o755)

        self.assert_root_unreadable(result, out)

    def test_file_name_that_is_not_utf8_is_refused_without_writing(self) -> None:
        self.fx.minimal()
        for directory in ("rules", "docs"):
            with self.subTest(directory=directory):
                (self.fx.root / directory).mkdir(exist_ok=True)
                name = os.fsencode(self.fx.root / directory) + b"/bad-\xff.md"
                with open(name, "wb") as handle:
                    handle.write(b"# Bad name\n")
                out = self.base / f"{directory}-inventory.json"
                try:
                    result = self.run_extract(out=out)
                finally:
                    os.unlink(name)

                line = self.assert_root_unreadable(result, out)
                self.assertIn("UTF-8", line)


class GitIsolationTests(ToolCase):
    def setUp(self) -> None:
        super().setUp()
        if REAL_GIT is None:
            self.skipTest("git is not installed")

    def test_repository_configured_fsmonitor_program_is_never_run(self) -> None:
        self.fx.minimal()
        self.fx.commit_all()
        marker = self.base / "fsmonitor-ran"
        monitor = self.base / "fsmonitor.sh"
        monitor.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 1\n", encoding="utf-8")
        monitor.chmod(0o755)
        self.fx.git("config", "core.fsmonitor", str(monitor))
        self.fx.write("rules/alpha-flow.md", "# Alpha flow changed\n")
        marker.unlink(missing_ok=True)

        inventory = self.extract()

        self.assertFalse(marker.exists(), "git ran the repository's fsmonitor program")
        self.assertEqual(inventory["worktree"], {"state": "dirty",
                                                 "paths": ["rules/alpha-flow.md"]})


# ---------------------------------------------------------------------------
# Reference edges
# ---------------------------------------------------------------------------

EDGE_KEYS = [
    "source", "class", "line", "column", "context", "form", "raw", "load", "md_suffix",
    "in_spec09_grammar", "status", "targets",
]
TARGET_KEYS = ["path", "heading_status"]

# Rule stems: alpha-flow, r-one, shared-step, solo. Workflow stems: shared-step, w-one.
# rules/reference/deep-note.md is audited but nested, so it names no stem.
NODE_FILES = {
    "rules/r-one.md": ("# R one\n\n## Step 1\n\n### Detail\n\n## Scope — overview\n\n"
                       "## Sample Reading Rules\n"),
    "rules/alpha-flow.md": "# Alpha flow\n\n## Present\n",
    "rules/shared-step.md": "# Shared rule\n\n## Step 1\n",
    "rules/solo.md": "# Solo\n",
    "rules/reference/deep-note.md": "# Deep note\n",
    "workflows/w-one.md": "# W one\n\n## Step 1\n\n### Sub\n",
    "workflows/shared-step.md": "# Shared workflow\n\n## Other\n",
    "harness/gamma/always-on.md": "# Essentials\n",
    "templates/codex-global-AGENTS.md": "# Codex essentials\n",
}
TOP_LEVEL_RULES = ["rules/alpha-flow.md", "rules/r-one.md", "rules/shared-step.md",
                   "rules/solo.md"]
SHARED_PAIR = ["rules/shared-step.md", "workflows/shared-step.md"]
W_ONE = "workflows/w-one.md"
R_ONE = "rules/r-one.md"

Target = str | tuple[str, str]


def load_tool_module() -> object:
    """Load the tool's source as a module without running its command line."""
    spec = importlib.util.spec_from_file_location("audit_instructions_under_test", TOOL)
    if spec is None or spec.loader is None:
        raise AssertionError("the tool cannot be loaded as a module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def edge(source: str, lines: Sequence[str], text: str, raw: str, form: str, status: str,
         targets: Sequence[Target] = (), *, reader_class: str = "active",
         context: str = "span", load: bool = False, md_suffix: bool = False,
         grammar: bool = False, nth: int = 0) -> dict:
    """The expected edge for the `nth` occurrence of `raw` on the line `text`."""
    column = -1
    for _ in range(nth + 1):
        column = text.index(raw, column + 1)
    return {
        "source": source, "class": reader_class, "line": list(lines).index(text) + 1,
        "column": column, "context": context, "form": form, "raw": raw, "load": load,
        "md_suffix": md_suffix, "in_spec09_grammar": grammar, "status": status,
        "targets": [{"path": target, "heading_status": None} if isinstance(target, str)
                    else {"path": target[0], "heading_status": target[1]}
                    for target in targets],
    }


class EdgeCase(ToolCase):
    """Cases that extract a root holding known rule and workflow nodes plus sources."""

    maxDiff = None

    def setUp(self) -> None:
        super().setUp()
        for path, text in NODE_FILES.items():
            self.fx.write(path, text)

    def write_lines(self, path: str, lines: Sequence[str], newline: str = "\n"
                    ) -> Sequence[str]:
        self.fx.write(path, "".join(line + newline for line in lines))
        return lines

    def edges_of(self, inventory: dict, source: str) -> list[dict]:
        return [item for item in inventory["edges"] if item["source"] == source]

    def assert_edges(self, inventory: dict, source: str, expected: Sequence[dict]) -> None:
        ordered = sorted(expected, key=lambda item: (item["line"], item["column"]))
        self.assertEqual(self.edges_of(inventory, source), ordered)

    def defect_predicate(self) -> Callable[[dict], bool]:
        self.require_tool()
        predicate = getattr(load_tool_module(), "is_defect_edge", None)
        self.assertTrue(callable(predicate), "the tool exposes no is_defect_edge function")
        return predicate


class ControlExampleTests(EdgeCase):
    def test_section_reference_to_a_heading_the_rule_lacks_is_a_missing_heading_defect(
            self) -> None:
        source = "workflows/beta-step.md"
        lines = self.write_lines(source, ["# Beta step", "", "See `alpha-flow → ## Missing`.",
                                          "Then `alpha-flow → ## Present`."])

        inventory = self.extract()

        missing = edge(source, lines, lines[2], "alpha-flow → ## Missing", "section-ref",
                       "missing-heading", [("rules/alpha-flow.md", "missing-heading")],
                       grammar=True)
        present = edge(source, lines, lines[3], "alpha-flow → ## Present", "section-ref",
                       "resolved", [("rules/alpha-flow.md", "resolved")], grammar=True)
        self.assert_edges(inventory, source, [missing, present])
        predicate = self.defect_predicate()
        self.assertTrue(predicate(self.edges_of(inventory, source)[0]))
        self.assertFalse(predicate(self.edges_of(inventory, source)[1]))


class SpanCommandAndSectionTests(EdgeCase):
    SOURCE = "docs/GUIDE.md"

    def test_command_spans_resolve_workflow_stems_and_report_unknown_commands(self) -> None:
        lines = self.write_lines(self.SOURCE, ["`/w-one`", "`/w-one.md`", "`/zz-gone <path>`",
                                               "`/w-one <task-dir> --batch`"])

        inventory = self.extract()

        self.assert_edges(inventory, self.SOURCE, [
            edge(self.SOURCE, lines, lines[0], "/w-one", "command", "resolved", [W_ONE]),
            edge(self.SOURCE, lines, lines[1], "/w-one.md", "command", "resolved", [W_ONE],
                 md_suffix=True),
            edge(self.SOURCE, lines, lines[2], "/zz-gone <path>", "command",
                 "unknown-command"),
            edge(self.SOURCE, lines, lines[3], "/w-one <task-dir> --batch", "command",
                 "resolved", [W_ONE]),
        ])

    def test_slash_prefixed_section_reference_is_a_section_ref_never_a_command(self) -> None:
        lines = self.write_lines(self.SOURCE, ["`/w-one → ## Step 1`", "`w-one.md → ## Step 1`",
                                               "`rules/r-one.md`"])

        inventory = self.extract()

        self.assert_edges(inventory, self.SOURCE, [
            edge(self.SOURCE, lines, lines[0], "/w-one → ## Step 1", "section-ref", "resolved",
                 [(W_ONE, "resolved")]),
            edge(self.SOURCE, lines, lines[1], "w-one.md → ## Step 1", "section-ref",
                 "resolved", [(W_ONE, "resolved")], md_suffix=True),
            edge(self.SOURCE, lines, lines[2], "rules/r-one.md", "path", "resolved", [R_ONE]),
        ])

    def test_section_reference_candidates_follow_the_head(self) -> None:
        lines = self.write_lines(self.SOURCE, [
            "`shared-step → ## Step 1`",
            "`rule-shared-step → ## Step 1`",
            "`workflows/shared-step.md → ## Other`",
            "`rules/shared-step.md → ## Other`",
            "`/r-one → ## Step 1`",
            "`zz-gone → ## X`",
            "`rule-zz-gone → ## X`",
            "`state.md → ## X`",
            "`zz-gone → Plain words`",
            "`rules/zz-gone.md → ## X`",
        ])

        inventory = self.extract()

        s = self.SOURCE
        self.assert_edges(inventory, s, [
            edge(s, lines, lines[0], "shared-step → ## Step 1", "section-ref", "ambiguous-stem",
                 [("rules/shared-step.md", "resolved"),
                  ("workflows/shared-step.md", "missing-heading")]),
            edge(s, lines, lines[1], "rule-shared-step → ## Step 1", "section-ref", "resolved",
                 [("rules/shared-step.md", "resolved")]),
            edge(s, lines, lines[2], "workflows/shared-step.md → ## Other", "section-ref",
                 "resolved", [("workflows/shared-step.md", "resolved")]),
            edge(s, lines, lines[3], "rules/shared-step.md → ## Other", "section-ref",
                 "missing-heading", [("rules/shared-step.md", "missing-heading")]),
            edge(s, lines, lines[4], "/r-one → ## Step 1", "section-ref", "resolved",
                 [(R_ONE, "resolved")]),
            edge(s, lines, lines[5], "zz-gone → ## X", "section-ref", "missing-target"),
            edge(s, lines, lines[6], "rule-zz-gone → ## X", "section-ref", "missing-target"),
        ])

    def test_heading_components_resolve_inside_the_current_extent(self) -> None:
        cases = [
            ("r-one → ## Scope", R_ONE, "resolved-prefix"),
            ("r-one → Sample Reading Rules", R_ONE, "heading-unmarked"),
            ("r-one → Scope", R_ONE, "heading-unmarked"),
            ("r-one → Missing Part", R_ONE, "missing-heading"),
            ("r-one → # R one", R_ONE, "resolved"),
            ("r-one → ### Detail", R_ONE, "resolved"),
            ("r-one → ## Step 1 → ### Detail", R_ONE, "resolved"),
            ("r-one → ## Sample Reading Rules → ### Detail", R_ONE, "missing-heading"),
            ("r-one → ## Step 1 → 4.2", R_ONE, "resolved"),
            ("r-one → ## Scope → ### Detail", R_ONE, "missing-heading"),
            ("r-one → Step 1 → ### Detail", R_ONE, "heading-unmarked"),
            ("r-one → ## Missing → ### Detail", R_ONE, "missing-heading"),
            ("r-one → #### Step 1", R_ONE, "missing-heading"),
            ("w-one → ## Step 1 → ### Sub", W_ONE, "resolved"),
        ]
        lines = self.write_lines(self.SOURCE, [f"`{raw}`" for raw, _, _ in cases])

        inventory = self.extract()

        self.assert_edges(inventory, self.SOURCE, [
            edge(self.SOURCE, lines, f"`{raw}`", raw, "section-ref", status, [(path, status)])
            for raw, path, status in cases])


class SpanNameAndPathTests(EdgeCase):
    SOURCE = "docs/GUIDE.md"

    def test_rule_name_spans_resolve_only_rules(self) -> None:
        lines = self.write_lines(self.SOURCE, [
            "The `shared-step` rule applies.", "The `zz-gone` rules apply.",
            "Use `rule-r-one` here.", "Use `rule-zz-gone` here.", "Use `rule-shared-step` too.",
        ])

        inventory = self.extract()

        s = self.SOURCE
        self.assert_edges(inventory, s, [
            edge(s, lines, lines[0], "shared-step", "rule-name", "resolved",
                 ["rules/shared-step.md"]),
            edge(s, lines, lines[1], "zz-gone", "rule-name", "missing-target"),
            edge(s, lines, lines[2], "rule-r-one", "rule-name", "resolved", [R_ONE]),
            edge(s, lines, lines[3], "rule-zz-gone", "rule-name", "missing-target"),
            edge(s, lines, lines[4], "rule-shared-step", "rule-name", "resolved",
                 ["rules/shared-step.md"]),
        ])

    def test_path_spans_resolve_audited_paths_globs_and_skip_placeholders(self) -> None:
        lines = self.write_lines(self.SOURCE, [
            "`rules/r-one.md`", "`rules/zz-gone.md`", "`harness/gamma/always-on.md`",
            "`templates/codex-global-AGENTS.md`", "`rules/*.md`", "`rules/*/*.md`",
            "`harness/*/zz.json`", "`rules/<stem>.md`", "`rules/reference`",
            "`templates/other.md`",
        ])

        inventory = self.extract()

        s = self.SOURCE
        self.assert_edges(inventory, s, [
            edge(s, lines, lines[0], "rules/r-one.md", "path", "resolved", [R_ONE]),
            edge(s, lines, lines[1], "rules/zz-gone.md", "path", "missing-path"),
            edge(s, lines, lines[2], "harness/gamma/always-on.md", "path", "resolved",
                 ["harness/gamma/always-on.md"]),
            edge(s, lines, lines[3], "templates/codex-global-AGENTS.md", "path", "resolved",
                 ["templates/codex-global-AGENTS.md"]),
            edge(s, lines, lines[4], "rules/*.md", "glob", "resolved", TOP_LEVEL_RULES),
            edge(s, lines, lines[5], "rules/*/*.md", "glob", "resolved",
                 ["rules/reference/deep-note.md"]),
            edge(s, lines, lines[6], "harness/*/zz.json", "glob", "glob-empty"),
        ])

    def test_bare_name_spans_match_any_stem_and_report_shared_stems(self) -> None:
        lines = self.write_lines(self.SOURCE, ["`shared-step`", "`w-one`", "`solo`",
                                               "`deep-note`", "`zz-gone`"])

        inventory = self.extract()

        s = self.SOURCE
        self.assert_edges(inventory, s, [
            edge(s, lines, lines[0], "shared-step", "bare-name", "ambiguous-stem", SHARED_PAIR),
            edge(s, lines, lines[1], "w-one", "bare-name", "resolved", [W_ONE]),
            edge(s, lines, lines[2], "solo", "bare-name", "resolved", ["rules/solo.md"]),
        ])


class TokenGrammarTests(EdgeCase):
    SOURCE = "docs/GUIDE.md"

    def test_token_forms_in_text_resolve_in_order_with_masking(self) -> None:
        lines = self.write_lines(self.SOURCE, [
            "See rules/r-one.md and w-one.md here.",
            "Also shared-step.md and solo.md.",
            "Use rule-r-one or rule-zz-gone.",
            "Run /w-one or /zz-gone or /solo.",
            "Mention shared-step and w-one and solo.",
            "Glob workflows/*.md and harness/*/none.json.",
            "Path rules/zz-gone.md and rules/reference here.",
            "Adapter templates/codex-global-AGENTS.md here.",
        ])

        inventory = self.extract()

        s, text = self.SOURCE, "text"
        self.assert_edges(inventory, s, [
            edge(s, lines, lines[0], "rules/r-one.md", "path", "resolved", [R_ONE],
                 context=text),
            edge(s, lines, lines[0], "w-one.md", "md-name", "resolved", [W_ONE], context=text,
                 md_suffix=True),
            edge(s, lines, lines[1], "shared-step.md", "md-name", "ambiguous-stem",
                 SHARED_PAIR, context=text, md_suffix=True),
            edge(s, lines, lines[1], "solo.md", "md-name", "resolved", ["rules/solo.md"],
                 context=text, md_suffix=True),
            edge(s, lines, lines[2], "rule-r-one", "skill-name", "resolved", [R_ONE],
                 context=text),
            edge(s, lines, lines[2], "rule-zz-gone", "skill-name", "missing-target",
                 context=text),
            edge(s, lines, lines[3], "/w-one", "command", "resolved", [W_ONE], context=text),
            edge(s, lines, lines[4], "shared-step", "bare-name", "ambiguous-stem", SHARED_PAIR,
                 context=text),
            edge(s, lines, lines[4], "w-one", "bare-name", "resolved", [W_ONE], context=text),
            edge(s, lines, lines[5], "workflows/*.md", "glob", "resolved",
                 ["workflows/shared-step.md", W_ONE], context=text),
            edge(s, lines, lines[5], "harness/*/none.json", "glob", "glob-empty",
                 context=text),
            edge(s, lines, lines[6], "rules/zz-gone.md", "path", "missing-path",
                 context=text),
            edge(s, lines, lines[7], "templates/codex-global-AGENTS.md", "path", "resolved",
                 ["templates/codex-global-AGENTS.md"], context=text),
        ])

    def test_tokens_need_whole_token_boundaries_and_hyphenated_stems(self) -> None:
        lines = self.write_lines(self.SOURCE, [
            "Edges x_w-one w-one-x -w-one w-one_x and solo alone.",
            "Only w-one counts.",
        ])

        inventory = self.extract()

        self.assert_edges(inventory, self.SOURCE, [
            edge(self.SOURCE, lines, lines[1], "w-one", "bare-name", "resolved", [W_ONE],
                 context="text"),
        ])

    def test_span_that_no_span_form_matches_is_scanned_by_tokens(self) -> None:
        lines = self.write_lines(self.SOURCE, ["`see w-one.md and rule-r-one`",
                                               "`/w-one` and `w-one.md`"])

        inventory = self.extract()

        s = self.SOURCE
        self.assert_edges(inventory, s, [
            edge(s, lines, lines[0], "w-one.md", "md-name", "resolved", [W_ONE],
                 md_suffix=True),
            edge(s, lines, lines[0], "rule-r-one", "skill-name", "resolved", [R_ONE]),
            edge(s, lines, lines[1], "/w-one", "command", "resolved", [W_ONE]),
            edge(s, lines, lines[1], "w-one.md", "md-name", "resolved", [W_ONE],
                 md_suffix=True),
        ])

    def test_non_markdown_sources_use_only_the_token_grammar(self) -> None:
        json_source, text_source = "harness/gamma/capabilities.json", "docs/notes.txt"
        json_lines = self.write_lines(json_source,
                                      ['{"see": "`w-one` and `/w-one → ## Step 1`"}'])
        text_lines = self.write_lines(text_source, ["`rule-r-one → ## Step 1`"])

        inventory = self.extract()

        self.assert_edges(inventory, json_source, [
            edge(json_source, json_lines, json_lines[0], "w-one", "bare-name", "resolved",
                 [W_ONE], context="text"),
            edge(json_source, json_lines, json_lines[0], "/w-one", "command", "resolved",
                 [W_ONE], context="text"),
        ])
        self.assert_edges(inventory, text_source, [
            edge(text_source, text_lines, text_lines[0], "rule-r-one", "skill-name",
                 "resolved", [R_ONE], context="text"),
        ])


class EdgeContextTests(EdgeCase):
    def test_front_matter_and_fence_references_get_their_contexts(self) -> None:
        source = "docs/FENCES.md"
        lines = self.write_lines(source, [
            "---", "description: uses `/w-one` and rules/zz-gone.md", "---",
            "Body `w-one` here.", "```text", "Fenced `/w-one` and rules/zz-gone.md", "```",
            "  ~~~", "Unclosed `w-one`",
        ])

        inventory = self.extract()

        self.assert_edges(inventory, source, [
            edge(source, lines, lines[1], "/w-one", "command", "resolved", [W_ONE],
                 context="front-matter"),
            edge(source, lines, lines[1], "rules/zz-gone.md", "path", "missing-path",
                 context="front-matter"),
            edge(source, lines, lines[3], "w-one", "bare-name", "resolved", [W_ONE]),
            edge(source, lines, lines[5], "/w-one", "command", "resolved", [W_ONE],
                 context="fence"),
            edge(source, lines, lines[5], "rules/zz-gone.md", "path", "missing-path",
                 context="fence"),
            edge(source, lines, lines[8], "w-one", "bare-name", "resolved", [W_ONE],
                 context="fence"),
        ])
        predicate = self.defect_predicate()
        by_line = {(item["line"], item["raw"]): predicate(item)
                   for item in self.edges_of(inventory, source)}
        self.assertTrue(by_line[(2, "rules/zz-gone.md")])
        self.assertFalse(by_line[(6, "rules/zz-gone.md")])

    def test_validator_check_descriptions_and_comments_get_their_contexts(self) -> None:
        validator, other = "scripts/validate-contracts.sh", "scripts/other-tool.sh"
        lines = self.write_lines(validator, [
            "#!/bin/bash",
            "# covers rules/r-one.md and w-one",
            'check "rules/r-one.md names w-one" "$(grep -c w-one rules/r-one.md)"',
            '  check "indented \\"w-one\\" rule-r-one" "$(true)"',
            "    # indented comment rules/zz-gone.md",
            "echo w-one",
            'recheck "w-one"',
        ])
        other_lines = self.write_lines(other, ["# uses rules/r-one.md", 'check "w-one"'])

        inventory = self.extract()

        v, described, comment, text = validator, "check-description", "comment", "text"
        self.assert_edges(inventory, v, [
            edge(v, lines, lines[1], "rules/r-one.md", "path", "resolved", [R_ONE],
                 context=comment),
            edge(v, lines, lines[1], "w-one", "bare-name", "resolved", [W_ONE],
                 context=comment),
            edge(v, lines, lines[2], "rules/r-one.md", "path", "resolved", [R_ONE],
                 context=described),
            edge(v, lines, lines[2], "w-one", "bare-name", "resolved", [W_ONE],
                 context=described),
            edge(v, lines, lines[2], "w-one", "bare-name", "resolved", [W_ONE], context=text,
                 nth=1),
            edge(v, lines, lines[2], "rules/r-one.md", "path", "resolved", [R_ONE],
                 context=text, nth=1),
            edge(v, lines, lines[3], "w-one", "bare-name", "resolved", [W_ONE],
                 context=described),
            edge(v, lines, lines[3], "rule-r-one", "skill-name", "resolved", [R_ONE],
                 context=described),
            edge(v, lines, lines[4], "rules/zz-gone.md", "path", "missing-path",
                 context=comment),
            edge(v, lines, lines[5], "w-one", "bare-name", "resolved", [W_ONE], context=text),
            edge(v, lines, lines[6], "w-one", "bare-name", "resolved", [W_ONE], context=text),
        ])
        self.assert_edges(inventory, other, [
            edge(other, other_lines, other_lines[0], "rules/r-one.md", "path", "resolved",
                 [R_ONE], context=text),
            edge(other, other_lines, other_lines[1], "w-one", "bare-name", "resolved",
                 [W_ONE], context=text),
        ])

    def test_planning_history_and_frozen_references_are_recorded_but_never_defects(
            self) -> None:
        readers = {
            ".ai/memory/state.md": "planning", ".ai/specs/01-alpha-change.md": "planning",
            ".ai/adr/0001-alpha.md": "history", "docs/analysis/2020-01-01-alpha.md": "history",
            "tests/fixtures/validator-runtime/case.md": "frozen", "docs/ACTIVE.md": "active",
        }
        text = "Uses `rules/zz-gone.md` and `zz-gone → ## X`."
        for path in readers:
            self.write_lines(path, [text])

        inventory = self.extract()

        predicate = self.defect_predicate()
        for path, reader_class in readers.items():
            with self.subTest(source=path):
                self.assert_edges(inventory, path, [
                    edge(path, [text], text, "rules/zz-gone.md", "path", "missing-path",
                         reader_class=reader_class),
                    edge(path, [text], text, "zz-gone → ## X", "section-ref",
                         "missing-target", reader_class=reader_class),
                ])
                verdicts = [predicate(item) for item in self.edges_of(inventory, path)]
                self.assertEqual(verdicts, [reader_class == "active"] * 2)


class LoadLineTests(EdgeCase):
    def test_span_edges_on_load_lines_of_audited_markdown_are_load_edges(self) -> None:
        source, reader = "workflows/w-load.md", "docs/LOAD.md"
        lines = self.write_lines(source, [
            "Read `r-one` first.",
            "The `read` step names `w-one`.",
            "Loads rules/r-one.md and `w-one` now.",
            "The reader uses `w-one` daily.",
            "LOADING `rule-r-one` now.",
            "Then `r-one` is read.",
            "```",
            "Read `w-one` inside.",
            "```",
        ])
        reader_lines = self.write_lines(reader, ["Read `w-one` first."])

        inventory = self.extract()

        s = source
        self.assert_edges(inventory, s, [
            edge(s, lines, lines[0], "r-one", "bare-name", "resolved", [R_ONE], load=True),
            edge(s, lines, lines[1], "w-one", "bare-name", "resolved", [W_ONE]),
            edge(s, lines, lines[2], "rules/r-one.md", "path", "resolved", [R_ONE],
                 context="text"),
            edge(s, lines, lines[2], "w-one", "bare-name", "resolved", [W_ONE], load=True),
            edge(s, lines, lines[3], "w-one", "bare-name", "resolved", [W_ONE]),
            edge(s, lines, lines[4], "rule-r-one", "rule-name", "resolved", [R_ONE],
                 load=True, grammar=True),
            edge(s, lines, lines[5], "r-one", "bare-name", "resolved", [R_ONE], load=True),
            edge(s, lines, lines[7], "w-one", "bare-name", "resolved", [W_ONE],
                 context="fence"),
        ])
        self.assert_edges(inventory, reader, [
            edge(reader, reader_lines, reader_lines[0], "w-one", "bare-name", "resolved",
                 [W_ONE]),
        ])


class SpecGrammarFlagTests(EdgeCase):
    LINES = [
        "`w-one → ## Step 1`",
        "`/w-one`",
        "`rule-shared-step`",
        "`rules/solo.md`",
        "`rules/zz-gone.md`",
        "`w-one.md → ### Sub`",
        "`rules/*.md`",
        "`w-one`",
        "`r-one → Sample Reading Rules`",
        "`r-one → #### Deep`",
        "`workflows/w-one.md → ## Step 1`",
        "Text w-one.md here.",
        "## Sample Reading Rules",
    ]
    IN_GRAMMAR = {
        (1, "w-one → ## Step 1"): True, (2, "/w-one"): True, (3, "rule-shared-step"): True,
        (4, "rules/solo.md"): True, (5, "rules/zz-gone.md"): True,
        (6, "w-one.md → ### Sub"): True, (7, "rules/*.md"): False, (8, "w-one"): False,
        (9, "r-one → Sample Reading Rules"): False, (10, "r-one → #### Deep"): False,
        (11, "workflows/w-one.md → ## Step 1"): False, (12, "w-one.md"): False,
    }

    def test_grammar_flag_holds_only_for_span_forms_in_top_level_instruction_files(
            self) -> None:
        sources = {"rules/r-one.md": True, "harness/gamma/always-on.md": True,
                   "docs/G.md": False, "harness/gamma/notes.md": False,
                   "rules/reference/nested.md": False}
        for path in sources:
            self.write_lines(path, self.LINES)

        inventory = self.extract()

        for path, top_level in sources.items():
            with self.subTest(source=path):
                flags = {(item["line"], item["raw"]): item["in_spec09_grammar"]
                         for item in self.edges_of(inventory, path)}
                expected = {key: value and top_level for key, value in self.IN_GRAMMAR.items()}
                self.assertEqual(flags, expected)

    def test_token_found_inside_an_unmatched_span_is_never_in_the_grammar(self) -> None:
        source = "rules/r-one.md"
        lines = self.write_lines(source, ["`run /w-one now`", "`/w-one`"])

        inventory = self.extract()

        self.assert_edges(inventory, source, [
            edge(source, lines, lines[0], "/w-one", "command", "resolved", [W_ONE]),
            edge(source, lines, lines[1], "/w-one", "command", "resolved", [W_ONE],
                 grammar=True),
        ])


class EdgeEncodingTests(EdgeCase):
    def test_crlf_lines_match_without_the_carriage_return(self) -> None:
        self.fx.write("rules/crlf-rule.md", b"# Crlf\r\n## Step 1   \r\n")
        source = "workflows/w-crlf.md"
        lines = self.write_lines(source, ["See `crlf-rule → ## Step 1` and crlf-rule",
                                          "Path rules/crlf-rule.md"], newline="\r\n")

        inventory = self.extract()

        s = source
        self.assert_edges(inventory, s, [
            edge(s, lines, lines[0], "crlf-rule → ## Step 1", "section-ref", "resolved",
                 [("rules/crlf-rule.md", "resolved")], grammar=True),
            edge(s, lines, lines[0], "crlf-rule", "bare-name", "resolved",
                 ["rules/crlf-rule.md"], context="text", nth=1),
            edge(s, lines, lines[1], "rules/crlf-rule.md", "path", "resolved",
                 ["rules/crlf-rule.md"], context="text"),
        ])

    def test_undecodable_sources_add_no_edges_and_undecodable_candidates_have_no_headings(
            self) -> None:
        self.fx.write("docs/BAD.md", b"`rules/zz-gone.md`\n\xff\n")
        self.fx.write("rules/bad-bytes.md", b"## A\n`/w-one`\n\xff\n")
        self.fx.write("rules/ctl-rule.md", b"## A\n`/w-one`\n\x1e\n")
        outside = self.base / "outside.md"
        outside.write_text("## A\n`/w-one`\n", encoding="utf-8")
        os.symlink(outside, self.fx.root / "rules" / "link-rule.md")
        source = "docs/OK.md"
        lines = self.write_lines(source, ["`bad-bytes → ## A`", "`ctl-rule → ## A`",
                                          "`link-rule → ## A`", "`ctl-rule`"])

        inventory = self.extract()

        s = source
        self.assert_edges(inventory, s, [
            edge(s, lines, lines[0], "bad-bytes → ## A", "section-ref", "missing-heading",
                 [("rules/bad-bytes.md", "missing-heading")]),
            edge(s, lines, lines[1], "ctl-rule → ## A", "section-ref", "missing-heading",
                 [("rules/ctl-rule.md", "missing-heading")]),
            edge(s, lines, lines[2], "link-rule → ## A", "section-ref", "missing-heading",
                 [("rules/link-rule.md", "missing-heading")]),
            edge(s, lines, lines[3], "ctl-rule", "bare-name", "resolved",
                 ["rules/ctl-rule.md"]),
        ])
        for path in ("docs/BAD.md", "rules/bad-bytes.md", "rules/ctl-rule.md",
                     "rules/link-rule.md"):
            self.assertEqual(self.edges_of(inventory, path), [], path)


class EdgeListTests(EdgeCase):
    def test_edges_have_documented_keys_and_are_ordered_by_source_line_and_column(
            self) -> None:
        self.write_lines("workflows/w-order.md", ["See w-one and `r-one` and rules/r-one.md.",
                                                  "`w-one`"])
        self.write_lines("docs/A.md", ["`r-one` then w-one"])
        self.write_lines(".ai/memory/state.md", ["`w-one`"])

        inventory = self.extract()

        edges = inventory["edges"]
        positions = [(item["source"], item["line"], item["column"]) for item in edges]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(positions, [
            (".ai/memory/state.md", 1, 1), ("docs/A.md", 1, 1), ("docs/A.md", 1, 13),
            ("workflows/w-order.md", 1, 4), ("workflows/w-order.md", 1, 15),
            ("workflows/w-order.md", 1, 26), ("workflows/w-order.md", 2, 1),
        ])
        for item in edges:
            self.assertEqual(list(item), EDGE_KEYS)
            for target in item["targets"]:
                self.assertEqual(list(target), TARGET_KEYS)


class DefectPredicateTests(EdgeCase):
    def test_defect_predicate_follows_class_context_form_status_and_suffix(self) -> None:
        source = "docs/DEFECTS.md"
        cases = [
            ("`r-one → ## Scope`", "r-one → ## Scope", False),
            ("`r-one → Scope`", "r-one → Scope", True),
            ("`shared-step`", "shared-step", False),
            ("Mention shared-step here.", "shared-step", False),
            ("`w-one.md → ## Step 1`", "w-one.md → ## Step 1", True),
            ("`/w-one`", "/w-one", False),
            ("`/zz-gone`", "/zz-gone", True),
            ("`shared-step → ## Step 1`", "shared-step → ## Step 1", True),
            ("`rules/*.md`", "rules/*.md", False),
            ("`harness/*/zz.json`", "harness/*/zz.json", True),
            ("`r-one → ## Step 1`", "r-one → ## Step 1", False),
            ("Read w-one.md now.", "w-one.md", True),
        ]
        self.write_lines(source, [text for text, _, _ in cases])

        inventory = self.extract()

        predicate = self.defect_predicate()
        verdicts = {(item["line"], item["raw"]): predicate(item)
                    for item in self.edges_of(inventory, source)}
        self.assertEqual(verdicts, {(index + 1, raw): defect
                                    for index, (_, raw, defect) in enumerate(cases)})


# ---------------------------------------------------------------------------
# Candidates, legacy mentions and duplicate clusters
# ---------------------------------------------------------------------------

REPEAT_LOAD_KEYS = ["id", "caller", "callee", "target"]
LINE_CANDIDATE_KEYS = ["id", "source", "line", "text"]
LEGACY_KEYS = ["source", "line", "column", "term", "text"]
CLUSTER_KEYS = ["id", "sha256", "words", "text", "members"]
MEMBER_KEYS = ["path", "line_start", "line_end"]
CANDIDATE_LIST_KEYS = ["repeat_loads", "full_output", "harness_names", "legacy_mentions",
                       "duplicate_clusters"]
LOAD_R_ONE = "Load the `r-one` rule."


def workflow_path(stem: str) -> str:
    return f"workflows/{stem}.md"


def repeat_load(number: int, caller: str, callee: str, target: str = R_ONE) -> dict:
    return {"id": f"RL-{number:03d}", "caller": workflow_path(caller),
            "callee": workflow_path(callee), "target": target}


def collapsed(text: str) -> str:
    return " ".join(text.split())


def line_candidate(prefix: str, number: int, source: str, line: int, text: str) -> dict:
    return {"id": f"{prefix}-{number:03d}", "source": source, "line": line,
            "text": collapsed(text)[:160]}


def legacy_mention(source: str, line: int, text: str, term_text: str, nth: int = 0) -> dict:
    column = -1
    for _ in range(nth + 1):
        column = text.index(term_text, column + 1)
    return {"source": source, "line": line, "column": column, "term": term_text.lower(),
            "text": collapsed(text)[:160]}


def cluster(number: int, text: str, members: Sequence[tuple[str, int, int]]) -> dict:
    return {"id": f"DUP-{number:03d}", "sha256": sha256(text.encode("utf-8")),
            "words": len(text.split()), "text": text,
            "members": [{"path": path, "line_start": start, "line_end": end}
                        for path, start, end in members]}


class CandidateCase(ToolCase):
    """Cases that write small workflow and rule trees and read the candidate lists."""

    maxDiff = None

    def setUp(self) -> None:
        super().setUp()
        self.make_node_directories(self.fx)

    @staticmethod
    def make_node_directories(fixture: FixtureRoot) -> None:
        for name in ("rules", "workflows"):
            (fixture.root / name).mkdir(exist_ok=True)

    def write_lines(self, path: str, lines: Sequence[str],
                    fixture: FixtureRoot | None = None) -> Sequence[str]:
        (fixture or self.fx).write(path, "".join(line + "\n" for line in lines))
        return lines

    def write_workflow(self, stem: str, lines: Sequence[str],
                       fixture: FixtureRoot | None = None, invocable: bool = True) -> None:
        header = [f"# {stem}"] + ([f"Invocation: `/{stem}`"] if invocable else [])
        self.write_lines(workflow_path(stem), header + list(lines), fixture)

    def fresh_fixture(self, name: str) -> FixtureRoot:
        base = self.base / name
        base.mkdir()
        fixture = FixtureRoot(base)
        self.make_node_directories(fixture)
        return fixture

    def extract_fixture(self, fixture: FixtureRoot) -> dict:
        out = fixture.base / "inventory.json"
        result = self.run_extract(out=out, root=fixture.root, env=fixture.env)
        self.assertEqual(result.returncode, 0,
                         f"extract failed: stdout={result.stdout!r} stderr={result.stderr!r}")
        return parse_inventory(out.read_text(encoding="utf-8"))

    def build_call_graph(self, fixture: FixtureRoot | None = None) -> None:
        (fixture or self.fx).write(R_ONE, "# R one\n")
        self.write_workflow("w-root", [LOAD_R_ONE, "Run `/w-child`.", "see `/w-a`",
                                       "Do not run `/w-b`", "**stop**: run `/w-a` first"],
                            fixture)
        self.write_workflow("w-child", [LOAD_R_ONE], fixture)
        self.write_workflow("w-a", [LOAD_R_ONE, "Run `/w-b` next."], fixture)
        self.write_workflow("w-b", [LOAD_R_ONE, "Then run `/w-a`."], fixture)
        self.write_workflow("HUB", [LOAD_R_ONE, "Run `/w-root`, then run `/w-child`."],
                            fixture, invocable=False)


class RepeatLoadTests(CandidateCase):
    NOT_CALLS = [
        "see `/w-child`",
        "Do not run `/w-child`",
        "**stop**: run `/w-child` first",
        "Don't run `/w-child` here.",
        "Never call `/w-child` directly.",
        "Run the checks → see `/w-child`.",
        "Run the checks — see `/w-child`.",
        "Run the checks (see `/w-child`).",
        "Run the checks; the result names `/w-child`.",
        "Running `/w-child` is optional.",
    ]
    CALLS = [
        "If no file remains, run `/w-child`.",
        "Run `/w-child`. It does not ask.",
        "Run /w-child now.",
        "Run `a.b` with `/w-child`.",
        "Run `/w-child`; **stop** after it.",
        "Invoke the step: then delegate to `/w-child`.",
        "Run it and never skip `/w-child`.",
        "CALLS `/w-child` once.",
    ]

    def test_calls_between_invocable_workflows_that_share_a_load_are_repeat_loads(
            self) -> None:
        self.build_call_graph()

        inventory = self.extract()

        self.assertEqual(inventory["repeat_loads"], [
            repeat_load(1, "w-a", "w-b"),
            repeat_load(2, "w-b", "w-a"),
            repeat_load(3, "w-root", "w-child"),
        ])

    def test_only_a_call_verb_without_earlier_negation_or_stop_marker_makes_a_call(
            self) -> None:
        control = repeat_load(1, "w-ctl", "w-child")
        cases = [(line, False) for line in self.NOT_CALLS]
        cases += [(line, True) for line in self.CALLS]
        for index, (line, is_call) in enumerate(cases):
            with self.subTest(line=line):
                fixture = self.fresh_fixture(f"case-{index}")
                fixture.write(R_ONE, "# R one\n")
                self.write_workflow("w-root", [LOAD_R_ONE, line], fixture)
                self.write_workflow("w-child", [LOAD_R_ONE], fixture)
                self.write_workflow("w-ctl", [LOAD_R_ONE, "Run `/w-child`."], fixture)

                inventory = self.extract_fixture(fixture)

                expected = [control]
                if is_call:
                    expected.append(repeat_load(2, "w-root", "w-child"))
                self.assertEqual(inventory["repeat_loads"], expected)

    def test_each_shared_single_target_load_of_a_call_pair_is_one_candidate(self) -> None:
        for path in ("rules/r-one.md", "rules/r-two.md", "rules/r-three.md",
                     "rules/shared-step.md", "workflows/shared-step.md"):
            self.fx.write(path, "# Node\n")
        self.write_workflow("w-p", [
            "Load the `r-two` rule.",
            "Load the `r-one` rule and the `r-three` rule.",
            "Read `shared-step` first.",
            "Run `/w-q`.",
            "Then run `/w-q` again.",
        ])
        self.write_workflow("w-q", ["Load the `r-one` rule and the `r-two` rule.",
                                    "Read `shared-step` too."])

        inventory = self.extract()

        self.assertEqual(inventory["repeat_loads"], [
            repeat_load(1, "w-p", "w-q", "rules/r-one.md"),
            repeat_load(2, "w-p", "w-q", "rules/r-two.md"),
        ])

    def test_commands_that_are_not_workflow_calls_add_no_candidates(self) -> None:
        self.fx.write(R_ONE, "# R one\n")
        self.write_lines("rules/r-caller.md", [LOAD_R_ONE, "Run `/w-q`."])
        self.write_lines(workflow_path("w-p"), [
            "---",
            "description: Utility — run `/w-q` first",
            "---",
            "# w-p",
            "Invocation: `/w-p`",
            LOAD_R_ONE,
            "```",
            "Run `/w-q`.",
            "```",
            "Run `/w-p` again.",
            "Run `/zz-gone` now.",
            "See `/w-q` for details.",
        ])
        self.write_workflow("w-q", [LOAD_R_ONE, "Compare with /w-p."])
        self.write_workflow("w-x", [LOAD_R_ONE, "Run `/w-y`."])
        self.write_workflow("w-y", [LOAD_R_ONE])

        inventory = self.extract()

        self.assertEqual(inventory["repeat_loads"], [repeat_load(1, "w-x", "w-y")])


class LineCandidateTests(CandidateCase):
    def test_full_output_and_harness_name_lines_of_audited_markdown_are_candidates(
            self) -> None:
        source = workflow_path("w-text")
        lines = self.write_lines(source, [
            "---",
            "description: Paste the full output to Codex",
            "---",
            "# W text",
            "paste the full test output",
            "Ask Codex first.",
            "```",
            "full log from codex",
            "```",
            "Nothing to flag here.",
        ])

        inventory = self.extract()

        self.assertEqual(inventory["full_output"],
                         [line_candidate("FO", 1, source, 5, lines[4])])
        self.assertEqual(inventory["harness_names"],
                         [line_candidate("HN", 1, source, 6, lines[5])])

    def test_candidate_lines_are_numbered_by_source_and_line_with_collapsed_and_cut_text(
            self) -> None:
        long_line = "Keep  the\tfull output " + " ".join(["abcdefghi"] * 20)
        harness = self.write_lines("harness/h/always-on.md", ["Show the raw stdout to claude."])
        rule = self.write_lines("rules/r-b.md", ["# R b", "The whole diff goes to Claude Code.",
                                                 long_line])
        flow = self.write_lines(workflow_path("w-a"), [
            "# W a", "Keep  the\tfull output here.", "The fullness of output is fine.",
            "codexes and claudette stay quiet.",
        ])
        self.fx.write("harness/h/config.json", '{"note": "full output for codex"}\n')
        self.fx.write("docs/GUIDE.md", "Full output goes to Codex.\n")

        inventory = self.extract()

        self.assertEqual(inventory["full_output"], [
            line_candidate("FO", 1, "harness/h/always-on.md", 1, harness[0]),
            line_candidate("FO", 2, "rules/r-b.md", 2, rule[1]),
            line_candidate("FO", 3, "rules/r-b.md", 3, rule[2]),
            line_candidate("FO", 4, workflow_path("w-a"), 2, flow[1]),
        ])
        self.assertEqual(len(inventory["full_output"][2]["text"]), 160)
        self.assertEqual(inventory["harness_names"], [
            line_candidate("HN", 1, "harness/h/always-on.md", 1, harness[0]),
            line_candidate("HN", 2, "rules/r-b.md", 2, rule[1]),
        ])


class LegacyMentionTests(CandidateCase):
    def test_legacy_terms_in_a_rule_yield_two_mentions_and_not_a_longer_devin_word(
            self) -> None:
        source = "rules/r-legacy.md"
        lines = self.write_lines(source, ["# R legacy",
                                          "Use Windsurf with `.devin/` but not devinly."])

        inventory = self.extract()

        self.assertEqual(inventory["legacy_mentions"], [
            legacy_mention(source, 2, lines[1], "Windsurf"),
            legacy_mention(source, 2, lines[1], "devin"),
        ])

    def test_legacy_mentions_cover_whole_audited_markdown_and_json_files_only(self) -> None:
        config = '{"tool": "Devin", "x": "devin-cli"}'
        self.fx.write("harness/h/config.json", config + "\n")
        self.fx.write("harness/h/run.sh", "windsurf\n")
        self.fx.write("docs/GUIDE.md", "Windsurf\n")
        zone = self.write_lines("rules/r-zone.md", [
            "---", "trigger: always_on (Windsurf semantics)", "---", "# Zone", "```",
            "windsurfing  with CODEIUM", "```",
        ])
        template = self.write_lines("templates/codex-global-AGENTS.md", ["Codeium and devin."])

        inventory = self.extract()

        self.assertEqual(inventory["legacy_mentions"], [
            legacy_mention("harness/h/config.json", 1, config, "Devin"),
            legacy_mention("harness/h/config.json", 1, config, "devin"),
            legacy_mention("rules/r-zone.md", 2, zone[1], "Windsurf"),
            legacy_mention("rules/r-zone.md", 6, zone[5], "windsurf"),
            legacy_mention("rules/r-zone.md", 6, zone[5], "CODEIUM"),
            legacy_mention("templates/codex-global-AGENTS.md", 1, template[0], "Codeium"),
            legacy_mention("templates/codex-global-AGENTS.md", 1, template[0], "devin"),
        ])


class DuplicateClusterTests(CandidateCase):
    EIGHT = "Every audited file keeps exactly one map row."
    SEVEN = "Every reader keeps exactly one class label."

    def test_sentence_of_eight_words_shared_by_two_rules_is_one_cluster_and_seven_none(
            self) -> None:
        self.write_lines("rules/r-a.md", ["# R a", "", "Intro text for a. " + self.EIGHT, "",
                                          self.SEVEN])
        self.write_lines("rules/r-b.md", ["# R b", "", self.EIGHT + " Closing words for b.", "",
                                          self.SEVEN])

        inventory = self.extract()

        self.assertEqual(inventory["duplicate_clusters"], [
            cluster(1, self.EIGHT, [("rules/r-a.md", 3, 3), ("rules/r-b.md", 3, 3)]),
        ])

    def test_quote_indentation_and_list_markers_are_stripped_and_lines_joined(self) -> None:
        self.write_lines("rules/r-c.md", ["> - Every audited file keeps",
                                          ">   exactly one map row."])
        self.write_lines(workflow_path("w-d"),
                         ["1. Every   audited file keeps exactly one map row."])
        self.write_lines(workflow_path("w-e"), ["Intro line.", "", "    + Every audited file",
                                                "      keeps exactly one map row."])
        self.write_lines(workflow_path("w-f"), ["2) Every audited file keeps exactly one map row."])

        inventory = self.extract()

        self.assertEqual(inventory["duplicate_clusters"], [
            cluster(1, self.EIGHT, [("rules/r-c.md", 1, 2), (workflow_path("w-d"), 1, 1),
                                    (workflow_path("w-e"), 3, 4),
                                    (workflow_path("w-f"), 1, 1)]),
        ])

    def test_paragraphs_split_into_sentences_after_terminal_punctuation(self) -> None:
        alpha = "Alpha sentence names eight plain words right here!"
        beta = "Beta sentence keeps version 3.5 intact as written?"
        gamma = "Gamma sentence ends without any punctuation mark at all"
        delta = "Delta sentence closes with a plain full stop."
        self.write_lines("rules/r-s.md", ["# R s", "", f"{alpha} {beta}", f"{delta} {gamma}"])
        self.write_lines(workflow_path("w-s"), [gamma, "", delta, "", beta, "", alpha])

        inventory = self.extract()

        flow = workflow_path("w-s")
        self.assertEqual(inventory["duplicate_clusters"], [
            cluster(1, alpha, [("rules/r-s.md", 3, 3), (flow, 7, 7)]),
            cluster(2, beta, [("rules/r-s.md", 3, 3), (flow, 5, 5)]),
            cluster(3, delta, [("rules/r-s.md", 4, 4), (flow, 3, 3)]),
            cluster(4, gamma, [("rules/r-s.md", 4, 4), (flow, 1, 1)]),
        ])

    def test_unit_repeated_in_one_file_and_cluster_order_follow_first_member(self) -> None:
        zeta = "Zeta rule repeats this sentence twice in one file."
        alpha = "Alpha rule shares this sentence with one workflow file."
        self.write_lines("rules/r-m.md", [zeta, "", alpha, "", zeta])
        self.write_lines(workflow_path("w-m"), [alpha])

        inventory = self.extract()

        self.assertEqual(inventory["duplicate_clusters"], [
            cluster(1, zeta, [("rules/r-m.md", 1, 1), ("rules/r-m.md", 5, 5)]),
            cluster(2, alpha, [("rules/r-m.md", 3, 3), (workflow_path("w-m"), 1, 1)]),
        ])

    def test_headings_separators_fences_front_matter_and_other_files_give_no_units(
            self) -> None:
        table_row = "| First part. Second part | third cell |"
        lines = [
            "---", "description: Every front matter line keeps one map row now.", "---",
            "## Every audited file keeps exactly one map row here", "", table_row,
            "| --- | --- | --- | --- |", "", "```",
            "Every fenced line keeps exactly one map row now.", "```",
        ]
        self.write_lines("rules/x-one.md", lines)
        self.write_lines("rules/x-two.md", lines)
        other = "Every other file keeps exactly one map row now.\n"
        for path in ("docs/A.md", "docs/B.md", "harness/h/a.txt", "harness/h/b.txt"):
            self.fx.write(path, other)
        for path in ("rules/bad-a.md", "rules/bad-b.md"):
            self.fx.write(path, other.encode("utf-8") + b"\xff\n")
        for path in ("rules/ctl-a.md", "rules/ctl-b.md"):
            self.fx.write(path, other + "\x1e\n")

        inventory = self.extract()

        self.assertEqual(inventory["duplicate_clusters"], [
            cluster(1, table_row, [("rules/x-one.md", 6, 6), ("rules/x-two.md", 6, 6)]),
        ])


class CandidateInventoryTests(CandidateCase):
    def test_candidate_lists_have_documented_keys_and_repeat_runs_are_byte_identical(
            self) -> None:
        self.build_call_graph()
        self.write_lines("rules/r-text.md", [
            "paste the full test output", "Ask Codex first.", "Use Windsurf here.",
            DuplicateClusterTests.EIGHT,
        ])
        self.write_lines("rules/r-copy.md", [DuplicateClusterTests.EIGHT])
        first, second = self.base / "first.json", self.base / "second.json"

        inventory = self.extract(out=first)
        self.extract(out=second)

        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertNotIn(str(self.base), first.read_text(encoding="utf-8"))
        self.assertEqual(list(inventory)[-5:], CANDIDATE_LIST_KEYS)
        expected_keys = {"repeat_loads": REPEAT_LOAD_KEYS, "full_output": LINE_CANDIDATE_KEYS,
                         "harness_names": LINE_CANDIDATE_KEYS, "legacy_mentions": LEGACY_KEYS,
                         "duplicate_clusters": CLUSTER_KEYS}
        for key, keys in expected_keys.items():
            with self.subTest(list=key):
                self.assertNotEqual(inventory[key], [])
                for entry in inventory[key]:
                    self.assertEqual(list(entry), keys)
        for entry in inventory["duplicate_clusters"]:
            for found in entry["members"]:
                self.assertEqual(list(found), MEMBER_KEYS)


class HomePathRewriteTests(CandidateCase):
    def test_home_directory_prefixes_in_copied_text_become_tilde_paths(self) -> None:
        shared = "Install the helper from /home/someone/tools/x and copy /Users/someone/y here."
        variant = "Install the helper from /home/other/tools/x and copy /Users/else/y here."
        rewritten = "Install the helper from ~/tools/x and copy ~/y here."
        output_line = "Keep the full output of Codex in /home/someone/logs/run.txt now."
        legacy_line = "Windsurf lives in /Users/someone/apps now."
        self.write_lines("rules/r-home-a.md", [shared, "", output_line, "", legacy_line])
        self.write_lines("rules/r-home-b.md", [shared])
        self.write_lines("rules/r-home-c.md", [variant])
        out = self.base / "inventory.json"

        inventory = self.extract(out=out)

        source = "rules/r-home-a.md"
        self.assertEqual(inventory["duplicate_clusters"], [
            cluster(1, rewritten, [(source, 1, 1), ("rules/r-home-b.md", 1, 1),
                                   ("rules/r-home-c.md", 1, 1)]),
        ])
        output_text = "Keep the full output of Codex in ~/logs/run.txt now."
        self.assertEqual(inventory["full_output"],
                         [line_candidate("FO", 1, source, 3, output_text)])
        self.assertEqual(inventory["harness_names"],
                         [line_candidate("HN", 1, source, 3, output_text)])
        self.assertEqual(inventory["legacy_mentions"], [
            {"source": source, "line": 5, "column": 0, "term": "windsurf",
             "text": "Windsurf lives in ~/apps now."},
        ])
        text = out.read_text(encoding="utf-8")
        self.assertNotIn("/home/", text)
        self.assertNotIn("/Users/", text)

    def test_home_rewrite_needs_a_home_directory_and_a_name_segment(self) -> None:
        line = ("Keep the full output in /homestead/x, /home/ alone, /Users/ too, ~/kept/y "
                "and /home/someone/z.")
        kept = ("Keep the full output in /homestead/x, /home/ alone, /Users/ too, ~/kept/y "
                "and ~/z.")
        self.write_lines("rules/r-paths.md", [line])

        inventory = self.extract()

        self.assertEqual(inventory["full_output"],
                         [line_candidate("FO", 1, "rules/r-paths.md", 1, kept)])


AUDIT_DATE = "2026-01-02"
REPORT_PATH = f"docs/audits/{AUDIT_DATE}-rules-workflows-audit.md"
INVENTORY_PATH = f"docs/audits/{AUDIT_DATE}-rules-workflows-audit.inventory.json"
ASSESSMENT_PATH = f"docs/audits/{AUDIT_DATE}-rules-workflows-audit.assessment.json"
ROLE = "Implementer"
ALPHA = "rules/alpha-flow.md"
DELTA = "rules/delta-rule.md"
BETA = "workflows/beta-step.md"
GAMMA = "workflows/gamma-run.md"
CAPS = "harness/x/caps.json"
LINK = "harness/x/link.json"
BLOB = "harness/x/blob.bin"
GUIDE = "docs/GUIDE.md"
SHARED_SENTENCE = "Every change keeps the recorded state on disk for later readers."
PHASE_DISCOVERY = "rules/phase-discovery.md"
PHASE_DISCOVERY_TEXT = (
    "# Phase discovery\n\nThe phase starts here.\n\n## Codebase Reading Rules\n\n"
    "- Inspect the target files before any proposal.\n"
    "- Cite each observed line by its number.\n\n## Decision Protocol\n\n"
    "Decide alone when the evidence is sufficient.\nRecord the decision with its reason.\n\n"
    "## Other\n\nUnrelated text sits outside both sections.\n")
STATEMENT_UNIT_LINES = (7, 8, 12)
DISCOVERY_BOOTSTRAP = "rules/bootstrap-discovery.md"
DISCOVERY_CONDUCT = "rules/protocol-discovery-conduct.md"
AUTONOMOUS_DECISION = "rules/protocol-autonomous-decision.md"
DISCOVERY_OVERFLOW = "rules/reference/discovery-examples.md"
KIND_PREFIXED_RULE_RE = re.compile(r"rules/(bootstrap|contract|protocol|procedure)-[^/]+\.md")
SPEC09_PATH = ".ai/specs/09-synthetic-migration.md"
SPEC09_ANY = ".ai/specs/09-*.md:0"
SPEC09_CURRENT = "The conduct rule covers every statement unit."
SPEC09_TEXT = (
    "# 09. Synthetic naming migration\n\n## Requirements\n\n"
    f"- **REQ-21 Conduct coverage.** {SPEC09_CURRENT}\n\n## Acceptance Criteria\n\n"
    "- **AC-05** — Given a map, then each target is checked.\n\n## Terminology\n\n"
    "| Term | Meaning |\n|---|---|\n| Kind prefix | The first stem component |\n\n"
    "## Notes\n\n### Ownership\n\nThe migration owns every rename.\n")

VERIFY_FILES: dict[str, str | bytes] = {
    ALPHA: ("---\ntrigger: always_on\n---\n# Alpha flow\n\nIntro line.\n\n## Contract\n\n"
            f"{SHARED_SENTENCE}\nPaste the full test output into the report.\n\n## Example\n\n"
            "Windsurf users read the old directory.\nCodex reads this rule as a skill.\n"),
    DELTA: f"# Delta rule\n\n{SHARED_SENTENCE}\n",
    BETA: ("---\ndescription: Beta step — checks the flow\n---\n# Beta step\n\n"
           "Invocation: `/beta-step`\n\nLoad the `alpha-flow` rule.\n"
           "See `alpha-flow → ## Missing`.\nAlso `/zz-none`.\n"),
    GAMMA: ("# Gamma run\n\nInvocation: `/gamma-run`\n\n"
            "Load the `alpha-flow` rule when the flow is active.\nRun `/beta-step`.\n"),
    CAPS: '{"name": "x"}\n',
    BLOB: b"\xff\xfe\n",
    GUIDE: "See rules/zz-gone.md for history.\n",
    PHASE_DISCOVERY: PHASE_DISCOVERY_TEXT,
    SPEC09_PATH: SPEC09_TEXT,
}
VERIFY_LINKS = {LINK: "caps.json"}
VERIFY_KINDS = {
    ALPHA: ["contract", "reference"], DELTA: ["contract"], BETA: ["workflow"],
    GAMMA: ["workflow"], CAPS: ["adapter-config"], LINK: ["adapter-config"],
    BLOB: ["adapter-config"], PHASE_DISCOVERY: ["bootstrap", "protocol"],
}
VERIFY_SECTIONS = {
    ALPHA: [
        {"heading": "(preamble)", "kind": "contract", "proposed_home": ALPHA},
        {"heading": "## Contract", "kind": "contract", "proposed_home": ALPHA},
        {"heading": "## Example", "kind": "reference", "proposed_home": "rules/reference/alpha.md"},
    ],
    PHASE_DISCOVERY: [
        {"heading": "(preamble)", "kind": "bootstrap", "proposed_home": DISCOVERY_BOOTSTRAP},
        {"heading": "## Codebase Reading Rules", "kind": "protocol",
         "proposed_home": DISCOVERY_CONDUCT},
        {"heading": "## Decision Protocol", "kind": "protocol",
         "proposed_home": DISCOVERY_CONDUCT},
        {"heading": "## Other", "kind": "protocol", "proposed_home": DISCOVERY_CONDUCT},
    ],
}
LOAD_CONDITIONS = {(GAMMA, 5): "when the flow is active"}
ALWAYS_SECTIONED = ("rules/phase-atomic-execution.md", "rules/phase-discovery.md")


def assessment_at(fragment: str) -> str:
    return f"{ASSESSMENT_PATH}#{fragment}"


def inventory_at(fragment: str) -> str:
    return f"{INVENTORY_PATH}#{fragment}"


def build_verify_fixture(base: Path, extra: dict[str, str | bytes] | None = None,
                         use_git: bool = True,
                         before_extract: Callable[[FixtureRoot], None] | None = None
                         ) -> tuple[FixtureRoot, dict]:
    """Write the verify fixture root, commit it when asked, and extract its inventory."""
    fixture = FixtureRoot(base)
    for path, content in {**VERIFY_FILES, **(extra or {})}.items():
        fixture.write(path, content)
    for path, target in VERIFY_LINKS.items():
        (fixture.root / path).symlink_to(target)
    if use_git:
        fixture.commit_all()
    if before_extract is not None:
        before_extract(fixture)
    fixture.write(REPORT_PATH, f"# Rules and workflows audit — {AUDIT_DATE}\n")
    out = fixture.root / INVENTORY_PATH
    result = run_tool(["extract", "--root", str(fixture.root), "--out", str(out)],
                      fixture.env, base)
    if result.returncode != 0:
        raise AssertionError(f"extract failed: {result.stderr!r}")
    return fixture, parse_inventory(out.read_text(encoding="utf-8"))


def inventory_entry(inventory: dict, path: str) -> dict:
    found = [entry for entry in inventory["files"] + inventory["readers"]
             if entry["path"] == path]
    if len(found) != 1:
        raise AssertionError(f"{path} is not one inventory entry")
    return found[0]


def edge_ref(inventory: dict, source: str, line: int) -> dict:
    found = [item for item in inventory["edges"]
             if item["source"] == source and item["line"] == line]
    if len(found) != 1:
        raise AssertionError(f"no single edge at {source}:{line}")
    return {"source": source, "line": line, "column": found[0]["column"]}


def empty_repetition() -> dict:
    return {"report": [], "checkpoint": [], "review": []}


def files_row(entry: dict) -> dict:
    path = entry["path"]
    invocable = path.startswith("workflows/") and bool(entry["invocation_lines"])
    return {"path": path, "sha256": entry["sha256"],
            "kinds": list(VERIFY_KINDS.get(path, ["contract"])),
            "sections": copy.deepcopy(VERIFY_SECTIONS.get(path)),
            "evidence": [f"{path}:1" if entry["lines"] is not None else f"{CAPS}:1"],
            "repetition": empty_repetition() if invocable else None}


def coverage_row(entry: dict) -> dict:
    if entry["entry"] != "file":
        status = "not-a-file"
    else:
        status = "read" if entry["encoding"] == "utf-8" else "unavailable"
    return {"path": entry["path"], "sha256": entry["sha256"], "status": status,
            "reader": ROLE}


def load_row(edge_entry: dict) -> dict:
    condition = LOAD_CONDITIONS.get((edge_entry["source"], edge_entry["line"]))
    return {"source": edge_entry["source"], "line": edge_entry["line"],
            "column": edge_entry["column"],
            "mode": "conditional" if condition else "mandatory", "condition": condition}


def candidate_rows(inventory: dict) -> list[dict]:
    rows = [{"id": item["id"], "disposition": "finding", "finding": "AUD-08-003",
             "reason": None} for item in inventory["repeat_loads"]]
    rows += [{"id": item["id"], "disposition": "not-applicable", "finding": None,
              "reason": "The line names a report field."} for item in inventory["full_output"]]
    rows += [{"id": item["id"], "disposition": "guarded", "finding": None,
              "reason": "The harness is named as an example only."}
             for item in inventory["harness_names"]]
    return rows


def group_rows(inventory: dict) -> list[dict]:
    return [{"id": f"DG-{number:03d}", "clusters": [item["id"]], "locations": [],
             "normative_source": {"path": DELTA, "section": "(preamble)"},
             "condition_differences": "None.", "disposition": "intentional",
             "owner": "none", "finding": None,
             "rationale": "Both rules restate the shared state rule."}
            for number, item in enumerate(inventory["duplicate_clusters"], start=1)]


def finding_row(inventory: dict, number: int, kind: str, severity: str, source: str,
                section: str, lines: list[int], owner: str, blocks: bool,
                evidence: list[str], edges: list[dict] | None = None) -> dict:
    return {"id": f"AUD-08-{number:03d}", "type": kind, "severity": severity,
            "source": source, "section": section,
            "sha256": inventory_entry(inventory, source)["sha256"], "lines": lines,
            "observation": "Observed on reading.", "consequence": "Readers are misled.",
            "owner": owner, "closure": "The cited lines are corrected.", "blocks_09": blocks,
            "status": "open", "evidence": evidence, "edges": edges or []}


def finding_rows(inventory: dict) -> list[dict]:
    return [
        finding_row(inventory, 1, "reference-defect", "major", BETA, "(preamble)", [9, 10],
                    "09", True, [f"{BETA}:9", f"{BETA}:10"],
                    [edge_ref(inventory, BETA, 9), edge_ref(inventory, BETA, 10)]),
        finding_row(inventory, 2, "reference-defect", "minor", GUIDE, "Guide", [1], "11",
                    False, [f"{GUIDE}:1"], [edge_ref(inventory, GUIDE, 1)]),
        finding_row(inventory, 3, "load-repeat", "minor", GAMMA, "(preamble)", [5], "12",
                    False, [f"{GAMMA}:5", f"{BETA}:8"]),
        finding_row(inventory, 4, "report-repeat", "minor", GAMMA, "(preamble)", [6], "11",
                    False, [f"{GAMMA}:6"]),
        finding_row(inventory, 5, "coverage-gap", "major", BLOB, "(file)", [1], "owner",
                    True, [BLOB]),
    ]


def amendment_rows() -> list[dict]:
    return [{"id": "AMD-08-01", "target": "REQ-21", "change": "editorial",
             "current": SPEC09_CURRENT, "proposed": "Proposed text.",
             "reason": "The reference names a heading that does not exist.",
             "evidence": ["AUD-08-001"], "affected": ["AC-05"], "depends_on": [],
             "requires_adr": False, "disposition": "proposed"}]


def map_target(path: str, sections: list[str] | None = None,
               merge_reason: str | None = None) -> dict:
    return {"path": path, "sections": sections, "merge_reason": merge_reason}


def default_of(targets: list[dict]) -> list[dict]:
    """The migration default that equals the given targets."""
    return [{"path": item["path"], "sections": copy.deepcopy(item["sections"])}
            for item in targets]


def map_row(entry: dict) -> dict:
    """A non-deviating map entry: the discovery rule split by its own sections, every other
    top-level rule renamed to a kind-prefixed stem, and every other path kept."""
    source = entry["path"]
    optional: list[str] = []
    if source == PHASE_DISCOVERY:
        headings = [item["heading"] for item in entry["sections"]]
        decision = "split"
        targets = [map_target(DISCOVERY_BOOTSTRAP, headings[:1]),
                   map_target(DISCOVERY_CONDUCT, headings[1:])]
        optional = [DISCOVERY_OVERFLOW]
    elif re.fullmatch(r"rules/[^/]+\.md", source) and not KIND_PREFIXED_RULE_RE.fullmatch(source):
        decision, targets = "rename", [map_target("rules/contract-" + source[len("rules/"):])]
    else:
        decision, targets = "keep", [map_target(source)]
    default = default_of(targets)
    return {"source": source, "decision": decision,
            "targets": targets + [map_target(path) for path in optional],
            "spec09_default": default, "spec09_optional": optional, "amendment": None}


def statement(line: int, covered_by: str | None = f"{ALPHA}:9") -> dict:
    return {"source": f"{PHASE_DISCOVERY}:{line}", "text": "A statement of the rule.",
            "covered_by": covered_by}


def req21_record(inventory: dict) -> dict:
    """One covered statement per statement unit of the fixture's discovery rule; none when a
    case replaced that rule by text without the two sections."""
    entry = inventory_entry(inventory, PHASE_DISCOVERY)
    lines = (STATEMENT_UNIT_LINES if entry["sha256"] == sha256(PHASE_DISCOVERY_TEXT.encode())
             else ())
    return {"verdict": "covered", "statements": [statement(line) for line in lines]}


def valid_assessment(inventory: dict) -> dict:
    """A fully valid assessment of the verify fixture, map and statement coverage included."""
    audited = {entry["path"] for entry in inventory["files"]}
    files = [files_row(entry) for entry in inventory["files"]]
    for row in files:
        if row["path"] == GAMMA:
            row["repetition"]["report"] = ["AUD-08-004"]
    return {
        "schema_version": 1,
        "inventory_digest": inventory["inventory_digest"],
        "run_date": AUDIT_DATE,
        "auditor": ROLE,
        "environment": {"python": "Python 3.12.16", "git": "git version 2.43.0"},
        "installed_access": "not-verified",
        "files": files,
        "coverage": [coverage_row(entry) for entry in inventory["files"]],
        "loads": [load_row(item) for item in inventory["edges"]
                  if item["load"] and item["source"] in audited],
        "candidates": candidate_rows(inventory),
        "legacy": [{"source": item["source"], "line": item["line"], "column": item["column"],
                    "role": "example", "note": "Names a former harness."}
                   for item in inventory["legacy_mentions"]],
        "duplicate_groups": group_rows(inventory),
        "map": [map_row(entry) for entry in inventory["files"]],
        "req21": req21_record(inventory),
        "findings": finding_rows(inventory),
        "amendments": amendment_rows(),
        "installed": [],
    }


DIAGNOSTIC_RE = re.compile(
    r"(?P<code>[a-z0-9]+(?:-[a-z0-9]+)*) (?P<location>\S+) (?P<message>\S.*)")


def diagnostic_pairs(result: subprocess.CompletedProcess[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        found = DIAGNOSTIC_RE.fullmatch(line)
        if found is None:
            raise AssertionError(f"not a `<code> <location> <message>` line: {line!r}")
        pairs.append((found["code"], found["location"]))
    return pairs


def row_index(rows: list[dict], key: str, value: object) -> int:
    matches = [index for index, row in enumerate(rows) if row.get(key) == value]
    if len(matches) != 1:
        raise AssertionError(f"no single row with {key}={value!r}")
    return matches[0]


class VerifyAssertions(unittest.TestCase):
    maxDiff = None

    def assert_silent(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def assert_reports(self, result: subprocess.CompletedProcess[str],
                       expected: list[tuple[str, str]]) -> None:
        self.assertEqual(result.returncode, 1,
                         f"stdout={result.stdout!r} stderr={result.stderr!r}")
        self.assertEqual(result.stderr, "")
        self.assertEqual(sorted(diagnostic_pairs(result)), sorted(expected))

    def assert_codes(self, result: subprocess.CompletedProcess[str], code: str,
                     location_prefix: str) -> None:
        self.assertEqual(result.returncode, 1,
                         f"stdout={result.stdout!r} stderr={result.stderr!r}")
        pairs = diagnostic_pairs(result)
        self.assertTrue(pairs)
        for found_code, location in pairs:
            self.assertEqual(found_code, code, result.stdout)
            self.assertTrue(location.startswith(location_prefix), result.stdout)


class SharedVerifyCase(VerifyAssertions):
    """Cases that vary only the assessment of one committed and extracted fixture root."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="audit-verify-")
        try:
            cls.fixture, cls.inventory = build_verify_fixture(Path(cls.temp.name))
        except BaseException:
            cls.temp.cleanup()
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def setUp(self) -> None:
        self.assessment = valid_assessment(self.inventory)
        (self.fixture.root / ASSESSMENT_PATH).write_text(canonical(self.assessment),
                                                         encoding="utf-8")
        refresh_report(self.fixture)

    def verify(self, *extra: str, text: str | None = None) -> subprocess.CompletedProcess[str]:
        target = self.fixture.root / ASSESSMENT_PATH
        target.write_text(text if text is not None else canonical(self.assessment),
                          encoding="utf-8")
        refresh_report(self.fixture)
        return self.run_verify(*extra)

    def run_verify(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return run_tool(["verify", "--root", str(self.fixture.root), "--report",
                         str(self.fixture.root / REPORT_PATH), *extra],
                        self.fixture.env, self.fixture.base)

    def index(self, key: str, path: str) -> int:
        return row_index(self.assessment[key], "path", path)

    def row(self, key: str, path: str) -> dict:
        return self.assessment[key][self.index(key, path)]

    def finding(self, finding_id: str) -> dict:
        return self.assessment["findings"][row_index(self.assessment["findings"], "id",
                                                     finding_id)]

    def candidate(self, candidate_id: str) -> dict:
        return self.assessment["candidates"][row_index(self.assessment["candidates"], "id",
                                                       candidate_id)]

    def rewrite_inventory(self, text: str) -> Callable[[], None]:
        path = self.fixture.root / INVENTORY_PATH
        original = path.read_bytes()
        path.write_text(text, encoding="utf-8")
        return lambda: path.write_bytes(original)


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


class VerifyValidFixtureTests(SharedVerifyCase):
    def test_valid_inventory_and_assessment_pair_yields_no_diagnostic_and_exit_zero(
            self) -> None:
        inventory = self.inventory
        self.assertEqual([item["id"] for item in inventory["repeat_loads"]], ["RL-001"])
        self.assertEqual([item["id"] for item in inventory["full_output"]], ["FO-001"])
        self.assertEqual([item["id"] for item in inventory["harness_names"]], ["HN-001"])
        self.assertEqual([item["id"] for item in inventory["duplicate_clusters"]], ["DUP-001"])
        self.assertEqual(len(inventory["legacy_mentions"]), 1)
        self.assertEqual(len(self.assessment["loads"]), 2)
        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})
        self.assert_silent(self.verify())

    def test_strict_verify_of_an_unchanged_extraction_is_silent(self) -> None:
        self.assert_silent(self.verify("--strict"))

    def test_verify_changes_no_file_with_or_without_diagnostics(self) -> None:
        faulty = valid_assessment(self.inventory)
        faulty["findings"][0]["owner"] = "15"
        faulty["installed"] = [{"path": ALPHA, "location": "/x", "source_sha256": "0",
                                "installed_sha256": "0"}]
        for name, text in (("valid", canonical(self.assessment)),
                           ("faulty", canonical(faulty)), ("unparseable", "{")):
            with self.subTest(assessment=name):
                (self.fixture.root / ASSESSMENT_PATH).write_text(text, encoding="utf-8")
                before = tree_digests(self.fixture.base)
                self.run_verify()
                self.run_verify("--strict")
                self.assertEqual(tree_digests(self.fixture.base), before)
                self.assertEqual(self.run_verify().returncode, 0 if name == "valid" else 1)


class VerifyOutputTests(SharedVerifyCase):
    def test_diagnostics_are_code_location_message_lines_ordered_by_code_then_location(
            self) -> None:
        self.assessment["inventory_digest"] = "f" * 64
        self.assessment["files"].pop(self.index("files", DELTA))
        self.finding("AUD-08-002")["observation"] = "It saves 3,000 tokens."
        self.finding("AUD-08-001")["edges"] = []

        result = self.verify()

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(diagnostic_pairs(result), [
            ("defect-unrecorded", f"{BETA}:10"),
            ("defect-unrecorded", f"{BETA}:9"),
            ("digest-mismatch", assessment_at("inventory_digest")),
            ("economics-claim", assessment_at("AUD-08-002")),
            *report_claims(self.fixture),
            ("row-missing", f"{DELTA}:0"),
        ])

    def test_locations_are_relative_to_the_root_and_hold_no_absolute_path(self) -> None:
        self.assessment["inventory_digest"] = "f" * 64
        result = self.verify()
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(str(self.fixture.base), result.stdout)
        self.assertNotIn("/home/", result.stdout)
        self.assertNotIn("/tmp", result.stdout)


class VerifyFileFrameTests(SharedVerifyCase):
    def test_missing_inventory_or_assessment_is_reported_with_exit_one(self) -> None:
        inventory_file = self.fixture.root / INVENTORY_PATH
        assessment_file = self.fixture.root / ASSESSMENT_PATH
        original = inventory_file.read_bytes()
        try:
            self.verify()
            assessment_file.unlink()
            result = self.run_verify()
            self.assert_reports(result, [("assessment-missing", f"{ASSESSMENT_PATH}:0")])
            inventory_file.unlink()
            result = self.run_verify()
            self.assert_reports(result, [("assessment-missing", f"{ASSESSMENT_PATH}:0"),
                                         ("inventory-missing", f"{INVENTORY_PATH}:0")])
            self.assert_reports(self.verify(), [("inventory-missing", f"{INVENTORY_PATH}:0")])
        finally:
            inventory_file.write_bytes(original)

    def test_unparseable_json_and_duplicate_keys_are_invalid_files(self) -> None:
        with self.subTest(file="assessment", fault="unparseable"):
            self.assert_codes(self.verify(text="{\n"), "assessment-invalid",
                              f"{ASSESSMENT_PATH}:")
        with self.subTest(file="assessment", fault="duplicate key"):
            text = canonical(self.assessment).replace(
                '"schema_version": 1,', '"schema_version": 1,\n  "schema_version": 1,', 1)
            self.assert_codes(self.verify(text=text), "assessment-invalid",
                              f"{ASSESSMENT_PATH}")
        original = (self.fixture.root / INVENTORY_PATH).read_text(encoding="utf-8")
        for fault, text in (("unparseable", original[:40]),
                            ("duplicate key", original.replace(
                                '"schema_version": 1,',
                                '"schema_version": 1,\n  "schema_version": 1,', 1))):
            with self.subTest(file="inventory", fault=fault):
                restore = self.rewrite_inventory(text)
                try:
                    self.assert_codes(self.verify(), "inventory-invalid", f"{INVENTORY_PATH}")
                finally:
                    restore()

    def test_inventory_schema_violations_are_inventory_invalid(self) -> None:
        def unknown_key(value: dict) -> None:
            value["extra"] = []

        def missing_key(value: dict) -> None:
            del value["readers"]

        def bad_enum(value: dict) -> None:
            value["files"][0]["set"] = "secondary"

        def duplicate_path(value: dict) -> None:
            value["files"].append(copy.deepcopy(value["files"][0]))

        def bad_type(value: dict) -> None:
            value["edges"] = {}

        for fault in (unknown_key, missing_key, bad_enum, duplicate_path, bad_type):
            with self.subTest(fault=fault.__name__):
                value = copy.deepcopy(self.inventory)
                fault(value)
                restore = self.rewrite_inventory(canonical(value))
                try:
                    self.assert_codes(self.verify(), "inventory-invalid", f"{INVENTORY_PATH}")
                finally:
                    restore()

    def test_unknown_and_missing_keys_are_assessment_invalid_at_the_key(self) -> None:
        self.assessment["extra"] = True
        self.assert_reports(self.verify(), [("assessment-invalid", assessment_at("extra"))])
        self.setUp()
        del self.assessment["legacy"]
        self.assert_reports(self.verify(), [("assessment-invalid", assessment_at("legacy"))])

    def test_key_order_of_the_assessment_does_not_matter(self) -> None:
        reordered = dict(reversed(list(self.assessment.items())))
        self.assert_silent(self.verify(text=canonical(reordered)))

    def test_duplicate_finding_id_is_assessment_invalid(self) -> None:
        self.assessment["findings"].append(copy.deepcopy(self.finding("AUD-08-002")))
        self.assert_reports(self.verify(),
                            [("assessment-invalid", assessment_at("AUD-08-002"))])

    def test_schema_types_and_enum_values_are_assessment_invalid(self) -> None:
        def top_level_list(value: dict) -> object:
            return []

        def schema_version(value: dict) -> object:
            value["schema_version"] = 2
            return value

        def installed_access(value: dict) -> object:
            value["installed_access"] = "maybe"
            return value

        def run_date(value: dict) -> object:
            value["run_date"] = "2026-02-30"
            return value

        def findings_not_list(value: dict) -> object:
            value["findings"] = "none"
            return value

        def empty_kinds(value: dict) -> object:
            value["files"][0]["kinds"] = []
            return value

        def unknown_kind(value: dict) -> object:
            value["files"][0]["kinds"] = ["category"]
            return value

        def coverage_status(value: dict) -> object:
            value["coverage"][0]["status"] = "skimmed"
            return value

        def reader_label(value: dict) -> object:
            value["coverage"][0]["reader"] = "the reader"
            return value

        def finding_missing_key(value: dict) -> object:
            del value["findings"][0]["closure"]
            return value

        def files_row_not_object(value: dict) -> object:
            value["files"][0] = "rules/alpha-flow.md"
            return value

        def candidate_disposition(value: dict) -> object:
            value["candidates"][0]["disposition"] = "ignored"
            return value

        def legacy_role(value: dict) -> object:
            value["legacy"][0]["role"] = "decorative"
            return value

        def group_disposition(value: dict) -> object:
            value["duplicate_groups"][0]["disposition"] = "merge"
            return value

        def load_mode(value: dict) -> object:
            value["loads"][0]["mode"] = "sometimes"
            return value

        def files_evidence(value: dict) -> object:
            value["files"][0]["evidence"] = []
            return value

        for fault in (top_level_list, schema_version, installed_access, run_date,
                      findings_not_list, empty_kinds, unknown_kind, coverage_status,
                      reader_label, finding_missing_key, files_row_not_object,
                      candidate_disposition, legacy_role, group_disposition, load_mode,
                      files_evidence):
            with self.subTest(fault=fault.__name__):
                value = fault(valid_assessment(self.inventory))
                self.assert_codes(self.verify(text=canonical(value)), "assessment-invalid",
                                  f"{ASSESSMENT_PATH}")

    def test_assessment_digest_unequal_to_the_inventory_is_digest_mismatch(self) -> None:
        self.assessment["inventory_digest"] = "f" * 64
        self.assert_reports(self.verify(),
                            [("digest-mismatch", assessment_at("inventory_digest"))])


class VerifyRowTests(SharedVerifyCase):
    def test_audited_path_without_a_files_or_coverage_row_is_row_missing(self) -> None:
        self.assessment["files"].pop(self.index("files", DELTA))
        self.assert_reports(self.verify(), [("row-missing", f"{DELTA}:0")])
        self.setUp()
        self.assessment["coverage"].pop(self.index("coverage", CAPS))
        self.assert_reports(self.verify(), [("row-missing", f"{CAPS}:0")])

    def test_row_for_a_path_outside_the_audited_set_is_row_extra(self) -> None:
        extra = coverage_row({"path": "rules/zz-extra.md", "entry": "file",
                              "encoding": "utf-8", "sha256": "0" * 64})
        self.assessment["coverage"].append(extra)
        position = len(self.assessment["coverage"]) - 1
        self.assert_reports(self.verify(), [("row-extra", assessment_at(f"coverage[{position}]"))])

    def test_second_row_for_one_path_is_row_duplicate(self) -> None:
        self.assessment["files"].append(copy.deepcopy(self.row("files", DELTA)))
        position = len(self.assessment["files"]) - 1
        self.assert_reports(self.verify(),
                            [("row-duplicate", assessment_at(f"files[{position}]"))])

    def test_row_digest_unequal_to_the_inventory_is_assessment_stale(self) -> None:
        self.row("files", DELTA)["sha256"] = "0" * 64
        self.row("coverage", ALPHA)["sha256"] = "0" * 64
        self.row("coverage", LINK)["sha256"] = "0" * 64
        self.assert_reports(self.verify(), [
            ("assessment-stale", assessment_at(f"files[{self.index('files', DELTA)}]")),
            ("assessment-stale", assessment_at(f"coverage[{self.index('coverage', ALPHA)}]")),
            ("assessment-stale", assessment_at(f"coverage[{self.index('coverage', LINK)}]")),
        ])

    def test_two_kind_rule_with_sections_covering_two_of_three_is_sections_incomplete(
            self) -> None:
        location = assessment_at(f"files[{self.index('files', ALPHA)}]")
        sections = self.row("files", ALPHA)["sections"]
        variants = {
            "two of three": sections[:2],
            "null": None,
            "repeated": sections + [copy.deepcopy(sections[0])],
            "unknown heading": sections[:2] + [{"heading": "## Elsewhere", "kind": "reference",
                                                "proposed_home": ALPHA}],
        }
        for name, value in variants.items():
            with self.subTest(sections=name):
                self.setUp()
                self.row("files", ALPHA)["sections"] = copy.deepcopy(value)
                self.assert_reports(self.verify(), [("sections-incomplete", location)])


class VerifyItemTests(SharedVerifyCase):
    def test_load_edge_without_entry_and_entry_naming_no_load_edge_are_load_unclassified(
            self) -> None:
        self.assessment["loads"] = [row for row in self.assessment["loads"]
                                    if row["source"] != BETA]
        self.assert_reports(self.verify(), [("load-unclassified", f"{BETA}:8")])
        self.setUp()
        stray = edge_ref(self.inventory, BETA, 9)
        self.assessment["loads"].append({**stray, "mode": "mandatory", "condition": None})
        position = len(self.assessment["loads"]) - 1
        self.assert_reports(self.verify(),
                            [("load-unclassified", assessment_at(f"loads[{position}]"))])

    def test_load_condition_must_match_its_mode(self) -> None:
        gamma = row_index(self.assessment["loads"], "source", GAMMA)
        beta = row_index(self.assessment["loads"], "source", BETA)
        self.assessment["loads"][gamma]["condition"] = None
        self.assessment["loads"][beta]["condition"] = "when asked"
        self.assert_reports(self.verify(), [
            ("load-unclassified", assessment_at(f"loads[{gamma}]")),
            ("load-unclassified", assessment_at(f"loads[{beta}]")),
        ])

    def test_candidate_without_entry_finding_or_reason_is_candidate_undisposed(self) -> None:
        with self.subTest(fault="no entry"):
            self.assessment["candidates"] = [row for row in self.assessment["candidates"]
                                             if row["id"] != "RL-001"]
            self.assert_reports(self.verify(),
                                [("candidate-undisposed", inventory_at("RL-001"))])
        with self.subTest(fault="finding disposition without finding"):
            self.setUp()
            self.candidate("RL-001")["finding"] = None
            self.assert_reports(self.verify(),
                                [("candidate-undisposed", assessment_at("RL-001"))])
        with self.subTest(fault="empty reason"):
            self.setUp()
            self.candidate("FO-001")["reason"] = ""
            self.assert_reports(self.verify(),
                                [("candidate-undisposed", assessment_at("FO-001"))])

    def test_candidate_naming_a_finding_of_the_wrong_type_is_candidate_undisposed(
            self) -> None:
        with self.subTest(candidate="RL"):
            self.candidate("RL-001")["finding"] = "AUD-08-002"
            self.assert_reports(self.verify(),
                                [("candidate-undisposed", assessment_at("RL-001"))])
        with self.subTest(candidate="HN"):
            self.setUp()
            self.candidate("HN-001").update(disposition="finding", finding="AUD-08-003",
                                            reason=None)
            self.assert_reports(self.verify(),
                                [("candidate-undisposed", assessment_at("HN-001"))])
        with self.subTest(candidate="HN naming"):
            self.setUp()
            self.finding("AUD-08-002")["type"] = "naming"
            self.candidate("HN-001").update(disposition="finding", finding="AUD-08-002",
                                            reason=None)
            self.assert_silent(self.verify())

    def test_legacy_mention_without_entry_is_legacy_role_missing(self) -> None:
        self.assessment["legacy"] = []
        self.assert_reports(self.verify(), [("legacy-role-missing", f"{ALPHA}:15")])

    def test_invocable_workflow_with_null_repetition_is_repetition_invalid(self) -> None:
        self.row("files", BETA)["repetition"] = None
        self.assert_reports(self.verify(), [
            ("repetition-invalid", assessment_at(f"files[{self.index('files', BETA)}]"))])

    def test_repetition_on_a_file_without_invocation_is_repetition_invalid(self) -> None:
        self.row("files", DELTA)["repetition"] = empty_repetition()
        self.assert_reports(self.verify(), [
            ("repetition-invalid", assessment_at(f"files[{self.index('files', DELTA)}]"))])

    def test_repetition_id_naming_a_full_output_finding_is_repetition_invalid(self) -> None:
        location = assessment_at(f"files[{self.index('files', GAMMA)}]")
        with self.subTest(fault="full-output finding"):
            self.finding("AUD-08-004")["type"] = "full-output"
            self.assert_reports(self.verify(), [("repetition-invalid", location)])
        with self.subTest(fault="unknown id"):
            self.setUp()
            self.row("files", GAMMA)["repetition"]["review"] = ["AUD-08-099"]
            self.assert_reports(self.verify(), [("repetition-invalid", location)])


class VerifyGroupTests(SharedVerifyCase):
    def test_cluster_in_no_group_is_duplicate_ungrouped(self) -> None:
        self.assessment["duplicate_groups"] = []
        self.assert_reports(self.verify(), [("duplicate-ungrouped", inventory_at("DUP-001"))])

    def test_cluster_in_two_groups_is_duplicate_multigrouped(self) -> None:
        second = copy.deepcopy(self.assessment["duplicate_groups"][0])
        second["id"] = "DG-002"
        self.assessment["duplicate_groups"].append(second)
        self.assert_reports(self.verify(),
                            [("duplicate-multigrouped", inventory_at("DUP-001"))])

    def test_contradiction_group_without_finding_is_group_invalid(self) -> None:
        self.assessment["duplicate_groups"][0].update(disposition="contradiction",
                                                      owner="owner", finding=None)
        self.assert_reports(self.verify(), [("group-invalid", assessment_at("DG-001"))])

    def test_group_owner_finding_rationale_and_locations_follow_the_group_rules(
            self) -> None:
        def consolidate_owned_by_owner(group: dict) -> None:
            group.update(disposition="consolidate", owner="owner", finding="AUD-08-002")

        def intentional_with_owner(group: dict) -> None:
            group["owner"] = "11"

        def consolidate_without_finding(group: dict) -> None:
            group.update(disposition="consolidate", owner="11", finding=None)

        def empty_rationale(group: dict) -> None:
            group["rationale"] = ""

        def single_location(group: dict) -> None:
            group.update(clusters=[], locations=[{"path": DELTA, "line_start": 3,
                                                  "line_end": 3}])

        def location_beyond_the_file(group: dict) -> None:
            group["locations"] = [{"path": DELTA, "line_start": 3, "line_end": 9}]

        def condition_specific_without_conditions(group: dict) -> None:
            group.update(disposition="condition-specific", condition_differences="")

        for fault in (consolidate_owned_by_owner, intentional_with_owner,
                      consolidate_without_finding, empty_rationale, single_location,
                      location_beyond_the_file, condition_specific_without_conditions):
            with self.subTest(fault=fault.__name__):
                self.setUp()
                fault(self.assessment["duplicate_groups"][0])
                expected = [("group-invalid", assessment_at("DG-001"))]
                if fault is single_location:
                    expected.append(("duplicate-ungrouped", inventory_at("DUP-001")))
                self.assert_reports(self.verify(), expected)

    def test_valid_consolidation_and_read_detected_locations_are_accepted(self) -> None:
        self.finding("AUD-08-002")["type"] = "duplicate"
        self.assessment["duplicate_groups"][0].update(
            disposition="consolidate", owner="09", finding="AUD-08-002",
            locations=[{"path": ALPHA, "line_start": 15, "line_end": 16}])
        self.assert_silent(self.verify())


class VerifyFindingTests(SharedVerifyCase):
    def test_control_defect_edge_named_by_no_finding_is_defect_unrecorded(self) -> None:
        finding = self.finding("AUD-08-001")
        finding["edges"] = [item for item in finding["edges"] if item["line"] != 9]
        self.assert_reports(self.verify(), [("defect-unrecorded", f"{BETA}:9")])

    def test_proposal_finding_owned_by_the_naming_migration_is_finding_invalid(self) -> None:
        self.finding("AUD-08-003")["owner"] = "09"
        self.assert_reports(self.verify(), [("finding-invalid", assessment_at("AUD-08-003"))])

    def test_migration_owned_finding_on_an_edge_outside_its_grammar_needs_an_amendment(
            self) -> None:
        self.finding("AUD-08-002")["owner"] = "09"
        self.assert_reports(self.verify(), [("finding-invalid", assessment_at("AUD-08-002"))])
        self.setUp()
        self.finding("AUD-08-002").update(owner="09",
                                          evidence=[f"{GUIDE}:1", "AMD-08-01"])
        self.assert_silent(self.verify())

    def test_blocks_09_must_equal_the_blocking_predicate(self) -> None:
        with self.subTest(fault="cited by an amendment but not blocking"):
            self.finding("AUD-08-001")["blocks_09"] = False
            self.assert_reports(self.verify(),
                                [("finding-invalid", assessment_at("AUD-08-001"))])
        with self.subTest(fault="minor finding blocking without justification"):
            self.setUp()
            self.finding("AUD-08-002")["blocks_09"] = True
            self.assert_reports(self.verify(),
                                [("finding-invalid", assessment_at("AUD-08-002"))])
        with self.subTest(fault="coverage gap on an audited source not blocking"):
            self.setUp()
            self.finding("AUD-08-005")["blocks_09"] = False
            self.assert_reports(self.verify(),
                                [("finding-invalid", assessment_at("AUD-08-005"))])
        with self.subTest(fault="contradiction not blocking"):
            self.setUp()
            self.finding("AUD-08-002").update(type="contradiction", owner="owner")
            self.assert_reports(self.verify(),
                                [("finding-invalid", assessment_at("AUD-08-002"))])

    def test_finding_value_rules_each_raise_finding_invalid(self) -> None:
        faults: tuple[tuple[str, str, Callable[[dict], None]], ...] = (
            ("blocker severity without blocking", "AUD-08-002",
             lambda finding: finding.update(severity="blocker")),
            ("status outside the set", "AUD-08-002",
             lambda finding: finding.update(status="closed")),
            ("line beyond the source", "AUD-08-002",
             lambda finding: finding.update(lines=[1, 2])),
            ("line zero", "AUD-08-002", lambda finding: finding.update(lines=[0])),
            ("section unknown for an audited source", "AUD-08-004",
             lambda finding: finding.update(section="## Nowhere")),
            ("source outside the inventory", "AUD-08-004",
             lambda finding: finding.update(source="docs/zz-none.md")),
            ("empty evidence", "AUD-08-002", lambda finding: finding.update(evidence=[])),
            ("accepted observation with an owner", "AUD-08-002",
             lambda finding: finding.update(type="accepted-observation", owner="11")),
            ("edge that is not a defect", "AUD-08-002",
             lambda finding: finding["edges"].append(edge_ref(self.inventory, BETA, 8))),
            ("edge that does not exist", "AUD-08-002",
             lambda finding: finding["edges"].append(
                 edge_ref(self.inventory, GUIDE, 1) | {"column": 0})),
            ("contradiction owned by the migration", "AUD-08-002",
             lambda finding: finding.update(type="contradiction", owner="09",
                                            blocks_09=True)),
        )
        for name, finding_id, fault in faults:
            with self.subTest(fault=name):
                self.setUp()
                fault(self.finding(finding_id))
                self.assert_reports(self.verify(),
                                    [("finding-invalid", assessment_at(finding_id))])

    def test_finding_severity_or_type_outside_its_set_is_assessment_invalid_once(
            self) -> None:
        for key, value in (("severity", "critical"), ("type", "typo")):
            with self.subTest(key=key):
                self.setUp()
                self.finding("AUD-08-002")[key] = value
                self.assert_reports(self.verify(),
                                    [("assessment-invalid", assessment_at("AUD-08-002"))])

    def test_accepted_observation_and_historical_fixed_findings_are_accepted(self) -> None:
        self.finding("AUD-08-002").update(type="accepted-observation", owner="none")
        self.finding("AUD-08-004")["status"] = "historical-fixed"
        self.assert_silent(self.verify())

    def test_finding_digest_unequal_to_its_source_is_finding_stale(self) -> None:
        self.finding("AUD-08-002")["sha256"] = "0" * 64
        self.assert_reports(self.verify(), [("finding-stale", assessment_at("AUD-08-002"))])

    def test_unknown_ids_cited_by_findings_candidates_and_groups_are_reference_unknown(
            self) -> None:
        def finding_cites_missing_amendment(value: dict) -> str:
            value["findings"][2]["evidence"].append("AMD-08-07")
            return "AUD-08-003"

        def candidate_cites_missing_finding(value: dict) -> str:
            value["candidates"][0]["finding"] = "AUD-08-099"
            return "RL-001"

        def candidate_entry_for_missing_candidate(value: dict) -> str:
            value["candidates"].append({"id": "FO-009", "disposition": "not-applicable",
                                        "finding": None, "reason": "Not a candidate."})
            return "FO-009"

        def group_cites_missing_cluster(value: dict) -> str:
            value["duplicate_groups"][0]["clusters"].append("DUP-009")
            return "DG-001"

        def group_cites_missing_finding(value: dict) -> str:
            value["duplicate_groups"][0]["finding"] = "AUD-08-099"
            return "DG-001"

        for fault in (finding_cites_missing_amendment, candidate_cites_missing_finding,
                      candidate_entry_for_missing_candidate, group_cites_missing_cluster,
                      group_cites_missing_finding):
            with self.subTest(fault=fault.__name__):
                value = valid_assessment(self.inventory)
                fragment = fault(value)
                self.assert_reports(self.verify(text=canonical(value)),
                                    [("reference-unknown", assessment_at(fragment))])


class VerifyCoverageAndInstalledTests(SharedVerifyCase):
    def test_unavailable_coverage_without_a_coverage_gap_finding_is_inconsistent(
            self) -> None:
        self.assessment["findings"] = [item for item in self.assessment["findings"]
                                       if item["id"] != "AUD-08-005"]
        self.assert_reports(self.verify(), [
            ("coverage-inconsistent", assessment_at(f"coverage[{self.index('coverage', BLOB)}]"))])

    def test_changed_coverage_without_a_coverage_gap_finding_is_inconsistent(self) -> None:
        self.row("coverage", DELTA)["status"] = "changed"
        self.assert_reports(self.verify(), [
            ("coverage-inconsistent", assessment_at(f"coverage[{self.index('coverage', DELTA)}]"))])

    def test_not_a_file_status_must_match_the_entry_kind(self) -> None:
        with self.subTest(fault="not-a-file on a regular file"):
            self.row("coverage", CAPS)["status"] = "not-a-file"
            self.assert_reports(self.verify(), [
                ("coverage-inconsistent",
                 assessment_at(f"coverage[{self.index('coverage', CAPS)}]"))])
        with self.subTest(fault="symbolic link read"):
            self.setUp()
            self.row("coverage", LINK)["status"] = "read"
            self.assert_reports(self.verify(), [
                ("coverage-inconsistent",
                 assessment_at(f"coverage[{self.index('coverage', LINK)}]"))])

    def test_installed_entries_follow_the_installed_access_rules(self) -> None:
        digest = inventory_entry(self.inventory, ALPHA)["sha256"]
        entry = {"path": ALPHA, "location": "~/.harness/skills/rule-alpha-flow/SKILL.md",
                 "source_sha256": digest, "installed_sha256": "0" * 64}
        with self.subTest(fault="entries while not verified"):
            self.assessment["installed"] = [copy.deepcopy(entry)]
            self.assert_reports(self.verify(), [("installed-invalid", assessment_at("installed"))])
        with self.subTest(fault="location outside the home directory"):
            self.setUp()
            self.assessment.update(installed_access="verified",
                                   installed=[entry | {"location": "/opt/skills/SKILL.md"}])
            self.assert_reports(self.verify(),
                                [("installed-invalid", assessment_at("installed[0]"))])
        with self.subTest(fault="source digest unequal to the inventory"):
            self.setUp()
            self.assessment.update(installed_access="verified",
                                   installed=[entry | {"source_sha256": "0" * 64}])
            self.assert_reports(self.verify(),
                                [("installed-invalid", assessment_at("installed[0]"))])
        with self.subTest(fault="none: verified comparison"):
            self.setUp()
            self.assessment.update(installed_access="verified", installed=[entry])
            self.assert_silent(self.verify())

    def test_token_and_money_strings_anywhere_in_the_assessment_are_economics_claims(
            self) -> None:
        cases = (
            ("tokens in a finding", lambda value: value["findings"][1].update(
                observation="The split saves 3,000 tokens per run."), "AUD-08-002"),
            ("money in a group", lambda value: value["duplicate_groups"][0].update(
                rationale="Each repeat costs $5 a month."), "DG-001"),
            ("currency in a candidate", lambda value: value["candidates"][1].update(
                reason="Worth 2 EUR."), "FO-001"),
            ("kilotokens in a section home", lambda value: value["files"][3]["sections"][2]
             .update(proposed_home="rules/reference/12ktokens.md"), "files[3]"),
        )
        for name, fault, fragment in cases:
            with self.subTest(case=name):
                value = valid_assessment(self.inventory)
                fault(value)
                self.assert_reports(self.verify(text=canonical(value)),
                                    [("economics-claim", assessment_at(fragment))]
                                    + report_claims(self.fixture))


class VerifyTreeTests(VerifyAssertions):
    """Cases that change the fixture tree or its git state, each on its own root."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="audit-verify-tree-")
        self.base = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build(self, name: str, **options: object) -> tuple[FixtureRoot, dict]:
        base = self.base / name
        base.mkdir()
        fixture, inventory = build_verify_fixture(base, **options)
        (fixture.root / ASSESSMENT_PATH).write_text(canonical(valid_assessment(inventory)),
                                                    encoding="utf-8")
        return fixture, inventory

    def verify(self, fixture: FixtureRoot, *extra: str,
               report: str | None = None) -> subprocess.CompletedProcess[str]:
        if report is None:
            refresh_report(fixture)
        return run_tool(["verify", "--root", str(fixture.root), "--report",
                         report if report is not None else str(fixture.root / REPORT_PATH),
                         *extra], fixture.env, fixture.base)

    def test_changed_added_and_removed_audited_files_are_inventory_stale(self) -> None:
        fixture, _ = self.build("changed")
        fixture.write(DELTA, "# Delta rule\n\nChanged.\n")
        self.assert_reports(self.verify(fixture), [("inventory-stale", f"{DELTA}:0")])
        fixture, _ = self.build("added")
        fixture.write("rules/new-rule.md", "# New rule\n")
        self.assert_reports(self.verify(fixture),
                            [("inventory-stale", "rules/new-rule.md:0")])
        fixture, _ = self.build("removed")
        (fixture.root / DELTA).unlink()
        self.assert_reports(self.verify(fixture), [("inventory-stale", f"{DELTA}:0")])

    def test_changed_reader_is_stale_only_under_strict(self) -> None:
        fixture, _ = self.build("reader")
        fixture.write(GUIDE, "See rules/zz-gone.md for history.\nMore text.\n")
        self.assert_silent(self.verify(fixture))
        self.assert_codes(self.verify(fixture, "--strict"), "inventory-stale",
                          f"{INVENTORY_PATH}:")

    def test_dirty_or_unknown_work_tree_is_worktree_dirty(self) -> None:
        fixture, inventory = self.build(
            "dirty", before_extract=lambda root: root.write("docs/NEW.md", "New.\n"))
        self.assertEqual(inventory["worktree"]["state"], "dirty")
        self.assert_reports(self.verify(fixture), [("worktree-dirty", inventory_at("worktree"))])
        fixture, inventory = self.build("unknown", use_git=False)
        self.assertEqual(inventory["worktree"]["state"], "unknown")
        self.assert_reports(self.verify(fixture), [("worktree-dirty", inventory_at("worktree"))])

    def test_rows_of_the_two_always_sectioned_rules_need_sections(self) -> None:
        extra = {path: "# Rule\n\n## Only\n\nText.\n" for path in ALWAYS_SECTIONED}
        fixture, inventory = self.build("always", extra=extra)
        assessment = valid_assessment(inventory)
        (fixture.root / ASSESSMENT_PATH).write_text(canonical(assessment), encoding="utf-8")
        expected = [("sections-incomplete",
                     assessment_at(f"files[{row_index(assessment['files'], 'path', path)}]"))
                    for path in ALWAYS_SECTIONED]
        self.assert_reports(self.verify(fixture), expected)
        for path in ALWAYS_SECTIONED:
            assessment["files"][row_index(assessment["files"], "path", path)]["sections"] = [
                {"heading": "(preamble)", "kind": "contract", "proposed_home": path},
                {"heading": "## Only", "kind": "contract", "proposed_home": path}]
        (fixture.root / ASSESSMENT_PATH).write_text(canonical(assessment), encoding="utf-8")
        self.assert_silent(self.verify(fixture))

    def test_usage_errors_and_an_invalid_root_exit_two_with_one_error_line(self) -> None:
        fixture, _ = self.build("usage")
        self.assert_silent(self.verify(fixture))
        cases = {
            "no report": ["verify", "--root", str(fixture.root)],
            "report not markdown": ["verify", "--root", str(fixture.root), "--report",
                                    str(fixture.root / "docs/audits/report.txt")],
            "unknown option": ["verify", "--root", str(fixture.root), "--report",
                               str(fixture.root / REPORT_PATH), "--fast"],
            "root without rules": ["verify", "--root", str(fixture.base / "missing"),
                                   "--report", str(fixture.root / REPORT_PATH)],
        }
        for name, arguments in cases.items():
            with self.subTest(case=name):
                result = run_tool(arguments, fixture.env, fixture.base)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                lines = result.stderr.strip().splitlines()
                self.assertEqual(len(lines), 1, lines)
                self.assertTrue(lines[0].startswith("ERROR: "), lines[0])
                self.assertNotIn("Traceback", result.stderr)


DEEP_LEVELS = 2000


def deeply_nested(innermost: object) -> object:
    value = innermost
    for _ in range(DEEP_LEVELS):
        value = [value]
    return value


def compact(value: object) -> str:
    """JSON text without indentation, which the standard encoder writes at any depth."""
    return json.dumps(value, ensure_ascii=False) + "\n"


def deep_directory(root: Path, top: str, levels: int) -> str:
    """Create `levels` nested one-letter directories below `top`; return their relative path."""
    relative = top
    for _ in range(levels):
        relative += "/d"
        os.mkdir(root / relative)
    return relative


def remove_deep_directory(root: Path, relative: str) -> None:
    """Remove a chain made by deep_directory from the bottom up, files first."""
    while "/" in relative:
        directory = root / relative
        for child in os.listdir(directory):
            if not (directory / child).is_dir():
                os.unlink(directory / child)
        os.rmdir(directory)
        relative = relative.rsplit("/", 1)[0]


class VerifyDepthTests(SharedVerifyCase):
    def test_deeply_nested_assessment_values_are_assessment_invalid_without_a_traceback(
            self) -> None:
        cases = (
            ("statement coverage", lambda value: value["req21"].update(
                statements=deeply_nested("Costs $5.")), "req21"),
            ("amendment field", lambda value: value["amendments"][0].update(
                current=deeply_nested("Costs $5.")), "AMD-08-01"),
            ("map entry", lambda value: value["map"].append(deeply_nested("Costs $5.")),
             f"map[{len(self.inventory['files'])}]"),
        )
        for name, fault, fragment_text in cases:
            with self.subTest(case=name):
                value = valid_assessment(self.inventory)
                fault(value)
                result = self.verify(text=compact(value))
                self.assertNotIn("Traceback", result.stderr)
                self.assert_reports(result, [("assessment-invalid", assessment_at(fragment_text))])

    def test_deeply_nested_values_without_amounts_are_assessment_invalid(self) -> None:
        self.assessment["req21"]["statements"] = deeply_nested([])
        result = self.verify(text=compact(self.assessment))
        self.assertNotIn("Traceback", result.stderr)
        self.assert_reports(result, [("assessment-invalid", assessment_at("req21"))])


class VerifyDeepTreeTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build
    verify = VerifyTreeTests.verify

    def test_file_below_a_deep_directory_chain_is_inventory_stale_without_a_traceback(
            self) -> None:
        fixture, _ = self.build("deep")
        directory = deep_directory(fixture.root, "rules", 1200)
        try:
            fixture.write(f"{directory}/x.md", "# X\n")
            result = self.verify(fixture)
        finally:
            remove_deep_directory(fixture.root, directory)
        self.assertNotIn("Traceback", result.stderr)
        self.assert_reports(result, [("inventory-stale", f"{directory}/x.md:0")])


class VerifyPinnedBehaviourTests(SharedVerifyCase):
    """Characterization cases that pin behaviour the earlier cases left unconstrained."""

    def test_accepted_observation_must_be_minor_and_must_not_block(self) -> None:
        with self.subTest(fault="major severity"):
            self.finding("AUD-08-002").update(type="accepted-observation", owner="none",
                                              severity="major")
            self.assert_reports(self.verify(),
                                [("finding-invalid", assessment_at("AUD-08-002"))])
        with self.subTest(fault="blocking although the predicate holds"):
            self.setUp()
            self.finding("AUD-08-001").update(type="accepted-observation", owner="none",
                                              severity="minor")
            self.assert_reports(self.verify(),
                                [("finding-invalid", assessment_at("AUD-08-001"))])

    def test_euro_and_pound_amounts_are_economics_claims(self) -> None:
        for text in ("Each repeat costs €5.", "Each repeat costs £ 3."):
            with self.subTest(text=text):
                self.setUp()
                self.finding("AUD-08-002")["observation"] = text
                self.assert_reports(self.verify(),
                                    [("economics-claim", assessment_at("AUD-08-002"))]
                                    + report_claims(self.fixture))

    def test_coverage_gap_finding_on_a_reader_does_not_block(self) -> None:
        self.finding("AUD-08-002")["type"] = "coverage-gap"
        self.assert_silent(self.verify())
        self.finding("AUD-08-002")["blocks_09"] = True
        self.assert_reports(self.verify(), [("finding-invalid", assessment_at("AUD-08-002"))])

    def test_finding_evidence_must_be_a_path_a_path_line_or_an_amendment_id(self) -> None:
        for item in ("docs/GUIDE.md line 1", "/abs/GUIDE.md", "../GUIDE.md", "AMD-8-1 x"):
            with self.subTest(item=item):
                self.setUp()
                self.finding("AUD-08-002")["evidence"] = [f"{GUIDE}:1", item]
                self.assert_reports(self.verify(),
                                    [("finding-invalid", assessment_at("AUD-08-002"))])
        self.setUp()
        self.finding("AUD-08-002")["evidence"] = [f"{GUIDE}:1", GUIDE, "AMD-08-01"]
        self.assert_silent(self.verify())

    def test_two_amounts_in_one_string_give_one_economics_claim(self) -> None:
        self.finding("AUD-08-002")["observation"] = "It costs $5 and saves 3,000 tokens."
        self.assert_reports(self.verify(), [("economics-claim", assessment_at("AUD-08-002"))]
                            + report_claims(self.fixture))


class VerifyParseLimitTests(SharedVerifyCase):
    def test_oversized_integer_or_unpaired_surrogate_makes_the_file_invalid_at_line_zero(
            self) -> None:
        long_integer = "9" * 4301

        def with_long_integer(text: str) -> str:
            return text.replace("{", '{"zz": ' + long_integer + ", ", 1)

        def assessment_with_surrogate() -> str:
            value = valid_assessment(self.inventory)
            value["coverage"].append({"path": "\ud800", "sha256": None, "status": "read",
                                      "reader": ROLE})
            return json.dumps(value)

        def inventory_with_surrogate() -> str:
            value = copy.deepcopy(self.inventory)
            value["files"][0]["path"] = "rules/\ud800.md"
            return json.dumps(value)

        original = (self.fixture.root / INVENTORY_PATH).read_text(encoding="utf-8")
        cases = (
            ("assessment", "integer longer than the conversion limit",
             with_long_integer(canonical(self.assessment)), None),
            ("assessment", "unpaired surrogate", assessment_with_surrogate(), None),
            ("inventory", "integer longer than the conversion limit", None,
             with_long_integer(original)),
            ("inventory", "unpaired surrogate", None, inventory_with_surrogate()),
        )
        for name, fault, assessment_text, inventory_text in cases:
            with self.subTest(file=name, fault=fault):
                restore = self.rewrite_inventory(inventory_text or original)
                try:
                    result = self.verify(text=assessment_text)
                finally:
                    restore()
                self.assertNotIn("Traceback", result.stderr)
                path = ASSESSMENT_PATH if name == "assessment" else INVENTORY_PATH
                self.assert_reports(result, [(f"{name}-invalid", f"{path}:0")])


def run_tool_bytes(arguments: list[bytes], env: dict[str, str], cwd: Path
                   ) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run([os.fsencode(sys.executable), b"-I", os.fsencode(TOOL), *arguments],
                          cwd=cwd, env=env, capture_output=True, timeout=60)


def output_lines(data: bytes) -> list[str]:
    """Decode tool output strictly as UTF-8 and split it into lines."""
    try:
        return data.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise AssertionError(f"the output is not valid UTF-8: {data!r}") from error


def locale_available(name: str) -> bool:
    """Whether the C library knows a locale; the process locale is restored afterwards."""
    import locale
    saved = locale.setlocale(locale.LC_CTYPE)
    try:
        locale.setlocale(locale.LC_CTYPE, name)
    except locale.Error:
        return False
    finally:
        locale.setlocale(locale.LC_CTYPE, saved)
    return True


class VerifyOutputBoundaryTests(SharedVerifyCase):
    def test_duplicate_key_with_an_unpaired_surrogate_is_one_invalid_line(self) -> None:
        injected = '{"\\ud800": 1, "\\ud800": 2, '
        original = (self.fixture.root / INVENTORY_PATH).read_text(encoding="utf-8")
        cases = (("assessment", canonical(self.assessment).replace("{", injected, 1), original),
                 ("inventory", None, original.replace("{", injected, 1)))
        for name, assessment_text, inventory_text in cases:
            with self.subTest(file=name):
                restore = self.rewrite_inventory(inventory_text)
                try:
                    (self.fixture.root / ASSESSMENT_PATH).write_text(
                        assessment_text or canonical(self.assessment), encoding="utf-8")
                    result = run_tool_bytes(
                        [b"verify", b"--root", os.fsencode(self.fixture.root), b"--report",
                         os.fsencode(self.fixture.root / REPORT_PATH)],
                        self.fixture.env, self.fixture.base)
                finally:
                    restore()
                self.assertNotIn(b"Traceback", result.stderr)
                self.assertEqual(result.returncode, 1, result.stderr)
                lines = output_lines(result.stdout)
                path = ASSESSMENT_PATH if name == "assessment" else INVENTORY_PATH
                self.assertEqual(len(lines), 1, lines)
                self.assertTrue(lines[0].startswith(f"{name}-invalid {path}:0 "), lines)

    def test_line_break_in_a_copied_string_stays_on_one_output_line(self) -> None:
        extra = coverage_row({"path": "rules/a b\nc.md", "entry": "file", "encoding": "utf-8",
                              "sha256": "0" * 64})
        self.assessment["coverage"].append(extra)
        position = len(self.assessment["coverage"]) - 1
        result = self.verify()
        self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout)
        self.assert_reports(result, [("row-extra", assessment_at(f"coverage[{position}]"))])
        self.assertNotIn("\n", result.stdout.rstrip("\n"))


class VerifyOutputBoundaryTreeTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build
    verify = VerifyTreeTests.verify

    def test_report_path_with_a_byte_that_is_not_utf8_is_escaped_in_every_locale(
            self) -> None:
        fixture, _ = self.build("bytes")
        report = os.fsencode(fixture.root / "docs/audits") + b"/\xff-x.md"
        for locale_name in ("C", "C.UTF-8", "en_US.UTF-8"):
            with self.subTest(locale=locale_name):
                if not locale_available(locale_name):
                    self.skipTest(f"the locale {locale_name} is not installed")
                env = dict(fixture.env, LC_ALL=locale_name)
                result = run_tool_bytes([b"verify", b"--root", os.fsencode(fixture.root),
                                         b"--report", report], env, fixture.base)
                self.assertNotIn(b"Traceback", result.stderr)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(sorted(output_lines(result.stdout)), [
                    "assessment-missing docs/audits/\\udcff-x.assessment.json:0 "
                    "the file does not exist",
                    "inventory-missing docs/audits/\\udcff-x.inventory.json:0 "
                    "the file does not exist",
                    "report-missing docs/audits/\\udcff-x.md:0 the file does not exist",
                ])

    def test_space_and_line_break_in_an_audited_path_are_escaped_in_its_location(
            self) -> None:
        fixture, _ = self.build("newline")
        fixture.write("rules/a b\nc.md", "# A\n")
        result = self.verify(fixture)
        self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout)
        self.assert_reports(result, [("inventory-stale", "rules/a\\x20b\\x0ac.md:0")])

    def test_error_line_with_a_line_break_in_an_argument_stays_one_line(self) -> None:
        fixture, _ = self.build("argument")
        result = run_tool(["verify", "--root", str(fixture.root), "--report",
                           str(fixture.root / REPORT_PATH), "extra\nargument"],
                          fixture.env, fixture.base)
        self.assertEqual(result.returncode, 2, result.stderr)
        lines = result.stderr.splitlines()
        self.assertEqual(len(lines), 1, lines)
        self.assertTrue(lines[0].startswith("ERROR: "), lines)


class MigrationMapCase(SharedVerifyCase):
    """Cases that vary the map, the amendments or the statement coverage of the valid pair."""

    def map_index(self, source: str) -> int:
        return row_index(self.assessment["map"], "source", source)

    def map_entry(self, source: str) -> dict:
        return self.assessment["map"][self.map_index(source)]

    def map_at(self, source: str) -> str:
        return assessment_at(f"map[{self.map_index(source)}]")

    def last_map_at(self) -> str:
        return assessment_at(f"map[{len(self.assessment['map']) - 1}]")

    def retarget(self, source: str, decision: str, targets: list[dict]) -> dict:
        """Give an entry new targets and the default equal to them, so it does not deviate."""
        entry = self.map_entry(source)
        entry.update(decision=decision, targets=targets, spec09_default=default_of(targets),
                     spec09_optional=[])
        return entry

    def split_discovery(self, bootstrap: list[str], conduct: list[str],
                        conduct_path: str = DISCOVERY_CONDUCT) -> dict:
        """Split the discovery rule into two sectioned targets plus the overflow target."""
        entry = self.retarget(PHASE_DISCOVERY, "split", [
            map_target(DISCOVERY_BOOTSTRAP, bootstrap), map_target(conduct_path, conduct)])
        entry["targets"].append(map_target(DISCOVERY_OVERFLOW))
        entry["spec09_optional"] = [DISCOVERY_OVERFLOW]
        return entry

    def add_amendment(self, **changes: object) -> str:
        """Append a valid second amendment with the given field values; return its id."""
        amendment = copy.deepcopy(self.assessment["amendments"][0])
        amendment.update(id="AMD-08-02", evidence=[f"{BETA}:9"])
        amendment.update(changes)
        self.assessment["amendments"].append(amendment)
        return amendment["id"]


DISCOVERY_SECTIONS = ["(preamble)", "## Codebase Reading Rules", "## Decision Protocol",
                      "## Other"]


class VerifyMapRowTests(MigrationMapCase):
    def test_valid_pair_holds_one_map_entry_per_audited_path_and_a_split_with_overflow(
            self) -> None:
        self.assertEqual(sorted(entry["source"] for entry in self.assessment["map"]),
                         sorted(entry["path"] for entry in self.inventory["files"]))
        discovery = self.map_entry(PHASE_DISCOVERY)
        self.assertEqual(discovery["targets"][-1], map_target(DISCOVERY_OVERFLOW))
        self.assertEqual(discovery["spec09_optional"], [DISCOVERY_OVERFLOW])
        self.assertEqual([item["source"] for item in self.assessment["req21"]["statements"]],
                         [f"{PHASE_DISCOVERY}:{line}" for line in STATEMENT_UNIT_LINES])
        self.assert_silent(self.verify())
        self.assessment["map"].pop(self.map_index(DELTA))
        self.assert_reports(self.verify(), [("row-missing", f"{DELTA}:0")])

    def test_map_entry_for_a_path_outside_the_audited_set_is_row_extra(self) -> None:
        self.assessment["map"].append(copy.deepcopy(self.map_entry(DELTA)) | {"source": GUIDE})
        self.assert_reports(self.verify(), [("row-extra", self.last_map_at())])

    def test_second_map_entry_for_one_source_is_row_duplicate_only(self) -> None:
        self.assessment["map"].append(copy.deepcopy(self.map_entry(DELTA)))
        self.assert_reports(self.verify(), [("row-duplicate", self.last_map_at())])


class VerifyMapShapeTests(MigrationMapCase):
    def test_decision_target_shapes_are_map_invalid(self) -> None:
        renamed = "rules/contract-delta-rule.md"
        faults: tuple[tuple[str, str, list[dict]], ...] = (
            ("keep with another target", "keep", [map_target(renamed)]),
            ("keep with two targets", "keep",
             [map_target(renamed), map_target("rules/contract-delta-extra.md")]),
            ("rename into another directory", "rename",
             [map_target("rules/sub/contract-delta-rule.md")]),
            ("move within its own directory", "move",
             [map_target("rules/contract-delta-moved.md")]),
            ("split with one target", "split", [map_target(renamed, ["(preamble)"])]),
            ("merge into a target no other entry shares", "merge",
             [map_target(renamed, None, "Both rules state one contract.")]),
            ("no target", "rename", []),
            ("one target path twice", "split",
             [map_target(renamed, ["(preamble)"]), map_target(renamed)]),
            ("section that is not a heading of the source", "rename",
             [map_target(renamed, ["## Nowhere"])]),
            ("blank merge reason", "rename", [map_target(renamed, None, "  ")]),
        )
        for name, decision, targets in faults:
            with self.subTest(fault=name):
                self.setUp()
                self.retarget(DELTA, decision, targets)
                self.assert_reports(self.verify(), [("map-invalid", self.map_at(DELTA))])
        accepted: tuple[tuple[str, str, str, list[dict]], ...] = (
            ("move into another directory", DELTA, "move",
             [map_target("rules/reference/delta.md")]),
            ("move with the same name", DELTA, "move",
             [map_target("rules/reference/delta-rule.md")]),
            ("keep with sections of the source", BETA, "keep", [map_target(BETA, ["(preamble)"])]),
        )
        for name, source, decision, targets in accepted:
            with self.subTest(accepted=name):
                self.setUp()
                self.retarget(source, decision, targets)
                self.assert_silent(self.verify())

    def test_map_schema_violations_are_assessment_invalid(self) -> None:
        def unknown_decision(entry: dict) -> None:
            entry["decision"] = "copy"

        def missing_key(entry: dict) -> None:
            del entry["amendment"]

        def absolute_target(entry: dict) -> None:
            entry["targets"][0]["path"] = "/rules/contract-delta-rule.md"

        def optional_not_a_list(entry: dict) -> None:
            entry["spec09_optional"] = None

        def malformed_amendment_id(entry: dict) -> None:
            entry["amendment"] = "AMD-8-1"

        def default_without_sections(entry: dict) -> None:
            del entry["spec09_default"][0]["sections"]

        for fault in (unknown_decision, missing_key, absolute_target, optional_not_a_list,
                      malformed_amendment_id, default_without_sections):
            with self.subTest(fault=fault.__name__):
                self.setUp()
                fault(self.map_entry(DELTA))
                self.assert_reports(self.verify(), [("assessment-invalid", self.map_at(DELTA))])


class VerifySplitTests(MigrationMapCase):
    def test_split_that_omits_repeats_or_invents_a_section_is_split_sections_incomplete(
            self) -> None:
        faults = (
            ("omits a section", ["(preamble)"], DISCOVERY_SECTIONS[1:3]),
            ("repeats a section", ["(preamble)", "## Other"], DISCOVERY_SECTIONS[1:]),
            ("names a heading the source lacks", ["(preamble)"],
             DISCOVERY_SECTIONS[1:] + ["## Missing"]),
        )
        for name, bootstrap, conduct in faults:
            with self.subTest(fault=name):
                self.setUp()
                self.split_discovery(bootstrap, conduct)
                self.assert_reports(self.verify(), [("split-sections-incomplete",
                                                     self.map_at(PHASE_DISCOVERY))])
        with self.subTest(accepted="sections moved between targets, overflow left out"):
            self.setUp()
            self.split_discovery(DISCOVERY_SECTIONS[:2], DISCOVERY_SECTIONS[2:])
            self.assert_silent(self.verify())


class VerifySharedTargetTests(MigrationMapCase):
    def test_shared_target_without_a_merge_reason_on_every_sharer_is_map_collision(
            self) -> None:
        alpha_target = self.map_entry(ALPHA)["targets"][0]
        self.map_entry(DELTA).update(
            decision="merge", amendment="AMD-08-01",
            targets=[map_target(alpha_target["path"], None, "Both rules state one contract.")])
        self.assert_reports(self.verify(), [("map-collision", self.map_at(ALPHA))])
        alpha_target["merge_reason"] = "The delta rule joins this contract."
        self.assert_silent(self.verify())

    def test_two_sources_merged_into_one_new_target_need_both_reasons(self) -> None:
        merged = "rules/contract-merged.md"
        for source in (ALPHA, DELTA):
            self.map_entry(source).update(decision="merge", amendment="AMD-08-01",
                                          targets=[map_target(merged)])
        self.assert_reports(self.verify(), [("map-collision", self.map_at(ALPHA)),
                                            ("map-collision", self.map_at(DELTA))])
        for source in (ALPHA, DELTA):
            self.map_entry(source)["targets"][0]["merge_reason"] = "One contract remains."
        self.assert_silent(self.verify())


class VerifyInstalledNameTests(MigrationMapCase):
    def test_final_installed_names_equal_under_casefolding_collide(self) -> None:
        with self.subTest(case="rule-A-b and rule-a-b"):
            self.retarget(ALPHA, "rename", [map_target("rules/A-b.md")])
            self.retarget(DELTA, "rename", [map_target("rules/a-b.md")])
            self.assert_reports(self.verify(), [
                ("installed-name-collision", self.map_at(ALPHA)),
                ("installed-name-collision", self.map_at(DELTA)),
                ("kind-prefix-invalid", self.map_at(ALPHA)),
                ("kind-prefix-invalid", self.map_at(DELTA))])
        with self.subTest(case="sharp s folds to ss"):
            self.setUp()
            self.retarget(ALPHA, "rename", [map_target("rules/contract-straße.md")])
            self.retarget(DELTA, "rename", [map_target("rules/contract-strasse.md")])
            self.assert_reports(self.verify(), [
                ("installed-name-collision", self.map_at(ALPHA)),
                ("installed-name-collision", self.map_at(DELTA))])
        with self.subTest(case="workflow named like the skill of a rule"):
            self.setUp()
            self.retarget(BETA, "rename", [map_target("workflows/rule-contract-alpha-flow.md")])
            self.assert_reports(self.verify(), [
                ("installed-name-collision", self.map_at(ALPHA)),
                ("installed-name-collision", self.map_at(BETA))])
        with self.subTest(accepted="paths below rules/reference/ are not deployed"):
            self.setUp()
            self.retarget(ALPHA, "move", [map_target("rules/reference/Alpha.md")])
            self.retarget(DELTA, "move", [map_target("rules/reference/alpha.md")])
            self.assert_silent(self.verify())

    def test_final_rule_stem_equal_to_a_final_workflow_stem_is_stem_overlap(self) -> None:
        self.retarget(BETA, "rename", [map_target("workflows/contract-alpha-flow.md")])
        self.assert_reports(self.verify(), [("stem-overlap", self.map_at(ALPHA)),
                                            ("stem-overlap", self.map_at(BETA))])

    def test_top_level_rule_target_without_a_kind_prefix_is_kind_prefix_invalid(self) -> None:
        self.retarget(DELTA, "rename", [map_target("rules/plain.md")])
        self.assert_reports(self.verify(), [("kind-prefix-invalid", self.map_at(DELTA))])
        for name, target in (("reference directory", "rules/reference/plain.md"),
                             ("procedure prefix", "rules/procedure-delta-rule.md")):
            with self.subTest(accepted=name):
                self.setUp()
                decision = "move" if "/reference/" in target else "rename"
                self.retarget(DELTA, decision, [map_target(target)])
                self.assert_silent(self.verify())


class VerifyDeviationTests(MigrationMapCase):
    def test_targets_unequal_to_the_default_need_an_amendment(self) -> None:
        entry = self.map_entry(DELTA)
        entry["targets"] = [map_target("rules/contract-delta-renamed.md")]
        self.assert_reports(self.verify(), [("deviation-unamended", self.map_at(DELTA))])
        entry["amendment"] = "AMD-08-01"
        self.assert_silent(self.verify())

    def test_null_default_needs_an_amendment(self) -> None:
        entry = self.map_entry(CAPS)
        entry["spec09_default"] = None
        self.assert_reports(self.verify(), [("deviation-unamended", self.map_at(CAPS))])
        entry["amendment"] = "AMD-08-01"
        self.assert_silent(self.verify())

    def test_default_plus_one_optional_path_is_no_deviation_and_another_path_is(self) -> None:
        extra = "rules/reference/delta-extra.md"
        entry = self.retarget(DELTA, "split", [
            map_target("rules/contract-delta-rule.md", ["(preamble)"])])
        entry["targets"].append(map_target(extra))
        entry["spec09_optional"] = [extra]
        self.assert_silent(self.verify())
        entry["spec09_optional"] = []
        self.assert_reports(self.verify(), [("deviation-unamended", self.map_at(DELTA))])

    def test_section_sets_order_and_optional_targets_decide_deviation(self) -> None:
        with self.subTest(case="same paths, other sections"):
            entry = self.split_discovery(DISCOVERY_SECTIONS[:1], DISCOVERY_SECTIONS[1:])
            entry["targets"][0]["sections"] = DISCOVERY_SECTIONS[:2]
            entry["targets"][1]["sections"] = DISCOVERY_SECTIONS[2:]
            self.assert_reports(self.verify(),
                                [("deviation-unamended", self.map_at(PHASE_DISCOVERY))])
        with self.subTest(case="default target missing"):
            self.setUp()
            entry = self.map_entry(DELTA)
            entry["spec09_default"].append({"path": "rules/contract-delta-more.md",
                                            "sections": None})
            self.assert_reports(self.verify(), [("deviation-unamended", self.map_at(DELTA))])
        with self.subTest(accepted="targets in another order, overflow left out"):
            self.setUp()
            entry = self.split_discovery(DISCOVERY_SECTIONS[:1], DISCOVERY_SECTIONS[1:])
            entry["targets"] = [entry["targets"][1], entry["targets"][0]]
            entry["targets"][1]["sections"] = list(reversed(DISCOVERY_SECTIONS[:1]))
            self.assert_silent(self.verify())

    def test_conduct_rule_replacement_is_no_deviation_only_while_coverage_is_covered(
            self) -> None:
        def replace_conduct_rule() -> dict:
            entry = self.split_discovery(DISCOVERY_SECTIONS[:1], DISCOVERY_SECTIONS[1:])
            entry["targets"][1]["path"] = AUTONOMOUS_DECISION
            return entry

        with self.subTest(case="covered"):
            replace_conduct_rule()
            self.assert_silent(self.verify())
        with self.subTest(case="not covered"):
            self.setUp()
            replace_conduct_rule()
            self.assessment["req21"]["verdict"] = "not-covered"
            self.assessment["req21"]["statements"][0]["covered_by"] = None
            self.assert_reports(self.verify(),
                                [("deviation-unamended", self.map_at(PHASE_DISCOVERY))])
        with self.subTest(case="covered, with other sections"):
            self.setUp()
            entry = replace_conduct_rule()
            entry["targets"][1]["sections"] = DISCOVERY_SECTIONS[1:3]
            entry["targets"][0]["sections"] = ["(preamble)", "## Other"]
            self.assert_reports(self.verify(),
                                [("deviation-unamended", self.map_at(PHASE_DISCOVERY))])

    def test_map_amendment_naming_no_amendment_is_reference_unknown(self) -> None:
        with self.subTest(case="deviating entry"):
            entry = self.map_entry(DELTA)
            entry.update(targets=[map_target("rules/contract-delta-renamed.md")],
                         amendment="AMD-08-09")
            self.assert_reports(self.verify(), [("deviation-unamended", self.map_at(DELTA)),
                                                ("reference-unknown", self.map_at(DELTA))])
        with self.subTest(case="entry equal to its default"):
            self.setUp()
            self.map_entry(ALPHA)["amendment"] = "AMD-08-09"
            self.assert_reports(self.verify(), [("reference-unknown", self.map_at(ALPHA))])


class VerifyAmendmentTests(MigrationMapCase):
    def test_amendment_target_absent_from_the_migration_specification_is_target_unknown(
            self) -> None:
        for target in ("REQ-99", "Notes:Missing", "REQ-2", "Notes:Owner",
                       "Terminology:Kind", "Section 4", "AC-05 and AC-06"):
            with self.subTest(target=target):
                self.setUp()
                amendment = self.add_amendment(target=target)
                self.assert_reports(self.verify(), [("amendment-target-unknown",
                                                     assessment_at(amendment))])

    def test_amendment_target_forms_present_in_the_migration_specification_are_accepted(
            self) -> None:
        self.add_amendment(target="Q-01")
        self.assert_reports(self.verify(), [("amendment-target-unknown",
                                             assessment_at("AMD-08-02"))])
        cases = (
            ("AC-05", "- **AC-05** — Given a map, then each target is checked."),
            ("Notes:Ownership", "The migration owns every rename."),
            ("Terminology:Kind prefix", "| Kind prefix | The first stem component |"),
            ("new-REQ", None),
            ("new-AC", None),
        )
        for target, current in cases:
            with self.subTest(target=target):
                self.setUp()
                self.add_amendment(target=target, current=current)
                self.assert_silent(self.verify())

    def test_affected_id_absent_from_the_migration_specification_is_target_unknown(
            self) -> None:
        for affected in ("AC-99", "AC-5"):
            with self.subTest(affected=affected):
                self.setUp()
                amendment = self.add_amendment(affected=["AC-05", affected])
                self.assert_reports(self.verify(), [("amendment-target-unknown",
                                                     assessment_at(amendment))])

    def test_amendment_field_faults_are_amendment_invalid(self) -> None:
        faults: tuple[tuple[str, dict], ...] = (
            ("no evidence", {"evidence": []}),
            ("new requirement with current text", {"target": "new-REQ"}),
            ("existing target without current text", {"current": None}),
            ("current text absent from the specification", {"current": "Text never written."}),
            ("blank proposed text", {"proposed": " "}),
            ("blank reason", {"reason": ""}),
            ("evidence that is no finding id or path:line", {"evidence": ["see the finding"]}),
            ("affected id that is not an acceptance criterion", {"affected": ["REQ-21"]}),
        )
        for name, changes in faults:
            with self.subTest(fault=name):
                self.setUp()
                amendment = self.add_amendment(**changes)
                self.assert_reports(self.verify(), [("amendment-invalid",
                                                     assessment_at(amendment))])

    def test_amendment_citing_an_unknown_finding_or_amendment_is_reference_unknown(
            self) -> None:
        for name, changes in (("finding", {"evidence": ["AUD-08-001", "AUD-08-099"]}),
                              ("dependency", {"depends_on": ["AMD-08-07"]})):
            with self.subTest(cited=name):
                self.setUp()
                amendment = self.add_amendment(**changes)
                self.assert_reports(self.verify(), [("reference-unknown",
                                                     assessment_at(amendment))])
        self.setUp()
        self.add_amendment(evidence=["AUD-08-001", f"{BETA}:9"], depends_on=["AMD-08-01"])
        self.assert_silent(self.verify())

    def test_amendment_schema_violations_are_assessment_invalid(self) -> None:
        faults: tuple[tuple[str, dict], ...] = (
            ("change outside its set", {"change": "rewrite"}),
            ("disposition outside its set", {"disposition": "accepted"}),
            ("requires_adr not a boolean", {"requires_adr": "no"}),
            ("malformed dependency id", {"depends_on": ["AMD-8-1"]}),
            ("unknown key", {"note": "Extra."}),
        )
        for name, changes in faults:
            with self.subTest(fault=name):
                self.setUp()
                amendment = self.add_amendment(**changes)
                self.assert_reports(self.verify(), [("assessment-invalid",
                                                     assessment_at(amendment))])
        for name, change in (("missing key", lambda item: item.pop("depends_on")),
                             ("repeated id", lambda item: item.update(id="AMD-08-01"))):
            with self.subTest(fault=name):
                self.setUp()
                self.add_amendment()
                change(self.assessment["amendments"][1])
                self.assert_codes(self.verify(), "assessment-invalid", assessment_at("AMD-08-0"))


class VerifyStatementCoverageTests(MigrationMapCase):
    def test_statements_must_be_one_per_unit_of_the_two_sections(self) -> None:
        statements = self.assessment["req21"]["statements"]
        added_at = assessment_at(f"req21.statements[{len(statements)}]")
        faults: tuple[tuple[str, Callable[[list[dict]], None], str], ...] = (
            ("two of three units", lambda items: items.pop(2), f"{PHASE_DISCOVERY}:12"),
            ("a line outside the two sections",
             lambda items: items.append(statement(17)), added_at),
            ("a line inside a unit that starts no unit",
             lambda items: items.append(statement(13)), added_at),
            ("a heading line", lambda items: items.append(statement(10)), added_at),
            ("a unit listed twice", lambda items: items.append(statement(7)), added_at),
            ("a line of another file",
             lambda items: items.append(statement(7) | {"source": f"{ALPHA}:7"}), added_at),
        )
        for name, fault, location in faults:
            with self.subTest(fault=name):
                self.setUp()
                fault(self.assessment["req21"]["statements"])
                self.assert_reports(self.verify(), [("req21-invalid", location)])

    def test_verdict_must_agree_with_the_covered_by_values(self) -> None:
        with self.subTest(fault="covered with a null covered_by"):
            self.assessment["req21"]["statements"][1]["covered_by"] = None
            self.assert_reports(self.verify(), [("req21-invalid", assessment_at("req21"))])
        with self.subTest(fault="not-covered with every unit covered"):
            self.setUp()
            self.assessment["req21"]["verdict"] = "not-covered"
            self.assert_reports(self.verify(), [("req21-invalid", assessment_at("req21"))])
        with self.subTest(accepted="not-covered with a null covered_by"):
            self.setUp()
            self.assessment["req21"]["verdict"] = "not-covered"
            self.assessment["req21"]["statements"][1]["covered_by"] = None
            self.assert_silent(self.verify())

    def test_statement_coverage_schema_violations_are_assessment_invalid(self) -> None:
        def verdict(record: dict) -> None:
            record["verdict"] = "partly"

        def statements_not_a_list(record: dict) -> None:
            record["statements"] = {}

        def statement_missing_key(record: dict) -> None:
            del record["statements"][0]["text"]

        def covered_by_not_a_line(record: dict) -> None:
            record["statements"][0]["covered_by"] = "the alpha rule"

        for fault in (verdict, statements_not_a_list, statement_missing_key,
                      covered_by_not_a_line):
            with self.subTest(fault=fault.__name__):
                self.setUp()
                fault(self.assessment["req21"])
                self.assert_reports(self.verify(), [("assessment-invalid",
                                                     assessment_at("req21"))])


UNIT_TABLE: tuple[tuple[str, bool], ...] = (
    ("---", False),
    ("description: Phase discovery fixture", False),
    ("---", False),
    ("# Phase discovery", False),
    ("", False),
    ("## Codebase Reading Rules", False),
    ("- First item", True),
    ("  continues here", False),
    ("  - nested item", True),
    ("* star item", True),
    ("1) numbered item", True),
    ("2. dotted item", True),
    ("| Column | Value |", True),
    ("|---|---|", False),
    ("| Row | One |", True),
    ("", False),
    ("```text", True),
    ("## Not a section", False),
    ("- not an item", False),
    ("", False),
    ("inside the fence", False),
    ("```", False),
    ("After the fence without a blank line.", False),
    ("", False),
    ("Paragraph after a blank line", True),
    ("still the same paragraph.", False),
    ("### Heading inside the paragraph", False),
    ("   ", False),
    ("### Heading after a blank line", True),
    ("", False),
    ("## Decision Protocol", False),
    ("Directly after the heading.", True),
    ("", False),
    ("## Trailing", False),
    ("Outside both sections.", False),
)
UNIT_STARTS = [number for number, (_, starts) in enumerate(UNIT_TABLE, start=1) if starts]


class VerifyStatementUnitTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build
    verify = VerifyTreeTests.verify

    def discovery_root(self, name: str, text: str) -> tuple[FixtureRoot, dict]:
        """A root whose discovery rule is `text`, with a files row naming its sections."""
        fixture, inventory = self.build(name, extra={PHASE_DISCOVERY: text})
        assessment = valid_assessment(inventory)
        row = assessment["files"][row_index(assessment["files"], "path", PHASE_DISCOVERY)]
        row["sections"] = [{"heading": item["heading"], "kind": "protocol",
                            "proposed_home": DISCOVERY_CONDUCT}
                           for item in inventory_entry(inventory, PHASE_DISCOVERY)["sections"]]
        return fixture, assessment

    def verify_statements(self, fixture: FixtureRoot, assessment: dict,
                          lines: list[int]) -> subprocess.CompletedProcess[str]:
        assessment["req21"] = {"verdict": "covered",
                               "statements": [statement(line) for line in lines]}
        (fixture.root / ASSESSMENT_PATH).write_text(canonical(assessment), encoding="utf-8")
        return self.verify(fixture)

    def test_units_start_at_list_items_table_rows_fences_and_paragraphs(self) -> None:
        for ending in ("\n", "\r\n"):
            with self.subTest(line_ending=repr(ending)):
                text = "".join(line + ending for line, _ in UNIT_TABLE)
                fixture, assessment = self.discovery_root(f"units{len(ending)}", text)
                self.assert_silent(self.verify_statements(fixture, assessment, UNIT_STARTS))
                fence = UNIT_STARTS.index(17)
                self.assert_reports(
                    self.verify_statements(fixture, assessment,
                                           UNIT_STARTS[:fence] + UNIT_STARTS[fence + 1:]),
                    [("req21-invalid", f"{PHASE_DISCOVERY}:17")])
                for line in (8, 14, 18, 19, 23, 26, 27, 35):
                    self.assert_reports(
                        self.verify_statements(fixture, assessment, UNIT_STARTS + [line]),
                        [("req21-invalid", assessment_at(f"req21.statements[{len(UNIT_STARTS)}]"))])

    def test_rule_without_the_two_sections_has_no_statement_units(self) -> None:
        fixture, assessment = self.discovery_root(
            "no-sections", "# Phase discovery\n\n## Other\n\nPlain text here.\n")
        self.assert_silent(self.verify_statements(fixture, assessment, []))
        self.assert_reports(self.verify_statements(fixture, assessment, [5]),
                            [("req21-invalid", assessment_at("req21.statements[0]"))])

    def test_first_line_directly_after_the_section_heading_starts_a_unit_even_a_heading(
            self) -> None:
        fixture, assessment = self.discovery_root(
            "after-heading", "# Phase discovery\n\n## Codebase Reading Rules\n### Sub rule\n"
            "Text of the sub rule.\n\n## Decision Protocol\n\nOne paragraph.\n")
        self.assert_silent(self.verify_statements(fixture, assessment, [4, 9]))
        self.assert_reports(self.verify_statements(fixture, assessment, [9]),
                            [("req21-invalid", f"{PHASE_DISCOVERY}:4")])
        self.assert_reports(self.verify_statements(fixture, assessment, [4, 9, 5]),
                            [("req21-invalid", assessment_at("req21.statements[2]"))])

    def test_not_covered_verdict_with_no_statement_is_req21_invalid(self) -> None:
        fixture, assessment = self.discovery_root(
            "vacuous", "# Phase discovery\n\n## Other\n\nPlain text here.\n")
        assessment["req21"] = {"verdict": "not-covered", "statements": []}
        (fixture.root / ASSESSMENT_PATH).write_text(canonical(assessment), encoding="utf-8")
        self.assert_reports(self.verify(fixture), [("req21-invalid", assessment_at("req21"))])


class VerifyMigrationSpecificationTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build
    verify = VerifyTreeTests.verify

    def test_absent_or_ambiguous_migration_specification_is_spec09_unavailable(self) -> None:
        cases: tuple[tuple[str, Callable[[FixtureRoot], object]], ...] = (
            ("no matching file", lambda fixture: (fixture.root / SPEC09_PATH).unlink()),
            ("two matching files",
             lambda fixture: fixture.write(".ai/specs/09-second-copy.md", SPEC09_TEXT)),
            ("no specification directory", lambda fixture: shutil.rmtree(fixture.root / ".ai")),
            ("specification directory is a file", lambda fixture: (
                shutil.rmtree(fixture.root / ".ai/specs"), fixture.write(".ai/specs", "x\n"))),
        )
        for name, change in cases:
            with self.subTest(case=name):
                fixture, _ = self.build(name.replace(" ", "-"))
                change(fixture)
                result = self.verify(fixture)
                self.assertNotIn("Traceback", result.stderr)
                self.assert_reports(result, [("spec09-unavailable", SPEC09_ANY)])

    def test_unreadable_or_undecodable_migration_specification_is_spec09_unavailable(
            self) -> None:
        cases = (
            ("byte that is not UTF-8", SPEC09_TEXT.encode("utf-8") + b"\xff\n"),
            ("encoded surrogate", SPEC09_TEXT.encode("utf-8") + b"\xed\xa0\x80\n"),
        )
        for name, data in cases:
            with self.subTest(case=name):
                fixture, _ = self.build(name.replace(" ", "-"))
                fixture.write(SPEC09_PATH, data)
                result = self.verify(fixture)
                self.assertNotIn("Traceback", result.stderr)
                self.assert_reports(result, [("spec09-unavailable", f"{SPEC09_PATH}:0")])
        if os.geteuid() == 0:
            self.skipTest("permissions do not restrict the superuser")
        for name, target, location in (("unreadable file", SPEC09_PATH, f"{SPEC09_PATH}:0"),
                                       ("unreadable directory", ".ai/specs", SPEC09_ANY)):
            with self.subTest(case=name):
                fixture, _ = self.build(name.replace(" ", "-"))
                path = fixture.root / target
                original = path.stat().st_mode
                path.chmod(0)
                try:
                    result = self.verify(fixture)
                finally:
                    path.chmod(original)
                self.assertNotIn("Traceback", result.stderr)
                self.assert_reports(result, [("spec09-unavailable", location)])

    def test_large_migration_specification_is_searched_to_its_end(self) -> None:
        fixture, inventory = self.build("large")
        fixture.write(SPEC09_PATH, "word " * 1_000_000 + "\n" + "x" * 2_000_000 + "\n"
                      + SPEC09_TEXT)
        assessment = valid_assessment(inventory)
        assessment["amendments"].append(copy.deepcopy(assessment["amendments"][0])
                                        | {"id": "AMD-08-02", "target": "REQ-98"})
        (fixture.root / ASSESSMENT_PATH).write_text(canonical(assessment), encoding="utf-8")
        result = self.verify(fixture)
        self.assertNotIn("Traceback", result.stderr)
        self.assert_reports(result, [("amendment-target-unknown",
                                      assessment_at("AMD-08-02"))])


# ---------------------------------------------------------------------------
# Rendered report region and report checks
# ---------------------------------------------------------------------------

REPORT_BEGIN = "<!-- audit:generated:begin -->"
REPORT_END = "<!-- audit:generated:end -->"
EMPTY_REGION = f"{REPORT_BEGIN}\n{REPORT_END}\n"
REPORT_TITLE = f"# Rules and workflows audit — {AUDIT_DATE}\n"
SUBSECTIONS = (
    "Passport", "Inventory", "Sections", "References", "Loads", "Repeated loads",
    "Full-output candidates", "Harness-name candidates", "Repetition review",
    "Legacy mentions", "Duplicates", "Migration map", "Validator and test impact",
    "Spec 09 inputs", "Findings", "Amendments to spec 09", "Read coverage",
    "Installed comparison",
)
LINE_BREAK_CATEGORIES = frozenset({"Cc", "Zl", "Zp"})
EDGE_STATUS_ORDER = ("resolved", "resolved-prefix", "heading-unmarked", "missing-heading",
                     "missing-target", "missing-path", "unknown-command", "glob-empty",
                     "ambiguous-stem")
READER_CLASS_ORDER = ("active", "frozen", "planning", "history")
GAP_STATUSES = ("unavailable", "changed")
VALIDATOR = "scripts/validate-contracts.sh"
IMPACT_CONTEXTS = ("text", "check-description", "comment")
SCOPE_LINE = (
    "primary {primary} (`rules/`, `workflows/`); adapter {adapter} (`harness/`, "
    "`templates/codex-global-AGENTS.md`); readers {readers} (active {active}, "
    "frozen {frozen}, planning {planning}, history {history}); excluded "
    "`docs/audits/*-rules-workflows-audit.md`, "
    "`docs/audits/*-rules-workflows-audit.inventory.json`, "
    "`docs/audits/*-rules-workflows-audit.assessment.json`, "
    "`scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`; skipped "
    "`.git/`, `logs/`, `output/`, `__pycache__/`, `*.pyc`")
HEADERS = {
    "Inventory": ["Path", "Set", "Entry", "Tracked", "Words", "Bytes", "Kinds", "Coverage",
                  "Decision", "Findings"],
    "Sections": ["Path", "Section", "Line", "Words", "Bytes", "Kind", "Proposed home"],
    "References": ["Class", *EDGE_STATUS_ORDER],
    "Defect edges": ["Source:line:column", "Raw", "Form", "Context", "Status", "Candidates",
                     "Findings"],
    "Loads": ["Source:line", "Targets", "Mode", "Condition"],
    "Repeated loads": ["ID", "Caller", "Callee", "Target", "Disposition", "Finding"],
    "Full-output candidates": ["ID", "Source:line", "Text", "Disposition", "Finding"],
    "Harness-name candidates": ["ID", "Source:line", "Text", "Disposition", "Finding"],
    "Repetition review": ["Workflow", "Report findings", "Checkpoint findings",
                          "Review findings"],
    "Legacy mentions": ["Source:line", "Term", "Role", "Note"],
    "Duplicates": ["Group", "Clusters", "Locations", "Normative source",
                   "Condition differences", "Disposition", "Owner", "Finding"],
    "Migration map": ["Source", "Decision", "Targets", "Spec 09 default", "Deviation",
                      "Amendment"],
    "Validator and test impact": ["Source", "Decision", "Validator text",
                                  "Validator check-description", "Validator comment",
                                  "Other tests", "Frozen", "Hooks", "Other active"],
    "Spec 09 inputs": ["Source", "Decision", "Targets", "Amendment"],
    "Statements": ["Statement", "Text", "Covered by"],
    "Findings": ["ID", "Type", "Severity", "Source", "Section", "Owner", "Blocks 09", "Status",
                 "Observation", "Closure"],
    "Amendments to spec 09": ["ID", "Target", "Change", "Proposed", "Reason", "Evidence",
                              "Affected", "Depends on", "Requires ADR", "Disposition"],
    "Read coverage": ["Path", "Status", "SHA-256", "Reader"],
    "Installed comparison": ["Path", "Location", "Source SHA-256", "Installed SHA-256",
                             "Match"],
}
DIAGNOSTIC_CODES = (
    "inventory-missing", "assessment-missing", "report-missing", "inventory-invalid",
    "assessment-invalid", "report-name-date", "inventory-stale", "worktree-dirty",
    "digest-mismatch", "row-missing", "row-extra", "row-duplicate", "assessment-stale",
    "sections-incomplete", "load-unclassified", "candidate-undisposed", "repetition-invalid",
    "legacy-role-missing", "duplicate-ungrouped", "duplicate-multigrouped", "group-invalid",
    "defect-unrecorded", "finding-invalid", "finding-stale", "reference-unknown",
    "map-invalid", "split-sections-incomplete", "map-collision", "installed-name-collision",
    "stem-overlap", "kind-prefix-invalid", "deviation-unamended", "spec09-unavailable",
    "amendment-invalid", "amendment-target-unknown", "req21-invalid", "coverage-inconsistent",
    "report-layout", "review-commit-unknown", "report-generated-mismatch", "blocker-unlisted",
    "economics-claim", "installed-invalid",
    "evidence-unresolved", "blocker-extra",
)
UNKNOWN_COMMIT = "1" * 40
OTHER_DATE = "2026-01-03"
OVERSIZED_REPORT_BYTES = 1 << 30
IMPACT_SOURCE = "rules/a-b.md"
IMPACT_FILES: dict[str, str | bytes] = {
    IMPACT_SOURCE: "# A b\n",
    VALIDATOR: ("#!/bin/bash\n# The comment names rules/a-b.md and again rules/a-b.md.\n"
                'check "rules/a-b.md exists" '
                '"$(test -f rules/a-b.md && echo pass || echo missing)"\n'),
    "tests/t.py": 'PATH = "rules/a-b.md"\n',
    "tests/fixtures/validator-runtime/case.txt": "rules/a-b.md\n",
    "hooks/h.sh": "# rules/a-b.md rules/a-b.md rules/a-b.md\n",
    "docs/NOTE.md": "rules/a-b.md\n" * 4,
    ".ai/memory/state.md": "rules/a-b.md\n",
}
REPORT_AMOUNT_PATTERNS = (re.compile(r"(?i)\b\d[\d,.]*\s*k?\s*tokens?\b"),
                          re.compile(r"[$€£]\s?\d"), re.compile(r"\b(USD|EUR)\b"))
_TOOL_MODULES: list[object] = []
_REFRESHED: dict[Path, tuple[bytes, bytes, bytes]] = {}


def report_text(region: str = EMPTY_REGION, blockers: Sequence[str] = (),
                run_date: str = AUDIT_DATE, review: str = "Reviewed: pending",
                acceptance: str = "Accepted: pending",
                summary: str = "Every audited file was read once.",
                method: str = "The inventory was extracted at a clean commit.") -> str:
    """A report in the documented layout around the given generated region."""
    listed = "".join(f"- {item}\n" for item in blockers) or "None.\n"
    return (f"# Rules and workflows audit — {run_date}\n\n## Summary\n\n{summary}\n\n"
            f"## Method\n\n{method}\n\n{region}\n## Blockers for spec 09\n\n{listed}\n"
            f"## Independent review\n\n{review}\n\n## Acceptance\n\n{acceptance}\n")


def blocking_ids(assessment: object) -> list[str]:
    """Ids of the findings with `blocks_09: true` in a parsed assessment."""
    findings = assessment.get("findings") if isinstance(assessment, dict) else None
    if not isinstance(findings, list):
        return []
    return sorted(item["id"] for item in findings if isinstance(item, dict)
                  and item.get("blocks_09") is True and isinstance(item.get("id"), str))


def run_render(fixture: FixtureRoot, *extra: str, report: Path | None = None
               ) -> subprocess.CompletedProcess[str]:
    target = report if report is not None else fixture.root / REPORT_PATH
    return run_tool(["render", "--root", str(fixture.root), "--report", str(target), *extra],
                    fixture.env, fixture.base)


def regular_bytes(path: Path) -> bytes | None:
    """The bytes of a regular file that is not a symbolic link, otherwise None."""
    if path.is_symlink() or not path.is_file():
        return None
    return path.read_bytes()


def refresh_report(fixture: FixtureRoot) -> None:
    """Rewrite the report around the assessment on disk (its run date in the title, its
    blocking findings listed, pending review and acceptance) and fill the generated region
    with `render --write`. When the inputs break their schema the rendering fails and the
    region stays empty. The rewrite is skipped while the inputs and the report hold the
    bytes of the previous refresh of the same root, since it would write the same bytes."""
    root = fixture.root
    inputs = (regular_bytes(root / ASSESSMENT_PATH), regular_bytes(root / INVENTORY_PATH))
    report = regular_bytes(root / REPORT_PATH)
    previous = _REFRESHED.pop(root, None)
    if report is not None and previous == (*inputs, report):
        _REFRESHED[root] = previous
        return
    _write_refreshed_report(fixture)
    report = regular_bytes(root / REPORT_PATH)
    if inputs[0] is not None and inputs[1] is not None and report is not None:
        _REFRESHED[root] = (inputs[0], inputs[1], report)


def _write_refreshed_report(fixture: FixtureRoot) -> None:
    try:
        assessment = json.loads((fixture.root / ASSESSMENT_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        assessment = None
    run_date = assessment.get("run_date") if isinstance(assessment, dict) else None
    fixture.write(REPORT_PATH, report_text(
        blockers=blocking_ids(assessment),
        run_date=run_date if isinstance(run_date, str) else AUDIT_DATE))
    run_render(fixture, "--write")


def report_claims(fixture: FixtureRoot) -> list[tuple[str, str]]:
    """One economics claim per line of the fixture report outside the generated region
    (the lines from the begin marker through the end marker) that names a token count or a
    monetary amount by the documented patterns."""
    text = (fixture.root / REPORT_PATH).read_text(encoding="utf-8")
    claims: list[tuple[str, str]] = []
    inside = False
    for number, line in enumerate(text.split("\n"), start=1):
        inside = inside or line == REPORT_BEGIN
        if not inside and any(pattern.search(line) for pattern in REPORT_AMOUNT_PATTERNS):
            claims.append(("economics-claim", f"{REPORT_PATH}:{number}"))
        inside = inside and line != REPORT_END
    return claims


def tool_module() -> object:
    if not _TOOL_MODULES:
        _TOOL_MODULES.append(load_tool_module())
    return _TOOL_MODULES[0]


def cell(value: object) -> str:
    """Documented cell text: `-` for null, true or false, `none` for an empty list, list
    items joined by commas, each backslash run directly before a `|` doubled and the `|`
    escaped, and every line-breaking or control character a space."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(cell(item) for item in value) if value else "none"
    text = "".join(" " if unicodedata.category(character) in LINE_BREAK_CATEGORIES
                   else character for character in str(value))
    return re.sub(r"(\\*)\|", lambda found: found.group(1) * 2 + "\\|", text)


def md_row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def md_table(header: Sequence[str], rows: Sequence[Sequence[object]] = ()) -> list[str]:
    return [md_row(header), "|" + "---|" * len(header),
            *(md_row([cell(value) for value in row]) for row in rows)]


def first_with(rows: object, **fields: object) -> dict | None:
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and all(row.get(key) == value for key, value in fields.items()):
            return row
    return None


def target_text(target: dict) -> str:
    sections = target["sections"]
    return target["path"] if sections is None else f"{target['path']} [{', '.join(sections)}]"


def targets_text(targets: list[dict] | None) -> str | None:
    if targets is None:
        return None
    return "; ".join(target_text(item) for item in targets) or "none"


def passport_body(inventory: dict, assessment: dict) -> list[str]:
    gaps = sum(1 for row in assessment["coverage"] if row["status"] in GAP_STATUSES)
    findings = assessment["findings"]
    opened = sum(1 for item in findings if item["status"] == "open")
    blocking = sum(1 for item in findings if item["blocks_09"] is True)
    sets = Counter(entry["set"] for entry in inventory["files"])
    classes = Counter(entry["class"] for entry in inventory["readers"])
    scope = SCOPE_LINE.format(primary=sets["primary"], adapter=sets["adapter"],
                              readers=len(inventory["readers"]),
                              **{name: classes[name] for name in READER_CLASS_ORDER})
    environment = "; ".join(cell(value) for value in assessment["environment"].values())
    return [
        f"- source_revision: {cell(inventory['source_revision'])}",
        f"- worktree: {cell(inventory['worktree']['state'])}",
        f"- inventory_digest: {cell(inventory['inventory_digest'])}",
        f"- method_version: {cell(inventory['method_version'])}",
        f"- scope: {scope}",
        f"- installed_access: {cell(assessment['installed_access'])}",
        "- read_coverage: " + ("complete" if not gaps else f"partial ({gaps} gaps)"),
        f"- findings: {len(findings)} total, {opened} open, {blocking} blocking spec 09",
        f"- run_date: {cell(assessment['run_date'])}",
        f"- environment: {environment}",
    ]


def inventory_body(inventory: dict, assessment: dict) -> list[str]:
    rows = []
    for entry in inventory["files"]:
        path = entry["path"]
        files_row = first_with(assessment["files"], path=path)
        coverage = first_with(assessment["coverage"], path=path)
        mapped = first_with(assessment["map"], source=path)
        rows.append([path, entry["set"], entry["entry"], entry["tracked"], entry["words"],
                     entry["bytes"], files_row["kinds"] if files_row else None,
                     coverage["status"] if coverage else None,
                     mapped["decision"] if mapped else None,
                     sorted(item["id"] for item in assessment["findings"]
                            if item["source"] == path)])
    return md_table(HEADERS["Inventory"], rows)


def sections_body(inventory: dict, assessment: dict) -> list[str]:
    rows = []
    for entry in inventory["files"]:
        files_row = first_with(assessment["files"], path=entry["path"])
        listed = files_row["sections"] if files_row else None
        for section in entry["sections"]:
            match = first_with(listed, heading=section["heading"])
            rows.append([entry["path"], section["heading"], section["line"], section["words"],
                         section["bytes"], match["kind"] if match else None,
                         match["proposed_home"] if match else None])
    return md_table(HEADERS["Sections"], rows)


def naming_findings(assessment: dict, edge_entry: dict) -> list[str]:
    key = {"source": edge_entry["source"], "line": edge_entry["line"],
           "column": edge_entry["column"]}
    return sorted(item["id"] for item in assessment["findings"] if key in item["edges"])


def references_body(inventory: dict, assessment: dict) -> list[str]:
    counts = Counter((item["class"], item["status"]) for item in inventory["edges"])
    count_rows = [[name, *(counts[(name, status)] for status in EDGE_STATUS_ORDER)]
                  for name in READER_CLASS_ORDER]
    is_defect = tool_module().is_defect_edge
    defect_rows = [[f"{item['source']}:{item['line']}:{item['column']}", item["raw"],
                    item["form"], item["context"], item["status"],
                    [target["path"] + (f" ({target['heading_status']})"
                                       if target["heading_status"] else "")
                     for target in item["targets"]],
                    naming_findings(assessment, item)]
                   for item in inventory["edges"] if is_defect(item)]
    return (md_table(HEADERS["References"], count_rows) + [""]
            + md_table(HEADERS["Defect edges"], defect_rows))


def loads_body(inventory: dict, assessment: dict) -> list[str]:
    audited = {entry["path"] for entry in inventory["files"]}
    rows = []
    for item in inventory["edges"]:
        if item["load"] and item["source"] in audited:
            row = first_with(assessment["loads"], source=item["source"], line=item["line"],
                             column=item["column"])
            rows.append([f"{item['source']}:{item['line']}",
                         [target["path"] for target in item["targets"]],
                         row["mode"] if row else None, row["condition"] if row else None])
    return md_table(HEADERS["Loads"], rows)


def disposition_of(assessment: dict, identifier: str) -> list[object]:
    row = first_with(assessment["candidates"], id=identifier)
    return [row["disposition"], row["finding"]] if row else [None, None]


def candidate_bodies(inventory: dict, assessment: dict) -> dict[str, list[str]]:
    repeated = [[item["id"], item["caller"], item["callee"], item["target"],
                 *disposition_of(assessment, item["id"])] for item in inventory["repeat_loads"]]
    bodies = {"Repeated loads": md_table(HEADERS["Repeated loads"], repeated)}
    for name, key in (("Full-output candidates", "full_output"),
                      ("Harness-name candidates", "harness_names")):
        bodies[name] = md_table(HEADERS[name], [
            [item["id"], f"{item['source']}:{item['line']}", item["text"],
             *disposition_of(assessment, item["id"])] for item in inventory[key]])
    return bodies


def repetition_body(inventory: dict, assessment: dict) -> list[str]:
    rows = []
    for entry in inventory["files"]:
        if re.fullmatch(r"workflows/[^/]+\.md", entry["path"]) and (entry["invocation_lines"]
                                                                     or 0) > 0:
            files_row = first_with(assessment["files"], path=entry["path"])
            repetition = files_row["repetition"] if files_row else None
            rows.append([entry["path"], *((repetition[key] if repetition else None)
                                          for key in ("report", "checkpoint", "review"))])
    return md_table(HEADERS["Repetition review"], rows)


def legacy_body(inventory: dict, assessment: dict) -> list[str]:
    rows = []
    for item in inventory["legacy_mentions"]:
        row = first_with(assessment["legacy"], source=item["source"], line=item["line"],
                         column=item["column"])
        rows.append([f"{item['source']}:{item['line']}", item["term"],
                     row["role"] if row else None, row["note"] if row else None])
    return md_table(HEADERS["Legacy mentions"], rows)


def duplicates_body(inventory: dict, assessment: dict) -> list[str]:
    clusters = {item["id"]: item for item in inventory["duplicate_clusters"]}
    rows = []
    for group in sorted(assessment["duplicate_groups"], key=lambda item: item["id"]):
        spans = [member for identifier in group["clusters"] if identifier in clusters
                 for member in clusters[identifier]["members"]] + group["locations"]
        normative = group["normative_source"]
        rows.append([group["id"], group["clusters"],
                     [f"{span['path']}:{span['line_start']}-{span['line_end']}"
                      for span in spans],
                     f"{normative['path']} → {normative['section']}",
                     group["condition_differences"], group["disposition"], group["owner"],
                     group["finding"]])
    return md_table(HEADERS["Duplicates"], rows)


def mapped_in_order(assessment: dict) -> list[dict]:
    return sorted(assessment["map"], key=lambda item: item["source"])


def map_body(assessment: dict, deviating: Sequence[str]) -> list[str]:
    return md_table(HEADERS["Migration map"], [
        [row["source"], row["decision"], targets_text(row["targets"]),
         targets_text(row["spec09_default"]), "yes" if row["source"] in deviating else "no",
         row["amendment"]] for row in mapped_in_order(assessment)])


def impact_counts(inventory: dict, source: str) -> list[int]:
    """Edges that name the source, grouped as validator contexts, other tests, frozen,
    hooks and other active edge sources; planning and history edges are not counted."""
    counts = Counter()
    for item in inventory["edges"]:
        if source not in [target["path"] for target in item["targets"]]:
            continue
        if item["source"] == VALIDATOR:
            counts[item["context"]] += 1
        elif item["class"] == "frozen":
            counts["frozen"] += 1
        elif item["class"] == "active" and item["source"].startswith("tests/"):
            counts["tests"] += 1
        elif item["class"] == "active" and item["source"].startswith("hooks/"):
            counts["hooks"] += 1
        elif item["class"] == "active":
            counts["active"] += 1
    return [counts[name] for name in (*IMPACT_CONTEXTS, "tests", "frozen", "hooks", "active")]


def impact_body(inventory: dict, assessment: dict) -> list[str]:
    return md_table(HEADERS["Validator and test impact"], [
        [row["source"], row["decision"], *impact_counts(inventory, row["source"])]
        for row in mapped_in_order(assessment) if row["decision"] != "keep"])


def spec09_body(assessment: dict) -> list[str]:
    nulls = [[row["source"], row["decision"], targets_text(row["targets"]), row["amendment"]]
             for row in mapped_in_order(assessment) if row["spec09_default"] is None]
    record = assessment["req21"]
    return (md_table(HEADERS["Spec 09 inputs"], nulls)
            + ["", f"req21 verdict: {cell(record['verdict'])}", ""]
            + md_table(HEADERS["Statements"], [[item["source"], item["text"], item["covered_by"]]
                                               for item in record["statements"]]))


def findings_body(assessment: dict) -> list[str]:
    return md_table(HEADERS["Findings"], [
        [item["id"], item["type"], item["severity"], item["source"], item["section"],
         item["owner"], item["blocks_09"], item["status"], item["observation"], item["closure"]]
        for item in sorted(assessment["findings"], key=lambda row: row["id"])])


def amendments_body(assessment: dict) -> list[str]:
    return md_table(HEADERS["Amendments to spec 09"], [
        [item["id"], item["target"], item["change"], item["proposed"], item["reason"],
         item["evidence"], item["affected"], item["depends_on"], item["requires_adr"],
         item["disposition"]]
        for item in sorted(assessment["amendments"], key=lambda row: row["id"])])


def coverage_body(assessment: dict) -> list[str]:
    return md_table(HEADERS["Read coverage"], [
        [item["path"], item["status"], item["sha256"], item["reader"]]
        for item in sorted(assessment["coverage"], key=lambda row: row["path"])])


def installed_body(assessment: dict) -> list[str]:
    if assessment["installed_access"] == "not-verified":
        return ["Not verified."]
    return md_table(HEADERS["Installed comparison"], [
        [item["path"], item["location"], item["source_sha256"], item["installed_sha256"],
         "yes" if item["source_sha256"] == item["installed_sha256"] else "no"]
        for item in sorted(assessment["installed"], key=lambda row: row["path"])])


def expected_bodies(inventory: dict, assessment: dict, deviating: Sequence[str] = ()
                    ) -> dict[str, list[str]]:
    """The documented body of every subsection, computed independently of the tool."""
    return {
        "Passport": passport_body(inventory, assessment),
        "Inventory": inventory_body(inventory, assessment),
        "Sections": sections_body(inventory, assessment),
        "References": references_body(inventory, assessment),
        "Loads": loads_body(inventory, assessment),
        **candidate_bodies(inventory, assessment),
        "Repetition review": repetition_body(inventory, assessment),
        "Legacy mentions": legacy_body(inventory, assessment),
        "Duplicates": duplicates_body(inventory, assessment),
        "Migration map": map_body(assessment, deviating),
        "Validator and test impact": impact_body(inventory, assessment),
        "Spec 09 inputs": spec09_body(assessment),
        "Findings": findings_body(assessment),
        "Amendments to spec 09": amendments_body(assessment),
        "Read coverage": coverage_body(assessment),
        "Installed comparison": installed_body(assessment),
    }


def expected_region(inventory: dict, assessment: dict, deviating: Sequence[str] = ()) -> str:
    """Begin marker, blank line, each `### <name>` with a blank line, its body and a blank
    line, then the end marker; every line ends with LF."""
    bodies = expected_bodies(inventory, assessment, deviating)
    lines = [REPORT_BEGIN, ""]
    for name in SUBSECTIONS:
        lines += [f"### {name}", "", *bodies[name], ""]
    lines.append(REPORT_END)
    return "".join(f"{line}\n" for line in lines)


def region_bodies(region: str) -> dict[str, list[str]]:
    """The body lines of each `###` subsection without the blank lines around them."""
    bodies: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in region.split("\n"):
        if line.startswith("### "):
            current = bodies.setdefault(line[4:], [])
        elif current is not None and line != REPORT_END:
            current.append(line)
    for lines in bodies.values():
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
    return bodies


def line_number(text: str, line: str, occurrence: int = 0) -> int:
    """The 1-based number of the given occurrence of a whole line in the text."""
    numbers = [number for number, found in enumerate(text.split("\n"), start=1)
               if found == line]
    if len(numbers) <= occurrence:
        raise AssertionError(f"the line {line!r} is not in the text")
    return numbers[occurrence]


def file_snapshot(root: Path) -> dict[Path, bytes]:
    """The bytes of every regular file below root, outside `.git`."""
    found: dict[Path, bytes] = {}
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name != ".git"]
        for name in filenames:
            path = Path(directory) / name
            if not path.is_symlink():
                found[path] = path.read_bytes()
    return found


def restore_snapshot(root: Path, snapshot: dict[Path, bytes]) -> None:
    for path in file_snapshot(root):
        if path not in snapshot:
            path.unlink()
    for path, data in snapshot.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file() or path.read_bytes() != data:
            path.write_bytes(data)


class RenderCase(SharedVerifyCase):
    """Cases that render or verify the report of the valid pair."""

    def write_assessment(self) -> None:
        (self.fixture.root / ASSESSMENT_PATH).write_text(canonical(self.assessment),
                                                         encoding="utf-8")

    def render(self, *extra: str, report: Path | None = None
               ) -> subprocess.CompletedProcess[str]:
        self.write_assessment()
        return run_render(self.fixture, *extra, report=report)

    def region(self) -> str:
        result = self.render()
        self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)
        return result.stdout

    def bodies(self) -> dict[str, list[str]]:
        return region_bodies(self.region())

    def report_file(self) -> Path:
        return self.fixture.root / REPORT_PATH

    def audits_listing(self) -> list[str]:
        return sorted(os.listdir(self.report_file().parent))

    def head(self) -> str:
        return self.fixture.git("rev-parse", "HEAD")

    def valid_report(self, **changes: object) -> str:
        changes.setdefault("blockers", blocking_ids(self.assessment))
        return report_text(region=self.region(), **changes)

    def verify_report(self, text: str | bytes) -> subprocess.CompletedProcess[str]:
        self.write_assessment()
        self.fixture.write(REPORT_PATH, text)
        return self.run_verify()


class RenderRegionTests(RenderCase):
    def test_region_holds_both_markers_and_the_eighteen_subsections_in_order(self) -> None:
        region = self.region()
        lines = region.split("\n")
        self.assertEqual(lines[0], REPORT_BEGIN)
        self.assertEqual(lines[-2:], [REPORT_END, ""])
        self.assertEqual([line[4:] for line in lines if line.startswith("### ")],
                         list(SUBSECTIONS))

    def test_valid_pair_renders_exactly_the_documented_region(self) -> None:
        self.assertEqual(self.region(), expected_region(self.inventory, self.assessment))

    def test_rendering_is_byte_identical_across_runs_and_names_no_absolute_path(self) -> None:
        first, second = self.render(), self.render()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        for absolute in (str(self.fixture.base), "/home/", "/Users/", "/tmp"):
            self.assertNotIn(absolute, first.stdout)

    def test_passport_states_partial_read_coverage_with_its_gap_count(self) -> None:
        body = self.bodies()["Passport"]
        self.assertEqual(body, passport_body(self.inventory, self.assessment))
        self.assertIn("- read_coverage: partial (1 gaps)", body)
        self.assertIn("- findings: 5 total, 5 open, 2 blocking spec 09", body)
        self.assertIn(f"- source_revision: {self.inventory['source_revision']}", body)
        self.assertIn("- installed_access: not-verified", body)
        for statuses, expected in (({BLOB: "read"}, "- read_coverage: complete"),
                                   ({DELTA: "changed"}, "- read_coverage: partial (2 gaps)")):
            with self.subTest(statuses=statuses):
                self.assessment = valid_assessment(self.inventory)
                for path, status in statuses.items():
                    self.row("coverage", path)["status"] = status
                self.finding("AUD-08-002")["status"] = "historical-fixed"
                body = self.bodies()["Passport"]
                self.assertIn(expected, body)
                self.assertIn("- findings: 5 total, 4 open, 2 blocking spec 09", body)

    def test_inventory_and_sections_tables_follow_path_and_line_order(self) -> None:
        bodies = self.bodies()
        self.assertEqual(bodies["Inventory"], inventory_body(self.inventory, self.assessment))
        self.assertIn(md_row([LINK, "adapter", "symlink", "true", "-", "-", "adapter-config",
                              "not-a-file", "keep", "none"]), bodies["Inventory"])
        gamma = [line for line in bodies["Inventory"] if line.startswith(f"| {GAMMA} |")]
        self.assertEqual(len(gamma), 1)
        self.assertTrue(gamma[0].endswith(" | AUD-08-003, AUD-08-004 |"), gamma[0])
        self.assertEqual(bodies["Sections"], sections_body(self.inventory, self.assessment))
        example = inventory_entry(self.inventory, ALPHA)["sections"][2]
        self.assertIn(md_row([ALPHA, "## Example", str(example["line"]), str(example["words"]),
                              str(example["bytes"]), "reference", "rules/reference/alpha.md"]),
                      bodies["Sections"])
        delta = inventory_entry(self.inventory, DELTA)["sections"][0]
        self.assertIn(md_row([DELTA, "(preamble)", str(delta["line"]), str(delta["words"]),
                              str(delta["bytes"]), "-", "-"]), bodies["Sections"])

    def test_references_count_edges_by_class_and_status_and_list_every_defect_edge(
            self) -> None:
        body = self.bodies()["References"]
        self.assertEqual(body, references_body(self.inventory, self.assessment))
        separator = body.index("")
        self.assertEqual(body[0], md_row(HEADERS["References"]))
        self.assertEqual([line.split(" | ")[0] for line in body[2:separator]],
                         [f"| {name}" for name in READER_CLASS_ORDER])
        defects = body[separator + 3:]
        self.assertEqual(len(defects), 3, defects)
        column = edge_ref(self.inventory, BETA, 9)["column"]
        self.assertIn(md_row([f"{BETA}:9:{column}", "alpha-flow → ## Missing", "section-ref",
                              "span", "missing-heading", f"{ALPHA} (missing-heading)",
                              "AUD-08-001"]), defects)

    def test_loads_candidates_repetition_and_legacy_tables(self) -> None:
        bodies = self.bodies()
        expected = expected_bodies(self.inventory, self.assessment)
        for name in ("Loads", "Repeated loads", "Full-output candidates",
                     "Harness-name candidates", "Repetition review", "Legacy mentions"):
            with self.subTest(subsection=name):
                self.assertEqual(bodies[name], expected[name])
        self.assertIn(md_row([f"{GAMMA}:5", ALPHA, "conditional", "when the flow is active"]),
                      bodies["Loads"])
        self.assertIn(md_row([f"{BETA}:8", ALPHA, "mandatory", "-"]), bodies["Loads"])
        self.assertEqual(bodies["Repeated loads"][2:], [
            md_row(["RL-001", GAMMA, BETA, ALPHA, "finding", "AUD-08-003"])])
        self.assertEqual(bodies["Repetition review"][2:], [
            md_row([BETA, "none", "none", "none"]),
            md_row([GAMMA, "AUD-08-004", "none", "none"])])

    def test_duplicate_groups_list_cluster_members_and_read_detected_locations(self) -> None:
        group = self.assessment["duplicate_groups"][0]
        group["locations"] = [{"path": GUIDE, "line_start": 1, "line_end": 1}]
        body = self.bodies()["Duplicates"]
        self.assertEqual(body, duplicates_body(self.inventory, self.assessment))
        members = self.inventory["duplicate_clusters"][0]["members"]
        locations = ", ".join([f"{item['path']}:{item['line_start']}-{item['line_end']}"
                               for item in members] + [f"{GUIDE}:1-1"])
        self.assertEqual(body[2:], [md_row([
            "DG-001", "DUP-001", locations, f"{DELTA} → (preamble)", "None.", "intentional",
            "none", "-"])])

    def test_migration_map_shows_targets_with_sections_default_and_computed_deviation(
            self) -> None:
        body = self.bodies()["Migration map"]
        self.assertEqual(body, map_body(self.assessment, ()))
        split = ("rules/bootstrap-discovery.md [(preamble)]; rules/protocol-discovery-conduct.md "
                 "[## Codebase Reading Rules, ## Decision Protocol, ## Other]")
        self.assertIn(md_row([PHASE_DISCOVERY, "split",
                              f"{split}; rules/reference/discovery-examples.md", split, "no",
                              "-"]), body)
        delta = self.assessment["map"][row_index(self.assessment["map"], "source", DELTA)]
        delta.update(spec09_default=None, amendment="AMD-08-01")
        alpha = self.assessment["map"][row_index(self.assessment["map"], "source", ALPHA)]
        alpha["targets"] = [map_target("rules/contract-alpha-other.md")]
        alpha["amendment"] = "AMD-08-01"
        bodies = self.bodies()
        self.assertEqual(bodies["Migration map"], map_body(self.assessment, (ALPHA, DELTA)))
        self.assertIn(md_row([DELTA, "rename", "rules/contract-delta-rule.md", "-", "yes",
                              "AMD-08-01"]), bodies["Migration map"])
        self.assertEqual(bodies["Spec 09 inputs"][2], md_row([
            DELTA, "rename", "rules/contract-delta-rule.md", "AMD-08-01"]))

    def test_spec09_inputs_list_null_default_entries_and_the_statement_coverage(self) -> None:
        body = self.bodies()["Spec 09 inputs"]
        self.assertEqual(body, md_table(HEADERS["Spec 09 inputs"]) + [
            "", "req21 verdict: covered", ""] + md_table(HEADERS["Statements"], [
                [f"{PHASE_DISCOVERY}:{line}", "A statement of the rule.", f"{ALPHA}:9"]
                for line in STATEMENT_UNIT_LINES]))
        self.assessment["req21"]["verdict"] = "not-covered"
        self.assessment["req21"]["statements"][0]["covered_by"] = None
        body = self.bodies()["Spec 09 inputs"]
        self.assertEqual(body, spec09_body(self.assessment))
        self.assertIn("req21 verdict: not-covered", body)
        self.assertIn(md_row([f"{PHASE_DISCOVERY}:7", "A statement of the rule.", "-"]), body)

    def test_findings_amendments_and_read_coverage_are_ordered_by_id_and_path(self) -> None:
        self.assessment["findings"].reverse()
        self.assessment["coverage"].reverse()
        bodies = self.bodies()
        self.assertEqual(bodies["Findings"], findings_body(self.assessment))
        self.assertEqual([line.split(" | ")[0] for line in bodies["Findings"][2:]],
                         [f"| AUD-08-00{number}" for number in range(1, 6)])
        self.assertIn(md_row(["AUD-08-001", "reference-defect", "major", BETA, "(preamble)",
                              "09", "true", "open", "Observed on reading.",
                              "The cited lines are corrected."]), bodies["Findings"])
        self.assertEqual(bodies["Amendments to spec 09"][2:], [md_row([
            "AMD-08-01", "REQ-21", "editorial", "Proposed text.",
            "The reference names a heading that does not exist.", "AUD-08-001", "AC-05",
            "none", "false", "proposed"])])
        self.assertEqual(bodies["Read coverage"], coverage_body(self.assessment))
        self.assertEqual([line.split(" | ")[0] for line in bodies["Read coverage"][2:]],
                         [f"| {path}" for path in sorted(item["path"] for item in
                                                         self.assessment["coverage"])])

    def test_installed_comparison_is_not_verified_or_lists_each_copy_with_its_match(
            self) -> None:
        self.assertEqual(self.bodies()["Installed comparison"], ["Not verified."])
        self.assessment["installed_access"] = "verified"
        self.assertEqual(self.bodies()["Installed comparison"],
                         md_table(HEADERS["Installed comparison"]))
        digest = inventory_entry(self.inventory, DELTA)["sha256"]
        self.assessment["installed"] = [
            {"path": DELTA, "location": "~/.claude/skills/rule-delta-rule/SKILL.md",
             "source_sha256": digest, "installed_sha256": "0" * 64},
            {"path": ALPHA, "location": "~/.claude/skills/rule-alpha-flow/SKILL.md",
             "source_sha256": digest, "installed_sha256": digest},
        ]
        body = self.bodies()["Installed comparison"]
        self.assertEqual(body, installed_body(self.assessment))
        self.assertEqual([line.split(" | ")[0] for line in body[2:]], [f"| {ALPHA}",
                                                                      f"| {DELTA}"])
        self.assertTrue(body[2].endswith(" | yes |") and body[3].endswith(" | no |"), body)

    def test_cells_escape_pipes_and_replace_line_breaks_with_spaces(self) -> None:
        self.finding("AUD-08-002")["observation"] = "a|b\nc\r\nd e\x85f\tg"
        self.assessment["legacy"][0]["note"] = "x | y\n## Not a heading"
        self.assessment["environment"]["python"] = "Python 3.12\nsecond"
        region = self.region()
        bodies = region_bodies(region)
        self.assertEqual(region, expected_region(self.inventory, self.assessment))
        self.assertIn("a\\|b c  d e f g", bodies["Findings"][3])
        self.assertTrue(bodies["Legacy mentions"][2].endswith(" | x \\| y ## Not a heading |"))
        self.assertIn("- environment: Python 3.12 second; git version 2.43.0",
                      bodies["Passport"])
        self.assertEqual(len(bodies["Findings"]), 7)
        self.assertEqual([line for line in region.split("\n") if line.startswith("## ")], [])

    def test_empty_tables_keep_their_header_and_separator_rows(self) -> None:
        for key in ("findings", "amendments", "duplicate_groups", "candidates", "legacy",
                    "loads"):
            self.assessment[key] = []
        for row in self.assessment["files"]:
            if row["repetition"] is not None:
                row["repetition"] = empty_repetition()
        bodies = self.bodies()
        for name in ("Findings", "Amendments to spec 09", "Duplicates"):
            with self.subTest(subsection=name):
                self.assertEqual(bodies[name], md_table(HEADERS[name]))
        self.assertEqual(bodies["Repeated loads"][2:], [
            md_row(["RL-001", GAMMA, BETA, ALPHA, "-", "-"])])
        self.assertEqual(bodies["Repetition review"][2:], [
            md_row([BETA, "none", "none", "none"]), md_row([GAMMA, "none", "none", "none"])])
        self.assertIn(md_row([f"{GAMMA}:5", ALPHA, "-", "-"]), bodies["Loads"])
        self.assertIn("- findings: 0 total, 0 open, 0 blocking spec 09", bodies["Passport"])


class RenderCommandTests(RenderCase):
    def test_render_without_write_prints_the_region_reads_no_report_and_writes_nothing(
            self) -> None:
        self.write_assessment()
        self.report_file().unlink()
        before = tree_digests(self.fixture.base)
        result = run_render(self.fixture)
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(result.stdout, expected_region(self.inventory, self.assessment))
        self.assertEqual(tree_digests(self.fixture.base), before)

    def test_inputs_that_break_their_schema_exit_one_with_diagnostics_and_no_region(
            self) -> None:
        del self.assessment["installed"]
        report_before = self.report_file().read_bytes()
        for extra in ((), ("--write",)):
            with self.subTest(arguments=extra):
                result = self.render(*extra)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertNotIn(REPORT_BEGIN, result.stdout)
                self.assertEqual(diagnostic_pairs(result),
                                 [("assessment-invalid", assessment_at("installed"))])
                self.assertEqual(self.report_file().read_bytes(), report_before)
        self.assessment = valid_assessment(self.inventory)
        inventory_file = self.fixture.root / INVENTORY_PATH
        original = inventory_file.read_bytes()
        inventory_file.unlink()
        try:
            result = self.render()
        finally:
            inventory_file.write_bytes(original)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(diagnostic_pairs(result), [("inventory-missing", f"{INVENTORY_PATH}:0")])

    def test_usage_errors_exit_two_with_one_error_line(self) -> None:
        self.assertEqual(self.render().returncode, 0)
        root, report = str(self.fixture.root), str(self.report_file())
        cases = {
            "no report": ["render", "--root", root],
            "report not markdown": ["render", "--root", root, "--report",
                                    str(self.fixture.root / "docs/audits/report.txt")],
            "unknown option": ["render", "--root", root, "--report", report, "--fast"],
            "argument with a line break": ["render", "--root", root, "--report", report,
                                           "extra\nargument"],
        }
        for name, arguments in cases.items():
            with self.subTest(case=name):
                before = self.report_file().read_bytes()
                result = run_tool(arguments, self.fixture.env, self.fixture.base)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                lines = result.stderr.splitlines()
                self.assertEqual(len(lines), 1, lines)
                self.assertTrue(lines[0].startswith("ERROR: "), lines)
                self.assertEqual(self.report_file().read_bytes(), before)

    def test_region_is_utf8_in_every_locale_and_equals_the_written_region(self) -> None:
        self.finding("AUD-08-002")["observation"] = "Naïve façade — ünïcode"
        self.write_assessment()
        self.fixture.write(REPORT_PATH, report_text(blockers=blocking_ids(self.assessment)))
        written = self.render("--write")
        self.assertEqual((written.returncode, written.stdout, written.stderr), (0, "", ""))
        text = self.report_file().read_text(encoding="utf-8")
        region = text[text.index(REPORT_BEGIN):text.index(REPORT_END) + len(REPORT_END) + 1]
        for locale_name in ("C", "C.UTF-8", "en_US.UTF-8"):
            with self.subTest(locale=locale_name):
                if not locale_available(locale_name):
                    self.skipTest(f"the locale {locale_name} is not installed")
                result = run_tool_bytes(
                    [b"render", b"--root", os.fsencode(self.fixture.root), b"--report",
                     os.fsencode(self.report_file())],
                    dict(self.fixture.env, LC_ALL=locale_name), self.fixture.base)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, region.encode("utf-8"))


class RenderWriteTests(RenderCase):
    def test_render_write_replaces_only_the_region_and_a_second_run_changes_nothing(
            self) -> None:
        stale = f"{REPORT_BEGIN}\n### Passport\n\nstale line\n{REPORT_END}\n"
        hand = report_text(region=stale, blockers=blocking_ids(self.assessment),
                           summary="Hand-written | summary.\n\nSecond paragraph.",
                           review=f"Reviewed: Validator {OTHER_DATE} pass {self.head()}")
        self.write_assessment()
        self.fixture.write(REPORT_PATH, hand)
        before = tree_digests(self.fixture.base)
        result = run_render(self.fixture, "--write")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        text = self.report_file().read_text(encoding="utf-8")
        prefix, suffix = hand.split(stale)
        self.assertEqual(text, prefix + expected_region(self.inventory, self.assessment) + suffix)
        after = tree_digests(self.fixture.base)
        changed = {path for path in before.keys() | after.keys()
                   if before.get(path) != after.get(path)}
        self.assertEqual(changed, {f"root/{REPORT_PATH}"})
        again = run_render(self.fixture, "--write")
        self.assertEqual((again.returncode, again.stdout, again.stderr), (0, "", ""))
        self.assertEqual(tree_digests(self.fixture.base), after)
        self.assert_silent(self.run_verify())

    def assert_refused(self, result: subprocess.CompletedProcess[str], code: str,
                       before: bytes | None, listing: list[str]) -> None:
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "")
        lines = result.stderr.splitlines()
        self.assertEqual(len(lines), 1, lines)
        self.assertTrue(lines[0].startswith(f"ERROR: {code}: "), lines)
        if before is not None:
            self.assertEqual(self.report_file().read_bytes(), before)
        self.assertEqual(self.audits_listing(), listing)

    def test_render_write_without_one_marker_pair_exits_two_and_leaves_the_file_unchanged(
            self) -> None:
        region = f"{REPORT_BEGIN}\n{REPORT_END}\n"
        cases = {
            "no markers": report_text(region=""),
            "begin marker only": report_text(region=f"{REPORT_BEGIN}\n"),
            "end marker only": report_text(region=f"{REPORT_END}\n"),
            "begin marker repeated": report_text(region=f"{REPORT_BEGIN}\n{region}"),
            "end marker repeated": report_text(region=f"{region}{REPORT_END}\n"),
            "markers reversed": report_text(region=f"{REPORT_END}\n{REPORT_BEGIN}\n"),
            "markers with trailing spaces": report_text(
                region=f"{REPORT_BEGIN} \n{REPORT_END} \n"),
            "marker inside a fence": report_text(
                method=f"```\n{REPORT_BEGIN}\n```", region=region),
        }
        self.write_assessment()
        for name, text in cases.items():
            with self.subTest(case=name):
                self.fixture.write(REPORT_PATH, text)
                before, listing = self.report_file().read_bytes(), self.audits_listing()
                self.assert_refused(run_render(self.fixture, "--write"), "report-markers",
                                    before, listing)

    def test_render_write_refuses_a_report_it_cannot_read_without_writing(self) -> None:
        report = self.report_file()
        valid = report.read_bytes()

        def oversized() -> None:
            report.unlink()
            with open(report, "wb") as handle:
                handle.truncate(OVERSIZED_REPORT_BYTES)

        def linked() -> None:
            report.unlink()
            (report.parent / "linked-target.txt").write_bytes(valid)
            report.symlink_to("linked-target.txt")

        cases: dict[str, Callable[[], object]] = {
            "missing": report.unlink,
            "directory": lambda: (report.unlink(), report.mkdir()),
            "symbolic link": linked,
            "byte that is not UTF-8": lambda: report.write_bytes(valid + b"\xff\n"),
            "encoded surrogate": lambda: report.write_bytes(valid + b"\xed\xa0\x80\n"),
            "larger than the size limit": oversized,
        }
        self.write_assessment()
        for name, change in cases.items():
            with self.subTest(case=name):
                change()
                listing = self.audits_listing()
                before = report.read_bytes() if report.is_file() and name not in (
                    "larger than the size limit", "symbolic link") else None
                try:
                    self.assert_refused(run_render(self.fixture, "--write"),
                                        "report-unreadable", before, listing)
                    if name == "symbolic link":
                        self.assertTrue(report.is_symlink())
                        self.assertEqual((report.parent / "linked-target.txt").read_bytes(),
                                         valid)
                finally:
                    if report.is_symlink() or report.is_file():
                        report.unlink()
                    elif report.is_dir():
                        report.rmdir()
                    with suppress(FileNotFoundError):
                        (report.parent / "linked-target.txt").unlink()
                    report.write_bytes(valid)

    def test_render_write_into_a_directory_without_write_permission_leaves_no_file(
            self) -> None:
        if os.geteuid() == 0:
            self.skipTest("permissions do not restrict the superuser")
        self.write_assessment()
        self.fixture.write(REPORT_PATH, report_text(blockers=blocking_ids(self.assessment)))
        directory = self.report_file().parent
        before, listing = self.report_file().read_bytes(), self.audits_listing()
        directory.chmod(0o555)
        try:
            result = run_render(self.fixture, "--write")
        finally:
            directory.chmod(0o755)
        self.assert_refused(result, "report-unwritable", before, listing)


class VerifyReportTests(RenderCase):
    def test_report_in_the_documented_layout_is_silent_and_an_absent_report_is_missing(
            self) -> None:
        head = self.head()
        fenced = ("Commands run:\n\n```\n# Rules and workflows audit — x\n## Summary\n"
                  "### Passport\n```")
        cases = {
            "pending review": {},
            "passing review": {"review": f"Reviewed: Validator {OTHER_DATE} pass {head}"},
            "failing review": {"review": f"Reviewed: Peer-Validator-2 {OTHER_DATE} fail {head}"},
            "owner acceptance": {"acceptance": f"Accepted: owner {OTHER_DATE}"},
            "headings inside a fence": {"method": fenced},
            "extra listed ids": {"blockers": ["AUD-08-001 (AMD-08-01)", "AUD-08-005"]},
            "subsection headings in hand-written text": {
                "summary": "### Scope\n\nEvery audited file was read once.",
                "method": "### Commands\n\nThe inventory was extracted."},
        }
        for name, changes in cases.items():
            with self.subTest(case=name):
                self.assert_silent(self.verify_report(self.valid_report(**changes)))
        self.report_file().unlink()
        self.assert_reports(self.run_verify(), [("report-missing", f"{REPORT_PATH}:0")])

    def test_layout_faults_are_report_layout(self) -> None:
        head = self.head()
        valid = self.valid_report()
        summary = "## Summary\n\nEvery audited file was read once.\n\n"
        method = "## Method\n\nThe inventory was extracted at a clean commit.\n\n"
        begin, end = f"{REPORT_BEGIN}\n", f"{REPORT_END}\n"

        def review(line: str) -> str:
            return valid.replace("Reviewed: pending\n", f"{line}\n", 1)

        def acceptance(line: str) -> str:
            return valid.replace("Accepted: pending\n", f"{line}\n", 1)

        cases = {
            "title missing": valid.replace(REPORT_TITLE, "", 1),
            "title with another date": valid.replace(
                REPORT_TITLE, f"# Rules and workflows audit — {OTHER_DATE}\n", 1),
            "title not on the first line": "\n" + valid,
            "second level-one heading": valid.replace(method, "# Extra\n\n" + method, 1),
            "summary heading missing": valid.replace("## Summary\n", "", 1),
            "method before summary": valid.replace(summary + method, method + summary, 1),
            "repeated summary heading": valid.replace(method, method + "## Summary\n\n", 1),
            "unknown level-two heading": valid + "\n## Notes\n\nLater text.\n",
            "blockers heading missing": valid.replace("## Blockers for spec 09\n", "", 1),
            "begin marker repeated": valid.replace(method, method + begin, 1),
            "end marker repeated": valid.replace(end, end + end, 1),
            "end marker missing": valid.replace(end, "", 1),
            "markers reversed": valid.replace(begin, "\0", 1).replace(end, begin, 1)
                                     .replace("\0", end, 1),
            "begin marker with a trailing space": valid.replace(begin, f"{REPORT_BEGIN} \n", 1),
            "region before the method heading": valid.replace(method, "", 1).replace(
                "## Blockers for spec 09\n", method + "## Blockers for spec 09\n", 1),
            "review line missing": review(""),
            "review line repeated": review("Reviewed: pending\nReviewed: pending"),
            "text beside the review line": review("Reviewed: pending\nLooks fine."),
            "review without role": review(f"Reviewed: {OTHER_DATE} pass {head}"),
            "role starting with a digit": review(f"Reviewed: 9validator {OTHER_DATE} pass {head}"),
            "role with an underscore": review(f"Reviewed: Valid_ator {OTHER_DATE} pass {head}"),
            "review date not in the calendar": review(
                f"Reviewed: Validator 2026-02-30 pass {head}"),
            "review date without padding": review(f"Reviewed: Validator 2026-1-03 pass {head}"),
            "review verdict outside pass and fail": review(
                f"Reviewed: Validator {OTHER_DATE} passed {head}"),
            "review commit in upper case": review(
                f"Reviewed: Validator {OTHER_DATE} pass {head.upper()}"),
            "review commit too short": review(f"Reviewed: Validator {OTHER_DATE} pass {head[:39]}"),
            "review with trailing text": review(
                f"Reviewed: Validator {OTHER_DATE} pass {head} later"),
            "acceptance by another role": acceptance(f"Accepted: Validator {OTHER_DATE}"),
            "acceptance date not in the calendar": acceptance("Accepted: owner 2026-13-01"),
            "acceptance without a date": acceptance("Accepted: owner"),
            "acceptance line repeated": acceptance("Accepted: pending\nAccepted: pending"),
            "acceptance line missing": acceptance(""),
        }
        for name, text in cases.items():
            with self.subTest(case=name):
                self.assertNotEqual(text, valid)
                result = self.verify_report(text)
                self.assertNotIn("Traceback", result.stderr)
                self.assert_codes(result, "report-layout", f"{REPORT_PATH}:")
        result = self.verify_report(valid.replace(method, method + begin, 1))
        self.assert_reports(result, [("report-layout", f"{REPORT_PATH}:12")])

    def test_report_that_cannot_be_read_as_text_is_report_layout_at_line_zero(self) -> None:
        report = self.report_file()
        valid = self.valid_report().encode("utf-8")

        def oversized() -> None:
            with open(report, "wb") as handle:
                handle.truncate(OVERSIZED_REPORT_BYTES)

        def linked() -> None:
            (report.parent / "linked-target.txt").write_bytes(valid)
            report.symlink_to("linked-target.txt")

        cases: dict[str, Callable[[], object]] = {
            "byte that is not UTF-8": lambda: report.write_bytes(valid + b"\xff\n"),
            "encoded surrogate": lambda: report.write_bytes(valid + b"\xed\xa0\x80\n"),
            "directory": report.mkdir,
            "symbolic link": linked,
            "larger than the size limit": oversized,
        }
        self.write_assessment()
        for name, change in cases.items():
            with self.subTest(case=name):
                report.unlink()
                change()
                try:
                    result = self.run_verify()
                finally:
                    if report.is_dir() and not report.is_symlink():
                        report.rmdir()
                    else:
                        report.unlink()
                    with suppress(FileNotFoundError):
                        (report.parent / "linked-target.txt").unlink()
                    report.write_bytes(valid)
                self.assertNotIn("Traceback", result.stderr)
                self.assert_reports(result, [("report-layout", f"{REPORT_PATH}:0")])

    def test_review_commit_absent_from_the_repository_is_review_commit_unknown(self) -> None:
        tree = self.fixture.git("rev-parse", "HEAD^{tree}")
        for name, commit in (("unknown commit", UNKNOWN_COMMIT), ("tree object", tree)):
            with self.subTest(case=name):
                line = f"Reviewed: Validator {OTHER_DATE} pass {commit}"
                text = self.valid_report(review=line)
                self.assert_reports(self.verify_report(text), [
                    ("review-commit-unknown", f"{REPORT_PATH}:{line_number(text, line)}")])
        self.assert_silent(self.verify_report(self.valid_report(
            review=f"Reviewed: Validator {OTHER_DATE} pass {self.head()}")))

    def test_file_name_date_unequal_to_the_run_date_is_report_name_date(self) -> None:
        text = self.valid_report()
        directory = self.report_file().parent
        for stem in (f"{OTHER_DATE}-rules-workflows-audit", "final-rules-workflows-audit"):
            with self.subTest(stem=stem):
                for suffix in (".inventory.json", ".assessment.json"):
                    shutil.copyfile(self.fixture.root / (REPORT_PATH[:-3] + suffix),
                                    directory / (stem + suffix))
                (directory / f"{stem}.md").write_text(text, encoding="utf-8")
                try:
                    result = run_tool(["verify", "--root", str(self.fixture.root), "--report",
                                       str(directory / f"{stem}.md")],
                                      self.fixture.env, self.fixture.base)
                finally:
                    for suffix in (".md", ".inventory.json", ".assessment.json"):
                        (directory / (stem + suffix)).unlink()
                self.assert_reports(result, [("report-name-date",
                                              f"docs/audits/{stem}.md:0")])

    def test_blocking_finding_missing_from_the_blockers_section_is_blocker_unlisted(
            self) -> None:
        heading = "## Blockers for spec 09"
        cases = {
            "one id left out": {"blockers": ["AUD-08-001"]},
            "id named only in the summary": {"blockers": ["AUD-08-001"],
                                             "summary": "AUD-08-005 is a blocker."},
            "id inside a longer token": {"blockers": ["AUD-08-001", "AUD-08-0050"]},
        }
        for name, changes in cases.items():
            with self.subTest(case=name):
                text = self.valid_report(**changes)
                self.assert_reports(self.verify_report(text), [
                    ("blocker-unlisted", f"{REPORT_PATH}:{line_number(text, heading)}")])
        text = self.valid_report(blockers=[])
        location = f"{REPORT_PATH}:{line_number(text, heading)}"
        self.assert_reports(self.verify_report(text), [
            ("blocker-unlisted", location), ("blocker-unlisted", location),
            ("report-layout", f"{REPORT_PATH}:{line_number(text, 'None.')}")])

    def test_changed_generated_region_is_report_generated_mismatch_at_its_first_line(
            self) -> None:
        text = self.valid_report()
        run_date_line = f"- run_date: {AUDIT_DATE}"
        edited = text.replace(run_date_line, f"- run_date: {OTHER_DATE}", 1)
        self.assert_reports(self.verify_report(edited), [
            ("report-generated-mismatch",
             f"{REPORT_PATH}:{line_number(text, run_date_line)}")])
        dropped = text.replace("Not verified.\n", "", 1)
        self.assert_reports(self.verify_report(dropped), [
            ("report-generated-mismatch",
             f"{REPORT_PATH}:{line_number(text, 'Not verified.')}")])
        stale = self.valid_report()
        self.finding("AUD-08-002")["observation"] = "Observed again on reading."
        fresh = self.valid_report()
        first = next(number for number, (old, new) in enumerate(
            zip(stale.split("\n"), fresh.split("\n")), start=1) if old != new)
        self.assert_reports(self.verify_report(stale), [
            ("report-generated-mismatch", f"{REPORT_PATH}:{first}")])

    def test_amounts_outside_the_generated_region_are_economics_claims(self) -> None:
        text = self.valid_report(summary="The change saves 3,000 tokens.",
                                 method="One run costs $5 in total.")
        self.assert_reports(self.verify_report(text), [
            ("economics-claim", f"{REPORT_PATH}:5"), ("economics-claim", f"{REPORT_PATH}:9")])
        self.finding("AUD-08-002")["observation"] = "It saves 3,000 tokens."
        text = self.valid_report()
        rows = [number for number, line in enumerate(text.split("\n"), start=1)
                if "It saves 3,000 tokens." in line]
        self.assertEqual(len(rows), 1)
        self.assert_reports(self.verify_report(text), [
            ("economics-claim", assessment_at("AUD-08-002"))])

    def test_report_rules_that_need_no_valid_input_run_when_an_input_breaks_its_schema(
            self) -> None:
        valid = self.valid_report()
        method = "## Method\n\nThe inventory was extracted at a clean commit.\n\n"
        review = f"Reviewed: Validator {OTHER_DATE} pass {UNKNOWN_COMMIT}"
        reviewed = valid.replace("Reviewed: pending", review, 1)
        stale = f"{REPORT_BEGIN}\n### Passport\n\nstale line\n{REPORT_END}\n"
        cases: dict[str, tuple[str | None, set[tuple[str, str]]]] = {
            "report absent": (None, {("report-missing", f"{REPORT_PATH}:0")}),
            "marker repeated": (valid.replace(method, method + f"{REPORT_BEGIN}\n", 1),
                                {("report-layout", f"{REPORT_PATH}:12")}),
            "unknown review commit": (reviewed, {
                ("review-commit-unknown", f"{REPORT_PATH}:{line_number(reviewed, review)}")}),
            "amount in the summary": (report_text(summary="It saves 3,000 tokens."),
                                      {("economics-claim", f"{REPORT_PATH}:5")}),
            "rules that need the inputs": (report_text(region=stale, run_date=OTHER_DATE),
                                           set()),
        }
        for name, (text, expected) in cases.items():
            with self.subTest(case=name, broken="assessment"):
                if text is None:
                    self.report_file().unlink()
                else:
                    self.fixture.write(REPORT_PATH, text)
                (self.fixture.root / ASSESSMENT_PATH).write_text("{\n", encoding="utf-8")
                result = self.run_verify()
                self.assertNotIn("Traceback", result.stderr)
                pairs = diagnostic_pairs(result)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("assessment-invalid", {code for code, _ in pairs})
                self.assertEqual({pair for pair in pairs if pair[0] != "assessment-invalid"},
                                 expected)
        text = report_text(region=stale, blockers=["AUD-08-001"])
        self.write_assessment()
        self.fixture.write(REPORT_PATH, text)
        inventory_file = self.fixture.root / INVENTORY_PATH
        original = inventory_file.read_bytes()
        inventory_file.unlink()
        try:
            result = self.run_verify()
        finally:
            inventory_file.write_bytes(original)
        self.assert_reports(result, [
            ("blocker-unlisted",
             f"{REPORT_PATH}:{line_number(text, '## Blockers for spec 09')}"),
            ("inventory-missing", f"{INVENTORY_PATH}:0")])


class VerifyReportTreeTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build

    def test_review_commit_in_a_root_without_git_is_review_commit_unknown(self) -> None:
        fixture, inventory = self.build("without-git", use_git=False)
        assessment = valid_assessment(inventory)
        rendered = run_render(fixture)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        line = f"Reviewed: Validator {OTHER_DATE} pass {UNKNOWN_COMMIT}"
        for review, expected in (
                ("Reviewed: pending", []),
                (line, [("review-commit-unknown", f"{REPORT_PATH}:{{line}}")])):
            with self.subTest(review=review):
                text = report_text(region=rendered.stdout, blockers=blocking_ids(assessment),
                                   review=review)
                fixture.write(REPORT_PATH, text)
                result = run_tool(["verify", "--root", str(fixture.root), "--report",
                                   str(fixture.root / REPORT_PATH)], fixture.env, fixture.base)
                self.assert_reports(result, [("worktree-dirty", inventory_at("worktree"))] + [
                    (code, location.format(line=line_number(text, review)))
                    for code, location in expected])


class ValidatorImpactTests(VerifyAssertions):
    def test_impact_row_counts_edges_by_validator_context_tests_frozen_hooks_and_active(
            self) -> None:
        with tempfile.TemporaryDirectory(prefix="audit-impact-") as name:
            fixture, inventory = build_verify_fixture(Path(name), extra=IMPACT_FILES)
            assessment = valid_assessment(inventory)
            (fixture.root / ASSESSMENT_PATH).write_text(canonical(assessment), encoding="utf-8")
            result = run_render(fixture)
        self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout)
        body = region_bodies(result.stdout)["Validator and test impact"]
        self.assertEqual(body, impact_body(inventory, assessment))
        self.assertIn(md_row([IMPACT_SOURCE, "rename", "1", "1", "2", "1", "1", "3", "4"]), body)
        self.assertEqual([line.split(" | ")[0][2:] for line in body[2:]],
                         sorted(row["source"] for row in assessment["map"]
                                if row["decision"] != "keep"))


class DiagnosticCompletenessTests(RenderCase):
    def assessment_case(self, change: Callable[[dict], object]
                        ) -> subprocess.CompletedProcess[str]:
        change(self.assessment)
        return self.verify()

    def map_case(self, source: str, decision: str, targets: list[dict]
                 ) -> subprocess.CompletedProcess[str]:
        row = self.assessment["map"][row_index(self.assessment["map"], "source", source)]
        row.update(decision=decision, targets=targets, spec09_default=default_of(targets),
                   spec09_optional=[])
        return self.verify()

    def unlink_case(self, relative: str) -> subprocess.CompletedProcess[str]:
        (self.fixture.root / relative).unlink()
        return self.run_verify()

    def inventory_case(self, text: str) -> subprocess.CompletedProcess[str]:
        (self.fixture.root / INVENTORY_PATH).write_text(text, encoding="utf-8")
        return self.verify()

    def renamed_report_case(self) -> subprocess.CompletedProcess[str]:
        directory, stem = self.report_file().parent, f"{OTHER_DATE}-rules-workflows-audit"
        for suffix in (".md", ".inventory.json", ".assessment.json"):
            shutil.copyfile(self.fixture.root / (REPORT_PATH[:-3] + suffix),
                            directory / (stem + suffix))
        return run_tool(["verify", "--root", str(self.fixture.root), "--report",
                         str(directory / f"{stem}.md")], self.fixture.env, self.fixture.base)

    def report_case(self, change: Callable[[str], str] = lambda region: region,
                    **fields: object) -> subprocess.CompletedProcess[str]:
        fields.setdefault("blockers", blocking_ids(self.assessment))
        return self.verify_report(report_text(region=change(self.region()), **fields))

    def code_cases(self) -> dict[str, Callable[[], subprocess.CompletedProcess[str]]]:
        a = self.assessment_case
        dirty = copy.deepcopy(self.inventory)
        dirty["worktree"] = {"state": "dirty", "paths": [DELTA]}

        def files(path: str) -> Callable[[dict], dict]:
            return lambda value: value["files"][row_index(value["files"], "path", path)]

        def finding(identifier: str) -> Callable[[dict], dict]:
            return lambda value: value["findings"][row_index(value["findings"], "id",
                                                             identifier)]

        def split_short(value: dict) -> None:
            row = value["map"][row_index(value["map"], "source", PHASE_DISCOVERY)]
            row["targets"][1]["sections"].pop()

        def group_twice(value: dict) -> None:
            value["duplicate_groups"].append(dict(value["duplicate_groups"][0], id="DG-002"))

        return {
            "inventory-missing": lambda: self.unlink_case(INVENTORY_PATH),
            "assessment-missing": lambda: self.unlink_case(ASSESSMENT_PATH),
            "report-missing": lambda: self.unlink_case(REPORT_PATH),
            "inventory-invalid": lambda: self.inventory_case("{\n"),
            "assessment-invalid": lambda: self.verify(text="{\n"),
            "report-name-date": self.renamed_report_case,
            "inventory-stale": lambda: (self.fixture.write(DELTA, "# Delta rule\n\nChanged.\n"),
                                        self.verify())[1],
            "worktree-dirty": lambda: self.inventory_case(canonical(dirty)),
            "digest-mismatch": lambda: a(lambda v: v.update(inventory_digest="f" * 64)),
            "row-missing": lambda: a(lambda v: v["files"].remove(files(DELTA)(v))),
            "row-extra": lambda: a(lambda v: v["files"].append(
                dict(files(DELTA)(v), path="rules/zz-extra.md"))),
            "row-duplicate": lambda: a(lambda v: v["files"].append(
                copy.deepcopy(files(DELTA)(v)))),
            "assessment-stale": lambda: a(lambda v: files(DELTA)(v).update(sha256="0" * 64)),
            "sections-incomplete": lambda: a(lambda v: files(ALPHA)(v)["sections"].pop()),
            "load-unclassified": lambda: a(lambda v: v["loads"].pop(0)),
            "candidate-undisposed": lambda: a(lambda v: v["candidates"].pop(
                row_index(v["candidates"], "id", "FO-001"))),
            "repetition-invalid": lambda: a(lambda v: files(BETA)(v).update(repetition=None)),
            "legacy-role-missing": lambda: a(lambda v: v["legacy"].clear()),
            "duplicate-ungrouped": lambda: a(lambda v: v["duplicate_groups"].clear()),
            "duplicate-multigrouped": lambda: a(group_twice),
            "group-invalid": lambda: a(lambda v: v["duplicate_groups"][0].update(
                disposition="contradiction", owner="owner", finding=None)),
            "defect-unrecorded": lambda: a(lambda v: finding("AUD-08-002")(v).update(edges=[])),
            "finding-invalid": lambda: a(lambda v: finding("AUD-08-003")(v).update(owner="09")),
            "finding-stale": lambda: a(lambda v: finding("AUD-08-003")(v).update(
                sha256="0" * 64)),
            "reference-unknown": lambda: a(lambda v: v["candidates"][row_index(
                v["candidates"], "id", "RL-001")].update(finding="AUD-08-099")),
            "map-invalid": lambda: self.map_case(ALPHA, "keep", [
                map_target("rules/contract-alpha-flow.md")]),
            "split-sections-incomplete": lambda: a(split_short),
            "map-collision": lambda: self.map_case(DELTA, "rename", [
                map_target("rules/contract-alpha-flow.md")]),
            "installed-name-collision": lambda: self.map_case(DELTA, "rename", [
                map_target("rules/contract-Alpha-flow.md")]),
            "stem-overlap": lambda: self.map_case(BETA, "rename", [
                map_target("workflows/contract-alpha-flow.md")]),
            "kind-prefix-invalid": lambda: self.map_case(DELTA, "rename", [
                map_target("rules/plain-delta.md")]),
            "deviation-unamended": lambda: a(lambda v: v["map"][row_index(
                v["map"], "source", DELTA)].update(spec09_default=None)),
            "spec09-unavailable": lambda: ((self.fixture.root / SPEC09_PATH).unlink(),
                                           self.verify())[1],
            "amendment-invalid": lambda: a(lambda v: v["amendments"][0].update(evidence=[])),
            "amendment-target-unknown": lambda: a(lambda v: v["amendments"][0].update(
                target="REQ-99")),
            "req21-invalid": lambda: a(lambda v: v["req21"]["statements"].pop()),
            "coverage-inconsistent": lambda: a(lambda v: finding("AUD-08-005")(v).update(
                type="other")),
            "report-layout": lambda: self.report_case(lambda region: REPORT_BEGIN + "\n"
                                                      + region),
            "review-commit-unknown": lambda: self.report_case(
                review=f"Reviewed: Validator {OTHER_DATE} pass {UNKNOWN_COMMIT}"),
            "report-generated-mismatch": lambda: self.report_case(lambda region: region.replace(
                f"- run_date: {AUDIT_DATE}", f"- run_date: {OTHER_DATE}")),
            "blocker-unlisted": lambda: self.report_case(blockers=["AUD-08-001"]),
            "blocker-extra": lambda: self.report_case(
                blockers=blocking_ids(self.assessment) + ["AUD-08-003"]),
            "evidence-unresolved": lambda: a(lambda v: files(DELTA)(v).update(
                evidence=["rules/zz-unknown.md:1"])),
            "economics-claim": lambda: a(lambda v: finding("AUD-08-002")(v).update(
                observation="It saves 3,000 tokens.")),
            "installed-invalid": lambda: a(lambda v: v["installed"].append({
                "path": ALPHA, "location": "~/.claude/skills/rule-alpha-flow/SKILL.md",
                "source_sha256": "0" * 64, "installed_sha256": "0" * 64})),
        }

    def test_every_diagnostic_code_has_a_producing_case_and_the_valid_fixture_is_silent(
            self) -> None:
        self.assert_silent(self.verify())
        snapshot = file_snapshot(self.fixture.root)
        cases = self.code_cases()
        self.assertEqual(sorted(cases), sorted(DIAGNOSTIC_CODES))
        produced: set[str] = set()
        for code in DIAGNOSTIC_CODES:
            with self.subTest(code=code):
                self.assessment = valid_assessment(self.inventory)
                try:
                    result = cases[code]()
                finally:
                    restore_snapshot(self.fixture.root, snapshot)
                self.assertNotIn("Traceback", result.stderr)
                codes = {found for found, _ in diagnostic_pairs(result)}
                self.assertIn(code, codes, result.stdout)
                produced.add(code)
        self.assertEqual(sorted(produced), sorted(DIAGNOSTIC_CODES))
        self.assessment = valid_assessment(self.inventory)
        self.assert_silent(self.verify())


# ---------------------------------------------------------------------------
# Git read isolation: attribute filters, lazy fetching and rename detection
# ---------------------------------------------------------------------------

def installed_git_version() -> tuple[int, int]:
    """Major and minor version of the git on PATH; (0, 0) when it cannot be read."""
    if REAL_GIT is None:
        return (0, 0)
    result = subprocess.run([REAL_GIT, "--version"], capture_output=True, text=True,
                            check=False)
    found = re.search(r"(\d+)\.(\d+)", result.stdout)
    return (int(found.group(1)), int(found.group(2))) if found else (0, 0)


def require_git(case: unittest.TestCase, minimum: tuple[int, int], reason: str) -> None:
    if REAL_GIT is None:
        case.skipTest("git is not installed")
    if installed_git_version() < minimum:
        case.skipTest(f"git {minimum[0]}.{minimum[1]} or later is needed {reason}")


def marker_program(path: Path, marker: Path, body: str) -> Path:
    """An executable shell program that creates the marker file and then runs body."""
    path.write_text(f"#!/bin/sh\ntouch '{marker}'\n{body}\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def make_stat_stale(path: Path) -> None:
    """Move the modification time so that git must hash the unchanged content again."""
    info = path.stat()
    os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns + 100 * 10**9))


class AttributeFilterIsolationTests(ToolCase):
    """A filter driver selected by attributes never runs, and the work tree still reads
    correctly: a file whose content is unchanged stays clean, a changed file is dirty."""

    def setUp(self) -> None:
        super().setUp()
        require_git(self, (2, 41), "to read attributes from a fixed tree")
        self.marker = self.base / "filter-ran"

    def clean_filter(self) -> str:
        return str(marker_program(self.base / "clean-filter.sh", self.marker, "cat"))

    def process_filter(self) -> str:
        return str(marker_program(self.base / "process-filter.sh", self.marker, "exit 1"))

    def extract_without_marker(self) -> dict:
        self.marker.unlink(missing_ok=True)
        inventory = self.extract()
        self.assertFalse(self.marker.exists(), "git ran a filter program")
        return inventory

    def test_clean_filter_of_the_repository_selected_by_committed_attributes_never_runs(
            self) -> None:
        self.fx.minimal()
        self.fx.write(".gitattributes", "*.md filter=alpha\n")
        self.fx.commit_all()
        self.fx.git("config", "filter.alpha.clean", self.clean_filter())
        make_stat_stale(self.fx.root / "rules/alpha-flow.md")
        self.fx.write("workflows/beta-step.md", "# Beta step changed\n")

        inventory = self.extract_without_marker()

        self.assertEqual(inventory["worktree"], {"state": "dirty",
                                                 "paths": ["workflows/beta-step.md"]})

    def test_process_filter_of_the_global_configuration_selected_by_attributes_never_runs(
            self) -> None:
        self.fx.minimal()
        self.fx.write(".gitattributes", "*.md filter=beta\n")
        self.fx.commit_all()
        (self.fx.home / ".gitconfig").write_text(
            f'[filter "beta"]\n\tprocess = {self.process_filter()}\n', encoding="utf-8")
        make_stat_stale(self.fx.root / "rules/alpha-flow.md")
        make_stat_stale(self.fx.root / "workflows/beta-step.md")

        inventory = self.extract_without_marker()

        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})

    def test_filter_selected_by_the_global_attributes_file_never_runs(self) -> None:
        self.fx.minimal()
        self.fx.commit_all()
        self.fx.git("config", "filter.gamma.clean", self.clean_filter())
        attributes = self.fx.home / ".config" / "git" / "attributes"
        attributes.parent.mkdir(parents=True, exist_ok=True)
        attributes.write_text("*.md filter=gamma\n", encoding="utf-8")
        make_stat_stale(self.fx.root / "rules/alpha-flow.md")

        inventory = self.extract_without_marker()

        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})

    def test_filter_selected_by_the_repository_information_attributes_never_runs(
            self) -> None:
        self.fx.minimal()
        self.fx.commit_all()
        self.fx.git("config", "filter.delta.clean", self.clean_filter())
        (self.fx.root / ".git" / "info").mkdir(exist_ok=True)
        (self.fx.root / ".git" / "info" / "attributes").write_text(
            "[attr]tracked-text filter=delta\n*.md tracked-text\n", encoding="utf-8")
        make_stat_stale(self.fx.root / "rules/alpha-flow.md")
        self.fx.write("workflows/beta-step.md", "# Beta step changed\n")

        inventory = self.extract_without_marker()

        self.assertEqual(inventory["worktree"], {"state": "dirty",
                                                 "paths": ["workflows/beta-step.md"]})


class AttributeFilterVerifyTests(VerifyAssertions):
    def setUp(self) -> None:
        require_git(self, (2, 41), "to read attributes from a fixed tree")
        self.temp = tempfile.TemporaryDirectory(prefix="audit-verify-filter-")
        self.base = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_strict_verify_runs_no_attribute_selected_filter_and_stays_silent(self) -> None:
        attributes = "rules/*.md filter=alpha\nworkflows/*.md filter=beta\n"
        fixture, inventory = build_verify_fixture(self.base,
                                                  extra={".gitattributes": attributes})
        (fixture.root / ASSESSMENT_PATH).write_text(canonical(valid_assessment(inventory)),
                                                    encoding="utf-8")
        refresh_report(fixture)
        marker = self.base / "filter-ran"
        clean = marker_program(self.base / "clean-filter.sh", marker, "cat")
        process = marker_program(self.base / "process-filter.sh", marker, "exit 1")
        fixture.git("config", "filter.alpha.clean", str(clean))
        (fixture.home / ".gitconfig").write_text(
            f'[filter "beta"]\n\tprocess = {process}\n', encoding="utf-8")
        make_stat_stale(fixture.root / ALPHA)
        make_stat_stale(fixture.root / BETA)
        marker.unlink(missing_ok=True)

        result = run_tool(["verify", "--root", str(fixture.root), "--report",
                           str(fixture.root / REPORT_PATH), "--strict"],
                          fixture.env, fixture.base)

        self.assertFalse(marker.exists(), "git ran a filter program")
        self.assert_silent(result)


OLD_FLOW = "rules/old-flow.md"
OLD_FLOW_TEXT = "# Old flow\n\nThe first step reads the state.\nThe second step writes it.\n"
NEW_FLOW = "rules/new-flow.md"


class PartialCloneIsolationTests(ToolCase):
    """In a partial clone whose promisor remote is a local repository, no git read fetches a
    missing object: the remote's upload program, which creates a marker, never starts."""

    def setUp(self) -> None:
        super().setUp()
        require_git(self, (2, 45), "to leave an object of a partial clone missing")
        self.marker = self.base / "fetch-ran"
        self.fx.minimal()
        self.fx.write(OLD_FLOW, OLD_FLOW_TEXT)
        self.fx.commit_all()
        self.fx.git("config", "uploadpack.allowFilter", "true")
        self.fx.git("config", "uploadpack.allowAnySHA1InWant", "true")
        self.clone = self.base / "clone"

    def clone_git(self, *args: str, env: dict[str, str] | None = None
                  ) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(REAL_GIT), "-C", str(self.clone), *args],
                              env=env if env is not None else self.fx.env, text=True,
                              capture_output=True, check=False)

    def make_clone(self, *options: str) -> None:
        result = subprocess.run([str(REAL_GIT), "clone", "-q", "--filter=blob:none", *options,
                                 f"file://{self.fx.root}", str(self.clone)],
                                cwd=self.base, env=self.fx.env, text=True,
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def watch_fetches(self) -> None:
        upload = marker_program(self.base / "upload-pack.sh", self.marker,
                                f"exec '{REAL_GIT}' upload-pack \"$@\"")
        self.assertEqual(self.clone_git("config", "remote.origin.uploadpack",
                                        str(upload)).returncode, 0)
        self.marker.unlink(missing_ok=True)

    def test_status_fetches_no_missing_object_and_still_lists_the_staged_change(
            self) -> None:
        self.make_clone("--no-checkout")
        for args in (("read-tree", "HEAD"), ("checkout", "--", "rules/alpha-flow.md",
                                             "workflows/beta-step.md")):
            result = self.clone_git(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
        old_blob = self.clone_git("rev-parse", f"HEAD:{OLD_FLOW}").stdout.strip()
        offline = {**self.fx.env, "GIT_NO_LAZY_FETCH": "1"}
        self.assertNotEqual(self.clone_git("cat-file", "-e", old_blob, env=offline).returncode,
                            0, "the clone must lack the blob of the renamed file")
        (self.clone / NEW_FLOW).write_text(OLD_FLOW_TEXT + "The third step reports.\n",
                                           encoding="utf-8")
        for args in (("add", NEW_FLOW), ("update-index", "--force-remove", OLD_FLOW)):
            result = self.clone_git(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.watch_fetches()

        out = self.base / "inventory.json"
        result = self.run_extract(out=out, root=self.clone)

        self.assertFalse(self.marker.exists(), "git fetched a missing object")
        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = parse_inventory(out.read_text(encoding="utf-8"))
        self.assertEqual(inventory["worktree"], {"state": "dirty",
                                                 "paths": [NEW_FLOW, OLD_FLOW]})

    def test_review_commit_lookup_fetches_nothing_and_reports_the_unknown_commit(
            self) -> None:
        self.make_clone()
        self.watch_fetches()
        review = f"Reviewed: Validator {OTHER_DATE} pass {UNKNOWN_COMMIT}"
        text = report_text(review=review)
        (self.clone / REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
        (self.clone / REPORT_PATH).write_text(text, encoding="utf-8")

        result = run_tool(["verify", "--root", str(self.clone), "--report",
                           str(self.clone / REPORT_PATH)], self.fx.env, self.base)

        self.assertFalse(self.marker.exists(), "git fetched a missing object")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(("review-commit-unknown", f"{REPORT_PATH}:{line_number(text, review)}"),
                      diagnostic_pairs(result))


GIT_CALL_SHAPES = {
    "rev-parse": ["--verify", "HEAD"],
    "ls-files": ["-z"],
    "status": ["--porcelain=v1", "-z", "--untracked-files=all"],
}


class GitReadSettingsTests(ToolCase):
    def setUp(self) -> None:
        super().setUp()
        if REAL_GIT is None:
            self.skipTest("git is not installed")

    def recorded_calls(self, log: Path) -> list[tuple[str, list[str], list[str]]]:
        """Each call as its lazy-fetch setting, its global options and its subcommand."""
        calls: list[tuple[str, list[str], list[str]]] = []
        lazy, arguments = "", []
        for line in log.read_text(encoding="utf-8").splitlines():
            if line.startswith("lazy="):
                lazy, arguments = line[len("lazy="):], []
            elif line.startswith("arg="):
                arguments.append(line[len("arg="):])
            elif line == "end":
                index = 0
                while index < len(arguments) and arguments[index] in {"--no-pager", "-c", "-C"}:
                    index += 1 if arguments[index] == "--no-pager" else 2
                calls.append((lazy, arguments[:index], arguments[index:]))
        return calls

    def test_git_reads_disable_lazy_fetching_and_renames_by_settings_older_git_ignores(
            self) -> None:
        self.fx.minimal()
        head = self.fx.commit_all()
        log = self.base / "git-calls.log"
        wrapper_bin = self.base / "wrapper-bin"
        wrapper_bin.mkdir()
        wrapper = wrapper_bin / "git"
        wrapper.write_text(
            "#!/bin/sh\n{\n  printf 'lazy=%s\\n' \"${GIT_NO_LAZY_FETCH-}\"\n"
            "  for argument in \"$@\"; do printf 'arg=%s\\n' \"$argument\"; done\n"
            f"  printf 'end\\n'\n}} >> '{log}'\nexec '{REAL_GIT}' \"$@\"\n", encoding="utf-8")
        wrapper.chmod(0o755)
        env = {**self.fx.env, "PATH": f"{wrapper_bin}{os.pathsep}{self.fx.env['PATH']}"}
        review = f"Reviewed: Validator {OTHER_DATE} pass {head}"
        self.fx.write(REPORT_PATH, report_text(review=review))

        inventory = self.extract(env=env)
        verified = run_tool(["verify", "--root", str(self.fx.root), "--report",
                             str(self.fx.root / REPORT_PATH)], env, self.base)

        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})
        self.assertNotIn("review-commit-unknown", {code for code, _ in
                                                   diagnostic_pairs(verified)})
        calls = self.recorded_calls(log)
        shapes = {**GIT_CALL_SHAPES, "cat-file": ["-e", f"{head}^{{commit}}"]}
        self.assertEqual(sorted({command[0] for _, _, command in calls}), sorted(shapes))
        for lazy, options, command in calls:
            with self.subTest(command=command[0]):
                self.assertEqual(lazy, "1", "lazy fetching is not disabled")
                self.assertEqual(command[1:], shapes[command[0]],
                                 "a subcommand option that older git may reject")
                if command[0] == "status":
                    self.assertIn("status.renames=false", options, "status detects renames")


class GitIsolationDocstringTests(unittest.TestCase):
    def test_module_docstring_states_the_git_isolation_and_the_git_versions_it_needs(
            self) -> None:
        docstring = ast.get_docstring(ast.parse(TOOL.read_text(encoding="utf-8")))
        self.assertIsNotNone(docstring)
        text = " ".join(str(docstring).split())
        self.assertNotIn("so no program named by the repository's configuration runs", text)
        for phrase in ("lazy fetching", "rename detection", "filter", "git 2.41",
                       "git 2.45"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


class GitRepositoryShapeTests(ToolCase):
    """Repository shapes that git reads without trouble keep the work tree readable, and the
    git reads still run no filter in them."""

    def setUp(self) -> None:
        super().setUp()
        require_git(self, (2, 41), "to read attributes from a fixed tree")
        self.marker = self.base / "filter-ran"

    def clean_filter(self) -> str:
        return str(marker_program(self.base / "clean-filter.sh", self.marker, "cat"))

    def information_attributes(self, data: bytes) -> None:
        info = self.fx.root / ".git" / "info"
        info.mkdir(exist_ok=True)
        (info / "attributes").write_bytes(data)

    def test_repository_with_sha256_object_names_reads_its_work_tree_and_runs_no_filter(
            self) -> None:
        self.fx.minimal()
        self.fx.write(".gitattributes", "*.md filter=alpha\n")
        self.fx.git("init", "-q", "-b", "main", "--object-format=sha256")
        self.fx.git("add", "-A")
        self.fx.git("commit", "-q", "-m", "chore: fixture")
        head = self.fx.git("rev-parse", "HEAD")
        self.fx.git("config", "filter.alpha.clean", self.clean_filter())
        make_stat_stale(self.fx.root / "rules/alpha-flow.md")
        self.marker.unlink(missing_ok=True)

        inventory = self.extract()

        self.assertFalse(self.marker.exists(), "git ran a filter program")
        self.assertEqual(len(head), 64)
        self.assertEqual(inventory["source_revision"], head)
        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})

    def test_git_file_with_an_embedded_nul_is_read_up_to_the_nul_as_git_reads_it(
            self) -> None:
        self.fx.minimal()
        head = self.fx.commit_all()
        os.rename(self.fx.root / ".git", self.base / "real-git")
        (self.fx.root / ".git").write_bytes(b"gitdir: ../real-git\x00ignored\n")
        make_stat_stale(self.fx.root / "rules/alpha-flow.md")

        result = self.run_extract()

        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = parse_inventory((self.base / "inventory.json").read_text(encoding="utf-8"))
        self.assertEqual(inventory["source_revision"], head)
        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})

    def test_first_in_first_out_entry_named_git_is_never_opened(self) -> None:
        self.fx.minimal()
        os.mkfifo(self.fx.root / ".git")
        out = self.base / "inventory.json"
        try:
            result = subprocess.run(
                [sys.executable, "-I", str(TOOL), "extract", "--root", str(self.fx.root),
                 "--out", str(out)], cwd=self.base, env=self.fx.env, text=True,
                capture_output=True, timeout=20)
        except subprocess.TimeoutExpired:
            self.fail("extract blocked on a first-in first-out entry named .git")

        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = parse_inventory(out.read_text(encoding="utf-8"))
        self.assertIsNone(inventory["source_revision"])
        self.assertEqual(inventory["worktree"], {"state": "unknown", "paths": []})

    def test_information_attribute_line_longer_than_git_reads_keeps_the_tree_readable(
            self) -> None:
        self.fx.minimal()
        self.fx.commit_all()
        self.information_attributes(b"x.md filter=" + b"q" * 200_000 + b"\n")
        make_stat_stale(self.fx.root / "rules/alpha-flow.md")

        inventory = self.extract()

        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})

    def test_many_information_attribute_filters_keep_the_tree_readable(self) -> None:
        self.fx.minimal()
        self.fx.commit_all()
        self.information_attributes("".join(f"x{number}.md filter=f{number}\n"
                                            for number in range(40_000)).encode("ascii"))
        make_stat_stale(self.fx.root / "rules/alpha-flow.md")

        inventory = self.extract()

        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})

    def test_filter_name_with_a_no_break_space_is_blanked_as_git_reads_the_name(
            self) -> None:
        self.fx.minimal()
        self.fx.commit_all()
        name = "a b"
        self.information_attributes(f"*.md filter={name}\n".encode("utf-8"))
        (self.fx.home / ".gitconfig").write_text(
            f'[filter "{name}"]\n\tclean = {self.clean_filter()}\n', encoding="utf-8")
        make_stat_stale(self.fx.root / "rules/alpha-flow.md")
        self.marker.unlink(missing_ok=True)

        inventory = self.extract()

        self.assertFalse(self.marker.exists(), "git ran a filter program")
        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})


class GitIsolationLimitsDocstringTests(unittest.TestCase):
    def test_module_docstring_names_the_cases_the_git_isolation_leaves_open(self) -> None:
        docstring = ast.get_docstring(ast.parse(TOOL.read_text(encoding="utf-8")))
        text = " ".join(str(docstring).split())
        for phrase in ("git 2.31", "submodule", "info/attributes", "top level", "SHA-256"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


# ---------------------------------------------------------------------------
# The blockers section in both directions, evidence resolution, audit-scope notes
# ---------------------------------------------------------------------------

BLOCKERS_HEADING = "## Blockers for spec 09"
BLOCKERS_BODY_RE = re.compile(r"(## Blockers for spec 09\n\n)(.*?)(\n## Independent review\n)",
                              re.DOTALL)
UNDECODED_READER = "docs/RAW.txt"
UNDECODED_READER_BYTES = b"\xff\xfe first\nsecond\nthird\n"
RUNBOOK = SOURCE_ROOT / ".ai" / "context" / "runbook.md"
LATER_TREE_CODES = ("inventory-stale", "review-commit-unknown", "spec09-unavailable",
                    "req21-invalid", "amendment-invalid", "amendment-target-unknown")
AUDIT_SPECIFIC_CONSTANTS = ("ALWAYS_SECTIONED", "DISCOVERY_RULE")


def with_blockers_body(text: str, body: str) -> str:
    """The report text with the body of its blockers section replaced."""
    replaced, count = BLOCKERS_BODY_RE.subn(
        lambda found: found.group(1) + body + found.group(3), text, count=1)
    if count != 1:
        raise AssertionError("the report has no blockers section to replace")
    return replaced


class VerifyBlockersSectionTests(RenderCase):
    def unblock_every_finding(self) -> None:
        """Make the valid assessment one in which no finding blocks: the amendment cites a
        line instead of a finding, and the unreadable file is read and its finding becomes
        an observation of type other."""
        self.assessment["amendments"][0]["evidence"] = [f"{BETA}:9"]
        self.finding("AUD-08-001")["blocks_09"] = False
        self.finding("AUD-08-005").update(type="other", blocks_09=False)
        self.row("coverage", BLOB)["status"] = "read"

    def test_listed_id_of_a_finding_that_does_not_block_or_does_not_exist_is_blocker_extra(
            self) -> None:
        blocking = ["AUD-08-001", "AUD-08-005"]
        cases: dict[str, tuple[list[str], list[str]]] = {
            "finding that does not block": (blocking + ["AUD-08-003"], ["- AUD-08-003"]),
            "id that names no finding": (blocking + ["AUD-08-099"], ["- AUD-08-099"]),
            "amendment id beside a finding that does not block": (
                blocking + ["AUD-08-004 (AMD-08-01)"], ["- AUD-08-004 (AMD-08-01)"]),
            "id twice on one line and again on another line": (
                blocking + ["AUD-08-003 and again AUD-08-003", "AUD-08-003 once more"],
                ["- AUD-08-003 and again AUD-08-003", "- AUD-08-003 once more"]),
            "amendment ids beside the blocking findings only": (
                ["AUD-08-001 (AMD-08-01)", "AUD-08-005 (AMD-08-99)"], []),
            "id inside a longer token": (blocking + ["AUD-08-0030"], []),
        }
        for name, (blockers, lines) in cases.items():
            with self.subTest(case=name):
                self.assessment = valid_assessment(self.inventory)
                text = self.valid_report(blockers=blockers)
                expected = [("blocker-extra", f"{REPORT_PATH}:{line_number(text, line)}")
                            for line in lines]
                result = self.verify_report(text)
                if expected:
                    self.assert_reports(result, expected)
                else:
                    self.assert_silent(result)

    def test_blockers_section_breaking_the_none_rule_is_report_layout(self) -> None:
        nothing_blocks = {
            "None. alone": ("None.\n", None),
            "empty section": ("", BLOCKERS_HEADING),
            "prose instead of None.": ("No finding blocks the migration.\n", BLOCKERS_HEADING),
            "None. followed by prose": ("None.\n\nSee the summary.\n", BLOCKERS_HEADING),
        }
        for name, (body, line) in nothing_blocks.items():
            with self.subTest(case=name, blocking="none"):
                self.assessment = valid_assessment(self.inventory)
                self.unblock_every_finding()
                text = with_blockers_body(self.valid_report(), body)
                result = self.verify_report(text)
                if line is None:
                    self.assert_silent(result)
                else:
                    self.assert_reports(result, [
                        ("report-layout", f"{REPORT_PATH}:{line_number(text, line)}")])
        with self.subTest(case="None. beside the blocking findings"):
            self.assessment = valid_assessment(self.inventory)
            text = with_blockers_body(self.valid_report(),
                                      "- AUD-08-001\n- AUD-08-005\n\nNone.\n")
            self.assert_reports(self.verify_report(text), [
                ("report-layout", f"{REPORT_PATH}:{line_number(text, 'None.')}")])
        with self.subTest(case="None. alone while findings block"):
            self.assessment = valid_assessment(self.inventory)
            text = self.valid_report(blockers=[])
            heading = f"{REPORT_PATH}:{line_number(text, BLOCKERS_HEADING)}"
            self.assert_reports(self.verify_report(text), [
                ("blocker-unlisted", heading), ("blocker-unlisted", heading),
                ("report-layout", f"{REPORT_PATH}:{line_number(text, 'None.')}")])


class VerifyEvidenceResolutionTests(SharedVerifyCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="audit-evidence-")
        try:
            cls.fixture, cls.inventory = build_verify_fixture(
                Path(cls.temp.name), extra={UNDECODED_READER: UNDECODED_READER_BYTES})
        except BaseException:
            cls.temp.cleanup()
            raise

    def lines_of(self, path: str) -> int:
        return int(inventory_entry(self.inventory, path)["lines"])

    def evidence_cases(self, cases: dict[str, tuple[str, str, list[str], int]]) -> None:
        """Each case replaces the evidence of one files row (by path), finding or amendment
        (by id) and expects that many evidence-unresolved diagnostics at that row."""
        for name, (key, identifier, evidence, count) in cases.items():
            with self.subTest(case=name):
                self.assessment = valid_assessment(self.inventory)
                field = "path" if key == "files" else "id"
                index = row_index(self.assessment[key], field, identifier)
                self.assessment[key][index]["evidence"] = evidence
                location = assessment_at(f"files[{index}]" if key == "files" else identifier)
                result = self.verify()
                if count:
                    self.assert_reports(result, [("evidence-unresolved", location)] * count)
                else:
                    self.assert_silent(result)

    def test_line_evidence_that_names_no_inventory_path_or_a_line_outside_it_is_unresolved(
            self) -> None:
        beta, guide = self.lines_of(BETA), self.lines_of(GUIDE)
        self.evidence_cases({
            "unknown path in a files row": ("files", DELTA, ["rules/zz-unknown.md:1"], 1),
            "line past the count of an audited file": (
                "findings", "AUD-08-003", [f"{GAMMA}:5", f"{BETA}:{beta + 1}"], 1),
            "line zero": ("findings", "AUD-08-004", [f"{GAMMA}:0"], 1),
            "line past the count of a reader": (
                "findings", "AUD-08-002", [f"{GUIDE}:{guide + 1}"], 1),
            "line on an entry without a line count": ("files", LINK, [f"{LINK}:1"], 1),
            "unknown path in an amendment": (
                "amendments", "AMD-08-01", ["AUD-08-001", "docs/zz-gone.md:2"], 1),
            "two unresolved items in one finding": (
                "findings", "AUD-08-004", ["rules/zz-unknown.md:1", f"{GAMMA}:99"], 2),
            "last line of an audited file": ("files", BETA, [f"{BETA}:{beta}"], 0),
            "line of a reader that is not decoded": (
                "findings", "AUD-08-002",
                [f"{GUIDE}:1", f"{UNDECODED_READER}:{self.lines_of(UNDECODED_READER)}"], 0),
            "reader line in an amendment": (
                "amendments", "AMD-08-01", ["AUD-08-001", f"{SPEC09_PATH}:1"], 0),
        })

    def test_range_evidence_resolves_only_within_the_line_count_of_its_entry(self) -> None:
        gamma = self.lines_of(GAMMA)
        self.evidence_cases({
            "reversed range": ("findings", "AUD-08-004", [f"{GAMMA}:6-5"], 1),
            "range past the count": ("findings", "AUD-08-004", [f"{GAMMA}:5-{gamma + 1}"], 1),
            "range starting at zero": ("findings", "AUD-08-004", [f"{GAMMA}:0-2"], 1),
            "range on an unknown path": ("findings", "AUD-08-004", ["rules/zz-unknown.md:1-2"],
                                         1),
            "range on an entry without a line count": (
                "findings", "AUD-08-004", [f"{GAMMA}:6", f"{LINK}:1-1"], 1),
            "range ending at the count": ("findings", "AUD-08-004", [f"{GAMMA}:1-{gamma}"], 0),
            "range of one line": ("findings", "AUD-08-004", [f"{GAMMA}:6-6"], 0),
        })

    def test_bare_evidence_path_that_names_no_inventory_path_is_unresolved(self) -> None:
        self.evidence_cases({
            "unknown bare path": ("findings", "AUD-08-005", [BLOB, "harness/x/zz-gone.bin"], 1),
            "bare audited and reader paths": (
                "findings", "AUD-08-005", [BLOB, GUIDE, UNDECODED_READER, LINK], 0),
        })


class AuditScopeNoteTests(unittest.TestCase):
    def test_runbook_limits_the_silent_verify_to_the_delivery_commit_and_names_later_codes(
            self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        bullets = [" ".join(item.split()) for item in re.split(r"\n(?=- )", text)
                   if "audit-instructions.py verify" in item]
        self.assertEqual(len(bullets), 1, "the runbook has no single note on the audit verify")
        note = bullets[0]
        self.assertNotIn("must print nothing for a delivered audit", note)
        self.assertIn("delivery commit", note)
        for code in LATER_TREE_CODES:
            with self.subTest(code=code):
                self.assertIn(code, note)

    def test_constants_of_this_audit_rule_set_are_marked_as_specific_to_this_audit(
            self) -> None:
        lines = TOOL.read_text(encoding="utf-8").split("\n")
        for name in AUDIT_SPECIFIC_CONSTANTS:
            with self.subTest(constant=name):
                starts = [index for index, line in enumerate(lines)
                          if line.startswith(f"{name} = ")]
                self.assertEqual(len(starts), 1, f"{name} is not assigned once")
                comments: list[str] = []
                index = starts[0] - 1
                while index >= 0 and lines[index].startswith("#"):
                    comments.insert(0, lines[index].lstrip("# "))
                    index -= 1
                self.assertIn("specific to this audit", " ".join(comments).lower())


OVERLONG_DIGITS = 4301


class VerifyEvidenceResolutionLimitTests(SharedVerifyCase):
    def evidence_case(self, key: str, identifier: str, evidence: list[str]
                      ) -> tuple[subprocess.CompletedProcess[str], str]:
        """Verify the valid assessment with the evidence of one files row (by path),
        finding or amendment (by id) replaced; return the result and that row's location."""
        self.assessment = valid_assessment(self.inventory)
        field = "path" if key == "files" else "id"
        index = row_index(self.assessment[key], field, identifier)
        self.assessment[key][index]["evidence"] = evidence
        location = assessment_at(f"files[{index}]" if key == "files" else identifier)
        return self.verify(), location

    def test_line_number_too_long_to_convert_is_a_line_outside_its_entry(self) -> None:
        long_number = "9" * OVERLONG_DIGITS
        cases = {
            "files row line": ("files", DELTA, [f"{DELTA}:{long_number}"]),
            "finding range end": ("findings", "AUD-08-003",
                                  [f"{GAMMA}:5", f"{GAMMA}:1-{long_number}"]),
            "finding range start": ("findings", "AUD-08-004", [f"{GAMMA}:{long_number}-6"]),
            "amendment line": ("amendments", "AMD-08-01",
                               ["AUD-08-001", f"{BETA}:{'1' * 5000}"]),
            "ten-digit line": ("findings", "AUD-08-004", [f"{GAMMA}:1234567890"]),
        }
        for name, (key, identifier, evidence) in cases.items():
            with self.subTest(case=name):
                result, location = self.evidence_case(key, identifier, evidence)
                self.assertNotIn("Traceback", result.stderr)
                self.assert_reports(result, [("evidence-unresolved", location)])

    def test_finding_id_in_the_evidence_of_a_finding_is_a_bare_path_that_is_unresolved(
            self) -> None:
        cases: dict[str, tuple[str, str, list[str], list[str]]] = {
            "unknown finding id beside a line and an amendment id": (
                "findings", "AUD-08-002", [f"{GUIDE}:1", "AMD-08-01", "AUD-08-999"],
                ["evidence-unresolved"]),
            "existing finding id": ("findings", "AUD-08-002", [f"{GUIDE}:1", "AUD-08-001"],
                                    ["evidence-unresolved"]),
            "unknown amendment id in a finding": (
                "findings", "AUD-08-002", [f"{GUIDE}:1", "AMD-08-99"], ["reference-unknown"]),
            "unknown finding id in an amendment": (
                "amendments", "AMD-08-01", ["AUD-08-001", "AUD-08-099"], ["reference-unknown"]),
        }
        for name, (key, identifier, evidence, codes) in cases.items():
            with self.subTest(case=name):
                result, location = self.evidence_case(key, identifier, evidence)
                self.assert_reports(result, [(code, location) for code in codes])


ADAPTER_FILE = "templates/codex-global-AGENTS.md"
DEEP_READER_LEVELS = 1200


class AdapterFileLookupTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build
    verify = VerifyTreeTests.verify

    def extract_into(self, fixture: FixtureRoot, out: Path
                     ) -> subprocess.CompletedProcess[str]:
        return run_tool(["extract", "--root", str(fixture.root), "--out", str(out)],
                        fixture.env, fixture.base)

    def test_adapter_file_below_an_unsearchable_templates_directory_refuses_the_root(
            self) -> None:
        if os.geteuid() == 0:
            self.skipTest("permission bits do not restrict the superuser")
        fixture, inventory = self.build("unsearchable")
        with self.subTest(case="absent templates directory"):
            self.assertNotIn(ADAPTER_FILE, [entry["path"] for entry in inventory["files"]])
            self.assert_silent(self.verify(fixture))
        fixture.write(ADAPTER_FILE, "# Essentials\n")
        refresh_report(fixture)
        report = str(fixture.root / REPORT_PATH)
        templates = fixture.root / "templates"
        for mode in (0o600, 0o000):
            for command in ("extract", "verify"):
                with self.subTest(mode=oct(mode), command=command):
                    out = fixture.base / f"inventory-{mode:o}.json"
                    os.chmod(templates, mode)
                    try:
                        result = (self.extract_into(fixture, out) if command == "extract"
                                  else self.verify(fixture, report=report))
                    finally:
                        os.chmod(templates, 0o755)
                    self.assertEqual(result.returncode, 2, f"stdout={result.stdout!r} "
                                                           f"stderr={result.stderr!r}")
                    self.assertEqual(result.stdout, "")
                    lines = result.stderr.strip().splitlines()
                    self.assertEqual(len(lines), 1, lines)
                    self.assertTrue(lines[0].startswith("ERROR: root-unreadable: "), lines[0])
                    self.assertNotIn(str(fixture.base), result.stderr)
                    self.assertFalse(out.exists())
        (fixture.root / ADAPTER_FILE).unlink()
        (fixture.root / ADAPTER_FILE).symlink_to("elsewhere.md")
        out = fixture.base / "inventory-link.json"
        result = self.extract_into(fixture, out)
        with self.subTest(case="link named like the adapter file"):
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = [entry for entry in parse_inventory(out.read_text(encoding="utf-8"))["files"]
                    if entry["path"] == ADAPTER_FILE]
            self.assertEqual([(row["set"], row["entry"]) for row in rows],
                             [("adapter", "symlink")])


class ReaderWalkTests(ToolCase):
    def test_unreadable_directory_that_cannot_hold_a_reader_does_not_refuse_the_root(
            self) -> None:
        if os.geteuid() == 0:
            self.skipTest("permission bits do not restrict the superuser")
        for index, directory in enumerate(("private", ".ai/context/sub")):
            with self.subTest(directory=directory):
                (self.base / f"case-{index}").mkdir()
                fixture = FixtureRoot(self.base / f"case-{index}")
                fixture.minimal()
                fixture.write("docs/GUIDE.md", "# Guide\n")
                fixture.write(f"{directory}/notes.md", "# Notes\n")
                out = fixture.base / "inventory.json"
                os.chmod(fixture.root / directory, 0)
                try:
                    result = self.run_extract(out=out, root=fixture.root, env=fixture.env)
                finally:
                    os.chmod(fixture.root / directory, 0o755)

                self.assertEqual(result.returncode, 0, result.stderr)
                inventory = parse_inventory(out.read_text(encoding="utf-8"))
                self.assertEqual({entry["path"]: entry["class"]
                                  for entry in inventory["readers"]},
                                 {"docs/GUIDE.md": "active"})

    def test_reader_below_a_deep_directory_chain_is_extracted_without_a_traceback(
            self) -> None:
        self.fx.minimal()
        (self.fx.root / "docs").mkdir()
        directory = deep_directory(self.fx.root, "docs", DEEP_READER_LEVELS)
        out = self.base / "inventory.json"
        try:
            self.fx.write(f"{directory}/x.md", "# X\n")
            result = self.run_extract(out=out)
        finally:
            remove_deep_directory(self.fx.root, directory)

        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        inventory = parse_inventory(out.read_text(encoding="utf-8"))
        self.assertEqual({entry["path"]: entry["class"] for entry in inventory["readers"]},
                         {f"{directory}/x.md": "history"})


class AdapterTokenBoundaryTests(EdgeCase):
    SOURCE = "docs/GUIDE.md"

    def test_adapter_path_token_ends_where_the_other_path_tokens_end(self) -> None:
        lines = self.write_lines(self.SOURCE, [
            "Backup templates/codex-global-AGENTS.md.bak here.",
            "Older templates/codex-global-AGENTS.md-old here.",
            "Adapter templates/codex-global-AGENTS.md. Also templates/codex-global-AGENTS.md, too.",
            "Rule rules/r-one.md.bak here.",
        ])

        inventory = self.extract()

        s, text = self.SOURCE, "text"
        self.assert_edges(inventory, s, [
            edge(s, lines, lines[2], ADAPTER_FILE, "path", "resolved", [ADAPTER_FILE],
                 context=text),
            edge(s, lines, lines[2], ADAPTER_FILE, "path", "resolved", [ADAPTER_FILE],
                 context=text, nth=1),
            edge(s, lines, lines[3], "rules/r-one.md.bak", "path", "missing-path",
                 context=text),
        ])


class BareHomeDirectoryTests(CandidateCase):
    def test_bare_home_directory_before_a_path_end_becomes_a_tilde(self) -> None:
        source = "rules/r-bare.md"
        cases = [
            ("Keep the full output in /home/someone and /Users/x, /home/abc; /Users/def: "
             "(/home/ghi) /Users/jkl.",
             "Keep the full output in ~ and ~, ~; ~: (~) ~."),
            ("Keep the full output under `/home/someone` now.",
             "Keep the full output under `~` now."),
            ("Keep the full output at /home/someone", "Keep the full output at ~"),
            ("Keep the full output in /home/ alone, /homestead/x and /home/someone/z.",
             "Keep the full output in /home/ alone, /homestead/x and ~/z."),
        ]
        self.write_lines(source, [line for line, _ in cases])
        out = self.base / "inventory.json"

        inventory = self.extract(out=out)

        self.assertEqual(inventory["full_output"],
                         [line_candidate("FO", number, source, number, kept)
                          for number, (_, kept) in enumerate(cases, start=1)])
        text = out.read_text(encoding="utf-8")
        self.assertNotIn("/home/someone", text)
        self.assertNotIn("/Users/x", text)


class SeparatorRowWhitespaceTests(CandidateCase):
    def test_separator_row_with_trailing_whitespace_is_not_a_unit(self) -> None:
        content_row = "| Every audited file | keeps one row | here |  "
        lines = ["# S", "", "| --- | --- | --- | --- |   ", "| :--- | ---: | :---: | --- |\t",
                 "|---|---|---|---|---|---|---|---|\t", content_row]
        for path in ("rules/s-one.md", "rules/s-two.md"):
            self.write_lines(path, lines)

        inventory = self.extract()

        self.assertEqual(inventory["duplicate_clusters"], [
            cluster(1, " ".join(content_row.split()),
                    [("rules/s-one.md", 6, 6), ("rules/s-two.md", 6, 6)]),
        ])


class StopMarkerTests(CandidateCase):
    NOT_CALLS = [
        "**Stop**: run `/w-child` first",
        "**STOP**, then run `/w-child`.",
    ]
    CALLS = [
        "The `**stop**` marker ends a step; run `/w-child` now.",
        "Write `**Stop**` as shown, then run `/w-child`.",
        "Run `/w-child`; **Stop** after it.",
    ]

    def test_stop_marker_in_any_case_outside_code_spans_ends_calls(self) -> None:
        control = repeat_load(1, "w-ctl", "w-child")
        cases = [(line, False) for line in self.NOT_CALLS]
        cases += [(line, True) for line in self.CALLS]
        for index, (line, is_call) in enumerate(cases):
            with self.subTest(line=line):
                fixture = self.fresh_fixture(f"case-{index}")
                fixture.write(R_ONE, "# R one\n")
                self.write_workflow("w-root", [LOAD_R_ONE, line], fixture)
                self.write_workflow("w-child", [LOAD_R_ONE], fixture)
                self.write_workflow("w-ctl", [LOAD_R_ONE, "Run `/w-child`."], fixture)

                inventory = self.extract_fixture(fixture)

                expected = [control]
                if is_call:
                    expected.append(repeat_load(2, "w-root", "w-child"))
                self.assertEqual(inventory["repeat_loads"], expected)


class BareHomeNameBoundaryTests(CandidateCase):
    def test_bare_home_name_ends_at_the_first_character_outside_a_user_name(self) -> None:
        source = "rules/r-names.md"
        cases = [
            ("Keep the full output in |/home/someone| here.",
             "Keep the full output in |~| here."),
            ("Keep the full output in **/home/x** here.", "Keep the full output in **~** here."),
            ("Keep the full output at /home/x> here.", "Keep the full output at ~> here."),
            ("Keep the full output in /home/someone's dir.",
             "Keep the full output in ~'s dir."),
            ("Keep the full output in /home/some.one-x_y, then /Users/jkl.",
             "Keep the full output in ~, then ~."),
            ("Keep the full output in /home/ alone, /homestead/x and /home/someone/z.",
             "Keep the full output in /home/ alone, /homestead/x and ~/z."),
        ]
        self.write_lines(source, [line for line, _ in cases])
        out = self.base / "inventory.json"

        inventory = self.extract(out=out)

        self.assertEqual(inventory["full_output"],
                         [line_candidate("FO", number, source, number, kept)
                          for number, (_, kept) in enumerate(cases, start=1)])
        text = out.read_text(encoding="utf-8")
        self.assertNotIn("/home/someone", text)
        self.assertNotIn("/home/x", text)


class AdapterBehindLinkTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build
    verify = VerifyTreeTests.verify

    def extract_rows(self, fixture: FixtureRoot, name: str) -> tuple[list[dict], str]:
        """Extract the fixture root; return its files rows and the inventory text."""
        out = fixture.base / f"inventory-{name}.json"
        result = run_tool(["extract", "--root", str(fixture.root), "--out", str(out)],
                          fixture.env, fixture.base)
        self.assertEqual(result.returncode, 0, f"stderr={result.stderr!r}")
        text = out.read_text(encoding="utf-8")
        return parse_inventory(text)["files"], text

    def test_templates_directory_that_is_a_link_is_never_followed(self) -> None:
        fixture, _ = self.build("outside")
        outside = fixture.base / "outside"
        outside.mkdir()
        (outside / "codex-global-AGENTS.md").write_text(
            "# Outside\n\nSee `rules/zz-outside.md`.\n", encoding="utf-8")
        (fixture.root / "templates").symlink_to(outside)

        rows, text = self.extract_rows(fixture, "outside")

        self.assertNotIn(ADAPTER_FILE, [row["path"] for row in rows])
        self.assertNotIn("templates", [row["path"] for row in rows])
        self.assertNotIn("zz-outside", text)
        self.assertNotIn(str(outside), text)
        self.assert_silent(self.verify(fixture))

    def test_templates_link_that_loops_is_an_absent_adapter(self) -> None:
        fixture, _ = self.build("loop")
        (fixture.root / "templates").symlink_to("templates")

        rows, _ = self.extract_rows(fixture, "loop")

        self.assertNotIn(ADAPTER_FILE, [row["path"] for row in rows])
        self.assert_silent(self.verify(fixture))


class SeparatorRowInnerWhitespaceTests(CandidateCase):
    def test_separator_row_with_tabs_inside_is_not_a_unit(self) -> None:
        content_row = "|\tEvery audited file\t|\tkeeps one row\t|\there\t|"
        lines = ["# S", "", "|\t---\t|\t---\t|\t---\t|\t---\t|",
                 "| :---\t| ---: |\t:---: | --- |", content_row]
        for path in ("rules/t-one.md", "rules/t-two.md"):
            self.write_lines(path, lines)

        inventory = self.extract()

        self.assertEqual(inventory["duplicate_clusters"], [
            cluster(1, " ".join(content_row.split()),
                    [("rules/t-one.md", 5, 5), ("rules/t-two.md", 5, 5)]),
        ])


class StopMarkerColonTests(CandidateCase):
    NOT_CALLS = [
        "**Stop:** run `/w-child` first",
        "**STOP:** then run `/w-child`.",
        "**stop:** run `/w-child` next.",
    ]
    CALLS = [
        "Write `**Stop:**` as shown, then run `/w-child`.",
        "Run `/w-child`; **Stop:** after it.",
    ]

    def test_stop_marker_with_the_colon_inside_the_emphasis_ends_calls(self) -> None:
        control = repeat_load(1, "w-ctl", "w-child")
        cases = [(line, False) for line in self.NOT_CALLS]
        cases += [(line, True) for line in self.CALLS]
        for index, (line, is_call) in enumerate(cases):
            with self.subTest(line=line):
                fixture = self.fresh_fixture(f"case-{index}")
                fixture.write(R_ONE, "# R one\n")
                self.write_workflow("w-root", [LOAD_R_ONE, line], fixture)
                self.write_workflow("w-child", [LOAD_R_ONE], fixture)
                self.write_workflow("w-ctl", [LOAD_R_ONE, "Run `/w-child`."], fixture)

                inventory = self.extract_fixture(fixture)

                expected = [control]
                if is_call:
                    expected.append(repeat_load(2, "w-root", "w-child"))
                self.assertEqual(inventory["repeat_loads"], expected)


# ---------------------------------------------------------------------------
# Git metadata read as git reads it, roots below the top level, home names before a slash
# ---------------------------------------------------------------------------

class HomePrefixNameTests(CandidateCase):
    def test_home_prefix_name_holds_only_name_characters_and_keeps_every_other_character(
            self) -> None:
        source = "rules/r-prefix.md"
        cases = [
            ("Keep the full output in [/home/x](/home/x/y) here.",
             "Keep the full output in [~](~/y) here."),
            ("Keep the full output in /home/x|/y here.", "Keep the full output in ~|/y here."),
            ("Keep the full output in /home/x)/y here.", "Keep the full output in ~)/y here."),
            ("Keep the full output in /home/éx ok.", "Keep the full output in ~ ok."),
            ("Keep the full output in /home/x́y ok.", "Keep the full output in ~ ok."),
            ("Keep the full output in /home/éx/y ok.", "Keep the full output in ~/y ok."),
            ("Keep the full output in /home/x./y and /home/some.one-x_y/z.",
             "Keep the full output in ~/y and ~/z."),
        ]
        self.write_lines(source, [line for line, _ in cases])
        out = self.base / "inventory.json"

        inventory = self.extract(out=out)

        self.assertEqual(inventory["full_output"],
                         [line_candidate("FO", number, source, number, kept)
                          for number, (_, kept) in enumerate(cases, start=1)])
        text = out.read_text(encoding="utf-8")
        self.assertNotIn("home/x", text)
        self.assertNotIn("\\u0301", text)


class GitMetadataReadTests(unittest.TestCase):
    """The functions that read git's metadata files, called after loading the tool's
    source as a module."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="audit-git-metadata-")
        self.base = Path(self.temp.name)
        self.tool = load_tool_module()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_link_to_a_device_node_is_never_opened(self) -> None:
        device = Path("/dev/null")
        if not stat.S_ISCHR(os.stat(device).st_mode):
            self.skipTest("/dev/null is not a character device here")
        linked_device = self.base / "linked-device"
        linked_device.symlink_to(device)
        regular = self.base / "regular"
        regular.write_bytes(b"gitdir: elsewhere\n")
        linked_regular = self.base / "linked-regular"
        linked_regular.symlink_to(regular)
        opened: list[str] = []
        real_open = os.open

        def recording_open(path: str | os.PathLike[str], flags: int, mode: int = 0o777, *,
                           dir_fd: int | None = None) -> int:
            opened.append(os.fspath(path))
            return real_open(path, flags, mode, dir_fd=dir_fd)

        with mock.patch.object(os, "open", recording_open):
            from_device = self.tool.read_git_metadata(linked_device, 1024)
            from_regular = self.tool.read_git_metadata(linked_regular, 1024)

        self.assertIsNone(from_device)
        self.assertNotIn(str(linked_device), opened)
        self.assertNotIn(str(device), opened)
        self.assertEqual(from_regular, b"gitdir: elsewhere\n")

    def test_information_attribute_line_is_read_up_to_its_first_nul(self) -> None:
        common = self.base / "common"
        (common / "info").mkdir(parents=True)
        cases = [
            (b"\x00*.md filter=kappa\n", []),
            (b"*.md\x00 filter=kappa\n", []),
            (b"*.md filter=kappa\x00" + b"q" * 3000 + b"\n", ["kappa"]),
            (b"*.md filter=ka\x00ppa\n", ["ka"]),
            (b"*.md filter=kappa\r\n", ["kappa"]),
        ]
        for data, names in cases:
            with self.subTest(line=data[:40]):
                (common / "info" / "attributes").write_bytes(data)

                found = self.tool.information_attribute_filters(common)

                self.assertEqual(found, names)


def git_config_file(config: Path, env: dict[str, str], key: str, value: str) -> None:
    """Set one key in the configuration file of a repository directory."""
    result = subprocess.run([str(REAL_GIT), "config", "--file", str(config), key, value],
                            env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise AssertionError(f"git config {key} failed: {result.stderr}")


class GitMetadataLineEndTests(ToolCase):
    """A `.git` file, its `commondir` and the info/attributes lines are read as git reads
    them, so the filters of the repository they name stay blanked."""

    def setUp(self) -> None:
        super().setUp()
        require_git(self, (2, 41), "to read attributes from a fixed tree")
        self.marker = self.base / "filter-ran"

    def watched_filter(self, common: Path, env: dict[str, str]) -> None:
        """A clean filter of the common directory that its info/attributes selects."""
        program = marker_program(self.base / "clean-filter.sh", self.marker, "cat")
        git_config_file(common / "config", env, "filter.kappa.clean", str(program))
        (common / "info").mkdir(exist_ok=True)
        (common / "info" / "attributes").write_text("*.md filter=kappa\n", encoding="utf-8")

    def extract_root(self, fixture: FixtureRoot) -> dict:
        make_stat_stale(fixture.root / "rules/alpha-flow.md")
        self.marker.unlink(missing_ok=True)
        out = fixture.base / "inventory.json"
        result = self.run_extract(out=out, root=fixture.root, env=fixture.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.marker.exists(), "git ran a filter program")
        return parse_inventory(out.read_text(encoding="utf-8"))

    def test_information_attribute_line_with_a_nul_before_the_line_limit_runs_no_filter(
            self) -> None:
        self.fx.minimal()
        self.fx.commit_all()
        self.watched_filter(self.fx.root / ".git", self.fx.env)
        (self.fx.root / ".git" / "info" / "attributes").write_bytes(
            b"*.md filter=kappa\x00" + b"q" * 3000 + b"\n")

        inventory = self.extract_root(self.fx)

        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})

    def test_git_file_naming_a_directory_with_a_trailing_space_keeps_its_filters_blank(
            self) -> None:
        for number, ending in enumerate((b"\r\n", b"\n")):
            with self.subTest(ending=ending):
                case = self.base / f"case-{number}"
                case.mkdir()
                fixture = FixtureRoot(case)
                fixture.minimal()
                head = fixture.commit_all()
                common = case / "repo-dir "
                os.rename(fixture.root / ".git", common)
                (fixture.root / ".git").write_bytes(b"gitdir: ../repo-dir " + ending)
                self.watched_filter(common, fixture.env)

                inventory = self.extract_root(fixture)

                self.assertEqual(inventory["source_revision"], head)
                self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})

    def test_common_directory_with_a_trailing_space_keeps_its_filters_blank(self) -> None:
        for number, ending in enumerate((b"\r", b"\r\n")):
            with self.subTest(ending=ending):
                case = self.base / f"case-{number}"
                case.mkdir()
                fixture = FixtureRoot(case)
                main = case / "main"
                main.mkdir()
                for relative, content in (("rules/alpha-flow.md", "# Alpha flow\n"),
                                          ("workflows/beta-step.md", "# Beta step\n")):
                    (main / relative).parent.mkdir(parents=True, exist_ok=True)
                    (main / relative).write_text(content, encoding="utf-8")
                for args in (("init", "-q", "-b", "main"), ("add", "-A"),
                             ("commit", "-q", "-m", "chore: fixture"),
                             ("worktree", "add", "-q", "--detach", str(fixture.root))):
                    result = subprocess.run([str(REAL_GIT), "-C", str(main), *args],
                                            env=fixture.env, text=True, capture_output=True,
                                            check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                head = fixture.git("rev-parse", "HEAD")
                common = case / "common "
                os.rename(main / ".git", common)
                gitdir = common / "worktrees" / "root"
                (fixture.root / ".git").write_bytes(b"gitdir: " + os.fsencode(gitdir) + b"\n")
                (gitdir / "commondir").write_bytes(b"../../../common " + ending)
                self.watched_filter(common, fixture.env)

                inventory = self.extract_root(fixture)

                self.assertEqual(inventory["source_revision"], head)
                self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})


class BelowTopLevelRootTests(ToolCase):
    def test_root_below_the_top_level_reads_its_work_tree_as_unknown_without_status(
            self) -> None:
        if REAL_GIT is None:
            self.skipTest("git is not installed")
        self.fx.write("sub/rules/alpha-flow.md", "# Alpha flow\n")
        self.fx.write("sub/workflows/beta-step.md", "# Beta step\n")
        head = self.fx.commit_all()
        self.fx.write("sub/rules/alpha-flow.md", "# Alpha flow changed\n")
        log = self.base / "git-arguments.log"
        wrapper_bin = self.base / "wrapper-bin"
        wrapper_bin.mkdir()
        wrapper = wrapper_bin / "git"
        wrapper.write_text(
            f"#!/bin/sh\nfor argument in \"$@\"; do printf '%s\\n' \"$argument\"; done "
            f">> '{log}'\nexec '{REAL_GIT}' \"$@\"\n", encoding="utf-8")
        wrapper.chmod(0o755)
        env = {**self.fx.env, "PATH": f"{wrapper_bin}{os.pathsep}{self.fx.env['PATH']}"}
        out = self.base / "inventory.json"

        result = self.run_extract(out=out, root=self.fx.root / "sub", env=env)

        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = parse_inventory(out.read_text(encoding="utf-8"))
        self.assertEqual(inventory["source_revision"], head)
        self.assertEqual(inventory["worktree"], {"state": "unknown", "paths": []})
        arguments = log.read_text(encoding="utf-8").splitlines()
        self.assertIn("rev-parse", arguments)
        self.assertNotIn("status", arguments)


ATTRIBUTE_LIMIT_RELEASES = ("2.30.7", "2.31.6", "2.32.5", "2.33.6", "2.34.6", "2.35.6",
                            "2.36.4", "2.37.5", "2.38.3", "2.39.1")


class GitIsolationBoundaryDocstringTests(unittest.TestCase):
    def docstring_text(self) -> str:
        docstring = ast.get_docstring(ast.parse(TOOL.read_text(encoding="utf-8")))
        return " ".join(str(docstring).split())

    def test_module_docstring_names_the_releases_that_brought_the_attribute_limits(
            self) -> None:
        text = self.docstring_text()
        for phrase in ("January 2023", *ATTRIBUTE_LIMIT_RELEASES, "from 2.31.0 to 2.39.0"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_module_docstring_states_that_a_root_below_the_top_level_reads_unknown(
            self) -> None:
        text = self.docstring_text()
        self.assertNotIn("mismatched work-tree paths", text)
        self.assertIn("top level", text)
        self.assertIn("work-tree state as `unknown`", text)


class AuditIndexRefreshNoteTests(unittest.TestCase):
    def test_runbook_suggests_refreshing_the_index_before_an_extraction(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        bullets = [" ".join(item.split()) for item in re.split(r"\n(?=- )", text)
                   if "git update-index --refresh" in item]
        self.assertEqual(len(bullets), 1, "the runbook has no single note on the refresh")
        note = bullets[0]
        self.assertNotIn("audit-instructions.py verify", note)
        self.assertIn("audit-instructions.py extract", note)


# ---------------------------------------------------------------------------
# Documented residuals, confirmed only on a git older than the boundary they name
# ---------------------------------------------------------------------------

def installed_git_release() -> tuple[int, int, int]:
    """Major, minor and patch version of the git on PATH; (0, 0, 0) when unreadable."""
    if REAL_GIT is None:
        return (0, 0, 0)
    result = subprocess.run([REAL_GIT, "--version"], capture_output=True, text=True,
                            check=False)
    found = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", result.stdout)
    if found is None:
        return (0, 0, 0)
    return (int(found.group(1)), int(found.group(2)), int(found.group(3) or 0))


def has_attribute_limits(release: tuple[int, int, int]) -> bool:
    """Whether a git release ignores overlong attribute lines and files."""
    if release[:2] >= (2, 40):
        return True
    first = {tuple(int(part) for part in name.split(".")[:2]): int(name.split(".")[2])
             for name in ATTRIBUTE_LIMIT_RELEASES}.get(release[:2])
    return first is not None and release[2] >= first


def require_git_below(case: unittest.TestCase, maximum: tuple[int, int, int],
                      reason: str) -> None:
    if REAL_GIT is None:
        case.skipTest("git is not installed")
    if installed_git_release() >= maximum:
        case.skipTest(f"only a git older than {'.'.join(map(str, maximum))} {reason}")


class GitIsolationResidualTests(ToolCase):
    """On a git older than a boundary that the module docstring names, the filter it names
    still runs; each case is skipped on every later git."""

    def setUp(self) -> None:
        super().setUp()
        if REAL_GIT is None:
            self.skipTest("git is not installed")
        self.marker = self.base / "filter-ran"
        self.fx.minimal()

    def clean_filter(self) -> str:
        return str(marker_program(self.base / "clean-filter.sh", self.marker, "cat"))

    def extract_with_marker(self) -> dict:
        make_stat_stale(self.fx.root / "rules/alpha-flow.md")
        self.marker.unlink(missing_ok=True)
        inventory = self.extract()
        self.assertTrue(self.marker.exists(), "the documented residual did not occur")
        return inventory

    def information_filter(self, data: bytes) -> None:
        self.fx.git("config", "filter.kappa.clean", self.clean_filter())
        (self.fx.root / ".git" / "info").mkdir(exist_ok=True)
        (self.fx.root / ".git" / "info" / "attributes").write_bytes(data)

    def test_filter_selected_by_committed_attributes_runs_on_a_git_without_attr_source(
            self) -> None:
        require_git_below(self, (2, 41, 0), "ignores the attribute source")
        self.fx.write(".gitattributes", "*.md filter=kappa\n")
        self.fx.commit_all()
        self.fx.git("config", "filter.kappa.clean", self.clean_filter())

        inventory = self.extract_with_marker()

        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})

    def test_filter_named_by_information_attributes_runs_on_a_git_without_config_count(
            self) -> None:
        require_git_below(self, (2, 31, 0), "ignores configuration from the environment")
        self.fx.commit_all()
        self.information_filter(b"*.md filter=kappa\n")

        inventory = self.extract_with_marker()

        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})

    def test_overlong_information_attribute_line_runs_its_filter_on_a_git_without_limits(
            self) -> None:
        release = installed_git_release()
        if REAL_GIT is None or release < (2, 31, 0) or has_attribute_limits(release):
            self.skipTest("only a git from 2.31.0 without the attribute line limit "
                          "reads an overlong line and blanks named filters")
        self.fx.commit_all()
        self.information_filter(b"*.md filter=kappa" + b" " * 3000 + b"\n")

        inventory = self.extract_with_marker()

        self.assertEqual(inventory["worktree"], {"state": "clean", "paths": []})


# ---------------------------------------------------------------------------
# A `.git` directory that git does not take as a repository
# ---------------------------------------------------------------------------

class InvalidGitDirectoryTests(ToolCase):
    """A root whose `.git` directory git would not take as a repository reads its work
    tree as unknown, even when git finds a SHA-1 repository above it."""

    def test_invalid_git_directory_below_a_sha1_top_level_reads_unknown(self) -> None:
        if REAL_GIT is None:
            self.skipTest("git is not installed")
        self.fx.write("sub/rules/alpha-flow.md", "# Alpha flow\n")
        self.fx.write("sub/workflows/beta-step.md", "# Beta step\n")
        self.fx.commit_all()
        self.fx.write("sub/rules/alpha-flow.md", "# Alpha flow changed\n")
        shapes = {
            "empty": {},
            "head only": {"HEAD": "ref: refs/heads/main\n"},
            "head and objects": {"HEAD": "ref: refs/heads/main\n", "objects/.keep": ""},
        }
        for number, (shape, files) in enumerate(shapes.items()):
            with self.subTest(shape=shape):
                dot_git = self.fx.root / "sub" / ".git"
                shutil.rmtree(dot_git, ignore_errors=True)
                dot_git.mkdir()
                for relative, content in files.items():
                    (dot_git / relative).parent.mkdir(parents=True, exist_ok=True)
                    (dot_git / relative).write_text(content, encoding="utf-8")
                out = self.base / f"inventory-{number}.json"

                result = self.run_extract(out=out, root=self.fx.root / "sub")

                self.assertEqual(result.returncode, 0, result.stderr)
                inventory = parse_inventory(out.read_text(encoding="utf-8"))
                self.assertEqual(inventory["worktree"], {"state": "unknown", "paths": []})

    def test_module_docstring_states_that_an_invalid_git_directory_reads_unknown(
            self) -> None:
        docstring = ast.get_docstring(ast.parse(TOOL.read_text(encoding="utf-8")))
        text = " ".join(str(docstring).split())
        self.assertIn("does not take as a repository", text)


# ---------------------------------------------------------------------------
# Verify inputs read without following links, and entry kinds compared
# ---------------------------------------------------------------------------

STORED_AUDITS = "docs/stored-audits"


class VerifyEntryKindTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build
    verify = VerifyTreeTests.verify

    def test_audited_entry_that_changes_kind_is_stale_without_strict(self) -> None:
        def link_to_pipe(fixture: FixtureRoot) -> None:
            (fixture.root / LINK).unlink()
            os.mkfifo(fixture.root / LINK)

        def file_to_link(fixture: FixtureRoot) -> None:
            (fixture.root / DELTA).unlink()
            (fixture.root / DELTA).symlink_to("alpha-flow.md")

        for name, path, change in (("link becomes a pipe", LINK, link_to_pipe),
                                   ("file becomes a link", DELTA, file_to_link)):
            with self.subTest(case=name):
                fixture, _ = self.build(name.replace(" ", "-"))
                change(fixture)
                result = self.verify(fixture)
                self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
                self.assertEqual(result.stdout,
                                 f"inventory-stale {path}:0 changed kind in the root\n")


class VerifyLinkedInputTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build
    verify = VerifyTreeTests.verify

    def test_linked_inventory_or_assessment_is_invalid_and_not_followed(self) -> None:
        for code, relative in (("inventory", INVENTORY_PATH), ("assessment", ASSESSMENT_PATH)):
            for target in ("stored.json", "absent.json"):
                with self.subTest(file=code, target=target):
                    fixture, _ = self.build(f"{code}-{target.split('.')[0]}")
                    refresh_report(fixture)
                    path = fixture.root / relative
                    if target == "stored.json":
                        path.rename(path.parent / target)
                    else:
                        path.unlink()
                    path.symlink_to(target)
                    result = self.verify(fixture, report=str(fixture.root / REPORT_PATH))
                    self.assertEqual((result.returncode, result.stderr), (1, ""),
                                     result.stdout)
                    self.assertEqual(result.stdout, f"{code}-invalid {relative}:0 is a "
                                                    "symbolic link and is not followed\n")

    def test_link_above_the_inputs_is_followed_like_the_report_directory(self) -> None:
        fixture, _ = self.build("parent-link")
        refresh_report(fixture)
        audits = fixture.root / "docs" / "audits"
        audits.rename(fixture.root / STORED_AUDITS)
        audits.symlink_to("stored-audits")
        self.assert_silent(self.verify(fixture, report=str(fixture.root / REPORT_PATH)))


# ---------------------------------------------------------------------------
# Amendment text, target and dependency rules
# ---------------------------------------------------------------------------

OTHER_TABLE = "\n## Other\n\n| Other term | Not a term of the migration |\n|---|---|\n" \
              "| Row term | Also not a term |\n"


class VerifyAmendmentFormTests(MigrationMapCase):
    def write_spec(self, text: str) -> None:
        path = self.fixture.root / SPEC09_PATH
        self.addCleanup(path.write_text, SPEC09_TEXT, encoding="utf-8")
        path.write_text(text, encoding="utf-8")

    def test_blank_current_text_of_an_existing_target_is_amendment_invalid(self) -> None:
        for current in ("", " ", "\n"):
            with self.subTest(current=current):
                self.setUp()
                amendment = self.add_amendment(current=current)
                self.assert_reports(self.verify(), [("amendment-invalid",
                                                     assessment_at(amendment))])

    def test_notes_target_matches_a_heading_with_trailing_whitespace(self) -> None:
        for ending in (" ", "\t", " \t "):
            with self.subTest(ending=repr(ending)):
                self.setUp()
                self.write_spec(SPEC09_TEXT.replace("### Ownership\n",
                                                    f"### Ownership{ending}\n"))
                self.add_amendment(target="Notes:Ownership",
                                   current="The migration owns every rename.")
                self.assert_silent(self.verify())

    def test_terminology_target_matches_only_a_body_row_of_the_terminology_table(
            self) -> None:
        self.write_spec(SPEC09_TEXT + OTHER_TABLE)
        for target in ("Terminology:Term", "Terminology:Other term", "Terminology:Row term"):
            with self.subTest(target=target):
                self.setUp()
                amendment = self.add_amendment(target=target)
                self.assert_reports(self.verify(), [("amendment-target-unknown",
                                                     assessment_at(amendment))])
        with self.subTest(target="Terminology:Kind prefix"):
            self.setUp()
            self.add_amendment(target="Terminology:Kind prefix",
                               current="| Kind prefix | The first stem component |")
            self.assert_silent(self.verify())

    def test_self_dependency_and_dependency_cycles_are_amendment_invalid(self) -> None:
        cases: dict[str, tuple[dict[str, list[str]], list[str]]] = {
            "self-dependency": ({"AMD-08-01": ["AMD-08-01"]}, ["AMD-08-01"]),
            "two-amendment cycle": ({"AMD-08-01": ["AMD-08-02"], "AMD-08-02": ["AMD-08-01"]},
                                    ["AMD-08-01", "AMD-08-02"]),
            "three-amendment cycle": ({"AMD-08-01": ["AMD-08-02"], "AMD-08-02": ["AMD-08-03"],
                                       "AMD-08-03": ["AMD-08-01"]},
                                      ["AMD-08-01", "AMD-08-02", "AMD-08-03"]),
            "dependency on a cycle": ({"AMD-08-01": ["AMD-08-02"], "AMD-08-02": ["AMD-08-01"],
                                       "AMD-08-03": ["AMD-08-02"]},
                                      ["AMD-08-01", "AMD-08-02"]),
            "chain without a cycle": ({"AMD-08-01": [], "AMD-08-02": ["AMD-08-01"],
                                       "AMD-08-03": ["AMD-08-02", "AMD-08-01"]}, []),
        }
        for name, (graph, members) in cases.items():
            with self.subTest(case=name):
                self.setUp()
                for identifier in sorted(graph):
                    if identifier != "AMD-08-01":
                        self.add_amendment(id=identifier)
                for identifier, depends_on in graph.items():
                    self.assessment["amendments"][row_index(
                        self.assessment["amendments"], "id", identifier)][
                        "depends_on"] = depends_on
                result = self.verify()
                if members:
                    self.assert_reports(result, [("amendment-invalid", assessment_at(item))
                                                 for item in members])
                else:
                    self.assert_silent(result)


# ---------------------------------------------------------------------------
# ASCII digits in identifiers and line numbers
# ---------------------------------------------------------------------------

ARABIC_INDIC = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def indic(text: str) -> str:
    """The text with its ASCII digits written as Arabic-Indic digits."""
    return text.translate(ARABIC_INDIC)


class VerifyAsciiDigitTests(RenderCase):
    add_amendment = MigrationMapCase.add_amendment

    def replaced(self, key: str, identifier: str, field: str, value: object) -> str:
        """Set one field of the files row (by path), finding or amendment (by id); return
        that row's location."""
        index = row_index(self.assessment[key], "path" if key == "files" else "id", identifier)
        self.assessment[key][index][field] = value
        return assessment_at(f"files[{index}]" if key == "files" else identifier)

    def test_line_evidence_with_other_digits_breaks_its_form_or_resolves_nowhere(
            self) -> None:
        cases: dict[str, tuple[str, str, list[str], str]] = {
            "files row": ("files", DELTA, [f"{DELTA}:{indic('3')}"], "assessment-invalid"),
            "finding line": ("findings", "AUD-08-004", [f"{GAMMA}:{indic('3')}"],
                             "evidence-unresolved"),
            "finding range": ("findings", "AUD-08-004", [f"{GAMMA}:1-{indic('3')}"],
                              "evidence-unresolved"),
            "amendment line": ("amendments", "AMD-08-01", ["AUD-08-001", f"{BETA}:{indic('3')}"],
                               "amendment-invalid"),
        }
        for name, (key, identifier, evidence, code) in cases.items():
            with self.subTest(case=name):
                self.setUp()
                location = self.replaced(key, identifier, "evidence", evidence)
                self.assert_reports(self.verify(), [(code, location)])

    def test_identifiers_with_other_digits_break_their_forms(self) -> None:
        with self.subTest(case="finding id"):
            self.setUp()
            self.replaced("findings", "AUD-08-002", "id", f"AUD-08-{indic('002')}")
            self.assert_codes(self.verify(), "assessment-invalid", assessment_at(""))
        with self.subTest(case="amendment id"):
            self.setUp()
            self.add_amendment(id=f"AMD-08-{indic('02')}")
            self.assert_codes(self.verify(), "assessment-invalid", assessment_at(""))
        with self.subTest(case="dependency id"):
            self.setUp()
            self.replaced("amendments", "AMD-08-01", "depends_on", [f"AMD-08-{indic('01')}"])
            self.assert_codes(self.verify(), "assessment-invalid", assessment_at(""))
        with self.subTest(case="statement coverage line"):
            self.setUp()
            self.assessment["req21"]["statements"][0]["covered_by"] = f"{ALPHA}:{indic('9')}"
            self.assert_codes(self.verify(), "assessment-invalid", assessment_at(""))
        cases: dict[str, tuple[str, list[str]]] = {
            "affected criterion id": ("affected", [f"AC-{indic('05')}"]),
            "finding id in amendment evidence": ("evidence",
                                                 ["AUD-08-001", f"AUD-08-{indic('001')}"]),
        }
        for name, (field, value) in cases.items():
            with self.subTest(case=name):
                self.setUp()
                location = self.replaced("amendments", "AMD-08-01", field, value)
                self.assert_reports(self.verify(), [("amendment-invalid", location)])

    def test_statement_source_with_other_digits_is_no_statement_unit(self) -> None:
        index, line = len(STATEMENT_UNIT_LINES) - 1, STATEMENT_UNIT_LINES[-1]
        self.assertGreater(line, 9)
        self.assessment["req21"]["statements"][index]["source"] = (
            f"{PHASE_DISCOVERY}:{str(line)[0]}{indic(str(line)[1:])}")
        self.assert_reports(self.verify(), [
            ("req21-invalid", assessment_at(f"req21.statements[{index}]")),
            ("req21-invalid", f"{PHASE_DISCOVERY}:{line}")])

    def test_blockers_line_with_other_digits_lists_no_finding(self) -> None:
        listed = blocking_ids(self.assessment) + [f"AUD-08-{indic('003')}"]
        text = self.valid_report(blockers=listed)
        self.assert_silent(self.verify_report(text))


TEN_LINE_READER = "docs/TEN.md"


class VerifyEvidenceLineDigitsTests(SharedVerifyCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="audit-line-digits-")
        try:
            cls.fixture, cls.inventory = build_verify_fixture(
                Path(cls.temp.name),
                extra={TEN_LINE_READER: "".join(f"Line {n}.\n" for n in range(1, 11))})
        except BaseException:
            cls.temp.cleanup()
            raise

    def test_line_with_more_digits_than_the_line_count_is_outside_its_entry(self) -> None:
        self.assertEqual(inventory_entry(self.inventory, TEN_LINE_READER)["lines"], 10)
        cases = {"ten-digit line": "1000000000", "three-digit line": "100",
                 "two-digit line past the count": "11", "last line": "10",
                 "last line with leading zeros": "0000000010"}
        for name, digits in cases.items():
            with self.subTest(case=name):
                self.setUp()
                index = row_index(self.assessment["findings"], "id", "AUD-08-002")
                self.assessment["findings"][index]["evidence"] = [
                    f"{GUIDE}:1", f"{TEN_LINE_READER}:{digits}"]
                result = self.verify()
                if int(digits) > 10:
                    self.assert_reports(result, [("evidence-unresolved",
                                                  assessment_at("AUD-08-002"))])
                else:
                    self.assert_silent(result)


# ---------------------------------------------------------------------------
# Output boundary: escapes, quoted values and a failing standard output
# ---------------------------------------------------------------------------

EPSILON = "rules/epsilon-rule.md"
COSTLY_OUTPUT_LINE = "Paste the full test output costing $5 into the report."
FINDINGS_OBSERVATION_COLUMN = 8


def extra_coverage_location(assessment: dict, path: str) -> str:
    """Append a coverage row for a path outside the inventory and return its location."""
    assessment["coverage"].append(coverage_row({"path": path, "entry": "file",
                                                "encoding": "utf-8", "sha256": "0" * 64}))
    return assessment_at(f"coverage[{len(assessment['coverage']) - 1}]")


def displayed_cells(row: str) -> list[str]:
    """The cells of a table row as GitHub-flavoured Markdown displays them: the row splits
    at each pipe without a backslash directly before it, the backslash of an escaped pipe
    is dropped, and a backslash before ASCII punctuation then displays that character."""
    inner = row.strip()[1:-1]
    return [re.sub(r"\\([!-/:-@\[-`{-~])", r"\1", piece.strip().replace("\\|", "|"))
            for piece in re.split(r"(?<!\\)\|", inner)]


class OutputBoundaryPinTests(SharedVerifyCase):
    def test_backslash_and_line_separators_in_a_copied_string_are_escaped(self) -> None:
        location = extra_coverage_location(self.assessment, "rules/a\\b\u2028c\x85d.md")
        result = self.verify()
        self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
        self.assertEqual(result.stdout, f"row-extra {location} "
                                        "rules/a\\x5cb\\u2028c\\x85d.md is not an audited path\n")


class OutputBoundaryPinToolTests(ToolCase):
    def test_root_unreadable_line_for_a_name_with_a_line_break_stays_one_line(self) -> None:
        self.fx.minimal()
        name = os.fsencode(self.fx.root / "rules") + b"/bad\n\xff.md"
        with open(name, "wb") as handle:
            handle.write(b"# Bad name\n")
        out = self.base / "inventory.json"
        result = self.run_extract(out=out)
        self.assertEqual((result.returncode, result.stdout), (2, ""), result.stderr)
        self.assertEqual(result.stderr, "ERROR: root-unreadable: a file name is not valid "
                                        "UTF-8: rules/bad\\x0a\\udcff.md\n")
        self.assertFalse(out.exists())


class OutputBoundaryStreamTests(unittest.TestCase):
    def test_write_lines_escapes_what_an_ascii_stream_cannot_encode(self) -> None:
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding="ascii", newline="\n")
        tool_module().write_lines(stream, [
            ("code-x", "rules/\u00e9.md:0", "na\u00efve \u2713 \U0001f600"),
            "ERROR: code-y: caf\u00e9"])
        stream.flush()
        self.assertEqual(buffer.getvalue(), b"code-x rules/\\xe9.md:0 na\\xefve \\u2713 "
                                            b"\\U0001f600\nERROR: code-y: caf\\xe9\n")


class OutputEscapeTests(SharedVerifyCase):
    def test_format_characters_in_a_message_are_escaped(self) -> None:
        location = extra_coverage_location(self.assessment, "rules/a\u202eb\u200dc\ufeffd.md")
        self.finding("AUD-08-003")["section"] = "## Con\u00adtract"
        result = self.verify()
        self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
        self.assertEqual(result.stdout.split("\n"), [
            f"finding-invalid {assessment_at('AUD-08-003')} section \"## Con\\xadtract\" is "
            "not a section of the source",
            f"row-extra {location} rules/a\\u202eb\\u200dc\\ufeffd.md is not an audited path",
            ""])

    def test_quoted_values_double_an_inner_quote(self) -> None:
        cases = {'a"b': '"a""b"', '"': '""""', 'a\\"b': '"a\\x5c""b"'}
        for value, quoted in cases.items():
            with self.subTest(value=value):
                self.setUp()
                self.finding("AUD-08-003")["section"] = value
                result = self.verify()
                self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
                self.assertEqual(result.stdout, f"finding-invalid {assessment_at('AUD-08-003')} "
                                                f"section {quoted} is not a section of the "
                                                "source\n")
        self.setUp()
        self.finding("AUD-08-002")["evidence"] = [f"{GUIDE}:1", 'x" y']
        result = self.verify()
        self.assertEqual(result.stdout, f"finding-invalid {assessment_at('AUD-08-002')} "
                                        'evidence "x"" y" is not path:line, a path or an '
                                        "amendment id\n")

    def test_empty_quoted_value_is_two_quotes(self) -> None:
        self.finding("AUD-08-003")["section"] = ""
        result = self.verify()
        self.assertEqual(result.stdout, f"finding-invalid {assessment_at('AUD-08-003')} "
                                        'section "" is not a section of the source\n')


class OutputLocationEscapeTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build
    verify = VerifyTreeTests.verify

    def test_space_separators_and_a_soft_hyphen_in_a_location_are_escaped(self) -> None:
        fixture, _ = self.build("separators")
        names = {"rules/a\u00a0b.md": "rules/a\\xa0b.md",
                 "rules/c\u2003d.md": "rules/c\\u2003d.md",
                 "rules/e\u3000f.md": "rules/e\\u3000f.md",
                 "rules/g\u00adh.md": "rules/g\\xadh.md"}
        for name in names:
            fixture.write(name, "# Added\n")
        result = self.verify(fixture)
        self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
        self.assertEqual(sorted(result.stdout.split("\n")[:-1]),
                         sorted(f"inventory-stale {escaped}:0 added to the root"
                                for escaped in names.values()))


class OutputFailureTests(SharedVerifyCase):
    def commands(self) -> dict[str, list[str]]:
        """A verify that prints a diagnostic and a render that prints the region."""
        self.assessment["inventory_digest"] = "f" * 64
        self.assertEqual(self.verify().returncode, 1)
        root, report = str(self.fixture.root), str(self.fixture.root / REPORT_PATH)
        return {"verify": ["verify", "--root", root, "--report", report],
                "render": ["render", "--root", root, "--report", report]}

    def run_into(self, arguments: list[str], descriptor: int
                 ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run([sys.executable, "-I", str(TOOL), *arguments],
                              cwd=self.fixture.base, env=self.fixture.env, stdout=descriptor,
                              stderr=subprocess.PIPE, timeout=60)

    def assert_output_unwritable(self, result: subprocess.CompletedProcess[bytes]) -> None:
        self.assertNotIn(b"Traceback", result.stderr)
        self.assertEqual(result.returncode, 2, result.stderr)
        lines = result.stderr.decode("utf-8").split("\n")
        self.assertEqual(len(lines), 2, lines)
        self.assertEqual(lines[1], "")
        self.assertTrue(lines[0].startswith("ERROR: output-unwritable: "), lines)

    def test_full_device_as_standard_output_exits_two_with_one_error_line(self) -> None:
        if not os.path.exists("/dev/full"):
            self.skipTest("/dev/full does not exist")
        for name, arguments in self.commands().items():
            with self.subTest(command=name), open("/dev/full", "wb") as full:
                self.assert_output_unwritable(self.run_into(arguments, full.fileno()))

    def test_closed_pipe_as_standard_output_exits_two_with_one_error_line(self) -> None:
        for name, arguments in self.commands().items():
            with self.subTest(command=name):
                reading, writing = os.pipe()
                os.close(reading)
                try:
                    result = self.run_into(arguments, writing)
                finally:
                    os.close(writing)
                self.assert_output_unwritable(result)


class OutputBoundaryDocstringTests(unittest.TestCase):
    def test_module_docstring_states_the_escapes_and_the_output_failure(self) -> None:
        docstring = ast.get_docstring(ast.parse(TOOL.read_text(encoding="utf-8")))
        text = " ".join(str(docstring).split())
        for phrase in ("`\\xNN`", "`\\uNNNN`", "`\\UNNNNNNNN`", "format characters",
                       "space separator", "doubled", "output-unwritable",
                       "owner write permission", "outside its generated region"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertNotIn("amounts anywhere in it", text)


# ---------------------------------------------------------------------------
# Render: cell escapes, row order and report permissions
# ---------------------------------------------------------------------------

class RenderCellEscapeTests(RenderCase):
    def test_backslashes_before_a_pipe_stay_in_one_cell_and_display_as_written(self) -> None:
        values = {"AUD-08-001": "a\\|b", "AUD-08-002": "x\\\\\\|y", "AUD-08-003": "p|q\\r"}
        for identifier, value in values.items():
            self.finding(identifier)["observation"] = value
        region = self.region()
        self.assertEqual(region, expected_region(self.inventory, self.assessment))
        rows = {row.split(" | ")[0][2:]: row for row in region_bodies(region)["Findings"][2:]}
        for identifier, value in values.items():
            with self.subTest(value=value):
                cells = displayed_cells(rows[identifier])
                self.assertEqual(len(cells), len(HEADERS["Findings"]), cells)
                self.assertEqual(cells[FINDINGS_OBSERVATION_COLUMN], value)


class RenderRowOrderTests(RenderCase):
    def test_shuffled_inventory_renders_its_rows_sorted_by_path_line_and_column(self) -> None:
        ordered = copy.deepcopy(self.inventory)
        mention = ordered["legacy_mentions"][0]
        ordered["legacy_mentions"].append(dict(mention, column=mention["column"] + 1))
        shuffled = copy.deepcopy(ordered)
        for key in ("files", "edges", "legacy_mentions"):
            shuffled[key].reverse()
        for entry in shuffled["files"]:
            if entry["sections"]:
                entry["sections"].reverse()
        expected = expected_region(ordered, self.assessment)
        in_input_order = expected_bodies(shuffled, self.assessment)
        for name in ("Inventory", "Sections", "References", "Loads", "Legacy mentions"):
            with self.subTest(table=name):
                self.assertNotEqual(in_input_order[name], region_bodies(expected)[name])
        restore = self.rewrite_inventory(canonical(shuffled))
        try:
            region = self.region()
        finally:
            restore()
        self.assertEqual(region, expected)


class RenderWritePermissionTests(RenderCase):
    assert_refused = RenderWriteTests.assert_refused

    def write_report_with_mode(self, mode: int) -> Path:
        """An unrendered report with the given permission bits, made writable again after
        the case."""
        self.write_assessment()
        self.fixture.write(REPORT_PATH, report_text(blockers=blocking_ids(self.assessment)))
        report = self.report_file()
        report.chmod(mode)
        self.addCleanup(report.chmod, 0o644)
        return report

    def test_render_write_refuses_a_report_without_owner_write_permission(self) -> None:
        for mode in (0o444, 0o460):
            with self.subTest(mode=oct(mode)):
                report = self.write_report_with_mode(mode)
                before, listing = report.read_bytes(), self.audits_listing()
                result = run_render(self.fixture, "--write")
                self.assertEqual(stat.S_IMODE(report.stat().st_mode), mode)
                report.chmod(0o644)
                self.assert_refused(result, "report-unwritable", before, listing)

    def test_render_write_keeps_the_mode_of_a_writable_report(self) -> None:
        for mode in (0o640, 0o600):
            with self.subTest(mode=oct(mode)):
                report = self.write_report_with_mode(mode)
                result = run_render(self.fixture, "--write")
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
                self.assertEqual(stat.S_IMODE(report.stat().st_mode), mode)
                self.assertIn(expected_region(self.inventory, self.assessment),
                              report.read_text(encoding="utf-8"))
                report.chmod(0o644)


# ---------------------------------------------------------------------------
# Report economics outside the generated region
# ---------------------------------------------------------------------------

class ReportEconomicsRegionTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build

    def test_amount_copied_into_the_region_is_silent_and_one_outside_it_is_a_claim(
            self) -> None:
        fixture, inventory = self.build(
            "copied-amount", extra={EPSILON: f"# Epsilon rule\n\n{COSTLY_OUTPUT_LINE}\n"})
        self.assertIn(COSTLY_OUTPUT_LINE, [item["text"] for item in inventory["full_output"]])
        rendered = run_render(fixture)
        self.assertEqual((rendered.returncode, rendered.stderr), (0, ""), rendered.stdout)
        self.assertIn(COSTLY_OUTPUT_LINE, rendered.stdout)
        blockers = blocking_ids(valid_assessment(inventory))
        for summary, expected in (
                ("Every audited file was read once.", []),
                ("One run costs $5 in total.", [("economics-claim", f"{REPORT_PATH}:5")])):
            with self.subTest(summary=summary):
                fixture.write(REPORT_PATH, report_text(region=rendered.stdout,
                                                       blockers=blockers, summary=summary))
                result = run_tool(["verify", "--root", str(fixture.root), "--report",
                                   str(fixture.root / REPORT_PATH)], fixture.env, fixture.base)
                if expected:
                    self.assert_reports(result, expected)
                else:
                    self.assert_silent(result)


# ---------------------------------------------------------------------------
# Separator rows without dashes, and the stricter terminology table separator
# ---------------------------------------------------------------------------

DASHLESS_SEPARATORS = ("| | |", "|:|:|", "|\t|\t|", "| :\t| :\t|")


class SeparatorRowWithoutDashesTests(CandidateCase):
    def test_separator_row_with_empty_or_colon_only_cells_is_not_a_unit(self) -> None:
        content_row = "| Every audited file | keeps one row | here |"
        lines = ["# S", "", "| | | | | | | | |", "| : | : | : | : |",
                 "|:\t|:\t|:\t|:\t|:\t|:\t|:\t|:\t|", "|\t|\t|\t|\t|\t|\t|\t|\t|  ",
                 content_row]
        for path in ("rules/u-one.md", "rules/u-two.md"):
            self.write_lines(path, lines)

        inventory = self.extract()

        self.assertEqual(inventory["duplicate_clusters"], [
            cluster(1, " ".join(content_row.split()),
                    [("rules/u-one.md", 7, 7), ("rules/u-two.md", 7, 7)]),
        ])


class StatementUnitSeparatorTests(VerifyAssertions):
    setUp = VerifyTreeTests.setUp
    tearDown = VerifyTreeTests.tearDown
    build = VerifyTreeTests.build
    verify = VerifyTreeTests.verify
    discovery_root = VerifyStatementUnitTests.discovery_root
    verify_statements = VerifyStatementUnitTests.verify_statements

    def test_separator_row_with_empty_or_colon_only_cells_starts_no_statement_unit(
            self) -> None:
        for index, separator in enumerate(DASHLESS_SEPARATORS):
            with self.subTest(separator=repr(separator)):
                fixture, assessment = self.discovery_root(
                    f"dashless{index}", "# Phase discovery\n\n## Codebase Reading Rules\n\n"
                    f"| Rule | Meaning |\n{separator}\n| Read once | Every file |\n")
                self.assert_silent(self.verify_statements(fixture, assessment, [5, 7]))
                self.assert_reports(self.verify_statements(fixture, assessment, [5, 7, 6]),
                                    [("req21-invalid", assessment_at("req21.statements[2]"))])


class TerminologySeparatorTests(MigrationMapCase):
    write_spec = VerifyAmendmentFormTests.write_spec

    def test_terminology_table_needs_dashes_in_its_separator_row(self) -> None:
        for separator in ("| | |", "|:|:|"):
            with self.subTest(separator=separator):
                self.setUp()
                self.write_spec(SPEC09_TEXT.replace("|---|---|", separator))
                amendment = self.add_amendment(target="Terminology:Kind prefix",
                                               current="| Kind prefix | The first stem component |")
                self.assert_reports(self.verify(), [("amendment-target-unknown",
                                                     assessment_at(amendment))])

    def test_terminology_separator_with_alignment_colons_keeps_the_table(self) -> None:
        for separator in ("|:---|---:|", "| :---: | --- |"):
            with self.subTest(separator=separator):
                self.setUp()
                self.write_spec(SPEC09_TEXT.replace("|---|---|", separator))
                self.add_amendment(target="Terminology:Kind prefix",
                                   current="| Kind prefix | The first stem component |")
                self.assert_silent(self.verify())


class AssessmentCellEconomicsTests(SharedVerifyCase):
    def test_amount_that_a_cell_displays_is_a_claim_at_the_assessment_location(self) -> None:
        cases = {
            "control between number and unit": (
                ("findings", "AUD-08-002", "observation"), "It costs 5\u0001tokens.",
                "5 tokens"),
            "control after the currency sign": (
                ("findings", "AUD-08-002", "observation"), "It costs $\u00015.", "$ 5"),
            "delete between number and unit": (
                ("findings", "AUD-08-002", "observation"), "It costs 5\u007ftokens.",
                "5 tokens"),
            "control in a legacy note": (("legacy", 0, "note"), "Costs 5\u0002tokens",
                                         "5 tokens"),
        }
        for name, ((key, row, field), value, amount) in cases.items():
            with self.subTest(case=name):
                self.setUp()
                if isinstance(row, str):
                    self.finding(row)[field] = value
                    location = assessment_at(row)
                else:
                    self.assessment[key][row][field] = value
                    location = assessment_at(f"{key}[{row}]")
                result = self.verify()
                self.assertEqual((result.returncode, result.stderr), (1, ""), result.stdout)
                self.assertEqual(result.stdout, f"economics-claim {location} names an amount: "
                                                f'"{amount}"\n')


if __name__ == "__main__":
    unittest.main()
