#!/usr/bin/env python3
"""Contracts for the frozen validator inventory and measurement manifest."""

import copy
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validator_runtime_oracle", ROOT / "tests/fixtures/validator-runtime/oracle.py")
ORACLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORACLE)


def sample(seconds: float) -> dict:
    return {"exit_code": 0, "failures": 0, "elapsed_seconds": seconds,
            "user_seconds": 10.0, "system_seconds": 2.0,
            "max_rss_kb": 1000, "pass_count": 500, "skip_count": 2,
            "stdout": "stdout.txt", "stderr": "stderr.txt",
            "time_output": "time.txt"}


def manifest() -> dict:
    return {"commit": "a" * 40, "payload_sha256": "b" * 64,
            "configuration_sha256": "c" * 64, "locale": "C", "cache_policy": "warm",
            "source_blob": "d" * 40, "dirty_paths": [], "machine": "fixture",
            "cpu_quota": "unlimited", "ram_bytes": 1000000,
            "python_version": "3.11", "bash_version": "5.2", "grep_version": "3.8",
            "bytecode_existed": False, "hygiene_policy": "isolated",
            "cpu_count": 4, "jobs": 1,
            "samples": [sample(100), sample(102)]}


class OracleContract(unittest.TestCase):
    def test_inventory_contains_all_source_contracts(self) -> None:
        inventory = ORACLE.inventory(ROOT / "scripts/validate-contracts.sh")
        self.assertIsInstance(inventory, dict)
        self.assertEqual(len(inventory["expressions"]), 36)
        self.assertEqual(len(inventory["focused"]), 37)
        self.assertGreater(len(inventory["results"]), 36)
        self.assertEqual(len(inventory["resources"]), 36)
        self.assertTrue(all(row["classification"] in {"independent", "exclusive", "conflict"}
                            and row["evidence"] for row in inventory["resources"]))

    def test_matching_inventory_is_accepted(self) -> None:
        inventory = {"results": ["first", "second"],
                     "expressions": [{"name": "first", "body": "true"}],
                     "focused": ["--example-only"], "resources": []}
        self.assertIs(ORACLE.matches(inventory, copy.deepcopy(inventory)), True)

    def test_independent_name_expression_and_order_mutations_rejected(self) -> None:
        inventory = {"results": ["first", "second"],
                     "expressions": [{"name": "first", "body": "true"}],
                     "focused": ["--example-only"], "resources": []}
        mutations = []
        changed = copy.deepcopy(inventory)
        changed["expressions"][0]["name"] = "changed"
        mutations.append(changed)
        changed = copy.deepcopy(inventory)
        changed["expressions"][0]["body"] = "false"
        mutations.append(changed)
        changed = copy.deepcopy(inventory)
        changed["results"].reverse()
        mutations.append(changed)
        for changed in mutations:
            with self.subTest(changed=changed):
                self.assertIs(ORACLE.matches(inventory, changed), False)

    def test_two_consistent_successful_samples_accepted(self) -> None:
        self.assertIs(ORACLE.valid_manifest(manifest(), "b" * 64, "c" * 64), True)

    def test_incomplete_failed_or_drifted_manifest_rejected(self) -> None:
        examples = []
        missing = manifest()
        del missing["locale"]
        examples.append((missing, "b" * 64, "c" * 64))
        failed = manifest()
        failed["samples"][0]["failures"] = 1
        examples.append((failed, "b" * 64, "c" * 64))
        incomplete = manifest()
        del incomplete["samples"][0]["max_rss_kb"]
        examples.append((incomplete, "b" * 64, "c" * 64))
        bad_exit = manifest()
        bad_exit["samples"][0]["exit_code"] = 1
        examples.append((bad_exit, "b" * 64, "c" * 64))
        examples.append((manifest(), "d" * 64, "c" * 64))
        examples.append((manifest(), "b" * 64, "d" * 64))
        for record, payload, config in examples:
            with self.subTest(record=record, payload=payload, config=config):
                self.assertIs(ORACLE.valid_manifest(record, payload, config), False)

    def test_high_variance_requires_third_retained_sample(self) -> None:
        record = manifest()
        record["samples"][1]["elapsed_seconds"] = 120
        self.assertIs(ORACLE.valid_manifest(record, "b" * 64, "c" * 64), False)
        record["samples"].append(sample(110))
        self.assertIs(ORACLE.valid_manifest(record, "b" * 64, "c" * 64), True)


if __name__ == "__main__":
    unittest.main()
