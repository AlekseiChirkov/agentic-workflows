#!/usr/bin/env python3
"""Tests for bounded reads of explicitly selected local sources."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
MODULE = ROOT / 'scripts/usage_telemetry_sources.py'
if MODULE.exists():
    spec = importlib.util.spec_from_file_location('usage_telemetry_sources', MODULE)
    sources = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sources)
else:
    sources = None

OWNER = {'owner_kind': 'task', 'owner_id': 'sha256:' + '1' * 64}
SOURCE = 'sha256:' + '2' * 64


def manifest(path, content, **changes):
    result = {
        'schema_version': 1, 'kind': 'source_selection',
        'profile_id': 'synthetic-profile', 'profile_version': '1',
        'owner_scope': copy.deepcopy(OWNER),
        'attribution_map': [{'source_id': SOURCE, 'owner_kind': 'unattributed',
                             'quality': 'unknown', 'candidates': []}],
        'observed_at': '2026-01-02T03:04:05Z',
        'sources': [{'source_id': SOURCE, 'local_path': str(path),
                     'sha256': hashlib.sha256(content).hexdigest(),
                     'size_bytes': len(content)}],
        'max_source_bytes': len(content), 'max_total_bytes': len(content), 'max_records': 10,
    }
    result.update(changes)
    return result


def read(value, profile=('synthetic-profile', '1'), owner=OWNER):
    if sources is None:
        return None
    return sources.read_selected_sources(value, expected_profile=profile, expected_owner_scope=owner)


def parse(data, limit):
    if sources is None:
        return None
    return sources.parse_json_records(data, max_records=limit)


class BoundedSourceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'private-source.jsonl'
        self.content = '{"text":"é"}\n'.encode('utf-8')
        self.path.write_bytes(self.content)
        self.selection = manifest(self.path, self.content)

    def test_selected_external_file_bytes_and_no_neighbor_access(self):
        (self.path.parent / 'unselected-secret').write_text('unselected', encoding='utf-8')
        result = read(self.selection)
        self.assertEqual(result, [{'source_id': SOURCE, 'data': self.content, 'partial': False}])
        self.assertNotIn(str(self.path), repr(result))

    def test_invalid_manifest_profile_or_scope_rejected_before_source_access(self):
        bad = copy.deepcopy(self.selection)
        del bad['max_total_bytes']
        for value, profile, owner in [(bad, ('synthetic-profile', '1'), OWNER),
                (self.selection, ('wrong', '1'), OWNER),
                (self.selection, ('synthetic-profile', '1'), OWNER | {'owner_id': 'sha256:' + '9' * 64})]:
            with self.subTest(value=value, profile=profile), patch('os.open', side_effect=AssertionError('opened')):
                with self.assertRaises(ValueError):
                    read(value, profile, owner)

    def test_size_hash_exact_byte_limits_and_multibyte(self):
        self.assertEqual(read(self.selection)[0]['data'], self.content)
        for field in ('max_source_bytes', 'max_total_bytes'):
            bad = copy.deepcopy(self.selection)
            bad[field] -= 1
            with self.subTest(field=field), self.assertRaises(ValueError):
                read(bad)
        self.path.write_bytes(self.content[:-1] + b' ')
        with self.assertRaises(ValueError) as error:
            read(self.selection)
        self.assertNotIn(str(self.path), str(error.exception))
        self.assertNotIn('é', str(error.exception))
        self.path.write_bytes(self.content + b'x')
        with self.assertRaises(ValueError):
            read(self.selection)

    def test_prefix_hash_and_changed_prefix(self):
        prefix = self.content[:8]
        self.path.write_bytes(prefix + b'changed suffix')
        selection = manifest(self.path, prefix)
        selection['sources'][0]['size_bytes'] = len(self.path.read_bytes())
        selection['sources'][0]['verified_prefix_bytes'] = len(prefix)
        self.assertEqual(read(selection), [{'source_id': SOURCE, 'data': prefix, 'partial': True}])
        self.path.write_bytes(b'X' + self.path.read_bytes()[1:])
        with self.assertRaises(ValueError):
            read(selection)

    def test_symlinks_directories_and_symlinked_ancestors_are_rejected(self):
        link = self.path.parent / 'link'
        link.symlink_to(self.path)
        for path in (link, self.path.parent):
            with self.subTest(path=path), self.assertRaises(ValueError):
                read(manifest(path, self.content))
        directory_link = self.path.parent / 'dirlink'
        directory_link.symlink_to(self.path.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            read(manifest(directory_link / self.path.name, self.content))

    def test_symlink_swap_during_open_never_reads_target(self):
        target = self.path.parent / 'target'
        target.write_bytes(self.content)
        real_open = os.open
        swapped = False
        def swap(path, flags, *args, **kwargs):
            nonlocal swapped
            if os.fsdecode(path) == self.path.name and not swapped:
                swapped = True
                self.path.unlink()
                self.path.symlink_to(target)
            return real_open(path, flags, *args, **kwargs)
        with patch('os.open', side_effect=swap):
            with self.assertRaises(ValueError):
                read(self.selection)
        self.assertTrue(swapped)

    def test_json_record_limits_bytes_depth_and_no_partial_success(self):
        self.assertEqual(parse(b'{"a":1}\n{"b":2}\n', 2), [{'a': 1}, {'b': 2}])
        with self.assertRaises(ValueError):
            parse(b'{"a":1}\n{"b":2}\n', 1)
        with self.assertRaises(ValueError):
            parse(b'[' * 33 + b'0' + b']' * 33 + b'\n', 1)
        with self.assertRaises(ValueError):
            parse(b'"' + b'x' * (16 * 1024 * 1024) + b'"\n', 1)
        with self.assertRaises(ValueError):
            parse(b'{bad json}\n', 1)

    def test_selected_reads_do_not_use_network(self):
        with patch('socket.socket', side_effect=AssertionError('network')):
            self.assertEqual(read(self.selection)[0]['data'], self.content)


if __name__ == '__main__':
    unittest.main()
