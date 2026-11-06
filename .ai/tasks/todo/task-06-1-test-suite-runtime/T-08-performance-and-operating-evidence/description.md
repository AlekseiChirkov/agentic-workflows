## Goal
Complete performance acceptance and operating guidance with the observable outcomes below.

## Context
- type: composite
- children: T-08a, T-08b
- Dependencies: T-01, T-02, T-03, T-04, T-05, T-06, T-07
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: Controlled performance acceptance and delivered operating documentation have separate verifiable outcomes; the parent checks their agreement.
- TDD mode: integration validation after all children are reviewed; no parent atomic RED cycle

- Parallel execution: lane `composite join / coordinator`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Integrated complete performance acceptance and operating guidance; each child owns its distinct component and RED/characterization evidence.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `.ai/memory/progress.md`, `.ai/tasks/todo/task-06-1-test-suite-runtime/state.md`, `.ai/context/runbook.md`, `docs/USAGE.md`, `.ai/adr/0018-task-06-1-bounded-validator-runtime.md`, `.ai/adr/index.md`, `.ai/memory/architecture.md`

## Steps
See children: T-08a (Measure the complete optimized validator against the baseline), T-08b (Document the verified validator behavior and decisions).

## Acceptance Criteria
- C1 (AC-02/04/09/10/12): the exact stable implementation described in the operating guidance has valid baseline/sequential/default evidence meeting every binding target, or acceptance remains explicitly incomplete.
- C2 (AC-11/12): docs, indexed ADR, memory and complete result inventory agree with the verified jobs/timing/cleanup behavior; no deployment, reduced coverage or internal planning identifier enters product changes.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - C1: reconcile measurement manifests and retained samples against delivered docs and immutable spec budgets; any missing/missed budget prevents parent completion.
  - C2: inspect source/docs/ADR/memory consistency, exact full/focused outputs and product identifier hygiene; ensure real stores/settings remain unchanged.
- **Edge cases:** cross-child contract drift, resource/record lifetime, evidence/documentation disagreement.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
