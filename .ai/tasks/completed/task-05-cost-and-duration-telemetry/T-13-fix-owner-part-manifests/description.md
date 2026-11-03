## Goal
Preserve owner evidence in selected-part warning delivery.

## Context
- Owner-authorized fresh validation finding in PR #62.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** preserve owner evidence in selected-part warning delivery and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage-telemetry.py, scripts/usage_telemetry_delivery.py, scripts/usage_telemetry_contract.py, tests/usage-status-delivery-integration.py, tests/usage-status-parts-cli.py, tests/usage-status-large-parts.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Empty, small and large split owner manifests produce deliverable proposals while preserving immutable persisted owner evidence; public proposals remain free of local paths and are bound to the exact selected evidence.
- Selected usage, segment and warning parts evaluate correctly; revision checks, pending recovery and idempotence remain intact.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - Empty, small and large split owner manifests produce deliverable proposals while preserving immutable persisted owner evidence; public proposals remain free of local paths and are bound to the exact selected evidence. Verify the stated result through the relevant public boundary.
  - Selected usage, segment and warning parts evaluate correctly; revision checks, pending recovery and idempotence remain intact. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
