## Goal
Replace complete warning-fixture runs with the guarded prefix with the observable outcomes below.

## Context
- Dependencies: T-01, T-02
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: One history-fixture construction change removes recursive work while preserving its three warning assertions.
- TDD mode: RED

- Parallel execution: lane `guard`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Trim the real validator prefix and minimal git fixture, record the narrow test amendment, and register the already verified source guard once.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `scripts/validate-contracts.sh`, `tests/validator-runtime-warning.py`, `.ai/memory/progress.md`

## Steps
1. Before amending any frozen test, record the exact removed incidental complete-copy assertion and why REQ-03 replaces its coverage; keep all three warning and exit-status assertions.
2. Add RED construction tests for missing/duplicate standalone anchors, a top-level check before the anchor and an executable sentinel after the cut; add warning always-present/always-absent/ignores-worktree mutations.
3. Replace whole-tree tar and six-group/31-call stripping with a real prefix through the unique warn_stale_contract_version call plus exit 0. Copy only the trimmed script, VERSION and necessary rule material before the initial fixture commit.
4. Isolate HOME/XDG/git identity/config, disable inherited signing/hooks and retain exact history-state warning text and exit 0 assertions.
5. Register the nested-run source guard exactly once as an additive named outer check, preserving the baseline result sequence. Reconcile its precise trim exception and new fixture references.
6. Run all warning/guard mutations and the frozen existing warning cases. Record an isolated full-fixture measurement for later <=10-second acceptance without placing that budget inside the ordinary suite.

## Acceptance Criteria
- C1 (AC-01/02): no copied outer check or post-cut sentinel executes; the three warning states and exit 0 assertions pass, while every warning mutation and invalid construction fails.
- C2 (AC-02/07/10): the exact source guard is GREEN on the amended source, registered once with a declared inventory delta, and the private fixture contains only required material and no complete validator run. The TDD construction amendment is recorded.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - C1: execute the real warning prefix in three isolated git states, then all construction/warning mutants; inspect sentinel and outputs, never run repeated full validators for mutations.
  - C2: compare the new declared result inventory to the baseline plus one guard result, run the guard on both frozen unsafe and amended safe source, and inspect fixture contents and amendment evidence.
- **Edge cases:** anchor cardinality, early checks, unstaged version edits, signing/hooks/config inheritance, failure exits.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
