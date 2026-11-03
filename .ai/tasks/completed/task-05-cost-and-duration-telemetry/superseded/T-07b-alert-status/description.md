## Goal
Provide pure status and threshold episodes with observable, deterministic behavior.

## Context
- Dependencies: T-07a — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Current status and thresholds; AC-17; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** pure status and threshold episodes, including all applicable requirements and negative cases in Current status and thresholds; AC-17.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_status.py, tests/usage-alert-status.py, scripts/usage-telemetry.py.

## Steps
1. Validate explicit current-owner snapshot and threshold policy without history discovery.
2. Evaluate measured values and completeness against strict policy boundaries.
3. Produce stable candidate identities and proposed episode state without modifying inputs.

## Acceptance Criteria
- Repeated status on the same input returns the same pending alert identity and proposed state without writing the input.
- Equality does not cross a threshold; unknown values do not reset an episode and expired policy produces no token or money alert.

- Out-of-range completeness policy is rejected; a proven lower bound can cross a threshold, and only an observed non-crossing resets an episode while corrections preserve prior alerts.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Repeated status on the same input returns the same pending alert identity and proposed state without writing the input. → the stated result is observed.
  - Equality does not cross a threshold; unknown values do not reset an episode and expired policy produces no token or money alert. → the stated result is observed.
  - Out-of-range completeness policy is rejected; a proven lower bound can cross a threshold, and only an observed non-crossing resets an episode while corrections preserve prior alerts. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
