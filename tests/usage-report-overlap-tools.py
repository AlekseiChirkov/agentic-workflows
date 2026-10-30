#!/usr/bin/env python3
"""Tool records in separate profiles cannot silently double-count one usage."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tests' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool_fixture = load('tool_fixture', 'usage-outcome-tool-cost.py')
multi = load('multi', 'usage-multibundle-report.py')


class OverlapToolTests(unittest.TestCase):
    def build_case(self, *, duplicate):
        case = tool_fixture.OutcomeToolCostTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        positive = case.analyze()
        self.assertEqual(positive['totals']['total_cost'], '0.02578')
        helper = multi.MultiBundleReportTests()
        helper.base = case.base
        alternate = helper.add_second_profile()
        tool = copy.deepcopy(case.tool)
        if not duplicate:
            tool['usage_id'] = 'sha256:' + 'e' * 64
        tool['profile_id'] = alternate['profile']['profile_id']
        tool['profile_version'] = alternate['profile']['profile_version']
        for item in tool['evidence_objects']:
            item['profile_id'] = tool['profile_id']
        quantity = next(item for item in tool['evidence_objects'] if item['kind'] == 'tool_quantity_evidence')
        inventory = alternate['bundle']['inventories'][0]
        proof = next(item for item in alternate['bundle']['evidence_objects'] if item['kind'] == 'inventory_evidence')
        declaration = {'inventory_evidence': proof, 'tool_usage_ids': [tool['usage_id']]}
        case.fixture.add('alternate-tool', 'tool_usage', tool)
        case.fixture.authorize('tool_privacy', case.scope, tool, tool)
        case.fixture.authorize('tool_usage', case.scope, tool, quantity)
        for kind in ('tool_inventory', 'tool_nonoverlap'):
            case.fixture.authorize(kind, case.scope, inventory, declaration)
        for item in tool['evidence_objects']:
            if item['kind'] != 'tool_quantity_evidence':
                case.fixture.authorize('pricing_context', case.scope, tool, item)
        return case, inventory, tool

    def test_duplicate_tool_identity_across_profiles_never_becomes_a_complete_sum(self):
        case, _, _ = self.build_case(duplicate=True)
        try:
            result = case.analyze()
        except ValueError:
            return
        self.assertIsNone(result['totals']['total_cost'])
        self.assertNotEqual(result['outcomes']['coverage'], 'complete')

    def test_distinct_tool_ids_need_independent_complete_nonoverlap_union(self):
        case, second_inventory, tool = self.build_case(duplicate=False)
        first_inventory = case.base.data['bundle']['inventories'][0]
        groups = [{'inventory_id': contract.content_id(first_inventory), 'tool_usage_ids': [case.tool['usage_id']]},
                  {'inventory_id': contract.content_id(second_inventory), 'tool_usage_ids': [tool['usage_id']]}]
        declaration = {'groups': sorted(groups, key=lambda item: item['inventory_id'])}
        denied = case.analyze()
        self.assertIsNone(denied['totals']['total_cost'])
        case.fixture.authorize('tool_inventory_union', case.scope, declaration, declaration)
        allowed = case.analyze()
        self.assertEqual(allowed['totals']['total_cost'], '0.05156')
        self.assertNotEqual(denied['corpus_id'], allowed['corpus_id'])


if __name__ == '__main__':
    unittest.main()
