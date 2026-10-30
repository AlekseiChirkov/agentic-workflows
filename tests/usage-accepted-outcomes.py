#!/usr/bin/env python3
"""Offline checks for independently accepted outcome accounting."""
import copy
import importlib.util
import json
import itertools
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'scripts/usage_telemetry_outcomes.py'
if MODULE.exists():
    spec = importlib.util.spec_from_file_location('outcomes', MODULE)
    outcomes = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(outcomes)
else:
    outcomes = None


def opportunity(number):
    return {'task_revision': 'task-v1', 'input_revision': 'input-v1',
            'acceptance_contract': 'contract-v1', 'strategy': 'strategy-a',
            'repetition': number}


def attempt(identifier, number, cost, *, complete=True, category='workload'):
    return {'attempt_id': identifier, 'opportunity': opportunity(number),
            'cost': cost, 'complete': complete, 'category': category,
            'observed_at': '2026-01-02T00:00:00Z'}


def revision(number, status, when='2026-01-02T00:00:00Z', evidence='verified-acceptance'):
    return {'opportunity': opportunity(number), 'status': status,
            'observed_at': when, 'revision': 1, 'evidence_id': evidence,
            'acceptance_contract': 'contract-v1'}


def verify_acceptance(label):
    """Stand-in for an independently controlled evidence verification boundary."""
    return label['evidence_id'] in {'verified-acceptance', 'verified-late-defect'}


def summarize(attempts, labels, *, as_of='2026-01-03T00:00:00Z', include_experimental=False):
    if outcomes is None:
        return None
    return outcomes.summarize_outcomes(attempts, labels, as_of=as_of,
                                       verify_acceptance=verify_acceptance,
                                       include_experimental=include_experimental)


def comparison_group(cost='1.5'):
    return {'task_revision': 'task-v1', 'input_revision': 'input-v1',
            'acceptance_contract': 'contract-v1', 'repetitions': 1,
            'quality_policy': 'quality-v1', 'coverage': 'complete',
            'price_basis': 'price-v1', 'scope': 'root',
            'independent_quality': True, 'cost_per_accepted': cost}


class AcceptedOutcomesTests(unittest.TestCase):
    def test_resumed_failed_rejected_and_incomplete_attempts(self):
        attempts = [attempt('failed', 1, '0.4'), attempt('resumed', 1, '0.6'),
                    attempt('rejected', 2, '0.3'), attempt('unfinished', 3, '0.2', complete=False)]
        report = summarize(attempts, [revision(1, 'accepted'), revision(2, 'rejected')])
        self.assertEqual(report['opportunity_count'], 3)
        self.assertEqual(report['accepted_count'], 1)
        self.assertEqual(report['observed_workload_cost'], '1.5')
        self.assertEqual(report['cost_per_accepted'], '1.5')
        self.assertEqual(report['ratio_quality'], 'descriptive_incomplete')
        self.assertEqual(report['coverage'], 'incomplete')

    def test_no_independent_acceptance_is_unavailable(self):
        report = summarize([attempt('finished', 1, '0.4')], [])
        self.assertEqual(report['accepted_count'], 0)
        self.assertIsNone(report['cost_per_accepted'])
        self.assertIn('accepted_denominator_zero', report['diagnostics'])
        # A model's own claim, even a forged independence flag, is not evidence.
        forged = revision(1, 'accepted', evidence='model-claimed-finish')
        forged['independent'] = True
        report = summarize([attempt('finished', 1, '0.4')], [forged])
        self.assertEqual(report['accepted_count'], 0)
        self.assertIsNone(report['cost_per_accepted'])

    def test_exact_decimal_arithmetic_and_unknown_cost(self):
        report = summarize([attempt('a', 1, '0.1'), attempt('b', 2, '0.2')],
                           [revision(1, 'accepted')])
        self.assertEqual(report['observed_workload_cost'], '0.3')
        self.assertEqual(report['cost_per_accepted'], '0.3')
        report = summarize([attempt('a', 1, '0.1'), attempt('b', 2, None)],
                           [revision(1, 'accepted')])
        self.assertEqual(report['observed_workload_cost'], '0.1')
        self.assertEqual(report['ratio_quality'], 'descriptive_incomplete')
        self.assertEqual(report['coverage'], 'incomplete')

    def test_experimental_evaluation_is_separate_and_counted_once(self):
        attempts = [attempt('work', 1, '0.4'),
                    attempt('production-verification', 1, '0.2', category='production_verification'),
                    attempt('evaluation', 1, '0.3', category='experimental_evaluation')]
        labels = [revision(1, 'accepted')]
        normal = summarize(attempts, labels)
        combined = summarize(attempts, labels, include_experimental=True)
        self.assertEqual(normal['observed_workload_cost'], '0.6')
        self.assertEqual(normal['experimental_evaluation_cost'], '0.3')
        self.assertIsNone(normal['combined_cost'])
        self.assertEqual(combined['combined_cost'], '0.9')
        self.assertEqual(combined['cost_per_accepted'], '0.6')
        repeated = summarize(attempts + [copy.deepcopy(attempts[-1])], labels,
                             include_experimental=True)
        self.assertEqual(repeated['combined_cost'], '0.9')

    def test_late_revision_applies_only_to_new_report(self):
        attempts = [attempt('completed', 1, '0.4')]
        first = revision(1, 'accepted')
        late = revision(1, 'defect', '2026-01-04T00:00:00Z', 'verified-late-defect')
        late['revision'] = 2
        frozen = summarize(attempts, [first, late], as_of='2026-01-03T00:00:00Z')
        frozen_copy = copy.deepcopy(frozen)
        newer = summarize(attempts, [first, late], as_of='2026-01-05T00:00:00Z')
        self.assertEqual(frozen['accepted_count'], 1)
        self.assertEqual(newer['accepted_count'], 0)
        self.assertIsNone(newer['cost_per_accepted'])
        self.assertEqual(frozen, frozen_copy)
        self.assertEqual(frozen, summarize(attempts, [first], as_of='2026-01-03T00:00:00Z'))

    def test_comparison_requires_compatible_evidence_and_scope(self):
        if outcomes is None:
            self.fail('outcome comparison is unavailable')
        left, right = comparison_group('1.5'), comparison_group('2.0')
        comparison = outcomes.compare_outcome_groups(left, right)
        self.assertEqual(comparison['winner'], 'left')
        for field, value in [('task_revision', 'other-task'), ('input_revision', 'other-input'),
                             ('acceptance_contract', 'other-contract'), ('repetitions', 2),
                             ('quality_policy', 'different'), ('coverage', 'incomplete'),
                             ('price_basis', 'different'), ('scope', 'phase'),
                             ('independent_quality', False), ('cost_per_accepted', None)]:
            with self.subTest(field=field):
                changed = dict(right, **{field: value})
                result = outcomes.compare_outcome_groups(left, changed)
                self.assertIsNone(result['winner'])
                self.assertIn('comparison_ineligible', result['diagnostics'])

    def test_contract_mismatch_and_unrelated_evidence_do_not_accept(self):
        mismatch = revision(1, 'accepted')
        mismatch['acceptance_contract'] = 'other-contract'
        report = summarize([attempt('a', 1, '0.4')], [mismatch, revision(2, 'accepted')])
        self.assertEqual(report['accepted_count'], 0)
        self.assertIsNone(report['cost_per_accepted'])

    def test_order_independence_and_output_privacy(self):
        attempts = [attempt('a', 1, '0.4'), attempt('b', 2, '0.3')]
        labels = [revision(1, 'accepted'), revision(2, 'rejected')]
        report = summarize(attempts, labels)
        self.assertEqual(report, summarize(list(reversed(attempts)), list(reversed(labels))))
        serialized = json.dumps(report, sort_keys=True)
        self.assertNotIn('verified-acceptance', serialized)
        self.assertNotIn('/private/source/path', serialized)

    def test_late_work_and_evaluation_do_not_enter_older_corpus(self):
        early = attempt('early', 1, '0.4')
        late = attempt('late', 1, '0.6')
        late['observed_at'] = '2026-01-04T00:00:00Z'
        evaluation = attempt('evaluation', 1, '0.2', category='experimental_evaluation')
        evaluation['observed_at'] = '2026-01-04T00:00:00Z'
        labels = [revision(1, 'accepted')]
        original = summarize([early, late, evaluation], labels, include_experimental=True)
        self.assertEqual(original['observed_workload_cost'], '0.4')
        self.assertEqual(original['experimental_evaluation_cost'], '0')
        self.assertEqual(original['combined_cost'], '0.4')
        later = summarize([early, late, evaluation], labels,
                          as_of='2026-01-05T00:00:00Z', include_experimental=True)
        self.assertEqual(later['observed_workload_cost'], '1')
        self.assertEqual(later['combined_cost'], '1.2')
        self.assertEqual(original, summarize([early], labels, include_experimental=True))

    def test_revision_conflicts_are_rejected_for_every_input_order(self):
        accepted = revision(1, 'accepted')
        conflict = revision(1, 'rejected')
        latest = revision(1, 'accepted', '2026-01-02T01:00:00Z')
        latest['revision'] = 2
        for labels in itertools.permutations([accepted, conflict, latest]):
            with self.subTest(labels=labels), self.assertRaises(ValueError):
                summarize([attempt('a', 1, '0.4')], list(labels))

    def test_nonterminating_ratio_remains_exact_and_comparable(self):
        attempts = [attempt('a', 1, '1'), attempt('b', 2, '0'), attempt('c', 3, '0')]
        labels = [revision(number, 'accepted') for number in (1, 2, 3)]
        report = summarize(attempts, labels)
        self.assertEqual(report['cost_per_accepted'], '1/3')
        left = comparison_group(report['cost_per_accepted'])
        right = comparison_group('0.34')
        self.assertEqual(outcomes.compare_outcome_groups(left, right)['winner'], 'left')
        left['cost_per_accepted'] = '2/6'
        self.assertEqual(outcomes.compare_outcome_groups(left, right)['winner'], 'left')

    def test_incomplete_experimental_cost_marks_combined_total_incomplete(self):
        attempts = [attempt('work', 1, '0.4'),
                    attempt('evaluation', 1, '0.2', complete=False,
                            category='experimental_evaluation')]
        report = summarize(attempts, [revision(1, 'accepted')], include_experimental=True)
        self.assertEqual(report['coverage'], 'complete')
        self.assertEqual(report['experimental_evaluation_cost'], '0.2')
        self.assertEqual(report['combined_cost'], '0.6')
        self.assertEqual(report['combined_coverage'], 'incomplete')
        attempts[-1]['cost'] = None
        report = summarize(attempts, [revision(1, 'accepted')], include_experimental=True)
        self.assertEqual(report['combined_cost'], '0.4')
        self.assertEqual(report['combined_coverage'], 'incomplete')

    def test_large_exact_results_remain_comparable_after_carry(self):
        large = '9' * 255 + '8'
        attempts = [attempt('a', 1, large), attempt('b', 1, large)]
        report = summarize(attempts, [revision(1, 'accepted')])
        total = str(int(large) * 2)
        self.assertEqual(len(total), 257)
        self.assertEqual(report['observed_workload_cost'], total)
        self.assertEqual(report['cost_per_accepted'], total)
        left, right = comparison_group(total), comparison_group(str(int(total) + 1))
        self.assertEqual(outcomes.compare_outcome_groups(left, right)['winner'], 'left')
        self.assertIsNone(outcomes.compare_outcome_groups(left, left)['winner'])
        self.assertEqual(outcomes.compare_outcome_groups(left, left)['diagnostics'], [])
        attempts.extend([attempt('c', 2, '0'), attempt('d', 3, '0')])
        labels = [revision(number, 'accepted') for number in (1, 2, 3)]
        report = summarize(attempts, labels)
        self.assertEqual(report['cost_per_accepted'], f'{total}/3')
        left = comparison_group(report['cost_per_accepted'])
        self.assertEqual(outcomes.compare_outcome_groups(left, right)['winner'], 'left')
        self.assertEqual(outcomes.compare_outcome_groups(left, left)['diagnostics'], [])

    def test_same_attempt_conflicts_cannot_be_silently_double_counted(self):
        original = attempt('a', 1, '0.4')
        duplicate = attempt('a', 1, '0.8')
        with self.assertRaises(ValueError):
            summarize([original, duplicate], [revision(1, 'accepted')])


if __name__ == '__main__':
    unittest.main()
