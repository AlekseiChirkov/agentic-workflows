"""Read-only exact interval analysis over an explicit, verified producer snapshot."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import NoReturn, TypeAlias, cast

JsonValue: TypeAlias = 'str | Decimal | bool | None | list[JsonValue] | DecodedObject'
Output: TypeAlias = dict[str, object]
Interval: TypeAlias = tuple[int, int]
Key: TypeAlias = tuple[str, str]
Actor: TypeAlias = tuple[str, str]
Diagnostic: TypeAlias = dict[str, str | int]


@dataclass(frozen=True)
class DecodedObject:
    values: dict[str, JsonValue]
    duplicates: frozenset[str]


@dataclass(frozen=True)
class SelectedFile:
    original: Path
    snapshot: Path
    payload: bytes


@dataclass(frozen=True)
class Row:
    number: int
    record: DecodedObject | None
    eligible: bool


@dataclass(frozen=True)
class Contract:
    identity: re.Pattern[str]
    correlation_fields: frozenset[str]
    maximum: int


@dataclass(frozen=True)
class LintCoverage:
    status: str
    excluded: frozenset[tuple[str, int]]
    violations: int
    reason: str | None


@dataclass(frozen=True)
class Run:
    selected: SelectedFile
    identity: str | None
    rows: list[Row]
    diagnostics: list[Diagnostic] = field(default_factory=list)


@dataclass(frozen=True)
class Boundaries:
    metadata: dict[str, JsonValue]
    interval: Interval


@dataclass(frozen=True)
class Span:
    key: Key
    actor: Actor
    step: str
    kind: str
    parent: str | None
    interval: Interval
    source: str
    boundary: str


@dataclass
class Checkpoint:
    key: Key
    rows: list[Row] = field(default_factory=list)
    parents: set[Key] = field(default_factory=set)
    span: Span | None = None
    invalid: bool = False


@dataclass(frozen=True)
class Graph:
    checkpoints: dict[Key, Checkpoint]
    opaque: bool


@dataclass(frozen=True)
class TimingFailure(Exception):
    code: str


def decode_object(pairs: list[tuple[str, JsonValue]]) -> DecodedObject:
    values: dict[str, JsonValue] = {}
    duplicates: set[str] = set()
    for name, value in pairs:
        if name in values:
            duplicates.add(name)
        values[name] = value
    return DecodedObject(values, frozenset(duplicates))


def decode_record(payload: bytes) -> DecodedObject | None:
    try:
        value = json.loads(payload.decode('utf-8'), parse_int=Decimal, parse_float=Decimal,
                           parse_constant=Decimal, object_pairs_hook=decode_object)
        return value if isinstance(value, DecodedObject) else None
    except (ValueError, UnicodeError, RecursionError):
        return None


def decimal_key(value: Decimal) -> tuple[object, ...]:
    if not value.is_finite():
        raise TimingFailure('nonfinite-json')
    sign, digits, exponent = value.as_tuple()
    trimmed = list(digits)
    while trimmed and trimmed[0] == 0:
        trimmed.pop(0)
    if not trimmed:
        return ('number', 0)
    scale = cast(int, exponent)
    while trimmed[-1] == 0:
        trimmed.pop()
        scale += 1
    return ('number', sign, tuple(trimmed), scale)


def equality_key(value: JsonValue) -> tuple[object, ...]:
    if isinstance(value, Decimal):
        return decimal_key(value)
    if isinstance(value, DecodedObject):
        return ('object', tuple((key, equality_key(item)) for key, item in sorted(value.values.items())),
                tuple(sorted(value.duplicates)))
    if isinstance(value, list):
        return ('array', tuple(equality_key(item) for item in value))
    return (type(value).__name__, value)


def duplicate_diagnostic(rows: list[Row], boundary: bool = False) -> Diagnostic:
    result: Diagnostic = dict(code='duplicate-boundary' if boundary else 'duplicate-checkpoint', copies=len(rows))
    fields = {'seq': 'sequence_variants', 'ts': 'timestamp_variants'}
    if not boundary:
        fields['ts_ms'] = 'clock_variants'
    for name, label in fields.items():
        variants = {equality_key(DecodedObject({name: row.record.values[name]} if name in row.record.values else {},
                                              frozenset())) for row in rows if row.record is not None}
        result[label] = len(variants)
    return result


def normalized_row(row: Row, boundary: bool = False) -> tuple[object, ...]:
    assert row.record is not None
    ignored = {'seq', 'ts'} if boundary else {'seq', 'ts', 'ts_ms'}
    values = {key: value for key, value in row.record.values.items() if key not in ignored}
    if not boundary:
        values.setdefault('span_kind', 'work')
    return equality_key(DecodedObject(values, row.record.duplicates))


def integer(value: JsonValue, maximum: int) -> int | None:
    if not isinstance(value, Decimal) or not value.is_finite():
        return None
    if value < 0 or value > maximum or value != value.to_integral_value():
        return None
    return int(value)


def physical_lines(payload: bytes) -> list[bytes]:
    if not payload:
        return []
    parts = payload.split(b'\n')
    return parts[:-1] if parts[-1] == b'' else parts


def select_paths(arguments: list[str]) -> list[Path]:
    if arguments[:1] == ['--']:
        arguments = arguments[1:]
    elif any(argument.startswith('-') for argument in arguments):
        raise TimingFailure('invalid-arguments')
    if not arguments:
        raise TimingFailure('missing-inputs')
    selected: list[Path] = []
    for argument in arguments:
        path = Path(argument).resolve(strict=True)
        if not path.is_file():
            raise TimingFailure('unreadable-input')
        if path not in selected:
            selected.append(path)
    return selected


def copy_files(paths: list[Path], root: Path) -> list[SelectedFile]:
    runs = root / 'runs'
    runs.mkdir(mode=0o700)
    selected: list[SelectedFile] = []
    for index, original in enumerate(paths):
        payload = original.read_bytes()
        snapshot = runs / f'{index:08d}.jsonl'
        descriptor = os.open(snapshot, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(payload)
        selected.append(SelectedFile(original, snapshot, payload))
    return selected


def inventory(root: Path) -> dict[str, tuple[int, bytes | None]]:
    entries: dict[str, tuple[int, bytes | None]] = {}
    for path in (root, *root.rglob('*')):
        mode = path.lstat().st_mode
        entries[str(path.relative_to(root))] = (mode, path.read_bytes() if stat.S_ISREG(mode) else None)
    return entries


def invoke_producer(helper: Path, arguments: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ, ORCHESTRAIL_LOG_ROOT=str(root), ORCHESTRAIL_HOME=str(helper.parent.parent))
    return subprocess.run(['/bin/bash', str(helper), *arguments], env=environment, text=True,
                          capture_output=True, timeout=60)


def read_contract(helper: Path, root: Path) -> Contract:
    response = invoke_producer(helper, ['contract'], root)
    values: dict[str, str] = {}
    for line in response.stdout.splitlines():
        name, separator, value = line.partition('=')
        if not separator or name in values:
            raise TimingFailure('invalid-contract')
        values[name] = value
    required = values.get('hook.required', '').split()
    maximum = values.get('count.maximum', '')
    if (response.returncode != 0 or not {'session_id', 'agent_id', 'checkpoint_id', 'span_start_ms', 'span_end_ms',
                 'timing_source', 'boundary'}.issubset(required)
            or len(required) != len(set(required)) or not re.fullmatch('[1-9][0-9]*', maximum)):
        raise TimingFailure('invalid-contract')
    try:
        pattern = re.compile(values['hook.identity_pattern'])
    except (KeyError, re.error) as error:
        raise TimingFailure('invalid-contract') from error
    if not values['hook.identity_pattern'] or pattern.fullmatch(''):
        raise TimingFailure('invalid-contract')
    return Contract(pattern, frozenset([*required, 'parent_checkpoint_id', 'span_kind']), int(maximum))


def control(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def violation_key(value: Output, files: dict[str, int]) -> tuple[str, int] | None:
    filename, number = value.get('file'), value.get('line')
    if not isinstance(filename, str) or filename not in files or not control(number):
        return None
    if not 1 <= cast(int, number) <= files[filename]:
        return None
    if any(not isinstance(value.get(name), str) or not value[name] for name in ('field', 'code')):
        return None
    return filename, cast(int, number)


def diagnostic_object(pairs: list[tuple[str, object]]) -> Output:
    values: Output = {}
    for name, value in pairs:
        if name in values:
            raise ValueError('duplicate diagnostic field')
        values[name] = value
    return values


def reject_constant(value: str) -> NoReturn:
    raise ValueError('nonfinite diagnostic number')


def parse_diagnostics(payload: str) -> tuple[list[Output], bool]:
    records: list[Output] = []
    malformed = False
    lines = payload.split('\n')
    if lines[-1] == '':
        lines.pop()
    for line in lines:
        try:
            value = json.loads(line, object_pairs_hook=diagnostic_object, parse_constant=reject_constant)
            if isinstance(value, dict):
                records.append(value)
            else:
                malformed = True
        except (ValueError, RecursionError):
            malformed = True
    return records, malformed or not records


def summary_matches(summary: Output, counts: tuple[int, int], violations: tuple[int, int]) -> bool:
    controls = ('files', 'lines', 'violations', 'invalid_lines')
    if any(not control(summary.get(name)) for name in controls):
        return False
    if (summary['violations'], summary['invalid_lines']) != violations or summary['invalid_lines'] > summary['lines']:
        return False
    if summary.get('status') == 'ok':
        return (summary['files'], summary['lines']) == counts
    return (summary.get('status') in ('partial', 'unavailable') and cast(int, summary['files']) <= counts[0]
            and cast(int, summary['lines']) <= counts[1])


def verify_lint(response: subprocess.CompletedProcess[str], selected: list[SelectedFile]) -> LintCoverage:
    files = {str(item.snapshot): len(physical_lines(item.payload)) for item in selected}
    records, malformed = parse_diagnostics(response.stdout)
    excluded: set[tuple[str, int]] = set()
    violations = 0
    for diagnostic in records or []:
        if diagnostic.get('kind') == 'violation':
            key = violation_key(diagnostic, files)
            if key is None:
                malformed = True
            else:
                excluded.add(key)
                violations += 1
        elif diagnostic.get('kind') != 'summary':
            malformed = True
    summaries = [value for value in records or [] if value.get('kind') == 'summary']
    if (len(summaries) != 1 or not records or records[-1].get('kind') != 'summary'
            or response.returncode != 0):
        malformed = True
    if not malformed:
        malformed = not summary_matches(summaries[0], (len(files), sum(files.values())), (violations, len(excluded)))
    status = 'unavailable' if malformed else cast(str, summaries[0]['status'])
    return LintCoverage(status, frozenset(excluded), violations, None if status == 'ok' else 'unverified-lint')


def coverage_output(selected: list[SelectedFile], coverage: LintCoverage) -> Output:
    verified = coverage.status == 'ok'
    return dict(lint_status=coverage.status, selected_files=len(selected),
                examined_lines=sum(len(physical_lines(item.payload)) for item in selected) if verified else None,
                invalid_lines=len(coverage.excluded), violations=coverage.violations, invalid_lines_exact=verified)


def build_run(selected: SelectedFile, coverage: LintCoverage) -> Run:
    rows: list[Row] = []
    for number, payload in enumerate(physical_lines(selected.payload), 1):
        record = decode_record(payload)
        eligible = (str(selected.snapshot), number) not in coverage.excluded
        rows.append(Row(number, record, eligible and record is not None and not record.duplicates))
    identities = {row.record.values['run_id'] for row in rows if row.record is not None
                  and isinstance(row.record.values.get('run_id'), str) and row.record.values['run_id']}
    return Run(selected, cast(str, next(iter(identities))) if len(identities) == 1 else None, rows)


def boundary_candidate(row: Row, contract: Contract) -> bool:
    if not row.eligible or row.record is None:
        return False
    if integer(row.record.values.get('ts_ms'), contract.maximum) is None:
        return False
    return all(name not in row.record.values or isinstance(row.record.values[name], str)
               for name in ('pipeline', 'project', 'task', 'flow'))


def resolve_boundary(run: Run, event: str, contract: Contract) -> Row | None:
    candidates = [row for row in run.rows if row.record is not None and row.record.values.get('event') == event]
    if not candidates or any(not boundary_candidate(row, contract) for row in candidates):
        run.diagnostics.append(dict(code='unusable-boundary', event=event))
        return None
    try:
        keys = {normalized_row(row, True) for row in candidates}
    except TimingFailure:
        keys = set()
    if len(keys) != 1:
        run.diagnostics.append(dict(code='conflicting-boundary', event=event))
        return None
    if len(candidates) > 1:
        run.diagnostics.append(dict(duplicate_diagnostic(candidates, True), event=event))
    return candidates[0]


def same_metadata(values: dict[str, JsonValue], metadata: dict[str, JsonValue]) -> bool:
    for name in ('pipeline', 'project', 'task', 'flow'):
        if (name in values) != (name in metadata):
            return False
        if name in values and (not isinstance(values[name], str) or values[name] != metadata[name]):
            return False
    return True


def resolve_boundaries(run: Run, contract: Contract) -> Boundaries | None:
    if any(row.record is not None and 'event' in row.record.duplicates for row in run.rows):
        run.diagnostics.append(dict(code='ambiguous-boundary-kind'))
        return None
    start = resolve_boundary(run, 'run-start', contract)
    end = resolve_boundary(run, 'run-end', contract)
    if start is None or end is None:
        return None
    assert start.record is not None and end.record is not None
    metadata = start.record.values
    interval = (cast(int, integer(metadata.get('ts_ms'), contract.maximum)),
                cast(int, integer(end.record.values.get('ts_ms'), contract.maximum)))
    if interval[1] < interval[0] or not same_metadata(end.record.values, metadata):
        run.diagnostics.append(dict(code='invalid-run-boundaries'))
        return None
    return Boundaries(metadata, interval)


def identity_value(value: JsonValue, contract: Contract) -> str | None:
    return value if isinstance(value, str) and contract.identity.fullmatch(value) else None


def evidence_key(row: Row, run: Run, contract: Contract) -> Key | None:
    assert row.record is not None
    values = row.record.values
    identity_fields = {'run_id', 'session_id', 'checkpoint_id', 'parent_checkpoint_id'}
    if row.record.duplicates & identity_fields or values.get('run_id') != run.identity:
        return None
    session = identity_value(values.get('session_id'), contract)
    checkpoint = identity_value(values.get('checkpoint_id'), contract)
    if session is None or checkpoint is None:
        return None
    if 'parent_checkpoint_id' in values and identity_value(values['parent_checkpoint_id'], contract) is None:
        return None
    return session, checkpoint


def collect_graph(run: Run, contract: Contract) -> Graph:
    checkpoints: dict[Key, Checkpoint] = {}
    opaque = False
    for row in run.rows:
        if row.record is None:
            opaque = True
            continue
        values = row.record.values
        if not contract.correlation_fields.intersection(values):
            continue
        key = evidence_key(row, run, contract)
        if key is None:
            opaque = True
            continue
        checkpoint = checkpoints.setdefault(key, Checkpoint(key))
        checkpoint.rows.append(row)
        parent = values.get('parent_checkpoint_id')
        if isinstance(parent, str):
            checkpoint.parents.add((key[0], parent))
        if not row.eligible or values.get('event') != 'step':
            checkpoint.invalid = True
    if opaque:
        run.diagnostics.append(dict(code='unverified-exclusive-graph'))
    return Graph(checkpoints, opaque)


def make_span(row: Row, boundaries: Boundaries, contract: Contract) -> Span | None:
    assert row.record is not None
    values = row.record.values
    start = integer(values.get('span_start_ms'), contract.maximum)
    end = integer(values.get('span_end_ms'), contract.maximum)
    if start is None or end is None or not boundaries.interval[0] <= start <= end <= boundaries.interval[1]:
        return None
    if not same_metadata(values, boundaries.metadata):
        return None
    session, checkpoint = cast(str, values['session_id']), cast(str, values['checkpoint_id'])
    return Span((session, checkpoint), (session, cast(str, values['agent_id'])), cast(str, values['step']),
                cast(str, values.get('span_kind', 'work')), cast(str | None, values.get('parent_checkpoint_id')),
                (start, end), cast(str, values['timing_source']), cast(str, values['boundary']))


def resolve_checkpoint(checkpoint: Checkpoint, boundaries: Boundaries, contract: Contract) -> None:
    if checkpoint.invalid:
        return
    try:
        keys = {normalized_row(row) for row in checkpoint.rows}
    except TimingFailure:
        checkpoint.invalid = True
        return
    if len(keys) != 1:
        checkpoint.invalid = True
        return
    checkpoint.span = make_span(checkpoint.rows[0], boundaries, contract)
    checkpoint.invalid = checkpoint.span is None


def resolve_spans(run: Run, graph: Graph, context: tuple[Boundaries, Contract]) -> list[Span]:
    boundaries, contract = context
    spans: list[Span] = []
    for checkpoint in graph.checkpoints.values():
        resolve_checkpoint(checkpoint, boundaries, contract)
        if checkpoint.invalid:
            run.diagnostics.append(dict(code='excluded-checkpoint', session_id=checkpoint.key[0],
                                        checkpoint_id=checkpoint.key[1]))
        elif checkpoint.span is not None:
            spans.append(checkpoint.span)
            if len(checkpoint.rows) > 1:
                run.diagnostics.append(dict(duplicate_diagnostic(checkpoint.rows), checkpoint_id=checkpoint.key[1],
                                            session_id=checkpoint.key[0]))
    return spans


def adjacency(graph: Graph) -> dict[Key, set[Key]]:
    edges: dict[Key, set[Key]] = defaultdict(set)
    for key, checkpoint in graph.checkpoints.items():
        edges[key]
        for parent in checkpoint.parents:
            edges[key].add(parent)
            edges[parent].add(key)
    return edges


def components(edges: dict[Key, set[Key]]) -> list[set[Key]]:
    remaining = set(edges)
    result: list[set[Key]] = []
    while remaining:
        pending, component = [min(remaining)], set()
        while pending:
            key = pending.pop()
            if key in component:
                continue
            component.add(key)
            pending.extend(edges[key] - component)
        remaining.difference_update(component)
        result.append(component)
    return result


def invalid_relationship(key: Key, graph: Graph) -> bool:
    checkpoint = graph.checkpoints.get(key)
    if checkpoint is None or checkpoint.invalid or checkpoint.span is None:
        return True
    child = checkpoint.span
    for parent_key in checkpoint.parents:
        parent = graph.checkpoints.get(parent_key)
        if parent is None or parent.span is None:
            return True
        if not parent.span.interval[0] <= child.interval[0] <= child.interval[1] <= parent.span.interval[1]:
            return True
    return len(checkpoint.parents) > 1


def cyclic(component: set[Key], graph: Graph) -> bool:
    counts = {key: len(graph.checkpoints[key].parents) if key in graph.checkpoints else 0 for key in component}
    children: dict[Key, list[Key]] = defaultdict(list)
    for key in component:
        for parent in graph.checkpoints[key].parents if key in graph.checkpoints else ():
            children[parent].append(key)
    ready = deque(key for key, count in counts.items() if count == 0)
    visited = 0
    while ready:
        visited += 1
        for child in children[ready.popleft()]:
            counts[child] -= 1
            if counts[child] == 0:
                ready.append(child)
    return visited != len(component)


def quarantined(graph: Graph) -> set[Key]:
    bad: set[Key] = set()
    for component in components(adjacency(graph)):
        if any(invalid_relationship(key, graph) for key in component) or cyclic(component, graph):
            bad.update(component)
    return bad


def merge(intervals: list[Interval]) -> list[Interval]:
    result: list[Interval] = []
    for start, end in sorted(intervals):
        if start == end:
            continue
        if result and start <= result[-1][1]:
            result[-1] = result[-1][0], max(end, result[-1][1])
        else:
            result.append((start, end))
    return result


def subtract(interval: Interval, children: list[Interval]) -> list[Interval]:
    cursor, end = interval
    result: list[Interval] = []
    for start, stop in merge(children):
        if cursor < start:
            result.append((cursor, min(start, end)))
        cursor = max(cursor, stop)
    if cursor < end:
        result.append((cursor, end))
    return result


def measure(intervals: list[Interval]) -> int:
    return sum(end - start for start, end in intervals)


def overlap(intervals: list[Interval]) -> int:
    events: dict[int, int] = defaultdict(int)
    for start, end in intervals:
        events[start] += 1
        events[end] -= 1
    active, total, previous = 0, 0, 0
    for point, change in sorted(events.items()):
        if active >= 2:
            total += point - previous
        active += change
        previous = point
    return total


def exclusive_segments(graph: Graph, spans: list[Span]) -> dict[Key, list[Interval] | None]:
    bad = quarantined(graph)
    children: dict[Key, list[Interval]] = defaultdict(list)
    for span in spans:
        if span.parent is not None:
            children[(span.key[0], span.parent)].append(span.interval)
    return {span.key: None if graph.opaque or span.key in bad else subtract(span.interval, children[span.key])
            for span in spans}


def endpoints(intervals: list[Interval]) -> list[list[str]]:
    return [[str(start), str(end)] for start, end in intervals]


def ratio(numerator: int | None, denominator: int) -> Output | None:
    if numerator is None or denominator == 0:
        return None
    return dict(numerator_ms=str(numerator), denominator_ms=str(denominator))


def active_intervals(spans: list[Span], segments: dict[Key, list[Interval] | None]) -> dict[Actor, list[Interval]]:
    actors: dict[Actor, list[Interval]] = defaultdict(list)
    for span in spans:
        if span.kind == 'work' and segments[span.key] is not None:
            actors[span.actor].extend(cast(list[Interval], segments[span.key]))
    return actors


def exclusive_available(spans: list[Span], segments: dict[Key, list[Interval] | None]) -> bool:
    work = [span for span in spans if span.kind == 'work']
    candidates = work if work else spans
    return any(segments[span.key] is not None for span in candidates)


def metric_output(boundaries: Boundaries, spans: list[Span], segments: dict[Key, list[Interval] | None]) -> Output:
    work = [span.interval for span in spans if span.kind == 'work']
    waiting = [span.interval for span in spans if span.kind == 'waiting']
    observed = [span.interval for span in spans]
    wall = boundaries.interval[1] - boundaries.interval[0]
    actors = active_intervals(spans, segments)
    exclusive = [interval for values in actors.values() for interval in values]
    available = exclusive_available(spans, segments)
    active = measure(merge(exclusive)) if available else None
    parallel = overlap([interval for values in actors.values() for interval in merge(values)]) if available else None
    values: dict[str, int | None] = dict(wall_ms=wall, inclusive_work_span_ms=measure(work),
        work_union_ms=measure(merge(work)), observed_union_ms=measure(merge(observed)), exclusive_work_union_ms=active,
        excess_work_span_ms=measure(work) - measure(merge(work)), wall_overlap_ms=overlap(observed),
        parallel_worker_overlap_ms=parallel, inclusive_waiting_span_ms=measure(waiting), waiting_union_ms=measure(merge(waiting)))
    return {**{name: str(value) if value is not None else None for name, value in values.items()},
            'coverage_ratio': ratio(measure(merge(observed)), wall), 'active_work_coverage_ratio': ratio(active, wall),
            'gaps': endpoints(subtract(boundaries.interval, observed))}


def span_output(span: Span, segments: list[Interval] | None, run: Run) -> Output:
    return dict(run_id=run.identity, session_id=span.key[0], checkpoint_id=span.key[1], agent_id=span.actor[1],
                step=span.step, span_kind=span.kind, parent_checkpoint_id=span.parent, timing_source=span.source,
                boundary=span.boundary, span_start_ms=str(span.interval[0]), span_end_ms=str(span.interval[1]),
                inclusive_ms=str(span.interval[1] - span.interval[0]),
                exclusive_ms=None if segments is None else str(measure(segments)),
                exclusive_segments=None if segments is None else endpoints(segments))


def worker_output(run: Run, spans: list[Span], segments: dict[Key, list[Interval] | None]) -> list[Output]:
    grouped: dict[Actor, list[Span]] = defaultdict(list)
    for span in spans:
        if span.kind == 'work':
            grouped[span.actor].append(span)
    result: list[Output] = []
    for actor, observations in sorted(grouped.items()):
        unavailable = any(segments[span.key] is None for span in observations)
        intervals = [item for span in observations for item in segments[span.key] or []]
        has_overlap = measure(intervals) != measure(merge(intervals))
        if unavailable or has_overlap:
            run.diagnostics.append(dict(code='worker-exclusive-unavailable' if unavailable else 'same-actor-overlap',
                                        session_id=actor[0], agent_id=actor[1]))
        result.append(dict(session_id=actor[0], agent_id=actor[1],
                           exclusive_work_ms=None if unavailable or has_overlap else str(measure(intervals))))
    return result


def named_output(run: Run, spans: list[Span], segments: dict[Key, list[Interval] | None]) -> list[Output]:
    grouped: dict[str, list[Span]] = defaultdict(list)
    for span in spans:
        if span.kind == 'work' and span.step != 'unknown':
            grouped[span.step].append(span)
    result: list[Output] = []
    for name, observations in sorted(grouped.items()):
        unavailable = any(segments[span.key] is None for span in observations)
        if unavailable:
            run.diagnostics.append(dict(code='step-exclusive-unavailable', step=name))
        result.append(dict(step=name, inclusive_work_span_ms=str(sum(span.interval[1] - span.interval[0]
                           for span in observations)), exclusive_work_span_ms=None if unavailable else
                           str(sum(measure(segments[span.key] or []) for span in observations))))
    return result


def approximate(run: Run, contract: Contract) -> bool:
    for row in run.rows:
        if not row.eligible or row.record is None or row.record.values.get('event') != 'step':
            continue
        values = row.record.values
        note = values.get('note')
        if isinstance(note, str) and (note == 'approximate' or note.startswith('approximate; ')):
            return True
        if not contract.correlation_fields.intersection(values):
            return True
    return False


def has_legacy_steps(run: Run, contract: Contract) -> bool:
    return any(row.eligible and row.record is not None and row.record.values.get('event') == 'step'
               and not contract.correlation_fields.intersection(row.record.values) for row in run.rows)


def analyze_run(run: Run, contract: Contract, duplicate: bool) -> Output:
    result: Output = dict(file=str(run.selected.original), run_id=run.identity, status='unavailable',
                          approximate=approximate(run, contract), metrics=None, spans=[], workers=[], named_steps=[],
                          diagnostics=run.diagnostics)
    excluded = sum(not row.eligible for row in run.rows)
    if excluded:
        run.diagnostics.append(dict(code='excluded-lines', count=excluded))
    boundaries = resolve_boundaries(run, contract)
    if run.identity is None or duplicate or boundaries is None:
        run.diagnostics.append(dict(code='ambiguous-run-identity' if run.identity is None or duplicate else 'unavailable-run-time'))
        return result
    graph = collect_graph(run, contract)
    spans = resolve_spans(run, graph, (boundaries, contract))
    segments = exclusive_segments(graph, spans)
    if any(value is None for value in segments.values()):
        run.diagnostics.append(dict(code='quarantined-parent-component'))
    if has_legacy_steps(run, contract):
        run.diagnostics.append(dict(code='unmeasured-prompt-steps'))
    workers, named = worker_output(run, spans, segments), named_output(run, spans, segments)
    partial = (any(not row.eligible for row in run.rows) or graph.opaque or has_legacy_steps(run, contract)
               or any(checkpoint.invalid for checkpoint in graph.checkpoints.values())
               or any(value is None for value in segments.values()) or any(worker['exclusive_work_ms'] is None for worker in workers))
    result.update(status='partial' if partial else 'ok', metrics=metric_output(boundaries, spans, segments),
                  spans=[span_output(span, segments[span.key], run) for span in spans], workers=workers, named_steps=named)
    return result


def unavailable_output(code: str, selected_count: int | None = None) -> Output:
    return dict(schema_version=1, status='unavailable', runs=None, diagnostics=[dict(code=code)],
                coverage=dict(lint_status='unavailable', selected_files=selected_count, examined_lines=None,
                              invalid_lines=0, violations=0, invalid_lines_exact=False))


def analyze_snapshot(selected: list[SelectedFile], helper: Path, root: Path) -> Output:
    contract = read_contract(helper, root)
    before = inventory(root)
    coverage = verify_lint(invoke_producer(helper, ['lint', '--all'], root), selected)
    try:
        unchanged = inventory(root) == before
    except OSError:
        unchanged = False
    if not unchanged:
        coverage = LintCoverage('unavailable', coverage.excluded, coverage.violations, 'changed-snapshot')
    result: Output = dict(schema_version=1, status='unavailable', coverage=coverage_output(selected, coverage),
                          runs=None, diagnostics=[])
    if coverage.status != 'ok':
        result['diagnostics'] = [dict(code=coverage.reason or 'unverified-lint')]
        return result
    runs = [build_run(item, coverage) for item in selected]
    counts: dict[str | None, int] = defaultdict(int)
    for run in runs:
        counts[run.identity] += 1
    analyzed = [analyze_run(run, contract, counts[run.identity] > 1) for run in runs]
    result.update(status='partial' if any(run['status'] != 'ok' for run in analyzed) else 'ok', runs=analyzed)
    return result


def execute(arguments: list[str]) -> Output:
    paths = select_paths(arguments)
    helper = Path(__file__).resolve().with_name('log-step.sh')
    try:
        with tempfile.TemporaryDirectory(prefix='orchestrail timing ') as directory:
            root = Path(directory)
            return analyze_snapshot(copy_files(paths, root), helper, root)
    except TimingFailure as error:
        return unavailable_output(error.code, len(paths))
    except (OSError, ValueError, subprocess.SubprocessError, RecursionError):
        return unavailable_output('analysis-unavailable', len(paths))


def main() -> None:
    if sys.argv[1:] in (['-h'], ['--help']):
        print('Usage: bash scripts/run-log-timing.sh [--] FILE...')
        return
    try:
        result = execute(sys.argv[1:])
    except TimingFailure as error:
        result = unavailable_output(error.code)
    except (OSError, ValueError, subprocess.SubprocessError, RecursionError):
        result = unavailable_output('analysis-unavailable')
    print(json.dumps(result, sort_keys=True, separators=(',', ':'), ensure_ascii=True))


if __name__ == '__main__':
    main()
