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
  --note "resolved 3 ambiguities from principles" || true
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
successful `step` and `run-end` print nothing. Filesystem failures warn once and
remain non-blocking; transactional rollback of partial operating-system writes is
not required. Existing `path` and `active` behavior remains available.

## Read-only lint

Invoke `scripts/log-step.sh lint [<run-id>|--all]`. No argument means `--all`.
Select all `runs/*.jsonl`, including active runs, or every `*-<run-id>.jsonl` match;
selection does not depend on active metadata. Report no matches without failing.
Visit filenames lexicographically and physical lines in ascending line order.
Never rewrite JSONL, digests, or metadata, and never create an absent log store.

Every line must contain exactly one JSON object. Validate `event`; common `ts`,
`run_id`, `seq`, `pipeline`, `flow`; step `step` and `outcome`; run-end `outcome`;
and any supplied enum/count from the vocabulary tables. Required flow is nonempty.
Counts, sequence, and duration must be mathematical nonnegative JSON integers within
the bound; other optional fields retain their current meanings. Recognizable legacy
aliases are violations, not normalized historical data.

Stdout is newline-delimited JSON with one object per field violation:
`{"kind":"violation","file":"<path>","line":2,"field":"tests","code":"invalid-enum"}`.
Keys are stable and raw values never appear. Codes are `invalid-json`,
`invalid-object`, `missing-field`, `invalid-type`, `invalid-enum`,
`invalid-integer`, and `empty-flow`.

Every invocation ends with exactly one summary object:
`{"kind":"summary","status":"ok","files":2,"lines":9,"invalid_lines":1,"violations":2}`.
`invalid_lines` counts distinct file/line pairs; `violations` counts individual issues.
`files` and `lines` count examined files and lines, excluding unreadable attempts.
Status is `ok`, `partial`, or `unavailable`; an empty corpus is `ok` with zeros.
Missing jq or unreadable files warn on stderr and report `unavailable` or `partial`,
never an apparently clean unchecked corpus. Lint requires jq; writing still supports
the optional-jq fallback. Lint exits zero even with violations.

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
