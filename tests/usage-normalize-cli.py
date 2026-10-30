#!/usr/bin/env python3
"""End-to-end checks for the explicitly configured offline normalizer."""
import copy
import hashlib
import importlib.util
import json
import os
import socket
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

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
                       'provider_identifier': 'PRIVATE_PROVIDER', 'run_id': '1a2b3c4d',
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

    def run_cli(self, profile='synthetic-profile', env=None):
        return subprocess.run([sys.executable, str(CLI), 'normalize', '--profile', profile,
                               '--input-manifest', str(self.manifest)],
                              capture_output=True, text=True, env=env or self.env, timeout=10)

    def test_nonblocking_pipe_never_reports_success_for_truncated_bundle(self):
        import fcntl
        self.write_records([self.raw, self.raw, self.raw])
        expected = self.run_cli().stdout.encode()
        read_fd, write_fd = os.pipe()
        try:
            fcntl.fcntl(write_fd, fcntl.F_SETPIPE_SZ, 4096)
            os.set_blocking(write_fd, False)
            result = subprocess.run([sys.executable, '-u', str(CLI), 'normalize',
                                     '--profile', 'synthetic-profile', '--input-manifest', str(self.manifest)],
                                    stdout=write_fd, stderr=subprocess.PIPE, env=self.env, timeout=10)
            os.close(write_fd)
            write_fd = -1
            received = os.read(read_fd, len(expected) + 1)
            if result.returncode == 0:
                self.assertEqual(received, expected)
            else:
                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stderr, b'usage telemetry: normalization failed\n')
        finally:
            os.close(read_fd)
            if write_fd >= 0:
                os.close(write_fd)

    def test_buffered_nonblocking_pipe_reports_sanitized_failure(self):
        import fcntl
        self.write_records([self.raw, self.raw, self.raw])
        env = self.env.copy()
        env.pop('PYTHONUNBUFFERED', None)
        read_fd, write_fd = os.pipe()
        try:
            fcntl.fcntl(write_fd, fcntl.F_SETPIPE_SZ, 4096)
            os.set_blocking(write_fd, False)
            result = subprocess.run([sys.executable, str(CLI), 'normalize',
                                     '--profile', 'synthetic-profile', '--input-manifest', str(self.manifest)],
                                    stdout=write_fd, stderr=subprocess.PIPE, env=env, timeout=10)
            self.assertEqual(result.returncode, 3)
            self.assertEqual(result.stderr, b'usage telemetry: normalization failed\n')
        finally:
            os.close(read_fd)
            os.close(write_fd)

    def test_all_output_commands_handle_short_and_no_progress_writes(self):
        import io
        import usage_telemetry_contract as runtime_contract
        import usage_telemetry_delivery as delivery
        import usage_telemetry_report as report
        import usage_telemetry_exports as exports
        import usage_telemetry_alerts as alerts
        cli = load('stream_cli', CLI)
        class Stream:
            def __init__(self, fd, mode):
                self.fd = fd
                self.buffer = self
                self.mode = mode
                self.data = bytearray()
            def fileno(self):
                return self.fd
            def write(self, data):
                if self.mode in (None, 0):
                    return self.mode
                count = min(self.mode, len(data))
                self.data.extend(data[:count])
                return count
            def flush(self):
                pass
        read_fd, write_fd = os.pipe()
        self.addCleanup(os.close, read_fd)
        self.addCleanup(os.close, write_fd)
        authority = {'schema_version': 1, 'kind': 'warning_owner_authority',
                     'owner_scope': {'owner_kind': 'run', 'owner_id': 'sha256:' + 'b' * 64}, 'destinations': []}
        cases = [
            (['normalize', '--profile', 'synthetic-profile', '--input-manifest', str(self.manifest)], None),
            (['status', '--receipt-snapshot', 'snapshot'], b'{"ok":true}'),
            (['owner-deliver', '--state', 'state', '--owner-authority', 'authority'], b'{"ok":true}'),
            (['analyze', '--corpus-manifest', 'manifest', '--scenario', 'baseline'], b'archive payload'),
        ]
        for args, expected in cases:
            for mode in (3, None, 0):
                with self.subTest(command=args[0], mode=mode):
                    stream = Stream(write_fd, mode)
                    with patch.object(sys, 'stdout', stream), patch.dict(os.environ, self.env), \
                         patch.object(cli, '_read_file', side_effect=lambda path, **kw: json.dumps(authority).encode() if path == 'authority' else b'{}' if path in ('snapshot', 'manifest') else Path(path).read_bytes()), \
                         patch.object(cli, '_snapshot_with_parts', return_value=({}, None, None)), \
                         patch.object(cli, '_status_authority', return_value=None), \
                         patch.object(alerts, 'evaluate_status', return_value={'ok': True}), \
                         patch.object(delivery, 'resume_delivery', return_value={'ok': True}), \
                         patch.object(runtime_contract, 'validate_analysis_corpus_json', return_value={'scenario_id': 'baseline'}), \
                         patch.object(cli, '_analysis_authority', return_value=(None, None)), \
                         patch.object(report, 'analyze_corpus', return_value={}), \
                         patch.object(exports, 'render_exports', return_value={}), \
                         patch.object(exports, 'archive_exports', return_value=b'archive payload'):
                        if mode in (None, 0):
                            with self.assertRaises(OSError):
                                cli.main(args)
                        else:
                            cli.main(args)
                            if expected is None:
                                contract.validate_usage_bundle(json.loads(stream.data))
                            else:
                                self.assertEqual(stream.data, expected)

    def test_normalize_emits_self_contained_sanitized_bundle(self):
        (self.root / 'private-unselected').write_text('NEIGHBOR_SENTINEL')
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        bundle = json.loads(result.stdout)
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        self.assertEqual(bundle['run_id'], '1a2b3c4d')
        self.assertEqual(bundle['observations'][0]['measurements']['tokens_in']['value'], 1000)
        self.assertEqual(bundle['observations'][0]['observed_at'], self.selection['observed_at'])
        self.assertTrue(bundle['evidence_objects'])
        exposed = result.stdout + result.stderr
        for secret in ('PRIVATE_PROJECT', 'PRIVATE_PROVIDER', 'PAYLOAD_SENTINEL',
                       'NEIGHBOR_SENTINEL', str(self.source), str(self.config_path), '7f' * 32):
            self.assertNotIn(secret, exposed)

    def test_bad_record_quarantined_in_partial_bundle(self):
        self.write_records([self.raw, {'usage': {'input': -1}, 'secret': 'BAD_SENTINEL'}, self.raw])
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        bundle = json.loads(result.stdout)
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        self.assertEqual(sorted(item['record_number'] for item in bundle['observations']), [1, 3])
        self.assertEqual(bundle['diagnostics'][0]['record_number'], 2)
        self.assertEqual(bundle['diagnostics'][0]['completeness'], 'partial')
        self.assertNotIn('BAD_SENTINEL', result.stdout + result.stderr)

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
                self.assertEqual(result.stdout, '')
                self.assertNotIn(str(self.source), result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_invalid_config_permissions_or_missing_config_fail_without_result(self):
        self.config_path.chmod(0o644)
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertNotIn(str(self.config_path), result.stderr)
        env = self.env.copy()
        del env['USAGE_TELEMETRY_CONFIG']
        result = self.run_cli(env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertNotIn('Traceback', result.stderr)

    def test_symlinked_config_is_rejected(self):
        alias = self.root / 'config-alias'
        alias.symlink_to(self.config_path)
        env = self.env | {'USAGE_TELEMETRY_CONFIG': str(alias)}
        result = self.run_cli(env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertNotIn(str(alias), result.stderr)

    def test_invalid_run_identifiers_never_produce_output_or_disclose_values(self):
        for run_id in ('PRIVATE_RUN_SECRET', '1a2b3c4', '1A2B3C4D', '1a2b3c4d5', '../1a2b3c4d'):
            with self.subTest(case=run_id):
                self.output.unlink(missing_ok=True)
                self.config['run_id'] = run_id
                self.write_config()
                result = self.run_cli()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')
                self.assertNotIn(run_id, result.stdout + result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_changed_source_and_invalid_manifest_do_not_replace_output(self):
        self.output.write_text('existing output')
        self.source.write_bytes(b'CHANGED_PRIVATE_SOURCE')
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_text(), 'existing output')
        self.assertEqual(result.stdout, '')
        self.assertNotIn('CHANGED_PRIVATE_SOURCE', result.stderr)
        self.assertNotIn(str(self.source), result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_file_destination_argument_is_rejected_without_writes(self):
        shared = self.log_root / 'usage' / 'v1'
        shared.mkdir(parents=True)
        result = subprocess.run([sys.executable, str(CLI), 'normalize', '--profile',
                                 'synthetic-profile', '--input-manifest', str(self.manifest),
                                 '--output', str(shared / 'bundle.json')],
                                capture_output=True, text=True, env=self.env, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertEqual(list(shared.iterdir()), [])

    def test_regular_file_stdout_is_rejected_without_writes(self):
        shared = self.log_root / 'usage' / 'v1'
        shared.mkdir(parents=True)
        evidence = shared / 'existing.json'
        evidence.write_bytes(b'existing evidence')
        with evidence.open('ab') as output:
            result = subprocess.run([sys.executable, str(CLI), 'normalize', '--profile',
                                     'synthetic-profile', '--input-manifest', str(self.manifest)],
                                    stdout=output, stderr=subprocess.PIPE, env=self.env, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(evidence.read_bytes(), b'existing evidence')
        self.assertEqual(list(shared.iterdir()), [evidence])

    def test_socket_stdout_emits_valid_bundle(self):
        reader, writer = socket.socketpair()
        self.addCleanup(reader.close)
        self.addCleanup(writer.close)
        result = subprocess.run([sys.executable, str(CLI), 'normalize', '--profile',
                                 'synthetic-profile', '--input-manifest', str(self.manifest)],
                                stdout=writer, stderr=subprocess.PIPE, env=self.env, timeout=10)
        writer.close()
        chunks = []
        while True:
            data = reader.recv(65536)
            if not data:
                break
            chunks.append(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        bundle = json.loads(b''.join(chunks))
        self.assertEqual(contract.validate_usage_bundle(bundle)['run_id'], '1a2b3c4d')

    def test_closed_pipe_returns_failure_with_sanitized_diagnostics(self):
        read_fd, write_fd = os.pipe()
        os.close(read_fd)
        try:
            result = subprocess.run([sys.executable, str(CLI), 'normalize', '--profile',
                                     'synthetic-profile', '--input-manifest', str(self.manifest)],
                                    stdout=write_fd, stderr=subprocess.PIPE, env=self.env, timeout=10)
        finally:
            os.close(write_fd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'normalization failed', result.stderr)
        for secret in (str(self.source), str(self.config_path), 'PAYLOAD_SENTINEL', 'PRIVATE_PROJECT'):
            self.assertNotIn(secret.encode(), result.stderr)
        self.assertNotIn(b'Traceback', result.stderr)

    def test_destination_moved_after_final_check_never_publishes_to_shared_store(self):
        module = load('usage_cli_stream_race', CLI)
        destination = self.root / 'destination'
        destination.mkdir()
        shared = self.log_root / 'usage' / 'v1'
        shared.parent.mkdir(parents=True)
        evidence = self.log_root / 'lifecycle.jsonl'
        evidence.write_bytes(b'existing lifecycle evidence\n')
        original = module.adapter.normalize_selection

        def move_during_normalization(*args, **kwargs):
            result = original(*args, **kwargs)
            destination.rename(shared)
            return result

        read_fd, write_fd = os.pipe()
        args = ['normalize', '--profile', 'synthetic-profile', '--input-manifest', str(self.manifest)]
        with os.fdopen(write_fd, 'w') as output, \
                patch.dict(os.environ, self.env, clear=True), \
                patch.object(sys, 'stdout', output), \
                patch.object(module.adapter, 'normalize_selection', side_effect=move_during_normalization):
            module.main(args)
        with os.fdopen(read_fd, 'rb') as stream:
            bundle = json.loads(stream.read())
        self.assertEqual(contract.validate_usage_bundle(bundle)['run_id'], '1a2b3c4d')
        self.assertEqual(list(shared.iterdir()), [])
        self.assertEqual(evidence.read_bytes(), b'existing lifecycle evidence\n')

    def test_unreviewed_profile_strings_never_appear_in_output(self):
        def source(profile):
            profile['source'] = 'https://example.invalid/PRIVATE_PROFILE_SECRET'

        def nested_evidence(profile):
            profile['inventory']['evidence'] = 'PRIVATE_PROFILE_SECRET'

        def nested_path(profile):
            profile['counter_fields'][0]['path'][1] = 'PRIVATE_PROFILE_SECRET'

        for mutate in (source, nested_evidence, nested_path):
            with self.subTest(field=mutate.__name__):
                profile = copy.deepcopy(self.profile)
                mutate(profile)
                self.config['profiles'][0] = {'profile': profile,
                    'sha256': hashlib.sha256(contract.canonical_bytes(profile)).hexdigest()}
                self.write_config()
                self.output.unlink(missing_ok=True)
                result = self.run_cli()
                exposed = result.stdout + result.stderr
                if result.returncode == 0:
                    bundle = json.loads(result.stdout)
                    self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
                    exposed += result.stdout
                else:
                    self.assertNotEqual(result.returncode, 0)
                self.assertFalse('PRIVATE_PROFILE_SECRET' in exposed, 'private profile text was published')


if __name__ == '__main__':
    unittest.main()
