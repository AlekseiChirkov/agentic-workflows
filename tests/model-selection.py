"""Check conservative selection with invented evidence and no provider access."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from itertools import product
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
import urllib.request

# Any permits deliberately malformed JSON fixtures and the heterogeneous runpy namespace.
# Production validation must reject those invalid values at the public boundary.

ROOT = Path(__file__).resolve().parents[1]
SELECTOR = ROOT / "scripts/model_selection.py"
COMMAND = ROOT / "scripts/model-catalog.py"
TODAY = date(2032, 6, 15)
FACTORS = ("C", "A", "V", "R", "Ver", "Crit", "RW")


def identity(name: str, provider: str = "openai") -> dict[str, str]:
    return {"provider": provider, "id": name}


def fixture_catalog() -> dict[str, Any]:
    models = []
    for name, tier, quality in (("fixture-small", "light", 2),
                                ("fixture-middle", "standard", 3),
                                ("fixture-strong", "frontier", 5)):
        models.append({**identity(name), "tier": tier, "availability": "available",
                       "context_window": 64000, "tools": ["read", "shell"],
                       "traits": ["creative", "heavy-reasoning", "mechanical"],
                       "capability_evidence": {"reference": f"fixture-quality:{name}",
                                               "date": TODAY.isoformat(), "quality": quality},
                       "price_snapshot": {"reference": f"fixture-price:{name}",
                                          "date": TODAY.isoformat(), "relative_cost": quality}})
    return {"schema_version": 1, "refreshed": TODAY.isoformat(),
            "evidence_date": TODAY.isoformat(), "models": models}


def fixture_request() -> dict[str, Any]:
    return {"scores": {factor: 2 for factor in FACTORS}, "hard_constraints": [],
            "traits": [], "task_class": "fixture-equivalent-work",
            "requirements": {"context_tokens": 8000, "tools": ["read", "shell"]},
            "harness": {"reference": "fixture-request-support", "date": TODAY.isoformat(),
                        "models": [{**identity(model["id"]), "availability": "available",
                                    "context_window": 64000, "tools": ["read", "shell"]}
                                   for model in fixture_catalog()["models"]]},
            "owner": {"allowed_models": None, "excluded_models": []},
            "default_model": identity("fixture-strong"), "cost_comparisons": []}


def fixture_comparison() -> dict[str, Any]:
    return {"reference": "fixture-evaluation:equivalent-result-quality",
            "date": TODAY.isoformat(), "qualification": "comparable-task-evaluation",
            "task_class": "fixture-equivalent-work", "quality_floor": 2, "traits": [],
            "requirements": {"context_tokens": 8000, "tools": ["read", "shell"]},
            "currency": "USD", "estimates": [
                {**identity("fixture-small"), "total_cost_lower": "1.00", "total_cost_upper": "2.00"},
                {**identity("fixture-middle"), "total_cost_lower": "3.00", "total_cost_upper": "4.00"},
                {**identity("fixture-strong"), "total_cost_lower": "5.00", "total_cost_upper": "6.00"}]}


def fixture_markdown(catalog: dict[str, Any]) -> str:
    lines = ["# Fictional selection fixture", "", "```json model-catalog",
             json.dumps(catalog), "```", "",
             "| tier | anthropic model id | openai model id | relative cost |",
             "|---|---|---|---|"]
    for model in catalog["models"]:
        lines.append(f"| {model['tier']} | - | {model['id']} | "
                     f"{model['id']}={model['price_snapshot']['relative_cost']} |")
    return "\n".join(lines) + "\n"


class SelectionContractTests(unittest.TestCase):
    def api(self) -> dict[str, Any]:
        self.assertTrue(SELECTOR.is_file(),
                        "selection policy unavailable: expected scripts/model_selection.py")
        return runpy.run_path(str(SELECTOR), run_name="selection_contract_fixture")

    def select(self, api: dict[str, Any], catalog: dict[str, Any],
               request: dict[str, Any]) -> dict[str, Any]:
        return api["select_model"](catalog, request, TODAY)

    def test_floor_every_score_tuple_has_exact_bounded_weighted_result(self) -> None:
        api = self.api()
        observed = set()
        for values in product(range(1, 6), repeat=7):
            scores = dict(zip(FACTORS, values))
            expected = (25 * scores["C"] + 20 * scores["A"] + 20 * scores["R"]
                        + 20 * scores["Crit"] + 15 * scores["V"] + 50) // 100
            expected = max(1, min(5, expected + (scores["RW"] == 5) - (scores["Ver"] == 5)))
            actual = api["quality_floor"](scores)
            self.assertEqual(actual, expected, scores)
            observed.add(actual)
        self.assertEqual(observed, {1, 2, 3, 4, 5})

    def test_floor_every_worsening_neighbor_never_decreases_requirement(self) -> None:
        api = self.api()
        for values in product(range(1, 6), repeat=7):
            scores = dict(zip(FACTORS, values))
            floor = api["quality_floor"](scores)
            for factor in FACTORS:
                step = -1 if factor == "Ver" else 1
                if 1 <= scores[factor] + step <= 5:
                    worse = dict(scores, **{factor: scores[factor] + step})
                    self.assertGreaterEqual(api["quality_floor"](worse), floor, (scores, factor))

    def test_floor_invalid_scores_and_unknown_constraints_are_rejected(self) -> None:
        api = self.api()
        for factor in FACTORS:
            for value in (0, 6, -1, 2.0, "2", True, False, None):
                with self.subTest(factor=factor, value=value):
                    with self.assertRaises(ValueError):
                        api["quality_floor"](dict(fixture_request()["scores"], **{factor: value}))
        for scores in ({}, {"C": 2}, dict(fixture_request()["scores"], extra=2), None, []):
            with self.assertRaises(ValueError):
                api["quality_floor"](scores)
        for constraints in (["unknown"], "security", [True], ["security", "security"]):
            with self.assertRaises(ValueError):
                api["quality_floor"](fixture_request()["scores"], constraints)

    def test_floor_hard_categories_require_five_even_with_easy_creative_work(self) -> None:
        api = self.api()
        scores = {factor: 1 for factor in FACTORS}
        scores["Ver"] = 5
        for constraint in ("security", "financial", "architecture", "core-invariant", "high-blast-radius"):
            self.assertEqual(api["quality_floor"](scores, [constraint]), 5)
            catalog, request = fixture_catalog(), fixture_request()
            request.update(scores=scores, hard_constraints=[constraint], traits=["creative"])
            report = self.select(api, catalog, request)
            self.assertEqual(report["quality_floor"], 5)
            self.assertEqual(report["selected"], identity("fixture-strong"))
            self.assertEqual(report["eligible"], [identity("fixture-strong")])

    def test_eligibility_actual_availability_is_required_before_economics(self) -> None:
        api = self.api()
        for unavailable in ("unavailable", "unknown", "missing"):
            catalog, request = fixture_catalog(), fixture_request()
            request["cost_comparisons"] = [fixture_comparison()]
            if unavailable == "missing":
                request["harness"]["models"].pop(0)
            else:
                request["harness"]["models"][0]["availability"] = unavailable
            report = self.select(api, catalog, request)
            self.assertNotIn(identity("fixture-small"), report["eligible"])
            self.assertEqual(report["excluded"][0]["id"], "fixture-small")
            self.assertIn("harness-unavailable", report["excluded"][0]["reasons"])
            self.assertNotEqual(report["selected"], identity("fixture-small"))
        for catalog_state in ("unknown", "unavailable"):
            catalog = fixture_catalog()
            catalog["models"][0]["availability"] = catalog_state
            report = self.select(api, catalog, fixture_request())
            self.assertIn("catalog-unavailable", report["excluded"][0]["reasons"])

    def test_eligibility_context_tools_owner_and_quality_precede_economics(self) -> None:
        api = self.api()
        cases = (("context", "context-insufficient"), ("tools", "tools-unsupported"),
                 ("owner", "owner-excluded"), ("quality", "quality-below-floor"),
                 ("capability", "quality-unknown"))
        for condition, reason in cases:
            for boundary in ("catalog", "harness") if condition in ("context", "tools") else ("catalog",):
                catalog, request = fixture_catalog(), fixture_request()
                request["cost_comparisons"] = [fixture_comparison()]
                entry = catalog["models"][0] if boundary == "catalog" else request["harness"]["models"][0]
                if condition == "context":
                    entry["context_window"] = 7999
                elif condition == "tools":
                    entry["tools"] = ["read"]
                elif condition == "owner":
                    request["owner"]["excluded_models"] = [identity("fixture-small")]
                elif condition == "quality":
                    entry["capability_evidence"]["quality"] = 1
                else:
                    entry["capability_evidence"] = None
                report = self.select(api, catalog, request)
                self.assertNotIn(identity("fixture-small"), report["eligible"])
                self.assertIn(reason, report["excluded"][0]["reasons"])
                self.assertNotEqual(report["selected"], identity("fixture-small"))

    def test_eligibility_unknown_limits_and_empty_allowlist_do_not_admit_candidates(self) -> None:
        api = self.api()
        for field in ("context_window", "tools"):
            for boundary in ("catalog", "harness"):
                catalog, request = fixture_catalog(), fixture_request()
                entries = catalog["models"] if boundary == "catalog" else request["harness"]["models"]
                for entry in entries:
                    entry[field] = None
                report = self.select(api, catalog, request)
                self.assertEqual(report["status"], "stopped")
                self.assertIsNone(report["selected"])
        request = fixture_request()
        request["owner"]["allowed_models"] = []
        report = self.select(api, fixture_catalog(), request)
        self.assertEqual(report["eligible"], [])
        self.assertEqual(report["status"], "stopped")
        self.assertTrue(report["reasons"])

    def test_economics_price_band_equal_prices_and_unknown_prices_retain_default(self) -> None:
        api = self.api()
        for prices in ((1, 1, 1), (None, None, None), (1, 999, None)):
            catalog, request = fixture_catalog(), fixture_request()
            for model, price in zip(catalog["models"], prices):
                model["price_snapshot"] = None if price is None else {
                    "reference": "fixture-token-price", "date": TODAY.isoformat(), "relative_cost": price}
            report = self.select(api, catalog, request)
            self.assertEqual(report["selected"], request["default_model"])
            self.assertTrue(report["uncertainty"])
            self.assertIn("fixture-quality:fixture-strong", report["evidence"])
        catalog = fixture_catalog()
        catalog["models"][0]["tier"], catalog["models"][2]["tier"] = "frontier", "light"
        report = self.select(api, catalog, fixture_request())
        self.assertEqual(report["selected"], identity("fixture-strong"))

    def test_economics_qualified_comparable_total_cost_can_recommend_cheaper_model(self) -> None:
        api = self.api()
        catalog, request = fixture_catalog(), fixture_request()
        request["cost_comparisons"] = [fixture_comparison()]
        report = self.select(api, catalog, request)
        self.assertEqual(report["status"], "selected")
        self.assertEqual(report["selected"], identity("fixture-small"))
        self.assertIn(request["cost_comparisons"][0]["reference"], report["evidence"])
        self.assertTrue(report["reasons"])
        self.assertNotIn("actual_model", report)

    def test_economics_incomparable_or_unqualified_evidence_retains_default(self) -> None:
        api = self.api()
        mutations = (("reference", ""), ("date", (TODAY + timedelta(days=1)).isoformat()),
                     ("qualification", "uncalibrated-judgment"), ("task_class", "other-work"),
                     ("quality_floor", 1), ("traits", ["creative"]), ("currency", ""),
                     ("requirements", {"context_tokens": 7999, "tools": ["read"]}))
        for field, value in mutations:
            request, comparison = fixture_request(), fixture_comparison()
            comparison[field] = value
            request["cost_comparisons"] = [comparison]
            report = self.select(api, fixture_catalog(), request)
            self.assertEqual(report["selected"], request["default_model"], field)
            self.assertTrue(report["uncertainty"], field)
        request = fixture_request()
        request["cost_comparisons"] = [{"reference": "fixture-token-price-only", "relative_cost": 0.01}]
        self.assertEqual(self.select(api, fixture_catalog(), request)["selected"], request["default_model"])

    def test_economics_equal_overlapping_invalid_and_missing_totals_retain_default(self) -> None:
        api = self.api()
        for lower, upper in (("5.00", "6.00"), ("1", "5"), ("1", "9"),
                             ("NaN", "2"), ("1", "Infinity"), ("2", "1"),
                             (True, "2"), (None, "2"), ("-1", "2")):
            request, comparison = fixture_request(), fixture_comparison()
            comparison["estimates"][0].update(total_cost_lower=lower, total_cost_upper=upper)
            comparison["estimates"][1].update(total_cost_lower="5", total_cost_upper="7")
            request["cost_comparisons"] = [comparison]
            report = self.select(api, fixture_catalog(), request)
            self.assertEqual(report["selected"], request["default_model"], (lower, upper))
        request, comparison = fixture_request(), fixture_comparison()
        comparison["estimates"].pop()
        request["cost_comparisons"] = [comparison]
        self.assertEqual(self.select(api, fixture_catalog(), request)["selected"], request["default_model"])

    def test_economics_stronger_first_remains_selectable_with_qualified_lower_total(self) -> None:
        api = self.api()
        catalog, request, comparison = fixture_catalog(), fixture_request(), fixture_comparison()
        request["default_model"] = identity("fixture-small")
        comparison["estimates"][0].update(total_cost_lower="5", total_cost_upper="6")
        comparison["estimates"][2].update(total_cost_lower="1", total_cost_upper="2")
        request["cost_comparisons"] = [comparison]
        report = self.select(api, catalog, request)
        self.assertEqual(report["selected"], identity("fixture-strong"))
        self.assertIn(comparison["reference"], report["evidence"])

    def test_default_missing_or_unsuitable_uses_strongest_eligible_without_invented_identity(self) -> None:
        api = self.api()
        for default in (None, identity("not-in-catalog"), identity("fixture-small")):
            request = fixture_request()
            request.update(default_model=default, hard_constraints=["security"])
            report = self.select(api, fixture_catalog(), request)
            self.assertEqual(report["selected"], identity("fixture-strong"))
            self.assertTrue(report["reasons"])
        request = fixture_request()
        request["harness"]["models"] = []
        report = self.select(api, fixture_catalog(), request)
        self.assertEqual(report["status"], "stopped")
        self.assertIsNone(report["selected"])
        self.assertEqual(report["eligible"], [])

    def test_traits_legacy_mapping_is_explicit_and_unknown_conflicts_are_rejected(self) -> None:
        api = self.api()
        cases = (([], []), (["general"], []), (["general (default)"], []),
                 (["creative"], ["creative"]), (["coding-heavy"], ["heavy-reasoning"]),
                 (["long-context"], ["heavy-reasoning"]), (["web-knowledge"], ["heavy-reasoning"]),
                 (["cost-efficient-bulk"], ["mechanical"]),
                 (["creative", "heavy-reasoning"], ["creative", "heavy-reasoning"]))
        for incoming, expected in cases:
            self.assertEqual(api["normalize_traits"](incoming), expected)
        for traits in (["unknown"], ["creative", "mechanical"], ["heavy-reasoning", "mechanical"],
                       ["creative", "creative"], ["general", "creative"], "creative", None, [True]):
            with self.assertRaises(ValueError):
                api["normalize_traits"](traits)

    def test_traits_each_override_filters_support_without_bypassing_quality_floor(self) -> None:
        api = self.api()
        for trait in ("creative", "heavy-reasoning", "mechanical"):
            catalog, request = fixture_catalog(), fixture_request()
            catalog["models"][0]["traits"] = []
            request["traits"] = [trait]
            report = self.select(api, catalog, request)
            self.assertEqual(report["traits"], [trait])
            self.assertNotIn(identity("fixture-small"), report["eligible"])
            self.assertIn("traits-unsupported", report["excluded"][0]["reasons"])
            request["hard_constraints"] = ["financial"]
            report = self.select(api, catalog, request)
            self.assertEqual(report["selected"], identity("fixture-strong"))
            self.assertEqual(report["quality_floor"], 5)

    def test_identity_same_id_different_providers_is_never_conflated(self) -> None:
        api = self.api()
        catalog, request = fixture_catalog(), fixture_request()
        other = deepcopy(catalog["models"][2])
        other.update(provider="anthropic", availability="available")
        catalog["models"].append(other)
        request["default_model"] = identity("fixture-strong", "anthropic")
        report = self.select(api, catalog, request)
        self.assertEqual(report["selected"], identity("fixture-strong"))
        self.assertNotIn(identity("fixture-strong", "anthropic"), report["eligible"])

    def test_request_invalid_snapshot_requirements_and_owner_shapes_are_rejected(self) -> None:
        api = self.api()
        cases = (("harness", None), ("harness", {"models": []}),
                 ("requirements", {"context_tokens": True, "tools": []}),
                 ("requirements", {"context_tokens": 0, "tools": []}),
                 ("requirements", {"context_tokens": 100, "tools": ["read", "read"]}),
                 ("owner", {"allowed_models": ["fixture-small"], "excluded_models": []}),
                 ("default_model", "fixture-strong"), ("task_class", ""),
                 ("traits", ["creative", "mechanical"]))
        for field, value in cases:
            request = fixture_request()
            request[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.select(api, fixture_catalog(), request)
        request = fixture_request()
        request["harness"]["models"].append(deepcopy(request["harness"]["models"][0]))
        with self.assertRaises(ValueError):
            self.select(api, fixture_catalog(), request)

    def test_selection_is_offline_readonly_repeatable_and_does_not_mutate_inputs(self) -> None:
        api = self.api()
        catalog, request = fixture_catalog(), fixture_request()
        before = deepcopy((catalog, request))
        with patch.object(socket, "socket", side_effect=AssertionError("network access")), \
             patch.object(urllib.request, "urlopen", side_effect=AssertionError("network access")), \
             patch.object(subprocess, "run", side_effect=AssertionError("process execution")):
            first = self.select(api, catalog, request)
            self.assertEqual(self.select(api, catalog, request), first)
        self.assertEqual((catalog, request), before)
        self.assertEqual(first["selected"], request["default_model"])

    def test_cli_selection_reports_recommendation_and_refuses_refresh_combination_before_writes(self) -> None:
        self.api()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, request_path = root / "catalog.md", root / "request.json"
            catalog.write_text(fixture_markdown(fixture_catalog()))
            request_path.write_text(json.dumps(fixture_request()))
            environment = dict(os.environ, HOME=str(root / "home"), XDG_CONFIG_HOME=str(root / "config"),
                               PYTHONDONTWRITEBYTECODE="1")
            command = [sys.executable, str(COMMAND), "--catalog", str(catalog),
                       "--today", TODAY.isoformat(), "--select", str(request_path)]
            before = catalog.read_bytes()
            result = subprocess.run(command, capture_output=True, text=True, env=environment, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["selected"], identity("fixture-strong"))
            self.assertEqual(report["quality_floor"], 2)
            self.assertNotIn("actual_model", report)
            refused = subprocess.run(command + ["--refresh", str(request_path)], capture_output=True,
                                     text=True, env=environment, timeout=10)
            self.assertEqual(refused.returncode, 2)
            self.assertEqual(catalog.read_bytes(), before)
            self.assertEqual(sorted(path.name for path in root.iterdir()), ["catalog.md", "request.json"])
            request = fixture_request()
            request["harness"]["models"] = []
            request_path.write_text(json.dumps(request))
            stopped = subprocess.run(command, capture_output=True, text=True, env=environment, timeout=10)
            self.assertEqual(stopped.returncode, 2, stopped.stderr)
            self.assertEqual(json.loads(stopped.stdout)["status"], "stopped")
            self.assertIsNone(json.loads(stopped.stdout)["selected"])
            request_path.write_text('{"scores": invalid}')
            malformed = subprocess.run(command, capture_output=True, text=True, env=environment, timeout=10)
            self.assertEqual(malformed.returncode, 2)
            self.assertEqual(json.loads(malformed.stdout)["status"], "unavailable")


    def test_request_dated_harness_snapshot_cannot_authorize_current_selection(self) -> None:
        api = self.api()
        for age in (1, 14, 31, 365):
            request = fixture_request()
            request["harness"]["date"] = (TODAY - timedelta(days=age)).isoformat()
            with self.subTest(age=age), self.assertRaises(ValueError):
                self.select(api, fixture_catalog(), request)


if __name__ == "__main__":
    unittest.main(verbosity=2)
