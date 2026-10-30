#!/usr/bin/env python3
"""End-to-end outcome and timing checks from a fixed, authorized corpus."""
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


def opportunity(number):
    return {'task_revision': 'task-v1', 'input_revision': 'input-v1',
            'acceptance_contract': 'contract-v1', 'strategy': 'strategy-a', 'repetition': number}


def journal(identifier, start, end, sequence, parent=None):
    value = {'event': 'step', 'ts': '2026-01-01T00:00:00Z', 'run_id': 'run',
             'seq': sequence, 'pipeline': 'spec-run', 'flow': 'main', 'step': 'subtask',
             'outcome': 'ok', 'session_id': 'session', 'agent_id': 'agent',
             'checkpoint_id': identifier, 'span_start_ms': start, 'span_end_ms': end,
             'timing_source': 'hook', 'boundary': 'subagent', 'span_kind': 'work'}
    if parent is not None:
        value['parent_checkpoint_id'] = parent
    return value


class RetrospectiveOutcomeTimingTests(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.ResolvedReportTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.scope = self.base.data['scope']
        self.configure_real_prices()
        self.serial = 0
        for number in (1, 2, 3):
            value = {'schema_version': 1, 'kind': 'outcome_opportunity',
                     'identity': opportunity(number), 'observed_at': '2028-01-01T00:00:00Z'}
            self.add('outcome_opportunity', value)
            self.authorize('outcome_opportunity', value)
        self.attempts = [
            self.attempt('failed', 1, ['sha256:' + '1' * 64]),
            self.attempt('resumed', 1, ['sha256:' + '2' * 64]),
            self.attempt('rejected', 2, []),
            self.attempt('unfinished', 3, []),
        ]
        self.accepted = self.revision(1, 'accepted', 1, '2028-01-02T00:00:00Z')
        self.rejected = self.revision(2, 'rejected', 1, '2028-01-02T00:00:00Z')
        self.add_revision(self.accepted)
        self.add_revision(self.rejected)

    def configure_real_prices(self):
        # Explicit synthetic rates: the verified 600 uncached tokens cost 1.5.
        # Other supported components have zero rates, and the second historical
        # response remains outside the snapshot's applicable period.
        snapshot = self.base.data['snapshots'][0]
        for rate in snapshot['rates']:
            rate['usd'] = '2500' if rate['component'] == 'input_uncached' else '0'
        snapshot_id = contract.price_snapshot_id(snapshot)
        self.base.data['scenario']['snapshot_ids'] = [snapshot_id]
        for proof in self.base.data['price_evidence']:
            if proof['kind'] == 'price_snapshot_evidence':
                proof['snapshot_id'] = snapshot_id
        self.base.authority.allowed = [entry for entry in self.base.authority.allowed if entry[0] != 'price']
        def canonical(value):
            return contract.parse_json(contract.canonical_bytes(value))
        for proof in self.base.data['price_evidence']:
            self.base.authority.allowed.append(('price', canonical(self.scope),
                                                 canonical(snapshot), canonical(proof)))
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
        # Positive control ensures the outcome tests use real resolved prices.
        self.assertEqual(self.base.analyze()['pricing']['priced_subtotal_cost'], '1.5')

    def add(self, kind, value):
        self.serial += 1
        raw = contract.canonical_bytes(value)
        path = self.base.directory / ('retrospective-' + str(self.serial) + '.json')
        path.write_bytes(raw)
        item = {'kind': kind, 'schema_version': 1, 'local_path': str(path),
                'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)}
        self.base.manifest['inputs'].append(item)
        self.base.selected.add(item['sha256'])
        return item

    def authorize(self, kind, value):
        def canonical(item):
            return contract.parse_json(contract.canonical_bytes(item))
        self.base.authority.allowed.append((kind, canonical(self.scope), canonical(value), canonical(value)))

    def attempt(self, identifier, number, response_ids):
        value = {'schema_version': 1, 'kind': 'outcome_attempt', 'attempt_id': identifier,
                 'opportunity': opportunity(number), 'response_ids': response_ids,
                 'category': 'workload', 'complete': bool(response_ids),
                 'observed_at': '2028-01-02T00:00:00Z'}
        self.add('outcome_attempt', value)
        self.authorize('outcome_attempt', value)
        return value

    def revision(self, number, status, version, observed_at):
        return {'schema_version': 1, 'kind': 'acceptance_revision', 'opportunity': opportunity(number),
                'status': status, 'revision': version, 'observed_at': observed_at,
                'acceptance_contract': 'contract-v1', 'evaluator_id': 'sha256:' + 'a' * 64,
                'evidence_id': 'sha256:' + 'b' * 64}

    def add_revision(self, value):
        self.add('acceptance_revision', value)
        self.authorize('acceptance_revision', value)

    def verify_input(self, entry, value, scope):
        proof = self.base.verify_input(entry, value, scope)
        if entry['kind'] == 'acceptance_revision' and value['observed_at'] > proof['observed_at']:
            proof['observed_at'] = value['observed_at']
        return proof

    def analyze(self, manifest=None):
        from usage_telemetry_report import analyze_corpus
        return analyze_corpus(copy.deepcopy(manifest or self.base.manifest),
                              verify_input=self.verify_input, verify_evidence=self.base.authority)

    def add_graph(self, root, children, group, sequence):
        self.add('lifecycle_event', root)
        for child in children:
            self.add('lifecycle_event', child)
        graph = {'schema_version': 1, 'kind': 'duration_graph', 'run_id': 'run',
                 'root_checkpoint_id': root['checkpoint_id'], 'group': group,
                 'event_hashes': sorted(contract.content_id(event) for event in [root, *children]),
                 'complete': True, 'observed_at': '2028-01-01T00:00:00Z'}
        self.add('duration_graph', graph)
        self.authorize('duration_graph', graph)

    def test_timing_and_acceptance_without_usage_bundle(self):
        self.add_graph(journal('root', 0, 10, 1),
                       [journal('child', 1, 7, 2, 'root')], 'standalone', 1)
        selected = {'lifecycle_event', 'duration_graph', 'outcome_opportunity',
                    'outcome_attempt', 'acceptance_revision'}
        self.base.manifest['inputs'] = [entry for entry in self.base.manifest['inputs']
                                        if entry['kind'] in selected]
        result = self.analyze()
        self.assertEqual(result['outcomes']['opportunity_count'], 3)
        self.assertEqual(result['outcomes']['accepted_count'], 1)
        self.assertIsNone(result['outcomes']['cost_per_accepted'])
        self.assertEqual(result['durations'][0]['wall_ms'], '10')
        self.assertEqual(result['durations'][0]['exclusive_ms'], '4')
        exports.render_exports(result)

    def test_independently_accepted_outcomes_use_only_actual_resolved_costs(self):
        report = self.analyze()
        summary = report['outcomes']
        self.assertEqual(summary['opportunity_count'], 3)
        self.assertEqual(summary['accepted_count'], 1)
        self.assertEqual(summary['observed_workload_cost'], '1.5')
        self.assertEqual(summary['cost_per_accepted'], '1.5')
        self.assertEqual(summary['ratio_quality'], 'descriptive_incomplete')
        self.assertEqual(summary['coverage'], 'incomplete')
        self.assertIsNone(report['totals']['total_cost'])
        rendered = exports.render_exports(report)
        self.assertEqual(json.loads(rendered['json'])['outcomes'], summary)
        for artifact in rendered.values():
            self.assertIn('1.5', artifact)
            self.assertNotIn(str(self.base.directory), artifact)
            self.assertNotIn(self.accepted['evidence_id'], artifact)

    def test_unselected_experimental_cost_is_unknown_not_zero(self):
        summary = self.analyze()['outcomes']
        self.assertEqual(summary['observed_workload_cost'], '1.5')
        self.assertIsNone(summary['experimental_evaluation_cost'])
        self.assertIsNone(summary['combined_cost'])

    def test_empty_experimental_cost_needs_independent_empty_inventory(self):
        self.assertIsNone(self.analyze()['outcomes']['experimental_evaluation_cost'])
        inventory = {'schema_version': 1, 'kind': 'experimental_inventory',
                     'scope': copy.deepcopy(self.scope), 'state': 'complete',
                     'expected_attempt_ids': [], 'observed_at': '2028-01-02T00:00:00Z'}
        self.add('experimental_inventory', inventory)
        self.authorize('experimental_inventory', inventory)
        model_inventory = self.base.data['bundle']['inventories'][0]
        proof = next(item for item in self.base.data['bundle']['evidence_objects']
                     if item['kind'] == 'inventory_evidence')
        def canonical(value):
            return contract.parse_json(contract.canonical_bytes(value))
        self.base.authority.allowed.append(('tool_scope_empty', canonical(self.scope),
                                            canonical(model_inventory), canonical(proof)))
        proven = self.analyze()
        self.assertEqual(proven['outcomes']['experimental_evaluation_cost'], '0')
        previous = self.base.authority.allowed[:]
        self.base.authority.allowed = [item for item in previous if item[0] != 'tool_scope_empty']
        unknown_tools = self.analyze()
        self.assertIsNone(unknown_tools['outcomes']['experimental_evaluation_cost'])
        self.assertNotEqual(proven['corpus_id'], unknown_tools['corpus_id'])
        self.base.authority.allowed = previous
        self.base.authority.allowed = [item for item in self.base.authority.allowed
                                       if item[0] != 'experimental_inventory']
        untrusted = self.analyze()
        self.assertIsNone(untrusted['outcomes']['experimental_evaluation_cost'])
        self.assertNotEqual(proven['corpus_id'], untrusted['corpus_id'])

    def test_untrusted_acceptance_does_not_become_a_success(self):
        positive = self.analyze()
        self.assertEqual(positive['outcomes']['accepted_count'], 1)
        self.base.authority.allowed = [item for item in self.base.authority.allowed
                                       if item[0] != 'acceptance_revision']
        report = self.analyze()
        self.assertEqual(report['outcomes']['accepted_count'], 0)
        self.assertIsNone(report['outcomes']['cost_per_accepted'])
        self.assertNotEqual(report['corpus_id'], positive['corpus_id'])

    def test_later_defect_revision_does_not_rewrite_older_report(self):
        before_manifest = copy.deepcopy(self.base.manifest)
        original = self.analyze(before_manifest)
        defect = self.revision(1, 'defect', 2, '2030-01-01T00:00:00Z')
        self.add_revision(defect)
        still_old = self.analyze()
        self.assertEqual(still_old['outcomes']['accepted_count'], 1)
        self.assertEqual(original, self.analyze(before_manifest))
        newer_manifest = copy.deepcopy(self.base.manifest)
        newer_manifest['as_of'] = '2031-01-01T00:00:00Z'
        newer = self.analyze(newer_manifest)
        self.assertEqual(newer['outcomes']['accepted_count'], 0)
        self.assertIsNone(newer['outcomes']['cost_per_accepted'])
        self.assertNotEqual(newer['corpus_id'], still_old['corpus_id'])

    def test_one_response_cannot_be_charged_to_two_attempts(self):
        positive = self.analyze()
        self.assertEqual(positive['outcomes']['observed_workload_cost'], '1.5')
        self.attempt('duplicate', 2, ['sha256:' + '1' * 64])
        try:
            result = self.analyze()
        except ValueError:
            return
        self.assertIn(result['outcomes']['observed_workload_cost'], (None, '1.5'))
        self.assertNotEqual(result['outcomes']['coverage'], 'complete')

    def test_measured_intervals_use_union_and_independent_graph_completeness(self):
        parent = journal('p', 0, 10, 1)
        children = [journal('a', 1, 7, 2, 'p'), journal('b', 4, 9, 3, 'p'),
                    journal('g', 2, 5, 4, 'a')]
        self.add_graph(parent, children, 'tree', 1)
        report = self.analyze()
        tree = next(item for item in report['durations'] if item['group'] == 'tree')
        self.assertEqual((tree['wall_ms'], tree['worker_sum_ms'], tree['coverage_ms'],
                          tree['exclusive_ms']), ('10', '11', '8', '2'))
        self.base.authority.allowed = [item for item in self.base.authority.allowed
                                       if item[0] != 'duration_graph']
        untrusted = self.analyze()
        tree = next(item for item in untrusted['durations'] if item['group'] == 'tree')
        self.assertIsNone(tree['exclusive_ms'])

    def test_omitted_child_cannot_inherit_a_complete_graph_attestation(self):
        parent = journal('p', 0, 10, 1)
        children = [journal('a', 1, 7, 2, 'p'), journal('b', 4, 9, 3, 'p')]
        self.add_graph(parent, children, 'tree', 1)
        positive = self.analyze()
        tree = next(item for item in positive['durations'] if item['group'] == 'tree')
        self.assertEqual(tree['exclusive_ms'], '2')
        removed_hash = hashlib.sha256(contract.canonical_bytes(children[1])).hexdigest()
        self.base.manifest['inputs'] = [item for item in self.base.manifest['inputs']
                                        if item['sha256'] != removed_hash]
        try:
            report = self.analyze()
        except ValueError:
            return
        tree = next(item for item in report['durations'] if item['group'] == 'tree')
        self.assertIsNone(tree['exclusive_ms'])
        self.assertFalse(tree['coverage_complete'])
        self.assertNotEqual(report['corpus_id'], positive['corpus_id'])

    def test_conflicting_selected_root_cannot_inherit_graph_attestation(self):
        parent = journal('p', 0, 10, 1)
        self.add_graph(parent, [journal('a', 1, 7, 2, 'p')], 'tree', 1)
        positive = self.analyze()
        tree = next(item for item in positive['durations'] if item['group'] == 'tree')
        self.assertEqual(tree['exclusive_ms'], '4')
        self.add('lifecycle_event', journal('p', 0, 11, 9))
        try:
            report = self.analyze()
        except ValueError:
            return
        tree = next(item for item in report['durations'] if item['group'] == 'tree')
        self.assertIsNone(tree['exclusive_ms'])
        self.assertFalse(tree['coverage_complete'])

    def test_real_measured_groups_have_exact_statistics_and_stable_exports(self):
        for index in range(1, 5):
            self.add_graph(journal('sample' + str(index), 0, index, index + 10), [], 'samples', index)
        first = self.analyze()
        group = next(item for item in first['groups'] if item['name'] == 'samples')
        self.assertEqual((group['count'], group['median'], group['p90'], group['small_sample']),
                         (4, '2.5', '4', True))
        reversed_manifest = copy.deepcopy(self.base.manifest)
        reversed_manifest['inputs'].reverse()
        second = self.analyze(reversed_manifest)
        self.assertEqual(exports.render_exports(first), exports.render_exports(second))


if __name__ == '__main__':
    unittest.main()
