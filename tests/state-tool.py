"""Acceptance suite for the subtask-progress state tool, using disposable task fixtures."""
from __future__ import annotations

import ast
import contextlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import select
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
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


def status_leaf(tests: str | None, execution: str = "not-started", *notes: str,
                validation: str = "not-started") -> str:
    """Build leaf T-01 with the given statuses and one notes group per given note."""
    return leaf("T-01", header=leaf_statuses(tests, execution, validation), body=leaf_body(*notes))


Outcome = str | tuple[str, ...]


class LifecycleCase(NoteAndFileCase):
    """Runs set with fields and notes against a fresh fixture and checks the named outcome:
    an error code means exit 6 with nothing changed; a tuple names the changed fields."""

    def set_with(self, *fields: str, notes: tuple[str, ...] = ()) -> ToolResult:
        return self.set_fields(*fields, extra=tuple(part for note in notes
                                                    for part in ("--note", note)))

    def check_set(self, block_text: str, fields: tuple[str, ...], notes: tuple[str, ...],
                  expected: Outcome) -> dict[str, Any]:
        self.write_state(state_text(block_text, leaf("T-02")))
        before = self.files_without_lock()

        result = self.set_with(*fields, notes=notes)

        if isinstance(expected, str):
            document = self.write_refused(result, 6, expected)
            self.assertIn(REFUSAL_SENTENCE, result.stderr)
            self.assert_unchanged_after_refusal(before)
            return document
        return self.applied(result, *expected)

    def header_after(self, block_id: str = "T-01") -> dict[str, str]:
        return self.header_values(self.block(self.read_ok(self.get("--block", block_id)), block_id))

    def validate_codes(self) -> tuple[int, list[str]]:
        result = self.run_tool("validate", "--root", str(self.root), "--task", str(self.task))
        return result.code, [item["code"] for item in self.output(result)["errors"]]


class TestsStatusTransitionTests(LifecycleCase):
    def test_downgrade_and_pinned_rules_refuse_only_their_moves(self) -> None:
        tests_changed = ("atomic-tests", "state_receipts")
        cases: dict[str, tuple[str, tuple[str, ...], tuple[str, ...], Outcome]] = {
            "pinned to red": (status_leaf("pinned"), ("atomic-tests=red",), (),
                              "pinned-transition"),
            "pinned to failed": (status_leaf("pinned"), ("atomic-tests=failed",), (),
                                 "pinned-transition"),
            "pinned to justified n-a": (status_leaf("pinned"), ("atomic-tests=n-a",),
                                        (EM_DASH_JUSTIFICATION,), "pinned-transition"),
            "green to red": (status_leaf("green"), ("atomic-tests=red",), (), "downgrade"),
            "green to justified n-a": (status_leaf("green"), ("atomic-tests=n-a",),
                                       (EM_DASH_JUSTIFICATION,), "downgrade"),
            "red to not-started": (status_leaf("red"), ("atomic-tests=not-started",), (),
                                   "downgrade"),
            "failed to not-started": (status_leaf("failed"), ("atomic-tests=not-started",), (),
                                      "downgrade"),
            "pinned to green": (status_leaf("pinned"), ("atomic-tests=green",), (), tests_changed),
            "not-started to red": (status_leaf("not-started"), ("atomic-tests=red",), (),
                                   tests_changed),
            "failed to red inside the middle rank": (status_leaf("failed"), ("atomic-tests=red",),
                                                     (), tests_changed),
            "red to failed inside the middle rank": (status_leaf("red"), ("atomic-tests=failed",),
                                                     (), tests_changed),
            "red to justified n-a inside the middle rank": (
                status_leaf("red"), ("atomic-tests=n-a",), (EM_DASH_JUSTIFICATION,),
                ("atomic-tests", "notes", "state_receipts")),
            "validation status moved back": (
                status_leaf("green", "complete", validation="complete"),
                ("atomic-validation=not-started",), (), ("atomic-validation", "state_receipts")),
        }
        for label, (block_text, fields, notes, expected) in cases.items():
            with self.subTest(case=label):
                self.check_set(block_text, fields, notes, expected)
                if not isinstance(expected, str):
                    name, value = fields[0].split("=", 1)
                    self.assertEqual(self.header_after()[name], value)

    def test_composite_statuses_are_checked_by_vocabulary_only(self) -> None:
        cases = {"rollup moved back": (composite_block("T-01", rollup="done"), "rollup=not-started",
                                       ("rollup", "state_receipts")),
                 "integration validation moved back": (
                     composite_block("T-01", integration="complete"),
                     "integration-validation=not-started",
                     ("integration-validation", "state_receipts")),
                 "pinned leaf beside it moved to red": (status_leaf("pinned"), "atomic-tests=red",
                                                        "pinned-transition")}
        for label, (block_text, pair, expected) in cases.items():
            with self.subTest(case=label):
                self.check_set(block_text, (pair,), (), expected)

    def test_green_is_reached_only_from_red_or_pinned(self) -> None:
        cases: dict[str, tuple[str, Outcome]] = {
            "from justified n-a": (status_leaf("n-a", "not-started", EM_DASH_JUSTIFICATION),
                                   "invalid-transition"),
            "from failed": (status_leaf("failed"), "invalid-transition"),
            "from not-started": (status_leaf("not-started"), "invalid-transition"),
            "from an absent tests status": (status_leaf(None, "in-progress"), "invalid-transition"),
            "from red": (status_leaf("red", "in-progress"), ("atomic-tests", "state_receipts"))}
        for label, (block_text, expected) in cases.items():
            with self.subTest(case=label):
                self.check_set(block_text, ("atomic-tests=green",), (), expected)

    def test_n_a_needs_the_justification_in_the_notes_of_the_result(self) -> None:
        later_group = leaf_body("first note", EM_DASH_JUSTIFICATION)
        continuation = leaf_body("first note", extra=CONTINUATION + EM_DASH_JUSTIFICATION + "\n")
        cases: dict[str, tuple[str, tuple[str, ...], Outcome]] = {
            "no note": (status_leaf("not-started"), (), "n-a-unjustified"),
            "hyphen instead of the dash": (status_leaf("not-started", "not-started",
                                                       HYPHEN_JUSTIFICATION),
                                           (), "n-a-unjustified"),
            "note of the same call": (status_leaf("not-started"), (EM_DASH_JUSTIFICATION,),
                                      ("atomic-tests", "notes", "state_receipts")),
            "justification in a later notes group": (
                leaf("T-01", header=leaf_statuses("not-started"), body=later_group), (),
                ("atomic-tests", "state_receipts")),
            "justification on a continuation line": (
                leaf("T-01", header=leaf_statuses("not-started"), body=continuation), (),
                ("atomic-tests", "state_receipts"))}
        for label, (block_text, notes, expected) in cases.items():
            with self.subTest(case=label):
                self.check_set(block_text, ("atomic-tests=n-a",), notes, expected)
                if not isinstance(expected, str):
                    self.assertEqual(self.header_after()["atomic-tests"], "n-a")


class CompletionAndStartTests(LifecycleCase):
    def test_completion_needs_green_or_justified_tests_or_the_pre_tdd_note(self) -> None:
        execution_changed = ("atomic-execution", "state_receipts")
        cases: dict[str, tuple[str, tuple[str, ...], tuple[str, ...], Outcome]] = {
            "tests not started":(status_leaf("not-started", "in-progress"), (), (),
                                  "completion-without-tests"),
            "tests red": (status_leaf("red", "in-progress"), (), (), "completion-without-tests"),
            "tests failed": (status_leaf("failed", "in-progress"), (), (),
                             "completion-without-tests"),
            "pre-TDD note but previous execution blocked": (
                status_leaf(None, "blocked", PRE_TDD_NOTE), (), (), "completion-without-tests"),
            "pre-TDD note already recorded": (status_leaf(None, "in-progress", PRE_TDD_NOTE), (),
                                              (), execution_changed),
            "tests green": (status_leaf("green", "in-progress"), (), (), execution_changed),
            "tests justified n-a": (status_leaf("n-a", "in-progress", EM_DASH_JUSTIFICATION), (),
                                    (), execution_changed),
            "tests turned green by the same call": (
                status_leaf("red", "in-progress"), ("atomic-tests=green",), (),
                ("atomic-tests", "atomic-execution", "state_receipts"))}
        for label, (block_text, more, notes, expected) in cases.items():
            with self.subTest(case=label):
                self.check_set(block_text, ("atomic-execution=complete",) + more, notes, expected)
                if not isinstance(expected, str):
                    self.assertEqual(self.header_after()["atomic-execution"], "complete")

    def test_pre_tdd_completion_keeps_the_header_without_a_tests_segment(self) -> None:
        self.check_set(status_leaf(None, "in-progress"), ("atomic-execution=complete",), (),
                       "completion-without-tests")

        self.check_set(status_leaf(None, "in-progress"), ("atomic-execution=complete",),
                       (PRE_TDD_NOTE,), ("atomic-execution", "notes", "state_receipts"))

        self.assertIn("T-01 | Leaf | atomic-execution: complete | atomic-validation: not-started\n"
                      "  last_action:\n", self.state())
        self.assertNotIn("atomic-tests", self.header_after())

    def test_leaving_not_started_without_a_tests_status_needs_one_in_the_same_call(self) -> None:
        cases: dict[str, tuple[str, tuple[str, ...], Outcome]] = {
            "to blocked": (status_leaf(None), ("atomic-execution=blocked",),
                           "pre-tdd-not-applicable"),
            "from in-progress to blocked": (status_leaf(None, "in-progress"),
                                            ("atomic-execution=blocked",),
                                            ("atomic-execution", "state_receipts"))}
        for label, (block_text, fields, expected) in cases.items():
            with self.subTest(case=label):
                self.check_set(block_text, fields, (), expected)

        self.assertIn("T-01 | Leaf | atomic-execution: blocked | atomic-validation: not-started\n",
                      self.state())

    def test_pre_tdd_start_with_a_tests_status_writes_it_before_the_execution_segment(self) -> None:
        self.check_set(status_leaf(None), ("atomic-execution=in-progress",), (),
                       "pre-tdd-not-applicable")

        self.check_set(status_leaf(None), ("atomic-execution=in-progress", "atomic-tests=red"), (),
                       ("atomic-tests", "atomic-execution", "state_receipts"))

        self.assertIn("T-01 | Leaf | atomic-tests: red | atomic-execution: in-progress | "
                      "atomic-validation: not-started\n", self.state())


class FieldGroupAtomicityTests(LifecycleCase):
    def test_one_refused_input_among_valid_fields_and_notes_changes_nothing(self) -> None:
        cases: dict[str, tuple[str, tuple[str, ...], tuple[str, ...], str]] = {
            "value outside the vocabulary": (status_leaf("not-started"),
                                             ("last_action=x", "atomic-execution=done"), ("y",),
                                             "invalid-value"),
            "value rules before transition rules": (
                status_leaf("not-started"), ("atomic-tests=green", "atomic-validation=passed"), (),
                "invalid-value"),
            "green from not-started": (status_leaf("not-started"),
                                       ("last_action=x", "atomic-tests=green"), ("y",),
                                       "invalid-transition"),
            "completion with red tests": (status_leaf("red", "in-progress"),
                                          ("blocker=waiting", "last_action=x",
                                           "atomic-execution=complete"), ("a", "b"),
                                          "completion-without-tests"),
            "justification does not allow a downgrade": (
                status_leaf("green", "in-progress"), ("atomic-tests=n-a", "last_action=x"),
                (EM_DASH_JUSTIFICATION,), "downgrade")}
        for label, (block_text, fields, notes, error) in cases.items():
            with self.subTest(case=label):
                self.check_set(block_text, fields, notes, error)

    def test_justified_n_a_with_a_field_and_its_note_is_one_revision(self) -> None:
        self.check_set(status_leaf("not-started"), ("atomic-tests=n-a", "last_action=x"), ("y",),
                       "n-a-unjustified")
        original = self.state()
        source = file_revision(self.task / "state.md")

        document = self.check_set(status_leaf("not-started"),
                                  ("atomic-tests=n-a", "last_action=x"), (EM_DASH_JUSTIFICATION,),
                                  ("atomic-tests", "last_action", "notes", "state_receipts"))

        result = self.state()
        receipt = self.receipt_line(result)
        self.assertRegex(receipt, rf"^  state_receipts: {OPERATION_ID}#[0-9a-f]{{16}}\n$")
        self.assertEqual(result, original.replace("atomic-tests: not-started", "atomic-tests: n-a", 1)
                         .replace("  last_action:\n", "  last_action: x\n", 1)
                         .replace("  notes:\n", "  notes: " + EM_DASH_JUSTIFICATION + "\n" + receipt,
                                  1))
        self.assertEqual(document["source_revision"], source)
        self.assertEqual(document["result_revision"], file_revision(self.task / "state.md"))

    def test_status_named_with_its_current_value_is_not_a_transition(self) -> None:
        unjustified = status_leaf("n-a", "not-started", HYPHEN_JUSTIFICATION)
        cases: dict[str, tuple[str, str, list[str]]] = {
            "green kept": (status_leaf("green", "in-progress"), "atomic-tests=green", []),
            "pinned kept": (status_leaf("pinned", "in-progress"), "atomic-tests=pinned", []),
            "pre-TDD not-started kept": (status_leaf(None), "atomic-execution=not-started", []),
            "unjustified n-a kept": (unjustified, "atomic-tests=n-a", ["pre-existing-violation"]),
            "completion with red tests kept": (status_leaf("red", "complete"),
                                               "atomic-execution=complete",
                                               ["pre-existing-violation"])}
        for label, (block_text, pair, warnings) in cases.items():
            with self.subTest(case=label):
                document = self.check_set(block_text, (pair, "last_action=x"), (),
                                          ("last_action", "state_receipts"))
                self.assertEqual(document["warnings"], warnings)


class PreExistingViolationTests(LifecycleCase):
    def test_violation_in_an_unchanged_field_is_applied_with_a_warning(self) -> None:
        unjustified = status_leaf("n-a", "not-started", HYPHEN_JUSTIFICATION)
        cases: dict[str, tuple[str, str, tuple[str, ...], tuple[str, ...]]] = {
            "unjustified n-a with set": (unjustified, "set", ("--field", "last_action=y"),
                                         ("last_action", "state_receipts")),
            "unjustified n-a with another status": (
                unjustified, "set", ("--field", "atomic-validation=in-progress"),
                ("atomic-validation", "state_receipts")),
            "unjustified n-a with append-note": (unjustified, "append-note", ("--note", "z"),
                                                 ("notes", "state_receipts")),
            "unjustified n-a with add-file": (unjustified, "add-file", ("--path", "c.sh"),
                                              ("target_files", "state_receipts")),
            "value outside the vocabulary": (status_leaf("not-started", validation="reviewed"),
                                             "set", ("--field", "last_action=y"),
                                             ("last_action", "state_receipts")),
            "completion with red tests": (status_leaf("red", "complete"), "set",
                                          ("--field", "last_action=y"),
                                          ("last_action", "state_receipts"))}
        for label, (block_text, command, options, changed) in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(block_text, leaf("T-02")))

                document = self.write_applied(self.write(command, *options), command, *changed)

                self.assertEqual(document["warnings"], ["pre-existing-violation"])

    def test_unjustified_n_a_stays_invalid_after_an_unrelated_write(self) -> None:
        self.write_state(state_text(status_leaf("n-a", "not-started", HYPHEN_JUSTIFICATION)))

        document = self.applied(self.set_fields("last_action=y"), "last_action", "state_receipts")

        self.assertEqual(document["warnings"], ["pre-existing-violation"])
        code, errors = self.validate_codes()
        self.assertEqual(code, 6)
        self.assertIn("n-a-unjustified", errors)

    def test_missing_required_field_is_reported_by_writes_unless_the_write_supplies_it(
            self) -> None:
        no_target_files = "  last_action:\n  blocker: none\n  notes:\n"
        no_notes = "  last_action:\n  target_files:\n  blocker: none\n"
        neither = "  last_action:\n  blocker: none\n"
        cases: dict[str, tuple[str, str, tuple[str, ...], tuple[str, ...], list[str]]] = {
            "set on a leaf without target_files": (
                leaf("T-01", body=no_target_files), "set", ("--field", "last_action=x"),
                ("last_action", "state_receipts"), ["required-field-missing"]),
            "set on a composite without children": (
                composite_block("T-01", body="  blocker: none\n  notes:\n"), "set",
                ("--field", "rollup=in-progress"), ("rollup", "state_receipts"),
                ["required-field-missing"]),
            "append-note on a leaf without notes and target_files": (
                leaf("T-01", body=neither), "append-note", ("--note", "a"),
                ("notes", "state_receipts"), ["required-field-missing"]),
            "append-note supplying the only missing field": (
                leaf("T-01", body=no_notes), "append-note", ("--note", "a"),
                ("notes", "state_receipts"), []),
            "add-file supplying the only missing field": (
                leaf("T-01", body=no_target_files), "add-file", ("--path", "b.sh"),
                ("target_files", "state_receipts"), [])}
        for label, (block_text, command, options, changed, warnings) in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(block_text, leaf("T-02")))

                document = self.write_applied(self.write(command, *options), command, *changed)

                self.assertEqual(document["warnings"], warnings)


LEAF_HEADER_CHANGES = ("atomic-tests", "atomic-execution", "atomic-validation")
LEAF_INIT_CHANGES = LEAF_HEADER_CHANGES + ("last_action", "target_files", "blocker", "notes",
                                           "state_receipts")
COMPOSITE_INIT_CHANGES = ("rollup", "integration-validation", "children", "blocker", "notes",
                          "state_receipts")
LAST_BLOCK_T04 = leaf("T-04", body=leaf_body(extra="  pr: none\n"))


def init_inputs(kind: str, name: str, *, paths: tuple[str, ...] = (),
                children: tuple[str, ...] = (), notes: tuple[str, ...] = ()) -> dict[str, Any]:
    """Digest inputs of init-block: kind, name, and paths, children and notes in argument order."""
    return {"kind": kind, "name": name, "paths": list(paths), "children": list(children),
            "notes": list(notes)}


def new_leaf(block_id: str, name: str, receipt: str, *, paths: tuple[str, ...] = (),
             notes: tuple[str, ...] = ()) -> str:
    """The canonical initial lines of a new leaf block; empty values have no trailing space."""
    lines = [f"{block_id} | {name} | atomic-tests: not-started | atomic-execution: not-started"
             " | atomic-validation: not-started",
             "  last_action:",
             "  target_files:" + (" " + ", ".join(paths) if paths else ""),
             "  blocker: none",
             "  notes:" + (" " + notes[0] if notes else "")]
    lines += [CONTINUATION + note for note in notes[1:]]
    lines.append(f"  state_receipts: {receipt}")
    return "\n".join(lines) + "\n"


class InitBlockCase(NoteAndFileCase):
    """Runner and outcome assertions for init-block."""

    def init_block(self, block_id: str, kind: str, name: str, *options: str,
                   revision: str | None = None, operation_id: str = OPERATION_ID,
                   task: Path | None = None) -> ToolResult:
        """Run init-block for the id, kind and name with the current revision by default."""
        task_path = self.task if task is None else task
        if revision is None:
            revision = file_revision(task_path / "state.md")
        return self.run_tool("init-block", "--root", str(self.root), "--task", str(task_path),
                             "--block", block_id, "--kind", kind, "--name", name,
                             "--expected-revision", revision, "--operation-id", operation_id,
                             *options)

    def initialized(self, result: ToolResult, block_id: str, kind: str) -> dict[str, Any]:
        """An applied init-block lists every header field and field line it wrote."""
        changed = LEAF_INIT_CHANGES if kind == "leaf" else COMPOSITE_INIT_CHANGES
        document = self.write_applied(result, "init-block", *changed)
        self.assertEqual(document["block_id"], block_id)
        self.assertEqual(document["block_kind"], kind)
        self.assertEqual(document["operation_id"], OPERATION_ID)
        self.assertEqual(document["result_revision"], file_revision(self.task / "state.md"))
        self.assertNotEqual(document["result_revision"], document["source_revision"])
        return document

    def assert_valid_state(self) -> None:
        result = self.run_tool("validate", "--root", str(self.root), "--task", str(self.task))
        self.assertEqual(result.code, 0, result.stdout + result.stderr)
        self.assertEqual(self.output(result)["result"], "valid")

    def init_refused(self, result: ToolResult, code: int, error: str) -> dict[str, Any]:
        document = self.refused_by(result, "init-block", code, error)
        if code in (4, 6):
            self.assertIn(REFUSAL_SENTENCE, result.stderr)
        return document


class InitBlockLayoutTests(InitBlockCase):
    def test_block_after_the_last_block_keeps_one_blank_line_before_the_next_heading(self) -> None:
        original = state_text(LAST_BLOCK_T04, after="## Next\n")
        self.write_state(original)
        receipt = expected_receipt("init-block", init_inputs("leaf", "Demo"), block_id="T-05")

        self.initialized(self.init_block("T-05", "leaf", "Demo"), "T-05", "leaf")

        self.assertEqual(self.state(), original.replace(
            "  pr: none\n\n## Next\n",
            "  pr: none\n"
            "\n"
            "T-05 | Demo | atomic-tests: not-started | atomic-execution: not-started | "
            "atomic-validation: not-started\n"
            "  last_action:\n"
            "  target_files:\n"
            "  blocker: none\n"
            "  notes:\n"
            f"  state_receipts: {receipt}\n"
            "\n"
            "## Next\n", 1))
        self.assert_valid_state()

    def test_block_in_a_heading_only_section_follows_the_heading_directly(self) -> None:
        receipt = expected_receipt("init-block", init_inputs("leaf", "Demo"), block_id="T-05")
        block = new_leaf("T-05", "Demo", receipt)
        cases = {"heading, blank line and next heading": (
                     state_text(after="## Next\n"), "## Subtask Progress\n\n## Next\n",
                     "## Subtask Progress\n" + block + "\n## Next\n"),
                 "heading as the last line of the file": (
                     state_text(after="").removesuffix("\n"), "## Subtask Progress\n",
                     "## Subtask Progress\n" + block)}
        for label, (original, before, after) in cases.items():
            with self.subTest(case=label):
                self.write_state(original)
                self.assertTrue(original.endswith(before), original)

                self.initialized(self.init_block("T-05", "leaf", "Demo"), "T-05", "leaf")

                self.assertEqual(self.state(), original.removesuffix(before) + after)
                self.assert_valid_state()

    def test_blank_lines_after_the_last_line_stay_after_the_new_block(self) -> None:
        receipt = expected_receipt("init-block", init_inputs("leaf", "Demo"), block_id="T-05")
        block = new_leaf("T-05", "Demo", receipt)
        cases = {"two blank lines before the next heading": (
                     state_text(LAST_BLOCK_T04, after="\n## Next\n"), "  pr: none\n\n\n## Next\n",
                     "  pr: none\n\n" + block + "\n\n## Next\n"),
                 "one blank line at the end of the file": (
                     state_text(LAST_BLOCK_T04, after=""), "  pr: none\n\n",
                     "  pr: none\n\n" + block + "\n"),
                 "no blank line at the end of the file": (
                     state_text(LAST_BLOCK_T04, after="").removesuffix("\n"), "  pr: none\n",
                     "  pr: none\n\n" + block)}
        for label, (original, before, after) in cases.items():
            with self.subTest(case=label):
                self.write_state(original)
                self.assertTrue(original.endswith(before), original)

                self.initialized(self.init_block("T-05", "leaf", "Demo"), "T-05", "leaf")

                self.assertEqual(self.state(), original.removesuffix(before) + after)

    def test_section_at_the_end_of_a_file_without_a_final_newline_keeps_that_state(self) -> None:
        original = state_text(LAST_BLOCK_T04, after="").rstrip("\n")
        self.write_state(original)
        self.assertTrue(original.endswith("  pr: none"), original)
        receipt = expected_receipt("init-block", init_inputs("leaf", "Demo"), block_id="T-05")

        self.initialized(self.init_block("T-05", "leaf", "Demo"), "T-05", "leaf")

        result = self.state()
        self.assertEqual(result, original + "\n\n" + new_leaf("T-05", "Demo", receipt)
                         .removesuffix("\n"))
        self.assertFalse(result.endswith("\n"))
        self.assert_valid_state()

    def test_last_non_blank_line_may_be_a_column_zero_foreign_line(self) -> None:
        original = state_text(leaf("T-04"), "Foreign column-zero line\n", after="## Next\n")
        self.write_state(original)
        receipt = expected_receipt("init-block", init_inputs("leaf", "Demo"), block_id="T-05")

        self.initialized(self.init_block("T-05", "leaf", "Demo"), "T-05", "leaf")

        self.assertEqual(self.state(), original.replace(
            "Foreign column-zero line\n\n## Next\n",
            "Foreign column-zero line\n\n" + new_leaf("T-05", "Demo", receipt) + "\n## Next\n", 1))
        self.assert_valid_state()

    def test_last_non_blank_line_may_be_a_closing_fence_delimiter(self) -> None:
        receipt = expected_receipt("init-block", init_inputs("leaf", "Demo"), block_id="T-05")
        block = new_leaf("T-05", "Demo", receipt)
        in_block_fence = leaf("T-04", body=leaf_body(extra="   ```\n  pr: hidden\n   ```\n"))
        cases = {"fence after the last block": (state_text(leaf("T-04"), FENCE, after="## Next\n"),
                                                "```\n\n## Next\n"),
                 "fence inside the last block": (state_text(in_block_fence, after="## Next\n"),
                                                 "   ```\n\n## Next\n")}
        for label, (original, ending) in cases.items():
            with self.subTest(case=label):
                self.write_state(original)
                self.assertIn(ending, original)
                fields_before = self.block(self.read_ok(self.get("--block", "T-04")), "T-04")["fields"]

                self.initialized(self.init_block("T-05", "leaf", "Demo"), "T-05", "leaf")

                closing = ending.removesuffix("\n\n## Next\n")
                self.assertEqual(self.state(), original.replace(
                    ending, closing + "\n\n" + block + "\n## Next\n", 1))
                document = self.read_ok(self.get())
                self.assertEqual([item["block_id"] for item in document["blocks"]], ["T-04", "T-05"])
                self.assertEqual(self.block(document, "T-04")["fields"], fields_before)
                self.assert_valid_state()

    def test_fix_task_block_id_is_accepted(self) -> None:
        original = state_text(LAST_BLOCK_T04)
        self.write_state(original)

        self.initialized(self.init_block("T-04-fix-some-slug", "leaf", "Fix"),
                         "T-04-fix-some-slug", "leaf")

        block = self.block(self.read_ok(self.get("--block", "T-04-fix-some-slug")),
                           "T-04-fix-some-slug")
        self.assertEqual(block["block_kind"], "leaf")
        self.assertEqual(block["name"], "Fix")
        self.assert_valid_state()


class InitBlockContentTests(InitBlockCase):
    def test_composite_block_has_its_canonical_lines_and_reads_back_as_composite(self) -> None:
        original = state_text(LAST_BLOCK_T04)
        self.write_state(original)
        receipt = expected_receipt("init-block", init_inputs(
            "composite", "Parent", children=("T-06a", "T-06b"), notes=("two components",)),
            block_id="T-06")

        self.initialized(self.init_block("T-06", "composite", "Parent", "--children", "T-06a,T-06b",
                                         "--note", "two components"), "T-06", "composite")

        self.assertEqual(self.state(), original.replace(
            "  pr: none\n\n",
            "  pr: none\n"
            "\n"
            "[composite] T-06 | Parent | rollup: not-started | integration-validation: not-started\n"
            "  children: T-06a, T-06b\n"
            "  blocker: none\n"
            "  notes: two components\n"
            f"  state_receipts: {receipt}\n"
            "\n", 1))
        block = self.block(self.read_ok(self.get("--block", "T-06")), "T-06")
        self.assertEqual(block["block_kind"], "composite")
        self.assertEqual(self.field_values(block, "children"), ["T-06a, T-06b"])
        self.assert_valid_state()

    def test_repeated_target_file_is_written_once_and_an_empty_notes_line_has_no_trailing_space(
            self) -> None:
        original = state_text(LAST_BLOCK_T04)
        self.write_state(original)
        options = ("--target-file", "a.sh", "--target-file", "a.sh", "--target-file", "b.sh")
        receipt = expected_receipt("init-block", init_inputs(
            "leaf", "Demo", paths=("a.sh", "a.sh", "b.sh")), block_id="T-05")

        self.initialized(self.init_block("T-05", "leaf", "Demo", *options), "T-05", "leaf")

        result = self.state()
        self.assertEqual(result, original.replace(
            "  pr: none\n\n",
            "  pr: none\n\n" + new_leaf("T-05", "Demo", receipt, paths=("a.sh", "b.sh")) + "\n", 1))
        self.assertIn("  target_files: a.sh, b.sh\n  blocker: none\n  notes:\n  state_receipts: ",
                      result)
        self.assertIn("\nT-05 | Demo | atomic-tests: not-started | atomic-execution: not-started | "
                      "atomic-validation: not-started\n  last_action:\n  target_files: ", result)
        self.assert_valid_state()

    def test_further_notes_follow_the_first_note_as_continuation_lines(self) -> None:
        cases = {"leaf": ("T-05", ()), "composite": ("T-06", ("--children", "T-06a"))}
        for kind, (block_id, more) in cases.items():
            with self.subTest(kind=kind):
                self.write_state(state_text(LAST_BLOCK_T04))

                self.initialized(self.init_block(block_id, kind, "Demo", *more, "--note", "a",
                                                 "--note", "b c"), block_id, kind)

                self.assertIn("  notes: a\n" + CONTINUATION + "b c\n  state_receipts: ",
                              self.state())
                block = self.block(self.read_ok(self.get("--block", block_id)), block_id)
                notes = [item for item in block["fields"] if item["name"] == "notes"]
                self.assertEqual([(item["value"], item["continuation"]) for item in notes],
                                 [("a", [CONTINUATION + "b c"])])
                self.assert_valid_state()

    def test_receipt_digest_covers_the_inputs_in_argument_order(self) -> None:
        cases = {
            "leaf": ("T-05", "leaf", ("--note", "y", "--target-file", "b.sh", "--note", "x",
                                      "--target-file", "a.sh"),
                     init_inputs("leaf", "Demo", paths=("b.sh", "a.sh"), notes=("y", "x"))),
            "composite": ("T-06", "composite", ("--children", "T-06b,T-06a", "--note", "y",
                                                "--note", "x"),
                          init_inputs("composite", "Demo", children=("T-06b", "T-06a"),
                                      notes=("y", "x")))}
        for label, (block_id, kind, options, inputs) in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(LAST_BLOCK_T04))

                self.initialized(self.init_block(block_id, kind, "Demo", *options), block_id, kind)

                self.assertEqual(self.receipt_line(self.state()),
                                 "  state_receipts: "
                                 f"{expected_receipt('init-block', inputs, block_id=block_id)}\n")

    def test_names_and_notes_are_stored_literally(self) -> None:
        name = "Demo $(touch injected) `touch quoted` ; & > out"
        note = "$HOME; touch noted && echo `id`"
        self.write_state(state_text(LAST_BLOCK_T04))

        self.initialized(self.init_block("T-05", "leaf", name, "--note", note), "T-05", "leaf")

        block = self.block(self.read_ok(self.get("--block", "T-05")), "T-05")
        self.assertEqual(block["name"], name)
        self.assertEqual(self.field_values(block, "notes"), [note])
        self.assertEqual(sorted(path.name for path in self.base.iterdir()), ["project"])


class InitBlockRefusalTests(InitBlockCase):
    def test_existing_id_is_refused_with_block_exists_and_nothing_changes(self) -> None:
        cases = {"existing leaf": (state_text(leaf("T-04"), leaf("T-05")), "T-05", "leaf", ()),
                 "existing composite": (state_text(leaf("T-04"), composite_block("T-05")), "T-05",
                                        "composite", ("--children", "T-05a", "--note", "n")),
                 "existing block that is not the last": (state_text(leaf("T-04"), leaf("T-05")),
                                                         "T-04", "leaf", ())}
        for label, (original, block_id, kind, options) in cases.items():
            with self.subTest(case=label):
                self.write_state(original)
                before = self.files_without_lock()

                document = self.init_refused(self.init_block(block_id, kind, "Demo", *options), 6,
                                             "block-exists")

                self.assertEqual(document["block_id"], block_id)
                self.assertEqual(document["block_kind"], kind)
                self.assert_unchanged_after_refusal(before)

    def test_missing_section_exits_3_section_missing(self) -> None:
        cases = {"leaf": ("T-05", ()), "composite": ("T-06", ("--children", "T-06a", "--note", "n"))}
        original = state_text().replace("## Subtask Progress\n\n", "", 1)
        for kind, (block_id, options) in cases.items():
            with self.subTest(kind=kind):
                self.write_state(original)
                before = self.files_without_lock()

                document = self.init_refused(self.init_block(block_id, kind, "Demo", *options), 3,
                                             "section-missing")

                self.assertEqual(document["block_kind"], kind)
                self.assert_unchanged_after_refusal(before)

    def test_invalid_kind_combinations_exit_2_invalid_arguments(self) -> None:
        path = self.write_state(state_text(LAST_BLOCK_T04))
        common = ["--root", str(self.root), "--task", str(self.task), "--block", "T-06",
                  "--expected-revision", file_revision(path), "--operation-id", OPERATION_ID]
        cases = {
            "composite without a note": ["--kind", "composite", "--name", "P",
                                         "--children", "T-06a"],
            "composite without children": ["--kind", "composite", "--name", "P", "--note", "n"],
            "composite with a target file": ["--kind", "composite", "--name", "P",
                                             "--children", "T-06a", "--note", "n",
                                             "--target-file", "a.sh"],
            "leaf with children": ["--kind", "leaf", "--name", "P", "--children", "T-06a"],
            "kind outside leaf and composite": ["--kind", "group", "--name", "P"],
            "kind missing": ["--name", "P"],
            "name missing": ["--kind", "leaf"],
            "children given twice": ["--kind", "composite", "--name", "P", "--children", "T-06a",
                                     "--children", "T-06b", "--note", "n"],
            "field option of set": ["--kind", "leaf", "--name", "P", "--field", "blocker=x"]}
        before = snapshot(self.task)
        for label, options in cases.items():
            with self.subTest(case=label):
                document = self.init_refused(self.run_tool("init-block", *common, *options), 2,
                                             "invalid-arguments")

                self.assertIsNone(document["source_revision"])
                self.assertIsNone(document["result_revision"])
                self.assertEqual(snapshot(self.task), before)

    def test_invalid_children_lists_exit_2_invalid_arguments(self) -> None:
        path = self.write_state(state_text(LAST_BLOCK_T04))
        common = ["--root", str(self.root), "--task", str(self.task), "--block", "T-06",
                  "--kind", "composite", "--name", "P", "--expected-revision",
                  file_revision(path), "--operation-id", OPERATION_ID, "--note", "n"]
        children = {"empty item": "T-01a,,T-01b", "repeated item": "T-01a,T-01a",
                    "space after the comma": "T-01a, T-01b", "leading comma": ",T-01a",
                    "trailing comma": "T-01a,", "empty list": "", "malformed id": "T-1a",
                    "the block's own id": "T-06a,T-06"}
        before = snapshot(self.task)
        for label, value in children.items():
            with self.subTest(case=label):
                result = self.run_tool("init-block", *common, "--children", value)

                self.init_refused(result, 2, "invalid-arguments")
                self.assertEqual(snapshot(self.task), before)

    def test_invalid_note_or_target_file_is_refused_with_exit_6(self) -> None:
        cases = {
            "empty note on a leaf": ("leaf", ("--note", ""), "invalid-value"),
            "empty note on a composite": ("composite", ("--children", "T-05a", "--note", ""),
                                          "invalid-value"),
            "empty note after a valid one": ("composite", ("--children", "T-05a", "--note", "a",
                                                           "--note", ""), "invalid-value"),
            "note with a line feed": ("leaf", ("--note", "a\nb"), "invalid-value"),
            "absolute path": ("leaf", ("--target-file", "/abs"), "invalid-path"),
            "parent segment": ("leaf", ("--target-file", "a.sh", "--target-file", "../x"),
                               "invalid-path"),
            "comma in a path": ("leaf", ("--target-file", "a,b"), "invalid-path"),
            "empty path": ("leaf", ("--target-file", ""), "invalid-path")}
        for label, (kind, options, error) in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(LAST_BLOCK_T04))
                before = self.files_without_lock()

                self.init_refused(self.init_block("T-05", kind, "Demo", *options), 6, error)

                self.assert_unchanged_after_refusal(before)

    def test_stale_revision_is_refused_with_the_no_bypass_sentence(self) -> None:
        self.write_state(state_text(LAST_BLOCK_T04))
        before = self.files_without_lock()

        document = self.init_refused(self.init_block("T-05", "leaf", "Demo",
                                                     revision=ZERO_REVISION), 4,
                                     "revision-conflict")

        self.assertEqual(document["block_kind"], "leaf")
        self.assert_unchanged_after_refusal(before)

    def test_invalid_name_content_is_invalid_value_and_nothing_changes(self) -> None:
        cases = {"empty name": ("leaf", "", ()),
                 "vertical bar in the name": ("leaf", "a | b", ()),
                 "line feed in the name": ("leaf", "a\nb", ()),
                 "carriage return in the name": ("leaf", "a\rb", ()),
                 "empty name of a composite": ("composite", "",
                                               ("--children", "T-05a", "--note", "n"))}
        for label, (kind, name, options) in cases.items():
            with self.subTest(case=label):
                self.write_state(state_text(LAST_BLOCK_T04))
                before = self.files_without_lock()

                document = self.init_refused(self.init_block("T-05", kind, name, *options), 6,
                                             "invalid-value")

                self.assertEqual(document["block_kind"], kind)
                self.assert_unchanged_after_refusal(before)

    def test_invalid_name_with_a_stale_revision_is_a_revision_conflict(self) -> None:
        self.write_state(state_text(LAST_BLOCK_T04))
        before = self.files_without_lock()

        self.init_refused(self.init_block("T-05", "leaf", "a | b", revision=ZERO_REVISION), 4,
                          "revision-conflict")

        self.assert_unchanged_after_refusal(before)

    def test_missing_name_option_exits_2_invalid_arguments(self) -> None:
        path = self.write_state(state_text(LAST_BLOCK_T04))
        before = snapshot(self.task)

        document = self.init_refused(self.run_tool(
            "init-block", "--root", str(self.root), "--task", str(self.task), "--block", "T-05",
            "--kind", "leaf", "--expected-revision", file_revision(path),
            "--operation-id", OPERATION_ID), 2, "invalid-arguments")

        self.assertIsNone(document["source_revision"])
        self.assertEqual(snapshot(self.task), before)

    def test_unclosed_fence_at_the_end_of_the_section_exits_1_and_writes_nothing(self) -> None:
        cases = {"column-zero fence after the last block": state_text(
                     leaf("T-04"), "```text\nunclosed example\n", after="## Next\n"),
                 "indented fence inside the last block": state_text(
                     leaf("T-04", body=leaf_body(extra="   ```\n  pr: hidden\n")), after="")}
        for label, original in cases.items():
            with self.subTest(case=label):
                self.write_state(original)
                before = self.files_without_lock()

                document = self.init_refused(self.init_block("T-05", "leaf", "Demo"), 1,
                                             "internal-error")

                self.assertEqual(document["block_kind"], "leaf")
                self.assertEqual(self.state(), original)
                self.assert_unchanged_after_refusal(before)

    def test_malformed_revision_or_operation_id_exits_2(self) -> None:
        self.write_state(state_text(LAST_BLOCK_T04))
        before = snapshot(self.task)
        cases = {"malformed revision": ({"revision": "sha256:abc"}, "malformed-revision"),
                 "invalid operation id": ({"operation_id": "-op"}, "invalid-operation-id")}
        for label, (keywords, error) in cases.items():
            with self.subTest(case=label):
                self.init_refused(self.init_block("T-05", "leaf", "Demo", **keywords), 2, error)

                self.assertEqual(snapshot(self.task), before)


RECEIPT_STATE = state_text(leaf("T-01"), LAST_BLOCK_T04)
# Each write command: its target block, the options of a first operation, and other options
# that a reused operation id must not carry.
REPEATABLE_WRITES = {
    "set": ("T-01", ("--field", "last_action=first"), ("--field", "last_action=second")),
    "append-note": ("T-01", ("--note", "first"), ("--note", "second")),
    "add-file": ("T-01", ("--path", "a.sh"), ("--path", "b.sh")),
    "init-block": ("T-05", ("--kind", "leaf", "--name", "First"),
                   ("--kind", "leaf", "--name", "Second"))}
LONGEST_OPERATION_ID = "A" + "b" * 62 + "9"


class ReceiptCase(InitBlockCase):
    """Outcome assertions for repeated and reused operation ids."""

    def assert_untouched(self, task: Path, before: Snapshot) -> None:
        self.assertEqual(self.files_without_lock(task), before)
        self.assertEqual([path.name for path in task.glob(".state.md.*.tmp")], [])

    def applied_once(self, result: ToolResult) -> None:
        self.assertEqual(result.code, 0, result.stdout + result.stderr)
        self.assertEqual(self.output(result)["result"], "applied", result.stdout)

    def already_applied(self, result: ToolResult, command: str, block_id: str, kind: str,
                        task: Path | None = None,
                        operation_id: str = OPERATION_ID) -> dict[str, Any]:
        """A repeat writes nothing and reports the current revision as both revisions."""
        document = self.output(result)
        self.assertEqual(result.code, 0, result.stdout + result.stderr)
        self.assertEqual(document["command"], command)
        self.assertEqual(document["result"], "already_applied", result.stdout)
        self.assertEqual(document["errors"], [])
        self.assertEqual(document["changed_fields"], [])
        self.assertEqual(document["operation_id"], operation_id)
        self.assertEqual(document["block_id"], block_id)
        self.assertEqual(document["block_kind"], kind)
        current = file_revision((self.task if task is None else task) / "state.md")
        self.assertEqual(document["source_revision"], current)
        self.assertEqual(document["result_revision"], current)
        return document

    def conflict(self, result: ToolResult, command: str) -> dict[str, Any]:
        document = self.refused_by(result, command, 8, "operation-conflict")
        self.assertIn(REFUSAL_SENTENCE, result.stderr)
        return document


class ReceiptRepeatTests(ReceiptCase):
    def test_repeat_with_identical_inputs_is_already_applied_for_every_write_command(self) -> None:
        for command, (block_id, first, _) in REPEATABLE_WRITES.items():
            task = self.task_copy(f"task-{command}", RECEIPT_STATE)
            initial = file_revision(task / "state.md")
            self.applied_once(self.write(command, *first, block=block_id, task=task))
            before = self.files_without_lock(task)
            for label, revision in {"stale": initial,
                                    "current": file_revision(task / "state.md")}.items():
                with self.subTest(command=command, revision=label):
                    result = self.write(command, *first, block=block_id, revision=revision,
                                        task=task)

                    self.already_applied(result, command, block_id, "leaf", task)
                    self.assert_untouched(task, before)

    def test_reused_operation_id_with_other_inputs_is_an_operation_conflict(self) -> None:
        for command, (block_id, first, other) in REPEATABLE_WRITES.items():
            task = self.task_copy(f"task-{command}", RECEIPT_STATE)
            initial = file_revision(task / "state.md")
            self.applied_once(self.write(command, *first, block=block_id, task=task))
            before = self.files_without_lock(task)
            for label, revision in {"stale": initial,
                                    "current": file_revision(task / "state.md")}.items():
                with self.subTest(command=command, revision=label):
                    result = self.write(command, *other, block=block_id, revision=revision,
                                        task=task)

                    self.conflict(result, command)
                    self.assert_untouched(task, before)

    def test_operation_id_is_matched_within_its_block_and_across_commands(self) -> None:
        self.write_state(RECEIPT_STATE)
        self.applied_once(self.write("set", "--field", "last_action=first"))
        before = self.files_without_lock()

        with self.subTest(case="another command on the same block"):
            self.conflict(self.append_notes("first"), "append-note")
            self.assert_unchanged_after_refusal(before)

        with self.subTest(case="the same inputs on another block"):
            self.applied_once(self.write("set", "--field", "last_action=first", block="T-04"))
            self.assertEqual(self.state().count("  state_receipts: "), 2)

    def test_field_order_keeps_the_digest_while_note_and_path_order_change_it(self) -> None:
        self.write_state(RECEIPT_STATE)
        cases = {
            "fields in the other order": (
                "fields-op", "set", ("--field", "last_action=a", "--field", "blocker=b"),
                ("--field", "blocker=b", "--field", "last_action=a"), "already_applied"),
            "notes in the other order": (
                "notes-op", "set", ("--field", "last_action=c", "--note", "a", "--note", "b"),
                ("--field", "last_action=c", "--note", "b", "--note", "a"), "operation-conflict"),
            "paths in the other order": (
                "paths-op", "add-file", ("--path", "a.sh", "--path", "b.sh"),
                ("--path", "b.sh", "--path", "a.sh"), "operation-conflict"),
            "a repeated path given once": (
                "repeat-op", "add-file", ("--path", "c.sh", "--path", "c.sh"),
                ("--path", "c.sh"), "operation-conflict")}
        for label, (operation_id, command, first, repeat, outcome) in cases.items():
            with self.subTest(case=label):
                initial = file_revision(self.task / "state.md")
                self.applied_once(self.write(command, *first, operation_id=operation_id))
                before = self.files_without_lock()

                result = self.write(command, *repeat, revision=initial, operation_id=operation_id)

                if outcome == "already_applied":
                    self.already_applied(result, command, "T-01", "leaf",
                                         operation_id=operation_id)
                else:
                    self.conflict(result, command)
                self.assert_unchanged_after_refusal(before)

    def test_unchanged_result_records_no_receipt_so_its_repeat_is_unchanged_again(self) -> None:
        self.write_state(RECEIPT_STATE)
        original = self.state()

        for attempt in ("first", "repeat"):
            with self.subTest(attempt=attempt):
                result = self.write("set", "--field", "blocker=none")

                self.assertEqual(result.code, 0, result.stdout + result.stderr)
                self.assertEqual(self.output(result)["result"], "unchanged")
                self.assertEqual(self.state(), original)
                self.assertNotIn("state_receipts", self.state())

        before_change = file_revision(self.task / "state.md")
        self.applied_once(self.write("set", "--field", "blocker=waiting"))
        before = self.files_without_lock()
        result = self.write("set", "--field", "blocker=waiting", revision=before_change)

        self.already_applied(result, "set", "T-01", "leaf")
        self.assert_unchanged_after_refusal(before)

    def test_receipts_on_a_composite_block_make_repeats_idempotent(self) -> None:
        self.write_state(state_text(composite_block("T-02")))
        cases = {"append-note": ("note-op", ("--note", "first")),
                 "set": ("blocker-op", ("--field", "blocker=waiting"))}
        for command, (operation_id, options) in cases.items():
            with self.subTest(command=command):
                initial = file_revision(self.task / "state.md")
                self.applied_once(self.write(command, *options, block="T-02",
                                             operation_id=operation_id))
                before = self.files_without_lock()

                result = self.write(command, *options, block="T-02", revision=initial,
                                    operation_id=operation_id)

                self.already_applied(result, command, "T-02", "composite",
                                     operation_id=operation_id)
                self.assert_unchanged_after_refusal(before)

    def test_operation_id_at_the_length_limit_is_recorded_and_recognized(self) -> None:
        self.write_state(RECEIPT_STATE)
        initial = file_revision(self.task / "state.md")
        self.assertEqual(len(LONGEST_OPERATION_ID), 64)
        self.applied_once(self.write("set", "--field", "last_action=x",
                                     operation_id=LONGEST_OPERATION_ID))
        self.receipt_line(self.state(), operation_id=LONGEST_OPERATION_ID)
        before = self.files_without_lock()

        result = self.write("set", "--field", "last_action=x", revision=initial,
                            operation_id=LONGEST_OPERATION_ID)

        self.already_applied(result, "set", "T-01", "leaf", operation_id=LONGEST_OPERATION_ID)
        self.assert_unchanged_after_refusal(before)


class InitBlockReceiptTests(ReceiptCase):
    def test_existing_id_is_judged_by_its_receipts_then_the_revision_then_block_exists(
            self) -> None:
        self.write_state(state_text(LAST_BLOCK_T04))
        stale = file_revision(self.task / "state.md")
        self.applied_once(self.init_block("T-05", "leaf", "Demo"))
        self.applied_once(self.write("set", "--field", "last_action=started", block="T-05",
                                     operation_id="later-op"))
        current = file_revision(self.task / "state.md")
        before = self.files_without_lock()
        cases = {
            "other operation id, stale revision": ("T-05", "op-other", "Demo", stale,
                                                   (4, "revision-conflict")),
            "block without receipts, stale revision": ("T-04", OPERATION_ID, "Demo", stale,
                                                       (4, "revision-conflict")),
            "other operation id, current revision": ("T-05", "op-other", "Demo", current,
                                                     (6, "block-exists")),
            "block without receipts, current revision": ("T-04", OPERATION_ID, "Demo", current,
                                                         (6, "block-exists")),
            "matching receipt, stale revision": ("T-05", OPERATION_ID, "Demo", stale, None),
            "matching receipt, current revision": ("T-05", OPERATION_ID, "Demo", current, None),
            "same operation id, other name, stale revision": ("T-05", OPERATION_ID, "Other",
                                                              stale, (8, "operation-conflict")),
            "same operation id, other name, current revision": ("T-05", OPERATION_ID, "Other",
                                                                current,
                                                                (8, "operation-conflict"))}
        for label, (block_id, operation_id, name, revision, refusal) in cases.items():
            with self.subTest(case=label):
                result = self.init_block(block_id, "leaf", name, revision=revision,
                                         operation_id=operation_id)

                if refusal is None:
                    self.already_applied(result, "init-block", block_id, "leaf")
                elif refusal[0] == 8:
                    self.conflict(result, "init-block")
                else:
                    self.init_refused(result, *refusal)
                self.assert_unchanged_after_refusal(before)

    def test_existing_id_whose_receipts_cannot_be_looked_up_is_refused_with_exit_3(
            self) -> None:
        cases = {"duplicated id": (state_text(leaf("T-04"), leaf("T-05"), leaf("T-05")),
                                   "block-duplicate"),
                 "malformed receipts line": (state_text(leaf("T-04"), leaf("T-05", body=leaf_body(
                     extra=f"  state_receipts: {receipts(21)}\n"))), "malformed-receipts")}
        for label, (original, error) in cases.items():
            with self.subTest(case=label):
                self.write_state(original)
                before = self.files_without_lock()

                self.init_refused(self.init_block("T-05", "leaf", "Demo"), 3, error)

                self.assert_unchanged_after_refusal(before)


class ReceiptCapTests(ReceiptCase):
    def test_twenty_one_operations_keep_the_twenty_newest_receipts_and_a_dropped_one_is_new(
            self) -> None:
        self.write_state(RECEIPT_STATE)
        operations = [(f"step-{index:02d}", f"last_action=value {index}") for index in range(21)]
        revisions = []
        for operation_id, pair in operations:
            revisions.append(file_revision(self.task / "state.md"))
            self.applied_once(self.write("set", "--field", pair, operation_id=operation_id))
        entries = [expected_receipt("set", {"fields": [pair.split("=", 1)], "notes": []},
                                    operation_id=operation_id)
                   for operation_id, pair in operations]

        self.assertEqual(self.receipt_line(self.state(), operation_id="step-20"),
                         "  state_receipts: " + ", ".join(entries[1:]) + "\n")
        before = self.files_without_lock()

        with self.subTest(case="the dropped oldest operation"):
            result = self.write("set", "--field", operations[0][1], revision=revisions[0],
                                operation_id=operations[0][0])

            self.refused_by(result, "set", 4, "revision-conflict")
            self.assertIn(REFUSAL_SENTENCE, result.stderr)
            self.assert_unchanged_after_refusal(before)

        with self.subTest(case="the oldest kept operation"):
            result = self.write("set", "--field", operations[1][1], revision=revisions[1],
                                operation_id=operations[1][0])

            self.already_applied(result, "set", "T-01", "leaf", operation_id=operations[1][0])
            self.assert_unchanged_after_refusal(before)


class MalformedReceiptsWriteTests(ReceiptCase):
    def test_malformed_receipts_line_refuses_writes_to_its_block_only(self) -> None:
        damaged = f"  state_receipts: {receipts(21)}\n"
        self.write_state(state_text(leaf("T-01", body=leaf_body(extra=damaged)), leaf("T-02")))
        before = self.files_without_lock()
        cases = {"set": ("set", ("--field", "last_action=x"), {}),
                 "set reusing a listed id with a stale revision": (
                     "set", ("--field", "last_action=x"),
                     {"operation_id": "op-00", "revision": ZERO_REVISION}),
                 "append-note": ("append-note", ("--note", "x"), {}),
                 "add-file": ("add-file", ("--path", "x.sh"), {})}
        for label, (command, options, keywords) in cases.items():
            with self.subTest(case=label):
                result = self.write(command, *options, **keywords)

                self.refused_by(result, command, 3, "malformed-receipts")
                self.assert_unchanged_after_refusal(before)

        initial = file_revision(self.task / "state.md")
        self.applied_once(self.write("set", "--field", "last_action=x", block="T-02"))
        self.assertIn(damaged, self.state())
        after = self.files_without_lock()

        with self.subTest(case="repeat on the well-formed block"):
            result = self.write("set", "--field", "last_action=x", block="T-02", revision=initial)

            self.already_applied(result, "set", "T-02", "leaf")
            self.assert_unchanged_after_refusal(after)


# The helper takes the lock on an existing lock file, reports it on stdout and keeps it until it
# is killed or its standard input is closed, so it never outlives the test that started it.
LOCK_HOLDER_SOURCE = (
    "import fcntl, os, sys\n"
    "descriptor = os.open(sys.argv[1], os.O_RDWR)\n"
    "fcntl.flock(descriptor, fcntl.LOCK_EX)\n"
    "sys.stdout.write('locked\\n')\n"
    "sys.stdout.flush()\n"
    "sys.stdin.read()\n")
LOCK_READY = "locked\n"
PROCESS_TIMEOUT_SECONDS = 30
PAUSE_PROOF_SECONDS = 0.3
POLL_SECONDS = 0.005
STALE_AGE_SECONDS = 660
TEMPORARY_FILE = re.compile(r"\.state\.md\.[0-9a-f]{32}\.tmp")
HOLDER_TOKEN = "0123456789abcdef" * 2


def started_at(seconds_ago: int) -> str:
    """UTC start time of a lock owner the given number of seconds ago, in whole seconds."""
    moment = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


class RecoveryCase(NoteAndFileCase):
    """Helper processes for lock contention and tool runs with a test fault configured."""

    def setUp(self) -> None:
        super().setUp()
        self.lock = self.task / ".state-tool.lock"

    def launch(self, arguments: list[str],
               environment: dict[str, str] | None = None) -> subprocess.Popen[str]:
        """Start the current interpreter without bytecode on the given arguments; inherited test
        fault variables are dropped, and a process still running at cleanup is killed."""
        variables = {key: value for key, value in os.environ.items()
                     if not key.startswith("STATE_TOOL_TEST_")}
        variables["PYTHONDONTWRITEBYTECODE"] = "1"
        variables.update(environment or {})
        process = subprocess.Popen([sys.executable, "-B", *arguments], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   cwd=str(self.base), env=variables)
        self.addCleanup(self.reap, process)
        return process

    @staticmethod
    def reap(process: subprocess.Popen[str]) -> None:
        """Kill the started process if it still runs, wait for it and close its pipes."""
        if process.poll() is None:
            process.kill()
        process.wait(timeout=PROCESS_TIMEOUT_SECONDS)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                with contextlib.suppress(OSError):
                    stream.close()

    def hold_lock(self) -> subprocess.Popen[str]:
        """Create the task lock file with mode 0600 and keep it locked by a helper process."""
        self.lock.touch(mode=0o600)
        holder = self.launch(["-c", LOCK_HOLDER_SOURCE, str(self.lock)])
        assert holder.stdout is not None
        ready, _, _ = select.select([holder.stdout], [], [], PROCESS_TIMEOUT_SECONDS)
        self.assertTrue(ready, "the lock holder did not report the lock in time")
        self.assertEqual(holder.stdout.readline(), LOCK_READY, "the lock holder failed to lock")
        return holder

    def owner(self, pid: int, seconds_ago: int = STALE_AGE_SECONDS) -> dict[str, Any]:
        return {"owner_token": HOLDER_TOKEN, "pid": pid, "host": "holder-host",
                "started_at": started_at(seconds_ago)}

    def start_tool(self, fault: str | None, *arguments: str,
                   resume: Path | None = None) -> subprocess.Popen[str]:
        """Start the tool with the given test fault and resume file configured."""
        environment = {}
        if fault is not None:
            environment["STATE_TOOL_TEST_FAULT"] = fault
        if resume is not None:
            environment["STATE_TOOL_TEST_RESUME"] = str(resume)
        return self.launch([str(TOOL), *arguments], environment)

    @staticmethod
    def finish(process: subprocess.Popen[str]) -> ToolResult:
        stdout, stderr = process.communicate(timeout=PROCESS_TIMEOUT_SECONDS)
        return ToolResult(process.returncode, stdout, stderr)

    def set_arguments(self, field: str, revision: str, task: Path | None = None,
                      operation_id: str = OPERATION_ID) -> tuple[str, ...]:
        return ("set", "--root", str(self.root), "--task", str(self.task if task is None else task),
                "--block", "T-01", "--expected-revision", revision, "--operation-id", operation_id,
                "--field", field)

    def note_arguments(self, note: str, revision: str,
                       task: Path | None = None) -> tuple[str, ...]:
        return ("append-note", "--root", str(self.root), "--task",
                str(self.task if task is None else task), "--block", "T-01",
                "--expected-revision", revision, "--operation-id", OPERATION_ID, "--note", note)

    def temporary_files(self, task: Path | None = None) -> list[str]:
        directory = self.task if task is None else task
        return sorted(path.name for path in directory.iterdir()
                      if TEMPORARY_FILE.fullmatch(path.name))

    def busy(self, result: ToolResult) -> dict[str, Any]:
        """An exit-5 refusal: one JSON object with the owner details and the no-bypass sentence."""
        document = self.write_refused(result, 5, "lock-busy")
        self.assertIn(REFUSAL_SENTENCE, result.stderr)
        self.assertIsNone(document["source_revision"])
        for key in ("lock_owner", "lock_age_seconds", "stale_suspected"):
            self.assertIn(key, document, result.stdout)
        return document


class LockContentionTests(RecoveryCase):
    def test_held_lock_with_old_metadata_is_refused_with_owner_details_until_the_holder_dies(
            self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        arguments = self.set_arguments("last_action=x", file_revision(path))
        holder = self.hold_lock()
        owner = self.owner(holder.pid)
        self.lock.write_text(json.dumps(owner) + "\n", encoding="utf-8")
        before = snapshot(self.task)

        with self.subTest(phase="lock held"):
            document = self.busy(self.run_tool(*arguments, "--lock-wait-seconds", "1"))

            self.assertEqual(document["lock_owner"], owner)
            self.assertIsInstance(document["lock_age_seconds"], int)
            self.assertGreaterEqual(document["lock_age_seconds"], STALE_AGE_SECONDS)
            self.assertLess(document["lock_age_seconds"], STALE_AGE_SECONDS + 60)
            self.assertIs(document["stale_suspected"], True)
            self.assertEqual(snapshot(self.task), before)

        holder.kill()
        self.assertEqual(holder.wait(timeout=PROCESS_TIMEOUT_SECONDS), -signal.SIGKILL)

        with self.subTest(phase="holder killed"):
            self.applied(self.run_tool(*arguments, "--lock-wait-seconds", "1"),
                         "last_action", "state_receipts")

    def test_owner_details_follow_the_recorded_start_time_with_a_zero_wait(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        arguments = self.set_arguments("last_action=x", file_revision(path))
        holder = self.hold_lock()
        fresh = self.owner(holder.pid, seconds_ago=5)
        undated = dict(fresh, started_at="yesterday")
        cases = {"fresh owner": (fresh, 5), "start time not readable": (undated, None)}
        for label, (owner, age) in cases.items():
            with self.subTest(case=label):
                self.lock.write_text(json.dumps(owner) + "\n", encoding="utf-8")
                before = snapshot(self.task)

                document = self.busy(self.run_tool(*arguments, "--lock-wait-seconds", "0"))

                self.assertEqual(document["lock_owner"], owner)
                if age is None:
                    self.assertIsNone(document["lock_age_seconds"])
                else:
                    self.assertIsInstance(document["lock_age_seconds"], int)
                    self.assertGreaterEqual(document["lock_age_seconds"], age)
                    self.assertLess(document["lock_age_seconds"], age + 60)
                self.assertIs(document["stale_suspected"], False)
                self.assertEqual(snapshot(self.task), before)

    def test_unreadable_metadata_while_the_lock_is_held_reports_no_owner(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        arguments = self.set_arguments("last_action=x", file_revision(path))
        self.hold_lock()
        cases = {"empty": b"", "not JSON": b"owner unknown\n", "JSON list": b"[1, 2]\n",
                 "JSON text": b"\"owner\"\n", "not UTF-8": b"\xff\xfe{}\n"}
        for label, content in cases.items():
            with self.subTest(case=label):
                self.lock.write_bytes(content)
                before = snapshot(self.task)

                document = self.busy(self.run_tool(*arguments, "--lock-wait-seconds", "0"))

                self.assertIsNone(document["lock_owner"])
                self.assertIsNone(document["lock_age_seconds"])
                self.assertIs(document["stale_suspected"], False)
                self.assertEqual(snapshot(self.task), before)

    def test_metadata_naming_a_live_process_without_the_lock_never_blocks(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        recorded = self.owner(os.getpid())
        self.lock.write_text(json.dumps(recorded) + "\n", encoding="utf-8")
        self.lock.chmod(0o600)

        self.applied(self.run_tool(*self.set_arguments("last_action=x", file_revision(path)),
                                   "--lock-wait-seconds", "0"), "last_action", "state_receipts")

        metadata = json.loads(self.lock.read_text(encoding="utf-8"))
        self.assertEqual(sorted(metadata), ["host", "owner_token", "pid", "started_at"])
        self.assertNotEqual(metadata["owner_token"], HOLDER_TOKEN)
        self.assertNotEqual(metadata["pid"], os.getpid())

    def test_refused_write_keeps_the_lock_file_with_its_own_metadata(self) -> None:
        self.write_state(state_text(leaf("T-01")))
        self.lock.write_text(json.dumps(self.owner(os.getpid())) + "\n", encoding="utf-8")
        self.lock.chmod(0o600)
        before = self.files_without_lock()

        self.write_refused(self.run_tool(*self.set_arguments("last_action=x", ZERO_REVISION)),
                           4, "revision-conflict")

        self.assert_unchanged_after_refusal(before)
        metadata = json.loads(self.lock.read_text(encoding="utf-8"))
        self.assertEqual(sorted(metadata), ["host", "owner_token", "pid", "started_at"])
        self.assertRegex(metadata["owner_token"], r"^[0-9a-f]{32}$")
        self.assertNotEqual(metadata["owner_token"], HOLDER_TOKEN)
        self.assertEqual(stat.S_IMODE(os.lstat(self.lock).st_mode), 0o600)


class InterruptionRecoveryTests(RecoveryCase):
    def reference_bytes(self, original: str, note: str) -> bytes:
        """Bytes of an uninterrupted append-note with the same inputs on a copy of the task."""
        copy = self.task_copy("task-reference", original)
        result = self.run_tool(*self.note_arguments(note, file_revision(copy / "state.md"),
                                                    task=copy))
        self.write_applied(result, "append-note", "notes", "state_receipts")
        return (copy / "state.md").read_bytes()

    def test_kill_before_replace_keeps_the_old_file_and_a_retry_applies_the_note_once(
            self) -> None:
        original = state_text(leaf("T-01"))
        path = self.write_state(original)
        initial = file_revision(path)
        note = "recorded after an interruption"
        expected = self.reference_bytes(original, note)

        result = self.finish(self.start_tool("kill-before-replace",
                                             *self.note_arguments(note, initial)))

        self.assertEqual(result.code, -signal.SIGKILL, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(path.read_bytes(), original.encode("utf-8"))
        leftovers = self.temporary_files()
        self.assertEqual(len(leftovers), 1, leftovers)
        leftover_bytes = (self.task / leftovers[0]).read_bytes()

        validation = self.output(self.run_tool("validate", "--root", str(self.root),
                                               "--task", str(self.task)))
        self.assertEqual(validation["stale_temp_files"], leftovers)
        self.assertEqual(self.temporary_files(), leftovers)

        retry = self.write_applied(self.append_notes(note, revision=initial), "append-note",
                                   "notes", "state_receipts")
        self.assertEqual(retry["stale_temp_files"], leftovers)
        self.assertEqual(path.read_bytes(), expected)
        self.assertEqual(self.state().count(note), 1)
        self.assertEqual(self.temporary_files(), leftovers)
        self.assertEqual((self.task / leftovers[0]).read_bytes(), leftover_bytes)

    def test_kill_after_replace_leaves_the_new_file_and_a_retry_is_already_applied(
            self) -> None:
        original = state_text(leaf("T-01"))
        path = self.write_state(original)
        initial = file_revision(path)
        note = "recorded before an interruption"
        expected = self.reference_bytes(original, note)

        result = self.finish(self.start_tool("kill-after-replace",
                                             *self.note_arguments(note, initial)))

        self.assertEqual(result.code, -signal.SIGKILL, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(path.read_bytes(), expected)
        self.assertEqual(self.temporary_files(), [])
        after = self.files_without_lock()

        retry = self.append_notes(note, revision=initial)

        document = self.output(retry)
        self.assertEqual(retry.code, 0, retry.stdout + retry.stderr)
        self.assertEqual(document["result"], "already_applied", retry.stdout)
        self.assertEqual(self.state().count(note), 1)
        self.assertEqual(self.files_without_lock(), after)

    def test_directory_sync_failure_after_the_rename_is_applied_with_a_warning(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        real_sync = os.fsync

        def failing_directory_sync(descriptor: int) -> None:
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise OSError(errno.EIO, "injected directory sync failure")
            real_sync(descriptor)

        with patch.dict(os.environ), patch.object(os, "fsync", failing_directory_sync):
            for key in [key for key in os.environ if key.startswith("STATE_TOOL_TEST_")]:
                del os.environ[key]
            result = InProcessTests.run_in_process(
                self, *self.set_arguments("last_action=synced", file_revision(path)))

        document = self.applied(result, "last_action", "state_receipts")
        self.assertEqual(document["warnings"], ["directory-sync-failed"])
        self.assertIn("directory-sync-failed", result.stderr)
        self.assertIn("  last_action: synced\n", self.state())
        self.assertEqual(document["result_revision"], file_revision(path))
        self.assertEqual(self.temporary_files(), [])


class RecheckTests(RecoveryCase):
    def pause_before_recheck(self, path: Path) -> tuple[subprocess.Popen[str], Path]:
        """Start a set that pauses before its recheck and return once it is proven paused."""
        resume = self.base / "resume"
        process = self.start_tool("pause-before-recheck",
                                  *self.set_arguments("last_action=x", file_revision(path)),
                                  resume=resume)
        deadline = time.monotonic() + PROCESS_TIMEOUT_SECONDS
        while not self.temporary_files():
            if process.poll() is not None:
                self.fail("the tool finished without pausing before the recheck: "
                          f"exit {process.returncode}")
            self.assertLess(time.monotonic(), deadline, "no temporary file appeared")
            time.sleep(POLL_SECONDS)
        with self.assertRaises(subprocess.TimeoutExpired,
                               msg="the tool did not stay paused before the recheck"):
            process.wait(timeout=PAUSE_PROOF_SECONDS)
        self.assertEqual(len(self.temporary_files()), 1)
        return process, resume

    def changed(self, process: subprocess.Popen[str], resume: Path) -> dict[str, Any]:
        resume.touch()
        result = self.finish(process)
        document = self.write_refused(result, 4, "state-file-changed")
        self.assertIn(REFUSAL_SENTENCE, result.stderr)
        self.assertEqual(self.temporary_files(), [])
        return document

    def test_rewrite_during_the_pause_is_refused_and_the_temporary_file_is_removed(
            self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        rewritten = state_text(leaf("T-01", name="Rewritten elsewhere")).encode("utf-8")
        process, resume = self.pause_before_recheck(path)
        inode = os.lstat(path).st_ino
        with path.open("r+b") as handle:
            handle.write(rewritten)
            handle.truncate()

        document = self.changed(process, resume)

        self.assertEqual(path.read_bytes(), rewritten)
        self.assertEqual(os.lstat(path).st_ino, inode)
        self.assertEqual(document["result_revision"], file_revision(path))

    def test_identical_bytes_under_a_new_inode_during_the_pause_are_refused(self) -> None:
        original = state_text(leaf("T-01")).encode("utf-8")
        path = self.write_state(original)
        process, resume = self.pause_before_recheck(path)
        inode = os.lstat(path).st_ino
        replacement = self.task / "replacement.md"
        replacement.write_bytes(original)
        os.replace(replacement, path)
        self.assertNotEqual(os.lstat(path).st_ino, inode)

        self.changed(process, resume)

        self.assertEqual(path.read_bytes(), original)

    def test_state_file_removed_during_the_pause_reports_no_result_revision(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        process, resume = self.pause_before_recheck(path)
        path.unlink()

        document = self.changed(process, resume)

        self.assertFalse(path.exists())
        self.assertIsNone(document["result_revision"])


class WritePathSafetyTests(RecoveryCase):
    def test_write_paths_outside_root_or_through_links_are_refused(self) -> None:
        text = state_text(leaf("T-01"))
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "state.md").write_text(text, encoding="utf-8")
        (self.root / "escape").symlink_to(outside, target_is_directory=True)
        revision = file_revision(outside / "state.md")
        outside_before = snapshot(outside)
        for label, task in {"dot-dot escape": self.root / ".." / "outside",
                            "symbolic link leaving root": self.root / "escape"}.items():
            with self.subTest(case=label):
                document = self.write_refused(
                    self.run_tool(*self.set_arguments("last_action=x", revision, task=task)),
                    2, "path-outside-root")

                self.assertIsNone(document["task"])
                self.assertIsNone(document["source_revision"])
                self.assertEqual(snapshot(outside), outside_before)

        (self.task / "real.md").write_text(text, encoding="utf-8")
        (self.task / "state.md").symlink_to("real.md")
        before = snapshot(self.task)
        with self.subTest(case="state file is a symbolic link"):
            document = self.write_refused(
                self.run_tool(*self.set_arguments("last_action=x", revision)),
                7, "unsafe-state-file")

            self.assertIsNone(document["source_revision"])
            self.assertEqual(snapshot(self.task), before)

    def test_lock_path_that_is_a_directory_or_a_named_pipe_is_refused(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        for label, make in {"directory": self.lock.mkdir,
                            "named pipe": lambda: os.mkfifo(self.lock, 0o600)}.items():
            with self.subTest(case=label):
                make()
                before = snapshot(self.task)

                document = self.write_refused(
                    self.run_tool(*self.set_arguments("last_action=x", file_revision(path))),
                    7, "unsafe-lock-path")

                self.assertIsNone(document["source_revision"])
                self.assertEqual(snapshot(self.task), before)
                if self.lock.is_dir():
                    self.lock.rmdir()
                else:
                    self.lock.unlink()

    @unittest.skipIf(os.geteuid() == 0, "permission bits do not restrict the superuser")
    def test_unwritable_task_directory_exits_7_with_the_file_unchanged(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        self.addCleanup(self.task.chmod, 0o755)
        for label, lock_present in {"lock file absent": False, "lock file present": True}.items():
            with self.subTest(case=label):
                self.task.chmod(0o755)
                if lock_present:
                    self.lock.touch(mode=0o600)
                self.task.chmod(0o555)
                before = self.files_without_lock()

                self.write_refused(
                    self.run_tool(*self.set_arguments("last_action=x", file_revision(path))),
                    7, "io-error")

                self.assertEqual(self.files_without_lock(), before)
                self.assertEqual(self.temporary_files(), [])
                self.assertEqual(self.lock.exists(), lock_present)


class FaultSeamTests(RecoveryCase):
    def test_unknown_fault_values_behave_exactly_as_unset(self) -> None:
        text = state_text(leaf("T-01"))
        for number, value in enumerate(("anything-else", "", "KILL-BEFORE-REPLACE",
                                        "kill-before-replace ", "pause-before-recheck-now")):
            with self.subTest(value=value):
                unset = self.task_copy(f"task-unset-{number}", text)
                faulted = self.task_copy(f"task-faulted-{number}", text)
                revision = file_revision(unset / "state.md")

                expected = self.run_tool(*self.set_arguments("last_action=x", revision, task=unset))
                actual = self.finish(self.start_tool(
                    value, *self.set_arguments("last_action=x", revision, task=faulted)))

                self.assertEqual(actual.code, expected.code, actual.stdout + actual.stderr)
                self.assertEqual(actual.stderr, expected.stderr)
                reports = [self.output(item) for item in (expected, actual)]
                for report in reports:
                    report.pop("task")
                self.assertEqual(reports[1], reports[0])
                self.assertEqual((faulted / "state.md").read_bytes(),
                                 (unset / "state.md").read_bytes())
                self.assertEqual(sorted(os.listdir(faulted)), sorted(os.listdir(unset)))


def strict_json(text: str) -> Any:
    """Parse text as standard JSON, refusing the non-finite number tokens Python accepts."""
    def refuse(token: str) -> Any:
        raise ValueError(f"non-standard JSON number token {token}")
    return json.loads(text, parse_constant=refuse)


class LockMetadataRobustnessTests(RecoveryCase):
    def test_metadata_that_cannot_be_reported_as_standard_json_reports_no_owner(self) -> None:
        path = self.write_state(state_text(leaf("T-01")))
        arguments = self.set_arguments("last_action=x", file_revision(path))
        self.hold_lock()
        cases = {"deeply nested object": b'{"a":' * 9997 + b"1" + b"}" * 9997,
                 "deeply nested array": b"[" * 60000,
                 "non-finite constants": b'{"pid": NaN, "x": Infinity}',
                 "negative infinity": b'{"pid": -Infinity}',
                 "number overflowing to infinity": b'{"pid": 1e999}'}
        for label, content in cases.items():
            with self.subTest(case=label):
                self.assertLess(len(content), 65536)
                self.lock.write_bytes(content)
                before = snapshot(self.task)

                result = self.run_tool(*arguments, "--lock-wait-seconds", "0")

                try:
                    document = strict_json(result.stdout)
                except (ValueError, RecursionError) as error:
                    self.fail(f"stdout is not one standard JSON object ({error}); exit "
                              f"{result.code}; stderr: {result.stderr[-300:]!r}")
                self.assertIsInstance(document, dict)
                self.assertEqual(result.code, 5, result.stdout[:300])
                self.assertEqual(document["result"], "rejected")
                self.assertEqual([item["code"] for item in document["errors"]], ["lock-busy"])
                self.assertIsNone(document.get("lock_owner", "missing"))
                self.assertIsNone(document.get("lock_age_seconds", "missing"))
                self.assertIs(document.get("stale_suspected"), False)
                self.assertIn(REFUSAL_SENTENCE, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(snapshot(self.task), before)


CONTRACT_VALIDATOR = ROOT / "scripts" / "validate-contracts.sh"
TASK_VALIDATOR = ROOT / "scripts" / "validate-task.sh"
REFERENCE_RULES = ROOT / "rules" / "workflow-reference.md"
COMPLETED_TASKS = ROOT / ".ai" / "tasks" / "completed"
RECEIPTS_DEFINITION = (
    "Tool-managed field state_receipts: <operation_id>#<16-hex digest>, … — at most 20 entries, "
    "oldest first; written only by scripts/state-tool.py; never edited or removed by hand or by "
    "/compress-state.")
READER_RULE = "a block without a `state_receipts:` line is valid"
PROTECTED_ENTRY = re.compile(r"^- `state_receipts:` lines.*$", re.M)
DEFINITION_CHECK = ("RECEIPTS: workflow-globals defines state_receipts: on one anchored line and "
                    "keeps blocks without it valid")
PROTECTED_CHECK = "RECEIPTS: the Protected Sections Contract protects state_receipts: lines"
VOCABULARY_CHECK = "RECEIPTS: the state tool vocabulary constants equal the anchored status lines"
VOCABULARY_CONSTANTS = ("ATOMIC_STATUS_VALUES", "ATOMIC_TESTS_VALUES", "ROLLUP_VALUES",
                        "INTEGRATION_VALIDATION_VALUES")
RECEIPTS_TASK_CHECK = "every state_receipts: line has 1 to 20 well-formed entries with unique operation ids"
ATOMIC_TESTS_MESSAGE = "not-started|red|pinned|green|n-a|failed expected"
ACCEPTANCE_START = "# ── End public identity smoke checks"
ACCEPTANCE_END = "hygiene_tracked_tree_result() {"
FOCUSED_DISPATCH = ('if [ "${1:-}" = --state-tool-only ]; then\n  shift\n'
                    '  exec python3 "$REPO_ROOT/tests/state-tool.py" "$@"\nfi\n')
ACCEPTANCE_NAME = "test_state_tool_acceptance"


def run_bash(arguments: list[str], cwd: Path) -> ToolResult:
    """Run bash on a validator script or on fragments copied from the contract validator."""
    environment = {key: value for key, value in os.environ.items()
                   if key != "STATE_TOOL_TEST_FAULT"}
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(["bash", *arguments], capture_output=True, text=True,
                               cwd=str(cwd), env=environment, timeout=60)
    return ToolResult(completed.returncode, completed.stdout, completed.stderr)


class ContractValidatorCase(unittest.TestCase):
    """Evaluate single contract-validator statements against a disposable copy of their inputs."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tree = Path(temporary.name)
        self.source = CONTRACT_VALIDATOR.read_text(encoding="utf-8")
        for path in (RULES, REFERENCE_RULES, TOOL):
            target = self.tree / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)

    def statement(self, name: str) -> str:
        head = f'check "{name}" \\\n'
        self.assertEqual(self.source.count(head), 1, f"validator statement missing: {name}")
        start = self.source.index(head)
        return self.source[start:self.source.index("\n", start + len(head)) + 1]

    def helpers(self, statement: str) -> str:
        """Return the validator functions the statement's expression calls, in call order."""
        found = []
        for name in re.findall(r"\$\(([A-Za-z_][A-Za-z_0-9]*)", statement):
            definitions = re.findall(rf"^{name}\(\) \{{\n.*?^\}}\n", self.source, re.M | re.S)
            self.assertLessEqual(len(definitions), 1, f"validator function repeated: {name}")
            found.extend(definitions)
        return "".join(found)

    def evaluate(self, name: str) -> str:
        """Return the one result line the validator statement prints in the disposable tree."""
        statement = self.statement(name)
        renderer = self.source[self.source.index("check() {"):self.source.index("\n# ── Group 1:")]
        script = ("PASS=0\nFAIL=0\nSKIP=0\n" + renderer + "\n" + self.helpers(statement)
                  + statement)
        result = run_bash(["-c", script], self.tree)
        self.assertEqual(result.code, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 1, result.stdout)
        return lines[0]

    def passes(self, name: str) -> None:
        self.assertEqual(self.evaluate(name), f"[PASS] {name}")

    def fails(self, name: str) -> None:
        self.assertTrue(self.evaluate(name).startswith(f"[FAIL] {name}: "))

    def edit(self, path: Path, old: str, new: str) -> None:
        """Replace one exact occurrence of old in the disposable copy of path."""
        target = self.tree / path.relative_to(ROOT)
        text = target.read_text(encoding="utf-8")
        self.assertEqual(text.count(old), 1, f"mutation anchor not unique in {path.name}: {old!r}")
        target.write_text(text.replace(old, new, 1), encoding="utf-8")

    def restore(self, path: Path) -> None:
        shutil.copyfile(path, self.tree / path.relative_to(ROOT))


class ContractValidatorTests(ContractValidatorCase):
    def test_receipts_definition_passes_on_source_and_fails_without_its_anchored_line(self) -> None:
        self.passes(DEFINITION_CHECK)
        line = RECEIPTS_DEFINITION + "\n"
        mutations = {
            "anchored line absent": (RULES, line, ""),
            "anchored line repeated": (RULES, line, line + line),
            "anchored line altered": (RULES, line, line.replace("at most 20", "at most 21")),
            "reader rule absent": (RULES, READER_RULE, "a block is read"),
        }
        for label, (path, old, new) in mutations.items():
            with self.subTest(mutation=label):
                self.restore(path)
                self.edit(path, old, new)
                self.fails(DEFINITION_CHECK)

    def test_protected_entry_passes_on_source_and_fails_when_absent_or_outside_the_contract(self) -> None:
        self.passes(PROTECTED_CHECK)
        text = REFERENCE_RULES.read_text(encoding="utf-8")
        entries = PROTECTED_ENTRY.findall(text)
        self.assertEqual(len(entries), 1, entries)
        entry = entries[0] + "\n"
        for label, new in (("entry absent", ""), ("entry renamed", entry.replace("state_receipts", "receipts"))):
            with self.subTest(mutation=label):
                self.restore(REFERENCE_RULES)
                self.edit(REFERENCE_RULES, entry, new)
                self.fails(PROTECTED_CHECK)
        with self.subTest(mutation="entry outside the contract"):
            self.restore(REFERENCE_RULES)
            self.edit(REFERENCE_RULES, entry, "")
            target = self.tree / REFERENCE_RULES.relative_to(ROOT)
            target.write_text(target.read_text(encoding="utf-8") + "\n" + entry, encoding="utf-8")
            self.fails(PROTECTED_CHECK)

    def test_vocabulary_constants_pass_on_source_and_fail_on_any_value_or_order_drift(self) -> None:
        self.passes(VOCABULARY_CHECK)
        tool_text = TOOL.read_text(encoding="utf-8")
        for name in VOCABULARY_CONSTANTS:
            lines = re.findall(rf"^{name} = \(.*\)$", tool_text, re.M)
            self.assertEqual(len(lines), 1, name)
            values = ast.literal_eval(lines[0].split(" = ", 1)[1])
            for label, changed in (("last value dropped", values[:-1]),
                                   ("first two values swapped", (values[1], values[0], *values[2:]))):
                with self.subTest(constant=name, mutation=label):
                    self.restore(TOOL)
                    self.edit(TOOL, lines[0] + "\n", f"{name} = {changed!r}\n")
                    self.fails(VOCABULARY_CHECK)
        self.restore(TOOL)
        anchor = "Status values for `rollup`: `not-started` | `in-progress` | `done` | `blocked`."
        with self.subTest(mutation="anchored line gained a value"):
            self.edit(RULES, anchor, anchor[:-1] + " | `paused`.")
            self.fails(VOCABULARY_CHECK)


class ValidatorRegistrationTests(unittest.TestCase):
    def test_focused_mode_and_default_registration_run_this_suite(self) -> None:
        source = CONTRACT_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(source.count(FOCUSED_DISPATCH), 1, "focused --state-tool-only mode missing")
        self.assertLess(source.index(FOCUSED_DISPATCH), source.index('if [ "$#" -gt 0 ]; then'))
        functions = re.findall(rf"^{ACCEPTANCE_NAME}\(\) \{{\n.*?^\}}\n", source, re.M | re.S)
        self.assertEqual(len(functions), 1, "acceptance function missing")
        self.assertIn('python3 "$REPO_ROOT/tests/state-tool.py"', functions[0])
        head = (f'check "{ACCEPTANCE_NAME}" \\\n'
                f'  "$({ACCEPTANCE_NAME} && echo pass || echo \'')
        self.assertEqual(source.count(head), 1, "default-run registration missing")
        position = source.index(head)
        self.assertLess(source.index(ACCEPTANCE_START), position)
        self.assertLess(position, source.index(ACCEPTANCE_END))
        self.assertLess(source.index(functions[0]), position)


def task_state(*blocks: str, progress: bool = True, preamble: str = "") -> str:
    """Return a task state.md that the task validator reads as a conforming full-tier task."""
    text = ("spec_path: .ai/specs/demo.md\nflow: full\n\n## Phases\n- discovery: in-progress\n"
            "- execution: not-started\n- validation: not-started\n\n" + preamble)
    if progress:
        text += "## Subtask Progress\n\n" + "\n".join(blocks)
    return text


def receipts_leaf(block_id: str, value: str | None, notes: str = "  notes:\n") -> str:
    receipts_line = "" if value is None else f"  state_receipts:{' ' + value if value else ''}\n"
    return leaf(block_id, body=f"  last_action:\n  target_files:\n  blocker: none\n{notes}{receipts_line}")


class TaskValidatorReceiptsTests(StateToolCase):
    def validate_task(self, text: str) -> ToolResult:
        self.write_state(text)
        return run_bash([str(TASK_VALIDATOR), str(self.task)], self.base)

    def rejected(self, text: str) -> None:
        result = self.validate_task(text)
        self.assertEqual(result.code, 1, result.stdout)
        self.assertIn(f"[FAIL] {RECEIPTS_TASK_CHECK}: ", result.stdout)

    def accepted(self, text: str) -> None:
        result = self.validate_task(text)
        self.assertEqual(result.code, 0, result.stdout)
        self.assertIn(f"[PASS] {RECEIPTS_TASK_CHECK}\n", result.stdout)

    def test_receipts_line_with_twenty_one_entries_fails(self) -> None:
        self.rejected(task_state(receipts_leaf("T-01", receipts(21))))

    def test_malformed_receipt_entries_fail(self) -> None:
        digest = "0123456789abcdef"
        cases = {"uppercase digest": "op-1#0123456789ABCDEF",
                 "short digest": "op-1#0123456789abcde",
                 "long digest": "op-1#0123456789abcdef0",
                 "missing separator": "op-1" + digest,
                 "two separators": f"op-1#{digest}#{digest}",
                 "identifier starts with punctuation": f"-op#{digest}",
                 "identifier with a space": f"op 1#{digest}",
                 "identifier over 64 characters": "A" * 65 + f"#{digest}",
                 "entries joined without a space": f"op-1#{digest},op-2#{digest}",
                 "trailing separator": f"op-1#{digest}, ",
                 "empty value": "",
                 "malformed entry after a valid one": f"op-1#{digest}, op-2#xyz"}
        for label, value in cases.items():
            with self.subTest(case=label):
                self.rejected(task_state(receipts_leaf("T-01", value)))

    def test_repeated_operation_id_fails(self) -> None:
        value = "op-1#0123456789abcdef, op-2#0123456789abcdef, op-1#fedcba9876543210"
        self.rejected(task_state(receipts_leaf("T-01", value)))

    def test_bad_receipts_in_any_block_fail_even_when_another_block_is_well_formed(self) -> None:
        self.rejected(task_state(receipts_leaf("T-01", receipts(3)),
                                 receipts_leaf("T-02", "op-1#0123456789abcdef, op-1#0123456789abcdef")))

    def test_well_formed_receipts_pass(self) -> None:
        composite = (COMPOSITE_T02.rstrip("\n").replace("  notes:", "  notes: composite rationale")
                     + "\n  state_receipts: init.T-02#00000000000000ff\n")
        prose = ("  notes: receipts are tool-managed\n"
                 "         state_receipts: x is how the field begins, not a field line\n")
        self.accepted(task_state(receipts_leaf("T-01", receipts(20)), composite,
                                 receipts_leaf("T-03", "A" + "b" * 62 + "9#0123456789abcdef"),
                                 receipts_leaf("T-04", None, notes=prose)))

    def test_task_without_receipts_passes(self) -> None:
        self.accepted(task_state(receipts_leaf("T-01", None), receipts_leaf("T-02", None)))

    def test_task_without_progress_section_ignores_receipts_text(self) -> None:
        preamble = "## Task Analysis\n  state_receipts: not a block field\n\n"
        result = self.validate_task(task_state(progress=False, preamble=preamble))
        self.assertEqual(result.code, 0, result.stdout)
        self.assertNotIn("state_receipts", result.stdout)

    def test_atomic_tests_vocabulary_message_names_all_six_values(self) -> None:
        text = task_state(receipts_leaf("T-01", None)).replace("atomic-tests: not-started",
                                                               "atomic-tests: bogus")
        result = self.validate_task(text)
        self.assertEqual(result.code, 1, result.stdout)
        self.assertIn(f"[FAIL] atomic-tests: uses the canonical vocabulary: {ATOMIC_TESTS_MESSAGE}",
                      result.stdout)

    def test_completed_task_directories_still_conform(self) -> None:
        directories = sorted(path for path in COMPLETED_TASKS.iterdir() if (path / "state.md").is_file())
        self.assertTrue(directories)
        for directory in directories:
            with self.subTest(task=directory.name):
                result = run_bash([str(TASK_VALIDATOR), str(directory)], ROOT)
                self.assertEqual(result.code, 0, result.stdout[-2000:])


GIT_FIELD_LINES = ("  branch: feat/demo\n  base_branch: main\n  base_commit: " + "a" * 40 + "\n"
                   "  commits: none\n  pr: none\n")
FIELD_NAME = re.compile(r"^  ([a-z][a-z0-9_-]*):(?: .*)?$")


class ReceiptsPositionRuleTests(SetCase):
    def receipts_paragraph(self) -> str:
        text = RULES.read_text(encoding="utf-8")
        self.assertEqual(text.count(RECEIPTS_DEFINITION + "\n"), 1)
        start = text.index(RECEIPTS_DEFINITION)
        return text[start:text.index("**Backward compatibility", start)]

    def field_before_receipts(self, body: str) -> str:
        """Apply one write to a leaf with the given body; return the field line written before the receipts."""
        self.write_state(state_text(leaf("T-01", body=body)))
        self.applied(self.set_fields("last_action=x"), "last_action", "state_receipts")
        lines = self.state().splitlines()
        index = next(number for number, line in enumerate(lines) if line.startswith("  state_receipts:"))
        field = next(line for line in reversed(lines[:index]) if FIELD_NAME.match(line))
        return FIELD_NAME.match(field).group(1)

    def test_rule_states_the_receipts_position_the_tool_writes(self) -> None:
        paragraph = self.receipts_paragraph()
        plain = "  last_action:\n  target_files:\n  blocker: none\n  notes: first\n         second\n"
        positions = {"without git fields": self.field_before_receipts(plain),
                     "with git fields": self.field_before_receipts(plain + GIT_FIELD_LINES)}
        self.assertEqual(positions, {"without git fields": "notes", "with git fields": "pr"})
        for label, field in positions.items():
            with self.subTest(block=label):
                self.assertIn(f"`{field}:`", paragraph)
        self.assertNotRegex(paragraph, r"[Tt]he line follows the block's last `notes:` group\.")


STATE_TOOL_PATTERNS = (".state-tool.lock", ".state.md.*.tmp")
SETUP_SCRIPT = ROOT / "scripts" / "setup-new-project.sh"
MANUAL = ROOT / "docs" / "USAGE.md"
SCRIPT_INVENTORY = ROOT / "scripts" / "README.md"
ISOLATED_VARIABLES = frozenset({
    "HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "ORCHESTRAIL_HOME",
    "ORCHESTRAIL_LOG_ROOT", "BASH_ENV", "ENV", "CDPATH", "PYTHONPATH", "PYTHONSTARTUP",
    "STATE_TOOL_TEST_FAULT", "STATE_TOOL_TEST_RESUME"})


def run_isolated(arguments: list[str], cwd: Path, home: Path, stdin: str = "") -> ToolResult:
    """Run git or the project setup script with HOME and the XDG roots inside a disposable tree.

    Inherited git variables and shell startup files are dropped, the source root is this
    checkout, and the running interpreter's directory leads PATH so that the setup script's
    python3 never resolves to a version-manager shim that would install into the fake home.
    """
    environment = {key: value for key, value in os.environ.items()
                   if key not in ISOLATED_VARIABLES and not key.startswith("GIT_")}
    environment.update(
        HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"),
        XDG_STATE_HOME=str(home / ".local" / "state"), XDG_CACHE_HOME=str(home / ".cache"),
        ORCHESTRAIL_HOME=str(ROOT), GIT_CONFIG_NOSYSTEM="1", PYTHONDONTWRITEBYTECODE="1",
        PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", os.defpath))
    completed = subprocess.run(arguments, capture_output=True, text=True, cwd=str(cwd),
                               env=environment, input=stdin, timeout=60)
    return ToolResult(completed.returncode, completed.stdout, completed.stderr)


class DisposableHomeCase(unittest.TestCase):
    """Provide a disposable home directory below a temporary base for isolated processes."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.home = self.base / "home"
        (self.home / ".claude" / "skills" / "demo-skill").mkdir(parents=True)


class RepositoryIgnoreRuleTests(DisposableHomeCase):
    def ignored(self, relative: str, *options: str) -> int:
        """Return the exit of git check-ignore for a path of this repository."""
        result = run_isolated(["git", "check-ignore", "-q", *options, "--", relative], ROOT,
                              self.home)
        self.assertIn(result.code, (0, 1), result.stderr)
        return result.code

    def test_repository_ignores_the_tool_files_and_never_a_task_state_file(self) -> None:
        task = ".ai/tasks/todo/task-x/"
        cases = {"lock file": (task + ".state-tool.lock", 0),
                 "temporary file": (task + ".state.md.0123456789abcdef0123456789abcdef.tmp", 0),
                 "task state file": (task + "state.md", 1)}
        for label, (relative, expected) in cases.items():
            with self.subTest(path=label):
                self.assertEqual(self.ignored(relative), expected)
        existing = sorted(path.relative_to(ROOT).as_posix()
                          for path in (ROOT / ".ai" / "tasks").glob("*/*/state.md"))
        self.assertTrue(existing, "no task state file found in this repository")
        for relative in [task + "state.md", *existing]:
            with self.subTest(path=relative, index="not consulted"):
                self.assertEqual(self.ignored(relative, "--no-index"), 1)


class ConsumerSetupIgnoreTests(DisposableHomeCase):
    def new_project(self, name: str, ignore_text: str | None = None) -> Path:
        """Create a disposable git project, optionally with an initial .gitignore."""
        project = self.base / name
        project.mkdir()
        initialized = run_isolated(["git", "init", "-q"], project, self.home)
        self.assertEqual(initialized.code, 0, initialized.stderr)
        if ignore_text is not None:
            (project / ".gitignore").write_text(ignore_text, encoding="utf-8")
        return project

    def set_up_twice(self, project: Path) -> list[str]:
        """Run the setup script twice in the project and return its .gitignore lines."""
        for _ in range(2):
            result = run_isolated(["bash", str(SETUP_SCRIPT)], project, self.home, stdin="2\n")
            self.assertEqual(result.code, 0, result.stdout + result.stderr)
        registry = self.home / ".config" / "orchestrail" / "projects"
        self.assertIn(str(project), registry.read_text(encoding="utf-8").splitlines(),
                      "setup did not register the project in the disposable configuration root")
        return (project / ".gitignore").read_text(encoding="utf-8").splitlines()

    def test_setup_run_twice_creates_the_ignore_file_with_each_tool_pattern_once(self) -> None:
        project = self.new_project("fresh consumer")
        self.assertFalse((project / ".gitignore").exists())

        lines = self.set_up_twice(project)

        for pattern in (*STATE_TOOL_PATTERNS, ".ai/"):
            with self.subTest(pattern=pattern):
                self.assertEqual(lines.count(pattern), 1, lines)

    def test_setup_does_not_repeat_a_tool_pattern_the_project_already_ignores(self) -> None:
        for index, present in enumerate(STATE_TOOL_PATTERNS):
            with self.subTest(present=present):
                project = self.new_project(f"consumer {index}", f"{present}\n")

                lines = self.set_up_twice(project)

                self.assertEqual(lines[0], present)
                for pattern in STATE_TOOL_PATTERNS:
                    self.assertEqual(lines.count(pattern), 1, lines)

    def test_tracking_consumer_step_states_what_rerunning_setup_does_to_the_knowledge_base(self) -> None:
        project = self.new_project("tracking consumer", "node_modules/\n")
        tracked = project / ".ai" / "tasks" / "todo" / "task-01-a" / "state.md"
        tracked.parent.mkdir(parents=True)
        tracked.write_text("tracked task state\n", encoding="utf-8")
        added = run_isolated(["git", "add", "--", ".ai/tasks/todo/task-01-a/state.md"], project,
                             self.home)
        self.assertEqual(added.code, 0, added.stderr)

        lines = self.set_up_twice(project)
        probe = run_isolated(["git", "check-ignore", "-q", "--", ".ai/tasks/todo/task-02-b/state.md"],
                             project, self.home)
        self.assertIn(probe.code, (0, 1), probe.stderr)
        rerun_ignores_new_knowledge = ".ai/" in lines and probe.code == 0

        manual = MANUAL.read_text(encoding="utf-8")
        heading = STATE_TOOL_HEADING.search(manual)
        self.assertIsNotNone(heading, "manual State tool section missing")
        following = re.compile(r"^## ", re.M).search(manual, heading.end())
        section = manual[heading.end():following.start() if following else len(manual)]
        paragraphs = [paragraph for paragraph in re.split(r"\n\s*\n", section)
                      if re.search(r"(?i)\btrack", paragraph) and "`.ai/`" in paragraph
                      and "scripts/setup-new-project.sh" in paragraph
                      and re.search(r"(?i)\bby hand\b", paragraph)]
        self.assertEqual(len(paragraphs), 1, "consumer step naming both routes missing or repeated")
        sentences = re.split(r"(?<=\.)\s+", " ".join(paragraphs[0].split()))
        warns = any("`.ai/`" in sentence and re.search(r"(?i)\b(?:appends|adds)\b", sentence)
                    and re.search(r"(?i)\bremov", sentence) for sentence in sentences)
        self.assertEqual(warns, rerun_ignores_new_knowledge,
                         "the consumer step must warn that rerunning setup appends the .ai/ entry, "
                         "which must be removed again, exactly when the setup script does so")


STATE_TOOL_HEADING = re.compile(r"^## (?:[0-9]+\. )?State tool$", re.I | re.M)
FALLBACK_STEPS = (r"(?i)\bstop\b.*\bconcurrent writers\b", r"(?i)\bread the whole block\b",
                  r"(?i)\bchange only the needed fields\b", r"(?i)\breview the diff\b",
                  r"`scripts/validate-task\.sh`", r"(?i)\brecord the reason\b.*`notes:`")
COMMANDS = ("get", "validate", "set", "append-note", "add-file", "init-block")


def tool_exit_codes() -> dict[int, list[str]]:
    """Return the error codes the tool's own description lists for each exit code."""
    description = " ".join(ast.get_docstring(ast.parse(TOOL.read_text(encoding="utf-8"))).split())
    text = description[description.index("Exit codes:") + len("Exit codes:"):
                       description.index(" validate exits")]
    segments = re.split(r";\s+(?=[0-9] )", text.strip())
    return {int(segment.split()[0]): re.findall(r"\b[a-z]+(?:-[a-z]+)+\b", segment)
            for segment in segments}


def numbered_items(text: str) -> list[str]:
    """Return the items of ordered lists in the text, each with its continuation lines."""
    items: list[str] = []
    current = False
    for line in text.splitlines():
        match = re.match(r"[0-9]+\. (\S.*)", line)
        if match:
            items.append(match.group(1))
            current = True
        elif current and line.startswith("   ") and line.strip():
            items[-1] += " " + line.strip()
        else:
            current = False
    return items


class ManualTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manual = MANUAL.read_text(encoding="utf-8")

    def section(self, heading: re.Pattern[str]) -> str:
        """Return the text below one level-two heading of the manual, up to the next one."""
        matches = list(heading.finditer(self.manual))
        self.assertEqual(len(matches), 1, f"manual section missing or repeated: {heading.pattern}")
        start = matches[0].end()
        following = re.compile(r"^## ", re.M).search(self.manual, start)
        return self.manual[start:following.start() if following else len(self.manual)]

    def test_setup_table_entry_list_names_both_tool_patterns(self) -> None:
        setup = self.section(re.compile(r"^## 5\. Adding the System to a Project$", re.M))
        rows = [line for line in setup.splitlines()
                if line.startswith("|") and "`.gitignore` entries" in line]
        self.assertEqual(len(rows), 1, "setup table entry list missing or repeated")
        for pattern in STATE_TOOL_PATTERNS:
            with self.subTest(pattern=pattern):
                self.assertIn(f"`{pattern}`", rows[0])

    def test_state_tool_section_lists_the_manual_fallback_steps_in_order(self) -> None:
        items = numbered_items(self.section(STATE_TOOL_HEADING))
        position = 0
        for pattern in FALLBACK_STEPS:
            index = next((number for number in range(position, len(items))
                          if re.search(pattern, items[number])), None)
            self.assertIsNotNone(index, f"fallback step missing or out of order: {pattern}")
            position = index + 1

    def test_state_tool_section_tells_a_tracking_consumer_to_rerun_setup_or_edit_by_hand(self) -> None:
        paragraphs = re.split(r"\n\s*\n", self.section(STATE_TOOL_HEADING))
        matching = [paragraph for paragraph in paragraphs
                    if re.search(r"(?i)\btrack", paragraph) and "`.ai/`" in paragraph
                    and "scripts/setup-new-project.sh" in paragraph
                    and re.search(r"(?i)\bby hand\b", paragraph)
                    and all(f"`{pattern}`" in paragraph for pattern in STATE_TOOL_PATTERNS)]
        self.assertEqual(len(matching), 1, "consumer step for projects that track .ai/ missing")

    def test_state_tool_section_lists_the_six_commands_and_every_exit_code(self) -> None:
        section = self.section(STATE_TOOL_HEADING)
        for command in COMMANDS:
            with self.subTest(command=command):
                self.assertRegex(section, rf"python3 scripts/state-tool\.py {re.escape(command)} ")
        rows: dict[int, list[str]] = {}
        for line in section.splitlines():
            match = re.match(r"\| *`?([0-9]+)`? *\|(.*\S.*)\|$", line)
            if match:
                rows.setdefault(int(match.group(1)), []).append(match.group(2))
        expected = tool_exit_codes()
        self.assertEqual(sorted(expected), list(range(9)))
        self.assertEqual(sorted(rows), list(range(9)), "exit-code table must list 0 to 8")
        self.assertRegex(" ".join(rows[0]), r"(?i)\bapplied\b")
        for code, names in expected.items():
            self.assertEqual(len(rows[code]), 1, f"exit {code} listed more than once")
            for name in names:
                with self.subTest(exit=code, error=name):
                    self.assertIn(f"`{name}`", rows[code][0])

    def test_state_tool_section_keeps_refusals_binding_and_states_the_limits(self) -> None:
        section = self.section(STATE_TOOL_HEADING)
        self.assertIn(REFUSAL_SENTENCE, section)
        statements = {"optional": r"(?i)\boptional\b",
                      "not wired": r"(?i)\bno workflow\b",
                      "external editors": r"(?i)\bexternal editors?\b",
                      "local file systems": r"(?i)\blocal file ?systems?\b",
                      "reads without fcntl": r"`fcntl`",
                      "temporary files kept": r"(?is)`\.state\.md\.\*\.tmp`.{0,300}\bnever deleted\b"}
        for label, pattern in statements.items():
            with self.subTest(statement=label):
                self.assertRegex(section, pattern)

    def test_manual_reference_sections_name_the_tool_its_mode_and_its_receipts_field(self) -> None:
        tree = self.section(re.compile(r"^## 2\. Directory Structure$", re.M))
        self.assertRegex(tree, r"(?m)^│   [├└]── state-tool\.py +\S")
        roles = self.section(re.compile(r"^## 9\. File Roles Quick Reference$", re.M))
        self.assertRegex(roles, r"(?m)^\| `scripts/state-tool\.py` +\| +\S")
        reference = self.section(re.compile(r"^## 10\. Status & Contract Quick Reference$", re.M))
        self.assertIn("`state_receipts:`", reference)
        self.assertIn("--state-tool-only", self.section(STATE_TOOL_HEADING))

    def test_script_inventory_has_a_row_for_the_state_tool(self) -> None:
        inventory = SCRIPT_INVENTORY.read_text(encoding="utf-8")
        self.assertRegex(inventory, r"(?m)^\| `state-tool\.py` \| [^|]*\S[^|]* \|$")


if __name__ == "__main__":
    unittest.main()
