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

At Step 0, preserve an inherited `RUN_ID`; otherwise open an owned run with `scripts/log-step.sh run-start` through the configured helper:

```bash
LOG_HELPER="${ORCHESTRAIL_HOME:+$ORCHESTRAIL_HOME/scripts/log-step.sh}"
PHASE_OWNS_RUN=false
if [ -z "${RUN_ID:-}" ] && [ -x "$LOG_HELPER" ]; then
  RUN_ID=$("$LOG_HELPER" run-start --pipeline phase-validation \
  --project "$(pwd)" --task <task-directory> --flow <quick|full>) || RUN_ID=""
  [ -z "$RUN_ID" ] || PHASE_OWNS_RUN=true
fi
```

Log one `step` line after each of `pv-contract`, `pv-review`, `pv-issues`,
`pv-classify-fixes`, `pv-create-fixes`, `pv-execute-fixes`, and `pv-finalize`. Carry
`--gate pass|fail` from `pv-contract` and `pv-review`, `--fix-tasks` from
`pv-create-fixes`, `--stops 1` on the `pv-issues` approve/defer prompt when a human
answered it, and `--decisions` when `/phase-pipeline` answered it instead.

Close with `run-end` only when `PHASE_OWNS_RUN=true`; an inherited run stays open for
its owner. Do not open a second run for `/phase-pipeline` or `/spec-run`.

Logging is best-effort: if `$LOG_HELPER` is missing or a call fails,
continue unchanged and mention it once in the final report. Never stop, retry, or ask the
user because of a log write.

---

## Context Bootstrap

Load the `phase-validation` rule (`## Context Bootstrap`) before reading implementation files or
writing project files; run the full bootstrap when invoked standalone. The rule owns
the load order, umbrella precedence, conditional sources, and reporting.

---

## Guard

Step 0 — State Check

Resolve the task directory absolutely and read `state.md → ## Phases` before writing.
Missing state or execution not `complete` → **stop**: "Complete `/phase-execution` first."
Validation complete → ask for explicit confirmation before replacing completed artifacts.
Absent `flow:` means `full`.

On resume, use persisted outputs, not directory existence:
- `## Contract Check` → contract check ran; enforce its critical-failure decision before review.
- `## Code Review` → review ran.
- `## Issue List` with both decision subsections → issue decisions recorded.
- `## Fix-Tasks` with `fixes-created: complete`, valid Created list, and every approved
  issue assigned → fix creation finished. Newly approved unassigned issues resume step 4
  in append mode; never discard completed fixes.
- `fixes-count: 0`, or every listed fix is `reviewed` → fix execution finished.
A partial/malformed output resumes its writer. Never infer "all fixes reviewed" from an
empty directory glob. Report the selected resume step; set `validation: in-progress`.
Open an owned run only after prerequisites and flow are known.

---

## Execution

Run sequentially, skipping only completed steps whose evidence remains valid:

1. `/pv-contract <task-directory>`.
2. `/pv-review <task-directory>`.
3. `/pv-issues <task-directory>` — record approval/deferral before applying findings.
4. `/pv-create-fixes <task-directory>` — full tier only; it calls `/pv-classify-fixes`.
5. `/pv-execute-fixes <task-directory>` — full tier only, skipped when `fixes-count: 0`.
6. `/pv-finalize <task-directory>` — after approved work and final checks succeed.

For `flow: quick`, steps 1–3 remain mandatory against `## Contract (quick)`.
Skip separate fix-task steps 4–5. Apply only approved findings inline, run the TDD gate
before changed behaviour, keep frozen tests, and rerun both `/pv-contract` and `/pv-review`.
Preserve the original issue decisions and record which approved items are resolved.
New findings return to the decision step. If a quick gate fails, promote per `quick-flow`;
do not silently expand inline scope. The ADR trigger remains unchanged.

Any child stop/failure propagates; do not advance using an incomplete result. On a full
fix cycle, recheck the affected contract and review findings before finalization without
recreating already-recorded fix directories. Persist unresolved/deferred results.

Close only the run this invocation owns. Report verification, fixes, deferrals, and final
status. Child completion is a progress marker, not an extra user handoff.
