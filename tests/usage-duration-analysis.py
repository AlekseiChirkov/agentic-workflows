#!/usr/bin/env python3
"""Offline contract tests for measured interval analysis."""

import importlib.util
import pathlib
import unittest

MODULE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "usage_telemetry_duration.py"
if MODULE.exists():
    spec = importlib.util.spec_from_file_location("usage_telemetry_duration", MODULE)
    duration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(duration)
else:
    duration = None


def analyze(parent, children, *, complete=True, offsets=None):
    if duration is None:
        return None
    return duration.analyze_intervals(parent, children, complete=complete, clock_offsets=offsets)


def interval(identifier, start, end, *, parent_id=None, clock="clock-a", approximate=False):
    return {"id": identifier, "parent_id": parent_id, "start_ms": start,
            "end_ms": end, "clock": clock, "approximate": approximate}


class DurationAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.parent = interval("p", 0, 10)
        self.children = [interval("a", 1, 7, parent_id="p"),
                         interval("b", 4, 9, parent_id="p")]

    def test_overlapping_children_have_distinct_sum_and_union(self):
        result = analyze(self.parent, self.children)
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertEqual((result["wall_ms"], result["worker_sum_ms"],
                          result["coverage_ms"], result["exclusive_ms"]), (10, 11, 8, 2))
        self.assertTrue(result["coverage_complete"])

    def test_grandchildren_are_not_subtracted_again(self):
        result = analyze(self.parent, self.children + [interval("g", 2, 5, parent_id="a")])
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertEqual((result["worker_sum_ms"], result["coverage_ms"], result["exclusive_ms"]),
                         (11, 8, 2))

    def test_missing_child_preserves_observed_coverage_but_not_exclusive(self):
        result = analyze(self.parent, self.children, complete=False)
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertEqual(result["coverage_ms"], 8)
        self.assertFalse(result["coverage_complete"])
        self.assertIsNone(result["exclusive_ms"])

    def test_incompatible_clock_prevents_exclusive(self):
        children = [self.children[0], interval("b", 4, 9, parent_id="p", clock="clock-b")]
        result = analyze(self.parent, children)
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertIsNone(result["exclusive_ms"])
        self.assertFalse(result["coverage_complete"])

    def test_proven_offset_makes_clocks_comparable(self):
        children = [interval("a", 101, 107, parent_id="p", clock="clock-b")]
        result = analyze(self.parent, children, offsets={"clock-b": -100})
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertEqual((result["coverage_ms"], result["exclusive_ms"]), (6, 4))

    def test_out_of_bounds_child_is_clipped_but_tree_is_inconsistent(self):
        result = analyze(self.parent, [interval("a", -2, 4, parent_id="p")])
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertEqual(result["coverage_ms"], 4)
        self.assertFalse(result["coverage_complete"])
        self.assertIsNone(result["exclusive_ms"])

    def test_unrelated_overlap_does_not_prove_parentage(self):
        result = analyze(self.parent, self.children + [interval("orphan", 3, 6, parent_id="missing")])
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertIsNone(result["exclusive_ms"])
        self.assertFalse(result["coverage_complete"])

    def test_duplicate_identical_interval_is_not_counted_twice(self):
        result = analyze(self.parent, self.children + [dict(self.children[0])])
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertEqual((result["worker_sum_ms"], result["coverage_ms"], result["exclusive_ms"]),
                         (11, 8, 2))

    def test_conflicting_duplicate_identity_invalidates_tree(self):
        result = analyze(self.parent, self.children + [interval("a", 2, 5, parent_id="p")])
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertFalse(result["coverage_complete"])
        self.assertIsNone(result["exclusive_ms"])

    def test_negative_and_unfinished_intervals_are_not_exact(self):
        for child in (interval("a", 8, 2, parent_id="p"),
                      interval("a", 2, None, parent_id="p")):
            with self.subTest(child=child):
                result = analyze(self.parent, [child])
                self.assertIsNotNone(result, "measured interval analysis is required")
                self.assertIsNone(result["exclusive_ms"])
                self.assertFalse(result["coverage_complete"])

    def test_invalid_parent_does_not_report_exact_wall(self):
        result = analyze(interval("p", 10, 0), [])
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertIsNone(result["wall_ms"])
        self.assertIsNone(result["exclusive_ms"])

    def test_empty_complete_tree_has_zero_child_work(self):
        result = analyze(self.parent, [])
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertEqual((result["wall_ms"], result["worker_sum_ms"], result["coverage_ms"],
                          result["exclusive_ms"]), (10, 0, 0, 10))

    def test_omitted_completeness_does_not_prove_exclusive(self):
        self.assertIsNotNone(duration, "measured interval analysis is required")
        result = duration.analyze_intervals(self.parent, self.children)
        self.assertEqual(result["coverage_ms"], 8)
        self.assertFalse(result["coverage_complete"])
        self.assertIsNone(result["exclusive_ms"])

    def test_conflicting_identifiers_are_unknown_independent_of_order(self):
        first = interval("a", 1, 7, parent_id="p")
        second = interval("a", 2, 5, parent_id="p")
        for children in ([first, second], [second, first]):
            with self.subTest(children=children):
                result = analyze(self.parent, children, complete=True)
                self.assertIsNone(result["worker_sum_ms"])
                self.assertIsNone(result["coverage_ms"])
                self.assertIsNone(result["exclusive_ms"])
                self.assertFalse(result["coverage_complete"])

    def test_invalid_child_identity_does_not_claim_zero_work(self):
        child = interval("", 1, 7, parent_id="p")
        result = analyze(self.parent, [child], complete=True)
        self.assertIsNone(result["worker_sum_ms"])
        self.assertIsNone(result["coverage_ms"])
        self.assertIsNone(result["exclusive_ms"])
        self.assertFalse(result["coverage_complete"])

    def test_explicit_complete_graph_proves_exclusive(self):
        result = analyze(self.parent, self.children, complete=True)
        self.assertEqual(result["exclusive_ms"], 2)
        self.assertTrue(result["coverage_complete"])

    def test_unhashable_parent_identifiers_are_invalid_parentage(self):
        for invalid in ([], {}):
            for children in (
                [interval("bad", 1, 4, parent_id=invalid)],
                [interval("a", 1, 7, parent_id="p"),
                 interval("bad", 2, 4, parent_id=invalid)],
            ):
                with self.subTest(invalid=invalid, children=children):
                    result = analyze(self.parent, children, complete=True)
                    self.assertIsNone(result["exclusive_ms"])
                    self.assertFalse(result["coverage_complete"])
                    self.assertIn("invalid_parentage", result["diagnostics"])

    def test_non_string_parentage_does_not_claim_zero_work(self):
        for invalid in (None, 3):
            with self.subTest(invalid=invalid):
                result = analyze(self.parent, [interval("bad", 1, 4, parent_id=invalid)], complete=True)
                self.assertIsNone(result["worker_sum_ms"])
                self.assertIsNone(result["coverage_ms"])
                self.assertIsNone(result["exclusive_ms"])
                self.assertFalse(result["coverage_complete"])
                self.assertIn("invalid_parentage", result["diagnostics"])

    def test_diagnostics_are_stable_under_input_permutation(self):
        children = [interval("bad-clock", 1, 4, parent_id="p", clock="other"),
                    interval("orphan", 2, 3, parent_id="missing")]
        first = analyze(self.parent, children, complete=True)
        second = analyze(self.parent, list(reversed(children)), complete=True)
        self.assertEqual(first, second)
        self.assertIn("invalid_parentage", first["diagnostics"])
        self.assertIn("invalid_or_incompatible_interval", first["diagnostics"])

    def test_approximate_intervals_never_become_exact(self):
        result = analyze(self.parent, [interval("a", 1, 7, parent_id="p", approximate=True)])
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertIsNone(result["exclusive_ms"])
        self.assertFalse(result["coverage_complete"])

    def test_gaps_are_not_invented_as_waiting(self):
        result = analyze(self.parent, self.children)
        self.assertIsNotNone(result, "measured interval analysis is required")
        self.assertNotIn("waiting_ms", result)


if __name__ == "__main__":
    unittest.main()
