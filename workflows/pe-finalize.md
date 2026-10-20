---
description: Execution Step 2 — Summary report, update state files, compress context
---

Invocation: `/pe-finalize <task-directory>`
Called by: `/phase-execution` as Step 2.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md` in the task directory.
2. Check `## Phases → execution`. If `complete` → **stop**: "Execution phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Otherwise → continue.

---

## Instructions

Load `workflow-reference` for .ai/memory/state.md Entry Format and
.ai/project_state.md Update Rules before starting step 3.

**Flow-tier branch (read `flow:` from `state.md`).** If `flow: quick`, there are no T-XX
subtasks, no `plan.md`, and no `## Execution Report` — `/pe-execute` never runs on this tier
(`quick-flow → The quick path`). Skip steps 1, 2, 2b and the `plan.md` update in step 3, and
read the execution outcome from `## TDD (quick)` (`green-observed:`) plus the files the quick
task changed. If `green-observed:` is absent or does not read `yes` → **stop**: "Quick task
has no recorded GREEN. Finish the inline TDD step before finalizing." Everything else in
step 3 onward runs unchanged. If `flow: full`, run every step below unchanged.

1. Read the `## Execution Report` section from the task-level `state.md` (populated by `/pe-execute`). If the section is missing → **stop**: "Execution report not found. `/pe-execute` was not completed." Do not continue.

2. Compile summary report from `## Execution Report`:
   - List of completed subtasks (status `done` or `reviewed`).
   - List of skipped subtasks (`blocked` / `deferred`) with reasons.
   - Any subtasks from `plan.md` that are missing from the report (not reached).

2b. **Final composite status reconciliation** (skip if no composite rows exist in `plan.md`).

   For each composite row in `plan.md`:
   a. Read the composite block `[composite] T-XX …` from `state.md → ## Subtask Progress`.
   b. Read all children listed in `children:` and check their status.
   c. Apply consistency rules:
      - If all children are `reviewed` AND `integration-validation: complete` → composite must be `reviewed`. Correct if not.
      - If all children are `reviewed` AND `integration-validation: not-started` → flag as inconsistency: "Composite T-XX children all reviewed but integration validation was never triggered. Run `/phase-composite-validation`." Record in Execution Report as `composite-stalled`.
      - If all children are `reviewed` AND `integration-validation: failed` → composite stays `in-progress`; composite validation fix cycle must complete before `pe-finalize` can set `execution: complete`. **Stop** and report to user.
      - If any child is `not-reached` or `blocked` → composite is `blocked`; update composite block `rollup: blocked` and `plan.md Status: blocked`.
   d. Ensure the `## Execution Report` line for the composite reflects its actual final status.

3. Update the following files explicitly:

   **Task-level `state.md` (in the task directory):**
   - Set `execution: complete` in `## Phases`.
   - Finalize `## Execution Report`: ensure one line per subtask from `plan.md` (including composite rows and their children); add missing ones as `not-reached` with reason.

   **`plan.md` (in the task directory):**
   - Ensure each subtask `Status` column reflects the value from `## Execution Report` (`done` / `reviewed` / `blocked` / `deferred` / `not-reached`).
   - `flow: quick` — no `plan.md` exists; skip without error.

   **`.ai/memory/state.md`:**
   - Update the status of this task using the entry format defined in `workflow-reference → ## .ai/memory/state.md Entry Format`:
     `phase: execution | status: complete | note: <one line — what was implemented>`

   **`.ai/project_state.md`** — update per rules in `workflow-reference → ## .ai/project_state.md Update Rules`:
   - Add/update entries in `## Module inventory` for each module implemented in this task (key exports, purpose).
   - Add/update entries in `## HTTP surface` for each new endpoint exposed.
   - Remove this task's entry from `## In-flight work` (it was added by discovery).
   - Surgical edits only. If the file does not exist — skip without error.

   **Root files — for each file, explicitly state your decision (update / skip) and the reason:**

   | File | Update when | Surgical edit: only |
   |------|-------------|---------------------|
   | `.ai/memory/architecture.md` | New modules, endpoints, data flows, or dependencies were implemented | affected architecture/component sections |
   | `.ai/principles/architecture.md` | Implementation deviated from or extended existing documented architectural decisions | corresponding decision sections |

   **Update principle:** surgical edits only — write factual descriptions of how the system works now, not "task completed" statements. Do not rewrite unrelated sections. If a file does not exist — skip without error.

4. **Artifact conformance check.** Run the contract validator against the task
   directory:

   ```bash
   bash "${ORCHESTRAIL_HOME:?Set ORCHESTRAIL_HOME}/scripts/validate-task.sh" <task-directory> --phase execution
   ```

   It applies the canonical contracts — `## Phases` vocabulary, the `flow:` tier, the
   six-section `description.md`, the `## Subtask Progress` block format, the required-even-
   when-empty fields, and the TDD audit trail — to the artifacts this phase produced, rather
   than to the workflow definitions. The manual review above says what to look for; this says
   whether it is actually there.

   - **Exit 0** → continue.
   - **Exit 1** → fix every reported failure, then re-run until it passes. A malformed
     artifact is cheap to fix now and expensive later: the next phase parses these files and
     will either misread them or stop.
   - **Script missing or not executable** → report that in one line and continue. The
     validator is a check, not a gate that can block work on its own absence.

5. Run `/compress-state --auto` on task-level `state.md`.

6. **Post-execution improvement review** (batch proposals collected during `/pe-execute`, which
   invokes `/phase-atomic-validation … --batch`).

   Scan task-level `state.md` for all `## Improvement Proposals (T-XX)` sections that contain at least one "Do Now" item.

   If any exist:
   - Present a consolidated list to the user: one block per T-XX, listing only "Do Now" items with a short description.
   - Ask: "These Do Now improvements were deferred during batch execution. What would you like to do?
     1. Create new subtasks for them (they will appear in `plan.md` as pending T-XX items).
     2. Apply them now, before validation.
     3. Skip — discard the Do Now proposals (Do Later / Optional items remain in `state.md`)."
   - **Wait for user choice.** Then:
     - Option 1 → create a new pending subtask entry in `plan.md` for each Do Now improvement group (one per T-XX that had items), then continue to step 6.
     - Option 2 → apply improvements inline now (treat each group as an ad-hoc implementation step; do not create subtasks), then continue to step 6.
     - Option 3 → remove only the "Do Now" subsections from the `## Improvement Proposals (T-XX)` blocks; preserve "Do Later" / "Optional" entries.

   **Autonomous callers — do not wait.** When this workflow runs under `/phase-pipeline`,
   choose **option 2** (apply them now, before validation) without prompting, apply each group
   inline, and record the automatic choice in `state.md` by appending
   `pipeline: Do Now applied automatically (phase-pipeline override)` to the corresponding
   `## Improvement Proposals (T-XX)` section. The override is declared in
   `phase-pipeline → ## Pipeline Overrides` and registered in
   `workflow-globals → Workflow-declared mode overrides`. It exists because
   `/pav-propose --batch` records proposals and never applies them — without this step the
   pipeline would finish with the improvements it collected left unmade.

   If no Do Now proposals exist → skip this step silently.

7. Report to user (display as text — do NOT invoke):
   - Summary table of all subtask outcomes (from `## Execution Report`); on `flow: quick`,
     the `## TDD (quick)` record and the changed files instead.
   - "Execution complete. Run `/phase-validation <task-directory>` to start validation."

**STOP. Do not run `/phase-validation` automatically.**
