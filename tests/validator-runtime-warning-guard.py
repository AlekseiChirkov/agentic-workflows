#!/usr/bin/env python3
"""Additional prefix safety and bytecode isolation checks."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('warning_contract', ROOT / 'tests/validator-runtime-warning.py')
warning = importlib.util.module_from_spec(spec)
spec.loader.exec_module(warning)


class GuardSafety(unittest.TestCase):
    def test_early_compound_checks_are_rejected(self) -> None:
        for statement in (':; check "early" pass', 'if :; then check "early" pass; fi'):
            with self.subTest(statement=statement), tempfile.TemporaryDirectory() as temp:
                source = warning.SOURCE.replace(warning.ANCHOR, '\n' + statement + '\n' + warning.ANCHOR, 1)
                result = warning.invoke(source, Path(temp))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('ordinary check precedes version-warning call', result.stderr)

    def test_isolation_suite_creates_no_bytecode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'tests').mkdir()
            (root / 'scripts').mkdir()
            for name in ('validator-runtime-warning.py', 'validator-runtime-warning-isolation.py'):
                shutil.copy(ROOT / 'tests' / name, root / 'tests' / name)
            shutil.copy(ROOT / 'scripts/validate-contracts.sh', root / 'scripts/validate-contracts.sh')
            env = os.environ.copy()
            env.pop('PYTHONDONTWRITEBYTECODE', None)
            result = subprocess.run([sys.executable, str(root / 'tests/validator-runtime-warning-isolation.py')],
                                    capture_output=True, text=True, env=env, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((root / 'tests/__pycache__').exists())


if __name__ == '__main__':
    unittest.main()
