#!/usr/bin/env python3
"""Verified response token components retain independent quality and evidence."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('revisions', ROOT / 'tests/usage-resolution-revisions.py')
revisions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revisions)
base, contract = revisions.base, revisions.contract


class TokenComponentTests(unittest.TestCase):
    def test_verified_final_response_exposes_independent_components(self):
        data, allowed = base.fixture()
        result = base.resolve(data, base.Verifier(allowed))
        expected = {'input_uncached': '600', 'input_cache_read': '200',
                    'input_cache_write': '200', 'output': '100', 'reasoning': '25'}
        for response in result['responses']:
            self.assertEqual(response['token_components'], {
                key: {'value': value, 'quality': 'complete'} for key, value in expected.items()})

    def test_conflicting_unsplit_writes_do_not_recreate_input_totals(self):
        for included in (False, True):
            with self.subTest(included=included):
                selected = base.profiles.profile(included)
                selected['counter_fields'].append(base.profiles.field('other_write', 'input_cache_write_unsplit'))
                raw = {'input': 1000 if included else 600, 'read': 200, 'write': 200,
                       'other_write': 999, 'short': 100, 'long': 100, 'output': 100, 'reasoning': 25}
                data, allowed = base.fixture(raw_override=raw, profile_override=selected)
                result = base.resolve(data, base.Verifier(allowed))
                for response in result['responses']:
                    self.assertEqual(response['tokens']['input'], {'quality': 'unavailable'})
                    self.assertEqual(response['tokens']['output'], {'value': '100', 'quality': 'complete'})

    def test_partial_component_is_never_reported_complete(self):
        data, _ = revisions.snapshot_fixture()
        observation = data['bundle']['observations'][1]
        observation['measurements']['input_cache_write'][0]['tokens']['measurement_state'] = 'partial'
        observation['measurements']['reasoning_subset']['measurement_state'] = 'partial'
        data['contexts'][1]['observation_id'] = contract.observation_id(observation)
        result = base.resolve(data, base.Verifier(revisions.authorize(data)))
        components = result['responses'][0]['token_components']
        self.assertEqual(components['input_cache_write'], {'value': '200', 'quality': 'partial'})
        self.assertEqual(components['reasoning'], {'value': '25', 'quality': 'partial'})
        self.assertEqual(components['output'], {'value': '100', 'quality': 'complete'})

    def test_missing_authorization_never_produces_a_value(self):
        data, allowed = base.fixture()
        allowed = [entry for entry in allowed if not (
            entry[0] == 'measurement' and entry[2]['observation']['record_number'] == 1 and
            (entry[2]['field'] == 'reasoning_subset' or
             entry[2]['field'] == 'input_cache_write' and entry[2].get('ttl') == '1h'))]
        result = base.resolve(data, base.Verifier(allowed))
        first = next(item for item in result['responses'] if item['identity']['id'] == base.opaque('1'))
        self.assertEqual(first['token_components']['reasoning'], {'quality': 'unavailable'})
        self.assertEqual(first['token_components']['input_cache_write'], {'quality': 'unavailable'})

    def test_final_delta_parts_use_terminal_without_double_counting(self):
        data, allowed = revisions.delta_fixture()
        result = base.resolve(data, base.Verifier(allowed))
        components = result['responses'][0]['token_components']
        self.assertEqual(components['input_uncached'], {'value': '30', 'quality': 'complete'})
        self.assertEqual(components['output'], {'value': '3', 'quality': 'complete'})
        self.assertEqual(components['reasoning'], {'quality': 'unavailable'})


if __name__ == '__main__':
    unittest.main()
