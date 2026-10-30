#!/usr/bin/env python3
"""Verify multi-bundle retrospectives using explicitly selected evidence."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract
import usage_telemetry_exports as exports

spec = importlib.util.spec_from_file_location('report_fixtures', ROOT / 'tests/usage-resolved-report-integration.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def canonical(value):
    return contract.parse_json(contract.canonical_bytes(value))


class MultiBundleReportTests(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.ResolvedReportTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)

    def add(self, name, kind, value):
        self.base.add(name, kind, value)
        self.base.selected.add(self.base.manifest['inputs'][-1]['sha256'])

    def remove_original_bundle(self):
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
                                       if item['kind'] != 'usage_bundle']

    @staticmethod
    def summary(report):
        tokens = {item['name']: item['value'] for item in report['metrics']}
        return (report['coverage'], report['completeness']['measurements'],
                report['pricing'], tokens)

    def test_two_explicit_partial_bundles_preserve_full_inventory(self):
        original = self.base.analyze()
        bundle = self.base.data['bundle']
        self.remove_original_bundle()
        for index, observation in enumerate(bundle['observations']):
            part = copy.deepcopy(bundle)
            part['observations'] = [copy.deepcopy(observation)]
            contract.validate_usage_bundle(part)
            self.add('partition-' + str(index), 'usage_bundle', part)
        report = self.base.analyze()
        self.assertEqual(self.summary(report), self.summary(original))
        self.assertEqual(report['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['coverage']['pricing'], {'numerator': 1, 'denominator': 2})
        self.assertEqual(report['pricing']['priced_subtotal_cost'], '0.00289')
        self.assertNotEqual(report['corpus_id'], original['corpus_id'])
        reversed_manifest = copy.deepcopy(self.base.manifest)
        reversed_manifest['inputs'].reverse()
        from usage_telemetry_report import analyze_corpus
        reversed_report = analyze_corpus(reversed_manifest, verify_input=self.base.verify_input,
                                         verify_evidence=self.base.authority)
        self.assertEqual(exports.render_exports(report), exports.render_exports(reversed_report))

    def test_duplicate_selected_bundle_does_not_double_count(self):
        original = self.base.analyze()
        self.add('duplicate', 'usage_bundle', copy.deepcopy(self.base.data['bundle']))
        report = self.base.analyze()
        self.assertEqual(self.summary(report), self.summary(original))
        self.assertEqual(report['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['pricing']['priced_subtotal_cost'], '0.00289')
        self.assertNotEqual(report['corpus_id'], original['corpus_id'])

    def alternate_fixture(self, *, overlap=False, conflict=False, different_provider=False):
        module = self.base.fixture
        original_profile = module.profiles.profile
        original_split = module.profiles.split_bundle
        original_opaque = module.opaque
        original_inventory_opaque = module.inventories.opaque
        def alternate_profile(*args, **kwargs):
            value = copy.deepcopy(original_profile(*args, **kwargs))
            value['profile_id'] = 'alternate-profile'
            value['provider'] = 'synthetic-provider' if overlap and not different_provider else 'alternate-provider'
            return value
        def alternate_split():
            value = copy.deepcopy(original_split())
            value['profile_id'] = 'alternate-profile'
            for observation in value['observations']:
                observation['profile_id'] = 'alternate-profile'
            return value
        def alternate_opaque(char):
            return original_opaque(char if overlap else {'1': '3', '2': '4'}.get(char, char))
        try:
            module.profiles.profile = alternate_profile
            module.profiles.split_bundle = alternate_split
            module.opaque = alternate_opaque
            module.inventories.opaque = alternate_opaque
            raw = ({'input': 2000, 'read': 200, 'write': 200, 'short': 100,
                    'long': 100, 'output': 100, 'reasoning': 25} if conflict else None)
            data, bindings = module.fixture(raw_override=raw)
        finally:
            module.profiles.profile = original_profile
            module.profiles.split_bundle = original_split
            module.opaque = original_opaque
            module.inventories.opaque = original_inventory_opaque
        contract.validate_source_profile(data['profile'])
        contract.validate_usage_bundle(data['bundle'])
        self.assertEqual(data['scope'], self.base.data['scope'])
        self.assertNotEqual(data['profile']['profile_id'], self.base.data['profile']['profile_id'])
        return data, bindings

    def add_second_profile(self, *, overlap=False, conflict=False, different_provider=False):
        data, bindings = self.alternate_fixture(overlap=overlap, conflict=conflict,
                                                different_provider=different_provider)
        self.add('alternate-profile', 'source_profile', data['profile'])
        self.add('alternate-bundle', 'usage_bundle', data['bundle'])
        for index, context in enumerate(data['contexts']):
            self.add('alternate-context-' + str(index), 'resolution_context', context)
        self.base.authority.allowed.extend((kind, canonical(scope), canonical(subject), canonical(evidence))
                                           for kind, scope, subject, evidence in bindings)
        inventory_ids = sorted(contract.content_id(item) for item in
            (self.base.data['bundle']['inventories'][0], data['bundle']['inventories'][0]))
        union = {'inventory_ids': inventory_ids}
        # This is independently held authorization for the exact selected set,
        # including completeness and nonoverlap across the two inventories.
        self.base.authority.allowed.append(('inventory_union', canonical(data['scope']), union, union))
        return data

    def test_two_profiles_combine_only_with_independent_inventory_union(self):
        original = self.base.analyze()
        self.add_second_profile()
        report = self.base.analyze()
        self.assertEqual(report['coverage']['measurements'], {'numerator': 4, 'denominator': 4})
        self.assertEqual(report['coverage']['pricing'], {'numerator': 2, 'denominator': 4})
        self.assertEqual(report['pricing']['priced_subtotal_cost'], '0.00578')
        self.assertEqual(report['completeness']['measurements'], 'complete')
        tokens = {item['name']: item['value'] for item in report['metrics']}
        self.assertEqual(tokens['input_tokens'], '4000')
        self.assertEqual(tokens['output_tokens'], '400')
        self.assertTrue(any(call[0] == 'inventory_union' for call in self.base.authority.calls))
        self.assertNotEqual(report['corpus_id'], original['corpus_id'])

    def test_cross_profile_same_responses_are_deduplicated_once(self):
        original = self.base.analyze()
        self.add_second_profile(overlap=True)
        report = self.base.analyze()
        self.assertEqual(self.summary(report), self.summary(original))
        self.assertEqual(report['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['coverage']['pricing'], {'numerator': 1, 'denominator': 2})
        self.assertEqual(report['pricing']['priced_subtotal_cost'], '0.00289')
        self.assertTrue(any(call[0] == 'inventory_union' for call in self.base.authority.calls))
        self.assertNotEqual(report['corpus_id'], original['corpus_id'])

    def test_conflicting_cross_profile_response_is_not_summed_or_selected(self):
        positive = self.base.analyze()
        self.assertEqual(positive['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.add_second_profile(overlap=True, conflict=True)
        try:
            report = self.base.analyze()
        except ValueError:
            return
        self.assertNotEqual(report['completeness']['measurements'], 'complete')
        self.assertIsNone(report['totals']['total_cost'])
        self.assertNotEqual(report['pricing']['priced_subtotal_cost'], '0.00578')

    def test_same_response_ids_from_different_providers_are_not_silently_unified(self):
        positive = self.base.analyze()
        self.assertEqual(positive['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        # The alternate profile is structurally valid, but inventories do not
        # carry provider scope for these colliding opaque response references.
        self.add_second_profile(overlap=True, different_provider=True)
        try:
            report = self.base.analyze()
        except ValueError:
            return
        self.assertNotEqual(report['completeness']['measurements'], 'complete')
        self.assertIsNone(report['totals']['total_cost'])

    def test_missing_selected_profile_does_not_claim_complete_measurements(self):
        self.add_second_profile()
        positive = self.base.analyze()
        self.assertEqual(positive['coverage']['measurements'], {'numerator': 4, 'denominator': 4})
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
            if not (item['kind'] == 'source_profile' and
                    contract.parse_json(Path(item['local_path']).read_bytes())['profile_id'] == 'alternate-profile')]
        try:
            result = self.base.analyze()
        except ValueError:
            return
        self.assertNotEqual(result['coverage']['measurements'], {'numerator': 4, 'denominator': 4})
        self.assertNotEqual(result['completeness']['measurements'], 'complete')
        self.assertIsNone(result['totals']['total_cost'])

    def test_untrusted_inventory_union_does_not_invent_a_denominator(self):
        self.add_second_profile()
        positive = self.base.analyze()
        self.assertEqual(positive['coverage']['measurements'], {'numerator': 4, 'denominator': 4})
        self.base.authority.allowed = [item for item in self.base.authority.allowed
                                       if item[0] != 'inventory_union']
        denied = self.base.analyze()
        self.assertIsNone(denied['coverage']['measurements']['denominator'])
        self.assertIsNone(denied['coverage']['pricing']['denominator'])
        self.assertIsNone(denied['totals']['total_cost'])
        self.assertNotEqual(denied['completeness']['measurements'], 'complete')
        self.assertNotEqual(denied['corpus_id'], positive['corpus_id'])


if __name__ == '__main__':
    unittest.main()
