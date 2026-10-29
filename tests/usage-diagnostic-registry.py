#!/usr/bin/env python3
"""Exercise offline diagnostic views and their accounting boundary."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contract', ROOT / 'scripts/usage_telemetry_contract.py')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def opaque(digit):
    return 'sha256:' + digit * 64


SCOPE = {'owner_kind': 'run', 'owner_id': opaque('a')}
SOURCE = opaque('b')
METRICS = {
    'context.loaded_bytes': 'bytes',
    'orchestration.tool_calls': 'count',
    'verification.evidence_reuses': 'count',
    'tool_output.full_bytes': 'bytes',
    'tool_output.shown_bytes': 'bytes',
    'tool_output.additional_read_bytes': 'bytes',
    'repair.attempts': 'count',
    'decomposition.rework': 'count',
}


def measurement(metric, value, event):
    return {'schema_version': 1, 'kind': 'diagnostic_measurement',
            'metric': metric, 'value': value, 'unit': METRICS[metric],
            'scope': copy.deepcopy(SCOPE), 'source_id': SOURCE,
            'quality': 'measured', 'event_id': event}


def view(records, metrics, scope=SCOPE, source=SOURCE):
    function = getattr(contract, 'diagnostic_registry_view', lambda *args: None)
    return function(records, metrics, scope, source)


class DiagnosticRegistryTests(unittest.TestCase):
    def test_registered_namespaces_preserve_exact_measurement_and_provenance(self):
        records = [measurement(metric, i, opaque('c'))
                   for i, metric in enumerate(METRICS, 1)]
        result = view(records, list(METRICS))
        self.assertIsInstance(result, list)
        self.assertEqual({item['metric']: item for item in result},
                         {item['metric']: item for item in records})
        self.assertEqual(result, view(list(reversed(records)), list(reversed(METRICS))))

    def test_absent_and_explicit_unknown_do_not_become_measured_zero(self):
        absent = view([], ['context.loaded_bytes'])
        self.assertEqual(len(absent), 1)
        self.assertEqual(absent[0], {'schema_version': 1, 'kind': 'diagnostic_measurement',
            'metric': 'context.loaded_bytes', 'value': None, 'unit': 'bytes',
            'scope': SCOPE, 'source_id': SOURCE, 'quality': 'unknown'})
        unknown = absent[0] | {'event_id': opaque('c')}
        self.assertEqual(view([unknown], ['context.loaded_bytes']), [unknown])
        zero = measurement('context.loaded_bytes', 0, opaque('c'))
        self.assertEqual(view([zero], ['context.loaded_bytes']), [zero])

    def test_scope_source_and_metric_filter_cannot_borrow_other_evidence(self):
        first = measurement('context.loaded_bytes', 3, opaque('c'))
        foreign = copy.deepcopy(first)
        foreign['scope']['owner_id'] = opaque('d')
        foreign['value'] = 99
        other_source = first | {'source_id': opaque('e'), 'value': 88}
        unrelated = measurement('repair.attempts', 7, opaque('f'))
        self.assertEqual(view([foreign, first, other_source, unrelated],
                              ['context.loaded_bytes']), [first])
        self.assertEqual(view([foreign], ['context.loaded_bytes'])[0]['quality'], 'unknown')

    def test_replayed_event_does_not_double_count_and_conflict_is_rejected(self):
        first = measurement('repair.attempts', 1, opaque('c'))
        retry = measurement('repair.attempts', 1, opaque('d'))
        self.assertEqual(view([first, copy.deepcopy(first), retry], ['repair.attempts']),
                         view([retry, first], ['repair.attempts']))
        self.assertEqual(len(view([first, copy.deepcopy(first), retry], ['repair.attempts'])), 2)
        conflict = first | {'value': 2}
        with self.assertRaises(ValueError):
            view([first, conflict], ['repair.attempts'])

    def test_byte_observation_does_not_create_usage_cost_or_quality(self):
        record = measurement('tool_output.full_bytes', 8192, opaque('c'))
        result = view([record], ['tool_output.full_bytes'])
        self.assertEqual(result, [record])
        self.assertEqual(set(result[0]), set(record))
        for invented in ('tokens', 'input_tokens', 'output_tokens', 'money', 'cost',
                         'model_request', 'paid_request', 'quality_score', 'cache_hit'):
            self.assertNotIn(invented, result[0])

    def test_unregistered_names_invalid_records_and_nonopaque_scope_fail_closed(self):
        valid = measurement('context.loaded_bytes', 4, opaque('c'))
        self.assertEqual(view([valid], ['context.loaded_bytes']), [valid])
        with self.assertRaises(ValueError):
            view([valid], ['context.imaginary'])
        with self.assertRaises(ValueError):
            view([valid | {'unit': 'tokens'}], ['context.loaded_bytes'])
        with self.assertRaises(ValueError):
            view([valid], ['context.loaded_bytes'], {'owner_kind': 'run', 'owner_id': '/private'})
        with self.assertRaises(ValueError):
            view([valid], ['context.loaded_bytes'], SCOPE, '/private')


if __name__ == '__main__':
    unittest.main()
