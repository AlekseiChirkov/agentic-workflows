#!/usr/bin/env python3
"""Selected-source adapter to independently authorized resolution context."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


base = load('integration', 'tests/usage-resolution-integration.py')
evidence = load('evidence_fixtures', 'tests/usage-resolution-evidence.py')
source = load('source_fixtures', 'tests/usage-bounded-source-reads.py')
adapter = load('usage_adapter', 'scripts/usage_telemetry_adapter.py')
contract = base.contract


def profile():
    result = base.profiles.profile()
    result['resolution_fields'] = {
        'status': 'verified',
        'response_id': ['metadata', 'response'],
        'call_id': ['metadata', 'call'],
        'session_id': ['metadata', 'session'],
        'execution_time': ['metadata', 'time'],
        'finality': {'path': ['metadata', 'complete'], 'kind': 'snapshot', 'final_value': True},
        'parameters': {name: ['metadata', name] for name in ('model', 'service_tier', 'region', 'modality')},
        'cache_ttl_seconds': {'5m': 300, '1h': 3600},
    }
    return result


class ProducerResolutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'private-source.jsonl'
        self.raw = {'usage': {'input': 1000, 'read': 200, 'write': 200,
                              'short': 100, 'long': 100, 'output': 100, 'reasoning': 25},
                    'metadata': {'response': 'PRIVATE_RESPONSE', 'call': 'PRIVATE_CALL',
                                 'session': 'PRIVATE_SESSION', 'time': '2026-01-01T00:00:00Z',
                                 'complete': True, 'model': 'vendor/model', 'service_tier': 'standard',
                                 'region': 'example-region', 'modality': 'text'},
                    'private_payload': 'PRIVATE_PAYLOAD_SENTINEL'}
        self.scope = {'owner_kind': 'run', 'owner_id': base.opaque('b')}
        self.calls = []
        self.write()

    def write(self):
        content = (json.dumps(self.raw) + '\n').encode()
        self.path.write_bytes(content)
        self.selection = source.manifest(self.path, content, owner_scope=self.scope)

    def verify_resolution(self, kind, selected_profile, observation, proof):
        self.calls.append((kind, copy.deepcopy(selected_profile), copy.deepcopy(observation), copy.deepcopy(proof)))
        if (selected_profile != profile() or observation['source_hash'] != self.selection['sources'][0]['sha256']
                or observation['record_number'] != 1 or observation['counter_scope'] != 'response_total'):
            return False
        allowed = {'model': 'vendor/model', 'service_tier': 'standard',
                   'region': 'example-region', 'modality': 'text'}
        if kind == 'measurement_finality':
            value = observation['measurements'].get(proof['field'])
            if isinstance(value, list):
                value = next((part['tokens'] for part in value if part['ttl'] == proof.get('ttl')), None)
            return value == proof['measurement'] and value is not None and value['measurement_state'] == 'partial'
        if kind == 'parameter':
            return (proof.get('kind') == 'source_parameter_evidence' and
                    proof.get('field') in allowed and proof.get('value') == allowed[proof['field']] and
                    all(proof[k] == observation[k] for k in ('profile_id', 'source_hash', 'record_number')))
        if kind == 'context':
            expected = dict(allowed)
            for field in expected:
                if field not in self.raw['metadata']:
                    expected[field] = None
            return (proof['parameters'] == expected and
                    proof['execution_time'] == self.raw['metadata'].get('time') and
                    all(proof[k] == observation[k] for k in ('profile_id', 'profile_version', 'source_hash',
                                                             'record_number', 'provider_scope', 'counter_scope')))
        return False

    def produce(self, selected_profile, verifier=True):
        options = {'verify_resolution': self.verify_resolution} if verifier else {}
        return adapter.normalize_selection(self.selection, profile=selected_profile,
                    expected_owner_scope=self.scope, project_identifier='PRIVATE_PROJECT',
                    provider_identifier='PRIVATE_ACCOUNT', run_id='run',
                    key=b'private-mapping-key-that-is-long-enough-for-tests', **options)

    def prepare_resolution(self, result, selected_profile):
        data, _ = base.fixture()
        bundle = result['bundle']
        observation = bundle['observations'][0]
        inv, _ = base.inventories.inventory(('1',))
        inv.update(profile_id=selected_profile['profile_id'], source_hash=observation['source_hash'],
                   owner_scope=self.scope, window={'start': '2026-01-01T00:00:00Z',
                                                   'end': '2026-01-02T00:00:00Z'},
                   observed_at='2026-01-02T00:00:01Z',
                   expected_calls=[{'call_id': observation['call_id']}],
                   expected_responses=[{'call_id': observation['call_id'],
                                        'response_id': observation['response_id']}])
        inv, inv_proof = base.inventories.bind(inv)
        bundle['inventories'] = [inv]
        bundle['evidence_objects'].append(inv_proof)
        data.update(bundle=bundle, profile=selected_profile, contexts=result['contexts'], scope=self.scope)
        allowed = [('profile', self.scope, selected_profile, selected_profile),
                   ('inventory', self.scope, inv, inv_proof),
                   ('nonnegative_scope', self.scope, inv, inv_proof)]
        for context in result['contexts']:
            allowed.append(('context', self.scope, observation, context))
            allowed.append(('response_privacy', self.scope, observation, observation))
            for proof in context['evidence_objects']:
                allowed.append(('pricing_context', self.scope, observation, proof))
        objects = {contract.content_id(item): item for item in bundle['evidence_objects']}
        for field, value in observation['measurements'].items():
            parts = [(item['ttl'], item['tokens']) for item in value] if isinstance(value, list) else [(None, value)]
            for ttl, measurement in parts:
                if 'evidence' in measurement:
                    subject = {'observation': observation, 'field': field}
                    if ttl is not None:
                        subject['ttl'] = ttl
                    allowed.append(('measurement', self.scope, subject, objects[measurement['evidence']]))
        evidence.authorize_operands(data, allowed)
        for proof in data['price_evidence']:
            allowed.append(('price', self.scope, data['snapshots'][0], proof))
        contract.validate_usage_bundle(bundle)
        return data, allowed

    def test_verified_profile_produces_sanitized_bound_context_usable_by_resolver(self):
        selected_profile = profile()
        actual = __import__('usage_telemetry_sources')._open_regular
        opened = []
        def track(path):
            opened.append(path)
            return actual(path)
        with patch('socket.socket', side_effect=AssertionError('network')), \
             patch('usage_telemetry_sources._open_regular', side_effect=track):
            result = self.produce(selected_profile)
        self.assertEqual(opened, [str(self.path)])
        self.assertEqual(len(result['contexts']), 1)
        parameters = [call for call in self.calls if call[0] == 'parameter']
        self.assertEqual({call[3]['field'] for call in parameters}, {'model', 'service_tier', 'region', 'modality'})
        self.assertTrue(all(call[2]['record_number'] == call[3]['record_number'] == 1 and
                            call[2]['source_hash'] == call[3]['source_hash'] for call in parameters))
        self.assertTrue(any(call[0] == 'context' for call in self.calls))
        observation = result['bundle']['observations'][0]
        context = result['contexts'][0]
        self.assertEqual(context['observation_id'], contract.observation_id(observation))
        self.assertEqual(context['source_hash'], observation['source_hash'])
        self.assertEqual(context['record_number'], observation['record_number'])
        self.assertEqual(context['provider_scope'], observation['provider_scope'])
        self.assertEqual(context['counter_scope'], observation['counter_scope'])
        self.assertTrue(context['event']['final'])
        wrappers = [item for item in result['bundle']['evidence_objects']
                    if item.get('kind') == 'resolution_context_evidence']
        self.assertEqual(len(wrappers), 1)
        self.assertEqual(wrappers[0]['context'], context)
        self.assertEqual(contract.validate_evidence_object(wrappers[0]), wrappers[0])
        forged = copy.deepcopy(result['bundle'])
        wrapper = next(item for item in forged['evidence_objects']
                       if item.get('kind') == 'resolution_context_evidence')
        wrapper['context']['provider_scope'] = base.opaque('f')
        with self.assertRaises(ValueError):
            contract.validate_usage_bundle(forged)
        for item in (observation['response_id'], observation['call_id'], context['session_id']):
            self.assertRegex(item, r'^sha256:[0-9a-f]{64}$')
        self.assertNotEqual(observation['response_id'], observation['call_id'])
        serialized = json.dumps(result)
        for secret in ('PRIVATE_RESPONSE', 'PRIVATE_CALL', 'PRIVATE_SESSION', 'PRIVATE_PROJECT',
                       'PRIVATE_ACCOUNT', 'PRIVATE_PAYLOAD_SENTINEL', str(self.path)):
            self.assertNotIn(secret, serialized)
        data, allowed = self.prepare_resolution(result, selected_profile)
        report = base.resolve(data, base.Verifier(allowed))
        self.assertEqual(report['tokens']['input'], {'value': '1000', 'quality': 'complete'})
        self.assertEqual(report['tokens']['output'], {'value': '100', 'quality': 'complete'})
        self.assertEqual(report['responses'][0]['model_cost']['cost_usd'], '0.00289')
        untrusted = [item for item in allowed if item[0] != 'context']
        report = base.resolve(data, base.Verifier(untrusted))
        self.assertNotEqual(report['tokens']['input'].get('quality'), 'complete')
        self.assertNotIn('cost_usd', report['cost'])

    def test_missing_or_unknown_profile_semantics_never_guess_context_or_identity(self):
        for selected_profile in (base.profiles.profile(), profile() | {'resolution_fields': {'status': 'unknown'}}):
            with self.subTest(profile=selected_profile.get('resolution_fields')):
                result = self.produce(selected_profile)
                self.assertEqual(result.get('contexts', []), [])
                self.assertNotIn('response_id', result['bundle']['observations'][0])
                self.assertNotIn('call_id', result['bundle']['observations'][0])

    def test_finality_and_missing_required_source_data_never_become_final_by_guessing(self):
        self.raw['metadata']['complete'] = False
        self.write()
        result = self.produce(profile())
        self.assertFalse(result['contexts'][0]['event']['final'])
        self.raw['metadata'].pop('model')
        self.raw['metadata']['complete'] = True
        self.write()
        selected_profile = profile()
        result = self.produce(selected_profile)
        self.assertIsNone(result['contexts'][0]['parameters']['model'])
        self.assertFalse(any(proof.get('field') == 'model' for proof in result['contexts'][0]['evidence_objects']))
        data, allowed = self.prepare_resolution(result, selected_profile)
        report = base.resolve(data, base.Verifier(allowed))
        self.assertEqual(report['tokens']['input'], {'value': '1000', 'quality': 'complete'})
        self.assertEqual(report['completeness']['priced'], {'numerator': 0, 'denominator': 1})
        self.assertNotIn('cost_usd', report['cost'])
        self.assertNotIn('PRIVATE_PAYLOAD_SENTINEL', json.dumps(result))

    def test_any_unknown_pricing_dimension_preserves_independent_tokens(self):
        original = copy.deepcopy(self.raw)
        for field in ('model', 'service_tier', 'region', 'modality'):
            with self.subTest(field=field):
                self.raw = copy.deepcopy(original)
                del self.raw['metadata'][field]
                self.write()
                selected_profile = profile()
                result = self.produce(selected_profile)
                self.assertIsNone(result['contexts'][0]['parameters'][field])
                data, allowed = self.prepare_resolution(result, selected_profile)
                report = base.resolve(data, base.Verifier(allowed))
                self.assertEqual(report['tokens']['input'], {'value': '1000', 'quality': 'complete'})
                self.assertEqual(report['completeness']['priced'], {'numerator': 0, 'denominator': 1})
                self.assertNotIn('cost_usd', report['cost'])

    def test_unknown_execution_time_does_not_hide_tokens_or_assume_a_price(self):
        del self.raw['metadata']['time']
        self.write()
        selected_profile = profile()
        result = self.produce(selected_profile)
        context = result['contexts'][0]
        self.assertIsNone(context['execution_time'])
        self.assertFalse(any(proof.get('kind') == 'execution_time_evidence'
                             for proof in context['evidence_objects']))
        data, allowed = self.prepare_resolution(result, selected_profile)
        report = base.resolve(data, base.Verifier(allowed))
        self.assertEqual(report['tokens']['input'], {'value': '1000', 'quality': 'complete'})
        self.assertEqual(report['completeness']['priced'], {'numerator': 0, 'denominator': 1})
        self.assertNotIn('cost_usd', report['cost'])

    def test_unverified_context_and_secret_parameter_are_never_published(self):
        result = self.produce(profile(), verifier=False)
        self.assertEqual(result.get('contexts', []), [])
        self.assertNotIn('response_id', result['bundle']['observations'][0])
        self.assertFalse(any(item.get('kind') == 'resolution_context_evidence'
                             for item in result['bundle']['evidence_objects']))
        self.raw['metadata']['model'] = 'PRIVATE_SECRET'
        self.write()
        result = self.produce(profile())
        self.assertEqual(result.get('contexts', []), [])
        self.assertNotIn('PRIVATE_SECRET', json.dumps(result))
        self.assertFalse(any(item.get('kind') == 'resolution_context_evidence'
                             for item in result['bundle']['evidence_objects']))

    def test_nonboolean_verification_claims_do_not_authorize_publication(self):
        result = adapter.normalize_selection(self.selection, profile=profile(),
                    expected_owner_scope=self.scope, project_identifier='PRIVATE_PROJECT',
                    provider_identifier='PRIVATE_ACCOUNT', run_id='run',
                    key=b'private-mapping-key-that-is-long-enough-for-tests',
                    verify_resolution=lambda *_: {'verified': True})
        self.assertEqual(result.get('contexts', []), [])
        self.assertNotIn('response_id', result['bundle']['observations'][0])

    def test_source_mapping_is_closed_bounded_and_rejects_unverified_guesses(self):
        valid = profile()
        self.assertEqual(contract.validate_source_profile(valid), valid)
        for mutation in ({'status': 'unknown', 'response_id': ['metadata', 'response']},
                         {'status': 'verified', 'response_id': ['/private/path']},
                         {'status': 'verified', 'unexpected': 'PRIVATE_SECRET'}):
            bad = copy.deepcopy(valid)
            bad['resolution_fields'] = mutation
            with self.subTest(mutation=list(mutation)), self.assertRaises(ValueError) as caught:
                contract.validate_source_profile(bad)
            self.assertNotIn('PRIVATE_SECRET', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
