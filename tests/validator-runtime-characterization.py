#!/usr/bin/env python3
"""Characterize the existing validator using disposable repositories."""

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "scripts/validate-contracts.sh").read_text()
START = "# ── Public identity smoke checks"
END = "# ── End public identity smoke checks"
TOKEN = "agentic" + "-" + "workflows"


def section(start: str, end: str) -> str:
    lines = SOURCE.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.startswith(start)]
    ends = [index for index, line in enumerate(lines) if line.startswith(end)]
    assert len(starts) == len(ends) == 1 and starts[0] < ends[0]
    return "".join(lines[starts[0]:ends[0]])


SCANNER = section(START, END).split('\ncheck "', 1)[0]
RENDERER = SOURCE[SOURCE.index("check() {"):SOURCE.index("\n# ── Group 1:")]


def command(args: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)


class ScannerCharacterization(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="validator-characterization-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env.update(HOME=str(self.root), XDG_CONFIG_HOME=str(self.root / "config"),
                        XDG_STATE_HOME=str(self.root / "state"), LC_ALL="C")
        for args in (["git", "init", "-q"],
                     ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                      "commit", "--allow-empty", "-qm", "fixture"]):
            result = command(args, self.root, self.env)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.commit = command(["git", "rev-parse", "HEAD"], self.root, self.env).stdout.decode().strip()

    def scan(self, payload: bytes, rows: str, name: str = "input.txt", locale: str = "C") -> subprocess.CompletedProcess:
        (self.root / name).write_bytes(payload)
        ledger = ("### Exact Identity Match Ledger\n"
                  "| Path | Line | Expected token counts |\n|---|---:|---|\n"
                  + rows + "\n### Other\n  base_commit: " + self.commit + "\n")
        (self.root / "ledger.md").write_text(ledger)
        env = self.env | {"LC_ALL": locale}
        args = ["bash", "-c", SCANNER + "\ntest_public_identity_matches_exact_ledger_and_preserves_knowledge"]
        result = command(args, self.root, env)
        if locale == "C":
            locales = command(["locale", "-a"], self.root, self.env).stdout.decode().splitlines()
            utf8 = next((item for item in locales if item.lower().replace("-", "").replace(".", "") in ("cutf8", "en_usutf8")), None)
            if utf8 is not None:
                other = command(args, self.root, self.env | {"LC_ALL": utf8})
                def normalized(output: bytes) -> bytes:
                    return re.sub(rb"(?m)^(---|\+\+\+) /[^\n]*identity-scan\.[^\n]*$", rb"\1 <fixture>", output)
                self.assertEqual((other.returncode, normalized(other.stdout), other.stderr),
                                 (result.returncode, normalized(result.stdout), result.stderr))
        return result

    def test_counts_lines_case_and_final_line(self) -> None:
        lower = TOKEN
        upper = TOKEN.upper()
        row = f"| `input.txt` | 1 | `{lower}` × 2; `{upper}` × 1 |"
        result = self.scan(f"{lower} {lower} {upper}".encode(), row)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        for altered in (row.replace("× 2", "× 1"), row.replace("| 1 |", "| 2 |"),
                        f"| `input.txt` | 1 | `{lower}` × 3 |"):
            result = self.scan(f"{lower} {lower} {upper}".encode(), altered)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b"Identity scan differs", result.stdout)

    def test_bytes_paths_and_empty_file(self) -> None:
        name = "space: back\\slash.txt"
        row = f"| `{name}` | 2 | `{TOKEN}` × 1 |"
        result = self.scan(b"\xff\x00nothing\n" + TOKEN.encode() + b"\x00", row, name)
        self.assertEqual((result.returncode, result.stdout), (0, b""))
        (self.root / "empty").write_bytes(b"")
        result = self.scan(b"\xff\x00nothing\n" + TOKEN.encode() + b"\x00", row, name)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_missing_ledger_path_fails(self) -> None:
        row = f"| `missing.txt` | 1 | `{TOKEN}` × 1 |"
        result = self.scan(b"no matches", row)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"Scanned path is missing or unreadable: missing.txt", result.stdout)

    def test_nul_split_and_symlink_target(self) -> None:
        link = self.root / "link"
        link.symlink_to(TOKEN)
        row = (f"| `input.txt` | 1 | `{TOKEN}` × 1 |\n"
               f"| `link` | 1 | `{TOKEN}` × 1 |")
        payload = TOKEN[:5].encode() + b"\0" + TOKEN[5:].encode()
        result = self.scan(payload, row)
        self.assertEqual((result.returncode, result.stdout), (0, b""))

    def test_grep_failure_is_not_a_clean_scan(self) -> None:
        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        fake_grep = fake_bin / "grep"
        fake_grep.write_text('#!/bin/bash\nif [ "$1" = -aEio ]; then exit 2; fi\nexec /usr/bin/grep "$@"\n')
        fake_grep.chmod(0o755)
        self.env["PATH"] = str(fake_bin) + os.pathsep + self.env["PATH"]
        row = f"| `input.txt` | 1 | `{TOKEN}` × 1 |"
        result = self.scan(TOKEN.encode(), row)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"Identity scan failed on", result.stdout)

    def test_ledger_mask_preserves_line_numbers(self) -> None:
        ledger = ("### Exact Identity Match Ledger\n"
                  "| Path | Line | Expected token counts |\n|---|---:|---|\n"
                  f"| `ledger.md` | 6 | `{TOKEN}` × 1 |\n"
                  "### Other\n" + TOKEN + "\n  base_commit: " + self.commit + "\n")
        (self.root / "ledger.md").write_text(ledger)
        result = command(["bash", "-c", SCANNER + "\ntest_public_identity_matches_exact_ledger_and_preserves_knowledge"], self.root, self.env)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_sort_failure_does_not_report_success(self) -> None:
        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        fake_sort = fake_bin / "sort"
        fake_sort.write_text("#!/bin/bash\nexit 2\n")
        fake_sort.chmod(0o755)
        self.env["PATH"] = str(fake_bin) + os.pathsep + self.env["PATH"]
        row = f"| `input.txt` | 1 | `{TOKEN}` × 1 |"
        result = self.scan(TOKEN.encode(), row)
        self.assertEqual(result.returncode, 1)

    def test_available_utf8_locale(self) -> None:
        locales = command(["locale", "-a"], self.root, self.env).stdout.decode().splitlines()
        locale = next((item for item in locales if item.lower().replace("-", "").replace(".", "") in ("cutf8", "en_usutf8")), None)
        if locale is None:
            self.skipTest("No C or en_US UTF-8 locale is available")
        row = f"| `input.txt` | 1 | `{TOKEN}` × 1 |"
        result = self.scan(TOKEN.encode(), row, locale=locale)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))


class RenderingCharacterization(unittest.TestCase):
    def test_run_log_extraction_markers_and_standalone_syntax(self) -> None:
        groups = (("Run-log contract smoke checks", "End run-log contract smoke checks"),
                  ("Run-log producer smoke checks", "End run-log producer smoke checks"),
                  ("Retrospective executable corpus contract", "End retrospective executable corpus contract"))
        definitions = []
        for opening, closing in groups:
            block = section("# ── " + opening, "# ── " + closing)
            block, removed = re.subn(r"^check [^\n]*\\\n[^\n]*\n", "", block, flags=re.M)
            self.assertGreater(removed, 0, opening)
            self.assertNotRegex(block, r"(?m)^check ")
            definitions.append(block)
        body = "\n".join(definitions)
        names = re.findall(r"^(test_(?:run_log|retro)_[a-z_]+)\(\)", body, re.M)
        self.assertGreaterEqual(len(names), 20)
        self.assertEqual(len(names), len(set(names)))
        result = subprocess.run(["bash", "-n"], input=body.encode(), capture_output=True, check=False)
        self.assertEqual((result.returncode, result.stderr), (0, b""))

    def test_generic_wrapper_suppresses_diagnostics(self) -> None:
        call = ('check "test_usage_warning_acceptance" \\\n'
                '  "$(usage_warning_acceptance >/dev/null 2>&1 && echo pass || echo '
                "'usage status and warning fixtures must pass')\"")
        self.assertIn(call, SOURCE)
        script = ("PASS=0 FAIL=0 SKIP=0\n" + RENDERER +
                  "\nusage_warning_acceptance() { echo out; echo err >&2; return 1; }\n" + call)
        result = subprocess.run(["bash", "-c", script], capture_output=True, check=False)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, b"[FAIL] test_usage_warning_acceptance: usage status and warning fixtures must pass\n", b""))

    def test_wrapper_excerpt_conventions(self) -> None:
        cases = (("test_usage_diagnostic_registry_acceptance", 20),
                 ("test_usage_contract_export_acceptance", 35),
                 ("test_model_workflow_acceptance", 60))
        for name, length in cases:
            with self.subTest(wrapper=name):
                start = SOURCE.index(name + "() {")
                end = SOURCE.index("\n}", start) + 2
                wrapper = SOURCE[start:end]
                fake = ('python3() { for ((i=1;i<=70;i++)); do '
                        'if ((i % 2)); then echo "line-$i"; else echo "line-$i" >&2; fi; '
                        'done; return 1; }\n')
                result = subprocess.run(["bash", "-c", fake + wrapper + "\n" + name],
                                        capture_output=True, check=False)
                expected = "".join(f"line-{i}\n" for i in range(71 - length, 71)).encode()
                self.assertEqual((result.returncode, result.stdout, result.stderr), (1, expected, b""))

    def test_conditional_command_substitution_isolated_under_errexit(self) -> None:
        start = SOURCE.index("test_usage_contract_export_acceptance() {")
        end = SOURCE.index("\n}", start) + 2
        wrapper = SOURCE[start:end]
        script = ("set -e\nPASS=0 FAIL=0 SKIP=0\n" + RENDERER + "\n" + wrapper +
                  "\npython3() { echo diagnostic >&2; return 1; }\n"
                  "check fixture \"$(test_usage_contract_export_acceptance && echo pass || echo fallback)\"\n"
                  "printf 'continued:%s,%s,%s\\n' \"$PASS\" \"$FAIL\" \"$SKIP\"\n")
        result = subprocess.run(["bash", "-c", script], capture_output=True, check=False)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, b"[FAIL] fixture: diagnostic\nfallback\ncontinued:0,1,0\n", b""))

    def test_result_channels_and_counters(self) -> None:
        script = ("PASS=0 FAIL=0 SKIP=0\n" + RENDERER +
                  "\ncheck alpha pass\ncheck beta 'skip: reason'\ncheck gamma $'line one\\nline two'\n"
                  "printf 'counts:%s,%s,%s\\n' \"$PASS\" \"$FAIL\" \"$SKIP\"\n")
        result = subprocess.run(["bash", "-c", script], capture_output=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"[PASS] alpha\n[SKIP] beta: reason\n[FAIL] gamma: line one\nline two\ncounts:1,1,1\n")
        self.assertEqual(result.stderr, b"")

    def test_focused_exec_forwards_arguments_and_exit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="focused-characterization-") as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            (root / "tests").mkdir()
            validator = root / "scripts/validate-contracts.sh"
            validator.write_text(SOURCE)
            target = root / "tests/usage-bounded-source-reads.py"
            target.write_text("import sys\nprint(repr(sys.argv[1:]))\nsys.exit(23)\n")
            env = os.environ | {"HOME": temp, "XDG_CONFIG_HOME": temp + "/config",
                                "XDG_STATE_HOME": temp + "/state",
                                "ORCHESTRAIL_TEST_JOBS": "invalid",
                                "ORCHESTRAIL_TEST_TIMINGS": "1"}
            result = subprocess.run(["bash", str(validator), "--usage-bounded-source-reads-only",
                                     "with space", "--example"], env=env, capture_output=True,
                                    check=False)
            self.assertEqual(result.returncode, 23)
            self.assertEqual(result.stdout, b"['with space', '--example']\n")
            self.assertEqual(result.stderr, b"")

    def test_focused_chained_and_bash_dispatch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="focused-characterization-") as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            (root / "tests").mkdir()
            validator = root / "scripts/validate-contracts.sh"
            validator.write_text(SOURCE)
            (root / "tests/usage-source-normalization.py").write_text(
                "import sys\nprint('first', repr(sys.argv[1:]))\n")
            (root / "tests/usage-normalize-cli.py").write_text(
                "import sys\nprint('last', repr(sys.argv[1:]))\nsys.exit(19)\n")
            (root / "tests/hook-shell-quality.sh").write_text(
                "printf 'shell:<%s>:<%s>\\n' \"$1\" \"$2\"\nexit 17\n")
            env = os.environ | {"HOME": temp, "XDG_CONFIG_HOME": temp + "/config",
                                "XDG_STATE_HOME": temp + "/state"}
            for flag, code, expected in (
                ("--usage-source-normalization-only", 19,
                 b"first ['with space', '--example']\nlast ['with space', '--example']\n"),
                ("--hook-shell-quality-only", 17, b"shell:<with space>:<--example>\n"),
            ):
                with self.subTest(flag=flag):
                    result = subprocess.run(["bash", str(validator), flag, "with space", "--example"],
                                            env=env, capture_output=True, check=False)
                    self.assertEqual((result.returncode, result.stdout, result.stderr), (code, expected, b""))


if __name__ == "__main__":
    unittest.main()
