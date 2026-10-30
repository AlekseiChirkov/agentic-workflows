#!/usr/bin/env python3
"""Check independent first-seen times for frozen context evidence."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract

spec = importlib.util.spec_from_file_location('fixtures', ROOT / 'tests/usage-frozen-pricing-inputs.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class ContextEvidenceTimingTests(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.FrozenPricingInputsTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        context = copy.deepcopy(self.base.context)
        self.evidence = {'schema_version': 1, 'kind': 'execution_time_evidence',
                         'profile_id': context['profile_id'], 'source_hash': context['source_hash'],
                         'record_number': context['record_number'], 'value': context['execution_time']}
        context['evidence_objects'] = [self.evidence]
        entry = next(item for item in self.base.manifest['inputs'] if item['kind'] == 'resolution_context')
        self.base.allowed.remove(entry['sha256'])
        data = contract.canonical_bytes(context)
        Path(entry['local_path']).write_bytes(data)
        entry.update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        self.base.allowed.add(entry['sha256'])
        self.digest = contract.content_id(self.evidence)

    def verify_with(self, timestamp):
        def verify(entry, value, scope):
            proof = self.base.verify(entry, value, scope)
            if entry['kind'] == 'resolution_context' and timestamp is not None:
                proof['member_times'] = {self.digest: timestamp}
            return proof
        return verify

    @staticmethod
    def evidence_in(result):
        context = next(item['value'] for item in result['inputs'] if item['kind'] == 'resolution_context')
        return context['evidence_objects']

    def test_only_independently_proven_early_evidence_is_retained(self):
        trusted = self.base.freeze(self.verify_with('2026-01-02T00:00:00Z'))
        self.assertEqual(self.evidence_in(trusted), [self.evidence])
        unknown = self.base.freeze(self.verify_with(None))
        self.assertEqual(self.evidence_in(unknown), [])
        self.assertIn('timing_unavailable', [item['reason'] for item in unknown['exclusions']])
        late = self.base.freeze(self.verify_with('2026-01-04T00:00:00Z'))
        self.assertEqual(self.evidence_in(late), [])
        self.assertIn('late_evidence', [item['reason'] for item in late['exclusions']])
        self.assertEqual(len({trusted['corpus_id'], unknown['corpus_id'], late['corpus_id']}), 3)

    def test_invented_member_proofs_fail_closed(self):
        self.assertEqual(self.evidence_in(self.base.freeze(
            self.verify_with('2026-01-02T00:00:00Z'))), [self.evidence])
        def verify(entry, value, scope):
            proof = self.base.verify(entry, value, scope)
            if entry['kind'] == 'resolution_context':
                proof['member_times'] = {'a' * 64: '2026-01-02T00:00:00Z'}
            return proof
        with self.assertRaises(ValueError):
            self.base.freeze(verify)

    def test_nested_members_count_toward_the_record_limit(self):
        self.assertEqual(self.evidence_in(self.base.freeze(
            self.verify_with('2026-01-02T00:00:00Z'))), [self.evidence])
        manifest = self.base.manifest
        bundle = self.base.bundle
        manifest['max_records'] = (len(manifest['inputs']) + sum(len(bundle[field]) for field in
            ('observations', 'inventories', 'segments', 'diagnostics', 'evidence_objects')))
        with self.assertRaises(ValueError):
            self.base.freeze(self.verify_with('2026-01-02T00:00:00Z'))


if __name__ == '__main__':
    unittest.main()
