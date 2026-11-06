#!/usr/bin/env python3
"""Reject later definitions of the protected runtime wrappers."""
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


class WrapperShadow(unittest.TestCase):
    def test_indented_and_function_definitions_are_rejected(self) -> None:
        source = (ROOT / 'scripts/validate-contracts.sh').read_text()
        marker = '\ncheck "test_validator_runtime_oracle"'
        self.assertEqual(source.count(marker), 1)
        frozen = contract.load_frozen_inventory(ROOT / 'tests/fixtures/validator-runtime/source-inventory.json.gz')
        for name in ('test_validator_runtime_characterization', 'test_validator_runtime_oracle',
                     'test_validator_runtime_warning'):
            for definition in ('  ' + name + '() { :; }', 'function ' + name + ' { :; }'):
                with self.subTest(definition=definition), tempfile.TemporaryDirectory() as temp:
                    path = Path(temp) / 'validate-contracts.sh'
                    path.write_text(source.replace(marker, '\n' + definition + marker, 1))
                    try:
                        actual = contract.ORACLE.inventory(path, include_resources=False)
                        accepted = contract.ORACLE.matches_structure(frozen, actual)
                    except ValueError:
                        accepted = False
                    self.assertFalse(accepted)


if __name__ == '__main__':
    unittest.main()
