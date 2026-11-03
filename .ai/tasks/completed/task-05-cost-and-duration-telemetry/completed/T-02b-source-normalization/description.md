## Goal
Provide profile-driven source normalization and quarantine with observable, deterministic behavior.

## Context
- Dependencies: T-02a — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Source limits and errors; AC-01, AC-15, AC-24; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** profile-driven source normalization and quarantine, including all applicable requirements and negative cases in Source limits and errors; AC-01, AC-15, AC-24.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_sources.py, tests/usage-source-normalization.py, scripts/usage-telemetry.py.

## Steps
1. Decode only selected files through an evidenced versioned profile.
2. Normalize permitted numeric fields with fixed provenance and segment information.
3. Quarantine invalid records without retaining sensitive payload and reject invalid containers atomically.

## Acceptance Criteria
- Opaque project, source, provider-account scope and owner-candidate IDs are derived from explicitly selected inputs using a keyed domain-separated mapping or independently random local IDs; any identifying map and key remain private, and raw names, paths and secrets do not enter the normalized bundle.
- A valid selected export produces sanitized observations with fixed provenance and observation time.
- An invalid individual record is quarantined without its contents, while valid siblings remain partial and an invalid container yields no result.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Normalize selected synthetic inputs containing distinct low-entropy local identifiers → shared output contains only authorized opaque IDs, with no raw values or key, and unselected files are not read.
  - A valid selected export produces sanitized observations with fixed provenance and observation time. → the stated result is observed.
  - An invalid individual record is quarantined without its contents, while valid siblings remain partial and an invalid container yields no result. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
