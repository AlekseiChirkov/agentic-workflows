## Goal
Provide causal ownership and late evidence with observable, deterministic behavior.

## Context
- Dependencies: T-04d — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Identity, attribution and late data; AC-12, AC-13, AC-23; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** causal ownership and late evidence, including all applicable requirements and negative cases in Identity, attribution and late data; AC-12, AC-13, AC-23.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_resolution.py, tests/usage-causal-ownership.py.

## Steps
1. Assign exactly one evidenced owner or shared and unattributed pool for each response.
2. Calculate scope-relative attribution without inventing per-leaf shares.
3. Apply late evidence only to new immutable reports and preserve previously accepted artifacts.

## Acceptance Criteria
- A measurement is not treated as independently evidenced unless its explicitly supplied sanitized evidence matches the reference, source, scope and measured value; absent or unauthorized evidence remains unverified without discovering history.
- A shared 0.1 expense with two candidate leaves is counted once in the proven parent pool and is not split into 0.05 shares.
- A late observation changes only a newly produced report and an external unattributed pool is not included in a complete parent total.

- A 0.1 shared pool included once in a complete proven parent remains unattributed to both leaves, so neither leaf is declared complete.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Resolve matching, mismatched, absent and unauthorized evidence → only a proven matching association is verified.
  - A shared 0.1 expense with two candidate leaves is counted once in the proven parent pool and is not split into 0.05 shares. → the stated result is observed.
  - A late observation changes only a newly produced report and an external unattributed pool is not included in a complete parent total. → the stated result is observed.
  - A 0.1 shared pool included once in a complete proven parent remains unattributed to both leaves, so neither leaf is declared complete. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
