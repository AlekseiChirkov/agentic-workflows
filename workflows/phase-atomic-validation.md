---
description: Atomic Validation orchestrator — Validate a single T-XX subtask: check, propose improvements, close
---

Invocation: `/phase-atomic-validation <path-to-atomic-description> [--batch]`
Example: `/phase-atomic-validation .ai/tasks/todo/task_foo/T-01-slug/description.md`

If path is not provided — ask the user and do not continue.
Atomic task directory = parent directory of the provided `description.md`.
Parent task directory = one level above.

`--batch` flag: when present, pass it through to `/pav-propose` so improvement proposals are recorded without blocking for user input. Use this flag when called from `/pe-execute` (batch execution loop). When called standalone — omit the flag to preserve interactive behaviour.

To run a single step directly, call the child workflow:
`/pav-check`, `/pav-propose`, `/pav-close`.

---

## Context Bootstrap

Load the `phase-atomic-validation` rule (`## Context Bootstrap`) before reading implementation files or
writing project files; run the full bootstrap when invoked standalone. The rule owns
the load order, umbrella precedence, conditional sources, and reporting.

Resolve the description and parent task paths before changing directories. Resolve
`working_dir:` from `description.md → ## Context` relative to the atomic task directory;
if absent, use the invocation directory. Set `WORK_DIR` to that absolute directory
and `AI_DIR = WORK_DIR/.ai`. The umbrella is `WORK_DIR/../.ai`.
Keep task-artifact paths absolute; run code reads, writes, and commands in `WORK_DIR`.

---

Under `/spec-run`, write only this leaf's progress block and permitted code/tests.
Return proposals sections, composite state, plan changes, new sibling descriptions, and
compression as deltas under `orchestration → ## Shared-file discipline`.

## Guard

Step 0 — State Check

Read parent `state.md`. Locate the `## Subtask Progress` block for this T-XX.

**Input for validation:**
- `T-XX/description.md → ## Acceptance Criteria` — source of truth for what "done" means.
- The subtask's tests (from `target_files:`) plus `atomic-tests:` — the executable form of
  those criteria. `/pav-check` audits both that they pass and that they were not weakened.
- Parent `state.md → ## Subtask Progress → T-XX` block — context on what was done (`last_action`, `target_files:`, `notes`).
- Parent `state.md → ## Solution Design` — `### Invariants`, `### Off-limits`.

Checks:
- If `T-XX/description.md` is missing or has no `## Acceptance Criteria` → **stop**: "description.md is incomplete. Run `/pd-decompose` + `/pd-finalize`."
- If the `## Subtask Progress` block for this T-XX is missing → **stop**: "No execution record for T-XX. Run `/phase-atomic-execution` first."
- If `atomic-execution` is not `complete` → **stop**: "Atomic execution not complete. Run `/phase-atomic-execution` first."
- If `atomic-validation: complete` → **stop**: "Atomic validation already complete."
- If `atomic-validation: in-progress` → resume from the step the recorded `last_action:` marker
  names. Every resume point below is a value some workflow actually writes:

  | `last_action:` in the block | Resume at |
  |---|---|
  | `pav-check DONE` (written by `/pav-check`) | step 2 — `/pav-propose` |
  | `pav-propose done` (written by `/pav-propose` step 6, in every mode) | step 3 — `/pav-close` |
  | anything else, or absent | step 1 — `/pav-check`; it re-derives the verdict from the criteria and its own Guard handles the repeat |

  Do not infer the resume point from `## Improvement Proposals (T-XX)`: `/pav-propose` writes
  that section only when proposals are non-empty, so its absence does not mean step 2 was
  skipped.
- If `atomic-validation: not-started` (or field absent) → start from Step 1.

---

## Execution

Update parent `state.md → ## Subtask Progress` block for this T-XX: set `atomic-validation: in-progress`.

Run child workflows in order, skipping completed steps:
1. Call `/pav-check <path-to-atomic-description>` — Final check against `## Acceptance Criteria` + verdict (DONE / NEEDS WORK).
2. Call `/pav-propose <path-to-atomic-description> [--batch if --batch was passed to this workflow]` — Improvement proposals (only if DONE).
3. Call `/pav-close <path-to-atomic-description>` — Close task (only if DONE).

After each call, re-read its result. `/pav-check` owns `failed`; `/pav-close` owns `complete`.
A failed/stopped check ends this cycle immediately; do not run proposals or closure and do
not overwrite the failure with completion. Surface findings before creating fix-tasks.
A resumed `failed` record requires repaired implementation and a fresh `/pav-check`.

After completion, report final verdict and updated status.

This completion is a progress marker for the active caller, not a handoff.
