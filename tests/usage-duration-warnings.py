#!/usr/bin/env python3
"""Offline duration warning decisions from explicitly supplied evidence."""

import importlib.util
import pathlib
import statistics
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "usage_telemetry_duration_warning.py"
if MODULE_PATH.exists():
    spec = importlib.util.spec_from_file_location("duration_warning", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    decide = module.evaluate_duration
else:
    # Keep tests executable in the absence of the feature.
    def decide(*args, **kwargs):
        return None


GROUP = {
    "stage": "review",
    "duration_kind": "work",
    "clock_quality": "measured",
    "environment": "local",
    "profile": "default",
    "contract": "v1",
    "configuration": "standard",
}
NOW = "2026-10-01T12:00:00Z"


def candidate(seconds=7201, **changes):
    value = {"id": "candidate", "seconds": seconds, "closed": True,
             "clock_quality": "measured", "collection": "on", "group": dict(GROUP)}
    value.update(changes)
    return value


def sample(identifier, seconds=3000, **changes):
    value = {"id": identifier, "seconds": seconds, "closed": True,
             "clock_quality": "measured", "kind": "work", "group": dict(GROUP)}
    value.update(changes)
    return value


def export(samples, **changes):
    eligible = [item["seconds"] for item in samples
                if item.get("id") != "candidate" and item.get("closed") is True
                and item.get("clock_quality") == "measured"
                and item.get("kind") == "work" and item.get("group") == GROUP]
    value = {"schema_version": 1, "group": dict(GROUP),
             "corpus_hash": "sha256:" + "a" * 64,
             "window_start": "2026-09-01T00:00:00Z", "window_end": "2026-10-01T00:00:00Z",
             "created_at": "2026-10-01T00:00:00Z", "expires_at": "2026-10-02T00:00:00Z",
             "sample_size": len(eligible),
             "median": str(statistics.median(eligible)) if eligible else None,
             "samples": samples}
    value.update(changes)
    return value


def decision(warn, historical=False, approximate=False):
    return {"available": True, "warn": warn, "historical": historical,
            "approximate": approximate}


class DurationWarnings(unittest.TestCase):
    def test_two_hour_boundary_without_history(self):
        self.assertEqual(decide(candidate(7200), None, NOW), decision(False))
        self.assertEqual(decide(candidate(7201), None, NOW), decision(True))

    def test_four_samples_use_fallback(self):
        history = export([sample(str(i)) for i in range(4)])
        self.assertEqual(decide(candidate(7201), history, NOW), decision(True))

    def test_five_samples_require_both_strict_boundaries(self):
        history = export([sample(str(i)) for i in range(5)])
        self.assertEqual(decide(candidate(7200), history, NOW), decision(False, True))
        self.assertEqual(decide(candidate(9000), history, NOW), decision(False, True))
        self.assertEqual(decide(candidate(9001), history, NOW), decision(True, True))

    def test_candidate_is_excluded_before_sample_count(self):
        history = export([sample("candidate", 1)] + [sample(str(i)) for i in range(4)])
        self.assertEqual(decide(candidate(7201), history, NOW), decision(True))

    def test_ineligible_samples_do_not_establish_history(self):
        history = export([sample(str(i)) for i in range(4)] + [
            sample("waiting", kind="wait"),
            sample("summary", kind="summary"),
            sample("open", closed=False),
            sample("incorrect", clock_quality="invalid"),
            sample("estimate", clock_quality="approximate"),
            sample("different", group={**GROUP, "environment": "other"}),
        ])
        self.assertEqual(decide(candidate(7201), history, NOW), decision(True))

    def test_candidate_only_cannot_supply_history(self):
        history = export([sample("candidate", 1)])
        self.assertEqual(decide(candidate(7201), history, NOW), decision(True))

    def test_expired_and_incompatible_exports_use_fallback(self):
        samples = [sample(str(i)) for i in range(5)]
        for history in (export(samples, expires_at=NOW),
                        export(samples, schema_version=2),
                        export(samples, group={**GROUP, "profile": "other"})):
            with self.subTest(history=history):
                self.assertEqual(decide(candidate(7201), history, NOW), decision(True))

    def test_boolean_version_is_not_version_one(self):
        history = export([sample(str(i)) for i in range(5)], schema_version=True)
        self.assertEqual(decide(candidate(7201), history, NOW), decision(True))

    def test_missing_required_aggregates_use_fallback(self):
        samples = [sample(str(i)) for i in range(5)]
        for missing in ("sample_size", "median"):
            history = export(samples)
            del history[missing]
            with self.subTest(missing=missing):
                self.assertEqual(decide(candidate(7201), history, NOW), decision(True))

    def test_forged_aggregate_values_use_fallback(self):
        samples = [sample(str(i)) for i in range(5)]
        for overrides in ({"sample_size": 6}, {"sample_size": True},
                          {"median": "1000"}, {"median": "invalid"}):
            with self.subTest(overrides=overrides):
                self.assertEqual(decide(candidate(7201), export(samples, **overrides), NOW),
                                 decision(True))

    def test_excessively_long_median_uses_fallback(self):
        history = export([sample(str(i)) for i in range(5)], median="9" * 5000)
        self.assertEqual(decide(candidate(7201), history, NOW), decision(True))

    def test_aggregate_values_exclude_candidate_and_ineligible_records(self):
        samples = [sample("candidate", 1), sample("waiting", 1, kind="wait")]
        samples += [sample(str(i)) for i in range(5)]
        history = export(samples)
        self.assertEqual(history["sample_size"], 5)
        self.assertEqual(history["median"], "3000")
        self.assertEqual(decide(candidate(7201), history, NOW), decision(False, True))
        history["sample_size"] = 7
        self.assertEqual(decide(candidate(7201), history, NOW), decision(True))

    def test_malformed_or_future_evidence_uses_fallback(self):
        samples = [sample(str(i)) for i in range(5)]
        for history in (export(samples, corpus_hash="not-a-hash"),
                        export(samples, created_at="2026-10-02T00:00:00Z"),
                        export(samples, window_start="2026-10-02T00:00:00Z")):
            with self.subTest(history=history):
                self.assertEqual(decide(candidate(7201), history, NOW), decision(True))

    def test_even_median_uses_two_central_values(self):
        history = export([sample(str(i), seconds) for i, seconds in enumerate(
            (1000, 1000, 2000, 4000, 4000, 4000))])
        self.assertEqual(decide(candidate(9000), history, NOW), decision(False, True))
        self.assertEqual(decide(candidate(9001), history, NOW), decision(True, True))

    def test_collection_off_still_allows_time_only_warning(self):
        self.assertEqual(decide(candidate(7201, collection="off"), None, NOW), decision(True))

    def test_missing_clock_and_unclosed_interval_are_unavailable(self):
        self.assertEqual(decide(candidate(None), None, NOW),
                         {"available": False, "reason": "clock_unavailable"})
        self.assertEqual(decide(candidate(7201, closed=False), None, NOW),
                         {"available": False, "reason": "interval_unclosed"})

    def test_approximate_warning_is_not_measured_anomaly(self):
        history = export([sample(str(i), 1) for i in range(5)])
        approximate = candidate(7201, clock_quality="approximate",
                                group={**GROUP, "clock_quality": "approximate"})
        self.assertEqual(decide(approximate, history, NOW), decision(True, False, True))


if __name__ == "__main__":
    unittest.main()
