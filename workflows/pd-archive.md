---
description: Discovery Step 4b — Archive verbose Discovery content to state-archive.md
             to reduce Execution-phase context load. Called by /pd-finalize.
---

Invocation: `/pd-archive <task-directory>`
Called by: `/pd-finalize` after `/compress-state --auto`.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md` in the task directory.
2. Check `discovery: complete` in `## Phases`. If NOT complete → **stop**:
   "`/pd-archive` must run after `discovery: complete`. This is called automatically
   by `/pd-finalize` — do not call manually before discovery finishes."
3. Check if `state-archive.md` already exists in the task directory.
   If it exists → **stop**: "state-archive.md already created. Re-running will
   overwrite. Confirm? (yes/no)" Wait for explicit confirmation.
4. Otherwise → continue.

---

## Instructions

1. Read `state.md` fully from the task directory.
2. Extract the following content verbatim (do not summarize or compress):
   a. Full body of `## Task Analysis` — everything under the header, before the
      next `##`, **except `### Assumptions`**, which stays in `state.md`.
      Assumptions are decisions taken without the user during autonomous
      Discovery; Execution must see them without opening the archive. They are
      one line each, so the context cost is negligible.
   b. Full body of `## Solution Design → ### Variants`
   c. Full body of `## Solution Design → ### Rejected`

3. Write `state-archive.md` in the task directory with this exact structure:

# state-archive — <task-directory-basename>

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis
<exact content from step 2a>

## Archived Solution Design — Variants
<exact content from step 2b>

## Archived Solution Design — Rejected
<exact content from step 2c>

4. Update `state.md` — replace the archived bodies with pointer lines.
   For each archived section, replace the full body with exactly one line:
   `→ archived to state-archive.md`

   After this step, the affected sections in `state.md` must look like:

   ## Task Analysis
   → archived to state-archive.md

   ### Assumptions
   <retained verbatim — never archived>

   (Omit the `### Assumptions` block only if the section does not exist.)

   ## Solution Design
   ### Variants
   → archived to state-archive.md

   ### Rejected
   → archived to state-archive.md

   ### Decision
   <unchanged — full content remains>

   The following subsections of `## Solution Design` must NOT be touched:
   `### Decision`, `### Scope`, `### Off-limits`, `### Invariants`,
   `### Acceptance Criteria`

5. Do NOT modify `## Decomposition`, `## Subtask Progress`, `## Phases`,
   `## Execution Report`, `## Contract Check`, `## Code Review`, `## Issue List`,
   `## Fix-Tasks`, `## Deferred`, or `spec_path:`.

6. Report: "Archive complete. state-archive.md created.
   Archived: Task Analysis (~N lines), Variants (~N lines), Rejected (~N lines).
   state.md reduced by approximately N lines."
