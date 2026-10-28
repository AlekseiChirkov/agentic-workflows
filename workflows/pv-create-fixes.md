---
description: Validation Step 4 — Create fix-task subtask directories from approved issues
---

Invocation: `/pv-create-fixes <task-directory>`
Called by: `/phase-validation` as Step 4.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md` in the task directory.
2. Check `## Phases → validation`. If `complete` → **stop**: "Validation phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Check `## Issue List` with `### Approved` present in `state.md`. If missing → **stop**: "Step 3 (/pv-issues) must be completed first. Run /pv-issues <path>."
4. Check existing issue-to-fix assignments and `## Fix-Tasks`. Reuse them on resume.
   If `fixes-created: complete` exists and every approved issue is already assigned,
   report the existing fixes and return. An initial empty approval list must still write
   the zero-fix marker below.
   Newly approved issues append new assignments/work; replacing an existing assignment
   or completed description requires explicit confirmation. Never overwrite completed fixes.
5. Otherwise → continue.

---

## Context Bootstrap

Load the `phase-validation` rule (`## Context Bootstrap`) before writes, including standalone calls.
Quick tasks apply approved fixes inline in `/phase-validation`; do not create atomic fixes.

## Instructions

1. Read `state.md → ## Issue List → ### Approved`, existing classification, and Created list.
   Operate only on new approved issues or incomplete creations; preserve prior IDs, groups,
   directories, progress, and decisions. Reuse existing artifacts on resume.

   **Empty-Approved early exit.** If `### Approved` is empty or `None` (all issues deferred or no issues found):
   - If a prior Created list exists, preserve its IDs/count and report zero new fixes;
     do not reset completed work to zero. Otherwise upsert in `state.md`:
     ```
     ## Fix-Tasks
     fixes-created: complete
     fixes-count: 0
     Created: none
     ```
   - Report to user: "No approved issues. Skipping `/pv-execute-fixes`. Proceeding to `/pv-finalize`."
   - Do not execute any of the steps below. The `fixes-count: 0` field in `## Fix-Tasks` in `state.md` is the contract the orchestrator uses to skip Step 5.

1b. **Classify the approved issues.** Call `/pv-classify-fixes <task-directory>`. It writes
   `## Fix-Tasks → ### Fix Classification`, deciding for each issue whether it joins a shared
   fix branch (it clears the `quick-flow` gate) or gets a dedicated one (it breaches the gate,
   or its severity is `critical`). Use that table when assigning fix-task IDs and, in
   orchestrated mode, when creating branches.

2. Read `plan.md` → determine fix-task IDs. **Two cases apply:**

   **Case A — Fix for a top-level leaf or a top-level context (standard, unchanged):**
   Continue numbering after the highest existing top-level T-XX number. Fix-task ID: `T-NN-fix-<slug>`.

   Use one fix-task per distinct ID in the classification table's `Branch` column:
   - Each `dedicated` issue becomes its own fix-task, `T-NN-fix-<slug>`.
   - Each `shared` group becomes **one** fix-task, `T-NN-fix-<group-slug>`, whose
     `description.md` covers every issue in that group (one `## Steps` entry and at least one
     Acceptance Criterion per issue). The name is the one the classifier already wrote in the
     table's `Branch` column — reuse it verbatim, do not re-derive it.

   Persist every allocated ID in `Created:`; `/pv-execute-fixes` consumes this list,
   including the sibling form below. Do not discover fixes with a top-level-only glob.

   **Case B — Fix for a child of a composite (D8):**
   The issue references a specific child leaf (e.g. T-04b). Apply D8 naming:
   - Determine the parent composite ID (e.g. `T-04`) and existing children (e.g. T-04a, T-04b, T-04c).
   - Next sibling letter = letter after the highest existing child letter (e.g. after `c` → `d`).
   - Fix-task ID: `T-04d-fix-<slug>` (sibling letter + fix suffix).
   - Reuse the classifier's sibling ID; add it to the composite's `children:` list in
     both its progress block and description. Derive membership from the actual list,
     not a letter-suffixed ID alone.
   - **Revert the parent composite** whenever a new child fix opens, including a previously failed integration check:
     - Set `integration-validation: not-started` in the composite block.
     - Set `rollup: in-progress` in the composite block.
     - Update `plan.md` composite row `Status` from `reviewed` → `in-progress`.
     - This ensures the composite never falsely reports as reviewed while a fix is open.

3. For each fix-task ID determined in step 2 (one per dedicated issue, one per shared group), create a new subtask directory with that ID, containing exactly ONE file:
   - `description.md` — following the same six-section template `/pd-decompose` uses for a leaf
     subtask (`## Goal`, `## Context`, `## Scope`, `## Steps`, `## Acceptance Criteria`,
     `## Test Plan`); see `/pd-decompose` step 3. The source skeleton is
     `templates/subtask-description.md` in Orchestrail — it is not copied into projects,
     so do not look for it under the project root.

   `## Test Plan` is required. Derive scenarios from the approved issue: reproduce the
   defect before implementing its fix, then run the standard atomic cycle. Preserve each
   issue's Acceptance Criteria when a shared group combines issues.

   For issues where a reproducing test is genuinely impossible (a documentation correction, a
   naming change with no behaviour), set `Level: none` with the justification required by the
   `tdd` rule.

   Do NOT create `state.md` or `plan.md` inside fix-task directories. All progress is tracked in the parent task's `## Subtask Progress`.

   Fix-task progress tracking (atomic-tests, atomic-execution, atomic-validation status) follows the same format as regular T-XX leaf blocks and is written under `## Subtask Progress` in the parent `state.md`. Do NOT create a separate `## Fix-Task Progress` section.

4. Update top-level `plan.md` → add new fix-task rows to `## Subtasks` table with status `not-started`.
   - For Case A fixes: add as standard rows (no `Type` column change needed unless the overall plan already uses types).
   - For Case B fixes (D8): add with `Type: leaf`; `Depends On` = the composite's other children (or the child being fixed); include the fix row immediately after its parent composite's child rows.

5. Update `state.md`:
   Upsert a canonical block for each new fix under `## Subtask Progress`, preserving existing progress. Initialize new blocks with
   `atomic-tests: not-started`, both atomic phases `not-started`, `blocker: none`,
   and required `target_files:` / `notes:` even when empty.
   a. Upsert `## Fix-Tasks` (create if absent), unioning prior/new Created IDs once and counting the complete list:
   ```
   ## Fix-Tasks
   fixes-created: complete
   fixes-count: <N>
   Created: T-XX-fix-<slug>, T-04d-fix-<slug>, ...
   ```
   Besides these three lines, the section carries only the `### Fix Classification` table written by `/pv-classify-fixes`. Do NOT add progress blocks here — fix-task progress lives in `## Subtask Progress` like any other leaf.
   b. In `## Issue List → Deferred`, mark deferred issues with status `deferred`.
   c. For Case B fixes: note the composite reversion in the composite's `notes:` field: "fix T-04d created for T-04b; integration-validation reset."
6. **Orchestrated mode only** (`/spec-run`): fix branches extend the stack from its tip.
   Each shared-group fix has one branch and pull request; each dedicated fix has its own.
   Branch naming (feature-based, no identifiers) and commit type (`fix:`) follow `git-flow`. Record `branch:`,
   `base_branch:`, `base_commit:`, `commits:`, and `pr:` in each fix-task's progress block
   exactly as for a regular subtask.

7. Report: "Step 4 (Create Fix-Tasks) complete. Created N fix-tasks: T-XX, T-YY, ..."
Return to the caller; this is a progress marker.
