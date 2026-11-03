## Goal
Provide canonical encoding and content identities with observable, deterministic behavior.

## Context
- Dependencies: none.
- Constraints: Follow the specification sections Serialization and content identity; AC-21; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** canonical encoding and content identities, including all applicable requirements and negative cases in Serialization and content identity; AC-21.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-canonical-encoding.py.

## Steps
1. Parse strict JSON and reject duplicate keys and unsupported numeric representations.
2. Serialize normalized objects with schema-specific ordering and compute SHA-256 identities.
3. Verify fixed observation time, ordered sequences and canonical byte vectors.

## Acceptance Criteria
- Permuting object keys and schema-defined sets preserves canonical bytes and SHA-256; changing ordered stream sequence changes them.
- Duplicate keys, boolean counters, invalid decimal strings and unsupported schema versions are rejected.

- A repeat on a later day with the same fixed observation time yields identical canonical bytes and hashes, matching a documented byte vector.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Permuting object keys and schema-defined sets preserves canonical bytes and SHA-256; changing ordered stream sequence changes them. → the stated result is observed.
  - Duplicate keys, boolean counters, invalid decimal strings and unsupported schema versions are rejected. → the stated result is observed.
  - A repeat on a later day with the same fixed observation time yields identical canonical bytes and hashes, matching a documented byte vector. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
