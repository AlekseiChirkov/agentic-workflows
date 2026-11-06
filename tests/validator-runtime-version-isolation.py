#!/usr/bin/env python3
"""The contract version fixture must not write to an inherited log root."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(os.environ.get('VERSION_FIXTURE_ROOT', Path(__file__).resolve().parents[1]))
SOURCE = Path(os.environ.get('VERSION_FIXTURE_SOURCE', ROOT / 'scripts/validate-contracts.sh'))


class VersionFixtureIsolation(unittest.TestCase):
    def test_inherited_log_root_is_untouched(self):
        source = SOURCE.read_text()
        start = source.index('test_contract_version_run_start_stamps_current_and_reads_legacy() (')
        end = source.index('\ntest_contract_version_rule_history_warns_until_version_changes()', start)
        with tempfile.TemporaryDirectory(prefix='version-isolation-') as temp:
            root = Path(temp)
            foreign = root / 'foreign'
            foreign.mkdir()
            sentinel = foreign / 'sentinel'
            sentinel.write_bytes(b'unchanged\n')
            scratch = root / 'scratch'
            scratch.mkdir()
            script = root / 'fixture.sh'
            script.write_text(source[start:end])
            environment = os.environ.copy()
            environment.update(ORCHESTRAIL_LOG_ROOT=str(foreign), TMPDIR=str(scratch),
                               ORCHESTRAIL_HOME=str(root / 'unavailable-home'))
            result = subprocess.run(['bash', '-c', 'source "$1"; test_contract_version_run_start_stamps_current_and_reads_legacy',
                                     'version-fixture', str(script)], cwd=ROOT, env=environment,
                                    capture_output=True, text=True, timeout=8)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual([(p.name, p.read_bytes()) for p in foreign.iterdir()], [('sentinel', b'unchanged\n')])


if __name__ == '__main__':
    unittest.main()
