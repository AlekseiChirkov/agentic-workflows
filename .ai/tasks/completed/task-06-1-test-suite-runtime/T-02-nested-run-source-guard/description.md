## Goal
Implement the bounded nested-run source guard with the observable outcomes below.

## Context
- Dependencies: T-01
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: A single source-classification component has its own mutation oracle and can reject unsafe source before runtime integration.
- TDD mode: RED

- Parallel execution: lane `guard`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Implement the bounded reference inventory/scanner and exact exception validation. Define its callable validator check, but defer ordinary full-run registration until the guarded warning fixture is safe.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `scripts/validate-contracts.sh`, `tests/validator-runtime-guard.py`, `tests/fixtures/validator-runtime/`

## Steps
1. Use the frozen reference inventory to enumerate direct Bash calls, $validator aliases, copied paths, multiline Python argv, generated scripts, comments and source-copy data across the validator and regular tests shell/Python sources.
2. Add RED tests for absent classification and unsafe calls; require the unchanged pre-warning-optimization source to be rejected for exactly its three complete history calls.
3. Implement bounded classification with a real supported focused flag on the same argv. Unknown executable/reference/alias forms fail for review; comments and literal source data are classified rather than silently ignored.
4. Bind each exception to its stable container, exact statement/fingerprint, count and reason. Only a locally verified exact guarded trim can allow the three history calls; pin approved relocation/installer stubs without blanket file exemptions.
5. Run all prescribed mutations: direct/copied/alias full calls, multiline argv, missing/altered focused flag, unrelated trim text and changed/deleted/duplicated/stale allowances. Verify expected rejection and cleanup in private fixtures.
6. Expose the guard as a self-contained callable and retain pre-change rejection evidence. Its production result registration belongs with the next fixture amendment so this intermediate commit does not knowingly add a failing ordinary gate.

## Acceptance Criteria
- C1 (REQ-16/17; AC-07): the source scanner rejects unchanged pre-W1 source for the three complete history invocations and rejects every unclassified or mutated executable form; each approved focused call has a supported flag on its own argv.
- C2 (AC-07): exact trimmed-fixture and stub exceptions pass only at their frozen statement/context/count; unrelated trimming text, stale exceptions and count changes all fail. Comments/source-copy data pass their explicit classification.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - C1: run every AC-07 mutation and the real frozen pre-W1 source through the scanner; compare nonzero verdict and offending reference identity, with no production full validator executed.
  - C2: test approved miniature source forms, then independently alter context, fingerprint and occurrence count; only the original approved forms pass.
- **Edge cases:** multiline argv, aliases, copied/generated code, source-as-data, stale exceptions, scanner self-references.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
