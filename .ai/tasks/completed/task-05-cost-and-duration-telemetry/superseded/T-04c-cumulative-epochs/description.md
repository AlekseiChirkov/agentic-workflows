## Goal
Provide cumulative epochs and aggregate coverage with observable, deterministic behavior.

## Context
- Dependencies: T-04b — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Cumulative epochs and aggregates; AC-10; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** cumulative epochs and aggregate coverage, including all applicable requirements and negative cases in Cumulative epochs and aggregates; AC-10.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_resolution.py, tests/usage-cumulative-epochs.py.

## Steps
1. Validate epoch, account, model, units and consecutive cumulative snapshot boundaries.
2. Compute request deltas only for proven enclosed single requests or an equivalent atomic profile.
3. Keep unresolved aggregates separate and prevent overlapping additions.

## Acceptance Criteria
- Two adjacent snapshots with one fully enclosed request produce its exact evidenced delta.
- A mid-request snapshot, unknown epoch, reset or gap does not invent full request usage or double-count an overlapping aggregate.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Two adjacent snapshots with one fully enclosed request produce its exact evidenced delta. → the stated result is observed.
  - A mid-request snapshot, unknown epoch, reset or gap does not invent full request usage or double-count an overlapping aggregate. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
