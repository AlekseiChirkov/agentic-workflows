#!/usr/bin/env bash
# Verify workflow logging instructions with isolated public adapter/producer fixtures.
# Usage: bash tests/hook-workflow-contract.sh [test-name ...]. Exit 1 on a contract failure.
# Synthetic fixtures exercise the documented controller decisions, not model compliance.
set -uo pipefail
workflow_test_source="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
python3 - "$workflow_test_source" "$@" <<'PY'
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import TypeAlias, cast
import unittest
import uuid

Record: TypeAlias = dict[str, object]
SOURCE = Path(sys.argv[1])


def compact(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def record(value: str) -> Record:
    return cast(Record, json.loads(value))


class WorkflowLogging(unittest.TestCase):
    root: Path
    checkout: Path
    project: Path
    state: Path
    logs: Path
    helper: Path
    adapter: Path
    env: dict[str, str]
    direct_calls: int
    fallback_calls: int

    def setUp(self) -> None:
        scratch = tempfile.TemporaryDirectory(prefix='workflow logging ')
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.checkout = self.root / 'source checkout'
        for folder in ('scripts', 'hooks', 'rules', 'workflows'):
            shutil.copytree(SOURCE / folder, self.checkout / folder)
        self.project = self.root / 'registered project'
        self.project.mkdir()
        self.state, self.logs = self.root / 'state', self.root / 'logs'
        config = self.root / 'config'
        (config / 'orchestrail').mkdir(parents=True)
        (config / 'orchestrail/projects').write_text(str(self.project) + '\n')
        self.env = dict(os.environ, HOME=str(self.root / 'home'), XDG_CONFIG_HOME=str(config),
                        XDG_STATE_HOME=str(self.state), ORCHESTRAIL_HOME=str(self.checkout),
                        ORCHESTRAIL_LOG_ROOT=str(self.logs), CLAUDE_CODE_SESSION_ID='native-session')
        self.helper = self.checkout / 'scripts/log-step.sh'
        self.adapter = self.checkout / 'hooks/log-step-hook.sh'
        self.direct_calls, self.fallback_calls = 0, 0

    def command(self, script: Path, args: list[str]) -> str:
        if script == self.helper and args[0] == 'step':
            self.direct_calls += 1
        if script == self.adapter and args[0] == 'fallback':
            self.fallback_calls += 1
        result = subprocess.run(['bash', str(script), *args], cwd=self.project, env=self.env,
                                text=True, capture_output=True, timeout=12)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(len(result.stderr.encode()), 4096)
        return result.stdout.strip()

    def start(self) -> str:
        run = self.command(self.helper, ['run-start', '--pipeline', 'spec-run'])
        self.assertRegex(run, r'^[0-9a-f]{8}$')
        return run

    def dispatch(self, run: str, boundary: str = 'subagent') -> tuple[Record, str]:
        actor = 'native-session' if boundary == 'session' else 'logical-worker'
        line = self.command(self.adapter, ['dispatch', '--run', run, '--agent-id', actor,
                            '--boundary', boundary, '--expected-skill', 'pae-tests'])
        self.assertTrue(line.startswith('ORCHESTRAIL_DISPATCH_V1 '))
        return record(line.split(' ', 1)[1]), line

    def status(self, identity: Record) -> Record | None:
        output = self.command(self.adapter, ['status', '--checkpoint', str(identity['checkpoint_id'])])
        return record(output) if output else None

    def steps(self, run: str) -> list[Record]:
        path = self.command(self.helper, ['path', '--run', run])
        return [row for row in map(record, Path(path).read_text().splitlines()) if row['event'] == 'step']

    def payload(self, envelope: tuple[Record, str], skills: tuple[str, ...]) -> Record:
        identity, line = envelope
        transcript = self.root / (uuid.uuid4().hex + '.jsonl')
        entries: list[Record] = [{'type': 'user', 'message': {'role': 'user', 'content': line}}]
        for skill in skills:
            entries.append({'type': 'assistant', 'message': {'role': 'assistant', 'content': [
                {'type': 'tool_use', 'id': 'tool-' + uuid.uuid4().hex, 'name': 'Skill',
                 'input': {'skill': skill}}]}})
        transcript.write_text(''.join(compact(entry) + '\n' for entry in entries))
        session = identity['agent_id'] == identity['session_id']
        return {'hook_event_name': 'Stop' if session else 'SubagentStop',
                'session_id': identity['session_id'], 'agent_id': 'native-worker',
                'cwd': str(self.project), 'transcript_path': str(transcript),
                'agent_transcript_path': str(transcript), 'last_assistant_message':
                'ORCHESTRAIL_REPORT_V1 ' + compact(dict(identity, outcome='ok', tests='red'))}

    def native(self, payload: Record) -> None:
        result = subprocess.run(['bash', str(self.adapter)], input=compact(payload),
                                cwd=self.project, env=self.env, text=True,
                                capture_output=True, timeout=12)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(len(result.stderr.encode()), 4096)

    def fallback(self, identity: Record) -> None:
        self.command(self.adapter, ['fallback', '--checkpoint', str(identity['checkpoint_id']),
                                   '--step', 'pae-tests', '--outcome', 'ok', '--tests', 'red'])

    def valid_receipt(self, receipt: object, retained: Record) -> bool:
        if not isinstance(receipt, dict) or receipt.get('kind') != 'accepted':
            return False
        sequence = receipt.get('seq')
        exported = self.command(self.helper, ['contract'])
        maximum = int(dict(line.split('=', 1) for line in exported.splitlines())['count.maximum'])
        return type(sequence) is int and 0 < sequence <= maximum and all(
            receipt.get(key) == value for key, value in retained.items() if key != 'schema_version')

    def resolve(self, retained: Record, observed: Record | None) -> str:
        # Test-only controller: an issued envelope can only use its retained checkpoint.
        if observed is None or any(observed.get(key) != value for key, value in retained.items()):
            self.fallback(retained)
            return 'uncertain'
        state = observed.get('state')
        if state == 'accepted':
            receipt = observed.get('receipt')
            if self.valid_receipt(receipt, retained):
                return 'suppress'
            self.fallback(retained)
            return 'uncertain'
        if state == 'pending':
            self.fallback(retained)
            return 'fallback'
        return 'native-only' if state == 'delivering' else 'no-second-attempt'

    def ordinary(self, run: str, step: str) -> None:
        self.command(self.helper, ['step', '--run', run, '--step', step,
                                  '--outcome', 'ok', '--note', 'approximate'])

    def policy(self, patterns: tuple[str, ...]) -> None:
        text = (SOURCE / 'rules/run-log.md').read_text()
        for pattern in patterns:
            with self.subTest(contract=pattern):
                self.assertTrue(re.search(pattern, text), 'missing canonical workflow routing integration: ' + pattern)

    def assert_approximate(self, run: str) -> None:
        rows = self.steps(run)
        self.assertTrue(rows)
        self.assertTrue(all(row.get('note') == 'approximate' for row in rows))
        self.assertTrue(all('timing_source' not in row for row in rows))

    def unavailable_fixtures(self) -> None:
        run = self.start()
        # No envelope ever issued permits ordinary prompt logging; unknown resume does not.
        for step in ('pd-analyze', 'pae-tests', 'pae-implement', 'pav-check', 'subtask'):
            self.ordinary(run, step)
        self.assert_approximate(run)
        before = self.steps(run)
        unknown_resume: Record | None = None
        if unknown_resume is not None:
            self.fallback(unknown_resume)
        self.assertEqual(self.steps(run), before)
        self.command(self.helper, ['run-end', '--run', run, '--outcome', 'completed'])
        self.env.pop('CLAUDE_CODE_SESSION_ID')
        unavailable = self.command(self.adapter, ['dispatch', '--run', self.start(),
                                   '--agent-id', 'logical-worker', '--boundary', 'subagent'])
        self.assertEqual(unavailable, '', 'missing native session cannot issue an envelope')

    def test_unavailable_hooks_keep_every_prompt_step_approximate(self) -> None:
        self.unavailable_fixtures()
        for name in ('spec-run', 'phase-pipeline', 'phase-discovery', 'phase-execution', 'phase-validation'):
            text = (SOURCE / 'workflows' / (name + '.md')).read_text()
            with self.subTest(workflow=name):
                self.assertTrue(re.search(r'--note[ \t]+["\']?approximate', text), 'ordinary prompt paths lack approximate note')
                self.assertIn('run-start', text)
                self.assertIn('run-end', text)
                self.assertIn('run-log → ## Workflow coverage and routing', text)
        self.policy((r'(?m)^## Workflow coverage and routing$', r'(?i)no envelope[^\n]*ever',
                     r'(?i)unknown[^\n]*resume|resume[^\n]*unknown',
                     r'(?i)run-start[^\n]*run-end[^\n]*prompt'))

    def ambiguous_fixtures(self) -> None:
        for skills in (('pae-implement', 'pae-finalize'), ('pav-check', 'pav-propose', 'pav-close'),
                       ('pae-tests', 'pae-tests'), ('phase-atomic-execution',)):
            run = self.start()
            envelope = self.dispatch(run)
            self.native(self.payload(envelope, skills))
            self.assertEqual(cast(Record, self.status(envelope[0]))['state'], 'pending')
            self.assertEqual(self.steps(run), [])
            self.resolve(envelope[0], self.status(envelope[0]))
            for skill in skills:
                self.ordinary(run, skill)
            self.assert_approximate(run)
        run = self.start()
        envelope = self.dispatch(run, 'session')
        self.native(self.payload(envelope, ()))
        self.assertEqual(self.steps(run)[0]['step'], 'unknown')
        run = self.start()
        envelope = self.dispatch(run)
        self.assertEqual(self.steps(run), [], 'test-level none has no RED report or row')
        self.assertEqual(cast(Record, self.status(envelope[0]))['state'], 'pending')

    def test_batches_and_absent_red_do_not_claim_named_coverage(self) -> None:
        self.ambiguous_fixtures()
        text = (SOURCE / 'workflows/spec-run.md').read_text()
        for pattern in (r'(?is)none.{0,220}no RED (?:report|marker|row)',
                        r'(?is)GREEN.{0,180}(?:never|not|must not).{0,80}(?:reuse|re-use).{0,60}RED',
                        r'(?is)(?:synthetic|aggregate).{0,140}(?:distinct|separate)|distinct.{0,140}subtask'):
            with self.subTest(integration=pattern):
                self.assertTrue(re.search(pattern, text), 'missing batch/RED integration constraint: ' + pattern)
        self.policy((r'(?is)session.{0,30}unknown.{0,100}(?:never|not).{0,50}named',
                     r'(?is)exactly one.{0,90}(?:native )?Skill',
                     r'(?is)expected.skill.{0,100}(?:evidence|assertion)',
                     r'(?is)(?:arbitration|Arbiter).{0,120}approximate'))

    def accepted_and_pending(self) -> None:
        run = self.start()
        envelope = self.dispatch(run)
        self.native(self.payload(envelope, ('pae-tests',)))
        self.assertEqual(self.resolve(envelope[0], self.status(envelope[0])), 'suppress')
        self.assertEqual((self.direct_calls, self.fallback_calls), (0, 0))
        self.assertEqual(len(self.steps(run)), 1)
        self.assertEqual(self.steps(run)[0]['timing_source'], 'hook')
        self.ordinary(run, 'subtask')
        self.assertEqual(len(self.steps(run)), 2, 'synthetic summary is distinct from named RED row')
        for observed in (None, {'state': 'accepted', 'checkpoint_id': 'wrong'}):
            self.resolve(envelope[0], observed)
            self.assertEqual(len(self.steps(run)), 2, 'untrusted status cannot duplicate an accepted row')
        for wrong in (None, {'state': 'accepted', 'checkpoint_id': 'wrong'}):
            run = self.start()
            identity, _ = self.dispatch(run)
            self.resolve(identity, wrong)
            self.resolve(identity, self.status(identity))
            self.assertEqual(len(self.steps(run)), 1)
            self.assert_approximate(run)
        run = self.start()
        identity, _ = self.dispatch(run)
        self.assertEqual(self.resolve(identity, self.status(identity)), 'fallback')
        self.resolve(identity, self.status(identity))
        self.assertEqual(len(self.steps(run)), 1, 'pending serialized fallback is attempted once')

    def missing_private_and_owned_fallback(self) -> None:
        for state in ('fallback', 'fallback-attempted', 'missing'):
            run = self.start()
            identity, _ = self.dispatch(run)
            path = next(self.state.rglob(str(identity['checkpoint_id']) + '.json'))
            if state == 'missing':
                path.unlink()
            else:
                value = record(path.read_text())
                value['state'] = state
                path.write_text(compact(value))
            self.resolve(identity, self.status(identity))
            self.assertEqual(self.steps(run), [], 'owned or missing private route cannot write again')

    def lost_receipt(self) -> None:
        run = self.start()
        envelope = self.dispatch(run)
        payload = self.payload(envelope, ('pae-tests',))
        real = self.helper.with_name('real-log-step.sh')
        self.helper.rename(real)
        self.helper.write_text('#!/bin/bash\nif [ "$1" = step ]; then\n'
                               '  bash "$(dirname "$0")/real-log-step.sh" "$@" > /dev/null\n'
                               'else\n  bash "$(dirname "$0")/real-log-step.sh" "$@"\nfi\n')
        self.native(payload)
        status = self.status(envelope[0])
        self.assertEqual(cast(Record, status)['state'], 'delivering')
        counts = (self.direct_calls, self.fallback_calls)
        self.assertEqual(self.resolve(envelope[0], status), 'native-only')
        self.assertEqual((self.direct_calls, self.fallback_calls), counts)
        self.fallback(envelope[0])
        self.assertEqual(len(self.steps(run)), 1)
        self.helper.write_bytes(real.read_bytes())
        self.native(payload)  # Retry the original native payload; never synthesize a retry event.
        self.assertEqual(self.resolve(envelope[0], self.status(envelope[0])), 'suppress')
        self.assertEqual(len(self.steps(run)), 1, 'lost receipt retry must deduplicate persistence')

    def failed_fallback(self) -> None:
        run = self.start()
        identity, _ = self.dispatch(run)
        real = self.helper.read_bytes()
        self.helper.write_text('#!/bin/bash\nexit 0\n')
        self.resolve(identity, self.status(identity))
        self.assertEqual(cast(Record, self.status(identity))['state'], 'fallback-attempted')
        self.helper.write_bytes(real)
        counts = (self.direct_calls, self.fallback_calls)
        self.resolve(identity, self.status(identity))
        self.assertEqual((self.direct_calls, self.fallback_calls), counts)
        self.assertEqual(self.steps(run), [], 'failed ordinary persistence cannot take a second route')

    def malformed_receipt_status(self) -> None:
        exported = self.command(self.helper, ['contract'])
        maximum = int(dict(line.split('=', 1) for line in exported.splitlines())['count.maximum'])
        for sequence in (None, 0, True, -1, 1.5, '1', maximum + 1):
            with self.subTest(malformed_receipt_sequence=sequence):
                run = self.start()
                identity, _ = self.dispatch(run)
                receipt = {key: value for key, value in identity.items() if key != 'schema_version'}
                receipt['kind'] = 'accepted'
                if sequence is not None:
                    receipt['seq'] = sequence
                observed = dict(identity, state='accepted', receipt=receipt)
                self.assertEqual(self.resolve(identity, observed), 'uncertain')
                self.assertEqual(len(self.steps(run)), 1)
                self.assert_approximate(run)
                self.assertEqual(cast(Record, self.status(identity))['state'], 'fallback-attempted')
        with self.subTest(malformed_receipt_sequence='accepted-private-zero'):
            run = self.start()
            envelope = self.dispatch(run)
            self.native(self.payload(envelope, ('pae-tests',)))
            observed = cast(Record, self.status(envelope[0]))
            cast(Record, observed['receipt'])['seq'] = 0
            self.assertEqual(self.resolve(envelope[0], observed), 'uncertain')
            self.assertEqual(len(self.steps(run)), 1, 'malformed observation cannot duplicate accepted data')
            self.assertEqual(self.steps(run)[0]['timing_source'], 'hook')

    def test_dispatch_report_status_preserve_one_delivery_route(self) -> None:
        self.accepted_and_pending()
        self.malformed_receipt_status()
        self.missing_private_and_owned_fallback()
        self.lost_receipt()
        self.failed_fallback()
        text = (SOURCE / 'workflows/spec-run.md').read_text()
        for pattern in (r'dispatch[^\n]*--run', r'--expected-skill[ \t]+pae-tests',
                        r'ORCHESTRAIL_DISPATCH_V1', r'ORCHESTRAIL_REPORT_V1',
                        r'(?is)capability.{0,120}installation.{0,100}session',
                        r'"outcome":"ok"[^\n]*"tests":"red"',
                        r'(?is)original.{0,100}unchanged.{0,100}(?:native|user)',
                        r'(?is)(?:status|serialized fallback).{0,160}before.{0,80}(?:git|commit)'):
            with self.subTest(integration=pattern):
                self.assertTrue(re.search(pattern, text), 'missing existing RED checkpoint wiring: ' + pattern)
        self.policy((r'status --checkpoint', r'fallback --checkpoint',
                     r'(?is)accepted.{0,160}(?:matching|match).{0,80}receipt',
                     r'(?is)pending.{0,130}serialized fallback',
                     r'(?is)delivering.{0,150}frozen',
                     r'(?is)fallback-attempted.{0,130}(?:no second|never|omit)',
                     r'(?is)(?:missing|malformed|wrong).{0,120}status.{0,160}retained',
                     r'(?is)(?:missing|unavailable).{0,70}private.{0,100}(?:omit|uncertain)',
                     r'(?is)(?:never|not).{0,80}fabricat.{0,80}native'))


suite = unittest.TestSuite(WorkflowLogging(name) for name in sys.argv[2:]) if len(sys.argv) > 2 else unittest.defaultTestLoader.loadTestsFromTestCase(WorkflowLogging)
raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
PY
