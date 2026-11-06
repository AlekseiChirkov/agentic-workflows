## Goal
Add opt-in timing around complete result evaluation with the observable outcomes below.

## Context
- Dependencies: T-01
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: One timing adapter must prove its expansion boundary and output compatibility before scheduler integration.
- TDD mode: RED

- Parallel execution: lane `timing`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Add full-run-only monotonic timing without rewriting extracted run-log check shapes or starting an interpreter per check.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `scripts/validate-contracts.sh`, `tests/validator-runtime-timing.py`

## Steps
1. Add RED synthetic tests for enabled per-result timing, clock failures and pre-expansion measurement, retaining pinned conditional/errexit/subshell checks.
2. Gate timing after existing focused dispatch. Adopt the opt-in pre-expansion hook only after executable proof; use Bash built-in reads of /proc/uptime, document centisecond quantization and avoid per-check Python/date/EPOCHREALTIME.
3. Attach exactly one indented time_ms integer after each entire result block, including multiline failure/skip text; preserve all non-timing stdout/stderr bytes.
4. Make timing-off paths perform no timing-only sampling/helper startup; keep scheduler lifecycle clocks conceptually separate. Missing or invalid clock data fails abnormally without a fabricated result duration.
5. Test a controlled monotonic source against real-time jumps and argument-side work, and prove queue/report waits are excluded when worker integration is added.
6. Run unchanged extracted run-log harness and PYCORRELATED inspection; keep marker pairs, literal function line and two-line harness-parsed check calls self-contained.

## Acceptance Criteria
- C1 (AC-08/16): unset/empty/0/other timings values preserve ordinary bytes; 1 emits one nonnegative integer time_ms line per complete outer result, including expression evaluation and excluding queue/report waits.
- C2 (AC-08/11/16): timing off performs no timing-only sampling/helper startup; focused dispatch ignores invalid jobs and enabled timings; unchanged Bash semantics, extracted harness and PYCORRELATED checks pass. A clock failure is nonzero.

## Test Plan
- **Level:** unit, integration, contract
- **Scenarios:**
  - C1: deterministic clock/argument probes cover PASS, SKIP and multiline FAIL, simulated wall-clock jumps and withheld report release; assert one correctly placed line and exact stable non-timing channels.
  - C2: instrument clock access/startup, exercise focused mode with hostile new variables, execute the pinned Bash/consumer fixtures, and inject clock read/parse failures.
- **Edge cases:** argument expansion order, DEBUG recursion/inheritance, conditional errexit, multiline blocks, clock faults.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
