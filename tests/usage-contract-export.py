#!/usr/bin/env python3
"""Integration coverage for the additive producer contract export."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "log-step.sh"
MODULE = ROOT / "scripts" / "usage_telemetry_contract.py"

LEGACY = {
    "hook.required": "session_id agent_id checkpoint_id span_start_ms span_end_ms timing_source boundary",
    "hook.identity_pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
    "hook.timing_source": "hook", "hook.boundary": "session|subagent",
    "hook.span_kind": "work|waiting", "step.outcome": "ok|blocked|failed|skipped|deferred",
    "step.gate": "pass|fail|n-a|needs-work|ready",
    "step.tests": "red|green|n-a|failed|not-run|pinned", "step.promoted": "yes|no",
    "run-end.outcome": "completed|stopped|failed|abandoned",
    "count.fields": "stops escalations decisions questions fix_tasks amendments files",
    "count.maximum": "9007199254740991", "alias.outcome.completed": "ok",
    "alias.outcome.implemented": "ok", "alias.outcome.restarted": "failed",
    "alias.outcome.needs-work": "failed", "alias.gate.PASS": "pass",
    "alias.gate.NEEDS_WORK_EXACT": "needs-work",
    "alias.gate.NEEDS_WORK_PREFIX": "^NEEDS WORK([[:space:]:-].*)$",
    "alias.gate.escalated": "fail", "step.synthetic": "batch-gate|subtask|dry-run",
}


def invoke(script=SCRIPT, args=("contract",), env=None):
    return subprocess.run(["/bin/bash", str(script), *args], env=env, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def entries(result):
    rows = result.stdout.splitlines()
    assert all("=" in row for row in rows), rows
    pairs = [row.split("=", 1) for row in rows]
    assert len({key for key, _ in pairs}) == len(pairs), pairs
    return dict(pairs)


def isolated_path(directory, *, python):
    for name in ("dirname", "sort", "mkdir", "date", "tr", "od", "sed", "cat", "rm",
                 "mktemp", "sleep", "flock", "basename", "wc", "chmod", "head",
                 "touch", "mv", "grep"):
        source = shutil.which(name)
        if source:
            (directory / name).symlink_to(source)
    if python:
        (directory / "python3").symlink_to(shutil.which("python3"))
    return str(directory)


class ProducerContractExport(unittest.TestCase):
    def test_legacy_vocabulary_is_preserved(self):
        result = invoke()
        self.assertEqual(result.returncode, 0)
        actual = entries(result)
        self.assertEqual({k: actual.get(k) for k in LEGACY}, LEGACY)

    def test_export_matches_shared_registry_and_validator_vocabulary(self):
        spec = importlib.util.spec_from_file_location("telemetry_contract", MODULE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        registry = module.schema_registry()
        result = invoke()
        self.assertEqual(result.returncode, 0)
        actual = entries(result)
        self.assertEqual(actual["usage.availability"], "available")
        exported = json.loads(actual["usage.registry"])
        self.assertEqual(exported, registry)
        self.assertEqual(exported["schema_version"], 1)
        self.assertEqual(set(exported["measurement_states"]), module.MEASUREMENT_STATES)
        self.assertEqual(set(exported["measurement_reasons"]), module.MEASUREMENT_REASONS)
        self.assertTrue({"source_profile", "source_selection", "observation", "usage_bundle",
                         "inventory", "collection_segment", "diagnostic_measurement",
                         "price_snapshot", "pricing_scenario", "warning_policy",
                         "analysis_corpus", "usage_accepted", "lifecycle_projection",
                         "current_run_snapshot"}.issubset(exported["kinds"]))

    def test_no_jq_preserves_contract_and_existing_logging(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "bin"
            path.mkdir()
            env = {**os.environ, "PATH": isolated_path(path, python=True),
                   "ORCHESTRAIL_LOG_ROOT": str(root / "logs")}
            result = invoke(env=env)
            self.assertEqual(result.returncode, 0)
            actual = entries(result)
            self.assertEqual({k: actual.get(k) for k in LEGACY}, LEGACY)
            self.assertEqual(json.loads(actual["usage.registry"])["schema_version"], 1)
            start = invoke(args=("run-start", "--pipeline", "spec-run", "--project", str(root)), env=env)
            self.assertEqual(start.returncode, 0)
            self.assertRegex(start.stdout.strip(), r"^[0-9a-f]{8}$")
            self.assertTrue(list((root / "logs" / "runs").glob("*.jsonl")))

    def test_missing_python_does_not_claim_usage_is_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "bin"
            path.mkdir()
            env = {**os.environ, "PATH": isolated_path(path, python=False),
                   "ORCHESTRAIL_LOG_ROOT": str(root / "logs")}
            result = invoke(env=env)
            self.assertEqual(result.returncode, 0)
            actual = entries(result)
            self.assertEqual({k: actual.get(k) for k in LEGACY}, LEGACY)
            self.assertEqual(actual["usage.availability"], "unavailable")
            self.assertNotIn("usage.registry", actual)
            self.assertNotIn("usage_accepted", result.stdout)
            start = invoke(args=("run-start", "--pipeline", "spec-run", "--project", str(root)), env=env)
            self.assertEqual(start.returncode, 0)
            self.assertRegex(start.stdout.strip(), r"^[0-9a-f]{8}$")

    def test_broken_registry_cannot_assert_availability(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "scripts"
            scripts.mkdir()
            shutil.copyfile(SCRIPT, scripts / SCRIPT.name)
            (scripts / MODULE.name).write_text("this is not valid python syntax !!!\n", encoding="utf-8")
            result = invoke(script=scripts / SCRIPT.name)
            self.assertEqual(result.returncode, 0)
            actual = entries(result)
            self.assertEqual({k: actual.get(k) for k in LEGACY}, LEGACY)
            self.assertEqual(actual["usage.availability"], "unavailable")
            self.assertNotIn("usage.registry", actual)
            self.assertNotIn("usage_accepted", result.stdout)


if __name__ == "__main__":
    unittest.main()
