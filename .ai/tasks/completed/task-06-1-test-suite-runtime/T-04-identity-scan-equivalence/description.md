## Goal
Optimize successful identity scans against the frozen corpus with the observable outcomes below.

## Context
- Dependencies: T-01
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: Successful byte/path/ledger semantics form one equivalence component; new failure handling is a separate RED cycle.
- TDD mode: characterize: behavior-preserving optimization only; new I/O expectations belong to T-05

- Parallel execution: lane `identity`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Replace only the identity hot loop with per-file normalization, matching and exact row aggregation; retain existing detected errors and ledger/knowledge logic.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `scripts/validate-contracts.sh`, `tests/validator-runtime-identity.py`, `tests/fixtures/validator-runtime/`

## Steps
1. Run and pin the complete frozen successful-input and existing-detected-error corpus before changing the hot loop; preserve the reference loop as test evidence, not a second production path.
2. Normalize embedded NUL bytes once per input, preserving newlines, CR, case and unterminated final lines; leave discovery, NUL filename transport, masking and symlink target selection intact.
3. Use at most one grep -aEion matching pass per scanned file, accept status 1 as empty and retain status >=2 as failure; preserve inherited locale and final LC_ALL=C sorts.
4. Aggregate exact path/line/token/count rows without awk -v backslash interpretation. Split line numbers at only the first colon and keep case-sensitive count keys.
5. Compare complete sorted rows, negative verdicts and diagnostics across C and an available UTF-8 locale; prove the unchanged knowledge inventory and ledger row validation still execute.
6. Measure the complete optimized identity/knowledge check in the controlled environment and retain the <=10-second result for final performance acceptance; no wall threshold is added to ordinary tests.

## Acceptance Criteria
- C1 (AC-03): every AC-03 frozen byte/path/ledger case produces identical sorted rows and verdicts before/after, including existing grep/output errors; unavailable UTF-8 coverage is disclosed.
- C2 (AC-04; REQ-06/08): hot-loop matching runs at most once per scanned file with no per-line subprocesses; discovery, row validation, expected rows and baseline knowledge inventory remain unchanged.

## Test Plan
- **Level:** unit, integration, contract
- **Scenarios:**
  - C1: run the differential corpus including NUL-split tokens, invalid bytes, CR, empty/final lines, mixed-case and merged-case ledgers, repeated tokens, path spaces/colons/backslashes, symlinks, ledger masks, missing paths and existing detected faults.
  - C2: count matching-process launches in disposable fixtures with varying line counts, compare exact row output, and verify source-bound ledger/knowledge logic plus complete-check timing evidence.
- **Edge cases:** complete AC-03 corpus; exact case counts, byte normalization, safe filenames, grep 1 versus >=2.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
