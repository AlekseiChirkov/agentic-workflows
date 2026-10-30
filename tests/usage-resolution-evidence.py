#!/usr/bin/env python3
"""Bounded resolution evidence and independent source-operand authorization."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)
contract = integration.contract


def authorize_operands(data, allowed):
    objects = {contract.content_id(item): item for item in data['bundle']['evidence_objects']}
    for observation in data['bundle']['observations']:
        def add(digest):
            evidence = objects[digest]
            if evidence['kind'] == 'derived_measurement_evidence':
                for child in evidence['operands']:
                    add(child)
            else:
                subject = {'observation': observation, 'field': evidence['field']}
                if 'ttl' in evidence:
                    subject['ttl'] = evidence['ttl']
                binding = ('measurement', data['scope'], subject, evidence)
                if binding not in allowed:
                    allowed.append(binding)
        for value in observation['measurements'].values():
            values = [part['tokens'] for part in value] if isinstance(value, list) else [value]
            for measurement in values:
                if 'evidence' in measurement:
                    add(measurement['evidence'])


class ContextEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data, self.allowed = integration.fixture()
        authorize_operands(self.data, self.allowed)
        self.verifier = integration.Verifier(self.allowed)

    def test_context_has_closed_bounded_schema(self):
        validate = getattr(contract, 'validate_resolution_context', None)
        self.assertIsNotNone(validate, 'a bounded resolution context schema is required')
        context = self.data['contexts'][0]
        self.assertEqual(validate(context), context)
        for mutation in ({'raw_text': 'PRIVATE_SENTINEL'}, {'record_number': True},
                         {'counter_scope': 'unsupported'}, {'session_id': '/secret'},
                         {'observation_id': 'invalid'}, {'evidence_objects': [{}] * 10001}):
            with self.subTest(mutation=list(mutation)), self.assertRaises((TypeError, ValueError)) as error:
                validate(context | mutation)
            self.assertNotIn('PRIVATE_SENTINEL', str(error.exception))

    def test_operand_provenance_is_independently_authorized(self):
        result = integration.resolve(self.data, self.verifier)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['completeness']['measurements']['input'], {'numerator': 2, 'denominator': 2})
        operands = [call for call in self.verifier.calls if call[0] == 'measurement'
                    and call[2]['field'] == 'input_total']
        self.assertEqual({call[2]['observation']['record_number'] for call in operands}, {1, 2})
        self.assertTrue(all(call[3]['source_hash'] == call[2]['observation']['source_hash'] and
                            call[3]['record_number'] == call[2]['observation']['record_number'] and
                            call[3]['value'] == 1000 for call in operands))

    def test_matching_derived_digest_does_not_authorize_untrusted_raw_operand(self):
        self.verifier.allowed = [item for item in self.allowed if not (
            item[0] == 'measurement' and item[2]['field'] == 'input_total' and
            item[2]['observation']['record_number'] == 1)]
        result = integration.resolve(self.data, self.verifier)
        self.assertIsInstance(result, dict)
        self.assertLess(result['completeness']['measurements']['input']['numerator'], 2)
        self.assertNotIn('cost_usd', result['cost'])

    def test_scope_binding_changes_evidence_domain(self):
        original = copy.deepcopy(self.data['contexts'][0])
        changed = copy.deepcopy(original)
        changed['provider_scope'] = integration.opaque('f')
        self.assertNotEqual(contract.content_id(original), contract.content_id(changed))
        self.data['contexts'][0] = changed
        result = integration.resolve(self.data, self.verifier)
        self.assertIsInstance(result, dict)
        self.assertLess(result['completeness']['measurements']['input']['numerator'], 2)
        self.assertNotIn('cost_usd', result['cost'])


if __name__ == '__main__':
    unittest.main()
