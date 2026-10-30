#!/usr/bin/env python3
"""Explicit bounded owner snapshot parts with independently authorized receipts."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('status_cli_fixture', ROOT / 'tests/usage-status-cli-integration.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
contract = base.fixture.contract


class SelectedPartsTests(base.StatusCommandTests):
    def setUp(self):
        super().setUp()
        snapshot = json.loads(self.snapshot.read_text())
        self.parts = []
        for section, kind in (('bundles', 'usage_bundle'), ('accepted_receipts', 'usage_accepted'),
                              ('inventories', 'inventory'), ('inventory_evidence', 'inventory_evidence')):
            for index, item in enumerate(snapshot[section]):
                encoded = contract.canonical_bytes(item)
                path = self.root / (section + str(index) + '.json')
                path.write_bytes(encoded)
                path.chmod(0o600)
                self.parts.append({'kind': kind, 'local_path': str(path),
                                   'sha256': hashlib.sha256(encoded).hexdigest(), 'size_bytes': len(encoded)})
            snapshot[section] = []
        snapshot['parts'] = copy.deepcopy(self.parts)
        self.snapshot.write_bytes(contract.canonical_bytes(snapshot))
        self.original = snapshot

    def save(self, snapshot):
        self.snapshot.write_bytes(contract.canonical_bytes(snapshot))

    def test_exact_selected_parts_are_loaded_without_touching_neighbor_or_source(self):
        neighbor = self.root / 'unselected-secret.json'
        neighbor.write_text('PRIVATE_CONTENT_SENTINEL')
        before = self.snapshot.read_bytes()
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(self.output.read_text())
        self.assertEqual({entry['metric'] for entry in output['candidates']}, {'tokens', 'cost_usd'})
        self.assertEqual(self.snapshot.read_bytes(), before)
        self.assertEqual(neighbor.read_text(), 'PRIVATE_CONTENT_SENTINEL')
        self.assertNotIn('PRIVATE_CONTENT_SENTINEL', json.dumps(output))
        self.assertNotIn(str(self.root), json.dumps(output))

    def test_incorrect_hash_size_and_changed_file_fail_before_output(self):
        for change in ({'sha256': 'f' * 64}, {'size_bytes': self.parts[0]['size_bytes'] + 1}):
            with self.subTest(change=change):
                invalid = copy.deepcopy(self.original)
                invalid['parts'][0].update(change)
                self.save(invalid)
                result = self.run_status()
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.output.exists())
        self.save(self.original)
        Path(self.parts[0]['local_path']).write_bytes(b'{}')
        result = self.run_status()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_invalid_schema_and_foreign_owner_are_rejected(self):
        foreign = json.loads(Path(self.parts[1]['local_path']).read_text())
        foreign['scope']['owner_id'] = 'sha256:' + 'f' * 64
        for payload in ({'raw_content': 'PRIVATE_CONTENT_SENTINEL'}, foreign):
            with self.subTest(payload=payload):
                invalid = copy.deepcopy(self.original)
                encoded = contract.canonical_bytes(payload)
                path = Path(invalid['parts'][1]['local_path'])
                path.write_bytes(encoded)
                invalid['parts'][1].update(sha256=hashlib.sha256(encoded).hexdigest(), size_bytes=len(encoded))
                self.save(invalid)
                result = self.run_status()
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.output.exists())
                self.assertNotIn('PRIVATE_CONTENT_SENTINEL', result.stderr)

    def test_symlink_selected_part_is_not_followed(self):
        target = Path(self.parts[0]['local_path'])
        saved = self.root / 'replacement.json'
        target.rename(saved)
        target.symlink_to(saved)
        result = self.run_status()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_declared_total_bytes_and_record_limit_are_enforced(self):
        for bounds in ({'max_total_bytes': sum(item['size_bytes'] for item in self.parts) - 1},
                       {'max_source_bytes': self.parts[0]['size_bytes'] - 1},
                       {'max_records': 1}):
            with self.subTest(bounds=bounds):
                invalid = copy.deepcopy(self.original)
                invalid['bounds'].update(bounds)
                self.save(invalid)
                result = self.run_status()
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.output.exists())

    def test_parts_are_not_authorized_by_hash_or_receipt_alone(self):
        result = self.run_status(authority=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(self.output.read_text())
        self.assertEqual(output['candidates'], [])
        self.assertNotEqual(output['measurements'].get('tokens', {}).get('state'), 'final')


if __name__ == '__main__':
    unittest.main()
