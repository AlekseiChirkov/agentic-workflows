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
import hashlib
import importlib.util
import json
import os
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


if __name__ == "__main__":
    unittest.main()
