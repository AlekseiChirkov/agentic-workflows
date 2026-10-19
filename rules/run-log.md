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
beyond one line in its final report. `log-step.sh` is written to exit `0` on every error
path for exactly this reason. A workflow must never stop, retry, or ask the user because a
log write failed, and must never let a logging concern change a decision it would otherwise
have made.

---

## Where the log lives

```
$AGENTIC_LOG_ROOT            # if set — used verbatim
~/Documents/projects/alterra/agentic_workflows/logs/     # otherwise (the default)
  runs/
    <ISO-timestamp>-<pipeline>-<run-id>.jsonl   # append-only, one JSON object per line
    <ISO-timestamp>-<pipeline>-<run-id>.md      # human-readable digest, written at run-end
  .active/<run-id>                              # open-run metadata; removed at run-end
  .gitignore                                    # `*` — the store is never committed
```

The store is **central and cross-project**: runs from every repository land in one place,
because the question the log answers ("what should change in the workflows?") is only
answerable across projects. The path is machine-global and identical for every deployed
copy of a workflow — a workflow must never hard-code a project-relative log path.

The store is local telemetry. It is not committed, not synced by `sync.sh`, and not copied
into a project.

---

## How a pipeline logs

Three calls, all through `log-step.sh` via the shell. **Agents never hand-write a JSON
line** — the helper stamps the time and derives every duration from its own previous write.
A duration written by a model is a guess, and a guessed number in a metrics store is worse
than a missing one.

Resolve the helper as `~/Documents/projects/alterra/agentic_workflows/log-step.sh`. If it is not executable there, skip
logging for the whole run and note that once in the final report.

**1 — At the start of the pipeline, before its first step:**

```bash
RUN_ID=$(~/Documents/projects/alterra/agentic_workflows/log-step.sh run-start \
  --pipeline phase-discovery \
  --project "$(pwd)" \
  --task .ai/tasks/todo/task-01-add-oauth \
  --spec .ai/specs/01-add-oauth.md \
  --flow full \
  --flags "--step-by-step")
```

Keep `RUN_ID` for the rest of the run. If the pipeline resumes in a later session, start a
new run — `/retro` correlates runs by `task`, so a resumed task reads as two runs of the
same task, which is itself a signal worth measuring.

**2 — Immediately after each step completes**, before moving to the next one:

```bash
~/Documents/projects/alterra/agentic_workflows/log-step.sh step --run "$RUN_ID" \
  --step pd-analyze --outcome ok \
  --decisions 3 --questions 2 --stops 1 \
  --note "resolved 3 ambiguities from principles"
```

Log the step **after it finishes**, whatever the outcome — a step that failed, blocked, or
was skipped is the most valuable line in the file. A step that ends the run still gets its
own `step` line before `run-end`.

**3 — When the pipeline stops, for any reason:**

```bash
~/Documents/projects/alterra/agentic_workflows/log-step.sh run-end --run "$RUN_ID" \
  --outcome stopped --note "escalated: two ADRs conflict"
```

This includes a planned stop. `/phase-discovery` completing normally is `--outcome
completed`; the batch gate in `/spec-run` handing control to the human is `--outcome
stopped`. A run left without `run-end` shows up in `log-step.sh active` and is counted by
`/retro` as an abandoned run — which is accurate, and deliberately visible.

---

## Field vocabulary

`ts`, `run_id`, `event`, `seq`, `pipeline`, `project`, `task`, `flow`, and `duration_s` are
written by the helper. The workflow supplies the rest.

| Field | Type | Meaning |
|---|---|---|
| `step` | string | The child workflow or named step that just finished — `pd-analyze`, `pae-tests`, `batch-gate`. Use the workflow's own name, without a leading slash. |
| `outcome` | enum | `ok` \| `blocked` \| `failed` \| `skipped` \| `deferred`. `blocked` = an external blocker; `failed` = the step could not produce its artifact. |
| `stops` | int | How many times this step handed control to a human and waited. The core autonomy metric. |
| `escalations` | int | How many times the Autonomous Decision Protocol hit its escalation threshold, or a class-B ambiguity was raised. |
| `decisions` | int | Autonomous decisions recorded during the step (`### Assumptions` lines, `### Autonomous Decision` blocks). |
| `questions` | int | Clarifying questions asked of the human. |
| `gate` | string | Result of whatever gate the step owns: `pass`, `fail`, `n-a`, or a short verdict (`needs-work`, `ready`). |
| `tests` | enum | `red` \| `green` \| `n-a` \| `failed` \| `not-run` — mirrors `atomic-tests:` for the subtask this step touched. |
| `fix_tasks` | int | Fix-tasks created by this step. |
| `promoted` | `yes`/`no` | Whether a `quick` task was promoted to `full` during this step. |
| `amendments` | int | Description amendments applied during this step. |
| `files` | int | Count of files written or modified. A count, never a list. |
| `subtask` | string | `T-XX` when the step belongs to one subtask. |
| `blocker` | string | One clause naming the blocker, when `outcome` is `blocked`. |
| `note` | string | One short clause of context. Not a summary of the work. |

Omit a field rather than writing `0` or `unknown` for something the step genuinely does not
measure. An omitted field reads as "not applicable here"; a fabricated `0` reads as "measured
and found to be none", and the two must not be confused.

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
