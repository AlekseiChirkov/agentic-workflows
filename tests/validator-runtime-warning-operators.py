#!/usr/bin/env python3
"""Guard shell operators that can precede a top-level check."""
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


class OperatorGuard(unittest.TestCase):
    def test_compound_command_operators_are_rejected(self) -> None:
        statements = ('true && check "early" pass', 'false || check "early" pass',
                      ': | check "early" pass', '{ check "early" pass; }')
        for statement in statements:
            with self.subTest(statement=statement), tempfile.TemporaryDirectory() as temp:
                source = warning.SOURCE.replace(warning.ANCHOR, '\n' + statement + '\n' + warning.ANCHOR, 1)
                result = warning.invoke(source, Path(temp))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('ordinary check precedes version-warning call', result.stderr)


if __name__ == '__main__':
    unittest.main()
