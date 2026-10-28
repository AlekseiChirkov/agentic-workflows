---
description: Validation Step 1 — Verify implementation against Invariants, Acceptance Criteria, Off-limits
---

Invocation: `/pv-contract <task-directory>`
Called by: `/phase-validation` as Step 1.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md` in the task directory; missing state or execution not `complete` → **stop**: "Complete `/phase-execution` first."
2. Check `## Phases → validation`. If `complete` → **stop**: "Validation phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Otherwise → continue.

---

## Context Bootstrap

Load the `phase-validation` rule (`## Context Bootstrap`) before reading implementation files or
writing project files; run the full bootstrap when invoked standalone. The rule owns
the load order, umbrella precedence, conditional sources, and reporting.

---

## Instructions

1. Read `state.md` — extract `## Solution Design`: `### Invariants`, `### Acceptance Criteria`, `### Off-limits`.
   **`flow: quick`:** there is no `## Solution Design`. Read the same three sub-sections from
   `## Contract (quick)` instead — the quick tier's contract is inline and mandatory
   (`quick-flow → The quick path`). Everything below is unchanged.
2. Read all implementation files referenced in parent `state.md → ## Subtask Progress → T-XX → target_files:` for each T-XX subtask.
   Resolve each file relative to its subtask's `working_dir:`. `flow: quick` has no leaf
   blocks: use the cumulative file list recorded alongside `## TDD (quick)`. If absent,
   recover only from task-specific git evidence and persist the source. Do not treat an
   unrelated/latest commit or an unbounded worktree diff as proof of task ownership.
   If ownership cannot be established → **stop**: "Identify the task's changed files first."
3. For each Invariant: verify it holds. Record pass/fail with reason.
4. For each Acceptance Criterion: verify it is met. Record pass/fail with reason.
5. For each Off-limits constraint: verify it is not violated. Record pass/fail with reason.
6. Upsert one `## Contract Check` section in `state.md`; do not duplicate on rerun:

```
## Contract Check

### Invariants
| Invariant | Status |
|-----------|--------|
| <name> | PASS / FAIL: <reason> |

### Acceptance Criteria
| Criterion | Status |
|-----------|--------|
| <name> | PASS / FAIL: <reason> |

### Off-limits
| Constraint | Status |
|------------|--------|
| <name> | PASS / FAIL: <reason> |
```

7. **Critical-failure stop gate.** If at least one Invariant or Off-limits entry has status `FAIL` — **stop immediately** before yielding back to the orchestrator or `/pv-review`:
   - List all critical failures (Invariant / Off-limits) with reasons.
   - Ask the user: "Critical contract failures detected. Choose: (1) pause validation and fix now, (2) continue review with these failures marked `critical` in the issue list."
   - Wait for explicit user decision. Do not proceed to `/pv-review` or any subsequent step until an answer is received.
   - Record the chosen decision in `state.md` as `### Critical Failures Decision: <pause | continue-marked>`.

   Acceptance Criteria failures do not trigger the gate — they are batched for `/pv-issues` as usual.

8. Report: "Step 1 (Contract Verification) complete. N passes, M failures (K critical)."
This is a progress marker; return to the caller only after the critical gate is resolved.
