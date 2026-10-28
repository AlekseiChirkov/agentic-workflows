"""Validate cached model-selection callers and executable offline guide examples."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any
import unittest

# Any represents heterogeneous JSON CLI reports emitted by the executable guide.
# Assertions below check the specific report fields required by each caller contract.
ROOT = Path(__file__).resolve().parents[1]
GUIDE = "docs/MODEL-CATALOG.md"
REFERENCE = "workflow-reference → ### Model columns and resolution"
EXECUTORS = ("spec-run", "pe-execute", "phase-atomic-execution")
PRESERVERS = ("pd-decompose", "pd-design", "pd-finalize")
DERIVED = ("docs/USAGE.md", "docs/SPEC-RUN-QUICKSTART.md", "docs/README.md",
           "workflows/PIPELINE.md")
HELPERS = ("model-catalog.py", "model_selection.py", "model_plan.py")


def reachability_errors(root: Path) -> list[str]:
    errors = []
    for relative in (GUIDE, *(f"scripts/{name}" for name in HELPERS)):
        if not (root / relative).is_file():
            errors.append(f"missing {relative}")
    canonical = root / "rules/workflow-reference.md"
    if not canonical.is_file() or "### Model columns and resolution" not in canonical.read_text():
        errors.append("missing canonical model resolution section")
    for reader in (*EXECUTORS, *PRESERVERS, "pd-select-model"):
        path = root / f"workflows/{reader}.md"
        if not path.is_file() or REFERENCE not in path.read_text():
            errors.append(f"unreachable resolution contract: {reader}")
    for relative in DERIVED:
        path = root / relative
        if not path.is_file() or "MODEL-CATALOG.md" not in path.read_text():
            errors.append(f"unreachable catalog guide: {relative}")
    return errors


class WorkflowContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        path = ROOT / relative
        self.assertTrue(path.is_file(), f"required caller documentation missing: {relative}")
        return path.read_text(encoding="utf-8")

    def patterns(self, content: str, patterns: tuple[str, ...]) -> None:
        for pattern in patterns:
            with self.subTest(contract=pattern):
                self.assertTrue(re.search(pattern, content, re.I | re.S) is not None,
                                f"missing caller contract: {pattern}")

    def canonical(self) -> str:
        text = self.read("rules/workflow-reference.md")
        self.assertTrue("### Model columns and resolution" in text,
                        "canonical optional model columns and resolution are absent")
        parent = text.split("## Parent `plan.md` Table Format", 1)[1].split("\n## ", 1)[0]
        self.assertIn("### Model columns and resolution", parent,
                      "model columns belong to the canonical parent plan table definition")
        return parent.split("### Model columns and resolution", 1)[1]

    def examples(self) -> dict[str, dict[str, Any]]:
        text = self.read(GUIDE)
        blocks = re.findall(r"^```bash model-catalog-example\n(.*?)^```\s*$", text, re.M | re.S)
        self.assertEqual(len(blocks), 1, "provide one complete, independently runnable CLI fixture")
        with tempfile.TemporaryDirectory(prefix="workflow-guide-") as temporary:
            directory = Path(temporary)
            guard = directory / "guard"
            guard.mkdir()
            (guard / "sitecustomize.py").write_text(
                "import socket\n"
                "def denied(*args: object, **kwargs: object) -> None:\n"
                "    raise AssertionError('network forbidden in offline guide')\n"
                "socket.socket = denied\nsocket.create_connection = denied\n")
            environment = dict(os.environ, HOME=str(directory / "home"),
                               XDG_CONFIG_HOME=str(directory / "config"),
                               XDG_STATE_HOME=str(directory / "state"), TMPDIR=str(directory),
                               ORCHESTRAIL_HOME=str(ROOT), ORCHESTRAIL_LOG_ROOT=str(directory / "logs"),
                               PYTHONPATH=str(guard))
            result = subprocess.run(["bash", "-eu", "-c", blocks[0]], cwd=directory,
                                    env=environment, text=True, capture_output=True, timeout=30,
                                    check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        reports = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        self.assertTrue(reports, "CLI example must emit inspectable JSON scenario reports")
        self.assertEqual(len(reports), len({report["example"] for report in reports}))
        return {report["example"]: report for report in reports}

    def test_selector_cached_single_bulk_contract_is_compact_and_reachable(self) -> None:
        text = self.read("workflows/pd-select-model.md")
        self.assertLessEqual(len(text.split()), 1500, "selector exceeds its invocation context budget")
        self.patterns(text, (r"Invocation:.*path-to-atomic-description.*task-directory.*--refresh",
                             r"Single.*chat", r"Bulk.*plan\.md", r"model-catalog\.py",
                             r"--catalog", r"--select", r"MODEL-CATALOG\.md"))
        self.assertTrue(REFERENCE in text, "selector must reach the canonical model contract")
        for obsolete in ("live web search (every run", "never read or write a catalog cache",
                         "rebuilt every run", "live sources on every invocation"):
            self.assertNotIn(obsolete, text.lower())

    def test_selector_explicit_refresh_research_preserves_failed_install(self) -> None:
        text = self.read("workflows/pd-select-model.md")
        self.patterns(text, (r"only.*--refresh.*(?:research|brows)",
                             r"workflow.*(?:research|brows)", r"--refresh\s+(?:CANDIDATE|<candidate>)",
                             r"helper.*(?:never|does not).*brows", r"complete.*candidate",
                             r"validat.*atomic", r"fail.*(?:preserv|retain).*prior.*catalog"))

    def test_selector_unavailable_dependencies_preserve_session_without_eligibility_bypass(self) -> None:
        text = self.read("workflows/pd-select-model.md")
        self.patterns(text, (r"Python.*3\.11", r"missing.*helper", r"selection unavailable",
                             r"preserv.*session", r"explicit.*request.*(?:eligib|verif)",
                             r"(?:must not|never|do not).*bypass", r"(?:no|never).*historical.*(?:log|store)"))

    def test_selector_explicit_refresh_recovers_catalog_before_selection_availability_guard(self) -> None:
        text = self.read("workflows/pd-select-model.md")
        dependency_guard = text.split("### Step 0", 1)[1].split("Catalog:", 1)[0]
        self.assertNotIn("invalid catalog", dependency_guard,
                         "invalid catalog must not return before explicitly authorized repair")
        self.assertNotIn("absent current support", dependency_guard,
                         "refresh research must remain possible without selectable current support")
        self.patterns(text, (r"--refresh.*(?:missing|invalid).*catalog.*(?:initialize|repair|recover)",
                             r"refresh research.*does not require.*(?:support|selectable)"))

    def test_canonical_model_columns_define_empty_precedence_and_explicit_migration(self) -> None:
        text = self.canonical()
        self.patterns(text, (r"Model \(Claude\)", r"Model \(Codex\)", r"legacy.*`Model`",
                             r"present.*empty.*(?:overrid|precedence|default)",
                             r"missing.*(?:column|columns).*session", r"populated.*legacy",
                             r"explicit.*(?:value|decision).*every", r"null"))
        self.assertNotIn("Model (Claude)", self.read("rules/workflow-globals.md"),
                         "the provider-column definition has one canonical owner")

    def test_canonical_resolution_requires_invocation_support_permissions_and_restrictions(self) -> None:
        text = self.canonical()
        self.patterns(text, (r"(?:fresh|current).*invocation", r"harness\.date", r"permission",
                             r"restriction", r"context", r"owner", r"quality", r"tools",
                             r"(?:TTL|catalog age).*not.*support", r"provider.*name.*not.*support",
                             r"logging.*(?:file|capabilit).*not.*support"))

    def test_canonical_resolution_separates_request_resolution_and_observed_actual(self) -> None:
        text = self.canonical()
        self.patterns(text, (r"requested", r"resolved", r"actual", r"execution.*null",
                             r"recommendation.*resolution", r"(?:separate|independent).*current.*receipt",
                             r"caller.*provenance", r"spawn.*(?:alone|insufficient|does not)",
                             r"fallback.*authorized", r"(?:fallback.*eligible|eligible.*fallback)",
                             r"(?:stop|stopped)", r"actual.*(?:unknown|null)"))

    def test_execution_readers_resolve_before_request_and_preserve_inline_session(self) -> None:
        for reader in EXECUTORS:
            with self.subTest(reader=reader):
                text = self.read(f"workflows/{reader}.md")
                self.assertTrue(REFERENCE in text, f"{reader} must reach the canonical model contract")
                self.patterns(text, (r"--resolve-plan", r"(?:before|prior to).*(?:spawn|request|execut)",
                                     r"(?:same|current).*session", r"requested.*resolved.*actual"))

    def test_spec_run_unavailable_model_override_preserves_worker_role_boundaries(self) -> None:
        text = self.read("workflows/spec-run.md")
        selection = text.split("## Step 2 — Model selection", 1)[1].split("\n---", 1)[0]
        self.assertNotIn("continue in the same session", selection,
                         "the orchestrator must not implement inline when model override is unavailable")
        self.patterns(selection, (r"spawn.*(?:default|override)", r"worker.*unavailable.*stop",
                                  r"(?:never|do not).*inline"))

    def test_discovery_and_quickstart_readers_preserve_optional_columns_and_staleness(self) -> None:
        for reader in PRESERVERS:
            with self.subTest(reader=reader):
                self.assertTrue(REFERENCE in self.read(f"workflows/{reader}.md"),
                                f"{reader} must reach the canonical model contract")
        self.patterns(self.read("workflows/pd-decompose.md"),
                      (r"preserv.*(?:optional|model).*column", r"composite.*(?:blank|empty)"))
        self.patterns(self.read("workflows/pd-design.md"),
                      (r"(?:either|any).*provider.*(?:cell|column)", r"stale", r"bulk"))
        self.patterns(self.read("workflows/pd-finalize.md"),
                      (r"(?:optional|provider).*model.*column", r"legacy"))
        quickstart = self.read("docs/SPEC-RUN-QUICKSTART.md")
        self.patterns(quickstart, (r"Model \(Claude\)", r"Model \(Codex\)", r"legacy", r"actual.*unknown"))

    def test_operating_documents_reach_cached_guide_and_drop_retired_contract(self) -> None:
        for relative in DERIVED:
            with self.subTest(document=relative):
                text = self.read(relative)
                self.assertTrue("MODEL-CATALOG.md" in text, f"{relative} must link the catalog guide")
                self.assertNotRegex(text.lower(), r"every (?:run|invocation).*live (?:web|search)")
        self.patterns(self.read("docs/USAGE.md"), (r"--refresh", r"Model \(Claude\)", r"Model \(Codex\)"))
        self.patterns(self.read("workflows/PIPELINE.md"), (r"--refresh", r"session default"))

    def test_guide_documents_age_quality_economics_migration_and_ownership(self) -> None:
        text = self.read(GUIDE)
        self.patterns(text, (r"14.*30", r"31|over 30|more than 30", r"future.*(?:invalid|unavailable)",
                             r"rollback", r"disable", r"uncalibrated.*null", r"quality.*1.*5",
                             r"price_snapshot", r"comparable.*total.cost", r"cost_comparisons",
                             r"long-context.*heavy-reasoning", r"coding-heavy.*heavy-reasoning",
                             r"web-knowledge.*heavy-reasoning", r"cost-efficient-bulk.*mechanical",
                             r"general.*(?:none|empty|no trait)", r"telemetry.*owner",
                             r"calibration.*owner", r"historical.*(?:must not|never|do not|only)",
                             r"--model-workflow-only"))

    def test_guide_cli_refresh_success_and_rejection_preserve_prior_bytes(self) -> None:
        examples = self.examples()
        self.assertEqual(examples["refresh"]["exit_code"], 0)
        self.assertTrue(examples["refresh"]["report"]["refreshed"])
        rejected = examples["refresh-rejected"]
        self.assertEqual(rejected["exit_code"], 2)
        self.assertFalse(rejected["report"]["refreshed"])
        self.assertTrue(rejected["catalog_bytes_unchanged"])
        self.assertTrue(any("Refresh rejected" in error for error in rejected["report"]["errors"]))
        self.assertEqual(examples["inspect"]["report"]["status"], "fresh")

    def test_guide_cli_plan_compatibility_and_migration_are_explicit(self) -> None:
        examples = self.examples()
        legacy = examples["read-legacy"]["report"]["rows"][0]
        self.assertEqual(legacy["requested"], {"provider": "openai", "id": "fixture-middle"})
        self.assertEqual(legacy["source"], "Model")
        empty = examples["read-dual-empty"]["report"]["rows"][0]
        self.assertIsNone(empty["requested"])
        self.assertEqual(empty["source"], "Model (Codex)")
        self.assertIsNone(examples["read-missing"]["report"]["rows"][0]["requested"])
        self.assertEqual(examples["migration-rejected"]["exit_code"], 2)
        self.assertTrue(examples["migration-rejected"]["plan_bytes_unchanged"])
        self.assertEqual(examples["update"]["report"]["status"], "updated")
        self.assertTrue(examples["update"]["unrelated_bytes_preserved"])

    def test_guide_cli_resolution_surfaces_request_fallback_stop_and_unknown_actual(self) -> None:
        examples = self.examples()
        cases = (("resolve-requested", "resolved", "fixture-middle"),
                 ("resolve-fallback", "fallback", "fixture-strong"),
                 ("resolve-stop", "stopped", None),
                 ("resolve-default", "session-default", "fixture-strong"))
        for name, status, model in cases:
            with self.subTest(example=name):
                report = examples[name]["report"]
                self.assertEqual(report["status"], status)
                self.assertEqual(report["resolved"], None if model is None else
                                 {"provider": "openai", "id": model})
                self.assertIsNone(report["actual"])
        requested = examples["resolve-stop"]["report"]["requested"]
        self.assertEqual(requested, {"provider": "openai", "id": "fixture-absent"})
        self.assertEqual(examples["resolve-stop"]["exit_code"], 2)

    def test_guide_cli_default_path_and_missing_dependencies_preserve_session(self) -> None:
        examples = self.examples()
        self.assertEqual(examples["default-path"]["exit_code"], 0)
        self.assertEqual(examples["default-path"]["report"]["status"], "fresh")
        for name in ("missing-catalog", "missing-helper", "missing-python"):
            with self.subTest(example=name):
                case = examples[name]
                self.assertEqual(case["exit_code"], 2)
                self.assertEqual(case["report"]["status"], "unavailable")
                self.assertEqual(case["report"]["session_action"], "preserve")
                self.assertIsNone(case["report"].get("resolved"))
                self.assertIsNone(case["report"].get("actual"))
                self.assertTrue(case["report"]["errors"])

    def test_guide_cli_current_support_tools_and_unknown_quality_cannot_be_inferred(self) -> None:
        examples = self.examples()
        restricted = examples["restricted-tools"]["report"]
        self.assertEqual(restricted["status"], "stopped")
        self.assertIn("tools-unsupported", restricted["reasons"])
        self.assertIsNone(restricted["actual"])
        stale = examples["stale-support"]["report"]
        self.assertEqual(stale["status"], "unavailable")
        self.assertTrue(any("harness.date" in error for error in stale["errors"]))
        unknown = examples["unknown-quality"]["report"]
        excluded = next(model for model in unknown["excluded"] if model["id"] == "fixture-middle")
        self.assertIn("quality-unknown", excluded["reasons"])
        self.assertEqual(examples["select"]["report"]["selected"],
                         {"provider": "openai", "id": "fixture-strong"})

    def test_guide_timing_labels_measured_fixture_and_unmeasured_live_target(self) -> None:
        text = self.read(GUIDE)
        self.patterns(text, (r"measured.*(?:fictional|fixture)", r"60.second.*target",
                             r"live.*unmeasured", r"(?:no|not).*savings.*(?:measur|claim)"))
        timing = self.examples()["warm-fixture-latency"]
        self.assertEqual(timing["iterations"], 100)
        self.assertGreaterEqual(timing["elapsed_seconds"], 0)
        self.assertLess(timing["elapsed_seconds"], 1)
        self.assertFalse(timing["live_selection_measured"])

    def test_contract_gate_rejects_broken_helper_canonical_reader_and_guide_links(self) -> None:
        self.assertEqual(reachability_errors(ROOT), [])
        paths = (GUIDE, "rules/workflow-reference.md", *DERIVED,
                 *(f"scripts/{helper}" for helper in HELPERS),
                 *(f"workflows/{reader}.md" for reader in (*EXECUTORS, *PRESERVERS, "pd-select-model")))
        with tempfile.TemporaryDirectory(prefix="workflow-drift-") as temporary:
            directory = Path(temporary)
            for relative in paths:
                target = directory / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            self.assertEqual(reachability_errors(directory), [])
            (directory / "scripts/model_plan.py").unlink()
            canonical = directory / "rules/workflow-reference.md"
            canonical.write_text(canonical.read_text().replace("### Model columns and resolution", "### Removed"))
            reader = directory / "workflows/pe-execute.md"
            reader.write_text(reader.read_text().replace(REFERENCE, "removed reference"))
            guide = directory / "docs/USAGE.md"
            guide.write_text(guide.read_text().replace("MODEL-CATALOG.md", "REMOVED.md"))
            errors = reachability_errors(directory)
        self.assertIn("missing scripts/model_plan.py", errors)
        self.assertIn("missing canonical model resolution section", errors)
        self.assertIn("unreachable resolution contract: pe-execute", errors)
        self.assertIn("unreachable catalog guide: docs/USAGE.md", errors)


if __name__ == "__main__":
    unittest.main()
