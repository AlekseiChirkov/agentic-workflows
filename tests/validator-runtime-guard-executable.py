#!/usr/bin/env python3
"""Reject unclassified Python executable forms referencing the validator."""

import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "source_guard", ROOT / "tests/fixtures/validator-runtime/source_guard.py"
)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class UnknownExecutableForms(unittest.TestCase):
    def assert_rejected(self, statement):
        path = "tests/example.py"
        violations = guard.inspect_sources({path: "import os\n" + statement + "\n"})
        self.assertTrue(violations, statement)
        self.assertTrue(any(path in str(item) for item in violations))

    def test_execl_validator_reference_requires_review(self):
        self.assert_rejected("os.execl('/bin/bash', 'bash', 'scripts/validate-contracts.sh')")

    def test_execv_validator_reference_requires_review(self):
        self.assert_rejected("os.execv('/bin/bash', ['bash', 'scripts/validate-contracts.sh'])")

    def test_execv_validator_path_alias_requires_review(self):
        self.assert_rejected("p = 'scripts/validate-contracts.sh'\nos.execv('/bin/bash', ['bash', p])")

    def test_unknown_callable_validator_path_alias_requires_review(self):
        self.assert_rejected("p = 'scripts/validate-contracts.sh'\ncustom_runner(p)")

    def test_unknown_callable_validator_reference_requires_review(self):
        self.assert_rejected("custom_runner('scripts/validate-contracts.sh')")


if __name__ == "__main__":
    unittest.main()
