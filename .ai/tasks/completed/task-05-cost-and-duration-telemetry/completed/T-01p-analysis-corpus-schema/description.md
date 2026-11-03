## Goal
Define and validate the versioned analysis corpus schema.

## Context
- Dependencies: T-01o — sequential shared-schema construction.
- Constraints: Follow the specification data model, serialization, bounds and privacy rules; unknown values remain explicit and no history is discovered.
- Reason: This entity has its own independently testable schema and coherent acceptance cluster.

Off-limits: Paid calls, unselected file discovery, shared publication, mutation of lifecycle evidence and unrelated entity schemas.

## Scope
- **In scope:** analysis corpus schema definitions, validation and any required bundle integration for this entity.
- **Out of scope:** Algorithms consuming the entity, other entity schemas and producer contract export.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-analysis-corpus-schema.py, scripts/validate-contracts.sh.

## Steps
1. Define versioned fields, explicit unknowns and limits for analysis corpus schema using the specification.
2. Validate typed fields and scope, and integrate the entity into its shared envelope where the specification requires it.
3. Verify synthetic positive and negative examples without network or model calls.

## Acceptance Criteria
- A valid synthetic analysis corpus schema with bounded explicit hashed inputs, as_of, scope, scenario, exclusions and schema versions is accepted and retains its declared data and explicit unknowns.
- Missing limits or hashes, unsupported version, invalid scope and excessive entries are rejected.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - Validate a complete synthetic analysis corpus schema → the declared values and explicit unknowns are preserved.
  - Supply missing limits or hashes, unsupported version, invalid scope and excessive entries are rejected → validation rejects it without leaking payload or creating a false result.
- **Edge cases:** missing fields, invalid types, duplicate keys, exact bounds and one-over limits, unknowns and forbidden fields.
