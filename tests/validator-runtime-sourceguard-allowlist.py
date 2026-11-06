#!/usr/bin/env python3
"""The source guard registration must remain exact and in order."""
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


class SourceGuardAllowlist(unittest.TestCase):
    def test_registration_is_required_and_immutable(self) -> None:
        source = (ROOT / 'scripts/validate-contracts.sh').read_text()
        frozen = contract.load_frozen_inventory(ROOT / 'tests/fixtures/validator-runtime/source-inventory.json.gz')
        name = 'test_nested_validator_source_guard'
        start = source.index('check "' + name + '"')
        end = source.index('\n', source.index('\n', start) + 1) + 1
        check = source[start:end]
        self.assertEqual(source.count(check), 1)
        wrapper = re.search(r'^' + name + r'\(\) \{\n.*?^\}', source, re.M | re.S)
        self.assertIsNotNone(wrapper)
        self.assertEqual(wrapper.group().count('tests/validator-runtime-guard-dynamic.py'), 1)
        self.assertEqual(wrapper.group().count('tests/validator-runtime-external-source-guard.py'), 1)
        warning = 'check "test_validator_runtime_warning"'
        cases = (
            ('current', source, True),
            ('missing', source.replace(check, '', 1), False),
            ('duplicate', source.replace(check, check + check, 1), False),
            ('expression', source.replace(check, check.replace('echo pass', 'echo altered', 1), 1), False),
            ('position', source.replace(check, '', 1).replace(warning, warning + '\n' + check, 1), False),
            ('wrapper', re.sub(r'^' + name + r'\(\) \{\n.*?^\}', name + '() { :; }',
                               source, count=1, flags=re.M | re.S), False),
        )
        with tempfile.TemporaryDirectory(prefix='sourceguard-allowlist-') as temp:
            path = Path(temp) / 'validate-contracts.sh'
            for label, candidate, expected in cases:
                with self.subTest(case=label):
                    path.write_text(candidate)
                    try:
                        actual = contract.ORACLE.inventory(path, include_resources=False)
                        accepted = contract.ORACLE.matches_structure(frozen, actual)
                    except ValueError:
                        accepted = False
                    self.assertEqual(accepted, expected)


if __name__ == '__main__':
    unittest.main()
