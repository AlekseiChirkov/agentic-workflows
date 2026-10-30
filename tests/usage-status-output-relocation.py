#!/usr/bin/env python3
"""Status output must not reach shared storage after a directory relocation."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('usage_cli', ROOT / 'scripts/usage-telemetry.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class StatusOutputRelocationTests(unittest.TestCase):
    def test_relocation_between_check_and_replace_cannot_publish_to_shared_store(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'output'
            source.mkdir()
            shared = root / 'logs' / 'usage' / 'v1'
            shared.mkdir(parents=True)
            relocated = shared / 'relocated'
            with patch.dict(os.environ, {'ORCHESTRAIL_LOG_ROOT': str(root / 'logs')}):
                fd, name, parent, log_root = cli._output_directory(str(source / 'status.json'))
                original = os.replace
                def relocate_then_replace(*args, **kwargs):
                    source.rename(relocated)
                    return original(*args, **kwargs)
                try:
                    with patch.object(cli.os, 'replace', side_effect=relocate_then_replace):
                        with self.assertRaises((ValueError, OSError)):
                            cli._publish(fd, name, parent, log_root, b'{}')
                finally:
                    os.close(fd)
            self.assertFalse((relocated / 'status.json').exists())


if __name__ == '__main__':
    unittest.main()
