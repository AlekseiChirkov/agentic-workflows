## Goal
Contain and reap complete worker process trees with the observable outcomes below.

## Context
- Dependencies: T-01
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: Worker lifecycle has a standalone PID/cleanup oracle independent of scheduling and report policy.
- TDD mode: RED

- Parallel execution: lane `lifecycle`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Implement the Linux standard-library ownership supervisor and private worker record lifecycle, tested with tiny synthetic trees before real suites.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `scripts/validate-contracts.sh`, `tests/validator-runtime-processes.py`

## Steps
1. Add RED handshake-driven direct/grandchild/stubborn/setsid worker fixtures and an unrelated sentinel; establish recorded PIDs alive before interruption.
2. Implement inline Linux subreaper containment for the runner and per-worker ownership boundaries, with standard-library process control and fail-closed initialization. Ownership must survive shell exit, reparenting and new sessions.
3. Create one mktemp -d runner directory with per-group separate stdout/stderr, result/status and optional timing records; publish complete records atomically and distinguish execution failure from a valid failure verdict.
4. On INT/TERM, stop launches, forward to owned descendants, allow at most 2 seconds for grace, escalate remaining owned processes to KILL and finish reaping/cleanup within a further 2 seconds in controlled tests. Return 130/143 and protect caller/sentinel.
5. Exercise normal/failing/externally killed workers and supervisor errors; reap descendants before removing records, handle missing/partial metadata and capture/launch failures as infrastructure errors.
6. Verify no owned PID or held-open pipe survives and no unrelated process is signaled. Keep cleanup tests bounded and independent of unittest addCleanup in a killed fixture.

## Acceptance Criteria
- C1 (AC-06/14): normal, failed and handled INT/TERM runs reap direct, grandchild, stubborn and escaped-session descendants and remove the private directory; signal cleanup meets the 2+2-second controlled budget, exits 130/143, and preserves the sentinel/caller.
- C2 (AC-14): launch, capture, missing/malformed/partial-record and unwritable-output faults all cause a nonzero infrastructure result, complete owned-resource cleanup and no invented PASS or successful completion summary.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - C1: handshake each PID alive, signal while spawning/waiting/reporting, verify escalation, PID disappearance, directory removal and sentinel survival; repeat for normal and nonzero worker exits.
  - C2: inject each publication/capture/launch fault and an externally killed worker, assert abnormal status and no leaks/double-counted result; keep fake PASS text in stdout as a counter-confusion probe.
- **Edge cases:** reparenting, setsid, PID identity/reuse, signal races, partial metadata, retained pipes, supervisor failure.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
