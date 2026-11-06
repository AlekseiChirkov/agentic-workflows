#!/usr/bin/env python3
"""The frozen inventory accepts only explicitly placed runtime checks."""
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
ORACLE = contract.ORACLE


class RuntimeAllowlist(unittest.TestCase):
    def test_runtime_additions_have_exact_expressions_order_and_positions(self) -> None:
        frozen = contract.load_frozen_inventory(ROOT / 'tests/fixtures/validator-runtime/source-inventory.json.gz')
        source = (ROOT / 'scripts/validate-contracts.sh').read_text()
        names = ('test_validator_runtime_characterization', 'test_validator_runtime_oracle')
        blocks = []
        for name in names:
            start = source.index('check "' + name + '"')
            end = source.index('\n', source.index('\n', start) + 1) + 1
            blocks.append(source[start:end])
        first, second = blocks
        first_frozen = 'check "' + frozen['results'][0]['name'] + '"'
        self.assertEqual(source.count(first_frozen), 1)
        mutations = {
            'changed expression': source.replace(first, first.replace('echo pass', 'echo altered', 1), 1),
            'duplicate': source.replace(first, first + first, 1),
            'missing': source.replace(first, '', 1),
            'reordered': source.replace(first, 'RUNTIME_TEMP_MARKER\n', 1).replace(second, first, 1)
                               .replace('RUNTIME_TEMP_MARKER\n', second, 1),
            'moved': source.replace(first, '', 1).replace(first_frozen, first + first_frozen, 1),
        }
        with tempfile.TemporaryDirectory(prefix='validator-allowlist-') as temp:
            path = Path(temp) / 'validate-contracts.sh'
            path.write_text(source)
            self.assertTrue(ORACLE.matches_structure(frozen, ORACLE.inventory(path, include_resources=False)))
            for name, candidate in mutations.items():
                with self.subTest(mutation=name):
                    path.write_text(candidate)
                    try:
                        actual = ORACLE.inventory(path, include_resources=False)
                        accepted = ORACLE.matches_structure(frozen, actual)
                    except ValueError:
                        accepted = False
                    self.assertFalse(accepted, name)


if __name__ == '__main__':
    unittest.main()
