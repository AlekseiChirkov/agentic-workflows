#!/usr/bin/env python3
"""Freeze bundled source contexts only with independent first-seen evidence."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract
import usage_telemetry_corpus as corpus

spec = importlib.util.spec_from_file_location('report_fixtures', ROOT / 'tests/usage-resolved-report-integration.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class FrozenContextEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.ResolvedReportTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        bundle = copy.deepcopy(self.base.data['bundle'])
        self.wrappers = []
        for context in self.base.data['contexts']:
            wrapper = {'schema_version': 1, 'kind': 'resolution_context_evidence', 'context': context}
            # The wrapper defines its nested evidence as a schema set.
            wrapper = contract.parse_json(contract.canonical_bytes(wrapper))
            self.wrappers.append(wrapper)
            bundle['evidence_objects'].append(wrapper)
            normalized = wrapper['context']
            self.base.authority.allowed = [binding for binding in self.base.authority.allowed
                if not (binding[0] == 'context' and binding[3]['observation_id'] == normalized['observation_id'])]
            observation = next(item for item in bundle['observations']
                               if contract.observation_id(item) == normalized['observation_id'])
            scope = contract.parse_json(contract.canonical_bytes(self.base.data['scope']))
            observation = contract.parse_json(contract.canonical_bytes(observation))
            self.base.authority.allowed.append(('context', scope, observation, copy.deepcopy(normalized)))
        contract.validate_usage_bundle(bundle)
        entry = next(item for item in self.base.manifest['inputs'] if item['kind'] == 'usage_bundle')
        self.base.selected.remove(entry['sha256'])
        data = contract.canonical_bytes(bundle)
        Path(entry['local_path']).write_bytes(data)
        entry.update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        self.base.selected.add(entry['sha256'])
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
                                       if item['kind'] != 'resolution_context']
        self.times = {}
        for wrapper in self.wrappers:
            self.times[contract.content_id(wrapper)] = '2029-01-01T00:00:00Z'
            for proof in wrapper['context']['evidence_objects']:
                self.times[contract.content_id(proof)] = '2029-01-01T00:00:00Z'

    def verify(self, item, value, scope):
        proof = self.base.verify_input(item, value, scope)
        if item['kind'] == 'usage_bundle':
            proof['member_times'] = copy.deepcopy(self.times)
        return proof

    def freeze(self):
        return corpus.freeze_corpus(copy.deepcopy(self.base.manifest), verify_input=self.verify)

    def analyze(self):
        from usage_telemetry_report import analyze_corpus
        return analyze_corpus(copy.deepcopy(self.base.manifest), verify_input=self.verify,
                              verify_evidence=self.base.authority)

    def retained(self, frozen):
        bundle = next(item['value'] for item in frozen['inputs'] if item['kind'] == 'usage_bundle')
        self.assertEqual(contract.validate_usage_bundle(bundle), bundle)
        return [item for item in bundle['evidence_objects']
                if item.get('kind') == 'resolution_context_evidence']

    def test_selected_timed_contexts_survive_and_resolve_real_usage(self):
        kept = self.retained(self.freeze())
        self.assertEqual({contract.content_id(item) for item in kept},
                         {contract.content_id(item) for item in self.wrappers})
        report = self.analyze()
        self.assertEqual(report['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['coverage']['pricing'], {'numerator': 1, 'denominator': 2})
        self.assertEqual(report['pricing']['priced_subtotal_cost'], '0.00289')

    def test_unverified_or_late_wrapper_never_becomes_context(self):
        positive = self.freeze()
        self.assertEqual(len(self.retained(positive)), 2)
        digest = contract.content_id(self.wrappers[1])
        del self.times[digest]
        unknown = self.freeze()
        self.assertEqual(len(self.retained(unknown)), 1)
        self.assertIn('timing_unavailable', [entry['reason'] for entry in unknown['exclusions']])
        self.times[digest] = '2030-01-01T00:00:00Z'
        late = self.freeze()
        self.assertEqual(len(self.retained(late)), 1)
        self.assertIn('late_evidence', [entry['reason'] for entry in late['exclusions']])
        self.assertNotEqual(positive['corpus_id'], late['corpus_id'])

    def test_late_nested_pricing_proof_is_removed_and_bundle_revalidated(self):
        positive = self.freeze()
        self.assertEqual(len(self.retained(positive)), 2)
        wrapper = self.wrappers[0]
        proof = wrapper['context']['evidence_objects'][0]
        proof_id = contract.content_id(proof)
        self.times[proof_id] = '2030-01-01T00:00:00Z'
        late = self.freeze()
        contexts = self.retained(late)
        selected = next(item for item in contexts if item['context']['observation_id'] == wrapper['context']['observation_id'])
        self.assertNotIn(proof_id, {contract.content_id(item) for item in selected['context']['evidence_objects']})
        self.assertIn('late_evidence', [entry['reason'] for entry in late['exclusions']])
        self.assertNotEqual(positive['corpus_id'], late['corpus_id'])

    def test_duplicate_context_evidence_set_permutation_is_equivalent(self):
        positive = self.analyze()
        self.assertEqual(positive['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        context = copy.deepcopy(self.wrappers[0]['context'])
        context['evidence_objects'].reverse()
        self.base.add('duplicate-context', 'resolution_context', context)
        self.base.selected.add(self.base.manifest['inputs'][-1]['sha256'])
        report = self.analyze()
        self.assertEqual(report['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(report['coverage']['pricing'], {'numerator': 1, 'denominator': 2})
        self.assertEqual(report['pricing']['priced_subtotal_cost'], '0.00289')
        self.assertNotEqual(report['corpus_id'], positive['corpus_id'])

    def test_untrusted_context_cannot_invent_known_usage(self):
        positive = self.freeze()
        self.assertEqual(len(self.retained(positive)), 2)
        self.base.authority.allowed = [item for item in self.base.authority.allowed if item[0] != 'context']
        report = self.analyze()
        self.assertNotEqual(report['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
        self.assertIsNone(report['totals']['total_cost'])

    def test_context_without_its_selected_observation_is_rejected(self):
        self.assertEqual(len(self.retained(self.freeze())), 2)
        entry = next(item for item in self.base.manifest['inputs'] if item['kind'] == 'usage_bundle')
        bundle = contract.parse_json(Path(entry['local_path']).read_bytes())
        missing = self.wrappers[0]['context']['observation_id']
        bundle['observations'] = [item for item in bundle['observations']
                                  if contract.observation_id(item) != missing]
        self.base.selected.remove(entry['sha256'])
        data = contract.canonical_bytes(bundle)
        Path(entry['local_path']).write_bytes(data)
        entry.update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        self.base.selected.add(entry['sha256'])
        with self.assertRaises(ValueError):
            self.freeze()


if __name__ == '__main__':
    unittest.main()
