---
description: Validation Step 6 — Finalize validation, update state files, compress context
---

Invocation: `/pv-finalize <task-directory>`
Called by: `/phase-validation` as Step 6.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md` in the task directory.
2. Check `## Phases → validation`. If `complete` → **stop**: "Validation phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Check `## Fix-Tasks` section present in `state.md`. If missing → **stop**: "Step 4 (/pv-create-fixes) must be completed first. Run /pv-create-fixes <path>."
   **Exception — `flow: quick`.** The quick tier skips `/pv-create-fixes` and `/pv-execute-fixes`
   by design (`quick-flow → The quick path`), so `## Fix-Tasks` is absent and its absence is
   not a failure. When the top-of-file `flow:` field reads `quick`, skip this check and step 4
   below, and read the fix outcome from `## Code Review` instead — review findings were fixed
   inline in that phase.
4. If `## Fix-Tasks → fixes-count: 0` → skip fix-task status check, continue. Otherwise read `## Fix-Tasks → Created` list and verify each listed T-XX has status `reviewed` in `plan.md`. If any is not `reviewed` → **stop**: "Step 5 (/pv-execute-fixes) must be completed first. Run /pv-execute-fixes <path>."
5. Otherwise → continue.

---

## Instructions

Load `workflow-reference` for .ai/memory/state.md Entry Format and
.ai/project_state.md Update Rules before starting step 1.

1. Update the following files explicitly:

   **Task-level `state.md` (in the task directory):**
   - Set `validation: complete` in `## Phases`.
   - Aggregate ALL deferred items into `## Deferred` from TWO sources:
     1. `## Issue List → ### Deferred` (from pv-issues — deferred fix decisions)
     2. `plan.md` subtasks with status: `deferred` (from pe-finalize — deferred subtasks)

     Format each entry:
     - [source: issues] <item description>
     - [source: subtasks] <item description>

     If both sources are empty: write `## Deferred` followed by `(none)`.

   Read fix-task status from `## Subtask Progress` in `state.md` — not from `## Fix-Tasks`.

   **`plan.md` (in the task directory):**
   - Ensure each fix-task and original subtask `Status` column reflects its final status (`reviewed` / `deferred` / `blocked` / `not-reached`).

   **`.ai/memory/state.md`:**
   - Update using the entry format defined in `workflow-reference → ## .ai/memory/state.md Entry Format`:
     - If no deferred items: move task entry to `## Done` with `status: reviewed`
     - If deferred items remain: update entry with `status: blocked | note: deferred — <list items>`

   **`.ai/project_state.md`** — update per rules in `workflow-reference → ## .ai/project_state.md Update Rules`:
   - If deferred items affect the system boundary (planned modules or endpoints not implemented): add them to `## What doesn't exist` with `planned but deferred` note.
   - If no deferred items with system-level impact — no update required.
   - Surgical edits only. If the file does not exist — skip without error.

   **Root files — for each file, explicitly state your decision (update / skip) and the reason:**

   | File | Update when | Skip when |
   |------|-------------|-----------|
   | `.ai/memory/architecture.md` | Any module, endpoint, data flow, dependency, or architectural component changed | Only internal implementation details changed with no observable system-level effect |
   | `.ai/principles/architecture.md` | Architectural decisions, known issues, or system behaviors documented here were changed or resolved | No documented decisions or behaviors changed |

   **Update principle:** surgical edits only — write factual descriptions of how the system works now, not "task completed" statements. Do not remove unrelated sections. If a file does not exist — skip without error.

2. Run `/compress-state --auto` on task-level `state.md`.

2.5. Mark spec as complete. This is the one permitted write to a spec file: it adds a
   completion marker, never a change to the task statement — see
   `workflow-reference → ## File Responsibility`. A content change still goes through the
   Description Amendment procedure and is recorded in `state.md`, not in the spec.
   a. Read `spec_path:` from `state.md`.
   b. If `spec_path:` is present and the file exists:
      - Read the spec file content.
      - If the file already starts with a `---` frontmatter block → skip (already marked).
      - Otherwise prepend the following frontmatter:
        ```
        ---
        status: done
        completed_task: <task-directory-basename>
        completed_at: <today's date YYYY-MM-DD>
        ---

        ```
        (blank line after closing `---` before original content)
   c. If `spec_path:` absent or file not found → skip silently (legacy task).

3. **Record Architectural Decisions (ADR).** The task is NOT considered complete until this step is finished.

   **Language requirement (strict).** The ADR file, the `.ai/adr/index.md` index, and every section, table, header, and line written by this step MUST be in English. This applies even if the chat dialogue with the user happens in another language — the artifacts on disk are project files and follow the project English-only rule (`rules/language.md`). Do NOT mix languages inside the ADR.

   **Sources to analyze before writing the ADR:**
   - Task statement (resolve via dual-mode: if `state.md` contains `spec_path:` →
     read file at that path; else → read `description.md` from task directory if present)
   - `state.md` sections: `## Solution Design`, `## Autonomous Decision` (if pipeline), `## Subtask Progress → notes`, `## Issue List`, `## Contract Check`, `## Code Review`, `## Deferred`
   - `plan.md` (final subtask statuses, target files)
   - Q&A exchanged with the user during Discovery / Execution / Validation
   - Actual code changes and the resulting list of modified files
   - Off-limits constraints, accepted compromises, deferred items, declined alternatives

   **What to record as a decision** (only items useful for future development):
   choice of library / framework / external service; architectural approach; module / layer / boundary structure; data schema, entities, relations, migrations; error-handling approach; validation strategy; authorization / permissions strategy; caching, queues, background-job, or synchronization strategy; explicit refusal of an alternative; agreement reached with user / client / teammate; constraint that will affect future work; compromise made for deadlines / compatibility / simplicity.

   **Do NOT record:** formatting changes, local variable renames, obvious small fixes, technical noise, or anything that does not influence future development.

   If a decision was not stated explicitly but follows clearly from the implementation — record it and mark it as `inferred from implementation`.

   **3.0. Check for a provisional ADR first.**
   Read `state.md` for an `adr:` line, and scan `.ai/adr/` for a record matching this task
   whose `## Status` is `Provisional` — written by `/pd-design` via `/adr-new` at the moment
   the decision was made.

   - **Found** → do **not** allocate a new number and do **not** write a second record.
     Update that file in place: set `## Status` to `Accepted`, fill `## Verification` from
     this task's validation results, add any decision taken after Discovery to
     `## Decisions`, and update its row in `.ai/adr/index.md` (`Status` column → `Accepted`,
     `Date` → today). Then continue from step 4 of this workflow.
   - **Not found** → continue with 3.1 below and write the ADR as usual.

   This is the only correct handling: allocating a new number for a task that already has a
   provisional record leaves two ADRs describing one decision, and the index cannot show
   which is current.

   **3.1. Locate `.ai/adr/` directory.**
   - If `.ai/adr/` does not exist → create it.
   - If `.ai/adr/index.md` does not exist → create it with the header table shown below.

   **3.2. Determine the next ADR number.**
   - List files in `.ai/adr/` matching `NNNN-*.md`.
   - Next number = highest existing `NNNN` + 1, zero-padded to 4 digits. If folder is empty → `0001`.

   **3.3. Compose the file name.**
   - Format: `NNNN-task-<ID>-<short-title>.md`.
   - `<ID>` — task ID from `description.md` (e.g. `5`, `18`, `27`). If task ID is unknown → use `unknown`.
   - `<short-title>` — 2–5 words, kebab-case, ASCII.
   - Examples: `0001-task-5-image-processing.md`, `0002-task-18-refresh-token-rotation.md`, `0003-task-unknown-background-jobs.md`.

   **3.4. Write the ADR using EXACTLY this template (English only):**

   ```md
   # ADR-NNNN: Decisions for Task <ID> — <Task Title>

   ## Status

   Accepted

   ## Date

   YYYY-MM-DD

   ## Related Task

   - Task: <ID or link>
   - Related pull request: <if known>
   - Related files: <if applicable>

   ## Summary

   Briefly describe what was implemented and why.

   ## Context

   Describe the original problem, constraints, requirements, and important inputs.

   ## Decisions

   ### Decision 1: <short title>

   **What was decided:**
   Describe the specific decision.

   **Why:**
   Explain the reason for the choice.

   **Alternatives:**
   List the alternatives considered and why they were rejected.

   **Consequences:**
   Describe pros, cons, constraints, and impact on future work.

   **Related files:**
   - `path/to/file`

   ### Decision 2: <short title>

   **What was decided:**
   ...

   **Why:**
   ...

   **Alternatives:**
   ...

   **Consequences:**
   ...

   **Related files:**
   ...

   ## Questions and Answers

   | Question | Answer | Impact on implementation |
   |---|---|---|
   | ... | ... | ... |

   If there were no questions, write exactly:

   No external questions and answers were recorded during this task.

   ## Rejected Options

   Describe options that were considered but not used.

   ## Implications for Future Work

   Describe what must be kept in mind for future changes in this area.

   ## Verification

   Describe which checks were performed.

   ## References

   - Task:
   - Pull request:
   - Related documents:
   ```

   **3.5. Quality requirements (strict).**
   - Each decision MUST answer at least: (a) what exactly was chosen, (b) why, (c) which alternatives were rejected, (d) what it changes for future development.
   - Be concrete. Do NOT use vague phrases such as: "architecture improved", "business logic added", "handling implemented", "standard approach used", "code became better". Instead write specifically, e.g. "validation moved into the service layer so the controller no longer holds business rules"; "queue-based retries chosen because synchronous processing can hit timeouts"; "job state stored in a dedicated table because the background result must be available after the request finishes".
   - The ADR and the decisions index must be written entirely in English (see Language requirement above).

   **3.6. If no architecturally significant decisions were made.**
   Still create the ADR file. In the `## Decisions` section write exactly:

   > No architecturally significant decisions were made for this task. Only implementation details are recorded.

   The document must still contain: a short summary of the task, the list of modified files (under `## Related Task → Related files`), the checks that were performed (under `## Verification`), and the note above.

   **3.7. Update `.ai/adr/index.md` (the decisions index, English only).**

   The index uses one schema across the whole system — the one seeded by
   `templates/.ai/adr/index.md` and written by `/onboard-legacy-project`. Do not invent a
   second one: appending a row in a different column order against an already-seeded index
   silently shifts every value one column to the right.

   - If the file is empty or missing — initialize it with:
     ```
     # index.md — index of architectural decision records

     ## Records

     | Number | Title | Status | Date | Link |
     |--------|-------|--------|------|------|
     ```
   - Append one row for the new ADR under `## Records`, in that same column order:
     `| NNNN | <ADR title — the decision in a few words> | Accepted | YYYY-MM-DD | [<adr-file-name>.md](<adr-file-name>.md) |`
   - `NNNN` and `<adr-file-name>` are the number and file name composed in step 3.3 — the
     task id is already carried by the file name the `Link` column points at, so it needs no
     column of its own.

4. **Reconcile the spec.** Run `/spec-sync <task-directory>` (add `--auto-mode` when this
   workflow is running under `/phase-pipeline` or `/spec-run`).

   The spec was immutable for the whole task, and that is what stopped anyone rewriting a
   requirement to match what got built. Now that validation has decided what is true, the
   divergences the task recorded — assumptions, amendments, deferrals, accepted compromises,
   validation fixes — are folded back into `.ai/specs/<NN>-<slug>.md` with a citation each.
   Without this step the spec keeps describing a system that no longer exists, and every
   later task starts from a stale source of truth.

   - `state.md` has no `spec_path:` (legacy task) → skip without error.
   - `/spec-sync` reports a **failed** Acceptance Criterion → do not proceed to step 5.
     A failed criterion is a defect and belongs in a fix-task, never in a spec edit.
   - `/spec-sync` unavailable or erroring → report it in one line and continue; the
     reconciliation is owed, not optional, so name it in the report as outstanding.

5. Report to user:
   - Validation complete.
   - Summary: N fix-tasks completed, M deferred.
   - If deferred tasks exist — list them with status `deferred`.
   - **Multi-phase handoff** — if the just-closed task's `state.md` contains
     `active_phase: N` AND `## Spec Phases` lists at least one phase K > N,
     append: "Phase <N> complete. Run `/phase-discovery <spec_path> --phase <N+1>`
     to begin Phase <N+1> Discovery."
   - **ADR section (mandatory):**
     - Path to the created ADR: `.ai/adr/NNNN-task-<ID>-<short-title>.md`.
     - Whether `.ai/adr/index.md` was updated (yes / created from scratch).
     - Short bullet list of the decisions recorded in the ADR.
     - Any candidate decisions that in the future may deserve a separate ADR (or "none").
     - If the ADR was not created — state the explicit reason. This is allowed ONLY when this workflow did not itself execute the task implementation.
