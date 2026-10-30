#!/usr/bin/env python3
"""Integration checks for immutable, evidence-bound lifecycle projections."""
import copy
import hashlib
import hmac
import sys
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/log-step.sh'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

fixtures = load('projection_fixtures', 'tests/usage-lifecycle-projection-schema.py')
contract = fixtures.contract

def exact_projection():
    """Evidence binds synthetic quantities and prices, not provider authenticity."""
    value = fixtures.projection()
    quantities = (1000, 320)
    costs = ('0.002', '0.00064')
    for contributor, quantity, cost in zip(value['contributors'], quantities, costs):
        measurement = contributor['measurements']['input_uncached']
        evidence = next(item for item in value['evidence_objects']
                        if contract.content_id(item) == measurement['evidence'])
        evidence['value'] = quantity
        measurement['value'] = quantity
        measurement['evidence'] = contract.content_id(evidence)
        contributor['priced_usd'] = cost
    value['cost_usd'] = '0.00264'
    contract.validate_lifecycle_projection(value)
    return value

def contains(tree, value):
    if tree == value:
        return True
    if isinstance(tree, dict):
        return any(contains(item, value) for item in tree.values())
    if isinstance(tree, list):
        return any(contains(item, value) for item in tree)
    return False

class LifecycleProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = dict(os.environ, ORCHESTRAIL_HOME=str(ROOT),
                        ORCHESTRAIL_LOG_ROOT=str(self.root / 'logs'))
        for name in ('USAGE_TELEMETRY_CONFIG', 'USAGE_TELEMETRY_AUTHORITY_KEY'):
            self.env.pop(name, None)
        self.private_key = self.root / 'test-private.pem'
        self.public_key = self.root / 'test-public.pem'
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048',
                        '-out', str(self.private_key)], check=True, capture_output=True)
        subprocess.run(['openssl', 'pkey', '-in', str(self.private_key), '-pubout', '-out', str(self.public_key)],
                       check=True, capture_output=True)
        bootstrap = self.root / 'bootstrap.py'
        bootstrap.write_text('import os, runpy, sys\n'
            'sys.path.insert(0, os.environ["TEST_SCRIPTS"])\n'
            'import usage_telemetry_ingest as ingest\n'
            'ingest.trusted_authority_key = lambda path: open(os.environ["TEST_PUBLIC_KEY"], "rb").read()\n'
            'script = sys.argv[1]\n'
            'sys.argv = sys.argv[1:]\n'
            'ingest.main() if script.endswith("usage_telemetry_ingest.py") else runpy.run_path(script, run_name="__main__")\n')
        bindir = self.root / 'authority-bin'
        bindir.mkdir()
        wrapper = bindir / 'python3'
        wrapper.write_text('#!/bin/sh\nexec ' + sys.executable + ' ' + str(bootstrap) + ' "$@"\n')
        wrapper.chmod(0o755)
        normalizer = load('normalization_fixtures', 'tests/usage-normalize-cli.py')
        registration = normalizer.NormalizeCliTests('test_normalize_emits_self_contained_sanitized_bundle')
        registration.setUp()
        self.addCleanup(registration.doCleanups)
        self.registration = registration
        self.authority_env = dict(self.env, PATH=str(bindir) + os.pathsep + self.env['PATH'],
                                  TEST_SCRIPTS=str(ROOT / 'scripts'), TEST_PUBLIC_KEY=str(self.public_key),
                                  USAGE_TELEMETRY_CONFIG=str(registration.config_path),
                                  USAGE_TELEMETRY_AUTHORITY_KEY='/etc/orchestrail/usage-authorities/test.pem')
        start = self.invoke('run-start', '--pipeline', 'spec-run', '--project', str(self.root), env=self.authority_env)
        self.run = start.stdout.strip()
        self.assertRegex(self.run, r'^[0-9a-f]{8}$')
        self.log = next((self.root / 'logs/runs').glob('*.jsonl'))
        self.active = self.root / 'logs/.active' / self.run
        self.path = self.root / 'projection.json'
        import usage_telemetry_adapter as adapter
        self.registration.config['project_identifier'] = str(self.root)
        self.registration.config['run_id'] = self.run
        owner_id = adapter._opaque(bytes.fromhex(self.registration.config['key_hex']), 'run', self.run)
        self.registration.config['owner_scope'] = {'owner_kind': 'run', 'owner_id': owner_id}
        self.registration.write_config()
        projection = exact_projection()
        projection['scope']['owner_id'] = owner_id
        self.value = json.loads(contract.canonical_bytes(projection))
        self.write(self.value)
        permit = {'schema_version': 1, 'kind': 'lifecycle_authority_permit',
                  'projection_sha256': hashlib.sha256(contract.canonical_bytes(self.value)).hexdigest(),
                  'scope': self.value['scope'], 'run_id': self.run}
        message = b'orchestrail:lifecycle-authority:v1\0' + contract.canonical_bytes(permit)
        signature = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(self.private_key)],
                                   input=message, capture_output=True, check=True).stdout.hex()
        self.permit_path = self.root / 'permit.json'
        self.permit_path.write_bytes(contract.canonical_bytes(permit | {'signature': signature}))
        self.permit_path.chmod(0o600)
        self.authority_env['USAGE_TELEMETRY_LIFECYCLE_PERMIT'] = str(self.permit_path)

    def invoke(self, *args, env=None):
        result = subprocess.run(['/bin/bash', str(SCRIPT), *args], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=env or self.env, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def write(self, value):
        self.path.write_bytes(contract.canonical_bytes(value))

    def snapshot(self):
        return self.log.read_bytes(), self.active.read_bytes()

    def step(self, *extra):
        return self.invoke('step', '--run', self.run, '--step', 'subtask', '--outcome', 'ok', *extra)

    def correlated(self, *extra):
        return self.step('--session-id', 'session-a', '--agent-id', 'worker-a',
                         '--checkpoint-id', 'checkpoint-a', '--span-start-ms', '1000',
                         '--span-end-ms', '2000', '--timing-source', 'hook',
                         '--boundary', 'session', *extra)

    def test_published_observations_match_first_projection_and_replay(self):
        bundle_fixtures = load('bundle_fixtures', 'tests/usage-observation-bundle-schema.py')
        bundle = bundle_fixtures.bundle()
        bundle['run_id'] = self.run
        bundle['observations'] = []
        bundle['evidence_objects'] = []
        projection = copy.deepcopy(self.value)
        references = {}
        for item in projection['evidence_objects']:
            old_id = contract.content_id(item)
            if item.get('profile_id') == 'profile':
                item['profile_id'] = 'synthetic-profile'
                references[old_id] = contract.content_id(item)
        def remap(value):
            if isinstance(value, dict):
                return {key: remap(item) for key, item in value.items()}
            if isinstance(value, list):
                return [remap(item) for item in value]
            if value == 'profile':
                return 'synthetic-profile'
            return references.get(value, value) if isinstance(value, str) else value
        projection = remap(projection)
        bundle['profile_id'] = 'synthetic-profile'
        for index, contributor in enumerate(projection['contributors'], 1):
            measurement = contributor['measurements']['input_uncached']
            evidence = next(item for item in projection['evidence_objects']
                            if contract.content_id(item) == measurement['evidence'])
            observation = bundle_fixtures.observation()
            observation['record_number'] = index
            observation['profile_id'] = bundle['profile_id']
            observation['measurements'] = {'input_uncached': copy.deepcopy(measurement)}
            bundle['observations'].append(observation)
            bundle['evidence_objects'].append(copy.deepcopy(evidence))
            contributor['observation_ids'] = [contract.observation_id(observation)]
        contract.validate_usage_bundle(bundle)
        contract.validate_lifecycle_projection(projection)
        scope = projection['scope']
        bundle_path = self.root / 'bundle.json'
        bundle_path.write_bytes(contract.canonical_bytes(bundle))
        digest = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
        proof = {'schema_version': 1, 'kind': 'usage_provenance', 'bundle_sha256': digest,
                 'profile_id': bundle['profile_id'], 'profile_version': bundle['profile_version'],
                 'scope': self.registration.config['owner_scope']}
        proof['mac'] = hmac.new(bytes.fromhex(self.registration.config['key_hex']),
                                b'orchestrail:usage-provenance:v1\0' + contract.canonical_bytes(proof),
                                hashlib.sha256).hexdigest()
        proof_path = self.root / 'proof.json'
        proof_path.write_bytes(contract.canonical_bytes(proof))
        proof_path.chmod(0o600)
        permit = {'schema_version': 1, 'kind': 'usage_authority_permit', 'bundle_sha256': digest,
                  'profile_id': bundle['profile_id'], 'profile_version': bundle['profile_version'],
                  'run_id': self.run, 'scope': self.registration.config['owner_scope']}
        signature = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(self.private_key)],
                                   input=b'orchestrail:usage-authority:v1\0' + contract.canonical_bytes(permit),
                                   capture_output=True, check=True).stdout.hex()
        usage_permit = self.root / 'usage-permit.json'
        usage_permit.write_bytes(contract.canonical_bytes(permit | {'signature': signature}))
        usage_permit.chmod(0o600)
        self.authority_env.update(ORCHESTRAIL_USAGE_MODE='on', USAGE_TELEMETRY_PROVENANCE=str(proof_path),
                                  USAGE_TELEMETRY_AUTHORITY_PERMIT=str(usage_permit))
        before = self.snapshot()
        import usage_telemetry_ingest as ingest
        def publish():
            with patch.dict(os.environ, self.authority_env, clear=True), \
                    patch.object(ingest, 'trusted_authority_key', return_value=self.public_key.read_bytes()):
                return ingest.ingest(str(bundle_path), str(self.root / 'logs'))
        receipt = publish()
        self.assertFalse(receipt['duplicate'])
        self.assertEqual((self.root / 'logs/usage/v1' / (digest + '.json')).read_bytes(), bundle_path.read_bytes())
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(set(receipt['observation_ids']),
                         {item['observation_ids'][0] for item in projection['contributors']})
        duplicate = publish()
        self.assertTrue(duplicate['duplicate'])
        self.assertEqual(self.snapshot(), before)
        for observation, contributor in zip(bundle['observations'], projection['contributors']):
            self.assertEqual(observation['measurements']['input_uncached'],
                             contributor['measurements']['input_uncached'])
        self.write(projection)
        permit = {'schema_version': 1, 'kind': 'lifecycle_authority_permit',
                  'projection_sha256': hashlib.sha256(contract.canonical_bytes(projection)).hexdigest(),
                  'scope': scope, 'run_id': self.run}
        signature = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(self.private_key)],
                                   input=b'orchestrail:lifecycle-authority:v1\0' + contract.canonical_bytes(permit),
                                   capture_output=True, check=True).stdout.hex()
        self.permit_path.write_bytes(contract.canonical_bytes(permit | {'signature': signature}))
        self.env = self.authority_env
        args = ('--usage-file', str(self.path), '--cost-usd', '0.00264',
                '--tokens-in', '1320', '--tokens-out', '0')
        first = self.correlated(*args)
        self.assertFalse(json.loads(first.stdout)['duplicate'])
        self.assertTrue(contains(json.loads(self.log.read_text().splitlines()[-1]), projection))
        accepted = self.snapshot()
        replay = self.correlated(*args)
        self.assertTrue(json.loads(replay.stdout)['duplicate'])
        self.assertEqual(self.snapshot(), accepted)

    def test_valid_exact_projection_and_replay_preserve_first_payload(self):
        args = ('--usage-file', str(self.path), '--cost-usd', '0.00264',
                '--tokens-in', '1320', '--tokens-out', '0')
        self.env = self.authority_env
        first = self.correlated(*args)
        records = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(len(records), 2, first.stderr)
        self.assertEqual(records[-1]['event'], 'step')
        self.assertTrue(contains(records[-1], self.value), records[-1])
        before = self.snapshot()
        replay = self.correlated(*args)
        self.assertEqual(self.snapshot(), before, replay.stderr)
        self.assertEqual(json.loads(first.stdout)['duplicate'], False)
        self.assertEqual(json.loads(replay.stdout)['duplicate'], True)

        changed = copy.deepcopy(self.value)
        changed['cost_usd'] = '0'
        self.write(changed)
        self.correlated(*args)
        self.assertEqual(self.snapshot(), before)

    def test_signed_foreign_owner_and_unbound_session_cannot_mutate_checkpoint(self):
        self.env = self.authority_env
        for kind, identifier in (('run', 'sha256:' + 'f' * 64), ('session', 'sha256:' + 'e' * 64)):
            with self.subTest(kind=kind):
                forged = copy.deepcopy(self.value)
                forged['scope'].update(owner_kind=kind, owner_id=identifier)
                self.write(forged)
                permit = {'schema_version': 1, 'kind': 'lifecycle_authority_permit',
                          'projection_sha256': hashlib.sha256(contract.canonical_bytes(forged)).hexdigest(),
                          'scope': forged['scope'], 'run_id': self.run}
                message = b'orchestrail:lifecycle-authority:v1\0' + contract.canonical_bytes(permit)
                signature = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(self.private_key)],
                                           input=message, capture_output=True, check=True).stdout.hex()
                self.permit_path.write_bytes(contract.canonical_bytes(permit | {'signature': signature}))
                before = self.snapshot()
                self.step('--session-id', 'session-a', '--agent-id', 'worker-a',
                          '--checkpoint-id', 'checkpoint-' + kind, '--span-start-ms', '1000',
                          '--span-end-ms', '2000', '--timing-source', 'hook', '--boundary', 'session',
                          '--usage-file', str(self.path), '--cost-usd', '0.00264')
                self.assertEqual(self.snapshot(), before)

    def test_registered_project_and_key_must_still_match_current_run(self):
        self.env = self.authority_env
        self.registration.config['project_identifier'] = 'another-project'
        self.registration.write_config()
        before = self.snapshot()
        self.correlated('--usage-file', str(self.path), '--cost-usd', '0.00264')
        self.assertEqual(self.snapshot(), before)

    def test_untrusted_complete_projection_cannot_mutate_state(self):
        before = self.snapshot()
        self.correlated('--usage-file', str(self.path), '--cost-usd', '0.00264')
        self.assertEqual(self.snapshot(), before)
        self.env = self.authority_env
        self.permit_path.write_bytes(contract.canonical_bytes({'signature': 'forged'}))
        self.correlated('--usage-file', str(self.path), '--cost-usd', '0.00264')
        self.assertEqual(self.snapshot(), before)

    def test_invalid_projection_or_scalar_never_mutates_any_state(self):
        self.env = self.authority_env
        variants = [
            (self.value, ('--cost-usd', '0')),
            (self.value, ('--cost-usd', '0.00264', '--cost-usd', '0.00264')),
            (self.value, ('--cost-usd', '0.002640')),
            (self.value, ('--tokens-in', '-1')),
            (self.value, ('--tokens-out', 'true')),
            (self.value | {'cost_usd': '0'}, ('--cost-usd', '0')),
        ]
        wrong_evidence = copy.deepcopy(self.value)
        next(item for item in wrong_evidence['evidence_objects']
             if item['kind'] == 'measurement_evidence')['value'] += 1
        variants.append((wrong_evidence, ('--cost-usd', '0.00264')))
        partial = copy.deepcopy(self.value)
        partial['completeness']['pricing'] = 'partial'
        variants.append((partial, ('--cost-usd', '0.00264')))
        for projection, args in variants:
            with self.subTest(args=args, cost=projection['cost_usd']):
                self.write(projection)
                before = self.snapshot()
                self.step('--usage-file', str(self.path), *args)
                self.assertEqual(self.snapshot(), before)
        before = self.snapshot()
        self.step('--cost-usd', '0.00264')
        self.assertEqual(self.snapshot(), before)
        self.path.write_text('{"schema_version":1,"schema_version":1}')
        self.step('--usage-file', str(self.path))
        self.assertEqual(self.snapshot(), before)

    def test_caller_counters_are_recorded_without_verified_cost(self):
        self.step('--tokens-in', '20', '--tokens-out', '4')
        rows = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]['tokens_in'], 20)
        self.assertEqual(rows[-1]['tokens_out'], 4)
        self.assertNotIn('cost_usd', rows[-1])

    def test_unavailable_dependency_preserves_legacy_logging(self):
        helper = load('contract_export', 'tests/usage-contract-export.py')
        path = self.root / 'bin'
        path.mkdir()
        env = dict(self.env, PATH=helper.isolated_path(path, python=False))
        before = self.snapshot()
        self.invoke('step', '--run', self.run, '--step', 'subtask', '--outcome', 'ok',
                    '--usage-file', str(self.path), '--cost-usd', '0.00264', env=env)
        self.assertEqual(self.snapshot(), before)
        self.invoke('step', '--run', self.run, '--step', 'subtask', '--outcome', 'ok', env=env)
        rows = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual([row['event'] for row in rows], ['run-start', 'step'])

if __name__ == '__main__':
    unittest.main()
