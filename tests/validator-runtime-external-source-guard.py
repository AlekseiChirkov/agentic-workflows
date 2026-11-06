#!/usr/bin/env python3
"""Reject unreviewed nested validator calls in extracted fixture sources."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExternalSourceGuardTests(unittest.TestCase):
    def test_version_fixture_does_not_execute_unreviewed_root_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            marker = root / 'executed'
            (root / 'scripts/log-step.sh').write_text(f'touch "{marker}"\n')
            env = dict(os.environ, VERSION_FIXTURE_ROOT=str(root),
                       VERSION_FIXTURE_SOURCE=str(ROOT / 'scripts/validate-contracts.sh'))
            subprocess.run([sys.executable, str(ROOT / 'tests/validator-runtime-version-isolation.py')],
                           env=env, capture_output=True, timeout=10)
            self.assertFalse(marker.exists(), 'unreviewed root helper was executed')

    def test_version_fixture_accepts_identical_root_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            (root / 'rules').mkdir()
            shutil.copyfile(ROOT / 'scripts/log-step.sh', root / 'scripts/log-step.sh')
            shutil.copyfile(ROOT / 'rules/run-log.md', root / 'rules/run-log.md')
            env = dict(os.environ, VERSION_FIXTURE_ROOT=str(root),
                       VERSION_FIXTURE_SOURCE=str(ROOT / 'scripts/validate-contracts.sh'))
            result = subprocess.run([sys.executable, str(ROOT / 'tests/validator-runtime-version-isolation.py')],
                                    env=env, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_equivalent_external_source_preserves_differential_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'candidate.sh'
            source.write_bytes((ROOT / 'scripts/validate-contracts.sh').read_bytes())
            for fixture, variable, selection in (
                ('validator-runtime-identity.py', 'IDENTITY_SOURCE',
                 'IdentityScanTests.test_success_matches_original_loop'),
                ('validator-runtime-version-isolation.py', 'VERSION_FIXTURE_SOURCE',
                 'VersionFixtureIsolation.test_inherited_log_root_is_untouched'),
            ):
                with self.subTest(fixture=fixture):
                    env = dict(os.environ, **{variable: str(source)})
                    result = subprocess.run([sys.executable, str(ROOT / 'tests' / fixture), selection],
                                            env=env, capture_output=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_version_fixture_does_not_execute_unreviewed_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / 'executed'
            source = root / 'candidate.sh'
            source.write_text('test_contract_version_run_start_stamps_current_and_reads_legacy() (\n'
                              f'  touch "{marker}"\n'
                              ')\n'
                              'test_contract_version_rule_history_warns_until_version_changes() (\n)\n')
            env = dict(os.environ, VERSION_FIXTURE_SOURCE=str(source))
            subprocess.run([sys.executable, str(ROOT / 'tests/validator-runtime-version-isolation.py')],
                           env=env, capture_output=True, timeout=10)
            self.assertFalse(marker.exists(), 'unreviewed override was executed')

    def test_identity_fixture_does_not_execute_unreviewed_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / 'executed'
            source = root / 'candidate.sh'
            original = (ROOT / 'scripts/validate-contracts.sh').read_text()
            anchor = '    line_number=0\n'
            if anchor not in original:
                anchor = '    # Bash read drops embedded NUL bytes; normalize once to retain that behavior.\n'
            source.write_text(original.replace(anchor, anchor + f'    touch "{marker}"\n', 1))
            env = dict(os.environ, IDENTITY_SOURCE=str(source))
            subprocess.run([sys.executable, str(ROOT / 'tests/validator-runtime-identity.py'),
                            'IdentityScanTests.test_success_matches_original_loop'],
                           env=env, capture_output=True, timeout=10)
            self.assertFalse(marker.exists(), 'unreviewed override was executed')


if __name__ == '__main__':
    unittest.main()
