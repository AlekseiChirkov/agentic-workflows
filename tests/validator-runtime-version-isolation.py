#!/usr/bin/env python3
"""The contract version fixture must not write to an inherited log root."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

TRUSTED_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('VERSION_FIXTURE_ROOT', TRUSTED_ROOT))
SOURCE = Path(os.environ.get('VERSION_FIXTURE_SOURCE', ROOT / 'scripts/validate-contracts.sh'))


class VersionFixtureIsolation(unittest.TestCase):
    def test_inherited_log_root_is_untouched(self):
        source = SOURCE.read_bytes().decode('utf-8')
        start = source.index('test_contract_version_run_start_stamps_current_and_reads_legacy() (')
        end = source.index('\ntest_contract_version_rule_history_warns_until_version_changes()', start)
        fragment = source[start:end]
        trusted = (TRUSTED_ROOT / 'scripts/validate-contracts.sh').read_bytes().decode('utf-8')
        trusted_start = trusted.index('test_contract_version_run_start_stamps_current_and_reads_legacy() (')
        trusted_end = trusted.index('\ntest_contract_version_rule_history_warns_until_version_changes()', trusted_start)
        if fragment != trusted[trusted_start:trusted_end]:
            raise ValueError('Version fixture source differs from the reviewed function')
        helper = (ROOT / 'scripts/log-step.sh').read_bytes()
        if helper != (TRUSTED_ROOT / 'scripts/log-step.sh').read_bytes():
            raise ValueError('Version fixture helper differs from the reviewed helper')
        with tempfile.TemporaryDirectory(prefix='version-isolation-') as temp:
            root = Path(temp)
            checkout = root / 'checkout'
            (checkout / 'scripts').mkdir(parents=True)
            (checkout / 'rules').mkdir()
            (checkout / 'scripts/log-step.sh').write_bytes(helper)
            (checkout / 'rules/run-log.md').write_bytes((ROOT / 'rules/run-log.md').read_bytes())
            foreign = root / 'foreign'
            foreign.mkdir()
            sentinel = foreign / 'sentinel'
            sentinel.write_bytes(b'unchanged\n')
            scratch = root / 'scratch'
            scratch.mkdir()
            script = root / 'fixture.sh'
            script.write_text(fragment)
            environment = os.environ.copy()
            environment.update(ORCHESTRAIL_LOG_ROOT=str(foreign), TMPDIR=str(scratch),
                               ORCHESTRAIL_HOME=str(root / 'unavailable-home'))
            result = subprocess.run(['bash', '-c', 'source "$1"; test_contract_version_run_start_stamps_current_and_reads_legacy',
                                     'version-fixture', str(script)], cwd=checkout, env=environment,
                                    capture_output=True, text=True, timeout=8)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual([(p.name, p.read_bytes()) for p in foreign.iterdir()], [('sentinel', b'unchanged\n')])


if __name__ == '__main__':
    unittest.main()
