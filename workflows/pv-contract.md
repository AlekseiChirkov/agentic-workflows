---
description: Validation Step 1 — Verify implementation against Invariants, Acceptance Criteria, Off-limits
---

Invocation: `/pv-contract <task-directory>`
Called by: `/phase-validation` as Step 1.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md` in the task directory.
2. Check `## Phases → validation`. If `complete` → **stop**: "Validation phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Otherwise → continue.

---

## Context Bootstrap

Follow `phase-validation` rules — ## Context Bootstrap. Load in order, skip missing files.
In multi-repo projects: load umbrella (`../.ai/`) first, then local (`.ai/`) — local overrides.

1. `.ai/memory/architecture.md` — system invariants, integration contracts
2. `.ai/memory/state.md` — what was executed, task progress
3. `.ai/principles/architecture.md` — patterns the implementation must conform to
4. `.ai/principles/coding.md` — code standards
5. `.ai/principles/domain.md` — domain correctness rules
6. `.ai/adr/index.md` — past decisions (violations = critical findings)
7. `.ai/context/runbook.md` — test/lint commands

Report: "Validation context loaded: [files read]". Then read implementation files.

---

## Instructions

1. Read `state.md` — extract `## Solution Design`: `### Invariants`, `### Acceptance Criteria`, `### Off-limits`.
   **`flow: quick`:** there is no `## Solution Design`. Read the same three sub-sections from
   `## Contract (quick)` instead — the quick tier's contract is inline and mandatory
   (`quick-flow → The quick path`). Everything below is unchanged.
2. Read all implementation files referenced in parent `state.md → ## Subtask Progress → T-XX → target_files:` for each T-XX subtask.
   **`flow: quick`:** there are no T-XX blocks. Use the files the quick task changed, recorded
   in `## TDD (quick)` and the task's `progress.md` entry; if neither lists them, recover them
   from `git diff --name-only` and say so in the report.
3. For each Invariant: verify it holds. Record pass/fail with reason.
4. For each Acceptance Criterion: verify it is met. Record pass/fail with reason.
5. For each Off-limits constraint: verify it is not violated. Record pass/fail with reason.
6. Write to `state.md`:

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
