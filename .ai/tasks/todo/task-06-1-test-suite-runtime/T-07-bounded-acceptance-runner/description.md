## Goal
Run acceptance groups with bounded owned concurrency with the observable outcomes below.

## Context
- type: composite
- children: T-07a, T-07b, T-07c
- Dependencies: T-01
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: Lifecycle ownership, admission policy and Bash reporting integration are three independently testable components with three criteria clusters.
- TDD mode: integration validation after all children are reviewed; no parent atomic RED cycle

- Parallel execution: lane `composite join / coordinator`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Integrated run acceptance groups with bounded owned concurrency; each child owns its distinct component and RED/characterization evidence.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `scripts/validate-contracts.sh`, `tests/validator-runtime-processes.py`, `tests/validator-runtime-scheduler.py`, `tests/validator-runtime-integration.py`, `tests/fixtures/validator-runtime/`

## Steps
See children: T-07a (Contain and reap complete worker process trees), T-07b (Validate jobs and schedule productive bounded slots), T-07c (Integrate original expressions and ordered output).

## Acceptance Criteria
- C1 (AC-05/06/13/14): integrated real-expression workers respect jobs/exclusive admission and source-order reporting, preserve diagnostics/counters and continue independent groups after failures; signal/infrastructure exits never report successful completion.
- C2 (AC-11/15/16): no owned tree crosses a source-snapshot barrier, focused/extracted consumers remain unchanged, and handled interruptions leave neither owned PIDs nor runner records while an unrelated sentinel survives.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - C1: compose lifecycle, scheduler and Bash reporting against delayed/failing synthetic groups plus all frozen expression mappings, checking exact channels, counters and 130/143 exits.
  - C2: run before/after snapshot handshakes, escaped-descendant interruption, focused-variable fixtures, unchanged harness extraction and the disposable sync failure sentinel.
- **Edge cases:** cross-child contract drift, resource/record lifetime, evidence/documentation disagreement.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
