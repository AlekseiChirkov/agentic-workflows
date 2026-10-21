---
status: done
completed_task: task-02-run-log-vocabulary-validation
completed_at: 2026-10-21
---

# Enforce Run-Log Field Vocabulary and Validation in `log-step.sh`

## Goal

Make run-log telemetry consistent and aggregatable without ever obstructing a workflow.
`scripts/log-step.sh` must normalize the known legacy spellings, reject other invalid
inputs before any state change, and expose a read-only linter for historical logs.
`/retro` must distinguish valid measurements from invalid records. This implements
[issue #1](https://github.com/AlekseiChirkov/agentic-workflows/issues/1)
and ADR-0009 Decision 5. The existing logs remain untouched.

## Contract Decisions

The following decisions are binding for implementation and tests. There are no
unresolved vocabulary, error-handling, or reporting choices in this spec.

### 1. Field vocabulary and presence

Allowed values are **case-sensitive**, with no implicit trimming, case folding, or
conversion except the legacy mappings in section 2.

| Event | Field | Required? | Allowed value / type |
|---|---|---|---|
| `step` | `outcome` | yes | `ok`, `blocked`, `failed`, `skipped`, `deferred` |
| `step` | `gate` | no | `pass`, `fail`, `n-a`, `needs-work`, `ready` |
| `step` | `tests` | no | `red`, `green`, `n-a`, `failed`, `not-run`, `pinned` |
| `step` | `promoted` | no | `yes`, `no` |
| `step` | `stops`, `escalations`, `decisions`, `questions`, `fix_tasks`, `amendments`, `files` | no | JSON integer from `0` through `9007199254740991` |
| `run-end` | `outcome` | yes | `completed`, `stopped`, `failed`, `abandoned` |
| `run-start` | `flow` | yes in storage | nonempty string; default `unknown` |
| `step`, `run-end` | `flow` | yes in storage | inherited nonempty string from `run-start` |

- Integer arguments must have the exact decimal syntax `0` or `[1-9][0-9]*`;
  negatives, `+1`, `01`, decimals, exponent notation, whitespace, and values
  above the maximum are invalid. Valid supplied `0` is stored as a JSON number,
  never omitted or quoted; genuinely absent counts are omitted.
- An omitted optional enum is omitted. An explicitly supplied empty value
  (for example `--tests ""` or `--gate ""`) is invalid, not equivalent to omission.
  Empty optional free-text fields continue to be omitted.
- `--flow` omitted or explicitly empty at `run-start` produces `flow: "unknown"`.
  Other nonempty flow labels are preserved; this task does **not** introduce a
  `flow` enum, and `unknown` is a valid deliberate fallback, not a validation error.
- Required `--pipeline` at `run-start`, `--run` and `--step` at `step`, and
  `--run` at `run-end` remain mandatory. Required outcome is never defaulted.
- `gate` becomes a closed vocabulary. Previously documented arbitrary short
  verdicts are no longer allowed: free-text verdicts would make `/retro` gate
  metrics uncountable. Use `note` for context.
- `run-end --outcome` has a **different** enum from `step --outcome`:
  `completed` is valid only at run end and is not normalized to `ok` there.

### 2. Exact legacy normalization

Normalize **only** `step` values with the mappings below, before validation:

| Field | Raw input / match rule | Canonical stored value |
|---|---|---|
| `outcome` | exact `completed` | `ok` |
| `outcome` | exact `implemented` | `ok` |
| `outcome` | exact `restarted` | `failed` |
| `outcome` | exact `needs-work` | `failed` |
| `gate` | exact `PASS` | `pass` |
| `gate` | `NEEDS WORK`, or `NEEDS WORK` followed by whitespace, `:` or `-` and any text | `needs-work` |
| `gate` | exact `escalated` | `fail` |

The prefix match must not accept `NEEDS WORKING` or other lookalikes. Other
case variants (for example `pass` is canonical, `Pass` is not) are **not**
normalized. The original input is preserved byte-for-byte inside the JSON
string `note`, using the exact fragment `raw:<original value>`. If a caller
already supplied `--note`, keep it first and append fragments separated by
`; `. When both fields normalize, append the `outcome` fragment first and
the `gate` fragment second. Example:

`--outcome completed --gate PASS --note "checked"` becomes
`outcome: "ok"`, `gate: "pass"`,
`note: "checked; raw:completed; raw:PASS"`.

No `raw:` fragment is added for an already canonical value. The preserved
text is part of local telemetry and must obey the existing privacy rules in
`rules/run-log.md`. Diagnostics must never echo arbitrary raw values.

### 3. Validation, warnings, and non-blocking writes

Validation happens on the complete argument set **before** a file is opened
for writing and before `seq`, `last_epoch`, or other `.active` metadata changes.
For `step` or `run-end`, if **any** supplied field is invalid, reject the
entire event, not just that field. Invalid `run-start` input must not create
an active run or log file.

- Unknown arguments, missing argument operands, duplicate arguments,
  missing required arguments, invalid enum values, and invalid counts
  produce exactly **one** single-line diagnostic on stderr per rejected
  invocation, with a field/argument name and reason code but no raw value.
  A flag must not silently consume the next flag as its operand.
- An unsupported value or a failure to open/write the log must **never**
  interrupt the pipeline: all command paths return process exit code `0`.
  Do not emit success-shaped output for a failed operation.
- On rejected `step`, there is no JSONL append, no sequence increment, and
  no timestamp/metadata advance. The next valid step uses the next
  consecutive sequence number and measures from the last *accepted* event.
- On rejected `run-end`, there is no closing entry, no digest rewrite,
  and no removal of `.active/<run-id>`. The caller may issue a valid end
  afterward. On successful close, remove active metadata only after
  persisting the closing JSONL line; a digest-write failure warns but
  cannot undo an already persisted close.
- `run-start` prints its run ID on stdout **only if** the start event was
  successfully persisted and usable metadata exists. If it cannot start,
  stdout is empty and stderr contains one warning. Successful `step` and
  `run-end` print nothing to stdout.
- Keep existing `path` and `active` semantics. File-system failures
  remain best-effort, non-blocking warnings; transactional rollback of
  partially completed operating-system writes is **not** required.
- Reject unsafe `--run` identifiers before any metadata path lookup:
  accept the helper's existing eight-lowercase-hex-character run IDs only.
  This prevents a malformed identifier from becoming a filesystem path.

### 4. Step names: advisory check only

For a `step` invocation, derive recognized names at call time from the
basenames of `*.md` in `$ORCHESTRAIL_HOME/workflows/`, or, if
`ORCHESTRAIL_HOME` is unset/empty, the helper checkout's `workflows/`
directory. Also recognize synthetic steps `batch-gate`, `subtask`,
and `dry-run`.

An unknown, nonempty step name is **stored unchanged**, accompanied by
one warning on stderr; this is not a vocabulary violation and the linter
does not retrospectively flag step names (workflow names change over time).
If the workflows directory is inaccessible, warn once that verification
is unavailable and still write the valid event. Never hard-code a snapshot
of the workflow list or consult the consuming project directory.

### 5. Read-only lint interface

Add `scripts/log-step.sh lint [<run-id>|--all]`:

- No argument is equivalent to `--all`. `--all` visits every
  `$ORCHESTRAIL_LOG_ROOT/runs/*.jsonl` file, including currently active
  runs. `<run-id>` visits every matching `*-<run-id>.jsonl` file (use
  the existing eight-hex-character identifier format); report the
  no-match case without failing. Do not depend on `.active` records.
- Iterate selected files in lexicographic filename order and JSONL lines
  in ascending line-number order. **Never** rewrite historical JSONL,
  digests, or metadata; do not create the log store if absent.
- Parse each line as a JSON object. Report malformed JSON, non-object
  JSON, missing required event fields, invalid field types, empty
  required `flow`, invalid enum values (including recognizable legacy
  aliases), and invalid integer counts. At minimum validate:
  `event`; common `ts`, `run_id`, `seq`, `pipeline`, `flow`;
  `step` and `outcome` for step lines;
  `outcome` for run-end lines; and any supplied fields from section 1.
  `duration_s` and `seq` must be nonnegative JSON integers within the
  same numeric bound. Other optional fields retain their current
  meanings and are not newly restricted.
- The linter **does not normalize** old values and does not mark
  previously valid rows invalid solely because their workflow step
  names are no longer present.
- `jq` is required for linting, not newly required for writing. With
  missing `jq` or unreadable files, emit a warning and mark the result
  `unavailable` or `partial`; never emit an apparently clean result
  for records that were not checked.
- Diagnostics are newline-delimited JSON on **stdout** (one object per
  field violation), with stable keys:
  `{"kind":"violation","file":"<path>","line":2,"field":"tests","code":"invalid-enum"}`.
  Values are **never** included. Use codes `invalid-json`, `invalid-object`,
  `missing-field`, `invalid-type`, `invalid-enum`,
  `invalid-integer`, and `empty-flow` as applicable.
- End every lint invocation with exactly one summary JSON object:
  `{"kind":"summary","status":"ok","files":2,"lines":9,"invalid_lines":1,"violations":2}`.
  `status` is one of `ok`, `partial`, `unavailable`. `invalid_lines`
  counts distinct `(file,line)` pairs, while `violations` counts
  individual issues. `files` and `lines` count examined files/lines,
  not attempted but unreadable ones. Empty corpus produces an `ok`
  summary with zeros. Exit code remains `0` even with violations.

### 6. Retrospective reporting

Update `workflows/retro.md` Step 1 to invoke `lint --all` and intersect
its per-file diagnostics with the **same run-file corpus** selected
by `--since`, `--pipeline`, `--project`, and `--limit`. In `## Corpus`,
report total runs, examined event lines, invalid lines, number of affected
runs, violation counts by field/code, and up to five `file:line` examples
without raw values. State `partial`/`unavailable` explicitly if lint
was incomplete.

Exclude lint-invalid **lines** from downstream metric calculations rather
than assigning guessed canonical values. An affected run must be labeled
as having incomplete telemetry; all metric denominators must count only
usable observations, and the report must disclose where exclusions affect
a result. Count "abandoned" by a *missing physical run-end event*;
a present but invalid end event is instead reported as an unusable close,
not misclassified as an abandonment. Keep the existing fewer-than-five
runs warning, honesty rules, and recommendation-only behavior.

### 7. Documentation and contract drift detection

Update `rules/run-log.md → ## Field vocabulary` to make the enum sets
and the complete normalization table in sections 1–2 explicit, including
`tests: pinned`, count bounds, absent-versus-empty semantics, strict
`gate` values, and the `unknown` flow default. Document the linter and
its reporting contract, plus the rule that invalid events leave state
untouched.

Extend `scripts/validate-contracts.sh` to compare the **effective
enumerations and mappings used by the helper** with the canonical tables
in the documentation, including `NEEDS WORK` prefix semantics. Implement
these as structured, machine-comparable data in the script and tables,
not scattered greps for mere mentions. A missing, extra, or modified
value or mapping on either side fails contract validation (nonzero exit),
with a field-specific explanation. In contrast to `log-step.sh`,
`validate-contracts.sh` is a gate and must retain failure exit status.

The validator must detect drift when a test temporarily removes a value
or changes a mapping from **either side**. Do not introduce a second
independent vocabulary hidden in lint or the validator: both writes and
lint must use the same authoritative runtime definitions.

## Acceptance Criteria

- [ ] All four `step.outcome` and three `step.gate` legacy cases
      normalize exactly as in section 2, with deterministic `raw:`
      provenance retained alongside an existing note.
- [ ] The exact `outcome`, `gate`, `tests` (including `pinned`),
      `promoted`, run-end outcome, and integer vocabularies from section 1
      are enforced; unmapped values and malformed numbers write nothing.
- [ ] Missing or empty `--flow` on `run-start` becomes `unknown` in
      start, subsequent step, and end events.
- [ ] Every invalid invocation emits one stderr warning and exits `0`;
      no JSONL, active metadata, sequence, digest, or timestamp is
      changed by a rejected event.
- [ ] `run-start` failure emits no run ID; a valid `run-end` after an
      invalid `run-end` still closes normally; simulated write failures
      do not block the caller.
- [ ] Step membership is checked against current `workflows/*.md`
      and the three synthetic steps; unknown names warn but are written.
- [ ] `lint` supports no args, `--all`, and `<run-id>`; reports stable
      JSON diagnostics and an accurate summary without modifying files.
- [ ] `/retro` reports lint-invalid rows for the filtered corpus and
      excludes invalid lines from metrics with clear denominators.
- [ ] `rules/run-log.md` reflects the actual enums, aliases, integer
      syntax, presence rules, and `lint` invocation; `validate-contracts.sh`
      detects enum and mapping drift in either direction.
- [ ] `tests/log-step.sh` is an executable, isolated smoke-test script.
      It covers every branch above using a temporary
      `ORCHESTRAIL_LOG_ROOT` and temporary workflow fixture, including:
      every alias, both aliases in one event, all canonical enum values,
      explicit empty optional values, unknown values, zero/boundary/negative/
      fractional/leading-zero/oversized counts, invalid follow-up then
      valid step or end, missing `flow`, known/synthetic/unknown step,
      absent workflow directory, malformed JSON in lint, legacy lint rows,
      no-match and empty corpus, closed and active runs, no `jq` behavior,
      nonblocking errors, documentation drift, and preservation of
      historical file checksums.
- [ ] Execute `bash tests/log-step.sh` and
      `bash scripts/validate-contracts.sh` successfully; run
      `bash -n` on modified shell scripts. Test fixtures must not
      read, modify, or depend on real `logs/runs/`.

## Out of Scope

- Rewriting, migrating, or "fixing" historical log files. The ten
  historical runs described by the original spec must remain unchanged.
- Token/cost accounting (spec 05), hook-driven logging (spec 03),
  or adjustments to the already-planned spec 06.
- Schema validation for unrelated free-text fields, privacy scanning of
  existing notes, historical workflow-name enforcement, or a new log
  storage format.
- General concurrency/locking redesign, file-system transactional
  recovery after an I/O failure, or changing `/retro` into a workflow
  that automatically edits implementation files.

## Notes

- Source contract: `rules/run-log.md`; producer:
  `scripts/log-step.sh`; consumer: `workflows/retro.md`.
- ADR-0009 Decision 5: normalize known drift, warn on unknown step
  names, leave historical files unchanged. Decision 7: complete spec
  02 before specs 03, 05, and 06.
- Preserve the existing shell-only producer and optional-`jq` write
  fallback. Lint is allowed to require `jq` because `/retro` already
  uses it; missing tooling must be reported, never disguised as a
  clean corpus.
- Test level: smoke. The in-repository executable
  `tests/log-step.sh` is the acceptance harness.

## Change Log

### 2026-10-21 — reconciled from completed run-log validation
- No requirement deltas. All acceptance criteria are met; the four validation defects were repaired without changing their requirements. Source: task Contract Check, Code Review and reviewed fix records.
