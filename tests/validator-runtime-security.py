#!/usr/bin/env python3
"""Safety properties of the validator characterization and frozen oracle."""
import gzip
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeSecurity(unittest.TestCase):
    def test_git_environment_cannot_redirect_fixture(self) -> None:
        scanner = load('scanner_contract', ROOT / 'tests/validator-runtime-characterization.py')
        with tempfile.TemporaryDirectory(prefix='validator-hostile-git-') as temp:
            foreign = Path(temp) / 'foreign'
            foreign.mkdir()
            template = Path(temp) / 'template'
            template.mkdir()
            hostile = {'GIT_DIR': str(foreign / 'missing'), 'GIT_WORK_TREE': str(foreign),
                       'GIT_INDEX_FILE': str(foreign / 'index'), 'GIT_TEMPLATE_DIR': str(template)}
            fixture = scanner.ScannerCharacterization('test_counts_lines_case_and_final_line')
            try:
                with mock.patch.dict(os.environ, hostile):
                    fixture.setUp()
                self.assertTrue((fixture.root / '.git').is_dir())
                self.assertEqual(list(foreign.iterdir()), [])
                self.assertEqual(fixture.env.get('GIT_CONFIG_NOSYSTEM'), '1')
                self.assertEqual(fixture.env.get('GIT_CONFIG_GLOBAL'), os.devnull)
                self.assertNotIn('GIT_TEMPLATE_DIR', fixture.env)
            finally:
                fixture.doCleanups()

    def test_import_does_not_write_bytecode(self) -> None:
        with tempfile.TemporaryDirectory(prefix='validator-oracle-import-') as temp:
            root = Path(temp)
            fixture = root / 'tests/fixtures/validator-runtime'
            fixture.mkdir(parents=True)
            shutil.copy(ROOT / 'tests/validator-runtime-oracle.py', root / 'tests')
            shutil.copy(ROOT / 'tests/fixtures/validator-runtime/oracle.py', fixture)
            env = os.environ.copy()
            env.pop('PYTHONDONTWRITEBYTECODE', None)
            result = subprocess.run([sys.executable, '-c', 'import runpy,sys; runpy.run_path(sys.argv[1])',
                                     str(root / 'tests/validator-runtime-oracle.py')], env=env,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((fixture / '__pycache__').exists())

    def test_inventory_digest_rejects_valid_modified_data(self) -> None:
        oracle = load('oracle_contract', ROOT / 'tests/validator-runtime-oracle.py')
        source = ROOT / 'tests/fixtures/validator-runtime/source-inventory.json.gz'
        self.assertTrue(oracle.load_frozen_inventory(source))
        with tempfile.TemporaryDirectory(prefix='validator-oracle-digest-') as temp:
            modified = Path(temp) / 'inventory.json.gz'
            with gzip.open(source, 'rt') as stream:
                data = json.load(stream)
            data['results'][0]['name'] += ' changed'
            with gzip.open(modified, 'wt') as stream:
                json.dump(data, stream)
            with self.assertRaises(ValueError):
                oracle.load_frozen_inventory(modified)


if __name__ == '__main__':
    unittest.main()
