#!/usr/bin/env bash
# Exercise hook dispatch, native evidence, delivery ownership and retry in isolation.
# Usage: bash tests/log-step-hook.sh [test-name ...]. Never reads real logs/settings.
set -uo pipefail
hook_test_source="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
python3 - "$hook_test_source" "$@" <<'PY'
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import uuid

SOURCE = Path(sys.argv[1])
SELECTED = sys.argv[2:]

def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

class HookContract(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix='hook acceptance ')
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.checkout = self.root / 'checkout with spaces'
        self.project = self.root / 'registered project'
        self.project.mkdir()
        for folder in ('scripts', 'rules', 'workflows', 'hooks'):
            (self.checkout / folder).mkdir(parents=True)
        for folder, names in [('scripts', ['log-step.sh']), ('rules', ['run-log.md'])]:
            for name in names:
                shutil.copy2(SOURCE / folder / name, self.checkout / folder / name)
        for path in (SOURCE / 'workflows').glob('*.md'):
            shutil.copy2(path, self.checkout / 'workflows' / path.name)
        if (SOURCE / 'hooks').is_dir():
            shutil.copytree(SOURCE / 'hooks', self.checkout / 'hooks', dirs_exist_ok=True)
        self.home = self.root / 'home'
        self.config = self.root / 'config'
        self.state = self.root / 'state'
        self.logs = self.root / 'logs'
        (self.config / 'orchestrail').mkdir(parents=True)
        (self.config / 'orchestrail' / 'projects').write_text(str(self.project.resolve()) + '\n')
        self.env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.config),
                        XDG_STATE_HOME=str(self.state), ORCHESTRAIL_HOME=str(self.checkout),
                        ORCHESTRAIL_LOG_ROOT=str(self.logs), CLAUDE_CODE_SESSION_ID='session-' + uuid.uuid4().hex)
        self.env.pop('AGENTIC_LOG_ROOT', None)
        self.adapter = self.checkout / 'hooks' / 'log-step-hook.sh'
        self.helper = self.checkout / 'scripts' / 'log-step.sh'

    def producer(self, *args):
        result = subprocess.run(['bash', str(self.helper), *args], env=self.env,
                                cwd=self.project, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def call(self, *args, payload=None, env=None):
        # A not-yet-defined adapter is an absent capability, represented by no
        # marker; assertions below fail on missing behavior, never command 127.
        command = ['bash', str(self.adapter), *args] if self.adapter.exists() else ['bash', '-c', ':']
        result = subprocess.run(command, input=payload, env=env or self.env, cwd=self.project,
                                text=True, capture_output=True, timeout=12)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(len(result.stderr.encode()), 4096, 'diagnostic leaked input or was unbounded')
        return result

    def start(self):
        run = self.producer('run-start', '--pipeline', 'phase-execution')
        self.assertRegex(run, r'^[a-f0-9]{8}$')
        return run

    def dispatch(self, run=None, boundary='subagent', skill='pae-tests', actor=None, extra=()):
        run = run or self.start()
        actor = actor or (self.env['CLAUDE_CODE_SESSION_ID'] if boundary == 'session' else 'actor-' + uuid.uuid4().hex)
        args = ['dispatch', '--run', run, '--agent-id', actor, '--boundary', boundary]
        if skill is not None:
            args += ['--expected-skill', skill]
        result = self.call(*args, *extra)
        self.assertTrue(result.stdout.startswith('ORCHESTRAIL_DISPATCH_V1 '),
                        'dispatch must emit the explicit canonical correlation marker')
        self.assertEqual(len(result.stdout.splitlines()), 1)
        text = result.stdout.strip()
        identity = json.loads(text.split(' ', 1)[1])
        self.assertEqual(set(identity), {'schema_version','run_id','session_id','agent_id','checkpoint_id'})
        self.assertEqual(text, 'ORCHESTRAIL_DISPATCH_V1 ' + compact(identity))
        self.assertEqual(identity['run_id'], run)
        self.assertEqual(identity['agent_id'], actor)
        self.assertEqual(identity['session_id'], self.env['CLAUDE_CODE_SESSION_ID'])
        self.assertEqual(identity['schema_version'], 1)
        return identity, text

    def status(self, identity):
        result = self.call('status', '--checkpoint', identity['checkpoint_id'])
        self.assertTrue(result.stdout.strip(), 'status must disclose private checkpoint ownership')
        return json.loads(result.stdout)

    def events(self, run):
        path = self.producer('path', '--run', run)
        return [json.loads(line) for line in Path(path).read_text().splitlines()]

    def snapshot(self):
        return {str(p.relative_to(self.logs)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.logs.rglob('*') if p.is_file()}

    def report(self, identity, **fields):
        return 'ORCHESTRAIL_REPORT_V1 ' + compact(dict(identity, outcome='ok', **fields))

    def transcript(self, dispatch, skills=('pae-tests',), input_record=True):
        path = self.root / ('transcript-' + uuid.uuid4().hex + '.jsonl')
        records = [{'type': 'user' if input_record else 'assistant',
                    'message': {'role': 'user' if input_record else 'assistant', 'content': dispatch}}]
        for skill in skills:
            records.append({'type':'assistant', 'message':{'role':'assistant','content':[
                {'type':'tool_use','id':'toolu_' + uuid.uuid4().hex,'name':'Skill','input':{'skill':skill}}]}})
        path.write_text(''.join(compact(r) + '\n' for r in records))
        return path

    def payload(self, identity, dispatch, boundary='subagent', skills=('pae-tests',), report=None):
        transcript = self.transcript(dispatch, skills)
        data = {'hook_event_name':'SubagentStop' if boundary == 'subagent' else 'Stop',
                'session_id':identity['session_id'], 'cwd':str(self.project),
                'transcript_path':str(self.root / 'unused-parent.jsonl'),
                'last_assistant_message':report or self.report(identity, tests='red')}
        if boundary == 'subagent':
            data.update(agent_id='native-' + uuid.uuid4().hex, agent_transcript_path=str(transcript))
        else:
            data['transcript_path'] = str(transcript)
        return data

    def deliver(self, data):
        return self.call(payload=compact(data))

    def rejected(self, identity, data):
        before = self.snapshot()
        result = self.deliver(data)
        self.assertRegex(result.stderr, r'coverage[^\n]*[a-z]+[-_][a-z]+', 'rejection needs a safe reason code')
        self.assertEqual(self.snapshot(), before, 'rejected input mutated event state')
        self.assertEqual(self.status(identity)['state'], 'pending')

    def test_hook_dispatch_private_correlation_is_explicit(self):
        identity, line = self.dispatch()
        status = self.status(identity)
        self.assertEqual(status['state'], 'pending')
        self.assertNotIn('ORCHESTRAIL_REPORT', compact(status))
        for path in self.state.rglob('*'):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700 if path.is_dir() else 0o600)
        env = dict(self.env)
        env.pop('CLAUDE_CODE_SESSION_ID')
        before = self.snapshot()
        result = self.call('dispatch', '--run', identity['run_id'], '--agent-id', 'worker', '--boundary', 'subagent', env=env)
        self.assertEqual(result.stdout, '')
        self.assertIn('coverage', result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_hook_interleaved_runs_preserve_exact_identity(self):
        first, line_a = self.dispatch()
        second, line_b = self.dispatch(boundary='session', skill='pae-implement')
        self.deliver(self.payload(second, line_b, 'session', ('pae-implement',), self.report(second, tests='green')))
        self.deliver(self.payload(first, line_a))
        for identity, skill in [(first, 'pae-tests'), (second, 'pae-implement')]:
            steps = [event for event in self.events(identity['run_id']) if event['event'] == 'step']
            self.assertEqual(len(steps), 1)
            for key in ('run_id', 'session_id', 'agent_id', 'checkpoint_id'):
                self.assertEqual(steps[0][key], identity[key])
            self.assertEqual(steps[0]['step'], skill)
            self.assertEqual(steps[0]['timing_source'], 'hook')
            self.assertLessEqual(steps[0]['span_start_ms'], steps[0]['span_end_ms'])

    def test_hook_concurrent_duplicate_deliveries_append_once(self):
        identity, line = self.dispatch()
        payload = self.payload(identity, line)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(lambda _: self.deliver(payload), range(5)))
        steps = [e for e in self.events(identity['run_id']) if e['event'] == 'step']
        self.assertEqual(len(steps), 1)
        self.assertEqual(self.status(identity)['state'], 'accepted')

    def test_hook_closed_run_delivery_never_reopens(self):
        identity, line = self.dispatch()
        payload = self.payload(identity, line)
        self.producer('run-end', '--run', identity['run_id'], '--outcome', 'completed')
        before = self.snapshot()
        result = self.deliver(payload)
        self.assertIn('coverage', result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertNotEqual(self.status(identity)['state'], 'accepted')

    def test_hook_missing_and_conflicting_native_fields_preserve_pending(self):
        identity, line = self.dispatch()
        original = self.payload(identity, line)
        for key in ('session_id','cwd','transcript_path','last_assistant_message','agent_id','agent_transcript_path','hook_event_name'):
            for replacement in (None, 1, ''):
                data = dict(original, **{key:replacement})
                self.rejected(identity, data)
        self.rejected(identity, dict(original, session_id='another-session'))
        self.rejected(identity, dict(original, hook_event_name='Stop'))
        wrong_project = self.root / 'other registered'
        wrong_project.mkdir()
        registry = self.config / 'orchestrail' / 'projects'
        registry.write_text(registry.read_text() + str(wrong_project) + '\n')
        self.rejected(identity, dict(original, cwd=str(wrong_project)))

    def test_hook_inactive_project_gates_before_transcript_and_state_reads(self):
        identity, line = self.dispatch()
        original = self.payload(identity, line)
        # FIFOs would hang on any attempted transcript read; component sibling
        # must remain inactive even though its prefix matches the registered root.
        fifo = self.root / 'unreadable-transcript'
        os.mkfifo(fifo)
        sibling = Path(str(self.project) + '-unregistered')
        sibling.mkdir()
        payload = dict(original, cwd=str(sibling), agent_transcript_path=str(fifo))
        before = self.snapshot()
        state_before = {str(p): p.read_bytes() for p in self.state.rglob('*') if p.is_file()}
        result = self.deliver(payload)
        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr, '')
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(state_before, {str(p): p.read_bytes() for p in self.state.rglob('*') if p.is_file()})

    def test_hook_session_unknown_and_unique_skill_remain_distinct(self):
        identity, line = self.dispatch(boundary='session', skill=None)
        self.deliver(self.payload(identity, line, 'session', ()))
        self.assertEqual(self.events(identity['run_id'])[-1]['step'], 'unknown')
        second, line_b = self.dispatch(boundary='session', skill=None)
        self.deliver(self.payload(second, line_b, 'session', ('pd-analyze',)))
        self.assertEqual(self.events(second['run_id'])[-1]['step'], 'pd-analyze')
        third, line_c = self.dispatch(skill=None)
        self.rejected(third, self.payload(third, line_c, skills=()))

    def test_hook_native_schema_and_input_limits_warn_safely(self):
        identity, line = self.dispatch()
        before = self.snapshot()
        for raw in ('', '{', 'null', '[]', compact({'cwd':str(self.project)}), ' ' * (1048576 + 1)):
            result = self.call(payload=raw)
            self.assertRegex(result.stderr, r'coverage[^\n]*[a-z]+[-_][a-z]+')
            self.assertEqual(result.stdout, '')
            self.assertEqual(before, self.snapshot())
        payload = self.payload(identity, line)
        payload['last_assistant_message'] = self.report(identity) + 'x' * 4096
        self.rejected(identity, payload)
        self.deliver(self.payload(identity, line))
        self.assertEqual(self.status(identity)['state'], 'accepted')

    def test_hook_bounded_transcript_tail_requires_dispatch_input(self):
        identity, line = self.dispatch()
        payload = self.payload(identity, line)
        path = Path(payload['agent_transcript_path'])
        with path.open('a') as stream:
            stream.write(compact({'type':'assistant','message':{'content':'x' * (16 * 1024 * 1024)}}) + '\n')
        self.rejected(identity, payload)

    def test_hook_accepted_status_blocks_fallback_and_returns_receipt(self):
        identity, line = self.dispatch()
        self.deliver(self.payload(identity, line))
        status = self.status(identity)
        self.assertEqual(status['state'], 'accepted')
        receipt = status['receipt']
        for key in ('run_id','session_id','agent_id','checkpoint_id'):
            self.assertEqual(receipt[key], identity[key])
        self.assertEqual(receipt['kind'], 'accepted')
        self.assertGreater(receipt['seq'], 0)
        before = self.snapshot()
        self.call('fallback', '--checkpoint', identity['checkpoint_id'], '--step', 'pae-tests', '--outcome', 'ok')
        self.assertEqual(before, self.snapshot())

    def test_hook_fallback_first_owns_route_even_when_legacy_write_fails(self):
        identity, line = self.dispatch()
        self.call('fallback', '--checkpoint', identity['checkpoint_id'], '--step', 'pae-tests', '--outcome', 'ok', '--tests', 'red')
        self.assertEqual(self.status(identity)['state'], 'fallback-attempted')
        steps = [e for e in self.events(identity['run_id']) if e['event'] == 'step']
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]['note'], 'approximate')
        self.assertNotIn('timing_source', steps[0])
        before = self.snapshot()
        self.deliver(self.payload(identity, line))
        self.call('fallback', '--checkpoint', identity['checkpoint_id'], '--step', 'pae-tests', '--outcome', 'ok')
        self.assertEqual(before, self.snapshot())
        failed, failed_line = self.dispatch()
        self.helper.write_text('#!/usr/bin/env bash\nexit 0\n')
        self.call('fallback', '--checkpoint', failed['checkpoint_id'], '--step', 'pae-tests', '--outcome', 'ok')
        self.assertEqual(self.status(failed)['state'], 'fallback-attempted')
        self.assertNotIn('receipt', self.status(failed))

    def test_hook_frozen_retry_requires_matching_receipt(self):
        identity, line = self.dispatch()
        payload = self.payload(identity, line)
        real_helper = self.helper.read_bytes()
        captures = self.root / 'producer-calls.jsonl'
        self.helper.write_text('''#!/usr/bin/env bash
python3 - "$@" <<'INNER'
import json, os, sys
with open(os.environ['HOOK_TEST_CAPTURE'], 'a') as stream:
    stream.write(json.dumps(sys.argv[1:]) + '\\n')
print('{"kind":"accepted","run_id":"wrong","seq":1}')
INNER
''')
        self.env['HOOK_TEST_CAPTURE'] = str(captures)
        self.deliver(payload)
        self.assertEqual(self.status(identity)['state'], 'delivering')
        self.call('fallback', '--checkpoint', identity['checkpoint_id'], '--step', 'pae-tests', '--outcome', 'ok')
        self.deliver(payload)
        calls = [json.loads(s) for s in captures.read_text().splitlines()]
        self.assertEqual(len(calls), 2, 'fallback cannot attempt the ordinary route after delivery starts')
        self.assertEqual(calls[0], calls[1], 'retry must use identical frozen complete payload')
        self.helper.write_bytes(real_helper)
        self.deliver(payload)
        self.assertEqual(self.status(identity)['state'], 'accepted')
        event = self.events(identity['run_id'])[-1]
        self.assertEqual(str(event['span_end_ms']), calls[0][calls[0].index('--span-end-ms') + 1])

    def test_hook_marker_canonicality_and_exact_tuple_reject_ambiguity(self):
        identity, line = self.dispatch()
        canonical = self.report(identity)
        body = canonical.split(' ', 1)[1]
        cases = [canonical + '\n' + canonical, '```\n' + canonical + '\n```', ' ' + canonical,
                 'ORCHESTRAIL_REPORT_V1 ' + json.dumps(dict(identity, outcome='ok')),
                 'ORCHESTRAIL_REPORT_V1 ' + body[:-1] + ',"outcome":"ok"}',
                 'ORCHESTRAIL_REPORT_V1 ' + compact(dict(identity, outcome='ok', step='pae-tests')),
                 'ORCHESTRAIL_REPORT_V1 ' + compact(dict(identity, outcome='success')),
                 'successfully completed all tests']
        for key in ('run_id','session_id','agent_id','checkpoint_id'):
            changed = dict(identity, outcome='ok')
            changed[key] = 'wrong-identity'
            cases.append('ORCHESTRAIL_REPORT_V1 ' + compact(changed))
        for report in cases:
            self.rejected(identity, self.payload(identity, line, report=report))
        self.deliver(self.payload(identity, line))
        self.assertEqual(self.status(identity)['state'], 'accepted')

    def test_hook_native_evidence_uses_input_and_unique_invocation_ids(self):
        identity, line = self.dispatch()
        original = self.payload(identity, line)
        path = Path(original['agent_transcript_path'])
        # Output text and arbitrary JSON fields are not native dispatch evidence.
        for records in [[{'type':'assistant','message':{'role':'assistant','content':line}}],
                        [{'type':'user','debug':line,'message':{'content':'unrelated'}}]]:
            path.write_text(''.join(compact(r) + '\n' for r in records))
            self.rejected(identity, original)
        wrong = self.transcript('unrelated', ('pae-tests',))
        original['transcript_path'] = str(self.transcript(line))
        original['agent_transcript_path'] = str(wrong)
        self.rejected(identity, original)
        for skills in [('pae-tests','pae-tests'), ('pae-tests','pae-implement'), ('pd-analyze',)]:
            self.rejected(identity, self.payload(identity, line, skills=skills))
        original = self.payload(identity, line)
        path = Path(original['agent_transcript_path'])
        rows = path.read_text().splitlines()
        path.write_text('\n'.join(rows + [rows[-1]]) + '\n')
        self.deliver(original)
        self.assertEqual(self.status(identity)['state'], 'accepted')
        conflicting, other_line = self.dispatch()
        data = self.payload(conflicting, other_line)
        path = Path(data['agent_transcript_path'])
        rows = path.read_text().splitlines()
        changed = json.loads(rows[-1])
        changed['message']['content'][0]['input']['skill'] = 'pd-analyze'
        path.write_text('\n'.join(rows + [compact(changed)]) + '\n')
        self.rejected(conflicting, data)

    def test_hook_registered_roots_choose_most_specific_and_reject_changed_owner(self):
        nested = self.project / 'nested project'
        nested.mkdir()
        registry = self.config / 'orchestrail' / 'projects'
        registry.write_text(str(nested) + '\n' + str(self.project) + '\n' + str(nested) + '\n')
        self.project = nested
        identity, line = self.dispatch()
        self.deliver(self.payload(identity, line))
        self.assertEqual(self.status(identity)['state'], 'accepted')
        broader = nested.parent
        self.project = broader
        registry.write_text(str(broader) + '\n')
        changed, changed_line = self.dispatch()
        self.project = nested
        registry.write_text(str(broader) + '\n' + str(nested) + '\n')
        before = self.snapshot()
        result = self.deliver(self.payload(changed, changed_line))
        self.assertIn('project-mismatch', result.stderr)
        self.assertEqual(before, self.snapshot())
        self.project = broader
        self.assertEqual(self.status(changed)['state'], 'pending')

    def test_hook_invalid_fallback_arguments_leave_pending_and_unmutated(self):
        identity, line = self.dispatch()
        before = self.snapshot()
        variants = [('--step','pae-tests','--outcome','success'),
                    ('--step','pae-tests','--outcome','ok','--gate','unknown'),
                    ('--step','pae-tests','--outcome','ok','--tests',''),
                    ('--step','pae-tests','--outcome','ok','--outcome','failed'),
                    ('--step','pae-tests','--outcome','ok','--note','arbitrary')]
        for args in variants:
            result = self.call('fallback','--checkpoint',identity['checkpoint_id'],*args)
            self.assertIn('coverage', result.stderr)
            self.assertEqual(self.status(identity)['state'], 'pending')
            self.assertEqual(before, self.snapshot())
        self.deliver(self.payload(identity, line))
        self.assertEqual(self.status(identity)['state'], 'accepted')

    def test_hook_fallback_and_native_delivery_concurrently_choose_one_route(self):
        identity, line = self.dispatch()
        data = self.payload(identity, line)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(self.deliver, data)
            b = pool.submit(self.call, 'fallback','--checkpoint',identity['checkpoint_id'],
                            '--step','pae-tests','--outcome','ok')
            a.result()
            b.result()
        status = self.status(identity)
        self.assertIn(status['state'], ('accepted','fallback-attempted'))
        steps = [e for e in self.events(identity['run_id']) if e['event'] == 'step']
        self.assertEqual(len(steps), 1)
        if status['state'] == 'accepted':
            self.assertEqual(steps[0]['timing_source'], 'hook')
        else:
            self.assertEqual(steps[0]['note'], 'approximate')
            self.assertNotIn('receipt', status)

    def test_hook_missing_hook_dependencies_leave_store_unchanged(self):
        identity, line = self.dispatch()
        data = self.payload(identity, line)
        directory = self.root / 'limited commands'
        directory.mkdir()
        for name in ('bash','dirname'):
            (directory / name).symlink_to(shutil.which(name))
        env = dict(self.env, PATH=str(directory))
        before = self.snapshot()
        result = self.call(payload=compact(data), env=env)
        self.assertEqual(result.stdout, '')
        self.assertIn('dependency-unavailable', result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.status(identity)['state'], 'pending')

    def test_hook_byte_limits_and_native_identity_preserve_exact_bytes(self):
        identity, line = self.dispatch()
        original = self.payload(identity, line)
        raw = compact(original)
        before = self.snapshot()
        variants = [raw + '\n' * (1048577 - len(raw)),
                    raw.replace(',"session_id"', ',\x00"session_id"')]
        for payload in variants:
            result = self.call(payload=payload)
            self.assertIn('coverage', result.stderr)
            self.assertEqual(before, self.snapshot())
            self.assertEqual(self.status(identity)['state'], 'pending')
        self.rejected(identity, dict(original, session_id=identity['session_id'] + '\n'))
        self.rejected(identity, dict(original, last_assistant_message=self.report(identity) + '\x00'))

    def test_hook_predispatch_and_tool_result_evidence_do_not_count(self):
        identity, line = self.dispatch()
        data = self.payload(identity, line)
        path = Path(data['agent_transcript_path'])
        rows = path.read_text().splitlines()
        # A prior invocation cannot establish this checkpoint; a tool_result's
        # text never becomes the checkpoint's native input envelope.
        path.write_text('\n'.join([rows[1], rows[0]]) + '\n')
        self.rejected(identity, data)
        input_row = {'type':'user','message':{'role':'user','content':[
            {'type':'tool_result','tool_use_id':'old','content':line}]}}
        path.write_text(compact(input_row) + '\n' + rows[1] + '\n')
        self.rejected(identity, data)
        block = {'type':'user','message':{'role':'user','content':[{'type':'text','text':line}]}}
        path.write_text(compact(block) + '\n' + rows[1] + '\n')
        self.deliver(data)
        self.assertEqual(self.status(identity)['state'], 'accepted')

    def test_hook_explicit_waiting_and_parent_survive_out_of_order_delivery(self):
        parent, parent_line = self.dispatch()
        child, child_line = self.dispatch(run=parent['run_id'],
            extra=('--parent-checkpoint-id', parent['checkpoint_id'], '--span-kind','waiting'))
        self.deliver(self.payload(child, child_line))
        self.deliver(self.payload(parent, parent_line))
        steps = [e for e in self.events(parent['run_id']) if e['event'] == 'step']
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0]['checkpoint_id'], child['checkpoint_id'])
        self.assertEqual(steps[0]['parent_checkpoint_id'], parent['checkpoint_id'])
        self.assertEqual(steps[0]['span_kind'], 'waiting')
        self.assertEqual(steps[1]['checkpoint_id'], parent['checkpoint_id'])

    def test_hook_missing_start_time_rejects_before_delivery(self):
        identity, line = self.dispatch()
        record = self.state / 'orchestrail' / 'hooks' / (identity['checkpoint_id'] + '.json')
        metadata = json.loads(record.read_text())
        metadata.pop('span_start_ms')
        record.write_text(compact(metadata))
        before = self.snapshot()
        result = self.deliver(self.payload(identity, line))
        self.assertIn('invalid-correlation', result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_hook_receipt_must_be_one_matching_object_with_integer_sequence(self):
        identity, line = self.dispatch()
        data = self.payload(identity, line)
        real_helper = self.helper.read_bytes()
        self.helper.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$HOOK_TEST_RECEIPT"\n')
        receipt = dict(identity, kind='accepted', seq=1, duplicate=False)
        variants = [compact(dict(receipt,seq=0)),compact(dict(receipt,seq=True)),
                    compact(dict(receipt,agent_id='different')),compact(receipt) + '\n' + compact(receipt),
                    '', '{}']
        for value in variants:
            self.env['HOOK_TEST_RECEIPT'] = value
            result = self.deliver(data)
            self.assertIn('acceptance-uncertain', result.stderr)
            self.assertEqual(self.status(identity)['state'], 'delivering')
        self.helper.write_bytes(real_helper)
        self.deliver(data)
        self.assertEqual(self.status(identity)['state'], 'accepted')

    def test_hook_delivering_retries_survive_rotation_and_reject_changed_report_or_actor(self):
        identity, line = self.dispatch()
        data = self.payload(identity, line)
        real_helper = self.helper.read_bytes()
        captures = self.root / 'retry-calls'
        self.env['HOOK_TEST_CAPTURE'] = str(captures)
        self.helper.write_text('''#!/usr/bin/env bash
printf 'called\\n' >> "$HOOK_TEST_CAPTURE"
''')
        self.deliver(data)
        self.assertEqual(self.status(identity)['state'], 'delivering')
        Path(data['agent_transcript_path']).unlink()
        self.assertEqual(captures.read_text().splitlines(), ['called'])
        for changed in [dict(data, agent_id='other-native'),
                        dict(data, last_assistant_message=self.report(identity, tests='green')),
                        dict(data, last_assistant_message=self.report(identity))]:
            result = self.deliver(changed)
            self.assertIn('conflicting-delivery', result.stderr)
            self.assertEqual(self.status(identity)['state'], 'delivering')
            self.assertEqual(captures.read_text().splitlines(), ['called'])
        self.helper.write_bytes(real_helper)
        self.deliver(data)
        self.assertEqual(self.status(identity)['state'], 'accepted')
        self.assertEqual(self.events(identity['run_id'])[-1]['tests'], 'red')

    def test_hook_unicode_json_byte_limit_is_not_character_limit(self):
        identity, line = self.dispatch()
        data = self.payload(identity, line)
        data['native_extension'] = '\u00e9' * 524288
        raw = compact(data)
        self.assertLess(len(raw), 1048576)
        self.assertGreater(len(raw.encode()), 1048576)
        before = self.snapshot()
        result = self.call(payload=raw)
        self.assertIn('input-too-large', result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.status(identity)['state'], 'pending')

    def test_hook_skill_name_suffix_is_rejected_without_normalization(self):
        identity, line = self.dispatch()
        self.rejected(identity, self.payload(identity, line, skills=('pae-tests\n',)))

    def test_hook_corrupted_frozen_payload_or_receipt_never_changes_run_attribution(self):
        identity, line = self.dispatch()
        other = self.start()
        data = self.payload(identity, line)
        real_helper = self.helper.read_bytes()
        self.helper.write_text('#!/usr/bin/env bash\nexit 0\n')
        self.deliver(data)
        self.assertEqual(self.status(identity)['state'], 'delivering')
        self.helper.write_bytes(real_helper)
        record = self.state / 'orchestrail' / 'hooks' / (identity['checkpoint_id'] + '.json')
        frozen = json.loads(record.read_text())
        before = self.snapshot()
        alterations = [('run_id',other), ('session_id','different'), ('agent_id','different'),
                       ('checkpoint_id','different'), ('span_start_ms',0), ('span_end_ms',-1),
                       ('boundary','session'), ('span_kind','waiting'), ('parent_checkpoint_id','different'),
                       ('outcome','success'), ('tests','invalid'), ('gate','invalid'), ('step','pd-analyze')]
        for field, value in alterations:
            metadata = json.loads(compact(frozen))
            metadata['payload'][field] = value
            record.write_text(compact(metadata))
            result = self.deliver(data)
            self.assertIn('invalid-correlation', result.stderr, field)
            self.assertEqual(before, self.snapshot(), field)
        record.write_text(compact(frozen))
        self.deliver(data)
        self.assertEqual(self.status(identity)['state'], 'accepted')
        accepted = json.loads(record.read_text())
        before = self.snapshot()
        for field, value in [('run_id',other),('seq',True),('seq',0)]:
            metadata = json.loads(compact(accepted))
            metadata['receipt'][field] = value
            record.write_text(compact(metadata))
            result = self.call('status','--checkpoint',identity['checkpoint_id'])
            self.assertEqual(result.stdout, '')
            self.assertIn('invalid-correlation', result.stderr)
            self.assertEqual(before, self.snapshot())

    def test_hook_documented_dispatch_marker_and_ownership_contract(self):
        rule = (SOURCE / 'rules' / 'run-log.md').read_text()
        for token in ('ORCHESTRAIL_DISPATCH_V1', 'ORCHESTRAIL_REPORT_V1', 'last_assistant_message',
                      'agent_transcript_path', 'fallback-attempted', 'delivering', 'status --checkpoint',
                      '1048576', '16777216', 'claude-stop-v1'):
            self.assertIn(token, rule, 'canonical rule must publish adapter interface: ' + token)

suite = unittest.TestSuite(HookContract(name) for name in SELECTED) if SELECTED else unittest.defaultTestLoader.loadTestsFromTestCase(HookContract)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
PY
