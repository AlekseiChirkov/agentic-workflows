## Goal
Define and validate the versioned source-profile schema.

## Context
- Dependencies: T-01e supplies common observation and bundle schema primitives.
- Constraints: Follow the specification data model and interface tables; keep source paths in closed local manifests only.
- Reason: Profile schema validation is independently verifiable from other entity schemas and the producer export.

Off-limits: Source discovery, report publication, warning delivery and production pricing changes.

## Scope
- **In scope:** Source-profile schema including provider, runtime, proven format version, field semantics, identity scope, finality, inventory, cache, effort, tools, known gaps and evidence date/source.
- **Out of scope:** Other entity schemas, source adapter algorithms and producer contract export.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-entity-schemas.py, scripts/validate-contracts.sh.

## Steps
1. Define the source-profile schema and required evidence and capability fields from the specification.
2. Validate typing, explicit unknown capabilities, profile version, identifiers and size/depth bounds.
3. Verify synthetic valid profiles and invalid or unsupported profiles without claiming real-provider support.

## Acceptance Criteria
- A versioned synthetic profile with explicit identity, counter semantics, finality and inventory evidence validates while unverified capabilities remain unknown.
- Missing mandatory fields, forbidden fields, unsupported versions and applicable limit violations are rejected without exposing raw source content.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - Validate a complete synthetic profile → declared capabilities and unknowns are preserved.
  - Mutate required fields, versions and bounds → typed rejection without private payload.
- **Edge cases:** unknown capability, exact limits, nested arrays, opaque identifiers and unsupported versions.
