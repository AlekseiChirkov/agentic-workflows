## Goal
Provide legacy compatibility and recovery with observable, deterministic behavior.

## Context
- Dependencies: T-07d — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Nonfunctional requirements and errors; AC-05, AC-08, AC-14, AC-24; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** legacy compatibility and recovery, including all applicable requirements and negative cases in Nonfunctional requirements and errors; AC-05, AC-08, AC-14, AC-24.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** docs/USAGE.md, tests/usage-compatibility-recovery.py, scripts/validate-contracts.sh, tests/log-step.sh, tests/usage-end-to-end.py, workflows/retro.md.

## Steps
1. Exercise old lifecycle behavior and optional dependency absence in isolated fixtures.
2. Inject filesystem, concurrency and interrupted-publication failures and verify exact retry.
3. Run synthetic offline acceptance checks with network and paid calls forbidden.

## Acceptance Criteria
- Legacy logging works without optional usage dependencies and telemetry failures leave accepted lifecycle artifacts unchanged.
- Fault injection at publication and recovery boundaries produces no false receipt and an exact retry recognizes a previously installed bundle.

- The ordinary synthetic validation suite makes no network or paid model calls.

- An explicitly selected synthetic source, duplicate response and independent two-response inventory pass through normalization, publication, resolution, pricing and all three exports: tokens are 2/2 complete, pricing is 1/2, the duplicate is counted once, and a fixed-corpus rerun has identical semantic results.

- A projection built from resolved and priced evidence passes the producer check with the exact computed amount 0.00264; canonical zero is rejected without changing lifecycle evidence.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Legacy logging works without optional usage dependencies and telemetry failures leave accepted lifecycle artifacts unchanged. → the stated result is observed.
  - Fault injection at publication and recovery boundaries produces no false receipt and an exact retry recognizes a previously installed bundle. → the stated result is observed.
  - The ordinary synthetic validation suite makes no network or paid model calls. → the stated result is observed.
  - An explicitly selected synthetic source, duplicate response and independent two-response inventory pass through normalization, publication, resolution, pricing and all three exports: tokens are 2/2 complete, pricing is 1/2, the duplicate is counted once, and a fixed-corpus rerun has identical semantic results. → the integrated boundary produces the stated result.
  - A projection built from resolved and priced evidence passes the producer check with the exact computed amount 0.00264; canonical zero is rejected without changing lifecycle evidence. → the exact result and unchanged evidence are verified.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
