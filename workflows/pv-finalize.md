---
description: Validation Step 6 — Finalize validation, update state files, compress context
---

Invocation: `/pv-finalize <task-directory>`
Called by: `/phase-validation` as Step 6.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read task `state.md`; require Execution complete and completed `## Contract Check`,
   `## Code Review`, and `## Issue List` decisions. Validation already complete → ask for
   explicit confirmation before replacing completed artifacts.
2. **Exception — `flow: quick`.** This tier skips `## Fix-Tasks`: verify approved inline fixes and review evidence.
   On `full`, require `## Fix-Tasks` with `fixes-created: complete`.
   `fixes-count: 0` skips the fix-status check. Otherwise every `Created:` entry must have
   `atomic-validation: complete` and plan status `reviewed`; read progress from
   `## Subtask Progress`, never from `## Fix-Tasks`.
3. Every affected composite must have passed integration. Approved unresolved fixes,
   failed Acceptance Criteria, unresolved critical contract gates, or missing final
   verification → **stop**: "Finish validation and approved repairs before finalization."
   A deferral is recorded incomplete scope, never evidence that a failed criterion passed.

## Context Bootstrap

Load the `phase-validation` rule (`## Context Bootstrap`) before writes, including standalone runs.
Load `workflow-reference` for the memory entry format and project-state update rules.
Keep `validation: in-progress` until finalization succeeds; do not announce completion early.

## Instructions

1. **Prepare final state and factual knowledge updates.**
   - Aggregate `## Issue List → ### Deferred` and plan rows with `deferred`, `blocked`,
     or `not-reached` outcomes into `## Deferred`, retaining each source/reason. Use
     `[source: issues]` / `[source: subtasks]`; write `(none)` when empty. Deduplicate on resume.
   - Reconcile every plan row with actual atomic/composite progress. Do not turn `done`
     into `reviewed` without validation or discard blocked/not-reached work.
   - Prepare `.ai/memory/state.md`: no outstanding scope → move the task to `## Done`
     using `- [task-id] | completed | note: <delivered outcome>`; otherwise retain an
     active `status: blocked` entry naming
     the deferred/outstanding scope. Apply completion entries only in step 5.
   - Update `.ai/project_state.md` surgically: affected implemented inventory and planned
     system boundaries under `## What doesn't exist` (`planned but deferred`). Skip if absent.
   - For `.ai/memory/architecture.md` and `.ai/principles/architecture.md`, report update/skip
     and a reason. Update only changed interfaces, flows, dependencies, and approved decisions;
     never rewrite principles to make a deviation pass.

2. Confirm final evidence covers the changed surface after the last fix. If not, rerun
   `/pv-contract` and `/pv-review`; preserve issue decisions and resolution history. A new
   finding returns to its decision/fix cycle. Do not recreate completed fix directories.

2.5. **Mark spec as complete — prepare metadata only.** Read `spec_path:` and determine
   whether the entire spec is delivered, including all phases and required scope. Pending
   later phases or deferred/blocked/not-reached requirements prevent `status: done`.
   Stage the permitted completion marker for step 5; do not write it before reconciliation.
   Missing `spec_path:` is a legacy task; skip this metadata step. Merge existing frontmatter
   fields rather than assuming any `---` block already means complete.

3. **Record Architectural Decisions (ADR).** This step owns the canonical trigger and schema
   also consumed by `/adr-new`; do not execute other finalization steps when loading the schema.

   **Trigger:** record a decision a future developer needs to understand: architectural
   approach, dependency/service choice, module boundary, schema/migration, validation/error/
   authorization strategy, caching/queue/synchronization, rejected alternative, or lasting
   constraint/compromise. Formatting, local renames, and obvious fixes alone do not qualify.
   No qualifying decision → record/report "No architecturally significant decisions" and
   skip ADR creation. The quick tier uses this same trigger.

   Read decision-bearing portions of the spec, Solution Design, autonomous decisions,
   subtask notes, issue decisions, contract/review results, deferrals, and actual changes.
   Include recorded user decisions; do not depend on unpersisted conversation memory.
   Label a supported implementation inference `inferred from implementation`; missing
   rationale or alternatives are `not recorded`, never invented.

   **3.0. Reuse before allocating.** Read every task `adr:` pointer and matching records:
   - Provisional decision implemented and verified → promote that record in place to
     `Accepted`, fill verification, and update its index row. Retain number/date history;
     do not create a duplicate. Do this for every matching provisional record.
   - Matching Accepted record unchanged → reuse it. A replaced accepted decision requires
     an authorized superseding record, not silent rewriting.
   - New independent qualifying decision → allocate a new record as below.

   **3.1. Location:** use the resolved project's `.ai/adr/`; create it/index only when writing
   a qualifying ADR. Under `/spec-run`, shared files remain the orchestrator's responsibility.

   **3.2. Number:** highest filename matching `NNNN-*.md` plus one, four digits;
   no records → `0001`. Recheck before writing to avoid collisions.

   **3.3. Filename:** `NNNN-task-<ID>-<short-title>.md`, using the recorded task ID or
   `unknown`, and a 2–5 word ASCII kebab-case title. Keep planning references inside the
   knowledge record; never copy them into product code, commits, branches, or pull requests.

   **3.4. Body template (English only):**

   ```md
   # ADR-NNNN: Decisions for Task <ID> — <Task Title>

   ## Status

   Accepted

   ## Date

   YYYY-MM-DD

   ## Related Task

   - Task: <ID or link>
   - Related pull request: <if known>
   - Related files: <affected files>

   ## Summary

   <What was implemented and why>

   ## Context

   <Problem, constraints, requirements, inputs>

   ## Decisions

   ### Decision 1: <short title>

   **What was decided:**
   <Concrete choice>

   **Why:**
   <Recorded reason, or not recorded>

   **Alternatives:**
   <Rejected alternatives and reasons, or not recorded>

   **Consequences:**
   <Benefits, costs, constraints, future impact>

   **Related files:**
   - <path>

   ## Questions and Answers

   | Question | Answer | Impact on implementation |
   |---|---|---|
   | <recorded question> | <answer> | <impact> |

   ## Rejected Options

   <Options not used, or none recorded>

   ## Implications for Future Work

   <Constraints future changes must respect>

   ## Verification

   <Commands actually run, results, limitations>

   ## References

   - Task:
   - Pull request:
   - Related documents:
   ```

   Repeat the Decision subsection for additional decisions. With no external Q&A, replace
   the table with exactly: `No external questions and answers were recorded during this task.`
   Each decision states what, why, alternatives, and future consequences concretely.

   **3.5. Index schema.** Initialize a missing/empty index as:
   ```md
   # index.md — index of architectural decision records

   ## Records

   | Number | Title | Status | Date | Link |
   |--------|-------|--------|------|------|
   ```
   Upsert one matching row, preserving column order and unrelated records:
   `| NNNN | <decision title> | Accepted | YYYY-MM-DD | [<adr-file-name>.md](<adr-file-name>.md) |`

4. **Reconcile the spec.** Run `/spec-sync <task-directory>` (add `--auto-mode` under
   `/phase-pipeline` or `/spec-run`). Supply the verified finalization context: all validation
   prerequisites above have passed, and final completion status has not yet been written.
   Legacy task without `spec_path:` → skip. Failed criterion → **stop** and repair it in a
   fix-task; never weaken the spec. Unavailable/erroring reconciliation → record it outstanding,
   keep Validation `in-progress`, and report the required rerun instead of claiming completion.
   "Already reconciled; no new changes" is a successful no-op: continue to step 5.

5. **Commit final state.** After reconciliation and required ADR updates succeed, apply
   the prepared knowledge/memory updates. If the whole spec passed the
   completion test in step 2.5, merge these fields into its existing frontmatter:
   ```yaml
   status: done
   completed_task: <task-directory-basename>
   completed_at: <YYYY-MM-DD>
   ```
   Preserve unrelated fields and the original body. Partial delivery gets no done marker.
   Append one completion entry to `.ai/memory/progress.md` with delivered changes,
   verification, and outstanding scope; deduplicate on a no-op rerun.
   Run `/compress-state --auto` on parent state; preserve every protected field. After
   required writes succeed, set `validation: complete` as the final state transition.
   Report validation evidence, fix count, outstanding scope, spec reconciliation, and each
   ADR path/index update or the reason no ADR was needed.
   For `active_phase: N` with a later phase listed in `## Spec Phases`, display the next
   actual phase number K and `/phase-discovery <spec_path> --phase K`; do not invoke it.

Return to the active caller; completion is a progress marker, not an extra handoff.
