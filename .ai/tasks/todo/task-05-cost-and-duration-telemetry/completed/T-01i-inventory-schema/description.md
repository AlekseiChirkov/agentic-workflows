## Goal
Define and validate the versioned inventory schema.

## Context
- Dependencies: T-01h — sequential shared-schema construction.
- Constraints: Follow the specification data model, serialization, bounds and privacy rules; unknown values remain explicit and no history is discovered.
- Reason: This entity has its own independently testable schema and coherent acceptance cluster.

Off-limits: Paid calls, unselected file discovery, shared publication, mutation of lifecycle evidence and unrelated entity schemas.

## Scope
- **In scope:** inventory schema definitions, validation and any required bundle integration for this entity.
- **Out of scope:** Algorithms consuming the entity, other entity schemas and producer contract export.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-inventory-schema.py, scripts/validate-contracts.sh.

## Steps
1. Define versioned fields, explicit unknowns and limits for inventory schema using the specification.
2. Validate typed fields and scope, and integrate the entity into its shared envelope where the specification requires it.
3. Verify synthetic positive and negative examples without network or model calls.

## Acceptance Criteria
- A valid synthetic inventory schema with scope, independent expected calls and responses, unresolved slots and complete, partial or unknown state with evidence is accepted and retains its declared data and explicit unknowns.
- Invalid inventory state, missing scope or over-limit entries are rejected without creating a denominator.
- A nonempty valid inventory is accepted within the shared usage bundle; malformed inventory entries are rejected without a false completeness claim.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - Validate a complete synthetic inventory schema → the declared values and explicit unknowns are preserved.
  - Supply invalid inventory state, missing scope or over-limit entries are rejected without creating a denominator → validation rejects it without leaking payload or creating a false result.
  - Validate bundles with valid and invalid inventory entries → the valid entry is accepted and the malformed entry is rejected.
- **Edge cases:** missing fields, invalid types, duplicate keys, exact bounds and one-over limits, unknowns and forbidden fields.
