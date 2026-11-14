## Goal
The repository's identity ledger records the manual's clone command on its current line, so the complete contract validator passes on the stack tip.

## Context
- Dependencies: T-10 — its manual change moved the recorded occurrence from line 254 to line 255 of `docs/USAGE.md`.
- Constraints: the ledger lives in the completed task record `.ai/tasks/completed/task-01-git-source-of-truth/state.md` under `### Exact Identity Match Ledger`; the identity check reads only the ledger rows. That file is a shared knowledge record: under the orchestrated run only the orchestrator writes it, so the change is applied by the orchestrator as a shared-file delta, not by a worker. Later fixes in this task must not insert lines above the recorded occurrence in `docs/USAGE.md`; if one does, it refreshes the ledger in the same change.
- Reason: a critical contract failure found by the task-level contract check; fixed alone because it is critical.

Off-limits: no other ledger row, count or prose changes; no change to `docs/USAGE.md`, to the identity check or to any other completed-task content.

## Scope
- **In scope:** the ledger row for `docs/USAGE.md` and the prose line above the ledger that names the same line number.
- **Out of scope:** any change to how the identity check works; the hygiene checks that need a local pattern file.
- **Target files:** `.ai/tasks/completed/task-01-git-source-of-truth/state.md`

## Steps
1. Confirm the failing state: the identity check of the contract validator reports `docs/USAGE.md` line 254 expected and line 255 found, with no other difference.
2. Change the ledger row `docs/USAGE.md | 254` to `255` and the prose reference `docs/USAGE.md:254` to `:255`.
3. Run the identity check alone and confirm it passes; the complete validator is re-run after all fixes of this task.

## Acceptance Criteria
- The identity check `test_public_identity_matches_exact_ledger_and_preserves_knowledge` passes on the branch tip, with the knowledge inventory half unchanged.
- The diff of the ledger file is exactly two lines, both changing 254 to 255 for `docs/USAGE.md`.
- After all fixes of this task, the complete contract validator reports 0 failed.

## Test Plan
- **Level:** smoke — the existing identity check of the contract validator is the failing test; it was observed failing in the complete run on the stack tip before the change.
- **Scenarios:**
  - Identity check before the change → fails with the single 254/255 difference.
  - Identity check after the change → passes.
  - Ledger diff → two lines.
  - Complete validator after all fixes → 0 failed.
- **Edge cases:** no other ledger row moved (the scan difference has one hunk).
