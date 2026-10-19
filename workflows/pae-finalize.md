---
description: Atomic Execution Step 3 — Update statuses in atomic and parent state files, compress
---

Invocation: `/pae-finalize <path-to-atomic-description>`
Called by: `/phase-atomic-execution` as Step 3.

Atomic task directory = parent directory of the provided `description.md`.
Parent task directory = one level above.

---

## Guard

1. Read parent `state.md`. Locate the `## Subtask Progress` block for this T-XX.
2. If block has `atomic-execution: complete` → ask: "This subtask is already complete. Confirm re-run? (yes/no)" Wait for explicit confirmation before proceeding. Do NOT block unconditionally.
3. Otherwise → continue.

---

## Pre-check

Read parent `state.md → ## Subtask Progress` block for this T-XX.
If `atomic-execution: complete` is NOT present in the block → **stop**: "pae-implement must complete successfully before pae-finalize can run."

Check `atomic-tests:` in the same block. It must be `green` or `n-a` — those are the only
values consistent with a completed execution. If it is `red`, `failed`, or `not-started`
while `atomic-execution: complete` → **stop**: "Inconsistent state: execution is complete but
`atomic-tests: <value>`. `/pae-implement` did not reach GREEN. Re-run it before finalizing."
If the field is absent → pre-TDD task; continue without it.

---

## Instructions

Before updating plan.md in step 2, load `workflow-reference` for the Status Translation Table.

After atomic-execution completes for T-XX:

0. **Working directory resolution** (same as `/pae-implement`).
   Read `T-XX/description.md → ## Context` for `working_dir:` field.
   - If present: `WORK_DIR = <resolved path>`, `AI_DIR = WORK_DIR/.ai`.
   - If absent: `WORK_DIR = <current directory>`, `AI_DIR = .ai`.

1. Update parent `state.md → ## Subtask Progress` block for this T-XX:
   - Set `atomic-execution: complete`.
   - Fill `last_action:` with a one-line summary of what was implemented.
   - Set `blocker: none` (or describe if execution finished in a blocked state).
   - Preserve `atomic-tests:` as set by `/pae-tests` / `/pae-implement` (`green` or `n-a`). Never remove or downgrade it.
   - Preserve `notes:` if already set by `/pae-tests` or `/pae-implement` — including the `tdd:` lines (level, justification, test amendments).
   - Preserve `target_files:` as set by `/pae-tests` and `/pae-implement` — test files included.

1b. Architecture self-update check.
    Read `.ai/memory/architecture.md` (path resolved via AI_DIR from step 0).
    For each module created or significantly modified in this subtask
    (derived from `target_files:` set by /pae-implement):
    - If the module is NOT described in `architecture.md` → add a one-paragraph
      entry: module name, purpose, key exports, which layer it lives in.
    - If the module IS described but its interface changed → update that entry in place.
    - If no new modules and no interface changes → skip without error.
    Write "architecture.md updated: <module list>" or "architecture.md: no update needed"
    to the `notes:` field in the Subtask Progress block (append, do not overwrite existing notes).
    If `architecture.md` does not exist → skip without error.

2. Update parent `plan.md`: set the `Status` column for this T-XX row to `done`.
   (Translation: atomic-execution `complete` → plan.md `done` — per Status Translation Table in workflow-reference)

   **Orchestrated mode (`/spec-run`) — do not write the file.** Running as the Implementer
   sub-agent, report the transition (`T-XX → done`) as a delta and let the orchestrator apply
   it; `plan.md` has exactly one writer (`orchestration → ## Shared-file discipline`). In every
   other mode, make the edit here. State which mode applies in the step 5 report.

3. Do NOT write to `T-XX/state.md` or `T-XX/plan.md` — those files do not exist in the new structure.

4. Run `/compress-state --auto` on the parent task's `state.md`.

5. Report: "Atomic execution complete for T-XX (TDD: <level>, <N> tests green). Parent `## Subtask Progress` and `plan.md` updated. Next: `/phase-atomic-validation <path>`."

6. **Incremental composite rollup (only when this T-XX is a leaf child of a composite).**

   Detect: if the current subtask ID matches the pattern `T-\d+[a-z]` (letter suffix), it **may** be a child OR a Type 3 leaf — verify below by checking for an actual parent composite block in `state.md`; do not treat the ID pattern alone as proof of childhood. Derive candidate parent composite ID by removing the letter suffix (e.g. `T-04a` → candidate `T-04`).

   If the parent composite block exists in `state.md → ## Subtask Progress`:
   a. Read all sibling children listed in `children:` of the composite block.
   b. Check their atomic-execution status in `## Subtask Progress`.
   c. Compute new rollup:
      - If any child has `atomic-execution: blocked` → `rollup: blocked`.
      - Else if all children have `atomic-execution: complete` → `rollup: done`.
      - Else → `rollup: in-progress`.
   d. Update the composite block's `rollup:` field in `state.md`.
   e. Update `plan.md` composite row `Status`:
      - `rollup: done` → `Status: done`
      - `rollup: blocked` → `Status: blocked`
      - `rollup: in-progress` → `Status: in-progress`
   f. Update composite's `blocker:` field:
      - `rollup: blocked` → copy the blocking child's `blocker:` description.
      - Otherwise → `blocker: none`.

   If this subtask ID does NOT match the child pattern → skip step 6 without error.
