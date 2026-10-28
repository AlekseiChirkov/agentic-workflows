---
description: Discovery Step 4b — Archive verbose Discovery content to state-archive.md
             to reduce Execution-phase context load. Called by /pd-finalize.
---

Invocation: `/pd-archive <task-directory>`
Called by: `/pd-finalize` after `/compress-state --auto`.

Resolve `state.md` and `state-archive.md` inside the provided task directory.

## Guard

1. Missing/unreadable `state.md` or `## Phases → discovery` other than `complete`
   → **stop**: run `/pd-finalize` first.
2. Existing `state-archive.md` → **stop** for explicit overwrite confirmation.
   Before replacement, verify the full source bodies still exist in `state.md`.
   Pointer-only source cannot recreate an archive; preserve the existing archive
   and report that no safe replacement can be produced.
3. `flow: quick` → report that archiving is skipped and end without writes.

## Instructions

1. Read task `state.md`. Extract these bodies verbatim, retaining their internal
   headings: all of `## Task Analysis` except `### Assumptions`; and only
   `## Solution Design → ### Variants` and `### Rejected`. A body ends at the next
   heading of equal or higher level. Do not include adjacent design sections.
2. Write and verify `state-archive.md` before replacing any source content:

   ```
   # state-archive — <task-directory-basename>

   Archived after discovery: complete.
   Read by Validation-phase workflows when full context is needed.
   Do not edit manually.

   ## Archived Task Analysis
   <verbatim analysis body except Assumptions>

   ## Archived Solution Design — Variants
   <verbatim Variants body>

   ## Archived Solution Design — Rejected
   <verbatim Rejected body>
   ```

   Verify each extracted body matches its archive copy. Missing required source
   sections or a failed write/verification → **stop**, leaving `state.md` intact.
3. Replace each archived body with exactly `→ archived to state-archive.md`.
   Keep its original heading and position. Keep `### Assumptions` verbatim under
   `## Task Analysis` (omit only when absent in a legacy file).
4. Preserve all other content byte-for-byte: design Decision, Autonomous Decision,
   Scope, Off-limits, Invariants and Acceptance Criteria; phase/metadata fields;
   decomposition, progress and all execution/validation sections. Re-read pointers
   and retained sections to verify the move did not remove decisions or status.
5. Report the archive path, sections archived, actual before/after line counts and
   reduction. Under a parent this is a progress marker, not a handoff; return
   to finalization without starting another phase.
