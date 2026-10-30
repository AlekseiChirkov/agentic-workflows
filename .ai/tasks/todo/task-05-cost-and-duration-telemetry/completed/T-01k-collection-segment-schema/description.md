## Goal
Define and validate the versioned collection segment schema.

## Context
- Dependencies: T-01j — sequential shared-schema construction.
- Constraints: Follow the specification data model, serialization, bounds and privacy rules; unknown values remain explicit and no history is discovered.
- Reason: This entity has its own independently testable schema and coherent acceptance cluster.

Off-limits: Paid calls, unselected file discovery, shared publication, mutation of lifecycle evidence and unrelated entity schemas.

## Scope
- **In scope:** collection segment schema definitions, validation and any required bundle integration for this entity.
- **Out of scope:** Algorithms consuming the entity, other entity schemas and producer contract export.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-collection-segment-schema.py, scripts/validate-contracts.sh.

## Steps
1. Define versioned fields, explicit unknowns and limits for collection segment schema using the specification.
2. Validate typed fields and scope, and integrate the entity into its shared envelope where the specification requires it.
3. Verify synthetic positive and negative examples without network or model calls.

## Acceptance Criteria
- A valid synthetic collection segment schema with explicit owner-scoped collection segment, mode, boundaries and gap state is accepted and retains its declared data and explicit unknowns.
- Invalid mode, invalid timestamps, missing scope or unsupported version is rejected.
- A nonempty valid collection segment is accepted within the shared usage bundle, and malformed segments are rejected.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - Validate a complete synthetic collection segment schema → the declared values and explicit unknowns are preserved.
  - Supply invalid mode, invalid timestamps, missing scope or unsupported version is rejected → validation rejects it without leaking payload or creating a false result.
  - Validate bundles with valid and invalid collection segments → the valid segment is accepted and the malformed segment is rejected.
- **Edge cases:** missing fields, invalid types, duplicate keys, exact bounds and one-over limits, unknowns and forbidden fields.
