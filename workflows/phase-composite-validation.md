---
description: Integration validation for a composite subtask — runs after all children are individually reviewed
---

Invocation: `/phase-composite-validation <path-to-composite-description>`
Example: `/phase-composite-validation .ai/tasks/todo/task-01-feature/T-04-component/description.md`

Called by: `/pav-close` (automatically, when the last child of a composite is reviewed) or manually.

If path is not provided — ask the user and do not continue.
Composite task directory = parent directory of the provided `description.md`.
Parent task directory = one level above the composite task directory.

---

## Context Bootstrap

Load the `phase-atomic-validation` rule (`## Context Bootstrap`) for the composite's `working_dir:`
before code reads or writes. Resolve that path relative to its description directory;
keep parent task paths absolute. Resolve each child's `target_files:` against that child's
own `working_dir:` so multi-repo integration reads the correct files. Run relevant tests
and lint from the corresponding service runbooks; report unavailable checks.

**Orchestrated mode (`/spec-run`) — do not write the shared files.** Return the composite
block, plan rows, Integration Issues, fix-sibling artifacts, and compression as deltas for
the orchestrator (`orchestration → ## Shared-file discipline`). The Validator's own leaf
block exemption never covers its composite. In other modes apply the edits below.

## Guard

Step 0 — Prerequisites

1. Read the composite `description.md`. Verify `## Context` contains `type: composite` and `children:` list.
   If not → **stop**: "This is not a composite description.md. Use `/phase-atomic-validation` for leaf subtasks."

2. Read parent `state.md`. Locate the composite block `[composite] T-XX | …` in `## Subtask Progress`.
   If block is missing → **stop**: "No composite block found for T-XX in state.md. Run `/pd-decompose` first."

3. Check `integration-validation` field in the composite block:
   - If `integration-validation: complete` → **stop**: "Integration validation already complete. Re-running will overwrite. Confirm? (yes/no)" Wait for explicit confirmation.
   - If `integration-validation: in-progress` or `failed` → rerun the integration check against current evidence; reuse recorded decisions and existing fix siblings rather than recreating them.
   - If `integration-validation: not-started` or absent → start from step 1.

4. Verify all children are individually reviewed:
   - Read `children:` list from the composite block.
   - For each child: check `atomic-validation: complete` in its leaf block.
   - If any child is NOT `complete` → **stop**: "Integration validation cannot run: child T-XXb is not yet reviewed (atomic-validation: <current status>). Complete all children first."

---

## Step 1 — Integration check

Update composite block in parent `state.md`: set `integration-validation: in-progress`.

1. Read composite `description.md → ## Acceptance Criteria` (these are integration-level criteria — verified AFTER children, against the combined result of all children's work).
2. Read parent `state.md → ## Solution Design → ### Invariants` and `### Off-limits`.
3. Collect all `target_files:` from every child's leaf block in `## Subtask Progress`. Union of all files changed by any child = the integration surface.
4. Read the changed files.

Check each integration Acceptance Criterion with executable evidence; mark partial/unmet
ones `[INCOMPLETE]`. Verify producer/consumer outputs agree across component/repo boundaries,
shared API/schema contracts work end-to-end, and combined changes preserve Invariants /
Off-limits. Report interface mismatches, untested seams, and missing integration glue with
reproduction, affected files, and `critical` / `important` / `optional` severity.

**Verdict:**
- **DONE**: all integration AC met, no critical or important integration bugs.
- **NEEDS WORK**: has `[INCOMPLETE]` criteria, critical, or important bugs.

---

## Step 2 — Verdict and close / fix

**If DONE:**

1. Update composite block in parent `state.md`:
   - Set `integration-validation: complete`.
   - Set `rollup: done` (confirming complete execution + validation).
   - Append `integration validation passed — <evidence summary>` to `notes:`; preserve the classifier rationale.
   - Set `blocker: none`.

2. Update parent `plan.md`: set composite row `Status` to `reviewed`.
   (Translation: `integration-validation: complete` → `plan.md: reviewed` — only composites follow this rule; leaf translation is unchanged.)

3. Run `/compress-state --auto` on parent `state.md`.

4. Report: "Composite T-XX integration validation passed. Status: reviewed."

**If NEEDS WORK:**

1. Update composite block in parent `state.md`:
   - Set `integration-validation: failed`.
   - In `notes:` list the specific integration Acceptance Criteria that were not met plus critical/important bug summary.
   - Set `rollup: in-progress` (composite is not done yet).
   - Keep composite row in `plan.md` at `done` while no approved fix is pending; use `in-progress` once a fix sibling exists.

2. **Present failures and record approve/defer decisions** before creating any fix work.

   a. Compile the integration failures as a numbered list, in the same shape `/pv-issues` uses:
      ```
      [N]. <what failed>
           Problem: <unmet integration criterion, interface mismatch, or seam failure>
           Solution: <what the fix must do>
           Priority: critical | important | optional
      ```
   b. **Interactive mode (default):** present the list and **wait for the user's decision** —
      which failures to fix now, which to defer.
   c. **Autonomous mode** (`/phase-pipeline`, `/spec-run`): do not wait. Approve every
      `critical` and `important` failure, defer every `optional` one. Record the automatic split.
   d. Write the decision to the parent `state.md` before creating any directory:
      ```
      ## Integration Issues (T-XX)

      ### Approved
      <numbered items approved for a fix sibling, or "None">

      ### Deferred
      <numbered items deferred, with reason, or "None">
      ```
      Deferring every failure is a valid outcome: record it, leave
      `integration-validation: failed`, create no sibling, and report that the composite stays
      unreviewed pending a decision.

3. **D8 — Create a fix sibling:** for each item under `### Approved` in step 2d, determine the next available sibling letter after the highest existing child letter. In orchestrated mode this whole step is returned as a delta, not performed — see the clause above; the orchestrator creates the directory and writes the rows:
   - Existing children T-04a, T-04b, T-04c → next letter is `d`.
   - Create directory `T-04d-fix-<slug>/` with a `description.md` following the standard six-section template (Goal, Context, Scope, Steps, Acceptance Criteria, Test Plan). The fix targets the integration failure. Its `## Test Plan` scenarios are derived from the integration failure itself — the test that reproduces the failure is the RED test `/pae-tests` will write.
   - Reuse an existing sibling already assigned to this approved issue on resume.
   - Add T-04d to the composite's `children:` list in the composite block and description;
     preserve matching lists as the source of membership.
   - Add T-04d to `plan.md → ## Subtasks` table with `Type: leaf` and `Status: not-started`.
   - If `## Fix-Tasks` already exists, append each new sibling once to `Created:` and update `fixes-count:`; preserve existing entries/classification.
   - Add a canonical leaf block with `atomic-tests: not-started`, empty `target_files:` / `notes:`, and `blocker: none` in `state.md → ## Subtask Progress`.
   - **Revert the composite's `integration-validation` field to `not-started`** in the composite block (the composite is not reviewed until the fix closes and integration validation re-runs).
   - Update `plan.md` composite row `Status` back to `in-progress`.

4. Report failures, approved/deferred counts, and actual sibling paths (or "none").
   State who made the decision and whether writes were applied or returned as deltas.
   In an active execution loop, return new sibling work to the caller; standalone, display
   `/phase-atomic-execution <fix-description>` followed by the integration recheck.
   Do not claim a sibling was created when all failures were deferred.

**Stop. Do not auto-advance.** Return to an active caller as a progress marker; the caller
may schedule approved siblings within its current phase.
