---
description: Validation Step 5 — Execute fix-tasks via atomic execution → validation cycles
---

Invocation: `/pv-execute-fixes <task-directory>`
Called by: `/phase-validation` as Step 5.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md` in the task directory.
2. Check `## Phases → validation`. If `complete` → **stop**: "Validation phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Check `## Fix-Tasks → fixes-created`:
   - If the section is missing or the marker is absent → **stop**: "`/pv-create-fixes` has not been completed. Run it first."
   - If the marker is `complete` and `fixes-count: 0` is present → **stop**: "No fix-tasks were created (all issues deferred). `/pv-execute-fixes` has nothing to do. Proceed to `/pv-finalize`."
   - If the marker is `complete` with `fixes-count` greater than 0 → continue.
4. Otherwise → continue.

---

## Instructions

1. Read `plan.md` — identify all fix-tasks (T-XX-fix-*) that are not `reviewed`.
2. For each fix-task, verify `T-XX-fix-*/description.md` contains `## Steps` and `## Acceptance Criteria`. If missing → **stop**: "Fix-task description.md is incomplete. Run `/pv-create-fixes` to regenerate."
3. For each fix-task sequentially:
   a. Call `/phase-atomic-execution <path-to-fix-task/description.md>`
   b. Call `/phase-atomic-validation <path-to-fix-task/description.md> --batch`
      (`--batch` for the same reason `/pe-execute` step 2d passes it: a fix cycle is not the
      place to prompt for improvement proposals. Semantics — record only, apply nothing — are
      fixed in `workflow-globals → Workflow-declared mode overrides`.)

All global principles apply in full:
- Continue from stopping point if cycle was interrupted.
- Stop and wait for user decision at any blocker or ambiguity.
- After each completed fix-task, run `/compress-state --auto` on the parent task's `state.md`.
- Between fix-tasks, apply aggressive compression: remove intermediate reasoning, keep only final state.

4. Report: "Step 5 (Execute Fix-Tasks) complete. N fix-tasks reviewed."
