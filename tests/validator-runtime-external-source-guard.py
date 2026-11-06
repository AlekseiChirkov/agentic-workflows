#!/usr/bin/env python3
"""Reject unreviewed nested validator calls in extracted fixture sources."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExternalSourceGuardTests(unittest.TestCase):
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
