## Goal
Integrate bounded source adapters into the complete telemetry contract.

## Context
- type: composite
- children: T-02a, T-02b, T-02c
- Dependencies: T-01d
- Constraints: Preserve explicit scope, immutable evidence and unknown values throughout.
- Reason: The components are separately testable and require integrated verification.

Off-limits: Paid model calls, automatic model or policy changes, unsolicited history discovery and changes to existing evidence.

## Scope
- **In scope:** T-02a bounded explicit source selection; T-02b profile-driven source normalization and quarantine; T-02c destination safety.
- **Out of scope:** Other telemetry components and unrelated workflow behavior.
- **Target files:** scripts/usage_telemetry_sources.py, tests/usage-source-selection.py, scripts/usage-telemetry.py, tests/usage-source-normalization.py.

## Steps
See children: T-02a bounded explicit source selection; T-02b profile-driven source normalization and quarantine; T-02c destination safety.

## Acceptance Criteria
- An explicitly selected, digest-verified file is normalized using its declared profile and fixed observation time into a sanitized bundle.
- An invalid record in a valid selected source is quarantined while valid sibling observations remain explicitly partial.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - An explicitly selected, digest-verified file is normalized using its declared profile and fixed observation time into a sanitized bundle. → the integrated outputs agree.
  - An invalid record in a valid selected source is quarantined while valid sibling observations remain explicitly partial. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.
