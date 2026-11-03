## Goal
Deduplicate identical selected observations.

## Context
- Owner-authorized fresh validation finding in PR #57.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** deduplicate identical selected observations and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage_telemetry_adapter.py, tests/usage-source-normalization.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Identical selected files with distinct source declarations produce a valid deduplicated bundle.
- Distinct valid sources, associated contexts/evidence and quarantine diagnostics survive without duplicate paid contributions.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - Identical selected files with distinct source declarations produce a valid deduplicated bundle. Verify the stated result through the relevant public boundary.
  - Distinct valid sources, associated contexts/evidence and quarantine diagnostics survive without duplicate paid contributions. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
