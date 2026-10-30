#!/usr/bin/env python3
"""Analysis errors identify the operation and never disclose local paths."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cli_fixture', ROOT / 'tests/usage-analyze-cli-evidence.py')
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)


class AnalyzeErrorTests(unittest.TestCase):
    def test_failed_analysis_reports_analysis_and_hides_private_paths(self):
        fixture = fixture_module.AnalyzeCliEvidenceTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        process = subprocess.run([sys.executable, str(ROOT / 'scripts/usage-telemetry.py'), *fixture.args()],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(process.stdout, b'')
        self.assertIn(b'analysis failed', process.stderr)
        self.assertNotIn(b'normalization failed', process.stderr)
        self.assertNotIn(str(fixture.base.directory).encode(), process.stderr)
        self.assertFalse(fixture.output.exists())


if __name__ == '__main__':
    unittest.main()
