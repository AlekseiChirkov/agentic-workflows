#!/usr/bin/env python3
"""End-to-end checks for the explicitly configured offline normalizer."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

fixtures = load('source_fixtures', ROOT / 'tests/usage-bounded-source-reads.py')
profiles = load('profile_fixtures', ROOT / 'tests/usage-source-profiles.py')
contract = load('contract', ROOT / 'scripts/usage_telemetry_contract.py')
CLI = ROOT / 'scripts/usage-telemetry.py'


class NormalizeCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'private-source.jsonl'
        self.manifest = self.root / 'selection.json'
        self.output = self.root / 'bundle.json'
        self.config_path = self.root / 'private-config.json'
        self.log_root = self.root / 'logs'
        self.profile = profiles.profile()
        self.raw = {'usage': {'input': 1000, 'read': 200, 'write': 150,
                              'short': 100, 'long': 50, 'output': 500, 'reasoning': 100},
                    'private': 'PAYLOAD_SENTINEL'}
        self.config = {'schema_version': 1, 'profiles': [{'profile': self.profile,
                       'sha256': hashlib.sha256(contract.canonical_bytes(self.profile)).hexdigest()}],
                       'owner_scope': fixtures.OWNER, 'project_identifier': 'PRIVATE_PROJECT',
                       'provider_identifier': 'PRIVATE_PROVIDER', 'run_id': 'run-1',
                       'key_hex': '7f' * 32}
        self.write_config()
        self.write_records([self.raw])
        self.env = dict(os.environ, USAGE_TELEMETRY_CONFIG=str(self.config_path),
                        ORCHESTRAIL_LOG_ROOT=str(self.log_root))

    def write_config(self):
        self.config_path.write_text(json.dumps(self.config), encoding='utf-8')
        self.config_path.chmod(0o600)

    def write_records(self, records):
        data = b''.join((json.dumps(item) + '\n').encode() for item in records)
        self.source.write_bytes(data)
        self.selection = fixtures.manifest(self.source, data)
        self.write_manifest()

    def write_manifest(self):
        self.manifest.write_text(json.dumps(self.selection), encoding='utf-8')

    def run_cli(self, profile='synthetic-profile', output=None, env=None):
        return subprocess.run([sys.executable, str(CLI), 'normalize', '--profile', profile,
                               '--input-manifest', str(self.manifest), '--output', str(output or self.output)],
                              capture_output=True, text=True, env=env or self.env, timeout=10)

    def test_normalize_emits_self_contained_sanitized_bundle(self):
        (self.root / 'private-unselected').write_text('NEIGHBOR_SENTINEL')
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        bundle = json.loads(self.output.read_text())
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        self.assertEqual(bundle['observations'][0]['measurements']['tokens_in']['value'], 1000)
        self.assertEqual(bundle['observations'][0]['observed_at'], self.selection['observed_at'])
        self.assertTrue(bundle['evidence_objects'])
        exposed = self.output.read_text() + result.stdout + result.stderr
        for secret in ('PRIVATE_PROJECT', 'PRIVATE_PROVIDER', 'PAYLOAD_SENTINEL',
                       'NEIGHBOR_SENTINEL', str(self.source), str(self.config_path), '7f' * 32):
            self.assertNotIn(secret, exposed)

    def test_bad_record_quarantined_in_partial_bundle(self):
        self.write_records([self.raw, {'usage': {'input': -1}, 'secret': 'BAD_SENTINEL'}, self.raw])
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        bundle = json.loads(self.output.read_text())
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        self.assertEqual(sorted(item['record_number'] for item in bundle['observations']), [1, 3])
        self.assertEqual(bundle['diagnostics'][0]['record_number'], 2)
        self.assertEqual(bundle['diagnostics'][0]['completeness'], 'partial')
        self.assertNotIn('BAD_SENTINEL', self.output.read_text() + result.stderr)

    def test_invalid_selection_and_untrusted_profiles_fail_without_result(self):
        cases = []
        missing_limit = copy.deepcopy(self.selection)
        del missing_limit['max_total_bytes']
        cases.append((missing_limit, self.config, 'synthetic-profile'))
        wrong_version = copy.deepcopy(self.selection)
        wrong_version['profile_version'] = 'untrusted'
        cases.append((wrong_version, self.config, 'synthetic-profile'))
        wrong_hash = copy.deepcopy(self.config)
        wrong_hash['profiles'][0]['sha256'] = '0' * 64
        cases.append((self.selection, wrong_hash, 'synthetic-profile'))
        cases.append((self.selection, self.config, 'untrusted'))
        for selection, config, profile in cases:
            with self.subTest(selection=selection, profile=profile):
                self.selection, self.config = selection, config
                self.write_manifest()
                self.write_config()
                result = self.run_cli(profile)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.output.exists())
                self.assertNotIn(str(self.source), result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_invalid_config_permissions_or_missing_config_fail_without_result(self):
        self.config_path.chmod(0o644)
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertNotIn(str(self.config_path), result.stderr)
        env = self.env.copy()
        del env['USAGE_TELEMETRY_CONFIG']
        result = self.run_cli(env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertNotIn('Traceback', result.stderr)

    def test_symlinked_config_is_rejected(self):
        alias = self.root / 'config-alias'
        alias.symlink_to(self.config_path)
        env = self.env | {'USAGE_TELEMETRY_CONFIG': str(alias)}
        result = self.run_cli(env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertNotIn(str(alias), result.stderr)

    def test_changed_source_and_invalid_manifest_do_not_replace_output(self):
        self.output.write_text('existing output')
        self.source.write_bytes(b'CHANGED_PRIVATE_SOURCE')
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_text(), 'existing output')
        self.assertNotIn('CHANGED_PRIVATE_SOURCE', result.stderr)
        self.assertNotIn(str(self.source), result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_output_cannot_enter_shared_usage_storage(self):
        shared = self.log_root / 'usage' / 'v1'
        shared.mkdir(parents=True)
        result = self.run_cli(output=shared / 'bundle.json')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((shared / 'bundle.json').exists())
        self.assertEqual(list(shared.iterdir()), [])
        self.assertNotIn('Traceback', result.stderr)
        alias = self.root / 'shared-alias'
        alias.symlink_to(shared, target_is_directory=True)
        result = self.run_cli(output=alias / 'bundle.json')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(shared.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
