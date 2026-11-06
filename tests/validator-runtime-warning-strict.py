#!/usr/bin/env python3
"""Fail closed on ambiguous early checks and nested warning anchors."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('warning_contract', root / 'tests/validator-runtime-warning.py')
warning = importlib.util.module_from_spec(spec)
spec.loader.exec_module(warning)


class StrictGuard(unittest.TestCase):
    def test_indirect_early_checks_fail_closed(self) -> None:
        statements = ('X=1 check "early" pass', 'command check "early" pass',
                      "'check' \"early\" pass", '"check" "early" pass',
                      'env\tcheck\t"early"\tpass')
        for statement in statements:
            with self.subTest(statement=statement), tempfile.TemporaryDirectory() as temp:
                source = warning.SOURCE.replace(warning.ANCHOR, '\n' + statement + '\n' + warning.ANCHOR, 1)
                result = warning.invoke(source, Path(temp))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('ordinary check precedes version-warning call', result.stderr)

    def test_nested_anchor_is_rejected_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = warning.SOURCE.replace(warning.ANCHOR,
                                            '\nif false; then' + warning.ANCHOR + 'fi\n', 1)
            result = warning.invoke(source, Path(temp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('version-warning call is not at top level', result.stderr)


if __name__ == '__main__':
    unittest.main()
