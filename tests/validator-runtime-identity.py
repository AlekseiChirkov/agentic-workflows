#!/usr/bin/env python3
"""Small differential and fault checks for the public identity scan loop."""

import os
import locale
import re
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('IDENTITY_SOURCE', ROOT / 'scripts/validate-contracts.sh'))
REFERENCE_FUNCTION = (ROOT / 'tests/fixtures/validator-runtime/identity-original.sh').read_text()
REFERENCE = REFERENCE_FUNCTION[REFERENCE_FUNCTION.index('    line_number=0\n'):
                               REFERENCE_FUNCTION.index('  done < "$scratch/scan-files"')]


def complete_function(source):
    start = source.index('test_public_identity_matches_exact_ledger_and_preserves_knowledge() (')
    end = source.index('\n)\n\ncheck ', start) + 3
    result = source[start:end]
    trusted = (ROOT / 'scripts/validate-contracts.sh').read_bytes().decode('utf-8')
    trusted_start = trusted.index('test_public_identity_matches_exact_ledger_and_preserves_knowledge() (')
    trusted_end = trusted.index('\n)\n\ncheck ', trusted_start) + 3
    if result != trusted[trusted_start:trusted_end]:
        raise ValueError('Identity fixture source differs from the reviewed function')
    return result



def available_locales():
    result = ['C']
    listed = subprocess.run(['locale', '-a'], capture_output=True, text=True, timeout=5)
    utf8 = next((name for name in listed.stdout.splitlines()
                 if 'utf8' in name.lower().replace('-', '')), None)
    if utf8:
        result.append(utf8)
    else:
        print('UTF-8 locale unavailable; UTF-8 comparison skipped', file=sys.stderr)
    return result


def scan_loop():
    source = SOURCE.read_bytes().decode('utf-8')
    def extract(text):
        start = text.index('test_public_identity_matches_exact_ledger_and_preserves_knowledge()')
        anchors = ('    line_number=0\n', '    # Bash read drops embedded NUL bytes; normalize once to retain that behavior.\n')
        start = min(text.index(anchor, start) for anchor in anchors if anchor in text[start:])
        end = text.index('  done < "$scratch/scan-files"', start)
        return text[start:end]
    result = extract(source)
    if result != extract((ROOT / 'scripts/validate-contracts.sh').read_bytes().decode('utf-8')):
        raise ValueError('Identity fixture source differs from the reviewed loop')
    return result


class IdentityScanTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.file = self.root / 'space: back\\slash'
        name = b'agentic' + b'-workflows'
        upper = b'AGENTIC' + b'_workflows'
        self.file.write_bytes(upper + b' ' + name + b' ' + name + b'\nagentic\x00_workflows\r\n\xff' + name)

    def run_loop(self, loop, *, input_path=None, shim=None, locale='C', blocked_output=None):
        script = r'''scratch="$1"; input="$2"; file="$3"; identity_pattern='agentic''[_-]''workflows'
declare -A token_counts=()
: > "$scratch/actual"
scan() {
''' + loop + r'''
}
scan
status=$?
LC_ALL=C sort "$scratch/actual"
exit "$status"
'''
        env = dict(os.environ, LC_ALL=locale)
        if blocked_output:
            blocked = self.root / blocked_output
            if blocked.exists():
                blocked.unlink()
            blocked.mkdir()
        if shim:
            directory = self.root / ('shim-' + shim[0])
            directory.mkdir(exist_ok=True)
            executable = directory / shim[0]
            executable.write_text('#!/bin/sh\n' + shim[1] + '\n')
            executable.chmod(0o755)
            env['PATH'] = str(directory) + os.pathsep + env['PATH']
        if blocked_output == 'actual':
            script = script.replace(': > "$scratch/actual"', ':')
        return subprocess.run(
            ['bash', '-c', script, 'identity-test', str(self.root),
             str(input_path or self.file), self.file.name],
            env=env, capture_output=True, timeout=5,
        )

    def test_success_matches_original_loop(self):
        for locale in available_locales():
            with self.subTest(locale=locale):
                original = self.run_loop(REFERENCE, locale=locale)
                candidate = self.run_loop(scan_loop(), locale=locale)
                self.assertEqual((candidate.returncode, candidate.stdout, candidate.stderr),
                                 (original.returncode, original.stdout, original.stderr))

    def test_full_ledger_discovery_and_symlink(self):
        fixture = self.root / 'repository'
        fixture.mkdir()
        template = self.root / 'empty-template'
        template.mkdir()
        home = self.root / 'home'
        home.mkdir()
        env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
        env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
                   GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
                   GIT_CONFIG_SYSTEM='/dev/null', GIT_TEMPLATE_DIR=str(template),
                   GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='core.hooksPath',
                   GIT_CONFIG_VALUE_0='/dev/null', GIT_CONFIG_KEY_1='commit.gpgSign',
                   GIT_CONFIG_VALUE_1='false',
                   GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                   GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
        def git(*args):
            return subprocess.run(['git', *args], cwd=fixture, env=env, check=True,
                                  capture_output=True, text=True, timeout=5).stdout.strip()
        git('init', '-q')
        (fixture / '.ai').mkdir()
        (fixture / '.ai' / 'knowledge').write_text('knowledge\n')
        git('add', '.ai/knowledge')
        git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')
        commit = git('rev-parse', 'HEAD')
        token = 'agentic' + '-workflows'
        upper = 'AGENTIC' + '_workflows'
        name = 'space: back\\slash'
        (fixture / name).write_text(upper + ' ' + token + ' ' + token + '\n')
        (fixture / 'link').symlink_to(token)
        ledger = fixture / '.ai' / 'ledger'
        heading = '### Exact Identity ' + 'Match Ledger'
        ledger.write_text(f'  base_commit: {commit}\n{heading}\n'
                          '| Path | Line | Expected token counts |\n|---|---:|---|\n'
                          f'| `{name}` | 1 | `{upper}` × 1; `{token}` × 2 |\n'
                          f'| `link` | 1 | `{token}` × 1 |\n')
        locales = available_locales()
        def full_scan(function, selected):
            process = subprocess.run(['bash', '-c', function + '\n'
                                      'test_public_identity_matches_exact_ledger_and_preserves_knowledge'],
                                     cwd=fixture, env=dict(env, LC_ALL=selected),
                                     capture_output=True, timeout=8)
            # Diff headers contain nondeterministic scratch paths and timestamps.
            stdout = re.sub(rb'(?m)^(---|\+\+\+) [^\n]*$', rb'\1 <scratch>', process.stdout)
            return process.returncode, stdout, process.stderr
        candidate = complete_function(SOURCE.read_bytes().decode('utf-8'))
        for selected in locales:
            with self.subTest(locale=selected, scenario='valid ledger'):
                original = full_scan(REFERENCE_FUNCTION, selected)
                self.assertEqual(original[0], 0, original)
                self.assertEqual(full_scan(candidate, selected), original)
            with self.subTest(locale=selected, scenario='missing path'):
                (fixture / name).unlink()
                original = full_scan(REFERENCE_FUNCTION, selected)
                self.assertNotEqual(original[0], 0, original)
                self.assertEqual(full_scan(candidate, selected), original)
                (fixture / name).write_text(upper + ' ' + token + ' ' + token + '\n')
            with self.subTest(locale=selected, scenario='unexpected occurrence'):
                extra = fixture / 'unexpected'
                extra.write_text(token + '\n')
                original = full_scan(REFERENCE_FUNCTION, selected)
                self.assertNotEqual(original[0], 0, original)
                self.assertEqual(full_scan(candidate, selected), original)
                extra.unlink()

    def test_registered_check_ignores_external_source_override(self):
        source = (ROOT / 'scripts/validate-contracts.sh').read_text()
        start = source.index('check "test_validator_runtime_identity" "$(')
        end = source.index('\n)"', start) + len('\n)"')
        script = 'check() { :; }\n' + source[start:end] + '\n'
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        fake = bin_dir / 'python3'
        fake.write_text('#!/bin/sh\nprintf %s "${IDENTITY_SOURCE-unset}" > "$IDENTITY_SENTINEL"\n')
        fake.chmod(0o755)
        sentinel = self.root / 'seen-source'
        env = dict(os.environ, IDENTITY_SOURCE='/hostile/source', IDENTITY_SENTINEL=str(sentinel),
                   PATH=str(bin_dir) + os.pathsep + os.environ['PATH'])
        process = subprocess.run(['bash', '-c', script], env=env, capture_output=True, timeout=5)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(sentinel.read_text(), 'unset')

    def test_git_fixture_ignores_hostile_environment(self):
        sentinel = self.root / 'external'
        sentinel.mkdir()
        index = sentinel / 'index'
        index.write_bytes(b'external index sentinel')
        marker = sentinel / 'hook-ran'
        hook = sentinel / 'pre-commit'
        hook.write_text('#!/bin/sh\nprintf changed > "' + str(marker) + '"\n')
        hook.chmod(0o755)
        hostile = {'GIT_DIR': str(sentinel), 'GIT_WORK_TREE': str(sentinel),
                   'GIT_INDEX_FILE': str(index), 'GIT_CONFIG_COUNT': '1',
                   'GIT_CONFIG_KEY_0': 'core.hooksPath', 'GIT_CONFIG_VALUE_0': str(sentinel),
                   'GIT_TEMPLATE_DIR': str(sentinel)}
        with patch.dict(os.environ, hostile):
            self.test_full_ledger_discovery_and_symlink()
        self.assertEqual(index.read_bytes(), b'external index sentinel')
        self.assertFalse(marker.exists())
        self.assertEqual(sorted(path.name for path in sentinel.iterdir()), ['index', 'pre-commit'])

    def test_input_read_error_fails(self):
        # Reading a directory fails even as root; Bash's old read loop treats it as EOF.
        original = self.run_loop(REFERENCE, input_path=self.root)
        self.assertEqual(original.returncode, 0)
        self.assertIn(b'Is a directory', original.stderr)
        self.assertNotEqual(self.run_loop(scan_loop(), input_path=self.root).returncode, 0)

    def test_partial_normalization_failure_fails(self):
        shim = ('tr', "printf '%s\\n' 'agentic''-workflows'; exit 1")
        self.assertNotEqual(self.run_loop(scan_loop(), shim=shim).returncode, 0)

    def test_partial_aggregation_failure_fails(self):
        shim = ('awk', "printf 'partial output\\n'; exit 1")
        self.assertNotEqual(self.run_loop(scan_loop(), shim=shim).returncode, 0)

    def test_normalized_open_failure_fails(self):
        self.assertNotEqual(self.run_loop(scan_loop(), blocked_output='normalized').returncode, 0)

    def test_matches_open_failure_fails(self):
        self.assertNotEqual(self.run_loop(scan_loop(), blocked_output='matches').returncode, 0)

    def test_actual_open_failure_fails(self):
        self.assertNotEqual(self.run_loop(scan_loop(), blocked_output='actual').returncode, 0)

    def test_grep_failure_fails(self):
        shim = ('grep', "printf '1:%s\\n' 'agentic''-workflows'; exit 2")
        self.assertNotEqual(self.run_loop(scan_loop(), shim=shim).returncode, 0)


if __name__ == '__main__':
    unittest.main()
