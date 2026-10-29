#!/usr/bin/env python3
"""Offline checks for registered diagnostic measurements."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contract', ROOT / 'scripts/usage_telemetry_contract.py')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def call(name, *args):
    return getattr(contract, name, lambda *args: None)(*args)


def opaque(digit):
    return 'sha256:' + digit * 64


def diagnostic():
    return {'schema_version': 1, 'kind': 'diagnostic_measurement',
            'metric': 'context.loaded_bytes', 'value': 42, 'unit': 'bytes',
            'scope': {'owner_kind': 'run', 'owner_id': opaque('a')},
            'source_id': opaque('b'), 'quality': 'measured'}


def bundle():
    return {'schema_version': 1, 'kind': 'usage_bundle', 'profile_id': 'profile',
            'profile_version': '1', 'project_id': opaque('d'), 'run_id': 'run',
            'sources': [], 'observations': [], 'evidence_objects': [], 'inventories': [],
            'segments': [], 'diagnostics': [diagnostic()]}


class DiagnosticSchemaTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_diagnostic_measurement', value), value)

    def test_registered_metrics_preserve_units_and_scopes(self):
        for metric, unit in (('context.loaded_bytes', 'bytes'),
                             ('orchestration.tool_calls', 'count'),
                             ('verification.evidence_reuses', 'count'),
                             ('tool_output.full_bytes', 'bytes'),
                             ('tool_output.shown_bytes', 'bytes'),
                             ('tool_output.additional_read_bytes', 'bytes'),
                             ('repair.attempts', 'count'),
                             ('decomposition.rework', 'count')):
            value = diagnostic() | {'metric': metric, 'unit': unit}
            with self.subTest(metric=metric):
                self.assert_valid(value)
        self.assert_valid(diagnostic() | {'value': 0})

    def test_event_attempt_and_context_references_remain_opaque(self):
        value = diagnostic() | {'event_id': opaque('c'), 'attempt_id': opaque('e'),
                                'context_hash': opaque('f')}
        self.assert_valid(value)
        for field in ('event_id', 'attempt_id', 'context_hash'):
            with self.subTest(field=field):
                self.assert_valid(value | {field: None})
                for invalid in ('/private/path', 'secret-token', 'sha256:' + 'A' * 64):
                    with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                        call('validate_diagnostic_measurement', value | {field: invalid})

    def test_unknown_is_explicit_and_does_not_become_zero(self):
        value = diagnostic() | {'value': None, 'quality': 'unknown'}
        self.assert_valid(value)
        with self.assertRaises(ValueError):
            call('validate_diagnostic_measurement', value | {'value': 0})
        with self.assertRaises(ValueError):
            call('validate_diagnostic_measurement', value | {'quality': 'measured'})

    def test_invalid_metric_unit_value_scope_and_source(self):
        value = diagnostic()
        self.assert_valid(value)
        changes = ({'metric': 'secret.loaded_bytes'}, {'metric': 'context.arbitrary'},
                   {'unit': 'tokens'}, {'unit': 'USD'}, {'value': True}, {'value': -1},
                   {'value': 1.5}, {'value': 9007199254740992}, {'quality': 'excellent'},
                   {'scope': {}}, {'scope': {'owner_kind': 'run', 'owner_id': '/private'}},
                   {'source_id': '/private/source'})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_diagnostic_measurement', value | change)
        for field in value:
            with self.subTest(missing=field), self.assertRaises(ValueError):
                call('validate_diagnostic_measurement', {k: v for k, v in value.items() if k != field})
        for change in ({'schema_version': True}, {'schema_version': 2}, {'kind': 'other'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_diagnostic_measurement', value | change)

    def test_private_fields_are_rejected_without_echo(self):
        value = diagnostic()
        self.assert_valid(value)
        secret = 'PRIVATE_CONTENT_SENTINEL'
        with self.assertRaises(ValueError) as error:
            call('validate_diagnostic_measurement', value | {'raw_content': secret})
        self.assertNotIn(secret, str(error.exception))

    def test_byte_limit_and_duplicate_keys(self):
        value = diagnostic()
        self.assert_valid(value)
        data = json.dumps(value, separators=(',', ':')).encode()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'DIAGNOSTIC_LIMIT', size, create=True):
            self.assert_valid(value)
        with patch.object(contract, 'DIAGNOSTIC_LIMIT', size - 1, create=True):
            with self.assertRaises(ValueError):
                call('validate_diagnostic_measurement', value)
        with patch.object(contract, 'DIAGNOSTIC_LIMIT', len(data), create=True):
            self.assertEqual(call('validate_diagnostic_measurement_json', data), value)
            with self.assertRaises(ValueError):
                call('validate_diagnostic_measurement_json', data + b' ')
        with self.assertRaises(ValueError):
            call('validate_diagnostic_measurement_json', b'{"schema_version":1,"schema_version":1}')

    def test_bundle_accepts_valid_and_rejects_malformed_diagnostics(self):
        value = bundle()
        self.assertEqual(call('validate_usage_bundle', value), value)
        invalid = copy.deepcopy(value)
        invalid['diagnostics'][0]['unit'] = 'tokens'
        with self.assertRaises(ValueError):
            call('validate_usage_bundle', invalid)
        invalid = copy.deepcopy(value)
        invalid['diagnostics'][0]['source_id'] = '/private'
        with self.assertRaises(ValueError):
            call('validate_usage_bundle', invalid)


if __name__ == '__main__':
    unittest.main()
