#!/usr/bin/env python3
"""Reject drift in the integrated identity and warning registrations."""
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('oracle_contract', ROOT / 'tests/validator-runtime-oracle.py')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class IntegratedContracts(unittest.TestCase):
    def test_source_guard_wrapper_emits_no_success_text(self) -> None:
        source = (ROOT / 'scripts/validate-contracts.sh').read_text()
        match = re.search(r'^test_nested_validator_source_guard\(\) \{\n.*?^\}',
                          source, flags=re.M | re.S)
        self.assertIsNotNone(match)
        script = 'REPO_ROOT=$1\n' + match.group() + '\ntest_nested_validator_source_guard\n'
        with tempfile.TemporaryDirectory(prefix='validator-wrapper-') as temp:
            wrapper_path = Path(temp) / 'wrapper.sh'
            wrapper_path.write_text(script)
            result = subprocess.run(['bash', str(wrapper_path), str(ROOT)], cwd=ROOT,
                                    capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')

    def test_registration_and_wrapper_mutations_are_rejected(self) -> None:
        source = (ROOT / 'scripts/validate-contracts.sh').read_text()
        frozen = contract.load_frozen_inventory(ROOT / 'tests/fixtures/validator-runtime/source-inventory.json.gz')
        start = source.index('check "test_validator_runtime_identity"')
        end = source.index('\n# ── End public identity smoke checks', start)
        identity = source[start:end]
        warning = 'check "test_validator_runtime_warning" \\\n  "$(test_validator_runtime_warning && echo pass || echo \'warning fixture contracts must pass\')"\n'
        self.assertEqual(source.count(warning), 1)
        candidates = (
            source[:start] + identity.replace('echo pass', 'echo altered', 1) + source[end:],
            source.replace(identity, '', 1),
            source.replace(warning, '', 1),
            source.replace(warning, warning + warning, 1),
            re.sub(r'^test_validator_runtime_warning\(\) \{\n.*?^\}',
                   'test_validator_runtime_warning() { :; }', source, count=1, flags=re.M | re.S),
        )
        with tempfile.TemporaryDirectory(prefix='validator-integrated-') as temp:
            path = Path(temp) / 'validate-contracts.sh'
            path.write_text(source)
            self.assertTrue(contract.ORACLE.matches_structure(frozen, contract.ORACLE.inventory(path, include_resources=False)))
            for index, candidate in enumerate(candidates):
                with self.subTest(mutation=index):
                    path.write_text(candidate)
                    try:
                        actual = contract.ORACLE.inventory(path, include_resources=False)
                        accepted = contract.ORACLE.matches_structure(frozen, actual)
                    except ValueError:
                        accepted = False
                    self.assertFalse(accepted)


if __name__ == '__main__':
    unittest.main()
