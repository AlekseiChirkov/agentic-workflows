## Goal
Define and validate the versioned price snapshot schema.

## Context
- Dependencies: T-01l — sequential shared-schema construction.
- Constraints: Follow the specification data model, serialization, bounds and privacy rules; unknown values remain explicit and no history is discovered.
- Reason: This entity has its own independently testable schema and coherent acceptance cluster.

Off-limits: Paid calls, unselected file discovery, shared publication, mutation of lifecycle evidence and unrelated entity schemas.

## Scope
- **In scope:** price snapshot schema definitions, validation and any required bundle integration for this entity.
- **Out of scope:** Algorithms consuming the entity, other entity schemas and producer contract export.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-price-snapshot-schema.py, scripts/validate-contracts.sh.

## Steps
1. Define versioned fields, explicit unknowns and limits for price snapshot schema using the specification.
2. Validate typed fields and scope, and integrate the entity into its shared envelope where the specification requires it.
3. Verify synthetic positive and negative examples without network or model calls.

## Acceptance Criteria
- A valid synthetic price snapshot schema with USD decimal rates, exact units, effective period or explicit unknown, model aliases, region, service, cache and tool parameters is accepted and retains its declared data and explicit unknowns.
- Noncanonical rates, ambiguous required fields and malformed time or unsupported versions are rejected.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - Validate a complete synthetic price snapshot schema → the declared values and explicit unknowns are preserved.
  - Supply noncanonical rates, ambiguous required fields and malformed time or unsupported versions are rejected → validation rejects it without leaking payload or creating a false result.
- **Edge cases:** missing fields, invalid types, duplicate keys, exact bounds and one-over limits, unknowns and forbidden fields.
