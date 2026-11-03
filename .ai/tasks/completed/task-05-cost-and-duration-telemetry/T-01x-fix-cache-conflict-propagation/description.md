## Goal
Propagate contradictory cache write evidence.

## Context
- Owner-authorized fresh validation finding in PR #54.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** propagate contradictory cache write evidence and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage_telemetry_contract.py, scripts/usage_telemetry_resolution.py, tests/usage-source-profiles.py, tests/usage-resolution-token-components.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Conflicting unsplit cache writes cannot produce usable derived input totals in separate or included-input profiles.
- Dependent measurements preserve conflict or unavailability and unrelated output counters remain usable; bundles and proofs preserve the distinction.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - Conflicting unsplit cache writes cannot produce usable derived input totals in separate or included-input profiles. Verify the stated result through the relevant public boundary.
  - Dependent measurements preserve conflict or unavailability and unrelated output counters remain usable; bundles and proofs preserve the distinction. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
