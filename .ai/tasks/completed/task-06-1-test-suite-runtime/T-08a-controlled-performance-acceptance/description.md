## Goal
Measure the complete optimized validator against the baseline with the observable outcomes below.

## Context
- Dependencies: T-01, T-02, T-03, T-04, T-05, T-06, T-07
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: One controlled acceptance record decides whether the runtime objective was achieved on the actual payload.
- TDD mode: characterize: compare the frozen full-run contract; external performance acceptance is measured evidence, not synthetic RED or a new in-suite threshold

- Parallel execution: lane `measurement / exclusive`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Run complete correctness/performance acceptance with unchanged source during each comparison; record all samples and budget misses.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `.ai/memory/progress.md`, `.ai/tasks/todo/task-06-1-test-suite-runtime/state.md`

## Steps
1. Check baseline provenance and stable intended-only source/config/cache differences against T-01; invalidate affected comparisons after unrelated source changes and repeat required baselines rather than reuse historical figures.
2. Run at least two jobs=1 and two default full commands sequentially under /usr/bin/time -v with no competing validator/heavy work. Retain every sample and the complete required environment, resource and outer-result records.
3. Apply the >10%-of-median variability rule with a third sample when required; use the arithmetic mean for two samples and the three-value median otherwise.
4. Compare exact check identities/positions/channels, baseline zero failures and additive named N: optimized clean counts must be (pass+N, 0, skip). Keep hygiene availability and optional skips identical.
5. Measure isolated complete warning and identity checks, plus prefix, concurrent makespan, exclusive groups and suffix. Verify S<=B*360/1171.4, P<=B*240/1171.4 and each individual check<=10 s; report old 360/240 s goals separately.
6. Record the full evidence and dominant costs. Any missed binding target leaves AC-09 and this subtask incomplete; do not lower targets, change suite assertions/timeouts or expand scope to force acceptance.

## Acceptance Criteria
- C1 (AC-02/04/09): valid retained samples prove the exact S/P proportional budgets and both <=10-second individual budgets under the specified protocol; any absent/missed target is explicitly incomplete, never rounded into success.
- C2 (AC-05/09/10/15): source/config/cache provenance is stable, every required measurement field and sample is retained, exclusive scheduling is documented and complete ordered output/count comparison matches the frozen inventory plus named additive checks.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - C1: compute B/S/P from retained controlled real runs, inspect variance/third-run handling and individual checks, and verify exact inequalities without ordinary-suite wall assertions.
  - C2: reconcile manifests, separate stdout/stderr outputs and exact name/count/order deltas; inspect CPU quota/RAM/runtime/locale/cache/hygiene/job/RSS/exit fields and prefix/makespan/suffix attribution.
- **Edge cases:** measurement source drift, cache parity, >10% variation, incomplete samples, binding budget misses.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
