## Goal
Provide inventory and measurement completeness with observable, deterministic behavior.

## Context
- Dependencies: T-04c — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Completeness and monetary states; AC-11, AC-23; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** inventory and measurement completeness, including all applicable requirements and negative cases in Completeness and monetary states; AC-11, AC-23.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_resolution.py, tests/usage-inventory-completeness.py.

## Steps
1. Validate independent inventories and track known expected slots and unresolved branches.
2. Calculate per-measurement finality and pricing numerators and denominators for the chosen scope.
3. Represent unknown and evidenced-empty billable scopes without invented fractions or costs.

## Acceptance Criteria
- Two independently inventoried final requests with one unknown price report token completeness 2/2 and priced coverage 1/2.
- Unknown inventory has an unknown denominator; proven empty billable scope alone permits exact zero.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Two independently inventoried final requests with one unknown price report token completeness 2/2 and priced coverage 1/2. → the stated result is observed.
  - Unknown inventory has an unknown denominator; proven empty billable scope alone permits exact zero. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
