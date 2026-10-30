## Goal
Provide validated lifecycle usage projection with observable, deterministic behavior.

## Context
- Dependencies: T-03a — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Lifecycle projections; AC-05, AC-16; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** validated lifecycle usage projection, including all applicable requirements and negative cases in Lifecycle projections; AC-05, AC-16.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_publication.py, tests/usage-lifecycle-projection.py, scripts/log-step.sh.

## Steps
1. Validate optional counters, projection inputs and exact cost scalar before lifecycle mutation.
2. Add first-acceptance projections without adding a lifecycle event or claiming unproved completeness.
3. Preserve accepted replay payloads and existing behavior on invalid inputs or unavailable dependencies.

## Acceptance Criteria
- A complete self-contained projection agrees exactly with its cost scalar and preserves the original payload on checkpoint replay.
- Invalid projections and mismatched scalars leave lifecycle bytes, sequence, clock and active state unchanged.

- A self-contained 0.00264 fixture is independently validated against its evidence and cannot be represented by canonical zero.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - A complete self-contained projection agrees exactly with its cost scalar and preserves the original payload on checkpoint replay. → the stated result is observed.
  - Invalid projections and mismatched scalars leave lifecycle bytes, sequence, clock and active state unchanged. → the stated result is observed.
  - A self-contained 0.00264 fixture is independently validated against its evidence and cannot be represented by canonical zero. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
