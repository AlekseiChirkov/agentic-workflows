#!/usr/bin/env bash
# Check focused delivery function size and positional APIs without executing sources.
# Usage: bash tests/hook-shell-quality.sh [test-name ...]. Failures exit one.
set -uo pipefail
quality_source="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
python3 - "$quality_source" "$@" <<'PY'
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import unittest

SOURCE = Path(sys.argv[1])
SELECTED = sys.argv[2:]
DECLARATION = re.compile(
    r'(?m)^[ \t]*(?:function\s+([A-Za-z_][A-Za-z_0-9]*)(?:\s*\(\s*\))?'
    r'|([A-Za-z_][A-Za-z_0-9]*)\s*\(\s*\))\s*[({]'
)
POSITION = re.compile(r'\$(?:([1-9])|\{([1-9][0-9]*)(?=[:}/#%+?=\-]))')
ACTIVE_POSITION = re.compile(r'\$(?:([1-9])|\{([1-9][0-9]*))')
INSPECTION_SAMPLE = r'''
# ignored_comment() { printf '%s' "$9"; }
literal='
ignored_single() { printf "%s" "$9"; }
'
literal="
ignored_double() { printf '%s' '\$9'; }
"
cat <<'DATA'
ignored_heredoc() { printf '%s' "$9"; }
DATA
outer()
{
  printf '%s\n' '}' # quoted braces cannot terminate the function
  function inner {
    printf '%s\n' "${4:-fallback}" "$2" "$3"
  }
}
'''


@dataclass
class ShellSource:
    text: str
    index: int = 0
    masked: list[str] = field(default_factory=list)
    modes: list[str] = field(default_factory=lambda: ['shell'])
    heredocs: list[tuple[str, bool]] = field(default_factory=list)

    def consume(self: ShellSource, count: int, visible: bool = False) -> None:
        value = self.text[self.index:self.index + count]
        self.masked.extend(value if visible else re.sub(r'[^\n]', ' ', value))
        self.index += count

    def quoted(self: ShellSource) -> bool:
        char = self.text[self.index]
        mode = self.modes[-1]
        if mode == 'single':
            self.consume(1)
            if char == "'":
                self.modes.pop()
            return True
        if char == '\\':
            self.consume(min(2, len(self.text) - self.index))
            return True
        if char == '"' and mode != 'parameter':
            self.consume(1)
            if mode == 'double':
                self.modes.pop()
            else:
                self.modes.append('double')
            return True
        if char == "'" and mode not in ('double', 'parameter'):
            self.consume(1)
            self.modes.append('single')
            return True
        return False

    def expansion(self: ShellSource) -> bool:
        tail = self.text[self.index:]
        match = POSITION.match(tail)
        if match:
            self.consume(len(match.group()), True)
            if match.group(2):
                self.modes.append('parameter')
            return True
        if tail.startswith('${@') or tail.startswith('${*'):
            self.consume(3, True)
            self.modes.append('parameter')
            return True
        if tail.startswith('$(') or tail.startswith('${'):
            self.consume(2)
            self.modes.append('command' if tail[1] == '(' else 'parameter')
            return True
        if tail.startswith('$@') or tail.startswith('$*'):
            self.consume(2, True)
            return True
        return False

    def delimiters(self: ShellSource) -> bool:
        char = self.text[self.index]
        mode = self.modes[-1]
        if char == '`' and mode != 'parameter':
            self.consume(1)
            if mode == 'backtick':
                self.modes.pop()
            else:
                self.modes.append('backtick')
            return True
        if mode == 'parameter' and char == '}':
            self.consume(1)
            self.modes.pop()
            return True
        if mode not in ('double', 'parameter') and char in '()':
            self.consume(1, True)
            if char == '(':
                self.modes.append('command')
            elif mode == 'command':
                self.modes.pop()
            return True
        return False

    def heredoc(self: ShellSource) -> bool:
        tail = self.text[self.index:]
        if tail.startswith('<<<'):
            self.consume(3, True)
            return True
        if not tail.startswith('<<'):
            return False
        match = re.match(r'<<(-)?[ \t]*(?:([\'\"])(\w+)\2|(\w+))', tail)
        if not match:
            raise AssertionError('unsupported heredoc delimiter in source inspection')
        self.heredocs.append((match.group(3) or match.group(4), bool(match.group(1))))
        self.consume(len(match.group()))
        return True

    def heredoc_bodies(self: ShellSource) -> None:
        while self.heredocs:
            delimiter, strip_tabs = self.heredocs.pop(0)
            while self.index < len(self.text):
                end = self.text.find('\n', self.index)
                end = len(self.text) if end < 0 else end + 1
                line = self.text[self.index:end].rstrip('\n')
                self.consume(end - self.index)
                if (line.lstrip('\t') if strip_tabs else line) == delimiter:
                    break
            else:
                raise AssertionError('unterminated heredoc in source inspection')

    def mask(self: ShellSource) -> str:
        while self.index < len(self.text):
            if self.quoted() or self.expansion() or self.delimiters():
                continue
            char = self.text[self.index]
            visible = self.modes[-1] not in ('single', 'double', 'parameter')
            if visible and char == '#' and (
                self.index == 0 or self.text[self.index - 1] in ' \t\n;()|&<>'
            ):
                end = self.text.find('\n', self.index)
                self.consume((len(self.text) if end < 0 else end) - self.index)
                continue
            if visible and self.heredoc():
                continue
            self.consume(1, visible)
            if char == '\n' and self.heredocs:
                self.heredoc_bodies()
        if self.modes != ['shell']:
            raise AssertionError('unbalanced lexical context in source inspection')
        return ''.join(self.masked)


@dataclass(frozen=True)
class ShellFunction:
    name: str
    text: str
    active: str

    def parameters(self: ShellFunction) -> int:
        positions = [int(match.group(1) or match.group(2))
                     for match in ACTIVE_POSITION.finditer(self.active)]
        return max(positions, default=0)


def parses(source: str) -> bool:
    result = subprocess.run(['bash', '--noprofile', '--norc', '-n'],
                            input=source, text=True, capture_output=True, timeout=5)
    return result.returncode == 0


def function_end(text: str, start: int) -> int:
    end = text.find('\n', start)
    while end >= 0:
        if parses(text[start:end + 1]):
            return end + 1
        end = text.find('\n', end + 1)
    if parses(text[start:]):
        return len(text)
    raise AssertionError('unparseable function declaration')


def functions(text: str) -> dict[str, ShellFunction]:
    if not parses(text):
        raise AssertionError('shell source must parse before inspection')
    active = ShellSource(text).mask()
    found: dict[str, ShellFunction] = {}
    for declaration in DECLARATION.finditer(active):
        name = declaration.group(1) or declaration.group(2)
        if name in found:
            raise AssertionError(f'duplicate function declaration: {name}')
        end = function_end(text, declaration.start())
        found[name] = ShellFunction(name, text[declaration.start():end],
                                    active[declaration.start():end])
    if not found:
        raise AssertionError('source inspection found no function declarations')
    return found


@dataclass(frozen=True)
class ShellLimits:
    baseline: dict[str, str]
    extended: dict[str, int]
    argv: set[str]


def violations(path: str, limits: ShellLimits) -> list[str]:
    found = functions((SOURCE / path).read_text())
    named = limits.baseline.keys() | limits.extended.keys()
    if not named <= found.keys():
        raise AssertionError(f'stale function exceptions: {named - found.keys()}')
    errors: list[str] = []
    for name, function in found.items():
        if name in limits.baseline:
            if hashlib.sha256(function.text.encode()).hexdigest() != limits.baseline[name]:
                errors.append(f'{path}:{name}: excluded baseline function was changed')
            continue
        length = len(function.text.splitlines())
        maximum = limits.extended.get(name, 30)
        if length > maximum:
            errors.append(f'{path}:{name}: {length} physical lines exceeds {maximum}')
        if function.parameters() > 3:
            errors.append(f'{path}:{name}: {function.parameters()} parameters exceeds 3')
        if name not in limits.argv and re.search(r'\$[@*]|\$\{[@*]', function.active):
            errors.append(f'{path}:{name}: unbounded positional argument vector')
    return errors


class ShellQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls: type[ShellQuality]) -> None:
        # Check the inspector's lexical boundaries before trusting source measurements.
        found = functions(INSPECTION_SAMPLE)
        if set(found) != {'outer', 'inner'}:
            raise AssertionError(f'quoted/comment/heredoc declarations leaked: {set(found)}')
        if len(found['outer'].text.splitlines()) != 7 or found['inner'].parameters() != 4:
            raise AssertionError('physical function bounds or positional expansions were lost')
        for malformed in ('not a function', 'repeat() { :; }\nrepeat() { :; }', 'broken() {'):
            try:
                functions(malformed)
            except AssertionError:
                continue
            raise AssertionError('missing, duplicate or invalid declarations must fail closed')

    def test_native_shell_functions_meet_focused_limits(self: ShellQuality) -> None:
        # A single cached-record jq predicate retains cross-field consistency.
        limits = ShellLimits({}, {'record_valid': 40}, {'main', 'options'})
        errors = violations('hooks/log-step-hook.sh', limits)
        self.assertEqual(errors, [], '\n'.join(errors))

    def test_correlated_shell_functions_meet_focused_limits(self: ShellQuality) -> None:
        # Unchanged legacy functions are excluded separately from lifecycle exceptions.
        baseline = {
            'normalize_step_aliases': '90a760fcfc60ce6bbd79857a1d64b4e27f6cb3f753d22bfde9c22fdde71d33e3',
            'write_digest': 'bde737839e6352463fa0f9f3267f5e85965d86625290474a1958851831bf5a66',
            'validate_enum_arg': 'eae3669825510b047af11ac2ded88f1d66397e5b543b2a700465a4638b662d99',
        }
        lifecycle = {'cmd_run_start': 92, 'cmd_run_end': 64, 'cmd_lint': 186}
        argv = {'warn', 'die', 'parse_arguments', 'cmd_step', *lifecycle}
        errors = violations('scripts/log-step.sh', ShellLimits(baseline, lifecycle, argv))
        self.assertEqual(errors, [], '\n'.join(errors))

    def test_hook_metadata_api_uses_at_most_three_parameters(self: ShellQuality) -> None:
        found = functions((SOURCE / 'scripts/log-step.sh').read_text())
        self.assertIn('stage_hook_metadata', found)
        self.assertLessEqual(found['stage_hook_metadata'].parameters(), 3)


suite = unittest.TestSuite(ShellQuality(name) for name in SELECTED) if SELECTED else (
    unittest.defaultTestLoader.loadTestsFromTestCase(ShellQuality))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
PY
