## Goal
Define and validate the versioned diagnostic measurement schema.

## Context
- Dependencies: T-01k — sequential shared-schema construction.
- Constraints: Follow the specification data model, serialization, bounds and privacy rules; unknown values remain explicit and no history is discovered.
- Reason: This entity has its own independently testable schema and coherent acceptance cluster.

Off-limits: Paid calls, unselected file discovery, shared publication, mutation of lifecycle evidence and unrelated entity schemas.

## Scope
- **In scope:** diagnostic measurement schema definitions, validation and any required bundle integration for this entity.
- **Out of scope:** Algorithms consuming the entity, other entity schemas and producer contract export.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-diagnostic-schema.py, scripts/validate-contracts.sh.

## Steps
1. Define versioned fields, explicit unknowns and limits for diagnostic measurement schema using the specification.
2. Validate typed fields and scope, and integrate the entity into its shared envelope where the specification requires it.
3. Verify synthetic positive and negative examples without network or model calls.

## Acceptance Criteria
- A valid synthetic diagnostic measurement schema with registered metric name, numeric value, unit, scope, source and measurement quality is accepted and retains its declared data and explicit unknowns.
- Unknown namespace, invalid unit or number and forbidden free-text fields are rejected.
- A nonempty valid diagnostic measurement is accepted within the shared usage bundle, and malformed diagnostics are rejected.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - Validate a complete synthetic diagnostic measurement schema → the declared values and explicit unknowns are preserved.
  - Supply unknown namespace, invalid unit or number and forbidden free-text fields are rejected → validation rejects it without leaking payload or creating a false result.
  - Validate bundles with valid and invalid diagnostic measurements → the valid measurement is accepted and the malformed measurement is rejected.
- **Edge cases:** missing fields, invalid types, duplicate keys, exact bounds and one-over limits, unknowns and forbidden fields.
