#!/usr/bin/env bash
# Exercise exact timing analysis and complete hook lifecycle in disposable roots.
# Usage: bash tests/hook-timing.sh [test-name ...]. Never reads real telemetry.
set -uo pipefail
timing_test_source="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
python3 - "$timing_test_source" "$@" <<'PY'
from __future__ import annotations
import ast
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import TypeAlias
import unittest
import uuid

Record: TypeAlias = dict[str, object]
Environment: TypeAlias = dict[str, str]
SOURCE = Path(sys.argv[1])


def compact(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


class HookTiming(unittest.TestCase):
    root: Path
    checkout: Path
    project: Path
    helper: Path
    env: Environment
    run_id: str
    session: str

    def setUp(self) -> None:
        scratch = tempfile.TemporaryDirectory(prefix='timing acceptance ')
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.checkout = self.root / "source 'quoted' with spaces"
        for folder in ('scripts', 'hooks', 'rules', 'workflows', 'harness', 'templates', 'principles'):
            shutil.copytree(SOURCE / folder, self.checkout / folder)
        self.project = self.root / 'registered project'
        self.project.mkdir()
        config = self.root / 'config'
        (config / 'orchestrail').mkdir(parents=True)
        (config / 'orchestrail/projects').write_text(str(self.project.resolve()) + '\n')
        self.helper = self.checkout / 'scripts/log-step.sh'
        self.env = dict(os.environ, HOME=str(self.root / 'home'), XDG_CONFIG_HOME=str(config),
                        XDG_STATE_HOME=str(self.root / 'state'), ORCHESTRAIL_HOME=str(self.checkout),
                        ORCHESTRAIL_LOG_ROOT=str(self.root / 'unselected store'),
                        CLAUDE_CODE_SESSION_ID='session-' + uuid.uuid4().hex)
        for name in ('PYTHONPATH', 'PYTHONSTARTUP', 'BASH_ENV', 'ENV'):
            self.env.pop(name, None)
        self.run_id, self.session = uuid.uuid4().hex[:8], 'session-' + uuid.uuid4().hex

    def base(self, event: str, stamp: int) -> Record:
        return dict(event=event, run_id=self.run_id, ts='2026-01-01T00:00:00Z', ts_ms=stamp,
                    seq=0, pipeline='phase-execution', project=str(self.project), flow='full')

    def boundary(self, event: str, stamp: int) -> Record:
        row = self.base(event, stamp)
        if event == 'run-end':
            row.update(outcome='completed', duration_s=stamp // 1000)
        return row

    def span(self, description: tuple[str, tuple[int, int]], **fields: object) -> Record:
        checkpoint, interval = description
        start, end = interval
        row = self.base('step', end)
        row.update(step='pae-tests', outcome='ok', duration_s=(end - start) // 1000,
                   session_id=self.session, agent_id='worker-a', checkpoint_id=checkpoint,
                   span_start_ms=start, span_end_ms=end, timing_source='hook', boundary='subagent')
        row.update(fields)
        return row

    def corpus(self, spans: list[Record], bounds: tuple[int, int] = (0, 10000)) -> list[Record]:
        return [self.boundary('run-start', bounds[0]), *spans, self.boundary('run-end', bounds[1])]

    def write(self, rows: list[Record | str], name: str = 'explicit selected.jsonl') -> Path:
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(''.join((r if isinstance(r, str) else compact(r)) + '\n' for r in rows))
        return target

    def command(self, request: tuple[Path, list[str]], **options: object) -> subprocess.CompletedProcess[str]:
        script, args = request
        return subprocess.run(['/bin/bash', str(script), *args], cwd=self.project,
                              env=options.get('env', self.env), input=options.get('payload'),
                              text=True, capture_output=True, timeout=25)

    def analyze(self, paths: list[Path | str], env: Environment | None = None) -> Record:
        launcher = self.checkout / 'scripts/run-log-timing.sh'
        before = {str(p): p.read_bytes() for p in paths if isinstance(p, Path) and p.is_file()}
        command = ['/bin/bash', str(launcher), *map(str, paths)] if launcher.exists() else ['/bin/bash', '-c', ':']
        result = subprocess.run(command, cwd=self.project, env=env or self.env,
                                text=True, capture_output=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1, 'timing CLI must emit one structured result')
        result_json = json.loads(result.stdout)
        self.assertEqual(result_json['schema_version'], 1)
        self.assertEqual({str(p): Path(p).read_bytes() for p in before}, before, 'source bytes changed')
        self.assertNotIn('SECRET-CONTEXT', result.stdout + result.stderr)
        self.assertLess(len(result.stderr.encode()), 4096)
        return result_json

    def one(self, rows: list[Record | str]) -> Record:
        data = self.analyze([self.write(rows)])
        self.assertIn(data['status'], ('ok', 'partial'))
        self.assertEqual(len(data['runs']), 1)
        return data['runs'][0]

    def measures(self, run: Record, expected: Record) -> None:
        for name, value in expected.items():
            self.assertEqual(run['metrics'][name], None if value is None else str(value), name)

    def ratio(self, run: Record, expected: tuple[str, int, int]) -> None:
        name, numerator, denominator = expected
        self.assertEqual(run['metrics'][name], dict(numerator_ms=str(numerator), denominator_ms=str(denominator)))

    def workers(self, run: Record) -> dict[str, object]:
        return {worker['agent_id']: worker['exclusive_work_ms'] for worker in run['workers']}

    def unavailable(self, data: Record) -> None:
        self.assertEqual(data['status'], 'unavailable')
        self.assertIsNone(data['runs'])
        self.assertTrue(data['diagnostics'], 'unavailable result needs reason-coded diagnostics')
        self.assertNotEqual(data['coverage'].get('lint_status'), 'ok')

    def test_timing_sequential_complete_uses_exact_wall_denominator(self) -> None:
        run = self.one(self.corpus([self.span(('first', (0, 4000))), self.span(('second', (4000, 10000)))]))
        self.assertEqual(run['status'], 'ok')
        self.measures(run, dict(wall_ms=10000, inclusive_work_span_ms=10000, work_union_ms=10000,
                               observed_union_ms=10000, exclusive_work_union_ms=10000,
                               excess_work_span_ms=0, wall_overlap_ms=0, parallel_worker_overlap_ms=0))
        self.ratio(run, ('coverage_ratio', 10000, 10000))
        self.assertEqual(run['metrics']['gaps'], [])
        self.assertEqual(self.workers(run), {'worker-a': '10000'})
        self.assertEqual(len(run['spans']), 2)

    def test_timing_successive_actor_spans_preserve_gaps_without_waiting(self) -> None:
        run = self.one(self.corpus([self.span(('first', (0, 4000))), self.span(('second', (6000, 10000)))]))
        self.measures(run, dict(observed_union_ms=8000, waiting_union_ms=0, inclusive_waiting_span_ms=0))
        self.assertEqual(run['metrics']['gaps'], [['4000', '6000']])
        self.ratio(run, ('coverage_ratio', 8000, 10000))
        self.assertEqual(self.workers(run), {'worker-a': '8000'})

    def test_timing_nested_reference_subtracts_waiting_from_direct_parent(self) -> None:
        spans = [self.span(('outer', (0, 10000))),
                 self.span(('child', (2000, 8000)), agent_id='worker-b', parent_checkpoint_id='outer'),
                 self.span(('wait', (4000, 6000)), agent_id='worker-b', parent_checkpoint_id='child', span_kind='waiting')]
        run = self.one(self.corpus(list(reversed(spans))))
        self.measures(run, dict(inclusive_work_span_ms=16000, work_union_ms=10000, observed_union_ms=10000,
                               exclusive_work_union_ms=8000, excess_work_span_ms=6000, wall_overlap_ms=6000,
                               parallel_worker_overlap_ms=0, inclusive_waiting_span_ms=2000, waiting_union_ms=2000))
        self.assertEqual(self.workers(run), {'worker-a': '4000', 'worker-b': '4000'})
        self.ratio(run, ('active_work_coverage_ratio', 8000, 10000))

    def test_timing_same_actor_overlap_retains_union_and_distinct_actor_parallelism(self) -> None:
        spans = [self.span(('first', (0, 6000))), self.span(('second', (4000, 10000))),
                 self.span(('other', (5000, 7000)), agent_id='worker-b')]
        run = self.one(self.corpus(spans))
        self.measures(run, dict(inclusive_work_span_ms=14000, work_union_ms=10000, observed_union_ms=10000,
                               exclusive_work_union_ms=10000, excess_work_span_ms=4000, wall_overlap_ms=3000,
                               parallel_worker_overlap_ms=2000, inclusive_waiting_span_ms=0, waiting_union_ms=0))
        self.assertEqual(self.workers(run), {'worker-a': None, 'worker-b': '2000'})
        self.assertEqual(run['status'], 'partial')
        self.assertTrue(run['diagnostics'])

    def test_timing_invalid_component_reference_preserves_disconnected_root(self) -> None:
        spans = [self.span(('invalid', (0, 4000)), agent_id='worker-i', parent_checkpoint_id='missing'),
                 self.span(('descendant', (1000, 3000)), agent_id='worker-j', parent_checkpoint_id='invalid'),
                 self.span(('root', (6000, 10000)), agent_id='worker-r'),
                 self.span(('wait', (7000, 8000)), agent_id='worker-r', parent_checkpoint_id='root', span_kind='waiting')]
        run = self.one(self.corpus(spans))
        self.measures(run, dict(inclusive_work_span_ms=10000, work_union_ms=8000, observed_union_ms=8000,
                               exclusive_work_union_ms=3000, excess_work_span_ms=2000, wall_overlap_ms=3000,
                               parallel_worker_overlap_ms=0, inclusive_waiting_span_ms=1000, waiting_union_ms=1000))
        self.assertEqual(self.workers(run), {'worker-i': None, 'worker-j': None, 'worker-r': '3000'})
        self.assertEqual(run['metrics']['gaps'], [['4000', '6000']])
        self.ratio(run, ('active_work_coverage_ratio', 3000, 10000))

    def test_timing_parallel_roots_allow_worker_sum_above_wall(self) -> None:
        spans = [self.span(('a', (0, 10000))), self.span(('b', (0, 10000)), agent_id='worker-b')]
        run = self.one(self.corpus(spans))
        self.measures(run, dict(inclusive_work_span_ms=20000, exclusive_work_union_ms=10000,
                               parallel_worker_overlap_ms=10000, wall_overlap_ms=10000))
        self.assertEqual(self.workers(run), {'worker-a': '10000', 'worker-b': '10000'})

    def test_timing_waiting_sum_and_union_are_independent_of_active_work(self) -> None:
        spans = [self.span(('work', (0, 10000))), self.span(('w1', (1000, 6000)), span_kind='waiting', agent_id='waiter'),
                 self.span(('w2', (4000, 8000)), span_kind='waiting', agent_id='waiter')]
        run = self.one(self.corpus(spans))
        self.measures(run, dict(inclusive_waiting_span_ms=9000, waiting_union_ms=7000,
                               observed_union_ms=10000, exclusive_work_union_ms=10000))
        self.assertEqual(run['metrics']['gaps'], [])

    def test_timing_unknown_session_span_contributes_only_observed_coverage(self) -> None:
        spans = [self.span(('unknown', (0, 10000)), step='unknown', boundary='session', agent_id=self.session)]
        run = self.one(self.corpus(spans))
        self.measures(run, dict(observed_union_ms=10000))
        self.assertEqual(run['named_steps'], [])
        self.assertEqual(len(run['spans']), 1)

    def test_timing_measured_span_approximation_markers_are_exact(self) -> None:
        for note, expected in [('approximate', True), ('approximate; private SECRET-CONTEXT', True),
                               (' approximate', False), ('Approximate', False), ('x approximate', False),
                               ('approximate;', False), ('approximate;\tcontext', False)]:
            with self.subTest(note=note):
                row = self.span(('measured', (0, 10000)), note=note)
                run = self.one(self.corpus([row]))
                self.assertEqual(run['approximate'], expected)
                self.assertEqual(len(run['spans']), 1)
                self.measures(run, dict(observed_union_ms=10000))

    def test_timing_unmarked_legacy_and_missing_interval_remain_unmeasured(self) -> None:
        row = self.base('step', 10000)
        row.update(step='pae-tests', outcome='ok', duration_s=10)
        incomplete = self.span(('incomplete', (0, 10000)))
        del incomplete['span_start_ms']
        run = self.one(self.corpus([row, incomplete]))
        self.assertTrue(run['approximate'])
        self.assertEqual(run['spans'], [])
        self.measures(run, dict(observed_union_ms=0, exclusive_work_union_ms=None))

    def test_timing_invalid_producer_fields_exclude_entire_lines(self) -> None:
        for changes in [dict(outcome='invalid'), dict(tests='invalid'), dict(gate='invalid'),
                        dict(flow=''), dict(seq=-1), dict(stops=-1), dict(decisions=True)]:
            with self.subTest(changes=changes):
                row = self.span(('bad', (0, 10000)), **changes)
                data = self.analyze([self.write(self.corpus([row]))])
                self.assertEqual(data['coverage']['lint_status'], 'ok')
                self.assertEqual(data['coverage']['invalid_lines'], 1)
                self.assertTrue(data['coverage']['invalid_lines_exact'])
                run = data['runs'][0]
                self.assertEqual(run['spans'], [])
                self.assertEqual(run['workers'], [])
                self.assertEqual(run['named_steps'], [])

    def test_timing_large_integer_totals_and_ratios_are_lossless_strings(self) -> None:
        maximum = 9007199254740991
        spans = [self.span(('a', (0, maximum))), self.span(('b', (0, maximum)), agent_id='worker-b')]
        run = self.one(self.corpus(spans, (0, maximum)))
        self.measures(run, dict(wall_ms=maximum, inclusive_work_span_ms=maximum * 2,
                               work_union_ms=maximum, excess_work_span_ms=maximum))
        self.ratio(run, ('coverage_ratio', maximum, maximum))

    def test_timing_historical_integral_lexemes_preserve_exact_endpoints(self) -> None:
        rows = self.corpus([self.span(('exact', (0, 9007199254740991)))], (0, 9007199254740991))
        text = '\n'.join(compact(row) for row in rows).replace('9007199254740991', '9007199254740991.000')
        run = self.one(text.split('\n'))
        self.measures(run, dict(wall_ms=9007199254740991, observed_union_ms=9007199254740991))

    def test_timing_fractional_nonfinite_boolean_or_out_of_bounds_spans_are_excluded(self) -> None:
        for token in ['-1', '0.1', 'true', 'NaN', 'Infinity', '9007199254740992']:
            with self.subTest(token=token):
                row = compact(self.span(('invalid', (123, 1000)))).replace('"span_start_ms":123', '"span_start_ms":' + token)
                run = self.one(self.corpus([row]))
                self.assertEqual(run['spans'], [])
                self.measures(run, dict(observed_union_ms=0))

    def test_timing_out_of_run_or_reversed_spans_do_not_create_groups(self) -> None:
        for start, end in [(0, 11000), (10001, 10002), (10000, 9999)]:
            with self.subTest(interval=(start, end)):
                run = self.one(self.corpus([self.span(('outside', (start, end)))]))
                self.assertEqual(run['spans'], [])
                self.assertEqual(run['workers'], [])
                self.assertEqual(run['named_steps'], [])
                self.measures(run, dict(observed_union_ms=0))

    def test_timing_zero_wall_and_endpoint_spans_have_unavailable_ratios(self) -> None:
        run = self.one(self.corpus([self.span(('zero', (10000, 10000)))], (10000, 10000)))
        self.measures(run, dict(wall_ms=0, observed_union_ms=0, exclusive_work_union_ms=0))
        self.assertIsNone(run['metrics']['coverage_ratio'])
        self.assertIsNone(run['metrics']['active_work_coverage_ratio'])
        self.assertEqual(self.workers(run), {'worker-a': '0'})

    def test_timing_zero_length_children_at_parent_end_remain_valid(self) -> None:
        spans = [self.span(('outer', (0, 10000))), self.span(('zero', (10000, 10000)), parent_checkpoint_id='outer'),
                 self.span(('leaf', (10000, 10000)), parent_checkpoint_id='zero')]
        run = self.one(self.corpus(spans))
        self.measures(run, dict(exclusive_work_union_ms=10000))
        self.assertEqual(run['status'], 'ok')

    def test_timing_waiting_only_observations_establish_zero_active_work(self) -> None:
        run = self.one(self.corpus([self.span(('waiting', (0, 10000)), span_kind='waiting')]))
        self.measures(run, dict(observed_union_ms=10000, work_union_ms=0, exclusive_work_union_ms=0,
                               inclusive_work_span_ms=0, inclusive_waiting_span_ms=10000, waiting_union_ms=10000))
        self.ratio(run, ('coverage_ratio', 10000, 10000))
        self.ratio(run, ('active_work_coverage_ratio', 0, 10000))
        self.assertEqual(run['named_steps'], [])

    def test_timing_zero_length_cycles_still_quarantine_exclusive_metrics(self) -> None:
        spans = [self.span(('a', (10000, 10000)), parent_checkpoint_id='b'),
                 self.span(('b', (10000, 10000)), parent_checkpoint_id='a')]
        run = self.one(self.corpus(spans))
        self.measures(run, dict(observed_union_ms=0, exclusive_work_union_ms=None))
        self.assertIsNone(self.workers(run)['worker-a'])
        self.assertEqual(run['status'], 'partial')

    def test_timing_duplicate_checkpoints_collapse_generated_variations(self) -> None:
        span = self.span(('same', (0, 10000)))
        repeat = dict(span, seq=7, ts='different generated timestamp', ts_ms=9999, span_kind='work')
        run = self.one(self.corpus([span, repeat]))
        self.measures(run, dict(inclusive_work_span_ms=10000))
        self.assertEqual(len(run['spans']), 1)
        self.assertTrue(run['diagnostics'])

    def test_timing_conflicting_checkpoint_delivery_fields_exclude_entire_key(self) -> None:
        for changes in [dict(agent_id='other'), dict(outcome='failed'), dict(tests='red'), dict(stops=1),
                        dict(duration_s=11), dict(note='SECRET-CONTEXT'), dict(extra_extension=2),
                        dict(span_kind='waiting'), dict(step='pae-implement')]:
            with self.subTest(changes=changes):
                span = self.span(('same', (0, 10000)))
                run = self.one(self.corpus([span, dict(span, **changes)]))
                self.assertEqual(run['spans'], [])
                self.assertEqual(run['workers'], [])
                self.assertEqual(run['named_steps'], [])
                self.measures(run, dict(observed_union_ms=0))

    def test_timing_duplicate_numeric_equality_uses_exact_mathematical_values(self) -> None:
        span = self.span(('same', (0, 10000)), opaque={'value': 1, 'items': [0, True]})
        original = compact(span)
        equivalent = original.replace('"value":1', '"value":1e0').replace('"items":[0,true]', '"items":[-0.0,true]')
        run = self.one(self.corpus([original, equivalent]))
        self.assertEqual(len(run['spans']), 1)
        unequal = original.replace('"value":1', '"value":1.0000000000000000000000000000000000000001')
        run = self.one(self.corpus([original, unequal]))
        self.assertEqual(run['spans'], [])
        typed = original.replace('"value":1', '"value":true')
        self.assertEqual(self.one(self.corpus([original, typed]))['spans'], [])

    def test_timing_boundaries_require_unique_substantive_equality(self) -> None:
        for event, changes in [('run-start', dict(spec='different')), ('run-start', dict(flags='different')),
                               ('run-end', dict(outcome='failed')), ('run-end', dict(duration_s=11)),
                               ('run-end', dict(ts_ms=10001)), ('run-end', dict(extra={'a': True}))]:
            with self.subTest(event=event, changes=changes):
                rows = self.corpus([self.span(('a', (0, 10000)))])
                candidate = rows[0] if event == 'run-start' else rows[-1]
                rows.append(dict(candidate, **changes))
                run = self.analyze([self.write(rows)])['runs'][0]
                self.assertEqual(run['status'], 'unavailable')
                self.assertIsNone(run['metrics'])
                self.assertTrue(run['diagnostics'])

    def test_timing_identical_boundaries_collapse_only_generated_fields(self) -> None:
        rows = self.corpus([self.span(('a', (0, 10000)))])
        rows += [dict(rows[0], seq=20, ts='alternate'), dict(rows[-1], seq=21, ts='alternate')]
        run = self.one(rows)
        self.measures(run, dict(wall_ms=10000, observed_union_ms=10000))
        self.assertTrue(run['diagnostics'])

    def test_timing_unusable_or_missing_boundaries_never_invent_denominators(self) -> None:
        for event in ('run-start', 'run-end'):
            for changes in [dict(ts_ms=None), dict(ts_ms=True), dict(ts_ms=-1), dict(seq=-1), dict(project=42)]:
                with self.subTest(event=event, changes=changes):
                    rows = self.corpus([self.span(('a', (0, 10000)))])
                    candidate = rows[0] if event == 'run-start' else rows[-1]
                    rows.append(dict(candidate, **changes))
                    run = self.analyze([self.write(rows)])['runs'][0]
                    self.assertIsNone(run['metrics'])
        for rows in [self.corpus([])[:-1], self.corpus([])[1:], []]:
            data = self.analyze([self.write(rows)])
            self.assertNotEqual(data['status'], 'ok')

    def test_timing_metadata_presence_and_exact_strings_control_attribution(self) -> None:
        for field in ('pipeline', 'project', 'task', 'flow'):
            with self.subTest(field=field):
                rows = self.corpus([self.span(('a', (0, 10000)))])
                rows[-1][field] = '' if field == 'task' else 'different'
                self.assertIsNone(self.analyze([self.write(rows)])['runs'][0]['metrics'])
                rows = self.corpus([self.span(('a', (0, 10000)), **{field: '' if field == 'task' else 'different'})])
                run = self.one(rows)
                self.assertEqual(run['spans'], [])
                self.assertTrue(run['diagnostics'])

    def test_timing_omitted_optional_metadata_and_start_only_labels_are_supported(self) -> None:
        rows = self.corpus([self.span(('a', (0, 10000)))])
        for row in rows:
            row.pop('project')
        rows[0].update(spec='only start', flags='start flags', host='start host', contract_version='historical')
        rows[1].update(spec='opaque step', host='other host')
        run = self.one(rows)
        self.measures(run, dict(wall_ms=10000, observed_union_ms=10000))
        self.assertEqual(run['status'], 'ok')

    def test_timing_parent_cycles_missing_or_cross_session_links_quarantine_components(self) -> None:
        cases = [dict(parent_checkpoint_id='missing'), dict(parent_checkpoint_id='outer'),
                 dict(parent_checkpoint_id='child'), dict(parent_checkpoint_id='foreign')]
        for index, fields in enumerate(cases):
            with self.subTest(index=index):
                outer = self.span(('outer', (0, 10000)), **fields)
                child = self.span(('child', (2000, 8000)), parent_checkpoint_id='outer')
                foreign = self.span(('foreign', (0, 10000)), session_id='another-session', agent_id='foreign')
                run = self.one(self.corpus([outer, child, foreign] if index == 3 else [outer, child]))
                self.measures(run, dict(observed_union_ms=6000 if index == 1 else 10000))
                self.assertIsNone(self.workers(run)['worker-a'])
                self.assertEqual(run['status'], 'partial')
                self.assertTrue(run['diagnostics'])

    def test_timing_same_actor_and_step_partial_components_keep_totals_unavailable(self) -> None:
        spans = [self.span(('invalid', (0, 4000)), parent_checkpoint_id='missing'),
                 self.span(('valid', (6000, 10000)))]
        run = self.one(self.corpus(spans))
        self.measures(run, dict(inclusive_work_span_ms=8000, exclusive_work_union_ms=4000))
        self.assertEqual(self.workers(run), {'worker-a': None})
        self.assertEqual(len(run['named_steps']), 1)
        named = run['named_steps'][0]
        self.assertEqual(named['step'], 'pae-tests')
        self.assertEqual(named['inclusive_work_span_ms'], '8000')
        self.assertIsNone(named['exclusive_work_span_ms'])
        valid = next(span for span in run['spans'] if span['checkpoint_id'] == 'valid')
        invalid = next(span for span in run['spans'] if span['checkpoint_id'] == 'invalid')
        self.assertEqual(valid['exclusive_ms'], '4000')
        self.assertEqual(valid['exclusive_segments'], [['6000', '10000']])
        self.assertIsNone(invalid['exclusive_ms'])
        self.assertIsNone(invalid['exclusive_segments'])
        self.assertEqual(run['status'], 'partial')

    def test_timing_parent_containment_failure_keeps_raw_union_only(self) -> None:
        spans = [self.span(('outer', (0, 4000))), self.span(('child', (2000, 6000)), parent_checkpoint_id='outer')]
        run = self.one(self.corpus(spans))
        self.measures(run, dict(inclusive_work_span_ms=8000, observed_union_ms=6000,
                               exclusive_work_union_ms=None, parallel_worker_overlap_ms=None))
        self.assertIsNone(self.workers(run)['worker-a'])

    def test_timing_rejected_child_tombstone_excludes_valid_parent_exclusive_time(self) -> None:
        spans = [self.span(('outer', (0, 10000))),
                 self.span(('child', (2000, 4000)), parent_checkpoint_id='outer', outcome='invalid', agent_id='rejected-only'),
                 self.span(('other', (6000, 8000)), agent_id='independent')]
        run = self.one(self.corpus(spans))
        self.measures(run, dict(inclusive_work_span_ms=12000, exclusive_work_union_ms=2000))
        self.assertEqual(self.workers(run), {'worker-a': None, 'independent': '2000'})
        self.assertEqual(len(run['spans']), 2)

    def test_timing_invalid_child_endpoint_quarantines_transitive_siblings(self) -> None:
        spans = [self.span(('outer', (0, 10000))),
                 self.span(('invalid', (2000, 12000)), parent_checkpoint_id='outer'),
                 self.span(('sibling', (4000, 6000)), parent_checkpoint_id='outer', agent_id='sibling'),
                 self.span(('descendant', (3000, 4000)), parent_checkpoint_id='invalid', agent_id='descendant')]
        run = self.one(self.corpus(spans))
        self.measures(run, dict(observed_union_ms=10000, exclusive_work_union_ms=None))
        self.assertEqual(self.workers(run), {'worker-a': None, 'sibling': None, 'descendant': None})

    def test_timing_conflicting_parent_declarations_quarantine_every_connected_component(self) -> None:
        spans = [self.span(('left', (0, 10000)), agent_id='left'), self.span(('right', (0, 10000)), agent_id='right'),
                 self.span(('conflict', (2000, 4000)), parent_checkpoint_id='left'),
                 self.span(('conflict', (2000, 4000)), parent_checkpoint_id='right')]
        run = self.one(self.corpus(spans))
        self.assertEqual(self.workers(run), {'left': None, 'right': None})
        self.measures(run, dict(inclusive_work_span_ms=20000, exclusive_work_union_ms=None))

    def test_timing_opaque_rejected_evidence_makes_exclusive_graph_unverified(self) -> None:
        for bad in ['{broken', compact(self.span(('bad', (0, 1)), session_id='invalid\nidentity')),
                    compact(self.span(('bad', (0, 1)), parent_checkpoint_id='invalid\nparent')),
                    compact(self.span(('bad', (0, 1)))).replace('"checkpoint_id":"bad"', '"checkpoint_id":"bad","checkpoint_id":"other"')]:
            with self.subTest(bad=bad):
                run = self.one(self.corpus([self.span(('good', (0, 10000))), bad]))
                self.measures(run, dict(observed_union_ms=10000, exclusive_work_union_ms=None,
                                       parallel_worker_overlap_ms=None))
                self.assertIsNone(run['metrics']['active_work_coverage_ratio'])
                self.assertIsNone(self.workers(run)['worker-a'])

    def test_timing_rejected_uncorrelated_legacy_rows_do_not_hide_graph_edges(self) -> None:
        legacy = self.base('step', 5000)
        legacy.update(step='pae-tests', outcome='invalid', duration_s=2)
        run = self.one(self.corpus([self.span(('good', (0, 10000))), legacy]))
        self.measures(run, dict(exclusive_work_union_ms=10000))
        self.assertEqual(self.workers(run), {'worker-a': '10000'})

    def test_timing_explicit_files_deduplicate_paths_without_discovering_store(self) -> None:
        selected = self.write(self.corpus([self.span(('a', (0, 10000)))]))
        unselected = Path(self.env['ORCHESTRAIL_LOG_ROOT']) / 'runs/private.jsonl'
        unselected.parent.mkdir(parents=True)
        unselected.write_text('SECRET-CONTEXT')
        alias = self.root / 'alias.jsonl'
        alias.symlink_to(selected)
        data = self.analyze([selected, alias, selected])
        self.assertEqual(data['coverage']['selected_files'], 1)
        self.assertEqual(data['coverage']['examined_lines'], 3)
        self.assertEqual(len(data['runs']), 1)
        self.assertEqual(data['runs'][0]['file'], str(selected.resolve()))

    def test_timing_cross_file_and_intra_file_run_identity_conflicts_are_unavailable(self) -> None:
        first = self.write(self.corpus([self.span(('a', (0, 10000)))]), 'first/shared.jsonl')
        second = self.write(self.corpus([self.span(('b', (0, 10000)))]), 'second/shared.jsonl')
        data = self.analyze([first, second])
        self.assertNotEqual(data['status'], 'ok')
        self.assertTrue(all(run['metrics'] is None for run in data['runs']))
        rows = self.corpus([self.span(('a', (0, 10000)), run_id=uuid.uuid4().hex[:8])])
        self.assertIsNone(self.analyze([self.write(rows)])['runs'][0]['metrics'])

    def test_timing_same_basename_distinct_runs_remain_independent(self) -> None:
        first = self.write(self.corpus([self.span(('a', (0, 10000)))]), 'first/shared.jsonl')
        self.run_id = uuid.uuid4().hex[:8]
        second = self.write(self.corpus([self.span(('b', (0, 5000)))]), 'second/shared.jsonl')
        data = self.analyze([first, second])
        self.assertEqual(data['coverage']['selected_files'], 2)
        self.assertEqual([run['metrics']['observed_union_ms'] for run in data['runs']], ['10000', '5000'])

    def test_timing_input_errors_never_look_like_clean_empty_corpus(self) -> None:
        for paths in [[], [self.root / 'missing.jsonl'], [self.root], ['--unknown-option']]:
            with self.subTest(paths=paths):
                self.unavailable(self.analyze(paths))

    def test_timing_end_of_options_accepts_literal_dash_path(self) -> None:
        selected = self.write(self.corpus([]), '-literal.jsonl')
        data = self.analyze(['--', selected])
        self.assertEqual(data['coverage']['selected_files'], 1)
        self.assertEqual(data['runs'][0]['metrics']['wall_ms'], '10000')

    def shim_path(self, excluded: tuple[str, ...] = ()) -> Path:
        target = self.root / ('commands-' + uuid.uuid4().hex)
        target.mkdir()
        for name in ('bash', 'dirname', 'python3', 'jq', 'mktemp', 'rm', 'cat', 'wc', 'find', 'sort', 'date', 'sed', 'awk'):
            command = shutil.which(name)
            if name not in excluded and command:
                (target / name).symlink_to(command)
        return target

    def test_timing_missing_python_jq_and_unsupported_python_return_null(self) -> None:
        selected = self.write(self.corpus([]))
        for missing in ('python3', 'jq', 'old-python'):
            with self.subTest(missing=missing):
                shim = self.shim_path(('python3',) if missing != 'jq' else ('jq',))
                if missing == 'old-python':
                    (shim / 'python3').write_text('#!/bin/bash\nexit 1\n')
                    (shim / 'python3').chmod(0o755)
                self.unavailable(self.analyze([selected], dict(self.env, PATH=str(shim))))

    def lint_shim(self, body: str) -> None:
        real = self.helper.with_name('real-log-step.sh')
        if not real.exists():
            self.helper.rename(real)
        self.helper.write_text('#!/bin/bash\nif [ "${1:-}" = lint ]; then\n' + body +
                               '\nexit 0\nfi\nexec /bin/bash ' + shlex.quote(str(real)) + ' "$@"\n')

    def test_timing_incomplete_or_malformed_lint_never_authorizes_metrics(self) -> None:
        selected = self.write(self.corpus([self.span(('a', (0, 10000)))]))
        summary = dict(kind='summary', status='ok', files=1, lines=3, invalid_lines=0, violations=0)
        cases = ['', '{}', compact(dict(summary, status='partial')), compact(dict(summary, files=0)),
                 compact(dict(summary, lines=2)), compact(dict(summary, lines=True)), compact(dict(summary, files=1.0)),
                 compact(dict(summary, invalid_lines=1)), compact(dict(summary, violations=1)),
                 compact(dict(summary, files=-1)), compact(summary)+'\n'+compact(summary),
                 compact(summary)+'\n'+compact(dict(kind='unknown'))]
        for diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                self.lint_shim('printf "%s\\n" ' + shlex.quote(diagnostic))
                self.unavailable(self.analyze([selected]))

    def test_timing_invalid_lint_references_and_unique_counts_are_rejected(self) -> None:
        selected = self.write(self.corpus([]))
        for field, value in [('file', '/unknown'), ('line', 0), ('line', 3), ('line', True),
                             ('field', ''), ('code', ''), ('kind', 'mystery')]:
            with self.subTest(field=field, value=value):
                fields = dict(kind='violation', file='$file', line=1, field='outcome', code='invalid-enum')
                fields[field] = value
                output = compact(fields).replace('"$file"', '"'+'${file}'+'"')
                summary = compact(dict(kind='summary', status='ok', files=1, lines=2, invalid_lines=1, violations=1))
                self.lint_shim('file=("$ORCHESTRAIL_LOG_ROOT"/runs/*)\nprintf "%s\\n" "' +
                               output.replace('"', '\\"').replace('\\"${file}\\"', '\\"${file[0]}\\"') +
                               '" ' + shlex.quote(summary))
                self.unavailable(self.analyze([selected]))

    def test_timing_known_lint_violations_remain_lower_bounds_when_summary_fails(self) -> None:
        selected = self.write(self.corpus([]))
        summary = compact(dict(kind='summary', status='partial', files=1, lines=2, invalid_lines=1, violations=1))
        violation = compact(dict(kind='violation', file='%s', line=1, field='outcome', code='invalid-enum'))
        self.lint_shim('file=("$ORCHESTRAIL_LOG_ROOT"/runs/*)\n' +
                       'printf ' + shlex.quote(violation + '\\n') + ' "${file[0]}"\n' +
                       'printf "%s\\n" ' + shlex.quote(summary))
        data = self.analyze([selected])
        self.unavailable(data)
        self.assertEqual(data['coverage']['invalid_lines'], 1)
        self.assertEqual(data['coverage']['violations'], 1)
        self.assertFalse(data['coverage']['invalid_lines_exact'])
        self.assertIsNone(data['coverage']['examined_lines'])

    def test_timing_physical_lf_lines_and_unterminated_final_record_are_exact(self) -> None:
        selected = self.write(self.corpus([self.span(('a', (0, 10000)))]))
        selected.write_bytes(selected.read_bytes().rstrip(b'\n'))
        data = self.analyze([selected])
        self.assertEqual(data['coverage']['examined_lines'], 3)
        self.assertEqual(data['coverage']['invalid_lines'], 0)
        self.assertEqual(data['runs'][0]['metrics']['observed_union_ms'], '10000')
        selected.write_bytes(selected.read_bytes() + b'\n\n')
        data = self.analyze([selected])
        self.assertEqual(data['coverage']['examined_lines'], 4)
        self.assertEqual(data['coverage']['invalid_lines'], 1)
        selected.write_bytes(b'{"event":"step","note":"a\rb"}\n')
        self.assertEqual(self.analyze([selected])['coverage']['examined_lines'], 1)

    def test_timing_snapshot_mutation_or_inventory_change_invalidates_coverage(self) -> None:
        selected = self.write(self.corpus([]))
        for body in ['printf "x" >> "$ORCHESTRAIL_LOG_ROOT"/runs/*',
                     'touch "$ORCHESTRAIL_LOG_ROOT/runs/injected.jsonl"']:
            with self.subTest(body=body):
                self.lint_shim(body + '\nprintf "%s\\n" ' + shlex.quote(compact(
                    dict(kind='summary', status='ok', files=1, lines=2, invalid_lines=0, violations=0))))
                self.unavailable(self.analyze([selected]))

    def test_timing_snapshot_is_private_byte_exact_and_cleaned_after_lint(self) -> None:
        selected = self.write(self.corpus([self.span(('a', (0, 10000)), opaque=9007199254740991)]))
        trace = self.root / 'snapshot-path'
        real = self.helper.with_name('real-log-step.sh')
        body = 'snapshot=("$ORCHESTRAIL_LOG_ROOT"/runs/*)\n' + \
               'stat -c "%a" "$ORCHESTRAIL_LOG_ROOT" "${snapshot[0]}" > "$TIMING_MODES"\n' + \
               'cmp "${snapshot[0]}" "$TIMING_ORIGINAL" || exit 1\n' + \
               'printf "%s" "$ORCHESTRAIL_LOG_ROOT" > "$TIMING_TRACE"\n' + \
               'exec /bin/bash ' + shlex.quote(str(real)) + ' "$@"'
        self.lint_shim(body)
        self.env.update(TIMING_TRACE=str(trace), TIMING_ORIGINAL=str(selected), TIMING_MODES=str(self.root / 'modes'))
        data = self.analyze([selected])
        self.assertEqual(data['coverage']['lint_status'], 'ok')
        self.assertEqual((self.root / 'modes').read_text().splitlines(), ['700', '600'])
        self.assertFalse(Path(trace.read_text()).exists())

    def test_timing_contract_export_must_be_usable_and_fetched_once(self) -> None:
        selected = self.write(self.corpus([self.span(('good', (0, 10000)))]))
        real = self.helper.with_name('real-log-step.sh')
        self.helper.rename(real)
        trace = self.root / 'contract-calls'
        self.helper.write_text('#!/bin/bash\nif [ "${1:-}" = contract ]; then\n'
                               'printf x >> "$TIMING_CONTRACT_TRACE"\nfi\nexec /bin/bash ' + shlex.quote(str(real)) + ' "$@"\n')
        self.env['TIMING_CONTRACT_TRACE'] = str(trace)
        data = self.analyze([selected])
        self.assertEqual(data['coverage']['lint_status'], 'ok')
        self.assertEqual(trace.read_text(), 'x')
        self.helper.write_text('#!/bin/bash\nif [ "${1:-}" = contract ]; then printf "hook.required=bad\\n"; exit 0; fi\n'
                               'exec /bin/bash ' + shlex.quote(str(real)) + ' "$@"\n')
        self.unavailable(self.analyze([selected]))

    def test_timing_retro_docs_preserve_loader_and_describe_honest_measures(self) -> None:
        retro = (self.checkout / 'workflows/retro.md').read_text()
        for phrase in ('run-log-timing.sh', 'inclusive_work_span_ms', 'exclusive', 'waiting', 'CPU', 'approximate; '):
            self.assertIn(phrase, retro)
        for filename in ('docs/USAGE.md', 'scripts/README.md'):
            self.assertIn('run-log-timing.sh', (SOURCE / filename).read_text())
        self.assertTrue((self.checkout / 'scripts/run-log-timing.py').is_file())

    def test_timing_python_and_introduced_fixtures_have_complete_annotations(self) -> None:
        engine = SOURCE / 'scripts/run-log-timing.py'
        self.assertTrue(engine.is_file(), 'source-only typed timing engine is required')
        blocks = [engine.read_text(), self.python_block(SOURCE / 'tests/log-step-hook.sh', 'PY'),
                  self.python_block(SOURCE / 'scripts/validate-contracts.sh', 'PYCORRELATED'),
                  self.python_block(SOURCE / 'tests/hook-timing.sh', 'PY')]
        exceptions = {'call': (4, 30), 'dispatch': (6, 30), 'transcript': (4, 30), 'payload': (6, 30),
                      'accepted': (4, 30),
                      'test_hook_corrupted_frozen_payload_or_receipt_never_changes_run_attribution': (3, 36)}
        for block in blocks:
            tree = ast.parse(block)
            self.assert_python_function_limits(tree, exceptions if block in blocks[1:3] else {})
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.assertIsNotNone(node.returns, node.name)
                    parameters = (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
                                  node.args.vararg, node.args.kwarg)
                    for parameter in parameters:
                        if parameter is not None and parameter.arg not in ('self', 'cls'):
                            self.assertIsNotNone(parameter.annotation, node.name + ':' + parameter.arg)
        adapter = ast.parse(blocks[1])
        contract = next(node for node in adapter.body if isinstance(node, ast.ClassDef))
        self.assertEqual(len([node for node in contract.body if isinstance(node, ast.AnnAssign)]), 11)

    def assert_python_function_limits(self, tree: ast.AST, exceptions: dict[str, tuple[int, int]]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                maximum_parameters, maximum_lines = exceptions.get(node.name, (3, 30))
                parameters = (len(node.args.posonlyargs) + len(node.args.args) + len(node.args.kwonlyargs)
                              + bool(node.args.vararg) + bool(node.args.kwarg))
                self.assertLessEqual(parameters, maximum_parameters, node.name)
                self.assertLessEqual(node.end_lineno - node.lineno + 1, maximum_lines, node.name)
            if isinstance(node, ast.ClassDef):
                self.assertFalse(any(isinstance(member, ast.Assign) for member in node.body), node.name)
            if isinstance(node, ast.Name):
                self.assertNotEqual(node.id, 'Any', 'scoped fixture and timing code need concrete types')

    def python_block(self, path: Path, tag: str) -> str:
        return path.read_text().split("<<'" + tag + "'\n", 1)[1].split('\n' + tag, 1)[0]

    def public(self, relative: str, args: list[str]) -> str:
        result = self.command((self.checkout / relative, args))
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def envelope(self, run: str, boundary: str = 'subagent') -> tuple[Record, str]:
        actor = self.env['CLAUDE_CODE_SESSION_ID'] if boundary == 'session' else 'worker-' + uuid.uuid4().hex
        line = self.public('hooks/log-step-hook.sh', ['dispatch', '--run', run, '--agent-id', actor,
                           '--boundary', boundary, '--expected-skill', 'pae-tests'])
        self.assertTrue(line.startswith('ORCHESTRAIL_DISPATCH_V1 '))
        return json.loads(line.split(' ', 1)[1]), line

    def native(self, dispatch: tuple[Record, str], boundary: str = 'subagent') -> Record:
        identity, line = dispatch
        transcript = self.root / ('native-' + uuid.uuid4().hex + '.jsonl')
        transcript.write_text(compact(dict(type='user', message=dict(role='user', content=line))) + '\n' +
                              compact(dict(type='assistant', message=dict(role='assistant', content=[dict(
                                  type='tool_use', id='tool-'+uuid.uuid4().hex, name='Skill', input=dict(skill='pae-tests'))]))) + '\n')
        payload = dict(hook_event_name='SubagentStop' if boundary == 'subagent' else 'Stop',
                       session_id=identity['session_id'], cwd=str(self.project), transcript_path=str(transcript),
                       last_assistant_message='ORCHESTRAIL_REPORT_V1 ' + compact(dict(identity, outcome='ok', tests='red')))
        if boundary == 'subagent':
            payload.update(agent_id='native-'+uuid.uuid4().hex, agent_transcript_path=str(transcript))
        return payload

    def deliver(self, payload: Record) -> None:
        result = self.command((self.checkout / 'hooks/log-step-hook.sh', []), payload=compact(payload))
        self.assertEqual(result.returncode, 0, result.stderr)

    def status(self, identity: Record) -> Record:
        return json.loads(self.public('hooks/log-step-hook.sh', ['status', '--checkpoint', identity['checkpoint_id']]))

    def test_timing_two_run_lifecycle_preserves_attribution_fallback_and_owned_settings(self) -> None:
        settings = self.prepare_lifecycle()
        runs = [self.public('scripts/log-step.sh', ['run-start', '--pipeline', 'phase-execution']) for _ in range(2)]
        first, line_a = self.envelope(runs[0])
        second, line_b = self.envelope(runs[1], 'session')
        fallback, _ = self.envelope(runs[0])
        payload_a, payload_b = self.native((first, line_a)), self.native((second, line_b), 'session')
        self.deliver(payload_b)
        self.deliver(payload_a)
        self.deliver(payload_a)
        self.assertEqual(self.status(first)['state'], 'accepted')
        self.assertEqual(self.status(second)['state'], 'accepted')
        self.public('hooks/log-step-hook.sh', ['fallback', '--checkpoint', fallback['checkpoint_id'], '--step', 'pae-tests', '--outcome', 'ok'])
        self.assertEqual(self.status(fallback)['state'], 'fallback-attempted')
        paths = self.close_runs(runs)
        data = self.analyze(paths)
        self.assertEqual(len(data['runs']), 2)
        self.assertEqual([run['run_id'] for run in data['runs']], runs)
        self.assertEqual([len(run['spans']) for run in data['runs']], [1, 1])
        self.assertEqual([run['approximate'] for run in data['runs']], [True, False])
        self.assertEqual(json.loads(self.public('scripts/install-hooks.sh', ['uninstall']))['status'], 'uninstalled')
        self.assert_preserved_settings(settings)

    def prepare_lifecycle(self) -> Path:
        registry = Path(self.env['XDG_CONFIG_HOME']) / 'orchestrail/projects'
        registry.unlink()
        for _ in range(2):
            result = self.command((self.checkout / 'scripts/setup-new-project.sh', []), payload='2\n')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(registry.read_text().splitlines(), [str(self.project.resolve())])
        settings = Path(self.env['HOME']) / '.claude/settings.json'
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(compact(dict(custom='preserved', hooks={'UserPromptSubmit': []})))
        installed = json.loads(self.public('scripts/install-hooks.sh', ['install']))
        self.assertEqual(installed['status'], 'installed')
        self.assertEqual(json.loads(self.public('scripts/install-hooks.sh', ['install']))['status'], 'installed')
        return settings

    def close_runs(self, runs: list[str]) -> list[Path]:
        paths = [Path(self.public('scripts/log-step.sh', ['path', '--run', run])) for run in runs]
        for run, path in zip(runs, paths):
            self.public('scripts/log-step.sh', ['run-end', '--run', run, '--outcome', 'completed'])
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertTrue(all(row['run_id'] == run for row in rows))
            self.assertEqual(len([row for row in rows if row.get('timing_source') == 'hook']), 1)
        return paths

    def assert_preserved_settings(self, settings: Path) -> None:
        actual = json.loads(settings.read_text())
        self.assertEqual(actual['custom'], 'preserved')
        self.assertEqual(actual['hooks']['UserPromptSubmit'], [])
        self.assertFalse(actual['hooks'].get('Stop'))
        self.assertFalse(actual['hooks'].get('SubagentStop'))


selected = sys.argv[2:]
names = selected or unittest.defaultTestLoader.getTestCaseNames(HookTiming)
suite = unittest.TestSuite(HookTiming(name) for name in names)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
PY
