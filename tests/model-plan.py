"""Check compatible plan reading and visible offline resolution with invented evidence."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
import json
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

# Any represents heterogeneous JSON fixtures and runpy namespaces. Deliberately invalid
# inputs remain representable so the public boundaries can prove strict rejection.
ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts/model_plan.py"
COMMAND = ROOT / "scripts/model-catalog.py"
TODAY = date(2032, 6, 15)


def identity(name: str, provider: str = "openai") -> dict[str, str]:
    return {"provider": provider, "id": name}


def catalog() -> dict[str, Any]:
    models = [{**identity(name), "tier": tier, "availability": "available",
               "context_window": 64000, "tools": ["read", "shell"], "traits": [],
               "capability_evidence": {"reference": f"fixture-quality:{name}",
                                       "date": TODAY.isoformat(), "quality": quality},
               "price_snapshot": {"reference": f"fixture-price:{name}",
                                  "date": TODAY.isoformat(), "relative_cost": quality}}
              for name, tier, quality in (("small", "light", 2), ("middle", "standard", 3),
                                          ("strong", "frontier", 5))]
    return {"schema_version": 1, "refreshed": TODAY.isoformat(),
            "evidence_date": TODAY.isoformat(), "models": models}


def resolution() -> dict[str, Any]:
    selection = {"scores": {factor: 2 for factor in ("C", "A", "V", "R", "Ver", "Crit", "RW")},
                 "hard_constraints": [], "traits": [], "task_class": "fixture-work",
                 "requirements": {"context_tokens": 8000, "tools": ["read", "shell"]},
                 "harness": {"reference": "fixture-current-support", "date": TODAY.isoformat(),
                             "models": [{**identity(model["id"]), "availability": "available",
                                         "context_window": 64000, "tools": ["read", "shell"]}
                                        for model in catalog()["models"]]},
                 "owner": {"allowed_models": None, "excluded_models": []},
                 "default_model": identity("strong"), "cost_comparisons": []}
    return {"provider": "openai", "requested": identity("middle"), "selection": selection,
            "fallback": {"authorized": False, "model": None}, "execution": None}


def plan(headers: list[str], rows: list[list[str]]) -> str:
    return "# Fixture\n\n## Subtasks\n\n" + "\n".join(
        "| " + " | ".join(cells) + " |" for cells in [headers, ["---"] * len(headers), *rows]
    ) + "\n\n## Notes\n\nPreserve this text and its trailing spaces.  \n"


def catalog_markdown() -> str:
    lines = ["# Fixture", "", "```json model-catalog", json.dumps(catalog()), "```", "",
             "| tier | anthropic model id | openai model id | relative cost |", "|---|---|---|---|"]
    lines.extend(f"| {model['tier']} | - | {model['id']} | {model['id']}="
                 f"{model['price_snapshot']['relative_cost']} |" for model in catalog()["models"])
    return "\n".join(lines) + "\n"


class PlanContractTests(unittest.TestCase):
    def api(self) -> dict[str, Any]:
        self.assertTrue(ENGINE.is_file(), "plan behavior unavailable: expected scripts/model_plan.py")
        return runpy.run_path(str(ENGINE), run_name="plan_contract_fixture")

    def run_cli(self, arguments: list[str], directory: Path) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ, HOME=str(directory), XDG_CONFIG_HOME=str(directory / "config"),
                           XDG_STATE_HOME=str(directory / "state"))
        return subprocess.run([sys.executable, str(COMMAND), *arguments], capture_output=True,
                              text=True, env=environment, check=False)

    def test_legacy_reordered_columns_read_exact_active_provider_requests(self) -> None:
        api = self.api()
        document = plan(["Status", "Extra", "Model", "ID"], [["done", "keep", "middle", "build"]])
        for provider in ("anthropic", "openai"):
            self.assertEqual(api["read_plan"](document, provider), [
                {"id": "build", "status": "done", "source": "Model",
                 "requested": identity("middle", provider)}])

    def test_dual_columns_override_conflicting_legacy_by_active_provider(self) -> None:
        api = self.api()
        document = plan(["Model (Codex)", "ID", "Model", "Status", "Model (Claude)"],
                        [["middle", "build", "old", "reviewed", "claude-exact"]])
        for provider, expected, source in (("openai", "middle", "Model (Codex)"),
                                            ("anthropic", "claude-exact", "Model (Claude)")):
            self.assertEqual(api["read_plan"](document, provider)[0], {
                "id": "build", "status": "reviewed", "source": source,
                "requested": identity(expected, provider)})

    def test_absent_empty_and_placeholder_models_mean_explicit_session_default(self) -> None:
        api = self.api()
        variants = [plan(["ID", "Status"], [["build", "done"]]),
                    plan(["ID", "Status", "Model (Claude)"], [["build", "done", "foreign"]])]
        variants.extend(plan(["ID", "Status", "Model", "Model (Codex)"],
                             [["build", "done", "old", value]]) for value in ("", "-", "—"))
        for document in variants:
            row = api["read_plan"](document, "openai")[0]
            self.assertIsNone(row["requested"])
            self.assertIn(row["source"], ("session-default", "Model (Codex)"))

    def test_escaped_pipes_fenced_examples_and_composite_blanks_preserve_rows(self) -> None:
        api = self.api()
        document = "```markdown\n" + plan(["ID", "Status"], [["example", "done"]]) + "```\n"
        document += plan(["ID", "Type", "Name", "Model", "Status"],
                         [["bundle", "composite", "Parent", "", "in-progress"],
                          ["build", "leaf", r"Read \| write", "middle", "done"]])
        rows = api["read_plan"](document, "openai")
        self.assertEqual([row["id"] for row in rows], ["bundle", "build"])
        self.assertIsNone(rows[0]["requested"])
        self.assertEqual(rows[1]["requested"], identity("middle"))
        self.assertEqual(api["update_plan"](document, {}), document)

    def test_malformed_and_ambiguous_tables_are_rejected_before_reading(self) -> None:
        api = self.api()
        valid = plan(["ID", "Status", "Model"], [["build", "done", "middle"]])
        variants = [valid.replace("| ID |", "| ID | ID |"), valid.replace("| --- |", "| --bad |", 1),
                    valid.replace("| build | done | middle |", "| build | done |"),
                    valid.replace("\n\n## Notes", "\n| build | done | middle |\n\n## Notes"),
                    valid + valid, valid.replace("| ID |", "| Name |"),
                    valid.replace("| Status |", "| State |"), valid.replace("middle", "bad id")]
        for document in variants:
            with self.subTest(document=document):
                with self.assertRaises(ValueError):
                    api["read_plan"](document, "openai")
        with self.assertRaises(ValueError):
            api["read_plan"](valid, "unsupported")

    def test_bulk_additions_preserve_unknown_columns_statuses_and_composite_blanks(self) -> None:
        api = self.api()
        document = plan(["ID", "Name", "Model", "Custom", "Status"],
                        [["bundle", "Parent", "", r"A \| B", "in-progress"],
                         ["build", "Child", "", "keep", "done"]]).replace("\n", "\r\n")
        updated = api["update_plan"](document, {"build": {"anthropic": "claude-exact", "openai": "middle"}})
        self.assertTrue(updated.startswith("# Fixture\r\n\r\n## Subtasks\r\n\r\n"))
        self.assertEqual(updated.split("## Notes", 1)[1], document.split("## Notes", 1)[1])
        self.assertIn(r"A \| B", updated)
        for provider in ("anthropic", "openai"):
            rows = api["read_plan"](updated, provider)
            self.assertEqual([(row["id"], row["status"]) for row in rows],
                             [("bundle", "in-progress"), ("build", "done")])
            self.assertIsNone(rows[0]["requested"])
        self.assertEqual(api["read_plan"](updated, "openai")[1]["requested"], identity("middle"))
        self.assertEqual(api["update_plan"](updated, {"build": {"openai": "middle"}}), updated)

    def test_existing_provider_updates_preserve_every_untouched_byte_and_allow_clear(self) -> None:
        api = self.api()
        document = plan(["ID", "Model (Codex)", "Model (Claude)", "Status"],
                        [["build", "middle", "claude-exact", "done"], ["review", "strong", "", "reviewed"]])
        document = document.rstrip("\n")
        updated = api["update_plan"](document, {"build": {"openai": None}})
        self.assertEqual(updated, document.replace("| build | middle |", "| build |  |"))
        self.assertIsNone(api["read_plan"](updated, "openai")[0]["requested"])
        self.assertEqual(api["update_plan"](updated, {}), updated)

    def test_legacy_migration_requires_explicit_values_for_each_added_provider(self) -> None:
        api = self.api()
        document = plan(["ID", "Model", "Status"], [["build", "old", "done"]])
        for updates in ({"build": {"openai": "middle"}}, {"build": {"anthropic": None}}):
            with self.assertRaisesRegex(ValueError, "legacy"):
                api["update_plan"](document, updates)
        updated = api["update_plan"](document, {"build": {"openai": "middle", "anthropic": None}})
        self.assertEqual(api["read_plan"](updated, "openai")[0]["requested"], identity("middle"))
        self.assertIsNone(api["read_plan"](updated, "anthropic")[0]["requested"])

    def test_invalid_bulk_updates_leave_original_plan_bytes_unchanged(self) -> None:
        api = self.api()
        document = plan(["ID", "Status"], [["build", "done"]])
        invalid = [{"missing": {"openai": "middle"}}, {"build": {"other": "middle"}},
                   {"build": {"openai": "bad | value"}}, {"build": {"openai": True}},
                   {"build": []}, [], {"build": {"openai": "bad\nvalue"}}]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plan.md"
            path.write_bytes(document.encode())
            for updates in invalid:
                with self.assertRaises(ValueError):
                    api["write_plan"](path, updates)
                self.assertEqual(path.read_bytes(), document.encode())
            path.write_text(document.replace("| --- |", "| broken |", 1))
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                api["write_plan"](path, {"build": {"openai": "middle"}})
            self.assertEqual(path.read_bytes(), before)

    def test_atomic_replace_failure_preserves_plan_and_cleans_staging_file(self) -> None:
        api = self.api()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plan.md"
            path.write_text(plan(["ID", "Status"], [["build", "done"]]))
            before = path.read_bytes()
            with patch("os.replace", side_effect=OSError("fixture replace refusal")):
                with self.assertRaises(OSError):
                    api["write_plan"](path, {"build": {"openai": "middle"}})
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(path.parent.iterdir()), [path])
            self.assertTrue(api["write_plan"](path, {"build": {"openai": "middle"}}))
            with patch("os.replace", side_effect=AssertionError("no-op must not replace")):
                self.assertFalse(api["write_plan"](path, {"build": {"openai": "middle"}}))

    def test_exact_requested_identity_resolves_without_economic_substitution(self) -> None:
        api = self.api()
        request = resolution()
        request["selection"]["cost_comparisons"] = [{"invalid": "ignored for request routing"}]
        report = api["resolve_model"](catalog(), request, TODAY)
        self.assertEqual(report["status"], "resolved")
        self.assertEqual(report["requested"], identity("middle"))
        self.assertEqual(report["resolved"], identity("middle"))
        self.assertIsNone(report["actual"])
        self.assertTrue(report["reasons"])

    def test_identity_uses_provider_and_exact_id_without_provider_switching(self) -> None:
        api = self.api()
        request = resolution()
        request["requested"] = identity("middle", "anthropic")
        with self.assertRaises(ValueError):
            api["resolve_model"](catalog(), request, TODAY)
        models = catalog()
        models["models"][1]["provider"] = "anthropic"
        report = api["resolve_model"](models, resolution(), TODAY)
        self.assertEqual(report["status"], "stopped")
        self.assertIsNone(report["resolved"])
        self.assertIn("catalog-unlisted", report["reasons"])

    def test_unsupported_request_stops_visibly_without_undeclared_or_unauthorized_fallback(self) -> None:
        api = self.api()
        for fallback in ({"authorized": False, "model": None},
                         {"authorized": False, "model": identity("strong")},
                         {"authorized": True, "model": None}):
            request = resolution()
            request.update(requested=identity("missing"), fallback=fallback)
            report = api["resolve_model"](catalog(), request, TODAY)
            self.assertEqual(report["status"], "stopped")
            self.assertEqual(report["requested"], identity("missing"))
            self.assertIsNone(report["resolved"])
            self.assertIsNone(report["actual"])
            self.assertIn("catalog-unlisted", report["reasons"])

    def test_authorized_declared_suitable_fallback_is_visible_and_never_actual(self) -> None:
        api = self.api()
        request = resolution()
        request.update(requested=identity("missing"),
                       fallback={"authorized": True, "model": identity("strong")})
        report = api["resolve_model"](catalog(), request, TODAY)
        self.assertEqual(report["status"], "fallback")
        self.assertEqual(report["requested"], identity("missing"))
        self.assertEqual(report["resolved"], identity("strong"))
        self.assertIsNone(report["actual"])
        self.assertIn("catalog-unlisted", report["reasons"])

    def test_fallback_independently_obeys_support_quality_context_tools_owner_and_traits(self) -> None:
        api = self.api()
        changes = [("hard_constraints", ["security"]), ("requirements", {"context_tokens": 64001, "tools": []}),
                   ("requirements", {"context_tokens": 8000, "tools": ["browser"]}),
                   ("owner", {"allowed_models": [], "excluded_models": []}), ("traits", ["creative"])]
        for key, value in changes:
            request = resolution()
            request.update(requested=identity("missing"),
                           fallback={"authorized": True, "model": identity("middle")})
            request["selection"][key] = value
            report = api["resolve_model"](catalog(), request, TODAY)
            self.assertEqual(report["status"], "stopped", key)
            self.assertIsNone(report["resolved"])
        request = resolution()
        request.update(requested=identity("missing"), fallback={"authorized": True, "model": identity("strong")})
        request["selection"]["harness"]["models"][-1]["availability"] = "unavailable"
        self.assertEqual(api["resolve_model"](catalog(), request, TODAY)["status"], "stopped")
        request["fallback"]["model"] = identity("strong", "anthropic")
        with self.assertRaises(ValueError):
            api["resolve_model"](catalog(), request, TODAY)

    def test_session_default_resolves_only_its_own_suitable_identity_or_stops(self) -> None:
        api = self.api()
        request = resolution()
        request["requested"] = None
        report = api["resolve_model"](catalog(), request, TODAY)
        self.assertEqual(report["status"], "session-default")
        self.assertIsNone(report["requested"])
        self.assertEqual(report["resolved"], identity("strong"))
        for default in (None, identity("missing")):
            request["selection"]["default_model"] = default
            report = api["resolve_model"](catalog(), request, TODAY)
            self.assertEqual(report["status"], "stopped")
            self.assertIsNone(report["resolved"])
            self.assertIsNone(report["actual"])

    def test_stale_support_and_malformed_resolution_inputs_fail_explicitly(self) -> None:
        api = self.api()
        stale = resolution()
        stale["selection"]["harness"]["date"] = (TODAY - timedelta(days=1)).isoformat()
        cases = [stale, dict(resolution(), provider="other"), dict(resolution(), requested={"id": "middle"}),
                 dict(resolution(), fallback={"authorized": "yes", "model": identity("strong")}),
                 dict(resolution(), execution={"model": identity("middle")}),
                 dict(resolution(), extra=True)]
        for request in cases:
            with self.assertRaises(ValueError):
                api["resolve_model"](catalog(), request, TODAY)

    def test_actual_requires_fresh_separate_evidence_of_the_authorized_resolved_identity(self) -> None:
        api = self.api()
        request = resolution()
        request.update(requested=identity("missing"),
                       fallback={"authorized": True, "model": identity("strong")})
        request["execution"] = {"model": identity("strong"),
                                "reference": "fixture-execution-receipt", "date": TODAY.isoformat()}
        report = api["resolve_model"](catalog(), request, TODAY)
        self.assertEqual(report["requested"], identity("missing"))
        self.assertEqual(report["resolved"], identity("strong"))
        self.assertEqual(report["actual"], identity("strong"))
        for evidence in (dict(request["execution"], reference=""),
                         dict(request["execution"], model=identity("missing")),
                         dict(request["execution"], date=(TODAY - timedelta(days=1)).isoformat()),
                         dict(request["execution"], date=(TODAY + timedelta(days=1)).isoformat())):
            with self.assertRaises(ValueError):
                api["resolve_model"](catalog(), dict(request, execution=evidence), TODAY)

    def test_resolution_is_pure_without_network_files_processes_or_input_mutation(self) -> None:
        api = self.api()
        models, request = catalog(), resolution()
        before = deepcopy((models, request))
        with patch("builtins.open", side_effect=AssertionError("no file reads")), \
                patch.object(Path, "read_text", side_effect=AssertionError("no file reads")), \
                patch.object(socket, "socket", side_effect=AssertionError("no provider calls")), \
                patch.object(subprocess, "run", side_effect=AssertionError("no execution")):
            report = api["resolve_model"](models, request, TODAY)
        self.assertEqual(report["resolved"], identity("middle"))
        self.assertEqual((models, request), before)

    def test_cli_read_update_and_resolve_are_explicit_json_operations(self) -> None:
        self.api()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            paths = {name: directory / name for name in ("plan.md", "updates.json", "request.json", "catalog.md")}
            paths["plan.md"].write_text(plan(["ID", "Status"], [["build", "done"]]))
            paths["updates.json"].write_text(json.dumps({"build": {"openai": "middle"}}))
            request = resolution()
            paths["request.json"].write_text(json.dumps({key: request[key] for key in ("selection", "fallback", "execution")}))
            paths["catalog.md"].write_text(catalog_markdown())
            read = self.run_cli(["--read-plan", str(paths["plan.md"]), "--provider", "openai"], directory)
            self.assertEqual(read.returncode, 0, read.stderr)
            self.assertIsNone(json.loads(read.stdout)["rows"][0]["requested"])
            update = self.run_cli(["--update-plan", str(paths["plan.md"]), "--updates", str(paths["updates.json"])], directory)
            self.assertEqual(update.returncode, 0, update.stderr)
            self.assertEqual(json.loads(update.stdout)["status"], "updated")
            resolved = self.run_cli(["--resolve-plan", str(paths["plan.md"]), "--provider", "openai", "--row", "build",
                                     "--resolution", str(paths["request.json"]), "--catalog", str(paths["catalog.md"]),
                                     "--today", TODAY.isoformat()], directory)
            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            self.assertEqual(json.loads(resolved.stdout)["resolved"], identity("middle"))
            self.assertIsNone(json.loads(resolved.stdout)["actual"])
            self.assertFalse((directory / "config").exists())

    def test_cli_rejects_invalid_updates_and_reports_unavailable_support_without_writes(self) -> None:
        self.api()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            path, updates, request_path, catalog_path = [directory / name for name in
                                                        ("plan.md", "updates.json", "request.json", "catalog.md")]
            path.write_text(plan(["ID", "Status", "Model"], [["build", "done", "missing"]]))
            updates.write_text('{"build":{"openai":"middle","openai":"strong"}}')
            before = path.read_bytes()
            rejected = self.run_cli(["--update-plan", str(path), "--updates", str(updates)], directory)
            self.assertEqual(rejected.returncode, 2)
            self.assertTrue(json.loads(rejected.stdout)["errors"])
            self.assertEqual(path.read_bytes(), before)
            request = resolution()
            request["selection"]["harness"]["date"] = (TODAY - timedelta(days=1)).isoformat()
            request_path.write_text(json.dumps({key: request[key] for key in ("selection", "fallback", "execution")}))
            catalog_path.write_text(catalog_markdown())
            report = self.run_cli(["--resolve-plan", str(path), "--provider", "openai", "--row", "build",
                                   "--resolution", str(request_path), "--catalog", str(catalog_path),
                                   "--today", TODAY.isoformat()], directory)
            self.assertEqual(report.returncode, 2, report.stderr)
            self.assertEqual(json.loads(report.stdout)["status"], "unavailable")
            self.assertIsNone(json.loads(report.stdout)["resolved"])
            self.assertIsNone(json.loads(report.stdout)["actual"])
            self.assertEqual(path.read_bytes(), before)

    def test_cli_auxiliary_flags_are_validated_before_any_mutation(self) -> None:
        self.api()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            path, updates = directory / "plan.md", directory / "updates.json"
            path.write_text(plan(["ID", "Status"], [["build", "done"]]))
            updates.write_text(json.dumps({"build": {"openai": "middle"}}))
            before = path.read_bytes()
            variants = [["--update-plan", str(path), "--updates", str(updates), "--row", "build"],
                        ["--read-plan", str(path), "--provider", "openai", "--updates", str(updates)],
                        ["--resolve-plan", str(path), "--provider", "openai", "--row", "build"],
                        ["--updates", str(updates)], ["--read-plan", str(path)]]
            for arguments in variants:
                result = self.run_cli(arguments, directory)
                self.assertEqual(result.returncode, 2, arguments)
                self.assertEqual(path.read_bytes(), before)


    def test_cli_stale_support_preserves_requested_identity_and_error_reason(self) -> None:
        self.api()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            paths = {name: directory / name for name in ("plan.md", "request.json", "catalog.md")}
            paths["plan.md"].write_text(plan(["ID", "Status", "Model"], [["build", "done", "missing"]]))
            request = resolution()
            request["selection"]["harness"]["date"] = (TODAY - timedelta(days=1)).isoformat()
            paths["request.json"].write_text(json.dumps({key: request[key] for key in ("selection", "fallback", "execution")}))
            paths["catalog.md"].write_text(catalog_markdown())
            result = self.run_cli(["--resolve-plan", str(paths["plan.md"]), "--provider", "openai", "--row", "build",
                                   "--resolution", str(paths["request.json"]), "--catalog", str(paths["catalog.md"]),
                                   "--today", TODAY.isoformat()], directory)
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["requested"], identity("missing"))
            self.assertIsNone(report["resolved"])
            self.assertIsNone(report["actual"])
            self.assertTrue(report["errors"])


    def test_unbounded_last_row_is_rejected_before_atomic_updates(self) -> None:
        api = self.api()
        document = plan(["ID", "Status", "Model (Codex)", "Model (Claude)"],
                        [["build", "done", "middle", ""]])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plan.md"
            for row in ("review | done | middle |  |", "review | done | middle | "):
                malformed = document.replace("\n\n## Notes", "\n" + row + "\n\n## Notes")
                path.write_text(malformed)
                before = path.read_bytes()
                with self.assertRaisesRegex(ValueError, "table"):
                    api["write_plan"](path, {"build": {"openai": "strong"}})
                self.assertEqual(path.read_bytes(), before)


    def test_indented_code_table_is_preserved_and_never_read_as_a_plan(self) -> None:
        api = self.api()
        document = plan(["ID", "Status", "Model (Codex)", "Model (Claude)"],
                        [["build", "done", "middle", ""]])
        example = "    | ID | Status | Model |\n    | --- | --- | --- |\n    | example | done | wrong |\n\n"
        document = document.replace("| ID |", example + "| ID |", 1)
        self.assertEqual([row["id"] for row in api["read_plan"](document, "openai")], ["build"])
        updated = api["update_plan"](document, {"build": {"openai": "strong"}})
        self.assertEqual(updated, document.replace("| build | done | middle |", "| build | done | strong |"))
        example_only = "## Subtasks\n\n" + example
        with self.assertRaises(ValueError):
            api["read_plan"](example_only, "openai")



if __name__ == "__main__":
    unittest.main()
