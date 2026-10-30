#!/usr/bin/env python3
"""Require evidence-backed revisions, contributors, terms and cost breakdowns."""
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

spec = importlib.util.spec_from_file_location('report_fixtures', ROOT / 'tests/usage-resolved-report-integration.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def canonical(value):
    return contract.parse_json(contract.canonical_bytes(value))


class EvidenceBackedReportTests(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.ResolvedReportTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.scope = copy.deepcopy(self.base.data['scope'])
        self.leaves = [{'owner_kind': 'task', 'owner_id': 'sha256:' + char * 64}
                       for char in ('8', '9')]
        self.configure_current_prices()
        self.metadata = {'schema_version': 1, 'kind': 'revision_metadata', 'scope': self.scope,
                         'source_hash': hashlib.sha256(b'private source revision').hexdigest(),
                         'expanded_hash': hashlib.sha256(b'private expanded revision').hexdigest(),
                         'observed_at': '2028-01-02T00:00:00Z'}
        self.add('revision-metadata', 'revision_metadata', self.metadata)
        self.authorize('revision_metadata', self.scope, self.metadata, self.metadata)
        inventory = self.base.data['bundle']['inventories'][0]
        inventory_proof = next(item for item in self.base.data['bundle']['evidence_objects']
                               if item['kind'] == 'inventory_evidence')
        self.authorize('tool_scope_empty', self.scope, inventory, inventory_proof)
        self.entries = []
        for observation, leaf in zip(self.base.data['bundle']['observations'], self.leaves):
            entry = {'observation_id': contract.observation_id(observation),
                     'observed_at': '2028-01-03T00:00:00Z',
                     'attribution': {'response_id': observation['response_id'],
                                     'provider': self.base.data['profile']['provider'],
                                     'provider_scope': observation['provider_scope'],
                                     'owner_kind': 'task', 'owner_id': leaf['owner_id'],
                                     'candidates': [], 'basis': 'correlation'}}
            self.entries.append(entry)
        self.ownership = {'schema_version': 1, 'kind': 'ownership_selection',
                          'owner_scopes': [self.scope, *self.leaves],
                          'entries': self.entries, 'observed_at': '2028-01-03T00:00:00Z'}
        self.add('ownership', 'ownership_selection', self.ownership)
        for context in self.base.data['contexts']:
            self.authorize('model_privacy', self.scope, context, context['parameters']['model'])
        for scope in [self.scope, *self.leaves]:
            self.authorize('ownership_inventory', scope, inventory, inventory_proof)
            if scope in self.leaves:
                self.authorize('leaf_billable_scope', scope, inventory, inventory_proof)
                self.authorize('owner_privacy', scope, scope, scope)
            for observation, entry in zip(self.base.data['bundle']['observations'], self.entries):
                self.authorize('ownership', scope, observation, entry)
                if scope == self.scope:
                    self.authorize('ownership_descendant', scope, observation, entry)
                elif entry['attribution']['owner_id'] != scope['owner_id']:
                    self.authorize('ownership_exclusion', scope, observation, entry)

    def configure_current_prices(self):
        snapshot = self.base.data['snapshots'][0]
        period = next(item for item in self.base.data['price_evidence'] if item['kind'] == 'price_period_evidence')
        period['end'] = '2029-01-01T00:00:00Z'
        snapshot['effective_period']['end'] = period['end']
        snapshot['effective_period']['evidence'] = contract.content_id(period)
        snapshot_id = contract.price_snapshot_id(snapshot)
        self.base.data['scenario']['snapshot_ids'] = [snapshot_id]
        for proof in self.base.data['price_evidence']:
            if proof['kind'] == 'price_snapshot_evidence':
                proof['snapshot_id'] = snapshot_id
        self.base.authority.allowed = [entry for entry in self.base.authority.allowed if entry[0] != 'price']
        for proof in self.base.data['price_evidence']:
            self.authorize('price', self.scope, snapshot, proof)
        for entry in self.base.manifest['inputs']:
            if entry['kind'] == 'price_snapshot':
                value = snapshot
            elif entry['kind'] == 'pricing_scenario':
                value = self.base.data['scenario']
            elif entry['kind'] == 'price_evidence':
                old = contract.parse_json(Path(entry['local_path']).read_bytes())
                value = next(item for item in self.base.data['price_evidence'] if item['kind'] == old['kind'])
            else:
                continue
            self.base.selected.remove(entry['sha256'])
            data = contract.canonical_bytes(value)
            Path(entry['local_path']).write_bytes(data)
            entry.update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
            self.base.selected.add(entry['sha256'])
        control = self.base.analyze()
        self.assertEqual(control['coverage']['pricing'], {'numerator': 2, 'denominator': 2})
        self.assertEqual(control['pricing']['priced_subtotal_cost'], '0.00578')

    def add(self, name, kind, value):
        self.base.add(name, kind, value)
        self.base.selected.add(self.base.manifest['inputs'][-1]['sha256'])

    def authorize(self, kind, scope, subject, evidence):
        self.base.authority.allowed.append((kind, canonical(scope), canonical(subject), canonical(evidence)))

    def verify_input(self, item, value, scope):
        proof = self.base.verify_input(item, value, scope)
        if item['kind'] == 'ownership_selection':
            proof['member_times'] = {contract.content_id(entry): '2029-01-01T00:00:00Z'
                                     for entry in value['entries']}
        return proof

    def analyze(self):
        from usage_telemetry_report import analyze_corpus
        return analyze_corpus(copy.deepcopy(self.base.manifest), verify_input=self.verify_input,
                              verify_evidence=self.base.authority)

    def test_revision_requires_exact_independent_authority(self):
        allowed = self.analyze()
        self.assertEqual((allowed['source_hash'], allowed['expanded_hash']),
                         (self.metadata['source_hash'], self.metadata['expanded_hash']))
        self.base.authority.allowed = [entry for entry in self.base.authority.allowed
                                       if entry[0] != 'revision_metadata']
        denied = self.analyze()
        self.assertIsNone(denied['source_hash'])
        self.assertIsNone(denied['expanded_hash'])
        self.assertNotEqual(allowed['corpus_id'], denied['corpus_id'])

    def test_model_publication_needs_independent_authority(self):
        positive = self.analyze()
        self.assertTrue(any(item['value'] == 'vendor/model' for item in positive['slices']))
        self.base.authority.allowed = [item for item in self.base.authority.allowed
                                       if item[0] != 'model_privacy']
        denied = self.analyze()
        self.assertFalse(any(item['value'] == 'vendor/model' for item in denied['slices']))
        for content in exports.render_exports(denied).values():
            self.assertNotIn('vendor/model', content)
        self.assertNotEqual(positive['corpus_id'], denied['corpus_id'])

    def test_owner_publication_needs_independent_authority(self):
        positive = self.analyze()
        self.assertEqual({item['owner_id'] for item in positive['top_leaves']},
                         {item['owner_id'] for item in self.leaves})
        self.base.authority.allowed = [item for item in self.base.authority.allowed
                                       if item[0] != 'owner_privacy']
        denied = self.analyze()
        for content in exports.render_exports(denied).values():
            for scope in self.leaves:
                self.assertNotIn(scope['owner_id'], content)
        self.assertNotEqual(positive['corpus_id'], denied['corpus_id'])

    def test_ownership_members_require_independent_cutoff(self):
        import usage_telemetry_corpus as corpus
        original = self.verify_input
        def verifier(item, value, scope):
            proof = original(item, value, scope)
            if item['kind'] == 'ownership_selection':
                proof['member_times'].pop(contract.content_id(value['entries'][0]))
                proof['member_times'][contract.content_id(value['entries'][1])] = '2029-01-03T00:00:00Z'
            return proof
        frozen = corpus.freeze_corpus(copy.deepcopy(self.base.manifest), verify_input=verifier)
        selection = next(item['value'] for item in frozen['inputs'] if item['kind'] == 'ownership_selection')
        self.assertEqual(selection['entries'], [])
        reasons = {item['reason'] for item in frozen['exclusions']}
        self.assertTrue({'timing_unavailable', 'late_evidence'} <= reasons)

    def test_six_verified_leaves_are_ranked_by_actual_cost_and_capped_at_five(self):
        bundle = self.base.data['bundle']
        profile = self.base.data['profile']
        contexts = self.base.data['contexts']
        for number in range(3, 7):
            raw = {'input': 1000 + 100 * number, 'read': 200, 'write': 200,
                   'short': 100, 'long': 100, 'output': 100, 'reasoning': 25}
            normalized = contract.normalize_source_counters(profile, {'usage': raw},
                profile_version='1', source_hash='a' * 64, record_number=number)
            for measurement in normalized['measurements'].values():
                parts = [item['tokens'] for item in measurement] if isinstance(measurement, list) else [measurement]
                for part in parts:
                    if part['measurement_state'] == 'partial':
                        part['measurement_state'] = 'final'
            observation = copy.deepcopy(bundle['observations'][1])
            observation.update(record_number=number, response_id='sha256:' + str(number) * 64,
                               call_id='sha256:' + str(number) * 64,
                               measurements=normalized['measurements'])
            bundle['observations'].append(observation)
            bundle['evidence_objects'].extend(normalized['evidence_objects'])
            context = copy.deepcopy(contexts[1])
            context.update(record_number=number, observation_id=contract.observation_id(observation))
            for proof in context['evidence_objects']:
                proof['record_number'] = number
            contexts.append(context)
            self.add('ranking-context-' + str(number), 'resolution_context', context)
            self.authorize('context', self.scope, observation, context)
            self.authorize('response_privacy', self.scope, observation, observation)
            self.authorize('model_privacy', self.scope, context, context['parameters']['model'])
            for proof in context['evidence_objects']:
                self.authorize('pricing_context', self.scope, observation, proof)
            objects = {contract.content_id(item): item for item in bundle['evidence_objects']}
            def authorize_operand(digest):
                proof = objects[digest]
                if proof['kind'] == 'derived_measurement_evidence':
                    for operand in proof['operands']:
                        authorize_operand(operand)
                else:
                    subject = {'observation': observation, 'field': proof['field']}
                    if 'ttl' in proof:
                        subject['ttl'] = proof['ttl']
                    self.authorize('measurement', self.scope, subject, proof)
            for field, measurement in observation['measurements'].items():
                parts = measurement if isinstance(measurement, list) else [measurement]
                for part in parts:
                    token = part['tokens'] if isinstance(measurement, list) else part
                    if 'evidence' in token:
                        subject = {'observation': observation, 'field': field}
                        if isinstance(measurement, list):
                            subject['ttl'] = part['ttl']
                        self.authorize('measurement', self.scope, subject, objects[token['evidence']])
                        authorize_operand(token['evidence'])
        inventory = bundle['inventories'][0]
        inventory['expected_calls'] = [{'call_id': item['call_id']} for item in bundle['observations']]
        inventory['expected_responses'] = [{'call_id': item['call_id'], 'response_id': item['response_id']}
                                           for item in bundle['observations']]
        inventory, proof = self.base.fixture.inventories.bind(inventory)
        bundle['evidence_objects'] = [item for item in bundle['evidence_objects']
                                    if item['kind'] != 'inventory_evidence'] + [proof]
        contract.validate_usage_bundle(bundle)
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
                                       if item['kind'] not in ('usage_bundle', 'ownership_selection')]
        self.add('ranking-bundle', 'usage_bundle', bundle)
        self.leaves = [{'owner_kind': 'task', 'owner_id': 'sha256:' + char * 64} for char in '89abcd']
        entries = [{'observation_id': contract.observation_id(observation), 'observed_at': '2028-01-03T00:00:00Z',
                    'attribution': {'response_id': observation['response_id'], 'provider': profile['provider'],
                                    'provider_scope': observation['provider_scope'], 'owner_kind': 'task',
                                    'owner_id': leaf['owner_id'], 'candidates': [], 'basis': 'correlation'}}
                   for observation, leaf in zip(bundle['observations'], self.leaves)]
        self.add('ranking-ownership', 'ownership_selection', {'schema_version': 1, 'kind': 'ownership_selection',
                 'owner_scopes': [self.scope, *self.leaves], 'entries': entries, 'observed_at': '2028-01-03T00:00:00Z'})
        for kind in ('inventory', 'nonnegative_scope', 'tool_scope_empty'):
            self.authorize(kind, self.scope, inventory, proof)
        for scope in [self.scope, *self.leaves]:
            self.authorize('ownership_inventory', scope, inventory, proof)
            if scope != self.scope:
                self.authorize('leaf_billable_scope', scope, inventory, proof)
                self.authorize('owner_privacy', scope, scope, scope)
            for observation, entry in zip(bundle['observations'], entries):
                self.authorize('ownership', scope, observation, entry)
                if scope == self.scope:
                    self.authorize('ownership_descendant', scope, observation, entry)
                elif scope['owner_id'] != entry['attribution']['owner_id']:
                    self.authorize('ownership_exclusion', scope, observation, entry)
        report = self.analyze()
        self.assertEqual(report['coverage']['pricing'], {'numerator': 6, 'denominator': 6})
        self.assertEqual(report['totals']['total_cost'], '0.02094')
        ranked = report['top_leaves']
        self.assertEqual(len(ranked), 5)
        self.assertEqual([item['owner_id'] for item in ranked[:4]], [leaf['owner_id'] for leaf in self.leaves[:1:-1]])
        self.assertIn(ranked[4]['owner_id'], {leaf['owner_id'] for leaf in self.leaves[:2]})
        self.assertEqual([item['cost_usd'] for item in ranked], ['0.00409', '0.00389', '0.00369', '0.00349', '0.00289'])

    def test_repricing_is_conditional_in_all_report_cost_views(self):
        snapshot = self.base.data['snapshots'][0]
        scenario = self.base.data['scenario']
        snapshot['effective_period'] = {'state': 'unknown', 'reason': 'historical_period_unavailable'}
        scenario['basis'] = 'reprice'
        scenario['assumptions'] = {'region': 'example-region'}
        scenario['source_parameters']['region'] = None
        scenario['snapshot_ids'] = [contract.price_snapshot_id(snapshot)]
        for proof in self.base.data['price_evidence']:
            if proof['kind'] == 'price_snapshot_evidence':
                proof['snapshot_id'] = contract.price_snapshot_id(snapshot)
        self.base.authority.allowed = [entry for entry in self.base.authority.allowed if entry[0] != 'price']
        for proof in self.base.data['price_evidence']:
            self.authorize('price', self.scope, snapshot, proof)
        for entry in self.base.manifest['inputs']:
            if entry['kind'] == 'price_snapshot':
                value = snapshot
            elif entry['kind'] == 'pricing_scenario':
                value = scenario
            elif entry['kind'] == 'price_evidence':
                old = contract.parse_json(Path(entry['local_path']).read_bytes())
                value = next(item for item in self.base.data['price_evidence'] if item['kind'] == old['kind'])
            else:
                continue
            self.base.selected.remove(entry['sha256'])
            raw = contract.canonical_bytes(value)
            Path(entry['local_path']).write_bytes(raw)
            entry.update(sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
            self.base.selected.add(entry['sha256'])
        report = self.analyze()
        self.assertEqual(report['coverage']['pricing'], {'numerator': 2, 'denominator': 2})
        self.assertIsNone(report['totals']['total_cost'])
        self.assertEqual(report['pricing']['priced_subtotal_cost'], '0.00578')
        self.assertIs(report['pricing']['conditional'], True)
        for field in ('terms', 'contributors', 'slices', 'top_leaves'):
            self.assertTrue(report[field])
            self.assertTrue(all(item['conditional'] is True for item in report[field]))
        for rendered in exports.render_exports(report).values():
            self.assertIn('conditional', rendered)

    def test_selected_revision_and_independently_verified_attribution_are_visible(self):
        report = self.analyze()
        self.assertEqual(report['source_hash'], self.metadata['source_hash'])
        self.assertEqual(report['expanded_hash'], self.metadata['expanded_hash'])
        self.assertEqual(report['completeness']['identity'], 'complete')
        self.assertEqual(report['completeness']['attribution'], 'complete')
        self.assertEqual(report['totals']['total_cost'], '0.00578')
        self.assertEqual(len(report['contributors']), 2)
        self.assertEqual(sorted(item['amount'] for item in report['contributors']), ['0.00289', '0.00289'])
        artifacts = exports.render_exports(report)
        self.assertEqual(json.loads(artifacts['json'])['source_hash'], self.metadata['source_hash'])
        for content in artifacts.values():
            self.assertIn(self.metadata['expanded_hash'], content)
            self.assertNotIn(str(self.base.directory), content)
            self.assertNotIn('private source revision', content)

    def test_price_terms_come_from_actual_independently_verified_rates(self):
        report = self.analyze()
        amounts = sorted(item['amount'] for item in report['terms'])
        self.assertEqual(amounts, sorted(['0.0012', '0.00004', '0.00025', '0.0004', '0.001'] * 2))
        self.assertEqual(report['totals']['total_cost'], '0.00578')
        artifacts = exports.render_exports(report)
        for content in artifacts.values():
            for amount in ('0.0012', '0.00004', '0.00025', '0.0004', '0.001'):
                self.assertIn(amount, content)

    def test_model_breakdown_and_leaf_ranking_require_proven_scope(self):
        report = self.analyze()
        model = next(item for item in report['slices']
                     if item['dimension'] == 'model' and item['value'] == 'vendor/model')
        self.assertEqual(model['count'], 2)
        self.assertEqual(model['cost_usd'], '0.00578')
        self.assertEqual(model['coverage'], 'complete')
        self.assertIn('role', report['unavailable_dimensions'])
        self.assertIn('effort', report['unavailable_dimensions'])
        self.assertEqual(len(report['top_leaves']), 2)
        self.assertEqual({item['owner_id'] for item in report['top_leaves']},
                         {leaf['owner_id'] for leaf in self.leaves})
        self.assertTrue(all(item['cost_usd'] == '0.00289' and item['coverage'] == 'complete'
                            for item in report['top_leaves']))

    def test_unverified_revision_or_ownership_never_becomes_a_claim(self):
        positive = self.analyze()
        self.assertEqual(positive['completeness']['attribution'], 'complete')
        self.base.authority.allowed = [item for item in self.base.authority.allowed
                                       if item[0] not in ('revision_metadata', 'ownership')]
        denied = self.analyze()
        self.assertIsNone(denied['source_hash'])
        self.assertIsNone(denied['expanded_hash'])
        self.assertNotEqual(denied['completeness']['attribution'], 'complete')
        self.assertEqual(denied['top_leaves'], [])
        self.assertNotEqual(denied['corpus_id'], positive['corpus_id'])

    def test_unverified_response_identity_never_claims_complete(self):
        positive = self.analyze()
        self.assertEqual(positive['completeness']['identity'], 'complete')
        self.base.authority.allowed = [item for item in self.base.authority.allowed if item[0] != 'context']
        denied = self.analyze()
        self.assertNotEqual(denied['completeness']['identity'], 'complete')
        self.assertIsNone(denied['totals']['total_cost'])
        self.assertEqual(denied['top_leaves'], [])
        self.assertNotEqual(denied['corpus_id'], positive['corpus_id'])

    def test_unverified_prices_do_not_create_terms_or_ranked_leaves(self):
        positive = self.analyze()
        self.assertEqual(positive['totals']['total_cost'], '0.00578')
        self.assertTrue(positive['terms'])
        self.base.authority.allowed = [item for item in self.base.authority.allowed if item[0] != 'price']
        denied = self.analyze()
        self.assertIsNone(denied['totals']['total_cost'])
        self.assertEqual(denied['terms'], [])
        self.assertEqual(denied['top_leaves'], [])
        self.assertNotEqual(denied['corpus_id'], positive['corpus_id'])

    def test_selected_input_permutations_preserve_all_export_formats(self):
        first = self.analyze()
        manifest = copy.deepcopy(self.base.manifest)
        manifest['inputs'].reverse()
        from usage_telemetry_report import analyze_corpus
        second = analyze_corpus(manifest, verify_input=self.verify_input, verify_evidence=self.base.authority)
        self.assertEqual(exports.render_exports(first), exports.render_exports(second))

    def test_unpriced_or_unverified_leaves_are_never_ranked_as_complete(self):
        positive = self.analyze()
        self.assertEqual(len(positive['top_leaves']), 2)
        target = self.leaves[1]
        self.base.authority.allowed = [item for item in self.base.authority.allowed
            if not (item[0] == 'leaf_billable_scope' and item[1] == target)]
        result = self.analyze()
        self.assertNotIn(target['owner_id'], {item['owner_id'] for item in result['top_leaves']})
        partial = next(item for item in result['partial_leaves'] if item['owner_id'] == target['owner_id'])
        self.assertIn(partial['coverage'], ('proven_lower_bound', 'subtotal_only'))


if __name__ == '__main__':
    unittest.main()
