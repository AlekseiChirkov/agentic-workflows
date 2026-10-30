#!/usr/bin/env python3
"""Cache applicability and unknown TTL are independently represented."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'tests/usage-resolution-integration.py')
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)


class CacheCapabilitiesTests(unittest.TestCase):
    def report(self, profile, allowed_filter=None):
        data, allowed = integration.fixture(profile_override=profile)
        if allowed_filter:
            allowed = [item for item in allowed if allowed_filter(item)]
        result = integration.resolve(data, integration.Verifier(allowed))
        self.assertIsInstance(result, dict)
        return result

    def test_proven_unsupported_cache_does_not_require_inapplicable_components(self):
        profile = integration.profiles.profile(False)
        profile['counter_fields'] = [entry for entry in profile['counter_fields']
                                     if entry['measurement'] not in ('input_cache_read', 'input_cache_write',
                                                                     'input_cache_write_unsplit')]
        profile['capabilities']['cache'] = 'unsupported'
        result = self.report(profile)
        self.assertEqual(result['tokens']['input'], {'value': '2000', 'quality': 'complete'})
        self.assertEqual(result['tokens']['output'], {'value': '200', 'quality': 'complete'})
        self.assertEqual(result['completeness']['priced'], {'numerator': 1, 'denominator': 2})
        self.assertEqual(result['cost']['priced_subtotal_usd'], '0.003')
        untrusted = self.report(profile, lambda item: item[0] != 'profile')
        self.assertNotEqual(untrusted['tokens']['input'].get('quality'), 'complete')

    def test_unsupported_cache_cannot_declare_cache_measurements(self):
        valid = integration.profiles.profile(False)
        valid['counter_fields'] = [entry for entry in valid['counter_fields']
                                   if entry['measurement'] not in ('input_cache_read', 'input_cache_write',
                                                                   'input_cache_write_unsplit')]
        valid['capabilities']['cache'] = 'unsupported'
        self.assertEqual(integration.contract.validate_source_profile(valid), valid)
        contradictory = integration.profiles.profile()
        contradictory['capabilities']['cache'] = 'unsupported'
        for forbidden in ('input_cache_read', 'input_cache_write', 'input_cache_write_unsplit'):
            bad = copy.deepcopy(valid)
            bad['counter_fields'].append(next(copy.deepcopy(entry) for entry in contradictory['counter_fields']
                                              if entry['measurement'] == forbidden))
            with self.subTest(measurement=forbidden), self.assertRaises(ValueError):
                integration.contract.validate_source_profile(bad)
        for included in ('input_cache_read', 'input_cache_write', 'input_cache_write_unsplit'):
            bad = copy.deepcopy(valid)
            bad['counter_fields'][0]['measurement'] = 'input_total'
            bad['counter_fields'][0]['includes'] = [included]
            with self.subTest(included=included), self.assertRaises(ValueError):
                integration.contract.validate_source_profile(bad)

    def test_unsplit_write_preserves_tokens_but_its_price_remains_unknown(self):
        profile = integration.profiles.profile()
        profile['counter_fields'] = [entry for entry in profile['counter_fields']
                                     if entry['measurement'] != 'input_cache_write']
        result = self.report(profile)
        self.assertEqual(result['tokens']['input'], {'value': '2000', 'quality': 'complete'})
        self.assertEqual(result['tokens']['output'], {'value': '200', 'quality': 'complete'})
        self.assertEqual(result['completeness']['priced'], {'numerator': 0, 'denominator': 2})
        self.assertEqual(result['cost']['priced_subtotal_usd'], '0.00224')
        self.assertTrue(result['cost']['unpriced_ids'])
        self.assertNotIn('cost_usd', result['cost'])


if __name__ == '__main__':
    unittest.main()
