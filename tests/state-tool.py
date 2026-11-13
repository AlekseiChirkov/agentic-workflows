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


if __name__ == "__main__":
    unittest.main()
