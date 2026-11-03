## Goal
Compare collection boundaries without precision loss.

## Context
- Owner-authorized fresh validation finding in PR #44.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** compare collection boundaries without precision loss and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-collection-segment-schema.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Reversed segment and gap boundaries beyond microsecond precision are rejected.
- Equal instants and correctly ordered arbitrary-precision boundaries remain valid, including gap containment.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - Reversed segment and gap boundaries beyond microsecond precision are rejected. Verify the stated result through the relevant public boundary.
  - Equal instants and correctly ordered arbitrary-precision boundaries remain valid, including gap containment. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
