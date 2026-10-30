## Goal
Provide immutable usage bundle publication with observable, deterministic behavior.

## Context
- Dependencies: T-02b — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Publication and recovery; AC-13, AC-14, AC-15; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** immutable usage bundle publication, including all applicable requirements and negative cases in Publication and recovery; AC-13, AC-14, AC-15.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_publication.py, tests/usage-usage-publication.py, scripts/log-step.sh.

## Steps
1. Check opt-in mode, registered scope and the entire bounded bundle before mutation.
2. Install canonical bytes at a content-derived address atomically without overwriting or following symlinks.
3. Verify exact repeats and races once and emit a receipt only after complete visibility.

## Acceptance Criteria
- Shared publication verifies the selected profile, owner scope and authorized provenance of sanitized IDs and evidence; a digest-shaped string alone cannot prove that its content is safe or originates from the selected source.
- Concurrent exact publications yield one content-addressed file and a receipt only after complete installation.
- Corrupt existing content, path substitution and failed installation yield no false receipt or lifecycle mutation.

- Collection is off when the mode is unset or invalid; disabled or unregistered scope produces no publication or acceptance receipt.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Submit a bundle with digest-shaped IDs but absent or unauthorized provenance → reject without publication or a receipt; accept a matching explicitly authorized synthetic bundle.
  - Concurrent exact publications yield one content-addressed file and a receipt only after complete installation. → the stated result is observed.
  - Corrupt existing content, path substitution and failed installation yield no false receipt or lifecycle mutation. → the stated result is observed.
  - Collection is off when the mode is unset or invalid; disabled or unregistered scope produces no publication or acceptance receipt. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
