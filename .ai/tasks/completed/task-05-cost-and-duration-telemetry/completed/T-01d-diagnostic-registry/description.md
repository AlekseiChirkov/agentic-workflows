## Goal
Provide typed diagnostic metrics with observable, deterministic behavior.

## Context
- Dependencies: T-01c — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Additional diagnostics; AC-20; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** typed diagnostic metrics, including all applicable requirements and negative cases in Additional diagnostics; AC-20.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-diagnostic-registry.py.

## Steps
1. Define the permitted diagnostic namespace, units, provenance and quality registry.
2. Validate diagnostic measurements and opaque contributor references.
3. Ensure missing diagnostics remain unknown and diagnostic events are not priced as requests.

## Acceptance Criteria
- Registered synthetic namespace measurements retain unit, scope, source and quality.
- Unknown metrics remain unavailable and diagnostic events never become paid model requests.

- Byte counts never populate token counts, monetary totals or independent quality labels.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Registered synthetic namespace measurements retain unit, scope, source and quality. → the stated result is observed.
  - Unknown metrics remain unavailable and diagnostic events never become paid model requests. → the stated result is observed.
  - Byte counts never populate token counts, monetary totals or independent quality labels. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
