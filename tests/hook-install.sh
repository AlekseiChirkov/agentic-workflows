#!/usr/bin/env bash
# Exercise user hook installation and deployment in disposable roots only.
# Usage: bash tests/hook-install.sh [test-name ...]. Never deploys to the real home.
set -uo pipefail
install_test_source="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
python3 - "$install_test_source" "$@" <<'PY'
import concurrent.futures
import copy
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(sys.argv[1])
SELECTED = sys.argv[2:]

class HookInstallation(unittest.TestCase):
    def setUp(self):
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

    def copy_source(self, target):
        for folder in ('scripts', 'hooks', 'harness', 'rules', 'workflows', 'principles', 'templates'):
            if (SOURCE / folder).exists():
                shutil.copytree(SOURCE / folder, target / folder)

    def write_settings(self, value):
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.settings.write_text(json.dumps(value, ensure_ascii=False))

    def read_settings(self):
        return json.loads(self.settings.read_text(), parse_float=Decimal)

    def assert_user_settings_preserved(self, expected):
        actual = self.read_settings()
        # Receipts track handler/group provenance. An empty manifest event array
        # or hooks object can remain when that container was originally absent.
        hooks = actual.get('hooks', {})
        expected_hooks = expected.get('hooks', {})
        for event in ('Stop', 'SubagentStop'):
            if event not in expected_hooks and hooks.get(event) == []:
                del hooks[event]
        if 'hooks' not in expected and actual.get('hooks') == {}:
            del actual['hooks']
        self.assertEqual(expected, actual)

    def raw_call(self, *args, env=None, checkout=None):
        installer = (checkout or self.checkout) / 'scripts' / 'install-hooks.sh'
        # Absent capability is an empty result so RED asserts the missing protocol,
        # rather than a command-not-found or fixture error.
        command = ['bash', str(installer), *args] if installer.exists() else ['bash', '-c', ':']
        return subprocess.run(command, cwd=self.project, env=env or self.env,
                              text=True, capture_output=True, timeout=15)

    def call(self, *args, expected='installed', env=None, checkout=None):
        result = self.raw_call(*args, env=env, checkout=checkout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1,
                         'installer must publish one structured lifecycle result')
        data = json.loads(result.stdout)
        self.assertEqual(data.get('status'), expected, result.stdout + result.stderr)
        self.assertLess(len(result.stderr.encode()), 4096, 'diagnostics must stay bounded')
        return data

    def install(self, **kwargs):
        return self.call('install', **kwargs)

    def owned_groups(self):
        value = self.read_settings()
        self.assertEqual(set(value['hooks']), {'Stop', 'SubagentStop'})
        for event, groups in value['hooks'].items():
            self.assertEqual(len(groups), 1, event)
            self.assertEqual(len(groups[0]['hooks']), 1, event)
        return value['hooks']

    def snapshot(self):
        return tuple(path.read_bytes() if path.exists() else None
                     for path in (self.settings, self.receipt, self.registry))

    def setup_project(self, cwd=None, env=None):
        result = subprocess.run(['bash', str(self.checkout / 'scripts' / 'setup-new-project.sh')],
                                cwd=cwd or self.project, env=env or self.env, input='2\n',
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def sync(self):
        # Replace only validation in this private source copy to avoid recursively
        # invoking these integration fixtures during the real deployment script.
        (self.checkout / 'scripts' / 'validate-contracts.sh').write_text('#!/bin/bash\nexit 0\n')
        result = subprocess.run(['bash', str(self.checkout / 'scripts' / 'sync.sh'),
                                 '--from', str(self.checkout)], cwd=self.project,
                                env=self.env, text=True, capture_output=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def prepare_upgrade(self, image='before'):
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
            self.assertEqual(receipt['schema_version'], 1)
            self.assertEqual(receipt['state'], 'committed')
        prepared = {'schema_version':1, 'state':'prepared', 'previous':previous, 'next':next_receipt,
                    'before':{'present':True, 'sha256':hashlib.sha256(before_settings).hexdigest()},
                    'after':{'present':True, 'sha256':hashlib.sha256(after_settings).hexdigest()}}
        self.receipt.write_text(json.dumps(prepared))
        self.settings.write_bytes(before_settings if image == 'before' else after_settings)
        return alternate, prepared

    def interrupt_replacement(self, destination):
        faults = self.root / ('interrupt-' + destination.name)
        faults.mkdir()
        (faults / 'sitecustomize.py').write_text(
            'import os\nfrom pathlib import Path\n'
            'def wrap(original):\n'
            '    def replacement(src, dst, *args, **kwargs):\n'
            '        result = original(src, dst, *args, **kwargs)\n'
            '        if Path(dst).resolve() == Path(os.environ["HOOK_TEST_DEST"]).resolve():\n'
            '            os._exit(91)\n'
            '        return result\n'
            '    return replacement\n'
            'os.replace = wrap(os.replace)\nos.rename = wrap(os.rename)\n')
        return dict(self.env, PYTHONPATH=str(faults), HOOK_TEST_DEST=str(destination))

    def test_hook_install_repeated_lifecycle_preserves_unrelated_settings(self):
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

    def test_hook_install_preexisting_identical_entries_remain_unowned(self):
        self.install()
        hooks = self.owned_groups()
        self.call('uninstall', expected='uninstalled')
        original = {'hooks': hooks, 'other': 17}
        self.write_settings(original)
        self.install()
        self.call('uninstall', expected='uninstalled')
        self.assertEqual(original, self.read_settings())

    def test_hook_uninstall_changed_and_moved_entries_survive(self):
        self.install()
        value = self.read_settings()
        handler = value['hooks']['Stop'][0]['hooks'][0]
        handler['timeout'] = 29
        moved = value['hooks'].pop('SubagentStop')
        moved[0]['matcher'] = 'user-selected'
        value['hooks']['PreToolUse'] = moved
        self.write_settings(value)
        self.call('uninstall', expected='uninstalled')
        self.assertEqual(value, self.read_settings())

    def test_hook_uninstall_equal_copies_preserve_unowned_multiplicity_and_empty_groups(self):
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

    def test_hook_uninstall_removes_only_created_newly_empty_groups(self):
        self.install()
        value = self.read_settings()
        original_group = copy.deepcopy(value['hooks']['Stop'][0])
        value['hooks']['Stop'].append(copy.deepcopy(original_group))
        value['hooks']['Stop'].append({'hooks':[]})
        self.write_settings(value)
        self.call('uninstall', expected='uninstalled')
        groups = self.read_settings()['hooks']['Stop']
        self.assertEqual(groups, [original_group, {'hooks':[]}])

    def test_hook_install_source_precedence_and_quoted_paths_use_literal_arguments(self):
        alternate = self.root / 'alternate "quoted" source'
        self.copy_source(alternate)
        env = dict(self.env, ORCHESTRAIL_HOME=str(self.root / 'absent'))
        self.call('install', '--from', os.path.relpath(alternate, self.project), env=env)
        hooks = self.owned_groups()
        for groups in hooks.values():
            handler = groups[0]['hooks'][0]
            self.assertEqual(handler['command'], 'bash')
            self.assertEqual(handler['args'], [str(alternate / 'hooks' / 'log-step-hook.sh')])
            result = subprocess.run([handler['command'], *handler['args']], input='{}',
                                    env=self.env, cwd=self.project, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0)
        self.call('install', '--from=' + str(self.checkout), env=env)
        for groups in self.owned_groups().values():
            self.assertEqual(groups[0]['hooks'][0]['args'], [str(self.checkout / 'hooks' / 'log-step-hook.sh')])
        self.call('uninstall', expected='uninstalled', env=env)
        self.call('install', env=dict(self.env, ORCHESTRAIL_HOME=str(alternate)))
        for groups in self.owned_groups().values():
            self.assertEqual(groups[0]['hooks'][0]['args'], [str(alternate / 'hooks' / 'log-step-hook.sh')])
        self.call('uninstall', expected='uninstalled')
        self.call('install', env=dict(self.env, ORCHESTRAIL_HOME=''))

    def test_hook_install_invalid_cli_and_manifest_never_mutate_settings(self):
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

    def test_hook_install_upgrade_preserves_changed_old_handler(self):
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

    def test_hook_install_malformed_settings_preserve_exact_bytes(self):
        for contents in ('{broken secret', '[]', '{"hooks":[]}', '{"hooks":{"Stop":[{"hooks":null}]}}',
                         '{"hooks":{"Stop":[{"hooks":[4]}]}}', '{"a":1,"a":2}'):
            with self.subTest(contents=contents):
                self.settings.parent.mkdir(parents=True, exist_ok=True)
                self.settings.write_text(contents)
                before = self.snapshot()
                self.call('install', expected='unavailable')
                self.assertEqual(before, self.snapshot())

    def test_hook_install_malformed_receipt_preserves_both_files(self):
        self.install()
        for contents in ('{broken', '[]', '{}', '{"schema_version":1,"owned":"wrong"}'):
            with self.subTest(contents=contents):
                self.receipt.write_text(contents)
                before = self.snapshot()
                self.call('install', expected='unavailable')
                self.assertEqual(before, self.snapshot())
                self.call('uninstall', expected='unavailable')
                self.assertEqual(before, self.snapshot())

    def test_hook_receipt_control_numbers_cannot_gain_deletion_ownership(self):
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
        self.receipt.write_text(valid_text.replace('"schema_version":1', '"schema_version":1e0'))
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

    def test_hook_ownership_object_equality_ignores_key_order_and_numeric_spelling(self):
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

    def test_hook_ownership_omitted_fields_and_changed_argument_arrays_remain_unowned(self):
        self.install()
        value = self.read_settings()
        value['hooks']['Stop'][0]['hooks'][0].pop('onFailure')
        value['hooks']['SubagentStop'][0]['hooks'][0]['args'].append('--user-argument')
        self.write_settings(value)
        self.call('uninstall', expected='uninstalled')
        self.assertEqual(self.read_settings(), value)

    def test_hook_recovery_before_image_restores_previous_then_recomputes_install(self):
        alternate, prepared = self.prepare_upgrade('before')
        self.call('install', '--from', str(alternate))
        self.assertEqual(json.loads(self.receipt.read_text()), prepared['next'])
        for groups in self.owned_groups().values():
            self.assertEqual(groups[0]['hooks'][0]['args'], [str(alternate / 'hooks/log-step-hook.sh')])
        self.assertEqual(self.read_settings()['user'], 'preserved')

    def test_hook_recovery_after_image_finalizes_then_recomputes_install(self):
        alternate, prepared = self.prepare_upgrade('after')
        self.call('install', '--from', str(alternate))
        self.assertEqual(json.loads(self.receipt.read_text()), prepared['next'])
        self.assertEqual(self.read_settings()['user'], 'preserved')

    def test_hook_recovery_external_edit_preserves_settings_and_prepared_receipt(self):
        alternate, prepared = self.prepare_upgrade('after')
        value = self.read_settings()
        value['external'] = 'new user value'
        self.write_settings(value)
        before = self.snapshot()
        self.call('install', '--from', str(alternate), expected='unavailable')
        self.assertEqual(before, self.snapshot())
        self.call('uninstall', expected='unavailable')
        self.assertEqual(before, self.snapshot())

    def test_hook_recovery_uninstall_uses_saved_state_after_old_source_disappears(self):
        alternate, prepared = self.prepare_upgrade('after')
        shutil.rmtree(self.checkout)
        env = dict(self.env, ORCHESTRAIL_HOME=str(self.checkout))
        self.call('uninstall', expected='uninstalled', checkout=alternate, env=env)
        self.assert_user_settings_preserved({'user':'preserved'})
        if self.receipt.exists():
            self.assertEqual(json.loads(self.receipt.read_text()),
                             {'schema_version':1, 'state':'committed', 'owned':[], 'created_groups':[]})

    def test_hook_recovery_malformed_prepared_receipt_never_replaces_settings(self):
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

    def test_hook_transaction_interruption_before_settings_recovers_absent_image(self):
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

    def test_hook_transaction_interruption_after_settings_recovers_committed_image(self):
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

    def test_hook_transaction_rechecks_before_image_after_preparing_ownership(self):
        self.install()
        alternate = self.root / 'upgrade source'
        self.copy_source(alternate)
        external = self.root / 'external-settings.json'
        external.write_text('{"external":"preserve this concurrent user edit"}')
        faults = self.root / 'concurrent-editor'
        faults.mkdir()
        (faults / 'sitecustomize.py').write_text(
            'import os\nfrom pathlib import Path\n'
            'def wrap(original):\n'
            '    def replacement(src, dst, *args, **kwargs):\n'
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

    def test_hook_transaction_replacement_failure_preserves_settings_and_allows_retry(self):
        self.install()
        self.call('uninstall', expected='uninstalled')
        before = self.settings.read_bytes()
        faults = self.root / 'failed-replacement'
        faults.mkdir()
        (faults / 'sitecustomize.py').write_text(
            'import os\nfrom pathlib import Path\n'
            'def wrap(original):\n'
            '    def replacement(src, dst, *args, **kwargs):\n'
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

    def test_hook_install_preserves_exact_json_numbers_and_strings(self):
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

    def test_hook_install_missing_dependencies_report_unavailable_without_mutation(self):
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

    def test_hook_install_concurrent_operations_are_serialized_and_parseable(self):
        self.install()
        def operation(index):
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

    def test_hook_manifest_and_capabilities_describe_available_mechanism_and_partial_coverage(self):
        manifest = self.checkout / 'harness' / 'claude' / 'hooks.json'
        self.assertTrue(manifest.is_file(), 'portable native hook manifest must exist')
        hooks = json.loads(manifest.read_text())['hooks']
        self.assertEqual(set(hooks), {'Stop','SubagentStop'})
        for groups in hooks.values():
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0]['hooks'], [{'type':'command', 'command':'bash',
                'args':['@ORCHESTRAIL_HOME@/hooks/log-step-hook.sh'], 'timeout':10, 'onFailure':'continue'}])
        claude = (self.checkout / 'harness' / 'claude' / 'capabilities.md').read_text()
        codex = (self.checkout / 'harness' / 'codex' / 'capabilities.md').read_text()
        for token in ('hooks: yes', 'claude-stop-v1', '2026-10-25', '2.1.309', 'coverage', 'unknown', 'approximate'):
            self.assertIn(token, claude)
        for token in ('hooks: no', 'approximate', 'release', 'coverage'):
            self.assertIn(token, codex)

    def test_hook_setup_registers_canonical_roots_idempotently_and_adapter_gates(self):
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
        result = subprocess.run(['bash', str(adapter)], input='{}', cwd=self.root,
                                env=self.env, text=True, capture_output=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        result = subprocess.run(['bash', str(adapter)], input='{}', cwd=self.project,
                                env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('coverage', result.stderr)

    def test_hook_setup_concurrent_registration_preserves_existing_roots(self):
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

    def test_hook_setup_default_config_location_preserves_custom_project_files(self):
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

    def test_hook_setup_invalid_registry_or_newline_root_preserves_existing_entries(self):
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

    def test_hook_sync_embeds_capabilities_once_and_preserves_all_deployment_targets(self):
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

    def test_hook_sync_unavailable_installation_still_refreshes_consumer_projects(self):
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

suite = unittest.TestSuite(HookInstallation(name) for name in SELECTED) if SELECTED else unittest.defaultTestLoader.loadTestsFromTestCase(HookInstallation)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
PY
