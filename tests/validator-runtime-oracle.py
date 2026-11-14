#!/usr/bin/env python3
"""Contracts for the frozen validator inventory and measurement manifest."""

import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validator_runtime_oracle", ROOT / "tests/fixtures/validator-runtime/oracle.py")
ORACLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORACLE)

# Fingerprint the immutable compressed inventory before parsing it.
FROZEN_INVENTORY_SHA256 = "57f7872d3525f608b57b29410792e2e02106542f28456f806319e2e7065557a1"


AMENDMENT_SHA256 = "4268fe3f384cd9ccba5a10985527be9d1f4c5f96880e99704442edce9b0306ca"
APPROVED_PATHS = frozenset({
    "scripts/model-catalog.py", "scripts/model_selection.py", "tests/model-plan.py",
    "tests/usage-observation-bundle-schema.py", "tests/usage-status-large-authority.py",
    "tests/usage-status-large-parts.py", "tests/usage-status-parts-cli.py",
    "tests/usage-bounded-source-reads.py", "tests/usage-usage-publication.py",
    "tests/usage-usage-receipt-schema.py", "tests/model-selection.py",
    "tests/model-workflow.py", "tests/log-step-hook.sh",
    "tests/usage-duration-analysis.py", "tests/usage-lifecycle-projection-token-scalars.py",
    "tests/usage-cumulative-epochs.py", "tests/usage-resolution-measurement-finality.py",
    "tests/git-rails.sh", "tests/hook-install.sh", "tests/hook-shell-quality.sh",
    "tests/usage-inventory-schema.py", "tests/usage-resolution-epochs.py",
    "tests/usage-status-integration.py", "tests/usage-stream-revisions.py",
    "tests/usage-warning-delivery-boundary.py", "tests/usage-analysis-corpus-schema.py",
    "tests/usage-current-run-snapshot-schema.py", "tests/usage-lifecycle-projection-schema.py",
    "tests/usage-resolution-evidence.py", "tests/usage-source-selection.py",
    "tests/usage-status-input-schema.py",
})


# The one approved extension of the frozen inventory, by name: the state tool contract
# results, its acceptance result, focused mode and resource row. Each entry is inserted
# directly after its anchor; any other addition, rename or omission is rejected.
ADDED_NAMES = {
    "results": [
        "RECEIPTS: workflow-globals defines state_receipts: on one anchored line and keeps blocks without it valid",
        "RECEIPTS: the Protected Sections Contract protects state_receipts: lines",
        "RECEIPTS: the state tool vocabulary constants equal the anchored status lines",
        "test_state_tool_acceptance",
    ],
    "expressions": ["test_state_tool_acceptance"],
    "focused": ["--state-tool-only"],
    "resources": ["test_state_tool_acceptance"],
}
ADDED_RESOURCE_PATHS = frozenset({"scripts/state-tool.py", "tests/state-tool.py"})


def add_named_entries(amended: dict, added: dict) -> None:
    """Insert exactly the approved named entries into the amended inventory in place."""
    if not isinstance(added, dict) or set(added) != set(ADDED_NAMES):
        raise ValueError("Invalid amendment additions")
    for section, names in ADDED_NAMES.items():
        key = "flag" if section == "focused" else "name"
        items, target = added[section], amended[section]
        if (not isinstance(items, list)
                or any(not isinstance(item, dict) or set(item) != {"after", "value"}
                       or not isinstance(item["value"], dict) or set(item["value"]) != set(target[0])
                       for item in items)
                or [item["value"][key] for item in items] != names):
            raise ValueError("Unexpected added entries")
        for item in items:
            if any(entry[key] == item["value"][key] for entry in target):
                raise ValueError("Added entry already exists")
            anchors = [index for index, entry in enumerate(target)
                       if (entry if section == "results" else entry[key]) == item["after"]]
            if len(anchors) != 1:
                raise ValueError("Added entry anchor is missing or repeated")
            target.insert(anchors[0] + 1, copy.deepcopy(item["value"]))
    name = ADDED_NAMES["expressions"][0]
    result = next(entry for entry in amended["results"] if entry["name"] == name)
    expression = next(entry for entry in amended["expressions"] if entry["name"] == name)
    if result["expression"] != expression["expression"]:
        raise ValueError("Added acceptance expression differs")
    row = next(entry for entry in amended["resources"] if entry["name"] == name)
    paths = {item["path"] for item in row["source_references"] + row["dynamic_dependencies"]}
    paths |= {item["path"] for values in row["observations"].values() for item in values}
    paths |= {path for item in row["dynamic_dependencies"]
              for field in ("target_candidates", "callsite_candidates") for path in item.get(field, [])}
    if not paths or not paths <= ADDED_RESOURCE_PATHS:
        raise ValueError("Added resource path is not approved")


def apply_amendment(frozen: dict, amendment: dict) -> dict:
    """Apply exact approved test-resource changes to a copy of the frozen inventory."""
    if set(amendment) != {"schema", "paths", "removed_results", "resources", "added"}:
        raise ValueError("Invalid amendment fields")
    if amendment["schema"] != 1 or amendment["paths"] != sorted(APPROVED_PATHS):
        raise ValueError("Invalid amendment scope")
    amended = copy.deepcopy(frozen)
    removed_results = amendment["removed_results"]
    expected_names = ["pd-analyze references architecture.md",
                      "SAFETY: git-flow defines the Enforcement vocabulary on one anchored line"]
    if [item.get("name") for item in removed_results] != expected_names:
        raise ValueError("Unexpected removed results")
    for removed in removed_results:
        if amended["results"].count(removed) != 1:
            raise ValueError("Unexpected removed result")
        amended["results"].remove(removed)
    names = [row["name"] for row in amended["resources"]]
    touched = set()
    for patch in amendment["resources"]:
        if set(patch) != {"name", "changes"} or names.count(patch["name"]) != 1 or patch["name"] in touched:
            raise ValueError("Invalid amendment resource")
        touched.add(patch["name"])
        row = amended["resources"][names.index(patch["name"])]
        seen = set()
        for change in patch["changes"]:
            field, path = change["field"], change["path"]
            kind = change.get("kind")
            fields = {"field", "path", "before", "after"} | ({"kind"} if field == "observations" else set())
            key = (field, kind, path)
            if set(change) != fields or path not in APPROVED_PATHS or key in seen:
                raise ValueError("Invalid resource change")
            seen.add(key)
            if field == "observations" and kind in row["observations"]:
                items = row["observations"][kind]
            elif field in {"source_references", "dynamic_dependencies"} and kind is None:
                items = row[field]
            else:
                raise ValueError("Invalid resource field")
            before, after = change["before"], change["after"]
            if any(item.get("path") != path for item in before + after):
                raise ValueError("Resource path differs")
            if [item for item in items if item["path"] == path] != before:
                raise ValueError("Frozen resource differs")
            items[:] = sorted([item for item in items if item["path"] != path] + copy.deepcopy(after),
                              key=lambda item: (item["path"], item.get("line", 0)))
    add_named_entries(amended, amendment["added"])
    return amended


def load_frozen_inventory(path: Path) -> dict:
    if hashlib.sha256(path.read_bytes()).hexdigest() != FROZEN_INVENTORY_SHA256:
        raise ValueError("Frozen inventory digest differs")
    amendment_bytes = path.with_name("inventory-amendment.json").read_bytes()
    if hashlib.sha256(amendment_bytes).hexdigest() != AMENDMENT_SHA256:
        raise ValueError("Inventory amendment digest differs")
    return apply_amendment(ORACLE.load_inventory(path), json.loads(amendment_bytes))


class SecurityContracts(unittest.TestCase):
    def test_version_fixture_isolates_inherited_log_root(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-version-isolation.py")],
                                capture_output=True, text=True, timeout=8)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_security(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-security.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_allowlist(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-allowlist.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_allowlist_guard(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-allowlist-guard.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_shell_guard(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-allowlist-shell.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_integrated_registrations(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-integrated.py")],
                                capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


    def test_runtime_wrapper_shadow(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-wrapper-shadow.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sourceguard_allowlist(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tests/validator-runtime-sourceguard-allowlist.py")],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


# The one approved extension of the frozen inventory: the state tool contract results,
# its acceptance result, focused mode and resource row. Nothing else may be added.
NAMED_RESULTS = [
    "RECEIPTS: workflow-globals defines state_receipts: on one anchored line and keeps blocks without it valid",
    "RECEIPTS: the Protected Sections Contract protects state_receipts: lines",
    "RECEIPTS: the state tool vocabulary constants equal the anchored status lines",
    "test_state_tool_acceptance",
]
NAMED_ACCEPTANCE = "test_state_tool_acceptance"
NAMED_FLAG = "--state-tool-only"


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
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = ORACLE.inventory(ROOT / "scripts/validate-contracts.sh")

    def test_runtime_checks_registered_once_after_focused_dispatch(self) -> None:
        source = (ROOT / "scripts/validate-contracts.sh").read_text()
        end_of_focused = source.index('if [ "${1:-}" = --run-log-contract-only ]; then')
        for name in ("test_validator_runtime_characterization", "test_validator_runtime_oracle"):
            with self.subTest(name=name):
                call = 'check "' + name + '"'
                self.assertEqual(source.count(call), 1)
                self.assertGreater(source.index(call), end_of_focused)

    def test_result_extraction_distinguishes_nested_diagnostics(self) -> None:
        output = (b"[PASS] first\n[FAIL] outer: [PASS] first\n[FAIL] inner: details\n"
                  b"[PASS] last\n=== Contract Validation ===\n  Passed: 2\n  Failed: 1\n  Skipped: 0\n")
        self.assertEqual(ORACLE.extract_results(output, ["first", "outer", "last"]),
                         [("PASS", "first"), ("FAIL", "outer"), ("PASS", "last")])
        self.assertIsNone(ORACLE.extract_results(output, None))

    def test_time_output_fields_are_parsed_and_missing_fields_fail(self) -> None:
        output = (b"\tUser time (seconds): 10.00\n\tSystem time (seconds): 2.00\n"
                  b"\tElapsed (wall clock) time (h:mm:ss or m:ss): 1:40.00\n"
                  b"\tMaximum resident set size (kbytes): 1000\n\tExit status: 0\n")
        self.assertEqual(ORACLE.parse_time(output), {"user_seconds": 10.0, "system_seconds": 2.0,
                                                    "elapsed_seconds": 100.0, "max_rss_kb": 1000,
                                                    "exit_code": 0})
        self.assertIsNone(ORACLE.parse_time(output.replace(b"Exit status: 0", b"Exit missing")))

    def test_nonfinite_sample_values_are_rejected(self) -> None:
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value):
                record = manifest()
                record["samples"][0]["elapsed_seconds"] = value
                self.assertIs(ORACLE.valid_manifest(record, "b" * 64, "c" * 64), False)

    def test_evidence_checks_file_bytes_digests_result_inventory_and_median(self) -> None:
        with tempfile.TemporaryDirectory(prefix="measurement-evidence-") as temp:
            root = Path(temp)
            (root / "source.txt").write_bytes(b"source payload\n")
            payload_hash = hashlib.sha256((root / "source.txt").read_bytes()).hexdigest()
            record = manifest()
            record["payload_sha256"] = payload_hash
            record["configuration"] = {"locale": "C", "cache_policy": "warm", "jobs": 1}
            configuration_hash = hashlib.sha256(json.dumps(record["configuration"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            record["configuration_sha256"] = configuration_hash
            record["source_files"] = {"source.txt": payload_hash}
            record["result_inventory"] = ["example"]
            record["baseline_median_seconds"] = 101
            for index, item in enumerate(record["samples"]):
                item.update(payload_sha256=payload_hash, configuration_sha256=configuration_hash,
                            pass_count=1, skip_count=0, process_exit_code=0,
                            source_files_unchanged=True, dirty_after="")
                time_output = ("User time (seconds): 10.00\nSystem time (seconds): 2.00\n"
                               f"Elapsed (wall clock) time (h:mm:ss or m:ss): 1:{40 + 2 * index:02d}.00\n"
                               "Maximum resident set size (kbytes): 1000\nExit status: 0\n").encode()
                contents = {"stdout": b"[PASS] example\n=== Contract Validation ===\n  Passed: 1\n  Failed: 0\n  Skipped: 0\n",
                            "stderr": b"", "time_output": time_output}
                item["file_sha256"] = {}
                for kind, data in contents.items():
                    item[kind] = f"{index}-{kind}.txt"
                    (root / item[kind]).write_bytes(data)
                    item["file_sha256"][kind] = hashlib.sha256(data).hexdigest()
            self.assertIs(ORACLE.verify_evidence(record, root), True)
            trusted = {key: copy.deepcopy(record[key]) for key in
                       ("commit", "source_blob", "source_files", "configuration", "result_inventory")}
            self.assertIs(ORACLE.verify_provenance(record, root, trusted), True)
            for key in trusted:
                altered = copy.deepcopy(trusted)
                if isinstance(altered[key], dict):
                    altered[key]["unexpected"] = "different"
                elif isinstance(altered[key], list):
                    altered[key].append("unexpected")
                else:
                    altered[key] = "different"
                with self.subTest(trusted_field=key):
                    self.assertIs(ORACLE.verify_provenance(record, root, altered), False)
            for mutation in ("source", "output", "sample_config", "inventory", "median",
                             "process_exit", "source_changed", "dirty"):
                changed = copy.deepcopy(record)
                path = root / ("source.txt" if mutation == "source" else "0-stdout.txt")
                old = path.read_bytes()
                if mutation in ("source", "output"):
                    path.write_bytes(old + b"tampered")
                elif mutation == "sample_config":
                    changed["samples"][0]["configuration_sha256"] = "d" * 64
                elif mutation == "inventory":
                    changed["result_inventory"] = ["different"]
                elif mutation == "median":
                    changed["baseline_median_seconds"] = 100
                elif mutation == "process_exit":
                    changed["samples"][0]["process_exit_code"] = 1
                elif mutation == "source_changed":
                    changed["samples"][0]["source_files_unchanged"] = False
                else:
                    changed["samples"][0]["dirty_after"] = " M source.txt"
                with self.subTest(mutation=mutation):
                    self.assertIs(ORACLE.verify_evidence(changed, root), False)
                path.write_bytes(old)

    def test_frozen_source_detects_actual_name_expression_and_order_changes(self) -> None:
        frozen = load_frozen_inventory(ROOT / "tests/fixtures/validator-runtime/source-inventory.json.gz")
        source = (ROOT / "scripts/validate-contracts.sh").read_text()
        self.assertTrue(ORACLE.matches(frozen, self.inventory))
        first, second = frozen["expressions"][:2]
        changes = (
            source.replace('check "' + first["name"] + '"', 'check "altered name"', 1),
            source.replace(first["expression"], first["expression"] + " # changed", 1),
            source.replace('check "' + first["name"] + '"', 'check "TEMPORARY_NAME"', 1)
                  .replace('check "' + second["name"] + '"', 'check "' + first["name"] + '"', 1)
                  .replace('check "TEMPORARY_NAME"', 'check "' + second["name"] + '"', 1),
        )
        with tempfile.TemporaryDirectory(prefix="oracle-mutation-") as temp:
            scripts = Path(temp) / "scripts"
            scripts.mkdir()
            for entry in (ROOT / "scripts").iterdir():
                if entry.name != "validate-contracts.sh":
                    (scripts / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
            (Path(temp) / "tests").symlink_to(ROOT / "tests", target_is_directory=True)
            candidate = scripts / "validate-contracts.sh"
            candidate.write_text(source)
            self.assertTrue(ORACLE.matches(frozen, ORACLE.inventory(candidate)))
            for changed in changes:
                with self.subTest(change=changes.index(changed)):
                    candidate.write_text(changed)
                    self.assertFalse(ORACLE.matches_structure(frozen, ORACLE.inventory(candidate, include_resources=False)))

    def test_amendment_pins_unrelated_fields_order_and_resource_changes(self) -> None:
        path = ROOT / "tests/fixtures/validator-runtime/source-inventory.json.gz"
        raw = ORACLE.load_inventory(path)
        amendment = json.loads(path.with_name("inventory-amendment.json").read_bytes())
        amended = apply_amendment(raw, amendment)
        self.assertTrue(ORACLE.matches(amended, self.inventory))
        unrelated = copy.deepcopy(self.inventory)
        unrelated["resources"][0]["evidence"] += " unexpected"
        self.assertFalse(ORACLE.matches(amended, unrelated))
        unrelated = copy.deepcopy(self.inventory)
        unrelated["results"][0], unrelated["results"][1] = unrelated["results"][1], unrelated["results"][0]
        self.assertFalse(ORACLE.matches(amended, unrelated))
        unrelated = copy.deepcopy(self.inventory)
        unrelated["resources"][0]["source_references"][0]["sha256"] = "0" * 64
        self.assertFalse(ORACLE.matches(amended, unrelated))
        with_observation = next(i for i, row in enumerate(self.inventory["resources"])
                                if any(row["observations"].values()))
        unrelated = copy.deepcopy(self.inventory)
        observations = unrelated["resources"][with_observation]["observations"]
        kind = next(k for k, values in observations.items() if values)
        observations[kind][0]["line_sha256"] = "0" * 64
        self.assertFalse(ORACLE.matches(amended, unrelated))
        with_dynamic = next(i for i, row in enumerate(self.inventory["resources"])
                            if row["dynamic_dependencies"])
        unrelated = copy.deepcopy(self.inventory)
        unrelated["resources"][with_dynamic]["dynamic_dependencies"][0]["reason"] += " unexpected"
        self.assertFalse(ORACLE.matches(amended, unrelated))
        bad = copy.deepcopy(amendment)
        bad["resources"][0]["changes"][0]["path"] = "tests/unapproved.py"
        with self.assertRaises(ValueError):
            apply_amendment(raw, bad)
        bad = copy.deepcopy(amendment)
        bad["resources"][0]["changes"][0]["before"] = [{"path": bad["resources"][0]["changes"][0]["path"], "sha256": "0" * 64}]
        with self.assertRaises(ValueError):
            apply_amendment(raw, bad)

    def test_inventory_extension_accepts_only_the_named_additions(self) -> None:
        path = ROOT / "tests/fixtures/validator-runtime/source-inventory.json.gz"
        raw = ORACLE.load_inventory(path)
        amendment = json.loads(path.with_name("inventory-amendment.json").read_bytes())
        added = amendment.get("added", {})
        self.assertEqual([item["value"]["name"] for item in added.get("results", [])], NAMED_RESULTS)
        self.assertEqual([item["value"]["name"] for item in added.get("expressions", [])],
                         [NAMED_ACCEPTANCE])
        self.assertEqual([item["value"]["flag"] for item in added.get("focused", [])], [NAMED_FLAG])
        self.assertEqual([item["value"]["name"] for item in added.get("resources", [])],
                         [NAMED_ACCEPTANCE])
        self.assertTrue(ORACLE.matches(apply_amendment(raw, amendment), self.inventory))

        source = (ROOT / "scripts/validate-contracts.sh").read_text()
        def statement(name: str) -> str:
            start = source.index('check "' + name + '" \\\n')
            return source[start:source.index("\n", source.index("\n", start) + 1) + 1]
        contract, acceptance = statement(NAMED_RESULTS[2]), statement(NAMED_ACCEPTANCE)
        dispatch = re.search(r'^if \[ "\$\{1:-\}" = ' + NAMED_FLAG + r' \]; then\n.*?^fi\n',
                             source, re.M | re.S).group(0)
        candidates = {
            "unlisted contract check": source.replace(
                contract, contract + contract.replace(NAMED_RESULTS[2], "RECEIPTS: an unlisted check"), 1),
            "unlisted acceptance check": source.replace(
                acceptance, acceptance + acceptance.replace(
                    'check "' + NAMED_ACCEPTANCE, 'check "test_unlisted_acceptance', 1), 1),
            "unlisted focused mode": source.replace(
                dispatch, dispatch + dispatch.replace(NAMED_FLAG, "--unlisted-only"), 1),
            "named contract check missing": source.replace(contract, "", 1),
            "named focused mode missing": source.replace(dispatch, "", 1),
        }
        with tempfile.TemporaryDirectory(prefix="oracle-extension-") as temp:
            candidate = Path(temp) / "validate-contracts.sh"
            for label, text in candidates.items():
                with self.subTest(source=label):
                    self.assertNotEqual(text, source)
                    candidate.write_text(text)
                    try:
                        accepted = ORACLE.matches_structure(
                            apply_amendment(raw, amendment),
                            ORACLE.inventory(candidate, include_resources=False))
                    except ValueError:
                        accepted = False
                    self.assertFalse(accepted, label)

        def changed(section: str, change) -> dict:
            altered = copy.deepcopy(amendment)
            change(altered["added"][section])
            return altered
        def extra(items: list) -> None:
            item = copy.deepcopy(items[-1])
            key = "flag" if "flag" in item["value"] else "name"
            item["after"] = item["value"][key] if isinstance(item["after"], str) else copy.deepcopy(item["value"])
            item["value"][key] = "unlisted-addition"
            items.append(item)
        def rename(items: list) -> None:
            key = "flag" if "flag" in items[0]["value"] else "name"
            items[0]["value"][key] += " renamed"
        def foreign_path(items: list) -> None:
            items[0]["value"]["source_references"].append(
                {"path": "tests/unapproved.py", "sha256": "0" * 64, "provenance": "direct lexical reference"})
        def missing_anchor(items: list) -> None:
            items[0]["after"] = "no such entry" if isinstance(items[0]["after"], str) else {"name": "none", "expression": "none"}
        bad_amendments = {"unlisted result": changed("results", extra),
                          "unlisted focused flag": changed("focused", extra),
                          "unlisted acceptance expression": changed("expressions", extra),
                          "unlisted resource row": changed("resources", extra),
                          "renamed result": changed("results", rename),
                          "renamed focused flag": changed("focused", rename),
                          "named result missing": changed("results", lambda items: items.pop()),
                          "resource path outside the suite": changed("resources", foreign_path),
                          "missing anchor": changed("results", missing_anchor)}
        unknown_section = copy.deepcopy(amendment)
        unknown_section["added"]["unlisted"] = []
        bad_amendments["unknown section"] = unknown_section
        for label, altered in bad_amendments.items():
            with self.subTest(amendment=label), self.assertRaises(ValueError):
                apply_amendment(raw, altered)

    def test_unapproved_nonstandard_check_is_rejected(self) -> None:
        source = (ROOT / "scripts/validate-contracts.sh").read_text()
        with tempfile.TemporaryDirectory(prefix="oracle-syntax-") as temp:
            candidate = Path(temp) / "validate-contracts.sh"
            candidate.write_text(source + "\n  check unexpected\n")
            with self.assertRaisesRegex(ValueError, "Unapproved check syntax"):
                ORACLE.inventory(candidate, include_resources=False)

    def test_inventory_contains_all_source_contracts(self) -> None:
        inventory = self.inventory
        self.assertIsInstance(inventory, dict)
        self.assertEqual(len(inventory["expressions"]), 37)
        self.assertEqual(len(inventory["focused"]), 38)
        self.assertGreater(len(inventory["results"]), 37)
        self.assertEqual(len(inventory["resources"]), 37)
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
