#!/usr/bin/env python3
"""Offline tests for bounded publication receipts."""
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


def receipt():
    return {
        'schema_version': 1, 'kind': 'usage_accepted',
        'bundle_sha256': 'a' * 64,
        'observation_ids': ['1' * 64, '2' * 64],
        'scope': {'owner_kind': 'run', 'owner_id': 'sha256:' + '3' * 64,
                  'attribution_quality': 'unknown'},
        'duplicate': False, 'validator_version': '1',
    }


class ReceiptSchemaTests(unittest.TestCase):
    def assert_valid(self, value):
        self.assertEqual(call('validate_usage_receipt', value), value)

    def test_complete_receipt_preserves_declarations_and_unknown_attribution(self):
        value = receipt()
        self.assert_valid(value)
        self.assertEqual(value['scope']['attribution_quality'], 'unknown')
        for quality in ('asserted', 'verified', 'inferred'):
            changed = copy.deepcopy(value)
            changed['scope']['attribution_quality'] = quality
            self.assert_valid(changed)
        changed = copy.deepcopy(value)
        changed['scope']['owner_kind'] = 'session'
        changed['duplicate'] = True
        self.assert_valid(changed)
        changed['observation_ids'] = []
        self.assert_valid(changed)

    def test_required_fields_versions_and_closed_shape(self):
        value = receipt()
        self.assert_valid(value)
        for field in value:
            with self.subTest(missing=field), self.assertRaises(ValueError):
                call('validate_usage_receipt', {k: v for k, v in value.items() if k != field})
        for change in ({'schema_version': 2}, {'schema_version': True}, {'kind': 'accepted'},
                       {'kind': 'analysis'}, {'duplicate': 0}, {'duplicate': 'false'},
                       {'validator_version': ''}, {'validator_version': None},
                       {'bundle_sha256': 'A' * 64}, {'bundle_sha256': 'a' * 63},
                       {'observation_ids': None}, {'observation_ids': ['1' * 63]},
                       {'observation_ids': ['1' * 64, '1' * 64]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_usage_receipt', value | change)

    def test_scope_is_declared_closed_and_has_explicit_quality(self):
        value = receipt()
        self.assert_valid(value)
        for field in value['scope']:
            changed = copy.deepcopy(value)
            del changed['scope'][field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                call('validate_usage_receipt', changed)
        for change in ({'owner_kind': 'other'}, {'owner_id': None},
                       {'owner_id': '/private/source'}, {'attribution_quality': None},
                       {'attribution_quality': 'proven'}, {'path': '/private/source'}):
            changed = copy.deepcopy(value)
            changed['scope'].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                call('validate_usage_receipt', changed)

    def test_observation_count_and_duplicate_identifier_bounds(self):
        value = receipt()
        self.assert_valid(value)
        value['observation_ids'] = [f'{index:064x}' for index in range(10000)]
        self.assert_valid(value)
        value['observation_ids'].append(f'{10000:064x}')
        with self.assertRaises(ValueError):
            call('validate_usage_receipt', value)

    def test_private_content_is_not_allowed_or_echoed(self):
        value = receipt()
        self.assert_valid(value)
        for change in ({'raw_content': 'PRIVATE_CONTENT_SENTINEL'},
                       {'validator_version': '/PRIVATE_CONTENT_SENTINEL'},
                       {'bundle_sha256': 'PRIVATE_CONTENT_SENTINEL'},
                       {'observation_ids': ['PRIVATE_CONTENT_SENTINEL']}):
            with self.subTest(change=change), self.assertRaises(ValueError) as error:
                call('validate_usage_receipt', value | change)
            self.assertNotIn('PRIVATE_CONTENT_SENTINEL', str(error.exception))

    def test_raw_and_canonical_byte_limits_and_duplicate_json_keys(self):
        value = receipt()
        self.assert_valid(value)
        data = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
        size = len(contract.canonical_bytes(value))
        with patch.object(contract, 'RECEIPT_LIMIT', size, create=True):
            self.assert_valid(value)
        with patch.object(contract, 'RECEIPT_LIMIT', size - 1, create=True):
            with self.assertRaises(ValueError):
                call('validate_usage_receipt', value)
        with patch.object(contract, 'RECEIPT_LIMIT', len(data), create=True):
            self.assertEqual(call('validate_usage_receipt_json', data), value)
            with self.assertRaises(ValueError):
                call('validate_usage_receipt_json', data + b' ')
        with self.assertRaises(ValueError):
            call('validate_usage_receipt_json', b'{"schema_version":1,"schema_version":1}')

    def test_validation_does_not_infer_acceptance_from_process_status(self):
        # A zero exit or any ordinary output is not a publication receipt.
        for output in ({'exit_code': 0}, {'kind': 'accepted'}, {}, None):
            with self.subTest(output=output), self.assertRaises(ValueError):
                call('validate_usage_receipt', output)

    def test_observation_identifiers_are_a_canonical_set(self):
        first = receipt()
        second = copy.deepcopy(first)
        second['observation_ids'].reverse()
        self.assert_valid(first)
        self.assert_valid(second)
        self.assertEqual(contract.canonical_bytes(first), contract.canonical_bytes(second))
        self.assertEqual(contract.content_id(first), contract.content_id(second))

    def test_callers_cannot_override_receipt_set_order(self):
        value = receipt()
        self.assert_valid(value)
        with self.assertRaises(ValueError):
            contract.canonical_bytes(value, set_keys={('observation_ids',): lambda item: -int(item, 16)})


if __name__ == '__main__':
    unittest.main()
