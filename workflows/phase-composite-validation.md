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

## Step 0 — Guard

1. Read the composite `description.md`. Verify `## Context` contains `type: composite` and `children:` list.
   If not → **stop**: "This is not a composite description.md. Use `/phase-atomic-validation` for leaf subtasks."

2. Read parent `state.md`. Locate the composite block `[composite] T-XX | …` in `## Subtask Progress`.
   If block is missing → **stop**: "No composite block found for T-XX in state.md. Run `/pd-decompose` first."

3. Check `integration-validation` field in the composite block:
   - If `integration-validation: complete` → **stop**: "Integration validation already complete. Re-running will overwrite. Confirm? (yes/no)" Wait for explicit confirmation.
   - If `integration-validation: in-progress` → continue from last completed step.
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

**Integration checks to perform:**
- Each integration-level Acceptance Criterion from `## Acceptance Criteria`: met / not met / partial. Mark `[INCOMPLETE]` if not fully met.
- **Cross-component coherence:** the outputs of child A are correctly consumed by child B (e.g. the producer component emits data in the format the consumer component correctly parses and processes, if cross-repo; or component A's output is correctly used by component B if same-repo).
- **No invariant violations** across the combined work of all children.
- **No off-limits violations** across the combined work.
- **Interface contracts**: integration-level contracts (e.g. shared IR format, shared API, shared data schema) are satisfied end-to-end.

**Bug detection (integration-scope only):**
- **Interface mismatches**: child A produces data in a shape child B cannot consume.
- **Seam failures**: the join between children's work has an untested edge case.
- **Missing integration glue**: a component assumed another component would handle something that neither actually did.

**Verdict:**
- **DONE**: all integration AC met, no critical or important integration bugs.
- **NEEDS WORK**: has `[INCOMPLETE]` criteria, critical, or important bugs.

---

## Step 2 — Verdict and close / fix

**Orchestrated mode (`/spec-run`) — do not write the shared files.** This workflow is reached
from `/pav-close` step 5 inside the **Validator** sub-agent, and everything the verdict
produces is shared: `plan.md`, the `[composite]` block, `## Integration Issues (T-XX)`, and any
D8 fix sibling with its directory, its `plan.md` row, and its leaf block. Report each of them
as a delta and let the orchestrator apply it; these files have exactly one writer
(`orchestration → ## Shared-file discipline`, which names this workflow explicitly). The
composite's block is **not** the Validator's own progress block — the carve-out for "its own
`## Subtask Progress` block" does not reach a composite's rollup row. In every other mode, make
the edits here. State which mode applies in the step 4 report.

**If DONE:**

1. Update composite block in parent `state.md`:
   - Set `integration-validation: complete`.
   - Set `rollup: done` (confirming complete execution + validation).
   - Update `last_action: integration validation passed — <one-line summary of what was validated>`.
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
   - Keep composite row in `plan.md` at `done` (children are done; composite is not yet reviewed).

2. **Present the failures and record an approve/defer decision.** This mirrors `/pv-issues`
   steps 3–5: in this system a finding becomes work only by an explicit, recorded decision, and
   step 3 below cannot evaluate "each approved fix" unless that decision exists.

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
      `critical` and `important` failure, defer every `optional` one — the same rule those
      workflows apply to `/pv-issues`. Record that the split was automatic.
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
   - Add T-04d to the composite's `children:` list in the composite block.
   - Add T-04d to `plan.md → ## Subtasks` table with `Type: leaf` and `Status: not-started`.
   - Add a leaf block for T-04d in `state.md → ## Subtask Progress`.
   - **Revert the composite's `integration-validation` field to `not-started`** in the composite block (the composite is not reviewed until the fix closes and integration validation re-runs).
   - Update `plan.md` composite row `Status` back to `in-progress`.

4. Report: "Integration validation NEEDS WORK. <N> failure(s) approved, <M> deferred. Fix sibling T-04d-fix-<slug> created. Run `/phase-atomic-execution` for T-04d, then re-run `/phase-composite-validation`." State whether the approve/defer split was made by the user or automatically, and whether the writes were applied here or returned as deltas for the orchestrator.

**Stop. Do not auto-advance.**
