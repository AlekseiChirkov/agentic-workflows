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

Follow `phase-atomic-validation` rules — ## Context Bootstrap.

**Resolve paths first:** Read `T-XX/description.md → ## Context → working_dir:`.
- If `working_dir:` present: `WORK_DIR = <resolved absolute path>`, `AI_DIR = WORK_DIR/.ai`
- If absent: `WORK_DIR = <current directory>`, `AI_DIR = .ai`
- Umbrella: if `AI_DIR/../.ai/` exists → load umbrella first, then `AI_DIR` (local overrides)

Report: "WORK_DIR=<path>, AI_DIR=<path>"

Load in order, skip missing files:

1. `AI_DIR/memory/architecture.md` — system invariants, integration contracts
2. `AI_DIR/memory/state.md` — what was executed, last known state
3. `AI_DIR/principles/architecture.md` — patterns the implementation must conform to
4. `AI_DIR/principles/coding.md` — code standards (deviations = findings)
5. `AI_DIR/principles/domain.md` — domain correctness rules
6. `AI_DIR/adr/index.md` — past decisions (violations = critical findings)
7. `AI_DIR/context/runbook.md` — commands for verification

Report: "Atomic validation context loaded from AI_DIR=<path>: [files read]"
Read `target_files` from parent `state.md → ## Subtask Progress → T-XX` AFTER context is loaded.

---

## Step 0 — State Check

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

After validation:
- Parent `state.md → ## Subtask Progress → T-XX`: set `atomic-validation: complete | failed`.
- If `failed` → add to `notes:` the specific Acceptance Criteria that were not met.
- Do NOT create fix-tasks automatically. Surface findings to the user first.

After completion, report final verdict and updated status.
