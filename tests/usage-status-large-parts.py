#!/usr/bin/env python3
"""Selected data parts may exceed the manifest byte limit within their own bounds."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('parts_fixture', ROOT / 'tests/usage-status-parts-cli.py')
parts_fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parts_fixture)
contract = parts_fixture.contract


class LargeStatusPartsTests(unittest.TestCase):
    def test_valid_large_bundle_within_part_and_total_limits_is_not_rejected(self):
        case = parts_fixture.SelectedPartsTests('test_exact_selected_parts_are_loaded_without_touching_neighbor_or_source')
        case.setUp()
        self.addCleanup(case.doCleanups)
        manifest = copy.deepcopy(case.original)
        bundle_path = Path(manifest['parts'][0]['local_path'])
        bundle = json.loads(bundle_path.read_text())
        for i in range(7000):
            digest = format(i, '064x')
            bundle['sources'].append({'source_id': 'sha256:' + digest, 'sha256': digest})
        contract.validate_usage_bundle(bundle)
        data = contract.canonical_bytes(bundle)
        self.assertGreater(len(data), 1024 * 1024)
        self.assertLess(len(data), contract.BUNDLE_LIMIT)
        bundle_path.write_bytes(data)
        manifest['parts'][0].update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        receipt_path = Path(manifest['parts'][1]['local_path'])
        receipt = json.loads(receipt_path.read_text())
        receipt['bundle_sha256'] = contract.content_id(bundle)
        receipt_data = contract.canonical_bytes(receipt)
        receipt_path.write_bytes(receipt_data)
        manifest['parts'][1].update(sha256=hashlib.sha256(receipt_data).hexdigest(), size_bytes=len(receipt_data))
        manifest['bounds']['max_source_bytes'] = len(data)
        manifest['bounds']['max_total_bytes'] = sum(item['size_bytes'] for item in manifest['parts'])
        case.save(manifest)
        self.assertLess(len(case.snapshot.read_bytes()), 1024 * 1024)
        result = case.run_status(authority=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(case.output.read_text())
        self.assertEqual(output['candidates'], [])
        self.assertNotIn(str(case.root), json.dumps(output))
        self.assertCountEqual(output['proposed_snapshot']['part_references'],
                         [{key: part[key] for key in ('kind', 'sha256', 'size_bytes')}
                          for part in manifest['parts']])
        delivery = parts_fixture.base.fixture.load('delivery_large', 'scripts/usage_telemetry_delivery.py')
        delivery.apply_revision(case.snapshot, manifest['revision'], output['proposed_snapshot'],
                                owner_scope=manifest['owner_scope'], destinations={})
        self.assertEqual(json.loads(case.snapshot.read_text())['parts'], manifest['parts'])


if __name__ == '__main__':
    unittest.main()
