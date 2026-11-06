#!/usr/bin/env python3
"""Reject unregistered checks hidden in shell command lists."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('oracle_contract', ROOT / 'tests/validator-runtime-oracle.py')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class ShellCheckGuard(unittest.TestCase):
    def test_command_lists_do_not_hide_checks(self) -> None:
        source = (ROOT / 'scripts/validate-contracts.sh').read_text()
        frozen = contract.load_frozen_inventory(ROOT / 'tests/fixtures/validator-runtime/source-inventory.json.gz')
        marker = '\ncheck "test_validator_runtime_characterization"'
        self.assertEqual(source.count(marker), 1)
        for statement in ('true && check "unexpected" pass', ':; check extra pass'):
            with self.subTest(statement=statement), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / 'validate-contracts.sh'
                path.write_text(source.replace(marker, '\n' + statement + marker, 1))
                try:
                    actual = contract.ORACLE.inventory(path, include_resources=False)
                    accepted = contract.ORACLE.matches_structure(frozen, actual)
                except ValueError:
                    accepted = False
                self.assertFalse(accepted)


if __name__ == '__main__':
    unittest.main()
