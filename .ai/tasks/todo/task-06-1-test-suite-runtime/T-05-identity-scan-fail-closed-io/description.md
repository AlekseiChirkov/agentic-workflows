## Goal
Reject incomplete identity-scan I/O with the observable outcomes below.

## Context
- Dependencies: T-04
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: New scan error semantics require their own observable RED set rather than an equivalence claim.
- TDD mode: RED

- Parallel execution: lane `identity`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Correct read/normalization/aggregation/write failure handling in the same scanner; preserve successful rows and existing diagnostics except the allowed per-file grep line-number omission.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `scripts/validate-contracts.sh`, `tests/validator-runtime-identity.py`

## Steps
1. Freeze new RED fault expectations separately from the pinned successful-input corpus; demonstrate a read error that the original Bash loop incorrectly treats as EOF.
2. Inject read, normalization, aggregation and output failures independently, including partial output whose rows would otherwise match the ledger; use deterministic seams effective under root.
3. Propagate failure status across every new normalization/matching/aggregation/write boundary and reject incomplete rows before ledger comparison; never convert an error into empty success.
4. Retain grep no-match success and existing grep failure behavior, allowing only the specified line-number omission for per-file grep errors.
5. Run the full fault matrix to GREEN and the frozen differential corpus unchanged. Record intentional error-handling corrections and all test amendments under the TDD rules.

## Acceptance Criteria
- C1 (AC-17): read-as-EOF, failed normalization, failed aggregation and partial-output-then-failure each produce a nonzero scanner failure even when partial rows match the ledger; root-safe injected failures are observed RED then GREEN.
- C2 (AC-03/17): the complete successful-input and existing-detected-error characterization remains passing with unchanged rows/verdicts, and diagnostics differ only by the permitted per-file grep line-number exception.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - C1: force each stage to fail before output and after valid partial output; verify nonzero status and no clean verdict, comparing the old read-as-EOF behavior only as correction evidence.
  - C2: rerun the immutable differential corpus and baseline failure cases under both locales, asserting exact diagnostics with only the explicitly permitted exception.
- **Edge cases:** root-insensitive fault injection, partial writes, pipe exit status, read-as-EOF, full disk/unwritable outputs.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
