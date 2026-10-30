#!/usr/bin/env python3
"""Freeze cumulative intervals only with independently timed evidence."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract
import usage_telemetry_report as report
import usage_telemetry_exports as exports

def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tests' / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

fixtures = load('reports', 'usage-resolved-report-integration.py')
epochs = load('epochs', 'usage-resolution-epochs.py')

class EpochReportTests(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.ResolvedReportTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        data = self.base.data
        pack = epochs.epoch_pack()
        data['epoch_inputs'] = [pack]
        epochs.own_bundle(data)
        epochs.authorize(data, self.base.allowed, pack)
        self.base.allowed[:] = [(kind, contract.parse_json(contract.canonical_bytes(scope)),
                                 contract.parse_json(contract.canonical_bytes(subject)),
                                 contract.parse_json(contract.canonical_bytes(evidence)))
                                for kind, scope, subject, evidence in self.base.allowed]
        self.base.authority.allowed = copy.deepcopy(self.base.allowed)
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
                                        if item['kind'] in ('usage_bundle', 'source_profile')]
        self.base.selected.clear()
        for item in self.base.manifest['inputs']:
            value = data['bundle'] if item['kind'] == 'usage_bundle' else data['profile']
            encoded = contract.canonical_bytes(value)
            Path(item['local_path']).write_bytes(encoded)
            item.update(sha256=hashlib.sha256(encoded).hexdigest(), size_bytes=len(encoded))
            self.base.selected.add(item['sha256'])
        self.wrapper = next(x for x in data['bundle']['evidence_objects'] if x['kind'] == 'epoch_interval_evidence')
        self.digests = [contract.content_id(self.wrapper)] + [contract.content_id(x) for x in pack['evidence_objects']]

    def analyze(self, times):
        def verify(item, value, scope):
            proof = self.base.verify_input(item, value, scope)
            if item['kind'] == 'usage_bundle':
                proof['member_times'] = times
            return proof
        return report.analyze_corpus(copy.deepcopy(self.base.manifest), verify_input=verify,
                                     verify_evidence=self.base.authority)

    def test_epoch_requires_all_independently_timed_evidence(self):
        timely = {digest: '2029-01-01T00:00:00Z' for digest in self.digests}
        valid = self.analyze(timely)
        metrics = [item for item in valid['metrics'] if item['name'] == 'cumulative_interval_input']
        self.assertEqual([item['value'] for item in metrics], ['20'])
        exports.render_exports(valid)
        boundary = self.analyze({digest: self.base.manifest['as_of'] for digest in self.digests})
        self.assertEqual([item['value'] for item in boundary['metrics']
                          if item['name'] == 'cumulative_interval_input'], ['20'])
        allowed = self.base.authority.allowed
        self.base.authority.allowed = [item for item in allowed if item[0] != 'epoch_privacy']
        denied = self.analyze(timely)
        self.assertFalse(any(item['name'] == 'cumulative_interval_input' for item in denied['metrics']))
        self.base.authority.allowed = allowed
        absent = self.analyze({})
        self.assertFalse(any(item['name'] == 'cumulative_interval_input' for item in absent['metrics']))
        self.assertTrue(any(x['reason'] == 'timing_unavailable' for x in absent['exclusions']))
        for digest in self.digests:
            late = dict(timely, **{digest: '2030-01-01T00:00:00Z'})
            result = self.analyze(late)
            self.assertFalse(any(item['name'] == 'cumulative_interval_input' for item in result['metrics']))
            self.assertTrue(any(x['reason'] == 'late_evidence' for x in result['exclusions']))

if __name__ == '__main__':
    unittest.main()
