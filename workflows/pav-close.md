---
description: Atomic Validation Step 3 — Close the task, update parent plan status to reviewed
---

Invocation: `/pav-close <path-to-atomic-description>`
Called by: `/phase-atomic-validation` as Step 3. Only runs if verdict is DONE.

Atomic task directory = parent directory of the provided `description.md`.
Parent task directory = one level above.

---

## Guard

1. Read parent `state.md`. Locate the `## Subtask Progress` block for this T-XX.
2. If block has `atomic-validation: complete` → **stop**: "Atomic validation already complete. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Otherwise → continue.

---

## Pre-check

Read parent `state.md → ## Subtask Progress` block for this T-XX.
If `atomic-validation: failed` → **stop**: "Cannot close: verdict is NEEDS WORK."
If `last_action` is not `pav-propose done` → **stop**: "Complete `/pav-propose` before closure."
Load the `phase-atomic-validation` rule (`## Context Bootstrap`) before project writes, including standalone invocation.

---

## Instructions

Before updating plan.md in step 2, load `workflow-reference` for the Status Translation Table.

1. Update parent `state.md → ## Subtask Progress` block for this T-XX:
   - Set `atomic-validation: complete`.
   - Update `last_action:` to a one-line summary (DoD status + key outcome).
   - Keep `blocker: none` and preserve `notes:` — including the `tdd:` audit lines.
   - Preserve `target_files:` as set by `/pae-tests` and `/pae-implement`.
   - Preserve `atomic-tests:` (`green` or `n-a`). Never remove or downgrade it.

2. Update parent `plan.md`: set the `Status` column for this T-XX row to `reviewed`.
   (Translation: atomic-validation `complete` → plan.md `reviewed` — per Status Translation Table in workflow-reference)

   **Orchestrated mode (`/spec-run`) — do not write the file.** Running as the Validator
   sub-agent, report the transition (`T-XX → reviewed`) as a delta and let the orchestrator
   apply it; `plan.md` has exactly one writer (`orchestration → ## Shared-file discipline`). In
   every other mode, make the edit here. State which mode applies in the step 6 report.

3. Do NOT write to `T-XX/state.md` — it does not exist in the new structure.

4. Run `/compress-state --auto` on the parent task's `state.md`; under `/spec-run`, return this shared edit as a delta.

5. **Composite integration-validation trigger (only when this T-XX is a leaf child of a composite).**

   Find a composite block whose actual `children:` list contains this leaf. No membership
   → skip step 5. Do not infer membership or derive a parent from ID spelling; Type 3
   leaves and promoted letter-suffixed parents can use overlapping ID forms.
   For the matched composite:
   a. Read all sibling children listed in `children:` of the composite block.
   b. Check their atomic-validation status in `## Subtask Progress`.
   c. If ALL siblings have `atomic-validation: complete`:
      - Verify the composite's `description.md` exists (`T-04-<slug>/description.md`) and contains `## Acceptance Criteria`.
      - If already `integration-validation: complete`, preserve the result; do not retrigger.
      - If yes and validation is not already complete → call `/phase-composite-validation <path-to-composite-description.md>`.
        Under `/spec-run`, return shared updates and any new sibling creation as deltas.
      - If no → **stop**: "Composite T-04 has no description.md or missing ## Acceptance Criteria. Re-run `/pd-decompose` to regenerate."
   d. If NOT all siblings are complete → do not trigger yet; report "Waiting for siblings: T-04c (not yet reviewed)."


6. Report: "Task T-XX closed. Status: reviewed. Parent `plan.md` and `## Subtask Progress` updated (or returned as deltas)."
This is a progress marker; return composite failures to the caller before continuing.
