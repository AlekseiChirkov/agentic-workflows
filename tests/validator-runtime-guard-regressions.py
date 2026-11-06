#!/usr/bin/env python3
"""Regression probes for unclassified nested-validator invocations."""
import importlib.util
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("source_guard", ROOT / "tests/fixtures/validator-runtime/source_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class UnsafeInvocationRegressions(unittest.TestCase):
    def test_split_shell_executable_is_not_silent(self):
        source = "bash scripts/val''idate-contracts.sh\n"
        self.assertTrue(guard.inspect_sources({"tests/example.sh": source}))

    def test_validator_alias_executed_in_assignment_is_not_silent(self):
        source = 'result="$("$validator")"\n'
        self.assertTrue(guard.inspect_sources({"tests/example.sh": source}))

    def test_split_shell_alias_is_not_silent(self):
        source = 'runner="$REPO_ROOT/scripts/validate-contracts."sh\nbash "$runner"\n'
        self.assertTrue(guard.inspect_sources({"tests/example.sh": source}))

    def test_shell_alias_split_inside_path_is_not_silent(self):
        source = 'runner="scripts/validate-"contracts.sh\nbash "$runner"\n'
        self.assertTrue(guard.inspect_sources({"tests/example.sh": source}))

    def test_python_indirect_subprocess_callable_is_not_silent(self):
        source = "import subprocess\ngetattr(subprocess, 'run')(['bash', 'scripts/validate-contracts.sh'])\n"
        self.assertTrue(guard.inspect_sources({"tests/example.py": source}))

    def test_python_indirect_concatenated_path_is_not_silent(self):
        source = "import subprocess\ngetattr(subprocess, 'run')(['bash', 'scripts/validate-' + 'contracts.sh'])\n"
        self.assertTrue(guard.inspect_sources({"tests/example.py": source}))

    def test_cli_scans_project_with_pinned_classifications(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'tests/fixtures/validator-runtime/source_guard.py'),
                                 '--root', str(ROOT)], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('nested validator source guard: pass', result.stdout)

    def test_python_subprocess_callable_assignment_is_not_silent(self):
        source = "import subprocess\nlaunch = subprocess.run\nlaunch(['bash', 'scripts/validate-contracts.sh'])\n"
        self.assertTrue(guard.inspect_sources({"tests/example.py": source}))

    def test_shell_command_substitution_text_is_not_a_literal_argument(self):
        source = 'bash scripts/validate-contracts.sh $(printf %s --hygiene-only >&2)\n'
        self.assertTrue(guard.inspect_sources({"tests/example.sh": source}))

    def test_python_import_alias_is_not_silent(self):
        source = "from subprocess import run as execute\nexecute(['bash', 'scripts/validate-contracts.sh'])\n"
        self.assertTrue(guard.inspect_sources({"tests/example.py": source}))

    def test_python_command_alias_is_not_silent(self):
        source = "import subprocess\ncmd = ['bash', 'scripts/validate-contracts.sh']\nsubprocess.run(cmd)\n"
        self.assertTrue(guard.inspect_sources({"tests/example.py": source}))

    def test_shell_c_tail_is_not_inner_validator_argument(self):
        source = "bash -c 'bash scripts/validate-contracts.sh' --hygiene-only\n"
        self.assertTrue(guard.inspect_sources({"tests/example.sh": source}))

    def test_python_shell_c_tail_is_not_inner_validator_argument(self):
        source = "import subprocess\nsubprocess.run(['bash', '-c', 'bash scripts/validate-contracts.sh', '--hygiene-only'])\n"
        self.assertTrue(guard.inspect_sources({"tests/example.py": source}))

    def test_redirect_target_is_not_a_focused_argument(self):
        source = 'bash scripts/validate-contracts.sh > --hygiene-only\n'
        self.assertTrue(guard.inspect_sources({"tests/example.sh": source}))

    def test_only_real_arguments_authorize_focused_dispatch(self):
        source = 'bash scripts/validate-contracts.sh --hygiene-only > output\n'
        self.assertEqual(guard.inspect_sources({"tests/example.sh": source}), [])

    def test_inventory_reads_regular_project_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            (root / "tests/nested").mkdir(parents=True)
            (root / "scripts/validate-contracts.sh").write_text("# validator\n")
            (root / "tests/nested/example.py").write_text("pass\n")
            (root / "tests/example.sh").write_text("true\n")
            (root / "tests/data.txt").write_text("ignored\n")
            self.assertEqual(set(guard.inventory_sources(root)), {
                "scripts/validate-contracts.sh", "tests/example.sh", "tests/nested/example.py"})

    def test_warning_exception_rejects_duplicate_container(self):
        source = (ROOT / "tests/fixtures/validator-runtime/warning-history-after.txt").read_text()
        self.assertTrue(guard.inspect_sources({"scripts/validate-contracts.sh": source + source}))

    def test_warning_exception_is_not_portable_to_other_path(self):
        source = (ROOT / "tests/fixtures/validator-runtime/warning-history-after.txt").read_text()
        self.assertTrue(guard.inspect_sources({"tests/copied-warning.sh": source}))


if __name__ == "__main__":
    unittest.main()
