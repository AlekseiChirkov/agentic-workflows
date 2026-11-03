## Goal
Preserve nested ordered arrays in canonical sets.

## Context
- Owner-authorized fresh validation finding in PR #37.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** preserve nested ordered arrays in canonical sets and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-canonical-encoding.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Permuting an enclosing declared set preserves its identity while changing the order inside an undeclared nested array changes bytes and identity.
- Schema field sets and key-based ordering retain their established canonical vectors.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - Permuting an enclosing declared set preserves its identity while changing the order inside an undeclared nested array changes bytes and identity. Verify the stated result through the relevant public boundary.
  - Schema field sets and key-based ordering retain their established canonical vectors. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
