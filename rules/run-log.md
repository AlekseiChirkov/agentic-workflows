---
trigger: always_on
---

# Run Log Contract

Every orchestrator pipeline writes a machine-readable record of what it did, step by step,
so the pipelines themselves can be improved from evidence instead of recollection. The log
is telemetry about **the process**, never a copy of the work product.

Consumed by `/retro`. Produced by `/spec-run`, `/phase-pipeline`, `/phase-discovery`,
`/phase-execution`, `/phase-validation`.

---

## The one rule that outranks the rest

**Logging never blocks, delays, or alters a pipeline.** If the helper is missing, the log
store is unwritable, or a call fails, the pipeline continues unchanged and says nothing
beyond one line in its final report. `scripts/log-step.sh` is written to exit `0` on every error
path for exactly this reason. A workflow must never stop, retry, or ask the user because a
log write failed, and must never let a logging concern change a decision it would otherwise
have made.

---

## Contract version

`contract_version`: optional string on `run-start`, read from the root `VERSION`
file beside the logging helper in the workflow source checkout. Record its current
numeric `major.minor.patch` value. If VERSION is absent, unreadable, empty, or malformed,
omit the field and continue logging. Older events without `contract_version` remain
valid; readers accept its absence. Other event fields keep their existing meaning.

## Where the log lives

```
$ORCHESTRAIL_LOG_ROOT            # if nonempty — used verbatim
<helper-directory>/logs/    # otherwise, relative to scripts/log-step.sh
  runs/
    <ISO-timestamp>-<pipeline>-<run-id>.jsonl   # append-only, one JSON object per line
    <ISO-timestamp>-<pipeline>-<run-id>.md      # human-readable digest, written at run-end
  .active/<run-id>                              # open-run metadata; removed at run-end
  .gitignore                                    # `*` — the store is never committed
```

The store is **central and cross-project**: runs from every repository land in one place,
because the question the log answers ("what should change in the workflows?") is only
answerable across projects. Set `ORCHESTRAIL_HOME` to the shared workflow checkout in every consuming environment
so all workflows resolve the same helper and default store. `ORCHESTRAIL_LOG_ROOT` can select
another shared store; never substitute the current consumer project directory.

The store is local telemetry. It is not committed, not synced by `scripts/sync.sh`, and not copied
into a project.

---

## How a pipeline logs

Three calls, all through `scripts/log-step.sh` via the shell. **Agents never hand-write a JSON
line** — the helper stamps the time and derives every duration from its own previous write.
A duration written by a model is a guess, and a guessed number in a metrics store is worse
than a missing one.

Resolve the helper from the configured `ORCHESTRAIL_HOME` checkout. If that variable is
unset or the helper is not executable, skip logging for the whole run and note that once
in the final report. Keep the resolved `LOG_HELPER` and `RUN_ID` for all three calls.

**1 — At the start of the pipeline, before its first step (`scripts/log-step.sh run-start`):**

```bash
LOG_HELPER="${ORCHESTRAIL_HOME:+$ORCHESTRAIL_HOME/scripts/log-step.sh}"
RUN_ID=""
if [ -x "$LOG_HELPER" ]; then
  RUN_ID=$("$LOG_HELPER" run-start \
  --pipeline phase-discovery \
  --project "$(pwd)" \
  --task .ai/tasks/todo/task-01-add-oauth \
  --spec .ai/specs/01-add-oauth.md \
  --flow full \
  --flags "--step-by-step") || RUN_ID=""
fi
```

Keep `RUN_ID` for the rest of the run. If the pipeline resumes in a later session, start a
new run — `/retro` correlates runs by `task`, so a resumed task reads as two runs of the
same task, which is itself a signal worth measuring.

**2 — Immediately after each step completes** (`scripts/log-step.sh step`), before moving to the next one:

```bash
[ -n "$RUN_ID" ] && "$LOG_HELPER" step --run "$RUN_ID" \
  --step pd-analyze --outcome ok \
  --decisions 3 --questions 2 --stops 1 \
  --note "approximate; resolved 3 ambiguities from principles" || true
```

Log the step **after it finishes**, whatever the outcome — a step that failed, blocked, or
was skipped is the most valuable line in the file. A step that ends the run still gets its
own `step` line before `run-end`.

**3 — When the pipeline stops, for any reason (`scripts/log-step.sh run-end`):**

```bash
[ -n "$RUN_ID" ] && "$LOG_HELPER" run-end --run "$RUN_ID" \
  --outcome stopped --note "escalated: two ADRs conflict" || true
```

This includes a planned stop. `/phase-discovery` completing normally is `--outcome
completed`; the batch gate in `/spec-run` handing control to the human is `--outcome
stopped`. A run left without `run-end` shows up in `scripts/log-step.sh active` and is counted by
`/retro` as an abandoned run — which is accurate, and deliberately visible.

---

## Workflow coverage and routing

Select coverage for each boundary independently. Mechanism support (`hooks: yes`),
the current installation result, and demonstrated checkpoint coverage are separate
facts. Read the harness capability declaration and current installation result;
unknown capability, `hooks: no`, unsupported payload/profile, unavailable installation,
or missing native session identity cannot establish a covered boundary. A supported
usable mechanism permits provisional dispatch, not a precision claim. Run-start and run-end remain prompt-driven.

Keep prompt instructions for every ordinary step and attach `--note approximate`
(or a note beginning `approximate; ` when adding a short clause). This includes
discovery, root work, arbitration and Arbiter decisions: all remain approximate.
Internal skills in GREEN and validation batches, single-session `/phase-*` steps,
pipeline overrides, batch gates, dry runs and synthetic subtask summaries also remain
approximate unless that exact boundary independently meets the native evidence
contract. Do not remove internal logging prompts because a generic Stop fired.
Session `unknown` coverage never counts as named workflow-step coverage.

Precisely observed named coverage requires the original dispatch in native user
input, a matching canonical final report, exactly one genuine native Skill invocation,
and a matching producer receipt. `expected_skill` is an assertion checked against
native evidence; it supplies no invocation evidence itself. A wrapper, repeated Skill
or multiple skills cannot establish one named interval. Never infer a skill or outcome
from prose, infer identity from active history, or supply model-written timestamps.

Before suppressing a prompt row, retain the original issued envelope and its complete
`run_id`, `session_id`, `agent_id`, `checkpoint_id` tuple. Query the adapter once with
`status --checkpoint ID` and match every tuple field and schema version to the retained
envelope. For accepted status, also require the receipt's `kind:"accepted"`, matching
four identity fields and positive integer sequence, as defined below. Exit zero and
ordinary fallback output never prove persistence. Apply this table to that boundary:

| Known boundary state | Workflow action |
|---|---|
| No envelope was ever issued | Write the ordinary step with `--note approximate`. |
| Unknown resume knowledge about whether an envelope existed | Omit the row and disclose uncertain coverage. Never assume no envelope. |
| `accepted` with a matching receipt | Suppress only the corresponding prompt row. |
| Matching `pending` | Invoke serialized fallback once using the retained checkpoint. |
| Matching `delivering` | Keep the frozen correlated payload route only; disclose uncertain acceptance. |
| Matching `fallback` or `fallback-attempted` | Make no second attempt; ordinary persistence remains unacknowledged. |
| Missing, malformed or wrong-tuple status | Use only serialized fallback for the retained checkpoint; if it cannot safely claim pending ownership, omit and disclose uncertainty. |
| Missing or unavailable private state | Omit and disclose uncertainty; never write an ordinary replacement. |

Once any envelope was issued, never call the ordinary producer directly for that
boundary. Serialized fallback is the adapter's ownership decision, not a workflow
guess based on missing status. Use its public command, with canonical result fields:

```bash
bash "$ORCHESTRAIL_HOME/hooks/log-step-hook.sh" status --checkpoint "$checkpoint_id"
bash "$ORCHESTRAIL_HOME/hooks/log-step-hook.sh" fallback --checkpoint "$checkpoint_id" \
  --step pae-tests --outcome ok --tests red
```

These are alternative actions selected by the table, not two unconditional calls.
Delivering retries belong to the native adapter and reuse its frozen payload only.
Never fabricate native input to retry a delivery, switch to ordinary logging after
delivery starts, or wait/poll for telemetry before proceeding with the workflow.
Report unavailable/uncertain coverage once without blocking work.

The existing `/spec-run` RED return is the named-step candidate in this release.
Its `pae-tests` row is distinct from the approximate synthetic subtask aggregate.
Provisional dispatch does not guarantee a RED return: test-level `none` leaves it
uncovered. GREEN combines two skills and validation combines three; neither batch,
nor its internal steps, acquires named precision from the RED marker. Preserve their
approximate prompts and never reuse that marker for a subsequent return.

The isolated `--hook-workflow-only` fixtures compose the public adapter and producer
and check these instructions. They demonstrate synthetic routing, not live model
compliance or live event firing.

## Field vocabulary

Values are case-sensitive. No trimming, case folding, or conversion occurs except
for the exact step aliases below. These canonical tables use JSON values: arrays
are sets, strings are exact values. `scripts/log-step.sh contract` exports the
shared runtime definitions consumed by writes and lint; contract validation compares
both directions, rejects duplicate rows and values, and checks prefix boundaries.

### Runtime vocabulary

| Runtime key | Canonical JSON value |
|---|---|
| `count.fields` | ["stops", "escalations", "decisions", "questions", "fix_tasks", "amendments", "files"] |
| `count.maximum` | "9007199254740991" |
| `hook.required` | ["session_id", "agent_id", "checkpoint_id", "span_start_ms", "span_end_ms", "timing_source", "boundary"] |
| `hook.identity_pattern` | "^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$" |
| `hook.timing_source` | ["hook"] |
| `hook.boundary` | ["session", "subagent"] |
| `hook.span_kind` | ["work", "waiting"] |
| `run-end.outcome` | ["completed", "stopped", "failed", "abandoned"] |
| `step.gate` | ["pass", "fail", "n-a", "needs-work", "ready"] |
| `step.outcome` | ["ok", "blocked", "failed", "skipped", "deferred"] |
| `step.promoted` | ["yes", "no"] |
| `step.synthetic` | ["batch-gate", "subtask", "dry-run"] |
| `step.tests` | ["red", "green", "n-a", "failed", "not-run", "pinned"] |

`step.outcome` is required; `step.gate`, `step.tests`, and `step.promoted` are optional
closed enums. `run-end.outcome` is required and uses its own enum; `completed` at run
end is never normalized to `ok`. `step.synthetic` lists the additional recognized
step names. Other names are derived at call time from the helper checkout's
`workflows/*.md`, selected through nonempty `ORCHESTRAIL_HOME`. Unknown nonempty
names are stored unchanged with one advisory warning; inaccessible workflows produce
one verification-unavailable warning. Lint does not enforce historical step names.

| Event | Required command arguments | Stored presence |
|---|---|---|
| `run-start` | `--pipeline` | Nonempty `flow`; omitted or empty `--flow` defaults to `unknown`. |
| `step` | `--run`, `--step`, `--outcome` | Nonempty inherited `flow`; required step and outcome. |
| `run-end` | `--run`, `--outcome` | Nonempty inherited `flow`; required end outcome. |

Flow is unrestricted nonempty text, not an enum; preserve its exact value across all
events. Optional enums and counts are omitted only when absent. Explicitly empty
enums or counts are invalid. Empty optional free-text fields are omitted.

Every supplied count named in `count.fields` uses exact CLI decimal syntax `0` or
`[1-9][0-9]*`, from zero through `count.maximum` inclusive. Reject signs, leading
zeros, fractions, exponent notation, whitespace, and larger values. A supplied zero
is a JSON number and must be stored. Omission means not measured; never fabricate a
zero or `unknown` for an unmeasured optional field. Lint checks mathematical JSON
integrality, so `1.0` and `1e0` are valid stored integers, unlike CLI arguments.
Stored `seq` and supplied `duration_s` share the nonnegative integer bound.

Free-text context retains its current meanings: `subtask` identifies the touched
subtask, `blocker` names an impediment, and `note` adds a short clause. Counts measure
human stops, escalations, autonomous decisions, questions, created fixes, amendments,
and written files, respectively.

### Legacy normalization

| Runtime key | Canonical JSON value |
|---|---|
| `alias.gate.NEEDS_WORK_EXACT` | "needs-work" |
| `alias.gate.NEEDS_WORK_PREFIX` | "^NEEDS WORK([[:space:]:-].*)$" |
| `alias.gate.PASS` | "pass" |
| `alias.gate.escalated` | "fail" |
| `alias.outcome.completed` | "ok" |
| `alias.outcome.implemented` | "ok" |
| `alias.outcome.needs-work` | "failed" |
| `alias.outcome.restarted` | "failed" |

Only step values normalize. Each outcome alias maps its exact suffix to the table's
value. Gate `PASS` and `escalated` also match exactly; `NEEDS_WORK_EXACT` denotes the
literal `NEEDS WORK`. `NEEDS_WORK_PREFIX` matches that literal followed by whitespace,
`:` or `-` and any text, mapping to `NEEDS_WORK_EXACT`'s value. It rejects
`NEEDS WORKING`, `NEEDS WORK_`, other lookalikes, and other case variants.

Preserve each normalized raw input byte-for-byte in the JSON string `note` as
`raw:<original value>`. Keep an existing note first, then append outcome provenance,
then gate provenance, separated by `; `. Canonical values add no fragment.
For example, outcome `completed`, gate `PASS`, and note `checked` store note
`checked; raw:completed; raw:PASS`. Diagnostics never echo arbitrary raw values.
Provenance remains subject to the privacy restrictions below.

## Validation and writes

Validate the complete argument set before opening files for writing or changing
sequence, timestamps, or active metadata. Unknown flags, missing operands, duplicate
flags, missing required arguments, invalid enums, counts, or unsafe run identifiers
reject the whole invocation. A flag cannot consume the next flag as its operand.
Run identifiers must be exactly eight lowercase hexadecimal characters, checked
before metadata path lookup. Every rejection produces exactly one single-line stderr
warning naming the field/argument and reason code, without the raw value.

Invalid starts create no active run or JSONL file. Invalid steps append nothing and
leave sequence, last accepted timestamp, and metadata unchanged; the next accepted
step uses the next consecutive sequence and measures from the last accepted event.
Invalid ends do not append, rewrite a digest, or remove active metadata; a later
valid close remains possible. Successful close removes active metadata only after
persisting the closing JSONL line; a digest failure warns without undoing that close.

All helper paths exit zero. Failed operations emit no success-shaped stdout.
`run-start` prints its run ID only after start persistence and usable metadata;
successful legacy `step` and `run-end` print nothing. Correlated steps use the
receipt contract below. Filesystem failures warn once and
remain non-blocking; transactional rollback of partial operating-system writes is
not required. Existing `path` and `active` behavior remains available.

## Correlated hook intervals

Use the ordinary `step` command with all fields in `hook.required` together:

```bash
bash "$ORCHESTRAIL_HOME/scripts/log-step.sh" step --run "$run_id" \
  --step "$skill" --outcome ok --session-id "$session_id" --agent-id "$agent_id" \
  --checkpoint-id "$checkpoint_id" --span-start-ms "$started_ms" --span-end-ms "$ended_ms" \
  --timing-source hook --boundary subagent
```

The CLI uses hyphens; stored JSON uses the underscore names in `hook.required`.
All identity strings must match `hook.identity_pattern` (1–128 ASCII letters,
digits, dots, underscores, colons or hyphens, starting with a letter or digit).
Any correlation field, including either optional field below, requires the entire
required set. The explicit run ID always selects active metadata; never select a
newest run or read historical events to discover attribution.

- `--span-start-ms` and `--span-end-ms` are executable clock stamps in Unix
  milliseconds, using the same canonical decimal syntax and inclusive bound as
  counts. End must be at least start; zero-length intervals are valid. The adapter
  stamps dispatch and completion; a model must never supply measured times.
- `--boundary session|subagent` names the observed boundary. `--step unknown` is
  permitted only for `session` with `agent_id` equal to `session_id`; the adapter
  must first establish that this session has one unambiguous active attribution.
- `--parent-checkpoint-id` optionally identifies a parent in the same run and
  session. A checkpoint is unique within that run/session, including across agents.
  Self-parenting is invalid. Parent completion may arrive later; the producer does
  not invent or require a historical parent event.
- `--span-kind work|waiting` optionally classifies observed elapsed activity or
  explicit waiting, defaulting to `work` on a correlated event. Work is elapsed
  activity, never CPU usage. Missing historical `span_kind` means `work` only when
  an otherwise valid correlated interval is present; gaps alone never imply waiting.

Every new event carries executable `ts_ms` in Unix milliseconds alongside legacy
`ts`. Start and end `ts_ms` supply precise run boundaries. Historical records may
omit it. Explicit span endpoints are authoritative for interval arithmetic;
correlated `duration_s` is their nonnegative difference rounded down to seconds.
Ordinary calls retain their existing since-last-write `duration_s` behavior.
Acceptance order sets `seq`; earlier-ending intervals may arrive after later ones.

Correlated writes require `jq`, `flock`, and the coreutils `truncate` command.
Unavailable dependencies warn and return no receipt. Workflow fallback selection
follows `run-log → ## Workflow coverage and routing`; a delivering checkpoint cannot
switch routes merely because a receipt is unavailable.
Legacy writes still work without jq; when flock is available, all step and close
writers acquire the same bounded per-run lock on the existing event file. Active
metadata is rechecked after locking. No historical content is read for correlation.

A successful correlated write prints exactly one JSON receipt, for example:

```json
{"kind":"accepted","run_id":"a1b2c3d4","session_id":"session-a","agent_id":"worker-a","checkpoint_id":"checkpoint-a","seq":1,"duplicate":false}
```

Match all four identity fields and a positive integer `seq` before treating a
checkpoint as accepted. Exit zero alone never proves acceptance. An identical retry
returns the original sequence with `duplicate:true` and appends nothing. A changed
normalized payload, including a different agent for the same run/session/checkpoint,
warns with no receipt or mutation. Equivalent omitted and explicit `span_kind work`
values are the same delivery. Deduplication reads only private active metadata and
lasts while the run remains active; delivery after close is rejected.

Validate before mutation, prepare complete receipt metadata, append the event under
the lock, then replace active metadata atomically before printing the receipt. A
recoverable append or metadata replacement failure emits no receipt and rolls back
that attempt's appended bytes so ordinary retry can persist one event. This is not
crash-proof exactly-once storage: process death, disk failure during rollback, or
partial operating-system writes can leave uncertain persistence. Do not infer a
receipt from such failures or repair history during attribution.

## Native hook adapter

`hooks/log-step-hook.sh` consumes the `claude-stop-v1` profile. It exits zero on
all paths, emits at most one reason-coded coverage warning, and returns no blocking
decision. Missing jq or flock makes precise coverage unavailable. The source
checkout resolves through nonempty `ORCHESTRAIL_HOME`, otherwise through the
adapter's parent directory; ordinary producer calls keep their existing behavior.

### Dispatch and native evidence

Before a checkpoint starts, call:

```bash
bash "$ORCHESTRAIL_HOME/hooks/log-step-hook.sh" dispatch \
  --run "$RUN_ID" --agent-id "$actor_id" --boundary subagent \
  --expected-skill pae-tests
```

Dispatch requires an explicit run ID and `CLAUDE_CODE_SESSION_ID`, generates a
unique checkpoint ID, and stamps its start time with an executable millisecond
clock. A session boundary uses `--boundary session` and an actor ID equal to the
session ID. A subagent boundary uses a stable caller-supplied actor ID; the native
subagent's ID need not equal this dispatch actor. Optional
`--parent-checkpoint-id` and `--span-kind work|waiting` preserve explicit parent and
waiting semantics. No model supplies a measured timestamp or discovers a recent run.

Dispatch prints exactly one compact key-sorted line. Include it unchanged in the
agent's native input:

```text
ORCHESTRAIL_DISPATCH_V1 {"agent_id":"worker-a","checkpoint_id":"checkpoint-a","run_id":"a1b2c3d4","schema_version":1,"session_id":"session-a"}
```

The final report contains exactly one unindented marker outside code fences.
Recognize top-level CommonMark fences with zero to three ASCII spaces before a
run of at least three backticks or tildes. Retain the opening character and full
run length. Backtick opener info cannot contain backticks; tilde info is unrestricted.
Only the same character repeated at least the opening length, followed solely by
spaces or tabs, closes a fence. A leading tab or four spaces cannot open or close
a top-level fence. Shorter runs, mixed delimiters and nonwhitespace closing suffixes
leave its contents fenced. An unclosed fence extends to the end of the report.
Treat LF, CRLF and lone CR as line separators without trimming marker/JSON content.
This is a bounded lexical scanner; quote/list-prefixed content does not establish
a top-level fence across an unprefixed report marker.

An eligible report line has this form:

```text
ORCHESTRAIL_REPORT_V1 {"agent_id":"worker-a","checkpoint_id":"checkpoint-a","outcome":"ok","run_id":"a1b2c3d4","schema_version":1,"session_id":"session-a","tests":"red"}
```

Require schema version `1`, the complete exact dispatch tuple and canonical
`step.outcome`. Optional `tests` and `gate` use the existing runtime vocabulary.
Compare the original JSON bytes to compact key-sorted serialization; unknown or
duplicate keys, noncanonical encoding, multiple reports, or mismatched identities
reject the delivery without changing pending ownership. Report markers cannot set
a step name or timestamp. RED success uses `outcome:"ok", tests:"red"`; GREEN
success uses `outcome:"ok", tests:"green"`; validation PASS uses
`outcome:"ok", gate:"pass"`; NEEDS WORK uses
`outcome:"failed", gate:"needs-work"`. Narrative prose never establishes outcome.

Native `Stop` input requires nonempty strings `hook_event_name`, `session_id`,
`cwd`, `transcript_path`, and `last_assistant_message`. `SubagentStop` additionally
requires `agent_id` and `agent_transcript_path`. Read the report from
`last_assistant_message`; the transcript may not yet contain the final response.
Only the native subagent transcript establishes subagent evidence. The native
session must equal the recorded session; `Stop` matches only session boundaries
and `SubagentStop` matches only subagent boundaries.

Find the matching dispatch line only in native `type:"user"` records, in
`message.content` text or direct `type:"text"` blocks. Quoted assistant output,
tool results, and arbitrary JSON fields do not establish dispatch input. Consider
only later native assistant `tool_use` objects with `name:"Skill"`, nonempty `id`
and `input.skill`. Repeated representations of an invocation ID must agree;
distinct IDs count separately, even when they name the same skill. Exactly one
eligible invocation establishes its skill name; check any expected skill. Multiple
invocations remain uncovered, preserving approximate logging for internal steps.
A session with a complete unambiguous tuple may use `step:"unknown"` when no
invocation is observable; a subagent without a unique invocation is omitted.

Native JSON input is bounded to 1048576 bytes, a report marker to 4096 bytes, and
the transcript tail to 16777216 bytes. Oversized, malformed, missing or conflicting
input emits one bounded safe coverage warning and never mutates accepted events.
A dispatch outside the bounded tail cannot establish coverage. The native hook
handler timeout is ten seconds; handlers use `onFailure:"continue"`.

### Project activation and private ownership

Canonical registered roots are one per line in
`${XDG_CONFIG_HOME:-$HOME/.config}/orchestrail/projects`. Resolve dispatch and native
`cwd` against the most-specific canonical registered ancestor, independent of
registry order and duplicate entries. Compare on path-component boundaries and
support spaces. Unregistered projects exit immediately before reading transcripts,
private correlation or run-log state. The selected root must equal dispatch
metadata; a newly registered nested root cannot inherit a broader root's checkpoint.

Fresh report/dispatch schema versions use the exact JSON integer token `1`.
Private numeric values and acceptance receipt sequence numbers use canonical
unsigned decimal integer tokens (`0` or a nonzero digit followed by digits), bounded
by `count.maximum`. Validate original JSON tokens before numeric conversion;
fractional, exponent, negative and negative-zero encodings are invalid even when
jq would round them to an integer. Sequence numbers must also be positive.
Quoted strings are never treated as numeric tokens. Historical lint retains its
separate mathematical-integer compatibility; it does not broaden this fresh
protocol. Invalid cached numeric encodings cannot forward delivery or return
accepted status.

Private schema-version `1` records live beneath
`${XDG_STATE_HOME:-$HOME/.local/state}/orchestrail/hooks/`, with directory mode
`0700` and file mode `0600`. Store only explicit identity, project, start time,
expected skill, optional parent/waiting semantics, ownership, the frozen normalized
producer payload and any matching receipt. Never store conversation text. Revalidate cached payload identities, start, boundary,
kind, parent, result and end against the dispatch record before retry; validate any
accepted receipt before returning status. Corrupted state never selects another run.
Do not read historical event lines to attribute a completion.

`status --checkpoint ID` reads only this private correlation state and returns one
JSON object containing `state`, the dispatch tuple and a `receipt` only for
`accepted`. State transitions are serialized under the checkpoint lock:

- `pending` → `delivering`: freeze the first validated completion timestamp and
  complete normalized producer payload before attempting a correlated write.
- `delivering` → `accepted`: require a single acceptance receipt matching every
  tuple field and a positive integer sequence. Exit zero does not prove acceptance.
  Every retry forwards the identical frozen payload, including its original end
  timestamp; missing or mismatched receipts leave acceptance uncertain. Durable
  retries require the original native agent binding and unchanged outcome/tests/gate.
  Reject contradictory reports without forwarding. The first validated transcript
  evidence is retained by ownership, so an aged or rotated transcript is not rescanned.
- `pending` → `fallback` → `fallback-attempted`: validate all fallback arguments,
  claim ownership, then attempt one ordinary step with `note:"approximate"`.
  Late hooks cannot append after the claim. Ordinary persistence offers no receipt,
  so fallback never describes itself as accepted and is never attempted twice.

Use `fallback --checkpoint ID --step NAME --outcome VALUE` with optional `--tests`
and `--gate` when precise coverage is unavailable before delivery starts. Once
`delivering` begins, retry only the frozen correlated payload; never switch to a
legacy route. Process death, state-write failure, or a lost receipt can leave
persistence uncertain. Report that condition without inventing acceptance or
attempting another route. A closed run rejects late delivery and is never reopened.

Select prompt logging and suppressions through the canonical workflow contract:
`run-log → ## Workflow coverage and routing`.

`bash scripts/validate-contracts.sh --hook-adapter-only` runs the isolated native
adapter fixtures, including concurrent delivery, exact attribution and fallback
ownership, without touching real settings or logs.

## Read-only lint

Invoke `scripts/log-step.sh lint [<run-id>|--all]`. No argument means `--all`.
Select all `runs/*.jsonl`, including active runs, or every `*-<run-id>.jsonl` match;
selection does not depend on active metadata. Report no matches without failing.
Visit filenames lexicographically and physical lines in ascending line order.
Never rewrite JSONL, digests, or metadata, and never create an absent log store.

Every line must contain exactly one JSON object. Validate `event`; common `ts`,
`run_id`, `seq`, `pipeline`, `flow`; step `step` and `outcome`; run-end `outcome`;
and any supplied enum/count from the vocabulary tables. Required flow is nonempty.
Counts, sequence, duration, optional `ts_ms` and any span endpoints must be
mathematical nonnegative JSON integers within the bound. When any correlation field
is present, require the complete `hook.required` set on a step and validate identity
strings, interval order, hook enums, self-parenting and unknown-step attribution.
Historical records may omit all correlation fields and `ts_ms`. Other optional
fields retain their current meanings. Recognizable legacy aliases are violations,
not normalized historical data.

Stdout is newline-delimited JSON with one object per field violation:
`{"kind":"violation","file":"<path>","line":2,"field":"tests","code":"invalid-enum"}`.
Keys are stable and raw values never appear. Codes are `invalid-json`,
`invalid-object`, `missing-field`, `invalid-type`, `invalid-enum`,
`invalid-integer`, `empty-flow`, `invalid-correlation`, `invalid-id`,
`invalid-interval`, `self-parent`, and `ambiguous-unknown`.

Every invocation ends with exactly one summary object:
`{"kind":"summary","status":"ok","files":2,"lines":9,"invalid_lines":1,"violations":2}`.
`invalid_lines` counts distinct file/line pairs; `violations` counts individual issues.
`files` and `lines` count examined files and lines, excluding unreadable attempts.
Status is `ok`, `partial`, or `unavailable`; an empty corpus is `ok` with zeros.
Missing jq or unreadable files warn on stderr and report `unavailable` or `partial`,
never an apparently clean unchecked corpus. Lint requires jq; ordinary legacy
writes still support the optional-jq fallback. Lint exits zero even with violations.

`bash scripts/validate-contracts.sh --run-log-contract-only` checks the canonical
runtime tables without running unrelated smoke tests. The default validator includes
the same gate, and either mode exits nonzero on drift with the affected field named.

---

## What must never enter the log

- Source code, diffs, file contents, test output, or command output.
- Secrets, tokens, credentials, connection strings, or personal data.
- Requirement text, spec prose, or the content of a decision. The log records *that* three
  decisions were made and *that* one escalated — `state.md` and the ADR record what they were.
- Paths outside the project root and the log store.

`note` and `blocker` are one clause each. If a clause needs more than a line, the place for
it is `state.md`, and the log carries the pointer implicitly through `task`.

---

## Relationship to the existing state files

The log does not replace anything. `state.md` remains the resumable state, `progress.md`
remains the chronological narrative, and neither is derived from the log. The log is the
only one of the three that is **structured, cross-project, and cheap to aggregate**, and it
is the only input `/retro` reads.

Nothing in a pipeline may read the log to decide what to do next. It is write-only during a
run; the sole reader is `/retro`, after the fact.
