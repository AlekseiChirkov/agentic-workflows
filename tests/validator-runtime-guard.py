#!/usr/bin/env python3
"""Small contract tests for bounded nested-validator source inspection."""

import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "tests/fixtures/validator-runtime/source_guard.py"
FIXTURES = ROOT / "tests/fixtures/validator-runtime"


def inspect(sources, exceptions=()):
    """Return the guard's violations; the missing implementation is observable RED."""
    if not GUARD.is_file():
        return None
    spec = importlib.util.spec_from_file_location("source_guard", GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.inspect_sources(sources, exceptions)


class NestedValidatorGuard(unittest.TestCase):
    def violations(self, sources):
        result = inspect(sources)
        self.assertIsInstance(result, list, "source guard must report a list of violations")
        return result

    def test_rejects_full_direct_copied_and_alias_calls(self):
        cases = (
            'bash scripts/validate-contracts.sh\n',
            'bash "$fixture/scripts/validate-contracts.sh"\n',
            'validator="$fixture/scripts/validate-contracts.sh"\nbash "$validator"\n',
        )
        for source in cases:
            with self.subTest(source=source):
                self.assertTrue(self.violations({"tests/example.sh": source}))

    def test_accepts_supported_focused_flag_on_actual_argv(self):
        safe = 'bash scripts/validate-contracts.sh --hygiene-only\n'
        self.assertEqual(self.violations({"tests/example.sh": safe}), [])
        for unsafe in (
            'bash scripts/validate-contracts.sh\nprintf "%s\\n" --hygiene-only\n',
            'bash scripts/validate-contracts.sh --invented-only\n',
        ):
            with self.subTest(source=unsafe):
                self.assertTrue(self.violations({"tests/example.sh": unsafe}))

    def test_inspects_multiline_python_argv_and_comments_as_data(self):
        focused = "import subprocess\nsubprocess.run([\n 'bash', 'scripts/validate-contracts.sh',\n '--run-log-contract-only'])\n"
        self.assertEqual(self.violations({"tests/example.py": focused}), [])
        self.assertTrue(self.violations({"tests/example.py": focused.replace("'--run-log-contract-only'", "'--invalid-only'")}))
        data = '# scripts/validate-contracts.sh is fixture data\nsource = "scripts/validate-contracts.sh"\n'
        self.assertEqual(self.violations({"tests/data.py": data}), [])

    def test_rejects_three_untrimmed_history_calls(self):
        before = (FIXTURES / "warning-history-before.txt").read_text()
        violations = self.violations({"scripts/validate-contracts.sh": before})
        self.assertEqual(len(violations), 3)
        self.assertTrue(all("scripts/validate-contracts.sh" in str(item) for item in violations))

    def test_stub_exception_is_exact_and_stale_entries_fail(self):
        statement = "printf '#!/bin/bash\\nexit 0\\n' > \"$fixture/scripts/validate-contracts.sh\""
        source = "fixture_stub() {\n  " + statement + "\n}\n"
        path = "tests/install-fixture.sh"
        exception = {"path": path, "statement": statement, "count": 1,
                     "context_sha256": hashlib.sha256(source.encode()).hexdigest(),
                     "reason": "private preflight stub"}
        self.assertEqual(inspect({path: source}, [exception]), [])
        self.assertTrue(inspect({path: source}, []))
        self.assertTrue(inspect({path: source}, [exception, exception]))
        self.assertTrue(inspect({path: source.replace(statement, statement + "\n  " + statement)}, [exception]))
        self.assertTrue(inspect({path: source.replace("exit 0", "exit 1")}, [exception]))
        self.assertTrue(inspect({path: "fixture_stub() { :; }\n"}, [exception]))

    def test_guarded_history_is_bound_to_context_and_exact_count(self):
        after = (FIXTURES / "warning-history-after.txt").read_text()
        self.assertEqual(self.violations({"scripts/validate-contracts.sh": after}), [])
        call = 'output="$(bash scripts/validate-contracts.sh 2>&1)"'
        self.assertEqual(after.count(call), 3)
        for mutated in (
            after.replace(call, call + '\n  ' + call, 1),
            after.replace('write_contract_warning_prefix "$root/scripts/validate-contracts.sh"', 'printf unrelated-trim "$root/scripts/validate-contracts.sh"', 1),
            after.replace('test_contract_version_rule_history_warns_until_version_changes()', 'different_context()', 1),
        ):
            with self.subTest(case=mutated[:90]):
                self.assertTrue(self.violations({"scripts/validate-contracts.sh": mutated}))


if __name__ == "__main__":
    unittest.main()
