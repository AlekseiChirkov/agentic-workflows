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

Load the `phase-atomic-execution` rule (`## Context Bootstrap`) before reading implementation files or
writing project files; run the full bootstrap when invoked standalone. The rule owns
the load order, umbrella precedence, conditional sources, and reporting.

Resolve the description and parent task paths before changing directories. Resolve
`working_dir:` from `description.md → ## Context` relative to the atomic task directory;
if absent, use the invocation directory. Set `WORK_DIR` to that absolute directory
and `AI_DIR = WORK_DIR/.ai`. The umbrella is `WORK_DIR/../.ai`.
Keep task-artifact paths absolute; run code reads, writes, and commands in `WORK_DIR`.

---

Under `/spec-run`, follow `orchestration → ## Shared-file discipline`: write only this
leaf's progress block and code/tests. Return architecture, composite, plan, and compression
updates as deltas for the orchestrator; this applies to every child in the cycle.

## Guard

Step 0 — State Check

Read parent `state.md` (one level above the atomic task directory) and `T-XX/description.md`.

- If `T-XX/description.md` does not exist → **stop**: "description.md not found. Run `/pd-decompose` + `/pd-finalize` in the parent task."
- Verify `T-XX/description.md` contains both `## Steps` and `## Acceptance Criteria`. If either is missing → **stop**: "description.md is incomplete (missing ## Steps or ## Acceptance Criteria). Run `/pd-decompose` + `/pd-finalize` to regenerate."
- Look up this T-XX block in parent `state.md → ## Subtask Progress`:
  - If block is missing → treat as `atomic-execution: not-started` (will be created).
  - If `atomic-execution: complete` and finalization is recorded (`pae-finalize done` or
    legacy plan `done`/`reviewed`) → report completion and return to the caller.
  - If execution complete but finalization is not recorded → resume `/pae-finalize`;
    do not rerun tests or implementation.
  - If `atomic-execution: blocked` → run **Blocker Reconciliation** (`phase-atomic-execution` rules). If the blocker is a dependency/status blocker whose prerequisites are all satisfied → clear it automatically, record the reconciliation in `last_action`/`notes`, and continue. Otherwise (non-status blocker, or a prerequisite still unmet) → report the blocker and ask "Is it resolved? (yes/no)". **Wait.**
  - If `atomic-execution: in-progress` → continue from `last_action` (may require re-running last step for idempotency).
  - If `atomic-execution: not-started` → start from step 1 of `## Steps`.

**TDD entry point.** Read `atomic-tests:` from the same block (see the `tdd` rule for the
value set). Unless the Guard already selected finalization, it selects the resume step:
  - `not-started`, or the field is absent **and** `atomic-execution: not-started` → start at `/pae-tests`.
  - Field absent **and** `atomic-execution: in-progress` → pre-TDD task already underway. Do not retroactively demand RED. Append to `notes:` — `pre-TDD task, TDD step skipped` — and resume at `/pae-implement`.
  - `red` or `pinned` → frozen tests already established; resume at `/pae-implement`.
  - `n-a` → gate returned `none` with a recorded justification; resume at `/pae-implement`.
  - `green` → implementation already passed its tests; resume at `/pae-finalize`.
  - `failed` → RED could not be established. Report the recorded reason and **wait** — do not implement against a test set that never went red.

T-XX directories no longer contain their own `state.md` or `plan.md`. All progress lives in the parent's `## Subtask Progress`.

---

## Execution

For a new leaf, create its canonical progress block with `atomic-tests: not-started` before
setting `atomic-execution: in-progress`; this prevents a new task from being mistaken for a
legacy pre-TDD resume. Preserve all existing test evidence and git fields.
Do not execute descriptions marked `type: composite`; run their leaf children instead.

Before requesting a model, spawning a worker or executing a child, apply
`workflow-reference → ### Model columns and resolution` to the parent plan row.
Read its active optional `Model (Claude)` / `Model (Codex)` column with legacy `Model`
and session-default compatibility. Resolve the configured or already-verified source root
through the canonical read-only guidance preflight. Use the same source root for the helper
and `$SOURCE_ROOT/docs/MODEL-CATALOG.md`, never CWD; installed skills read that absolute
guide, while [the relative guide](../docs/MODEL-CATALOG.md) serves source readers.
Missing guide/schema/rubric means selection unavailable: preserve session and inputs,
infer no scores/schema/candidates, and never bypass explicit-request eligibility.
Run the verified `model-catalog.py` helper with
`--resolve-plan <plan> --provider <provider> --row <row-id> --resolution <resolution.json>`;
use that guide for its exact input schema and keep
`execution: null`. Refresh the invocation support snapshot from actual permitted tools,
permissions and restrictions; verify requirements and owner limits before any request.
Report requested, resolved and actual identities plus visible fallback/stop reasons.
An unsupported explicit request requires an authorized eligible fallback or **stop**.
Missing Python 3.11, helpers or catalog makes selection unavailable: preserve the current
session and never bypass explicit request eligibility. Without switching capability,
execute inline in the same session only when its verified current identity satisfies
the request/fallback, or when no explicit request requires a switch, and note it.
Actual remains unknown until a separate matching current execution receipt with caller
provenance is available; a successful spawn alone is insufficient. Reuse a caller's
resolution only for the same invocation and unchanged support/restrictions.

Run child workflows in order, skipping steps already satisfied per the TDD entry point above:
1. Call `/pae-tests <path-to-atomic-description>` — RED: classify test level, write failing tests from `## Acceptance Criteria`, observe them fail
2. Call `/pae-implement <path-to-atomic-description>` — GREEN: execute steps from `## Steps` until the RED tests pass, then refactor + verify
3. Call `/pae-finalize <path-to-atomic-description>` — Update parent state/plan

Step 1 is skipped only when `atomic-tests:` is already `red`, `pinned`, `n-a`, or `green`, or when this
is a pre-TDD task resumed mid-execution. It is never skipped to save time.

Stop the cycle whenever a child stops or fails; never run the next child on an unresolved gate.

After completion, report:
- TDD level and RED→GREEN result (tests written, tests passing).
- Steps completed.
- Verification result.
- Next: `/phase-atomic-validation <path>`.

This is a progress marker for an active caller, not a phase handoff.
