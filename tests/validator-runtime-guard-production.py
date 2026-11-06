#!/usr/bin/env python3
"""Bounded project-inventory exception contracts."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('source_guard', ROOT / 'tests/fixtures/validator-runtime/source_guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class SourceInventoryContracts(unittest.TestCase):
    def test_exact_context_and_count_and_stale_exceptions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            (root / 'tests').mkdir()
            file = root / 'scripts/validate-contracts.sh'
            statement = "  echo 'Usage: scripts/validate-contracts.sh'"
            source = 'fixture() {\n' + statement + '\n}\n'
            file.write_text(source)
            entry = {'path': 'scripts/validate-contracts.sh', 'statement': statement,
                     'container': 'fixture', 'context_sha256': hashlib.sha256(source.rstrip('\n').encode()).hexdigest(),
                     'detail': 'unclassified shell reference', 'count': 1,
                     'reason': 'non-executable usage text'}
            self.assertEqual(guard.inspect_project(root, [entry]), [])
            self.assertTrue(guard.inspect_project(root, []))
            self.assertTrue(guard.inspect_project(root, [entry, entry]))
            file.write_text(source.replace(statement, statement + '\n' + statement))
            self.assertTrue(guard.inspect_project(root, [entry]))
            file.write_text(source.replace('fixture()', 'different()'))
            self.assertTrue(guard.inspect_project(root, [entry]))
            file.write_text('fixture() { :; }\n')
            self.assertTrue(guard.inspect_project(root, [entry]))

    def test_new_full_call_is_not_authorized_by_existing_exception(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            (root / 'tests').mkdir()
            (root / 'scripts/validate-contracts.sh').write_text('# validator\n')
            (root / 'tests/new.sh').write_text('bash scripts/validate-contracts.sh\n')
            self.assertTrue(guard.inspect_project(root, []))


if __name__ == '__main__':
    unittest.main()
