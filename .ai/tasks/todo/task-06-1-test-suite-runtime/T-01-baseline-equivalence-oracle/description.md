## Goal
Freeze the implementation equivalence oracle with the observable outcomes below.

## Context
- Dependencies: none
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: One frozen oracle supplies the source/result/resource provenance consumed by every optimization.
- TDD mode: characterize: pin existing behavior; baseline measurement is evidence, not a new wall-time assertion

- Parallel execution: lane `baseline / exclusive runs`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Freeze the stable integrated implementation payload and baseline evidence; add a reusable characterization corpus without changing validator behavior.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `tests/validator-runtime-characterization.py`, `tests/fixtures/validator-runtime/`, `.ai/memory/progress.md`

## Steps
1. Select an isolated current integrated checkout; record commit, content hashes, dirty paths and exact source payload before creating implementation fixtures. Preserve this checkout and all unrelated work.
2. Inventory ordered outer result identities and all 36 full-run expressions, wrapper bodies, excerpt lengths and channels; freeze all 37 focused dispatch forms and existing Bash conditional/errexit/subshell behavior.
3. Inventory validator references and per-group resources: source writes, bytecode, fixed paths, locks, ports, inherited stores and runtime bounds. Give each group an explicit independent/exclusive/conflict classification with evidence; unresolved classification stays exclusive.
4. Write successful-input scanner and consumer characterization using bounded extraction of the actual current functions. Include the complete AC-03 corpus, wrapper diagnostics and unchanged extraction markers; execute and pin these tests before changing implementation.
5. Run at least two unchanged real full baselines with /usr/bin/time -v, no competing heavy work, consistent cache/locale/hygiene policy, and all specified environment fields. Record every sample and the frozen result inventory outside the measured source payload.
6. If samples differ by more than 10% of their median, investigate and obtain a third, retaining all samples. Verify baseline failures are zero; record B and a reproducible manifest invalidated by later unrelated source changes.

## Acceptance Criteria
- C1 (REQ-22/24; AC-03/05/10/11/15/16): the frozen oracle identifies every actual outer result, exactly 36 original expression/body/diagnostic mappings, 37 focused dispatches and all resource classifications; deliberate expression, name or order changes are detected.
- C2 (AC-03/11/16): characterization passes on the unchanged implementation for the full byte/path/ledger corpus, all wrapper conventions, selected focused argument/exit fixtures and Bash semantics; no baseline assertion is inferred from historical counts.
- C3 (AC-09): at least two valid complete baseline samples have exit 0 and zero failures, identical payload/config manifests and every required measurement field; variability triggers the specified third sample before B is accepted.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - C1: mutate a disposable oracle input name, expression and result order independently; comparison rejects each and a matching frozen payload passes.
  - C2: execute the unchanged scanner under C and an available UTF-8 locale; rows, verdicts, wrapper channels and extraction fixtures match the captured oracle. Record unavailable locale coverage explicitly.
  - C3: validate the baseline record against required fields, source hashes, samples and variance rule, then inspect the retained real full outputs and calculated B.
- **Edge cases:** byte/path/locale boundaries, duplicate identities, source drift, real-store isolation, unstable samples.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
