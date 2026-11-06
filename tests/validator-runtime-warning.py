#!/usr/bin/env python3
"""Focused checks for the version-warning history fixture."""

import hashlib
import os
import re
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'scripts/validate-contracts.sh').read_text()
START = 'test_contract_version_rule_history_warns_until_version_changes() ('
END = '\n)\n\ncheck "test_contract_version_root_has_exact_release_value"'
ANCHOR = '\nwarn_stale_contract_version\n'
WARNING = "echo '[WARN] Rules changed after VERSION; update the contract version before release.' >&2"


def invoke(source: str, root: Path, trust_candidate: bool = True) -> subprocess.CompletedProcess:
    scripts = root / 'scripts'
    scripts.mkdir(exist_ok=True)
    (scripts / 'validate-contracts.sh').write_text(source)
    (root / 'rules').mkdir(exist_ok=True)
    (root / 'rules/run-log.md').write_text('Fixture rule.\n')
    (root / 'VERSION').write_text('0.9.0\n')
    body = source[source.index(START):source.index(END) + 2]
    anchors = list(re.finditer(r'^warn_stale_contract_version$', source, re.M))
    if trust_candidate and len(anchors) == 1:
        digest = hashlib.sha256(source[:anchors[0].end()].encode()).hexdigest()
        body = re.sub(r"expected_prefix_sha256='[0-9a-f]{64}'",
                      f"expected_prefix_sha256='{digest}'", body, count=1)
    env = os.environ.copy()
    env.update(HOME=str(root), XDG_CONFIG_HOME=str(root / 'xdg'), LC_ALL='C')
    return subprocess.run(['bash', '-c', body + '\n' + START.split('()')[0]],
                          cwd=root, env=env, capture_output=True, text=True, timeout=10)


class WarningFixture(unittest.TestCase):
    def setUp(self) -> None:
        # Never start a complete recursive validator while testing the old implementation.
        self.assertIn('write_contract_warning_prefix', SOURCE)
        self.assertEqual(SOURCE.count(ANCHOR), 1)
        self.assertEqual(SOURCE.count(WARNING), 1)
        self.temp = tempfile.TemporaryDirectory(prefix='warning-fixture-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_missing_duplicate_and_early_check_are_rejected(self) -> None:
        cases = (SOURCE.replace(ANCHOR, '\n', 1),
                 SOURCE.replace(ANCHOR, ANCHOR + ANCHOR, 1),
                 SOURCE.replace(ANCHOR, '\ncheck "early" pass\n' + ANCHOR, 1))
        for source in cases:
            with self.subTest(case=cases.index(source)):
                result = invoke(source, self.root)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_post_cut_sentinel_never_runs(self) -> None:
        sentinel = self.root / 'executed'
        source = SOURCE.replace(ANCHOR, ANCHOR + f'touch "{sentinel}"\n', 1)
        result = invoke(source, self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(sentinel.exists())

    def test_warning_mutations_fail_the_original_assertions(self) -> None:
        changes = (SOURCE.replace(WARNING, ':', 1),
                   SOURCE.replace(WARNING, WARNING + '\n  ' + WARNING, 1).replace(
                       'if [ -n "$newer_rules" ]; then', 'if :; then', 1),
                   SOURCE.replace('git diff --quiet "$version_commit" -- VERSION 2>/dev/null || return 0', ':', 1))
        for source in changes:
            with self.subTest(case=changes.index(source)):
                result = invoke(source, self.root)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
