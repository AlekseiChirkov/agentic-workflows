#!/usr/bin/env python3
"""The production warning fixture accepts only its audited prefix."""
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


class PrefixFingerprint(unittest.TestCase):
    def test_approved_prefix_runs_with_pinned_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = warning.invoke(warning.SOURCE, Path(temp), trust_candidate=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unapproved_prefix_changes_fail_closed(self) -> None:
        for statement in (': # changed prefix', "c''heck early pass"):
            with self.subTest(statement=statement), tempfile.TemporaryDirectory() as temp:
                source = warning.SOURCE.replace(warning.ANCHOR, '\n' + statement + '\n' + warning.ANCHOR, 1)
                result = warning.invoke(source, Path(temp), trust_candidate=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('unapproved version-warning prefix', result.stderr)


if __name__ == '__main__':
    unittest.main()
