## Goal
Keep account-scoped responses distinct in accounting.

## Context
- Owner-authorized fresh validation finding in PR #60.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** keep account-scoped responses distinct in accounting and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage_telemetry_resolution.py, scripts/usage_telemetry_completeness.py, tests/usage-resolution-integration.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Matching raw response IDs in distinct provider accounts resolve independently without component identity collisions.
- Response, token and cost contributions remain distinct and inventory/coverage never collapses them into a false completeness claim.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - Matching raw response IDs in distinct provider accounts resolve independently without component identity collisions. Verify the stated result through the relevant public boundary.
  - Response, token and cost contributions remain distinct and inventory/coverage never collapses them into a false completeness claim. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
