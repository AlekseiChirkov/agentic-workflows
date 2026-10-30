#!/usr/bin/env python3
"""Exercise retrospective coverage and pricing using the real resolver."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract
import usage_telemetry_report as report


def fixture_module():
    path = ROOT / 'tests/usage-resolution-integration.py'
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location('resolution_fixture', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ResolvedReportTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module()
        self.assertIsNotNone(self.fixture, 'real pricing resolver fixtures are unavailable')
        self.data, bindings = self.fixture.fixture()
        # Independent authorization refers to canonical values, including
        # schema-defined sets that may have a different source ordering.
        def canonical(value):
            return contract.parse_json(contract.canonical_bytes(value))
        self.allowed = [(kind, canonical(scope), canonical(subject), canonical(evidence))
                        for kind, scope, subject, evidence in bindings]
        self.authority = self.fixture.Verifier(self.allowed)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.manifest = {
            'schema_version': 1, 'kind': 'analysis_corpus', 'as_of': self.data['as_of'],
            'scope': copy.deepcopy(self.data['scope']), 'scenario_id': self.data['scenario']['scenario_id'],
            'versions': {'bundle_schema_version': 1, 'receipt_schema_version': 1,
                         'price_schema_version': 1, 'normalizer_version': '1'},
            'identifier_mappings': [], 'inputs': [], 'exclusions': [],
            'max_source_bytes': 1000000, 'max_total_bytes': 10000000, 'max_records': 1000,
        }
        self.add('bundle', 'usage_bundle', self.data['bundle'])
        self.add('profile', 'source_profile', self.data['profile'])
        self.add('scenario', 'pricing_scenario', self.data['scenario'])
        for index, snapshot in enumerate(self.data['snapshots']):
            self.add('snapshot' + str(index), 'price_snapshot', snapshot)
        for index, context in enumerate(self.data['contexts']):
            self.add('context' + str(index), 'resolution_context', context)
        for index, evidence in enumerate(self.data['price_evidence']):
            self.add('evidence' + str(index), 'price_evidence', evidence)
        self.selected = {item['sha256'] for item in self.manifest['inputs']}

    def add(self, name, kind, value):
        raw = contract.canonical_bytes(value)
        path = self.directory / (name + '.json')
        path.write_bytes(raw)
        self.manifest['inputs'].append({'kind': kind, 'schema_version': 1,
                                        'local_path': str(path),
                                        'sha256': hashlib.sha256(raw).hexdigest(),
                                        'size_bytes': len(raw)})

    def verify_input(self, item, value, scope):
        if item['sha256'] not in self.selected or scope != self.data['scope']:
            raise ValueError('input was not independently authorized')
        proof = {'scope': copy.deepcopy(scope), 'observed_at': '2029-01-01T00:00:00Z'}
        if item['kind'] == 'resolution_context':
            proof['member_times'] = {contract.content_id(evidence): '2029-01-01T00:00:00Z'
                                     for evidence in value['evidence_objects']}
        return proof

    def analyze(self):
        return report.analyze_corpus(copy.deepcopy(self.manifest), verify_input=self.verify_input,
                                     verify_evidence=self.authority)

    def test_real_selected_work_has_full_token_and_partial_pricing_coverage(self):
        result = self.analyze()
        self.assertEqual(result['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(result['coverage']['pricing'], {'numerator': 1, 'denominator': 2})
        self.assertEqual(result['completeness']['measurements'], 'complete')
        self.assertEqual(result['completeness']['pricing'], 'partial')
        self.assertIsNone(result['totals']['total_cost'])
        self.assertEqual(result['pricing']['priced_subtotal_cost'], '0.00289')
        self.assertEqual(result['pricing']['subtotal_quality'], 'proven_lower_bound')

    def test_changed_independent_assertions_change_identity_and_cannot_forge_coverage(self):
        trusted = self.analyze()
        self.authority.allowed = [item for item in self.allowed if item[0] != 'inventory']
        denied = self.analyze()
        self.assertNotEqual(trusted['corpus_id'], denied['corpus_id'])
        self.assertIsNone(denied['coverage']['pricing']['denominator'])
        self.assertIsNone(denied['totals']['total_cost'])

    def test_unselected_scenario_or_context_is_never_discovered(self):
        selected = self.analyze()
        scenario = next(item for item in self.manifest['inputs'] if item['kind'] == 'pricing_scenario')
        self.manifest['inputs'].remove(scenario)
        try:
            result = self.analyze()
        except ValueError:
            return
        self.assertNotEqual(result['corpus_id'], selected['corpus_id'])
        self.assertIsNone(result['totals']['total_cost'])
        self.assertEqual(result['coverage']['pricing'], {'numerator': 0, 'denominator': 2})
        self.assertIsNone(result['pricing']['priced_subtotal_cost'])


if __name__ == '__main__':
    unittest.main()
