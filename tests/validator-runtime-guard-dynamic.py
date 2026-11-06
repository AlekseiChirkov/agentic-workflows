#!/usr/bin/env python3
"""Contracts for bounded dynamic executable source inspection."""
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


class DynamicExecutableContracts(unittest.TestCase):
    def test_unclassified_dynamic_executable_requires_review(self):
        for statement in ('bash "$prefix/$suffix"', 'sh "$target"', 'exec "$runner"'):
            with self.subTest(statement=statement):
                self.assertTrue(guard.inspect_sources({'tests/example.sh': statement + '\n'}))

    def test_dynamic_command_positions_require_review(self):
        for statement in ('"$runner" argument', 'out="$("$prefix/$suffix")"',
                          'true; "$runner" argument', 'if "$runner" argument; then :; fi'):
            with self.subTest(statement=statement):
                self.assertTrue(guard.inspect_sources({'tests/example.sh': statement + '\n'}))

    def test_generated_source_dependency_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            (root / 'tests').mkdir()
            (root / 'scripts/validate-contracts.sh').write_text('# validator\n')
            dependency = root / 'scripts/generator.sh'
            dependency.write_text('safe generator\n')
            statement = '  bash "$generated"'
            source = 'fixture() {\n' + statement + '\n}\n'
            (root / 'tests/example.sh').write_text(source)
            entry = {'path': 'tests/example.sh', 'statement': statement, 'container': 'fixture',
                     'context_sha256': hashlib.sha256(source.rstrip('\n').encode()).hexdigest(),
                     'detail': 'dynamic executable requires review', 'count': 1,
                     'reason': 'reviewed generated command',
                     'dependencies': {'scripts/generator.sh': hashlib.sha256(dependency.read_bytes()).hexdigest()}}
            self.assertEqual(guard.inspect_project(root, [entry]), [])
            dependency.write_text('changed generator\n')
            self.assertTrue(guard.inspect_project(root, [entry]))

    def test_exact_classification_rejects_drift_duplicate_and_stale_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            (root / 'tests').mkdir()
            (root / 'scripts/validate-contracts.sh').write_text('# validator\n')
            path = root / 'tests/example.sh'
            statement = '  bash "$prefix/$suffix"'
            source = 'fixture() {\n' + statement + '\n}\n'
            path.write_text(source)
            entry = {'path': 'tests/example.sh', 'statement': statement,
                     'container': 'fixture', 'context_sha256': hashlib.sha256(source.rstrip('\n').encode()).hexdigest(),
                     'detail': 'dynamic executable requires review', 'count': 1,
                     'reason': 'reviewed non-validator fixture command'}
            self.assertEqual(guard.inspect_project(root, [entry]), [])
            self.assertTrue(guard.inspect_project(root, []))
            self.assertTrue(guard.inspect_project(root, [entry, entry]))
            path.write_text(source.replace(statement, statement + '\n' + statement))
            self.assertTrue(guard.inspect_project(root, [entry]))
            path.write_text(source.replace('fixture()', 'different()'))
            self.assertTrue(guard.inspect_project(root, [entry]))
            path.write_text('fixture() { :; }\n')
            self.assertTrue(guard.inspect_project(root, [entry]))


if __name__ == '__main__':
    unittest.main()
