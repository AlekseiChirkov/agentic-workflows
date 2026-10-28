---
description: Validation Step 2 — Code review: readability, architecture consistency, security, edge cases
---

Invocation: `/pv-review <task-directory>`
Called by: `/phase-validation` as Step 2.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md` in the task directory.
2. Check `## Phases → validation`. If `complete` → **stop**: "Validation phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Check `## Contract Check` must be present. If missing → **stop**: "Step 1 (`/pv-contract`) must be completed first."
4. Check `### Critical Failures Decision` inside `## Contract Check`:
   - If critical Invariant/Off-limits failures exist and the decision field is absent → **stop**: "`/pv-contract` stopped at the critical-failure gate. Resolve it before running `/pv-review`."
   - If decision is `pause` → **stop**: "Validation is paused pending critical-failure fix. Do not run `/pv-review`."
   - If decision is `continue-marked` or no critical failures → continue.
5. Otherwise → continue.

---

## Context Bootstrap

Load the `phase-validation` rule (`## Context Bootstrap`) before reading implementation files or
writing project files; run the full bootstrap when invoked standalone. The rule owns
the load order, umbrella precedence, conditional sources, and reporting.

---

## Instructions

1. Read `state.md` — extract `## Solution Design → Decision` for architectural context.
   **`flow: quick`:** read `## Contract (quick)` instead — it holds the tier's `### Off-limits`,
   `### Invariants`, and `### Acceptance Criteria`, and `## TDD (quick)` holds the test record
   the test-coverage findings below are judged against.
   If `### Critical Failures Decision: continue-marked` is recorded in `## Contract Check` — carry every failed Invariant/Off-limits entry into `### Findings` as a `critical` item (prefixed with `contract:`).
2. Read the same task-owned file set `/pv-contract` used, including tests. For full tasks,
   union cumulative `target_files:` and resolve each subtask's `working_dir:`; for quick
   tasks, use the persisted inline file list. Do not infer quick tasks have leaf blocks.
3. Review for:
   - **Readability and clarity** — naming, structure, comments where needed.
   - **Architectural consistency** — implementation matches chosen approach.
   - **Security vulnerabilities** — injection, access control, secret handling.
   - **Uncovered edge cases** — null values, empty collections, error paths, boundary conditions.
   - **Contract violations** — public interfaces changed unexpectedly.
   - **Test coverage and integrity** — review the test files in `target_files:` as code, not
     as an afterthought. Load the `tdd` rule and `testing-standards`. Findings:
     - A subtask with `atomic-tests: n-a` whose `notes:` justification is missing or
       hand-waving ("hard to test", "no framework", "small change", "will add later",
       "existing tests cover it") → `important`.
     - A test amendment recorded during GREEN whose stated reason blames the implementation
       rather than the test → `critical`: the contract was bent to fit the code.
     - Testable Acceptance Criteria with no corresponding test → `important`; justified
       `n-a` and recorded legacy exemptions are audited against their exemption instead.
     - Tests that assert implementation details rather than behaviour, use `Mock()` for
       repository interfaces, or whose only assertion is vacuous → `important`.
4. Upsert one `## Code Review` section in `state.md`, retaining prior resolution evidence:

```
## Code Review

### Findings
<numbered list: file, description, severity (critical / important / optional)>

### Summary
<overall assessment: count by severity>
```

5. Report: "Step 2 (Code Review) complete. N findings (X critical, Y important, Z optional)."
Return to the caller; this is a progress marker.
