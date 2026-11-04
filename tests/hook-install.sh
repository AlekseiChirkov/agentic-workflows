#!/usr/bin/env bash
# Exercise user hook installation and deployment in disposable roots only.
# Usage: bash tests/hook-install.sh [test-name ...]. Never deploys to the real home.
set -uo pipefail
install_test_source="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
python3 - "$install_test_source" "$@" <<'PY'
from __future__ import annotations
import ast
import concurrent.futures
import copy
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest
from typing import TypeAlias, TypedDict, Unpack

SOURCE = Path(sys.argv[1])
SELECTED = sys.argv[2:]

JsonValue: TypeAlias = str | int | float | Decimal | bool | None | list['JsonValue'] | dict[str, 'JsonValue']
JsonObject: TypeAlias = dict[str, JsonValue]
Environment: TypeAlias = dict[str, str]

class InstallOptions(TypedDict, total=False):
    expected: str
    env: Environment
    checkout: Path

class HookInstallation(unittest.TestCase):
    scratch: tempfile.TemporaryDirectory[str]
    root: Path
    checkout: Path
    home: Path
    config: Path
    state: Path
    project: Path
    settings: Path
    receipt: Path
    registry: Path
    env: Environment
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory(prefix='hook installation ')
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.checkout = self.root / "source 'quoted' with spaces"
        self.copy_source(self.checkout)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.config = self.root / 'config'
        self.state = self.root / 'state'
        self.project = self.root / 'consumer project'
        self.project.mkdir()
        self.settings = self.home / '.claude' / 'settings.json'
        self.receipt = self.config / 'orchestrail' / 'hooks-installed.json'
        self.registry = self.config / 'orchestrail' / 'projects'
        self.env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.config),
                        XDG_STATE_HOME=str(self.state), ORCHESTRAIL_HOME=str(self.checkout),
                        ORCHESTRAIL_LOG_ROOT=str(self.root / 'logs'))
        for name in ('PYTHONPATH', 'PYTHONSTARTUP', 'BASH_ENV', 'ENV'):
            self.env.pop(name, None)

    def copy_source(self, target: Path) -> None:
        for folder in ('scripts', 'hooks', 'harness', 'rules', 'workflows', 'principles', 'templates'):
            if (SOURCE / folder).exists():
                shutil.copytree(SOURCE / folder, target / folder)

    def write_settings(self, value: JsonObject) -> None:
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.settings.write_text(json.dumps(value, ensure_ascii=False))

    def read_settings(self) -> JsonObject:
        return json.loads(self.settings.read_text(), parse_float=Decimal)

    def assert_user_settings_preserved(self, expected: JsonObject) -> None:
        actual = self.read_settings()
        # Receipts track handler/group provenance. An empty manifest event array
        # or hooks object can remain when that container was originally absent.
        hooks = actual.get('hooks', {})
        expected_hooks = expected.get('hooks', {})
        for event in ('PreToolUse', 'Stop', 'SubagentStop'):
            if event not in expected_hooks and hooks.get(event) == []:
                del hooks[event]
        if 'hooks' not in expected and actual.get('hooks') == {}:
            del actual['hooks']
        self.assertEqual(expected, actual)

    def raw_call(self, *args: str, env: Environment | None = None, checkout: Path | None = None) -> subprocess.CompletedProcess[str]:
        installer = (checkout or self.checkout) / 'scripts' / 'install-hooks.sh'
        # Absent capability is an empty result so RED asserts the missing protocol,
        # rather than a command-not-found or fixture error.
        command = ['bash', str(installer), *args] if installer.exists() else ['bash', '-c', ':']
        return subprocess.run(command, cwd=self.project, env=env or self.env,
                              text=True, capture_output=True, timeout=15)

    def call(self, *args: str, expected: str = 'installed', env: Environment | None = None, checkout: Path | None = None) -> JsonObject:
        result = self.raw_call(*args, env=env, checkout=checkout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1,
                         'installer must publish one structured lifecycle result')
        data = json.loads(result.stdout)
        self.assertEqual(data.get('status'), expected, result.stdout + result.stderr)
        self.assertLess(len(result.stderr.encode()), 4096, 'diagnostics must stay bounded')
        return data

    def install(self, **kwargs: Unpack[InstallOptions]) -> JsonObject:
        return self.call('install', **kwargs)

    def owned_groups(self) -> dict[str, list[JsonObject]]:
        value = self.read_settings()
        self.assertEqual(set(value['hooks']), {'PreToolUse', 'Stop', 'SubagentStop'})
        for event, groups in value['hooks'].items():
            self.assertEqual(len(groups), 1, event)
            self.assertEqual(len(groups[0]['hooks']), 1, event)
        return value['hooks']

    def snapshot(self) -> tuple[bytes | None, ...]:
        return tuple(path.read_bytes() if path.exists() else None
                     for path in (self.settings, self.receipt, self.registry))

    def setup_project(self, cwd: Path | None = None, env: Environment | None = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(['bash', str(self.checkout / 'scripts' / 'setup-new-project.sh')],
                                cwd=cwd or self.project, env=env or self.env, input='2\n',
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def sync(self) -> subprocess.CompletedProcess[str]:
        # Replace only validation in this private source copy to avoid recursively
        # invoking these integration fixtures during the real deployment script.
        (self.checkout / 'scripts' / 'validate-contracts.sh').write_text('#!/bin/bash\nexit 0\n')
        result = subprocess.run(['bash', str(self.checkout / 'scripts' / 'sync.sh'),
                                 '--from', str(self.checkout)], cwd=self.project,
                                env=self.env, text=True, capture_output=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def prepare_upgrade(self, image: str = 'before') -> tuple[Path, JsonObject]:
        self.write_settings({'user':'preserved'})
        self.install()
        before_settings = self.settings.read_bytes()
        previous = json.loads(self.receipt.read_text())
        alternate = self.root / 'replacement source'
        self.copy_source(alternate)
        self.call('install', '--from', str(alternate))
        after_settings = self.settings.read_bytes()
        next_receipt = json.loads(self.receipt.read_text())
        for receipt in (previous, next_receipt):
            self.assertEqual(receipt['schema_version'], 2)
            self.assertEqual(receipt['state'], 'committed')
        prepared = {'schema_version':1, 'state':'prepared', 'previous':previous, 'next':next_receipt,
                    'before':{'present':True, 'sha256':hashlib.sha256(before_settings).hexdigest()},
                    'after':{'present':True, 'sha256':hashlib.sha256(after_settings).hexdigest()}}
        self.receipt.write_text(json.dumps(prepared))
        self.settings.write_bytes(before_settings if image == 'before' else after_settings)
        return alternate, prepared

    def interrupt_replacement(self, destination: Path) -> Environment:
        faults = self.root / ('interrupt-' + destination.name)
        faults.mkdir()
        (faults / 'sitecustomize.py').write_text(
            'from __future__ import annotations\nimport os\nfrom pathlib import Path\n'
            'from typing import Callable, Concatenate, ParamSpec, TypeVar\n'
            'P = ParamSpec("P")\nR = TypeVar("R")\nPathArg = str | os.PathLike[str]\n'
            'def wrap(original: Callable[Concatenate[PathArg, PathArg, P], R]) -> Callable[Concatenate[PathArg, PathArg, P], R]:\n'
            '    def replacement(src: PathArg, dst: PathArg, *args: P.args, **kwargs: P.kwargs) -> R:\n'
            '        result = original(src, dst, *args, **kwargs)\n'
            '        if Path(dst).resolve() == Path(os.environ["HOOK_TEST_DEST"]).resolve():\n'
            '            os._exit(91)\n'
            '        return result\n'
            '    return replacement\n'
            'os.replace = wrap(os.replace)\nos.rename = wrap(os.rename)\n')
        return dict(self.env, PYTHONPATH=str(faults), HOOK_TEST_DEST=str(destination))

    def interpreter_environment(self, usable: bool = True) -> Environment:
        binaries = self.root / ('older-python' if usable else 'unusable-python')
        binaries.mkdir()
        interpreter = shutil.which('python3')
        assert interpreter is not None
        driver = ('import collections,runpy,sys\n'
                  'sys.version_info=collections.namedtuple("Version","major minor micro releaselevel serial")(3,10,14,"final",0)\n'
                  'arguments=sys.argv[1:]\nsys.argv=arguments\n'
                  'if arguments[0] in ("--version","-V"):\n    print("Python 3.10.14")\n'
                  'elif arguments[0]=="-c":\n    exec(arguments[1],{"__name__":"__main__"})\n'
                  'else:\n    runpy.run_path(arguments[0],run_name="__main__")\n')
        command = 'exec ' + shlex.quote(interpreter) + ' -c ' + shlex.quote(driver) + ' "$@"\n'
        shim = binaries / 'python3'
        shim.write_text('#!/bin/bash\n' + (command if usable else 'exit 81\n'))
        shim.chmod(0o755)
        return dict(self.env, PATH=str(binaries) + os.pathsep + self.env.get('PATH',''))

    def test_hook_install_unsupported_python_preserves_settings_and_ownership(self) -> None:
        self.write_settings({'user':'keep this number', 'value':9007199254740993})
        before = self.snapshot()
        data = self.call('install', expected='unavailable', env=self.interpreter_environment())
        self.assertEqual(data['reason'], 'unsupported-python')
        self.assertEqual(before, self.snapshot())

    def test_hook_uninstall_unsupported_python_preserves_settings_and_ownership(self) -> None:
        self.install()
        before = self.snapshot()
        data = self.call('uninstall', expected='unavailable', env=self.interpreter_environment())
        self.assertEqual(data['reason'], 'unsupported-python')
        self.assertEqual(before, self.snapshot())

    def test_hook_unusable_python_reports_unsupported_before_either_operation(self) -> None:
        self.install()
        env = self.interpreter_environment(usable=False)
        for operation in ('install', 'uninstall'):
            with self.subTest(operation=operation):
                before = self.snapshot()
                data = self.call(operation, expected='unavailable', env=env)
                self.assertEqual(data['reason'], 'unsupported-python')
                self.assertEqual(before, self.snapshot())

    def test_hook_installer_functions_follow_public_python_standards(self) -> None:
        tree = ast.parse((self.checkout / 'scripts/install-hooks.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.assertIsNotNone(node.returns, node.name + ' requires a return annotation')
                parameters = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
                parameters += [arg for arg in (node.args.vararg, node.args.kwarg) if arg is not None]
                parameters = [arg for arg in parameters if arg.arg not in ('self', 'cls')]
                for argument in parameters:
                    self.assertIsNotNone(argument.annotation, node.name + '.' + argument.arg)
                self.assertLessEqual((node.end_lineno or node.lineno) - node.lineno + 1, 30, node.name)
                self.assertLessEqual(len(parameters), 3, node.name)
            if isinstance(node, ast.ClassDef):
                declared = {item.target.id for item in node.body
                            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)}
                assigned = {target.attr for item in ast.walk(node) if isinstance(item, ast.Assign)
                            for target in item.targets if isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name) and target.value.id == 'self'}
                self.assertFalse(assigned - declared, node.name + ' requires typed instance attributes')

    def test_hook_install_repeated_lifecycle_preserves_unrelated_settings(self) -> None:
        original = {'theme': 'user', 'hooks': {'PreToolUse': [{'matcher':'Bash', 'hooks':[
            {'type':'command', 'command':'user-tool'}]}]}, 'custom': ['x', {'enabled':False}]}
        self.write_settings(original)
        self.install()
        first = self.snapshot()
        self.install()
        self.assertEqual(first, self.snapshot(), 'repeat install must be byte-idempotent')
        self.call('uninstall', expected='uninstalled')
        self.assert_user_settings_preserved(original)
        first = self.snapshot()
        self.call('uninstall', expected='uninstalled')
        self.assertEqual(first, self.snapshot())
        self.assertFalse(self.registry.exists(), 'installation must not activate a project')

    def test_hook_install_preexisting_identical_entries_remain_unowned(self) -> None:
        self.install()
        hooks = self.owned_groups()
        self.call('uninstall', expected='uninstalled')
        original = {'hooks': hooks, 'other': 17}
        self.write_settings(original)
        self.install()
        self.call('uninstall', expected='uninstalled')
        self.assertEqual(original, self.read_settings())

    def test_hook_uninstall_changed_and_moved_entries_survive(self) -> None:
        self.install()
        value = self.read_settings()
        handler = value['hooks']['Stop'][0]['hooks'][0]
        handler['timeout'] = 29
        moved = value['hooks'].pop('SubagentStop')
        moved[0]['matcher'] = 'user-selected'
        value['hooks']['PreToolUse'] = moved
        self.write_settings(value)
        self.call('uninstall', expected='uninstalled')
        value.pop('permissions', None)
        self.assertEqual(value, self.read_settings())

    def test_hook_uninstall_equal_copies_preserve_unowned_multiplicity_and_empty_groups(self) -> None:
        self.write_settings({'hooks': {'Stop':[{'matcher':'', 'hooks':[]}], 'PreToolUse':[]}})
        self.install()
        value = self.read_settings()
        installed = next(group for group in value['hooks']['Stop'] if group['hooks'])
        installed['hooks'].append(copy.deepcopy(installed['hooks'][0]))
        value['hooks']['Stop'].append(copy.deepcopy(installed))
        value['hooks']['Stop'].append({'matcher':'user-empty', 'hooks':[]})
        before_handlers = sum(len(group['hooks']) for group in value['hooks']['Stop'])
        self.write_settings(value)
        self.call('uninstall', expected='uninstalled')
        after = self.read_settings()['hooks']['Stop']
        self.assertEqual(sum(len(group['hooks']) for group in after), before_handlers - 1)
        self.assertIn({'matcher':'', 'hooks':[]}, after)
        self.assertIn({'matcher':'user-empty', 'hooks':[]}, after)
        self.assertEqual(len(after), len(value['hooks']['Stop']))

    def test_hook_uninstall_removes_only_created_newly_empty_groups(self) -> None:
        self.install()
        value = self.read_settings()
        original_group = copy.deepcopy(value['hooks']['Stop'][0])
        value['hooks']['Stop'].append(copy.deepcopy(original_group))
        value['hooks']['Stop'].append({'hooks':[]})
        self.write_settings(value)
        self.call('uninstall', expected='uninstalled')
        groups = self.read_settings()['hooks']['Stop']
        self.assertEqual(groups, [original_group, {'hooks':[]}])

    def test_hook_install_source_precedence_and_quoted_paths_use_literal_arguments(self) -> None:
        alternate = self.root / 'alternate "quoted" source'
        self.copy_source(alternate)
        env = dict(self.env, ORCHESTRAIL_HOME=str(self.root / 'absent'))
        self.call('install', '--from', os.path.relpath(alternate, self.project), env=env)
        hooks = self.owned_groups()
        for groups in (hooks['Stop'], hooks['SubagentStop']):
            handler = groups[0]['hooks'][0]
            self.assertEqual(handler['command'], 'bash')
            self.assertEqual(handler['args'], [str(alternate / 'hooks' / 'log-step-hook.sh')])
            result = subprocess.run([handler['command'], *handler['args']], input='{}',
                                    env=self.env, cwd=self.project, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0)
        self.call('install', '--from=' + str(self.checkout), env=env)
        hooks = self.owned_groups()
        for groups in (hooks['Stop'], hooks['SubagentStop']):
            self.assertEqual(groups[0]['hooks'][0]['args'], [str(self.checkout / 'hooks' / 'log-step-hook.sh')])
        self.call('uninstall', expected='uninstalled', env=env)
        self.call('install', env=dict(self.env, ORCHESTRAIL_HOME=str(alternate)))
        hooks = self.owned_groups()
        for groups in (hooks['Stop'], hooks['SubagentStop']):
            self.assertEqual(groups[0]['hooks'][0]['args'], [str(alternate / 'hooks' / 'log-step-hook.sh')])
        self.call('uninstall', expected='uninstalled')
        self.call('install', env=dict(self.env, ORCHESTRAIL_HOME=''))

    def test_hook_install_invalid_cli_and_manifest_never_mutate_settings(self) -> None:
        self.install()
        for args in ((), ('unknown',), ('install','--from'), ('uninstall','--from','x'),
                     ('install','--unexpected'), ('install','--from=')):
            with self.subTest(args=args):
                before = self.snapshot()
                self.assertNotEqual(self.raw_call(*args).returncode, 0)
                self.assertEqual(before, self.snapshot())
        for flag in ('-h','--help'):
            before = self.snapshot()
            result = self.raw_call(flag)
            self.assertEqual(result.returncode, 0)
            self.assertIn('install', result.stdout)
            self.assertIn('uninstall', result.stdout)
            self.assertEqual(before, self.snapshot())
        manifest = self.checkout / 'harness/claude/hooks.json'
        valid = json.loads(manifest.read_text())
        for command in ('@ORCHESTRAIL_HOME@/hooks/log-step-hook.sh', 'bash; echo invalid'):
            invalid = copy.deepcopy(valid)
            invalid['hooks']['Stop'][0]['hooks'][0]['command'] = command
            manifest.write_text(json.dumps(invalid))
            before = self.snapshot()
            self.call('install', expected='unavailable')
            self.assertEqual(before, self.snapshot())

    def test_hook_install_upgrade_preserves_changed_old_handler(self) -> None:
        self.install()
        value = self.read_settings()
        changed = value['hooks']['Stop'][0]['hooks'][0]
        changed['timeout'] = 21
        self.write_settings(value)
        alternate = self.root / 'new source'
        self.copy_source(alternate)
        self.call('install', '--from', str(alternate))
        handlers = [handler for group in self.read_settings()['hooks']['Stop'] for handler in group['hooks']]
        self.assertIn(changed, handlers)
        self.assertEqual(len(handlers), 2)
        shutil.rmtree(alternate)
        self.call('uninstall', expected='uninstalled', env=dict(self.env, ORCHESTRAIL_HOME=str(alternate)))
        remaining = [h for g in self.read_settings()['hooks']['Stop'] for h in g['hooks']]
        self.assertEqual(remaining, [changed])

    def test_hook_install_malformed_settings_preserve_exact_bytes(self) -> None:
        for contents in ('{broken secret', '[]', '{"hooks":[]}', '{"hooks":{"Stop":[{"hooks":null}]}}',
                         '{"hooks":{"Stop":[{"hooks":[4]}]}}', '{"a":1,"a":2}'):
            with self.subTest(contents=contents):
                self.settings.parent.mkdir(parents=True, exist_ok=True)
                self.settings.write_text(contents)
                before = self.snapshot()
                self.call('install', expected='unavailable')
                self.assertEqual(before, self.snapshot())

    def test_hook_install_malformed_receipt_preserves_both_files(self) -> None:
        self.install()
        for contents in ('{broken', '[]', '{}', '{"schema_version":1,"owned":"wrong"}'):
            with self.subTest(contents=contents):
                self.receipt.write_text(contents)
                before = self.snapshot()
                self.call('install', expected='unavailable')
                self.assertEqual(before, self.snapshot())
                self.call('uninstall', expected='unavailable')
                self.assertEqual(before, self.snapshot())

    def test_hook_receipt_control_numbers_cannot_gain_deletion_ownership(self) -> None:
        self.install()
        valid = json.loads(self.receipt.read_text())
        self.assertEqual(valid['state'], 'committed')
        self.assertTrue(valid['owned'])
        valid_text = json.dumps(valid, separators=(',',':'))
        self.assertIn('"count":1', valid_text)
        for token in ('1.00000000000000001', '1e0', '-1', 'true', '0', '9007199254740992'):
            with self.subTest(token=token):
                self.receipt.write_text(valid_text.replace('"count":1', '"count":' + token))
                before = self.snapshot()
                self.call('uninstall', expected='unavailable')
                self.assertEqual(before, self.snapshot())
        self.receipt.write_text(valid_text.replace('"schema_version":2', '"schema_version":2e0'))
        before = self.snapshot()
        self.call('uninstall', expected='unavailable')
        self.assertEqual(before, self.snapshot())
        for field in ('owned', 'created_groups'):
            duplicate = copy.deepcopy(valid)
            self.assertTrue(duplicate[field])
            duplicate[field].append(copy.deepcopy(duplicate[field][0]))
            self.receipt.write_text(json.dumps(duplicate))
            before = self.snapshot()
            self.call('uninstall', expected='unavailable')
            self.assertEqual(before, self.snapshot())

    def test_hook_ownership_object_equality_ignores_key_order_and_numeric_spelling(self) -> None:
        self.install()
        value = self.read_settings()
        for groups in value['hooks'].values():
            group = groups[0]
            handler = group['hooks'][0]
            group['hooks'][0] = dict(reversed(list(handler.items())))
        serialized = json.dumps(value).replace('"timeout": 10', '"timeout": 1e1')
        self.settings.write_text(serialized)
        self.call('uninstall', expected='uninstalled')
        self.assertFalse(any(g['hooks'] for groups in self.read_settings().get('hooks',{}).values() for g in groups))

    def test_hook_ownership_omitted_fields_and_changed_argument_arrays_remain_unowned(self) -> None:
        self.install()
        value = self.read_settings()
        value['hooks']['Stop'][0]['hooks'][0].pop('onFailure')
        value['hooks']['SubagentStop'][0]['hooks'][0]['args'].append('--user-argument')
        self.write_settings(value)
        self.call('uninstall', expected='uninstalled')
        expected = copy.deepcopy(value)
        expected['hooks']['PreToolUse'] = []
        expected.pop('permissions', None)
        self.assertEqual(self.read_settings(), expected)

    def test_hook_recovery_before_image_restores_previous_then_recomputes_install(self) -> None:
        alternate, prepared = self.prepare_upgrade('before')
        self.call('install', '--from', str(alternate))
        self.assertEqual(json.loads(self.receipt.read_text()), prepared['next'])
        hooks = self.owned_groups()
        for groups in (hooks['Stop'], hooks['SubagentStop']):
            self.assertEqual(groups[0]['hooks'][0]['args'], [str(alternate / 'hooks/log-step-hook.sh')])
        self.assertEqual(self.read_settings()['user'], 'preserved')

    def test_hook_recovery_after_image_finalizes_then_recomputes_install(self) -> None:
        alternate, prepared = self.prepare_upgrade('after')
        self.call('install', '--from', str(alternate))
        self.assertEqual(json.loads(self.receipt.read_text()), prepared['next'])
        self.assertEqual(self.read_settings()['user'], 'preserved')

    def test_hook_recovery_external_edit_preserves_settings_and_prepared_receipt(self) -> None:
        alternate, prepared = self.prepare_upgrade('after')
        value = self.read_settings()
        value['external'] = 'new user value'
        self.write_settings(value)
        before = self.snapshot()
        self.call('install', '--from', str(alternate), expected='unavailable')
        self.assertEqual(before, self.snapshot())
        self.call('uninstall', expected='unavailable')
        self.assertEqual(before, self.snapshot())

    def test_hook_recovery_uninstall_uses_saved_state_after_old_source_disappears(self) -> None:
        alternate, prepared = self.prepare_upgrade('after')
        shutil.rmtree(self.checkout)
        env = dict(self.env, ORCHESTRAIL_HOME=str(self.checkout))
        self.call('uninstall', expected='uninstalled', checkout=alternate, env=env)
        self.assert_user_settings_preserved({'user':'preserved'})
        if self.receipt.exists():
            self.assertEqual(json.loads(self.receipt.read_text()),
                             {'schema_version':1, 'state':'committed', 'owned':[], 'created_groups':[]})

    def test_hook_recovery_malformed_prepared_receipt_never_replaces_settings(self) -> None:
        alternate, prepared = self.prepare_upgrade('before')
        invalid_variants = []
        for field, replacement in (('before', {'present':True,'sha256':'bad'}),
                                   ('after', {'present':False,'sha256':'a'*64}),
                                   ('previous', {'schema_version':1,'state':'prepared'})):
            invalid = copy.deepcopy(prepared)
            invalid[field] = replacement
            invalid_variants.append(invalid)
        for invalid in invalid_variants:
            self.receipt.write_text(json.dumps(invalid))
            before = self.snapshot()
            self.call('install', '--from', str(alternate), expected='unavailable')
            self.assertEqual(before, self.snapshot())

    def test_hook_transaction_interruption_before_settings_recovers_absent_image(self) -> None:
        self.install()
        self.call('uninstall', expected='uninstalled')
        self.settings.unlink()
        if self.receipt.exists():
            previous = json.loads(self.receipt.read_text())
            self.assertEqual(previous, {'schema_version':1, 'state':'committed',
                                        'owned':[], 'created_groups':[]})
            self.receipt.unlink()
        env = self.interrupt_replacement(self.receipt)
        self.raw_call('install', env=env)
        self.assertTrue(self.receipt.exists(), 'transaction must persist prepared ownership before settings')
        prepared = json.loads(self.receipt.read_text())
        self.assertEqual(prepared['state'], 'prepared')
        self.assertEqual(prepared['before'], {'present':False,'sha256':None})
        self.assertIsNone(prepared['previous'])
        self.assertFalse(self.settings.exists())
        self.install()
        self.owned_groups()
        self.assertEqual(json.loads(self.receipt.read_text())['state'], 'committed')

    def test_hook_transaction_interruption_after_settings_recovers_committed_image(self) -> None:
        self.install()
        self.call('uninstall', expected='uninstalled')
        env = self.interrupt_replacement(self.settings)
        self.raw_call('install', env=env)
        prepared = json.loads(self.receipt.read_text())
        self.assertEqual(prepared['state'], 'prepared')
        self.assertEqual(hashlib.sha256(self.settings.read_bytes()).hexdigest(), prepared['after']['sha256'])
        self.call('uninstall', expected='uninstalled')
        self.assertFalse(any(g['hooks'] for groups in self.read_settings().get('hooks',{}).values() for g in groups))
        if self.receipt.exists():
            self.assertEqual(json.loads(self.receipt.read_text()),
                             {'schema_version':1, 'state':'committed', 'owned':[], 'created_groups':[]})

    def test_hook_transaction_rechecks_before_image_after_preparing_ownership(self) -> None:
        self.install()
        alternate = self.root / 'upgrade source'
        self.copy_source(alternate)
        external = self.root / 'external-settings.json'
        external.write_text('{"external":"preserve this concurrent user edit"}')
        faults = self.root / 'concurrent-editor'
        faults.mkdir()
        (faults / 'sitecustomize.py').write_text(
            'from __future__ import annotations\nimport os\nfrom pathlib import Path\n'
            'from typing import Callable, Concatenate, ParamSpec, TypeVar\n'
            'P = ParamSpec("P")\nR = TypeVar("R")\nPathArg = str | os.PathLike[str]\n'
            'def wrap(original: Callable[Concatenate[PathArg, PathArg, P], R]) -> Callable[Concatenate[PathArg, PathArg, P], R]:\n'
            '    def replacement(src: PathArg, dst: PathArg, *args: P.args, **kwargs: P.kwargs) -> R:\n'
            '        result = original(src, dst, *args, **kwargs)\n'
            '        if Path(dst).resolve() == Path(os.environ["HOOK_TEST_RECEIPT"]).resolve():\n'
            '            Path(os.environ["HOOK_TEST_SETTINGS"]).write_bytes(Path(os.environ["HOOK_TEST_EXTERNAL"]).read_bytes())\n'
            '        return result\n'
            '    return replacement\n'
            'os.replace = wrap(os.replace)\nos.rename = wrap(os.rename)\n')
        env = dict(self.env, PYTHONPATH=str(faults),
                   HOOK_TEST_RECEIPT=str(self.receipt), HOOK_TEST_SETTINGS=str(self.settings),
                   HOOK_TEST_EXTERNAL=str(external))
        self.call('install', '--from', str(alternate), expected='unavailable', env=env)
        self.assertEqual(self.settings.read_bytes(), external.read_bytes())
        self.assertEqual(json.loads(self.receipt.read_text())['state'], 'prepared')
        before = self.snapshot()
        self.call('uninstall', expected='unavailable')
        self.assertEqual(before, self.snapshot())

    def test_hook_transaction_replacement_failure_preserves_settings_and_allows_retry(self) -> None:
        self.install()
        self.call('uninstall', expected='uninstalled')
        before = self.settings.read_bytes()
        faults = self.root / 'failed-replacement'
        faults.mkdir()
        (faults / 'sitecustomize.py').write_text(
            'from __future__ import annotations\nimport os\nfrom pathlib import Path\n'
            'from typing import Callable, Concatenate, ParamSpec, TypeVar\n'
            'P = ParamSpec("P")\nR = TypeVar("R")\nPathArg = str | os.PathLike[str]\n'
            'def wrap(original: Callable[Concatenate[PathArg, PathArg, P], R]) -> Callable[Concatenate[PathArg, PathArg, P], R]:\n'
            '    def replacement(src: PathArg, dst: PathArg, *args: P.args, **kwargs: P.kwargs) -> R:\n'
            '        if Path(dst).resolve() == Path(os.environ["HOOK_TEST_SETTINGS"]).resolve():\n'
            '            raise OSError("fixture denies settings replacement")\n'
            '        return original(src, dst, *args, **kwargs)\n'
            '    return replacement\n'
            'os.replace = wrap(os.replace)\nos.rename = wrap(os.rename)\n')
        env = dict(self.env, PYTHONPATH=str(faults), HOOK_TEST_SETTINGS=str(self.settings))
        self.call('install', expected='unavailable', env=env)
        self.assertEqual(before, self.settings.read_bytes())
        receipt = json.loads(self.receipt.read_text())
        self.assertIn(receipt['state'], ('prepared', 'committed'))
        self.install()
        self.owned_groups()

    def test_hook_install_preserves_exact_json_numbers_and_strings(self) -> None:
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        original = ('{"large":9007199254740993,"precise":1.2345678901234567890123456789,'
                    '"huge":1e400,"tiny":1e-400,"zero":-0,"text":"1e400 \\u263a",'
                    '"nested":{"literal":"@ORCHESTRAIL_HOME@"}}')
        self.settings.write_text(original)
        expected = json.loads(original, parse_float=Decimal)
        number_tokens = {'large':'9007199254740993', 'precise':'1.2345678901234567890123456789',
                         'huge':'1e400', 'tiny':'1e-400', 'zero':'-0'}
        self.install()
        for field, token in number_tokens.items():
            self.assertRegex(self.settings.read_text(),
                             '"' + field + r'"\s*:\s*' + re.escape(token) + r'(?=\s*[,}])',
                             'installation must preserve the original numeric token for ' + field)
        self.call('uninstall', expected='uninstalled')
        for field, token in number_tokens.items():
            self.assertRegex(self.settings.read_text(),
                             '"' + field + r'"\s*:\s*' + re.escape(token) + r'(?=\s*[,}])',
                             'uninstall must preserve the original numeric token for ' + field)
        self.assert_user_settings_preserved(expected)
        self.assertNotIn('Infinity', self.settings.read_text())

    def test_hook_install_missing_dependencies_report_unavailable_without_mutation(self) -> None:
        self.install()
        dependency_paths = {name: shutil.which(name) for name in ('python3', 'jq', 'flock')}
        for missing in dependency_paths:
            with self.subTest(missing=missing):
                bins = self.root / ('without-' + missing)
                bins.mkdir()
                # Include standard shell utilities without the selected dependency.
                for name in ('bash','dirname','mkdir','mktemp','mv','rm','cat','chmod','cp','realpath',
                             'readlink','pwd','sha256sum','cmp','stat','date','sed','grep','head','tr','wc'):
                    target = shutil.which(name)
                    if target:
                        (bins / name).symlink_to(target)
                for name, target in dependency_paths.items():
                    if name != missing and target:
                        (bins / name).symlink_to(target)
                before = self.snapshot()
                self.call('install', expected='unavailable', env=dict(self.env, PATH=str(bins)))
                self.assertEqual(before, self.snapshot())

    def test_hook_install_concurrent_operations_are_serialized_and_parseable(self) -> None:
        self.install()
        def operation(index: int) -> subprocess.CompletedProcess[str]:
            return self.raw_call('install' if index % 3 else 'uninstall')
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(operation, range(24)))
        for result in results:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(json.loads(result.stdout)['status'], ('installed','uninstalled'))
        self.install()
        self.owned_groups()
        json.loads(self.receipt.read_text())
        self.call('uninstall', expected='uninstalled')
        self.assertFalse(any(g['hooks'] for groups in self.read_settings().get('hooks', {}).values() for g in groups))

    def test_hook_uninstall_recovers_without_native_dependencies_but_requires_python(self) -> None:
        alternate, prepared = self.prepare_upgrade('after')
        shutil.rmtree(alternate)
        without_python = self.root / 'without-uninstall-python'
        without_python.mkdir()
        for name in ('bash','dirname','jq','flock'):
            (without_python / name).symlink_to(shutil.which(name))
        before = self.snapshot()
        self.call('uninstall', expected='unavailable', env=dict(self.env, PATH=str(without_python)))
        self.assertEqual(before, self.snapshot())
        without_native = self.root / 'without-native-runtime'
        without_native.mkdir()
        for name in ('bash','dirname','python3'):
            (without_native / name).symlink_to(shutil.which(name))
        self.call('uninstall', expected='uninstalled', env=dict(self.env, PATH=str(without_native)))
        self.assert_user_settings_preserved({'user':'preserved'})

    def test_hook_receipt_literal_null_is_invalid_and_nullable_next_recovers_absence(self) -> None:
        self.write_settings({'user':'preserved'})
        self.install()
        valid = self.receipt.read_bytes()
        self.receipt.write_text('null')
        before = self.snapshot()
        self.call('uninstall', expected='unavailable')
        self.assertEqual(before, self.snapshot())
        self.receipt.write_bytes(valid)
        previous = json.loads(valid)
        before_settings = self.settings.read_bytes()
        self.call('uninstall', expected='uninstalled')
        after_settings = self.settings.read_bytes()
        prepared = {'schema_version':1,'state':'prepared','previous':previous,'next':None,
                    'before':{'present':True,'sha256':hashlib.sha256(before_settings).hexdigest()},
                    'after':{'present':True,'sha256':hashlib.sha256(after_settings).hexdigest()}}
        self.receipt.write_text(json.dumps(prepared))
        self.call('uninstall', expected='uninstalled')
        self.assertFalse(self.receipt.exists())
        self.assert_user_settings_preserved({'user':'preserved'})

    def test_hook_manifest_and_capabilities_describe_available_mechanism_and_partial_coverage(self) -> None:
        manifest = self.checkout / 'harness' / 'claude' / 'hooks.json'
        self.assertTrue(manifest.is_file(), 'portable native hook manifest must exist')
        hooks = json.loads(manifest.read_text())['hooks']
        self.assertEqual(set(hooks), {'PreToolUse','Stop','SubagentStop'})
        self.assertEqual(hooks['PreToolUse'], [{'matcher':'Bash', 'hooks':[{'type':'command', 'command':'bash',
            'args':['@ORCHESTRAIL_HOME@/hooks/git-rails.sh'], 'timeout':10, 'onFailure':'block'}]}])
        for groups in (hooks['Stop'], hooks['SubagentStop']):
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0]['hooks'], [{'type':'command', 'command':'bash',
                'args':['@ORCHESTRAIL_HOME@/hooks/log-step-hook.sh'], 'timeout':10, 'onFailure':'continue'}])
        claude = (self.checkout / 'harness' / 'claude' / 'capabilities.md').read_text()
        codex = (self.checkout / 'harness' / 'codex' / 'capabilities.md').read_text()
        for token in ('hooks: yes', 'claude-stop-v1', '2026-10-25', '2.1.309', 'coverage', 'unknown', 'approximate'):
            self.assertIn(token, claude)
        for token in ('hooks: no', 'approximate', 'release', 'coverage'):
            self.assertIn(token, codex)

    def test_hook_setup_registers_canonical_roots_idempotently_and_adapter_gates(self) -> None:
        alias = self.root / 'alias'
        alias.symlink_to(self.project, target_is_directory=True)
        self.setup_project(cwd=alias)
        self.assertTrue(self.registry.is_file(), 'project setup must activate its physical root')
        self.assertEqual(self.registry.read_text().splitlines(), [str(self.project.resolve())])
        first = self.registry.read_bytes()
        self.setup_project()
        self.assertEqual(first, self.registry.read_bytes())
        self.assertIn('.ai/', (self.project / '.gitignore').read_text())
        adapter = self.checkout / 'hooks' / 'log-step-hook.sh'
        result = subprocess.run(['bash', str(adapter)], input=json.dumps({'cwd':str(self.root)}), cwd=self.root,
                                env=self.env, text=True, capture_output=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        result = subprocess.run(['bash', str(adapter)], input=json.dumps({'cwd':str(self.project)}), cwd=self.project,
                                env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('coverage', result.stderr)

    def test_hook_setup_trailing_newline_is_rejected_and_sibling_prefix_stays_inactive(self) -> None:
        self.setup_project()
        before = self.registry.read_bytes()
        newline_project = self.root / 'trailing-newline\n'
        newline_project.mkdir()
        result = self.setup_project(cwd=newline_project)
        self.assertIn('unavailable', result.stdout + result.stderr)
        self.assertEqual(before, self.registry.read_bytes())
        sibling = self.project.with_name(self.project.name + '-sibling')
        sibling.mkdir()
        adapter = self.checkout / 'hooks/log-step-hook.sh'
        result = subprocess.run(['bash', str(adapter)], input=json.dumps({'cwd':str(sibling)}),
                                cwd=self.project, env=self.env, text=True, capture_output=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        before = self.snapshot()
        result = subprocess.run(['bash', str(adapter)], input='{}', cwd=sibling,
                                env=self.env, text=True, capture_output=True)
        self.assertEqual((result.returncode, result.stdout), (0, ''))
        self.assertIn('invalid-native-input', result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_hook_setup_concurrent_registration_preserves_existing_roots(self) -> None:
        self.setup_project()
        self.assertTrue(self.registry.exists(), 'setup must publish the consumer registry')
        projects = [self.root / ('consumer ' + str(index)) for index in range(6)]
        for project in projects:
            project.mkdir()
            (project / 'AGENTS.md').write_text('# Existing project\n')
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(self.setup_project, projects + projects))
        self.assertEqual(set(self.registry.read_text().splitlines()), {str(p.resolve()) for p in [self.project, *projects]})
        self.assertEqual(len(self.registry.read_text().splitlines()), len(projects) + 1)

    def test_hook_setup_default_config_location_preserves_custom_project_files(self) -> None:
        (self.project / 'AGENTS.md').write_text('# Custom project guidance\n')
        (self.project / 'CLAUDE.md').write_text('# Custom Claude guidance\n')
        env = dict(self.env)
        env.pop('XDG_CONFIG_HOME')
        self.setup_project(env=env)
        registry = self.home / '.config/orchestrail/projects'
        self.assertTrue(registry.is_file(), 'setup must honor the default user configuration location')
        self.assertEqual(registry.read_text().splitlines(), [str(self.project.resolve())])
        self.assertFalse(self.registry.exists())
        self.assertEqual((self.project / 'AGENTS.md').read_text(), '# Custom project guidance\n')
        self.assertEqual((self.project / 'CLAUDE.md').read_text(), '# Custom Claude guidance\n')

    def test_hook_setup_invalid_registry_or_newline_root_preserves_existing_entries(self) -> None:
        self.setup_project()
        self.assertTrue(self.registry.exists(), 'setup must publish the registry before rejection checks')
        for contents in ('relative/path\n', '\x00bad\n', '/valid\n\n'):
            with self.subTest(contents=contents):
                self.registry.write_text(contents)
                result = self.setup_project()
                self.assertEqual(self.registry.read_text(), contents)
                self.assertIn('unavailable', result.stdout + result.stderr)
        self.registry.write_text(str(self.project) + '\n')
        strange = self.root / 'unsupported\nproject'
        strange.mkdir()
        before = self.registry.read_bytes()
        result = self.setup_project(cwd=strange)
        self.assertEqual(before, self.registry.read_bytes())
        self.assertIn('unavailable', result.stdout + result.stderr)

    def test_hook_sync_embeds_capabilities_once_and_preserves_all_deployment_targets(self) -> None:
        self.sync()
        claude_cap = self.checkout / 'harness' / 'claude' / 'capabilities.md'
        codex_cap = self.checkout / 'harness' / 'codex' / 'capabilities.md'
        self.assertTrue(claude_cap.exists(), 'sync requires declared native hook capability')
        self.assertTrue(codex_cap.exists(), 'sync requires an explicit fallback capability')
        for target, body, capability in (
            (self.home / '.claude' / 'CLAUDE.md', self.checkout / 'rules' / 'global-claude.md', claude_cap),
            (self.home / '.codex' / 'AGENTS.md', self.checkout / 'templates' / 'codex-global-AGENTS.md', codex_cap)):
            content = target.read_text()
            self.assertTrue(content.startswith(body.read_text()))
            self.assertEqual(content.count(capability.read_text().strip()), 1)
            self.assertIn('installed', content) if 'claude' in str(target) else self.assertIn('unavailable', content)
        first = ((self.home / '.claude' / 'CLAUDE.md').read_bytes(), (self.home / '.codex' / 'AGENTS.md').read_bytes())
        self.sync()
        self.assertEqual(first, ((self.home / '.claude' / 'CLAUDE.md').read_bytes(), (self.home / '.codex' / 'AGENTS.md').read_bytes()))
        for source_folder, target_folder, prefix in (
            ('workflows','.claude/skills',''), ('rules','.claude/skills','rule-'),
            ('principles','.claude/skills','principle-'), ('workflows','.codex/skills',''),
            ('rules','.codex/skills','rule-'), ('principles','.codex/skills','principle-')):
            for path in (self.checkout / source_folder).glob('*.md'):
                self.assertEqual(path.read_bytes(), (self.home / target_folder / (prefix + path.stem) / 'SKILL.md').read_bytes())
        for folder in ('workflows','rules','principles'):
            for path in (self.checkout / folder).glob('*.md'):
                destination = 'global_workflows' if folder == 'workflows' else 'global_rules'
                self.assertEqual(path.read_bytes(), (self.home / '.codeium/windsurf' / destination / path.name).read_bytes())
        self.assertFalse(self.registry.exists(), 'sync must not register the source or consumers implicitly')

    def test_hook_sync_unavailable_installation_still_refreshes_consumer_projects(self) -> None:
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text('{malformed')
        consumer = self.home / 'consumer'
        for folder in ('.devin/rules','.windsurf/rules','.claude/skills','.devin/workflows'):
            (consumer / folder).mkdir(parents=True, exist_ok=True)
        (consumer / '.devin/rules/tdd.md').write_text('stale')
        (consumer / '.devin/workflows/phase-discovery.md').write_text('stale')
        (consumer / '.devin/workflows/custom.md').write_text('custom')
        self.sync()
        claude = (self.home / '.claude/CLAUDE.md').read_text()
        self.assertIn('unavailable', claude, 'sync must disclose failed native installation')
        self.assertEqual(self.settings.read_text(), '{malformed')
        self.assertEqual((consumer / '.devin/rules/tdd.md').read_bytes(), (self.checkout / 'rules/tdd.md').read_bytes())
        self.assertEqual((consumer / '.windsurf/rules/tdd.md').read_bytes(), (self.checkout / 'rules/tdd.md').read_bytes())
        self.assertTrue((consumer / '.claude/skills/pae-tests').is_symlink())
        self.assertFalse((consumer / '.devin/workflows/phase-discovery.md').exists())
        self.assertEqual((consumer / '.devin/workflows/custom.md').read_text(), 'custom')

    # The git-rails PreToolUse registration shares the installer guarantees of the
    # logging handlers: exact ownership, idempotence, recovery and owned-only removal.
    GIT_RAILS_MANIFEST_HANDLER: JsonObject = {'type':'command', 'command':'bash',
        'args':['@ORCHESTRAIL_HOME@/hooks/git-rails.sh'], 'timeout':10, 'onFailure':'block'}
    LOGGING_MANIFEST_HANDLER: JsonObject = {'type':'command', 'command':'bash',
        'args':['@ORCHESTRAIL_HOME@/hooks/log-step-hook.sh'], 'timeout':10, 'onFailure':'continue'}
    GIT_RAILS_SELECTOR: JsonObject = {'matcher':'Bash'}

    def git_rails_handler(self, source: Path | None = None) -> JsonObject:
        return dict(self.GIT_RAILS_MANIFEST_HANDLER,
                    args=[str((source or self.checkout).resolve() / 'hooks' / 'git-rails.sh')])

    def logging_handler(self, source: Path | None = None) -> JsonObject:
        return dict(self.LOGGING_MANIFEST_HANDLER,
                    args=[str((source or self.checkout).resolve() / 'hooks' / 'log-step-hook.sh')])

    def git_rails_occurrences(self, value: JsonObject | None = None, source: Path | None = None) -> int:
        hooks = (value if value is not None else self.read_settings()).get('hooks', {})
        expected = self.git_rails_handler(source)
        return sum(1 for group in hooks.get('PreToolUse', []) if group.get('matcher') == 'Bash'
                   for handler in group['hooks'] if handler == expected)

    def assert_registered(self, source: Path | None = None) -> None:
        self.assertEqual(self.git_rails_occurrences(source=source), 1,
                         'installation must register exactly one owned git-rails Bash handler')

    def assert_no_owned_handlers(self) -> None:
        hooks = self.read_settings().get('hooks', {})
        owned = (self.git_rails_handler(), self.logging_handler())
        self.assertFalse([handler for groups in hooks.values() for group in groups
                          for handler in group['hooks'] if handler in owned])

    def assert_settings_restored(self, expected: JsonObject) -> None:
        # Removal may leave an empty event array or hooks object it did not find.
        actual = self.read_settings()
        hooks = actual.get('hooks', {})
        for event in ('PreToolUse', 'Stop', 'SubagentStop'):
            if event not in expected.get('hooks', {}) and hooks.get(event) == []:
                del hooks[event]
        if 'hooks' not in expected and actual.get('hooks') == {}:
            del actual['hooks']
        self.assertEqual(expected, actual)

    def manifest_path(self, source: Path | None = None) -> Path:
        return (source or self.checkout) / 'harness' / 'claude' / 'hooks.json'

    def registered_manifest(self) -> JsonObject:
        manifest = json.loads(self.manifest_path().read_text())
        self.assertIn('PreToolUse', manifest['hooks'], 'the manifest must register the git-rails PreToolUse handler')
        return manifest

    def install_logging_only_state(self) -> JsonObject:
        """Settings and ownership exactly as a logging-only installation left them."""
        logging = self.logging_handler()
        settings: JsonObject = {'user':'kept', 'hooks':{event:[{'hooks':[copy.deepcopy(logging)]}]
                                                        for event in ('Stop', 'SubagentStop')}}
        self.write_settings(settings)
        receipt: JsonObject = {'schema_version':1, 'state':'committed',
            'owned':[{'event':event, 'selector':{}, 'handler':copy.deepcopy(logging), 'count':1}
                     for event in ('Stop', 'SubagentStop')],
            'created_groups':[{'event':event, 'selector':{}, 'count':1} for event in ('Stop', 'SubagentStop')]}
        self.receipt.parent.mkdir(parents=True, exist_ok=True)
        self.receipt.write_text(json.dumps(receipt))
        return settings

    def concurrent_editor_environment(self, external: Path) -> Environment:
        faults = self.root / 'git-rails-concurrent-editor'
        faults.mkdir()
        (faults / 'sitecustomize.py').write_text(
            'from __future__ import annotations\nimport os\nfrom pathlib import Path\n'
            'from typing import Callable, Concatenate, ParamSpec, TypeVar\n'
            'P = ParamSpec("P")\nR = TypeVar("R")\nPathArg = str | os.PathLike[str]\n'
            'def wrap(original: Callable[Concatenate[PathArg, PathArg, P], R]) -> Callable[Concatenate[PathArg, PathArg, P], R]:\n'
            '    def replacement(src: PathArg, dst: PathArg, *args: P.args, **kwargs: P.kwargs) -> R:\n'
            '        result = original(src, dst, *args, **kwargs)\n'
            '        if Path(dst).resolve() == Path(os.environ["HOOK_TEST_RECEIPT"]).resolve():\n'
            '            Path(os.environ["HOOK_TEST_SETTINGS"]).write_bytes(Path(os.environ["HOOK_TEST_EXTERNAL"]).read_bytes())\n'
            '        return result\n'
            '    return replacement\n'
            'os.replace = wrap(os.replace)\nos.rename = wrap(os.rename)\n')
        return dict(self.env, PYTHONPATH=str(faults), HOOK_TEST_RECEIPT=str(self.receipt),
                    HOOK_TEST_SETTINGS=str(self.settings), HOOK_TEST_EXTERNAL=str(external))

    def test_hook_git_rails_manifest_registers_blocking_bash_handler_beside_logging(self) -> None:
        hooks = json.loads(self.manifest_path().read_text())['hooks']
        self.assertEqual(set(hooks), {'PreToolUse', 'Stop', 'SubagentStop'})
        self.assertEqual(hooks['PreToolUse'], [{'matcher':'Bash', 'hooks':[self.GIT_RAILS_MANIFEST_HANDLER]}])
        for event in ('Stop', 'SubagentStop'):
            self.assertEqual(hooks[event], [{'hooks':[self.LOGGING_MANIFEST_HANDLER]}], event)

    def test_hook_git_rails_fresh_install_adds_one_owned_group_and_repeats_byte_identically(self) -> None:
        self.install()
        hooks = self.read_settings()['hooks']
        self.assertEqual(hooks.get('PreToolUse'), [{'matcher':'Bash', 'hooks':[self.git_rails_handler()]}])
        for event in ('Stop', 'SubagentStop'):
            self.assertEqual(hooks[event], [{'hooks':[self.logging_handler()]}], event)
        receipt = json.loads(self.receipt.read_text())
        self.assertIn({'event':'PreToolUse', 'selector':self.GIT_RAILS_SELECTOR,
                       'handler':self.git_rails_handler(), 'count':1}, receipt['owned'])
        self.assertIn({'event':'PreToolUse', 'selector':self.GIT_RAILS_SELECTOR, 'count':1},
                      receipt['created_groups'])
        self.assertEqual(len(receipt['owned']), 3)
        self.assertEqual(len(receipt['created_groups']), 3)
        first = self.snapshot()
        self.install()
        self.assertEqual(first, self.snapshot(), 'a second install must be byte-identical')
        self.call('uninstall', expected='uninstalled')
        self.assert_no_owned_handlers()
        self.assertFalse([group for groups in self.read_settings().get('hooks', {}).values() for group in groups])

    def test_hook_git_rails_install_without_hooks_key_creates_every_manifest_event(self) -> None:
        self.write_settings({'theme':'kept', 'nested':{'enabled':False}})
        self.install()
        value = self.read_settings()
        self.assertEqual(set(value['hooks']), {'PreToolUse', 'Stop', 'SubagentStop'})
        self.assertEqual((value['theme'], value['nested']), ('kept', {'enabled':False}))
        self.assert_registered()
        self.call('uninstall', expected='uninstalled')
        self.assert_settings_restored({'theme':'kept', 'nested':{'enabled':False}})

    def test_hook_git_rails_registration_uses_the_physical_entrypoint_beside_its_core(self) -> None:
        alias = self.root / 'source alias'
        alias.symlink_to(self.checkout, target_is_directory=True)
        self.call('install', '--from', str(alias))
        self.assert_registered()
        group = next(group for group in self.read_settings()['hooks'].get('PreToolUse', [])
                     if group.get('matcher') == 'Bash')
        entrypoint = Path(group['hooks'][0]['args'][0])
        self.assertEqual(entrypoint, self.checkout.resolve() / 'hooks' / 'git-rails.sh')
        self.assertFalse(entrypoint.is_symlink())
        self.assertTrue((entrypoint.parent / 'git_rails.py').is_file())
        handler = group['hooks'][0]
        irrelevant = subprocess.run([handler['command'], *handler['args']], input='{}', env=self.env,
                                    cwd=self.project, text=True, capture_output=True, timeout=15)
        self.assertEqual((irrelevant.returncode, irrelevant.stdout, irrelevant.stderr), (0, '', ''))
        subprocess.run(['git', 'init', '-q'], cwd=self.project, env=self.env, check=True, timeout=15)
        self.registry.parent.mkdir(parents=True, exist_ok=True)
        self.registry.write_text(str(self.project.resolve()) + '\n')
        event = {'session_id':'fixture', 'hook_event_name':'PreToolUse', 'tool_name':'Bash',
                 'tool_input':{'command':'git add -A', 'description':'fixture'},
                 'cwd':str(self.project.resolve()), 'permission_mode':'default'}
        decided = subprocess.run([handler['command'], *handler['args']], input=json.dumps(event), env=self.env,
                                 cwd=self.project, text=True, capture_output=True, timeout=30)
        self.assertNotIn("can't open file", decided.stderr)
        self.assertEqual(decided.returncode, 2, decided.stderr)
        self.assertIn('rule: rules/git-flow.md', decided.stderr, 'the registered entrypoint must reach its core')

    def test_hook_git_rails_symlinked_entrypoint_is_never_registered_alone(self) -> None:
        elsewhere = self.root / 'detached entrypoint'
        elsewhere.mkdir()
        entrypoint = self.checkout / 'hooks' / 'git-rails.sh'
        shutil.copy2(entrypoint, elsewhere / 'git-rails.sh')
        entrypoint.unlink()
        entrypoint.symlink_to(elsewhere / 'git-rails.sh')
        self.write_settings({'user':'kept'})
        before = self.snapshot()
        # The detached target has no core beside it, so no registration can be correct.
        data = self.call('install', expected='unavailable')
        self.assertEqual(data.get('reason'), 'invalid-source')
        self.assertEqual(before, self.snapshot(), 'a rejected source must leave settings and ownership untouched')
        entrypoint.unlink()
        shutil.copy2(elsewhere / 'git-rails.sh', entrypoint)
        self.install()
        self.assert_registered()

    def test_hook_git_rails_source_without_entrypoint_or_core_is_rejected_without_writes(self) -> None:
        self.write_settings({'user':'kept'})
        self.install()
        self.assert_registered()
        for missing in ('git-rails.sh', 'git_rails.py'):
            with self.subTest(missing=missing):
                alternate = self.root / ('source without ' + missing)
                self.copy_source(alternate)
                (alternate / 'hooks' / missing).unlink()
                before = self.snapshot()
                data = self.call('install', '--from', str(alternate), expected='unavailable')
                self.assertEqual(data.get('reason'), 'invalid-source')
                self.assertEqual(before, self.snapshot())

    def test_hook_git_rails_malformed_manifest_variants_are_rejected_without_writes(self) -> None:
        self.write_settings({'user':'kept'})
        self.install()
        self.assert_registered()
        valid = self.registered_manifest()
        def handler_variant(change: JsonObject | None = None, drop: str | None = None) -> JsonObject:
            variant = copy.deepcopy(valid)
            handler = variant['hooks']['PreToolUse'][0]['hooks'][0]
            handler.update(change or {})
            if drop is not None:
                handler.pop(drop)
            return variant
        extra_group = copy.deepcopy(valid)
        extra_group['hooks']['PreToolUse'].append(copy.deepcopy(extra_group['hooks']['PreToolUse'][0]))
        extra_handler = copy.deepcopy(valid)
        extra_handler['hooks']['PreToolUse'][0]['hooks'].append(copy.deepcopy(self.GIT_RAILS_MANIFEST_HANDLER))
        extra_group_key = copy.deepcopy(valid)
        extra_group_key['hooks']['PreToolUse'][0]['unexpected'] = True
        empty_event = copy.deepcopy(valid)
        empty_event['hooks']['PreToolUse'] = []
        variants: dict[str, JsonObject] = {
            'command': handler_variant({'command':'sh'}),
            'shell command': handler_variant({'command':'bash; echo invalid'}),
            'type': handler_variant({'type':'http'}),
            'missing script': handler_variant({'args':['@ORCHESTRAIL_HOME@/hooks/missing.sh']}),
            'unplaced path': handler_variant({'args':[str(self.checkout / 'hooks' / 'git-rails.sh')]}),
            'escaping path': handler_variant({'args':['@ORCHESTRAIL_HOME@/hooks/../scripts/install-hooks.sh']}),
            'extra argument': handler_variant({'args':['@ORCHESTRAIL_HOME@/hooks/git-rails.sh', '--extra']}),
            'string timeout': handler_variant({'timeout':'10'}),
            'extra field': handler_variant({'statusMessage':'checking'}),
            'missing timeout': handler_variant(drop='timeout'),
            'missing failure mode': handler_variant(drop='onFailure'),
            'extra group': extra_group, 'extra handler': extra_handler,
            'extra group field': extra_group_key, 'empty event': empty_event}
        for name, variant in variants.items():
            with self.subTest(variant=name):
                self.manifest_path().write_text(json.dumps(variant))
                before = self.snapshot()
                self.call('install', expected='unavailable')
                self.assertEqual(before, self.snapshot())

    def test_hook_git_rails_malformed_settings_never_receive_a_partial_registration(self) -> None:
        self.install()
        self.assert_registered()
        self.call('uninstall', expected='uninstalled')
        for contents in ('{"hooks":{"PreToolUse":{}}}', '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":"x"}]}}',
                         '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[null]}]}}', '{"hooks":{"PreToolUse":[7]}}'):
            with self.subTest(contents=contents):
                self.settings.write_text(contents)
                before = self.snapshot()
                self.call('install', expected='unavailable')
                self.assertEqual(before, self.snapshot())

    def test_hook_git_rails_foreign_pretooluse_entries_survive_install_and_removal(self) -> None:
        original: JsonObject = {'theme':'user', 'hooks':{'PreToolUse':[
            {'matcher':'Edit', 'hooks':[{'type':'command', 'command':'user-edit-hook'}]},
            {'matcher':'Bash', 'hooks':[{'type':'command', 'command':'user-bash-hook', 'timeout':5}]},
            {'matcher':'Bash|Edit', 'hooks':[{'type':'command', 'command':'user-both-hook'}]}]}}
        self.write_settings(original)
        self.install()
        value = self.read_settings()
        groups = value['hooks']['PreToolUse']
        self.assertEqual(len(groups), 3, 'a user group with the same matcher receives the handler')
        self.assertEqual(groups[1], {'matcher':'Bash', 'hooks':[{'type':'command', 'command':'user-bash-hook', 'timeout':5},
                                                              self.git_rails_handler()]})
        self.assertEqual((groups[0], groups[2]), (original['hooks']['PreToolUse'][0], original['hooks']['PreToolUse'][2]))
        receipt = json.loads(self.receipt.read_text())
        self.assertNotIn('PreToolUse', [claim['event'] for claim in receipt['created_groups']])
        first = self.snapshot()
        self.install()
        self.assertEqual(first, self.snapshot())
        self.call('uninstall', expected='uninstalled')
        self.assert_settings_restored(original)

    def test_hook_git_rails_identical_foreign_handlers_keep_multiset_quotas(self) -> None:
        self.install()
        self.assert_registered()
        value = self.read_settings()
        installed = value['hooks']['PreToolUse'][0]
        installed['hooks'].append(copy.deepcopy(installed['hooks'][0]))
        value['hooks']['PreToolUse'].append(copy.deepcopy(installed))
        self.write_settings(value)
        self.assertEqual(self.git_rails_occurrences(), 4)
        self.call('uninstall', expected='uninstalled')
        self.assertEqual(self.git_rails_occurrences(), 3, 'removal deletes only the one owned occurrence')
        self.assertEqual(len(self.read_settings()['hooks']['PreToolUse']), 2)
        preexisting: JsonObject = {'hooks':{'PreToolUse':[{'matcher':'Bash', 'hooks':[self.git_rails_handler()]}]},
                                   'other':17}
        self.write_settings(preexisting)
        self.receipt.unlink(missing_ok=True)
        self.install()
        self.assertEqual(self.git_rails_occurrences(), 1, 'an identical foreign handler is not duplicated')
        receipt = json.loads(self.receipt.read_text())
        self.assertNotIn('PreToolUse', [claim['event'] for claim in receipt['owned']])
        self.call('uninstall', expected='uninstalled')
        self.assert_settings_restored(preexisting)

    def test_hook_git_rails_logging_only_receipt_upgrades_on_reinstall(self) -> None:
        original = self.install_logging_only_state()
        self.install()
        value = self.read_settings()
        for event in ('Stop', 'SubagentStop'):
            self.assertEqual(value['hooks'][event], original['hooks'][event], event)
        self.assertEqual(value['hooks'].get('PreToolUse'), [{'matcher':'Bash', 'hooks':[self.git_rails_handler()]}])
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt['state'], 'committed')
        self.assertEqual(sorted(claim['event'] for claim in receipt['owned']), ['PreToolUse', 'Stop', 'SubagentStop'])
        self.assertEqual(sorted(claim['event'] for claim in receipt['created_groups']), ['PreToolUse', 'Stop', 'SubagentStop'])
        first = self.snapshot()
        self.install()
        self.assertEqual(first, self.snapshot())
        self.call('uninstall', expected='uninstalled')
        self.assert_no_owned_handlers()
        self.assertEqual(self.read_settings()['user'], 'kept')

    def test_hook_git_rails_registration_preserves_numeric_lexemes(self) -> None:
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        original = ('{"large":9007199254740993,"huge":1e400,"zero":-0,"hooks":{"PreToolUse":'
                    '[{"matcher":"Edit","hooks":[{"type":"command","command":"user","timeout":1e1}]}]}}')
        self.settings.write_text(original)
        tokens = {'large':'9007199254740993', 'huge':'1e400', 'zero':'-0', 'timeout':'1e1'}
        for operation, status in (('install', 'installed'), ('uninstall', 'uninstalled')):
            self.call(operation, expected=status)
            if operation == 'install':
                self.assert_registered()
            for field, token in tokens.items():
                self.assertRegex(self.settings.read_text(), '"' + field + r'"\s*:\s*' + re.escape(token) + r'(?=\s*[,}])',
                                 operation + ' must preserve the numeric token for ' + field)

    def test_hook_git_rails_interrupted_replacements_recover(self) -> None:
        env = self.interrupt_replacement(self.receipt)
        self.raw_call('install', env=env)
        prepared = json.loads(self.receipt.read_text())
        self.assertEqual((prepared['state'], prepared['before']), ('prepared', {'present':False, 'sha256':None}))
        self.assertFalse(self.settings.exists())
        self.install()
        self.assert_registered()
        self.assertEqual(json.loads(self.receipt.read_text())['state'], 'committed')
        self.call('uninstall', expected='uninstalled')
        env = self.interrupt_replacement(self.settings)
        self.raw_call('install', env=env)
        prepared = json.loads(self.receipt.read_text())
        self.assertEqual(prepared['state'], 'prepared')
        self.assertEqual(hashlib.sha256(self.settings.read_bytes()).hexdigest(), prepared['after']['sha256'])
        self.assert_registered()
        self.call('uninstall', expected='uninstalled')
        self.assert_no_owned_handlers()
        self.assertEqual(json.loads(self.receipt.read_text())['state'], 'committed')

    def test_hook_git_rails_concurrent_edit_during_registration_is_not_overwritten(self) -> None:
        self.install_logging_only_state()
        external = self.root / 'external-settings.json'
        external.write_text('{"external":"preserve this concurrent user edit"}')
        self.call('install', expected='unavailable', env=self.concurrent_editor_environment(external))
        self.assertEqual(self.settings.read_bytes(), external.read_bytes())
        self.assertEqual(json.loads(self.receipt.read_text())['state'], 'prepared')
        before = self.snapshot()
        self.call('uninstall', expected='unavailable')
        self.assertEqual(before, self.snapshot())

    def test_hook_git_rails_concurrent_operations_keep_one_owned_registration(self) -> None:
        self.install()
        self.assert_registered()
        def operation(index: int) -> subprocess.CompletedProcess[str]:
            return self.raw_call('install' if index % 3 else 'uninstall')
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(operation, range(16)))
        for result in results:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(json.loads(result.stdout)['status'], ('installed', 'uninstalled'))
        self.install()
        self.assert_registered()
        self.call('uninstall', expected='uninstalled')
        self.assert_no_owned_handlers()

    def test_hook_git_rails_uninstall_ignores_the_manifest_and_removes_owned_entries(self) -> None:
        self.write_settings({'user':'kept'})
        self.install()
        self.assert_registered()
        alternate = self.root / 'logging-only installer'
        self.copy_source(alternate)
        logging_only = {'hooks':{event:[{'hooks':[self.LOGGING_MANIFEST_HANDLER]}] for event in ('Stop', 'SubagentStop')}}
        self.manifest_path(alternate).write_text(json.dumps(logging_only))
        shutil.rmtree(self.checkout)
        self.call('uninstall', expected='uninstalled', checkout=alternate,
                  env=dict(self.env, ORCHESTRAIL_HOME=str(self.checkout)))
        self.assert_no_owned_handlers()
        self.assert_settings_restored({'user':'kept'})

    def test_hook_git_rails_changed_owned_handler_survives_removal(self) -> None:
        self.install()
        self.assert_registered()
        value = self.read_settings()
        changed = value['hooks']['PreToolUse'][0]['hooks'][0]
        changed['onFailure'] = 'continue'
        self.write_settings(value)
        self.call('uninstall', expected='uninstalled')
        self.assertEqual(self.read_settings()['hooks']['PreToolUse'], [{'matcher':'Bash', 'hooks':[changed]}])
        self.install()
        self.assertEqual(self.read_settings()['hooks']['PreToolUse'],
                         [{'matcher':'Bash', 'hooks':[changed, self.git_rails_handler()]}])

    def test_hook_git_rails_fail_open_pretooluse_handler_is_rejected_without_writes(self) -> None:
        self.write_settings({'user':'kept'})
        self.install()
        self.assert_registered()
        valid = self.registered_manifest()
        continuing = copy.deepcopy(valid)
        continuing['hooks']['PreToolUse'][0]['hooks'][0]['onFailure'] = 'continue'
        undeclared = copy.deepcopy(valid)
        undeclared['hooks']['PreToolUse'][0]['hooks'][0].pop('onFailure')
        for name, variant in (('continue', continuing), ('missing', undeclared)):
            with self.subTest(failure_mode=name):
                self.manifest_path().write_text(json.dumps(variant))
                before = self.snapshot()
                self.call('install', expected='unavailable')
                self.assertEqual(before, self.snapshot())

    def test_hook_git_rails_pretooluse_group_without_matcher_is_rejected_without_writes(self) -> None:
        self.write_settings({'user':'kept'})
        self.install()
        self.assert_registered()
        variant = copy.deepcopy(self.registered_manifest())
        variant['hooks']['PreToolUse'][0].pop('matcher')
        self.manifest_path().write_text(json.dumps(variant))
        before = self.snapshot()
        self.call('install', expected='unavailable')
        self.assertEqual(before, self.snapshot())

    # The permission fragment is defence in depth beside the hook: exact Bash deny rules
    # for blanket staging and commit-all only, owned through exact multiset quotas.
    # Each rule maps to (matching command, legitimate non-matching command, hook reason).
    PERMISSION_FIXTURES: dict[str, tuple[str, str, str]] = {
        'Bash(git add -A)': ('git add -A', 'git add -- -A', 'blanket-staging (R01)'),
        'Bash(git add --all)': ('git add --all', 'git add -- --all', 'blanket-staging (R01)'),
        'Bash(git add .)': ('git add .', 'git add ./notes.txt', 'blanket-staging (R01)'),
        'Bash(git commit -a)': ('git commit -a', "git commit -m 'stage all with -a'", 'commit-all (R06)'),
        'Bash(git commit --all)': ('git commit --all', 'git commit --allow-empty -m empty', 'commit-all (R06)')}
    LEGITIMATE_COMMANDS = ('git add .gitignore', 'git add ./notes.txt', 'git add .github/ci.yml', 'git add notes.txt',
                           'git add -- -A', 'git add -- --all', "git commit -m 'add all'", 'git commit --amend --no-edit',
                           'git commit --allow-empty -m empty', 'git status', 'git add .gitignore && git commit -m ignore')
    PERMISSION_OPERATORS = ('&&', '||', '|&', ';', '|', '&', '\n')
    PERMISSION_PREFIXES = (re.compile(r'[A-Za-z_][A-Za-z0-9_]*=\S*\s+'),
                           re.compile(r'(?:timeout\s+\S+|time|nice|nohup|stdbuf|command|builtin|noglob|xargs)\s+'))

    @classmethod
    def permission_subcommands(cls, command: str) -> list[str]:
        """Split on the recorded compound operators outside quotes."""
        parts, current, quote, index = [], '', '', 0
        while index < len(command):
            character = command[index]
            operator = '' if quote else next((item for item in cls.PERMISSION_OPERATORS
                                              if command.startswith(item, index)), '')
            if operator:
                parts.append(current)
                current, index = '', index + len(operator)
                continue
            if character in '\'"' and quote in ('', character):
                quote = '' if quote else character
            current, index = current + character, index + 1
        parts.append(current)
        return [part.strip() for part in parts if part.strip()]

    @classmethod
    def permission_rule_matches(cls, rule: str, command: str) -> bool:
        """Offline model of the recorded Bash rule semantics: exact, or prefix for ' *' and ':*'."""
        body = re.fullmatch(r'Bash\((.+)\)', rule, re.S)
        assert body is not None, rule
        pattern = body.group(1)
        prefix = pattern[:-2] if pattern.endswith((' *', ':*')) else None
        for part in cls.permission_subcommands(command):
            stripped = True
            while stripped:
                found = next((match for match in (item.match(part) for item in cls.PERMISSION_PREFIXES) if match), None)
                stripped = found is not None
                part = part[found.end():] if found is not None else part
            if part == pattern if prefix is None else (part == prefix or part.startswith(prefix + ' ')):
                return True
        return False

    def fragment_path(self, source: Path | None = None) -> Path:
        return (source or self.checkout) / 'harness' / 'claude' / 'permissions.json'

    def fragment_rules(self) -> list[str]:
        path = self.fragment_path()
        self.assertTrue(path.is_file(), 'the permission fragment harness/claude/permissions.json must exist')
        return json.loads(path.read_text())['permissions']['deny']

    def permission_claims(self, rules: list[str]) -> list[JsonObject]:
        return sorted(({'list':'deny', 'rule':rule, 'count':1} for rule in rules), key=lambda claim: str(claim['rule']))

    def owned_permission_claims(self) -> list[JsonObject]:
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt.get('schema_version'), 2, 'the receipt must be schema version 2')
        self.assertIn('owned_permissions', receipt)
        return sorted(receipt['owned_permissions'], key=lambda claim: str(claim['rule']))

    def deny_rules(self) -> list[JsonValue]:
        return self.read_settings().get('permissions', {}).get('deny', [])

    def install_version_one_state(self, foreign: JsonObject | None = None) -> tuple[JsonObject, JsonObject]:
        """Settings and a committed version 1 receipt exactly as the previous installer left them."""
        handlers = {'PreToolUse':self.git_rails_handler(), 'Stop':self.logging_handler(),
                    'SubagentStop':self.logging_handler()}
        selectors: dict[str, JsonObject] = {'PreToolUse':self.GIT_RAILS_SELECTOR, 'Stop':{}, 'SubagentStop':{}}
        if foreign is None:
            foreign = {'user':'kept', 'permissions':{'allow':['Bash(git status)'], 'deny':['Bash(git add -A)']}}
        settings = dict(copy.deepcopy(foreign), hooks={event:[dict(selectors[event], hooks=[handler])]
                                                       for event, handler in handlers.items()})
        self.write_settings(settings)
        receipt: JsonObject = {'schema_version':1, 'state':'committed',
            'owned':[{'event':event, 'selector':selectors[event], 'handler':handler, 'count':1}
                     for event, handler in handlers.items()],
            'created_groups':[{'event':event, 'selector':selectors[event], 'count':1} for event in handlers]}
        self.receipt.parent.mkdir(parents=True, exist_ok=True)
        self.receipt.write_text(json.dumps(receipt))
        return foreign, receipt

    def assert_one_owned_handler_per_event(self) -> None:
        hooks = self.read_settings()['hooks']
        self.assertEqual(hooks['PreToolUse'], [{'matcher':'Bash', 'hooks':[self.git_rails_handler()]}])
        for event in ('Stop', 'SubagentStop'):
            self.assertEqual(hooks[event], [{'hooks':[self.logging_handler()]}], event)

    def git_rails_decision(self, repository: Path, command: str) -> subprocess.CompletedProcess[str]:
        event = {'session_id':'fixture', 'hook_event_name':'PreToolUse', 'tool_name':'Bash',
                 'tool_input':{'command':command, 'description':'fixture'},
                 'cwd':str(repository.resolve()), 'permission_mode':'default'}
        return subprocess.run(['bash', str(self.checkout / 'hooks' / 'git-rails.sh')], input=json.dumps(event),
                              env=dict(self.env, PYTHONDONTWRITEBYTECODE='1'), cwd=repository,
                              text=True, capture_output=True, timeout=30)

    def test_hook_permissions_fragment_holds_only_exact_staging_and_commit_all_rules(self) -> None:
        claude = (self.checkout / 'harness' / 'claude' / 'capabilities.md').read_text()
        for line in ('deny-rule exact: Bash(<command>) matches only that whole command text',
                     'deny-rule prefix: Bash(<command> *) and the equivalent trailing Bash(<command>:*)'):
            self.assertIn(line, claude, 'the fixtures follow the recorded match semantics')
        for rule, command, expected in (('Bash(git add .)', 'git add .gitignore', False),
                                        ('Bash(npm run *)', 'npm run', True), ('Bash(npm run *)', 'npm run test', True),
                                        ('Bash(npm run *)', 'npm runx', False), ('Bash(npm run:*)', 'npm run test', True),
                                        ('Bash(git add -A)', 'git status && git add -A', True),
                                        ('Bash(git add -A)', 'FIXTURE=1 timeout 5 git add -A', True),
                                        ('Bash(git add -A)', "echo 'git add -A; ok'", False)):
            with self.subTest(matcher=rule, command=command):
                self.assertIs(self.permission_rule_matches(rule, command), expected)
        path = self.fragment_path()
        self.assertTrue(path.is_file(), 'the permission fragment harness/claude/permissions.json must exist')
        document = json.loads(path.read_text())
        self.assertEqual(set(document), {'permissions'})
        self.assertEqual(set(document['permissions']), {'deny'}, 'the fragment holds deny rules only')
        rules = document['permissions']['deny']
        self.assertEqual(len(rules), len(set(rules)))
        self.assertEqual(set(rules), set(self.PERMISSION_FIXTURES), 'only blanket-staging and commit-all rules')
        for rule in rules:
            matching, legitimate, _reason = self.PERMISSION_FIXTURES[rule]
            with self.subTest(rule=rule):
                self.assertNotRegex(rule, r'(?: \*|:\*)\)$', 'exact forms only')
                for positive in (matching, 'FIXTURE=1 ' + matching, 'git status; ' + matching):
                    self.assertTrue(self.permission_rule_matches(rule, positive), positive)
                self.assertFalse(self.permission_rule_matches(rule, legitimate), legitimate)
                for command in self.LEGITIMATE_COMMANDS:
                    self.assertFalse(self.permission_rule_matches(rule, command), command)

    def test_hook_permissions_fixtures_are_hook_denials_and_negatives_are_not(self) -> None:
        repository = self.root / 'fixture repository'
        repository.mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=repository, env=self.env, check=True, timeout=15)
        for name in ('.gitignore', 'notes.txt', '-A', '--all'):
            (repository / name).write_text('fixture\n')
        self.registry.parent.mkdir(parents=True, exist_ok=True)
        self.registry.write_text(str(repository.resolve()) + '\n')
        rules = self.fragment_rules()
        for rule in rules:
            matching, legitimate, reason = self.PERMISSION_FIXTURES[rule]
            with self.subTest(rule=rule):
                denied = self.git_rails_decision(repository, matching)
                self.assertEqual(denied.returncode, 2, denied.stderr)
                self.assertEqual(denied.stderr.splitlines()[0], 'git-rails: deny ' + reason)
                allowed = self.git_rails_decision(repository, legitimate)
                self.assertNotRegex(allowed.stderr, r'\((?:R01|R06)\)', legitimate)
        gitignore = self.git_rails_decision(repository, 'git add .gitignore')
        self.assertEqual((gitignore.returncode, gitignore.stdout, gitignore.stderr), (0, '', ''))

    def test_hook_permissions_install_adds_owned_deny_rules_with_version_two_receipt(self) -> None:
        self.write_settings({'user':'kept'})
        self.install()
        rules = self.fragment_rules()
        self.assertEqual(self.read_settings()['permissions'], {'deny':rules})
        self.assertEqual(self.owned_permission_claims(), self.permission_claims(rules))
        first = self.snapshot()
        self.install()
        self.assertEqual(first, self.snapshot(), 'a second install must be byte-identical')
        alternate = self.root / 'switched source'
        self.copy_source(alternate)
        self.call('install', '--from', str(alternate))
        self.assertEqual(self.deny_rules(), rules, 'reinstalling from another source keeps one copy of each rule')
        self.assertEqual(self.owned_permission_claims(), self.permission_claims(rules))
        self.call('uninstall', expected='uninstalled')
        self.assert_settings_restored({'user':'kept'})
        receipt = json.loads(self.receipt.read_text()) if self.receipt.exists() else {}
        self.assertEqual(receipt.get('owned_permissions', []), [])

    def test_hook_permissions_foreign_rules_and_other_lists_survive_in_order(self) -> None:
        original_text = ('{"other":1.50,"permissions":{"allow":["Bash(git status)","Bash(ls *)"],'
                         '"ask":["Bash(git push *)"],"deny":["Bash(rm -rf *)","Bash(git add -A)"],'
                         '"defaultMode":"default"}}')
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.settings.write_text(original_text)
        original = self.read_settings()
        self.install()
        rules = self.fragment_rules()
        added = [rule for rule in rules if rule != 'Bash(git add -A)']
        value = self.read_settings()
        self.assertEqual(value['permissions']['deny'], ['Bash(rm -rf *)', 'Bash(git add -A)', *added])
        for name in ('allow', 'ask', 'defaultMode'):
            self.assertEqual(value['permissions'][name], original['permissions'][name], name)
        self.assertRegex(self.settings.read_text(), r'"other"\s*:\s*1\.50(?=\s*[,}])')
        self.assertEqual(self.owned_permission_claims(), self.permission_claims(added),
                         'an identical foreign rule is neither duplicated nor owned')
        first = self.snapshot()
        self.install()
        self.assertEqual(first, self.snapshot())
        self.call('uninstall', expected='uninstalled')
        self.assert_settings_restored(original)

    def test_hook_permissions_quota_keeps_identical_user_copies_and_tolerates_removed_rules(self) -> None:
        self.install()
        rules = self.fragment_rules()
        value = self.read_settings()
        value['permissions']['deny'] = [rule for rule in rules if rule != 'Bash(git add .)']
        value['permissions']['deny'] += ['Bash(git commit -a)', 'Bash(curl *)']
        self.write_settings(value)
        self.call('uninstall', expected='uninstalled')
        self.assertEqual(self.deny_rules(), ['Bash(git commit -a)', 'Bash(curl *)'],
                         'removal deletes one owned occurrence per claim and keeps every foreign rule')
        self.install()
        deny = self.deny_rules()
        self.assertEqual(sorted(deny, key=str), sorted([*rules, 'Bash(curl *)'], key=str))
        self.assertEqual(self.owned_permission_claims(),
                         self.permission_claims([rule for rule in rules if rule != 'Bash(git commit -a)']))
        self.call('uninstall', expected='uninstalled')
        self.assertEqual(self.deny_rules(), ['Bash(git commit -a)', 'Bash(curl *)'])

    def test_hook_permissions_missing_or_empty_containers_are_restored_exactly(self) -> None:
        for original in ({}, {'permissions':{'allow':['Bash(ls)']}}, {'permissions':{}},
                         {'permissions':{'deny':[]}}, {'permissions':{'deny':[], 'allow':[]}}):
            with self.subTest(original=original):
                self.write_settings(original)
                self.receipt.unlink(missing_ok=True)
                self.install()
                self.assertEqual(self.deny_rules(), self.fragment_rules())
                for name, items in original.get('permissions', {}).items():
                    if name != 'deny':
                        self.assertEqual(self.read_settings()['permissions'][name], items, name)
                self.call('uninstall', expected='uninstalled')
                self.assert_settings_restored(original)

    def test_hook_permissions_malformed_settings_are_rejected_without_writes(self) -> None:
        self.write_settings({'user':'kept'})
        self.install()
        self.assertEqual(self.deny_rules(), self.fragment_rules())
        installed = self.read_settings()
        installed_receipt = self.receipt.read_bytes()
        for permissions in ([], None, 'deny', {'deny':'Bash(git add -A)'}, {'deny':{}}, {'deny':None}, {'deny':[7]}):
            with self.subTest(permissions=permissions):
                self.write_settings(dict(installed, permissions=permissions))
                before = self.snapshot()
                self.call('install', expected='unavailable')
                self.assertEqual(before, self.snapshot())
                self.call('uninstall', expected='unavailable')
                self.assertEqual(before, self.snapshot())
                self.receipt.unlink()
                self.call('install', expected='unavailable')
                self.assertEqual(before[0], self.settings.read_bytes())
                self.assertFalse(self.receipt.exists())
                self.write_settings(installed)
                self.receipt.write_bytes(installed_receipt)

    def test_hook_permissions_malformed_fragment_is_rejected_without_writes(self) -> None:
        self.write_settings({'user':'kept'})
        self.install()
        rules = self.fragment_rules()
        self.assertEqual(self.deny_rules(), rules)
        def fragment(deny: JsonValue, **extra: JsonValue) -> str:
            return json.dumps({'permissions':dict({'deny':deny}, **extra)})
        variants: dict[str, str] = {
            'not json': '{broken', 'array root': '[]', 'null root': 'null',
            'extra top-level key': json.dumps({'permissions':{'deny':rules}, 'hooks':{}}),
            'allow list': fragment(rules, allow=['Bash(git status)']),
            'ask list': fragment(rules, ask=['Bash(git push *)']),
            'deny not a list': fragment('Bash(git add -A)'), 'empty deny': fragment([]),
            'non-string rule': fragment([*rules, 7]), 'duplicate rule': fragment([*rules, rules[0]]),
            'non-Bash rule': fragment([*rules, 'Read(./.env)']), 'empty Bash rule': fragment([*rules, 'Bash()']),
            'control character': fragment([*rules, 'Bash(git add -A\n)']),
            'duplicate key': '{"permissions":{"deny":[],"deny":' + json.dumps(rules) + '}}'}
        for name, contents in variants.items():
            with self.subTest(variant=name):
                self.fragment_path().write_text(contents)
                before = self.snapshot()
                data = self.call('install', expected='unavailable')
                self.assertEqual(data.get('reason'), 'invalid-manifest')
                self.assertEqual(before, self.snapshot())
        self.fragment_path().unlink()
        before = self.snapshot()
        data = self.call('install', expected='unavailable')
        self.assertEqual(data.get('reason'), 'invalid-source')
        self.assertEqual(before, self.snapshot())
        self.call('uninstall', expected='uninstalled')
        self.assert_settings_restored({'user':'kept'})

    def test_hook_permissions_receipt_claims_are_validated_before_use(self) -> None:
        self.write_settings({'user':'kept'})
        self.install()
        valid = json.loads(self.receipt.read_text())
        self.assertEqual(valid.get('schema_version'), 2)
        self.assertTrue(valid.get('owned_permissions'))
        claim = valid['owned_permissions'][0]
        def variant(owned: JsonValue, version: JsonValue = 2) -> JsonObject:
            return dict(copy.deepcopy(valid), schema_version=version, owned_permissions=owned)
        missing = copy.deepcopy(valid)
        missing.pop('owned_permissions')
        variants: dict[str, JsonObject] = {
            'not a list': variant({}), 'missing count': variant([{'list':'deny', 'rule':claim['rule']}]),
            'zero count': variant([dict(claim, count=0)]), 'fractional count': variant([dict(claim, count=1.5)]),
            'extra field': variant([dict(claim, origin='user')]), 'other list': variant([dict(claim, list='allow')]),
            'non-string rule': variant([dict(claim, rule=7)]), 'duplicate claim': variant([claim, claim]),
            'version 2 without claims': missing, 'version 1 with claims': variant(valid['owned_permissions'], 1),
            'unknown version': variant(valid['owned_permissions'], 3)}
        for name, receipt in variants.items():
            with self.subTest(variant=name):
                self.receipt.write_text(json.dumps(receipt))
                before = self.snapshot()
                self.call('install', expected='unavailable')
                self.assertEqual(before, self.snapshot())
                self.call('uninstall', expected='unavailable')
                self.assertEqual(before, self.snapshot())
        self.receipt.write_text(json.dumps(valid))
        self.call('uninstall', expected='uninstalled')
        self.assert_settings_restored({'user':'kept'})

    def test_hook_permissions_version_one_receipt_is_read_and_migrated(self) -> None:
        foreign, _receipt = self.install_version_one_state()
        self.call('uninstall', expected='uninstalled')
        self.assert_settings_restored(foreign)
        foreign, _receipt = self.install_version_one_state()
        self.install()
        self.assert_one_owned_handler_per_event()
        rules = self.fragment_rules()
        added = [rule for rule in rules if rule != 'Bash(git add -A)']
        value = self.read_settings()
        self.assertEqual(value['permissions'], {'allow':['Bash(git status)'], 'deny':['Bash(git add -A)', *added]})
        self.assertEqual(self.owned_permission_claims(), self.permission_claims(added))
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual((len(receipt['owned']), len(receipt['created_groups'])), (3, 3))
        first = self.snapshot()
        self.install()
        self.assertEqual(first, self.snapshot(), 'a migrated installation repeats byte-identically')
        self.call('uninstall', expected='uninstalled')
        self.assert_no_owned_handlers()
        self.assert_settings_restored(foreign)

    def test_hook_permissions_prepared_version_one_receipt_recovers_then_migrates(self) -> None:
        for image in ('before', 'after'):
            with self.subTest(image=image):
                self.install_logging_only_state()
                before_settings = self.settings.read_bytes()
                previous = json.loads(self.receipt.read_text())
                _foreign, committed = self.install_version_one_state({'user':'kept'})
                after_settings = self.settings.read_bytes()
                prepared = {'schema_version':1, 'state':'prepared', 'previous':previous, 'next':committed,
                            'before':{'present':True, 'sha256':hashlib.sha256(before_settings).hexdigest()},
                            'after':{'present':True, 'sha256':hashlib.sha256(after_settings).hexdigest()}}
                self.receipt.write_text(json.dumps(prepared))
                self.settings.write_bytes(before_settings if image == 'before' else after_settings)
                self.install()
                self.assert_one_owned_handler_per_event()
                self.assertEqual(self.deny_rules(), self.fragment_rules())
                self.assertEqual(json.loads(self.receipt.read_text())['state'], 'committed')
                self.assertEqual(self.owned_permission_claims(), self.permission_claims(self.fragment_rules()))
                self.call('uninstall', expected='uninstalled')
                self.assert_no_owned_handlers()
                self.assert_settings_restored({'user':'kept'})

    def test_hook_permissions_interrupted_migration_recovers_from_either_image(self) -> None:
        self.install_version_one_state()
        original = self.settings.read_bytes()
        self.raw_call('install', env=self.interrupt_replacement(self.receipt))
        prepared = json.loads(self.receipt.read_text())
        self.assertEqual((prepared['state'], prepared['schema_version']), ('prepared', 2))
        self.assertEqual((prepared['previous']['schema_version'], prepared['next']['schema_version']), (1, 2))
        self.assertTrue(prepared['next']['owned_permissions'])
        self.assertEqual(original, self.settings.read_bytes())
        self.install()
        self.assert_one_owned_handler_per_event()
        self.assertEqual(sorted(self.deny_rules(), key=str), sorted(self.fragment_rules(), key=str))
        foreign, _receipt = self.install_version_one_state()
        self.raw_call('install', env=self.interrupt_replacement(self.settings))
        prepared = json.loads(self.receipt.read_text())
        self.assertEqual(prepared['state'], 'prepared')
        self.assertEqual(hashlib.sha256(self.settings.read_bytes()).hexdigest(), prepared['after']['sha256'])
        self.assertEqual(sorted(self.deny_rules(), key=str), sorted(self.fragment_rules(), key=str))
        self.call('uninstall', expected='uninstalled')
        self.assert_no_owned_handlers()
        self.assert_settings_restored(foreign)

    def test_hook_permissions_concurrent_edit_is_not_overwritten(self) -> None:
        self.install_version_one_state()
        external = self.root / 'external-settings.json'
        external.write_text('{"external":"preserve this concurrent user edit","permissions":{"deny":["Bash(x)"]}}')
        self.call('install', expected='unavailable', env=self.concurrent_editor_environment(external))
        self.assertEqual(self.settings.read_bytes(), external.read_bytes())
        prepared = json.loads(self.receipt.read_text())
        self.assertEqual(prepared['state'], 'prepared')
        self.assertTrue(prepared['next'].get('owned_permissions'), 'the transaction carries the owned deny rules')
        before = self.snapshot()
        for operation in ('install', 'uninstall'):
            self.call(operation, expected='unavailable')
            self.assertEqual(before, self.snapshot())

    def test_hook_permissions_concurrent_operations_keep_one_copy_of_each_rule(self) -> None:
        self.install()
        def operation(index: int) -> subprocess.CompletedProcess[str]:
            return self.raw_call('install' if index % 3 else 'uninstall')
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(operation, range(16)))
        for result in results:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(json.loads(result.stdout)['status'], ('installed', 'uninstalled'))
        self.install()
        self.assertEqual(self.deny_rules(), self.fragment_rules())
        self.call('uninstall', expected='uninstalled')
        self.assertNotIn('permissions', self.read_settings())

    def test_hook_permissions_uninstall_ignores_the_fragment(self) -> None:
        self.write_settings({'user':'kept', 'permissions':{'allow':['Bash(ls)']}})
        self.install()
        self.assertEqual(self.deny_rules(), self.fragment_rules())
        alternate = self.root / 'installer without fragment'
        self.copy_source(alternate)
        self.fragment_path(alternate).write_text('{broken')
        shutil.rmtree(self.checkout)
        self.call('uninstall', expected='uninstalled', checkout=alternate,
                  env=dict(self.env, ORCHESTRAIL_HOME=str(self.checkout)))
        self.assert_no_owned_handlers()
        self.assert_settings_restored({'user':'kept', 'permissions':{'allow':['Bash(ls)']}})

suite =unittest.TestSuite(HookInstallation(name) for name in SELECTED) if SELECTED else unittest.defaultTestLoader.loadTestsFromTestCase(HookInstallation)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
PY
