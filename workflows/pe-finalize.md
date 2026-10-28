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

## Context Bootstrap

Load the `phase-execution` rule (`## Context Bootstrap`) before project writes, including standalone
runs. Resolve task paths absolutely; use each description's `working_dir:` for service files.

## Instructions

Load `workflow-reference` for the status translations, memory entry format, and project-state
update rules. Keep `execution: in-progress` until the work and checks below finish.

**Quick branch.** If `flow: quick`, there are no T-XX subtasks or required `plan.md` /
`## Execution Report`. Skip steps 1–2b and subtask/proposal processing. Read the outcome and
changed-file list from `## TDD (quick)`. Missing `green-observed: yes` → **stop**:
"Quick task has no recorded GREEN. Finish the inline TDD step before finalizing."
For justified `none`, `green-observed: yes` records completed applicable/manual verification,
not a claim that nonexistent tests passed; retain the exemption and evidence.

1. Read `## Execution Report`; if absent on `full` → **stop**:
   "Execution report not found. Complete `/pe-execute` first."
   Summarize completed, blocked, deferred, and not-reached rows. Compare every plan row
   with its progress block; report unexplained missing work instead of assuming completion.

2. Reconcile plan statuses with atomic progress and the report using
   `workflow-reference → ## Status Translation Table`. Never write report-only labels such
   as `composite-reviewed` into the plan's `Status` column.

2b. **Final composite status reconciliation.** For each composite, read its block and children:
   - All children `reviewed` and integration complete → plan `reviewed`, rollup `done`.
   - All children `reviewed` and integration not started/in progress → record
     `composite-stalled`; **stop**: "Run `/phase-composite-validation` for <composite> before finalizing."
   - `integration-validation: failed` → keep the composite unreviewed; **stop**:
     "Complete the integration fix cycle before finalizing Execution."
   - Blocked or not-reached children → record the reason and reconcile `rollup: blocked`.
     An explicitly deferred or externally blocked row may remain skipped; an approved,
     runnable fix may not be relabeled skipped to close the phase.

3. Prepare factual updates from implemented work:
   - `.ai/memory/state.md`: use `phase: execution | status: complete` only after step 6.
   - `.ai/project_state.md`: update affected module/HTTP entries and remove the task from
     `## In-flight work`; skip a missing file.
   - `.ai/memory/architecture.md`: update changed modules, interfaces, flows, or dependencies.
   - `.ai/principles/architecture.md`: update only decisions actually adopted; do not
     rewrite principles to conceal an unapproved deviation.
   Make surgical edits and report update/skip with a reason for each knowledge file.

4. Identify the artifact validator at
   `${ORCHESTRAIL_HOME}/scripts/validate-task.sh`. Run it in step 6 after proposal processing,
   so it checks the final artifacts once. Missing/unconfigured helper → report and continue;
   an available validator's reported artifact failures must be repaired.

5. **Post-execution improvement review.** Collect unresolved `### Do Now` items from all
   `## Improvement Proposals (T-XX)` sections; ignore items already applied or declined.
   Select the caller mode before prompting. Under `/spec-run`, keep every proposal pending,
   record `spec-run: proposals retained for post-delivery review; no application`, surface
   their counts/items in the final report, and continue without prompting or applying.
   Under `/phase-pipeline`, use its option-2 override below. Otherwise present one
   consolidated choice and wait for user choice:
   1. Create pending subtasks, one per improvement group, with complete descriptions,
      Test Plans, plan rows, and progress blocks. Keep Execution `in-progress`; return to
      `/pe-execute` to execute them before finalization.
   2. Apply approved items now within the existing scope. Follow the `tdd` gate before any
      changed behaviour, preserve frozen tests, update cumulative `target_files:`, rerun
      verification, then invalidate and repeat atomic validation for affected leaves.
   3. Discard only Do Now proposals; preserve Do Later / Optional items.

   Under `/phase-pipeline`, choose **option 2** without prompting and record
   `pipeline: Do Now applied automatically (phase-pipeline override)` in each affected
   proposal section. This override applies here; `/pav-propose --batch` still applies nothing.
   Mark each handled proposal applied/declined so resuming never applies it twice.
   No proposals → continue. Approved work that stops leaves Execution `in-progress`.

6. Run the available validator with the final artifacts:
   ```bash
   bash "$ORCHESTRAIL_HOME/scripts/validate-task.sh" <task-directory> --phase execution
   ```
   Exit 1 → repair reported artifacts and rerun; absence → report once and continue.
   Once all checks pass, finalize the report with one line per plan row, apply the knowledge
   updates from step 3, set `execution: complete`, and run `/compress-state --auto`.

7. Report outcomes, verification, and updated paths. On quick tasks report the inline TDD
   record and changed files. Display: "Execution complete. Run `/phase-validation <task-directory>` to start validation."

**STOP. Do not run `/phase-validation` automatically.** This completion is a progress
marker for an active caller; only a caller with an explicit cross-phase override advances.
