#!/usr/bin/env python3
"""Reject runtime wrapper drift and unsupported check syntax."""
import importlib.util
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('oracle_contract', ROOT / 'tests/validator-runtime-oracle.py')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class AllowlistGuard(unittest.TestCase):
    def test_wrapper_and_unsupported_checks_fail_closed(self) -> None:
        frozen = contract.load_frozen_inventory(ROOT / 'tests/fixtures/validator-runtime/source-inventory.json.gz')
        source = (ROOT / 'scripts/validate-contracts.sh').read_text()
        mutations = {}
        for name in ('test_validator_runtime_characterization', 'test_validator_runtime_oracle'):
            pattern = r'^' + name + r'\(\) \{\n.*?^\}'
            changed, count = re.subn(pattern, name + '() { :; }', source, count=1, flags=re.M | re.S)
            self.assertEqual(count, 1)
            mutations[name] = changed
        marker = '\ncheck "test_validator_runtime_characterization"'
        self.assertEqual(source.count(marker), 1)
        mutations['indented'] = source.replace(marker, '\n  check "unexpected" pass' + marker, 1)
        mutations['unquoted'] = source.replace(marker, '\ncheck unexpected pass' + marker, 1)
        with tempfile.TemporaryDirectory(prefix='validator-allowlist-guard-') as temp:
            path = Path(temp) / 'validate-contracts.sh'
            for name, candidate in mutations.items():
                with self.subTest(mutation=name):
                    path.write_text(candidate)
                    try:
                        actual = contract.ORACLE.inventory(path, include_resources=False)
                        accepted = contract.ORACLE.matches_structure(frozen, actual)
                    except ValueError:
                        accepted = False
                    self.assertFalse(accepted, name)


if __name__ == '__main__':
    unittest.main()
