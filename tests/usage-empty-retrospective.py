#!/usr/bin/env python3
"""Check reports for independently proven empty request inventories."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract
import usage_telemetry_exports as exports


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tests' / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixtures = load('resolved_fixtures', 'usage-resolved-report-integration.py')
inventories = load('inventory_fixtures', 'usage-inventory-completeness.py')


class EmptyRetrospectiveTests(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.ResolvedReportTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        inventory, _ = inventories.inventory(())
        inventory['profile_id'] = self.base.data['profile']['profile_id']
        inventory['window']['end'] = '2029-01-01T00:00:00Z'
        inventory['observed_at'] = '2029-01-01T00:00:01Z'
        inventory, evidence = inventories.bind(inventory)
        self.inventory, self.evidence = inventory, evidence
        bundle = copy.deepcopy(self.base.data['bundle'])
        bundle['observations'] = []
        bundle['inventories'] = [inventory]
        bundle['evidence_objects'] = [evidence]
        contract.validate_usage_bundle(bundle)
        item = next(entry for entry in self.base.manifest['inputs'] if entry['kind'] == 'usage_bundle')
        self.base.selected.remove(item['sha256'])
        data = contract.canonical_bytes(bundle)
        Path(item['local_path']).write_bytes(data)
        item.update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        self.base.selected.add(item['sha256'])
        self.base.manifest['inputs'] = [entry for entry in self.base.manifest['inputs']
                                        if entry['kind'] != 'resolution_context']
        def canonical(value):
            return contract.parse_json(contract.canonical_bytes(value))
        for kind in ('inventory', 'nonnegative_scope', 'tool_scope_empty'):
            self.base.authority.allowed.append((kind, canonical(self.base.data['scope']),
                                                 canonical(inventory), canonical(evidence)))

    def test_empty_request_coverage_is_not_applicable_and_exportable(self):
        value = self.base.analyze()
        self.assertEqual(value['completeness']['measurements'], 'not_applicable')
        self.assertEqual(value['completeness']['pricing'], 'not_applicable')
        self.assertEqual(value['coverage']['measurements'], {'numerator': None, 'denominator': None})
        self.assertEqual(value['coverage']['pricing'], {'numerator': None, 'denominator': None})
        rendered = exports.render_exports(value)
        decoded = json.loads(rendered['json'])
        self.assertEqual(decoded['completeness']['pricing'], 'not_applicable')
        self.assertIn('not_applicable', rendered['csv'])
        self.assertIn('not_applicable', rendered['markdown'])

    def test_zero_cost_requires_independent_empty_tool_scope(self):
        value = self.base.analyze()
        self.assertEqual(value['totals']['total_cost'], '0')
        self.base.authority.allowed = [entry for entry in self.base.authority.allowed
                                       if entry[0] != 'tool_scope_empty']
        unavailable = self.base.analyze()
        self.assertIsNone(unavailable['totals']['total_cost'])
        self.assertNotEqual(value['corpus_id'], unavailable['corpus_id'])


if __name__ == '__main__':
    unittest.main()
