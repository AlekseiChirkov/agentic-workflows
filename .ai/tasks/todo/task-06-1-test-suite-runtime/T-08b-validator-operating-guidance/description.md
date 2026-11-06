## Goal
Document the verified validator behavior and decisions with the observable outcomes below.

## Context
- Dependencies: T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08a
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: Operating guidance is one documented interface checked against the actual delivered runtime and acceptance evidence.
- TDD mode: RED

- Parallel execution: lane `docs finalization`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Update only validator operating text, the provisional indexed decision and relevant implementation memory after measurement; retain unresolved limitations honestly.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `.ai/context/runbook.md`, `docs/USAGE.md`, `.ai/adr/0018-task-06-1-bounded-validator-runtime.md`, `.ai/adr/index.md`, `.ai/memory/architecture.md`, `.ai/memory/progress.md`

## Steps
1. Add RED smoke/contract checks for the documented jobs grammar/default/cap, jobs=1 fallback, exclusive scheduling, full-only timing source/resolution and actual measured evidence; execute through additive runtime verification already registered by integration.
2. Update runbook and relevant usage validator sections to describe delivered behavior and real verified result counts, distinguishing binding performance evidence from historical stretch goals.
3. Update the matching provisional ADR in place with actual fixture amendment, cleanup/synchronization/timing choices and any literal-check convention exception; leave promotion to final validation after all acceptance passes.
4. Update relevant memory with implemented interfaces/evidence and pending limitations; keep unrelated task history and complete knowledge preservation intact.
5. Run the documentation contracts, inspect product diff for internal planning identifiers/attribution, and reconcile every operating claim to retained source and measurement evidence. Repeat affected optimized full correctness/performance comparisons after any new documentation check changes the tested payload; refresh the evidence before closing. Reuse B only when its original payload/config remains valid. No real deployment or installed-copy update is part of verification.

## Acceptance Criteria
- C1 (AC-12; REQ-20/21): runbook/usage describe exact delivered defaults, cap/validation, sequential fallback, exclusivity, timing scope/resolution and measured runtime/counts, with no unsupported completed-performance claim.
- C2 (AC-11/12): the existing indexed ADR records fixture/concurrency/cleanup/check-convention decisions and verified evidence without duplication; product changes contain no internal planning identifiers and real settings/stores/installed copies are untouched.

## Test Plan
- **Level:** smoke, contract
- **Scenarios:**
  - C1: observed RED documentation contracts become GREEN after wording updates, then compare claims to runtime cases and T-08a source/sample manifests.
  - C2: validate matching ADR/index linkage, required decision subjects and evidence; inspect the product diff and disposable sync failure result, asserting no real deployment.
- **Edge cases:** stale counts, unknown measurements, provisional-versus-accepted status, source/doc drift, identifier leakage.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
