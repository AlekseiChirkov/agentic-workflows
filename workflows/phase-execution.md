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

At Step 0, open the run:

Open the run with `scripts/log-step.sh run-start` through the configured helper:

```bash
LOG_HELPER="${ORCHESTRAIL_HOME:+$ORCHESTRAIL_HOME/scripts/log-step.sh}"
RUN_ID=""
if [ -x "$LOG_HELPER" ]; then
  RUN_ID=$("$LOG_HELPER" run-start --pipeline phase-execution \
  --project "$(pwd)" --task <task-directory> --flow <quick|full>) || RUN_ID=""
fi
```

Log one `step` line per subtask cycle rather than per inner workflow: after each subtask's
atomic-execution → atomic-validation loop closes, write `--step pe-execute --subtask T-XX --note approximate`
with `--tests` mirroring the leaf's `atomic-tests:` value, `--files` from its
`target_files:` count, `--gate` from the atomic-validation verdict, and `--outcome blocked`
plus `--blocker` when the subtask ends blocked. Log `pe-finalize` as its own step. Close
with `run-end`.

Logging is best-effort: if `$LOG_HELPER` is missing or a call fails,
continue unchanged and mention it once in the final report. Never stop, retry, or ask the
user because of a log write.

---

## Context Bootstrap

Follow `phase-execution` rules — ## Context Bootstrap. Load in order, skip missing files.
In multi-repo projects: load umbrella (`../.ai/`) first, then local (`.ai/`) — local overrides.

1. `.ai/memory/architecture.md` — component boundaries, integration points
2. `.ai/memory/state.md` — current task status, active blockers
3. `.ai/principles/architecture.md` — patterns to enforce, boundaries not to cross
4. `.ai/principles/coding.md` — code style, naming, error-handling, forbidden patterns
5. `.ai/principles/domain.md` — domain rules, terminology, business constraints
6. `.ai/adr/index.md` — past decisions that constrain current implementation
7. `.ai/context/runbook.md` — test/lint/build commands (required for Final Verification)

Report: "Execution context loaded: [files read]"

---

## Step 0 — State Check

Read `state.md` and `plan.md` in the task directory. Read `## Subtask Progress` blocks (one per T-XX) from the parent `state.md`.

- If `state.md` is not found in the task directory → report: "state.md not found. Run `/phase-discovery` first." **Stop.**
- If `discovery` is not `complete` → report: "Discovery not complete. Run `/phase-discovery` first." **Stop.**
- If `execution: complete` → report: "Execution already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation before continuing.
- If `execution: in-progress` → find first incomplete subtask, continue from it.
- If `execution: not-started` → start from first subtask per `plan.md` order.

Output status summary:
- Completed (`done` / `reviewed`): list.
- Skipped (`blocked` / `deferred`): list with reasons.
- Pending: list — will be executed.

If no pending subtasks → suggest `/phase-validation`. **Stop.**

---

## Execution

Update `## Phases` in `state.md`: set `execution: in-progress`.

**Flow-tier branch (read `flow:` from `state.md`).** If `flow: quick`, there are no T-XX
subtasks and no `plan.md` subtask list; ignore the "no pending subtasks" stop in Step 0.
Run the inline TDD step first — the quick tier has no `/pae-tests` invocation, but RED before
GREEN is mandatory: classify the level with the `tdd` gate, write the failing tests against
`## Contract (quick) → ### Acceptance Criteria`, observe them fail for the expected reason, and
record the result under `## TDD (quick)` (format and the `level: none` justification rules are
in `quick-flow → The quick path`). Only then implement against the `## Contract (quick)`
section and the spec's steps, honouring its `### Off-limits` and `### Invariants`, keeping the
RED set frozen, and recording `green-observed:` before running `/pe-finalize`. **Mid-flight escalation:**
if implementation breaches any gate condition — a fourth file becomes necessary, a new
invariant surfaces, a shipped-pipeline behaviour must change, or a migration is required —
STOP, promote to `full` per the `quick-flow` rule (set `flow: full`, add a
`## Flow Escalation` line with the reason, ensure a task directory exists, and run
`/pd-decompose` on the remaining work), and continue on the full path. Never silently finish
a quick task after a breach. If `flow: full`, run the steps below unchanged.

Run child workflows in order:
1. Call `/pe-execute <task-directory>` — Execute all pending subtasks
2. Call `/pe-finalize <task-directory>` — Summary report + finalization

After all steps complete, report to the user (display as text — do NOT invoke):
- Number of completed subtasks.
- Path to `plan.md` with updated statuses.
- "Execution complete. Run `/phase-validation <task-directory>` to start validation."

**STOP. Do not run `/phase-validation` automatically.**
