#!/usr/bin/env python3
"""Offline resolution of ordered response usage and proven revisions."""
import copy
import importlib.util
import itertools
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'scripts/usage_telemetry_stream.py'
if MODULE.exists():
    spec = importlib.util.spec_from_file_location('usage_telemetry_stream', MODULE)
    stream = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stream)
else:
    stream = None


def resolve(events):
    return getattr(stream, 'resolve_stream', lambda events: None)(events)


def ident(n):
    return 'sha256:' + format(n, '064x')


def snapshot(n, value, sequence=None, final=False, **changes):
    event = {'response_id': ident(1), 'observation_id': ident(n), 'kind': 'snapshot',
             'value': value, 'final': final}
    if sequence is not None:
        event['sequence'] = sequence
    event.update(changes)
    return event


def delta(n, value, sequence):
    return {'response_id': ident(1), 'observation_id': ident(n), 'kind': 'delta',
            'value': value, 'sequence': sequence}


def terminal(n, sequence):
    return {'response_id': ident(1), 'observation_id': ident(n), 'kind': 'terminal',
            'sequence': sequence}


class StreamRevisionsTests(unittest.TestCase):
    def assert_measurement(self, result, state, value=None, reason=None):
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('measurement_state'), state)
        if value is None:
            self.assertNotIn('value', result)
        else:
            self.assertEqual(result.get('value'), value)
        if reason:
            self.assertIn(reason, result.get('reasons', []))

    def test_final_snapshot_replaces_partial_snapshots_in_any_input_order(self):
        events = [snapshot(10, 1, 1), snapshot(11, 40, 2), snapshot(12, 100, 3, True)]
        for order in itertools.permutations(events):
            with self.subTest(order=[x['observation_id'] for x in order]):
                self.assert_measurement(resolve(list(order) + [copy.deepcopy(order[0])]), 'final', 100)

    def test_partial_snapshot_follows_source_order_not_max_or_arrival(self):
        events = [snapshot(10, 50, 1), snapshot(11, 40, 2)]
        for order in itertools.permutations(events):
            self.assert_measurement(resolve(list(order)), 'partial', 40, 'stream_incomplete')
        unordered = [snapshot(10, 50), snapshot(11, 40)]
        for order in itertools.permutations(unordered):
            result = resolve(list(order))
            self.assertIn(result.get('measurement_state'), ('partial', 'conflicted'))
            self.assertNotIn('value', result)

    def test_missing_delta_sequence_is_partial_even_with_terminal(self):
        events = [delta(10, 10, 1), delta(11, 30, 3), terminal(12, 4)]
        for order in itertools.permutations(events):
            self.assert_measurement(resolve(list(order)), 'partial', 40, 'stream_incomplete')

    def test_contiguous_deltas_count_duplicates_once(self):
        one, two, end = delta(10, 10, 1), delta(11, 30, 2), terminal(12, 3)
        self.assert_measurement(resolve([two, one, copy.deepcopy(one), end]), 'final', 40)
        self.assert_measurement(resolve([two, one, copy.deepcopy(one)]), 'partial', 40,
                                'stream_incomplete')

    def test_derived_delta_total_may_exceed_source_counter_limit(self):
        maximum = 9007199254740991
        self.assert_measurement(resolve([delta(10, maximum, 1), delta(11, maximum, 2), terminal(12, 3)]),
                                'final', 2 * maximum)

    def test_same_observation_or_sequence_with_different_values_conflicts(self):
        one = delta(10, 10, 1)
        for other in (delta(10, 11, 1), delta(11, 11, 1)):
            with self.subTest(other=other):
                self.assert_measurement(resolve([one, other, terminal(12, 2)]), 'conflicted',
                                        reason='revision_conflict')

    def test_later_partial_event_cannot_preserve_earlier_finality(self):
        events = [snapshot(10, 100, 1, True), snapshot(11, 120, 2, False)]
        for order in itertools.permutations(events):
            result = resolve(list(order))
            self.assertNotEqual(result['measurement_state'], 'final')
        events = [snapshot(10, 100, 1, True), delta(11, 5, 2)]
        for order in itertools.permutations(events):
            result = resolve(list(order))
            self.assertNotEqual(result['measurement_state'], 'final')

    def test_incompatible_finals_and_unverified_corrections_conflict(self):
        first = snapshot(10, 100, 1, True)
        second = snapshot(11, 90, 2, True)
        for other in (second, second | {'correction_of': first['observation_id'],
                                        'correction_verified': False}):
            for order in itertools.permutations([first, other]):
                self.assert_measurement(resolve(list(order)), 'conflicted',
                                        reason='revision_conflict')

    def test_verified_correction_chain_replaces_predecessors(self):
        first = snapshot(10, 100, 1, True)
        second = snapshot(11, 90, 2, True, correction_of=ident(10), correction_verified=True)
        third = snapshot(12, 95, 3, True, correction_of=ident(11), correction_verified=True)
        for order in itertools.permutations([first, second, third]):
            self.assert_measurement(resolve(list(order)), 'final', 95)

    def test_correction_cycles_and_incompatible_successors_conflict(self):
        first = snapshot(10, 100, 1, True)
        child = snapshot(11, 90, 2, True, correction_of=ident(10), correction_verified=True)
        sibling = snapshot(12, 95, 3, True, correction_of=ident(10), correction_verified=True)
        cycle_first = first | {'correction_of': ident(11), 'correction_verified': True}
        for events in ([first, child, sibling], [cycle_first, child]):
            for order in itertools.permutations(events):
                self.assert_measurement(resolve(list(order)), 'conflicted',
                                        reason='revision_conflict')

    def test_final_snapshot_and_deltas_do_not_double_count(self):
        events = [delta(10, 10, 1), delta(11, 30, 2), terminal(12, 3),
                  snapshot(13, 100, 4, True)]
        self.assert_measurement(resolve(events), 'final', 100)

    def test_partial_snapshots_and_deltas_do_not_prove_compatible_totals(self):
        combinations = [
            [delta(10, 10, 1), snapshot(11, 40, 2)],
            [snapshot(10, 40, 1), delta(11, 10, 2), terminal(12, 3)],
            [snapshot(10, 40), delta(11, 10, 1), terminal(12, 2)],
        ]
        for events in combinations:
            for order in itertools.permutations(events):
                with self.subTest(order=order):
                    result = resolve(list(order))
                    self.assertIn(result.get('measurement_state'), ('partial', 'conflicted'))
                    self.assertNotIn('value', result)
                    self.assertTrue(result.get('reasons'))

    def test_empty_is_unavailable_and_mixed_responses_are_rejected(self):
        self.assert_measurement(resolve([]), 'unavailable', reason='stream_incomplete')
        other = snapshot(11, 40, 2) | {'response_id': ident(2)}
        with self.assertRaises(ValueError):
            resolve([snapshot(10, 1, 1), other])

    def test_invalid_input_is_bounded_and_errors_do_not_expose_private_fields(self):
        valid = snapshot(10, 1, 1)
        invalid = [valid | {'value': -1}, valid | {'value': True},
                   valid | {'sequence': 0}, valid | {'kind': 'aggregate'},
                   valid | {'raw_text': 'PRIVATE_CONTENT_SENTINEL'}]
        for event in invalid:
            with self.subTest(event=event):
                with self.assertRaises(ValueError) as error:
                    resolve([event])
                self.assertNotIn('PRIVATE_CONTENT_SENTINEL', str(error.exception))
        with self.assertRaises(ValueError):
            resolve([valid] * 10001)


if __name__ == '__main__':
    unittest.main()
