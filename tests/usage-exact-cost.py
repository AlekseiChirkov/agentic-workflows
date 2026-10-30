#!/usr/bin/env python3
"""Contract tests for exact, evidence-scoped cost arithmetic."""

import importlib.util
from pathlib import Path
import unittest


MODULE = Path(__file__).resolve().parents[1] / "scripts" / "usage_telemetry_exact_cost.py"
if MODULE.exists():
    spec = importlib.util.spec_from_file_location("usage_telemetry_exact_cost", MODULE)
    exact_cost = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exact_cost)
else:
    exact_cost = None


def component(name, quantity, price, unit=1_000_000):
    return {"id": name, "quantity": quantity, "price_usd": price, "unit": unit}


def coverage(**overrides):
    # These describe conclusions already established by upstream evidence checks.
    result = {
        "inventory_complete": True,
        "identities_resolved": True,
        "quantities_final": True,
        "prices_applicable": True,
        "scope_proven": True,
        "nonoverlapping": True,
        "excluded_cannot_reduce": True,
        "contradiction": False,
        "historical_substitution": False,
        "unknown_signed_components": False,
    }
    result.update(overrides)
    return result


class ExactCostTests(unittest.TestCase):
    def evaluate(self, components, **overrides):
        self.assertIsNotNone(exact_cost, "exact cost module is unavailable")
        return exact_cost.calculate_cost(components, coverage(**overrides))

    def test_inclusive_cache_and_reasoning_are_not_counted_twice(self):
        # Upstream normalization has removed the included cache and reasoning.
        result = self.evaluate([
            component("input", 800, "2"), component("read", 200, "0.2"),
            component("output", 100, "10"),
        ])
        self.assertEqual(result["cost_usd"], "0.00264")
        self.assertEqual(result["display_usd"], "0.00")

    def test_separate_cache_write_ttls(self):
        result = self.evaluate([
            component("input", 600, "2"), component("read", 200, "0.2"),
            component("short", 100, "2.5"), component("long", 100, "4"),
            component("output", 100, "10"),
        ])
        self.assertEqual(result["cost_usd"], "0.00289")

    def test_unknown_cache_write_period_is_unpriced_not_zero(self):
        result = self.evaluate([
            component("input", 600, "2"), component("read", 200, "0.2"),
            component("output", 100, "10"),
            {"id": "write", "quantity": 200, "price_usd": None, "unit": None},
        ], prices_applicable=False)
        self.assertNotIn("cost_usd", result)
        self.assertEqual(result["priced_subtotal_usd"], "0.00224")
        self.assertEqual(result["subtotal_quality"], "proven_lower_bound")
        self.assertIn("write", result["unpriced_ids"])

    def test_round_only_the_final_sum(self):
        for price, expected in (("0.005", "0.01"), ("0.015", "0.03")):
            with self.subTest(price=price):
                result = self.evaluate([component("a", 1, price, 1), component("b", 1, price, 1)])
                self.assertEqual(result["cost_usd"], expected)
                self.assertEqual(result["display_usd"], expected)

    def test_half_even_display_and_exact_machine_value(self):
        for value, displayed in (("0.005", "0.00"), ("0.015", "0.02"), ("0.025", "0.02")):
            with self.subTest(value=value):
                result = self.evaluate([component("a", 1, value, 1)])
                self.assertEqual(result["cost_usd"], value)
                self.assertEqual(result["display_usd"], displayed)

    def test_unsupported_repeating_unit_does_not_get_rounded(self):
        result = self.evaluate([component("a", 1, "1", 3)])
        self.assertNotIn("cost_usd", result)
        self.assertIn("a", result["unpriced_ids"])

    def test_large_derived_sum_stays_exact(self):
        result = self.evaluate([
            component("a", 9_007_199_254_740_991, "1", 1),
            component("b", 9_007_199_254_740_991, "1", 1),
        ])
        self.assertEqual(result["cost_usd"], "18014398509481982")
        self.assertEqual(result["display_usd"], "18014398509481982.00")

    def test_known_empty_model_inventory_still_counts_separate_tool(self):
        result = self.evaluate([component("tool", 1, "0.02", 1)])
        self.assertEqual(result["cost_usd"], "0.02")

    def test_empty_unknown_inventory_never_produces_zero_cost(self):
        result = self.evaluate([], inventory_complete=False)
        self.assertNotIn("cost_usd", result)

    def test_proven_empty_billing_scope_is_exactly_zero(self):
        result = self.evaluate([])
        self.assertEqual(result["cost_usd"], "0")

    def test_completeness_requires_each_coverage_condition(self):
        for key in ("inventory_complete", "identities_resolved", "quantities_final", "prices_applicable", "scope_proven", "nonoverlapping"):
            with self.subTest(key=key):
                result = self.evaluate([component("a", 1, "0.02", 1)], **{key: False})
                self.assertNotIn("cost_usd", result)

    def test_conflict_overlap_unknown_sign_or_substitution_forbid_lower_bound(self):
        for overrides in ({"contradiction": True}, {"nonoverlapping": False},
                          {"unknown_signed_components": True}, {"historical_substitution": True},
                          {"excluded_cannot_reduce": False}):
            with self.subTest(overrides=overrides):
                result = self.evaluate([component("a", 1, "0.02", 1)], **overrides)
                self.assertNotIn("cost_usd", result)
                self.assertEqual(result["subtotal_quality"], "subtotal_only")

    def test_duplicate_contributor_is_not_summed_twice(self):
        with self.assertRaises(ValueError):
            self.evaluate([component("a", 1, "0.02", 1), component("a", 1, "0.02", 1)])

    def test_invalid_numbers_are_rejected(self):
        for item in (component("a", -1, "1", 1), component("a", 1, "-1", 1),
                     component("a", 1, "NaN", 1), component("a", 1, "1", 0),
                     component("a", 1, 0.1, 1), component("a", True, "1", 1)):
            with self.subTest(item=item):
                with self.assertRaises((TypeError, ValueError)):
                    self.evaluate([item])

    def test_order_does_not_change_exact_total(self):
        components = [component("a", 1, "0.0000000000000000000000000001", 1),
                      component("b", 9_007_199_254_740_991, "1", 1)]
        expected = "9007199254740991.0000000000000000000000000001"
        self.assertEqual(self.evaluate(components)["cost_usd"], expected)
        self.assertEqual(self.evaluate(list(reversed(components)))["cost_usd"], expected)

    def test_unpriced_reason_distinguishes_unsupported_unit_from_missing_rate(self):
        result = self.evaluate([
            component("repeating", 1, "1", 3),
            {"id": "missing", "quantity": 1, "price_usd": None, "unit": None},
        ], prices_applicable=False)
        self.assertEqual(result["unpriced_reasons"]["repeating"], "unsupported_exact_unit")
        self.assertEqual(result["unpriced_reasons"]["missing"], "missing_price")

    def test_large_accepted_decimal_and_derived_result_have_no_digit_limit(self):
        large = "9" * 4500
        result = self.evaluate([component("a", 1, large, 1), component("b", 1, "1", 1)])
        self.assertEqual(result["cost_usd"], "1" + "0" * 4500)
        self.assertEqual(result["display_usd"], "1" + "0" * 4500 + ".00")

    def test_private_path_is_never_exported_as_a_contributor_id(self):
        private_path = "/home/user/private-credentials"
        with self.assertRaises((ValueError, TypeError)) as caught:
            self.evaluate([{ "id": private_path, "quantity": 1, "price_usd": None, "unit": None }])
        self.assertNotIn(private_path, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
