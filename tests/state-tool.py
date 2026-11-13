"""Acceptance suite for the subtask-progress state tool, using disposable task fixtures."""
from __future__ import annotations

import ast
import contextlib
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

# Any carries decoded JSON documents whose shape is the subject under test.

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "state-tool.py"
RULES = ROOT / "rules" / "workflow-globals.md"
TASK_RELATIVE = ".ai/tasks/todo/task-demo"

LEAF_T01 = """T-01 | Progress parser | atomic-tests: green | atomic-execution: complete | atomic-validation: not-started
  last_action: tests pass
  target_files: scripts/tool.py, tests/tool.py
  blocker: none
  notes: "quoted first note"
         second line

         third line after blank
  verification: x
  branch: feat/demo
  pr: none
"""

COMPOSITE_T02 = """[composite] T-02 | Composite parent | rollup: in-progress | integration-validation: not-started
  children: T-02a, T-02b
  blocker: none
  notes:
"""

FENCE = """```text
## Subtask Progress
T-01 | Example | atomic-tests: red | atomic-execution: not-started | atomic-validation: not-started
  last_action: fenced
```
"""


def state_text(*blocks: str, contract_version: str | None = None, before: str = "",
               after: str = "## Solution Design\n\nNothing here.\n") -> str:
    """Build a task state file with the progress section holding the given blocks."""
    head = "spec_path: .ai/specs/demo.md\n"
    if contract_version is not None:
        head += f"contract_version: {contract_version}\n"
    head += "flow: full\n\n## Phases\n- discovery: complete\n\n" + before
    section = "## Subtask Progress\n\n" + "\n".join(blocks)
    if blocks:
        section += "\n"
    return head + section + after


def leaf(block_id: str, *, header: str | None = None, body: str | None = None,
         name: str = "Leaf") -> str:
    """Build a well-formed leaf block, optionally replacing its header statuses or body."""
    statuses = header if header is not None else (
        "atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started")
    lines = body if body is not None else (
        "  last_action:\n  target_files:\n  blocker: none\n  notes:\n")
    return f"{block_id} | {name} | {statuses}\n{lines}"


def receipts(count: int) -> str:
    """Return a receipts value with count well-formed entries and unique identifiers."""
    return ", ".join(f"op-{index:02d}#{index:016x}" for index in range(count))


@dataclass(frozen=True)
class ToolResult:
    code: int
    stdout: str
    stderr: str


Snapshot = dict[str, tuple[int, int, bytes | str | None]]


def snapshot(directory: Path) -> Snapshot:
    """Record bytes, mode and mtime of every entry below the directory without following links."""
    entries: Snapshot = {}
    for current, directories, files in os.walk(directory):
        for name in sorted(directories + files):
            path = Path(current) / name
            info = os.lstat(path)
            content: bytes | str | None = None
            if stat.S_ISLNK(info.st_mode):
                content = os.readlink(path)
            elif stat.S_ISREG(info.st_mode):
                content = path.read_bytes()
            entries[str(path.relative_to(directory))] = (info.st_mode, info.st_mtime_ns, content)
    return entries


class StateToolCase(unittest.TestCase):
    """Shared fixture builders, the subprocess runner and output assertions."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "project"
        self.task = self.root / TASK_RELATIVE
        self.task.mkdir(parents=True)

    def write_state(self, text: str | bytes) -> Path:
        path = self.task / "state.md"
        if isinstance(text, str):
            path.write_text(text, encoding="utf-8", newline="")
        else:
            path.write_bytes(text)
        return path

    def require_tool(self, tool: Path = TOOL) -> None:
        self.assertTrue(tool.is_file(), f"state tool unavailable: expected {tool}")

    def run_tool(self, *args: str, tool: Path = TOOL, cwd: Path | None = None) -> ToolResult:
        """Run the tool as a separate process without any test fault configured."""
        environment = {key: value for key, value in os.environ.items()
                       if key != "STATE_TOOL_TEST_FAULT"}
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run([sys.executable, str(tool), *args], capture_output=True,
                                   text=True, cwd=str(cwd or self.base), env=environment,
                                   timeout=30)
        return ToolResult(completed.returncode, completed.stdout, completed.stderr)

    def get(self, *args: str, tool: Path = TOOL, task: Path | str | None = None) -> ToolResult:
        return self.run_tool("get", "--root", str(self.root), "--task",
                             str(self.task if task is None else task), *args, tool=tool)

    def output(self, result: ToolResult) -> dict[str, Any]:
        """Parse stdout as exactly one JSON object carrying schema version 1."""
        try:
            document = json.loads(result.stdout)
        except ValueError:
            self.fail(f"stdout is not exactly one JSON object: {result.stdout!r}; "
                      f"exit {result.code}; stderr: {result.stderr!r}")
        self.assertIsInstance(document, dict, result.stdout)
        self.assertEqual(document.get("schema_version"), 1, result.stdout)
        for key in ("command", "result", "task", "source_revision", "errors", "warnings",
                    "stale_temp_files"):
            self.assertIn(key, document, result.stdout)
        return document

    def read_ok(self, result: ToolResult) -> dict[str, Any]:
        document = self.output(result)
        self.assertEqual(result.code, 0, result.stderr)
        self.assertEqual(document["command"], "get")
        self.assertEqual(document["result"], "read")
        self.assertEqual(document["errors"], [])
        return document

    def refused(self, result: ToolResult, code: int, error: str) -> dict[str, Any]:
        document = self.output(result)
        self.assertEqual(result.code, code, result.stdout)
        self.assertEqual(document["result"], "rejected")
        self.assertIn(error, [item["code"] for item in document["errors"]], result.stdout)
        self.assertTrue(result.stderr.strip(), "every refusal writes a diagnostic on stderr")
        return document

    def block(self, document: dict[str, Any], block_id: str) -> dict[str, Any]:
        matches = [item for item in document["blocks"] if item["block_id"] == block_id]
        self.assertEqual(len(matches), 1, document["blocks"])
        return matches[0]

    @staticmethod
    def field_values(block: dict[str, Any], name: str) -> list[str]:
        return [field["value"] for field in block["fields"] if field["name"] == name]

    @staticmethod
    def header_values(block: dict[str, Any]) -> dict[str, str]:
        return {field["name"]: field["value"] for field in block["header_fields"]}


class GetStructureTests(StateToolCase):
    def test_leaf_and_composite_kinds_reported_and_fenced_lines_ignored(self) -> None:
        self.write_state(state_text(LEAF_T01, COMPOSITE_T02 + "\n" + FENCE, before=FENCE + "\n"))

        first = self.block(self.read_ok(self.get("--block", "T-01")), "T-01")
        second = self.block(self.read_ok(self.get("--block", "T-02")), "T-02")
        everything = self.read_ok(self.get())

        self.assertEqual(first["block_kind"], "leaf")
        self.assertEqual(first["name"], "Progress parser")
        self.assertEqual(self.header_values(first)["atomic-tests"], "green")
        self.assertEqual(self.field_values(first, "last_action"), ["tests pass"])
        self.assertEqual(second["block_kind"], "composite")
        self.assertEqual(second["name"], "Composite parent")
        self.assertEqual(self.field_values(second, "children"), ["T-02a, T-02b"])
        self.assertEqual([item["block_id"] for item in everything["blocks"]], ["T-01", "T-02"])
        self.assertNotIn("fenced", json.dumps(everything))
        self.assertNotIn("Example", json.dumps(everything))

    def test_fields_report_values_continuations_and_known_flags(self) -> None:
        self.write_state(state_text(LEAF_T01))

        block = self.block(self.read_ok(self.get("--block", "T-01")), "T-01")

        self.assertEqual([field["name"] for field in block["fields"]],
                         ["last_action", "target_files", "blocker", "notes", "verification",
                          "branch", "pr"])
        notes = [field for field in block["fields"] if field["name"] == "notes"][0]
        self.assertEqual(notes["value"], '"quoted first note"')
        self.assertEqual([line.strip() for line in notes["continuation"]],
                         ["second line", "", "third line after blank"])
        known = {field["name"]: field["known"] for field in block["fields"]}
        self.assertTrue(known["notes"])
        self.assertTrue(known["pr"])
        self.assertFalse(known["verification"])
        self.assertEqual(block["header_fields"],
                         [{"name": "atomic-tests", "value": "green"},
                          {"name": "atomic-execution", "value": "complete"},
                          {"name": "atomic-validation", "value": "not-started"}])

    def test_repeated_notes_groups_are_separate_entries_in_file_order(self) -> None:
        body = ("  last_action: x\n  target_files:\n  blocker: none\n  notes: first\n"
                "  notes: second\n         second continued\n  notes: third\n")
        self.write_state(state_text(leaf("T-01", body=body)))

        block = self.block(self.read_ok(self.get("--block", "T-01", "--field", "notes")), "T-01")

        self.assertEqual(block["header_fields"], [])
        self.assertEqual(self.field_values(block, "notes"), ["first", "second", "third"])
        self.assertEqual(len(block["fields"]), 3)

    def test_field_filter_selects_a_header_field(self) -> None:
        self.write_state(state_text(LEAF_T01))

        block = self.block(self.read_ok(self.get("--block", "T-01", "--field", "atomic-tests")),
                           "T-01")

        self.assertEqual(block["header_fields"], [{"name": "atomic-tests", "value": "green"}])
        self.assertEqual(block["fields"], [])

    def test_absent_field_gives_empty_header_fields_and_fields(self) -> None:
        self.write_state(state_text(leaf("T-01")))

        block = self.block(self.read_ok(self.get("--block", "T-01", "--field", "pr")), "T-01")

        self.assertEqual(block["header_fields"], [])
        self.assertEqual(block["fields"], [])

    def test_column_zero_foreign_line_ends_block(self) -> None:
        body = "  last_action: x\n  target_files:\n  blocker: none\n  notes:\n"
        foreign = "Foreign column-zero text\n  last_action: stray\n### Aside\n"
        self.write_state(state_text(leaf("T-01", body=body) + foreign, leaf("T-02")))

        document = self.read_ok(self.get())

        self.assertEqual([item["block_id"] for item in document["blocks"]], ["T-01", "T-02"])
        self.assertEqual(self.field_values(self.block(document, "T-01"), "last_action"), ["x"])
        self.assertNotIn("stray", json.dumps(document))

    def test_section_without_blocks_reads_empty_list(self) -> None:
        self.write_state(state_text())

        self.assertEqual(self.read_ok(self.get())["blocks"], [])

    def test_missing_final_newline_is_read(self) -> None:
        text = state_text(leaf("T-01", body="  last_action:\n  target_files:\n  blocker: none\n"
                                            "  notes:\n  pr: none"), after="").removesuffix("\n")
        self.assertFalse(text.endswith("\n"))
        self.write_state(text)

        block = self.block(self.read_ok(self.get("--block", "T-01")), "T-01")

        self.assertEqual(self.field_values(block, "pr"), ["none"])

    def test_fix_task_block_id_is_accepted(self) -> None:
        self.write_state(state_text(leaf("T-01"), leaf("T-01-fix-retry-login")))

        block = self.block(self.read_ok(self.get("--block", "T-01-fix-retry-login")),
                           "T-01-fix-retry-login")

        self.assertEqual(block["block_kind"], "leaf")

    def test_report_names_task_relative_to_root_and_revision_of_bytes(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        expected = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

        document = self.read_ok(self.run_tool("get", "--root", str(self.root), "--task",
                                              TASK_RELATIVE, cwd=self.root))

        self.assertEqual(document["task"], TASK_RELATIVE)
        self.assertEqual(document["source_revision"], expected)
        self.assertEqual(document["stale_temp_files"], [])

    def test_repeated_read_gives_identical_output(self) -> None:
        self.write_state(state_text(LEAF_T01, COMPOSITE_T02))

        first, second = self.get(), self.get()

        self.read_ok(first)
        self.assertEqual(first.stdout, second.stdout)


class ReadOnlyTests(StateToolCase):
    def test_reads_leave_every_file_unchanged_and_create_none(self) -> None:
        self.write_state(state_text(LEAF_T01, COMPOSITE_T02, contract_version="0.9.0"))
        (self.task / "plan.md").write_text("plan\n", encoding="utf-8")
        before = snapshot(self.task)
        variants = (("--block", "T-01"), ("--block", "T-02", "--field", "notes"), (),
                    ("--block", "T-09"), ("--block", "T-1"))

        for arguments in variants:
            with self.subTest(arguments=arguments):
                self.output(self.get(*arguments))
                self.assertEqual(snapshot(self.task), before)
        self.assertFalse((self.task / ".state-tool.lock").exists())

    def test_stale_temporary_files_are_listed_but_never_read_or_deleted(self) -> None:
        self.write_state(state_text(leaf("T-01")))
        stale = ".state.md.0123456789abcdef0123456789abcdef.tmp"
        (self.task / stale).write_text(state_text(leaf("T-01"), leaf("T-09")), encoding="utf-8")
        before = snapshot(self.task)

        document = self.read_ok(self.get())

        self.assertEqual(document["stale_temp_files"], [stale])
        self.assertEqual([item["block_id"] for item in document["blocks"]], ["T-01"])
        self.assertEqual(snapshot(self.task), before)


class PreTddTests(StateToolCase):
    def test_leaf_without_atomic_tests_in_progress_is_applicable(self) -> None:
        self.write_state(state_text(leaf(
            "T-01", header="atomic-execution: in-progress | atomic-validation: not-started")))
        before = snapshot(self.task)

        block = self.block(self.read_ok(self.get("--block", "T-01")), "T-01")

        self.assertEqual(block["pre_tdd_exception"], "applicable")
        self.assertEqual(snapshot(self.task), before)

    def test_leaf_with_atomic_tests_not_started_is_not_applicable(self) -> None:
        self.write_state(state_text(leaf("T-01")))

        block = self.block(self.read_ok(self.get("--block", "T-01")), "T-01")

        self.assertEqual(block["pre_tdd_exception"], "not-applicable")

    def test_leaf_without_atomic_tests_not_started_is_not_applicable(self) -> None:
        self.write_state(state_text(leaf(
            "T-01", header="atomic-execution: not-started | atomic-validation: not-started")))

        block = self.block(self.read_ok(self.get("--block", "T-01")), "T-01")

        self.assertEqual(block["pre_tdd_exception"], "not-applicable")


class InvocationTests(StateToolCase):
    def test_unknown_command_exits_2(self) -> None:
        self.write_state(state_text(leaf("T-01")))

        result = self.run_tool("frobnicate", "--root", str(self.root), "--task", str(self.task))

        document = self.refused(result, 2, "unknown-command")
        self.assertIsNone(document["command"])

    def test_malformed_block_id_exits_2(self) -> None:
        self.write_state(state_text(leaf("T-01")))

        for block_id in ("T-1", "T-01-Fix", "X-01"):
            with self.subTest(block_id=block_id):
                self.refused(self.get("--block", block_id), 2, "invalid-arguments")

    def test_missing_required_option_exits_2(self) -> None:
        self.write_state(state_text(leaf("T-01")))

        self.refused(self.run_tool("get", "--root", str(self.root)), 2, "invalid-arguments")
        self.refused(self.run_tool("get", "--task", str(self.task)), 2, "invalid-arguments")


class WarningTests(StateToolCase):
    def isolated_tool(self, version: str | None) -> Path:
        """Copy the tool into a fresh tree whose VERSION file is the given text or absent."""
        self.require_tool()
        tree = self.base / "tool"
        (tree / "scripts").mkdir(parents=True)
        shutil.copy2(TOOL, tree / "scripts" / "state-tool.py")
        if version is not None:
            (tree / "VERSION").write_text(version + "\n", encoding="utf-8")
        return tree / "scripts" / "state-tool.py"

    def test_unrecognized_prefix_is_read_as_leaf_with_warning(self) -> None:
        self.write_state(state_text(leaf("T-01"), "[x] " + leaf("T-03")))

        document = self.read_ok(self.get("--block", "T-03"))

        block = self.block(document, "T-03")
        self.assertEqual(block["prefix"], "[x]")
        self.assertEqual(block["block_kind"], "leaf")
        self.assertIn("unrecognized-prefix", document["warnings"])

    def test_unknown_header_field_is_reported_with_warning(self) -> None:
        header = ("atomic-tests: red | atomic-foo: x | atomic-execution: in-progress | "
                  "atomic-validation: not-started")
        self.write_state(state_text(leaf("T-04", header=header)))

        document = self.read_ok(self.get("--block", "T-04"))

        self.assertEqual(self.header_values(self.block(document, "T-04"))["atomic-foo"], "x")
        self.assertIn("unknown-header-field", document["warnings"])

    def test_newer_contract_version_warns(self) -> None:
        self.write_state(state_text(leaf("T-01"), contract_version="99.0.0"))

        document = self.read_ok(self.get(tool=self.isolated_tool("1.0.0")))

        self.assertEqual(document["contract_version"], "99.0.0")
        self.assertIn("unsupported-contract-version", document["warnings"])

    def test_contract_version_without_tool_version_warns(self) -> None:
        self.write_state(state_text(leaf("T-01"), contract_version="0.9.0"))

        document = self.read_ok(self.get(tool=self.isolated_tool(None)))

        self.assertIn("unsupported-contract-version", document["warnings"])

    def test_supported_or_absent_contract_version_does_not_warn(self) -> None:
        tool = self.isolated_tool("1.0.0")
        cases = (("0.9.0", "0.9.0"), ("1.0.0", "1.0.0"), (None, None), ("1.0", None))
        for recorded, reported in cases:
            with self.subTest(recorded=recorded):
                self.write_state(state_text(leaf("T-01"), contract_version=recorded))

                document = self.read_ok(self.get(tool=tool))

                self.assertEqual(document["contract_version"], reported)
                self.assertNotIn("unsupported-contract-version", document["warnings"])

    def test_missing_required_fields_warn(self) -> None:
        self.write_state(state_text(leaf("T-01", body="  last_action:\n  blocker: none\n")))

        document = self.read_ok(self.get())

        self.assertIn("required-field-missing", document["warnings"])

    def test_malformed_receipts_line_warns(self) -> None:
        cases = {"over twenty entries": receipts(21),
                 "bad entry": "op-01#0123456789ABCDEF",
                 "repeated id": "op-01#0123456789abcdef, op-01#fedcba9876543210"}
        for label, value in cases.items():
            with self.subTest(case=label):
                body = ("  last_action:\n  target_files:\n  blocker: none\n  notes:\n"
                        f"  state_receipts: {value}\n")
                self.write_state(state_text(leaf("T-01", body=body)))

                document = self.read_ok(self.get("--block", "T-01"))

                self.assertIn("malformed-receipts", document["warnings"])

    def test_twenty_well_formed_receipts_do_not_warn(self) -> None:
        body = ("  last_action:\n  target_files:\n  blocker: none\n  notes:\n"
                f"  state_receipts: {receipts(20)}\n")
        self.write_state(state_text(leaf("T-01", body=body)))

        document = self.read_ok(self.get("--block", "T-01"))

        self.assertNotIn("malformed-receipts", document["warnings"])
        receipts_field = [field for field in self.block(document, "T-01")["fields"]
                          if field["name"] == "state_receipts"][0]
        self.assertTrue(receipts_field["known"])

    def test_well_formed_block_has_no_warnings(self) -> None:
        self.write_state(state_text(LEAF_T01, COMPOSITE_T02))

        self.assertEqual(self.read_ok(self.get())["warnings"], [])


class RefusalTests(StateToolCase):
    def test_duplicate_block_warns_on_other_block_and_rejects_whole_read(self) -> None:
        self.write_state(state_text(leaf("T-01"), leaf("T-02"), leaf("T-02")))

        targeted = self.read_ok(self.get("--block", "T-01"))
        whole = self.refused(self.get(), 3, "block-duplicate")
        duplicated = self.refused(self.get("--block", "T-02"), 3, "block-duplicate")

        self.assertIn("block-duplicate", targeted["warnings"])
        self.assertEqual(self.block(targeted, "T-01")["block_kind"], "leaf")
        self.assertNotIn("blocks", whole)
        self.assertNotIn("blocks", duplicated)

    def test_missing_state_file_exits_3(self) -> None:
        document = self.refused(self.get(), 3, "state-missing")

        self.assertIsNone(document["source_revision"])

    def test_missing_block_exits_3(self) -> None:
        self.write_state(state_text(leaf("T-01")))

        self.refused(self.get("--block", "T-09"), 3, "block-missing")

    def test_missing_or_duplicated_section_exits_3(self) -> None:
        cases = {"empty file": ("", "section-missing"),
                 "no section": ("spec_path: x\n\n## Phases\n- discovery: complete\n",
                                "section-missing"),
                 "two sections": (state_text(leaf("T-01")) + "\n## Subtask Progress\n\n"
                                  + leaf("T-02"), "section-duplicate")}
        for label, (text, error) in cases.items():
            with self.subTest(case=label):
                self.write_state(text)

                self.refused(self.get(), 3, error)

    def test_malformed_lines_make_block_malformed(self) -> None:
        cases = {"tab indented": "  last_action: x\n\tstray\n  target_files:\n  notes:\n",
                 "one space": "  last_action: x\n stray\n  target_files:\n  notes:\n",
                 "two-space non-field": "  last_action: x\n  Not a field\n  target_files:\n"
                                        "  notes:\n",
                 "orphan continuation": "         orphan\n  last_action: x\n  target_files:\n"
                                        "  notes:\n",
                 "repeated known field": "  last_action: x\n  last_action: y\n"
                                         "  target_files:\n  notes:\n"}
        for label, body in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(leaf("T-01", body=body), leaf("T-02")))

                self.refused(self.get("--block", "T-01"), 3, "malformed-block")
                whole = self.refused(self.get(), 3, "malformed-block")
                other = self.read_ok(self.get("--block", "T-02"))

                self.assertNotIn("blocks", whole)
                self.assertIn("malformed-block", other["warnings"])

    def test_repeated_unknown_field_is_preserved_not_malformed(self) -> None:
        body = ("  last_action: x\n  target_files:\n  blocker: none\n  notes:\n"
                "  verification: a\n  verification: b\n")
        self.write_state(state_text(leaf("T-01", body=body)))

        block = self.block(self.read_ok(self.get("--block", "T-01")), "T-01")

        self.assertEqual(self.field_values(block, "verification"), ["a", "b"])

    def test_unsupported_encodings_exit_3(self) -> None:
        text = state_text(leaf("T-01")).encode("utf-8")
        cases = {"byte order mark": b"\xef\xbb\xbf" + text,
                 "carriage return": text.replace(b"\n", b"\r\n"),
                 "invalid utf-8": text.replace(b"Leaf", b"Le\xffaf")}
        for label, content in cases.items():
            with self.subTest(case=label):
                self.write_state(content)

                self.refused(self.get(), 3, "unsupported-encoding")


class PathSafetyTests(StateToolCase):
    def test_symbolic_link_state_file_exits_7(self) -> None:
        (self.task / "real.md").write_text(state_text(leaf("T-01")), encoding="utf-8")
        (self.task / "state.md").symlink_to("real.md")
        before = snapshot(self.task)

        document = self.refused(self.get(), 7, "unsafe-state-file")

        self.assertIsNone(document["source_revision"])
        self.assertEqual(snapshot(self.task), before)

    def test_non_regular_state_file_exits_7(self) -> None:
        (self.task / "state.md").mkdir()

        self.refused(self.get(), 7, "unsafe-state-file")

    def test_task_outside_root_exits_2(self) -> None:
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "state.md").write_text(state_text(leaf("T-01")), encoding="utf-8")
        (self.root / "escape").symlink_to(outside, target_is_directory=True)
        cases = {"sibling directory": outside,
                 "dot-dot escape": self.root / ".." / "outside",
                 "symbolic link leaving root": self.root / "escape"}
        for label, task in cases.items():
            with self.subTest(case=label):
                document = self.refused(self.get(task=task), 2, "path-outside-root")

                self.assertIsNone(document["task"])


class InProcessTests(StateToolCase):
    def run_in_process(self, *args: str, block_fcntl: bool = False,
                       version_info: tuple[int, int, int, str, int] | None = None) -> ToolResult:
        """Run the tool as the main module of this interpreter with optional runtime faults."""
        self.require_tool()
        stdout, stderr = io.StringIO(), io.StringIO()
        saved_argv = sys.argv
        absent = object()
        saved_fcntl = sys.modules.get("fcntl", absent)
        code = 0
        try:
            sys.argv = [str(TOOL), *args]
            if block_fcntl:
                sys.modules["fcntl"] = None  # type: ignore[assignment]
            version = (patch.object(sys, "version_info", version_info)
                       if version_info is not None else contextlib.nullcontext())
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), version:
                try:
                    runpy.run_path(str(TOOL), run_name="__main__")
                except SystemExit as exit_request:
                    request = exit_request.code
                    code = request if isinstance(request, int) else (0 if request is None else 1)
        finally:
            sys.argv = saved_argv
            if saved_fcntl is absent:
                sys.modules.pop("fcntl", None)
            else:
                sys.modules["fcntl"] = saved_fcntl  # type: ignore[assignment]
        return ToolResult(code, stdout.getvalue(), stderr.getvalue())

    def test_get_works_without_fcntl(self) -> None:
        self.write_state(state_text(leaf("T-01")))

        result = self.run_in_process("get", "--root", str(self.root), "--task", str(self.task),
                                     block_fcntl=True)

        self.assertEqual(self.block(self.read_ok(result), "T-01")["block_kind"], "leaf")

    def test_old_python_exits_7_before_file_access(self) -> None:
        self.write_state(state_text(leaf("T-01")))
        before = snapshot(self.task)

        result = self.run_in_process("get", "--root", str(self.root), "--task", str(self.task),
                                     version_info=(3, 10, 12, "final", 0))

        document = self.refused(result, 7, "python-too-old")
        self.assertIsNone(document["source_revision"])
        self.assertEqual(snapshot(self.task), before)


class SourceContractTests(unittest.TestCase):
    def tree(self) -> ast.Module:
        self.assertTrue(TOOL.is_file(), f"state tool unavailable: expected {TOOL}")
        return ast.parse(TOOL.read_text(encoding="utf-8"), filename=str(TOOL))

    def test_imports_are_standard_library_only_and_no_dynamic_execution(self) -> None:
        tree = self.tree()
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    findings.append(f"relative import at line {node.lineno}")
                modules = [node.module or ""]
                if node.module == "os":
                    findings.extend(f"os.{alias.name} at line {node.lineno}" for alias in node.names
                                    if alias.name == "system" or alias.name.startswith("exec"))
            else:
                modules = []
            for module in modules:
                top = module.split(".")[0]
                if top not in sys.stdlib_module_names:
                    findings.append(f"non-standard import {module} at line {node.lineno}")
                if top == "subprocess":
                    findings.append(f"subprocess import at line {node.lineno}")
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id == "os"
                    and (node.attr == "system" or node.attr.startswith("exec"))):
                findings.append(f"os.{node.attr} at line {node.lineno}")
            if isinstance(node, ast.Name) and node.id in {"eval", "exec", "subprocess"}:
                findings.append(f"{node.id} at line {node.lineno}")
            if isinstance(node, ast.keyword) and node.arg == "shell":
                findings.append(f"shell keyword at line {node.value.lineno}")
        self.assertEqual(findings, [])

    def test_version_guard_precedes_every_import_other_than_sys(self) -> None:
        body = self.tree().body
        guard = next((index for index, node in enumerate(body) if isinstance(node, ast.If)
                      and "version_info" in ast.dump(node.test)), None)
        self.assertIsNotNone(guard, "module-level Python version guard is missing")
        assert guard is not None
        self.assertIn("(3, 11)", ast.unparse(body[guard].test))
        early = [ast.unparse(node) for node in body[:guard]
                 if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertTrue(all(statement == "import sys" for statement in early), early)
        self.assertIn("import sys", early)

    def test_vocabulary_constants_equal_anchored_rule_lines(self) -> None:
        anchors = {"ATOMIC_STATUS_VALUES": "Status values for atomic-execution / atomic-validation:",
                   "ATOMIC_TESTS_VALUES": "Status values for `atomic-tests`:",
                   "ROLLUP_VALUES": "Status values for `rollup`:",
                   "INTEGRATION_VALIDATION_VALUES": "Status values for `integration-validation`:"}
        rule_lines = RULES.read_text(encoding="utf-8").splitlines()
        assignments = {target.id: node for node in self.tree().body
                       if isinstance(node, ast.Assign) for target in node.targets
                       if isinstance(target, ast.Name)}
        for name, anchor in anchors.items():
            with self.subTest(constant=name):
                line = next(line for line in rule_lines if line.startswith(anchor))
                expected = tuple(re.findall(r"`([a-z-]+)`", line[len(anchor):]))
                self.assertIn(name, assignments)
                node = assignments[name]
                self.assertEqual(node.lineno, node.end_lineno, f"{name} must be on one line")
                self.assertIsInstance(node.value, ast.Tuple)
                self.assertEqual(ast.literal_eval(node.value), expected)


EM_DASH_JUSTIFICATION = "tdd: none — smoke considered; no executable surface"
HYPHEN_JUSTIFICATION = "tdd: none - smoke considered; no executable surface"
PRE_TDD_NOTE = "pre-TDD task, TDD step skipped"
STALE_TEMP_NAME = ".state.md.0123456789abcdef0123456789abcdef.tmp"


def leaf_statuses(tests: str | None, execution: str = "not-started",
                  validation: str = "not-started") -> str:
    """Return leaf header statuses; tests None omits the atomic-tests segment."""
    segments = [] if tests is None else [f"atomic-tests: {tests}"]
    segments += [f"atomic-execution: {execution}", f"atomic-validation: {validation}"]
    return " | ".join(segments)


def leaf_body(*notes: str, extra: str = "") -> str:
    """Return the required leaf field lines with one notes group per given note."""
    lines = "  last_action:\n  target_files:\n  blocker: none\n"
    lines += "".join(f"  notes: {note}\n" for note in notes) if notes else "  notes:\n"
    return lines + extra


def composite_block(block_id: str, *, rollup: str = "not-started",
                    integration: str = "not-started", body: str | None = None) -> str:
    """Build a composite block, optionally replacing its statuses or body."""
    lines = body if body is not None else "  children: T-09a, T-09b\n  blocker: none\n  notes:\n"
    return (f"[composite] {block_id} | Parent | rollup: {rollup} | "
            f"integration-validation: {integration}\n{lines}")


def copy_tool(directory: Path, version: str | None) -> Path:
    """Copy the tool into a fresh tree whose VERSION file is the given text or absent."""
    (directory / "scripts").mkdir(parents=True)
    shutil.copy2(TOOL, directory / "scripts" / "state-tool.py")
    if version is not None:
        (directory / "VERSION").write_text(version + "\n", encoding="utf-8")
    return directory / "scripts" / "state-tool.py"


class ValidateCase(StateToolCase):
    """Runner and outcome assertions for the validate command."""

    def validate(self, *args: str, tool: Path = TOOL,
                 task: Path | str | None = None) -> ToolResult:
        return self.run_tool("validate", "--root", str(self.root), "--task",
                             str(self.task if task is None else task), *args, tool=tool)

    def valid(self, result: ToolResult) -> dict[str, Any]:
        document = self.output(result)
        self.assertEqual(result.code, 0, result.stdout + result.stderr)
        self.assertEqual(document["command"], "validate")
        self.assertEqual(document["result"], "valid")
        self.assertEqual(document["errors"], [])
        return document

    def invalid(self, result: ToolResult, code: int, *errors: str) -> dict[str, Any]:
        document = self.output(result)
        self.assertEqual(result.code, code, result.stdout + result.stderr)
        self.assertEqual(document["command"], "validate")
        self.assertEqual(document["result"], "invalid")
        codes = [item["code"] for item in document["errors"]]
        for error in errors:
            self.assertIn(error, codes, result.stdout)
        self.assertTrue(result.stderr.strip(), "every invalid result writes a diagnostic on stderr")
        return document


class ValidateOutcomeTests(ValidateCase):
    def test_well_formed_fixture_is_valid_and_leaves_every_file_unchanged(self) -> None:
        path = self.write_state(state_text(LEAF_T01, COMPOSITE_T02, contract_version="0.9.0"))
        (self.task / "plan.md").write_text("plan\n", encoding="utf-8")
        expected_revision = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        before = snapshot(self.task)

        document = self.valid(self.validate())

        self.assertEqual(document["task"], TASK_RELATIVE)
        self.assertEqual(document["source_revision"], expected_revision)
        self.assertEqual(document["warnings"], [])
        self.assertEqual(document["stale_temp_files"], [])
        self.assertEqual(snapshot(self.task), before)
        self.assertFalse((self.task / ".state-tool.lock").exists())

    def test_every_outcome_creates_modifies_and_deletes_nothing(self) -> None:
        self.write_state(state_text(leaf("T-01"), leaf("T-02", header=leaf_statuses(
            "not-started", execution="done"))))
        before = snapshot(self.task)
        variants = ((("--block", "T-01"), 0), ((), 6), (("--block", "T-09"), 3),
                    (("--block", "T-1"), 2))

        for arguments, code in variants:
            with self.subTest(arguments=arguments):
                result = self.validate(*arguments)

                document = self.output(result)
                self.assertEqual(result.code, code, result.stdout)
                self.assertEqual(document["command"], "validate")
                self.assertEqual(snapshot(self.task), before)
        self.assertFalse((self.task / ".state-tool.lock").exists())

    def test_repeated_validation_gives_identical_output(self) -> None:
        self.write_state(state_text(LEAF_T01, leaf("T-03", header=leaf_statuses("passing"))))

        first, second = self.validate(), self.validate()

        self.invalid(first, 6, "invalid-value")
        self.assertEqual(first.stdout, second.stdout)

    def test_leftover_temporary_file_is_listed_and_kept(self) -> None:
        self.write_state(state_text(leaf("T-01")))
        (self.task / STALE_TEMP_NAME).write_text(state_text(leaf("T-01"), leaf("T-01")),
                                                 encoding="utf-8")
        before = snapshot(self.task)

        document = self.valid(self.validate())

        self.assertEqual(document["stale_temp_files"], [STALE_TEMP_NAME])
        self.assertTrue((self.task / STALE_TEMP_NAME).is_file())
        self.assertEqual(snapshot(self.task), before)

    def test_newer_contract_version_is_a_warning_only(self) -> None:
        self.require_tool()
        tool = copy_tool(self.base / "tool", "1.0.0")
        self.write_state(state_text(leaf("T-01"), contract_version="99.0.0"))

        document = self.valid(self.validate(tool=tool))

        self.assertIn("unsupported-contract-version", document["warnings"])

    def test_empty_and_composite_only_sections_are_valid(self) -> None:
        cases = {"empty section": state_text(),
                 "composite only": state_text(composite_block("T-01"), COMPOSITE_T02)}
        for label, text in cases.items():
            with self.subTest(case=label):
                self.write_state(text)

                self.assertEqual(self.valid(self.validate())["warnings"], [])


class ValidateInvariantTests(ValidateCase):
    def test_n_a_requires_em_dash_justification(self) -> None:
        cases = {HYPHEN_JUSTIFICATION: 6, EM_DASH_JUSTIFICATION: 0}
        for note, code in cases.items():
            with self.subTest(note=note):
                self.write_state(state_text(leaf("T-01", header=leaf_statuses("n-a"),
                                                 body=leaf_body(note))))

                result = self.validate()

                if code:
                    self.invalid(result, 6, "n-a-unjustified")
                else:
                    self.valid(result)

    def test_justification_in_a_later_notes_group_or_continuation_line_counts(self) -> None:
        cases = {"later group": leaf_body("first note", "second note", EM_DASH_JUSTIFICATION),
                 "continuation line": leaf_body("first note\n         " + EM_DASH_JUSTIFICATION)}
        for label, body in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(leaf("T-01", header=leaf_statuses("n-a"), body=body)))

                self.valid(self.validate())

    def test_missing_required_fields_per_kind_exit_6(self) -> None:
        cases = {"leaf without notes and target_files":
                     leaf("T-01", body="  last_action:\n  blocker: none\n"),
                 "composite without children":
                     composite_block("T-01", body="  blocker: none\n  notes:\n"),
                 "composite without blocker":
                     composite_block("T-01", body="  children: T-01a\n  notes:\n")}
        for label, block in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(block))

                self.invalid(self.validate(), 6, "required-field-missing")

    def test_completion_requires_green_or_justified_n_a_or_pre_tdd_note(self) -> None:
        cases = {"red": ("red", leaf_body(), 6),
                 "not-started": ("not-started", leaf_body(), 6),
                 "pinned": ("pinned", leaf_body(), 6),
                 "failed": ("failed", leaf_body(), 6),
                 "absent without note": (None, leaf_body(), 6),
                 "green": ("green", leaf_body(), 0),
                 "justified n-a": ("n-a", leaf_body(EM_DASH_JUSTIFICATION), 0),
                 "absent with pre-TDD note": (None, leaf_body(PRE_TDD_NOTE), 0)}
        for label, (tests, body, code) in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(leaf(
                    "T-01", header=leaf_statuses(tests, execution="complete"), body=body)))

                result = self.validate()

                if code:
                    self.invalid(result, 6, "completion-without-tests")
                else:
                    self.valid(result)

    def test_header_status_outside_vocabulary_is_invalid_value(self) -> None:
        cases = {"atomic-tests": leaf("T-01", header=leaf_statuses("passing")),
                 "atomic-execution": leaf("T-01", header=leaf_statuses("red", execution="done")),
                 "atomic-validation": leaf("T-01", header=leaf_statuses(
                     "red", validation="reviewed")),
                 "rollup": composite_block("T-01", rollup="complete"),
                 "integration-validation": composite_block("T-01", integration="done")}
        for label, block in cases.items():
            with self.subTest(field=label):
                self.write_state(state_text(block))

                self.invalid(self.validate(), 6, "invalid-value")

    def test_unknown_header_field_and_unrecognized_prefix_are_warnings_only(self) -> None:
        header = ("atomic-tests: red | atomic-foo: x | atomic-execution: in-progress | "
                  "atomic-validation: not-started")
        self.write_state(state_text(leaf("T-01", header=header), "[x] " + leaf("T-02")))

        document = self.valid(self.validate())

        self.assertIn("unknown-header-field", document["warnings"])
        self.assertIn("unrecognized-prefix", document["warnings"])

    def test_every_invariant_error_of_every_block_is_listed(self) -> None:
        self.write_state(state_text(
            leaf("T-01", header=leaf_statuses("red", execution="done")),
            leaf("T-02", header=leaf_statuses("n-a"), body=leaf_body(HYPHEN_JUSTIFICATION)),
            leaf("T-03", body="  last_action:\n  blocker: none\n")))

        self.invalid(self.validate(), 6, "invalid-value", "n-a-unjustified",
                     "required-field-missing")


class ValidateStructureTests(ValidateCase):
    def test_duplicated_block_exits_3(self) -> None:
        self.write_state(state_text(leaf("T-01"), leaf("T-02"), leaf("T-02")))

        self.invalid(self.validate(), 3, "block-duplicate")

    def test_two_progress_sections_exit_3(self) -> None:
        self.write_state(state_text(leaf("T-01")) + "\n## Subtask Progress\n\n" + leaf("T-02"))

        self.invalid(self.validate(), 3, "section-duplicate")

    def test_missing_state_or_section_exits_3(self) -> None:
        document = self.invalid(self.validate(), 3, "state-missing")
        self.assertIsNone(document["source_revision"])

        self.write_state("spec_path: x\n\n## Phases\n- discovery: complete\n")

        self.invalid(self.validate(), 3, "section-missing")

    def test_malformed_block_exits_3(self) -> None:
        self.write_state(state_text(leaf("T-01", body="  last_action: x\n\tstray\n"
                                                      "  target_files:\n  notes:\n")))

        self.invalid(self.validate(), 3, "malformed-block")

    def test_malformed_receipts_line_exits_3(self) -> None:
        cases = {"over twenty entries": receipts(21),
                 "bad entry": "op-01#0123456789ABCDEF",
                 "repeated id": "op-01#0123456789abcdef, op-01#fedcba9876543210"}
        for label, value in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(leaf("T-01", body=leaf_body(
                    extra=f"  state_receipts: {value}\n"))))

                self.invalid(self.validate(), 3, "malformed-receipts")

    def test_twenty_well_formed_receipts_are_valid(self) -> None:
        self.write_state(state_text(leaf("T-01", body=leaf_body(
            extra=f"  state_receipts: {receipts(20)}\n"))))

        self.valid(self.validate())

    def test_structure_and_invariant_errors_are_both_listed_with_exit_3(self) -> None:
        unjustified = leaf("T-01", header=leaf_statuses("n-a"), body=leaf_body(HYPHEN_JUSTIFICATION))
        cases = {"duplicate block": (
                     state_text(leaf("T-01", header=leaf_statuses("red", execution="done")),
                                leaf("T-02"), leaf("T-02")),
                     ("block-duplicate", "invalid-value")),
                 "malformed receipts": (
                     state_text(unjustified, leaf("T-02", body=leaf_body(
                         extra=f"  state_receipts: {receipts(21)}\n"))),
                     ("malformed-receipts", "n-a-unjustified"))}
        for label, (text, errors) in cases.items():
            with self.subTest(case=label):
                self.write_state(text)

                self.invalid(self.validate(), 3, *errors)

    def test_path_and_file_refusals_keep_exits_2_and_7(self) -> None:
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "state.md").write_text(state_text(leaf("T-01")), encoding="utf-8")

        document = self.invalid(self.validate(task=outside), 2, "path-outside-root")
        self.assertIsNone(document["task"])

        (self.task / "real.md").write_text(state_text(leaf("T-01")), encoding="utf-8")
        (self.task / "state.md").symlink_to("real.md")

        document = self.invalid(self.validate(), 7, "unsafe-state-file")
        self.assertIsNone(document["source_revision"])

    def test_invalid_arguments_exit_2(self) -> None:
        self.write_state(state_text(leaf("T-01")))
        cases = {"field option": self.validate("--field", "notes"),
                 "malformed block id": self.validate("--block", "T-1"),
                 "missing task": self.run_tool("validate", "--root", str(self.root))}
        for label, result in cases.items():
            with self.subTest(case=label):
                self.invalid(result, 2, "invalid-arguments")


class ValidateScopeTests(ValidateCase):
    def test_block_option_ignores_invariant_errors_of_other_blocks(self) -> None:
        self.write_state(state_text(leaf("T-01"), leaf("T-02", header=leaf_statuses(
            "red", execution="complete"))))

        self.valid(self.validate("--block", "T-01"))
        self.invalid(self.validate("--block", "T-02"), 6, "completion-without-tests")

    def test_block_option_ignores_structure_errors_of_other_blocks(self) -> None:
        self.write_state(state_text(leaf("T-01"), leaf("T-02"), leaf("T-02")))

        self.valid(self.validate("--block", "T-01"))
        self.invalid(self.validate("--block", "T-02"), 3, "block-duplicate")

    def test_block_option_refuses_missing_or_structurally_broken_block(self) -> None:
        self.write_state(state_text(
            leaf("T-01", body=leaf_body(extra=f"  state_receipts: {receipts(21)}\n")),
            leaf("T-02", body="  last_action: x\n stray\n  target_files:\n  notes:\n")))

        self.invalid(self.validate("--block", "T-09"), 3, "block-missing")
        self.invalid(self.validate("--block", "T-01"), 3, "malformed-receipts")
        self.invalid(self.validate("--block", "T-02"), 3, "malformed-block")


def fenced_leaf(fence_indent: str, inner: str = "  pr: hidden\n",
                after: str = "  branch: after\n") -> str:
    """Build leaf T-01 whose notes group is followed by a fence pair at the given indentation."""
    return (f"T-01 | Leaf | {leaf_statuses('not-started')}\n"
            "  last_action: x\n  target_files:\n  blocker: none\n  notes: a\n"
            f"{fence_indent}```\n{inner}{fence_indent}```\n{after}")


class BlockGrammarTests(ValidateCase):
    def test_indented_fence_inside_a_block_is_opaque_block_content(self) -> None:
        for indent in (" ", "  ", "   "):
            with self.subTest(indent=len(indent)):
                self.write_state(state_text(fenced_leaf(indent), leaf("T-02")))

                result = self.get("--block", "T-01")

                block = self.block(self.read_ok(result), "T-01")
                self.assertEqual([field["name"] for field in block["fields"]],
                                 ["last_action", "target_files", "blocker", "notes", "branch"])
                self.assertEqual(self.field_values(block, "branch"), ["after"])
                self.assertNotIn("hidden", result.stdout)
                self.assertEqual(self.read_ok(result)["warnings"], [])
                self.valid(self.validate())

    def test_continuation_after_a_closing_fence_belongs_to_the_preceding_field(self) -> None:
        self.write_state(state_text(fenced_leaf("   ", inner="   inner\n",
                                                after="         continued\n")))

        block = self.block(self.read_ok(self.get("--block", "T-01")), "T-01")

        notes = [field for field in block["fields"] if field["name"] == "notes"][0]
        self.assertEqual(notes["value"], "a")
        self.assertEqual([line.strip() for line in notes["continuation"]], ["continued"])
        self.valid(self.validate())

    def test_column_zero_fence_ends_the_block(self) -> None:
        self.write_state(state_text(fenced_leaf(""), leaf("T-02")))

        result = self.get()

        block = self.block(self.read_ok(result), "T-01")
        self.assertEqual([field["name"] for field in block["fields"]],
                         ["last_action", "target_files", "blocker", "notes"])
        self.assertNotIn("hidden", result.stdout)
        self.assertNotIn("after", result.stdout)
        self.valid(self.validate())

    def test_repeated_header_status_segment_makes_the_block_malformed(self) -> None:
        cases = {"atomic-tests": leaf("T-02", header=(
                     "atomic-tests: red | atomic-tests: green | atomic-execution: in-progress | "
                     "atomic-validation: not-started")),
                 "atomic-execution": leaf("T-02", header=(
                     "atomic-tests: red | atomic-execution: in-progress | "
                     "atomic-execution: complete | atomic-validation: not-started")),
                 "rollup": ("[composite] T-02 | Parent | rollup: done | rollup: in-progress | "
                            "integration-validation: not-started\n"
                            "  children: T-02a\n  blocker: none\n  notes:\n")}
        for label, block in cases.items():
            with self.subTest(segment=label):
                self.write_state(state_text(leaf("T-01"), block))

                self.refused(self.get("--block", "T-02"), 3, "malformed-block")
                whole = self.refused(self.get(), 3, "malformed-block")
                other = self.read_ok(self.get("--block", "T-01"))
                self.assertNotIn("blocks", whole)
                self.assertIn("malformed-block", other["warnings"])
                self.invalid(self.validate("--block", "T-02"), 3, "malformed-block")
                self.invalid(self.validate(), 3, "malformed-block")
                self.valid(self.validate("--block", "T-01"))


SPECIFICATION_LABEL = re.compile(r"\b(?:REQ|AC|I|D|A)-[0-9]+\b")


class SourceWordingTests(unittest.TestCase):
    def test_sources_state_rules_without_specification_labels(self) -> None:
        findings = []
        for path in (TOOL, Path(__file__).resolve()):
            self.assertTrue(path.is_file(), f"source unavailable: expected {path}")
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                findings.extend(f"{path.name}:{number}: {label}"
                                for label in SPECIFICATION_LABEL.findall(line))

        self.assertEqual(findings, [])


OPERATION_ID = "op-1"
REFUSAL_SENTENCE = "Do not edit state.md by hand to bypass this refusal."
RECEIPT_ENTRY_TEXT = r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}#[0-9a-f]{16}"
ZERO_REVISION = "sha256:" + "0" * 64
WRITE_KEYS = ("operation_id", "block_id", "block_kind", "result_revision", "changed_fields")

RICH_T01 = """T-01 | Rich leaf | atomic-tests: red | atomic-execution: in-progress | atomic-validation: not-started
  last_action:
  target_files:
  blocker: none
  notes: "quoted first note"
         second line

         third line after an inner blank
  verification: x
Foreign column-zero line after the block
"""


def file_revision(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class SetCase(StateToolCase):
    """Runner and outcome assertions for the set command."""

    def set_fields(self, *fields: str, block: str = "T-01", revision: str | None = None,
                   operation_id: str = OPERATION_ID, task: Path | None = None,
                   tool: Path = TOOL, extra: tuple[str, ...] = ()) -> ToolResult:
        """Run set with one --field per given pair and the current revision by default."""
        task_path = self.task if task is None else task
        if revision is None:
            revision = file_revision(task_path / "state.md")
        arguments = ["set", "--root", str(self.root), "--task", str(task_path), "--block", block,
                     "--expected-revision", revision, "--operation-id", operation_id]
        for item in fields:
            arguments += ["--field", item]
        return self.run_tool(*arguments, *extra, tool=tool)

    def task_copy(self, name: str, text: str) -> Path:
        """Create a second task directory inside the root holding the given state text."""
        directory = self.root / ".ai" / "tasks" / "todo" / name
        directory.mkdir(parents=True)
        (directory / "state.md").write_text(text, encoding="utf-8", newline="")
        return directory

    def state(self, task: Path | None = None) -> str:
        return ((self.task if task is None else task) / "state.md").read_bytes().decode("utf-8")

    def applied(self, result: ToolResult, *changed: str) -> dict[str, Any]:
        document = self.output(result)
        self.assertEqual(result.code, 0, result.stdout + result.stderr)
        self.assertEqual(document["command"], "set")
        self.assertEqual(document["result"], "applied", result.stdout)
        self.assertEqual(document["errors"], [])
        for key in WRITE_KEYS:
            self.assertIn(key, document, result.stdout)
        self.assertEqual(document["changed_fields"], list(changed))
        return document

    def write_refused(self, result: ToolResult, code: int, error: str) -> dict[str, Any]:
        document = self.refused(result, code, error)
        self.assertEqual(document["command"], "set")
        for key in WRITE_KEYS:
            self.assertIn(key, document, result.stdout)
        self.assertEqual(document["changed_fields"], [])
        return document

    def files_without_lock(self, task: Path | None = None) -> Snapshot:
        """Snapshot of the task directory leaving out the lock file a write may create."""
        entries = snapshot(self.task if task is None else task)
        entries.pop(".state-tool.lock", None)
        return entries

    def assert_unchanged_after_refusal(self, before: Snapshot) -> None:
        self.assertEqual(self.files_without_lock(), before)
        self.assertEqual([path.name for path in self.task.glob(".state.md.*.tmp")], [])

    def receipt_line(self, text: str, operation_id: str = OPERATION_ID) -> str:
        """Return the single receipts line of the text; its last entry names the operation."""
        lines = [line for line in text.splitlines(keepends=True)
                 if line.startswith("  state_receipts:")]
        self.assertEqual(len(lines), 1, text)
        self.assertRegex(lines[0], rf"^  state_receipts: (?:{RECEIPT_ENTRY_TEXT}, )*"
                                   rf"{re.escape(operation_id)}#[0-9a-f]{{16}}\n?$")
        return lines[0]


class SetApplyTests(SetCase):
    def test_rich_block_change_touches_only_the_changed_line_and_the_receipt_line(self) -> None:
        original = state_text(RICH_T01, leaf("T-02"), before="Text in another section.\n\n")
        self.write_state(original)
        copy = self.task_copy("task-copy", original)

        first = self.set_fields("last_action=done")
        second = self.set_fields("last_action=done", task=copy)

        self.applied(first, "last_action", "state_receipts")
        self.applied(second, "last_action", "state_receipts")
        result = self.state()
        receipt = self.receipt_line(result)
        expected = original.replace("  last_action:\n", "  last_action: done\n", 1).replace(
            "  verification: x\n", receipt + "  verification: x\n", 1)
        self.assertEqual(result, expected)
        self.assertEqual(self.state(copy), result)
        self.assertEqual(sorted(os.listdir(self.task)), [".state-tool.lock", "state.md"])

    def test_plain_field_change_reports_changed_fields_and_keeps_header_statuses(self) -> None:
        path = self.write_state(state_text(leaf("T-01"), leaf("T-02")))
        source = file_revision(path)
        header = leaf("T-01", body="")

        document = self.applied(self.set_fields("last_action=x"), "last_action", "state_receipts")

        self.assertEqual(document["operation_id"], OPERATION_ID)
        self.assertEqual(document["block_id"], "T-01")
        self.assertEqual(document["block_kind"], "leaf")
        self.assertEqual(document["source_revision"], source)
        self.assertEqual(document["result_revision"], file_revision(path))
        self.assertNotEqual(document["result_revision"], source)
        self.assertIn(header + "  last_action: x\n", self.state())
        block = self.block(self.read_ok(self.get("--block", "T-01")), "T-01")
        self.assertEqual(self.header_values(block), {"atomic-tests": "not-started",
                                                     "atomic-execution": "not-started",
                                                     "atomic-validation": "not-started"})
        self.assertEqual(self.field_values(block, "last_action"), ["x"])

    def test_missing_field_and_header_segment_are_inserted_at_canonical_positions(self) -> None:
        header = "T-01 | Leaf | atomic-execution: not-started | atomic-validation: not-started\n"
        body = "  last_action: x\n  target_files: a.sh\n  notes: n\n"
        original = state_text(header + body, leaf("T-02"))
        self.write_state(original)

        self.applied(self.set_fields("blocker=none", "atomic-tests=red"),
                     "atomic-tests", "blocker", "state_receipts")

        result = self.state()
        receipt = self.receipt_line(result)
        expected = original.replace(header + body, (
            "T-01 | Leaf | atomic-tests: red | atomic-execution: not-started | "
            "atomic-validation: not-started\n"
            "  last_action: x\n  target_files: a.sh\n  blocker: none\n  notes: n\n" + receipt), 1)
        self.assertEqual(result, expected)

    def test_several_fields_change_in_one_replace_and_are_listed_in_order(self) -> None:
        original = state_text(leaf("T-01"))
        self.write_state(original)

        self.applied(self.set_fields("blocker=waiting on review", "last_action=x",
                                     "atomic-validation=in-progress"),
                     "atomic-validation", "last_action", "blocker", "state_receipts")

        result = self.state()
        receipt = self.receipt_line(result)
        expected = (original.replace("atomic-validation: not-started", "atomic-validation: in-progress", 1)
                    .replace("  last_action:\n", "  last_action: x\n", 1)
                    .replace("  blocker: none\n", "  blocker: waiting on review\n", 1)
                    .replace("  notes:\n", "  notes:\n" + receipt, 1))
        self.assertEqual(result, expected)

    def test_composite_status_change_applies_with_the_receipt_after_notes(self) -> None:
        original = state_text(leaf("T-01"), composite_block("T-02"))
        self.write_state(original)

        document = self.applied(self.set_fields("rollup=in-progress", block="T-02"),
                                "rollup", "state_receipts")

        self.assertEqual(document["block_kind"], "composite")
        result = self.state()
        receipt = self.receipt_line(result)
        composite = composite_block("T-02")
        expected = original.replace(composite, composite.replace(
            "rollup: not-started", "rollup: in-progress", 1) + receipt, 1)
        self.assertEqual(result, expected)

    def test_values_equal_to_current_are_unchanged_without_write_or_receipt(self) -> None:
        path = self.write_state(state_text(leaf(
            "T-01", header=leaf_statuses("red", execution="in-progress"),
            body="  last_action: same\n  target_files:\n  blocker: none\n  notes:\n")))
        source = file_revision(path)
        before = self.files_without_lock()

        result = self.set_fields("last_action=same", "atomic-tests=red", "blocker=none")

        document = self.output(result)
        self.assertEqual(result.code, 0, result.stdout + result.stderr)
        self.assertEqual(document["result"], "unchanged")
        self.assertEqual(document["changed_fields"], [])
        self.assertEqual(document["source_revision"], source)
        self.assertEqual(document["result_revision"], source)
        self.assertNotIn("state_receipts", self.state())
        self.assert_unchanged_after_refusal(before)

    def test_missing_final_newline_is_preserved(self) -> None:
        at_block_end = state_text(leaf("T-01", body="  last_action:\n  target_files:\n"
                                                    "  blocker: none\n  notes:\n  pr: none"),
                                  after="").removesuffix("\n")
        elsewhere = state_text(leaf("T-01"), after="## Solution Design\n\nNo final newline")
        for label, original in {"receipt on the last line": at_block_end,
                                "unchanged last line": elsewhere}.items():
            with self.subTest(case=label):
                self.assertFalse(original.endswith("\n"))
                self.write_state(original)

                self.applied(self.set_fields("last_action=x", operation_id=f"op-{len(label)}"),
                             "last_action", "state_receipts")

                result = self.state()
                self.assertFalse(result.endswith("\n"), result[-80:])
                receipt = self.receipt_line(result, operation_id=f"op-{len(label)}")
                changed = original.replace("  last_action:\n", "  last_action: x\n", 1)
                if label == "receipt on the last line":
                    self.assertEqual(result, changed + "\n" + receipt)
                else:
                    self.assertEqual(result, changed.replace("  notes:\n", "  notes:\n" + receipt, 1))


class SetPlacementTests(SetCase):
    def test_missing_field_without_an_earlier_known_field_goes_directly_after_the_header(self) -> None:
        body = "  target_files:\n  blocker: none\n  notes:\n"
        original = state_text(leaf("T-01", body=body))
        self.write_state(original)
        header = leaf("T-01", body="")

        self.applied(self.set_fields("last_action=x"), "last_action", "state_receipts")

        result = self.state()
        receipt = self.receipt_line(result)
        self.assertEqual(result, original.replace(
            header + body, header + "  last_action: x\n" + body + receipt, 1))

    def test_out_of_order_known_fields_and_repeated_unknown_fields_keep_their_places(self) -> None:
        body = ("  target_files:\n  last_action: a\n  verification: one\n  notes: n\n"
                "  verification: two\n")
        original = state_text(leaf("T-01", body=body), leaf("T-02"))
        self.write_state(original)

        self.applied(self.set_fields("last_action=b"), "last_action", "state_receipts")

        result = self.state()
        receipt = self.receipt_line(result)
        self.assertEqual(result, original.replace(body, (
            "  target_files:\n  last_action: b\n  verification: one\n  notes: n\n" + receipt
            + "  verification: two\n"), 1))

    def test_existing_receipts_line_is_extended_in_place(self) -> None:
        existing = "  state_receipts: op-00#0000000000000000\n"
        body = "  last_action:\n  target_files:\n" + existing + "  blocker: none\n  notes:\n"
        original = state_text(leaf("T-01", body=body))
        self.write_state(original)

        self.applied(self.set_fields("last_action=x"), "last_action", "state_receipts")

        result = self.state()
        receipt = self.receipt_line(result)
        self.assertTrue(receipt.startswith("  state_receipts: op-00#0000000000000000, op-1#"),
                        receipt)
        self.assertEqual(result, original.replace("  last_action:\n", "  last_action: x\n", 1)
                         .replace(existing, receipt, 1))

    def test_in_block_fence_is_kept_in_place_and_never_an_insertion_point(self) -> None:
        cases = {"fence after the notes line":
                     (fenced_leaf("   ", after="  verification: x\n"), "  notes: a\n"),
                 "continuation after the closing fence":
                     (fenced_leaf("   ", inner="   inner\n",
                                  after="         continued\n  verification: x\n"),
                      "         continued\n")}
        for label, (block, anchor) in cases.items():
            with self.subTest(case=label):
                original = state_text(block, leaf("T-02"))
                self.write_state(original)

                self.applied(self.set_fields("last_action=y", operation_id=f"op-{len(label)}"),
                             "last_action", "state_receipts")

                result = self.state()
                receipt = self.receipt_line(result, operation_id=f"op-{len(label)}")
                self.assertEqual(result, original.replace("  last_action: x\n", "  last_action: y\n", 1)
                                 .replace(anchor, anchor + receipt, 1))

    def test_receipt_digest_depends_on_inputs_and_not_on_field_order(self) -> None:
        original = state_text(leaf("T-01"))
        self.write_state(original)
        reordered = self.task_copy("task-reordered", original)
        different = self.task_copy("task-different", original)

        self.applied(self.set_fields("last_action=a", "blocker=b"),
                     "last_action", "blocker", "state_receipts")
        self.applied(self.set_fields("blocker=b", "last_action=a", task=reordered),
                     "last_action", "blocker", "state_receipts")
        self.applied(self.set_fields("last_action=a", "blocker=c", task=different),
                     "last_action", "blocker", "state_receipts")

        self.assertEqual(self.state(reordered), self.state())
        self.assertNotEqual(self.receipt_line(self.state(different)),
                            self.receipt_line(self.state()))

    def test_values_are_stored_literally(self) -> None:
        value = 'a=b; $(touch pwned) `id` "quoted" — done, 100%'
        self.write_state(state_text(leaf("T-01")))

        self.applied(self.set_fields("last_action=" + value), "last_action", "state_receipts")

        block = self.block(self.read_ok(self.get("--block", "T-01")), "T-01")
        self.assertEqual(self.field_values(block, "last_action"), [value])
        self.assertIn("  last_action: " + value + "\n", self.state())
        self.assertEqual(list(self.base.rglob("pwned")), [])

    def test_other_duplicated_block_or_pre_existing_invalid_value_does_not_block(self) -> None:
        cases = {"duplicated other block": state_text(leaf("T-01"), leaf("T-02"), leaf("T-02")),
                 "invalid value in an unchanged field": state_text(leaf(
                     "T-01", header=leaf_statuses("not-started", validation="reviewed")))}
        for label, original in cases.items():
            with self.subTest(case=label):
                self.write_state(original)

                self.applied(self.set_fields("last_action=x", operation_id=f"op-{len(label)}"),
                             "last_action", "state_receipts")


class SetRefusalTests(SetCase):
    def test_second_writer_with_the_same_revision_is_refused(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        initial = file_revision(path)
        self.applied(self.set_fields("last_action=first", revision=initial, operation_id="writer-a"),
                     "last_action", "state_receipts")
        after_first = path.read_bytes()
        before = self.files_without_lock()

        result = self.set_fields("blocker=second", revision=initial, operation_id="writer-b")

        document = self.write_refused(result, 4, "revision-conflict")
        self.assertIn(REFUSAL_SENTENCE, result.stderr)
        self.assertEqual(path.read_bytes(), after_first)
        self.assertEqual(document["source_revision"], file_revision(path))
        self.assertEqual(document["result_revision"], file_revision(path))
        self.assert_unchanged_after_refusal(before)

    def test_change_in_another_section_after_the_revision_is_kept_and_refused(self) -> None:
        original = state_text(leaf("T-01"))
        path = self.write_state(original)
        initial = file_revision(path)
        edited = original.replace("Nothing here.", "Edited by another writer.")
        self.write_state(edited)
        before = self.files_without_lock()

        result = self.set_fields("last_action=x", revision=initial)

        self.write_refused(result, 4, "revision-conflict")
        self.assertIn(REFUSAL_SENTENCE, result.stderr)
        self.assertEqual(self.state(), edited)
        self.assert_unchanged_after_refusal(before)

    def test_damaged_structure_refuses_the_write_without_any_change(self) -> None:
        cases = {"two progress sections": (state_text(leaf("T-01")) + "\n## Subtask Progress\n\n"
                                           + leaf("T-02"), "section-duplicate"),
                 "two T-01 headers": (state_text(leaf("T-01"), leaf("T-01")), "block-duplicate"),
                 "tab-indented line": (state_text(leaf("T-01", body=(
                     "  last_action: x\n\tstray\n  target_files:\n  notes:\n"))), "malformed-block"),
                 "repeated header status segment": (state_text(leaf("T-01", header=(
                     "atomic-tests: red | atomic-tests: green | atomic-execution: in-progress | "
                     "atomic-validation: not-started"))), "malformed-block"),
                 "malformed receipts line": (state_text(leaf("T-01", body=leaf_body(
                     extra=f"  state_receipts: {receipts(21)}\n"))), "malformed-receipts"),
                 "missing block": (state_text(leaf("T-02")), "block-missing"),
                 "missing section": ("spec_path: x\n\n## Phases\n- discovery: complete\n",
                                     "section-missing")}
        for label, (text, error) in cases.items():
            with self.subTest(case=label):
                self.write_state(text)
                before = self.files_without_lock()

                self.write_refused(self.set_fields("last_action=y"), 3, error)

                self.assert_unchanged_after_refusal(before)

    def test_missing_state_file_exits_3(self) -> None:
        before = self.files_without_lock()

        document = self.write_refused(self.set_fields("last_action=x", revision=ZERO_REVISION),
                                      3, "state-missing")

        self.assertIsNone(document["source_revision"])
        self.assertIsNone(document["result_revision"])
        self.assert_unchanged_after_refusal(before)

    def test_value_outside_vocabulary_or_content_rules_is_invalid_value(self) -> None:
        cases = {"atomic-execution done": (leaf("T-01"), ("atomic-execution=done",)),
                 "atomic-tests passing": (leaf("T-01"), ("atomic-tests=passing",)),
                 "rollup complete": (composite_block("T-01"), ("rollup=complete",)),
                 "one invalid of several": (leaf("T-01"), ("last_action=x", "atomic-execution=done")),
                 "empty last_action": (leaf("T-01"), ("last_action=",)),
                 "empty blocker": (leaf("T-01"), ("blocker=",)),
                 "line feed": (leaf("T-01"), ("last_action=a\nb",)),
                 "carriage return": (leaf("T-01"), ("last_action=a\rb",))}
        for label, (block, fields) in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(block))
                before = self.files_without_lock()

                result = self.set_fields(*fields)

                self.write_refused(result, 6, "invalid-value")
                self.assertIn(REFUSAL_SENTENCE, result.stderr)
                self.assert_unchanged_after_refusal(before)

    def test_value_with_nul_is_invalid_value(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        before = self.files_without_lock()

        result = InProcessTests.run_in_process(
            self, "set", "--root", str(self.root), "--task", str(self.task), "--block", "T-01",
            "--expected-revision", file_revision(path), "--operation-id", OPERATION_ID,
            "--field", "last_action=a\x00b")

        self.write_refused(result, 6, "invalid-value")
        self.assert_unchanged_after_refusal(before)

    def test_unknown_header_field_and_unrecognized_prefix_refuse_writes(self) -> None:
        unknown = leaf("T-01", header=("atomic-tests: red | atomic-foo: x | "
                                       "atomic-execution: in-progress | atomic-validation: not-started"))
        cases = {"unknown header field": (state_text(unknown), "T-01", "unknown-header-field"),
                 "unrecognized prefix": (state_text(leaf("T-01"), "[x] " + leaf("T-03")), "T-03",
                                         "unrecognized-prefix")}
        for label, (text, block_id, error) in cases.items():
            with self.subTest(case=label):
                self.write_state(text)
                before = self.files_without_lock()

                self.write_refused(self.set_fields("last_action=x", block=block_id), 3, error)

                self.assert_unchanged_after_refusal(before)

    def test_newer_or_uncheckable_contract_version_refuses_writes(self) -> None:
        self.require_tool()
        versioned = copy_tool(self.base / "tool-versioned", "1.0.0")
        unversioned = copy_tool(self.base / "tool-unversioned", None)
        cases = {"newer task version": ("99.0.0", versioned, 3),
                 "tool version missing": ("0.9.0", unversioned, 3),
                 "supported task version": ("0.9.0", versioned, 0)}
        for label, (recorded, tool, code) in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(leaf("T-01"), contract_version=recorded))
                before = self.files_without_lock()

                result = self.set_fields("last_action=x", tool=tool, operation_id=f"op-{len(label)}")

                if code:
                    self.write_refused(result, 3, "unsupported-contract-version")
                    self.assert_unchanged_after_refusal(before)
                else:
                    self.applied(result, "last_action", "state_receipts")

    def test_read_only_and_inapplicable_fields_are_refused(self) -> None:
        leaf_block = leaf("T-01", body=leaf_body(extra="  verification: x\n  pr: none\n"))
        cases = {"git field with its current value": (leaf_block, "pr=none", "read-only-field"),
                 "absent git field": (leaf_block, "branch=feat/x", "read-only-field"),
                 "unknown field": (leaf_block, "verification=y", "read-only-field"),
                 "composite status on a leaf": (leaf_block, "rollup=done", "field-not-applicable"),
                 "last_action on a composite": (composite_block("T-01"), "last_action=x",
                                                "field-not-applicable"),
                 "atomic-tests on a composite": (composite_block("T-01"), "atomic-tests=red",
                                                 "field-not-applicable")}
        for label, (block, pair, error) in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(block))
                before = self.files_without_lock()

                result = self.set_fields(pair)

                self.write_refused(result, 6, error)
                self.assertIn(REFUSAL_SENTENCE, result.stderr)
                self.assert_unchanged_after_refusal(before)

    def test_refusals_with_exit_4_and_6_print_the_no_bypass_sentence(self) -> None:
        path = self.write_state(state_text(leaf("T-01", body=leaf_body(extra="  pr: none\n"))))

        conflict = self.set_fields("last_action=x", revision=ZERO_REVISION)
        read_only = self.set_fields("pr=#1", revision=file_revision(path))

        self.write_refused(conflict, 4, "revision-conflict")
        self.write_refused(read_only, 6, "read-only-field")
        self.assertIn(REFUSAL_SENTENCE, conflict.stderr)
        self.assertIn(REFUSAL_SENTENCE, read_only.stderr)


class SetInvocationTests(SetCase):
    def test_invalid_write_invocations_exit_2_with_one_json_object(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        revision = file_revision(path)
        target = ["set", "--root", str(self.root), "--task", str(self.task)]
        block = ["--block", "T-01"]
        expected = ["--expected-revision", revision]
        operation = ["--operation-id", OPERATION_ID]
        field = ["--field", "last_action=x"]
        cases = {
            "missing operation id": (target + block + expected + field, "invalid-arguments", True),
            "missing expected revision": (target + block + operation + field,
                                          "invalid-arguments", False),
            "missing block": (target + expected + operation + field, "invalid-arguments", False),
            "malformed block id": (target + ["--block", "T-1"] + expected + operation + field,
                                   "invalid-arguments", False),
            "upper-case revision": (target + block + ["--expected-revision", "sha256:" + "A" * 64]
                                    + operation + field, "malformed-revision", False),
            "short revision": (target + block + ["--expected-revision", "sha256:abc"] + operation
                               + field, "malformed-revision", False),
            "operation id with a space": (target + block + expected + ["--operation-id", "op 1"]
                                          + field, "invalid-operation-id", True),
            "operation id too long": (target + block + expected + ["--operation-id", "o" * 65]
                                      + field, "invalid-operation-id", True),
            "field without equals sign": (target + block + expected + operation
                                          + ["--field", "last_action"], "invalid-arguments", False),
            "field named twice": (target + block + expected + operation + field
                                  + ["--field", "last_action=y"], "invalid-arguments", False),
            "wait above range": (target + block + expected + operation + field
                                 + ["--lock-wait-seconds", "601"], "invalid-arguments", False),
            "negative wait": (target + block + expected + operation + field
                              + ["--lock-wait-seconds", "-1"], "invalid-arguments", False),
            "non-integer wait": (target + block + expected + operation + field
                                 + ["--lock-wait-seconds", "1.5"], "invalid-arguments", False)}
        before = snapshot(self.task)
        for label, (arguments, error, operation_unknown) in cases.items():
            with self.subTest(case=label):
                document = self.write_refused(self.run_tool(*arguments), 2, error)

                self.assertIsNone(document["source_revision"])
                self.assertIsNone(document["result_revision"])
                if operation_unknown:
                    self.assertIsNone(document["operation_id"])
                self.assertEqual(snapshot(self.task), before)

    def test_lock_wait_bounds_are_accepted(self) -> None:
        self.write_state(state_text(leaf("T-01")))

        for seconds in ("0", "600"):
            with self.subTest(seconds=seconds):
                result = self.set_fields(f"last_action=wait {seconds}", operation_id=f"op-{seconds}",
                                         extra=("--lock-wait-seconds", seconds))

                self.applied(result, "last_action", "state_receipts")


class SetFileSafetyTests(SetCase):
    def test_lock_file_holds_owner_metadata_with_private_mode(self) -> None:
        self.write_state(state_text(leaf("T-01")))

        self.applied(self.set_fields("last_action=x"), "last_action", "state_receipts")

        lock = self.task / ".state-tool.lock"
        self.assertEqual(stat.S_IMODE(os.lstat(lock).st_mode), 0o600)
        metadata = json.loads(lock.read_text(encoding="utf-8"))
        self.assertEqual(sorted(metadata), ["host", "owner_token", "pid", "started_at"])
        self.assertRegex(metadata["owner_token"], r"^[0-9a-f]{32}$")
        self.assertIsInstance(metadata["pid"], int)
        self.assertGreater(metadata["pid"], 0)
        self.assertIsInstance(metadata["host"], str)
        self.assertRegex(metadata["started_at"],
                         r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(Z|\+00:00)$")

    def test_original_permission_bits_are_kept(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        path.chmod(0o640)

        self.applied(self.set_fields("last_action=x"), "last_action", "state_receipts")

        self.assertEqual(stat.S_IMODE(os.lstat(path).st_mode), 0o640)

    def test_symbolic_link_lock_path_exits_7(self) -> None:
        self.write_state(state_text(leaf("T-01")))
        elsewhere = self.base / "elsewhere.lock"
        (self.task / ".state-tool.lock").symlink_to(elsewhere)
        before = snapshot(self.task)

        self.write_refused(self.set_fields("last_action=x"), 7, "unsafe-lock-path")

        self.assertEqual(snapshot(self.task), before)
        self.assertFalse(elsewhere.exists())

    def test_set_without_fcntl_exits_7_and_touches_nothing(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        before = snapshot(self.task)

        result = InProcessTests.run_in_process(
            self, "set", "--root", str(self.root), "--task", str(self.task), "--block", "T-01",
            "--expected-revision", file_revision(path), "--operation-id", OPERATION_ID,
            "--field", "last_action=x", block_fcntl=True)

        document = self.write_refused(result, 7, "locking-unavailable")
        self.assertIsNone(document["source_revision"])
        self.assertEqual(snapshot(self.task), before)


CONTINUATION = " " * 9


def expected_receipt(command: str, inputs: dict[str, Any], block_id: str = "T-01",
                     operation_id: str = OPERATION_ID) -> str:
    """Receipt entry of an operation: its id, '#' and the first 16 hex digits of SHA-256 over
    the sorted-key compact UTF-8 JSON of command, block id and inputs."""
    payload = json.dumps({"command": command, "block_id": block_id, "inputs": inputs},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"{operation_id}#{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


class NoteAndFileCase(SetCase):
    """Runners and outcome assertions for append-note, add-file and set with notes."""

    def write(self, command: str, *options: str, block: str = "T-01",
              revision: str | None = None, operation_id: str = OPERATION_ID,
              task: Path | None = None) -> ToolResult:
        """Run a write command against the block with the current revision by default."""
        task_path = self.task if task is None else task
        if revision is None:
            revision = file_revision(task_path / "state.md")
        return self.run_tool(command, "--root", str(self.root), "--task", str(task_path),
                             "--block", block, "--expected-revision", revision,
                             "--operation-id", operation_id, *options)

    def append_notes(self, *notes: str, **keywords: Any) -> ToolResult:
        return self.write("append-note", *[part for note in notes for part in ("--note", note)],
                          **keywords)

    def add_files(self, *paths: str, **keywords: Any) -> ToolResult:
        return self.write("add-file", *[part for path in paths for part in ("--path", path)],
                          **keywords)

    def write_applied(self, result: ToolResult, command: str, *changed: str) -> dict[str, Any]:
        document = self.output(result)
        self.assertEqual(result.code, 0, result.stdout + result.stderr)
        self.assertEqual(document["command"], command)
        self.assertEqual(document["result"], "applied", result.stdout)
        self.assertEqual(document["errors"], [])
        for key in WRITE_KEYS:
            self.assertIn(key, document, result.stdout)
        self.assertEqual(document["changed_fields"], list(changed))
        return document

    def refused_by(self, result: ToolResult, command: str, code: int, error: str) -> dict[str, Any]:
        document = self.refused(result, code, error)
        self.assertEqual(document["command"], command)
        for key in WRITE_KEYS:
            self.assertIn(key, document, result.stdout)
        self.assertEqual(document["changed_fields"], [])
        return document

    def notes_fields(self, block_id: str = "T-01") -> list[dict[str, Any]]:
        block = self.block(self.read_ok(self.get("--block", block_id)), block_id)
        return [item for item in block["fields"] if item["name"] == "notes"]


class AppendNotePlacementTests(NoteAndFileCase):
    def test_first_note_goes_on_an_empty_notes_line_and_further_notes_follow_as_continuations(
            self) -> None:
        original = state_text(leaf("T-01"), leaf("T-02"))
        self.write_state(original)

        document = self.write_applied(self.append_notes("a", "b"), "append-note",
                                      "notes", "state_receipts")

        result = self.state()
        receipt = self.receipt_line(result)
        self.assertEqual(result, original.replace(
            "  notes:\n", "  notes: a\n" + CONTINUATION + "b\n" + receipt, 1))
        self.assertEqual(document["block_kind"], "leaf")
        self.assertEqual(document["result_revision"], file_revision(self.task / "state.md"))
        self.assertEqual([(item["value"], item["continuation"]) for item in self.notes_fields()],
                         [("a", [CONTINUATION + "b"])])

    def test_note_after_continuation_lines_follows_the_last_continuation_line(self) -> None:
        original = state_text(RICH_T01, leaf("T-02"))
        self.write_state(original)
        last = "         third line after an inner blank\n"

        self.write_applied(self.append_notes("fourth note"), "append-note", "notes", "state_receipts")

        result = self.state()
        receipt = self.receipt_line(result)
        self.assertEqual(result, original.replace(
            last, last + CONTINUATION + "fourth note\n" + receipt, 1))

    def test_note_follows_the_last_line_of_the_last_notes_group(self) -> None:
        head = "  last_action: x\n  target_files: a.sh\n  blocker: none\n"
        tail = "  branch: feat/x\n  pr: none\n"
        four_groups = ("  notes: first group\n  notes: second group\n         second continued\n"
                       "  notes: third group\n  notes: fourth group\n         fourth continued\n"
                       "\n         fourth after an inner blank\n")
        cases = {"four notes groups": four_groups,
                 "two groups, the last one empty": "  notes: x\n  notes:\n",
                 "empty notes line with a continuation line": "  notes:\n         x\n"}
        for label, notes in cases.items():
            with self.subTest(case=label):
                block = leaf("T-01", body=head + notes + tail)
                original = state_text(block, leaf("T-02"))
                self.write_state(original)
                operation_id = f"op-{len(label)}"

                self.write_applied(self.append_notes("added", operation_id=operation_id),
                                   "append-note", "notes", "state_receipts")

                result = self.state()
                receipt = self.receipt_line(result, operation_id=operation_id)
                expected = leaf("T-01", body=head + notes + CONTINUATION + "added\n" + tail + receipt)
                self.assertEqual(result, original.replace(block, expected, 1))

    def test_note_is_never_placed_after_an_in_block_fence(self) -> None:
        cases = {"fence after the notes line":
                     (fenced_leaf("   ", after="  verification: x\n"), "  notes: a\n"),
                 "continuation after the closing fence":
                     (fenced_leaf("   ", inner="   inner\n",
                                  after="         continued\n  verification: x\n"),
                      "         continued\n")}
        for label, (block, anchor) in cases.items():
            with self.subTest(case=label):
                original = state_text(block, leaf("T-02"))
                self.write_state(original)
                operation_id = f"op-{len(label)}"

                self.write_applied(self.append_notes("b", operation_id=operation_id),
                                   "append-note", "notes", "state_receipts")

                result = self.state()
                receipt = self.receipt_line(result, operation_id=operation_id)
                self.assertEqual(result, original.replace(
                    anchor, anchor + CONTINUATION + "b\n" + receipt, 1))

    def test_missing_notes_line_is_inserted_after_the_blocker_group(self) -> None:
        body = "  last_action: x\n  blocker: none\n  branch: feat/x\n"
        cases = {"one note": (("a",), "  notes: a\n"),
                 "two notes": (("a", "b"), "  notes: a\n" + CONTINUATION + "b\n")}
        for label, (notes, inserted) in cases.items():
            with self.subTest(case=label):
                block = leaf("T-01", body=body)
                original = state_text(block, leaf("T-02"))
                self.write_state(original)
                operation_id = f"op-{len(label)}"

                self.write_applied(self.append_notes(*notes, operation_id=operation_id),
                                   "append-note", "notes", "state_receipts")

                result = self.state()
                receipt = self.receipt_line(result, operation_id=operation_id)
                self.assertEqual(result, original.replace(block, leaf("T-01", body=(
                    "  last_action: x\n  blocker: none\n" + inserted + "  branch: feat/x\n"
                    + receipt)), 1))

    def test_note_appended_to_the_last_line_keeps_the_missing_final_newline(self) -> None:
        original = state_text(leaf("T-01", body=leaf_body("x")), after="").rstrip("\n")
        self.assertFalse(original.endswith("\n"))
        self.write_state(original)

        self.write_applied(self.append_notes("y"), "append-note", "notes", "state_receipts")

        result = self.state()
        self.assertFalse(result.endswith("\n"), result[-80:])
        receipt = self.receipt_line(result)
        self.assertEqual(result, original + "\n" + CONTINUATION + "y\n" + receipt)

    def test_append_note_applies_to_a_composite_block(self) -> None:
        composite = composite_block("T-02")
        original = state_text(leaf("T-01"), composite)
        self.write_state(original)

        document = self.write_applied(self.append_notes("n", block="T-02"), "append-note",
                                      "notes", "state_receipts")

        self.assertEqual(document["block_kind"], "composite")
        result = self.state()
        receipt = self.receipt_line(result)
        self.assertEqual(result, original.replace(composite, composite.replace(
            "  notes:\n", "  notes: n\n" + receipt, 1), 1))


class NoteTextTests(NoteAndFileCase):
    def test_invalid_note_text_writes_no_note_of_the_call(self) -> None:
        cases = {"line feed after a valid note": ("append-note", ("--note", "ok", "--note", "a\nb")),
                 "carriage return": ("append-note", ("--note", "a\rb")),
                 "line feed in a set note": ("set", ("--field", "last_action=x", "--note", "a\nb")),
                 "valid note with an invalid field": ("set", ("--field", "atomic-execution=done",
                                                              "--note", "y"))}
        for label, (command, options) in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(leaf("T-01")))
                before = self.files_without_lock()

                result = self.write(command, *options)

                self.refused_by(result, command, 6, "invalid-value")
                self.assertIn(REFUSAL_SENTENCE, result.stderr)
                self.assert_unchanged_after_refusal(before)

    def test_note_with_nul_is_invalid_value(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        before = self.files_without_lock()

        result = InProcessTests.run_in_process(
            self, "append-note", "--root", str(self.root), "--task", str(self.task),
            "--block", "T-01", "--expected-revision", file_revision(path),
            "--operation-id", OPERATION_ID, "--note", "fine", "--note", "a\x00b")

        self.refused_by(result, "append-note", 6, "invalid-value")
        self.assert_unchanged_after_refusal(before)

    def test_note_and_path_with_shell_metacharacters_are_stored_literally(self) -> None:
        note = "$(touch pwned); rm -rf x"
        path = "$(touch pwned-path)/a `id` b.sh"
        self.write_state(state_text(leaf("T-01")))
        keep = self.base / "x"
        keep.write_text("keep\n", encoding="utf-8")

        self.write_applied(self.append_notes(note), "append-note", "notes", "state_receipts")
        self.write_applied(self.add_files(path, operation_id="op-2"), "add-file",
                           "target_files", "state_receipts")

        self.assertIn("  notes: " + note + "\n", self.state())
        self.assertIn("  target_files: " + path + "\n", self.state())
        self.assertEqual([item["value"] for item in self.notes_fields()], [note])
        self.assertEqual(list(self.base.rglob("pwned*")), [])
        self.assertTrue(keep.is_file())


class SetNoteTests(NoteAndFileCase):
    def test_set_with_a_field_and_a_note_applies_both_in_one_revision(self) -> None:
        original = state_text(leaf("T-01"), leaf("T-02"))
        path = self.write_state(original)
        source = file_revision(path)

        document = self.applied(self.set_fields("last_action=x", extra=("--note", "y")),
                                "last_action", "notes", "state_receipts")

        result = self.state()
        receipt = self.receipt_line(result)
        self.assertRegex(receipt, rf"^  state_receipts: {OPERATION_ID}#[0-9a-f]{{16}}\n$")
        self.assertEqual(result, original.replace("  last_action:\n", "  last_action: x\n", 1)
                         .replace("  notes:\n", "  notes: y\n" + receipt, 1))
        self.assertEqual(document["source_revision"], source)
        self.assertEqual(document["result_revision"], file_revision(path))

    def test_set_with_an_unchanged_field_still_appends_its_notes(self) -> None:
        original = state_text(leaf("T-01"))
        self.write_state(original)

        self.applied(self.set_fields("blocker=none", extra=("--note", "a", "--note", "b")),
                     "notes", "state_receipts")

        result = self.state()
        receipt = self.receipt_line(result)
        self.assertEqual(result, original.replace(
            "  notes:\n", "  notes: a\n" + CONTINUATION + "b\n" + receipt, 1))


class AddFileTests(NoteAndFileCase):
    def test_new_paths_are_appended_once_in_argument_order(self) -> None:
        body = "  last_action:\n  target_files: a.sh\n  blocker: none\n  notes:\n"
        original = state_text(leaf("T-01", body=body))
        cases = {"new and listed path": (("b.sh", "a.sh"), "a.sh, b.sh"),
                 "repeated new path": (("c.sh", "c.sh"), "a.sh, c.sh"),
                 "several new paths": (("d.sh", "b.sh", "d.sh"), "a.sh, d.sh, b.sh")}
        for label, (paths, value) in cases.items():
            with self.subTest(case=label):
                self.write_state(original)

                self.write_applied(self.add_files(*paths), "add-file", "target_files",
                                   "state_receipts")

                result = self.state()
                receipt = self.receipt_line(result)
                self.assertEqual(result, original.replace(
                    "  target_files: a.sh\n", f"  target_files: {value}\n", 1)
                    .replace("  notes:\n", "  notes:\n" + receipt, 1))

    def test_already_listed_paths_give_unchanged_without_write_or_receipt(self) -> None:
        body = "  last_action:\n  target_files: a.sh, docs/my guide.md\n  blocker: none\n  notes:\n"
        for paths in (("a.sh",), ("docs/my guide.md", "a.sh", "a.sh")):
            with self.subTest(paths=paths):
                path = self.write_state(state_text(leaf("T-01", body=body)))
                source = file_revision(path)
                before = self.files_without_lock()

                result = self.add_files(*paths)

                document = self.output(result)
                self.assertEqual(result.code, 0, result.stdout + result.stderr)
                self.assertEqual(document["command"], "add-file")
                self.assertEqual(document["result"], "unchanged")
                self.assertEqual(document["changed_fields"], [])
                self.assertEqual(document["source_revision"], source)
                self.assertEqual(document["result_revision"], source)
                self.assert_unchanged_after_refusal(before)

    def test_existing_entries_are_compared_whole_and_an_empty_value_has_none(self) -> None:
        cases = {"empty value": ("  target_files:\n", ("b.sh",), "  target_files: b.sh\n"),
                 "entries with spaces and prose": (
                     "  target_files: scripts/a.sh (new), docs/my guide.md\n",
                     ("docs/my guide.md", "scripts/a.sh"),
                     "  target_files: scripts/a.sh (new), docs/my guide.md, scripts/a.sh\n")}
        for label, (line, paths, expected) in cases.items():
            with self.subTest(case=label):
                original = state_text(leaf("T-01", body="  last_action:\n" + line
                                           + "  blocker: none\n  notes:\n"))
                self.write_state(original)
                operation_id = f"op-{len(label)}"

                self.write_applied(self.add_files(*paths, operation_id=operation_id), "add-file",
                                   "target_files", "state_receipts")

                result = self.state()
                receipt = self.receipt_line(result, operation_id=operation_id)
                self.assertEqual(result, original.replace(line, expected, 1)
                                 .replace("  notes:\n", "  notes:\n" + receipt, 1))

    def test_missing_target_files_line_is_inserted_after_the_last_action_group(self) -> None:
        body = "  last_action: x\n  blocker: none\n  branch: feat/x\n"
        block = leaf("T-01", body=body)
        original = state_text(block, leaf("T-02"))
        self.write_state(original)

        self.write_applied(self.add_files("b.sh"), "add-file", "target_files", "state_receipts")

        result = self.state()
        receipt = self.receipt_line(result)
        self.assertEqual(result, original.replace(block, leaf("T-01", body=(
            "  last_action: x\n  target_files: b.sh\n  blocker: none\n  branch: feat/x\n"
            + receipt)), 1))

    def test_invalid_paths_exit_6_invalid_path(self) -> None:
        cases = {"absolute": ("/abs",), "parent segment": ("../x",), "comma": ("a,b",),
                 "empty": ("",), "leading dot slash": ("./a.sh",), "trailing slash": ("a/",),
                 "inner parent segment": ("a/../b.sh",), "final parent segment": ("a/..",),
                 "valid path before an invalid one": ("ok.sh", "/abs")}
        for label, paths in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(leaf("T-01")))
                before = self.files_without_lock()

                result = self.add_files(*paths)

                self.refused_by(result, "add-file", 6, "invalid-path")
                self.assertIn(REFUSAL_SENTENCE, result.stderr)
                self.assert_unchanged_after_refusal(before)

    def test_add_file_on_a_composite_block_is_not_applicable(self) -> None:
        self.write_state(state_text(leaf("T-01"), composite_block("T-02")))
        before = self.files_without_lock()

        result = self.add_files("a.sh", block="T-02")

        self.refused_by(result, "add-file", 6, "field-not-applicable")
        self.assert_unchanged_after_refusal(before)


class NoteAndFileTransactionTests(NoteAndFileCase):
    def test_receipt_digest_covers_notes_and_paths_in_argument_order(self) -> None:
        original = state_text(leaf("T-01"))
        cases = {"append-note": (("--note", "b", "--note", "a"), {"notes": ["b", "a"]}),
                 "add-file": (("--path", "c.sh", "--path", "c.sh"), {"paths": ["c.sh", "c.sh"]}),
                 "set": (("--field", "last_action=x", "--note", "y", "--note", "z"),
                         {"fields": [["last_action", "x"]], "notes": ["y", "z"]})}
        for command, (options, inputs) in cases.items():
            with self.subTest(command=command):
                task = self.task_copy(f"task-{command}", original)

                result = self.write(command, *options, task=task)

                self.assertEqual(result.code, 0, result.stdout + result.stderr)
                self.assertEqual(self.output(result)["result"], "applied")
                self.assertEqual(self.receipt_line(self.state(task)),
                                 f"  state_receipts: {expected_receipt(command, inputs)}\n")

    def test_stale_revision_is_refused_with_the_no_bypass_sentence(self) -> None:
        self.write_state(state_text(leaf("T-01")))
        before = self.files_without_lock()

        for command, options in {"append-note": ("--note", "a"),
                                 "add-file": ("--path", "a.sh")}.items():
            with self.subTest(command=command):
                result = self.write(command, *options, revision=ZERO_REVISION)

                self.refused_by(result, command, 4, "revision-conflict")
                self.assertIn(REFUSAL_SENTENCE, result.stderr)
                self.assert_unchanged_after_refusal(before)

    def test_invalid_note_and_file_invocations_exit_2(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        target = ["--root", str(self.root), "--task", str(self.task), "--block", "T-01"]
        expected = ["--expected-revision", file_revision(path)]
        operation = ["--operation-id", OPERATION_ID]
        cases = {
            "append-note without a note": ("append-note", target + expected + operation,
                                           "invalid-arguments"),
            "add-file without a path": ("add-file", target + expected + operation,
                                        "invalid-arguments"),
            "append-note with a field": ("append-note", target + expected + operation
                                         + ["--note", "a", "--field", "last_action=x"],
                                         "invalid-arguments"),
            "add-file with a note": ("add-file", target + expected + operation
                                     + ["--path", "a.sh", "--note", "a"], "invalid-arguments"),
            "append-note without an operation id": ("append-note", target + expected
                                                    + ["--note", "a"], "invalid-arguments"),
            "add-file with a malformed revision": ("add-file", target
                                                   + ["--expected-revision", "sha256:abc"]
                                                   + operation + ["--path", "a.sh"],
                                                   "malformed-revision")}
        before = snapshot(self.task)
        for label, (command, arguments, error) in cases.items():
            with self.subTest(case=label):
                document = self.refused_by(self.run_tool(command, *arguments), command, 2, error)

                self.assertIsNone(document["source_revision"])
                self.assertIsNone(document["result_revision"])
                self.assertEqual(snapshot(self.task), before)


class EmptyNoteTests(NoteAndFileCase):
    def test_empty_note_is_invalid_value_and_the_call_writes_nothing(self) -> None:
        cases = {"append-note with only an empty note": ("append-note", ("--note", "")),
                 "append-note with a valid and an empty note": ("append-note",
                                                               ("--note", "a", "--note", "")),
                 "set with a changed field and an empty note": ("set", ("--field", "last_action=x",
                                                                        "--note", "")),
                 "set with an unchanged field and an empty note": ("set", ("--field", "blocker=none",
                                                                           "--note", ""))}
        for label, (command, options) in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(leaf("T-01")))
                before = self.files_without_lock()

                result = self.write(command, *options)

                self.refused_by(result, command, 6, "invalid-value")
                self.assertIn(REFUSAL_SENTENCE, result.stderr)
                self.assert_unchanged_after_refusal(before)

    def test_notes_line_with_a_whitespace_value_is_kept_and_followed_by_the_note(self) -> None:
        cases = {"colon and one space is empty": ("  notes: \n", "  notes: a\n"),
                 "two-space value is not empty": ("  notes:   \n",
                                                  "  notes:   \n" + CONTINUATION + "a\n")}
        for label, (line, written) in cases.items():
            with self.subTest(case=label):
                original = state_text(leaf("T-01", body="  last_action:\n  target_files:\n"
                                                        "  blocker: none\n" + line))
                self.write_state(original)
                operation_id = f"op-{len(label)}"

                self.write_applied(self.append_notes("a", operation_id=operation_id),
                                   "append-note", "notes", "state_receipts")

                result = self.state()
                receipt = self.receipt_line(result, operation_id=operation_id)
                self.assertEqual(result, original.replace(line, written + receipt, 1))


if __name__ == "__main__":
    unittest.main()
