## Goal
Provide measured duration and interval coverage with observable, deterministic behavior.

## Context
- Dependencies: T-06c — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Time measurement; AC-22; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** measured duration and interval coverage, including all applicable requirements and negative cases in Time measurement; AC-22.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_report.py, tests/usage-duration-analysis.py, scripts/usage-telemetry.py, scripts/run-log-timing.py.

## Steps
1. Validate measured parent and child intervals, clock compatibility and complete graph coverage.
2. Compute wall time, worker sum, interval union and exclusive time independently.
3. Preserve unavailable or approximate timing without inventing waiting or rewriting events.

## Acceptance Criteria
- Parent [0,10] with children [1,7] and [4,9] yields wall 10, worker sum 11, union 8 and exclusive 2.
- Missing children, incompatible clocks or invalid parentage leave exclusive time unknown without subtracting grandchildren twice.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Parent [0,10] with children [1,7] and [4,9] yields wall 10, worker sum 11, union 8 and exclusive 2. → the stated result is observed.
  - Missing children, incompatible clocks or invalid parentage leave exclusive time unknown without subtracting grandchildren twice. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
