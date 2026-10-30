#!/usr/bin/env python3
"""End-to-end checks over explicitly selected offline retrospective evidence."""
import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_contract as contract
import usage_telemetry_corpus as corpus
import usage_telemetry_exports as exports


def load(path, name):
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture = load(ROOT / 'tests/usage-fixed-corpus.py', 'fixed_corpus_fixture')
report = load(ROOT / 'scripts/usage_telemetry_report.py', 'report')


class RetrospectiveIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scope = copy.deepcopy(fixture.SCOPE)
        self.manifest = {
            'schema_version': 1, 'kind': 'analysis_corpus', 'as_of': fixture.AS_OF,
            'scope': self.scope, 'scenario_id': 'scenario',
            'versions': {'bundle_schema_version': 1, 'receipt_schema_version': 1,
                         'price_schema_version': 1, 'normalizer_version': '1'},
            'identifier_mappings': [], 'inputs': [], 'exclusions': [],
            'max_source_bytes': 100000, 'max_total_bytes': 200000, 'max_records': 100,
        }
        self.add('bundle.json', 'usage_bundle', fixture.bundle())

    def add(self, name, kind, value):
        data = contract.canonical_bytes(value)
        path = self.root / name
        path.write_bytes(data)
        self.manifest['inputs'].append({'kind': kind, 'schema_version': 1,
                                        'local_path': str(path),
                                        'sha256': hashlib.sha256(data).hexdigest(),
                                        'size_bytes': len(data)})
        return path

    @staticmethod
    def verify(item, value, scope):
        # This authority is part of the test harness, independent of the bytes.
        return {'scope': copy.deepcopy(scope), 'observed_at': '2026-01-01T00:00:00Z'}

    def analyze(self, manifest=None, verifier=None):
        self.assertIsNotNone(report, 'retrospective analysis implementation is missing')
        return report.analyze_corpus(copy.deepcopy(manifest or self.manifest),
                                     verify_input=verifier or self.verify)

    def test_valid_selected_corpus_produces_equivalent_exports_without_history(self):
        self.add('unselected.json', 'usage_bundle', fixture.bundle(number=3))
        unselected = self.manifest['inputs'].pop()
        with patch('os.listdir', side_effect=AssertionError('implicit discovery')), \
             patch('os.scandir', side_effect=AssertionError('implicit discovery')), \
             patch('socket.socket', side_effect=AssertionError('network access')):
            result = self.analyze()
            artifacts = exports.render_exports(result)
        decoded = json.loads(artifacts['json'])
        self.assertEqual(decoded['as_of'], self.manifest['as_of'])
        self.assertEqual(decoded['scenario_id'], self.manifest['scenario_id'])
        self.assertNotIn(unselected['sha256'], json.dumps(decoded))
        self.assertNotIn(str(self.root), json.dumps(decoded))
        rows = list(csv.DictReader(io.StringIO(artifacts['csv'], newline='')))
        self.assertEqual({row['path']: json.loads(row['value']) for row in rows},
                         dict(exports._rows(decoded)))
        self.assertIn(decoded['corpus_id'], artifacts['markdown'])
        self.assertEqual(artifacts, exports.render_exports(self.analyze()))

    def test_contract_identifiers_flow_from_corpus_to_archive(self):
        import tarfile
        identifier = 'baseline:' + 'x' * 247
        self.manifest['scenario_id'] = identifier
        self.manifest['versions']['normalizer_version'] = identifier
        contract.validate_analysis_corpus(self.manifest)
        artifacts = exports.render_exports(self.analyze())
        self.assertEqual(artifacts, exports.render_exports(self.analyze()))
        for content in artifacts.values():
            self.assertIn(identifier, content)
        archive = exports.archive_exports(artifacts)
        self.assertEqual(archive, exports.archive_exports(artifacts))
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            for key, name in exports._FILES.items():
                self.assertEqual(bundle.extractfile(name).read().decode(), artifacts[key])

    def test_uninventoried_unattributed_record_does_not_create_coverage_or_cost(self):
        result = self.analyze()
        self.assertEqual(result['completeness']['inventory'], 'unknown')
        self.assertEqual(result['completeness']['attribution'], 'unknown')
        self.assertIsNone(result['totals']['total_cost'])
        coverage = result['coverage']
        self.assertIsNone(coverage['measurements']['denominator'])
        self.assertIsNone(coverage['pricing']['denominator'])

    def test_late_observation_does_not_change_an_earlier_selected_report(self):
        before = self.analyze()
        original = copy.deepcopy(self.manifest)
        self.add('late.json', 'usage_bundle', fixture.bundle('2026-01-02T03:04:06Z', number=2))
        after = self.analyze()
        self.assertEqual(before, self.analyze(original))
        self.assertNotEqual(before['corpus_id'], after['corpus_id'])
        self.assertTrue(after['late_data'])

    def test_untrusted_or_tampered_selected_input_never_produces_report(self):
        self.analyze()
        with self.assertRaises(ValueError):
            self.analyze(verifier=lambda *_: None)
        Path(self.manifest['inputs'][0]['local_path']).write_text('tampered', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.analyze()

    def test_selected_lifecycle_record_uses_existing_event_contract(self):
        # This is a complete legacy run-start event, not a synthetic usage event.
        event = {'event': 'run-start', 'ts': '2026-01-01T00:00:00Z',
                 'run_id': 'run', 'seq': 1, 'pipeline': 'spec-run', 'flow': 'main'}
        self.add('start.json', 'lifecycle_event', event)
        frozen = corpus.freeze_corpus(copy.deepcopy(self.manifest), verify_input=self.verify)
        self.assertTrue(any(item['kind'] == 'lifecycle_event' for item in frozen['inputs']))
        result = self.analyze()
        self.assertEqual(result['as_of'], self.manifest['as_of'])

    def test_command_exposes_offline_explicit_analysis(self):
        completed = subprocess.run([sys.executable, str(ROOT / 'scripts/usage-telemetry.py'),
                                    'analyze', '--help'], capture_output=True, text=True,
                                   timeout=5, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for option in ('--corpus-manifest', '--scenario', '--authority'):
            self.assertIn(option, completed.stdout)


if __name__ == '__main__':
    unittest.main()
