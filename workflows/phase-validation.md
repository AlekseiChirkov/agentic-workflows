---
description: Phase 3 — Validation orchestrator: verify contract, review code, create and execute fix-tasks
---

Invocation: `/phase-validation <task-directory>`
Example: `/phase-validation .ai/tasks/todo/task-01-add-oauth/`

If path is not provided — ask the user and do not continue.
Task directory = provided argument (trailing slash optional).

To run a single step directly, call the child workflow:
`/pv-contract`, `/pv-review`, `/pv-issues`, `/pv-create-fixes` (which calls `/pv-classify-fixes`
as step 4a), `/pv-execute-fixes`, `/pv-finalize`.

---

## Run Logging

This pipeline writes a run log. Follow the **`run-log`** rule in full — it defines the
store, the field vocabulary, and the rule that logging never blocks a run.

Apply `run-log → ## Workflow coverage and routing` at each boundary. Keep internal
step logging instructions and add `--note approximate` to every ordinary prompt step.

At Step 0, open the run:

Open the run with `scripts/log-step.sh run-start` through the configured helper:

```bash
LOG_HELPER="${ORCHESTRAIL_HOME:+$ORCHESTRAIL_HOME/scripts/log-step.sh}"
RUN_ID=""
if [ -x "$LOG_HELPER" ]; then
  RUN_ID=$("$LOG_HELPER" run-start --pipeline phase-validation \
  --project "$(pwd)" --task <task-directory> --flow <quick|full>) || RUN_ID=""
fi
```

Log one `step` line after each of `pv-contract`, `pv-review`, `pv-issues`,
`pv-classify-fixes`, `pv-create-fixes`, `pv-execute-fixes`, and `pv-finalize`. Carry
`--gate pass|fail` from `pv-contract` and `pv-review`, `--fix-tasks` from
`pv-create-fixes`, `--stops 1` on the `pv-issues` approve/defer prompt when a human
answered it, and `--decisions` when `/phase-pipeline` answered it instead. Close with
`run-end`.

Logging is best-effort: if `$LOG_HELPER` is missing or a call fails,
continue unchanged and mention it once in the final report. Never stop, retry, or ask the
user because of a log write.

---

## Context Bootstrap

Follow `phase-validation` rules — ## Context Bootstrap. Load in order, skip missing files.
In multi-repo projects: load umbrella (`../.ai/`) first, then local (`.ai/`) — local overrides.

1. `.ai/memory/architecture.md` — system-level invariants, integration contracts
2. `.ai/memory/state.md` — what was executed, task progress
3. `.ai/principles/architecture.md` — patterns the implementation must conform to
4. `.ai/principles/coding.md` — code standards (deviations = findings)
5. `.ai/principles/domain.md` — domain correctness rules
6. `.ai/adr/index.md` — past decisions (violations = critical findings)
7. `.ai/context/runbook.md` — commands to run tests/lint during validation

Report: "Validation context loaded: [files read]"

---

## Step 0 — State Check

Read `state.md` in the task directory. Check `## Phases`:

- If `state.md` is not found in the task directory → report: "state.md not found. Run `/phase-execution` first." **Stop.**
- If `execution` is not `complete` → report: "Execution not complete. Run `/phase-execution` first." **Stop.**
- If `validation: complete` → report: "Validation already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation before continuing.
- If `validation: in-progress` → determine last completed step:
  - `## Contract Check` present → Step 1 done.
  - `## Code Review` present → Steps 1–2 done.
  - `## Issue List` present → Steps 1–3 done.
  - Fix-task directories (T-XX-fix-*) with `description.md` exist → Steps 1–4 done.
  - All fix-tasks have status `reviewed` → Steps 1–5 done.
  - Output: `Validation partially complete. Continuing from Step N.`
- If `validation: not-started` → start from Step 1.

---

## Execution

Update `## Phases` in `state.md`: set `validation: in-progress`.

**Flow-tier branch (read `flow:` from `state.md`).** If `flow: quick`: run Step 1
(`/pv-contract`, against the `## Contract (quick)` section) and Step 2 (`/pv-review`)
**unchanged — both are mandatory**. Then **skip Steps 4–5** (`/pv-create-fixes` /
`/pv-execute-fixes` as separate atomic cycles): apply any review findings **inline** in this
phase, re-run `/pv-review` on the fix, and record the outcome under `## Code Review`. Still
run Step 3 (`/pv-issues`) to surface findings for the user's decision, and Step 6
(`/pv-finalize`). The ADR trigger is unchanged: if a reader-relevant decision was made, write
the ADR. See the `quick-flow` rule. If `flow: full`, run all steps below unchanged.

Run child workflows in order, skipping completed steps:

1. Call `/pv-contract <task-directory>` — Contract verification
2. Call `/pv-review <task-directory>` — Code review
3. Call `/pv-issues <task-directory>` — Issue list for user (waits for decision)
4. Call `/pv-create-fixes <task-directory>` — Create fix-task directories.
   After it returns, re-read `state.md` and inspect `## Fix-Tasks`. If `fixes-count: 0` is present in `## Fix-Tasks` — skip Step 5 and jump to Step 6.
5. Call `/pv-execute-fixes <task-directory>` — Execute fix-tasks via atomic cycles (skipped when 0 fix-tasks were created).
6. Call `/pv-finalize <task-directory>` — Finalization + compress

After all steps, report final status including any deferred tasks.
