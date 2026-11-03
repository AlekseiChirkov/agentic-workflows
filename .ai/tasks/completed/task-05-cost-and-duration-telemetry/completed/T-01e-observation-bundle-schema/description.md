## Goal
Define and validate versioned observation and usage-bundle envelopes.

## Context
- Dependencies: T-01b supplies typed measurements and T-01a supplies canonical encoding.
- Constraints: Follow the specification data model, serialization, interface limits and quarantine requirements; shared bundles contain no raw source paths or content.
- Reason: Observation and bundle envelopes form one independently verifiable interchange component.

Off-limits: Shared-store publication, inferred provider capability and mutation of lifecycle events.

## Scope
- **In scope:** Observation, sanitized evidence-object and usage-bundle schemas, required and forbidden fields, types, bounds and canonical identifiers. Evidence references name a separate sanitized object and may not form a cycle.
- **Out of scope:** Other entity schemas, source parsing, producer contract export and publication.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-observation-bundle-schema.py, scripts/validate-contracts.sh.

## Steps
1. Define observation and bundle fields and their versioned constraints from the specification.
2. Validate positive examples, identity, byte and count limits, typed measurements and privacy exclusions.
3. Reject unsupported versions, duplicate or unknown normalized keys and invalid sizes before acceptance.

## Acceptance Criteria
- A complete synthetic observation and bundle validate and reproduce their canonical identifiers under key permutation.
- Unsupported versions, forbidden raw fields, identifiers above 256 characters, oversized observations and bundles are rejected without exposing source content.
- A measurement evidence digest matches canonical bytes of a separate sanitized evidence object; mismatched, absent or circular references cannot establish the association.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Validate positive observation and bundle fixtures under permutations → accepted objects and stable identifiers.
  - Supply invalid versions, fields and boundary-plus-one inputs → rejection without a normalized output or private text.
  - Link a measurement to an explicitly supplied sanitized evidence object → matching canonical digest is accepted; a mismatch, absence or cycle remains unverified.
- **Edge cases:** exact limits, multibyte strings, duplicate keys, nested objects, missing measurements and malformed hashes.
