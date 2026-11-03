## Goal
Provide response identity and deduplication with observable, deterministic behavior.

## Context
- Dependencies: T-03b — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Identity, attribution and late data; AC-03, AC-11, AC-12; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** response identity and deduplication, including all applicable requirements and negative cases in Identity, attribution and late data; AC-03, AC-11, AC-12.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_resolution.py, tests/usage-response-identity.py.

## Steps
1. Construct provider-account-response identities and verified call aliases.
2. Deduplicate branched copies and distinguish separate responses and ambiguous relationships.
3. Exclude potentially overlapping unresolved identities from additive totals.

## Acceptance Criteria
- The same response across branched sessions counts once, while two distinct responses from one call count twice.
- Ambiguous identity is retained as unresolved and is excluded from overlapping additive totals.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - The same response across branched sessions counts once, while two distinct responses from one call count twice. → the stated result is observed.
  - Ambiguous identity is retained as unresolved and is excluded from overlapping additive totals. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
