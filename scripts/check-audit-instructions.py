#!/usr/bin/env python3
"""Acceptance suite for scripts/audit-instructions.py.

Every case builds a disposable fixture root under a private temporary directory, with
minimal rules/, workflows/, harness/ and reader files and, where a case needs git, an
initialised repository whose git calls use a temporary HOME and XDG_CONFIG_HOME. The
tool runs as a subprocess with `python3 -I`, except that the defect predicate, a pure
function over one edge, is called after loading the tool's source as a module; no real
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
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable, Sequence
from pathlib import Path

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
                       "## Codebase Reading Rules\n"),
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
            ("r-one → Codebase Reading Rules", R_ONE, "heading-unmarked"),
            ("r-one → Scope", R_ONE, "heading-unmarked"),
            ("r-one → Missing Part", R_ONE, "missing-heading"),
            ("r-one → # R one", R_ONE, "resolved"),
            ("r-one → ### Detail", R_ONE, "resolved"),
            ("r-one → ## Step 1 → ### Detail", R_ONE, "resolved"),
            ("r-one → ## Codebase Reading Rules → ### Detail", R_ONE, "missing-heading"),
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
        "`r-one → Codebase Reading Rules`",
        "`r-one → #### Deep`",
        "`workflows/w-one.md → ## Step 1`",
        "Text w-one.md here.",
        "## Codebase Reading Rules",
    ]
    IN_GRAMMAR = {
        (1, "w-one → ## Step 1"): True, (2, "/w-one"): True, (3, "rule-shared-step"): True,
        (4, "rules/solo.md"): True, (5, "rules/zz-gone.md"): True,
        (6, "w-one.md → ### Sub"): True, (7, "rules/*.md"): False, (8, "w-one"): False,
        (9, "r-one → Codebase Reading Rules"): False, (10, "r-one → #### Deep"): False,
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
}
VERIFY_LINKS = {LINK: "caps.json"}
VERIFY_KINDS = {
    ALPHA: ["contract", "reference"], DELTA: ["contract"], BETA: ["workflow"],
    GAMMA: ["workflow"], CAPS: ["adapter-config"], LINK: ["adapter-config"],
    BLOB: ["adapter-config"],
}
VERIFY_SECTIONS = {
    ALPHA: [
        {"heading": "(preamble)", "kind": "contract", "proposed_home": ALPHA},
        {"heading": "## Contract", "kind": "contract", "proposed_home": ALPHA},
        {"heading": "## Example", "kind": "reference", "proposed_home": "rules/reference/alpha.md"},
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
            "evidence": [f"{path}:1"],
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
    return [{"id": "AMD-08-01", "target": "REQ-01", "change": "editorial",
             "current": "Current text.", "proposed": "Proposed text.",
             "reason": "The reference names a heading that does not exist.",
             "evidence": ["AUD-08-001"], "affected": [], "depends_on": [],
             "requires_adr": False, "disposition": "proposed"}]


def valid_assessment(inventory: dict) -> dict:
    """A fully valid assessment of the verify fixture; map and req21 are placeholders."""
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
        "map": [],
        "req21": {"verdict": "covered", "statements": []},
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

    def verify(self, *extra: str, text: str | None = None) -> subprocess.CompletedProcess[str]:
        target = self.fixture.root / ASSESSMENT_PATH
        target.write_text(text if text is not None else canonical(self.assessment),
                          encoding="utf-8")
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
             .update(proposed_home="rules/reference/12k-tokens.md"), "files[3]"),
        )
        for name, fault, fragment in cases:
            with self.subTest(case=name):
                value = valid_assessment(self.inventory)
                fault(value)
                self.assert_reports(self.verify(text=canonical(value)),
                                    [("economics-claim", assessment_at(fragment))])


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


if __name__ == "__main__":
    unittest.main()
