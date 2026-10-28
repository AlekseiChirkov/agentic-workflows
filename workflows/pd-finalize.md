---
description: Discovery Step 4 — Finalize discovery, verify consistency, compress state
---

Invocation: `/pd-finalize <task-directory> [--step-by-step]`
Called by: `/phase-discovery` as Step 4.

Resolve artifacts inside the task directory. `--step-by-step` affects the closing
digest only; consistency failures stop in every mode. Reuse parent context;
standalone use applies the `phase-discovery` bootstrap.

## Guard

1. Missing/unreadable `state.md` or `## Task Analysis` → **stop**: run `/pd-analyze`.
2. `discovery: complete` → **stop** for explicit overwrite confirmation unless
   the parent already obtained it for this exact rerun.
3. Require `## Solution Design` with `### Decision` for full flow.
   **Exception — `flow: quick`.** Verify `## Contract (quick)` instead, with
   `### Off-limits`, `### Invariants` and `### Acceptance Criteria`.
   Missing required contract/design → **stop**: rerun the applicable analysis/design step.

## Instructions

Load `workflow-reference → ## Protected Sections Contract` and its memory/project
state update formats once. Preserve unrelated content and progress.

**Quick branch:** skip steps 1, 2 and 4b; verify the inline quick contract's
criteria are binary and observable, and the recorded four-condition gate still
passes. Missing/untestable criteria → **stop** and return to `/pd-analyze`.
A failed quick gate requires promotion under `quick-flow`. Use the inline contract
where later steps refer to Solution Design. Full flow runs all steps.

1. Review full-flow consistency:
   - Task state has Task Analysis, complete Decomposition, and Solution Design/Decision.
   - `plan.md → ## Subtasks` has ID, Name, Key Steps (summary), Depends On, Status,
     plus Type/Slice/Repo where applicable. Preserve optional provider model columns
     `Model (Claude)` / `Model (Codex)` and legacy `Model` under
     `workflow-reference → ### Model columns and resolution`, including composite
     blanks and intentional active-provider defaults; missing columns are valid.
     IDs are unique, dependencies resolve without cycles, and execution order respects them.
   - Descriptions and `## Subtask Progress` match every plan row, including composites
     and their children; type, child order, target files and chosen scope agree.
2. Verify each listed description:
   - It exists and contains all six sections: `## Goal`, `## Context`, `## Scope`,
     `## Steps`, `## Acceptance Criteria`, `## Test Plan`.
   - Scope has nonempty In scope, Out of scope and Target files; constraints and
     Off-limits match the task design.
   - Leaves have 3–15 numbered implementation steps, one testable component and
     one coherent criteria cluster. For `type: composite`, Steps references at
     least two existing leaf children listed in Context; numbered step limits
     do not apply. Children meet all leaf checks and never contain another composite.
   - At least two criteria are binary, observable pass/fail assertions with exact
     results. Composite criteria verify combined output rather than repeat child checks.
   - Test Plan names applicable unit/integration/contract/smoke/none levels and at
     least one observable scenario per criterion. `none` explains why each other
     level is inapplicable; difficulty, size, framework absence, deferral or existing
     coverage do not justify it. Composites use integration and/or contract scenarios
     across children.
   - Each T-XX directory contains only `description.md`.

   Any inconsistency → **stop**, identify the file/check and return to design or
   decomposition as appropriate. Do not rewrite recorded progress to make it agree.
3. Run the task artifact validator when the configured source helper is available:

   ```bash
   if [ -n "${ORCHESTRAIL_HOME:-}" ] && [ -x "$ORCHESTRAIL_HOME/scripts/validate-task.sh" ]; then
     bash "$ORCHESTRAIL_HOME/scripts/validate-task.sh" <task-directory> --phase discovery
   fi
   ```

   Exit 0 → continue; nonzero → fix reported artifacts within scope and rerun.
   Unresolvable failures **stop** finalization. Missing configuration/helper →
   report once and continue with manual checks.
4. Run `/compress-state --auto <task-directory>/state.md`, preserving canonical
   markers, decisions, assumptions, progress and all other protected content.

4a. In `## Phases`, set `discovery: complete` before archiving; `/pd-archive` requires it.

4b. **`flow: quick` — skip this step.** For full flow:
    Run `/pd-archive <task-directory>`. If an archive already exists and all source
    bodies are pointers to it, verify it is readable and retain it. If fresh inline
    bodies coexist with an old archive, apply `/pd-archive`'s overwrite Guard;
    do not silently retain stale analysis. Failed archiving → restore
    `discovery: in-progress`, report the blocker and **stop**.
5. Upsert persistent planning state using `workflow-reference` formats:
   - `.ai/memory/state.md`: `[task-id] | phase: discovery | status: complete |
     note: plan ready, <N> subtasks`; for quick flow use `quick contract ready`
     rather than a subtask count. Use the full phased directory basename when present.
   - Multi-phase: upsert later undiscovered phases in `## Deferred` with their
     phase number, title and prerequisite validation; preserve already started or
     completed entries. On full flow only, prepend/update one `plan.md` scope banner
     identifying the active phase and actual remaining deferred phases. Omit a
     deferred range when none remains.
   - `.ai/project_state.md`, if present: update `## In-flight work` with planned
     changes from the decision. Describe them as planned; code does not exist yet.
6. For each file below, report update/skip and reason; edit only relevant sections:
   - `.ai/memory/architecture.md`: record planned structural changes with an
     explicit planned/in-flight label, preserving the current implemented snapshot.
   - `.ai/principles/architecture.md`: add only newly established durable constraints
     or decisions, not every implementation choice. Missing files are skipped.
7. Verify `discovery: complete` remains, archive pointers resolve, and no required
   artifact or protected field disappeared. Keep execution/validation statuses unchanged.
8. Emit the single final report (the parent reuses it):
   - Task `state.md` and full-flow `plan.md`; for quick flow, inline contract location.
   - Chosen approach; in autonomous mode, winner/score when present and every
     `### Assumptions` entry. Read assumptions and Autonomous Decision from state. For quick flow, mark architecture scoring
     inapplicable. Mention unresolved batch questions so `/spec-run` can apply its gate.
   - `Discovery complete. Run /phase-execution <task-directory> to start execution.`
   - Multi-phase: after this phase validates, show the command for the next actual
     phase number, if any. Do not invent N+1 when phase numbering has gaps.

**STOP. Do not run `/phase-execution` automatically.**
