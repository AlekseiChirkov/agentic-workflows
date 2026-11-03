## Goal
Provide owner-controlled warning delivery with observable, deterministic behavior.

## Context
- Dependencies: T-07c — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Delivery and crash recovery; AC-17; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** owner-controlled warning delivery, including all applicable requirements and negative cases in Delivery and crash recovery; AC-17.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_status.py, tests/usage-warning-delivery.py, scripts/usage-telemetry.py, workflows/spec-run.md, workflows/phase-pipeline.md.

## Steps
1. Represent pending and confirmed delivery in owner-controlled state.
2. Apply an idempotent note by stable candidate identity after the state is accepted.
3. Recover interrupted or unavailable delivery without stopping execution or writing outside the owner scope.

## Acceptance Criteria
- A pending warning survives interruption and retry applies one idempotent note under the same identifier.
- An unavailable note destination stays pending for the report and collection disablement does not erase delivery state.

- The authorized orchestrator atomically accepts the status-proposed revision, persists pending then confirmed delivery, recovers between those boundaries, and writes the warning only to the matching leaf or run notes and final report.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - A pending warning survives interruption and retry applies one idempotent note under the same identifier. → the stated result is observed.
  - An unavailable note destination stays pending for the report and collection disablement does not erase delivery state. → the stated result is observed.
  - The authorized orchestrator atomically accepts the status-proposed revision, persists pending then confirmed delivery, recovers between those boundaries, and writes the warning only to the matching leaf or run notes and final report. → the integrated boundary produces the stated result.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
