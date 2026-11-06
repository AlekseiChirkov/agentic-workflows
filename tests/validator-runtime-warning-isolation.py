#!/usr/bin/env python3
"""Isolation and registration checks for the warning fixture."""

import importlib.util
import os
from pathlib import Path
import tempfile
import sys
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('warning_contract', ROOT / 'tests/validator-runtime-warning.py')
warning = importlib.util.module_from_spec(spec)
spec.loader.exec_module(warning)


class WarningIsolation(unittest.TestCase):
    def test_indented_early_check_is_rejected(self) -> None:
        source = warning.SOURCE.replace(warning.ANCHOR, '\n  check "early" pass\n' + warning.ANCHOR, 1)
        with tempfile.TemporaryDirectory(prefix='warning-indent-') as temp:
            result = warning.invoke(source, Path(temp))
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('ordinary check precedes version-warning call', result.stderr)

    def test_inherited_git_environment_cannot_redirect_fixture(self) -> None:
        with tempfile.TemporaryDirectory(prefix='warning-env-') as temp:
            root = Path(temp)
            foreign = root / 'foreign'
            foreign.mkdir()
            hostile = {'GIT_DIR': str(foreign / 'missing-git-dir'),
                       'GIT_WORK_TREE': str(foreign),
                       'GIT_INDEX_FILE': str(foreign / 'index'),
                       'GIT_COMMON_DIR': str(foreign / 'common')}
            (root / 'fixture').mkdir()
            with mock.patch.dict(os.environ, hostile):
                result = warning.invoke(warning.SOURCE, root / 'fixture')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(list(foreign.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
