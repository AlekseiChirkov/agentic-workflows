## Goal
Validate jobs and schedule productive bounded slots with the observable outcomes below.

## Context
- Dependencies: T-01, T-07a
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: Admission decisions are one deterministic scheduling component using the already tested lifecycle interface.
- TDD mode: RED

- Parallel execution: lane `lifecycle`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Implement full-run jobs validation, resource/exclusive scheduling and productive slot refill over supervised synthetic workers.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `scripts/validate-contracts.sh`, `tests/validator-runtime-scheduler.py`

## Steps
1. Add RED grammar/default/clamp and barrier/counter scheduler tests with 0, 1 and partial-final-batch inputs; use observed active counts rather than wall-time concurrency guesses.
2. Validate set ORCHESTRAIL_TEST_JOBS with [1-9][0-9]* before any full check or worker; reject empty/sign/leading-zero/whitespace/nondecimal values naming the variable. Clamp valid huge decimals to 36 textually before bounded arithmetic.
3. For unset jobs, choose min(4, positive nproc result), else positive getconf _NPROCESSORS_ONLN, else 1. Preserve focused dispatch before all new validation.
4. Admit independent groups into available slots without batch waits, retain original registration order for jobs=1 and allow resource-inventory exclusive groups only when no other tree is alive.
5. Bind slots to complete owned worker lifetimes; a finished shell with live descendants cannot free its slot or release a snapshot barrier.
6. Prove maximum active counts, real overlap for independent jobs>1, immediate slot refill, exclusive drain, terminal-signal launch suppression and empty/partial input completion.

## Acceptance Criteria
- C1 (AC-06/13/16): every listed invalid value fails before a full check/worker; huge valid decimals clamp to 36 without overflow; nproc/getconf/fallback defaults and focused-mode bypass match REQ-10/15.
- C2 (AC-13/15): active groups never exceed jobs, independent jobs>1 overlap and free slots refill; jobs=1 runs exactly one in order, exclusive groups drain/isolate, and 0/1/partial batches finish without deadlock.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - C1: inject CPU command results and jobs values including empty, 0, -1, +1, 01, x, whitespace and thousands of decimal digits; assert rejection or exact effective cap before launch sentinel.
  - C2: controlled launch/finish handshakes and active counters prove bounds, overlap, refill, exclusive order and complete descendant drain without elapsed-time pass/fail guesses.
- **Edge cases:** textual overflow avoidance, CPU failures, set-empty versus unset, exclusivity, terminal races, empty input.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
