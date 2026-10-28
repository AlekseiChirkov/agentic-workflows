"""Exercise the optional catalog using fictional offline fixtures and disposable roots."""
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
import time
from typing import Any
import unittest
from unittest.mock import patch
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/model-catalog.py"
TODAY = date(2032, 6, 15)
TIERS = ("light", "standard", "frontier")


def fixture_payload(age: int = 0) -> dict[str, Any]:
    """Create invented identities and evidence without asserting a real model catalog."""
    refreshed = (TODAY - timedelta(days=age)).isoformat()
    models = []
    for index, tier in enumerate(TIERS):
        for provider in ("anthropic", "openai"):
            models.append({
                "provider": provider,
                "id": f"fixture-{provider}-{tier}-v1",
                "tier": tier,
                "availability": "available",
                "context_window": 32000,
                "tools": ["read", "write", "shell"],
                "traits": ["mechanical", "heavy-reasoning"],
                "capability_evidence": {
                    "reference": f"fixture-evaluation:{provider}-{tier}",
                    "date": refreshed,
                    "quality": index + 2,
                },
                "price_snapshot": None,
            })
    return {"schema_version": 1, "refreshed": refreshed,
            "evidence_date": refreshed, "models": models}


def fixture_markdown(payload: dict[str, Any]) -> str:
    """Render the specified derived table independently of the production helper."""
    lines = ["# Fictional catalog fixture", "", "```json model-catalog",
             json.dumps(payload, indent=2), "```", "",
             "| tier | anthropic model id | openai model id | relative cost |",
             "|---|---|---|---|"]
    for tier in TIERS:
        entries = sorted((model for model in payload.get("models", [])
                          if model.get("tier") == tier), key=lambda model: model["id"])
        cells = []
        for provider in ("anthropic", "openai"):
            cells.append(", ".join(model["id"] for model in entries
                                   if model["provider"] == provider) or "-")
        costs = []
        for model in entries:
            snapshot = model.get("price_snapshot")
            value = snapshot.get("relative_cost") if isinstance(snapshot, dict) else None
            costs.append(f"{model['id']}={format(value, 'g') if isinstance(value, (int, float)) else 'unknown'}")
        lines.append(f"| {tier} | {cells[0]} | {cells[1]} | {'; '.join(costs) or 'unknown'} |")
    return "\n".join(lines) + "\n"


class CatalogContractTests(unittest.TestCase):
    def api(self) -> dict[str, Any]:
        self.assertTrue(HELPER.is_file(),
                        "catalog command contract unavailable: expected scripts/model-catalog.py")
        return runpy.run_path(str(HELPER), run_name="catalog_contract_fixture")

    def invoke(self, *args: str, isolated_root: Path) -> subprocess.CompletedProcess[str]:
        self.assertTrue(HELPER.is_file(),
                        "catalog command contract unavailable: expected scripts/model-catalog.py")
        environment = dict(os.environ, HOME=str(isolated_root / "home"),
                           XDG_CONFIG_HOME=str(isolated_root / "config"),
                           PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run([sys.executable, str(HELPER), *args], text=True,
                              capture_output=True, env=environment, timeout=10)

    def test_catalog_age_boundaries_report_exact_usable_statuses(self) -> None:
        api = self.api()
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "catalog.md"
            for age, status in ((13, "fresh"), (14, "dated"), (30, "dated"), (31, "stale")):
                with self.subTest(age=age):
                    catalog.write_text(fixture_markdown(fixture_payload(age)))
                    report = api["inspect_catalog"](catalog, TODAY)
                    self.assertEqual(report["status"], status)
                    self.assertEqual(report["age_days"], age)
                    self.assertTrue(report["selection_available"])
                    self.assertIn(catalog.read_text().split('"refreshed": "')[1][:10], report["notice"])
                    self.assertEqual(report["session_action"], "preserve")
                    self.assertEqual(report["catalog"]["schema_version"], 1)
                    if age >= 14:
                        self.assertIn("dated" if age <= 30 else "stale", report["notice"].lower())

    def test_missing_malformed_future_dates_report_selection_unavailable(self) -> None:
        api = self.api()
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "catalog.md"
            for field in ("refreshed", "evidence_date"):
                for value in (None, "", "2032-02-30", "20320615", "2032-6-15",
                              (TODAY + timedelta(days=1)).isoformat()):
                    with self.subTest(field=field, value=value):
                        payload = fixture_payload()
                        if value is None:
                            payload.pop(field)
                        else:
                            payload[field] = value
                        catalog.write_text(fixture_markdown(payload))
                        before = catalog.read_bytes()
                        report = api["inspect_catalog"](catalog, TODAY)
                        self.assertEqual(report["status"], "unavailable")
                        self.assertFalse(report["selection_available"])
                        self.assertEqual(report["session_action"], "preserve")
                        self.assertIsNone(report["catalog"])
                        self.assertTrue(report["errors"])
                        self.assertEqual(catalog.read_bytes(), before)

    def test_missing_catalog_default_path_preserves_absent_configuration(self) -> None:
        api = self.api()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            absent = root / "missing" / "catalog.md"
            report = api["inspect_catalog"](absent, TODAY)
            self.assertEqual(report["status"], "unavailable")
            self.assertEqual(report["session_action"], "preserve")
            self.assertFalse(absent.parent.exists())
            result = self.invoke("--today", TODAY.isoformat(), isolated_root=root)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "unavailable")
            self.assertEqual(list(root.iterdir()), [])

    def test_strict_schema_identity_and_vocabulary_reject_invalid_payloads(self) -> None:
        api = self.api()
        cases = []
        for key in ("schema_version", "models"):
            payload = fixture_payload()
            payload.pop(key)
            cases.append((f"missing {key}", payload))
        for version in (True, 0, 2, "1"):
            payload = fixture_payload()
            payload["schema_version"] = version
            cases.append((f"version {version}", payload))
        for key, value in (("provider", "fictional-provider"), ("id", ""),
                           ("id", "alias with spaces"), ("tier", "cheap"),
                           ("availability", True), ("availability", "maybe"),
                           ("traits", ["long-context"]), ("traits", ["creative", "creative"]),
                           ("tools", ["read", "read"]), ("tools", "shell"),
                           ("context_window", True), ("context_window", 0)):
            payload = fixture_payload()
            payload["models"][0][key] = value
            cases.append((f"invalid {key}: {value}", payload))
        for key in ("provider", "id", "tier", "availability", "context_window", "tools",
                    "traits", "capability_evidence", "price_snapshot"):
            payload = fixture_payload()
            payload["models"][0].pop(key)
            cases.append((f"missing model {key}", payload))
        payload = fixture_payload()
        payload["surprise"] = True
        cases.append(("unknown payload field", payload))
        payload = fixture_payload()
        payload["models"][0]["actual_model"] = "fictional-execution"
        cases.append(("unknown execution field", payload))
        payload = fixture_payload()
        payload["models"].append(deepcopy(payload["models"][0]))
        cases.append(("duplicate exact identity", payload))
        for models in ([], [model for model in fixture_payload()["models"] if model["tier"] != "light"]):
            payload = fixture_payload()
            payload["models"] = models
            cases.append(("missing tier", payload))
        for label, payload in cases:
            with self.subTest(case=label):
                with self.assertRaises(api["CatalogError"], msg=label):
                    api["validate_catalog"](fixture_markdown(payload), TODAY)

    def test_markdown_payload_and_derived_tier_table_drift_are_rejected(self) -> None:
        api = self.api()
        valid = fixture_markdown(fixture_payload())
        table_row = next(line for line in valid.splitlines() if line.startswith("| light |"))
        invalid_documents = ("", "# No structured catalog\n", "```json model-catalog\n{}\n```\n",
                             valid.replace('"schema_version": 1,', '"schema_version": 1, "schema_version": 1,'),
                             valid + valid, valid.replace("| tier |", "| quality |", 1),
                             valid.replace(table_row + "\n", ""),
                             valid + table_row + "\n",
                             valid.replace(table_row, table_row.replace("unknown", "0", 1)),
                             valid.replace(table_row, table_row.replace("fixture-anthropic-light-v1", "invented-alias", 1)),
                             valid.replace("```json model-catalog", "```json"))
        for index, document in enumerate(invalid_documents):
            with self.subTest(document=index):
                with self.assertRaises(api["CatalogError"]):
                    api["validate_catalog"](document, TODAY)

    def test_capability_and_price_evidence_validate_dates_types_and_references(self) -> None:
        api = self.api()
        for evidence, field, values in (
                ("capability_evidence", "quality", (True, 0, 6, "5")),
                ("price_snapshot", "relative_cost", (True, 0, -1, "0.5", float("nan"), float("inf"))),
                ("capability_evidence", "reference", ("", None)),
                ("price_snapshot", "reference", ("", None)),
                ("capability_evidence", "date", ("bad-date", "2032-06-16")),
                ("price_snapshot", "date", ("bad-date", "2032-06-16"))):
            for value in values:
                with self.subTest(evidence=evidence, field=field, value=value):
                    payload = fixture_payload()
                    if evidence == "price_snapshot":
                        payload["models"][0][evidence] = {
                            "reference": "fixture-prices:light", "date": TODAY.isoformat(), "relative_cost": 1.0}
                    payload["models"][0][evidence][field] = value
                    with self.assertRaises(api["CatalogError"]):
                        api["validate_catalog"](fixture_markdown(payload), TODAY)
        for evidence in ("capability_evidence", "price_snapshot"):
            payload = fixture_payload()
            payload["models"][0][evidence] = {}
            with self.subTest(incomplete=evidence):
                with self.assertRaises(api["CatalogError"]):
                    api["validate_catalog"](fixture_markdown(payload), TODAY)
        payload = fixture_payload()
        payload["models"][0]["capability_evidence"]["date"] = "2032-06-14"
        payload["evidence_date"] = "2032-06-13"
        with self.assertRaises(api["CatalogError"]):
            api["validate_catalog"](fixture_markdown(payload), TODAY)

    def test_unknown_price_availability_and_capability_remain_unknown(self) -> None:
        api = self.api()
        payload = fixture_payload()
        model = payload["models"][0]
        model.update(availability="unknown", context_window=None, tools=None, capability_evidence=None)
        validated = api["validate_catalog"](fixture_markdown(payload), TODAY)
        self.assertEqual(validated, payload)
        self.assertIsNone(validated["models"][0]["price_snapshot"])
        self.assertIsNone(validated["models"][0]["capability_evidence"])
        self.assertEqual(validated["models"][0]["availability"], "unknown")

    def test_equal_relative_cost_preserves_independently_evidenced_quality(self) -> None:
        api = self.api()
        payload = fixture_payload()
        for model in payload["models"]:
            model["price_snapshot"] = {"reference": "fixture-prices:shared-cost",
                                       "date": TODAY.isoformat(), "relative_cost": 1.0}
        validated = api["validate_catalog"](fixture_markdown(payload), TODAY)
        self.assertEqual([model["capability_evidence"]["quality"] for model in validated["models"]],
                         [2, 2, 3, 3, 4, 4])
        self.assertEqual([model["price_snapshot"]["relative_cost"] for model in validated["models"]],
                         [1.0] * 6)

    def test_inspection_is_offline_readonly_and_repeatable(self) -> None:
        api = self.api()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = root / "catalog.md"
            catalog.write_text(fixture_markdown(fixture_payload(31)))
            before = catalog.read_bytes()
            metadata = catalog.stat()
            with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")), \
                    patch.object(socket, "create_connection", side_effect=AssertionError("network forbidden")), \
                    patch.object(urllib.request, "urlopen", side_effect=AssertionError("network forbidden")), \
                    patch.object(subprocess, "Popen", side_effect=AssertionError("model spawning forbidden")), \
                    patch.object(Path, "write_text", side_effect=AssertionError("inspection write forbidden")), \
                    patch.object(Path, "write_bytes", side_effect=AssertionError("inspection write forbidden")), \
                    patch.object(os, "replace", side_effect=AssertionError("inspection replacement forbidden")):
                first = api["inspect_catalog"](catalog, TODAY)
                second = api["inspect_catalog"](catalog, TODAY)
            self.assertEqual(first, second)
            self.assertEqual(first["status"], "stale")
            self.assertEqual(catalog.read_bytes(), before)
            self.assertEqual(catalog.stat().st_mtime_ns, metadata.st_mtime_ns)
            self.assertEqual(list(root.iterdir()), [catalog])

    def test_valid_refresh_installs_validated_candidate_with_same_directory_replacement(self) -> None:
        api = self.api()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, candidate = root / "catalog.md", root / "candidate.md"
            catalog.write_text(fixture_markdown(fixture_payload(31)))
            candidate.write_text(fixture_markdown(fixture_payload()))
            before = catalog.read_bytes()
            replacement = os.replace
            observed = []

            def observe_replace(source: str | Path, destination: str | Path) -> None:
                source_path, destination_path = Path(source), Path(destination)
                self.assertEqual(source_path.parent, catalog.parent)
                self.assertEqual(destination_path, catalog)
                self.assertEqual(catalog.read_bytes(), before)
                self.assertEqual(source_path.read_bytes(), candidate.read_bytes())
                api["validate_catalog"](source_path.read_text(), TODAY)
                observed.append((source_path, destination_path))
                replacement(source, destination)

            with patch.object(os, "replace", side_effect=observe_replace):
                report = api["refresh_catalog"](catalog, candidate, TODAY)
            self.assertEqual(report["status"], "fresh")
            self.assertTrue(report["refreshed"])
            self.assertEqual(len(observed), 1)
            self.assertEqual(catalog.read_bytes(), candidate.read_bytes())
            self.assertEqual(set(root.iterdir()), {catalog, candidate})

    def test_invalid_or_missing_refresh_candidate_preserves_previous_bytes(self) -> None:
        api = self.api()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, candidate = root / "catalog.md", root / "candidate.md"
            catalog.write_text(fixture_markdown(fixture_payload(14)))
            before = catalog.read_bytes()
            for document in (None, "", "invalid", fixture_markdown(fixture_payload(-1))):
                with self.subTest(document=document):
                    if document is not None:
                        candidate.write_text(document)
                    report = api["refresh_catalog"](catalog, candidate, TODAY)
                    self.assertFalse(report["refreshed"])
                    self.assertEqual(report["status"], "dated")
                    self.assertTrue(report["errors"])
                    self.assertEqual(catalog.read_bytes(), before)
                    self.assertEqual(set(root.iterdir()), {catalog} if document is None else {catalog, candidate})

    def test_failed_replacement_preserves_catalog_and_cleans_temporary_file(self) -> None:
        api = self.api()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, candidate = root / "catalog.md", root / "candidate.md"
            catalog.write_text(fixture_markdown(fixture_payload(30)))
            candidate.write_text(fixture_markdown(fixture_payload()))
            before = catalog.read_bytes()
            with patch.object(os, "replace", side_effect=OSError("fixture replacement denied")):
                report = api["refresh_catalog"](catalog, candidate, TODAY)
            self.assertFalse(report["refreshed"])
            self.assertEqual(report["status"], "dated")
            self.assertTrue(report["errors"])
            self.assertEqual(catalog.read_bytes(), before)
            self.assertEqual(set(root.iterdir()), {catalog, candidate})

    def test_refresh_creates_missing_directory_only_after_candidate_validation(self) -> None:
        api = self.api()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, candidate = root / "configuration" / "catalog.md", root / "candidate.md"
            candidate.write_text("invalid")
            report = api["refresh_catalog"](catalog, candidate, TODAY)
            self.assertFalse(report["refreshed"])
            self.assertFalse(catalog.parent.exists())
            candidate.write_text(fixture_markdown(fixture_payload()))
            report = api["refresh_catalog"](catalog, candidate, TODAY)
            self.assertTrue(report["refreshed"])
            self.assertEqual(catalog.read_bytes(), candidate.read_bytes())

    def test_cli_inspection_and_explicit_refresh_report_json_and_exit_status(self) -> None:
        self.api()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, candidate = root / "catalog.md", root / "candidate.md"
            catalog.write_text(fixture_markdown(fixture_payload(31)))
            candidate.write_text(fixture_markdown(fixture_payload()))
            before = catalog.read_bytes()
            result = self.invoke("--catalog", str(catalog), "--today", TODAY.isoformat(), isolated_root=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "stale")
            self.assertEqual(catalog.read_bytes(), before)
            result = self.invoke("--catalog", str(catalog), "--today", TODAY.isoformat(),
                                 "--refresh", str(candidate), isolated_root=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["refreshed"])
            self.assertEqual(catalog.read_bytes(), candidate.read_bytes())
            candidate.write_text("invalid")
            before = catalog.read_bytes()
            result = self.invoke("--catalog", str(catalog), "--today", TODAY.isoformat(),
                                 "--refresh", str(candidate), isolated_root=root)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(json.loads(result.stdout)["refreshed"])
            self.assertEqual(catalog.read_bytes(), before)
            result = self.invoke("--catalog", str(catalog), "--refresh", isolated_root=root)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(catalog.read_bytes(), before)

    def test_repeated_warm_isolated_lookup_measures_less_than_one_second(self) -> None:
        api = self.api()
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "catalog.md"
            catalog.write_text(fixture_markdown(fixture_payload()))
            expected = api["inspect_catalog"](catalog, TODAY)
            started = time.perf_counter()
            for _ in range(100):
                self.assertEqual(api["inspect_catalog"](catalog, TODAY), expected)
            elapsed = time.perf_counter() - started
            self.assertLess(elapsed, 1.0, "100 warm isolated lookups must complete below one second")
            print(f"warm isolated catalog fixture: 100 lookups in {elapsed:.6f}s; no live selection timing measured")


if __name__ == "__main__":
    unittest.main()
