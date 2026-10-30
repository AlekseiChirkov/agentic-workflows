#!/usr/bin/env python3
"""Status cannot publish through a relocated directory or regular-file descriptor."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('duration_fixture', ROOT / 'tests/usage-status-duration-integration.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class StatusOutputRelocationTests(unittest.TestCase):
    def test_relocation_between_check_and_replace_cannot_publish_to_shared_store(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot, _ = fixture.time_only()
            source = root / 'snapshot.json'
            source.write_text(json.dumps(snapshot), encoding='utf-8')
            output_dir = root / 'output'
            output_dir.mkdir()
            shared = root / 'logs' / 'usage' / 'v1'
            shared.mkdir(parents=True)
            relocated = shared / 'relocated'
            command = ['python3', str(ROOT / 'scripts/usage-telemetry.py'), 'status',
                       '--receipt-snapshot', str(source), '--observed-at', fixture.NOW]
            env = {**os.environ, 'ORCHESTRAIL_LOG_ROOT': str(root / 'logs')}
            with (output_dir / 'status.json').open('wb') as output:
                output_dir.rename(relocated)
                result = subprocess.run(command, stdout=output, stderr=subprocess.PIPE, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((relocated / 'status.json').read_bytes(), b'')
            self.assertIn(b'status failed', result.stderr)
            legacy = subprocess.run(command + ['--output', str(relocated / 'other.json')],
                                    capture_output=True, env=env)
            self.assertNotEqual(legacy.returncode, 0)
            self.assertFalse((relocated / 'other.json').exists())
            piped = subprocess.run(command, capture_output=True, env=env)
            self.assertEqual(piped.returncode, 0, piped.stderr)
            self.assertIsInstance(json.loads(piped.stdout), dict)

    def test_status_input_error_is_operation_specific_and_sanitized(self):
        missing = '/private/STATUS_SENTINEL'
        result = subprocess.run(['python3', str(ROOT / 'scripts/usage-telemetry.py'), 'status',
                                 '--receipt-snapshot', missing], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'status failed', result.stderr)
        self.assertNotIn(b'STATUS_SENTINEL', result.stderr)
        self.assertEqual(result.stdout, b'')

    def test_owner_delivery_errors_are_operation_specific_and_sanitized(self):
        missing = '/private/OWNER_SENTINEL'
        result = subprocess.run(['python3', str(ROOT / 'scripts/usage-telemetry.py'), 'owner-deliver',
                                 '--state', missing, '--owner-authority', missing], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'owner delivery failed', result.stderr)
        self.assertNotIn(b'OWNER_SENTINEL', result.stderr)


if __name__ == '__main__':
    unittest.main()
