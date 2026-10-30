## Goal
Integrate resolution and completeness into the complete telemetry contract.

## Context
- type: composite
- children: T-04a, T-04b, T-04c, T-04d, T-04e
- Dependencies: T-03b
- Constraints: Preserve explicit scope, immutable evidence and unknown values throughout.
- Reason: The components are separately testable and require integrated verification.

Off-limits: Paid model calls, automatic model or policy changes, unsolicited history discovery and changes to existing evidence.

## Scope
- **In scope:** T-04a response identity and deduplication; T-04b stream finality and revisions; T-04c cumulative epochs and aggregate coverage; T-04d inventory and measurement completeness; T-04e causal ownership and late evidence.
- **Out of scope:** Other telemetry components and unrelated workflow behavior.
- **Target files:** scripts/usage_telemetry_resolution.py, tests/usage-response-identity.py, tests/usage-stream-revisions.py, tests/usage-cumulative-epochs.py, tests/usage-inventory-completeness.py, tests/usage-causal-ownership.py.

## Steps
See children: T-04a response identity and deduplication; T-04b stream finality and revisions; T-04c cumulative epochs and aggregate coverage; T-04d inventory and measurement completeness; T-04e causal ownership and late evidence.

## Acceptance Criteria
- Duplicate and revised observations resolve once against the independent inventory and assign a proven shared pool to its parent.
- An unresolved identity prevents an unjustified complete scope total; proven late evidence changes only a new report, which can become complete when all completeness conditions hold.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - Duplicate and revised observations resolve once against the independent inventory and assign a proven shared pool to its parent. → the integrated outputs agree.
  - An unresolved identity prevents an unjustified complete scope total; proven late evidence changes only a new report, which can become complete when all completeness conditions hold. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.
