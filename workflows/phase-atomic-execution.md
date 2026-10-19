---
description: Atomic Execution orchestrator — Execute a single T-XX subtask step by step using its description.md
---

Invocation: `/phase-atomic-execution <path-to-atomic-description>`
Example: `/phase-atomic-execution .ai/tasks/todo/task_foo/T-01-slug/description.md`

If path is not provided — ask the user and do not continue.
Atomic task directory = parent directory of the provided `description.md`.
Parent task directory = one level above.

To run a single step directly, call the child workflow:
`/pae-tests`, `/pae-implement`, `/pae-finalize`.

This cycle is test-first: `/pae-tests` establishes RED before any implementation code is
written. The governing contract is the `tdd` rule.

---

## Context Bootstrap

Follow `phase-atomic-execution` rules — ## Context Bootstrap.

**Resolve paths first:** Read `T-XX/description.md → ## Context → working_dir:`.
- If `working_dir:` present: `WORK_DIR = <resolved absolute path>`, `AI_DIR = WORK_DIR/.ai`
- If absent: `WORK_DIR = <current directory>`, `AI_DIR = .ai`
- Umbrella: if `AI_DIR/../.ai/` exists → load umbrella first, then `AI_DIR` (local overrides)

Report: "WORK_DIR=<path>, AI_DIR=<path>"

Load in order, skip missing files:

1. `AI_DIR/memory/architecture.md` — component boundaries, integration points
2. `AI_DIR/memory/state.md` — current task status, active blockers
3. `AI_DIR/principles/architecture.md` — patterns to enforce
4. `AI_DIR/principles/coding.md` — style, naming, error-handling, forbidden patterns
5. `AI_DIR/principles/domain.md` — domain rules, terminology
6. `AI_DIR/adr/index.md` — decisions that constrain this implementation
7. `AI_DIR/context/runbook.md` — test/lint/build commands (required for both the TDD RED step and Final Verification)

Report: "Atomic execution context loaded from AI_DIR=<path>: [files read]"

---

## Step 0 — State Check

Read parent `state.md` (one level above the atomic task directory) and `T-XX/description.md`.

- If `T-XX/description.md` does not exist → **stop**: "description.md not found. Run `/pd-decompose` + `/pd-finalize` in the parent task."
- Verify `T-XX/description.md` contains both `## Steps` and `## Acceptance Criteria`. If either is missing → **stop**: "description.md is incomplete (missing ## Steps or ## Acceptance Criteria). Run `/pd-decompose` + `/pd-finalize` to regenerate."
- Look up this T-XX block in parent `state.md → ## Subtask Progress`:
  - If block is missing → treat as `atomic-execution: not-started` (will be created).
  - If `atomic-execution: complete` → report: "Atomic execution already complete." **Stop.**
  - If `atomic-execution: blocked` → run **Blocker Reconciliation** (`phase-atomic-execution` rules). If the blocker is a dependency/status blocker whose prerequisites are all satisfied → clear it automatically, record the reconciliation in `last_action`/`notes`, and continue. Otherwise (non-status blocker, or a prerequisite still unmet) → report the blocker and ask "Is it resolved? (yes/no)". **Wait.**
  - If `atomic-execution: in-progress` → continue from `last_action` (may require re-running last step for idempotency).
  - If `atomic-execution: not-started` → start from step 1 of `## Steps`.

**TDD entry point.** Read `atomic-tests:` from the same block (see the `tdd` rule for the
value set). It selects where this cycle resumes:
  - `not-started`, or the field is absent **and** `atomic-execution: not-started` → start at `/pae-tests`.
  - Field absent **and** `atomic-execution: in-progress` → pre-TDD task already underway. Do not retroactively demand RED. Append to `notes:` — `pre-TDD task, TDD step skipped` — and resume at `/pae-implement`.
  - `red` → RED already reached; resume at `/pae-implement`.
  - `n-a` → gate returned `none` with a recorded justification; resume at `/pae-implement`.
  - `green` → implementation already passed its tests; resume at `/pae-finalize`.
  - `failed` → RED could not be established. Report the recorded reason and **wait** — do not implement against a test set that never went red.

T-XX directories no longer contain their own `state.md` or `plan.md`. All progress lives in the parent's `## Subtask Progress`.

---

## Execution

Update parent `state.md → ## Subtask Progress` block for this T-XX: set `atomic-execution: in-progress`.

Run child workflows in order, skipping steps already satisfied per the TDD entry point above:
1. Call `/pae-tests <path-to-atomic-description>` — RED: classify test level, write failing tests from `## Acceptance Criteria`, observe them fail
2. Call `/pae-implement <path-to-atomic-description>` — GREEN: execute steps from `## Steps` until the RED tests pass, then refactor + verify
3. Call `/pae-finalize <path-to-atomic-description>` — Update parent state/plan

Step 1 is skipped only when `atomic-tests:` is already `red`, `n-a`, or `green`, or when this
is a pre-TDD task resumed mid-execution. It is never skipped to save time.

After completion, report:
- TDD level and RED→GREEN result (tests written, tests passing).
- Steps completed.
- Verification result.
- Next: `/phase-atomic-validation <path>`.
