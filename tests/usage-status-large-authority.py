#!/usr/bin/env python3
"""An independently provisioned digest binding can authorize a large selected part."""
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


class LargeAuthorityTests(unittest.TestCase):
    def prepare(self, *, wrong_digest=False):
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
        bundle_path.write_bytes(data)
        manifest['parts'][0].update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        receipt_path = Path(manifest['parts'][1]['local_path'])
        receipt = json.loads(receipt_path.read_text())
        receipt['bundle_sha256'] = contract.content_id(bundle)
        encoded = contract.canonical_bytes(receipt)
        receipt_path.write_bytes(encoded)
        manifest['parts'][1].update(sha256=hashlib.sha256(encoded).hexdigest(), size_bytes=len(encoded))
        manifest['bounds']['max_source_bytes'] = len(data)
        manifest['bounds']['max_total_bytes'] = sum(part['size_bytes'] for part in manifest['parts'])
        case.save(manifest)
        authority = json.loads(case.authority.read_text())
        authority['bindings'] = [item for item in authority['bindings'] if item['kind'] != 'receipt']
        authority['bindings'].append({'kind': 'receipt', 'scope': manifest['owner_scope'],
             'subject_sha256': contract.content_id(receipt),
             'evidence_sha256': ('f' * 64 if wrong_digest else contract.content_id(bundle))})
        case.authority.write_text(json.dumps(authority), encoding='utf-8')
        self.assertLess(case.authority.stat().st_size, 1024 * 1024)
        return case

    def test_explicitly_authorized_large_bundle_produces_real_metrics(self):
        case = self.prepare()
        process = case.run_status()
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(case.output.read_text())
        self.assertEqual(result['measurements']['tokens']['value'], 2200)
        self.assertEqual(result['measurements']['cost_usd']['value'], '0.00289')
        self.assertEqual({item['metric'] for item in result['candidates']}, {'tokens', 'cost_usd'})
        self.assertNotIn(str(case.root), json.dumps(result))
        contract.validate_current_run_snapshot(result['proposed_snapshot'])

    def test_mismatched_binding_is_not_authorization(self):
        case = self.prepare(wrong_digest=True)
        process = case.run_status()
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(case.output.read_text())
        self.assertEqual(result['candidates'], [])
        self.assertNotEqual(result['measurements'].get('tokens', {}).get('state'), 'final')


if __name__ == '__main__':
    unittest.main()
