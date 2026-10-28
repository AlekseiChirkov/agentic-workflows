---
description: Phase 2 — Execution orchestrator: execute all pending subtasks via atomic cycles
---

Invocation: `/phase-execution <task-directory>`
Example: `/phase-execution .ai/tasks/todo/task-01-add-oauth/`

If path is not provided — ask the user and do not continue.
Task directory = provided argument (trailing slash optional).

To run a single step directly, call the child workflow:
`/pe-execute`, `/pe-finalize`.

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
  RUN_ID=$("$LOG_HELPER" run-start --pipeline phase-execution \
  --project "$(pwd)" --task <task-directory> --flow <quick|full>) || RUN_ID=""
  [ -z "$RUN_ID" ] || PHASE_OWNS_RUN=true
fi
```

Log one `step` line per subtask cycle rather than per inner workflow: after each subtask's
atomic-execution → atomic-validation loop closes, write `--step pe-execute --subtask T-XX --note approximate`
with `--tests` mirroring the leaf's `atomic-tests:` value, `--files` from its
`target_files:` count, `--gate` from the atomic-validation verdict, and `--outcome blocked`
plus `--blocker` when the subtask ends blocked. Log `pe-finalize` as its own step.

Close with `run-end` only when `PHASE_OWNS_RUN=true`; an inherited run stays open for
its owner. Do not open a second run for `/phase-pipeline` or `/spec-run`.

Logging is best-effort: if `$LOG_HELPER` is missing or a call fails,
continue unchanged and mention it once in the final report. Never stop, retry, or ask the
user because of a log write.

---

## Context Bootstrap

Load the `phase-execution` rule (`## Context Bootstrap`) before reading implementation files or
writing project files; run the full bootstrap when invoked standalone. The rule owns
the load order, umbrella precedence, conditional sources, and reporting.

---

## Guard

Step 0 — State Check

Resolve the task directory to an absolute path. Read its `state.md` before writing anything.

- Missing state → **stop**: "state.md not found. Run `/phase-discovery` first."
- `discovery` is not `complete` → **stop**: "Discovery not complete. Run `/phase-discovery` first."
- `execution: complete` → ask for explicit confirmation before replacing completed artifacts.
- Otherwise resume from recorded progress; absent `flow:` means `full`.

For `flow: full`, require `plan.md`, read its dependency order and `## Subtask Progress`,
and report reviewed, pending, blocked, and deferred rows with reasons. A `done` leaf still
needs atomic validation. If no pending cycles remain, run `/pe-finalize` to reconcile and
close Execution; do not bypass finalization or start Validation.

For `flow: quick`, there are no subtasks or required `plan.md`; require
`## Contract (quick)` and inspect `## TDD (quick)` for the resume point.

Open the run only after resolving the flow and prerequisites. Set `execution: in-progress`.

---

## Execution

**Full tier:**
1. Call `/pe-execute <task-directory>`.
2. Call `/pe-finalize <task-directory>` only after the execution loop returns successfully.

**Quick tier:** Run the inline TDD step first; follow `quick-flow → ## The quick path — what changes` and the `tdd` rule.
Against the inline Acceptance Criteria, classify the test level, observe RED before
implementation (or record the justified `none` gate), and persist `## TDD (quick)`.
Implement within the inline contract, keep the test set frozen, run affected regression
and configured verification commands, and record GREEN plus the cumulative changed-file list.
For justified `none` without a suite, record actual manual/AC verification as completion;
never infer the exemption from missing tooling.
Resume existing evidence rather than rewriting tests after code exists. Then call `/pe-finalize`.
If any quick gate fails, stop implementation and promote per
`quick-flow → ## Mid-flight escalation (quick → full)` before continuing.

Close the owned run on completion or a stop, with the actual outcome. An inherited run
remains owned by its caller. Report completed/skipped work, verification, and artifact paths.
Display: "Execution complete. Run `/phase-validation <task-directory>` to start validation."

**STOP. Do not run `/phase-validation` automatically.** A caller with an explicit
cross-phase override owns its next phase. Child completion messages are progress markers,
not handoffs.
