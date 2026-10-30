#!/usr/bin/env python3
"""Offline acceptance across selected sources, publication and reporting."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

producer = load('producer_fixture', 'tests/usage-producer-resolution.py')
base = producer.base
contract = base.contract
rsa = load('acceptance_rsa', 'tests/usage-authority-rsa-permit.py')

class OfflineAcceptance(unittest.TestCase):
    def test_selected_source_to_frozen_exports(self):
        import usage_telemetry_report as report
        import usage_telemetry_exports as exports
        with tempfile.TemporaryDirectory() as temp, patch('socket.socket', side_effect=AssertionError('network')):
            root = Path(temp)
            fixture = producer.ProducerResolutionTests('test_verified_profile_produces_sanitized_bound_context_usable_by_resolver')
            fixture.setUp()
            self.addCleanup(fixture.doCleanups)
            authority = rsa.RsaPermitTests('test_valid_permit_publishes_without_external_libraries')
            authority.setUp()
            self.addCleanup(authority.doCleanups)
            fixture.scope = authority.fixture.config['owner_scope']
            first = copy.deepcopy(fixture.raw)
            second = copy.deepcopy(first)
            second['metadata'].update(response='SECOND_RESPONSE', call='SECOND_CALL', time='2028-01-01T00:00:00Z')
            raw = b''.join((json.dumps(row) + '\n').encode() for row in (first, first, second))
            fixture.path.write_bytes(raw)
            fixture.selection = producer.source.manifest(fixture.path, raw, owner_scope=fixture.scope)
            selected_profile = producer.profile()
            def verify(kind, profile, observation, proof):
                if profile != selected_profile or observation['source_hash'] != fixture.selection['sources'][0]['sha256']:
                    return False
                return kind in ('measurement_finality', 'parameter', 'context')
            result = producer.adapter.normalize_selection(fixture.selection, profile=selected_profile,
                expected_owner_scope=fixture.scope, project_identifier=authority.fixture.config['project_identifier'],
                provider_identifier='PRIVATE_ACCOUNT', run_id=authority.fixture.run_id,
                key=bytes.fromhex(authority.fixture.config['key_hex']), verify_resolution=verify)
            bundle = result['bundle']
            observations = bundle['observations']
            self.assertEqual(len(observations), 3)
            self.assertEqual(observations[0]['response_id'], observations[1]['response_id'])
            inv, _ = base.inventories.inventory(('1', '2'))
            inv.update(profile_id=selected_profile['profile_id'], source_hash=observations[0]['source_hash'],
                       owner_scope=fixture.scope, window={'start': '2026-01-01T00:00:00Z', 'end': '2029-01-01T00:00:00Z'},
                       observed_at='2029-01-01T00:00:01Z',
                       expected_calls=[{'call_id': observations[i]['call_id']} for i in (0, 2)],
                       expected_responses=[{'call_id': observations[i]['call_id'], 'response_id': observations[i]['response_id']} for i in (0, 2)])
            inv, inv_proof = base.inventories.bind(inv)
            bundle['inventories'] = [inv]
            bundle['evidence_objects'].append(inv_proof)
            authority.fixture.bundle = bundle
            authority.fixture.output.write_bytes(contract.canonical_bytes(bundle))
            authority.fixture.sign()
            authority.body.update(bundle_sha256=hashlib.sha256(contract.canonical_bytes(bundle)).hexdigest(),
                                  profile_id=bundle['profile_id'], profile_version=bundle['profile_version'],
                                  run_id=bundle['run_id'], scope=fixture.scope)
            authority.write_permit(authority.body)
            before = authority.fixture.lifecycle.read_bytes()
            receipt = authority.invoke()
            self.assertFalse(receipt['duplicate'])
            installed = authority.fixture.artifact()
            self.assertEqual(installed.read_bytes(), contract.canonical_bytes(bundle))
            self.assertTrue(authority.invoke()['duplicate'])
            self.assertEqual(authority.fixture.lifecycle.read_bytes(), before)
            data, _ = base.fixture()
            snapshot = data['snapshots'][0]
            old_snapshot_id = contract.price_snapshot_id(snapshot)
            next(rate for rate in snapshot['rates'] if rate['component'] == 'output')['usd'] = '7.5'
            new_snapshot_id = contract.price_snapshot_id(snapshot)
            data['scenario']['snapshot_ids'] = [new_snapshot_id]
            for proof in data['price_evidence']:
                if proof.get('snapshot_id') == old_snapshot_id:
                    proof['snapshot_id'] = new_snapshot_id
            data.update(bundle=json.loads(installed.read_bytes()), profile=selected_profile, contexts=result['contexts'], scope=fixture.scope)
            allowed = [('profile', fixture.scope, selected_profile, selected_profile), ('inventory', fixture.scope, inv, inv_proof), ('nonnegative_scope', fixture.scope, inv, inv_proof)]
            objects = {contract.content_id(item): item for item in bundle['evidence_objects']}
            for observation, context in zip(observations, result['contexts']):
                allowed.extend([('context', fixture.scope, observation, context), ('response_privacy', fixture.scope, observation, observation)])
                allowed.extend(('pricing_context', fixture.scope, observation, proof) for proof in context['evidence_objects'])
                for field, value in observation['measurements'].items():
                    parts = [(part['ttl'], part['tokens']) for part in value] if isinstance(value, list) else [(None, value)]
                    for ttl, measurement in parts:
                        if 'evidence' in measurement:
                            subject = {'observation': observation, 'field': field}
                            if ttl is not None: subject['ttl'] = ttl
                            allowed.append(('measurement', fixture.scope, subject, objects[measurement['evidence']]))
            producer.evidence.authorize_operands(data, allowed)
            allowed.extend(('price', fixture.scope, data['snapshots'][0], proof) for proof in data['price_evidence'])
            canonical = lambda value: contract.parse_json(contract.canonical_bytes(value))
            verifier = base.Verifier([(kind, canonical(scope), canonical(subject), canonical(proof)) for kind, scope, subject, proof in allowed])
            manifest = {'schema_version': 1, 'kind': 'analysis_corpus', 'as_of': data['as_of'], 'scope': fixture.scope,
                        'scenario_id': data['scenario']['scenario_id'], 'versions': {'bundle_schema_version': 1,
                        'receipt_schema_version': 1, 'price_schema_version': 1, 'normalizer_version': '1'},
                        'identifier_mappings': [], 'inputs': [], 'exclusions': [], 'max_source_bytes': 1000000,
                        'max_total_bytes': 10000000, 'max_records': 1000}
            values = [('usage_bundle', data['bundle']), ('source_profile', data['profile']), ('pricing_scenario', data['scenario'])]
            values += [('price_snapshot', v) for v in data['snapshots']] + [('resolution_context', v) for v in data['contexts']] + [('price_evidence', v) for v in data['price_evidence']]
            for index, (kind, value) in enumerate(values):
                encoded = contract.canonical_bytes(value)
                path = root / (str(index) + '.json')
                path.write_bytes(encoded)
                manifest['inputs'].append({'kind': kind, 'schema_version': 1, 'local_path': str(path), 'sha256': hashlib.sha256(encoded).hexdigest(), 'size_bytes': len(encoded)})
            selected = {item['sha256'] for item in manifest['inputs']}
            def verify_input(item, value, scope):
                if item['sha256'] not in selected or scope != fixture.scope: raise ValueError('untrusted input')
                proof = {'scope': copy.deepcopy(scope), 'observed_at': '2029-01-01T00:00:00Z'}
                if item['kind'] == 'resolution_context':
                    proof['member_times'] = {contract.content_id(e): '2029-01-01T00:00:00Z' for e in value['evidence_objects']}
                return proof
            def analyze():
                return report.analyze_corpus(copy.deepcopy(manifest), verify_input=verify_input, verify_evidence=verifier)
            output = analyze()
            self.assertEqual(output['coverage']['measurements'], {'numerator': 2, 'denominator': 2})
            self.assertEqual(output['coverage']['pricing'], {'numerator': 1, 'denominator': 2})
            self.assertEqual(output['pricing']['priced_subtotal_cost'], '0.00264')
            rendered = exports.render_exports(output)
            self.assertEqual(set(rendered), {'json', 'csv', 'markdown'})
            self.assertEqual(rendered, exports.render_exports(analyze()))


    def test_complete_resolved_price_is_accepted_as_lifecycle_projection(self):
        lifecycle = load('acceptance_lifecycle', 'tests/usage-lifecycle-projection.py')
        source = producer.ProducerResolutionTests('test_verified_profile_produces_sanitized_bound_context_usable_by_resolver')
        source.setUp()
        self.addCleanup(source.doCleanups)
        source.raw['usage'] = {'input': 1320, 'read': 0, 'write': 0, 'short': 0,
                               'long': 0, 'output': 0, 'reasoning': 0}
        source.write()
        selected_profile = base.profiles.profile(False)
        selected_profile['resolution_fields'] = producer.profile()['resolution_fields']
        normalized = producer.adapter.normalize_selection(source.selection, profile=selected_profile,
            expected_owner_scope=source.scope, project_identifier='PRIVATE_PROJECT',
            provider_identifier='PRIVATE_ACCOUNT', run_id='run',
            key=b'private-mapping-key-that-is-long-enough-for-tests',
            verify_resolution=lambda kind, profile, observation, proof: kind in ('measurement_finality', 'parameter', 'context'))
        data, allowed = source.prepare_resolution(normalized, selected_profile)
        resolved = base.resolve(data, base.Verifier(allowed))
        self.assertEqual(resolved['completeness']['priced'], {'numerator': 1, 'denominator': 1})
        self.assertEqual(resolved['responses'][0]['model_cost']['cost_usd'], '0.00264')
        observation = normalized['bundle']['observations'][0]
        measurement = observation['measurements']['input_uncached']
        self.assertEqual(measurement['value'], 1320)
        proof = next(item for item in normalized['bundle']['evidence_objects']
                     if contract.content_id(item) == measurement['evidence'])
        case = lifecycle.LifecycleProjectionTests('test_valid_exact_projection_and_replay_preserve_first_payload')
        case.setUp()
        self.addCleanup(case.doCleanups)
        projection = copy.deepcopy(case.value)
        contributor = projection['contributors'][0]
        projection['contributors'] = [contributor]
        contributor.update(profile_id=observation['profile_id'], profile_version=observation['profile_version'],
                           observation_ids=[contract.observation_id(observation)],
                           measurements={'input_uncached': measurement}, priced_usd='0.00264')
        # Reuse the exact snapshot and applicability facts used by the resolver.
        snapshot = data['snapshots'][0]
        context = data['contexts'][0]
        projection['price_snapshots'] = [copy.deepcopy(snapshot)]
        projection['scenario'] = copy.deepcopy(data['scenario'])
        snapshot_id = contract.price_snapshot_id(snapshot)
        contributor['price_snapshot_id'] = snapshot_id
        self.assertEqual(projection['scenario']['snapshot_ids'], [snapshot_id])
        self.assertEqual(contract.price_snapshot_id(projection['price_snapshots'][0]), snapshot_id)
        projection['evidence_objects'] = [copy.deepcopy(proof)]
        projection['evidence_objects'].extend(copy.deepcopy(data['price_evidence']))
        projection['evidence_objects'].extend(copy.deepcopy(context['evidence_objects']))
        time_proof = next(item for item in context['evidence_objects'] if item['kind'] == 'execution_time_evidence')
        contributor['execution_time'] = {'value': time_proof['value'], 'evidence': contract.content_id(time_proof)}
        contributor['parameter_evidence'] = {}
        for name, parameter in projection['scenario']['source_parameters'].items():
            parameter_proof = next(item for item in context['evidence_objects']
                                   if item['kind'] == 'source_parameter_evidence' and item['field'] == name)
            digest = contract.content_id(parameter_proof)
            parameter['evidence'] = digest
            contributor['parameter_evidence'][name] = digest
        projection['cost_usd'] = resolved['responses'][0]['model_cost']['cost_usd']
        contract.validate_lifecycle_projection(projection)
        projection = json.loads(contract.canonical_bytes(projection))
        case.write(projection)
        permit = {'schema_version': 1, 'kind': 'lifecycle_authority_permit',
                  'projection_sha256': hashlib.sha256(contract.canonical_bytes(projection)).hexdigest(),
                  'scope': projection['scope'], 'run_id': case.run}
        signature = __import__('subprocess').run(['openssl', 'dgst', '-sha256', '-sign', str(case.private_key)],
            input=b'orchestrail:lifecycle-authority:v1\0' + contract.canonical_bytes(permit),
            capture_output=True, check=True).stdout.hex()
        case.permit_path.write_bytes(contract.canonical_bytes(permit | {'signature': signature}))
        case.env = case.authority_env
        result = case.correlated('--usage-file', str(case.path), '--cost-usd', '0.00264',
                                 '--tokens-in', '1320', '--tokens-out', '0')
        self.assertFalse(json.loads(result.stdout)['duplicate'])
        self.assertTrue(lifecycle.contains(json.loads(case.log.read_text().splitlines()[-1]), projection))
        accepted = case.snapshot()
        case.step('--usage-file', str(case.path), '--cost-usd', '0')
        self.assertEqual(case.snapshot(), accepted)

if __name__ == '__main__': unittest.main()
